---
type: module
domain: gnn
category: encoders
name: "Comprehensive Node Encoding"
description: "Encodes each node with both structural role (via graph embedding) and temporal role (via positional encoding) information. This dual encoding enables the downstream model to distinguish nodes based on both their graph position and their temporal behavior."
source_papers: [[papers/gnn/2023-liu-taddy]]
validation_status: partially-validated
validation_evidence: "TADDY (2023) demonstrates strong performance across 6 datasets. The encoding's contribution is verified through ablation."
composable_with: [[modules/gnn/temporal/transformer-temporal]], [[modules/gnn/encoders/gcn-encoder]]
incompatible_with: []
assumptions: ["Structural role and temporal role are both informative for anomaly detection"]
limitations: ["Increased dimensionality (doubles embedding size)", "May be redundant if the downstream model already captures both roles"]
connections: [[papers/gnn/2023-liu-taddy]]
tags: [node-encoding, structural-role, temporal-role, positional-encoding]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Comprehensive Node Encoding

## Function
Encodes each node with both structural and temporal role information, providing richer input to the downstream temporal encoder.

## Design
Input: Node v at timestamp t. Structural encoding: graph embedding of v's neighborhood. Temporal encoding: positional encoding of t. Output: concatenated [structural_emb || temporal_emb].

## Source Papers
- [[papers/gnn/2023-liu-taddy]]: First to propose comprehensive encoding for dynamic graph anomaly detection. Ablation: removing either structural or temporal encoding degrades performance.