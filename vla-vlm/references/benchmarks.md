# VLA/VLM Benchmark Catalog

## VLA Benchmarks

| Benchmark | Tasks | Metric | Protocol |
|-----------|-------|--------|----------|
| LIBERO-Spatial | 10 | Success% | 20 rollouts/task |
| LIBERO-Object | 10 | Success% | 20 rollouts/task |
| LIBERO-Goal | 10 | Success% | 20 rollouts/task |
| LIBERO-Long | 10 | Success% | 20 rollouts/task |
| CALVIN | 34 | Avg task length | 1000 rollouts |
| SimplerEnv | 8 | Success% | Google Robot + Bridge |
| RLBench | 100 | Success% | 20 rollouts/task |
| VLABench | 100 categories | Success% | Long-horizon reasoning |
| CEBench | 36+8 | Success% | Cross-embodiment |

## VLM Benchmarks

### General Understanding
| Benchmark | Questions | Metric |
|-----------|-----------|--------|
| MME | 2,374 | Accuracy |
| MMBench | 2,974 | Accuracy |
| SEED-Bench | ~19K | Accuracy |
| MM-Vet | 218 | GPT-4 score |
| MMMU | 11.5K | Accuracy |

### Hallucination
POPE (object), HallusionBench (visual), MMHal-Bench.

### Specialized
MathVista, OCRBench, DocVQA, ChartQA, RealWorldQA, ScienceQA.

### Video
EgoSchema, MVBench, Video-MME.

## Protocol Requirements

- VLA: >=20 rollouts/task (LIBERO), >=1000 (CALVIN). Mean +/- std.
- VLM: Single pass. Document exact prompt. Test >=5 prompt variations (std < 2pp).
