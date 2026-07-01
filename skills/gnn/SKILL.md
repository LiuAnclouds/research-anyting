---
name: mr-gnn-research
description: This skill should be used when the user types "/mr gnn", references graph neural network research, dynamic graph anomaly detection, graph representation learning, or mentions specific GNN methods. Orchestrates a multi-agent research pipeline. All commands use the "/mr gnn" prefix.
---

# GNN Research Domain Orchestrator

See `../../COMMANDS.md` for the full command reference. This file only documents `/mr gnn` routing.

This orchestrator manages the GNN research pipeline. Each phase dispatches a specialized subagent using the `Agent` tool. Subagents are stateless: each receives complete input context and produces a complete output. The orchestrator handles quality gate verification between phases.

## Command Routing (canonical 10 verbs)

Every domain in Moon-Research exposes exactly the same 10 verbs. GNN's routing:

| Command | Backing agent | Purpose |
|---------|---------------|---------|
| `/mr gnn idea "topic"` | `agents/gnn-idea-broker.md` | Generate 3-5 candidate research directions |
| `/mr gnn survey "topic"` | `agents/literature-survey.md` | Systematic literature review |
| `/mr gnn read <paper>` | `agents/paper-reader.md` | Three-pass paper read |
| `/mr gnn theory` | `agents/theory-crafter.md` | Formalize + prove |
| `/mr gnn prototype` | `agents/gnn-rapid-prototype.md` | Minimum viable experiment (MVE) |
| `/mr gnn experiment` | `agents/experiment-engineer.md` | Full experiment matrix |
| `/mr gnn analyze` | `agents/gnn-insight-analyzer.md` via ANALYZE panel | Extract insights |
| `/mr gnn write` | `agents/paper-writer.md` via WRITE panel | Manuscript writing |
| `/mr gnn review` | `agents/reviewers/*.md` via REVIEW panel | 5-reviewer panel (includes reproducibility auditor) |
| `/mr gnn full "hypothesis"` | `workflows/gnn-full-pipeline.js` | Full 6-phase pipeline |

**Suffix flags** applicable to any of the above: `--target N`, `--max-rounds N`, `--no-audit`, `--legacy`.

Note: the standalone `/mr gnn verify` verb has been merged into `/mr gnn review` — the review panel already includes a reproducibility auditor, which was the entire purpose of standalone verify. The redundant `/mr gnn explore` verb has also been removed; use `idea` + `survey` instead.

## Domain-specific verbs (extensible)

A domain can add extra verbs beyond the 10 canonical ones. Convention:

- Add a row to the routing table below with `/mr <domain> <verb>` → `agents/<domain>-<verb>.md`.
- Create the corresponding `agents/<domain>-<verb>.md` with proper frontmatter (`rigor_contract` + `parallelism_contract`).
- Route: when the user types `/mr <domain> <verb>`, dispatch that agent via the `Agent` tool with the domain-knowledge context injection described in this file.

Currently no extra verbs are defined for this domain — the 10 canonical verbs above are the complete surface.

---

## Knowledge Base Integration

### Paper → Module → Idea Pipeline

When a paper is read and stored:

1. **Paper Reader agent** produces structured paper notes and stores the paper entry in `knowledge-base/papers/gnn/`.
2. **KB Manager** (dispatched automatically or via `/mr decompose`) decomposes the paper into its constituent modules — graph encoder, temporal module, anomaly scorer, loss function, training strategy — and stores each module in `knowledge-base/modules/gnn/`. If an equivalent module already exists from another paper, the evidence is merged and validation status is upgraded.
3. **KB Manager** recomputes module composability (`composable_with` / `incompatible_with` fields).
4. **KB Manager** (via `/mr combinations`) recomputes the idea hypergraph: discovers all K-way module combinations that satisfy complementarity, compatibility, synergy, and minimality. New combinations become idea entries in `ideas/incubating/`.
5. **KB Manager** (via `/mr recommend-venue`) recommends target venues for active ideas based on contribution strength and domain fit.

This pipeline ensures that every paper contributes reusable modules, every validated module combination becomes a candidate idea, and every idea has a concrete publication target.

### Pre-Dispatch Context Injection

Before dispatching any research agent, the orchestrator queries the KB for relevant context:

1. Read `knowledge-base/sessions/INDEX.md` to identify the most recent session in the same domain.
2. Read `knowledge-base/ideas/INDEX.md` to identify active ideas and their hyperedge relationships.
3. For paper-related tasks: read `knowledge-base/papers/INDEX.md` and `knowledge-base/modules/INDEX.md` to check what has already been catalogued and decomposed.
4. Inject a condensed KB context summary (<=500 words) into the agent's dispatch prompt.

### Difficulty-Adaptive Workflow

The orchestrator reads the active idea's `target_venue_tier` and `min_required_validation` fields to calibrate the pipeline:

| Tier | Experiment Engineer | Theory Crafter | Review Panel |
|------|---------------------|----------------|--------------|
| CCF-A | 6-8 datasets, 10+ baselines | Theory required (>=1 proof) | 5-reviewer panel calibrated to CCF-A |
| CCF-B | 4-5 datasets, 7+ baselines | Theory preferred | 5-reviewer panel calibrated to CCF-B |
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

### `/mr gnn idea "topic"` — Idea Generation

Dispatch the `gnn-idea-broker` subagent using the `Agent` tool with the definition at `agents/gnn-idea-broker.md`. Pass:

> Research area: `$TOPIC`
>
> Instructions:
> 1. Load domain knowledge from `gnn/references/papers.md`, `gnn/references/ideas.md`, and `gnn/references/datasets.md`.
> 2. Construct a literature tree for the specified area.
> 3. Apply challenge-insight mapping and technology transfer assessment.
> 4. Generate 3-5 candidate research directions, each with a falsifiable hypothesis, novelty assessment citing at least 3 specific papers, feasibility assessment with resource estimates, and impact assessment with target venue evidence.
> 5. Produce a structured Idea Broker Report.

Verify: each direction has a falsifiable hypothesis, at least 3 cited papers establishing the gap, and specific evidence for novelty/feasibility/impact scores. If quality gate fails, request re-execution with refined input.

### `/mr gnn survey "topic"` — Literature Survey

Dispatch `agents/literature-survey.md` with:

> Research topic: `$TOPIC`
> Optional filters: venue tier, year range, method type (from user input)
>
> Instructions:
> 1. Execute multi-source search (Semantic Scholar, arXiv, DBLP, GitHub).
> 2. Apply iterative snowball sampling until saturation.
> 3. Classify papers by method type, graph type, anomaly level, application, venue, and code availability.
> 4. Perform gap analysis using taxonomic, survey-based, and performance-based methods.
> 5. Produce a structured Literature Survey Report with verified BibTeX entries.

Verify: search methodology documented, at least 50 papers screened, at least 20 deep-analyzed, gap analysis cites at least 2 independent surveys.

### `/mr gnn read <paper>` — Paper Reading

Dispatch `agents/paper-reader.md` passing the paper content or path.

### `/mr gnn theory`, `/mr gnn prototype`, `/mr gnn experiment` — Construction Layer

Dispatch `theory-crafter`, `gnn-rapid-prototype`, and `experiment-engineer` following the same dispatch pattern. Pass outputs from previous phases as input context.

### `/mr gnn analyze`, `/mr gnn write`, `/mr gnn review` — Analysis / Write / Review Layer

Dispatch `gnn-insight-analyzer` (via ANALYZE panel), `paper-writer` (via WRITE panel), and the 5-reviewer panel at `agents/reviewers/*.md` (via REVIEW panel) respectively. The review panel must receive ALL outputs from prior phases; its reproducibility-auditor role subsumes what was formerly the standalone verify verb.

---

## Full Pipeline: `/mr gnn full "hypothesis"`

Backed by `workflows/gnn-full-pipeline.js`. Dispatches agents sequentially with quality gates:

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

Phase 7: Dispatch paper-writer (via WRITE panel) -> Manuscript

Phase 8: Dispatch review panel (via REVIEW panel, with manuscript + all reports) -> Review Report
  Gate G5: Score >=70/100 at target venue tier; reproducibility-auditor sign-off obtained.
```

At each gate, if the condition is not met, the orchestrator must either: route back to the appropriate agent with refined input, or report the failure to the user with specific evidence of which conditions are unmet.

---

## Concurrent Execution

Where agent outputs are independent, dispatch agents concurrently. For example, once an Idea Broker Report exists, `literature-survey` and `paper-reader` (over the top 2-3 seed papers) can be dispatched in parallel. This aligns with the plugin-wide **default-parallel** parallelism doctrine — serial ordering must be justified by a real data dependency.

---

## Error Handling

If a dispatched agent produces output that does not meet its quality requirements, the orchestrator must either request re-execution with refined input, or document the failure and its implications. If an agent encounters a fundamentally unresolved issue, the orchestrator may route back to an earlier phase or recommend terminating the direction.
