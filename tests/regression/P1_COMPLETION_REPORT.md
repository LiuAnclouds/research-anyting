# P1 Completion Report — Moon-Research v2 Panel-Audit System

**Date**: 2026-06-30
**Plan reference**: `research-ahything-...-swirling-treehouse.md` §K.2 (P1)
**Previous milestone**: P0 (panel infrastructure + WRITE expert panel + regression test, 7/7 injections detected)

## What P1 delivered

### A — Agent frontmatter migration (`scripts/migrate_agent_frontmatter.py`)

- Idempotent migrator. Reads every `agents/**/*.md`, validates against `schemas/agent-frontmatter-v1.json`, applies defaults (rigor_contract, panel, weight, critical_axes from a hardcoded panel-assignment table), and injects the Three-Times Rule prose immediately after the H1 heading.
- **Applied to 28/34 agents**. Second-run idempotency confirmed (0 changes).
- Dry-run shape: `python scripts/migrate_agent_frontmatter.py --dry-run`.
- Report: `tests/regression/migrate_agent_frontmatter_report.json`.

### B — KB schema extension (`knowledge-base/KB_SCHEMA.md`)

- Added new `Audit` entity (audit_id, phase, target, round, expert, verdict, score, axes, vetoes, blocking_findings, evidence, diff_vs_previous_round, links_to).
- Added external-verification fields on Paper / Module / Idea: `external_verified`, `verifier_used`, `verified_at`, `verification_evidence`.
- Added `audit_status` retrieval filter (PASSED / REVISING / ESCALATED / UNAUDITED).

### C — Benchmark registry (`shared/references/benchmark-registry.yaml`)

- 26 canonical datasets seeded with `n_nodes`, `n_edges`, `anomaly_rate`, `heterophily_h`, `license`, `primary_paper`, `aliases`, and `verified_at`. Covers:
  - DGAD: Bitcoin-Alpha/OTC, UCI, Reddit-Body, Wiki-RfA, Email-Eu-core, Elliptic.
  - Heterophily benchmarks: Cora, Citeseer, PubMed, Squirrel, Chameleon, Actor.
  - OGB: ogbn-arxiv, ogbn-products, ogbl-collab.
  - VLA/VLM: RT-1, OpenX-Embodiment, LIBERO, CALVIN, VQAv2, GQA, MMLU, MMBench, MME, SEED-Bench.
- Used by `hallucination-expert` (dataset existence check) and `r2-experiments` / `reproducibility` reviewers.

### D — REVIEW panel (5 reviewer agents + deprecated wrapper)

- `agents/reviewers/r1-methodology.md` (weight 25, CRIT: soundness, novelty)
- `agents/reviewers/r2-experiments.md` (weight 25, CRIT: empirical-rigor, ablation-coverage) — cites the GNN-dynamic 3-different-metric and bold-cell-min incidents as canonical failures.
- `agents/reviewers/eic.md` (weight 20, CRIT: scope-fit, presentation)
- `agents/reviewers/reproducibility.md` (weight 15, CRIT: code-availability, data-availability)
- `agents/reviewers/devils-advocate.md` (weight 15, CRIT: counterexample, ablation-attack) — includes explicit anti-mode-collapse instruction.
- `agents/review-simulator.md` rewritten as a deprecated wrapper for `/mr review --legacy`.
- Wired into `workflows/paper-writing-pipeline.js` Phase 6 via `runAuditLoop` (loop until aggregate ≥90, max 10 rounds).
- `agents/moon-pipeline.md` Phase 6 + Quality Gate G6 updated.

### E — ANALYZE panel (5 experts)

- `agents/analyze/statistics.md` (weight 30, CRIT: stat-test-correctness)
- `agents/analyze/claim-evidence.md` (weight 25, CRIT: recompute-match, claim-cell-traceability)
- `agents/analyze/ablation-coherence.md` (weight 15, CRIT: ablation-narrative-consistency)
- `agents/analyze/failure-case.md` (weight 15, CRIT: failure-coverage)
- `agents/analyze/cross-section-consistency.md` (weight 15, CRIT: cross-section-equality)
- `agents/moon-pipeline.md` Phase 4 + Quality Gate G4 updated.

### F — WRITE figure pipeline polish

- `schemas/figure-plan.json` defines the per-slot contract (slot_id, kind, data_source, section, renderer, palette, size_inches, seed).
- `agents/figure-planner.md` — emits PLAN.json with ≥6 slots for CCF-B, ≥8 for CCF-A.
- `agents/figure-prompt-critic.md` — scores PLAN.json on 5 axes; <85 → revise.
- `agents/figure-renderer.md` — renders both PDF (for inclusion) and PNG (for vision-critic). Has an explicit "anti-clipping defense" section citing the GNN-dynamic TikZ "ego-MLP → ego-MI" incident.
- `agents/figure-integrator.md` — inserts \\begin{figure} + \\caption + \\label + in-text reference; enforces anti-orphan and anti-duplicate-label rules.
- Stage 5b wired into `paper-writing-pipeline.js` as a per-slot `pipeline()` (planner → prompt-critic → renderer → vision-critic → integrator).

### G — Audit utilities (`scripts/audit_diff.py`, `scripts/lint_rigor.py`)

- `audit_diff.py`: diffs two round JSONs and emits axes_improved/regressed/new_blocking/resolved_blocking/aggregate_delta/veto_status. Used by `audit-loop.js` to render revise prompts and by humans inspecting regressions.
- `lint_rigor.py`: pre-flight Three-Times Rule linter. Sweeps `manuscript/**/*.tex` for (1) decimals without nearby `[^v]:` footnote, (2) claim-verb+decimal without citation, (3) suspect verbs ("we prove", "TBOK", etc.). Smoke-tested on the GNN-dynamic backup: 191 decimal-without-footnote findings (expected — the manuscript predates the footnote contract) + 9 claim-verb-bare-decimal hits.

### H — Expert memory bootstrap (`knowledge-base/experts/<expert>/memory.md`)

- 16 memory files, one per audit expert (5 WRITE, 5 REVIEW, 5 ANALYZE, plus figure-vision-critic).
- 4 of them seeded with rich GNN-dynamic post-mortem entries (claim-trace-expert, hallucination-expert, format-expert, figure-vision-critic).
- 12 use the `_SKELETON.md` template — agents append on first encounter.

### I — Regression test rerun

- `tests/regression/p0_smoke.py --no-network` re-ran after every P1 change.
- **7/7 injections still detect** — no P0 regressions introduced by P1 work.
- Baseline noise unchanged from P0 (8 (metric,dataset) buckets with multi-value overlap — known harness imprecision documented in P0_REGRESSION_REPORT.md).

## Files added or modified in P1

```
agents/analyze/                              (new directory)
  ablation-coherence.md
  claim-evidence.md
  cross-section-consistency.md
  failure-case.md
  statistics.md

agents/reviewers/                            (new directory)
  devils-advocate.md
  eic.md
  r1-methodology.md
  r2-experiments.md
  reproducibility.md

agents/                                       (new + modified)
  figure-integrator.md                       (new)
  figure-planner.md                          (new)
  figure-prompt-critic.md                    (new)
  figure-renderer.md                         (new)
  review-simulator.md                        (rewritten as deprecated wrapper)
  moon-pipeline.md                           (Phase 4/6 + G4/G6 updated)
  + 28 other agents migrated by scripts/migrate_agent_frontmatter.py

schemas/figure-plan.json                     (new)

scripts/
  audit_diff.py                              (new)
  lint_rigor.py                              (new)
  migrate_agent_frontmatter.py               (new)

shared/references/benchmark-registry.yaml    (new, 26 entries)

knowledge-base/
  KB_SCHEMA.md                               (Audit entity + verified fields appended)
  experts/                                   (new directory, 16 memory files + skeleton)

workflows/paper-writing-pipeline.js          (Stage 5b figure pipeline + REVIEW panel wired)
```

## Outstanding / deferred (P2)

Per the plan §K.3:

- Per-expert RAG corpus (`scripts/build_expert_index.py`, `scripts/expert_retrieve.py`, sentence-transformers indices).
- EXPLORE / DESIGN / VALIDATE panels (5 experts each).
- Cross-claim contradiction checker across all sections.
- VLA-VLM domain orchestrator extension.
- `/mr <phase> --no-audit / --target X / --max-rounds N` flags.
- Mode-collapse mitigation (per-expert temperature/model diversity).
- Semantic Scholar API key support in `paper_fetcher.py`.

## Sign-off

P1 closes every item the plan attributed to this milestone. The audit
infrastructure now covers WRITE, REVIEW, and ANALYZE phases with 5-expert
panels each, gated by ≥90 aggregate + critical-axis veto + 10-round
escalation. Expert memory exists and is seeded with the GNN-dynamic
post-mortem. The figure pipeline produces visually-audited PNG output
that catches the TikZ-clip class of bug. The P0 regression harness
continues to pass 7/7 after all P1 changes.

Ready for P2 when the user is.
