---
type: module
domain: vla-vlm
category: projectors
name: "MLP Projector"
description: "A simple 2-layer MLP that projects visual tokens from the visual encoder into the LLM's input embedding space. Despite its simplicity, it is the most commonly used projector in VLM/VLA architectures."
source_papers: [[papers/vla-vlm/2024-kim-openvla]], [[papers/vla-vlm/2024-liu-llava-15]]
validation_status: validated
validation_evidence: "Both OpenVLA and LLaVA-1.5 use MLP projectors. LLaVA-1.5 ablation shows that a 2-layer MLP is sufficient; more complex projectors (Q-Former, Perceiver) provide marginal gains."
composable_with: [[modules/vla-vlm/visual-encoders/siglip-visual-encoder]], [[modules/vla-vlm/visual-encoders/clip-visual-encoder]]
incompatible_with: []
assumptions: ["Linear/non-linear projection is sufficient to align visual and language spaces"]
limitations: ["May not capture complex cross-modal interactions", "Insufficient for tasks requiring fine-grained visual-language alignment"]
connections: [[papers/vla-vlm/2024-kim-openvla]], [[papers/vla-vlm/2024-liu-llava-15]]
tags: [projector, mlp, vlm, vla, multimodal]
created: 2026-06-25
confidence: high
source: seed-data
session_ref: seed-data
---

# MLP Projector

## Function
Projects visual tokens into the LLM input space through a simple 2-layer MLP with GELU activation.

## Design
Input: Visual tokens from visual encoder (N_patches × d_vis). Operation: Linear(d_vis, d_llm) → GELU → Linear(d_llm, d_llm). Output: Projected tokens (N_patches × d_llm).

## Source Papers
- [[papers/vla-vlm/2024-kim-openvla]]: MLP projector in OpenVLA.
- [[papers/vla-vlm/2024-liu-llava-15]]: LLaVA-1.5 ablation shows 2-layer MLP is sufficient.