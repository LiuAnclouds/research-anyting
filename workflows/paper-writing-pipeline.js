// workflows/paper-writing-pipeline.js
// Phase 5 (WRITE) of the Moon-Research v2 pipeline.
//
// Two modes:
//   - default (v2)        : runs the 5-expert WRITE audit panel via audit-loop.js
//                            until aggregate >= 90 (max 10 rounds).
//   - { useLegacy: true } : the original single-shot Analyze->Write->Review->Revise
//                            flow (kept for backward compatibility).
//
// Caller is expected to set context.runStartedAt = ISO string before invoking,
// since workflow scripts cannot call Date.now() / new Date().
//
// import { runAuditLoop } from './audit-loop.js'
import { runAuditLoop } from './audit-loop.js'
import { loadAgentDef, validateAgent } from './_dispatch.js'

// Up-front validation of executor agents used by the figure pipeline and
// the WRITE phase. These agents are dispatched directly via `agent(...)`
// (not through runAuditLoop, which validates its own panel/executor) so we
// fail early if any of them has been edited to drop `rigor_contract`.
// Wrapped in try/catch -- emit a warning but don't hard-fail if the workflow
// runtime doesn't have FS access to resolve agent files.
const _executorAgentsToValidate = [
  'figure-planner',
  'figure-prompt-critic',
  'figure-renderer',
  'figure-vision-critic',
  'figure-integrator',
  'paper-writer',
]
const _executorValidationErrors = []
for (const _name of _executorAgentsToValidate) {
  try {
    const _def = await loadAgentDef(_name)
    const _v = validateAgent(_def)
    if (!_v.ok) _executorValidationErrors.push({ agent: _name, errors: _v.errors })
  } catch (_e) {
    log(`[paper-writing-pipeline] WARN: could not validate ${_name}: ${_e?.message || _e}`)
  }
}
if (_executorValidationErrors.length) {
  throw new Error(`paper-writing-pipeline executor agent validation failed:\n${JSON.stringify(_executorValidationErrors, null, 2)}`)
}
log(`[paper-writing-pipeline] validated ${_executorAgentsToValidate.length} executor agents via _dispatch.js`)

export const meta = {
  name: 'paper-writing-pipeline',
  description: 'Phase 5 WRITE: section drafting + figure pipeline + 5-expert audit panel (loop until >=90).',
  phases: [
    { title: 'Analyze',    detail: 'Extract insights and narrative from experimental results' },
    { title: 'Write',      detail: 'Generate manuscript sections concurrently' },
    { title: 'Figures',    detail: 'Per-slot pipeline: planner -> prompt-critic -> renderer -> vision-critic -> integrator' },
    { title: 'AuditWrite', detail: 'WRITE panel: figure / hallucination / format / claim-trace / prose-rigor' },
    { title: 'Review',     detail: 'REVIEW panel: r1-methodology / r2-experiments / eic / reproducibility / devils-advocate' },
    { title: 'Revise',     detail: 'Apply review feedback' },
  ],
}

phase('Analyze')
const insightReport = await agent(
  'Analyze the experimental results and extract: (1) performance attribution per component, ' +
  '(2) failure case taxonomy, (3) condition analysis, (4) paper narrative. ' +
  'Use the appropriate insight-analyzer agent definition for the domain. ' +
  'Apply the Three-Times Rule (shared/references/audit-doctrine.md) to every quantitative claim.',
  { phase: 'Analyze', schema: null }
)

phase('Write')
const sections = ['abstract', 'introduction', 'related-work', 'method', 'experiments', 'conclusion']
const manuscript = await pipeline(
  sections,
  (section) => agent(
    `Write the ${section} section. Use agents/paper-writer.md. ` +
    `Target venue: see the idea's target_venues field. ` +
    `Follow shared/references/writing-standards.md. ` +
    `Three-Times Rule (shared/references/audit-doctrine.md) applies to every quantitative claim: ` +
    `each numeric value must carry a [^v]: footnote with locus-1 (data file:line), ` +
    `locus-2 (recompute cmd or external URL), locus-3 (other sections that mention it). ` +
    `Bare numerics without footnotes will be rewritten to [UNVERIFIED] and blocked.`,
    { label: `write-${section}`, phase: 'Write', schema: null }
  )
)

// Stage 5b: figure pipeline — runs per-slot through planner → prompt-critic → renderer → vision-critic → integrator.
// Each slot is independent; slots run in pipeline() so the slowest slot does not block the others.
phase('Figures')
const figurePlan = await agent(
  `Use agents/figure-planner.md to write manuscript/figures/PLAN.json. ` +
  `Target venue tier determines min_figures (CCF-B: 6, CCF-A: 8). ` +
  `Each slot must point to a real data file in experiments/**. ` +
  `Conform to schemas/figure-plan.json.`,
  { label: 'figure-planner', phase: 'Figures', schema: null }
)
// prompt-critic audits PLAN.json (read-only); figure-slot-list extracts slot_ids
// from PLAN.json (read-only). Neither consumes the other's output, so per
// shared/references/parallelism-doctrine.md they fan out after the planner.
// (In a full pipeline run, the planner-critic loop iterates here until prompt-critic PASSes.
// For brevity in this script we trust the prompt-critic's first pass.)
const [promptCritic, figureSlots] = await parallel([
  () => agent(
    `Use agents/figure-prompt-critic.md to audit manuscript/figures/PLAN.json. ` +
    `Score completeness / data-fidelity / visual-story / accessibility / caption-coherence. ` +
    `<85 aggregate → emit revise findings (figure-planner will re-run); ≥85 → PASS.`,
    { label: 'figure-prompt-critic', phase: 'Figures', schema: null }
  ),
  () => agent(
    `Read manuscript/figures/PLAN.json and emit ONLY a JSON list of slot_ids. ` +
    `No prose.`,
    { label: 'figure-slot-list', phase: 'Figures', schema: {
      type: 'object', required: ['slot_ids'],
      properties: { slot_ids: { type: 'array', items: { type: 'string', pattern: '^fig:[a-z0-9-]+$' } } }
    }}
  ),
])
const slotIds = (figureSlots && figureSlots.slot_ids) || []
const renderedSlots = await pipeline(
  slotIds,
  (slotId) => agent(
    `Use agents/figure-renderer.md to render slot ${slotId} from manuscript/figures/PLAN.json. ` +
    `Produce both fig_<slot>.pdf and fig_<slot>.png at the configured size and seed.`,
    { label: `render-${slotId}`, phase: 'Figures', schema: null }
  ),
  (renderOut, slotId) => agent(
    `Use agents/figure-vision-critic.md to score manuscript/figures/fig_${slotId.replace(/^fig:/,'')}.png on 6 axes: ` +
    `no-clipping, legend-not-overlapping, text-legibility, axis-labels-present, palette-accessible, data-vs-plan-fidelity. ` +
    `Open the PNG via Read. Score <85 → blocking; figure-renderer re-runs.`,
    { label: `vision-${slotId}`, phase: 'Figures', schema: null }
  ),
  (visionOut, slotId) => agent(
    `Use agents/figure-integrator.md to insert ${slotId} into its target section per PLAN.json. ` +
    `Add the \\begin{figure} block + caption + label + in-text reference. ` +
    `Skip if figure-vision-critic returned REVISE on the prior step.`,
    { label: `integrate-${slotId}`, phase: 'Figures', schema: null }
  ),
)

// Stage 5c: WRITE audit panel. Loops the executor against 5 experts until the
// weighted aggregate >= 90 or maxRounds (10) is reached.
phase('AuditWrite')

const writePanel = [
  {
    name: 'figure-expert',
    weight: 25,
    critical_axes: ['figure-count', 'figure-vision-pass'],
    prompt: (execOut, retrieved, round) =>
      `You are figure-expert (agents/figure-expert.md). Audit the manuscript's figure suite at the document level. ` +
      `Round ${round}. Read PLAN.json, count \\begin{figure} blocks, aggregate per-figure vision audits, score caption quality, ` +
      `and check in-section referencing. Output a JSON object matching schemas/audit-v1.json $defs/expertVerdict. ` +
      `Manuscript root: manuscript/. ` +
      `Three-Times Rule applies to your verdict itself.`,
  },
  {
    name: 'hallucination-expert',
    weight: 25,
    critical_axes: ['cite-resolves', 'baseline-resolves', 'dataset-resolves'],
    prompt: (execOut, retrieved, round) =>
      `You are hallucination-expert (agents/hallucination-expert.md). Run scripts/verify_citations.py on manuscript/references.bib ` +
      `and scripts/verify_baselines.py on the baselines extracted from sections/05_experiments.tex. ` +
      `Cross-reference datasets against shared/references/benchmark-registry.yaml (fall back to the hardcoded P0 registry in the agent prose if missing). ` +
      `Round ${round}. Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'format-expert',
    weight: 20,
    critical_axes: ['latex-compile-clean', 'xref-resolved', 'label-unique', 'no-placeholder'],
    prompt: (execOut, retrieved, round) =>
      `You are format-expert (agents/format-expert.md). Run pdflatex 3 passes + bibtex on manuscript/main.tex using ` +
      `TinyTeX at C:/Users/kangjie.xu/AppData/Roaming/TinyTeX/bin/windows. Parse main.log per the regex table in your agent definition. ` +
      `Also run the static .tex sweeps (label uniqueness, xref resolvability, placeholder check, cite-parity). ` +
      `Round ${round}. Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'claim-trace-expert',
    weight: 20,
    critical_axes: ['cross-section-equality', 'traceable-to-experiments'],
    prompt: (execOut, retrieved, round) =>
      `You are claim-trace-expert (agents/claim-trace-expert.md). Extract every decimal numeric from manuscript/**/*.tex, ` +
      `group by (metric, dataset, model) context, flag cross-section disagreements, and trace each group to a value in ` +
      `experiments/** (tolerance 0.5%). Round ${round}. Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'prose-rigor-expert',
    weight: 10,
    critical_axes: ['no-anonymous-placeholder'],
    prompt: (execOut, retrieved, round) =>
      `You are prose-rigor-expert (agents/prose-rigor-expert.md). Sweep manuscript/**/*.tex for prohibited constructions per ` +
      `shared/references/writing-standards.md and check hedging-where-data-is-firm. Round ${round}. Emit JSON matching ` +
      `schemas/audit-v1.json $defs/expertVerdict.`,
  },
]

const writeResult = await runAuditLoop({
  phase: 'WRITE',
  executor: 'paper-writer',
  executorPrompt: (round, revisePrompt, priorTrace) =>
    round === 1
      ? `Revise/finalize the manuscript sections drafted in Stage 5a. Apply the Three-Times Rule (shared/references/audit-doctrine.md). ` +
        `Ensure every figure block has a \\caption + \\label and an in-text reference in the same section. Output the entire .tex tree state hash.`
      : `Revise the manuscript per the audit feedback below. Round ${round}.\n\n${revisePrompt}\n\n` +
        `Previous rounds (last 3) summary: ${JSON.stringify((priorTrace||[]).map(r=>({round:r.round,aggregate:r.aggregate,decision:r.decision})))}\n\n` +
        `Apply shared/references/audit-doctrine.md Three-Times Rule when rewriting any quantitative claim.`,
  panel: writePanel,
  target: 90,
  maxRounds: 10,
  context: {
    runStartedAt: (typeof args === 'object' && args?.runStartedAt) || null,
    kbRoot: 'knowledge-base/audit-rounds',
    manuscriptPath: (typeof args === 'object' && args?.manuscriptPath) || 'manuscript',
  },
})

if (writeResult.status === 'ESCALATED') {
  log(`[WRITE] ESCALATED after ${writeResult.trace.rounds.length} rounds. See knowledge-base/audit-rounds/*-WRITE-ESCALATION.json.`)
}

phase('Review')
// REVIEW panel: 5 reviewer agents, loop until aggregate >= 90 (max 10 rounds).
// Replaces the legacy single-shot review-simulator. Use `useLegacyReview: true`
// in args to opt back into the 4-persona free-text wrapper.
const reviewPanel = [
  {
    name: 'r1-methodology',
    weight: 25,
    critical_axes: ['soundness', 'novelty'],
    prompt: (execOut, retrieved, round) =>
      `You are r1-methodology (agents/reviewers/r1-methodology.md). Audit the manuscript's problem formulation, ` +
      `theoretical claims, novelty delta vs. closest prior work, and assumption realism. Round ${round}. ` +
      `Cross-verify every cited prior work via paper_fetcher.py / WebFetch. ` +
      `Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'r2-experiments',
    weight: 25,
    critical_axes: ['empirical-rigor', 'ablation-coverage'],
    prompt: (execOut, retrieved, round) =>
      `You are r2-experiments (agents/reviewers/r2-experiments.md). Audit datasets, baselines, ablation, ` +
      `seed/std reporting, and metric appropriateness. Cross-check dataset stats against ` +
      `shared/references/benchmark-registry.yaml. Reconcile training (early-stop) and reporting metrics ` +
      `(GNN-dynamic's 3-different-metric incident is the canonical failure). Round ${round}. ` +
      `Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'eic',
    weight: 20,
    critical_axes: ['scope-fit', 'presentation'],
    prompt: (execOut, retrieved, round) =>
      `You are eic (agents/reviewers/eic.md). Calibrate venue-fit (CCF tier), check page-limit, ` +
      `placeholder-free, and the high-level "would I send this to my best PhD student to review?" gut-check. ` +
      `Round ${round}. Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'reproducibility',
    weight: 15,
    critical_axes: ['code-availability', 'data-availability'],
    prompt: (execOut, retrieved, round) =>
      `You are reproducibility (agents/reviewers/reproducibility.md). Verify every code URL resolves and the ` +
      `repo's last push is within 2 years. Verify every dataset has a download URL or is in benchmark-registry.yaml. ` +
      `Verify all hyperparameters are reported as explicit numbers and a 5-seed list is given. Round ${round}. ` +
      `Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
  {
    name: 'devils-advocate',
    weight: 15,
    critical_axes: ['counterexample', 'ablation-attack'],
    prompt: (execOut, retrieved, round) =>
      `You are devils-advocate (agents/reviewers/devils-advocate.md). Default stance: the central claim is wrong. ` +
      `Construct one concrete (dataset, condition, baseline) triple where the claim should fail and the paper does ` +
      `NOT report results on. Re-do the ablation reasoning honestly. If your score lands within 5 points of the ` +
      `panel aggregate, re-examine — your role exists to dissent. Round ${round}. ` +
      `Emit JSON matching schemas/audit-v1.json $defs/expertVerdict.`,
  },
]

let reviewResult
if ((typeof args === 'object' && args?.useLegacyReview) === true) {
  // Single-shot advisory wrapper (backward-compat).
  const reviewReport = await agent(
    'Review the complete manuscript via agents/review-simulator.md (deprecated wrapper). Single-shot advisory.',
    { phase: 'Review', schema: null }
  )
  reviewResult = { status: 'LEGACY', advisory: reviewReport }
} else {
  reviewResult = await runAuditLoop({
    phase: 'REVIEW',
    executor: 'paper-writer',
    executorPrompt: (round, revisePrompt, priorTrace) =>
      round === 1
        ? `The manuscript has passed the WRITE audit panel. Perform a final pre-submission revision pass. ` +
          `Apply the Three-Times Rule (shared/references/audit-doctrine.md). Output the entire .tex tree state hash.`
        : `Revise the manuscript per the REVIEW panel feedback below. Round ${round}.\n\n${revisePrompt}\n\n` +
          `Previous rounds (last 3) summary: ${JSON.stringify((priorTrace||[]).map(r=>({round:r.round,aggregate:r.aggregate,decision:r.decision})))}\n\n` +
          `Apply shared/references/audit-doctrine.md Three-Times Rule when rewriting any quantitative claim.`,
    panel: reviewPanel,
    target: 90,
    maxRounds: 10,
    context: {
      runStartedAt: (typeof args === 'object' && args?.runStartedAt) || null,
      kbRoot: 'knowledge-base/audit-rounds',
      manuscriptPath: (typeof args === 'object' && args?.manuscriptPath) || 'manuscript',
    },
  })
  if (reviewResult.status === 'ESCALATED') {
    log(`[REVIEW] ESCALATED after ${reviewResult.trace.rounds.length} rounds. See knowledge-base/audit-rounds/*-REVIEW-ESCALATION.json.`)
  }
}

phase('Revise')
const revised = await agent(
  'Apply any remaining REVIEW-stage advisory findings. Document changes with section/page/line references. ' +
  'Use agents/paper-writer.md.',
  { phase: 'Revise', schema: null }
)

log(`Paper writing pipeline complete. WRITE audit status=${writeResult.status} aggregate=${writeResult.audit?.aggregate ?? writeResult.escalation?.last_three_rounds?.slice(-1)[0]?.aggregate}; REVIEW status=${reviewResult.status} aggregate=${reviewResult.audit?.aggregate ?? reviewResult.escalation?.last_three_rounds?.slice(-1)[0]?.aggregate ?? 'n/a'}`)
return { insightReport, manuscript, writeResult, reviewResult, revised }
