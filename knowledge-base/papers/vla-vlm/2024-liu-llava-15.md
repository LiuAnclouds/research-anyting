---
type: paper
domain: vla-vlm
title: "LLaVA-1.5: Improved Baselines with Visual Instruction Tuning"
authors: "Liu et al."
year: 2024
venue: "CVPR"
venue_tier: CCF-A
code_available: true
code_url: "https://github.com/haotian-liu/LLaVA"
code_verified: true
novelty_level: medium
validation_quality: strong
modules: [[modules/vla-vlm/visual-encoders/clip-visual-encoder]], [[modules/vla-vlm/projectors/mlp-projector]], [[modules/vla-vlm/training-recipes/visual-instruction-tuning]]
key_contribution: "Established the de facto VLM baseline through systematic improvements to visual instruction tuning with 665K high-quality conversation data"
limitations: ["Fixed 336x336 resolution", "Single visual encoder (CLIP-L)", "English-only"]
connections: []
tags: [vlm, visual-instruction-tuning, multimodal, open-source, llava]
created: 2026-06-25
updated: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# LLaVA-1.5: Improved Baselines with Visual Instruction Tuning

## One-Sentence Synthesis
Systematically improved the LLaVA architecture through better data (665K high-quality conversations), CLIP-ViT-L visual encoder, and MLP projector, establishing the most widely reproduced VLM baseline.

## Method Summary
Uses CLIP-ViT-L/14 as the visual encoder, a 2-layer MLP projector, and Vicuna-7B/13B as the LLM backbone. Two-stage training: stage 1 aligns visual and language representations (projector only), stage 2 fine-tunes for instruction following (projector + LLM).

## Key Results
- MME: 1862 (7B), 1935 (13B)
- MMBench: 68.2 (7B), 71.6 (13B)
- SEED-Bench: 66.7 (7B), 69.5 (13B)

## Critical Assessment
Strengths: Reproducible, well-documented, strong baseline. Weaknesses: Fixed resolution limits OCR and fine-grained perception; CLIP-L visual encoder is not state-of-the-art (InternViT, SigLIP-G are stronger).