# Moon-Research Quick Start Guide

## 1. Explore a Research Direction

```bash
# Generate research ideas
/mr gnn idea "dynamic graph anomaly detection"

# Run a systematic literature survey across all sources
/mr gnn survey "heterophilic graph neural networks 2022-2025"

# Deep read a key paper
/mr gnn read https://arxiv.org/abs/2406.00134
```

## 2. Decompose Papers into Modules

```bash
# After reading papers, decompose them into reusable modules
/mr decompose papers/gnn/2019-zheng-addgraph

# See what modules are available
/mr modules --domain gnn

# Run K-way combination discovery
/mr combinations
```

## 3. Validate an Idea

```bash
# Quick feasibility test (1-2 days)
/mr gnn prototype "heterophily-aware encoder"

# If it passes, run full experiments
/mr gnn experiment

# Analyze results
/mr gnn analyze ./results/

# Independent verification
/mr gnn verify
```

## 4. Write and Review

```bash
# Discuss your findings
/mr discuss "My method works on heterophilic graphs but degrades on homophilic ones"

# Write the paper
/mr write "introduction" -> "ACM TKDD"

# Pre-submission review
/mr gnn review ./manuscript.pdf

# Respond to reviewers
/mr rebuttal ./reviewer_comments.txt
```

## 5. Maintain Context Across Sessions

```bash
# Enable automatic knowledge persistence
/mr auto-store on

# Check what's been stored
/mr status

# In a new session, recover context
/mr recall "active hypotheses in GNN domain"
```

## 6. Create a New Research Domain

```bash
# Create a new domain on the fly
/mr new-domain tsf "Time Series Forecasting with Deep Learning"

# Start using it immediately
/mr tsf idea "probabilistic forecasting"
/mr tsf survey "transformer time series 2024-2025"
```

## 7. Search and Browse

```bash
# Find venues for your idea
/mr recommend-venue ideas/incubating/heterophily-dygad

# Browse all CCF-B venues
/mr venues --tier B --domain gnn

# Search across the entire knowledge base
/mr search "heterophily anomaly detection"

# Export BibTeX for all GNN papers
/mr export bib gnn
```

## Common Workflows

### New PhD Student Starting Out
1. `/mr gnn idea "your topic"` → get 3-5 candidate directions
2. Pick the best one, run `/mr gnn survey "direction"` → deep literature understanding
3. `/mr gnn read` the top 5 papers → structured notes + hypotheses
4. `/mr decompose` each paper → build module library
5. `/mr combinations` → discover novel module combinations
6. Pick the most promising idea, run `/mr gnn prototype`

### Paper Deadline Sprint
1. `/mr gnn experiment` → comprehensive results
2. `/mr gnn analyze` → extract insights and narrative
3. `/mr write` each section → generate manuscript
4. `/mr gnn review` → pre-submission peer review
5. Fix critical issues → revise → submit

### Reviewer Response
1. `/mr rebuttal ./reviews.txt` → point-by-point response
2. `/mr discuss` difficult reviewer comments
3. Run additional experiments requested by reviewers
4. Update manuscript and response
5. Resubmit