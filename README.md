# Research-Anything

> A multi-agent autonomous research framework for Claude Code. From idea to manuscript — one command.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agents](https://img.shields.io/badge/agents-27-orange.svg)]()

[中文文档](README_CN.md)

## Overview

Research-Anything is a complete autonomous research pipeline built on Claude Code's multi-agent architecture. It covers the full research lifecycle across two built-in domains (GNN and VLA-VLM) with support for arbitrary user-created domains.

**One command. Six phases. From zero to submission-ready manuscript:**

```
/mr auto "your research topic"
```

```
Phase 1: EXPLORE      Phase 2: DESIGN        Phase 3: VALIDATE
Idea Broker ────→    Theory Crafter ────→   Experiment Engineer
Literature Survey     Code Generator          (real-time monitored)
Paper Reader          Hyperparam Optimizer
Venue Mapping         Rapid Prototype
     │                      │                      │
     ▼                      ▼                      ▼
Phase 4: ANALYZE      Phase 5: WRITE         Phase 6: REVIEW
Insight Analyzer      Paper Writer           Review Simulator
Deep Verification     All Sections           EIC + 2 Reviewers
Experiment Debugger   Figures + BibTeX       + Devil's Advocate
```

## Supported Agent Platforms

| Platform | Status | Installation |
|----------|--------|-------------|
| **Claude Code** | ✅ Primary | Native skill/plugin discovery |
| **Codex CLI** | ✅ Supported | Manual symlink or copy to `~/.codex/` |
| **Cursor** | ⚠️ Partial | Copy agent definitions; commands via prompt |
| **GitHub Copilot** | ⚠️ Partial | Agent definitions usable as custom instructions |
| **Gemini CLI** | ⚠️ Partial | Manual agent definition import |
| **Aider** | ⚠️ Partial | Agent definitions as context files |

## Installation

### Claude Code (Recommended)

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.claude/plugins/research-anyting

# Verify
ls ~/.claude/plugins/research-anyting/.claude-plugin/plugin.json
ls ~/.claude/plugins/research-anyting/mr/SKILL.md
```

Claude Code automatically discovers plugins in `~/.claude/plugins/` by scanning for `.claude-plugin/plugin.json` files. Restart Claude Code or run `/reload-plugins`.

### Codex CLI

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.codex/plugins/research-anyting

# Or symlink from Claude Code installation
ln -s ~/.claude/plugins/research-anyting ~/.codex/plugins/research-anyting
```

### Cursor / Windsurf

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/research-anyting
```

In Cursor, add the `agents/` directory as custom instructions or reference specific agent definitions in your prompt. The agent definitions in `agents/*.md` are self-contained specifications that any LLM coding agent can follow.

Usage pattern:
```
You are acting as the GNN Idea Broker from research-anyting.
[Paste agents/gnn-idea-broker.md content]
Topic: dynamic graph anomaly detection
```

### GitHub Copilot

Add agent definitions to Copilot's custom instructions:
```bash
mkdir -p .github/copilot-instructions/
cp ~/.claude/plugins/research-anyting/agents/gnn-idea-broker.md .github/copilot-instructions/
```

### Manual (Any Agent)

All agent definitions are standalone Markdown files in `agents/`. Copy the relevant agent definition into any LLM agent's context:

```bash
cat ~/.claude/plugins/research-anyting/agents/literature-survey.md
# Paste into your agent's prompt with the topic appended
```

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

## Tutorial: From Zero to Paper

### Step 1: Explore a Direction

```bash
/mr gnn idea "dynamic graph anomaly detection"
```

The Idea Broker generates 3-5 candidate directions with falsifiable hypotheses, novelty assessments, and feasibility estimates. Select the most promising one.

### Step 2: Survey the Literature

```bash
/mr gnn survey "heterophilic dynamic graph anomaly detection 2022-2025"
```

The Literature Survey agent searches 15+ academic sources (Google Scholar, Semantic Scholar, arXiv, IEEE Xplore, ACM DL, DBLP, OpenReview, etc.) and produces a structured report with taxonomy, leaderboard, and gap analysis.

### Step 3: Deep Read Key Papers

```bash
/mr gnn read https://arxiv.org/abs/2406.00134
```

The Paper Reader agent executes a three-pass reading protocol, extracting structured notes, critical analysis, and generating falsifiable hypotheses.

### Step 4: Decompose Papers into Modules

```bash
/mr decompose papers/gnn/2023-liu-taddy
```

The KB Manager extracts reusable methodological components (graph encoder, temporal module, anomaly scorer, etc.) from each paper. If the same module exists from another paper, evidence is merged.

### Step 5: Discover Module Combinations

```bash
/mr combinations
```

The KB Manager computes K-way (K >= 2) module combinations that satisfy complementarity, compatibility, synergy, and minimality. Valid combinations become incubating ideas.

### Step 6: Rapid Prototype

```bash
/mr gnn prototype "heterophily-aware encoder with dual-channel spectral filtering"
```

A minimal viable experiment (1-2 days) tests the core hypothesis before committing to full-scale validation. If the MVE fails, the Experiment Debugger diagnoses the root cause.

### Step 7: Full Experiments

```bash
/mr gnn experiment --monitor
```

The Experiment Engineer runs the complete experimental matrix (5+ datasets, 7+ baselines, 5 seeds). The Experiment Monitor watches training in real-time, auto-detects anomalies, and auto-recovers.

### Step 8: Analyze and Write

```bash
/mr gnn analyze ./results/
/mr write "introduction" -> "ACM TKDD"
```

The Insight Analyzer extracts causal explanations. The Paper Writer generates manuscript sections compliant with target venue standards.

### Step 9: Pre-Submission Review

```bash
/mr gnn review ./manuscript.pdf
```

Four independent reviewers (EIC, Reviewer#1 Methodology, Reviewer#2 Experiments, Devil's Advocate) evaluate the manuscript and produce a scored review with actionable revision recommendations.

### Step 10: Respond to Reviewers

```bash
/mr rebuttal ./reviewer_comments.txt
```

The Rebuttal Writer constructs point-by-point responses with evidence mapping and manuscript change documentation.

### One-Click Alternative

```bash
/mr auto "heterophily-aware dynamic graph anomaly detection" --target CCF-B
```

Runs all 10 steps autonomously. Add `--human-gates` to require approval at key decision points.

## Architecture

```
research-anyting/
├── .claude-plugin/plugin.json       # Plugin manifest
├── mr/SKILL.md                      # Top-level entry point (/mr)
├── agents/                          # 27 agent definitions
│   ├── gnn-*.md                     # GNN domain-specific (3)
│   ├── vlavlm-*.md                  # VLA-VLM domain-specific (3)
│   ├── literature-survey.md         # Shared pipeline agents (6)
│   ├── code-generator.md            # Construction agents (5)
│   ├── moon-pipeline.md             # Autonomous pipeline
│   ├── experiment-monitor.md        # Real-time training monitor
│   └── [support agents]             # Discuss, write, rebuttal, log, present
├── gnn/                             # GNN domain
│   ├── SKILL.md                     # /mr gnn orchestrator
│   └── references/                  # Papers, datasets, baselines, ideas
├── vla-vlm/                         # VLA-VLM domain
│   ├── SKILL.md                     # /mr vla-vlm orchestrator
│   └── references/                  # Papers, benchmarks, training recipes
├── knowledge-base/                  # Persistent memory system
│   ├── KB_SCHEMA.md
│   ├── papers/{gnn,vla-vlm}/        # Paper knowledge graph
│   ├── modules/{gnn,vla-vlm}/       # Reusable method components
│   ├── ideas/{active,incubating,discarded}/  # K-way hypergraph
│   ├── venues/{journals,conferences}/        # CCF venue database (61 entries)
│   ├── sessions/                    # Cross-session memory
│   ├── experiments/                 # Experiment records
│   └── insights/                    # Cross-cutting insights
├── shared/references/               # Cross-domain standards
├── templates/                       # Domain + entry scaffolding
├── scripts/                         # Utility scripts (5)
└── workflows/                       # Workflow scripts (5)
```

## Key Features

### 27 Specialized Agents

| Layer | Agents | Function |
|-------|--------|----------|
| **Exploration** | Idea Broker, Literature Survey, Paper Reader | Find research gaps and generate directions |
| **Construction** | Theory Crafter, Rapid Prototype, Experiment Engineer, Code Generator, Hyperparameter Optimizer | Design and validate methods |
| **Validation** | Insight Analyzer, Deep Verification, Review Simulator, Experiment Debugger | Verify correctness and extract insights |
| **Autonomous** | Moon Pipeline, Experiment Monitor, Literature Alert, Data Preprocessor | End-to-end automation |
| **Support** | Deep Discussion, Paper Writer, Rebuttal Writer, Research Log, Presentation Builder | Cross-cutting tools |

### Paper → Module → Idea Pipeline

Papers are decomposed into reusable methodological modules. Validated modules from different papers are recombined into novel ideas via K-way hypergraph computation. Each idea receives automatic venue recommendation.

### 61 CCF Venues with Automatic Recommendation

Complete database of CCF-A/B/C journals and conferences. `/mr recommend-venue <idea>` automatically matches contribution strength to suitable venues.

### Cross-Session Knowledge Persistence

`/mr auto-store on` persists deltas after each agent completes. `/mr recall "query"` retrieves context for new sessions.

### Difficulty-Adaptive Workflow

Pipeline calibrates automatically based on target venue tier — CCF-A requires more datasets, baselines, and theory than CCF-B or CCF-C.

### Real-Time Experiment Monitoring

Experiment Monitor watches training in real-time: detects divergence, NaN, plateau, overfitting; auto-recovers; auto-stops hopeless runs.

### Domain Creation on the Fly

`/mr new-domain` creates complete research domains. The system researches the field, identifies module categories, maps venues, and generates all scaffolding.

## Command Reference

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

See [COMMANDS.md](COMMANDS.md) for the complete reference.

## Supported Research Domains

### Built-in

| Domain | Focus | Key Venues |
|--------|-------|------------|
| **GNN** | Dynamic graph anomaly detection, graph representation learning, graph fraud detection | TKDD, TKDE, KDD, AAAI, Neural Networks |
| **VLA-VLM** | Vision-language-action models, embodied AI, multimodal LLMs, visual instruction tuning | CVPR, RSS, CoRL, ICLR, NeurIPS |

### User-Created (via `/mr new-domain`)

Any research field in CS/AI can be scaffolded. The system auto-generates: domain orchestrator, 3 domain-specific agents, KB directories, module categories, venue mapping, and initial reference files.

## Requirements

- Claude Code (primary) or other LLM coding agent
- Python 3.8+ (for scripts)

### Python Dependencies

The scripts in `scripts/` require Python with the following packages:

```bash
# Install dependencies
pip install scikit-learn scipy matplotlib numpy

# If 'pip: command not found', try:
pip3 install scikit-learn scipy matplotlib numpy
# or
python3 -m pip install scikit-learn scipy matplotlib numpy
```

Verify installation:
```bash
python3 -c "import sklearn, scipy, matplotlib, numpy; print('All dependencies OK')"
```

### Troubleshooting

**`pip: command not found`**: Use `pip3` or `python3 -m pip` instead.
**`python3: command not found`** (Windows): Install Python from [python.org](https://www.python.org/downloads/) (NOT the Microsoft Store version). Ensure "Add Python to PATH" is checked during installation.
**`ModuleNotFoundError: No module named 'sklearn'`**: Run `pip install scikit-learn` (note: package name is `scikit-learn`, import name is `sklearn`).
**SSL certificate errors** when fetching papers: Set `MOON_INSECURE_SSL=1` as an environment variable to bypass SSL verification in restricted network environments.

## Contributing

The system is designed to be extended. Key extension points:

- **New agents**: Add agent definition files in `agents/` with YAML frontmatter
- **New domains**: Use `/mr new-domain` or manually create `domain/SKILL.md`
- **New venues**: Add entries in `knowledge-base/venues/`
- **New workflows**: Add scripts in `workflows/`
- **New templates**: Add templates in `templates/`

## License

MIT