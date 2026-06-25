# Cross-Domain Evaluation Protocols

## Universal Requirements

1. Minimum 5 independent random seeds per experimental condition. Seeds documented.
2. Mean and standard deviation across seeds reported.
3. Wilcoxon signed-rank test for paired comparisons across datasets. Bonferroni correction for multiple comparisons.
4. Chronological data split for temporal data. Random shuffling is a methodological error.
5. Equal hyperparameter tuning budget across all compared methods.
6. Hardware and software: GPU model, CPU, RAM, OS, Python version, framework versions.

## GNN-Specific

**Metrics**: AUC-ROC, AUC-PR (primary); F1, Precision@K, Recall@K (secondary).
**Baselines**: AddGraph, StrGNN, TADDY minimum. Plus 2 recent methods, 1 classic method.
**Datasets**: Minimum 5 from >=3 domains, >=1 exceeding 100K edges.
**Ablation**: Every component individually ablated; GNN-only and temporal-only variants included.

## VLA-Specific

**Metrics**: Task success rate (%), average task length (CALVIN).
**Baselines**: OpenVLA or RT-2-X, Octo, RT-1 minimum.
**Benchmarks**: LIBERO (4 suites), CALVIN, SimplerEnv, RLBench minimum.
**Rollouts**: >=20 per task (LIBERO), >=1000 (CALVIN).
**Generalist claims**: >=3 robot morphologies; sim-to-real gap quantified.
**Latency**: Inference rate reported; real-time >=10 Hz.

## VLM-Specific

**Metrics**: MME, MMBench, SEED-Bench, MM-Vet (minimum 4).
**Hallucination**: POPE and HallusionBench mandatory; decomposed by type.
**Baselines**: LLaVA-1.5-7B, Qwen2-VL-7B, InternVL2-8B minimum.
**Prompt sensitivity**: >=5 variations; std <2 percentage points for stable results.
**Resolution**: Exact input resolution reported; resolution ablation performed.
