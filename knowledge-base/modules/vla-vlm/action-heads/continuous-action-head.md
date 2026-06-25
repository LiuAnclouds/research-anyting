---
type: module
domain: vla-vlm
category: action-heads
name: "Continuous Action Head"
description: "Predicts continuous 7-DOF robot actions (x, y, z, roll, pitch, yaw, gripper) from the LLM's output representation. Uses a simple MLP that maps the final hidden state to action coordinates."
source_papers: [[papers/vla-vlm/2024-kim-openvla]]
validation_status: partially-validated
validation_evidence: "OpenVLA (RSS 2024) demonstrates effective continuous action prediction. Limitation: continuous actions may lack precision for fine manipulation tasks."
composable_with: [[modules/vla-vlm/projectors/mlp-projector]]
incompatible_with: []
assumptions: ["Continuous action space adequately represents robot motions", "Action dimensions are independent"]
limitations: ["Lower precision than discrete or diffusion-based action heads", "Does not model action uncertainty"]
connections: [[papers/vla-vlm/2024-kim-openvla]]
tags: [action-head, continuous, vla, 7-dof]
created: 2026-06-25
confidence: medium
source: seed-data
session_ref: seed-data
---

# Continuous Action Head

## Function
Predicts continuous robot actions from the LLM output representation.

## Design
Input: Final hidden state from LLM. Operation: MLP(d_llm → 256 → 7). Output: 7-DOF action (x, y, z, roll, pitch, yaw, gripper).

## Source Papers
- [[papers/vla-vlm/2024-kim-openvla]]: Standard continuous action head in OpenVLA.