---
type: cross-link
subtype: idea-hyperedge
level: L2
ideas: [[ideas/incubating/heterophily-dygad]], [[ideas/incubating/multiscale-temporal-dygad]]
synergy_type: multiplicative
synergy_description: >
  Heterophily-awareness handles graph structure (high-frequency vs low-frequency signals),
  while multi-scale temporal modeling handles temporal granularity (short vs long windows).
  Together they address both spatial and temporal dimensions of the anomaly detection problem.
  Existing methods address neither dimension — this L2 combination is a coherent research
  direction that no single idea can achieve alone.
estimated_contribution: "0.05-0.08 AUC-ROC improvement over single-contribution methods"
risk: "Low-moderate: both components are independently feasible. The main risk is that the interaction
  between heterophily and temporal scale may introduce unexpected complexity."
validation_status: unvalidated
connections: [[ideas/incubating/heterophily-dygad]], [[ideas/incubating/multiscale-temporal-dygad]]
created: 2026-06-25
source: kb-manager
session_ref: seed-data
---

# Hyperedge L2: Heterophily-Aware + Multi-Scale Temporal DyG-AD

## Why These Two Ideas Together

The heterophily-aware idea addresses the spatial dimension: graph structure where connected nodes may have different properties. The multi-scale idea addresses the temporal dimension: anomalies at different time scales. Together they form a unified framework that addresses both dimensions simultaneously.

## Synergy Mechanism

**Multiplicative**: The two dimensions are orthogonal. Heterophily manifests at different temporal scales (a fraud ring may operate over weeks while individual fraudulent transactions occur in seconds). A method that handles both can detect anomalies that are invisible to methods that handle only one.

## Validation Path

1. First validate each idea independently (Rapid Prototype)
2. Combine and validate the full L2 method
3. Ablation: remove heterophily module → measure degradation; remove multi-scale module → measure degradation
4. Target: 4-5 datasets with varying heterophily ratios and temporal characteristics