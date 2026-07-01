---
type: paper
domain: gnn
title: "TADDY: Anomaly Detection in Dynamic Graphs via Transformer"
authors: "Liu et al."
year: 2023
venue: "IEEE Transactions on Knowledge and Data Engineering"
venue_tier: CCF-A
code_available: true
code_url: "https://github.com/yuetan031/TADDY_pytorch"
code_verified: true
novelty_level: high
validation_quality: strong
modules: [[modules/gnn/temporal/transformer-temporal]], [[modules/gnn/encoders/positional-encoding]], [[modules/gnn/encoders/comprehensive-node-encoding]]
key_contribution: "First method to apply Transformer architecture to dynamic graph anomaly detection with comprehensive node encoding capturing structural and temporal roles"
limitations: ["Assumes homophily", "Single-scale temporal modeling", "High computational cost for large graphs"]
connections: [[ideas/incubating/heterophily-dygad]]
tags: [dynamic-graph, anomaly-detection, transformer, temporal-encoding, edge-anomaly]
created: 2026-06-25
updated: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
external_verified: null  # P3 backfill: pre-migration; run scripts/verify_citations.py + scripts/paper_fetcher.py to set true/false

---

# TADDY: Anomaly Detection in Dynamic Graphs via Transformer

## One-Sentence Synthesis
Introduced Transformer-based encoding for dynamic graph anomaly detection, achieving state-of-the-art performance through comprehensive node encoding that captures both structural and temporal roles.

## Method Summary
Constructs a comprehensive node encoding strategy that represents each node's structural role (via graph embedding) and temporal role (via positional encoding) in evolving graph streams. A Transformer encoder processes the encoded node representations to capture long-range temporal dependencies. Anomaly scoring is based on reconstruction error.

## Key Results
- Bitcoin-Alpha: AUC-ROC 0.91
- Bitcoin-OTC: AUC-ROC 0.89
- UCI Messages: AUC-ROC 0.85
- Digg: AUC-ROC 0.83
- WikiMath: AUC-ROC 0.81

## Critical Assessment
Strengths: SOTA performance across 6 datasets; comprehensive node encoding; well-documented code. Weaknesses: Single-scale temporal modeling (fixed window size); assumes homophily; high computational cost for large graphs (Transformer complexity).

## Generated Hypotheses
1. Can multi-scale temporal modeling improve detection of anomalies at different time scales? (Open)
2. Can the homophily assumption be relaxed? (Open)