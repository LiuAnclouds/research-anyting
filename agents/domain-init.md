---
name: domain-init
description: This skill should be used when the user invokes "/new-domain", "/init-domain", asks to "create a new research domain", "add a research area", "set up a new sub-project", or specifies a research field they want to work on. Auto-generates a complete domain structure including orchestrator, agent definitions, KB directories, module categories, venue mapping, and initial reference files by researching the specified field.
---

# /new-domain — Domain Initialization Orchestrator

This orchestrator creates a complete, self-contained research domain within the Moon-Research system. The user provides a short name and a description of the research area. The orchestrator researches the field, identifies its structure, and generates all scaffolding.

## Command

```
/new-domain <short-name> "<description>"
```

Example: `/mr new-domain tsf "Time Series Forecasting with Deep Learning"`

## Execution Protocol

### Phase 0: Validate Input

1. Parse `<short-name>`: must be lowercase, alphanumeric with hyphens, 2-20 characters. Must not conflict with existing domain names (`gnn`, `vla-vlm`).
2. Parse `"<description>"`: must be >=10 words. Must describe a research field within computer science, artificial intelligence, or a related engineering discipline.
3. If validation fails, report the specific issue and request corrected input.

### Phase 1: Research the Domain

Dispatch a subagent using the `Agent` tool. Use the agent definition at `agents/domain-researcher.md`. Pass the following context:

> Research field: `<short-name>` — `<description>`
>
> Instructions:
> 1. Search for the 3-5 most cited survey papers in this field. Record titles, authors, venues, and years.
> 2. Identify the standard benchmark datasets used in this field. Record names, sizes, and domains.
> 3. Identify the 5-10 most cited baseline methods. Record names, years, venues, and code availability.
> 4. Identify the typical methodological decomposition of work in this field. What are the functional components that papers in this field are built from? (e.g., for GNN: encoders, temporal modules, anomaly scorers, loss functions, training strategies). Provide 3-6 categories.
> 5. Identify the CCF venues where work in this field is typically published. List journals and conferences with their tiers.
> 6. Identify the 3-5 most active research frontiers or open problems.
> 7. Produce a structured Domain Research Report.

After the subagent completes, verify: at least 3 surveys identified, at least 5 datasets, at least 5 baselines, at least 3 module categories, at least 5 venues.

### Phase 2: Generate Domain Structure

Based on the Domain Research Report, create the directory structure:

```bash
mkdir -p knowledge-base/papers/<short-name>
mkdir -p knowledge-base/modules/<short-name>/{<category-1>,<category-2>,...,<category-N>}
mkdir -p <short-name>/references
```

Create the following files:

**File 1: `<short-name>/SKILL.md`** — Domain orchestrator. Template:

```yaml
---
name: <short-name>-research
description: This skill should be used when the user invokes "/mr <short-name>", references <field description>, or mentions specific methods from this field. Orchestrates a multi-agent research pipeline where each phase dispatches a specialized subagent using the Agent tool.
---

# /mr <short-name> — <Field Name> Research Domain

## Command Routing

### Research Commands
| Command | Agent Dispatched |
|---------|-----------------|
| `/mr <short-name> idea "topic"` | <short-name>-idea-broker |
| `/mr <short-name> survey "topic"` | literature-survey (shared) |
| `/mr <short-name> read <paper>` | paper-reader (shared) |
| `/mr <short-name> theory` | theory-crafter (shared) |
| `/mr <short-name> prototype "approach"` | <short-name>-rapid-prototype |
| `/mr <short-name> experiment` | experiment-engineer (shared) |
| `/mr <short-name> analyze <results>` | <short-name>-insight-analyzer |
| `/mr <short-name> verify` | deep-verification (shared) |
| `/mr <short-name> review <manuscript>` | review-simulator (shared) |
| `/mr <short-name> explore "topic"` | idea-broker -> survey -> paper-reader (sequential) |
| `/mr <short-name> full "hypothesis"` | All agents with quality gates |

[Same KB commands, support commands, KB integration, and difficulty-adaptive workflow sections as gnn/SKILL.md, with domain-specific substitutions.]

Load domain knowledge from `<short-name>/references/`.
```

**File 2: `<short-name>/references/papers.md`** — Initial paper database with surveys, baselines, and frontier methods from the Domain Research Report.

**File 3: `<short-name>/references/datasets.md`** — Benchmark dataset catalog from the Domain Research Report.

**File 4: `<short-name>/references/ideas.md`** — Research directions with falsifiable hypotheses, derived from the open problems identified in the Domain Research Report.

**File 5: `agents/<short-name>-idea-broker.md`** — Domain-specific Idea Broker agent, adapted from the GNN Idea Broker template with the domain's literature tree, challenge-insight mapping, and key venues.

**File 6: `agents/<short-name>-rapid-prototype.md`** — Domain-specific Rapid Prototype agent with minimal viable experiment configurations appropriate to the domain's standard benchmarks.

**File 7: `agents/<short-name>-insight-analyzer.md`** — Domain-specific Insight Analyzer with analysis dimensions appropriate to the domain's typical evaluation metrics and failure modes.

### Phase 3: Initialize KB

1. Create `knowledge-base/papers/<short-name>/INDEX.md`.
2. Create `knowledge-base/modules/<short-name>/INDEX.md` with entries for each module category.
3. Add the domain to `knowledge-base/INDEX.md` and `knowledge-base/papers/INDEX.md`.
4. Add venue entries for any venues not already in `knowledge-base/venues/INDEX.md`.

### Phase 4: Report

Report a summary:
- Domain created: `<short-name>`
- Module categories: N categories identified
- Surveys catalogued: N
- Baselines catalogued: N
- Datasets catalogued: N
- Venues mapped: N
- Agent definitions created: 3 domain-specific + 6 shared (inherited)
- Next steps: `/ <UPPER-SHORT-NAME> survey "topic"` to begin literature survey, `/ <UPPER-SHORT-NAME> idea "topic"` to generate research directions.

---

## Additional Global Commands

The following commands operate across all domains and are available at any point:

### Idea Management
| Command | Function |
|---------|----------|
| `/mr ideas` | List all ideas across domains, filterable by status, domain, tier |
| `/idea <slug>` | View detailed idea entry with modules, papers, recommended venues |
| `/idea promote <slug>` | Promote idea from incubating to active |
| `/idea discard <slug>` | Discard idea with reason |
| `/idea combine <slug1> <slug2> ...` | Manually propose a new hyperedge of specific ideas |

### Module Library
| Command | Function |
|---------|----------|
| `/mr modules` | Browse module library, filterable by domain, category, validation status |
| `/module <slug>` | View detailed module entry with source papers, composability, assumptions |

### Paper Management
| Command | Function |
|---------|----------|
| `/mr papers` | List papers in KB, filterable by domain, venue tier, novelty, code availability |
| `/paper <slug>` | View detailed paper entry with modules, connections |

### Venue Browsing
| Command | Function |
|---------|----------|
| `/mr venues` | Browse venue database, filterable by tier, domain, category |
| `/venue <slug>` | View detailed venue entry with requirements, similar papers |

### Pipeline Status
| Command | Function |
|---------|----------|
| `/mr status` | Overview: active ideas, in-progress experiments, recent papers, pending decisions |
| `/mr status <domain>` | Domain-specific status |

### Cross-KB Search
| Command | Function |
|---------|----------|
| `/mr search "query"` | Unified search across papers, modules, ideas, venues, insights, and sessions |

### Export
| Command | Function |
|---------|----------|
| `/mr export idea <slug>` | Export idea as a structured research proposal (markdown) |
| `/mr export module <slug>` | Export module with all evidence and composability data |
| `/mr export bib <domain>` | Export all paper BibTeX entries for a domain |