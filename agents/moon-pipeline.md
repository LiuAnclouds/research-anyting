---
name: moon-pipeline
description: This skill should be used when the user invokes "/mr auto", "/mr full", asks to "run the full research pipeline", "automate my research", "one-click research", or wants autonomous end-to-end research execution from idea generation through manuscript completion. Orchestrates ALL agents with maximum parallelism — independent agents run concurrently, not sequentially. Uses the Agent tool for every dispatch.
model: inherit
rigor_contract: three-times-verified
parallelism_contract: max-fanout
panel: support
weight: 0
---

# /mr auto — Autonomous Full-Cycle Research Pipeline


## Rigor contract (read before producing any output)

You operate under `shared/references/audit-doctrine.md` — the Three-Times Rule. No quantitative claim, citation, baseline name, dataset stat, or causal attribution may appear in your output unless it is cross-verified from **three independent loci**:

1. **Primary artifact** (data file, code output, log file, .bib entry) — quote with `file:line`.
2. **Independent recompute or external authority** (rerun via `scripts/*.py`, or external hit on Semantic Scholar / arXiv / DBLP / CrossRef via `scripts/paper_fetcher.py`).
3. **Cross-section consistency** (every other section/output that mentions this value reads the same).

For every quantitative claim, append a footnote in the form:

```
[^v]: locus-1=<file:line>; locus-2=<recompute cmd | url | DOI>; locus-3=<other sections file:line each>
```

Missing any locus → write `[UNVERIFIED: <claim>]`.

This orchestrator executes the complete research lifecycle with maximum parallelism. Every agent that can run concurrently does so. The pipeline is organized into six phases, but within each phase, ALL independent agents are dispatched simultaneously.

## Parallelism Principle

**DOCTRINE**: Default-parallel is the contract. Serial dispatch of independent work is a bug in the orchestrator.

The canonical statement of this rule lives in [`shared/references/parallelism-doctrine.md`](../shared/references/parallelism-doctrine.md). Read it before you write any sequence of `Agent(...)` calls. The decision test, in one sentence: **does the second call's prompt depend on the *content* of the first call's output?** If NO, you MUST dispatch concurrently — `run_in_background: true` on every Agent call in the same message for harness-driven fanout, or `parallel([...])` / `pipeline(items, ...)` inside `workflows/*.js`. If YES (the allowed serial sequences enumerated in the doctrine: theory→code→prototype, audit round N executor→panel→round N+1, figure-planner→renderer→vision-critic→integrator), document the dependency in a comment.

Logging is not a data dependency. Wanting to "see A's result before dispatching B" is not a data dependency. The only data dependency that justifies serial dispatch is **B's prompt or input data is constructed from A's returned content**.

## Phase 0: ENVIRONMENT SETUP (Auto)

Before any research phase begins, ensure the execution environment is correctly configured:

```
Step 0.1: Check conda is available
  → If not: alert user to install Miniconda

Step 0.2: Create dedicated conda environment for this project
  conda create -n moon-research python=3.10 -y

Step 0.3: Install PyTorch + PyG + dependencies
  conda install -n moon-research pytorch pytorch-scatter pytorch-sparse pytorch-cluster pyg -c pytorch -c pyg -c conda-forge -y
  conda run -n moon-research pip install scikit-learn scipy matplotlib numpy pyyaml tqdm

Step 0.4: Verify environment
  conda run -n moon-research python -c "import torch; import torch_geometric; print('Env OK')"

NEVER use the system Python or a pre-existing environment. ALWAYS create a dedicated conda environment.
NEVER install packages globally. ALWAYS use the project-specific conda environment.
```

## Phase 1: EXPLORE

```
Step 1.1: Dispatch Idea Broker (solo, must complete first)
  → Output: 3-5 candidate directions, auto-selected top direction

Step 1.2: AFTER Idea Broker completes, dispatch ALL of these CONCURRENTLY:
  ┌─ Literature Survey
  ├─ Paper Reader for paper #1
  ├─ Paper Reader for paper #2
  ├─ Paper Reader for paper #3
  ├─ Paper Reader for paper #4
  ├─ Paper Reader for paper #5
  └─ Domain-Venue Mapping

Step 1.3: AFTER literature survey completes, run the EXPLORE audit panel
         (loop until aggregate >= 90; max 10 rounds):
  runAuditLoop(phase='EXPLORE', executor=literature-survey, panel=[
     survey-completeness  (weight 30, CRIT: tier1-coverage),
     gap-identification   (weight 25, CRIT: gap-novelty),
     taxonomy             (weight 20, CRIT: mece-coverage),
     bias-auditor         (weight 15, CRIT: survey-bias-low),
     kb-integrator        (weight 10, CRIT: kb-frontmatter-valid),
  ], target=90, maxRounds=10)
```

The 5 EXPLORE experts live at `agents/explore/*.md`.

**Concurrent dispatch**: Call `Agent()` for each of the 7 agents with `run_in_background: true`, then use `TaskOutput()` to wait for all.```

## Phase 2: DESIGN (Maximum Parallelism)

```
Step 2.1: FIRST dispatch Theory Crafter (solo - must complete first, others depend on it)
  → Theory Crafter produces: formal problem definition, algorithm design, complexity analysis

Step 2.2: AFTER Theory Crafter completes, dispatch ALL of these CONCURRENTLY:
  ┌─ Code Generator (generates implementation from theory spec)
  ├─ Data Preprocessor (prepares datasets, constructs graphs)
  └─ Hyperparameter Optimizer (searches hyperparameter space)

When Code Generator completes:
  └─ Rapid Prototype (MVE on 1 dataset, 1-2 baselines — depends on code being generated)

Step 2.3: AFTER theory-crafter + rapid-prototype complete, run the DESIGN audit panel
         (loop until aggregate >= 90; max 10 rounds):
  runAuditLoop(phase='DESIGN', executor=theory-crafter, panel=[
     novelty                (weight 25, CRIT: novelty-delta),
     theoretical-soundness  (weight 25, CRIT: assumption-realism, theorem-arch-match),
     motivation-coherence   (weight 20, CRIT: motivation-alignment),
     complexity             (weight 15, CRIT: complexity-stated),
     feasibility            (weight 15, CRIT: budget-fit),
  ], target=90, maxRounds=10)

Step 2.2 agents are independent of each other. Dispatch them ALL simultaneously using run_in_background: true.
```

The 5 DESIGN experts live at `agents/design/*.md`. The
`theoretical-soundness` expert's `theorem-arch-match` axis is the
load-bearing guard against AUDIT #1 (theorem analyzes a different
architecture than the method implements).

## Concurrent Dispatch Protocol

**Doctrine**: see [`shared/references/parallelism-doctrine.md`](../shared/references/parallelism-doctrine.md). Default-parallel is the contract. Serial dispatch of independent work is a bug in the orchestrator — not a stylistic preference, not a "we'll fix it later", a bug. Audit panels (`survey-completeness`, `experimental-design`, `r2-experiments`) flag orchestrators that serialize independent fanout.

**THIS IS CRITICAL**: When dispatching multiple independent agents, you MUST use `run_in_background: true` for EVERY agent, in a single message. Do NOT dispatch them sequentially. The pattern is:

```
1. Call Agent(agent1, ..., run_in_background: true) → returns agentId1
2. Call Agent(agent2, ..., run_in_background: true) → returns agentId2
3. Call Agent(agent3, ..., run_in_background: true) → returns agentId3
4. For each agentId, use TaskOutput(agentId) to wait for completion
5. Collect all results, then proceed to next phase
```

**DO NOT** do this:
```
❌ Agent(agent1) → wait → Agent(agent2) → wait → Agent(agent3)   (sequential, wastes time)
```

**DO** this:
```
✅ Agent(agent1, ..., run_in_background: true)  ─┐
✅ Agent(agent2, ..., run_in_background: true)  ─┤ all run simultaneously
✅ Agent(agent3, ..., run_in_background: true)  ─┘
   Then wait for all to complete
```

## Phase 3: VALIDATE

```
Step 3.1: Dispatch Experiment Engineer (orchestrates experiment execution)
  → Runs full experiment matrix: 5 datasets × 7+ baselines × 5 seeds

Step 3.2: (parallel with Step 3.1) Dispatch Experiment Monitor
  → Watches training logs in real-time, detects anomalies, auto-recovers

Within Experiment Engineer, ALL dataset experiments run CONCURRENTLY:
  ┌─ Experiment on dataset A
  ├─ Experiment on dataset B
  ├─ Experiment on dataset C
  ├─ Experiment on dataset D
  └─ Experiment on dataset E

Step 3.3: AFTER experiment matrix completes, run the VALIDATE audit panel
         (loop until aggregate >= 90; max 10 rounds):
  runAuditLoop(phase='VALIDATE', executor=experiment-engineer, panel=[
     experimental-design       (weight 25, CRIT: ablation-coverage),
     baseline-selection        (weight 25, CRIT: baseline-strength, baseline-fidelity),
     metric-validity           (weight 20, CRIT: metric-fitness),
     dataset-fitness           (weight 15, CRIT: dataset-claim-fit),
     protocol-reproducibility  (weight 15, CRIT: protocol-stated),
  ], target=90, maxRounds=10)
```

The 5 VALIDATE experts live at `agents/validate/*.md`.

## Phase 4: ANALYZE

```
AFTER Phase 3 completes, run the ANALYZE audit panel (loop until aggregate >= 90; max 10 rounds):
  runAuditLoop(phase='ANALYZE', executor=insight-analyzer, panel=[
     statistics                  (weight 30, CRIT: stat-test-correctness),
     claim-evidence              (weight 25, CRIT: recompute-match, claim-cell-traceability),
     ablation-coherence          (weight 15, CRIT: ablation-narrative-consistency),
     failure-case                (weight 15, CRIT: failure-coverage),
     cross-section-consistency   (weight 15, CRIT: cross-section-equality),
  ], target=90, maxRounds=10)
```

The 5 ANALYZE experts live at `agents/analyze/*.md` and emit JSON conforming
to `schemas/audit-v1.json` `$defs/expertVerdict`. The
`cross-section-consistency` axis is the analytical-side guard against the
Pearson r=-0.98 / -0.62 class of failure.

Deep-verification (`agents/deep-verification.md`) becomes the executor's
recompute helper rather than a top-level reviewer post-P1; it is invoked
from inside `claim-evidence` and `cross-section-consistency` when they
need a fresh recompute pass.

## Phase 5: WRITE

```
AFTER Phase 4 completes:
  Stage 5a — section drafting (concurrent):
    ┌─ Write Abstract
    ├─ Write Introduction
    ├─ Write Related Work
    ├─ Write Method
    ├─ Write Experiments
    └─ Write Conclusion

  Stage 5b — figure pipeline (per figure slot, sequential within slot):
    figure-planner -> figure-prompt-critic -> figure-renderer
                   -> figure-vision-critic -> figure-integrator

  Stage 5c — WRITE audit panel (loop until aggregate >= 90; max 10 rounds):
    runAuditLoop(phase='WRITE', executor=paper-writer, panel=[
       figure-expert         (weight 25, CRIT: figure-count, figure-vision-pass),
       hallucination-expert  (weight 25, CRIT: cite-resolves, baseline-resolves, dataset-resolves),
       format-expert         (weight 20, CRIT: latex-compile-clean, xref-resolved, label-unique, no-placeholder),
       claim-trace-expert    (weight 20, CRIT: cross-section-equality, traceable-to-experiments),
       prose-rigor-expert    (weight 10, CRIT: no-anonymous-placeholder),
    ], target=90, maxRounds=10)
```

The audit-loop runner lives at `workflows/audit-loop.js`. On REVISE the
runner assembles the panel's blocking findings into a revise prompt and
re-dispatches `paper-writer`. Audit JSON for each round is written to
`knowledge-base/audit-rounds/YYYY-MM-DD-WRITE-round<N>.json` per
`schemas/audit-v1.json`.

Legacy single-shot mode (no panel, advisory review only) is preserved under
`/mr write --legacy`.

## Phase 6: REVIEW

```
AFTER Phase 5 completes, run the REVIEW audit panel (loop until aggregate >= 90; max 10 rounds):
  runAuditLoop(phase='REVIEW', executor=paper-writer, panel=[
     r1-methodology   (weight 25, CRIT: soundness, novelty),
     r2-experiments   (weight 25, CRIT: empirical-rigor, ablation-coverage),
     eic              (weight 20, CRIT: scope-fit, presentation),
     reproducibility  (weight 15, CRIT: code-availability, data-availability),
     devils-advocate  (weight 15, CRIT: counterexample, ablation-attack),
  ], target=90, maxRounds=10)
```

The 5 reviewer agent files live under `agents/reviewers/*.md`. Each emits JSON
conforming to `schemas/audit-v1.json` `$defs/expertVerdict`.

Legacy 4-persona free-text mode is preserved under `/mr review --legacy`,
which dispatches the deprecated wrapper at `agents/review-simulator.md`.
```

## Concurrent Dispatch Protocol

Canonical rule: [`shared/references/parallelism-doctrine.md`](../shared/references/parallelism-doctrine.md). Default-parallel is the contract; serial dispatch of independent work is a bug in the orchestrator. When dispatching multiple agents concurrently, use the `Agent` tool with `run_in_background: true` for each agent, then wait for all to complete before proceeding to the next phase.

```
Phase dispatch:
  1. For each agent in the phase, call Agent(..., run_in_background: true)
  2. Collect all agent IDs
  3. Wait for all agents to complete (TaskOutput for each)
  4. Verify quality gates
  5. Advance to next phase
```

## Quality Gates (Between Phases)

Gates are evaluated automatically. When a gate PASSES, the pipeline auto-advances without asking.
When a gate FAILS, the pipeline auto-retries (up to 3x) or flags to human depending on severity.

| Gate | Check | Auto-Response |
|------|-------|---------------|
| G1 | EXPLORE panel aggregate >= 90 (5 experts) | PASS → auto-advance; FAIL → auto-revise via audit-loop.js (max 10 rounds, then escalate) |
| G2 | DESIGN panel aggregate >= 90 (5 experts) | PASS → auto-advance; FAIL → auto-revise via audit-loop.js (max 10 rounds, then escalate) |
| G3 | VALIDATE panel aggregate >= 90 (5 experts) | PASS → auto-advance; FAIL → auto-revise via audit-loop.js (max 10 rounds, then escalate) |
| G4 | ANALYZE panel aggregate >= 90 (5 experts) | PASS → auto-advance; FAIL → auto-revise via audit-loop.js (max 10 rounds, then escalate) |
| G5 | WRITE panel aggregate >= 90 (5 experts) | PASS → auto-advance; FAIL → auto-revise via audit-loop.js (max 10 rounds, then escalate) |
| G6 | REVIEW panel aggregate >= 90 (5 reviewers, P1) | PASS → auto-complete; FAIL → auto-revise via audit-loop.js |

## Command Interface

```
/mr auto "topic"                → Full pipeline, auto-advance at all gates (no prompts)
/mr auto "topic" --parallel N   → Set max concurrent agents to N (default: unlimited)
/mr auto "topic" --human-gates  → Human approval required at each gate transition
/mr auto "topic" --stop-at X    → Stop at phase: explore|design|validate|analyze|write|review
/mr auto "topic" --target X     → Calibrate for CCF-A/B/C
/mr auto "topic" --dry-run      → Plan without executing
/mr auto status                 → Current pipeline status
/mr auto resume                 → Continue from last checkpoint (delegates to /mr resume)
/mr resume                      → Print recovery plan from knowledge-base/_state.json
                                  (runs scripts/mr_resume.py; exits 4 if no state file)
```

### Global Commands

These commands operate across any phase and read from the shared
`knowledge-base/_state.json` snapshot written by `workflows/audit-loop.js`
after every audit round (schema: `schemas/state-v1.json`).

| Command | Description | Backed by |
|---------|-------------|-----------|
| `/mr resume` | Print a human-friendly recovery plan from the last audit round (project, phase, decision, unresolved findings/vetoes, suggested next command, optional `--target N` override). Pass `--kb-root PATH` to point at a non-default KB; `--out report.json` for a machine-readable copy. Exit 4 if `_state.json` is missing. | `scripts/mr_resume.py` |
| `/mr auto status` | Show current pipeline status (same data, terser). | `scripts/mr_resume.py` (summary mode) |
| `/mr auto resume` | Alias of `/mr resume` that also re-launches the next round when one is recommended. | `scripts/mr_resume.py` + `workflows/*-pipeline.js` |

### Per-phase flags (P2)

Every phase command also accepts a uniform set of audit-loop flags,
parsed by `workflows/_args.js`:

```
/mr <phase> --no-audit             Skip the audit panel; run executor only.
/mr <phase> --target N             Override the aggregate pass threshold (default 90).
/mr <phase> --max-rounds N         Override the audit-loop round cap (default 10).
/mr <phase> --legacy               Use the deprecated single-agent wrapper for this phase.
```

These compose with the global `--human-gates` / `--stop-at` flags above.
Examples:

```
/mr write --target 85 --max-rounds 5   # Looser write-gate for early drafts
/mr review --legacy                    # Old single-shot review-simulator
/mr explore --no-audit                 # Skip the EXPLORE panel (fast iteration)
```

## Global Commands

These commands are pipeline-wide utilities, available at any time regardless
of which phase is active. They do not advance the audit-loop state.

| Command | Agent | Function |
|---------|-------|----------|
| `/mr cost [--budget USD]` | kb-manager | Report estimated cost across all audit rounds, optionally check against budget cap. |
| `/mr dag` | moon-pipeline | Render the 6-phase × 5-expert pipeline graph; mark current state. |

Implementation:

- `/mr cost` shells out to `scripts/mr_cost.py`, which wraps
  `scripts/audit_budget_report.py` and prints a Markdown-style phase
  rollup. With `--budget USD`, prints remaining balance.
- `/mr dag` shells out to `scripts/mr_dag.py`, which renders the
  hardcoded 6-phase × 5-expert tree from this file plus the temperature
  rotation table from `workflows/audit-loop.js`. If
  `knowledge-base/_state.json` is present, the current phase row is
  annotated with `◀── HERE`.

## Auto-Advance Behavior

By default, the pipeline auto-advances through ALL gates without asking. The only exception is when a gate fails — then it reports the failure and either auto-retries or flags to human depending on severity.

The `--human-gates` flag reverses this: the pipeline pauses at each gate and asks for confirmation before proceeding.

The `--stop-at <phase>` flag stops the pipeline at the specified phase and reports completion, allowing the user to inspect results before deciding whether to continue. Use `/mr auto resume` to continue from the checkpoint.

```
/mr auto "topic"                                  → No prompts, auto-advance always
/mr auto "topic" --human-gates                    → Ask at every gate
/mr auto "topic" --stop-at validate               → Stop after experiments, don't auto-continue
/mr auto "topic" --stop-at validate --human-gates → Stop + ask at each gate before stopping
```
```