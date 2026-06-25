---
type: experiment
domain: gnn
project: "heterophily-dygad"
status: planned
created: 2026-06-25
tags: [mve, rapid-prototype, heterophily]
connections: [[ideas/incubating/heterophily-dygad]]
source: gnn-rapid-prototype
session_ref: seed-data
---

# Experiment: Heterophily-Aware DyG-AD — MVE

## Hypothesis Tested
"Adding a high-pass filter branch to the GCN encoder achieves >=3% AUC-ROC improvement over TADDY on Bitcoin-Alpha (heterophily ratio >0.3)."

## Configuration
- Dataset: Bitcoin-Alpha
- Model: 2-layer GCN (baseline) vs 2-layer GCN + high-pass filter (ours)
- Baselines: TADDY (strongest baseline)
- Hardware: 1×A100-80GB
- Software: PyTorch 2.0, PyG 2.4
- Random seeds: [42, 123, 456]

## Status
- Planned: 2026-06-25
- Expected completion: 2026-06-27