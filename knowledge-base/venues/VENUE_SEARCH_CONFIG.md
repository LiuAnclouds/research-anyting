# Venue Search Configuration

## Purpose

This file maps each CCF venue to its search endpoint. The literature-survey agent uses this mapping to ensure exhaustive venue coverage: for every topic, ALL relevant venues are explicitly searched. The agent reports which venues were searched and which returned results.

## Search Endpoint Mapping

### CCF-A Conferences

| Conference | Search Domain | API/Query Method |
|-----------|---------------|------------------|
| AAAI | ojs.aaai.org | `WebSearch site:ojs.aaai.org "<topic>"` |
| NeurIPS | papers.nips.cc / openreview.net | `WebSearch site:papers.nips.cc "<topic>"` + OpenReview |
| ICML | proceedings.mlr.press | `WebSearch site:proceedings.mlr.press "<topic>"` |
| ICLR | openreview.net | `WebSearch site:openreview.net "ICLR <topic>"` |
| KDD | dl.acm.org | `WebSearch site:dl.acm.org "KDD <topic>"` |
| WWW | dl.acm.org | `WebSearch site:dl.acm.org "WWW <topic>"` |
| IJCAI | ijcai.org | `WebSearch site:ijcai.org "<topic>"` |
| CVPR | openaccess.thecvf.com | `WebSearch site:openaccess.thecvf.com "CVPR <topic>"` |
| ICCV | openaccess.thecvf.com | `WebSearch site:openaccess.thecvf.com "ICCV <topic>"` |
| ACL | aclanthology.org | `WebSearch site:aclanthology.org "<topic>"` |

### CCF-A Journals

| Journal | Search Domain | API/Query Method |
|---------|---------------|------------------|
| TPAMI | ieeexplore.ieee.org | `WebSearch site:ieeexplore.ieee.org "TPAMI <topic>"` |
| TKDE | ieeexplore.ieee.org | `WebSearch site:ieeexplore.ieee.org "TKDE <topic>"` |
| IJCV | link.springer.com | `WebSearch site:link.springer.com "IJCV <topic>"` |
| JMLR | jmlr.org | `WebSearch site:jmlr.org "<topic>"` |
| AI | sciencedirect.com | `WebSearch site:sciencedirect.com "Artificial Intelligence <topic>"` |
| VLDBJ | link.springer.com | `WebSearch site:link.springer.com "VLDB Journal <topic>"` |
| TODS | dl.acm.org | `WebSearch site:dl.acm.org "TODS <topic>"` |
| TOIS | dl.acm.org | `WebSearch site:dl.acm.org "TOIS <topic>"` |

### CCF-B Conferences

| Conference | Search Domain |
|-----------|---------------|
| CIKM | dl.acm.org |
| ICDM | ieeexplore.ieee.org |
| ECML-PKDD | link.springer.com |
| SDM | epubs.siam.org |
| ECCV | link.springer.com |
| EMNLP | aclanthology.org |
| NAACL | aclanthology.org |
| COLING | aclanthology.org |
| RSS | roboticsproceedings.org |
| CoRL | openreview.net |
| ICRA | ieeexplore.ieee.org |
| RecSys | dl.acm.org |

### CCF-B Journals

| Journal | Search Domain |
|---------|---------------|
| ACM TKDD | dl.acm.org |
| TNNLS | ieeexplore.ieee.org |
| Neural Networks | sciencedirect.com |
| Pattern Recognition | sciencedirect.com |
| Information Sciences | sciencedirect.com |
| DMKD | link.springer.com |
| KAIS | link.springer.com |
| Machine Learning | link.springer.com |
| JAIR | jair.org |
| CVIU | sciencedirect.com |
| TCYB | ieeexplore.ieee.org |
| TFS | ieeexplore.ieee.org |
| TEC | ieeexplore.ieee.org |
| TAC | ieeexplore.ieee.org |
| TASLP | ieeexplore.ieee.org |
| IJAR | sciencedirect.com |
| DKE | sciencedirect.com |
| TWEB | dl.acm.org |
| IPM | sciencedirect.com |
| IS | sciencedirect.com |
| JASIST | Wiley Online |
| JWS | sciencedirect.com |
| Neural Computation | direct.mit.edu |
| Evolutionary Computation | direct.mit.edu |

### CCF-C Venues

| Venue | Search Domain |
|-------|---------------|
| Neurocomputing | sciencedirect.com |
| Applied Intelligence | link.springer.com |
| Neural Processing Letters | link.springer.com |
| EAAI | sciencedirect.com |
| IROS | ieeexplore.ieee.org |
| WACV | openaccess.thecvf.com |

## Search Coverage Protocol

For each literature survey, the agent must:

1. Select all venues from this mapping that are relevant to the topic (based on the domain-venue-mapping in `knowledge-base/insights/domain-venue-mapping.md`).
2. For each selected venue, execute a targeted search using the specified search domain.
3. Record results per venue in the Source Coverage Report.
4. If a venue returns no results, note it — this may indicate the topic is genuinely not published there, or the search query needs refinement.

## Cross-Source Deduplication

After searching all venues, deduplicate papers across sources:
1. Match by DOI (exact match).
2. Match by title (fuzzy match: lowercase, strip punctuation, first 80 chars).
3. When a paper appears in multiple sources, merge metadata: prefer DBLP for venue info, Semantic Scholar for citations, arXiv for preprints.