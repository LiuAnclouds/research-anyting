---
name: mr-vlavlm-research
description: This skill should be used when the user types "/mr vla-vlm", "/mr vla", "/mr vlm", or references vision-language-action models, embodied AI, robot foundation models, multimodal LLMs, vision-language models, or mentions specific VLA/VLM methods. Orchestrates a multi-agent research pipeline. All commands use "/mr vla-vlm", "/mr vla", or "/mr vlm" prefix.
---

# VLA/VLM Research Domain Orchestrator

See `../../COMMANDS.md` for the full command reference. This file only documents `/mr vla-vlm` routing.

This orchestrator manages the multi-agent research pipeline for VLA and VLM research. The pipeline architecture mirrors every other domain in Moon-Research but applies VLA/VLM-specific knowledge and evaluation protocols. Agents whose logical structure is identical to cross-domain counterparts (`literature-survey`, `paper-reader`, `theory-crafter`, `experiment-engineer`, `paper-writer`, reviewer panel) share the shared agent definition files but are dispatched with VLA/VLM domain knowledge loaded from `vla-vlm/references/`. Domain-specific agents (`vla-vlm-idea-broker`, `vla-vlm-rapid-prototype`, `vla-vlm-insight-analyzer`) have dedicated definitions.

## Command Routing (canonical 10 verbs)

Every domain in Moon-Research exposes exactly the same 10 verbs. VLA-VLM's routing:

| Command | Backing agent | Purpose |
|---------|---------------|---------|
| `/mr vla-vlm idea "topic"` | `agents/vla-vlm-idea-broker.md` | Generate 3-5 candidate research directions |
| `/mr vla-vlm survey "topic"` | `agents/literature-survey.md` | Systematic literature review |
| `/mr vla-vlm read <paper>` | `agents/paper-reader.md` | Three-pass paper read |
| `/mr vla-vlm theory` | `agents/theory-crafter.md` | Formalize + prove |
| `/mr vla-vlm prototype` | `agents/vla-vlm-rapid-prototype.md` | Minimum viable experiment (MVE) |
| `/mr vla-vlm experiment` | `agents/experiment-engineer.md` | Full experiment matrix |
| `/mr vla-vlm analyze` | `agents/vla-vlm-insight-analyzer.md` via ANALYZE panel | Extract insights |
| `/mr vla-vlm write` | `agents/paper-writer.md` via WRITE panel | Manuscript writing |
| `/mr vla-vlm review` | `agents/reviewers/*.md` via REVIEW panel | 5-reviewer panel (includes reproducibility auditor) |
| `/mr vla-vlm full "hypothesis"` | `workflows/vla-vlm-full-pipeline.js` | Full 6-phase pipeline |

**Suffix flags** applicable to any of the above: `--target N`, `--max-rounds N`, `--no-audit`, `--legacy`.

Sub-domain routing: `/mr vla <cmd>` restricts knowledge to VLA references only. `/mr vlm <cmd>` restricts to VLM references only. Both are aliases into the same 10-verb surface.

Note: the standalone `/mr vla-vlm verify` verb has been merged into `/mr vla-vlm review` — the review panel already includes a reproducibility auditor, which was the entire purpose of standalone verify. The redundant `/mr vla-vlm explore` verb has also been removed; use `idea` + `survey` instead.

## Domain-specific verbs (extensible)

A domain can add extra verbs beyond the 10 canonical ones. Convention:

- Add a row to the routing table below with `/mr <domain> <verb>` → `agents/<domain>-<verb>.md`.
- Create the corresponding `agents/<domain>-<verb>.md` with proper frontmatter (`rigor_contract` + `parallelism_contract`).
- Route: when the user types `/mr <domain> <verb>`, dispatch that agent via the `Agent` tool with the domain-knowledge context injection described in this file.

Currently no extra verbs are defined for this domain — the 10 canonical verbs above are the complete surface.

---

## Agent Dispatch Protocol

Each command dispatches a subagent using the `Agent` tool. The agent definition file path and domain knowledge paths are specified in the routing table above.

### Domain-Specific Context Injection

When dispatching an agent that shares a cross-domain definition file, append VLA/VLM-specific context to the dispatch prompt:

> **Domain**: VLA, VLM, or VLA+VLM (as specified by user).
> **Domain knowledge**: Load from `vla-vlm/references/papers-vla.md`, `vla-vlm/references/papers-vlm.md`, and `vla-vlm/references/benchmarks.md`.
> **Evaluation protocols**: VLA-specific (LIBERO, CALVIN, SimplerEnv; sim-to-real gap quantification; embodiment diversity requirements) or VLM-specific (MME, MMBench, SEED-Bench, MM-Vet, POPE, HallusionBench; hallucination decomposition; prompt sensitivity analysis), as specified in `shared/references/evaluation-protocols.md`.

### `/mr vla-vlm idea "topic"` — Idea Generation

Dispatch the `vla-vlm-idea-broker` subagent using `agents/vla-vlm-idea-broker.md`. Pass:

> Research area: `$TOPIC`
> Sub-domain preference: VLA | VLM | both
>
> Instructions:
> 1. Load domain knowledge from `vla-vlm/references/papers-vla.md`, `vla-vlm/references/papers-vlm.md`, and `vla-vlm/references/benchmarks.md`.
> 2. Construct a literature tree for the specified area, sub-domain filtered.
> 3. Apply challenge-insight mapping and technology transfer assessment.
> 4. Generate 3-5 candidate research directions, each with a falsifiable hypothesis, novelty assessment citing at least 3 specific papers, feasibility assessment with resource estimates, and impact assessment with target venue evidence.
> 5. Produce a structured Idea Broker Report.

Verify: each direction has a falsifiable hypothesis, at least 3 cited papers establishing the gap, and specific evidence for novelty/feasibility/impact scores.

### Remaining verbs

`survey`, `read`, `theory`, `prototype`, `experiment`, `analyze`, `write`, `review` follow the same dispatch pattern as their GNN-domain analogues, with the VLA/VLM domain context injected as described above. The `review` verb runs the 5-reviewer panel; its reproducibility-auditor role subsumes what was formerly the standalone verify verb.

---

## Full Pipeline: `/mr vla-vlm full "hypothesis"`

Backed by `workflows/vla-vlm-full-pipeline.js`. Same sequential dispatch pattern as GNN full pipeline (idea → survey → theory → prototype → experiment → analyze → write → review), with VLA/VLM-specific quality gates inserted at appropriate transitions (see below).

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

| Tier | Experiment Engineer | Theory Crafter | Review Panel |
|------|---------------------|----------------|--------------|
| CCF-A | 6-8 benchmarks, 10+ baselines | Theory required (>=1 proof) | 5-reviewer panel calibrated to CCF-A |
| CCF-B | 4-5 benchmarks, 7+ baselines | Theory preferred | 5-reviewer panel calibrated to CCF-B |
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

---

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
