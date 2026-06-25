---
name: moon-pipeline
description: This skill should be used when the user invokes "/mr auto", "/moon-full", asks to "run the full research pipeline", "automate my research", "one-click research", or wants autonomous end-to-end research execution from idea generation through manuscript completion. Orchestrates ALL agents in sequence with automated decision-making at quality gates and human-in-the-loop only for critical judgment calls.
---

# /mr auto — Autonomous Full-Cycle Research Pipeline

This orchestrator executes the complete research lifecycle autonomously. It chains all 25 agents in a structured pipeline with six phases. At each quality gate, the system makes automated decisions where criteria are clear and flags only critical judgment calls for human review.

## Pipeline Phases

```
Phase 1: EXPLORE     Phase 2: DESIGN      Phase 3: VALIDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Idea Broker           Theory Crafter       Experiment Engineer
Literature Survey     Code Generator       (monitored by
Paper Reader          Hyperparameter Opt   Experiment Monitor)
Domain-Venue Mapping  Rapid Prototype
                      ─────────────────────────────────────────
Phase 4: ANALYZE      Phase 5: WRITE       Phase 6: REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Insight Analyzer      Paper Writer         Review Simulator
Deep Verification     (all sections)       Rebuttal Writer
                      (prep for submission)
```

## Command Interface

```
/mr auto "research topic"                    → Full autonomous pipeline
/mr auto "topic" --human-gates              → Pipeline with human approval at each gate
/mr auto "topic" --stop-at phase            → Run up to specified phase
/mr auto "topic" --target CCF-A             → Calibrate for CCF-A target
/mr auto "topic" --dry-run                  → Plan the pipeline without executing
/mr auto status                              → Show current pipeline status
/mr auto resume                              → Resume from last checkpoint
```

## Autonomous Execution Protocol

### Phase 1: EXPLORE (Autonomous)

```
Step 1.1: Dispatch Idea Broker
  → Generate 3-5 candidate directions
  → Auto-select top-ranked direction (highest novelty×feasibility×potential)
  → [HUMAN GATE if --human-gates]: Confirm direction selection

Step 1.2: Dispatch Literature Survey (parallel)
  → Search ALL 15+ sources
  → Generate taxonomy, leaderboard, gap analysis
  → Auto-verify: >=50 papers screened, >=2 surveys cited

Step 1.3: Dispatch Paper Reader (for top 5 papers)
  → Deep read top 5 papers identified by survey
  → Extract modules, generate hypotheses
  → Auto-decompose each paper into KB modules

Step 1.4: Dispatch Domain-Venue Mapping
  → Match research direction to target venues
  → Auto-select: primary, secondary, fallback venues
  → [HUMAN GATE if --human-gates]: Confirm venue selection

AUTO-ADVANCE if: >=3 papers support the gap, >=1 idea has novelty >=4
```

### Phase 2: DESIGN (Autonomous)

```
Step 2.1: Dispatch Theory Crafter
  → Formalize problem, design method, analyze complexity
  → Auto-verify: all assumptions stated, complexity derived

Step 2.2: Dispatch Code Generator
  → Generate implementation from theory spec
  → Auto-verify: code is syntactically valid, runs without error

Step 2.3: Dispatch Hyperparameter Optimizer
  → Run systematic hyperparameter search
  → Auto-select best configuration

Step 2.4: Dispatch Rapid Prototype
  → Execute MVE on 1 dataset, 1-2 baselines
  → Pre-registered success criterion
  → Auto-decision: PASS → continue; BORDERLINE → retry with adjusted config; FAIL → flag to human

AUTO-ADVANCE if: MVE passes pre-registered criterion
BLOCK if: MVE fails 3 times → human must decide: adjust direction or continue
```

### Phase 3: VALIDATE (Autonomous + Monitored)

```
Step 3.1: Dispatch Experiment Engineer
  → Design full experiment matrix
  → Execute all experiments (may take hours/days)

Step 3.2: Launch Experiment Monitor (parallel, background)
  → Watch training logs in real-time
  → Detect: divergence, NaN, plateau, overfitting
  → Auto-stop: if loss diverges or NaN detected
  → Alert: if plateau detected, suggest LR adjustment
  → Report: per-epoch metrics, estimated time to completion

Step 3.3: On experiment completion
  → Auto-verify: >=5 seeds, >=7 baselines, statistical tests applied
  → [HUMAN GATE if --human-gates]: Review results before proceeding

AUTO-ADVANCE if: all experiment groups complete, statistical tests pass
```

### Phase 4: ANALYZE (Autonomous)

```
Step 4.1: Dispatch Insight Analyzer (parallel)
  → Performance attribution
  → Failure case taxonomy
  → Condition analysis
  → Narrative construction

Step 4.2: Dispatch Deep Verification
  → Independently verify all claims
  → Check statistical rigor, baseline fairness, overclaiming
  → Auto-flag: any claim that fails verification

Step 4.3: Dispatch Experiment Debugger (if results are unexpected)
  → Diagnose: why did certain experiments fail?
  → Recommend: additional experiments or method adjustments

AUTO-ADVANCE if: all claims verified, no critical issues
BLOCK if: verification finds critical issues → flag to human
```

### Phase 5: WRITE (Autonomous)

```
Step 5.1: Dispatch Paper Writer for each section
  → Abstract, Introduction, Related Work, Method, Experiments, Conclusion
  → Auto-enforce: all writing standards, no prohibited constructions

Step 5.2: Auto-generate figures using scripts/plot_results.py
  → Comparison bar chart, ablation study, training curves, sensitivity heatmap

Step 5.3: Auto-compile complete manuscript
  → Generate BibTeX from KB
  → Format for target venue

AUTO-ADVANCE if: all sections complete, all figures generated
```

### Phase 6: REVIEW (Autonomous)

```
Step 6.1: Dispatch Review Simulator
  → 4-role review: EIC, Reviewer#1, Reviewer#2, Skeptic
  → Auto-score the manuscript

Step 6.2: Auto-decision based on review score
  → Score >=80: manuscript ready for submission
  → Score 70-79: auto-revise minor issues, re-review
  → Score 60-69: flag major issues, suggest fixes
  → Score <60: significant revision needed, flag to human

Step 6.3: If score >=70, dispatch Rebuttal Writer
  → Pre-generate responses to anticipated reviewer questions

AUTO-COMPLETE if: score >=80
BLOCK if: score <70 → human must decide next steps
```

## Experiment Monitor Agent

The Experiment Monitor runs in parallel with the Experiment Engineer. It watches training progress in real-time and provides:

### Real-Time Monitoring
- Loss curves (train + val), updated per epoch
- Metric trends (AUC-ROC, AUC-PR, F1), updated per evaluation
- GPU utilization and memory usage
- Estimated time to completion (based on elapsed time per epoch)
- Early stopping detection (no improvement for N epochs)

### Anomaly Detection
- Divergence: loss increases >10x in one epoch → auto-stop, alert
- NaN: any NaN in loss or gradients → auto-stop, flag
- Plateau: val metric unchanged for 20% of total epochs → alert, suggest LR schedule adjustment
- Overfitting: train loss decreasing, val loss increasing → alert, suggest regularization

### Auto-Recovery
- If divergence detected: reduce LR by 10x, restart from last checkpoint
- If NaN detected: reduce LR by 10x, enable gradient clipping, restart
- If plateau detected: reduce LR by 2x, continue

### Progress Reporting
- Per epoch: loss, metrics, time elapsed, ETA
- Per experiment: completed / total, aggregated results so far
- Summary: when all experiments complete

## Pipeline Checkpoints

The pipeline saves checkpoints after each phase. If interrupted, `/mr auto resume` continues from the last checkpoint.

Checkpoint data includes:
- All agent outputs up to the checkpoint
- Current KB state
- Experiment progress (if mid-experiment)
- Decisions made and their rationale

## Human Gates (--human-gates mode)

When `--human-gates` is active, the pipeline pauses at these decision points:

1. After idea selection (Phase 1): "Proceed with this direction?"
2. After venue selection (Phase 1): "Target this venue?"
3. After rapid prototype (Phase 2): "Continue with full experiments?"
4. After experiment results (Phase 3): "Results satisfactory?"
5. After review (Phase 6): "Ready for submission?"

At each gate, the system presents:
- What was done
- Key findings
- Automated recommendation
- Alternative options

The user can: approve, reject with feedback, or request more information.

## Usage Examples

```bash
# Full autonomous pipeline for GNN research
/mr auto "heterophily-aware dynamic graph anomaly detection"

# Pipeline with human approval at each gate
/mr auto "multi-scale temporal graph anomaly detection" --human-gates

# Target CCF-A, stop after experiments
/mr auto "causal graph anomaly detection" --target CCF-A --stop-at validate

# Check status
/mr auto status

# Resume after interruption
/mr auto resume
```

## Error Recovery

If any agent fails:
1. **Transient error** (API timeout, network): Retry up to 3 times with exponential backoff.
2. **Logic error** (agent output doesn't meet quality gate): Re-dispatch with refined input, including the specific failure reason.
3. **Resource error** (out of GPU memory, disk full): Alert human, suggest mitigation (reduce batch size, free disk space).
4. **Fundamental error** (hypothesis disproven): Flag to human with evidence and alternative directions from the KB.