# VLA/VLM Domain Quality Gates

This file declares the domain-specific quality gates for the VLA/VLM domain, per the format defined in [`shared/references/domain-quality-gates.md`](../../shared/references/domain-quality-gates.md). Auditors from `agents/reviewers/r2-experiments.md`, `agents/validate/dataset-fitness.md`, `agents/validate/metric-validity.md`, and `agents/analyze/failure-case.md` read these gates at audit-time and add each as an advisory scoring axis atop their standard-axis table. See the shared doctrine for how findings are emitted (`axis = "<GATE-ID>"`, `advisory: true`, evidence loci) and how thresholds work (60 = advisory, 40 = blocking).

## VLA gates

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| **VLA-G1** | Sim-to-real gap ≤15pt (or explanation) | `metric-validity` / `metric-fitness` | 60 | A VLA policy whose real-robot success is >15pt below its simulation number without an explicit gap-analysis section (visual, dynamics, or contact ablation) is not credible for real-world claims; the sim-real gap is the dominant failure mode of the sub-domain. Larger gaps are permitted only when accompanied by a written attribution to specific sources (observation shift vs. dynamics shift vs. contact model). |
| **VLA-G2** | Embodiment diversity ≥3 morphologies | `dataset-fitness` / `dataset-claim-fit` | 60 | Any manuscript claiming a "generalist" or "cross-embodiment" VLA must evaluate on ≥3 robot morphologies differing in DoF, workspace, or gripper type. Single-embodiment "generalist" claims are advisory-flagged; two-embodiment claims are permitted only when the two embodiments span the manipulation/locomotion boundary. |
| **VLA-G3** | Action-token latency reported | `r2-experiments` / `empirical-rigor` | 60 | Every VLA method table must report closed-loop control-rate latency (ms/action or Hz) on the target hardware, alongside parameter count. VLA methods differ 100× in inference latency; success rate without latency is not a fair comparison and prevents deployment reasoning. |
| **VLA-G4** | ≥50 rollouts per task | `r2-experiments` / `empirical-rigor` | 60 | Success-rate claims must be averaged over ≥50 rollouts per task with reported std / seed-count. LIBERO-standard 20 rollouts is the community minimum but insufficient for two-decimal-place claims; short-horizon binomial variance at n=20 exceeds ±10pt at 95% CI. Papers claiming ≤5pt improvements over baselines must use ≥50 rollouts. |

## VLM gates

| ID | Name | Panel Expert / Axis | Threshold | Rationale |
|---|---|---|---|---|
| **VLM-G1** | Hallucination decomposed by type | `failure-case` / `failure-coverage` | 60 | Any VLM manuscript reporting hallucination results must decompose them into ≥4 types: object (POPE-style), attribute (color/count), relation (spatial), and OCR/text. Aggregate hallucination rate hides which failure mode a method actually fixed; a DPO run that reduces object hallucination but leaves attribute hallucination unchanged should not be reported as "hallucination reduction". |
| **VLM-G2** | Prompt sensitivity ≥5 variations, std ≤2pt | `metric-validity` / `metric-fitness` | 60 | VLM benchmarks are extremely prompt-sensitive; single-prompt evaluation numbers are not reproducible. Every headline metric must be reported as mean ± std over ≥5 semantically-equivalent prompt paraphrases, with std ≤2pt for the number to count. Larger stds must be reported and discussed as a limitation (potentially indicative of contamination — see VLM-G4). |
| **VLM-G3** | Visual grounding attribution | `claim-evidence` / `causal-vs-correlational` | 60 | VQA claims that a VLM "sees X" must be substantiated by visual grounding evidence: bounding-box output, attention-map visualization on the referent, or a probe evaluation on a grounding benchmark. Text-only VQA correctness is a correlational claim that a language prior may explain; grounding attribution converts it to a causal one. |
| **VLM-G4** | Benchmark contamination check | `dataset-fitness` / `preprocessing-honest` | 60 | Every VLM manuscript must state, per benchmark, whether the training corpus (pretrain + instruction-tune data) has been checked for the eval benchmark's items. Acceptable checks: n-gram overlap against the eval questions/images, canary-string probing, or an authoritative provenance statement from the base-model release. Absence of the check is a finding. |

## Threshold notes

- All gates default to **advisory (threshold 60)**. Findings are surfaced in the report but do not veto the panel decision.
- Gates may be **escalated to blocking (threshold 40)** on a per-manuscript basis when the manuscript's central contribution is exactly the gate's failure mode. Examples: a paper whose contribution is *sim-to-real robustness* triggers VLA-G1 as blocking; a paper whose contribution is *hallucination reduction* triggers VLM-G1 as blocking.
- Auditors: when scoring, consult both this file and the manuscript's central claim before selecting the threshold.

## Cross-references

- Governance and semantics of the format: [`../../shared/references/domain-quality-gates.md`](../../shared/references/domain-quality-gates.md)
- Evaluation protocol context: [`../../shared/references/evaluation-protocols.md`](../../shared/references/evaluation-protocols.md)
- Benchmark definitions and rollout minima: [`./datasets.md`](./datasets.md), [`./benchmarks.md`](./benchmarks.md)
- Baseline reproduction requirements: [`./baselines.md`](./baselines.md)
