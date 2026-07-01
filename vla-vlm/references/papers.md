# VLA/VLM Consolidated Paper Database

Consolidated reference of foundational and recent papers across Vision-Language-Action (VLA) and Vision-Language Model (VLM) sub-domains. Grouped by sub-domain, then by year descending. See `papers-vla.md` and `papers-vlm.md` for the domain-scoped originals.

---

## VLA (Vision-Language-Action)

### 2026
- **InstructVLA** — InstructVLA Team (2026, ICLR). Instruction-tuned VLA reaching 95.8% on LIBERO via 650K VLA-IT annotations; unifies instruction-following with action prediction. Code: https://github.com/InternRobotics/InstructVLA
- **UniVLA** — BAAI Vision Team (2026, ICLR). Unified VLA architecture spanning perception, planning, and action across embodiments. Code: https://github.com/baaivision/UniVLA

### 2025
- **OpenVLA-OFT** — Kim, M. J. et al. (2025). Optimized fine-tuning of OpenVLA reaching 97.1% on LIBERO; parallel decoding and continuous action head. Code: https://github.com/moojink/openvla-oft
- **GR00T N1** — NVIDIA (2025). 1.34B foundation model for humanoid robots; dual-system fast/slow architecture. Code: https://github.com/NVIDIA/Isaac-GR00T
- **SpatialVLA** — SpatialVLA Team (2025). 2B VLA with explicit 3D spatial encoding via Ego3D and adaptive action grids. Code: https://github.com/SpatialVLA/SpatialVLA
- **ChatVLA** — ChatVLA Team (2025). Dual-system MoE (2B) separating chat/reasoning from fast policy execution.
- **TinyVLA** — TinyVLA Team (2025). ~1B compact VLA optimized for edge deployment; distilled from larger backbones.
- **LLaVA-VLA** — LLaVA-VLA Team (2025). Consumer-GPU-tier VLA built on LLaVA base; single-GPU fine-tuning.

### 2024
- **OpenVLA** — Kim, M. J. et al. (2024, arXiv:2406.09246). 7B open-source VLA (Prismatic-VLM + discretized action head); reference open baseline. Code: https://github.com/openvla/openvla
- **Octo** — Octo Model Team (2024, RSS). Open-source generalist policy (27M-93M) with diffusion action head, trained on Open X-Embodiment. Code: https://github.com/octo-models/octo
- **π-0 (pi-0)** — Physical Intelligence (2024). Generalist robot policy with flow-matching action decoder for high-frequency control. Code: (partial community releases)

### 2023
- **RT-2** — Brohan, A. et al. (2023, arXiv:2307.15818). Co-fine-tunes PaLI-X/PaLM-E on web + robot data; introduces "VLA" framing. Closed-source.
- **RT-1** — Brohan, A. et al. (2023, RSS). Robotics Transformer with tokenized 7-DoF actions and FiLM conditioning; scale-oriented BC. Code: https://github.com/google-research/robotics_transformer
- **Diffusion Policy** — Chi, C. et al. (2023, RSS). DDPM-based visuomotor policy; strong non-VLA baseline. Code: https://github.com/real-stanford/diffusion_policy
- **ACT** — Zhao, T. et al. (2023, RSS). Action Chunking Transformer for bimanual manipulation; non-language BC baseline. Code: https://github.com/tonyzhaozh/act
- **Open X-Embodiment** — Padalkar, A. et al. (2023, arXiv:2310.08864). Cross-embodiment dataset consortium (22 robots, 60 datasets); RT-X models. Code: https://github.com/google-deepmind/open_x_embodiment

### 2022
- **SayCan (Do As I Can, Not As I Say)** — Ahn, M. et al. (2022, CoRL). LLM-planner + affordance-scored skills; hierarchical VLA precursor.

---

## VLM (Vision-Language Model)

### 2025
- **DeepSeek-VL2** — DeepSeek-AI (2025). MoE VLM at 3B / 16B / 68B active-params tiers with dynamic tiling. Code: https://github.com/deepseek-ai/DeepSeek-VL2

### 2024
- **Qwen2-VL** — Wang, P. et al. (2024, arXiv:2409.12191). Native dynamic-resolution ViT (M-RoPE); strong open VLM at 2B/7B/72B. Code: https://github.com/QwenLM/Qwen2-VL
- **InternVL2** — Chen, Z. et al. (2024). 6B InternViT visual encoder + progressive-resolution instruction tuning. Code: https://github.com/OpenGVLab/InternVL
- **LLaVA-NeXT** — Liu, H. et al. (2024). AnyRes tiling up to 1344² for high-resolution reasoning. Code: https://github.com/LLaVA-VL/LLaVA-NeXT
- **LLaVA-1.5** — Liu, H. et al. (2024, CVPR). MLP projector + academic-scale data recipe; de-facto VLM baseline. Code: https://github.com/haotian-liu/LLaVA
- **MiniCPM-V** — Yao, Y. et al. (2024). 2.4B efficient VLM with strong OCR. Code: https://github.com/OpenBMB/MiniCPM-V
- **Phi-3-Vision** — Abdin, M. et al. (2024). 4.2B vision-capable Phi-3 variant.

### 2023
- **LLaVA (Visual Instruction Tuning)** — Liu, H. et al. (2023, NeurIPS). GPT-4-generated instruction data + linear projector + Vicuna backbone. Code: https://github.com/haotian-liu/LLaVA
- **BLIP-2** — Li, J. et al. (2023, ICML). Q-Former connector between frozen ViT and frozen LLM. Code: https://github.com/salesforce/LAVIS
- **InstructBLIP** — Dai, W. et al. (2023, NeurIPS). Instruction-aware Q-Former; strong perception baseline. Code: https://github.com/salesforce/LAVIS/tree/main/projects/instructblip
- **MiniGPT-4** — Zhu, D. et al. (2023). Frozen ViT + Vicuna with lightweight projector; open-source LLaVA contemporary. Code: https://github.com/Vision-CAIR/MiniGPT-4

### 2022
- **Flamingo** — Alayrac, J.-B. et al. (2022, NeurIPS). Perceiver-Resampler + gated-cross-attention for few-shot VLM; DeepMind, closed-source.
- **BLIP** — Li, J. et al. (2022, ICML). Bootstrapped captioner + filter for noisy web data. Code: https://github.com/salesforce/BLIP

### 2021
- **CLIP** — Radford, A. et al. (2021, ICML). Contrastive image-text pretraining on 400M pairs; foundational visual encoder. Code: https://github.com/openai/CLIP

---

## Notes

- Papers marked "closed-source" reproduce only via community proxies (e.g., RT-2 → OpenVLA, Flamingo → OpenFlamingo).
- LIBERO / SimplerEnv / Open X-Embodiment are the standard evaluation surfaces for the VLA sub-domain (see `datasets.md`).
- VLM benchmarks (MME, MMBench, POPE, ...) are catalogued in `datasets.md`.
