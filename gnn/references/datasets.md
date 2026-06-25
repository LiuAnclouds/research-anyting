# GNN DyG-AD Benchmark Datasets

| Dataset | Nodes | Edges | Snapshots | Anomaly% | Domain | Source |
|---------|-------|-------|-----------|----------|--------|--------|
| Bitcoin-Alpha | 3,783 | 24,186 | ~150 | ~5% | Trust network | SNAP |
| Bitcoin-OTC | 5,881 | 35,592 | ~150 | ~5% | Trust network | SNAP |
| UCI Messages | 1,899 | 59,835 | ~200 | ~3% | Communication | NetworkRepository |
| Digg | Medium | Medium | ~200 | ~3% | Social news | — |
| CICIDS2017 | Variable | ~2.8M | Variable | ~20% | Security | UNB |
| CTU-13 | Variable | Variable | Variable | ~5% | Botnet | CTU |
| WikiMath | ~1K | Small | ~50 | ~3% | Collaboration | — |
| LANL-2015 | Large | Large | Variable | ~2% | Internal threat | LANL |
| OpTC | Large | Large | Variable | ~2% | Security | — |
| Elliptic | 203,769 | 234,355 | 49 | ~2% | Financial | Kaggle |
| TON-IoT | Variable | Variable | Variable | Variable | IoT | UNSW |
| ADDKG | Dynamic KG | — | — | ~4% | E-commerce | ISWC 2024 |

## Selection Requirements

- CCF-B minimum: 4-5 datasets from >=3 domains, >=1 exceeding 100K edges.
- CCF-A: 6-8 datasets from >=4 domains, both snapshot and streaming.
- Bitcoin-Alpha, Bitcoin-OTC, or Elliptic must be included as standard benchmarks.
- Security dataset required if method targets security applications.

## Synthetic Anomaly Injection

Types: Structural (edge insertion/deletion, dense subgraph), Temporal (frequency change, pattern disruption), Attributed (feature perturbation), Mixed (combination).
Ratios: 1%, 3%, 5%, 10%. Report breakdown by injection type.
