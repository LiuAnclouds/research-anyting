# GNN Domain Quality Gates

## Preamble

This file declares the **GNN-specific quality gates** that supplement the general audit-panel gates. It follows the format and wiring rules defined in the shared doctrine:

- Shared doctrine: [`shared/references/domain-quality-gates.md`](../../shared/references/domain-quality-gates.md)
- Purpose recap: domain gates ADD to (do not replace) the standard axes scored by `r2-experiments`, `dataset-fitness`, `metric-validity`, and `failure-case`. When an audit runs on a GNN manuscript, each auditor listed under `Panel Expert / Axis` below injects the corresponding gate as an additional advisory axis and emits a finding when the gate fails its threshold.

These gates encode the failure modes that repeatedly bit the GNN-dynamic line of work — heterophily under-coverage, silent over-smoothing, low-prevalence variance, baseline-reimplementation drift, and cross-section scalar disagreement. Each row's rationale links back to the concrete incident that justifies the gate.

## Gates

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| GNN-G1 | Heterophily calibration | `dataset-fitness` / `dataset-claim-fit` | ≥2 datasets with $h \geq 0.6$ | A single heterophilic datapoint (the GNN-dynamic UCI-only case) is insufficient to anchor a heterophily-correlation claim; at least two datasets in the $h \geq 0.6$ regime are required to distinguish trend from coincidence. |
| GNN-G2 | Over-smoothing depth-limit reporting | `metric-validity` / `metric-fitness` | ≥1 depth-vs-metric plot (per-layer variance decay) OR cited bound | Over-smoothing is a depth-triggered failure mode; any paper using $\geq 3$ GCN layers without a per-layer variance-decay plot or a cited theoretical bound is hiding the mechanism's own failure axis. |
| GNN-G3 | Seed variance for AUC-PR at low prevalence | `r2-experiments` / `empirical-rigor` | 5 seeds AND std $\leq 0.03$ | At anomaly-rate $< 10\%$, AUC-ROC is compressed and AUC-PR variance dominates the gap-vs-baseline story; single-seed or 3-seed AUC-PR numbers cannot support a claim of improvement. |
| GNN-G4 | Fair baseline reimplementation footnote | `r2-experiments` / `baseline-fidelity` | footnote present for every reimplementation | TADDY-faithful is not TADDY; when a baseline is reimplemented rather than run from official code, the manuscript must state which components deviated (see `knowledge-base/experts/hallucination-expert/memory.md` seed lesson on baseline-hallucination). |
| GNN-G5 | Cross-section numeric equality for global scalars | `claim-trace-expert` / `cross-section-equality` | 0 disagreements | Any paper-level scalar (single Pearson $r$, single $\lvert \mu_2 \rvert$, single anomaly-rate range) must appear identically in every section that mentions it; the Pearson $r=-0.62$ vs $-0.98$ incident lived in 7 places without any agent diffing it. |

## Wiring notes

- `GNN-G1` is consumed by `agents/validate/dataset-fitness.md` under the `dataset-claim-fit` axis; failure emits a finding citing the manuscript's dataset table and this row.
- `GNN-G2` is consumed by `agents/validate/metric-validity.md` under `metric-fitness`; the auditor scans for depth $\geq 3$ mentions and requires a linked figure or citation.
- `GNN-G3` is consumed by `agents/reviewers/r2-experiments.md` under `empirical-rigor`; auditor extracts anomaly-rate and seed count from the experimental setup.
- `GNN-G4` is also consumed by `agents/reviewers/r2-experiments.md` under a `baseline-fidelity` sub-axis; every reimplemented baseline row in the results table must resolve to a footnote.
- `GNN-G5` names a non-standard expert (`claim-trace-expert`). Per the shared doctrine's "If a gate references a `Panel Expert / Axis` value that names an auditor other than the four above, that auditor is expected to consume it as well," the claim-trace expert (or a delegated diff pass) is responsible for this gate. Absent that expert, the panel aggregator should surface an unassigned-gate warning rather than silently skip.

## Emission format (reminder)

Per the shared doctrine, when an auditor scores a GNN gate below threshold it must:

1. Emit `axis = "GNN-G<n>"` with the computed score in its JSON verdict.
2. Mark `advisory: true` unless the gate is treated as blocking (GNN-G4 and GNN-G5 are blocking — footnote-missing and scalar-disagreement are hard errors, not soft advisories).
3. Cite both the manuscript locus and this file's row (file:line) in `evidence`.
