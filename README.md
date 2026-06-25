# Research-Anything / 科研全流程

> A multi-agent autonomous research framework for Claude Code. From idea to manuscript — one command.
>
> 基于 Claude Code 的多 Agent 自主科研框架。从 Idea 到论文初稿，一条命令。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agents](https://img.shields.io/badge/agents-27-orange.svg)]()

---

[English](#english) | [中文](#中文)

---

## English

### Overview

Research-Anything is a complete autonomous research pipeline built on Claude Code's multi-agent architecture. It covers the full research lifecycle across two built-in domains (GNN and VLA-VLM) with support for arbitrary user-created domains.

**One command. Six phases. From zero to submission-ready manuscript:**

```
/mr auto "your research topic"
```

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

### Supported Agent Platforms

| Platform | Status | Installation |
|----------|--------|-------------|
| **Claude Code** | ✅ Primary | Native skill/plugin discovery |
| **Codex CLI** | ✅ Supported | Manual symlink or copy to `~/.codex/` |
| **Cursor** | ⚠️ Partial | Copy agent definitions; commands via prompt |
| **GitHub Copilot** | ⚠️ Partial | Agent definitions usable as custom instructions |
| **Gemini CLI** | ⚠️ Partial | Manual agent definition import |
| **Aider** | ⚠️ Partial | Agent definitions as context files |

### Installation

#### Claude Code (Recommended)

```bash
# Clone to Claude Code plugins directory
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.claude/plugins/research-anyting

# Verify
ls ~/.claude/plugins/research-anyting/.claude-plugin/plugin.json
ls ~/.claude/plugins/research-anyting/mr/SKILL.md
```

Claude Code automatically discovers plugins in `~/.claude/plugins/` by scanning for `.claude-plugin/plugin.json` files. Restart Claude Code or run `/reload-plugins`.

#### Codex CLI

```bash
# Clone to Codex plugins directory
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.codex/plugins/research-anyting

# Or symlink from Claude Code installation
ln -s ~/.claude/plugins/research-anyting ~/.codex/plugins/research-anyting
```

Trigger commands via `/mr gnn idea "topic"` or by describing the task in natural language.

#### Cursor / Windsurf

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

#### GitHub Copilot

Add agent definitions to Copilot's custom instructions:
```bash
# Copy agent definitions to Copilot workspace
mkdir -p .github/copilot-instructions/
cp ~/.claude/plugins/research-anyting/agents/gnn-idea-broker.md .github/copilot-instructions/
```

#### Manual (Any Agent)

All agent definitions are standalone Markdown files in `agents/`. Copy the relevant agent definition into any LLM agent's context:

```bash
# Example: use the literature survey agent
cat ~/.claude/plugins/research-anyting/agents/literature-survey.md
# Paste into your agent's prompt with the topic appended
```

### Quick Start

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

### Tutorial: From Zero to Paper

#### Step 1: Explore a Direction

```bash
/mr gnn idea "dynamic graph anomaly detection"
```

The Idea Broker generates 3-5 candidate directions with falsifiable hypotheses, novelty assessments, and feasibility estimates. Select the most promising one.

#### Step 2: Survey the Literature

```bash
/mr gnn survey "heterophilic dynamic graph anomaly detection 2022-2025"
```

The Literature Survey agent searches 15+ academic sources (Google Scholar, Semantic Scholar, arXiv, IEEE Xplore, ACM DL, DBLP, OpenReview, etc.) and produces a structured report with taxonomy, leaderboard, and gap analysis.

#### Step 3: Deep Read Key Papers

```bash
/mr gnn read https://arxiv.org/abs/2406.00134
```

The Paper Reader agent executes a three-pass reading protocol, extracting structured notes, critical analysis, and generating falsifiable hypotheses.

#### Step 4: Decompose Papers into Modules

```bash
/mr decompose papers/gnn/2023-liu-taddy
```

The KB Manager extracts reusable methodological components (graph encoder, temporal module, anomaly scorer, etc.) from each paper. If the same module exists from another paper, evidence is merged.

#### Step 5: Discover Module Combinations

```bash
/mr combinations
```

The KB Manager computes K-way (K >= 2) module combinations that satisfy complementarity, compatibility, synergy, and minimality. Valid combinations become incubating ideas.

#### Step 6: Rapid Prototype

```bash
/mr gnn prototype "heterophily-aware encoder with dual-channel spectral filtering"
```

A minimal viable experiment (1-2 days) tests the core hypothesis before committing to full-scale validation. If the MVE fails, the Experiment Debugger diagnoses the root cause.

#### Step 7: Full Experiments

```bash
/mr gnn experiment --monitor
```

The Experiment Engineer runs the complete experimental matrix (5+ datasets, 7+ baselines, 5 seeds). The Experiment Monitor watches training in real-time, auto-detects anomalies, and auto-recovers.

#### Step 8: Analyze and Write

```bash
/mr gnn analyze ./results/
/mr write "introduction" -> "ACM TKDD"
```

The Insight Analyzer extracts causal explanations. The Paper Writer generates manuscript sections compliant with target venue standards.

#### Step 9: Pre-Submission Review

```bash
/mr gnn review ./manuscript.pdf
```

Four independent reviewers (EIC, Reviewer#1 Methodology, Reviewer#2 Experiments, Devil's Advocate) evaluate the manuscript and produce a scored review with actionable revision recommendations.

#### Step 10: Respond to Reviewers

```bash
/mr rebuttal ./reviewer_comments.txt
```

The Rebuttal Writer constructs point-by-point responses with evidence mapping and manuscript change documentation.

#### One-Click Alternative

```bash
/mr auto "heterophily-aware dynamic graph anomaly detection" --target CCF-B
```

Runs all 10 steps autonomously. Add `--human-gates` to require approval at key decision points.

### Architecture

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

### Key Features

#### 27 Specialized Agents

| Layer | Agents | Function |
|-------|--------|----------|
| **Exploration** | Idea Broker, Literature Survey, Paper Reader | Find research gaps and generate directions |
| **Construction** | Theory Crafter, Rapid Prototype, Experiment Engineer, Code Generator, Hyperparameter Optimizer | Design and validate methods |
| **Validation** | Insight Analyzer, Deep Verification, Review Simulator, Experiment Debugger | Verify correctness and extract insights |
| **Autonomous** | Moon Pipeline, Experiment Monitor, Literature Alert, Data Preprocessor | End-to-end automation |
| **Support** | Deep Discussion, Paper Writer, Rebuttal Writer, Research Log, Presentation Builder | Cross-cutting tools |

#### Paper → Module → Idea Pipeline

Papers are decomposed into reusable methodological modules. Validated modules from different papers are recombined into novel ideas via K-way hypergraph computation. Each idea receives automatic venue recommendation.

#### 61 CCF Venues with Automatic Recommendation

Complete database of CCF-A/B/C journals and conferences. `/mr recommend-venue <idea>` automatically matches contribution strength to suitable venues.

#### Cross-Session Knowledge Persistence

`/mr auto-store on` persists deltas after each agent completes. `/mr recall "query"` retrieves context for new sessions.

#### Difficulty-Adaptive Workflow

Pipeline calibrates automatically based on target venue tier — CCF-A requires more datasets, baselines, and theory than CCF-B or CCF-C.

#### Real-Time Experiment Monitoring

Experiment Monitor watches training in real-time: detects divergence, NaN, plateau, overfitting; auto-recovers; auto-stops hopeless runs.

#### Domain Creation on the Fly

`/mr new-domain` creates complete research domains. The system researches the field, identifies module categories, maps venues, and generates all scaffolding.

### Command Reference

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

### Requirements

- Claude Code (primary) or other LLM coding agent
- Python 3.8+ (for scripts)
- scipy, scikit-learn, matplotlib (for metrics and plotting)

### License

MIT

---

## 中文

### 概述

Research-Anything 是一个基于 Claude Code 多 Agent 架构的完整自主科研流水线。覆盖两个内置研究领域（GNN 和 VLA-VLM），并支持用户创建任意新领域。

**一条命令，六个阶段，从零到投稿就绪的论文初稿：**

```
/mr auto "你的研究课题"
```

```
阶段1: 探索      阶段2: 设计       阶段3: 验证
Idea Broker ──→ Theory Crafter ──→ Experiment Engineer
文献调研          代码生成              (实时监控)
论文精读          超参优化
期刊匹配          快速原型验证
    │                  │                  │
    ▼                  ▼                  ▼
阶段4: 分析      阶段5: 写作       阶段6: 审稿
洞察分析         论文撰写           审稿模拟
深度验证         全部章节           主编+2审稿人
实验诊断         图表+BibTeX         +魔鬼代言人
```

### 支持的 Agent 平台

| 平台 | 状态 | 安装方式 |
|------|------|---------|
| **Claude Code** | ✅ 主要平台 | 原生 Skill/Plugin 自动发现 |
| **Codex CLI** | ✅ 支持 | 手动软链接或复制到 `~/.codex/` |
| **Cursor** | ⚠️ 部分支持 | 复制 Agent 定义；通过 prompt 调用 |
| **GitHub Copilot** | ⚠️ 部分支持 | Agent 定义可用作自定义指令 |
| **Gemini CLI** | ⚠️ 部分支持 | 手动导入 Agent 定义 |
| **Aider** | ⚠️ 部分支持 | Agent 定义作为上下文文件 |

### 安装

#### Claude Code（推荐）

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.claude/plugins/research-anyting

# 验证
ls ~/.claude/plugins/research-anyting/.claude-plugin/plugin.json
```

Claude Code 会自动扫描 `~/.claude/plugins/` 目录，发现 `.claude-plugin/plugin.json` 文件后自动加载。重启 Claude Code 或执行 `/reload-plugins`。

#### Codex CLI

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.codex/plugins/research-anyting

# 或从 Claude Code 安装目录软链接
ln -s ~/.claude/plugins/research-anyting ~/.codex/plugins/research-anyting
```

#### Cursor / Windsurf

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/research-anyting
```

在 Cursor 中，将 `agents/` 目录添加为自定义指令，或在 prompt 中引用特定 Agent 定义。`agents/*.md` 是自包含的规范，任何 LLM 编码 Agent 都可以遵循。

使用方式：
```
你现在扮演 research-anyting 中的 GNN Idea Broker。
[粘贴 agents/gnn-idea-broker.md 的内容]
课题：动态图异常检测
```

#### GitHub Copilot

将 Agent 定义添加到 Copilot 的自定义指令中：
```bash
mkdir -p .github/copilot-instructions/
cp ~/.claude/plugins/research-anyting/agents/gnn-idea-broker.md .github/copilot-instructions/
```

#### 手动安装（任意 Agent）

所有 Agent 定义都是独立的 Markdown 文件，复制到任何 LLM Agent 的上下文中即可使用：

```bash
cat ~/.claude/plugins/research-anyting/agents/literature-survey.md
# 将内容粘贴到你的 Agent prompt 中，附上研究课题
```

### 快速开始

```bash
# 探索研究方向
/mr gnn idea "动态图异常检测"

# 系统文献调研（15+数据源）
/mr gnn survey "异配图神经网络 2022-2025"

# 深度论文精读
/mr gnn read https://arxiv.org/abs/2406.00134

# 一键自主全流程
/mr auto "异配性感知的动态图异常检测"

# 创建你的研究领域
/mr new-domain nlp "大语言模型自然语言处理"
/mr nlp idea "高效微调方法"
```

### 使用教程：从零到论文

#### 第一步：探索方向

```bash
/mr gnn idea "动态图异常检测"
```

Idea Broker 生成 3-5 个候选方向，每个方向包含可证伪假设、新颖性评估和可行性估算。选择最有前景的方向。

#### 第二步：系统文献调研

```bash
/mr gnn survey "异配图动态异常检测 2022-2025"
```

Literature Survey Agent 搜索 15+ 学术数据源（Google Scholar、Semantic Scholar、arXiv、IEEE Xplore、ACM DL、DBLP、OpenReview 等），产出包含分类法、性能排行榜和研究空白的结构化报告。

#### 第三步：深度精读关键论文

```bash
/mr gnn read https://arxiv.org/abs/2406.00134
```

Paper Reader Agent 执行三遍精读协议，提取结构化笔记、批判性分析，并生成可证伪的研究假设。

#### 第四步：论文分解为模块

```bash
/mr decompose papers/gnn/2023-liu-taddy
```

KB Manager 从论文中提取可复用的方法组件（图编码器、时序模块、异常评分器等）。如果同一模块在其他论文中已存在，自动合并证据并升级验证状态。

#### 第五步：发现模块组合

```bash
/mr combinations
```

KB Manager 计算 K-way (K >= 2) 模块组合，满足互补性、兼容性、协同性和极小性。有效组合成为孵育中的 Idea。

#### 第六步：快速原型验证

```bash
/mr gnn prototype "双通道谱滤波的异配性感知编码器"
```

最小可行实验（1-2天）在投入完整实验前验证核心假设。如果 MVE 失败，Experiment Debugger 诊断根因。

#### 第七步：完整实验

```bash
/mr gnn experiment --monitor
```

Experiment Engineer 运行完整实验矩阵（5+ 数据集、7+ 基线、5 个随机种子）。Experiment Monitor 实时监控训练，自动检测异常并自动恢复。

#### 第八步：分析与写作

```bash
/mr gnn analyze ./results/
/mr write "introduction" -> "ACM TKDD"
```

Insight Analyzer 提取因果解释。Paper Writer 按目标期刊规范生成论文各节。

#### 第九步：投稿前审稿

```bash
/mr gnn review ./manuscript.pdf
```

四位独立审稿人（主编、方法论审稿人、实验审稿人、魔鬼代言人）评估稿件，产出带分数的审稿报告和可操作的修改建议。

#### 第十步：回复审稿意见

```bash
/mr rebuttal ./reviewer_comments.txt
```

Rebuttal Writer 构建逐条回复，附带证据映射和稿件修改位置标注。

#### 一键替代方案

```bash
/mr auto "异配性感知的动态图异常检测" --target CCF-B
```

自主执行全部 10 步。添加 `--human-gates` 在关键决策点需要人工审批。

### 命令参考

```
/mr gnn <cmd>              GNN 研究
/mr vla-vlm <cmd>          VLA-VLM 研究
/mr auto "topic"           自主全流程
/mr search/paper/module    文献与发现
/mr ideas/combinations     Idea 管理
/mr code-gen/hyperopt      构建
/mr debug/monitor          调试
/mr venues/recommend       期刊与投稿
/mr write/rebuttal/present 写作
/mr discuss                学术讨论
/mr store/recall/decompose 知识库
/mr new-domain/status      管理
```

完整命令参考见 [COMMANDS.md](COMMANDS.md)。

### 环境要求

- Claude Code（主要平台）或其他 LLM 编码 Agent
- Python 3.8+（用于脚本）
- scipy、scikit-learn、matplotlib（用于指标计算和绘图）

### 许可证

MIT