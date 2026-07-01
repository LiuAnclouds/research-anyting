// workflows/audit-loop.js
//
// Loop an executor agent against a multi-expert panel until the weighted
// aggregate >= target AND no veto fires, or escalate after maxRounds.
//
// RUNTIME AGENT VALIDATION
// ------------------------
// At the top of `runAuditLoop()` (right after panel weight totaling), every
// dispatched agent -- the executor plus every panel member -- is loaded and
// validated via `_dispatch.js` (loadAgentDef + validateAgent). The validator
// enforces agent-frontmatter-v1.json conformance and, critically, that
// `rigor_contract === 'three-times-verified'` is present. If any agent's
// frontmatter has been edited to strip the contract, the loop refuses to
// start. Agents whose definition file cannot be resolved (e.g. when running
// inside the Python audit_loop_sim harness where files are mocked) are
// logged and skipped -- the validation is the runtime safety net, not a
// strict precondition.
//
// Used as a building block by phase-specific pipelines (paper-writing,
// gnn-full, vlavlm-full). Each round writes a structured JSON audit verdict
// to knowledge-base/audit-rounds/YYYY-MM-DD-<phase>-round<N>.json.
//
// Public API:
//   runAuditLoop({phase, executorPrompt, panel, target=90, maxRounds=10,
//                 context={}, preFlight=true, kbRoot='knowledge-base'})
//     -> Promise<Result>
//
// `preFlight` (default true): for phase 'WRITE', run a deterministic
// scripts/lint_rigor.py scan before round 1 and, if gross rigor violations
// are detected, write a synthetic round-0 REVISE audit whose revise prompt
// feeds round 1's executor -- saving at least one full 5-expert round on
// fresh drafts. Non-WRITE phases and `preFlight: false` bypass it.
//
// where:
//   panel = [{ name: 'figure-expert', weight: 25, prompt: '...',
//              critical_axes: ['figure-vision-pass'] }, ...]
//
// Returns { status: 'PASS'|'ESCALATED', round, audit, executorOutput, trace }.
// On escalation also writes <phase>-ESCALATION.json. Does not throw -- callers
// decide whether escalation is fatal.

import {
  weightedMean,
  validateExpertVerdict,
  expertSchemaInline,
  normalizeExpertVerdict,
  validateAudit,
} from './_schema.js'
import { renderRevisePrompt } from './_prompts.js'
import { loadAgentDef, validateAgent } from './_dispatch.js'
import { estimateRoundCost, formatBudgetLine } from './_budget.js'

export const meta = {
  name: 'audit-loop',
  description: 'Generic loop-until-pass runner: executor + 3-5 expert panel, weighted score, gate >= 90, max 10 rounds.',
  phases: [
    { title: 'Execute', detail: 'Run the phase executor (with revise prompt on rounds > 1)' },
    { title: 'Audit', detail: 'Concurrent dispatch of 3-5 expert auditors' },
    { title: 'Aggregate', detail: 'Weighted score + veto check; PASS or REVISE' },
  ],
}

const AUDIT_DIR_DEFAULT = 'knowledge-base/audit-rounds'

function todayUTC() {
  // Date.now()/new Date() are not available in workflow scripts on this harness;
  // accept an injected timestamp via context or derive from round index.
  // Caller injects context.runStartedAt as ISO string when launching.
  return null
}

function todayStamp(ctx) {
  const iso = ctx?.runStartedAt || ctx?.timestamp || null
  if (!iso) return 'undated'
  return iso.slice(0, 10) // YYYY-MM-DD
}

function aggregate(phase, round, executor, results, ctx) {
  const totalW = results.reduce((s, r) => s + r.weight, 0)
  if (totalW !== 100) {
    throw new Error(`panel weights must sum to 100; got ${totalW}`)
  }
  for (let i = 0; i < results.length; i++) validateExpertVerdict(results[i], i)

  const agg = results.reduce((s, r) => s + r.score * r.weight, 0) / 100

  // Critical-axis veto: if an expert scores < 60 on one of its critical_axes,
  // it overrides aggregate.
  const vetoes = []
  for (const r of results) {
    const crit = r.critical_axes || []
    for (const axis of crit) {
      const s = r.axes?.[axis]
      if (s !== undefined && s < 60) {
        vetoes.push({
          axis, expert: r.name, reason: `critical axis '${axis}' scored ${s} < 60`,
          score_at_veto: s, threshold: 60,
        })
      }
    }
    if (r.vetoes && Array.isArray(r.vetoes)) vetoes.push(...r.vetoes)
  }

  const blocking = results.flatMap(r => r.blocking_findings || [])
  const advisory = results.flatMap(r => r.advisory_findings || [])

  return {
    panel: phase,
    round,
    timestamp: ctx?.runStartedAt || null,
    executor_agent: executor,
    experts: results,
    aggregate: Math.round(agg * 10) / 10,
    aggregate_formula: 'sum(expert.score * expert.weight) / 100',
    decision: (agg >= (ctx?.target ?? 90) && vetoes.length === 0) ? 'PASS' : 'REVISE',
    vetoes_global: vetoes,
    blocking_findings: blocking,
    advisory_findings: advisory,
    diff_vs_previous_round: null,
  }
}

function diffRounds(curr, prev) {
  if (!prev) return null
  const out = { axes_improved: [], axes_regressed: [], new_blocking: [], resolved_blocking: [] }
  const flatten = (a) => {
    const m = {}
    for (const e of a.experts) for (const [ax, sc] of Object.entries(e.axes)) m[`${e.name}.${ax}`] = sc
    return m
  }
  const c = flatten(curr), p = flatten(prev)
  for (const k of Object.keys(c)) {
    if (p[k] === undefined) continue
    if (c[k] > p[k] + 0.5) out.axes_improved.push(`${k}: ${p[k]} -> ${c[k]}`)
    if (c[k] < p[k] - 0.5) out.axes_regressed.push(`${k}: ${p[k]} -> ${c[k]}`)
  }
  const prevBlocking = new Set((prev.blocking_findings || []).map(f => `${f.axis}::${f.msg}`))
  const currBlocking = new Set((curr.blocking_findings || []).map(f => `${f.axis}::${f.msg}`))
  for (const k of currBlocking) if (!prevBlocking.has(k)) out.new_blocking.push(k)
  for (const k of prevBlocking) if (!currBlocking.has(k)) out.resolved_blocking.push(k)
  return out
}

// Log the running phase-total of estimated cost across all rounds in `trace`.
// Sums `audit.meta.estimated_cost_usd` (set by the in-loop estimator); rounds
// that lack meta (e.g. legacy reruns) contribute 0.
function logPhaseCostTotal(phaseName, trace) {
  const rounds = trace?.rounds || []
  const total = rounds.reduce((s, r) => s + (r.meta?.estimated_cost_usd || 0), 0)
  log(`[${phaseName}] total estimated cost across ${rounds.length} round(s): ~$${total.toFixed(2)}`)
}

/**
 * Persist the pipeline-recovery snapshot to `<kbRoot>/_state.json`.
 * Schema: `schemas/state-v1.json`. Called once per audit round, right after
 * the per-round audit JSON is written.
 *
 * Reuses the caller's `onWriteAudit(path, json)` callback because it is the
 * only filesystem primitive the harness gives us inside workflow scripts.
 * Workflow scripts can't call `new Date()` (no clock in the V8 sandbox), so
 * both `runStartedAt` and `lastUpdatedAt` are populated from
 * `ctx.runStartedAt` — the parent workflow injects it at launch. The
 * cumulative cost total is initialized to 0; the parent workflow script
 * maintains the running sum across rounds and may patch the field on the
 * file after each call (per-round cost is already on
 * `audit.meta.estimated_cost_usd`).
 *
 * Consumed by `scripts/mr_resume.py` and the `/mr resume` skill.
 */
async function writeState(ctx, phaseName, round, audit, auditPath, onWriteAudit) {
  if (!onWriteAudit) return
  const kbRoot = ctx?.kbRoot || 'knowledge-base'
  const state = {
    project_root: ctx?.manuscriptPath || ctx?.projectRoot || '.',
    current_phase: phaseName,
    last_audit_round_path: auditPath,
    last_audit_round: round,
    last_aggregate: audit.aggregate,
    last_decision: audit.decision,
    blocking_findings_unresolved: audit.blocking_findings || [],
    vetoes_unresolved: audit.vetoes_global || [],
    runStartedAt: ctx?.runStartedAt || null,
    lastUpdatedAt: ctx?.runStartedAt || null,
    estimated_cost_usd_to_date: 0,
  }
  try {
    await onWriteAudit(`${kbRoot}/_state.json`, state)
  } catch (e) {
    log(`[${phaseName}] writing _state.json failed (non-fatal): ${e?.message || e}`)
  }
}

/**
 * Main loop. Caller-supplied:
 *   executorPrompt: (round, revisePrompt, priorTrace) -> string
 *     -- builds the executor's prompt for round N
 *   panel: [{ name, weight, prompt: (executorOutput, retrievedEvidence, round) -> string,
 *             critical_axes?: [string], schema?: object }]
 *   target: pass threshold (default 90)
 *   maxRounds: escalate after this many (default 10)
 *   context: { runStartedAt, kbRoot, manuscriptPath, ... }
 *
 * Each executor and expert call uses the host's `agent()` runtime (assumed
 * imported in the surrounding workflow script via the standard Workflow API).
 * Because audit-loop.js is itself loaded inside a workflow script, the host
 * primitives `agent`, `parallel`, `phase`, `log` are global -- we don't import
 * them; the caller wires us in by name.
 *
 * RAG injection (P2): before the panel dispatch each round, we fan out N
 * parallel "rag-retrieve" sub-agents -- one per expert -- that invoke
 * `scripts/expert_retrieve.py` against that expert's prebuilt index (see
 * `scripts/build_expert_index.py`) using the executor output as the query.
 * The top-K passages are passed to `p.prompt(execOut, retrievedEvidence, round)`
 * as the `{{retrieved_evidence}}` substitution slot. Experts whose index is
 * missing (or whose retrieval errors out) receive `null` and the expert
 * prompt template is expected to degrade gracefully (i.e. operate without
 * external evidence). The N retrievals and K panel calls each round are
 * fully parallel -- N + K independent agent dispatches via two `parallel()`
 * blocks back-to-back.
 *
 * Side effect -- cost tracking: each round computes an estimated token + USD
 * cost via `_budget.js#estimateRoundCost` (using panel definitions + default
 * executor/expert token budgets), logs a one-line summary via
 * `formatBudgetLine`, and attaches the estimate to the per-round audit JSON
 * under `audit.meta = { estimated_tokens, estimated_cost_usd, cost_breakdown }`.
 * After the loop finishes (PASS or ESCALATED), a final phase-total summary
 * line is logged summing `audit.meta.estimated_cost_usd` across all rounds.
 * These are estimates only -- the harness does not return real telemetry,
 * so `_budget.js` defaults are assumed.
 *
 * Pre-flight rigor scan ("round 0", P4-E):
 *   When `preFlight === true` (default) AND `phaseName === 'WRITE'`, before
 *   round 1's executor fires we dispatch a tiny agent that runs
 *   `python scripts/lint_rigor.py <manuscript_root>` and returns the JSON
 *   report. We parse `n_findings` and `by_kind`. If the report shows gross
 *   rigor-contract violations -- `by_kind['decimal-without-footnote'] > 50`
 *   OR `n_findings > 100` -- we synthesise an audit verdict
 *   (panel='WRITE', round=0, aggregate=30, decision='REVISE') with one
 *   blocking finding per offending kind, push it into `trace.rounds`,
 *   persist it via `onWriteAudit` as `*-WRITE-round0.json` (so
 *   `audit_diff.py` and `mr_resume.py` see it like any normal round), and
 *   render a revise prompt via `renderRevisePrompt` that is fed into round
 *   1's executor. Round 1's executor is NOT skipped -- it uses the revise
 *   prompt to fix the placeholder problems before the 5-expert audit panel
 *   runs. The whole pre-flight is wrapped in try/catch: any failure
 *   (missing script, manuscript root unset, agent dispatch fault, JSON
 *   parse error) is non-fatal -- we log and proceed to the normal loop
 *   with `revisePrompt = null`. Callers pass `preFlight: false` to
 *   disable; the default saves at least one full 5-expert round on most
 *   fresh drafts.
 *
 * @param {object}   params
 * @param {string}   params.phase           Phase name (e.g. 'WRITE').
 * @param {string}   params.executor        Executor agent name.
 * @param {Function} params.executorPrompt  (round, revisePrompt, priorTrace) -> string
 * @param {Array}    params.panel           3-5 expert defs; weights sum to 100.
 * @param {number}  [params.target=90]      Pass threshold.
 * @param {number}  [params.maxRounds=10]   Escalate after N rounds.
 * @param {object}  [params.context={}]     { runStartedAt, kbRoot, manuscriptPath, ... }
 * @param {Function}[params.onWriteAudit]   Optional callback(jsonPath, audit).
 * @param {boolean} [params.preFlight=true] When true and `phase === 'WRITE'`,
 *   run a deterministic `scripts/lint_rigor.py` scan over the manuscript
 *   before round 1's executor. If gross violations are detected
 *   (>50 decimal-without-footnote OR >100 total findings), a synthetic
 *   round-0 audit (aggregate=30, decision='REVISE') is written to the
 *   audit-rounds dir and its revise prompt is threaded into round 1's
 *   executor, saving at least one full 5-expert audit round on fresh
 *   drafts. Failures are non-fatal. Pass `false` to skip entirely.
 */
export async function runAuditLoop(params) {
  const {
    phase: phaseName,
    executor,
    executorPrompt,
    panel,
    target = 90,
    maxRounds = 10,
    context = {},
    onWriteAudit = null, // optional callback(jsonPath, audit)
    preFlight = true,
  } = params

  if (!Array.isArray(panel) || panel.length < 3 || panel.length > 5) {
    throw new Error(`panel must have 3-5 experts; got ${panel?.length}`)
  }
  const totalWeight = panel.reduce((s, p) => s + p.weight, 0)
  if (totalWeight !== 100) {
    throw new Error(`panel weights must sum to 100; got ${totalWeight}`)
  }

  // Runtime agent-frontmatter validation via _dispatch.js. Refuses to start
  // the loop if any executor or panel member has been edited to drop
  // rigor_contract === 'three-times-verified'. Unresolvable agent files
  // (e.g. under the audit_loop_sim Python harness) are logged but non-fatal.
  const toValidate = [executor, ...panel.map(p => p.name)]
  const validationErrors = []
  for (const name of toValidate) {
    try {
      const def = await loadAgentDef(name)
      const v = validateAgent(def)
      if (!v.ok) validationErrors.push({ agent: name, errors: v.errors })
    } catch (e) {
      // Agent file unresolvable -- non-fatal; log it but continue.
      log(`[${phaseName}] could not validate ${name}: ${e?.message || e}`)
    }
  }
  if (validationErrors.length) {
    throw new Error(`Agent validation failed:\n${JSON.stringify(validationErrors, null, 2)}`)
  }
  log(`[${phaseName}] validated ${toValidate.length} agents via _dispatch.js`)

  // Mode-collapse mitigation (P2):
  //   Anchors (low temp, deterministic):  statistics, format-expert, claim-trace-expert,
  //                                       cross-section-consistency, hallucination-expert
  //   Critics (mid temp):                  most reviewers and analysts
  //   Adversaries (high temp, dissent):    devils-advocate, bias-auditor
  // A panel entry's explicit { temperature, model } wins over the rotation.
  // The rotation makes "all 5 experts on the same temperature → spurious agreement"
  // structurally impossible.
  const TEMP_ANCHORS    = new Set([
    'statistics', 'format-expert', 'claim-trace-expert',
    'cross-section-consistency', 'hallucination-expert',
    'complexity', 'protocol-reproducibility',
  ])
  const TEMP_ADVERSARIES = new Set([
    'devils-advocate', 'bias-auditor',
  ])
  for (const p of panel) {
    if (p.temperature === undefined) {
      if (TEMP_ANCHORS.has(p.name))         p.temperature = 0.2
      else if (TEMP_ADVERSARIES.has(p.name)) p.temperature = 0.9
      else                                   p.temperature = 0.5
    }
  }
  log(`[${phaseName}] mode-collapse mitigation: temps = ${panel.map(p => `${p.name}=${p.temperature}`).join(', ')}`)

  const trace = { phase: phaseName, target, maxRounds, rounds: [] }
  let revisePrompt = null

  // ---------------------------------------------------------------------
  // Pre-flight rigor scan ("round 0"). See JSDoc for `preFlight` above.
  // ---------------------------------------------------------------------
  if (preFlight && phaseName === 'WRITE') {
    try {
      phase(`${phaseName} round 0 - pre-flight rigor scan`)
      const manuscriptRoot =
        context.manuscriptPath || context.manuscriptRoot || 'manuscript'
      const auditDir = context.kbRoot || AUDIT_DIR_DEFAULT

      const report = await agent(
        `Run the command exactly: python scripts/lint_rigor.py ${manuscriptRoot}\n` +
        `The script prints a JSON report to stdout. Return ONLY that JSON object ` +
        `(no prose, no markdown fences). The JSON has keys: n_files, n_findings, ` +
        `by_kind (object: kind -> count), findings (array). If the script errors, ` +
        `return {"n_findings": 0, "by_kind": {}, "error": "<stderr-first-line>"}.`,
        {
          label: `${phaseName.toLowerCase()}-preflight-lint-r0`,
          phase: `${phaseName}-r0-preflight`,
          schema: {
            type: 'object',
            properties: {
              n_findings: { type: 'number' },
              by_kind:    { type: 'object' },
            },
          },
        }
      )

      const nFindings = Number(report?.n_findings || 0)
      const byKind    = report?.by_kind || {}
      const decimals  = Number(byKind['decimal-without-footnote'] || 0)
      const trip      = decimals > 50 || nFindings > 100

      if (trip) {
        // Build one blocking finding per kind (cap snippet at sensible len).
        const blocking_findings = Object.entries(byKind)
          .filter(([, n]) => Number(n) > 0)
          .map(([kind, n]) => ({
            axis: 'rigor_compliance',
            severity: 'blocking',
            msg:
              `lint_rigor reports ${n} ${kind} occurrence(s); rewrite to add ` +
              `[^v]: footnotes before paying for the 5-expert panel`,
            kind,
            count: Number(n),
          }))

        const round0Audit = {
          panel: phaseName,
          round: 0,
          timestamp: context?.runStartedAt || null,
          executor_agent: executor,
          experts: [],
          aggregate: 30,
          aggregate_formula: 'pre-flight synthetic (lint_rigor)',
          decision: 'REVISE',
          vetoes_global: [],
          blocking_findings,
          advisory_findings: [],
          diff_vs_previous_round: null,
          meta: {
            source: 'pre-flight-lint_rigor',
            lint_report_summary: {
              n_findings: nFindings,
              by_kind: byKind,
            },
            trip_reason:
              decimals > 50
                ? `decimal-without-footnote=${decimals} > 50`
                : `total findings=${nFindings} > 100`,
          },
        }

        trace.rounds.push(round0Audit)
        const r0Path = `${auditDir}/${todayStamp(context)}-${phaseName}-round0.json`
        if (onWriteAudit) {
          try { await onWriteAudit(r0Path, round0Audit) }
          catch (e) { log(`[${phaseName}] pre-flight: writing round0 audit failed: ${e?.message || e}`) }
        }
        // Persist recovery snapshot so /mr resume can see the pre-flight verdict.
        await writeState(context, phaseName, 0, round0Audit, r0Path, onWriteAudit)
        revisePrompt = renderRevisePrompt(round0Audit)
        log(
          `[${phaseName}] pre-flight tripped: ${decimals} decimal-without-footnote, ` +
          `${nFindings} total findings -> synthetic round 0 written; round 1 will ` +
          `revise against lint findings before audit panel runs`
        )
      } else {
        log(
          `[${phaseName}] pre-flight clean (${nFindings} lint findings, ` +
          `${decimals} decimal-without-footnote); entering round 1 audit panel`
        )
      }
    } catch (e) {
      // Non-fatal: log and continue to the normal loop.
      log(`[${phaseName}] pre-flight rigor scan failed (non-fatal): ${e?.message || e}`)
      revisePrompt = null
    }
  }

  for (let round = 1; round <= maxRounds; round++) {
    phase(`${phaseName} round ${round} - execute`)
    const execOut = await agent(
      executorPrompt(round, revisePrompt, trace.rounds.slice(-3)),
      { label: `${phaseName.toLowerCase()}-exec-r${round}`, phase: `${phaseName}-r${round}` }
    )

    // P2 RAG injection: `{{retrieved_evidence}}` is the slot in each expert's
    // prompt where the top-K passages from that expert's RAG index get
    // injected. If the expert has no seeded index (or retrieval fails) the
    // value is `null` and the expert prompt template degrades gracefully.
    // N retrievals here are fully parallel -- one tiny rag-retrieve agent
    // per expert -- and run before the K-way panel dispatch below.
    phase(`${phaseName} round ${round} - retrieve evidence`)
    const retrievedPerExpert = await parallel(
      panel.map(p => () => agent(
        `Run the command: python scripts/expert_retrieve.py ${p.name} --query <executor-output-first-4k-chars> --k 8 ` +
        `Return ONLY the JSON output from that script. ` +
        `Executor output (first 4k chars): ${execOut.slice(0, 4000)}`,
        {
          label: `${phaseName.toLowerCase()}-${p.name}-rag-r${round}`,
          phase: `${phaseName}-r${round}-rag`,
          schema: { type: 'object', properties: { results: { type: 'array' } } },
        }
      ).then(r => r?.results || null).catch(() => null))
    )

    phase(`${phaseName} round ${round} - audit`)
    const expertResults = await parallel(
      panel.map((p, i) => () => agent(
        p.prompt(execOut, retrievedPerExpert[i], round),
        {
          label: `${phaseName.toLowerCase()}-${p.name}-r${round}`,
          phase: `${phaseName}-r${round}`,
          schema: p.schema || expertSchemaInline(),
          // Mode-collapse mitigation: per-expert temperature; harness applies
          // it if the dispatched agent supports temperature, otherwise ignored.
          temperature: p.temperature,
          model: p.model,
        }
      ).then(v => normalizeExpertVerdict(v, p)))
    )

    // Cost tracking: estimate this round's token + USD spend from panel defs.
    // Real per-call telemetry is not surfaced by the harness, so we fall back
    // to _budget.js defaults (~12k/4k executor, ~8k/2k per expert). The
    // estimate is attached to audit.meta for downstream rollup tooling.
    const roundCost = estimateRoundCost({
      panel,
      expertAvgTokens: undefined,
      executorTokens:  undefined,
      executorModel:   'inherit',
    })
    log(formatBudgetLine(roundCost, `${phaseName} r${round}`))

    // Panel-completeness guard: if any expert returned null (agent failure,
    // schema-validation reject, dispatch fault), we CANNOT call aggregate()
    // -- it enforces weights-sum-to-100 and the surviving experts' weights
    // will fall short. Emit a synthetic REVISE audit that flags the missing
    // experts and let the loop continue to the next round.
    const nullCount = expertResults.filter(e => !e).length
    let audit
    if (nullCount > 0) {
      const failedExperts = panel
        .filter((_, i) => !expertResults[i])
        .map(p => p.name)
      log(
        `[${phaseName} r${round}] ${nullCount}/${panel.length} experts failed ` +
        `(${failedExperts.join(', ')}) -- emitting REVISE without aggregate`
      )
      audit = {
        panel: phaseName,
        round,
        timestamp: context?.runStartedAt || null,
        executor_agent: executor,
        experts: [],
        aggregate: 0,
        aggregate_formula: 'sum(expert.score * expert.weight) / 100',
        decision: 'REVISE',
        vetoes_global: [{
          axis: 'panel-completeness',
          expert: 'audit-loop',
          reason: `${nullCount} expert(s) failed to return: ${failedExperts.join(', ')}`,
          score_at_veto: 0,
          threshold: 100,
        }],
        blocking_findings: [{
          axis: 'panel-completeness',
          severity: 'blocking',
          msg: `Rerun panel: ${failedExperts.join(', ')} did not return`,
          fix_hint: 'Check the expert agent files and re-dispatch the panel',
        }],
        advisory_findings: [],
        diff_vs_previous_round: null,
      }
    } else {
      audit = aggregate(phaseName, round, executor, expertResults, { ...context, target })
    }
    audit.meta = {
      ...(audit.meta || {}),
      estimated_tokens: roundCost.tokens_total,
      estimated_cost_usd: roundCost.cost_usd,
      cost_breakdown: roundCost.breakdown,
    }
    audit.diff_vs_previous_round = diffRounds(audit, trace.rounds[trace.rounds.length - 1])
    trace.rounds.push(audit)

    const auditPath = `${context.kbRoot || AUDIT_DIR_DEFAULT}/${todayStamp(context)}-${phaseName}-round${round}.json`
    if (onWriteAudit) await onWriteAudit(auditPath, audit)
    // Persist recovery snapshot for /mr resume after every round.
    await writeState(context, phaseName, round, audit, auditPath, onWriteAudit)
    log(`${phaseName} round ${round}: aggregate=${audit.aggregate} decision=${audit.decision} vetoes=${audit.vetoes_global.length}`)

    if (audit.decision === 'PASS') {
      logPhaseCostTotal(phaseName, trace)
      return { status: 'PASS', round, audit, executorOutput: execOut, trace }
    }

    revisePrompt = renderRevisePrompt(audit)
  }

  // Escalation
  const escalation = {
    status: 'ESCALATED',
    reason: `Failed to reach target ${target} after ${maxRounds} rounds`,
    phase: phaseName,
    last_three_rounds: trace.rounds.slice(-3),
  }
  if (onWriteAudit) {
    await onWriteAudit(
      `${context.kbRoot || AUDIT_DIR_DEFAULT}/${todayStamp(context)}-${phaseName}-ESCALATION.json`,
      escalation
    )
  }
  log(`${phaseName}: ESCALATED after ${maxRounds} rounds (target=${target}). See audit-rounds/.`)
  logPhaseCostTotal(phaseName, trace)
  return { status: 'ESCALATED', escalation, trace }
}

// Re-export helpers for tests / external callers
export { aggregate, weightedMean, renderRevisePrompt, diffRounds, expertSchemaInline, writeState }
