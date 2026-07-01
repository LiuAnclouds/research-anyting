# VLA-VLM Baseline Reproduction Guide

## Required Baselines (Must Compare)

### OpenVLA (CoRL 2024)
- Repository: https://github.com/openvla/openvla
- Framework: PyTorch (built on Prismatic-VLM)
- Backbone: Llama-2 7B + DINOv2/SigLIP visual encoders
- Key hyperparameters: image_res=224, action_chunk=1, learning_rate=5e-4 (LoRA), batch_size=16 per GPU
- Data format: RLDS episodes (Open X-Embodiment format), 7-DoF end-effector actions discretized to 256 bins
- Reproduction notes: Official checkpoints on HuggingFace (`openvla/openvla-7b`). Fine-tune with LoRA (rank=32) for single-GPU reproduction; full fine-tune requires 8x A100.
- Known issues: Discretized action head limits precision on high-frequency control. Bfloat16 required for stable inference.

### RT-2 (CoRL 2023)
- Repository: No official code (Google DeepMind, closed-source weights)
- Framework: JAX/T5X (per paper)
- Backbone: PaLI-X 55B or PaLM-E 12B
- Reproduction notes: Not directly reproducible. Use OpenVLA or RT-2-X (open subset in Open X-Embodiment) as a proxy. Report against published numbers when comparing on the same evaluation split.
- Known issues: Closed-weight; comparisons must cite paper numbers.

### Diffusion Policy (RSS 2023)
- Repository: https://github.com/real-stanford/diffusion_policy
- Framework: PyTorch
- Key hyperparameters: horizon=16, n_obs_steps=2, n_action_steps=8, DDIM steps=100, learning_rate=1e-4
- Data format: HDF5 replay buffer with RGB observations + proprioception
- Reproduction notes: Well-maintained. Provides both CNN and Transformer variants. Use `diffusion_policy_cnn` for lower memory; `diffusion_policy_transformer` for long-horizon tasks.
- Known issues: Sensitive to normalization statistics; recompute per-dataset. Slow inference (100 DDIM steps); use DDIM=10 with EMA for real-time deployment.

### LLaVA-1.5 (CVPR 2024)
- Repository: https://github.com/haotian-liu/LLaVA
- Framework: PyTorch + DeepSpeed
- Backbone: Vicuna-7B/13B + CLIP ViT-L/14
- Key hyperparameters: image_res=336, projector=MLP-2, LR=2e-5 (fine-tune), 1 epoch on LLaVA-Instruct-665K
- Data format: JSON conversation format with image tokens
- Reproduction notes: Two-stage training (feature alignment then instruction tuning). Use LLaVA-1.5-13B for strongest baseline; -7B for compute-constrained comparisons.
- Known issues: 336x336 fixed resolution limits fine-grained reasoning. Hallucination on OCR-heavy inputs.

### VLA-Adapter / LLaRA (arXiv 2024)
- Repository: https://github.com/LostXine/LLaRA
- Framework: PyTorch (built on LLaVA)
- Key hyperparameters: LoRA rank=16, learning_rate=2e-4, action_head=discrete
- Reproduction notes: Adapter-based fine-tuning of LLaVA for VLA tasks. Lightweight compared to full VLA fine-tuning.
- Known issues: Depends on base LLaVA checkpoint; results vary with base model version.

### Octo (RSS 2024)
- Repository: https://github.com/octo-models/octo
- Framework: JAX
- Backbone: ViT-S/B + Transformer decoder with diffusion action head
- Key hyperparameters: image_res=256, action_chunk=4, diffusion_steps=20, learning_rate=3e-4
- Data format: RLDS (Open X-Embodiment)
- Reproduction notes: Multi-embodiment pretrained checkpoint. Fine-tune with `octo/scripts/finetune.py`. Good drop-in for cross-embodiment comparisons.
- Known issues: JAX-only; PyTorch port is community-maintained and lags upstream.

### RT-1 (RSS 2023)
- Repository: https://github.com/google-research/robotics_transformer
- Framework: TensorFlow 2 / JAX
- Key hyperparameters: image_res=300, tokens_per_action=8, EfficientNet-B3 backbone
- Reproduction notes: Tokenized action prediction with FiLM conditioning. Google-provided checkpoint. Slower to fine-tune than OpenVLA but simpler architecture.
- Known issues: Discretized 256-bin actions per DoF; TF2 dependencies are dated.

### InstructBLIP (NeurIPS 2023)
- Repository: https://github.com/salesforce/LAVIS/tree/main/projects/instructblip
- Framework: PyTorch (LAVIS)
- Backbone: Q-Former + Vicuna / FlanT5
- Reproduction notes: Instruction-aware Q-Former is the key ingredient. Use as a strong VLM baseline for perception-heavy tasks; not directly a VLA (no action head).

## Additional Baselines (Recommended)

### VLM-Only (perception baselines, no action)
- BLIP-2 (Q-Former, ICML 2023) — https://github.com/salesforce/LAVIS
- MiniGPT-4 — https://github.com/Vision-CAIR/MiniGPT-4
- Qwen-VL / Qwen2-VL — https://github.com/QwenLM/Qwen-VL

### Non-VLA Robot Learning (for ablation: demonstrate language grounding is necessary)
- BC-Z (behavior cloning, no language) — image + proprioception only
- ACT (Action Chunking Transformer, RSS 2023) — https://github.com/tonyzhaozh/act

## Baseline Configuration Protocol

For fair comparison:
1. Use official checkpoints and repositories whenever available. Document any deviations from the released config.
2. Use hyperparameters from the original paper or the repo's default recipe. If tuning is required, use the same tuning budget for all methods.
3. Report on the same evaluation splits (SimplerEnv, LIBERO, Open X-Embodiment held-out, or task-specific real-robot rollouts). Fix random seeds and report mean ± std over >= 3 seeds.
4. Match observation modalities across methods (e.g., if your method uses only RGB, disable depth in comparators that support it, or report both configurations).
5. Report inference latency and parameter count alongside task success — VLA methods have very different compute footprints.
6. Report hardware, framework versions, and driver stack; VLA reproducibility is fragile across CUDA/JAX versions.
