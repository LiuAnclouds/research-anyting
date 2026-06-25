# VLA Paper Database

## Foundational
- Brohan, A. et al. "RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control." arXiv:2307.15818, 2023. Co-fine-tuned VLM for robot control.
- Brohan, A. et al. "RT-1: Robotics Transformer for Real-World Control at Scale." RSS, 2023.
- Ahn, M. et al. "Do As I Can, Not As I Say: Grounding Language in Robotic Affordances." CoRL, 2022.
- Octo Model Team. "Octo: An Open-Source Generalist Robot Policy." RSS, 2024. 27M-93M params.

## Open-Source (2024-2026)
- Kim, M. J. et al. "OpenVLA: An Open-Source Vision-Language-Action Model." arXiv:2406.09246, 2024. 7B. github.com/openvla/openvla
- OpenVLA-OFT: Optimized fine-tuning, 97.1% LIBERO (2025).
- InstructVLA Team. "InstructVLA." ICLR, 2026. 95.8% LIBERO. github.com/InternRobotics/InstructVLA
- BAAI Vision Team. "UniVLA: Unified Vision-Language-Action Model." ICLR, 2026. github.com/baaivision/UniVLA
- Physical Intelligence. "pi-0: A Generalist Robot Policy." 2024. Flow-matching.
- NVIDIA. "GR00T N1: A Foundation Model for Humanoid Robots." 2025. 1.34B.
- TinyVLA (~1B, 2025), SpatialVLA (2B, 2025), ChatVLA (MoE, 2B, 2025), LLaVA-VLA (consumer GPU, 2025).

## Architecture Taxonomy
1. Monolithic: Single VLM forward pass -> actions (RT-2, OpenVLA).
2. Dual-System: Fast policy + slow reasoning (ChatVLA).
3. Hierarchical: LLM planner -> subtask policies (SayCan).
4. Diffusion/Flow: Iterative denoising (pi-0).

## Benchmarks
LIBERO (130 tasks, 4 suites), CALVIN (34), SimplerEnv (8), RLBench (100), VLABench (100 categories), CEBench (36+8 cross-embodiment).
