---
type: index
domain: cross-domain
status: active
created: 2026-06-25
tags: [venues-index]
---

# Venue Index

## By Tier and Category

### CCF-A Journals
| Venue | Domain | IF | Review | Best Fit |
|-------|--------|-----|--------|----------|
| TPAMI | AI/CV | ~20.8 | 6-12mo | Breakthrough methods with exhaustive validation |
| IJCV | CV | ~11.6 | 4-8mo | Computer vision foundations |
| JMLR | ML | ~6.0 | 6-12mo | Theoretical ML contributions |
| AI | AI | ~6.5 | 6-12mo | Fundamental AI research |
| TKDE | DB/DM | ~9.5 | 6-12mo | Data mining with strong experimental evidence |
| TODS | DB | — | 6-12mo | Database systems |
| TOIS | IR | ~4.0 | 6-12mo | Information retrieval |
| VLDBJ | DB | ~3.5 | 6-12mo | Database research |

### CCF-B Journals — Primary Targets
| Venue | Domain | IF | Review | Best Fit |
|-------|--------|-----|--------|----------|
| ACM TKDD | DB/DM | ~3.5 | 6-12mo | Graph mining, anomaly detection |
| Neural Networks | AI | ~6.0 | 4-8mo | Neural architecture innovation |
| Pattern Recognition | AI | ~7.5 | 4-8mo | Method + comprehensive experiments |
| TNNLS | AI | ~10.2 | 6-12mo | Neural networks, learning systems |
| Information Sciences | DB/DM | ~8.1 | 3-6mo | Applied methods, faster review |
| DMKD | DB/DM | ~3.5 | 4-8mo | Pure data mining |
| KAIS | DB/DM | ~3.0 | 4-8mo | Knowledge and information systems |
| Machine Learning | AI | ~4.0 | 4-8mo | Theoretical ML |
| JAIR | AI | ~3.5 | 3-6mo | Open access AI journal |
| CVIU | CV | ~4.0 | 4-8mo | Computer vision understanding |
| IPM | IR | ~7.5 | 3-6mo | Information processing |
| TCYB | AI | ~11.8 | 6-12mo | Cybernetics, AI-control |
| TFS | AI | ~10.7 | 4-8mo | Fuzzy systems |
| TEC | AI | ~11.5 | 6-12mo | Evolutionary computation |

### CCF-C Journals — Fast Publication
| Venue | Domain | IF | Review | Best Fit |
|-------|--------|-----|--------|----------|
| Neurocomputing | AI | ~5.5 | 2-4mo | Fast publication, moderate novelty |
| Applied Intelligence | AI | ~4.0 | 3-6mo | Applied AI methods |
| Neural Processing Letters | AI | ~2.5 | 3-6mo | Short neural network papers |
| Pattern Analysis and Applications | AI | ~3.0 | 4-8mo | Pattern recognition applications |
| Engineering Applications of AI | AI | ~7.5 | 3-6mo | Applied AI in engineering |

### CCF-A Conferences
| Venue | Deadline | Acceptance | Best Fit |
|-------|----------|------------|----------|
| AAAI | Aug | ~20% | Broad AI, GNN work regularly accepted |
| NeurIPS | May | ~25% | ML, favors theoretical novelty |
| ICML | Jan | ~25% | ML theory and methods |
| ICLR | Sep | ~30% | Learning representations, open review |
| KDD | Feb | ~18% | Applied data science, industry relevance |
| WWW | Oct | ~20% | Web, graph mining strong presence |
| IJCAI | Jan | ~15% | Broad AI, lower acceptance |

### CCF-B Conferences
| Venue | Deadline | Acceptance | Best Fit |
|-------|----------|------------|----------|
| CIKM | May | ~25% | Information and knowledge management |
| ICDM | Jun | ~20% | Data mining |
| ECML-PKDD | Mar | ~25% | European ML and data mining |
| SDM | Oct | ~25% | Data mining, SIAM affiliated |

## Venue Recommendation Protocol

Given an idea with assessed contribution strength, the KB Manager recommends venues by:

1. **Filter by tier**: Match the idea's `target_venue_tier` to venue tier.
2. **Filter by domain fit**: Match the idea's tags to venue `topics`.
3. **Filter by requirements**: Check `requires_theory`, `requires_code`, `requires_real_world_validation` against what the idea can provide.
4. **Rank by**: (a) how many `recent_similar_papers` exist (more = better fit), (b) review time preference, (c) impact factor or acceptance rate.

If no venue in the target tier matches, the KB Manager recommends either: (a) strengthen the contribution to meet the target tier, or (b) lower the target tier.
