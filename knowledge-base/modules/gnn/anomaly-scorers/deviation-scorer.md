---
type: module
domain: gnn
category: anomaly-scorers
name: "Deviation-Based Anomaly Scorer"
description: "Scores edges as anomalous when their learned representations deviate from a historical normal pattern. The deviation is computed as the distance between the current edge representation and a running average of past representations."
source_papers: [[papers/gnn/2019-zheng-addgraph]]
validation_status: partially-validated
validation_evidence: "AddGraph (2019) demonstrates effectiveness through ablation. No independent reproduction."
composable_with: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/temporal/gru-attention-temporal]]
incompatible_with: []
assumptions: ["Normal patterns are stable over time", "Deviation magnitude correlates with anomaly severity"]
limitations: ["Cannot detect anomalies that conform to historical patterns", "Sensitive to the choice of running average window"]
connections: [[papers/gnn/2019-zheng-addgraph]]
tags: [anomaly-scoring, deviation, edge-anomaly]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Deviation-Based Anomaly Scorer

## Function
Computes anomaly scores by measuring how much an edge's representation deviates from its historical norm. Higher deviation = more anomalous.

## Design
Input: Edge representation h_e. Historical norm: running average μ_e. Score: ||h_e - μ_e||₂. Output: anomaly score s_e ∈ [0, ∞).

## Source Papers
- [[papers/gnn/2019-zheng-addgraph]]: Introduced with GRU temporal module. Ablation: replacing deviation with a simple classifier reduces performance.