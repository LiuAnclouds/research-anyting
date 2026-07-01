---
name: mr-research
description: This skill should be used when the user types "/mr" followed by any subcommand, or asks to use the Moon-Research system. The "/mr" prefix distinguishes all Moon-Research commands from other Claude Code plugins and built-in commands. Routes to domain-specific orchestrators (gnn, vla-vlm), knowledge base operations, support agents, and the autonomous pipeline.
argument-hint: "[subcommand] [...args]"
---

# /mr — Moon-Research Entry Point

> See `COMMANDS.md` at plugin root for the canonical command reference.

All Moon-Research commands use the `/mr` prefix. This prevents conflicts with other Claude Code plugins and built-in commands.

## Command Parsing

When invoked, `$ARGUMENTS` contains the subcommand and all its arguments. Parse `$ARGUMENTS` to extract the subcommand (first token) and remaining arguments. Route based on the subcommand as specified below.

**IMPORTANT**: Every subcommand listed below MUST be handled. If the user types `/mr config kb.auto_store on`, parse subcommand=`config`, args=`kb.auto_store on`. Do not ignore unmatched subcommands — report "Unknown subcommand: X. Use /mr help for available commands."

Unprefixed aliases (`/idea`, `/paper`, `/venue`, `/module`) are **not accepted** — always require the `/mr` prefix, e.g. `/mr idea <slug>`.

## Command Routing

```
/mr
├── gnn <cmd>              → 转发到 gnn/SKILL.md
├── vla-vlm <cmd>          → 转发到 vla-vlm/SKILL.md
├── vla <cmd>              → 转发到 vla-vlm/SKILL.md (VLA子域)
├── vlm <cmd>              → 转发到 vla-vlm/SKILL.md (VLM子域)
├── <custom> <cmd>         → 转发到 <custom>/SKILL.md (用户创建领域)
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
├── recall "query"         → 从KB恢复上下文
├── kb-check               → KB完整性验证
├── fuse                   → KB条目合并去重
│
├── health [<domain>|--all]→ P5 完成度评分
├── cost [--budget USD]    → 成本报告
├── dag                    → ASCII 管线图
├── resume                 → 恢复计划
│
├── new-domain <name> "<desc>" → 创建新研究领域
├── init <project-name>     → 初始化项目目录
├── status [--domain]       → 管线概览
├── log                     → 科研日志
├── export <type> <target>  → 导出数据
├── config <key> <value>    → 配置系统参数 (含 kb.auto_store on|off)
│
└── help                    → 显示命令参考
```

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

Override via `/mr config projects.root /path/to/projects` and `/mr config kb.root /path/to/kb`.

## Dispatch Protocol

### Domain Commands

When the user types `/mr gnn <cmd>`, read the GNN orchestrator at `gnn/SKILL.md` and follow its dispatch protocol for `<cmd>`. The GNN orchestrator handles: idea, survey, read, theory, prototype, experiment, analyze, review, full, auto. (Note: `explore` is redundant with `idea+survey`; `verify` is redundant with `review` — do not route these.)

When the user types `/mr vla-vlm <cmd>` (or `/mr vla <cmd>` or `/mr vlm <cmd>`), read the VLA-VLM orchestrator at `vla-vlm/SKILL.md` and follow its dispatch protocol.

When the user types `/mr <custom> <cmd>` where `<custom>` is a user-created domain, read `<custom>/SKILL.md` and follow its dispatch protocol.

### Autonomous Pipeline

`/mr auto "topic"` is **deprecated**; use `/mr <domain> full` instead (e.g., `/mr gnn full`, `/mr vla-vlm full`). The domain-scoped `full` variant dispatches the moon-pipeline agent with the domain's calibrated 6-phase protocol. See `agents/moon-pipeline.md` for the complete protocol.

Supported flags (when passed to `/mr <domain> full`):
- `--human-gates` — require human approval at key decision points
- `--stop-at <phase>` — run up to specified phase (explore, design, validate, analyze, write, review)
- `--target <tier>` — calibrate for CCF-A, CCF-B, or CCF-C
- `--dry-run` — plan the pipeline without executing

Pipeline state inspection is available via `/mr resume` (see System Commands below).

### Knowledge Base Commands

`/mr store session info` — dispatch kb-manager agent to extract and persist the current session delta.
`/mr recall "query"` — dispatch kb-manager agent to retrieve relevant KB context.
`/mr decompose <paper>` — dispatch kb-manager agent to decompose a paper into modules.
`/mr combinations` — dispatch kb-manager agent to recompute the idea hypergraph.
`/mr recommend-venue <idea>` — dispatch kb-manager agent to recommend target venues.
`/mr kb-check` — dispatch kb-manager agent to verify KB integrity.
`/mr fuse` — dispatch kb-manager agent to consolidate related entries.

Autonomous KB storage is toggled via `/mr config kb.auto_store on|off` (see Management Commands).

### Support Commands

`/mr discuss "question"` — dispatch deep-discussion agent.
`/mr write "section" -> "venue"` — dispatch paper-writer agent.
`/mr rebuttal <reviews>` — dispatch rebuttal-writer agent.
`/mr log` — dispatch research-log agent.
`/mr present` — dispatch presentation-builder agent.

### Browse Commands

`/mr ideas [--domain X] [--status Y]` — dispatch kb-manager to list ideas.
`/mr idea <slug>` — dispatch kb-manager to view idea detail.
`/mr idea promote <slug>` — dispatch kb-manager to promote idea status.
`/mr idea discard <slug>` — dispatch kb-manager to discard idea.
`/mr modules [--domain X] [--category Y]` — dispatch kb-manager to browse modules.
`/mr module <slug>` — dispatch kb-manager to view module detail.
`/mr papers [--domain X] [--tier Y] [--code]` — dispatch kb-manager to list papers.
`/mr paper <slug>` — dispatch kb-manager to view paper detail.
`/mr venues [--tier X] [--domain Y]` — dispatch kb-manager to browse venues.
`/mr venue <slug>` — dispatch kb-manager to view venue detail.

### Specialized Commands

`/mr alert` — dispatch literature-alert agent.

### System Commands

The following commands invoke maintenance/inspection scripts under the plugin root. For each, run the corresponding `py` script via Bash from the plugin root and stream the output back verbatim.

| Command | Backing script | Purpose |
| --- | --- | --- |
| `/mr health [<domain>\|--all]` | `scripts/mr_health.py` | Compute 0-100 completeness score for a domain (P5). Runs 8 rubric checks (benchmark-registry entries, domain agents, quality gates, expert memory, RAG indices, SKILL routes, references, frontmatter). Prints a boxed scorecard with per-check status + suggested fix. Use `--all` to score every detected domain. |
| `/mr cost [--budget USD]` | `scripts/mr_cost.py` | Cost report aggregated from `knowledge-base/audit-rounds/*.json`. Groups by phase (EXPLORE→...→REVIEW), shows tokens + estimated USD. `--budget` checks remaining. |
| `/mr dag` | `scripts/mr_dag.py` | ASCII pipeline graph. All 6 panels with weights + CRIT axes + temperature-rotation tags. If `_state.json` exists, marks the current phase with ◀── HERE. |
| `/mr resume` | `scripts/mr_resume.py` | Read `_state.json` + latest audit round JSON, print a recovery plan (unresolved findings, vetoes, suggested next command). |

Invocation examples:
- `/mr health` → run `py scripts/mr_health.py` in the plugin root; stream output.
- `/mr health gnn` → run `py scripts/mr_health.py gnn`.
- `/mr health --all` → run `py scripts/mr_health.py --all`.
- `/mr cost --budget 500` → run `py scripts/mr_cost.py --budget 500`.
- `/mr dag` → run `py scripts/mr_dag.py`.
- `/mr resume` → run `py scripts/mr_resume.py`.

### Management Commands

`/mr new-domain <name> "<desc>"` — dispatch domain-init orchestrator.
`/mr init <project-name>` — dispatch project-init agent.
`/mr status [--domain]` — dispatch kb-manager with status query.
`/mr log` — dispatch research-log agent.
`/mr export <type> <target>` — dispatch kb-manager with export query.
`/mr search "query"` — dispatch kb-manager with unified search query.
`/mr config <key> <value>` — update system configuration. Notable keys: `kb.auto_store on|off` (autonomous KB storage after each agent completes), `projects.root <path>`, `kb.root <path>`.
`/mr help` — display command reference.

## Why `/mr` Prefix

- **No conflicts**: Generic commands like `/mr search`, `/mr write`, `/mr status` would conflict with other Claude Code plugins. The `/mr` prefix ensures all Moon-Research commands are uniquely identifiable.
- **Discoverability**: Typing `/mr` shows all available subcommands.
- **Consistency**: Every command follows the same pattern: `/mr <category> <action>`.
- **Brevity**: Two characters is short enough to type quickly while being distinctive enough to avoid conflicts.