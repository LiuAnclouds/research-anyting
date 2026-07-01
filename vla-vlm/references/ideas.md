# VLA/VLM Candidate Research Directions

Working list of research hypotheses for the VLA/VLM domain. Each entry states a **falsifiable** hypothesis, ≥3 anchoring prior works, an expected result, and a target-venue tier. Tiers: **T1** = top ML/robotics venue (NeurIPS/ICML/ICLR/CoRL/RSS); **T2** = strong specialized (CVPR/ICCV/ECCV/ICRA/IROS); **T3** = workshop or arXiv report.

---

### Idea 1 — Continuous action heads dominate discretized tokens above ≥30 Hz control
**Hypothesis (falsifiable).** For end-effector control at rates ≥30 Hz, replacing OpenVLA's 256-bin discretized action head with a continuous flow-matching or Gaussian head yields ≥5pt LIBERO-Long improvement AND ≥2× lower jerk (mean |Δ²action|), holding backbone and data fixed. Falsifier: gap ≤2pt or jerk unchanged.
**Prior work.**
- OpenVLA (Kim et al., 2024) — discretized head baseline.
- π-0 (Physical Intelligence, 2024) — flow-matching action head.
- Diffusion Policy (Chi et al., 2023) — DDPM continuous head.
- OpenVLA-OFT (2025) — continuous head ablation on LIBERO.
**Expected result.** +5-8pt on LIBERO-Long, +3-5pt on LIBERO-Spatial; jerk reduction ~2-3× on real robot.
**Target venue.** CoRL / RSS (T1).

---

### Idea 2 — Cross-embodiment transfer degrades monotonically with morphology-space distance
**Hypothesis (falsifiable).** Zero-shot VLA transfer success on target embodiment E' correlates (Pearson |r| ≥ 0.7) with a scalar morphology-distance metric d(E, E') defined over DoF, workspace volume, and gripper type — computed against training set E. Falsifier: |r| < 0.4 across ≥4 target embodiments.
**Prior work.**
- Open X-Embodiment (Padalkar et al., 2023) — 22-embodiment corpus.
- Octo (2024) — cross-embodiment fine-tuning.
- CEBench (2025) — cross-embodiment eval protocol.
- RT-X (2023) — cross-embodiment training.
**Expected result.** |r| ≈ 0.65-0.80; identifies WidowX↔Franka as easy pair, quadruped↔arm as hard pair.
**Target venue.** CoRL (T1) or ICRA (T2).

---

### Idea 3 — Hallucination decomposition reveals attribute-hallucination as the dominant residual after DPO
**Hypothesis (falsifiable).** After DPO fine-tuning on POPE-style object-existence pairs, ≥60% of remaining hallucinations on HallusionBench are attribute (color, count, spatial-relation) rather than object hallucinations. Falsifier: attribute share <40% in ≥2 of 3 tested VLMs (LLaVA-1.5, Qwen2-VL, InternVL2).
**Prior work.**
- POPE (Li et al., 2023) — object hallucination benchmark.
- HallusionBench (Guan et al., 2024) — decomposed hallucination taxonomy.
- MMHal-Bench (Sun et al., 2023) — severity taxonomy.
- Silkie / RLHF-V (2024) — DPO for VLMs.
**Expected result.** Attribute+relation share 55-70%; object-existence share drops from ~40% pre-DPO to ~15% post-DPO.
**Target venue.** ACL / EMNLP (T2) or CVPR (T2).

---

### Idea 4 — Visual grounding attribution predicts VQA robustness better than accuracy
**Hypothesis (falsifiable).** A VLM's *bbox-grounding IoU* on a probe set (≥500 items with ground-truth referent boxes) correlates more strongly with out-of-distribution VQAv2 accuracy (RealWorldQA transfer) than in-distribution VQAv2 accuracy does. Falsifier: rank correlation of grounding-IoU with OOD < accuracy-with-OOD across ≥6 VLMs.
**Prior work.**
- LLaVA-Grounding / Shikra (2023) — grounded VQA.
- HallusionBench (2024) — visual grounding attribution.
- POPE (2023) — grounding-adjacent probing.
- RealWorldQA (2024) — spatial OOD.
**Expected result.** Grounding-IoU Spearman ρ ≈ 0.7 with OOD; ID-accuracy Spearman ρ ≈ 0.4.
**Target venue.** ICLR / NeurIPS (T1).

---

### Idea 5 — Prompt sensitivity is a proxy for benchmark contamination
**Hypothesis (falsifiable).** VLMs with lower prompt-sensitivity std (across 5 paraphrases) on MMBench have *higher* likelihood of MMBench being in pretraining, measured via canary-token or n-gram overlap check. Prediction: rank correlation ρ ≤ -0.5 between prompt-std and contamination score across ≥8 VLMs. Falsifier: |ρ| < 0.3.
**Prior work.**
- MMBench (Liu et al., 2024) — CircularEval already probes prompt sensitivity.
- Marathi et al. (2024) — LLM contamination detection.
- Sainz et al. (2023) — data contamination survey.
- Dong et al. (2024) — VLM benchmark leakage audit.
**Expected result.** ρ ≈ -0.55; identifies 2-3 VLMs with likely leakage.
**Target venue.** ACL / EMNLP (T2). Provocative → could be T1 with stronger causal design.

---

### Idea 6 — Dual-system VLA (fast policy + slow reasoner) beats monolithic on long-horizon only
**Hypothesis (falsifiable).** Dual-system architectures (ChatVLA-style) match monolithic VLAs (OpenVLA) within ±2pt on LIBERO-Spatial/Object but exceed them by ≥8pt on LIBERO-Long, at ≤2× the parameter budget. Falsifier: dual-system fails to exceed monolithic by ≥5pt on Long, or exceeds on short-horizon suites (indicating gain came from scale, not architecture).
**Prior work.**
- SayCan (Ahn et al., 2022) — hierarchical planner + skill library.
- ChatVLA (2025) — dual-system MoE.
- GR00T N1 (NVIDIA, 2025) — dual-system for humanoids.
- π-0 with high-level planner (2024).
**Expected result.** +8-12pt on Long-suite, ~0-1pt on short suites.
**Target venue.** CoRL / RSS (T1).

---

### Idea 7 — Sim-to-real gap is dominated by observation shift, not dynamics shift
**Hypothesis (falsifiable).** Freezing dynamics-conditioning and only re-training the visual encoder on 100 real-robot images closes ≥70% of the sim-to-real gap for VLA policies pretrained in SimplerEnv/LIBERO. Falsifier: <40% gap closure, or dynamics-only fine-tuning closes ≥50%.
**Prior work.**
- SimplerEnv (Li et al., 2024) — sim-real correlation study.
- Real-to-Sim (Torne et al., 2024) — asset-driven closure.
- OpenVLA sim-real audits (2024).
- Domain randomization (Tobin et al., 2017).
**Expected result.** Vision-only fine-tune closes 60-80% of gap on pick-place; ≤20% on contact-rich (peg-in-hole).
**Target venue.** ICRA / IROS (T2) or CoRL (T1).

---

### Idea 8 — Action-token latency budget forces a Pareto frontier: 7B is not deployable at 30 Hz
**Hypothesis (falsifiable).** On a single A100, the throughput-vs-quality Pareto frontier for open VLAs (OpenVLA-7B, TinyVLA-1B, LLaVA-VLA, SpatialVLA-2B) shows that no model >3B can sustain ≥30 Hz closed-loop control while retaining ≥80% of its offline LIBERO score, without speculative decoding or KV-cache tricks. Falsifier: any 7B model achieves ≥30 Hz + ≥80% score under standard decoding.
**Prior work.**
- OpenVLA-OFT (2025) — parallel decoding for latency.
- TinyVLA (2025) — small-model deployment.
- SpatialVLA (2025) — mid-scale trade-offs.
- π-0 real-time deployment reports.
**Expected result.** 1-3B models sit at knee of Pareto; 7B requires speculative decoding or chunk parallelism.
**Target venue.** ICRA (T2), or NeurIPS Datasets/Systems track (T1) with strong benchmarking.

---

## Prioritization heuristic

For each idea, score on: (a) tractable within 1-GPU-month, (b) hypothesis is genuinely falsifiable, (c) result publishable regardless of sign. Ideas 1, 3, 5, 8 are 1-GPU-month feasible. Ideas 2, 6, 7 need multi-embodiment or real-robot access. Idea 4 needs a curated probe set.
