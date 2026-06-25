---
type: module
domain: gnn
category: encoders
name: "Positional Encoding for Dynamic Graphs"
description: "Encodes temporal position information into node representations. Uses sinusoidal positional encoding adapted from the Transformer architecture to capture the relative temporal order of graph snapshots."
source_papers: [[papers/gnn/2023-liu-taddy]]
validation_status: partially-validated
validation_evidence: "TADDY (2023) demonstrates that positional encoding improves temporal modeling. The Transformer literature provides strong independent evidence for positional encoding effectiveness."
composable_with: [[modules/gnn/temporal/transformer-temporal]]
incompatible_with: []
assumptions: ["Temporal order is meaningful", "Relative temporal distance matters more than absolute time"]
limitations: ["Fixed encoding scheme may not capture domain-specific temporal patterns", "Sinusoidal encoding assumes smooth temporal variation"]
connections: [[papers/gnn/2023-liu-taddy]]
tags: [positional-encoding, temporal, transformer]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Positional Encoding for Dynamic Graphs

## Function
Encodes temporal position into node representations, enabling the Transformer temporal module to distinguish between different timestamps.

## Design
Input: timestamp index t. Encoding: PE(t, 2i) = sin(t / 10000^(2i/d)), PE(t, 2i+1) = cos(t / 10000^(2i/d)). Output: d-dimensional positional encoding vector.

## Source Papers
- [[papers/gnn/2023-liu-taddy]]: Adapted standard Transformer positional encoding for dynamic graph anomaly detection.