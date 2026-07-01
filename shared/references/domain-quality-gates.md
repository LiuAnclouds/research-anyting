# Domain-Specific Quality Gates

## Purpose

Every research domain in Moon-Research declares its own **domain-specific quality gates** — additional, advisory scoring axes that supplement the general audit-panel gates defined in `audit-doctrine.md`. These gates capture the discipline-specific failure modes that a general reviewer would miss: e.g., the sim-to-real gap in robot learning (VLA-G1), or hallucination decomposition in vision-language models (VLM-G1).

Domain gates **ADD to** the general audit-panel gates — they do not replace them. When an audit runs, the panel first scores the standard axes (empirical-rigor, ablation-coverage, dataset-claim-fit, metric-fitness, failure-coverage, ...). Then, if the manuscript's domain has a `references/quality-gates.md`, the auditors additionally score every gate declared there as an advisory axis, emitting findings for any gate that fails its threshold.

## Format

Each domain's `<domain>/references/quality-gates.md` declares its gates as a table:

| Field | Meaning |
|---|---|
| **ID** | Short-name-prefixed identifier, e.g. `TSF-G1`, `GNN-G1`, `VLA-G1`. |
| **Name** | Human-readable name of the failure mode this gate detects. |
| **Panel Expert / Axis** | Which auditor scores it and under what axis label. Typical assignments: `r2-experiments`, `dataset-fitness`, `metric-validity`, `failure-case`. |
| **Threshold** | Numeric cutoff below which a finding must be emitted. Typically 60 for advisory, 40 for blocking. |
| **Rationale** | One-sentence explanation of why this failure mode is domain-critical. |

## Wiring

The following audit-panel agents read `<domain>/references/quality-gates.md` at the start of every audit and inject the declared gates as additional advisory axes on top of their standard axis table:

- `agents/reviewers/r2-experiments.md`
- `agents/validate/dataset-fitness.md`
- `agents/validate/metric-validity.md`
- `agents/analyze/failure-case.md`

If the file is absent (a domain has not yet declared its gates), auditors proceed with the standard axes only. If a gate references a `Panel Expert / Axis` value that names an auditor other than the four above, that auditor is expected to consume it as well.

## Reference: VLA-VLM domain gates

From `vla-vlm/SKILL.md`, the VLA-VLM domain declares (among others):

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| VLA-G1 | Sim-to-real gap | `r2-experiments` / `empirical-rigor` | 60 | A VLA policy evaluated only in simulation without a physical or hardware-in-loop trial is not credible; the sim-real gap is the dominant failure mode. |
| VLA-G2 | Task-generalization split | `dataset-fitness` / `regime-coverage` | 60 | VLA claims must be evaluated on held-out object/scene/skill combinations, not just interpolation within the training distribution. |
| VLM-G1 | Hallucination decomposition | `metric-validity` / `metric-fitness` | 60 | VLM outputs must be scored with a hallucination-vs-error decomposition (e.g., CHAIR, POPE) — bare accuracy hides the systematic-fabrication failure mode. |
| VLM-G2 | Visual-grounding attribution | `failure-case` / `failure-mechanism-hypothesis` | 60 | Every VLM failure mode should be attributable to a specific perceptual or linguistic locus (vision misread vs. language prior), not lumped as "model error". |

## Reference: GNN domain gates (indicative)

A GNN domain declaring `gnn/references/quality-gates.md` would list, for example:

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| GNN-G1 | Heterophily-regime coverage | `dataset-fitness` / `regime-coverage` | 60 | Any claim about heterophilic graphs must include ≥1 dataset with edge-homophily $h<0.3$; homophily-only benchmarks (Cora, Citeseer, Pubmed) do not test the mechanism. |
| GNN-G2 | Scale-vs-oversmoothing evidence | `r2-experiments` / `ablation-coverage` | 60 | Depth claims (`>4` layers) require an oversmoothing diagnostic (Dirichlet energy, feature rank) — accuracy curves alone conflate optimization and representation collapse. |
| GNN-G3 | Anomaly-metric fitness | `metric-validity` / `metric-fitness` | 60 | Anomaly-detection tasks with <5% prevalence must report AUC-PR alongside AUC-ROC; AUC-ROC is uninformative at low base rate. |

## Reference: Time-Series Forecasting (illustrative)

Domains created via `/mr new-domain` inherit this template shape. Example for a hypothetical `tsf`:

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| TSF-G1 | Look-ahead-leak audit | `dataset-fitness` / `preprocessing-honest` | 40 | Any preprocessing that uses statistics computed on the test window (mean/std normalization, differencing) is a look-ahead leak and invalidates the horizon. |
| TSF-G2 | Naive-baseline present | `r2-experiments` / `baseline-strength` | 60 | Every forecasting table must include a Naive / Seasonal-Naive / ARIMA baseline; deep-learning methods that fail to beat these are not publishable. |
| TSF-G3 | Multi-horizon reporting | `metric-validity` / `metric-population-match` | 60 | Claims about horizon $H$ must report metrics separately per horizon; single averaged number hides the short-horizon-dominance effect. |

## How auditors emit domain-gate findings

When an auditor scores a domain gate below its threshold, it must:

1. Emit an axis entry in its JSON verdict with `axis = "<GATE-ID>"` (e.g. `"VLA-G1"`) and `score = <computed>`.
2. Mark the entry `advisory: true` so it does not veto (unless the gate's threshold is 40, in which case treat as blocking).
3. In `evidence`, cite the manuscript locus that triggered the gate (file:line) and the domain's quality-gates.md entry (file:line).

The panel aggregator sums domain-gate advisory findings into the overall report but does not weight them against the standard-axis vetoes.
