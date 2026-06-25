---
type: paper
domain: vla-vlm
title: "OpenVLA: An Open-Source Vision-Language-Action Model"
authors: "Kim et al."
year: 2024
venue: "Robotics: Science and Systems (RSS)"
venue_tier: CCF-B
code_available: true
code_url: "https://github.com/openvla/openvla"
code_verified: true
novelty_level: high
validation_quality: strong
modules: [[modules/vla-vlm/visual-encoders/siglip-visual-encoder]], [[modules/vla-vlm/projectors/mlp-projector]], [[modules/vla-vlm/action-heads/continuous-action-head]]
key_contribution: "First fully open-source 7B-parameter VLA model achieving competitive performance with proprietary models"
limitations: ["Single embodiment (WidowX)", "Continuous action space only", "7B model requires significant GPU memory"]
connections: []
tags: [vla, open-source, robot-learning, visual-encoder, action-prediction]
created: 2026-06-25
updated: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# OpenVLA: An Open-Source Vision-Language-Action Model

## One-Sentence Synthesis
Established the open-source VLA baseline by combining a Prismatic VLM (SigLIP + LLaMA) with a continuous action head, achieving competitive performance with proprietary models on standard manipulation benchmarks.

## Method Summary
Uses SigLIP as the visual encoder, an MLP projector to map visual tokens to the LLM input space, a LLaMA-7B backbone, and a continuous action head that predicts 7-DOF actions. Trained on the Open X-Embodiment dataset.

## Key Results
- LIBERO-Spatial: 84.7%
- LIBERO-Object: 79.3%
- LIBERO-Goal: 76.1%
- LIBERO-Long: 72.5%

## Critical Assessment
Strengths: Fully open-source; strong baseline; well-documented. Weaknesses: Continuous action space limits precision for fine manipulation; 7B model is heavy for real-time control; single embodiment training limits generalization.