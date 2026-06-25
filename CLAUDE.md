# Moon Research Subagent System

## Purpose

A multi-agent research framework for rigorous scientific research. The system supports an arbitrary number of research domains, each with a dedicated orchestrator and agent pipeline. Domains can be pre-built (GNN, VLA-VLM) or user-created via `/mr new-domain`. The system integrates agent dispatch, persistent knowledge base, venue recommendation, and difficulty-adaptive workflows.

## Complete Command Reference

### Domain-Specific Commands

Replace `<DOMAIN>` with the actual domain short-name (e.g., `GNN`, `VLA-VLM`, `TSF`).

| Command | Function |
|---------|----------|
| `/<DOMAIN> idea "topic"` | Generate research directions via Idea Broker |
| `/<DOMAIN> survey "topic"` | Systematic literature survey |
| `/<DOMAIN> read <paper>` | Deep paper reading with structured notes |
| `/<DOMAIN> theory` | Mathematical formalization and algorithm design |
| `/<DOMAIN> prototype "approach"` | Minimal viable experiment (1-2 days) |
| `/<DOMAIN> experiment` | Full experimental validation |
| `/<DOMAIN> analyze <results>` | Root-cause analysis and insight extraction |
| `/<DOMAIN> verify` | Independent adversarial verification |
| `/<DOMAIN> review <manuscript>` | Multi-role peer review simulation |
| `/<DOMAIN> explore "topic"` | Full exploration layer (idea -> survey -> read) |
| `/<DOMAIN> full "hypothesis"` | Complete pipeline with quality gates |

### Knowledge Base Commands

| Command | Function |
|---------|----------|
| `/mr store session info` | Persist session findings to KB |
| `/mr auto-store on/off` | Toggle autonomous KB storage after each agent |
| `/mr recall "query"` | Retrieve relevant KB context |
| `/mr decompose <paper>` | Decompose paper into modules (Paper -> Module) |
| `/mr combinations` | Recompute idea hypergraph (Module -> Idea) |
| `/mr recommend-venue <idea>` | Recommend target venues for an idea |
| `/mr kb-check` | Verify KB integrity |
| `/mr fuse` | Consolidate related KB entries |

### Global Management Commands

| Command | Function |
|---------|----------|
| `/mr new-domain <name> "<desc>"` | Create a new research domain with full scaffolding |
| `/mr ideas [--domain X] [--status Y]` | List all ideas across domains |
| `/mr idea <slug>` | View detailed idea entry |
| `/mr idea promote\|discard <slug>` | Change idea status |
| `/mr modules [--domain X] [--category Y]` | Browse module library |
| `/mr module <slug>` | View module with source papers |
| `/mr papers [--domain X] [--tier Y] [--code]` | List papers in KB |
| `/mr paper <slug>` | View paper with modules |
| `/mr venues [--tier X] [--domain Y]` | Browse venue database |
| `/mr venue <slug>` | View venue with requirements |
| `/mr status [--domain X]` | Pipeline overview |
| `/mr search "query"` | Unified cross-KB search |
| `/mr export idea\|bib <target>` | Export structured data |

### Support Commands

| Command | Function |
|---------|----------|
| `/mr discuss "question"` | Structured academic debate (3 role modes) |
| `/mr write "section" -> "venue"` | Generate manuscript section |
| `/mr rebuttal <reviews>` | Point-by-point reviewer response |
| `/mr log` | Record daily research log entry |
| `/mr present` | Build academic presentation |

## Architecture

```
moon-research/
├── CLAUDE.md                            # System specification
├── agents/                              # Agent definitions (YAML frontmatter)
│   ├── gnn-*.md                         # GNN domain agents (9)
│   ├── vlavlm-*.md                      # VLA/mr vlm domain agents (3)
│   ├── domain-init.md                   # Domain initialization orchestrator
│   ├── domain-researcher.md             # Domain research agent
│   ├── kb-manager.md                    # Knowledge base manager
│   └── shared agents (5)
├── gnn/SKILL.md                         # GNN orchestrator
├── vla-vlm/SKILL.md                     # VLA/mr vlm orchestrator
├── <new-domain>/SKILL.md                # User-created domain (via /mr new-domain)
├── shared/references/                   # Cross-domain standards
├── templates/                           # Domain scaffolding templates
└── knowledge-base/                      # Persistent memory system
    ├── KB_SCHEMA.md
    ├── papers/{gnn,vla-vlm,<new>}/
    ├── modules/{gnn,vla-vlm,<new>}/
    ├── ideas/{active,incubating,discarded}/
    ├── venues/{journals,conferences}/{ccf-a,ccf-b,ccf-c}/
    ├── sessions/
    ├── experiments/
    ├── insights/
    └── cross-links/
```

## Key Workflows

### Creating a New Domain

```
/mr new-domain tsf "Time Series Forecasting with Deep Learning"
```

This triggers the domain-init orchestrator which:
1. Dispatches the domain-researcher agent to survey the field.
2. Generates the domain directory with orchestrator SKILL.md.
3. Creates domain-specific agent definitions (Idea Broker, Rapid Prototype, Insight Analyzer).
4. Initializes KB directories for papers and modules.
5. Creates initial reference files (papers, datasets, ideas).
6. Maps venues to the KB venue database.

After creation, the domain is immediately usable: `/mr tsf idea "probabilistic forecasting"`.

### Paper → Module → Idea Pipeline

1. `/mr gnn read <paper>` stores paper entry.
2. `/mr decompose <paper>` extracts modules from the paper.
3. `/mr combinations` recomputes the K-way idea hypergraph from validated modules.
4. `/mr recommend-venue <idea>` matches idea to target venues.

### Cross-Session Continuity

1. New session: orchestrator reads most recent session entry.
2. `/mr recall "active context"` retrieves: open hypotheses, pending decisions, active ideas, unresolved questions.
3. Context injected into agent dispatch prompts.
4. `/mr auto-store on` persists deltas after each agent completes.

## Agent Count by Domain

| Domain | Agents | Specific | Shared | Status |
|--------|--------|----------|--------|--------|
| GNN | 9 | 3 (idea, prototype, insight) | 6 | Built-in |
| VLA-VLM | 9 | 3 (idea, prototype, insight) | 6 | Built-in |
| User-created | 9 | 3 (auto-generated) | 6 | Via /mr new-domain |
| Cross-domain | 5 | 5 (discuss, write, rebuttal, log, present) | 0 | Always available |
| KB | 2 | 2 (kb-manager, domain-researcher) | 0 | Always available |
| Domain init | 1 | 1 (domain-init) | 0 | Always available |

## Installation

System location: `~/.claude/skills/moon-research/`

Claude Code automatically discovers orchestrators by scanning `*/SKILL.md` files. When a new domain is created via `/mr new-domain`, its SKILL.md is immediately discoverable.