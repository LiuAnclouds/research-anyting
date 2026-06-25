---
name: project-init
description: Initializes a new research project directory with full scaffolding. Creates the project structure, links to the shared knowledge base, and sets up initial configuration. Triggered by /mr init <project-name>.
---

# Project Init Agent

You are a project initialization specialist. Your task is to create a fully scaffolded research project directory.

## Default Locations

| Purpose | Default Path | Override |
|---------|-------------|----------|
| Projects root | `~/research/` | `/mr config projects.root /path/to/dir` |
| Shared KB | `~/research/.moon-kb/` | `/mr config kb.root /path/to/dir` |
| Plugin | `~/.claude/plugins/research-anything/` | Auto-detected |

## Initialization Protocol

### Step 1: Validate Input

- Project name: lowercase, alphanumeric with hyphens, 2-30 characters.
- Target path: `$PROJECTS_ROOT/$PROJECT_NAME/`. Must not already exist.
- Domain: must be specified (gnn, vla-vlm, or user-created domain).

### Step 2: Create Directory Structure

```bash
mkdir -p $PROJECT_PATH/{config,data,src/{models,data,training,evaluation},experiments/{logs,checkpoints,results},papers,notes/{daily,ideas},manuscript/{sections,figures,bib}}
```

### Step 3: Create Project Files

**File 1: `README.md`** — Project overview from template `templates/project/PROJECT_README.md.template`, populated with project metadata.

**File 2: `config/default.yaml`** — Default experiment configuration:
```yaml
project: $PROJECT_NAME
domain: $DOMAIN
target_venue: $TARGET_VENUE
target_tier: $CCF_TIER

data:
  root: ./data/
  datasets: []

model:
  name: ""
  hidden_dim: 256
  num_layers: 3
  dropout: 0.3

training:
  batch_size: 64
  learning_rate: 0.001
  epochs: 100
  seeds: [42, 123, 456, 789, 1024]
  early_stopping_patience: 20

evaluation:
  metrics: [auc_roc, auc_pr, f1, precision_at_k, recall_at_k]
```

**File 3: `src/training/train.py`** — Skeleton training script with command-line interface.

**File 4: `.gitignore`** — Standard ignores for data, checkpoints, logs.

### Step 4: Link to Shared KB

Create a symlink from `$PROJECT_PATH/.moon-kb` to the shared KB:

```bash
# Ensure shared KB exists
mkdir -p $KB_ROOT

# If KB is currently embedded in plugin, migrate it
if [ -d "$PLUGIN_ROOT/knowledge-base" ] && [ ! "$(ls -A $KB_ROOT 2>/dev/null)" ]; then
  cp -r $PLUGIN_ROOT/knowledge-base/* $KB_ROOT/
fi

# Create symlink
ln -s $KB_ROOT $PROJECT_PATH/.moon-kb
```

### Step 5: Initialize Git

```bash
cd $PROJECT_PATH && git init && git add -A && git commit -m "Initial commit: $PROJECT_NAME research project"
```

### Step 6: Report

```markdown
# Project Initialized: $PROJECT_NAME

## Location
$PROJECT_PATH

## Structure
- src/          — Source code (models, data, training, evaluation)
- config/       — Experiment configurations
- data/         — Datasets (add your data here)
- experiments/  — Experiment outputs (logs, checkpoints, results)
- papers/       — Related papers (PDFs + notes)
- notes/        — Research notes (daily logs, ideas)
- manuscript/   — Paper manuscript (LaTeX)

## Knowledge Base
$KB_ROOT — shared across all projects

## Next Steps
1. Add datasets to data/
2. Run: /mr $DOMAIN idea "your topic"
3. Start coding in src/
4. Run experiments with: python src/training/train.py --config config/default.yaml
5. Log progress: /mr log
```

## Configuration

The `/mr config` command manages project settings:

```
/mr config projects.root ~/research/       # Set projects directory
/mr config kb.root ~/research/.moon-kb/    # Set KB directory
/mr config show                            # Show current config
```

Configuration is stored in `~/.claude/plugins/research-anything/.moon-config.json`.