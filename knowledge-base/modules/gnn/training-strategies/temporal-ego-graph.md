---
type: module
domain: gnn
category: training-strategies
name: "Temporal Ego-Graph Sampling"
description: "Samples temporal ego-graphs around each node to capture local structural-temporal patterns. Each ego-graph includes the target node, its k-hop neighbors, and the temporal edges connecting them within a time window."
source_papers: [[papers/gnn/2025-xu-generaldyd]]
validation_status: partially-validated
validation_evidence: "GeneralDyG (AAAI 2025) demonstrates strong generalization across datasets. Ablation verifies the contribution of ego-graph sampling."
composable_with: [[modules/gnn/encoders/gcn-encoder]]
incompatible_with: []
assumptions: ["Local neighborhood structure is sufficient to detect anomalies", "Ego-graph radius k is appropriately chosen"]
limitations: ["May miss anomalies that depend on global graph structure", "Sampling is computationally expensive for dense graphs"]
connections: [[papers/gnn/2025-xu-generaldyd]]
tags: [ego-graph, sampling, temporal, generalization]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Temporal Ego-Graph Sampling

## Function
Extracts local temporal subgraphs around each node for efficient and generalizable anomaly detection.

## Source Papers
- [[papers/gnn/2025-xu-generaldyd]]: Introduced as part of the GeneralDyG framework for generalizable dynamic graph anomaly detection.