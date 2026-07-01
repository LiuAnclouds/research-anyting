---
name: domain-init
description: This skill should be used when the user invokes "/new-domain", "/init-domain", asks to "create a new research domain", "add a research area", "set up a new sub-project", or specifies a research field they want to work on. Auto-generates a complete domain structure including orchestrator, agent definitions, KB directories, module categories, venue mapping, and initial reference files by researching the specified field.
model: inherit
rigor_contract: three-times-verified
parallelism_contract: max-fanout
panel: support
weight: 0
---

# /new-domain — Domain Initialization Orchestrator


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

This orchestrator creates a complete, self-contained research domain within the Moon-Research system. The user provides a short name and a description of the research area. The orchestrator researches the field, identifies its structure, and generates all scaffolding.


## Parallelism contract (read before dispatching sub-work)

You operate under `shared/references/parallelism-doctrine.md`: **default-parallel is the contract**. When this agent has independent sub-work — multiple files to read, multiple sources to query, multiple findings to verify, multiple sub-problems to solve — you MUST dispatch that work concurrently, never serially. Use the runtime's `parallel()` / `pipeline()` primitives (in workflows) or `run_in_background: true` on every `Agent` tool call (from the main loop), all in a single message. The runtime caps concurrency for you; you do not need to throttle.

The decision rule: if call B's prompt does NOT depend on call A's *output content*, dispatch them together. Logging order, narrative order, and aesthetic preference are NOT data dependencies.

## Command

```
/new-domain <short-name> "<description>"
```

Example: `/mr new-domain tsf "Time Series Forecasting with Deep Learning"`

## Execution Protocol

### Phase 0: Validate Input

1. Parse `<short-name>`: must be lowercase, alphanumeric with hyphens, 2-20 characters. Must not conflict with existing domain names (`gnn`, `vla-vlm`).
2. Parse `"<description>"`: must be >=10 words. Must describe a research field within computer science, artificial intelligence, or a related engineering discipline.
3. If validation fails, report the specific issue and request corrected input.

### Phase 1: Research the Domain

Dispatch a subagent using the `Agent` tool. Use the agent definition at `agents/domain-researcher.md`. Pass the following context:

> Research field: `<short-name>` — `<description>`
>
> Instructions:
> 1. Search for the 3-5 most cited survey papers in this field. Record titles, authors, venues, and years.
> 2. Identify the standard benchmark datasets used in this field. Record names, sizes, and domains.
> 3. Identify the 5-10 most cited baseline methods. Record names, years, venues, and code availability.
> 4. Identify the typical methodological decomposition of work in this field. What are the functional components that papers in this field are built from? (e.g., for GNN: encoders, temporal modules, anomaly scorers, loss functions, training strategies). Provide 3-6 categories.
> 5. Identify the CCF venues where work in this field is typically published. List journals and conferences with their tiers.
> 6. Identify the 3-5 most active research frontiers or open problems.
> 7. Produce a structured Domain Research Report.

After the subagent completes, verify: at least 3 surveys identified, at least 5 datasets, at least 5 baselines, at least 3 module categories, at least 5 venues.

### Phase 2: Generate Domain Structure

#### Parallel Dispatch Protocol for domain-init

> **Doctrine citation** (`shared/references/parallelism-doctrine.md`): *"When dispatching work that does not have a strict data dependency on the result of an earlier dispatch, you MUST dispatch concurrently. Default-parallel is the contract. Default-serial is the exception that requires written justification."*

Phase 2 has exactly **one** upstream data source: the Domain Research Report produced in Phase 1 (`domain-researcher.json`). Every artifact this phase creates reads that report and nothing else — none of the File 1-7 creations, none of the Phase 2b registry extension, and none of the quality-gates.md rendering consumes the output of another Phase 2 step. Phase 2c (memory seed) is entirely independent of the Phase 1 report — it operates on `knowledge-base/experts/_seed/*` and existing agent frontmatter — so it does not even need to wait for `domain-researcher.json`.

**Contract**: All independent Phase 2 sub-work MUST be dispatched in a single fan-out message. From a workflow, use `parallel([() => createFile1, () => createFile2, ..., () => extendRegistry, () => seedMemory])`. From the main loop / Agent tool, issue all `Agent` tool calls in the **same message** with `run_in_background: true`, then collect their outputs together. The runtime caps concurrency; you do not throttle.

#### Data-dependency table

| Step | Depends on |
|---|---|
| `domain-researcher.json` (Phase 1 output) | (root of DAG — Phase 0 validated input) |
| File 1: `<short-name>/SKILL.md` | `domain-researcher.json` |
| File 2: `<short-name>/references/papers.md` | `domain-researcher.json` |
| File 3: `<short-name>/references/datasets.md` | `domain-researcher.json` |
| File 4: `<short-name>/references/ideas.md` | `domain-researcher.json` |
| File 4b: `<short-name>/references/quality-gates.md` | `domain-researcher.json` |
| File 5: `agents/<short-name>-idea-broker.md` | `domain-researcher.json` |
| File 6: `agents/<short-name>-rapid-prototype.md` | `domain-researcher.json` |
| File 7: `agents/<short-name>-insight-analyzer.md` | `domain-researcher.json` |
| Phase 2b: benchmark-registry extend | `domain-researcher.json` |
| Phase 2c: memory seed (`domain_init_seed_memories.py`) | (independent — reads `_seed/*` + existing agents) |
| RAG index rebuild (`build_expert_index.py --all`) | Phase 2c memory seed must complete first |

Everything in the rows whose "Depends on" is `domain-researcher.json` is at the same DAG level: none of them consume any other row's output. All of them, **together with Phase 2c**, dispatch in one fan-out message. Only the RAG index rebuild is genuinely serial — it must run after Phase 2c's memory files land on disk (this is the one and only intra-phase barrier).

**Fan-out shape (single message)**:

```
Agent(create SKILL.md,               run_in_background: true) ─┐
Agent(create papers.md,              run_in_background: true) ─┤
Agent(create datasets.md,            run_in_background: true) ─┤
Agent(create ideas.md,               run_in_background: true) ─┤
Agent(create quality-gates.md,       run_in_background: true) ─┤  All 11 dispatch
Agent(create idea-broker.md,         run_in_background: true) ─┤  in ONE message.
Agent(create rapid-prototype.md,     run_in_background: true) ─┤  Harness runs
Agent(create insight-analyzer.md,    run_in_background: true) ─┤  them concurrently.
Bash(python domain_init_extend_registry.py <report>,
     run_in_background: true)                                  ─┤
Bash(python domain_init_seed_memories.py,
     run_in_background: true)                                  ─┘

# Barrier: wait for all above via TaskOutput()
Bash(python build_expert_index.py --all)   # serial: reads Phase 2c output
```

#### File creations (all independent — dispatch together)

Based on the Domain Research Report, create the directory structure:

```bash
mkdir -p knowledge-base/papers/<short-name>
mkdir -p knowledge-base/modules/<short-name>/{<category-1>,<category-2>,...,<category-N>}
mkdir -p <short-name>/references
```

Create the following files (all in the same fan-out; each reads only `domain-researcher.json`):

**File 1: `<short-name>/SKILL.md`** — Domain orchestrator. Template:

```yaml
---
name: <short-name>-research
description: This skill should be used when the user invokes "/mr <short-name>", references <field description>, or mentions specific methods from this field. Orchestrates a multi-agent research pipeline where each phase dispatches a specialized subagent using the Agent tool.
---

# /mr <short-name> — <Field Name> Research Domain

## Command Routing

### Research Commands
| Command | Agent Dispatched |
|---------|-----------------|
| `/mr <short-name> idea "topic"` | <short-name>-idea-broker |
| `/mr <short-name> survey "topic"` | literature-survey (shared) |
| `/mr <short-name> read <paper>` | paper-reader (shared) |
| `/mr <short-name> theory` | theory-crafter (shared) |
| `/mr <short-name> prototype "approach"` | <short-name>-rapid-prototype |
| `/mr <short-name> experiment` | experiment-engineer (shared) |
| `/mr <short-name> analyze <results>` | <short-name>-insight-analyzer |
| `/mr <short-name> verify` | deep-verification (shared) |
| `/mr <short-name> review <manuscript>` | review-simulator (shared) |
| `/mr <short-name> explore "topic"` | idea-broker -> survey -> paper-reader (sequential) |
| `/mr <short-name> full "hypothesis"` | All agents with quality gates |

[Same KB commands, support commands, KB integration, and difficulty-adaptive workflow sections as gnn/SKILL.md, with domain-specific substitutions.]

Load domain knowledge from `<short-name>/references/`.
```

**File 2: `<short-name>/references/papers.md`** — Initial paper database with surveys, baselines, and frontier methods from the Domain Research Report.

**File 3: `<short-name>/references/datasets.md`** — Benchmark dataset catalog from the Domain Research Report.

**File 4: `<short-name>/references/ideas.md`** — Research directions with falsifiable hypotheses, derived from the open problems identified in the Domain Research Report.

**File 4b: `<short-name>/references/quality-gates.md`** — Domain-specific quality gates that supplement the general audit-panel gates. Populate from the `quality_gates[]` array in the Domain Research Report JSON. Each entry has fields `{id, name, panel_expert, axis, threshold, rationale}`; render them into the following template:

```markdown
# Domain-Specific Quality Gates — <domain-short-name>

Panel-specific axes that supplement the general audit-panel gates for this domain. See `shared/references/domain-quality-gates.md` for the canonical spec.

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| <SHORT>-G1 | ... | <expert> / <axis> | ... | ... |
| <SHORT>-G2 | ... | <expert> / <axis> | ... | ... |
| ...        | ... | ...                 | ... | ... |
```

The `panel_expert` field must be one of `r2-experiments`, `dataset-fitness`, `metric-validity`, `failure-case` (or another named audit-panel agent). If the Domain Research Report did not produce a `quality_gates[]` array, dispatch the domain-researcher subagent a second time with the prompt "Identify 3-6 domain-specific quality gates for `<short-name>` following the schema in `shared/references/domain-quality-gates.md`" before writing this file.

**File 5: `agents/<short-name>-idea-broker.md`** — Domain-specific Idea Broker agent, adapted from the GNN Idea Broker template with the domain's literature tree, challenge-insight mapping, and key venues.

**File 6: `agents/<short-name>-rapid-prototype.md`** — Domain-specific Rapid Prototype agent with minimal viable experiment configurations appropriate to the domain's standard benchmarks.

**File 7: `agents/<short-name>-insight-analyzer.md`** — Domain-specific Insight Analyzer with analysis dimensions appropriate to the domain's typical evaluation metrics and failure modes.

### Phase 2b: Extend Benchmark Registry

*Dispatched in the Phase 2 fan-out — reads `domain-researcher.json`, writes to `benchmark-registry.yaml`; no dependency on Files 1-7.*

Run: `python scripts/domain_init_extend_registry.py <path/to/domain-research.json>`

This appends the new domain's benchmark datasets into `shared/references/benchmark-registry.yaml`
with `domain=<short-name>` and `verified_at: pending`. The `hallucination-expert`, `r2-experiments`,
`dataset-fitness`, and `reproducibility` panels will now find these datasets on lookup
without falling back to `paper_fetcher`.

If the script reports collisions, review them — usually means the domain-researcher found an
alias for an existing dataset (e.g. someone re-named MMLU). Capture the reported `added` count
so it can be included in the Phase 4 report.

Exit codes: 0 = clean append; 1 = collisions were found and skipped (report them, don't retry
blindly); 2 = IO error.

### Phase 2c: Seed Expert Memory

*The `domain_init_seed_memories.py` call is dispatched in the Phase 2 fan-out — it is fully independent of `domain-researcher.json` (it only reads `_seed/*` and existing expert frontmatter). The `build_expert_index.py --all` call is the ONE genuine serial barrier in this phase — it must run after `domain_init_seed_memories.py` completes, because it indexes the files that pass writes.*

For every expert in the 6 audit panels (30 experts total), append the domain-agnostic canonical failures from `knowledge-base/experts/_seed/generic-canonical-failures.md` into that expert's `knowledge-base/experts/<expert-name>/memory.md` (creating the file if absent). Filter by axis — each expert receives only the seed events relevant to its critical_axes.

Then run: python scripts/build_expert_index.py --all  (regenerates RAG indices so the new seed events are searchable).

Concretely, dispatch (first line in the Phase 2 fan-out, second line only after the barrier):

```bash
python scripts/domain_init_seed_memories.py   # in Phase 2 fan-out
# --- barrier: wait for all Phase 2 dispatches ---
python scripts/build_expert_index.py --all    # serial: reads Phase 2c output
```

The first pass parses the 8 canonical failures out of the seed file, reads each expert's `critical_axes` from its `agents/**/<expert>.md` frontmatter, and appends only the axis-matching seed entries per expert. The second pass rebuilds the sentence-transformer indices so downstream `expert_retrieve.py` calls surface seed events alongside real encounters. A brand-new domain therefore starts with pre-loaded class-of-bug awareness even before its own experts have run once.

### Phase 3: Initialize KB

#### Parallel Dispatch Protocol for Phase 3

> **Doctrine citation** (`shared/references/parallelism-doctrine.md`): *"If you can split it, you must split it."*

All four KB scaffolding operations below touch **different files** and read only the Domain Research Report + existing INDEX.md contents. None of them consumes the output of another. Steps 1 and 2 create *new* files; steps 3 and 4 append/edit *disjoint* existing INDEX.md files (`knowledge-base/INDEX.md` + `knowledge-base/papers/INDEX.md` in step 3, `knowledge-base/venues/INDEX.md` in step 4). There is no read-after-write dependency between any pair.

**Contract**: dispatch all four in a single fan-out message. Same shape as Phase 2 — a single message with four `Agent` (or `Edit`/`Write`) tool calls with `run_in_background: true` where applicable, awaited together.

| Step | Depends on |
|---|---|
| 1. `knowledge-base/papers/<short-name>/INDEX.md` (new) | Phase 1 report only |
| 2. `knowledge-base/modules/<short-name>/INDEX.md` (new) | Phase 1 report only |
| 3. Register domain in `knowledge-base/INDEX.md` + `knowledge-base/papers/INDEX.md` | Phase 1 report only |
| 4. Add venue entries to `knowledge-base/venues/INDEX.md` | Phase 1 report only |

Steps (dispatched together, not sequentially):

1. Create `knowledge-base/papers/<short-name>/INDEX.md`.
2. Create `knowledge-base/modules/<short-name>/INDEX.md` with entries for each module category.
3. Add the domain to `knowledge-base/INDEX.md` and `knowledge-base/papers/INDEX.md`.
4. Add venue entries for any venues not already in `knowledge-base/venues/INDEX.md`.

The numbering is narrative order for the reader, **not** dispatch order — dispatch order is "all at once."

### Anti-pattern warning (Phases 2 and 3)

The following orchestration shapes are **bugs in the orchestrator** per `shared/references/parallelism-doctrine.md` and MUST NOT appear in any domain-init execution trace:

- **Do NOT** dispatch each file with a separate `await` — e.g. `await createSkillMd; await createPapersMd; await createDatasetsMd; ...`. That's 8× the wall-clock for zero gain.
- **Do NOT** wait for File 1 (SKILL.md) to land before starting File 2 (papers.md). They share zero data — SKILL.md does not reference papers.md's content and vice versa; both read only `domain-researcher.json`.
- **Do NOT** wait for Phase 2b (registry extend) before starting Phase 2c (memory seed). They touch disjoint files (`benchmark-registry.yaml` vs `knowledge-base/experts/*/memory.md`) and share no data.
- **Do NOT** wait for Phase 2 to fully drain before starting Phase 3's *file creations* if you can start them in the same fan-out — the KB INDEX writes read only the Phase 1 report, same as Phase 2. (The only reason to keep Phase 3 as a separate barrier is if the Phase 4 report needs the Phase 2 collision counts; otherwise you can collapse Phase 2 + Phase 3 file writes into a single mega-fanout.)
- **Do NOT** dispatch INDEX.md steps 1→2→3→4 serially "so the log reads in order." Logging order is not a data dependency — dispatch them together and log when they all return.

A serial domain-init is a **contract violation**. The runtime already caps concurrency; the orchestrator's job is to *offer* maximum fan-out, not to throttle it manually.

### Phase 4: Report

Report a summary:
- Domain created: `<short-name>`
- Module categories: N categories identified
- Surveys catalogued: N
- Baselines catalogued: N
- Datasets catalogued: N
- Benchmark-registry entries added: N (from Phase 2b `added` count; note any collisions skipped)
- Venues mapped: N
- Agent definitions created: 3 domain-specific + 6 shared (inherited)
- Next steps: `/ <UPPER-SHORT-NAME> survey "topic"` to begin literature survey, `/ <UPPER-SHORT-NAME> idea "topic"` to generate research directions.

---

## Additional Global Commands

The following commands operate across all domains and are available at any point:

### Idea Management
| Command | Function |
|---------|----------|
| `/mr ideas` | List all ideas across domains, filterable by status, domain, tier |
| `/idea <slug>` | View detailed idea entry with modules, papers, recommended venues |
| `/idea promote <slug>` | Promote idea from incubating to active |
| `/idea discard <slug>` | Discard idea with reason |
| `/idea combine <slug1> <slug2> ...` | Manually propose a new hyperedge of specific ideas |

### Module Library
| Command | Function |
|---------|----------|
| `/mr modules` | Browse module library, filterable by domain, category, validation status |
| `/module <slug>` | View detailed module entry with source papers, composability, assumptions |

### Paper Management
| Command | Function |
|---------|----------|
| `/mr papers` | List papers in KB, filterable by domain, venue tier, novelty, code availability |
| `/paper <slug>` | View detailed paper entry with modules, connections |

### Venue Browsing
| Command | Function |
|---------|----------|
| `/mr venues` | Browse venue database, filterable by tier, domain, category |
| `/venue <slug>` | View detailed venue entry with requirements, similar papers |

### Pipeline Status
| Command | Function |
|---------|----------|
| `/mr status` | Overview: active ideas, in-progress experiments, recent papers, pending decisions |
| `/mr status <domain>` | Domain-specific status |

### Cross-KB Search
| Command | Function |
|---------|----------|
| `/mr search "query"` | Unified search across papers, modules, ideas, venues, insights, and sessions |

### Export
| Command | Function |
|---------|----------|
| `/mr export idea <slug>` | Export idea as a structured research proposal (markdown) |
| `/mr export module <slug>` | Export module with all evidence and composability data |
| `/mr export bib <domain>` | Export all paper BibTeX entries for a domain |