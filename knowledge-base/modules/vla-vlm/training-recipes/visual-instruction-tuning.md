---
type: module
domain: vla-vlm
category: training-recipes
name: "Visual Instruction Tuning"
description: "Two-stage training paradigm for VLMs: Stage 1 aligns visual and language representations (train projector only), Stage 2 fine-tunes for instruction following (train projector + LLM). This is the standard training recipe established by LLaVA."
source_papers: [[papers/vla-vlm/2024-liu-llava-15]]
validation_status: validated
validation_evidence: "LLaVA-1.5 (CVPR 2024) and 30+ subsequent VLMs use this paradigm. Ablation: two-stage training is consistently better than single-stage."
composable_with: [[modules/vla-vlm/visual-encoders/clip-visual-encoder]], [[modules/vla-vlm/projectors/mlp-projector]]
incompatible_with: []
assumptions: ["Sufficient image-caption and instruction data is available"]
limitations: ["Two-stage training doubles the training pipeline complexity", "Stage 1 alignment data quality significantly impacts downstream performance"]
connections: [[papers/vla-vlm/2024-liu-llava-15]]
tags: [instruction-tuning, two-stage, vlm, training-recipe]
created: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# Visual Instruction Tuning

## Function
Standard two-stage training paradigm for vision-language models.

## Design
Stage 1: Train projector only on image-caption pairs (558K samples). Stage 2: Train projector + LLM on multi-turn conversations (665K samples). LR: 1e-3 (Stage 1), 2e-5 (Stage 2).

## Source Papers
- [[papers/vla-vlm/2024-liu-llava-15]]: Established the standard visual instruction tuning recipe.