---
type: module
domain: gnn
category: training-strategies
name: "Self-Supervised Pretraining for Dynamic Graphs"
description: "Pretrains a graph encoder using self-supervised learning on unlabeled dynamic graph data, then fine-tunes on the downstream anomaly detection task. The pretraining objective typically involves predicting masked edges or reconstructing graph structure."
source_papers: [[papers/gnn/2025-xu-generaldyd]]
validation_status: partially-validated
validation_evidence: "GeneralDyG (AAAI 2025) demonstrates that self-supervised pretraining improves generalization across datasets."
composable_with: [[modules/gnn/encoders/gcn-encoder]]
incompatible_with: []
assumptions: ["Unlabeled data is available and representative of the test distribution", "Pretraining objective is well-aligned with the downstream task"]
limitations: ["Requires substantial unlabeled data", "Pretraining adds 2-4x training time"]
connections: [[papers/gnn/2025-xu-generaldyd]]
tags: [self-supervised, pretraining, generalization, transfer-learning]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Self-Supervised Pretraining for Dynamic Graphs

## Function
Improves generalization through self-supervised pretraining on unlabeled dynamic graph data.

## Source Papers
- [[papers/gnn/2025-xu-generaldyd]]: First to apply self-supervised pretraining to dynamic graph anomaly detection.