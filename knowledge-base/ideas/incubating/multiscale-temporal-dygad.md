---
type: idea
domain: gnn
status: incubating
hypothesis: "A multi-branch temporal encoder with differentiable window selection (Gumbel-Softmax) achieves >=3% higher AUC-ROC than single-scale methods (TADDY, GeneralDyG) on datasets containing anomalies at multiple temporal scales, where the temporal scale mismatch between method and anomaly exceeds 10x."
derived_from_modules: [[modules/gnn/temporal/transformer-temporal]], [[modules/gnn/temporal/gru-attention-temporal]]
derived_from_papers: [[papers/gnn/2023-liu-taddy]]
synergy_type: multiplicative
synergy_description: "The Transformer temporal module captures long-range dependencies; the GRU-attention module captures short-range sequential patterns. Combining them in a multi-branch architecture with differentiable window selection allows the model to automatically determine which temporal scale is most relevant for each node or edge. This addresses a limitation of all existing methods which use a single fixed temporal window."
novelty_assessment: 4
feasibility_assessment: 5
target_venue_tier: CCF-B
target_venues: [[venues/journals/ccf-b/tkdd]], [[venues/journals/ccf-b/pattern-recognition]]
min_required_validation: "4-5 datasets, 7+ baselines, 5 seeds, ablation comparing single-scale vs multi-scale"
connections: [[modules/gnn/temporal/transformer-temporal]], [[modules/gnn/temporal/gru-attention-temporal]], [[papers/gnn/2023-liu-taddy]]
tags: [multi-scale, temporal-modeling, dynamic-graph, anomaly-detection]
created: 2026-06-25
updated: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Multi-Scale Temporal Graph Anomaly Detection

## Hypothesis (Falsifiable)
"A multi-branch temporal encoder with differentiable window selection achieves >=3% higher AUC-ROC than single-scale methods on datasets containing anomalies at multiple temporal scales, where the temporal scale mismatch between method and anomaly exceeds 10x."

## Module Composition
K = 2 modules combined:
1. [[modules/gnn/temporal/transformer-temporal]] — Long-range temporal dependencies
2. [[modules/gnn/temporal/gru-attention-temporal]] — Short-range sequential patterns

## Why These Modules Together
Existing methods use a single fixed temporal window. Anomalies can occur at multiple time scales (seconds for DDoS, days for account takeover, weeks for fraud rings). Combining Transformer (long-range) and GRU-attention (short-range) with differentiable window selection allows the model to adapt to the appropriate temporal scale automatically.

## Recommended Venues
1. [[venues/journals/ccf-b/tkdd]] — Best topic fit
2. [[venues/journals/ccf-b/pattern-recognition]] — Good for comprehensive experimental validation