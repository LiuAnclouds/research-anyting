---
type: module
domain: vla-vlm
category: visual-encoders
name: "CLIP Visual Encoder"
description: "Uses CLIP (Contrastive Language-Image Pre-training) as the visual encoder for VLM/VLA models. CLIP-ViT-L/14 is the most commonly used variant."
source_papers: [[papers/vla-vlm/2024-liu-llava-15]]
validation_status: validated
validation_evidence: "LLaVA-1.5 (CVPR 2024) and many subsequent VLMs use CLIP-ViT-L. CLIP's effectiveness for visual-language alignment is established across 50+ papers."
composable_with: [[modules/vla-vlm/projectors/mlp-projector]]
incompatible_with: []
assumptions: ["CLIP visual features are aligned with language for downstream tasks"]
limitations: ["Fixed resolution (336x336)", "Less effective than SigLIP or InternViT for fine-grained visual tasks"]
connections: [[papers/vla-vlm/2024-liu-llava-15]]
tags: [clip, visual-encoder, vlm, contrastive]
created: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# CLIP Visual Encoder (VLM)

## Function
Encodes images into visual token representations aligned with the language embedding space.

## Source Papers
- [[papers/vla-vlm/2024-liu-llava-15]]: Uses CLIP-ViT-L/14 as the visual encoder. Ablation: CLIP-ViT-L significantly outperforms smaller CLIP variants.