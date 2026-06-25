---
type: module
domain: gnn
category: encoders
name: "GCN-based Graph Encoder"
description: "Standard Graph Convolutional Network (GCN) encoder that learns node representations through neighborhood aggregation. Applies message passing over graph structure to capture local structural patterns. Used as the foundational graph encoder in most spatio-temporal GNN anomaly detection methods."
source_papers: [[papers/gnn/2019-zheng-addgraph]], [[papers/gnn/2023-liu-taddy]]
validation_status: validated
validation_evidence: "Consistently effective across multiple papers. AddGraph (2019) uses 2-layer GCN; TADDY (2023) uses 3-layer GCN. Both demonstrate GCN's necessity through ablation."
composable_with: [[modules/gnn/temporal/gru-attention-temporal]], [[modules/gnn/temporal/transformer-temporal]], [[modules/gnn/anomaly-scorers/deviation-scorer]], [[modules/gnn/encoders/comprehensive-node-encoding]]
incompatible_with: []
assumptions: ["Graph is homophilic (connected nodes share similar properties)", "Graph structure is informative for the task"]
limitations: ["Degrades on heterophilic graphs", "Over-smoothing with deep architectures (>4 layers)"]
connections: [[papers/gnn/2019-zheng-addgraph]], [[papers/gnn/2023-liu-taddy]]
tags: [gcn, graph-encoder, message-passing, node-representation]
created: 2026-06-25
updated: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# GCN-based Graph Encoder

## Function
Learns node representations from graph structure through neighborhood aggregation. Operates per snapshot in dynamic graph settings.

## Design
Input: Node features X, adjacency matrix A. Operations: GCNConv layers with ReLU activation. Output: Node embeddings H. Typical: 2-3 layers, 128-256 hidden dimensions.

## Source Papers
- [[papers/gnn/2019-zheng-addgraph]]: 2-layer GCN. Ablation: removing GCN significantly degrades performance.
- [[papers/gnn/2023-liu-taddy]]: 3-layer GCN with residual connections. Ablation: GCN depth matters; 3 layers optimal.

## Validation Evidence
Two independent papers confirm GCN's effectiveness for graph anomaly detection. Both include ablation studies demonstrating performance degradation when GCN is removed.

## Compatibility
Composable with: temporal modules (GRU, Transformer), anomaly scorers (deviation, reconstruction), loss functions
Incompatible with: None identified

## Assumptions
1. Graph is homophilic: Connected nodes share similar properties. Violated in fraud detection where fraudsters connect to normal users.
2. Graph structure is informative: The graph structure provides signal for the anomaly detection task.

## Limitations
1. Degrades on heterophilic graphs where neighbors have different properties.
2. Over-smoothing: stacking >4 GCN layers causes node representations to become indistinguishable.