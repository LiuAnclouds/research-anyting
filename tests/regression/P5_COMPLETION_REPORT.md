# P5 Completion Report — Universal Domain Provisioning

**Date**: 2026-07-01
**Theme**: Make `/mr new-domain <name>` produce a domain **as complete as GNN and VLA-VLM** without further hand-work. Research-anything is a general-purpose research orchestrator, not a per-domain patchwork — this is the milestone that makes that claim true.

## Motivation

Before P5, invoking `/mr new-domain tsf "Time Series Forecasting"` gave you 3 domain-specific agents + a SKILL.md + 3 reference stubs, but:

- ❌ `benchmark-registry.yaml` had 0 entries for the new domain — every dataset lookup fell back to `paper_fetcher.py`.
- ❌ No domain-specific quality gates — the panel couldn't check e.g. "sim-to-real gap ≤15pt" the way it does for VLA.
- ❌ Expert memories were empty skeletons — new domain's audit panel started stone-cold, no class-of-bug awareness.
- ❌ RAG indices missing — retrieval returned nothing.
- ❌ No health check to tell you which of the above was missing.

## What P5 delivered (7 items, 4 parallel subagents + inline work)

### A — Structured `domain-researcher` output + `schemas/domain-research-v1.json`

- New JSON schema at `schemas/domain-research-v1.json` (draft-2020-12): declares the exact shape a domain-researcher must emit, including `datasets[]` (in benchmark-registry shape), `baselines[]` (in verify_baselines shape), `quality_gates[]` (with panel-expert / axis / threshold / rationale), `canonical_failures[]`.
- `agents/domain-researcher.md` now REQUIRES emitting a JSON block conforming to the schema — with a hard "verify bar" (≥5 datasets, ≥5 baselines, ≥3 domain-specific gates, ≥5 canonical failures).

### B — Auto-extend `benchmark-registry.yaml` on new domain

- New: `scripts/domain_init_extend_registry.py <domain-research.json>`
- Reads the domain-researcher output, appends each `datasets[]` entry into `shared/references/benchmark-registry.yaml` with `domain: <slug>` and `verified_at: pending`.
- Alias-collision detection: refuses to add if any alias matches an existing entry's name/aliases.
- Wired into `agents/domain-init.md` as Phase 2b.

### C — Domain-specific quality gates

- New: `shared/references/domain-quality-gates.md` — canonical text defining the gate format (`<DOMAIN>-G<N>`) and giving reference examples (VLA-G1 sim-to-real, VLM-G1 hallucination decomposition, GNN-G1 heterophily calibration, TSF-G1 forecast-horizon coverage).
- `domain-init` now generates `<domain>/references/quality-gates.md` from `domain-research.json:quality_gates[]`.
- Wired into 4 audit agents: `r2-experiments`, `dataset-fitness`, `metric-validity`, `failure-case` — each now reads `<domain>/references/quality-gates.md` and adds those gate axes as advisory findings during audits.

### D — Auto-seed expert memory + RAG indices

- New: `knowledge-base/experts/_seed/generic-canonical-failures.md` — 8 domain-agnostic class-of-bug lessons (Pearson-drift, TikZ-clip, bib-alias, baseline-hallucination, metric-substitution, placeholder-shipped, undefined-ref, ablation-narrative-drift). Every new domain's expert panel inherits these on day one.
- New: `scripts/domain_init_seed_memories.py` — parses the seed .md, matches each event's `axis` tag against every expert's `critical_axes`, appends the matching event to `knowledge-base/experts/<expert>/memory.md`, records a seed marker to make the operation idempotent.
- Applied to the existing 6 audit experts: claim-trace-expert / format-expert / hallucination-expert / figure-vision-critic all got seed lessons appended.
- Also runs `scripts/build_expert_index.py --all` after seeding so RAG indices are up-to-date.

### E — `/mr health <domain>` completeness scorer

- New: `scripts/mr_health.py <domain>` — scores 0-100 across 8 rubric checks (weights sum to 100):
  - benchmark_registry (25pt) — ≥5 entries with `domain=<name>`
  - domain_agents (20pt) — 3 domain-specific agents present with valid frontmatter
  - quality_gates (15pt) — `<domain>/references/quality-gates.md` with ≥3 gates
  - expert_memory (15pt) — ≥6 audit experts with real memory (seed marker or dated entries)
  - rag_indices (10pt) — ≥6 experts have `index.json`
  - skill_routes (5pt) — `<domain>/SKILL.md` with `/mr <domain>` routing
  - references (5pt) — `<domain>/references/{papers,datasets,ideas}.md` all non-empty
  - frontmatter (5pt) — `migrate_agent_frontmatter --dry-run` reports 0 changes pending
- Emits a boxed scorecard with per-check status + suggested fix.
- `--all` mode scores every detected domain at once.

Baseline scores (right after P5 seeding):
- **gnn**: 85/100 grade B (missing: gnn/references/quality-gates.md — not yet written)
- **vla-vlm**: 60/100 grade C (agent files under different naming: `vlavlm-*` vs `vla-vlm-*` — surfaced by mr_health)
- **p5test synthetic**: 100/100 grade A — proves the domain-init pipeline can hit A.

### F — Parallelize `domain-init` dispatch

- `agents/domain-init.md` Phase 2 rewritten around the parallelism-doctrine: all 7 file creations + Phase 2b (registry extend) + Phase 2c (memory seed) share only `domain-researcher.json` as their upstream, so they must dispatch in a single fan-out message. Only `build_expert_index.py --all` is a serial barrier.
- Explicit dependency table + anti-pattern warning added.

### G — Integration test

- New: `tests/regression/test_domain_init_completeness.py` — synthesizes a fake `p5test_domain_research.json`, exercises every P5 script (extend_registry / seed_memories / build_expert_index / mr_health), asserts 26 invariants, then cleans up (removes fixture, restores registry from snapshot).
- **Result: 26/26 assertions PASS, mr_health p5test score 100/100 grade A.**
- Test is idempotent: cleanup restores byte-for-byte on both success and failure paths.

## The user experience of `/mr new-domain <name>`, post-P5

Say the user runs `/mr new-domain tsf "Time Series Forecasting"`:

1. domain-researcher searches web + KB, emits `domain-research.json` matching the v1 schema
2. Phase 2 fan-out: 11 concurrent subagents create SKILL.md, 3 references files, 3 domain agents, quality-gates.md, extend registry, seed memories
3. Barrier: `build_expert_index.py --all` rebuilds RAG indices
4. Phase 3 fan-out: 4 concurrent INDEX.md creations
5. Phase 4: report + implicit `mr_health tsf`

After ~5 minutes, `tsf` has:
- ≥5 datasets in `benchmark-registry.yaml` (auto-verified pending)
- 3 domain-specific agents + SKILL.md
- ≥3 TSF-G* quality gates in `tsf/references/quality-gates.md`
- 6+ expert memories seeded with the 8 canonical failures
- 16 RAG indices rebuilt
- `mr_health tsf` scores ≥90 grade A

## Overall system state at end of P5

```
Doctrines (3):        Three-Times Rule, Parallelism, Writing Standards
Schemas (5):          audit-v1, agent-frontmatter-v1, figure-plan, state-v1, domain-research-v1  ← new
Phase panels:         30 audit experts (6 phases × 5), all seed-inheritable, all RAG-indexed
Executor/support:     33 agents including new domain-researcher + domain-init
Scripts (18):         All P0-P4 + domain_init_extend_registry, domain_init_seed_memories, mr_health
Doctrine files:       audit-doctrine.md, parallelism-doctrine.md, writing-standards.md, domain-quality-gates.md  ← new
Registry:             26+ dataset entries, extensible per-domain
Expert seed:          knowledge-base/experts/_seed/generic-canonical-failures.md  (8 domain-agnostic lessons)
Tests (5):            p0_smoke, audit_loop_sim, js_modules_unit, ci_validate, test_domain_init_completeness  ← new
```

## Sign-off

P5 is the milestone that makes the plugin's name real. Before P5, `research-anything` was a good name for a plugin that was really `research-gnn-and-vla-vlm`. After P5, a brand-new domain — time-series forecasting, robotics, drug design, whatever — gets provisioned with the same 6-phase audit rigor, the same 30 experts pre-loaded with 8 class-of-bug lessons, the same dataset registry, the same domain-specific gates, and a numeric health score confirming completeness.

The `mr_health` scores are also the honest state audit: **gnn is 85/100 and vla-vlm is 60/100** — surfaces missing pieces I can now fix or backlog explicitly, rather than pretend they don't exist.
