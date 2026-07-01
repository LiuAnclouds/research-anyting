# VLA/VLM Consolidated Dataset & Benchmark Catalog

Consolidated dataset registry across VLA (robot manipulation) and VLM (vision-language) sub-domains. See `benchmarks.md` for the original benchmark-scoped table; this file adds licenses, sample counts, and sub-domain tags for triage.

## Table

| Name | Modality | n_samples | License | Sub-domain |
|---|---|---|---|---|
| **LIBERO** | RGB + proprio + language, 4 suites (Spatial/Object/Goal/Long) | 130 tasks × 50 demos = 6,500 demos | MIT | VLA |
| **CALVIN** | RGB-D + proprio + language, 4 environments (A-D) | 34 tasks; ~24h teleop, 20K+ language annotations | MIT | VLA |
| **RT-1 dataset** | RGB + language, Google kitchen scenes | ~130K episodes across 700+ tasks | Apache-2.0 (subset via RT-X) | VLA / robotics-only |
| **RT-2 dataset** | RGB + language + web VQA | Not released | Closed | VLA (proxy: OpenX) |
| **Open X-Embodiment** | RGB(-D) + proprio + language, 22 robot embodiments | 60 datasets, ~1M+ trajectories | Mixed (per-source; mostly CC-BY / Apache-2.0) | VLA / robotics-only |
| **SimplerEnv** | Sim benchmark on Google-Robot + Bridge-V2 | 8 tasks | Apache-2.0 | VLA |
| **RLBench** | Sim, CoppeliaSim | 100 tasks × configurable demos | MIT | VLA / robotics-only |
| **VLABench** | Sim + real, long-horizon reasoning | 100 categories | Apache-2.0 | VLA |
| **CEBench** | Cross-embodiment sim benchmark | 36 base + 8 transfer tasks | Research-use | VLA / robotics-only |
| **BridgeData V2** | Real WidowX teleop | ~60K trajectories | CC-BY-4.0 | VLA / robotics-only |
| **DROID** | Franka teleop, 564 scenes, 76 institutions | 76K trajectories, 350h | CC-BY-4.0 | VLA / robotics-only |
| **VQAv2** | Real-image VQA (COCO) | 265K images / 1.1M QA | CC-BY-4.0 | VLM |
| **GQA** | Compositional VQA over scene graphs | 22M QA over 113K images | CC-BY-4.0 | VLM |
| **MMLU** | Text-only knowledge (57 subjects) | ~15.9K test QA | MIT | VLM (LLM subcomponent) |
| **MMBench** | Multimodal multi-choice, 20 fine-grained abilities | 2,974 questions | Apache-2.0 | VLM |
| **MME** | Perception + cognition subtasks | 2,374 yes/no questions | Research-use | VLM |
| **SEED-Bench** | Comprehensive multimodal (12 dims, image+video) | ~19K questions | CC-BY-4.0 | VLM |
| **MM-Vet** | Integrated capability, GPT-4-scored | 218 open-ended questions | Apache-2.0 | VLM |
| **MMMU** | College-level multimodal reasoning, 30 subjects | 11.5K QA | Apache-2.0 | VLM |
| **POPE** | Object-hallucination polling | ~9K yes/no on COCO/A-OKVQA | MIT | VLM |
| **HallusionBench** | Language hallucination + visual illusion | 1,129 handcrafted QA | BSD-3 | VLM |
| **MMHal-Bench** | GPT-4-scored hallucination severity | 96 QA | Apache-2.0 | VLM |
| **MathVista** | Visual math reasoning | 6,141 QA | CC-BY-SA-4.0 | VLM |
| **OCRBench** | OCR-heavy VQA aggregate | 1,000 questions | Apache-2.0 | VLM |
| **DocVQA** | Document-image VQA | 50K QA over 12K docs | CC-BY-4.0 | VLM |
| **ChartQA** | Chart QA (extractive + reasoning) | 32K QA | GPL-3.0 | VLM |
| **RealWorldQA** | Real-world spatial understanding (X.ai) | 765 QA | CC-BY-ND-4.0 | VLM |
| **ScienceQA** | K-12 science QA with image + text | 21K QA | CC-BY-NC-SA-4.0 | VLM |
| **EgoSchema** | Long-form egocentric video QA | 5K QA over 250h | Ego4D-license | VLM (video) |
| **MVBench** | Video-QA across 20 temporal skills | 4K QA | Apache-2.0 | VLM (video) |
| **Video-MME** | Full-spectrum video eval (short/med/long) | 2,700 QA | CC-BY-NC-4.0 | VLM (video) |
| **ImageNet-1K** | Image classification | 1.28M train / 50K val | Custom (research) | vision-only |
| **COCO** | Detection / captioning | 118K train images / 5 caps ea. | CC-BY-4.0 | vision-only |
| **LAION-CC-SBU-558K** | Web image-caption pairs (LLaVA pretrain) | 558K pairs | CC-BY-4.0 | VLM (pretrain) |
| **LLaVA-Instruct-665K** | GPT-4-generated multimodal instructions | 665K conversations | Apache-2.0 (data) | VLM (instr-tune) |

## Protocol notes

- **VLA rollouts.** LIBERO reports ≥20 rollouts/task; CALVIN reports ≥1000; SimplerEnv typically 25/task. Report mean ± std, not just mean.
- **VLM eval determinism.** Fix decoding (`temperature=0`), document exact prompt templates, and report std over ≥5 prompt paraphrases.
- **License caveats.** Open X-Embodiment is a bundle — verify per-source license before commercial use. RealWorldQA is CC-BY-ND (no derivatives), do not modify questions.
- **Contamination watch.** Web-scraped VLM benchmarks (MME/MMBench items derived from public sources) are at risk of pretraining leakage; state a contamination check per `quality-gates.md#VLM-G4`.
