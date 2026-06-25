# VLM Paper Database

## Foundational
- Radford, A. et al. "Learning Transferable Visual Models From Natural Language Supervision." ICML, 2021. CLIP.
- Li, J. et al. "BLIP-2: Bootstrapping Language-Image Pre-training." ICML, 2023. Q-Former.
- Liu, H. et al. "Visual Instruction Tuning." NeurIPS, 2023. LLaVA.
- Liu, H. et al. "Improved Baselines with Visual Instruction Tuning." CVPR, 2024. LLaVA-1.5 (de facto baseline).

## SOTA (2024-2026)
- Liu, H. et al. "LLaVA-NeXT." 2024. AnyRes tiling up to 1344^2.
- Wang, P. et al. "Qwen2-VL." arXiv:2409.12191, 2024. Native dynamic resolution.
- Chen, Z. et al. "InternVL2." 2024. 6B visual encoder.
- DeepSeek-AI. "DeepSeek-VL2." 2025. MoE, 3B/16B/68B.
- Yao, Y. et al. "MiniCPM-V." 2024. 2.4B efficient.
- Abdin, M. et al. "Phi-3 Technical Report." 2024. Phi-3-Vision: 4.2B.

## Efficient VLMs (<4B)
MiniCPM-V (2.4B), Phi-3-Vision (4.2B), Qwen2-VL-2B, InternVL2-1B, DeepSeek-VL2-Tiny (3B).

## Benchmarks
General: MME (2,374Q), MMBench (2,974Q), SEED-Bench (~19KQ), MM-Vet (218Q), MMMU (11.5KQ).
Hallucination: POPE, HallusionBench, MMHal-Bench.
Specialized: MathVista, OCRBench, DocVQA, ChartQA, RealWorldQA.
Video: EgoSchema, MVBench, Video-MME.

## Training Paradigm
1. Vision-language alignment: train projector only; image-caption pairs.
2. Instruction tuning: train projector + LLM; multi-turn conversations.
3. Preference optimization (optional): DPO/RLHF for hallucination reduction.
