---
type: module
domain: gnn
category: temporal
name: "Transformer Temporal Module"
description: "Uses self-attention (Transformer) for temporal modeling in dynamic graphs. Unlike GRU-based approaches, the Transformer captures long-range dependencies across all timestamps simultaneously through multi-head self-attention."
source_papers: [[papers/gnn/2023-liu-taddy]]
validation_status: partially-validated
validation_evidence: "TADDY (2023) demonstrates strong performance across 6 datasets. Transformer generally outperforms GRU for temporal modeling in NLP and time series, but no direct comparison exists in the dynamic graph anomaly detection literature."
composable_with: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/encoders/comprehensive-node-encoding]]
incompatible_with: []
assumptions: ["Sufficient temporal context length for self-attention to be meaningful", "Positional encoding adequately captures temporal order"]
limitations: ["O(T^2) complexity in sequence length", "Requires more data than GRU for effective training"]
connections: [[papers/gnn/2023-liu-taddy]]
tags: [transformer, self-attention, temporal-modeling, long-range]
created: 2026-06-25
updated: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Transformer Temporal Module

## Function
Captures long-range temporal dependencies across all snapshots simultaneously. Multi-head self-attention allows each timestamp to attend to all other timestamps directly.

## Design
Input: Sequence of node embeddings with positional encoding. Multi-head self-attention: Q, K, V projections. Feed-forward network. Layer normalization. Output: temporally-aware node representation.

## Source Papers
- [[papers/gnn/2023-liu-taddy]]: First application of Transformer to dynamic graph anomaly detection. Ablation: Transformer outperforms GRU and TCN variants.

## Validation Evidence
Single-paper evidence for dynamic graph anomaly detection specifically. Transformer's superiority over GRU for temporal modeling is well-established in the broader ML literature.

## Compatibility
Composable with: GCN-based graph encoders, comprehensive node encoding, reconstruction-based anomaly scorers
Incompatible with: None identified

## Assumptions
1. Sufficient temporal context: Self-attention benefits from longer sequences.
2. Positional encoding: Must adequately capture temporal order.

## Limitations
1. O(T^2) complexity: Quadratic in sequence length, limiting scalability to very long sequences.
2. Data-hungry: Requires more training data than GRU for effective generalization.