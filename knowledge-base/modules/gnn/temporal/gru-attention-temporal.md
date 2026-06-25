---
type: module
domain: gnn
category: temporal
name: "GRU Attention Temporal Module"
description: "Combines Gated Recurrent Unit (GRU) with attention mechanism for temporal modeling in dynamic graphs. The GRU captures sequential dependencies across snapshots; the attention mechanism weights the importance of different historical timestamps."
source_papers: [[papers/gnn/2019-zheng-addgraph]]
validation_status: partially-validated
validation_evidence: "AddGraph (2019) demonstrates the module's effectiveness through ablation. No independent paper has reproduced this specific combination."
composable_with: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/anomaly-scorers/deviation-scorer]]
incompatible_with: []
assumptions: ["Data is organized as discrete snapshots", "Temporal dependencies are sequential"]
limitations: ["GRU may struggle with very long sequences (>100 snapshots)", "Attention weights are not interpretable"]
connections: [[papers/gnn/2019-zheng-addgraph]]
tags: [gru, attention, temporal-modeling, sequential]
created: 2026-06-25
updated: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# GRU Attention Temporal Module

## Function
Captures temporal evolution patterns across graph snapshots. The GRU processes sequential node representations; the attention mechanism selectively weights historical information.

## Design
Input: Sequence of node embeddings [h_1, h_2, ..., h_T]. GRU: processes embeddings sequentially. Attention: computes weighted sum of GRU hidden states. Output: temporally-aware node representation.

## Source Papers
- [[papers/gnn/2019-zheng-addgraph]]: Introduced this module. Ablation: removing attention reduces performance; removing GRU reduces performance more.

## Validation Evidence
Single-paper evidence. No independent reproduction of this specific GRU+attention combination for dynamic graph anomaly detection.

## Compatibility
Composable with: GCN-based graph encoders, deviation-based anomaly scorers
Incompatible with: None identified

## Assumptions
1. Discrete snapshots: Data must be organized into fixed-interval snapshots.
2. Sequential dependencies: Temporal patterns follow a sequential (not skip-gram or periodic) structure.

## Limitations
1. GRU struggles with very long sequences (vanishing gradient over >100 steps).
2. Attention weights provide limited interpretability — difficult to explain why a particular timestamp is important.