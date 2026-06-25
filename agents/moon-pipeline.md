---
name: moon-pipeline
description: This skill should be used when the user invokes "/mr auto", "/mr full", asks to "run the full research pipeline", "automate my research", "one-click research", or wants autonomous end-to-end research execution from idea generation through manuscript completion. Orchestrates ALL agents with maximum parallelism — independent agents run concurrently, not sequentially. Uses the Agent tool for every dispatch.
---

# /mr auto — Autonomous Full-Cycle Research Pipeline

This orchestrator executes the complete research lifecycle with maximum parallelism. Every agent that can run concurrently does so. The pipeline is organized into six phases, but within each phase, ALL independent agents are dispatched simultaneously.

## Parallelism Principle

**RULE**: If Agent B does not depend on Agent A's output, dispatch them concurrently. Do not serialize independent work.

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
```

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

Step 2.2 agents are independent of each other. Dispatch them ALL simultaneously using run_in_background: true.
```

## Concurrent Dispatch Protocol

**THIS IS CRITICAL**: When dispatching multiple independent agents, you MUST use `run_in_background: true` for EVERY agent. Do NOT dispatch them sequentially. The pattern is:

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
```

## Phase 4: ANALYZE

```
AFTER Phase 3 completes, dispatch ALL three CONCURRENTLY:
  ┌─ Insight Analyzer
  ├─ Deep Verification
  └─ Experiment Debugger
```

## Phase 5: WRITE

```
AFTER Phase 4 completes, dispatch ALL sections CONCURRENTLY:
  ┌─ Write Abstract
  ├─ Write Introduction
  ├─ Write Related Work
  ├─ Write Method
  ├─ Write Experiments
  └─ Write Conclusion
```

## Phase 6: REVIEW

```
AFTER Phase 5 completes, dispatch ALL four reviewers CONCURRENTLY:
  ┌─ EIC Review
  ├─ Reviewer #1 (Methodology)
  ├─ Reviewer #2 (Experiments)
  └─ Devil's Advocate
```
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

Gates are evaluated automatically. When a gate PASSES, the pipeline auto-advances without asking.
When a gate FAILS, the pipeline auto-retries (up to 3x) or flags to human depending on severity.

| Gate | Check | Auto-Response |
|------|-------|---------------|
| G1 | Gap validated by >=3 papers | PASS → auto-advance; FAIL → re-run survey |
| G2 | MVE passes pre-registered criterion | PASS → auto-advance; FAIL → auto-retry 3x then flag |
| G3 | All ablation + 5 seeds + stats | PASS → auto-advance; FAIL → flag missing items |
| G4 | All claims verified | PASS → auto-advance; FAIL → flag to human |
| G5 | Review score >= 70 | PASS → auto-complete; FAIL → auto-revise |

## Command Interface

```
/mr auto "topic"                → Full pipeline, auto-advance at all gates (no prompts)
/mr auto "topic" --parallel N   → Set max concurrent agents to N (default: unlimited)
/mr auto "topic" --human-gates  → Human approval required at each gate transition
/mr auto "topic" --stop-at X    → Stop at phase: explore|design|validate|analyze|write|review
/mr auto "topic" --target X     → Calibrate for CCF-A/B/C
/mr auto "topic" --dry-run      → Plan without executing
/mr auto status                 → Current pipeline status
/mr auto resume                 → Continue from last checkpoint
```

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