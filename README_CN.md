# Research-Anything / 科研全流程

> 基于 Claude Code 的多 Agent 自主科研框架。从 Idea 到论文初稿，一条命令。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agents](https://img.shields.io/badge/agents-27-orange.svg)]()

[English Documentation](README.md)

## 概述

Research-Anything 是一个基于 Claude Code 多 Agent 架构的完整自主科研流水线。覆盖两个内置研究领域（GNN 和 VLA-VLM），并支持用户创建任意新领域。

**一条命令，六个阶段，从零到投稿就绪：**

```
/mr auto "你的研究课题"
```

```
阶段 1: 探索        阶段 2: 设计         阶段 3: 验证
Idea Broker ────→  Theory Crafter ────→ Experiment Engineer
文献调研             代码生成                (实时监控)
论文精读             超参优化
期刊匹配             快速原型验证
    │                     │                     │
    ▼                     ▼                     ▼
阶段 4: 分析        阶段 5: 写作         阶段 6: 审稿
洞察分析            论文撰写             审稿模拟
深度验证            全部章节             主编 + 2 审稿人
实验诊断            图表 + BibTeX         + 魔鬼代言人
```

## 支持的 Agent 平台

| 平台 | 状态 | 安装方式 |
|------|------|---------|
| **Claude Code** | ✅ 主要平台 | 原生 Skill/Plugin 自动发现 |
| **Codex CLI** | ✅ 支持 | 手动软链接或复制到 `~/.codex/` |
| **Cursor** | ⚠️ 部分支持 | 复制 Agent 定义；通过 prompt 调用 |
| **GitHub Copilot** | ⚠️ 部分支持 | Agent 定义可用作自定义指令 |
| **Gemini CLI** | ⚠️ 部分支持 | 手动导入 Agent 定义 |
| **Aider** | ⚠️ 部分支持 | Agent 定义作为上下文文件 |

## 安装

### Claude Code（推荐）

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.claude/plugins/research-anyting

# 验证
ls ~/.claude/plugins/research-anyting/.claude-plugin/plugin.json
ls ~/.claude/plugins/research-anyting/mr/SKILL.md
```

Claude Code 会自动扫描 `~/.claude/plugins/` 目录，发现 `.claude-plugin/plugin.json` 文件后自动加载。重启 Claude Code 或执行 `/reload-plugins`。

### Codex CLI

```bash
git clone https://github.com/LiuAnclouds/research-anyting.git ~/.codex/plugins/research-anyting

# 或从 Claude Code 安装目录软链接
ln -s ~/.claude/plugins/research-anyting ~/.codex/plugins/research-anyting
```

### Cursor / Windsurf

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

### GitHub Copilot

将 Agent 定义添加到 Copilot 的自定义指令中：
```bash
mkdir -p .github/copilot-instructions/
cp ~/.claude/plugins/research-anyting/agents/gnn-idea-broker.md .github/copilot-instructions/
```

### 手动安装（任意 Agent）

所有 Agent 定义都是独立的 Markdown 文件，复制到任何 LLM Agent 的上下文中即可使用：

```bash
cat ~/.claude/plugins/research-anyting/agents/literature-survey.md
# 将内容粘贴到你的 Agent prompt 中，附上研究课题
```

## 快速开始

```bash
# 探索研究方向
/mr gnn idea "动态图异常检测"

# 系统文献调研（15+ 数据源）
/mr gnn survey "异配图神经网络 2022-2025"

# 深度论文精读
/mr gnn read https://arxiv.org/abs/2406.00134

# 一键自主全流程
/mr auto "异配性感知的动态图异常检测"

# 创建你的研究领域
/mr new-domain nlp "大语言模型自然语言处理"
/mr nlp idea "高效微调方法"
```

## 使用教程：从零到论文

### 第一步：探索方向

```bash
/mr gnn idea "动态图异常检测"
```

Idea Broker 生成 3-5 个候选方向，每个方向包含可证伪假设、新颖性评估和可行性估算。选择最有前景的方向。

### 第二步：系统文献调研

```bash
/mr gnn survey "异配图动态异常检测 2022-2025"
```

Literature Survey Agent 搜索 15+ 学术数据源（Google Scholar、Semantic Scholar、arXiv、IEEE Xplore、ACM DL、DBLP、OpenReview 等），产出包含分类法、性能排行榜和研究空白的结构化报告。

### 第三步：深度精读关键论文

```bash
/mr gnn read https://arxiv.org/abs/2406.00134
```

Paper Reader Agent 执行三遍精读协议，提取结构化笔记、批判性分析，并生成可证伪的研究假设。

### 第四步：论文分解为模块

```bash
/mr decompose papers/gnn/2023-liu-taddy
```

KB Manager 从论文中提取可复用的方法组件（图编码器、时序模块、异常评分器等）。如果同一模块在其他论文中已存在，自动合并证据并升级验证状态。

### 第五步：发现模块组合

```bash
/mr combinations
```

KB Manager 计算 K-way (K >= 2) 模块组合，满足互补性、兼容性、协同性和极小性。有效组合成为孵育中的 Idea。

### 第六步：快速原型验证

```bash
/mr gnn prototype "双通道谱滤波的异配性感知编码器"
```

最小可行实验（1-2 天）在投入完整实验前验证核心假设。如果 MVE 失败，Experiment Debugger 诊断根因。

### 第七步：完整实验

```bash
/mr gnn experiment --monitor
```

Experiment Engineer 运行完整实验矩阵（5+ 数据集、7+ 基线、5 个随机种子）。Experiment Monitor 实时监控训练，自动检测异常并自动恢复。

### 第八步：分析与写作

```bash
/mr gnn analyze ./results/
/mr write "introduction" -> "ACM TKDD"
```

Insight Analyzer 提取因果解释。Paper Writer 按目标期刊规范生成论文各节。

### 第九步：投稿前审稿

```bash
/mr gnn review ./manuscript.pdf
```

四位独立审稿人（主编、方法论审稿人、实验审稿人、魔鬼代言人）评估稿件，产出带分数的审稿报告和可操作的修改建议。

### 第十步：回复审稿意见

```bash
/mr rebuttal ./reviewer_comments.txt
```

Rebuttal Writer 构建逐条回复，附带证据映射和稿件修改位置标注。

### 一键替代方案

```bash
/mr auto "异配性感知的动态图异常检测" --target CCF-B
```

自主执行全部 10 步。添加 `--human-gates` 在关键决策点需要人工审批。

## 架构

```
research-anyting/
├── .claude-plugin/plugin.json       # 插件清单
├── mr/SKILL.md                      # 顶层入口（/mr）
├── agents/                          # 27 个 Agent 定义
│   ├── gnn-*.md                     # GNN 领域专属（3）
│   ├── vlavlm-*.md                  # VLA-VLM 领域专属（3）
│   ├── literature-survey.md         # 共享管线 Agent（6）
│   ├── code-generator.md            # 构建 Agent（5）
│   ├── moon-pipeline.md             # 自主管线
│   ├── experiment-monitor.md        # 实时训练监控
│   └── [支撑 Agent]                  # 讨论、写作、回复、日志、演示
├── gnn/                             # GNN 领域
│   ├── SKILL.md                     # /mr gnn 编排器
│   └── references/                  # 论文、数据集、基线、Idea
├── vla-vlm/                         # VLA-VLM 领域
│   ├── SKILL.md                     # /mr vla-vlm 编排器
│   └── references/                  # 论文、基准、训练配方
├── knowledge-base/                  # 持久化记忆系统
│   ├── KB_SCHEMA.md
│   ├── papers/{gnn,vla-vlm}/        # 论文知识图谱
│   ├── modules/{gnn,vla-vlm}/       # 可复用方法组件
│   ├── ideas/{active,incubating,discarded}/  # K-way 超图
│   ├── venues/{journals,conferences}/        # CCF 期刊数据库（61 条）
│   ├── sessions/                    # 跨 Session 记忆
│   ├── experiments/                 # 实验记录
│   └── insights/                    # 跨领域洞察
├── shared/references/               # 跨领域标准
├── templates/                       # 领域 + 条目脚手架
├── scripts/                         # 工具脚本（5 个）
└── workflows/                       # 工作流脚本（5 个）
```

## 核心特性

### 27 个专业 Agent

| 层级 | Agent | 功能 |
|------|-------|------|
| **探索层** | Idea Broker, Literature Survey, Paper Reader | 发现研究空白，生成方向 |
| **构建层** | Theory Crafter, Rapid Prototype, Experiment Engineer, Code Generator, Hyperparameter Optimizer | 设计与验证方法 |
| **验证层** | Insight Analyzer, Deep Verification, Review Simulator, Experiment Debugger | 验证正确性，提取洞察 |
| **自主层** | Moon Pipeline, Experiment Monitor, Literature Alert, Data Preprocessor | 端到端自动化 |
| **支撑层** | Deep Discussion, Paper Writer, Rebuttal Writer, Research Log, Presentation Builder | 跨领域工具 |

### Paper → Module → Idea 流水线

论文被自动分解为可复用的方法模块。来自不同论文的已验证模块通过 K-way 超图计算重组成新 Idea。每个 Idea 自动获得期刊推荐。

### 61 个 CCF 期刊/会议 + 自动推荐

完整的 CCF-A/B/C 期刊和会议数据库。`/mr recommend-venue <idea>` 自动根据贡献强度匹配目标期刊。

### 跨 Session 知识持久化

`/mr auto-store on` 在每个 Agent 完成后自动持久化增量。`/mr recall "query"` 为新 Session 恢复上下文。磁盘存储充裕，上下文精炼压缩。

### 难度自适应工作流

管线根据目标期刊等级自动校准——CCF-A 比 CCF-B 或 CCF-C 需要更多的数据集、基线和理论分析。

### 实时实验监控

Experiment Monitor 实时监控训练：检测发散、NaN、平台期、过拟合；自动恢复；自动停止无望的训练。

### 动态领域创建

`/mr new-domain` 一键创建完整研究领域。系统自动调研该领域，识别模块类别，映射期刊，生成全部脚手架。

## 命令参考

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

## 支持的研究领域

### 内置

| 领域 | 焦点 | 主要期刊 |
|------|------|---------|
| **GNN** | 动态图异常检测、图表示学习、图欺诈检测 | TKDD, TKDE, KDD, AAAI, Neural Networks |
| **VLA-VLM** | 视觉-语言-动作模型、具身智能、多模态大模型、视觉指令微调 | CVPR, RSS, CoRL, ICLR, NeurIPS |

### 用户创建（通过 `/mr new-domain`）

CS/AI 中的任何研究领域都可以一键生成。系统自动生成：领域编排器、3 个领域专属 Agent、KB 目录、模块类别、期刊映射和初始参考文件。

## 环境要求

- Claude Code（主要平台）或其他 LLM 编码 Agent
- Python 3.8+（用于脚本）
- scipy、scikit-learn、matplotlib（用于指标计算和绘图）

## 参与贡献

系统设计为可扩展的。关键扩展点：

- **新 Agent**：在 `agents/` 中添加带 YAML frontmatter 的 Agent 定义文件
- **新领域**：使用 `/mr new-domain` 或手动创建 `domain/SKILL.md`
- **新期刊**：在 `knowledge-base/venues/` 中添加条目
- **新工作流**：在 `workflows/` 中添加脚本
- **新模板**：在 `templates/` 中添加模板

## 许可证

MIT