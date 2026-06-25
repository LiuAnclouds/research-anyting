# GNN Dynamic Graph Anomaly Detection: Paper Database

## Survey Papers

1. Ekle, O. A. & Eberle, W. "Anomaly Detection in Dynamic Graphs: A Comprehensive Survey." *ACM TKDD*, Vol. 18, No. 8, Article 192, July 2024. 44 pages. DGAD review framework.

2. Qiao, H. et al. "Deep Graph Anomaly Detection: A Survey and New Perspectives." *IEEE TKDE*, Vol. 37, Issue 9, September 2025. 13-category taxonomy.

3. Ma, X. et al. "A Comprehensive Survey on Graph Anomaly Detection with Deep Learning." *IEEE TKDE*, Vol. 35, No. 12, December 2023.

4. Jin, M. et al. "A Survey on Graph Neural Networks for Time Series." *IEEE TPAMI*, Vol. 46, Issue 12, December 2024.

## Classic Baselines (Must Cite)

| Method | Year | Venue | Paradigm | Code |
|--------|------|-------|----------|------|
| AddGraph | 2019 | AAAI | Temporal GCN + Attention | github.com/Ljiajie/Addgraph |
| StrGNN | 2021 | CIKM | Structural-Temporal GNN | github.com/KnowledgeDiscovery/StrGNN |
| TADDY | 2023 | IEEE TKDE | Transformer | github.com/yuetan031/TADDY_pytorch |
| GDN | 2021 | AAAI | Graph Deviation Network | — |
| NetWalk | 2018 | KDD | Dynamic Embedding | — |
| EvolveGCN | 2020 | AAAI | RNN-evolved GCN | github.com/IBM/EvolveGCN |

## Frontier Methods (2024-2025)

| Method | Year | Venue | Paradigm | Key Result |
|--------|------|-------|----------|------------|
| GeneralDyG | 2025 | AAAI | Ego-graph + Self-Supervised | Generalization across 3 challenges |
| GADY | 2024 | Under Review | Continuous-time GNN + GAN | Up to 13.7% AUC improvement |
| RegraphGAN | 2024 | OpenReview | GAN on dynamic graphs | First GAN for dynamic graph AD |
| STEAM | 2025 | Knowl.-Based Syst. | Motif-level | 2.25% AUC improvement |
| DGATE-NAD | 2025 | Comp. Engineering | Graph Embedding + Transformer AE | 98.3% AUC (LANL-2015) |
| DuDi | 2024 | — | Spectral + Local | Dual-range patterns |
| ExpGraph | 2024 | — | Explainable | Prototype alignment |

## Verified Research Gaps

1. **Heterophily in dynamic graphs**: 0 papers.
2. **Multi-scale temporal**: 2 partial papers (DuDi, 2024).
3. **Continuous-discrete unification**: 1 partial paper (GADY, 2024).
4. **Causal graph anomaly detection**: 0 papers.
5. **Foundation model for GAD**: 1 early paper (GeneralDyG, AAAI 2025).
6. **Streaming-efficient expressive GNN**: 2 sketch-based papers.
