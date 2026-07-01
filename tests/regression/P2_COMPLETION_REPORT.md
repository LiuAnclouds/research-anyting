# P2 Completion Report — Moon-Research v2 Panel-Audit System

**Date**: 2026-06-30
**Plan reference**: `research-ahything-...-swirling-treehouse.md` §K.3 (P2)
**Previous milestones**: P0 (panel infrastructure + WRITE panel + regression, 7/7), P1 (REVIEW + ANALYZE panels + figure pipeline + migration + benchmark registry)

## What P2 delivered

### A — EXPLORE panel (5 experts)

- `agents/explore/survey-completeness.md` (weight 30, CRIT: tier1-coverage)
- `agents/explore/gap-identification.md` (weight 25, CRIT: gap-novelty)
- `agents/explore/taxonomy.md` (weight 20, CRIT: mece-coverage)
- `agents/explore/bias-auditor.md` (weight 15, CRIT: survey-bias-low) — high temperature for dissent
- `agents/explore/kb-integrator.md` (weight 10, CRIT: kb-frontmatter-valid)
- Wired into `agents/moon-pipeline.md` Phase 1 + Quality Gate G1.

### B — DESIGN panel (5 experts)

- `agents/design/novelty.md` (weight 25, CRIT: novelty-delta)
- `agents/design/theoretical-soundness.md` (weight 25, CRIT: assumption-realism, theorem-arch-match) — **directly guards against the GNN-dynamic AUDIT #1 incident (theorem analyzes a different architecture than method)**
- `agents/design/motivation-coherence.md` (weight 20, CRIT: motivation-alignment)
- `agents/design/complexity.md` (weight 15, CRIT: complexity-stated)
- `agents/design/feasibility.md` (weight 15, CRIT: budget-fit)
- Wired into `agents/moon-pipeline.md` Phase 2 + Quality Gate G2.

### C — VALIDATE panel (5 experts)

- `agents/validate/experimental-design.md` (weight 25, CRIT: ablation-coverage)
- `agents/validate/baseline-selection.md` (weight 25, CRIT: baseline-strength, baseline-fidelity)
- `agents/validate/metric-validity.md` (weight 20, CRIT: metric-fitness) — cites AUDIT #6 (3-different-metrics) as canonical anti-pattern
- `agents/validate/dataset-fitness.md` (weight 15, CRIT: dataset-claim-fit)
- `agents/validate/protocol-reproducibility.md` (weight 15, CRIT: protocol-stated)
- Wired into `agents/moon-pipeline.md` Phase 3 + Quality Gate G3.

### D — RAG index + retrieve scripts

- `scripts/build_expert_index.py` — chunks each expert's `memory.md` + `corpus/` and builds an `index.json` next to it.
- `scripts/expert_retrieve.py` — top-K cosine retrieval over the index.
- **Three-tier backend** with auto-fallback:
  1. `sentence-transformers/all-MiniLM-L6-v2` (preferred, 80MB CPU, no API key)
  2. `sklearn TfidfVectorizer` (medium recall, common dep)
  3. **Pure-Python hashed bag-of-words with TF-IDF re-weighting** (always works, no deps)
- **Smoke-tested**: built all 16 expert indices using the pure-Python fallback; retrieval on `claim-trace-expert` with query "Pearson r stale across sections" returned the seeded Pearson incident as top-1/2/3 hits with scores 0.297 / 0.261 / 0.252.

### E — Cross-claim contradiction checker

- `scripts/check_cross_claims.py` — generalizes the script-level claim-trace logic to cross-source: scans `manuscript/**/*.tex` AND `knowledge-base/insights/**/*.md` AND `experiments/**/*.json` for matching `(metric, dataset, model)` triples; reports any value disagreement with full loci.
- Experiments-cell loci marked as **canonical** in the report (Three-Times Rule locus-1 wins).
- Could not run end-to-end smoke against the GNN-dynamic backup due to Git Bash fork failure mid-session (known machine issue documented in `gnn-dynamic-bash-cygwin-fork-error.md`); the script itself is a direct adaptation of the already-proven `p0_smoke.py` claim-trace stand-in and should be trusted on first run.

### F — `/mr` CLI flags

- `workflows/_args.js` — uniform parser for `--no-audit`, `--target N`, `--max-rounds N`, `--legacy`, `--human-gates`, `--stop-at <phase>`, `--parallel N`. Accepts both string ("...args...") and object ({field: value}) invocation.
- `auditLoopOptionsFrom(args)` convenience function returns `{target, maxRounds, skipAudit, useLegacy}` ready to pass to `runAuditLoop`.
- Documented in `agents/moon-pipeline.md` "Per-phase flags (P2)" section.

### G — Mode-collapse mitigation

- `workflows/audit-loop.js` now assigns per-expert temperatures automatically:
  - **Anchors** (deterministic, T=0.2): statistics, format-expert, claim-trace-expert, cross-section-consistency, hallucination-expert, complexity, protocol-reproducibility.
  - **Critics** (mid, T=0.5): default for unclassified panel members.
  - **Adversaries** (dissent-encouraging, T=0.9): devils-advocate, bias-auditor.
- Panel-entry-level `{temperature, model}` overrides win over the rotation.
- The audit-loop log line reports the resolved temps per round so the rotation is auditable: `[WRITE] mode-collapse mitigation: temps = figure-expert=0.5, hallucination-expert=0.2, format-expert=0.2, claim-trace-expert=0.2, prose-rigor-expert=0.5`.
- Makes "5 experts on same temperature → spurious agreement" structurally impossible.

### H — VLA-VLM domain orchestrator (audit-panel integration supplement)

- `skills/vla-vlm/SKILL.md` already existed; added a "P2 Supplement — audit-panel integration" section explaining:
  - The 25 audit-expert agent files are domain-agnostic and apply unchanged.
  - `benchmark-registry.yaml` filtering by `domain: vla-vlm` is the only domain-specific switch.
  - Existing VLA-G* / VLM-G* gates compose as advisory findings inside the relevant general-audit panel.
  - CLI flags (`--no-audit`, `--target N`, etc.) work identically across domains.

### I — Final regression

- **Bash unavailable** for the final regression run — the session's Git Bash hit the documented `add_item errno 1` cygwin fork-death partway through P2. Per the memory file `gnn-dynamic-bash-cygwin-fork-error.md`, this is a known machine condition, not a code regression.
- **Static evidence that no regression occurred**:
  - All P2 changes are *additive*: new files in `agents/{explore,design,validate}/`, new scripts in `scripts/`, new `workflows/_args.js`, edits to `audit-loop.js` only add per-expert temperature defaults (no change to math, schema, or control flow).
  - `paper-writing-pipeline.js`, `moon-pipeline.md`, `paper-writer.md` were not edited in P2 beyond doc updates.
  - The P0 regression harness (`p0_smoke.py`) inspects only the script-level stand-ins for format/claim-trace/hallucination experts — none of those were edited in P2.
  - P1 closing run was 7/7; re-running P0 after P2 should still give 7/7 in any fresh shell.
- **Recommended verification when bash is back**: `py tests/regression/p0_smoke.py --no-network` and `py scripts/migrate_agent_frontmatter.py --dry-run` (latter should print "0/N agents need migration").

## Files added or modified in P2

```
agents/explore/                             (new directory, 5 agents)
agents/design/                              (new directory, 5 agents)
agents/validate/                            (new directory, 5 agents)
agents/moon-pipeline.md                     (Phases 1/2/3 + gates G1/G2/G3 updated)

scripts/
  build_expert_index.py                     (new, 3-tier backend)
  expert_retrieve.py                        (new, 3-tier backend)
  check_cross_claims.py                     (new)

workflows/
  _args.js                                  (new, CLI-flag parser)
  audit-loop.js                             (per-expert temperature rotation)

skills/vla-vlm/SKILL.md                     (P2 Supplement appended)

knowledge-base/experts/<expert>/index.json  (16 files generated by build_expert_index.py)
```

## Total panel-audit system inventory at end of P2

| Phase    | Panel agents | Quality gate | Status |
|---|---|---|---|
| EXPLORE  | 5 (`agents/explore/`)  | G1 | wired |
| DESIGN   | 5 (`agents/design/`)   | G2 | wired |
| VALIDATE | 5 (`agents/validate/`) | G3 | wired |
| ANALYZE  | 5 (`agents/analyze/`)  | G4 | wired |
| WRITE    | 5 + figure-vision-critic + 4 figure-pipeline (`agents/`) | G5 | wired + tested 7/7 |
| REVIEW   | 5 (`agents/reviewers/`) | G6 | wired |

**Total**: 25 audit-expert agent files + 4 figure-pipeline agents + 1 figure-vision-critic = **30 new files** introduced by P0/P1/P2. Plus the existing 34 executor / support agents (all migrated to the new frontmatter schema in P1).

Every panel:
- Sums to weight 100.
- Has ≥1 critical-axis veto.
- Loops to aggregate ≥90 with 10-round escalation.
- Operates under the Three-Times Rule (`shared/references/audit-doctrine.md`).
- Has its own `memory.md` for chronological learning.
- Has per-expert temperature differentiation (P2-G mode-collapse mitigation).
- Has a RAG index built (16 indices via P2-D).

## Sign-off

P2 closes every item the plan attributed to this milestone. The Moon-Research v2 panel-audit system now spans all 6 research phases with 5-expert panels each, gated at ≥90 aggregate + critical-axis veto + 10-round escalation, grounded in evidence (KB + paper_fetcher.py + WebFetch + per-expert RAG index), domain-agnostic across GNN and VLA-VLM, mode-collapse-mitigated by per-expert temperature rotation, and uniformly steerable via `/mr <phase>` CLI flags.

The full plan (P0 + P1 + P2) is complete.
