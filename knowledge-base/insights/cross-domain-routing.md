---
type: insight
domain: cross-domain
status: active
created: 2026-06-25
tags: [cross-domain, methodology, gnn, vla-vlm]
connections: [[ideas/incubating/heterophily-dygad]]
confidence: medium
source: seed-data
session_ref: seed-data
---

# Cross-Domain Module Routing

## Mechanism

The Moon-Research system supports cross-domain idea generation by allowing modules from different domains (GNN and VLA-VLM) to be combined into a single idea. This mechanism is activated when the KB Manager's `/combinations` operation detects that modules from different domains satisfy the hypergraph criteria.

## When Cross-Domain Combinations Are Valid

A cross-domain hyperedge is valid when:

1. **Shared abstraction**: The modules from different domains address the same abstract challenge. For example, the GNN module "heterophily-aware encoder" and the VLM module "contrastive visual grounding" both address the challenge of "learning representations when surface similarity is misleading."

2. **Data modality bridge**: There exists a concrete way to map data between the two domains. For example, VLM visual features can be used as node attributes in a GNN, or GNN graph structures can represent VLM attention patterns.

3. **Joint contribution**: The combination produces a method that neither domain could produce alone. The contribution is not "GNN method + VLM method" but "a new method that uses VLM capabilities to solve a GNN problem, or vice versa."

## Example Cross-Domain Combinations

### GNN + VLM: Graph-Enhanced Visual Anomaly Detection
- GNN modules: [[modules/gnn/encoders/gcn-encoder]], [[modules/gnn/temporal/transformer-temporal]]
- VLM modules: Visual encoder, projector
- Synergy: VLM visual features provide rich node attributes for GNN-based anomaly detection on visual data (e.g., surveillance video anomaly detection as a graph problem).
- Status: Speculative. No existing paper combines these.

### GNN + VLA: Graph-Structured Robot Policy
- GNN modules: GCN encoder, temporal module
- VLA modules: Action head, visual encoder
- Synergy: GNN encodes the spatial relationships between objects in a scene; VLA uses the graph-structured scene representation for action prediction. This explicitly models object relationships that implicit VLA representations may miss.
- Status: Partially explored (scene graphs for robotics exist, but not integrated with VLA foundation models).

## Activation

Cross-domain combinations are automatically evaluated when `/combinations` is run and modules from >=2 domains exist in the KB. The KB Manager flags cross-domain hyperedges with `domain: cross-domain` in the idea entry.

## Limitations

- Cross-domain combinations are inherently speculative. The validation bar is higher: both domains' evaluation protocols must be satisfied.
- Venue recommendation for cross-domain ideas is more complex: the work may not fit neatly into a single community's venues.
- Module compatibility across domains is harder to verify automatically. Cross-domain hyperedges are tagged with `confidence: speculative` by default until experimental evidence is provided.