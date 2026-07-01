// workflows/_budget.js
//
// Token + USD cost estimator for audit-loop rounds.
//
// Used by audit-loop.js (round-level estimate before dispatch) and by
// scripts/audit_budget_report.py (post-hoc per-phase rollup). The rate
// table below is duplicated in audit_budget_report.py; if you change one,
// change the other. See "KEEP IN SYNC" comment in that file.
//
// Public API:
//   MODEL_RATES                          -- per-million-token USD prices
//   estimateRoundCost({panel, ...})      -- token + USD breakdown for one round
//   formatBudgetLine(estimate)           -- one-line human summary
//
// All rates are 2026-era Anthropic public list prices (USD per 1M tokens).
// "inherit" is the harness placeholder that resolves to the parent agent's
// model at dispatch time; we cost it as Sonnet (the most common parent).

export const MODEL_RATES = Object.freeze({
  'claude-sonnet-4-6':  { input: 3.00,  output: 15.00 },
  'claude-haiku-4-5':   { input: 1.00,  output:  5.00 },
  'claude-opus-4-8':    { input: 15.00, output: 75.00 },
  'claude-fable-5':     { input: 2.00,  output: 10.00 },
  // "inherit" = run on whatever the dispatching agent uses. We estimate
  // as Sonnet because that is the default for /mr phase executors.
  'inherit':            { input: 3.00,  output: 15.00 },
})

const DEFAULT_MODEL = 'claude-sonnet-4-6'

function rateFor(model) {
  if (!model) return MODEL_RATES[DEFAULT_MODEL]
  return MODEL_RATES[model] || MODEL_RATES[DEFAULT_MODEL]
}

function tokensToUSD(inTok, outTok, model) {
  const r = rateFor(model)
  return (inTok / 1e6) * r.input + (outTok / 1e6) * r.output
}

/**
 * Estimate the token + USD cost of a single audit-loop round.
 *
 * @param {object}   opts
 * @param {Array}    opts.panel             panel definitions from audit-loop.js
 *                                          (each: {name, weight, model?, ...})
 * @param {object}   [opts.executorTokens]  {input, output} for executor; defaults
 *                                          12k in / 4k out (a typical write-round).
 * @param {object}   [opts.expertAvgTokens] {input, output} per-expert; defaults
 *                                          8k in / 2k out. Experts see the
 *                                          executor output + a prompt, hence
 *                                          larger input than output.
 * @param {string}   [opts.executorModel]   executor model id; defaults sonnet.
 *
 * @returns {{tokens_total: number, cost_usd: number, breakdown: object}}
 */
export function estimateRoundCost({
  panel,
  executorTokens = { input: 12000, output: 4000 },
  expertAvgTokens = { input:  8000, output: 2000 },
  executorModel = DEFAULT_MODEL,
} = {}) {
  if (!Array.isArray(panel)) {
    throw new Error('estimateRoundCost: panel must be an array')
  }

  const exec_in  = executorTokens.input  | 0
  const exec_out = executorTokens.output | 0
  const exec_cost = tokensToUSD(exec_in, exec_out, executorModel)

  const experts = []
  let expertsInTotal  = 0
  let expertsOutTotal = 0
  let expertsCost     = 0
  for (const p of panel) {
    const m = p.model || 'inherit'
    const in_  = expertAvgTokens.input  | 0
    const out_ = expertAvgTokens.output | 0
    const c    = tokensToUSD(in_, out_, m)
    experts.push({
      name: p.name,
      model: m,
      tokens_in: in_,
      tokens_out: out_,
      cost_usd: round4(c),
    })
    expertsInTotal  += in_
    expertsOutTotal += out_
    expertsCost     += c
  }

  const tokens_total = exec_in + exec_out + expertsInTotal + expertsOutTotal
  const cost_usd     = exec_cost + expertsCost

  return {
    tokens_total,
    cost_usd: round4(cost_usd),
    breakdown: {
      executor: {
        model: executorModel,
        tokens_in:  exec_in,
        tokens_out: exec_out,
        cost_usd:   round4(exec_cost),
      },
      experts,
      experts_subtotal: {
        tokens_in:  expertsInTotal,
        tokens_out: expertsOutTotal,
        cost_usd:   round4(expertsCost),
      },
    },
  }
}

/**
 * One-line human summary, e.g.
 *   "WRITE round: ~52k tokens, ~$0.42"
 *
 * @param {object} estimate         result of estimateRoundCost
 * @param {string} [phaseLabel]     optional phase label prefix; defaults "Round"
 */
export function formatBudgetLine(estimate, phaseLabel = 'Round') {
  if (!estimate || typeof estimate !== 'object') return `${phaseLabel}: (no estimate)`
  const ktok = (estimate.tokens_total / 1000).toFixed(0)
  const usd  = estimate.cost_usd.toFixed(2)
  return `${phaseLabel}: ~${ktok}k tokens, ~$${usd}`
}

function round4(n) {
  return Math.round(n * 10000) / 10000
}
