---
type: session
domain: gnn
status: completed
created: 2026-06-25
updated: 2026-06-25
tags: [seed-data, initialization]
connections: [[papers/gnn/2019-zheng-addgraph]], [[papers/gnn/2023-liu-taddy]], [[papers/gnn/2025-xu-generaldyd]], [[ideas/incubating/heterophily-dygad]], [[ideas/incubating/multiscale-temporal-dygad]]
source: seed-data
---

# Session: 2026-06-25 — Moon-Research System Initialization

## Context
Initial setup of the Moon-Research subagent system. Seed data created to populate the knowledge base with foundational papers, modules, and ideas for the GNN dynamic graph anomaly detection domain.

## Key Decisions
1. Seed data scope: 3 papers (AddGraph, TADDY, GeneralDyG) covering the temporal evolution of the field (2019-2025).
2. Module decomposition: 3 modules extracted (GCN encoder, GRU-attention temporal, Transformer temporal). Additional modules (deviation scorer, comprehensive node encoding, ego-graph sampling, self-supervised pretraining, sequential feature extraction) referenced but not yet individually created.
3. Idea generation: 2 incubating ideas (heterophily-aware, multi-scale temporal) derived from module combinations not yet explored by any published paper.
4. Venue targets: ACM TKDD and Neural Networks as primary CCF-B targets.

## Hypotheses Formulated
1. Heterophily-aware GNN for dynamic graph anomaly detection — Status: untested
2. Multi-scale temporal modeling for dynamic graph anomaly detection — Status: untested

## Unresolved Questions
1. What is the actual heterophily ratio of standard benchmark datasets (Bitcoin-Alpha, UCI, etc.)? Needs measurement.
2. Can the heterophily-aware and multi-scale ideas be combined into a single unified framework? (L3 hyperedge potential)
3. Should we target CCF-B journal (TKDD) or CCF-B conference (CIKM) for faster publication?

## Next Session Plan
- [ ] Measure heterophily ratios of standard DyG-AD datasets
- [ ] Run rapid prototype for heterophily-aware idea
- [ ] Decompose remaining papers (StrGNN, GDN, EvolveGCN) into modules
- [ ] Run `/combinations` to recompute the idea hypergraph with all modules