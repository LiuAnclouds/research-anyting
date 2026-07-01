# Parallelism Doctrine — Moon-Research v2

> **Default-parallel is the contract. Default-serial is the exception that requires written justification.**

## The rule (one sentence)

When dispatching work that does not have a strict data dependency on the result of an earlier dispatch, you MUST dispatch concurrently. The more independent subagents you can fan out, the better.

## Why this is the rule

Research work is mostly fan-out work. Surveying 30 papers, auditing 6 manuscript sections, scoring 5 expert axes, rendering 8 figures, re-checking 26 bib entries against 4 APIs — none of these require serial execution. Serial dispatch is **time wasted** and, for this orchestrator, also wall-clock that the user is paying for.

The 6-phase audit panel system is designed around this: every panel runs 5 expert agents *in parallel*, every figure pipeline runs the N slots *in parallel*, every multi-source paper lookup hits 4 sources *in parallel*. If your code dispatches them serially it is violating the contract.

## Decision rule

Before writing `await agent(...)` followed by another `await agent(...)`, ask yourself:

> Does the second call's prompt depend on the **content** of the first call's output?

- **NO** → you MUST use `parallel([() => agent(A), () => agent(B), ...])` or `pipeline(items, stage1, stage2, ...)`.
- **YES** → serial is allowed; document why in a comment.

The most common false dependency is "well I want to *log* A before starting B". Logging is not a data dependency. Dispatch them together, log them when both return.

## Allowed serial sequences

The exceptions list — every phase that genuinely must be serial:

1. **Theory-crafter → code-generator**: code generation reads the theory spec.
2. **Code-generator → rapid-prototype**: the prototype needs the generated code.
3. **Audit round N executor → audit round N panel**: the panel scores the executor's output.
4. **Audit round N panel → audit round N+1 executor**: the executor reads the revise prompt.
5. **Figure-planner → figure-renderer**: the renderer reads the plan.
6. **Figure-renderer → figure-vision-critic**: the critic reads the rendered PNG.
7. **Figure-vision-critic → figure-integrator**: the integrator skips slots that failed vision.

Everything else fans out.

## How to fan out properly

### Within a single phase / panel

Use the Workflow runtime's `parallel(thunks)` or `pipeline(items, stage1, stage2)`:

```js
// CORRECT — 5 audit experts fan out concurrently:
const expertResults = await parallel(
  panel.map(p => () => agent(p.prompt(execOut, retrieved, round), {schema: ...}))
)

// CORRECT — 6 figure slots run their 5-stage chain independently:
await pipeline(slotIds,
  slot => agent(`render ${slot}`),
  rendered => agent(`vision-critic ${rendered.slot}`),
  vetted   => agent(`integrate ${vetted.slot}`)
)
```

### When using the Agent tool from the main loop

Dispatch every independent subagent with `run_in_background: true` in the **same message** (the harness will run them concurrently). Wait for all via `TaskOutput()`.

```
1. Agent(literature-survey,    run_in_background: true)  ─┐
2. Agent(paper-reader-1,       run_in_background: true)  ─┤  All 7 dispatch
3. Agent(paper-reader-2,       run_in_background: true)  ─┤  in one message;
4. Agent(paper-reader-3,       run_in_background: true)  ─┤  harness runs them
5. Agent(paper-reader-4,       run_in_background: true)  ─┤  concurrently.
6. Agent(paper-reader-5,       run_in_background: true)  ─┤
7. Agent(domain-venue-mapping, run_in_background: true)  ─┘
```

The wrong shape is: dispatch agent 1, await, dispatch agent 2, await... that's 7× the latency.

### Inside a single agent's task

When an agent itself can shard its work (e.g. paper-reader processing 5 papers, literature-survey querying 4 APIs, hallucination-expert verifying 26 bib entries), it MUST use parallel HTTP / parallel subprocess / parallel ThreadPoolExecutor inside its tool calls. `scripts/paper_fetcher.py` already does this (4-way concurrent across SS / arXiv / DBLP / CrossRef). Every script that fan-outs work should follow the same pattern.

## Concurrency caps

The Workflow runtime caps concurrent `agent()` calls at `min(16, cpu_cores - 2)` per workflow. You can still pass 100 items to `parallel()` / `pipeline()` and they all complete; only ~10 run at any moment. The total agent count across a workflow's lifetime is capped at 1000 (a runaway-loop backstop, not a soft limit you should worry about).

Do not artificially serialize because you're worried about hitting the cap. The runtime handles backpressure.

## The "default-parallel" frontmatter contract

Every executor / panel / support agent in `agents/**/*.md` has a `parallelism_contract: max-fanout` field in its frontmatter. The contract reads:

> When this agent has independent sub-work (multiple files to read, multiple sources to query, multiple findings to verify), it will dispatch that work concurrently — never serially — using the runtime's parallel primitives.

Agents that violate this contract (serialize independent work) are themselves blocking findings in the audit panels:

- `survey-completeness` flags any survey that queried 4 sources serially.
- `experimental-design` flags any experiment matrix that ran datasets serially when CPU was available.
- `r2-experiments` flags any baseline re-run that didn't shard across processes.

## What this rule does NOT say

- It does not say "skip validation". Audit-loop's per-round barrier (round N panel must complete before round N+1 starts) is genuine data dependency.
- It does not say "fan out indefinitely". Use `pipeline()` over `parallel()` when stages are present — no barrier waste.
- It does not say "ignore cost". Fanning out 50 expert calls runs up token bills. Use the budget tracker (`workflows/_budget.js`, `scripts/audit_budget_report.py`) to monitor.

## In one line

**If you can split it, you must split it.**
