---
name: mr-research
description: This skill should be used when the user types "/mr" followed by any subcommand, or asks to use the Moon-Research system. The "/mr" prefix distinguishes all Moon-Research commands from other Claude Code plugins and built-in commands. Routes to domain-specific orchestrators (gnn, vla-vlm), knowledge base operations, support agents, and the autonomous pipeline.
---

# /mr — Moon-Research Entry Point

All Moon-Research commands use the `/mr` prefix. This prevents conflicts with other Claude Code plugins and built-in commands.

## Command Routing

```
/mr
├── gnn <cmd>              → 转发到 gnn/SKILL.md
├── vla-vlm <cmd>          → 转发到 vla-vlm/SKILL.md
├── vla <cmd>              → 转发到 vla-vlm/SKILL.md (VLA子域)
├── vlm <cmd>              → 转发到 vla-vlm/SKILL.md (VLM子域)
├── <custom> <cmd>         → 转发到 <custom>/SKILL.md (用户创建领域)
│
├── auto "topic" [...]     → 自主全流程管线
│
├── search "query"         → 跨KB搜索
├── papers [filters]       → 论文库浏览
├── paper <slug>           → 论文详情
├── modules [filters]      → 模块库浏览
├── module <slug>          → 模块详情
├── alert                  → 最新文献监控
│
├── ideas [filters]        → Idea列表
├── idea <slug>            → Idea详情
├── idea promote <slug>    → 孵育→活跃
├── idea discard <slug>    → 放弃Idea
├── combinations           → 重新计算K-way超图
├── decompose <paper>      → 论文→模块分解
│
├── code-gen               → 理论→可执行代码
├── hyperopt               → 系统化超参调优
├── preprocess             → 数据准备+标准化
│
├── debug                  → 实验失败根因诊断
├── monitor                → 训练实时监控
│
├── venues [filters]       → 期刊数据库浏览
├── venue <slug>           → 期刊详情
├── recommend-venue <idea> → 为Idea推荐期刊
│
├── write "section"→"venue" → 分节生成论文
├── rebuttal <reviews>     → 逐条审稿回复
├── present                → 生成答辩/组会PPT
│
├── discuss "question"     → 导师/同行/质疑者三角色
│
├── store session info     → 手动持久化
├── auto-store on/off      → 自动持久化开关
├── recall "query"         → 从KB恢复上下文
├── kb-check               → KB完整性验证
├── fuse                   → KB条目合并去重
│
├── new-domain <name> "<desc>" → 创建新研究领域
├── init <project-name>     → 初始化项目目录
├── status [--domain]       → 管线概览
├── log                     → 科研日志
├── export <type> <target>  → 导出数据
├── config <key> <value>    → 配置系统参数
│
└── help                    → 显示命令参考

## Project Management

When `/mr init <project-name>` is invoked, the project-init agent creates a fully scaffolded project directory at `~/research/<project-name>/` with:

```
~/research/<project-name>/
├── README.md                  # Project overview + hypothesis
├── config/default.yaml        # Experiment configuration
├── src/                       # Source code (models, data, training, eval)
├── data/                      # Datasets
├── experiments/               # Outputs (logs, checkpoints, results)
├── papers/                    # Related papers (PDFs + notes)
├── notes/daily/               # Daily research logs
├── manuscript/                # LaTeX manuscript
└── .moon-kb/ -> ~/research/.moon-kb/   # Shared KB symlink
```

The shared knowledge base lives at `~/research/.moon-kb/` and is shared across all projects. If it doesn't exist, `/mr init` migrates the plugin's seed data there on first run.

Default paths:
- Projects: `~/research/`
- Shared KB: `~/research/.moon-kb/`

Override via `/mr config projects.root /path/to/projects` and `/mr config kb.root /path/to/kb`.`
```

## Dispatch Protocol

### Domain Commands

When the user types `/mr gnn <cmd>`, read the GNN orchestrator at `gnn/SKILL.md` and follow its dispatch protocol for `<cmd>`. The GNN orchestrator handles: idea, survey, read, theory, prototype, experiment, analyze, verify, review, explore, full, auto.

When the user types `/mr vla-vlm <cmd>` (or `/mr vla <cmd>` or `/mr vlm <cmd>`), read the VLA-VLM orchestrator at `vla-vlm/SKILL.md` and follow its dispatch protocol.

When the user types `/mr <custom> <cmd>` where `<custom>` is a user-created domain, read `<custom>/SKILL.md` and follow its dispatch protocol.

### Autonomous Pipeline

`/mr auto "topic"` dispatches the moon-pipeline agent. See `agents/moon-pipeline.md` for the complete 6-phase autonomous protocol.

Supported flags:
- `--human-gates` — require human approval at key decision points
- `--stop-at <phase>` — run up to specified phase (explore, design, validate, analyze, write, review)
- `--target <tier>` — calibrate for CCF-A, CCF-B, or CCF-C
- `--dry-run` — plan the pipeline without executing
- `/mr auto status` — show current pipeline status
- `/mr auto resume` — resume from last checkpoint

### Knowledge Base Commands

`/mr store`, `/mr recall`, `/mr auto-store`, `/mr decompose`, `/mr combinations`, `/mr recommend-venue`, `/mr kb-check`, `/mr fuse` all dispatch the kb-manager agent (`agents/kb-manager.md`).

### Support Commands

`/mr discuss`, `/mr write`, `/mr rebuttal`, `/mr log`, `/mr present` dispatch the corresponding shared agents.

### Browse Commands

`/mr ideas`, `/mr idea`, `/mr modules`, `/mr module`, `/mr papers`, `/mr paper`, `/mr venues`, `/mr venue` all dispatch the kb-manager agent with the appropriate query.

### Specialized Commands

`/mr code-gen`, `/mr hyperopt`, `/mr preprocess`, `/mr debug`, `/mr monitor`, `/mr alert` dispatch the corresponding specialized agents.

### Management Commands

`/mr new-domain` dispatches the domain-init orchestrator.
`/mr status` dispatches kb-manager with a status query.
`/mr log` dispatches the research-log agent.
`/mr export` dispatches kb-manager with an export query.
`/mr search` dispatches kb-manager with a unified search query.

## Why `/mr` Prefix

- **No conflicts**: Generic commands like `/search`, `/write`, `/status` would conflict with other Claude Code plugins. The `/mr` prefix ensures all Moon-Research commands are uniquely identifiable.
- **Discoverability**: Typing `/mr` shows all available subcommands.
- **Consistency**: Every command follows the same pattern: `/mr <category> <action>`.
- **Brevity**: Two characters is short enough to type quickly while being distinctive enough to avoid conflicts.