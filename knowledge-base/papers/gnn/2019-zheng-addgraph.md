---
type: paper
domain: gnn
title: "AddGraph: Anomaly Detection in Dynamic Graph Using Attention-based Temporal GCN"
authors: "Zheng et al."
year: 2019
venue: "AAAI Conference on Artificial Intelligence"
venue_tier: CCF-A
code_available: true
code_url: "https://github.com/Ljiajie/Addgraph"
code_verified: false
novelty_level: high
validation_quality: moderate
modules: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/temporal/gru-attention-temporal]], [[modules/gnn/anomaly-scorers/deviation-scorer]]
key_contribution: "First method to combine temporal GCN with attention mechanism for dynamic graph anomaly detection, capturing both long-term and short-term patterns"
limitations: ["Requires discrete snapshots", "Assumes homophily", "Limited to edge-level anomalies"]
connections: [[ideas/incubating/heterophily-dygad]]
tags: [dynamic-graph, anomaly-detection, temporal-gcn, attention, edge-anomaly]
created: 2026-06-25
updated: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
external_verified: null  # P3 backfill: pre-migration; run scripts/verify_citations.py + scripts/paper_fetcher.py to set true/false

---

# AddGraph: Anomaly Detection in Dynamic Graph Using Attention-based Temporal GCN

## One-Sentence Synthesis
Pioneered the integration of temporal GCN with attention mechanisms for detecting anomalous edges in dynamic graphs, establishing the spatio-temporal GNN paradigm for anomaly detection.

## Method Summary
Uses a GCN encoder to learn node representations per snapshot, a GRU-based temporal attention module to capture temporal evolution, and a deviation-based anomaly scorer that flags edges whose representations deviate from historical patterns.

## Key Results
- Bitcoin-Alpha: AUC-ROC 0.85
- Bitcoin-OTC: AUC-ROC 0.83
- UCI Messages: AUC-ROC 0.78

## Critical Assessment
Strengths: First method to effectively combine GNN with temporal attention for anomaly detection. Weaknesses: Limited to snapshot-based processing; assumes graph homophily; does not handle continuous-time dynamics; anomaly scoring is simple deviation-based.

## Generated Hypotheses
1. Can the attention mechanism be replaced with a Transformer for better long-range temporal dependency capture? (Addressed by TADDY, 2023)
2. Can the homophily assumption be relaxed for fraud detection scenarios? (Open)