# Research-Anything

> A multi-agent autonomous research framework for Claude Code. From idea to manuscript — one command.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Files](https://img.shields.io/badge/files-175+-green.svg)]()
[![Agents](https://img.shields.io/badge/agents-27-orange.svg)]()
[![Venues](https://img.shields.io/badge/venues-61-purple.svg)]()

## Overview

Research-Anything is a complete autonomous research pipeline built on top of Claude Code's multi-agent architecture. It covers the full research lifecycle across two built-in domains (GNN and VLA-VLM) with support for arbitrary user-created domains.

### What It Does

```
/mr auto "your research topic"
```

One command. Six phases. From zero to submission-ready manuscript:

```
Phase 1: EXPLORE     Phase 2: DESIGN      Phase 3: VALIDATE
Idea Broker ──→     Theory Crafter ──→   Experiment Engineer
Lit Survey           Code Generator        (real-time monitored)
Paper Reader         Hyperparam Opt
Venue Mapping        Rapid Prototype
     │                    │                    │
     ▼                    ▼                    ▼
Phase 4: ANALYZE     Phase 5: WRITE       Phase 6: REVIEW
Insight Analyzer     Paper Writer         Review Simulator
Deep Verification    All sections         EIC + 2 Reviewers
Exp Debugger         Figures + BibTeX     + Devil's Advocate
```

## Installation

```bash
# Clone to Claude Code plugins directory
git clone https://github.com/LiuAnclouds/research-anything.git ~/.claude/plugins/research-anything

# Verify
ls ~/.claude/plugins/research-anything/.claude-plugin/plugin.json
```

Claude Code automatically discovers plugins in `~/.claude/plugins/` by scanning for `.claude-plugin/plugin.json` files.

# Verify
ls ~/.claude/skills/research-anything/mr/SKILL.md
ls ~/.claude/skills/research-anything/gnn/SKILL.md
ls ~/.claude/skills/research-anything/vla-vlm/SKILL.md
```

Claude Code automatically discovers skills by scanning for `SKILL.md` files.

## Quick Start

```bash
# Explore a research direction
/mr gnn idea "dynamic graph anomaly detection"

# Systematic literature survey across 15+ sources
/mr gnn survey "heterophilic GNN 2022-2025"

# Deep read a paper with structured notes
/mr gnn read https://arxiv.org/abs/2406.00134

# One-click autonomous pipeline
/mr auto "heterophily-aware dynamic graph anomaly detection"

# Create your own research domain
/mr new-domain nlp "Natural Language Processing with LLMs"
/mr nlp idea "efficient fine-tuning"
```

## Architecture

```
research-anything/
├── mr/SKILL.md                    # Top-level entry point (/mr)
├── agents/                        # 27 agent definitions
│   ├── gnn-*.md                   # GNN domain-specific (3)
│   ├── vlavlm-*.md                # VLA-VLM domain-specific (3)
│   ├── literature-survey.md       # Shared pipeline agents (6)
│   ├── code-generator.md          # Construction agents (5)
│   ├── moon-pipeline.md           # Autonomous pipeline
│   ├── experiment-monitor.md      # Real-time training monitor
│   └── [support agents]           # Discuss, write, rebuttal, log, present
├── gnn/                           # GNN domain
│   ├── SKILL.md                   # /mr gnn orchestrator
│   └── references/                # Papers, datasets, baselines, ideas
├── vla-vlm/                       # VLA-VLM domain
│   ├── SKILL.md                   # /mr vla-vlm orchestrator
│   └── references/                # Papers, benchmarks, training recipes
├── knowledge-base/                # Persistent memory system
│   ├── KB_SCHEMA.md               # Complete schema specification
│   ├── papers/{gnn,vla-vlm}/      # Paper knowledge graph
│   ├── modules/{gnn,vla-vlm}/     # Reusable method components
│   ├── ideas/{active,incubating,discarded}/  # K-way hypergraph
│   ├── venues/{journals,conferences}/        # CCF venue database (61 entries)
│   ├── sessions/                  # Cross-session memory
│   ├── experiments/               # Experiment records
│   ├── insights/                  # Cross-cutting insights
│   └── cross-links/               # Hypergraph edges
├── shared/references/             # Cross-domain standards
├── templates/                     # Domain + entry scaffolding
├── scripts/                       # Utility scripts (5)
│   ├── paper_fetcher.py           # Multi-source academic search
│   ├── compute_metrics.py         # Standard evaluation metrics
│   ├── statistical_tests.py       # Wilcoxon, Mann-Whitney, effect size
│   ├── plot_results.py            # Publication-quality figures
│   └── kb_check.py                # Knowledge base integrity checker
└── workflows/                     # Workflow scripts (5)
```

## Key Features

### 27 Specialized Agents

| Layer | Agents | Function |
|-------|--------|----------|
| **Exploration** | Idea Broker, Literature Survey, Paper Reader | Find research gaps and generate directions |
| **Construction** | Theory Crafter, Rapid Prototype, Experiment Engineer, Code Generator, Hyperparameter Optimizer | Design and validate methods |
| **Validation** | Insight Analyzer, Deep Verification, Review Simulator, Experiment Debugger | Verify correctness and extract insights |
| **Autonomous** | Moon Pipeline, Experiment Monitor, Literature Alert | End-to-end automation |
| **Support** | Deep Discussion, Paper Writer, Rebuttal Writer, Research Log, Presentation Builder | Cross-cutting tools |

### Paper → Module → Idea Pipeline

Papers are automatically decomposed into reusable methodological modules. Validated modules from different papers are recombined into novel ideas via K-way hypergraph computation. Each idea receives automatic venue recommendation based on contribution strength.

### 61 CCF Venues

Complete database of CCF-A/B/C journals and conferences with submission requirements, review timelines, and domain-specific fit assessments. Automatic venue recommendation based on idea contribution profile.

### Cross-Session Knowledge Persistence

Knowledge base enables agents to share information across independent sessions. `/mr auto-store on` persists deltas after each agent completes. `/mr recall` retrieves context for new sessions.

### Difficulty-Adaptive Workflow

Pipeline calibrates automatically based on target venue tier — CCF-A requires more datasets, baselines, and theoretical analysis than CCF-B or CCF-C.

### Real-Time Experiment Monitoring

Experiment Monitor watches training runs in real-time: detects divergence, NaN, plateau, overfitting; auto-recovers with LR adjustment and gradient clipping; auto-stops hopeless runs.

### Domain Creation

`/mr new-domain` creates complete research domains on the fly. The system researches the field, identifies module categories, maps venues, and generates all scaffolding.

## Command Reference

All commands use the `/mr` prefix. See [COMMANDS.md](COMMANDS.md) for the complete reference.

```
/mr gnn <cmd>              GNN research
/mr vla-vlm <cmd>          VLA-VLM research
/mr auto "topic"           Autonomous full pipeline
/mr search/paper/module    Literature & discovery
/mr ideas/combinations     Idea management
/mr code-gen/hyperopt      Construction
/mr debug/monitor          Debugging
/mr venues/recommend       Venue & submission
/mr write/rebuttal/present Writing
/mr discuss                Academic discussion
/mr store/recall/decompose Knowledge base
/mr new-domain/status      Management
```

## Supported Research Domains

### Built-in

| Domain | Focus | Key Venues |
|--------|-------|------------|
| **GNN** | Dynamic graph anomaly detection, graph representation learning, graph fraud detection | TKDD, TKDE, KDD, AAAI, Neural Networks |
| **VLA-VLM** | Vision-language-action models, embodied AI, multimodal LLMs, visual instruction tuning | CVPR, RSS, CoRL, ICLR, NeurIPS |

### User-Created (via `/mr new-domain`)

Any research field in CS/AI can be scaffolded. The system auto-generates: domain orchestrator, 3 domain-specific agents, KB directories, module categories, venue mapping, and initial reference files.

## Requirements

- Claude Code
- Python 3.8+ (for scripts)
- scipy, scikit-learn, matplotlib (for metrics and plotting)

## Contributing

The system is designed to be extended. Key extension points:

- **New agents**: Add agent definition files in `agents/` with YAML frontmatter
- **New domains**: Use `/mr new-domain` or manually create `domain/SKILL.md`
- **New venues**: Add entries in `knowledge-base/venues/`
- **New workflows**: Add scripts in `workflows/`
- **New templates**: Add templates in `templates/`

## License

MIT