// workflows/_args.js
// Centralized argument parser for /mr <phase> flags. Used by every
// phase-pipeline so the same flag set works everywhere.
//
// Supported flags:
//   --no-audit             skip the audit panel for this phase (legacy/single-shot mode)
//   --target N             override the audit panel pass threshold (default 90)
//   --max-rounds N         override the audit-loop round cap (default 10)
//   --legacy               use the deprecated single-agent wrapper (per phase)
//   --human-gates          ask the user at every gate transition
//   --stop-at <phase>      stop the pipeline at the named phase
//   --parallel N           max concurrent agents within a phase
//
// args is the `args` object passed to the workflow. Each phase script
// imports this and reads the resolved options. If args is a string
// (legacy invocation), it's parsed as a CLI-style flag list.

export function parseArgs(args) {
  const out = {
    noAudit: false,
    target: 90,
    maxRounds: 10,
    legacy: false,
    humanGates: false,
    stopAt: null,
    parallel: null,
    raw: args,
  }

  if (args == null) return out

  // String mode: parse CLI-style tokens.
  if (typeof args === 'string') {
    const tokens = args.trim().split(/\s+/)
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i]
      const next = () => tokens[++i]
      switch (t) {
        case '--no-audit':    out.noAudit = true; break
        case '--legacy':      out.legacy = true; break
        case '--human-gates': out.humanGates = true; break
        case '--target':      out.target = parseInt(next(), 10); break
        case '--max-rounds':  out.maxRounds = parseInt(next(), 10); break
        case '--stop-at':     out.stopAt = next(); break
        case '--parallel':    out.parallel = parseInt(next(), 10); break
      }
    }
    return _clamp(out)
  }

  // Object mode: take fields verbatim.
  if (typeof args === 'object') {
    if (args.noAudit === true || args['no-audit'] === true) out.noAudit = true
    if (typeof args.target === 'number')         out.target = args.target
    if (typeof args.maxRounds === 'number')      out.maxRounds = args.maxRounds
    if (typeof args['max-rounds'] === 'number')  out.maxRounds = args['max-rounds']
    if (args.legacy === true)                    out.legacy = true
    if (args.useLegacy === true)                 out.legacy = true
    if (args.useLegacyReview === true)           out.legacy = true
    if (args.humanGates === true)                out.humanGates = true
    if (typeof args.stopAt === 'string')         out.stopAt = args.stopAt
    if (typeof args['stop-at'] === 'string')     out.stopAt = args['stop-at']
    if (typeof args.parallel === 'number')       out.parallel = args.parallel
  }
  return _clamp(out)
}

function _clamp(o) {
  if (!Number.isFinite(o.target))     o.target = 90
  if (!Number.isFinite(o.maxRounds))  o.maxRounds = 10
  o.target    = Math.max(50, Math.min(100, o.target))
  o.maxRounds = Math.max(1,  Math.min(20,  o.maxRounds))
  return o
}

// Convenience: derive the audit-loop options object from parsed flags.
export function auditLoopOptionsFrom(args) {
  const a = parseArgs(args)
  return {
    target:     a.target,
    maxRounds:  a.maxRounds,
    skipAudit:  a.noAudit,
    useLegacy:  a.legacy,
  }
}
