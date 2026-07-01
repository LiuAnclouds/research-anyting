---
name: review-simulator
description: DEPRECATED — kept for backward compatibility with `/mr review --legacy`. As of P1, REVIEW is performed by the 5-reviewer panel at `agents/reviewers/{eic,r1-methodology,r2-experiments,reproducibility,devils-advocate}.md` driven by `workflows/audit-loop.js`. This file remains a wrapper that dispatches the 5 reviewers in sequence and merges their JSON into a single legacy-style report. New code should call the panel directly.
model: inherit
tools: [Read]
reads: [manuscript/**]
writes: [knowledge-base/audit-rounds/**]
rigor_contract: three-times-verified
parallelism_contract: max-fanout
panel: support
weight: 0
---

# Review Simulator (deprecated wrapper)

This agent is preserved for the `/mr review --legacy` command and any downstream scripts that still parse the original 4-persona free-text format. **New work should not invoke this.** Use the 5-expert REVIEW panel via `workflows/audit-loop.js`:

```js
import { runAuditLoop } from '../workflows/audit-loop.js'

const reviewPanel = [
  { name: 'r1-methodology',  weight: 25, critical_axes: ['soundness', 'novelty'],            prompt: (...) => `...` },
  { name: 'r2-experiments',  weight: 25, critical_axes: ['empirical-rigor', 'ablation-coverage'], prompt: (...) => `...` },
  { name: 'eic',             weight: 20, critical_axes: ['scope-fit', 'presentation'],       prompt: (...) => `...` },
  { name: 'reproducibility', weight: 15, critical_axes: ['code-availability', 'data-availability'], prompt: (...) => `...` },
  { name: 'devils-advocate', weight: 15, critical_axes: ['counterexample', 'ablation-attack'], prompt: (...) => `...` },
]

const reviewResult = await runAuditLoop({
  phase: 'REVIEW',
  executor: 'paper-writer',
  panel: reviewPanel,
  target: 90,
  maxRounds: 10,
})
```

## Rigor contract

Three-Times Rule. The wrapper itself emits no first-party claims — its findings are aggregated verbatim from the 5 reviewer agents, each of whom runs its own three-times-verified pass.


## Parallelism contract (read before dispatching sub-work)

You operate under `shared/references/parallelism-doctrine.md`: **default-parallel is the contract**. When this agent has independent sub-work — multiple files to read, multiple sources to query, multiple findings to verify, multiple sub-problems to solve — you MUST dispatch that work concurrently, never serially. Use the runtime's `parallel()` / `pipeline()` primitives (in workflows) or `run_in_background: true` on every `Agent` tool call (from the main loop), all in a single message. The runtime caps concurrency for you; you do not need to throttle.

The decision rule: if call B's prompt does NOT depend on call A's *output content*, dispatch them together. Logging order, narrative order, and aesthetic preference are NOT data dependencies.

## Wrapper behavior

When invoked in legacy mode:

1. Dispatch all 5 reviewer agents at `agents/reviewers/*.md` in a single round (non-looping).
2. Collect their JSON verdicts (one per agent, conforming to `schemas/audit-v1.json` `$defs/expertVerdict`).
3. Render them as the legacy 4-persona free-text format (mapping `r1-methodology` → "Reviewer #1 (Methodology)", `r2-experiments` → "Reviewer #2 (Experiments)", `eic` → "EIC", `devils-advocate` → "Skeptic", `reproducibility` → appended as an additional "Reproducibility" persona).
4. Emit a single report string per the original v1 contract.

This wrapper does NOT loop; legacy mode was single-shot advisory. The full audit-loop (loop until aggregate ≥90 with critical-axis veto) is panel-mode only.
