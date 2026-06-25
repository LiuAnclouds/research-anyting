---
type: paper
domain: gnn
title: "GeneralDyG: A Generalizable Anomaly Detection Method in Dynamic Graphs"
authors: "Xu et al."
year: 2025
venue: "AAAI Conference on Artificial Intelligence"
venue_tier: CCF-A
code_available: true
code_url: "https://github.com/YXNTU/GeneralDyG"
code_verified: true
novelty_level: high
validation_quality: strong
modules: [[modules/gnn/training-strategies/temporal-ego-graph]], [[modules/gnn/training-strategies/self-supervised-pretraining]], [[modules/gnn/encoders/sequential-feature-extraction]]
key_contribution: "Addresses generalization in dynamic graph anomaly detection through temporal ego-graph sampling and self-supervised pretraining"
limitations: ["Still assumes homophily", "Ego-graph sampling may miss global structural anomalies", "Pretraining requires large unlabeled data"]
connections: [[ideas/incubating/heterophily-dygad]]
tags: [dynamic-graph, anomaly-detection, self-supervised, ego-graph, generalization]
created: 2026-06-25
updated: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# GeneralDyG: A Generalizable Anomaly Detection Method in Dynamic Graphs

## One-Sentence Synthesis
Addresses three generalization challenges (data diversity, dynamic feature capture, computational cost) in dynamic graph anomaly detection through temporal ego-graph sampling with self-supervised sequential feature extraction.

## Method Summary
Samples temporal ego-graphs around each node to capture local structural-temporal patterns. Uses self-supervised pretraining to learn generalizable representations. Sequential feature extraction processes the sampled ego-graphs to detect anomalies. Key innovation: the method generalizes across different types of dynamic graphs without domain-specific tuning.

## Key Results
- Bitcoin-Alpha: AUC-ROC 0.93
- Bitcoin-OTC: AUC-ROC 0.91
- Significantly outperforms TADDY on all 4 datasets

## Critical Assessment
Strengths: Addresses generalization systematically; strong SOTA results; well-engineered code. Weaknesses: Still assumes homophily; ego-graph sampling may miss anomalies that manifest as global structural patterns; pretraining requires substantial unlabeled data.