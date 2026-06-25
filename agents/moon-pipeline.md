---
name: moon-pipeline
description: This skill should be used when the user invokes "/mr auto", "/mr full", asks to "run the full research pipeline", "automate my research", "one-click research", or wants autonomous end-to-end research execution from idea generation through manuscript completion. Orchestrates ALL agents with maximum parallelism — independent agents run concurrently, not sequentially. Uses the Agent tool for every dispatch.
---

# /mr auto — Autonomous Full-Cycle Research Pipeline

This orchestrator executes the complete research lifecycle with maximum parallelism. Every agent that can run concurrently does so. The pipeline is organized into six phases, but within each phase, ALL independent agents are dispatched simultaneously.

## Parallelism Principle

**RULE**: If Agent B does not depend on Agent A's output, dispatch them concurrently. Do not serialize independent work.

## Phase 1: EXPLORE (Maximum Parallelism)

```
Step 1.1: Dispatch Idea Broker (solo, must complete first)
  → Generate 3-5 candidate directions
  → Auto-select top-ranked direction

Step 1.2: AFTER Idea Broker completes, dispatch ALL of these CONCURRENTLY:
  ┌─ Literature Survey (searches all 15+ sources)
  ├─ Paper Reader for top paper #1
  ├─ Paper Reader for top paper #2  
  ├─ Paper Reader for top paper #3
  ├─ Paper Reader for top paper #4
  ├─ Paper Reader for top paper #5
  └─ Domain-Venue Mapping

ALL of these run simultaneously. They share the Idea Broker output but are independent of each other.
```

## Phase 2: DESIGN (Maximum Parallelism)

```
AFTER Phase 1 completes, dispatch ALL of these CONCURRENTLY:

  ┌─ Theory Crafter (formalizes method, derives complexity)
  ├─ Code Generator (generates implementation from theory spec)
  └─ Data Preprocessor (prepares datasets, constructs graphs)

When Theory Crafter completes:
  ┌─ Hyperparameter Optimizer (searches hyperparameter space)
  └─ Rapid Prototype (MVE on 1 dataset, 1-2 baselines)

Code Generator and Data Preprocessor can run independently.
Hyperparameter Optimizer depends on Theory Crafter.
Rapid Prototype depends on Theory Crafter + Code Generator.
```

## Phase 3: VALIDATE (Parallel + Monitored)

```
AFTER Phase 2 completes:

  ┌─ Experiment Engineer (runs full experiment matrix)
  │   └─ Experiment Monitor (parallel, background, watches training)
  │
  └─ (concurrent with above)
      ┌─ Run experiments on dataset A
      ├─ Run experiments on dataset B  
      ├─ Run experiments on dataset C
      ├─ Run experiments on dataset D
      └─ Run experiments on dataset E

All dataset experiments run concurrently. Experiment Monitor watches all.
```

## Phase 4: ANALYZE (Maximum Parallelism)

```
AFTER Phase 3 completes, dispatch ALL of these CONCURRENTLY:

  ┌─ Insight Analyzer (performance attribution, failure taxonomy, narrative)
  ├─ Deep Verification (statistical rigor, claim-evidence, overclaiming)
  └─ Experiment Debugger (diagnose any unexpected results)

All three are independent — they analyze the same experiment results from different angles.
```

## Phase 5: WRITE (Maximum Parallelism)

```
AFTER Phase 4 completes, dispatch sections CONCURRENTLY:

  ┌─ Write Abstract
  ├─ Write Introduction
  ├─ Write Related Work
  ├─ Write Method (Section 3)
  ├─ Write Experiments (Section 4)
  └─ Write Conclusion

ALL sections written simultaneously. Each section agent receives the full context.
After all sections complete:
  ┌─ Generate Figures (plot_results.py)
  └─ Compile BibTeX from KB
```

## Phase 6: REVIEW (Parallel Reviewers)

```
AFTER Phase 5 completes, dispatch ALL reviewers CONCURRENTLY:

  ┌─ EIC Review
  ├─ Reviewer #1 (Methodology)
  ├─ Reviewer #2 (Experiments)  
  └─ Devil's Advocate (Skeptic)

All four reviewers evaluate the manuscript independently and simultaneously.
After all reviews complete → synthesize final review report.

If score >= 80: AUTO-COMPLETE
If score >= 70: auto-revise minor issues, re-review
If score < 70: flag to human
```

## Concurrent Dispatch Protocol

When dispatching multiple agents concurrently, use the `Agent` tool with `run_in_background: true` for each agent, then wait for all to complete before proceeding to the next phase.

```
Phase dispatch:
  1. For each agent in the phase, call Agent(..., run_in_background: true)
  2. Collect all agent IDs
  3. Wait for all agents to complete (TaskOutput for each)
  4. Verify quality gates
  5. Advance to next phase
```

## Quality Gates (Between Phases)

| Gate | Check | Auto-Response |
|------|-------|---------------|
| G1 | Gap validated by >=3 papers | PASS → continue; FAIL → re-run survey |
| G2 | MVE passes pre-registered criterion | PASS → continue; FAIL → auto-retry 3x then flag |
| G3 | All ablation + 5 seeds + stats | PASS → continue; FAIL → flag missing items |
| G4 | All claims verified | PASS → continue; FAIL → flag to human |
| G5 | Review score >= 70 | PASS → auto-complete; FAIL → auto-revise |

## Command Interface

```
/mr auto "topic"                → Full autonomous pipeline (max parallelism)
/mr auto "topic" --parallel N   → Set max concurrent agents to N (default: unlimited)
/mr auto "topic" --human-gates  → Human approval at gate transitions
/mr auto "topic" --target X     → Calibrate for CCF-A/B/C
/mr auto "topic" --dry-run      → Plan without executing
/mr auto status                 → Current pipeline status
/mr auto resume                 → Continue from last checkpoint
```

## Parallelism Control

The `--parallel N` flag limits the maximum number of concurrent agents within a phase. If not specified, all independent agents run simultaneously.

```
/mr auto "topic" --parallel 3   → At most 3 agents run concurrently
/mr auto "topic"                 → Unlimited parallelism (default)
```