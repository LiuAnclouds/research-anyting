// workflows/_schema.js
//
// Schema constants, validators, and verdict normalization for the audit loop.
// Extracted from audit-loop.js so phase-specific pipelines can validate
// expert verdicts and panels without pulling in the full loop runtime.

const REQUIRED_KEYS = ['name', 'weight', 'axes', 'score']

function weightedMean(axes, weights) {
  const keys = Object.keys(axes)
  if (keys.length === 0) return 0
  let num = 0
  let den = 0
  for (const k of keys) {
    const w = weights?.[k] ?? 1
    num += w * axes[k]
    den += w
  }
  return den === 0 ? 0 : num / den
}

function validateExpertVerdict(v, idx) {
  for (const k of REQUIRED_KEYS) {
    if (v[k] === undefined) throw new Error(`expert[${idx}] missing required key '${k}'`)
  }
  if (typeof v.weight !== 'number' || v.weight < 0 || v.weight > 100)
    throw new Error(`expert[${idx}] '${v.name}' weight out of [0,100]`)
  const recompute = weightedMean(v.axes, v.axis_weights)
  if (Math.abs(recompute - v.score) > 0.5)
    throw new Error(`expert[${idx}] '${v.name}' score=${v.score} != weighted_mean(axes)=${recompute.toFixed(2)}`)
  // Evidence required for any axis >= 80 (no high score without grounding).
  // Note: the normalizer intentionally does NOT default `evidence` to [], so
  // an omitted field surfaces here as `undefined` (contract violation) rather
  // than being silently blank-filled. An explicit empty array [] is likewise
  // a violation for high-scoring axes: high scores demand external grounding.
  const hasHighAxis = Object.values(v.axes).some(s => s >= 80)
  if (hasHighAxis && (!Array.isArray(v.evidence) || v.evidence.length === 0)) {
    const reason = v.evidence === undefined
      ? 'evidence field missing from verdict (expert did not populate it)'
      : (!Array.isArray(v.evidence)
          ? `evidence must be an array; got ${typeof v.evidence}`
          : 'evidence array is empty; high scores require at least one citation')
    throw new Error(`expert[${idx}] '${v.name}' has axis >= 80 but ${reason}`)
  }
  return true
}

// Default schema for an expert verdict. Used when a panel entry doesn't
// specify its own schema. Mirrors schemas/audit-v1.json $defs/expertVerdict.
function expertSchemaInline() {
  return {
    type: 'object',
    required: ['name', 'weight', 'axes', 'score'],
    properties: {
      name: { type: 'string' },
      weight: { type: 'integer', minimum: 0, maximum: 100 },
      axes: { type: 'object', additionalProperties: { type: 'number', minimum: 0, maximum: 100 } },
      axis_weights: { type: 'object', additionalProperties: { type: 'number', minimum: 0 } },
      score: { type: 'number', minimum: 0, maximum: 100 },
      vetoes: { type: 'array' },
      evidence: { type: 'array' },
      blocking_findings: { type: 'array' },
      advisory_findings: { type: 'array' },
      critical_axes: { type: 'array', items: { type: 'string' } },
    },
  }
}

// If an expert agent returns a raw object missing the panel-level metadata
// (weight, critical_axes), splice them in from the panel definition so the
// aggregator can trust the shape.
function normalizeExpertVerdict(rawVerdict, panelEntry) {
  if (!rawVerdict || typeof rawVerdict !== 'object') return null
  const v = { ...rawVerdict }
  v.name = v.name || panelEntry.name
  v.weight = v.weight ?? panelEntry.weight
  if (!v.critical_axes && panelEntry.critical_axes) v.critical_axes = panelEntry.critical_axes
  v.vetoes = v.vetoes || []
  // NOTE: do NOT default `evidence` to []. The validator distinguishes
  // "evidence field omitted by the expert" (undefined -> contract violation
  // when any axis >= 80) from "expert emitted an explicit []" (also a
  // violation for high axes, but a clearer error message). Blank-filling
  // here would erase that signal.
  v.blocking_findings = v.blocking_findings || []
  v.advisory_findings = v.advisory_findings || []
  return v
}

// Public helper: validate a complete audit object. Checks that the panel
// weights sum to 100 and that every expert verdict passes
// validateExpertVerdict. Throws on the first violation; returns true on success.
function validateAudit(audit) {
  if (!audit || !Array.isArray(audit.experts)) {
    throw new Error('validateAudit: audit.experts must be an array')
  }
  const totalWeight = audit.experts.reduce((s, e) => s + (e?.weight ?? 0), 0)
  if (totalWeight !== 100) {
    throw new Error(`panel weights must sum to 100; got ${totalWeight}`)
  }
  for (let i = 0; i < audit.experts.length; i++) {
    validateExpertVerdict(audit.experts[i], i)
  }
  return true
}

export {
  REQUIRED_KEYS,
  weightedMean,
  validateExpertVerdict,
  expertSchemaInline,
  normalizeExpertVerdict,
  validateAudit,
}
