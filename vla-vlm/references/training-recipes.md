# VLA/VLM Training Recipes

## VLA Training Recipes

### OpenVLA Fine-tuning
- Base model: OpenVLA-7B (Prismatic VLM + action head)
- Stage 1 (optional): Vision-language alignment on robot-specific images
- Stage 2: Action fine-tuning
  - Trainable: LoRA on LLM backbone (r=32, alpha=64) + action head (full)
  - Learning rate: 2e-5 (LLM), 1e-4 (action head)
  - Batch size: 64 (gradient accumulation over 4 steps if needed)
  - Epochs: 10-20
  - Data: 1K-10K demonstration trajectories
  - Hardware: 4-8×A100-80GB
- Evaluation: 20 rollouts per task on LIBERO suites

### InstructVLA Recipe
- Base model: 1.5B-7B VLM
- Instruction tuning data: 650K VLA-IT annotations
- Learning rate: 2e-5
- Batch size: 128
- Epochs: 1
- Hardware: 8×A100

### RL Fine-tuning (ConRFT/VLAC)
- After supervised fine-tuning, apply RL fine-tuning
- Algorithm: Online RL (PPO) or offline RL
- Reward: Task success (sparse) or progress-based (dense)
- Learning rate: 5e-7 (actor), 1e-6 (critic)
- Rollouts per update: 256
- Hardware: 8×A100 + simulation environment

## VLM Training Recipes

### LLaVA-1.5 Recipe (Reproducible Baseline)
- Stage 1 (Pre-training):
  - Train: Projector only
  - Data: 558K LAION-CC-SBU image-text pairs
  - Learning rate: 1e-3
  - Batch size: 256
  - Epochs: 1
  - Hardware: 8×A100
- Stage 2 (Instruction Tuning):
  - Train: Projector + LLM
  - Data: 665K multi-turn conversations
  - Learning rate: 2e-5
  - Batch size: 128
  - Epochs: 1
  - Hardware: 8×A100

### InternVL2 Recipe (SOTA)
- Stage 1: Visual encoder training (separate, 6B parameters)
- Stage 2: Vision-language alignment
  - Train: Projector only
  - Data: ~1.5B samples
- Stage 3: Instruction tuning
  - Train: Projector + LLM
  - Data: ~5M conversations + QA + OCR + grounding
  - Progressive resolution increase

### LoRA Fine-tuning (Efficient)
- Base model: LLaVA-1.5-7B or Qwen2-VL-7B
- LoRA config: r=16, alpha=32, target_modules=["q_proj", "v_proj", "o_proj"]
- Learning rate: 2e-5
- Batch size: 16 (gradient accumulation over 4 steps)
- Epochs: 1-3
- Data: 1K-10K task-specific examples
- Hardware: 1-2×A100-80GB

### DPO Fine-tuning (Hallucination Reduction)
- After instruction tuning, apply DPO
- Preference pairs: winning response (accurate) vs losing response (hallucinated)
- Beta: 0.1
- Learning rate: 5e-7
- Batch size: 32
- Epochs: 1
- Hardware: 4×A100

## Common Pitfalls

1. **Overfitting**: VLA/VLM models can overfit to small demonstration datasets. Use early stopping based on validation performance.
2. **Catastrophic forgetting**: Fine-tuning on narrow domains can degrade general capabilities. Mix in general data (10-20% of batch) during fine-tuning.
3. **Resolution mismatch**: Ensure input resolution matches the base model's training resolution. Use the same preprocessing pipeline.
4. **Prompt sensitivity**: VLM evaluation is sensitive to prompt format. Document the exact prompt template and test multiple variations.
5. **Hardware requirements**: 7B+ models require significant GPU memory. Use gradient checkpointing, LoRA, and mixed precision (bf16) to reduce memory.