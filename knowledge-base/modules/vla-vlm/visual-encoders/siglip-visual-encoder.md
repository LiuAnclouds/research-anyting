---
type: module
domain: vla-vlm
category: visual-encoders
name: "SigLIP Visual Encoder"
description: "Uses SigLIP (Sigmoid Loss for Language Image Pre-training) as the visual encoder for VLA models. SigLIP provides strong visual representations with better zero-shot transfer than CLIP."
source_papers: [[papers/vla-vlm/2024-kim-openvla]]
validation_status: partially-validated
validation_evidence: "OpenVLA (RSS 2024) uses SigLIP as the visual encoder. SigLIP's superiority over CLIP is established in the broader VLM literature."
composable_with: [[modules/vla-vlm/projectors/mlp-projector]]
incompatible_with: []
assumptions: ["Visual features from SigLIP are sufficient for robot manipulation tasks"]
limitations: ["SigLIP was trained on web images, not robot egocentric views — domain gap exists"]
connections: [[papers/vla-vlm/2024-kim-openvla]]
tags: [siglip, visual-encoder, vla, zero-shot]
created: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# SigLIP Visual Encoder (VLA)

## Function
Encodes robot camera images into visual token representations for the VLA model.

## Source Papers
- [[papers/vla-vlm/2024-kim-openvla]]: Uses SigLIP as the visual encoder in the OpenVLA architecture.