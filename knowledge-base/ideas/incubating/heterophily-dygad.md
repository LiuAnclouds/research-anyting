---
type: idea
domain: gnn
status: incubating
hypothesis: "A GNN architecture with explicit heterophily modeling through separate high-frequency and low-frequency signal processing channels achieves >=5% higher AUC-ROC than TADDY on dynamic graphs with heterophily ratio >0.3, while maintaining comparable performance on homophilic graphs (heterophily ratio <0.1)."
derived_from_modules: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/temporal/transformer-temporal]]
derived_from_papers: [[papers/gnn/2019-zheng-addgraph]], [[papers/gnn/2023-liu-taddy]], [[papers/gnn/2025-xu-generaldyd]]
synergy_type: multiplicative
synergy_description: "Existing GCN encoders (from AddGraph, TADDY) assume homophily. None of the existing temporal modules (GRU-attention, Transformer) address heterophily. Combining a heterophily-aware encoder with the Transformer temporal module addresses BOTH graph structure AND temporal dynamics for heterophilic graphs — a combination no existing paper addresses."
novelty_assessment: 5
novelty_justification: "Zero papers address heterophily in dynamic graph anomaly detection. The closest work is in static heterophilic GNN literature (H2GCN, ACM-GNN, etc.), none of which address temporal dynamics or anomaly detection."
feasibility_assessment: 4
feasibility_justification: "Estimated 8-12 researcher-weeks. Requires implementing a dual-channel spectral encoder (high-pass + low-pass) and integrating with the Transformer temporal module. Primary risk: heterophily ratio may not be the dominant factor in anomaly detection performance."
target_venue_tier: CCF-B
target_venues: [[venues/journals/ccf-b/tkdd]], [[venues/journals/ccf-b/neural-networks]]
min_required_validation: "4-5 datasets from >=3 domains, 7+ baselines including AddGraph/StrGNN/TADDY/GeneralDyG, 5 seeds, ablation of heterophily module and temporal module separately"
connections: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/temporal/transformer-temporal]], [[papers/gnn/2019-zheng-addgraph]], [[papers/gnn/2023-liu-taddy]], [[venues/journals/ccf-b/tkdd]]
tags: [heterophily, dynamic-graph, anomaly-detection, gcn, transformer]
created: 2026-06-25
updated: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Heterophily-Aware Dynamic Graph Anomaly Detection

## Hypothesis (Falsifiable)
"A GNN architecture with explicit heterophily modeling through separate high-frequency and low-frequency signal processing channels achieves >=5% higher AUC-ROC than TADDY on dynamic graphs with heterophily ratio >0.3, while maintaining comparable performance on homophilic graphs."

## Module Composition
K = 2 modules combined:
1. [[modules/gnn/encoders/gcn-encoder]] — Modified to be heterophily-aware (dual-channel spectral filtering)
2. [[modules/gnn/temporal/transformer-temporal]] — Captures long-range temporal dependencies

## Why These Modules Together
Existing GCN encoders assume homophily (connected nodes share properties). This assumption is violated in fraud detection where fraudsters connect to normal users. The Transformer temporal module captures long-range temporal patterns. Together, they address both the graph structure problem (heterophily) and the temporal dynamics problem — a combination that no existing paper addresses.

## Novelty Assessment
Score: 5/5
- Closest prior work: Static heterophilic GNN literature (H2GCN, ACM-GNN) — none address temporal dynamics or anomaly detection.
- Has any paper combined these? No.
- The dynamic graph anomaly detection literature universally assumes homophily (verified by systematic survey).

## Feasibility Assessment
Score: 4/5
- Estimated implementation effort: 8-12 researcher-weeks
- Estimated GPU requirements: 200-500 GPU-hours
- Primary risk: Heterophily ratio may not be the dominant factor in anomaly detection performance.
- Mitigation: Start with ablation study on controlled heterophily ratios to verify the effect.

## Recommended Venues
1. [[venues/journals/ccf-b/tkdd]] — Best topic fit for graph mining and anomaly detection.
2. [[venues/journals/ccf-b/neural-networks]] — Good for neural architecture innovation.

## Status History
- 2026-06-25: Created (incubating). Awaiting rapid prototype validation.