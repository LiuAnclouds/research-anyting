---
type: module
domain: gnn
category: encoders
name: "Sequential Feature Extraction"
description: "Extracts features from temporal ego-graph sequences using a sequential encoder (e.g., LSTM, GRU, or Transformer) that processes the temporal dimension of the sampled ego-graphs."
source_papers: [[papers/gnn/2025-xu-generaldyd]]
validation_status: partially-validated
validation_evidence: "GeneralDyG (AAAI 2025) ablation demonstrates the contribution of sequential feature extraction."
composable_with: [[modules/gnn/training-strategies/temporal-ego-graph]]
incompatible_with: []
assumptions: ["Sequential order of ego-graphs captures meaningful temporal evolution"]
limitations: ["Sequential encoder may struggle with irregular time intervals between ego-graphs"]
connections: [[papers/gnn/2025-xu-generaldyd]]
tags: [sequential, feature-extraction, ego-graph, temporal]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Sequential Feature Extraction

## Function
Processes the temporal dimension of sampled ego-graphs to extract discriminative features for anomaly detection.

## Source Papers
- [[papers/gnn/2025-xu-generaldyd]]: Part of the GeneralDyG framework. Processes ego-graph sequences to capture temporal evolution patterns.