# /mr — Moon-Research Command Reference

Canonical single-source-of-truth for every `/mr` command. All commands use the `/mr` prefix to avoid collision with other Claude Code plugins.

Structure: **A.** per-domain research verbs · **B.** knowledge base · **C.** system · **D.** domain extensibility · **E.** deprecated.

---

## A. Research per-domain commands

The 10 canonical verbs. Every domain (`gnn`, `vla-vlm`, `vla`, `vlm`, and any domain created via `/mr new-domain`) receives them by default. Listed in canonical pipeline order.

| Command | Backing agent | Purpose |
|---|---|---|
| `/mr <domain> idea "<topic>"` | `agents/<domain>-idea-broker.md` | Generate 3-5 candidate directions with falsifiable hypotheses |
| `/mr <domain> survey "<topic>"` | `agents/literature-survey.md` | Systematic multi-source literature review |
| `/mr <domain> read <paper>` | `agents/paper-reader.md` | Three-pass deep read of a specific paper |
| `/mr <domain> theory` | `agents/theory-crafter.md` | Formalize + prove + complexity analysis |
| `/mr <domain> prototype` | `agents/<domain>-rapid-prototype.md` | Minimum viable experiment |
| `/mr <domain> experiment` | `agents/experiment-engineer.md` | Full experiment matrix, 5 seeds |
| `/mr <domain> analyze` | `agents/<domain>-insight-analyzer.md` | Extract insights + narrative from results (ANALYZE panel) |
| `/mr <domain> write` | `agents/paper-writer.md` via `workflows/paper-writing-pipeline.js` | Manuscript writing (WRITE panel, loop-until-90) |
| `/mr <domain> review` | `agents/reviewers/*.md` via audit-loop | 5-reviewer panel (REVIEW panel, loop-until-90) |
| `/mr <domain> full "<hypothesis>"` | `workflows/<domain>-full-pipeline.js` | Full 6-phase pipeline with all quality gates |

### Suffix flags

Applicable to any per-domain verb. Default execution is parallel per the parallelism-doctrine; serial fallback requires explicit justification.

| Flag | Effect |
|---|---|
| `--target N` | Override the ≥90 aggregate threshold |
| `--max-rounds N` | Override the 10-round audit-loop cap |
| `--no-audit` | Skip the panel audit for this phase (executor only) |
| `--legacy` | Use the pre-panel single-agent path |

---

## B. Knowledge base commands

Cross-domain, all backed by `agents/kb-manager.md` unless noted.

| Command | Purpose |
|---|---|
| `/mr ideas [--domain X] [--status Y]` | List ideas |
| `/mr paper <slug>` | Show paper entry |
| `/mr module <slug>` | Show module entry |
| `/mr venue <slug>` | Show venue entry |
| `/mr papers [--domain X] [--tier Y] [--code]` | List papers with filters |
| `/mr modules [--domain X] [--category Y]` | List modules |
| `/mr venues [--tier X] [--domain Y]` | List venues |
| `/mr search "<query>"` | Cross-KB fuzzy search |
| `/mr decompose <paper>` | Extract modules from a paper |
| `/mr combinations` | Recompute idea hypergraph |
| `/mr recommend-venue <idea>` | Rank venues for an idea |
| `/mr store <session\|paper\|module>` | Persist to KB |
| `/mr recall "<query>"` | Retrieve KB context |
| `/mr kb-check` | KB integrity + `audit_status` scan (P3) |
| `/mr fuse` | Consolidate related KB entries |
| `/mr export idea\|bib\|module <target>` | Export a KB entry |

---

## C. System commands

Meta-level; not tied to any domain.

| Command | Backing | Purpose |
|---|---|---|
| `/mr new-domain <name> "<desc>"` | `agents/domain-init.md` | Bootstrap a new research domain (P5) |
| `/mr health [<domain>\|--all]` | `scripts/mr_health.py` | 0-100 completeness score across 8 rubric checks (P5) |
| `/mr cost [--budget USD]` | `scripts/mr_cost.py` | Cost report across audit rounds (P4) |
| `/mr dag` | `scripts/mr_dag.py` | ASCII visualization of the 6-phase pipeline (P4) |
| `/mr resume` | `scripts/mr_resume.py` | Recover from `_state.json` + last audit round (P4) |
| `/mr status [--domain X]` | `agents/kb-manager.md` | Overall pipeline status |
| `/mr init [<project-name>]` | `agents/project-init.md` | Initialize a new project |
| `/mr config <key> <value>` | shell config write | Set config (`kb.root`, `kb.auto_store`, `projects.root`, ...) |
| `/mr log` | `agents/research-log.md` | Daily research log |
| `/mr discuss "<question>"` | `agents/deep-discussion.md` | Open-ended discussion |
| `/mr rebuttal <reviews>` | `agents/rebuttal-writer.md` | Response to peer review |
| `/mr present` | `agents/presentation-builder.md` | Build presentation slides |
| `/mr alert` | `agents/literature-alert.md` | Subscribe to arXiv new-paper alerts |
| `/mr help` | inline | List all commands |

---

## D. Domain extensibility

A new domain may add verbs beyond the 10 canonical ones.

Rule:

1. Add a row to `<domain>/SKILL.md` routing table: `/mr <domain> <verb>` → `agents/<domain>-<verb>.md`.
2. Create `agents/<domain>-<verb>.md` with proper frontmatter (`rigor_contract` + `parallelism_contract`).
3. The verb becomes routable through `/mr` transparently; no core changes required.

Example: `/mr vla-vlm sim2real "task"` dispatches `agents/vla-vlm-sim2real.md`.

---

## E. Deprecated / removed commands

Kept here for backward-compat awareness only. Do not use.

| Old | Replacement |
|---|---|
| `/mr auto ...` | `/mr <domain> full` |
| `/mr code-gen`, `/mr preprocess`, `/mr hyperopt`, `/mr monitor`, `/mr debug` | never implemented, removed |
| `/mr <domain> explore` | use `idea` + `survey` |
| `/mr <domain> verify` | merged into `review` |
| `/idea`, `/paper`, `/venue`, `/module` (unprefixed) | always use `/mr <cmd>` |
| `/mr auto-store on\|off` | `/mr config kb.auto_store on\|off` |
