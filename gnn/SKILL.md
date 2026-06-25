---
name: mr-gnn-research
description: This skill should be used when the user types "/mr gnn", references graph neural network research, dynamic graph anomaly detection, graph representation learning, or mentions specific GNN methods. Orchestrates a multi-agent research pipeline. All commands use the "/mr gnn" prefix.
---

# GNN Research Domain Orchestrator

This orchestrator manages a nine-agent research pipeline for GNN research. Each phase dispatches a specialized subagent using the `Agent` tool. Subagents are stateless: each receives complete input context and produces a complete output. The orchestrator handles quality gate verification between phases.

## Command Routing

### Research Commands

| Command | Agent Dispatched | Phase |
|---------|-----------------|-------|
| `/mr gnn idea "topic"` | gnn-idea-broker | Exploration |
| `/mr gnn survey "topic"` | literature-survey | Exploration |
| `/mr gnn read <paper>` | paper-reader | Exploration |
| `/mr gnn theory` | theory-crafter | Construction |
| `/mr gnn prototype "approach"` | gnn-rapid-prototype | Construction |
| `/mr gnn experiment` | experiment-engineer | Construction |
| `/mr gnn experiment --monitor` | experiment-engineer + experiment-monitor | Construction |
| `/mr gnn analyze <results>` | gnn-insight-analyzer | Validation |
| `/mr gnn verify` | deep-verification | Validation |
| `/mr gnn review <manuscript>` | review-simulator | Validation |
| `/mr gnn explore "topic"` | idea-broker -> literature-survey -> paper-reader (sequential) | Full Exploration |
| `/mr gnn full "hypothesis"` | All nine agents with quality gates | Full Pipeline |

### Knowledge Base Commands

| Command | Agent Dispatched | Function |
|---------|-----------------|----------|
| `/mr store session info` | kb-manager | Persist key decisions, hypotheses, results, papers, and ideas |
| `/mr auto-store on/off` | kb-manager (auto) | Toggle autonomous KB storage after each agent completes |
| `/mr recall "query"` | kb-manager | Retrieve relevant KB context for injection into current session |
| `/mr decompose <paper>` | kb-manager | Decompose a paper into its constituent modules (Paper → Module) |
| `/mr combinations` | kb-manager | Recompute idea hypergraph (Module → Idea); discover K-way combinations |
| `/mr recommend-venue <idea>` | kb-manager | Recommend target venues based on idea contribution profile |
| `/mr kb-check` | kb-manager | Verify KB integrity |
| `/mr fuse` | kb-manager | Consolidate related entries to prevent index bloat |

### Support Commands

`/discuss` -> deep-discussion, `/write` -> paper-writer, `/rebuttal` -> rebuttal-writer, `/log` -> research-log, `/present` -> presentation-builder.

---

## Knowledge Base Integration

### Paper → Module → Idea Pipeline

When a paper is read and stored:

1. **Paper Reader agent** produces structured paper notes and stores the paper entry in `knowledge-base/papers/gnn/`.
2. **KB Manager** (dispatched automatically or via `/decompose`) decomposes the paper into its constituent modules — graph encoder, temporal module, anomaly scorer, loss function, training strategy — and stores each module in `knowledge-base/modules/gnn/`. If an equivalent module already exists from another paper, the evidence is merged and validation status is upgraded.
3. **KB Manager** recomputes module composability (`composable_with` / `incompatible_with` fields).
4. **KB Manager** (via `/combinations`) recomputes the idea hypergraph: discovers all K-way module combinations that satisfy complementarity, compatibility, synergy, and minimality. New combinations become idea entries in `ideas/incubating/`.
5. **KB Manager** (via `/recommend-venue`) recommends target venues for active ideas based on contribution strength and domain fit.

This pipeline ensures that every paper contributes reusable modules, every validated module combination becomes a candidate idea, and every idea has a concrete publication target.

### Pre-Dispatch Context Injection

Before dispatching any research agent, the orchestrator queries the KB for relevant context:

1. Read `knowledge-base/sessions/INDEX.md` to identify the most recent session in the same domain.
2. Read `knowledge-base/ideas/INDEX.md` to identify active ideas and their hyperedge relationships.
3. For paper-related tasks: read `knowledge-base/papers/INDEX.md` and `knowledge-base/modules/INDEX.md` to check what has already been catalogued and decomposed.
4. Inject a condensed KB context summary (<=500 words) into the agent's dispatch prompt.

### Difficulty-Adaptive Workflow

The orchestrator reads the active idea's `target_venue_tier` and `min_required_validation` fields to calibrate the pipeline:

| Tier | Experiment Engineer | Theory Crafter | Review Simulator |
|------|-------------------|----------------|------------------|
| CCF-A | 6-8 datasets, 10+ baselines | Theory required (>=1 proof) | 4-role review calibrated to CCF-A |
| CCF-B | 4-5 datasets, 7+ baselines | Theory preferred | 4-role review calibrated to CCF-B |
| CCF-C | 3-4 datasets, 5+ baselines | Theory optional | Streamlined review |

The orchestrator passes these calibration parameters to each agent's dispatch prompt. This prevents over-engineering for CCF-C targets and under-engineering for CCF-A targets.

### Post-Dispatch Storage

After each agent completes:

**If `/mr auto-store on`**: The orchestrator automatically dispatches kb-manager to store the delta.

**If `/mr auto-store off`**: The orchestrator reminds the user. Manual `/mr store session info` is available.

### Cross-Session Continuity

When starting a new session: orchestrator reads the most recent session entry and dispatches kb-manager with `/mr recall "active context for [domain]"` to recover: open hypotheses, pending decisions, active ideas with their module compositions, unresolved questions, and recommended venues.

---

## Agent Dispatch Protocol

### Phase 1: Idea Generation

When the user invokes `/mr gnn idea "topic"` or Exploration phase:

**Step 1**: Dispatch the gnn-idea-broker subagent using the `Agent` tool.

Use the agent definition at `agents/gnn-idea-broker.md`. Pass the following context in the dispatch prompt:

> Research area: `$TOPIC`
>
> Instructions:
> 1. Load domain knowledge from `gnn/references/papers.md`, `gnn/references/ideas.md`, and `gnn/references/datasets.md`.
> 2. Construct a literature tree for the specified area.
> 3. Apply challenge-insight mapping and technology transfer assessment.
> 4. Generate 3-5 candidate research directions, each with a falsifiable hypothesis, novelty assessment citing at least 3 specific papers, feasibility assessment with resource estimates, and impact assessment with target venue evidence.
> 5. Produce a structured Idea Broker Report.

After the subagent completes, verify output quality: each direction must have a falsifiable hypothesis, at least 3 cited papers establishing the gap, and specific evidence for novelty/feasibility/impact scores. If quality gate fails, request re-execution with refined input.

### Phase 2: Literature Survey

When the user invokes `/mr gnn survey "topic"`:

**Step 1**: Dispatch the literature-survey subagent using the `Agent` tool.

Use the agent definition at `agents/literature-survey.md`. Pass the following context:

> Research topic: `$TOPIC`
> Optional filters: venue tier, year range, method type (from user input)
>
> Instructions:
> 1. Execute multi-source search (Semantic Scholar, arXiv, DBLP, GitHub).
> 2. Apply iterative snowball sampling until saturation.
> 3. Classify papers by method type, graph type, anomaly level, application, venue, and code availability.
> 4. Perform gap analysis using taxonomic, survey-based, and performance-based methods.
> 5. Produce a structured Literature Survey Report with verified BibTeX entries.

After the subagent completes, verify: search methodology documented, at least 50 papers screened, at least 20 deep-analyzed, gap analysis cites at least 2 independent surveys.

### Phase 3: Paper Reading

When the user invokes `/mr gnn read <paper-path>`:

**Step 1**: Dispatch the paper-reader subagent using the `Agent` tool.

Use the agent definition at `agents/paper-reader.md`. Pass the paper content or path.

### Phase 4-6: Construction Layer

For `/mr gnn theory`, `/mr gnn prototype`, and `/mr gnn experiment`, dispatch the corresponding agents (theory-crafter, gnn-rapid-prototype, experiment-engineer) following the same dispatch pattern. Pass outputs from previous phases as input context.

### Phase 7-9: Validation Layer

For `/mr gnn analyze`, `/mr gnn verify`, and `/mr gnn review`, dispatch gnn-insight-analyzer, deep-verification, and review-simulator respectively. The verification and review agents must receive ALL outputs from prior phases.

---

## Multi-Agent Pipeline: `/mr gnn full "hypothesis"`

When the user invokes the complete pipeline, dispatch agents sequentially with quality gates:

```
Phase 1: Dispatch gnn-idea-broker -> Idea Broker Report
  Gate G1: Gap validated by >=3 independent sources; hypothesis is falsifiable.

Phase 2: Dispatch literature-survey (with Idea Broker context) -> Literature Survey
  Verify: >=50 papers screened, >=2 surveys cited for gaps.

Phase 3: Dispatch theory-crafter (with Survey context) -> Theory Report
  Gate G2: All assumptions stated; complexity bounds derived.

Phase 4: Dispatch gnn-rapid-prototype (with Theory context) -> Prototype Report
  Gate G3: Pre-registered hypothesis passes MVE threshold.

Phase 5: Dispatch experiment-engineer (with Prototype context) -> Experiment Report
  Gate G4: >=5 seeds, >=7 baselines, statistical tests applied.

Phase 6: Dispatch gnn-insight-analyzer (with Experiment context) -> Insight Report

Phase 7: Dispatch deep-verification (with ALL prior outputs) -> Verification Report
  Gate G5: All claims verified; no overclaiming detected.

Phase 8: Dispatch review-simulator (with manuscript + all reports) -> Review Report
  Gate G6: Score >=70/100 at target venue tier.
```

At each gate, if the condition is not met, the orchestrator must either: route back to the appropriate agent with refined input, or report the failure to the user with specific evidence of which conditions are unmet.

---

## Concurrent Execution

Where agent outputs are independent, dispatch agents concurrently:

- `/mr gnn explore "topic"`: After Idea Broker completes, dispatch Literature Survey and (for the top 2-3 seed papers) Paper Reader concurrently.
- `/mr gnn verify` and `/mr gnn analyze`: These can execute concurrently since they serve different functions (one checks correctness, the other extracts meaning).

---

## Support Agent Dispatch

Support agents are dispatched similarly:

```
/mr discuss "question" -> Agent(agents/deep-discussion.md, "Discussion on: $QUESTION")
/mr write "section" -> "venue" -> Agent(agents/paper-writer.md, "Write $SECTION for $VENUE")
/mr rebuttal <reviews> -> Agent(agents/rebuttal-writer.md, "Respond to reviews")
/mr log -> Agent(agents/research-log.md, "Record daily entry")
/mr present -> Agent(agents/presentation-builder.md, "Build presentation")
```

## Global Commands (Domain-Agnostic)

The following commands are available at any time, regardless of which domain is active:

| Command | Agent | Function |
|---------|-------|----------|
| `/new-domain <name> "<desc>"` | domain-init | Create a new research domain with full scaffolding |
| `/ideas [--domain X] [--status Y]` | kb-manager | List ideas across domains with filtering |
| `/idea <slug>` | kb-manager | View detailed idea entry |
| `/idea promote\|discard <slug>` | kb-manager | Change idea status |
| `/modules [--domain X] [--category Y]` | kb-manager | Browse module library |
| `/module <slug>` | kb-manager | View module with source papers and composability |
| `/papers [--domain X] [--tier Y] [--code]` | kb-manager | List papers with filtering |
| `/paper <slug>` | kb-manager | View paper with modules and connections |
| `/venues [--tier X] [--domain Y]` | kb-manager | Browse venue database |
| `/venue <slug>` | kb-manager | View venue with requirements and similar papers |
| `/status [--domain X]` | kb-manager | Pipeline overview: active ideas, experiments, papers |
| `/search "query"` | kb-manager | Unified cross-KB search |
| `/export idea\|bib <target>` | kb-manager | Export structured data |

---

## Error Handling

If a dispatched agent produces output that does not meet its quality requirements, the orchestrator must either request re-execution with refined input, or document the failure and its implications. If an agent encounters a fundamentally unresolved issue, the orchestrator may route back to an earlier phase or recommend terminating the direction.
