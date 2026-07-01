---
name: mr-vlavlm-research
description: This skill should be used when the user types "/mr vla-vlm", "/mr vla", "/mr vlm", or references vision-language-action models, embodied AI, robot foundation models, multimodal LLMs, vision-language models, or mentions specific VLA/mr vlm methods. Orchestrates a multi-agent research pipeline. All commands use "/mr vla-vlm", "/mr vla", or "/mr vlm" prefix.
---

# VLA/mr vlm Research Domain Orchestrator

This orchestrator manages a multi-agent research pipeline for VLA and VLM research. The pipeline architecture mirrors the GNN domain but applies VLA/VLM-specific knowledge and evaluation protocols. Agents whose logical structure is identical to GNN counterparts (literature-survey, paper-reader, theory-crafter, experiment-engineer, deep-verification, review-simulator) share the GNN agent definition files but are dispatched with VLA/mr vlm domain knowledge loaded from `vla-vlm/references/`. Domain-specific agents (idea-broker, rapid-prototype, insight-analyzer) have dedicated definitions.

## Command Routing

| Command | Agent Definition | Domain Knowledge |
|---------|-----------------|------------------|
| `/mr vla-vlm idea "topic"` | agents/vla-vlm-idea-broker.md | vla-vlm/references/ |
| `/mr vla-vlm survey "topic"` | agents/literature-survey.md | vla-vlm/references/ |
| `/mr vla-vlm read <paper>` | agents/paper-reader.md | vla-vlm/references/ |
| `/mr vla-vlm theory` | agents/theory-crafter.md | vla-vlm/references/ |
| `/mr vla-vlm prototype` | agents/vla-vlm-rapid-prototype.md | vla-vlm/references/ |
| `/mr vla-vlm experiment` | agents/experiment-engineer.md | vla-vlm/references/ |
| `/mr vla-vlm analyze` | agents/vla-vlm-insight-analyzer.md | vla-vlm/references/ |
| `/mr vla-vlm verify` | agents/deep-verification.md | vla-vlm/references/ |
| `/mr vla-vlm review` | agents/review-simulator.md | vla-vlm/references/ |

Sub-domain routing: `/mr vla <cmd>` restricts knowledge to VLA references only. `/mr vlm <cmd>` restricts to VLM references only.

## Agent Dispatch Protocol

Each command dispatches a subagent using the `Agent` tool, following the same pattern as the GNN orchestrator. The agent definition file path and domain knowledge paths are specified in the table above.

### Domain-Specific Context Injection

When dispatching an agent that shares a GNN definition file, append VLA/VLM-specific context to the dispatch prompt:

> **Domain**: VLA, VLM, or VLA+VLM (as specified by user).
> **Domain knowledge**: Load from `vla-vlm/references/papers-vla.md`, `vla-vlm/references/papers-vlm.md`, and `vla-vlm/references/benchmarks.md`.
> **Evaluation protocols**: VLA-specific (LIBERO, CALVIN, SimplerEnv; sim-to-real gap quantification; embodiment diversity requirements) or VLM-specific (MME, MMBench, SEED-Bench, MM-Vet, POPE, HallusionBench; hallucination decomposition; prompt sensitivity analysis), as specified in `shared/references/evaluation-protocols.md`.

### Phase 1: Idea Generation

When the user invokes `/mr vla-vlm idea "topic"`:

**Step 1**: Dispatch the vla-vlm-idea-broker subagent using the `Agent` tool.

Use the agent definition at `agents/vla-vlm-idea-broker.md`. Pass the following context:

> Research area: `$TOPIC`
> Sub-domain preference: VLA | VLM | both
>
> Instructions:
> 1. Load domain knowledge from `vla-vlm/references/papers-vla.md`, `vla-vlm/references/papers-vlm.md`, and `vla-vlm/references/benchmarks.md`.
> 2. Construct a literature tree for the specified area, sub-domain filtered.
> 3. Apply challenge-insight mapping and technology transfer assessment.
> 4. Generate 3-5 candidate research directions, each with a falsifiable hypothesis, novelty assessment citing at least 3 specific papers, feasibility assessment with resource estimates, and impact assessment with target venue evidence.
> 5. Produce a structured Idea Broker Report.

After the subagent completes, verify: each direction has a falsifiable hypothesis, at least 3 cited papers establishing the gap, and specific evidence for novelty/feasibility/impact scores.

### Phase 2-9: [Same dispatch pattern as GNN orchestrator for all remaining phases]

## Multi-Agent Pipeline: `/mr vla-vlm full "hypothesis"`

Same sequential dispatch pattern as GNN full pipeline, with VLA/VLM-specific quality gates inserted at appropriate transitions.

## Knowledge Base Integration

### Paper → Module → Idea Pipeline

1. **Paper Reader agent** produces structured paper notes and stores the paper entry in `knowledge-base/papers/vla-vlm/`.
2. **KB Manager** (via `/mr decompose`) decomposes the paper into constituent modules — visual encoder, projector, action head, and training recipe — and stores each module in `knowledge-base/modules/vla-vlm/`. If an equivalent module already exists from another paper, the evidence is merged and validation status is upgraded.
3. **KB Manager** recomputes module composability.
4. **KB Manager** (via `/mr combinations`) recomputes the idea hypergraph.
5. **KB Manager** (via `/mr recommend-venue`) recommends target venues.

### Pre-Dispatch Context Injection

Before dispatching any research agent, the orchestrator queries the KB for relevant context:

1. Read `knowledge-base/sessions/INDEX.md` to identify the most recent session in the VLA-VLM domain.
2. Read `knowledge-base/ideas/INDEX.md` to identify active ideas and their hyperedge relationships.
3. For paper-related tasks: read `knowledge-base/papers/INDEX.md` and `knowledge-base/modules/INDEX.md` to check what has already been catalogued.
4. Inject a condensed KB context summary (<=500 words) into the agent's dispatch prompt.

### Difficulty-Adaptive Workflow

The orchestrator reads the active idea's `target_venue_tier` and `min_required_validation` fields to calibrate the pipeline:

| Tier | Experiment Engineer | Theory Crafter | Review Simulator |
|------|-------------------|----------------|------------------|
| CCF-A | 6-8 benchmarks, 10+ baselines | Theory required (>=1 proof) | 4-role review calibrated to CCF-A |
| CCF-B | 4-5 benchmarks, 7+ baselines | Theory preferred | 4-role review calibrated to CCF-B |
| CCF-C | 3-4 benchmarks, 5+ baselines | Theory optional | Streamlined review |

### VLA/VLM-Specific Quality Gates

- **VLA-G1**: Sim-to-real gap quantified when real-world applicability is claimed. Gap must not exceed 15 percentage points without explanation.
- **VLA-G2**: Embodiment diversity verified. Claims of generalist capability require evaluation on >=3 robot morphologies.
- **VLM-G1**: Hallucination decomposed by type (object, attribute, relation, OCR). Overall hallucination rate alone is insufficient.
- **VLM-G2**: Prompt sensitivity analyzed. Results must be stable across >=5 prompt variations (standard deviation <2 percentage points).

### Post-Dispatch Storage

After each agent completes:

**If `/mr auto-store on`**: The orchestrator automatically dispatches kb-manager to store the delta.

**If `/mr auto-store off`**: The orchestrator reminds the user. Manual `/mr store session info` is available.

### Cross-Session Continuity

When starting a new session: orchestrator reads the most recent session entry and dispatches kb-manager with `/mr recall "active context for VLA-VLM"` to recover: open hypotheses, pending decisions, active ideas with their module compositions, unresolved questions, and recommended venues.

## Global Commands

The following commands are available at any time regardless of domain:

| Command | Agent | Function |
|---------|-------|----------|
| `/mr new-domain <name> "<desc>"` | domain-init | Create a new research domain |
| `/mr ideas [--domain X] [--status Y]` | kb-manager | List ideas across domains |
| `/idea <slug>` | kb-manager | View detailed idea entry |
| `/idea promote\|discard <slug>` | kb-manager | Change idea status |
| `/mr modules [--domain X] [--category Y]` | kb-manager | Browse module library |
| `/module <slug>` | kb-manager | View module with source papers |
| `/mr papers [--domain X] [--tier Y] [--code]` | kb-manager | List papers with filtering |
| `/paper <slug>` | kb-manager | View paper with modules |
| `/mr venues [--tier X] [--domain Y]` | kb-manager | Browse venue database |
| `/venue <slug>` | kb-manager | View venue with requirements |
| `/mr status [--domain X]` | kb-manager | Pipeline overview |
| `/mr search "query"` | kb-manager | Unified cross-KB search |
| `/mr export idea\|bib <target>` | kb-manager | Export structured data |
| `/mr store session info` | kb-manager | Persist session findings |
| `/mr auto-store on/off` | kb-manager | Toggle autonomous storage |
| `/mr recall "query"` | kb-manager | Retrieve KB context |
| `/mr decompose <paper>` | kb-manager | Decompose paper into modules |
| `/mr combinations` | kb-manager | Recompute idea hypergraph |
| `/mr recommend-venue <idea>` | kb-manager | Recommend target venues |
| `/mr kb-check` | kb-manager | Verify KB integrity |
| `/mr fuse` | kb-manager | Consolidate related entries |

## Support Commands

```
/mr discuss "question" -> Agent(agents/deep-discussion.md, "Discussion on: $QUESTION")
/mr write "section" -> "venue" -> Agent(agents/paper-writer.md, "Write $SECTION for $VENUE")
/mr rebuttal <reviews> -> Agent(agents/rebuttal-writer.md, "Respond to reviews")
/mr log -> Agent(agents/research-log.md, "Record daily entry")
/mr present -> Agent(agents/presentation-builder.md, "Build presentation")
```

## Error Handling

If a dispatched agent produces output that does not meet its quality requirements, the orchestrator must either request re-execution with refined input, or document the failure and its implications. If an agent encounters a fundamentally unresolved issue, the orchestrator may route back to an earlier phase or recommend terminating the direction.

## P2 Supplement — audit-panel integration

As of the P2 panel rollout, every phase of the VLA-VLM pipeline runs through the **same audit-panel infrastructure as the GNN domain** — `workflows/audit-loop.js` + the 6 phase panels (EXPLORE / DESIGN / VALIDATE / ANALYZE / WRITE / REVIEW), each gated at aggregate ≥90 with critical-axis veto and 10-round escalation.

Domain-agnostic by design: the panel agents (`agents/explore/*.md`, `agents/design/*.md`, etc.) do not branch on domain — they audit the manuscript / experiments / KB content directly. VLA-VLM-specific behavior is achieved by:

1. **Benchmark-registry filter**: When `r2-experiments` / `dataset-fitness` / `reproducibility` look up cited datasets, they filter `shared/references/benchmark-registry.yaml` for `domain: vla-vlm`. The 26-entry seed registry already covers RT-1, OpenX-Embodiment, LIBERO, CALVIN, VQAv2, GQA, MMLU, MMBench, MME, SEED-Bench.

2. **VLA-G* / VLM-G* gate composition**: The domain-specific quality gates listed under "VLA/VLM-Specific Quality Gates" above run *in addition to* the general audit-panel gates. They appear as advisory findings in the relevant panel (sim-to-real gap → `r2-experiments`; embodiment diversity → `dataset-fitness`; hallucination decomposition → `failure-case`; prompt sensitivity → `metric-validity`).

3. **Per-expert temperature rotation** (P2-G mode-collapse mitigation): `audit-loop.js` automatically routes anchor experts (statistics, format-expert, claim-trace-expert) to low temperature 0.2 and adversarial experts (devils-advocate, bias-auditor) to high temperature 0.9, regardless of domain.

4. **CLI flags** (P2-F): `/mr vla-vlm <phase> --no-audit / --target X / --max-rounds N / --legacy` route through `workflows/_args.js` exactly like the GNN domain.

No new agent files are required for VLA-VLM; the existing 25 audit-expert agent files (5 EXPLORE + 5 DESIGN + 5 VALIDATE + 5 ANALYZE + 5 WRITE + 5 REVIEW) cover both domains.