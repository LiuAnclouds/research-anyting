---
type: insight
domain: cross-domain
status: active
created: 2026-06-25
tags: [venue-mapping, domain-routing, submission-strategy]
confidence: high
source: seed-data
session_ref: seed-data
---

# Domain-Venue Mapping: Which Venue for Which Research Direction

## Purpose

Different research directions target different venues. This document maps research domains to their primary, secondary, and fallback publication venues. The KB Manager's `/recommend-venue` operation uses this mapping to prioritize venues based on the research domain.

## GNN — Graph Neural Networks

### Dynamic Graph Anomaly Detection
- **Primary**: ACM TKDD (CCF-B journal), IEEE TKDE (CCF-A journal), KDD (CCF-A conf)
- **Secondary**: Neural Networks (CCF-B journal), Pattern Recognition (CCF-B journal), CIKM (CCF-B conf), ICDM (CCF-B conf)
- **Fallback**: Information Sciences (CCF-B journal), Neurocomputing (CCF-C journal), WWW (CCF-A conf)

### Graph Representation Learning
- **Primary**: ICLR (CCF-A conf), NeurIPS (CCF-A conf), ICML (CCF-A conf)
- **Secondary**: IEEE TPAMI (CCF-A journal), IEEE TNNLS (CCF-B journal), AAAI (CCF-A conf)
- **Fallback**: Neural Networks (CCF-B journal), Machine Learning (CCF-B journal)

### Graph Fraud Detection
- **Primary**: KDD (CCF-A conf), IEEE TKDE (CCF-A journal), AAAI (CCF-A conf)
- **Secondary**: ACM TKDD (CCF-B journal), CIKM (CCF-B conf), ICDM (CCF-B conf)
- **Fallback**: Information Sciences (CCF-B journal), WWW (CCF-A conf)

### Graph Neural Architecture Design
- **Primary**: ICLR (CCF-A conf), NeurIPS (CCF-A conf), IEEE TNNLS (CCF-B journal)
- **Secondary**: Neural Networks (CCF-B journal), ICML (CCF-A conf), AAAI (CCF-A conf)
- **Fallback**: Pattern Recognition (CCF-B journal), Neurocomputing (CCF-C journal)

## VLA — Vision-Language-Action

### VLA Architecture and Training
- **Primary**: RSS (CCF-B conf), CoRL (CCF-B conf), ICLR (CCF-A conf)
- **Secondary**: ICRA (CCF-B conf), NeurIPS (CCF-A conf), ICML (CCF-A conf)
- **Fallback**: IROS (CCF-C conf), AAAI (CCF-A conf)

### Robot Manipulation with VLA
- **Primary**: RSS (CCF-B conf), CoRL (CCF-B conf), ICRA (CCF-B conf)
- **Secondary**: ICLR (CCF-A conf), NeurIPS (CCF-A conf)
- **Fallback**: IROS (CCF-C conf), AAAI (CCF-A conf)

### Sim-to-Real Transfer
- **Primary**: CoRL (CCF-B conf), RSS (CCF-B conf), ICLR (CCF-A conf)
- **Secondary**: ICRA (CCF-B conf), NeurIPS (CCF-A conf)
- **Fallback**: IROS (CCF-C conf)

### Cross-Embodiment VLA
- **Primary**: CoRL (CCF-B conf), ICLR (CCF-A conf), RSS (CCF-B conf)
- **Secondary**: NeurIPS (CCF-A conf), ICML (CCF-A conf)
- **Fallback**: ICRA (CCF-B conf)

## VLM — Vision-Language Models

### VLM Architecture and Training
- **Primary**: CVPR (CCF-A conf), ICCV (CCF-A conf), NeurIPS (CCF-A conf)
- **Secondary**: ECCV (CCF-B conf), ICLR (CCF-A conf), IEEE TPAMI (CCF-A journal)
- **Fallback**: AAAI (CCF-A conf), IJCV (CCF-A journal)

### Visual Instruction Tuning
- **Primary**: CVPR (CCF-A conf), NeurIPS (CCF-A conf), ICLR (CCF-A conf)
- **Secondary**: ICCV (CCF-A conf), ECCV (CCF-B conf), IEEE TPAMI (CCF-A journal)
- **Fallback**: AAAI (CCF-A conf), EMNLP (CCF-B conf)

### Hallucination Reduction
- **Primary**: CVPR (CCF-A conf), NeurIPS (CCF-A conf), ACL (CCF-A conf)
- **Secondary**: ECCV (CCF-B conf), ICLR (CCF-A conf), IEEE TPAMI (CCF-A journal)
- **Fallback**: EMNLP (CCF-B conf), AAAI (CCF-A conf)

### Efficient/Small VLMs
- **Primary**: CVPR (CCF-A conf), ECCV (CCF-B conf), ICLR (CCF-A conf)
- **Secondary**: NeurIPS (CCF-A conf), ICCV (CCF-A conf)
- **Fallback**: AAAI (CCF-A conf), WACV (CCF-C conf)

### VLM for Document/Chart Understanding
- **Primary**: CVPR (CCF-A conf), ICCV (CCF-A conf), ACL (CCF-A conf)
- **Secondary**: ECCV (CCF-B conf), EMNLP (CCF-B conf), IEEE TPAMI (CCF-A journal)
- **Fallback**: AAAI (CCF-A conf), ICDAR (CCF-C conf)

## Cross-Domain (GNN + VLA/VLM)

### Graph-Enhanced Visual Understanding
- **Primary**: CVPR (CCF-A conf), NeurIPS (CCF-A conf), ICLR (CCF-A conf)
- **Secondary**: IEEE TPAMI (CCF-A journal), ICCV (CCF-A conf)
- **Fallback**: AAAI (CCF-A conf), Pattern Recognition (CCF-B journal)

### Graph-Structured Scene Representation for Robotics
- **Primary**: RSS (CCF-B conf), CoRL (CCF-B conf), ICLR (CCF-A conf)
- **Secondary**: ICRA (CCF-B conf), NeurIPS (CCF-A conf)
- **Fallback**: IROS (CCF-C conf), AAAI (CCF-A conf)

## Usage by KB Manager

When `/recommend-venue <idea>` is called, the KB Manager:
1. Reads the idea's tags to determine the research direction.
2. Consults this mapping to identify primary, secondary, and fallback venues.
3. Cross-references with the venue database for tier, requirements, and review time.
4. Returns ranked recommendations with justification.

When a new domain is created via `/new-domain`, the domain-researcher agent identifies relevant venues and adds them to this mapping.

## Auto-Discovery

When no mapping exists for a domain (new domain), the KB Manager falls back to:
1. Matching idea tags against venue topics.
2. Checking which venues have published similar papers (from `recent_similar_papers`).
3. Recommending based on tier match and topic overlap.