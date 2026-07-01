// workflows/_prompts.js
//
// Prompt rendering helpers for the audit loop. Extracted from audit-loop.js
// so phase-specific pipelines can share the boilerplate that turns an audit
// verdict into a revise prompt, and that builds the executor prompt for
// round N.

function renderRevisePrompt(audit) {
  const lines = []
  lines.push('## Audit feedback (must address before next round)')
  lines.push(`Round ${audit.round}; aggregate=${audit.aggregate}; decision=${audit.decision}.`)
  if (audit.vetoes_global.length) {
    lines.push('\n### Vetoes (critical-axis failures)')
    for (const v of audit.vetoes_global) {
      lines.push(`- [${v.expert}] axis '${v.axis}' = ${v.score_at_veto} (< ${v.threshold}). ${v.reason}`)
    }
  }
  if (audit.blocking_findings.length) {
    lines.push('\n### Blocking findings')
    for (const f of audit.blocking_findings) {
      lines.push(`- axis=${f.axis}: ${f.msg}` + (f.fix_hint ? `  -> fix: ${f.fix_hint}` : ''))
    }
  }
  if (audit.advisory_findings.length) {
    lines.push('\n### Advisory (consider fixing)')
    for (const f of audit.advisory_findings) {
      lines.push(`- axis=${f.axis}: ${f.msg}`)
    }
  }
  lines.push('\nApply the Three-Times Rule (see shared/references/audit-doctrine.md) when revising any quantitative claim.')
  return lines.join('\n')
}

// Public helper: build a default executor prompt for round N. On round 1 the
// executor is told to execute fresh; on later rounds the prior revisePrompt
// (rendered from the previous audit) is appended and the executor is asked
// to revise per audit feedback. priorTrace is included for context.
function renderExecutorPrompt({ phase, round, revisePrompt, priorTrace }) {
  const lines = []
  lines.push(`# ${phase} - round ${round}`)
  if (round === 1) {
    lines.push('')
    lines.push('Execute this phase fresh. No prior audit feedback applies.')
  } else {
    lines.push('')
    lines.push('Revise per audit feedback below; address every veto and blocking finding before resubmitting.')
    if (revisePrompt) {
      lines.push('')
      lines.push(revisePrompt)
    }
    if (Array.isArray(priorTrace) && priorTrace.length) {
      lines.push('')
      lines.push(`(Prior rounds in trace: ${priorTrace.length}; review the most recent audit verdict above.)`)
    }
  }
  return lines.join('\n')
}

export { renderRevisePrompt, renderExecutorPrompt }
