// workflows/_dispatch.js
// -----------------------------------------------------------------------------
// Runtime agent-frontmatter validator.
//
// SAFETY PROPERTY
// ---------------
// Every workflow that dispatches an agent should first call `dispatchAgent`
// (or at minimum `loadAgentDef` + `validateAgent`) on the target. This module
// enforces — at workflow-script load time, the moment before an agent is
// handed to the host's `agent()` primitive — that:
//
//   1. The agent's YAML frontmatter conforms to schemas/agent-frontmatter-v1.json.
//   2. `rigor_contract === 'three-times-verified'` is present and exact.
//      (Refuse to dispatch any agent whose frontmatter has been edited to
//       remove the contract — this is the property that keeps the Three-Times
//       Rule in force across the whole pipeline.)
//   3. Panel/weight/critical-axes invariants hold for panel members.
//
// In other words: a workflow file that imports `dispatchAgent` cannot be
// tricked into running an agent that has silently dropped the rigor contract.
// The offline migrator (`scripts/migrate_agent_frontmatter.py`) writes the
// contract; this module is the runtime check that nobody has stripped it.
//
// EXPORTS
// -------
//   loadAgentDef(name, agentsRoot?)  -> {name, frontmatter, body, path}
//   validateAgent(def)               -> {ok: true} | {ok: false, errors: [...]}
//   dispatchAgent(name, opts?, root?)-> def    (throws if invalid)
//
// NB: dispatchAgent does NOT call the host's agent() primitive — that's the
// workflow runtime's job. This module's responsibility ends at producing a
// validated definition object.
// -----------------------------------------------------------------------------

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs'
import { join, resolve, dirname, basename, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

// ---------- minimal YAML frontmatter parser (port of parse_frontmatter) ------

const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n/

function yamlScalar(v) {
  if (v === 'true') return true
  if (v === 'false') return false
  if ((v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1)
  }
  if (/^-?\d+$/.test(v)) return parseInt(v, 10)
  if (/^-?\d+\.\d+$/.test(v)) return parseFloat(v)
  return v
}

export function parseFrontmatter(text) {
  const m = FRONTMATTER_RE.exec(text)
  if (!m) return { fm: null, body: text }
  const body = m[1]
  const fm = {}
  let curList = null
  for (const raw of body.split('\n')) {
    if (raw.trim() === '') { curList = null; continue }
    const kv = /^(\w[\w-]*)\s*:\s*(.*)$/.exec(raw)
    if (kv) {
      const k = kv[1]
      const v = kv[2].trim()
      if (v === '') {
        fm[k] = []
        curList = fm[k]
      } else if (v.startsWith('[') && v.endsWith(']')) {
        const inner = v.slice(1, -1).trim()
        fm[k] = inner === ''
          ? []
          : inner.split(',').map(x => yamlScalar(x.trim().replace(/^['"]|['"]$/g, '')))
        curList = null
      } else {
        fm[k] = yamlScalar(v)
        curList = null
      }
      continue
    }
    const li = /^\s*-\s+(.*)$/.exec(raw)
    if (li && curList !== null) {
      curList.push(yamlScalar(li[1].trim()))
    }
  }
  return { fm, body: text.slice(m[0].length) }
}

// ---------- resolution -------------------------------------------------------

function findAgentFile(name, agentsRoot) {
  // Recursive search for `<name>.md` under agentsRoot. We don't use Grep/Glob
  // here because this is a tiny pure-JS module — keep zero external deps.
  if (!existsSync(agentsRoot)) {
    throw new Error(`agentsRoot does not exist: ${agentsRoot}`)
  }
  const stack = [agentsRoot]
  while (stack.length) {
    const dir = stack.pop()
    let entries
    try { entries = readdirSync(dir) } catch { continue }
    for (const e of entries) {
      const p = join(dir, e)
      let st
      try { st = statSync(p) } catch { continue }
      if (st.isDirectory()) stack.push(p)
      else if (e === `${name}.md`) return p
    }
  }
  return null
}

// ---------- public API -------------------------------------------------------

/**
 * Load and parse an agent definition by slug.
 *
 * @param {string} name         agent slug (filename without .md)
 * @param {string} [agentsRoot] absolute or relative path to the agents/ dir.
 *                              If relative, resolved against process.cwd().
 * @returns {{name:string, frontmatter:object, body:string, path:string}}
 * @throws  if the file does not exist or has no frontmatter
 */
export function loadAgentDef(name, agentsRoot = 'agents') {
  const root = resolve(agentsRoot)
  const path = findAgentFile(name, root)
  if (!path) {
    throw new Error(`loadAgentDef: agent '${name}' not found under ${root}`)
  }
  const text = readFileSync(path, 'utf8')
  const { fm, body } = parseFrontmatter(text)
  if (fm == null) {
    throw new Error(`loadAgentDef: ${path} has no YAML frontmatter`)
  }
  return { name, frontmatter: fm, body, path }
}

const NAME_RE = /^[a-z][a-z0-9-]*$/
const ALLOWED_PANELS = [
  'EXPLORE', 'DESIGN', 'VALIDATE', 'ANALYZE', 'WRITE', 'REVIEW',
  'executor', 'support',
]
const PANEL_PARTICIPANTS = ['EXPLORE','DESIGN','VALIDATE','ANALYZE','WRITE','REVIEW']
const ALLOWED_PARALLELISM = ['max-fanout', 'serial-justified']

/**
 * Validate a loaded agent definition against agent-frontmatter-v1.json.
 *
 * @param {{name:string, frontmatter:object, path:string}} def
 * @returns {{ok:true, warnings?:string[]} | {ok:false, errors:string[], warnings?:string[]}}
 */
export function validateAgent(def) {
  const errors = []
  const warnings = []
  const fm = def.frontmatter || {}

  // name
  if (typeof fm.name !== 'string' || !NAME_RE.test(fm.name)) {
    errors.push(`frontmatter.name missing or does not match /^[a-z][a-z0-9-]*$/ (got: ${JSON.stringify(fm.name)})`)
  } else {
    const slug = basename(def.path).replace(/\.md$/, '')
    if (fm.name !== slug) {
      errors.push(`frontmatter.name '${fm.name}' does not match filename slug '${slug}'`)
    }
  }

  // description
  if (typeof fm.description !== 'string' || fm.description.length < 10) {
    errors.push(`frontmatter.description must be a string of length >=10 (got length ${typeof fm.description === 'string' ? fm.description.length : 'n/a'})`)
  }

  // rigor_contract — THE safety property
  if (fm.rigor_contract !== 'three-times-verified') {
    errors.push(`frontmatter.rigor_contract must be exactly 'three-times-verified' (got: ${JSON.stringify(fm.rigor_contract)}). This agent has been stripped of the Three-Times Rule and refuses to dispatch.`)
  }

  // parallelism_contract — default with warning
  if (fm.parallelism_contract === undefined) {
    warnings.push(`frontmatter.parallelism_contract missing; defaulting to 'max-fanout'`)
    fm.parallelism_contract = 'max-fanout'
  } else if (!ALLOWED_PARALLELISM.includes(fm.parallelism_contract)) {
    errors.push(`frontmatter.parallelism_contract must be one of ${JSON.stringify(ALLOWED_PARALLELISM)} (got: ${JSON.stringify(fm.parallelism_contract)})`)
  }

  // panel
  if (fm.panel !== undefined && !ALLOWED_PANELS.includes(fm.panel)) {
    errors.push(`frontmatter.panel must be one of ${JSON.stringify(ALLOWED_PANELS)} (got: ${JSON.stringify(fm.panel)})`)
  }

  // panel-member invariants
  if (PANEL_PARTICIPANTS.includes(fm.panel)) {
    if (typeof fm.weight !== 'number' || !(fm.weight > 0)) {
      errors.push(`panel member '${fm.name}' on panel ${fm.panel} must have weight > 0 (got: ${JSON.stringify(fm.weight)})`)
    }
    if (!Array.isArray(fm.critical_axes) || fm.critical_axes.length === 0) {
      errors.push(`panel member '${fm.name}' on panel ${fm.panel} must have a non-empty critical_axes array`)
    }
  }

  if (errors.length) return { ok: false, errors, warnings }
  return { ok: true, warnings }
}

/**
 * Convenience: load + validate an agent. Throws on validation failure with
 * an aggregated error message. Returns the def for the workflow runtime to
 * pass to `agent()`. Does NOT itself dispatch — that's the host's job.
 *
 * @param {string} name
 * @param {object} [opts]       reserved for future flags; currently unused
 * @param {string} [agentsRoot]
 * @returns {{name:string, frontmatter:object, body:string, path:string, warnings?:string[]}}
 */
export function dispatchAgent(name, opts = {}, agentsRoot = 'agents') {
  const def = loadAgentDef(name, agentsRoot)
  const v = validateAgent(def)
  if (!v.ok) {
    const msg = [
      `dispatchAgent: refusing to dispatch '${name}' (${def.path}):`,
      ...v.errors.map(e => `  - ${e}`),
    ].join('\n')
    throw new Error(msg)
  }
  if (v.warnings && v.warnings.length) def.warnings = v.warnings
  return def
}

// ---------- optional CLI test path -------------------------------------------
// `node workflows/_dispatch.js [agentsRoot]` walks every agent file and
// prints a one-line summary. Best-effort detection of direct invocation.

function isMain() {
  try {
    if (typeof process === 'undefined' || !process.argv || !process.argv[1]) return false
    const here = fileURLToPath(import.meta.url)
    return resolve(process.argv[1]) === resolve(here)
  } catch { return false }
}

if (isMain()) {
  const root = resolve(process.argv[2] || 'agents')
  // walk
  const files = []
  const stack = [root]
  while (stack.length) {
    const d = stack.pop()
    let ents
    try { ents = readdirSync(d) } catch { continue }
    for (const e of ents) {
      const p = join(d, e)
      let st
      try { st = statSync(p) } catch { continue }
      if (st.isDirectory()) stack.push(p)
      else if (e.endsWith('.md')) files.push(p)
    }
  }
  files.sort()
  let nOk = 0, nFail = 0
  for (const path of files) {
    const slug = basename(path).replace(/\.md$/, '')
    try {
      const text = readFileSync(path, 'utf8')
      const { fm } = parseFrontmatter(text)
      if (fm == null) { console.log(`SKIP  ${slug}  (no frontmatter)`); continue }
      const v = validateAgent({ name: slug, frontmatter: fm, path })
      if (v.ok) {
        const w = v.warnings && v.warnings.length ? ` [warn: ${v.warnings.length}]` : ''
        console.log(`OK    ${slug}${w}`)
        nOk++
      } else {
        console.log(`FAIL  ${slug}`)
        for (const e of v.errors) console.log(`        - ${e}`)
        nFail++
      }
    } catch (err) {
      console.log(`ERR   ${slug}: ${err.message}`)
      nFail++
    }
  }
  console.log(`\n${nOk} ok, ${nFail} fail, ${files.length} total under ${root}`)
  if (nFail > 0 && typeof process !== 'undefined') process.exit(1)
}
