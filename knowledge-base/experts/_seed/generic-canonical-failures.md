# Generic Canonical Failures — expert-memory seed

Domain-agnostic class-of-bug encounters that every new domain's audit
experts should inherit on day one. When `/mr new-domain <slug>` provisions
a fresh domain, `scripts/domain_init_seed_memories.py` reads this file,
splits it into the 8 entries below, and appends each entry to every
expert whose `critical_axes` overlaps with the entry's `axis` tag.

The point: a brand-new domain's format-expert should already "know" that
`\ref{sec:prelim}` bugs happen even before that domain has audited its
first manuscript. The seed provides pre-loaded class-of-bug awareness.

Schema per entry (identical to individual expert `memory.md` files):

```
## YYYY-MM-DD — <one-line summary>
- **Project**: <repo/idea slug>
- **Phase / round**: <phase> r<N>
- **Locus**: <file:line list>
- **Issue**: <what was wrong>
- **Axis that caught it**: <axis name>   <-- machine-parsed; used for routing
- **Fix**: <what was changed>
- **Generalization**: <what this teaches about future runs>
```

Entries are ordered by the underlying class-of-bug, not chronology.
All dates below reference the GNN-dynamic post-mortem of 2026-06-30
because that is the incident from which these lessons were distilled.

---

## 2026-06-30 — Pearson r=-0.62 stale in 7 sections; raw data said r=-0.98

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0 (pre-audit, manual post-mortem)
- **Locus**: sections/00_abstract.tex; sections/01_introduction.tex; sections/02_related_work.tex; sections/04_theory.tex §4.3; sections/05_experiments.tex §5.4; sections/07_conclusion.tex; plus the C4 bullet in the intro lead paragraph.
- **Issue**: A single Pearson correlation `r=-0.62` between heterophily $h$ and ego-advantage was stated in seven places, all mutually consistent, none matching the raw `experiments/path_a/*.json` which recomputed to $r=-0.98$ vs GCN-vanilla and $r=-0.95$ vs TADDY-NE. No agent had been diffing numerics across sections, so the stale value propagated freely.
- **Axis that caught it**: `cross-section-equality`
- **Fix**: One sweep rewrote all seven loci to $-0.98$ / $-0.95$; added a `_global_` dataset bucket in the cross-section regression harness so paper-level scalars (single $r$, single $|\mu_2|$, single anomaly-rate interval) can no longer silently drop out of the cross-check.
- **Generalization**: Any headline scalar quoted in more than one section is a cross-section liability. The moment a value has no per-dataset home, it needs an explicit `_global_` bucket in the equality check, or the check silently skips it. Applies to every domain: single AUC, single accuracy, single latency number, single dollar cost — anything scalar-and-global.

## 2026-06-30 — TikZ architecture figure text clipped ("ego-MLP" -> "ego-MI")

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: figures/architecture.tex node label at (3.2, -1.4); rendered `figures/architecture.pdf` bounding box.
- **Issue**: The node labeled "ego-MLP" in the architecture figure was clipped by the enclosing rectangle so the rendered PDF read "ego-MI". Two characters were silently truncated at compile time; the .tex source was fine. Every reviewer would read a made-up component name.
- **Axis that caught it**: `no-clipping` on figure-vision-critic (also `figure-vision-pass` on figure-expert)
- **Fix**: Widened the node's minimum width to `2.4cm` and re-rendered; added a vision-critic pass that OCRs the compiled PDF and diffs against the .tex-declared label set.
- **Generalization**: Do not trust the .tex source alone for figure content. The rendered artifact is the ground truth reviewers see. Every figure needs a post-render OCR-vs-declared-label check, in every domain — architecture diagrams, ROC curves with legends, box-plots with axis labels. Clipping and font substitution are silent failures.

## 2026-06-30 — Bib aliases: 4 pairs of same-paper different-key

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: references.bib entries `kipf2017gcn` + `kipf2016semi` (same paper); `velic2018gat` + `velickovic2018graph`; `hamilton2017graphsage` + `hamilton2017inductive`; `xu2019gin` + `xu2018how`.
- **Issue**: Four paper duplicates lived in the .bib file under different keys, each cited from a different section. Reviewers saw what looked like eight distinct works but were four. Two entries also had subtly different titles because of a copy-paste from different arXiv listings, which would fail a DOI resolve.
- **Axis that caught it**: `cite-resolves`
- **Fix**: De-duplicated to canonical keys, re-pointed all `\cite{}` sites, added a `scripts/verify_citations.py` pass that resolves every BibTeX entry against Semantic Scholar / CrossRef and flags any two entries resolving to the same DOI.
- **Generalization**: A .bib file grown organically across sections will accumulate aliases. Every new domain needs an external-resolve gate at write-time. This is not a hallucination in the LLM sense — it is a hallucination in the manuscript sense: two entries claim to be different works, but they are not.

## 2026-06-30 — Baseline invented ("chen2024dudi", "wang2024gady")

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: sections/05_experiments.tex Table 3 rows 4 and 7; `\cite{chen2024dudi}` and `\cite{wang2024gady}`.
- **Issue**: Two baseline methods, "DUDI" and "GADY", were reported in the main results table with fabricated citations. No such papers exist on Semantic Scholar, arXiv, or DBLP. The rows had numeric AUC values that could not be traced to any run in `experiments/**`. Likely an LLM-drafted table that was never verified.
- **Axis that caught it**: `baseline-resolves`
- **Fix**: Both rows deleted; two real baselines (TADDY-NE, StrGNN) substituted with recomputed numbers from actual runs; `scripts/verify_baselines.py` added, which checks every baseline name against a cached external index and every reported cell against `experiments/baselines/**`.
- **Generalization**: Any baseline named in a results table must resolve to (a) a real paper AND (b) a real run. LLM-authored tables invent plausible-sounding names — "DUDI", "GADY", "MERIT-v2" — and pair them with plausible AUCs. Every domain needs a two-sided verify: external existence + local execution log.

## 2026-06-30 — Validation metric named three different ways (AUC vs AUC-PR vs AUC-ROC)

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: sections/03_method.tex line 128 ("validation AUC"); sections/05_experiments.tex line 34 ("validation AUC-PR"); Algorithm 1 caption ("validation AUC-ROC").
- **Issue**: The early-stopping signal was named three different ways in three places for what was supposed to be a single metric. Reviewers read this as either sloppiness or, worse, evidence of metric-shopping. In practice the code monitored AUC-PR; the other two mentions were stale from earlier drafts.
- **Axis that caught it**: `metric-fitness` (primary) and `cross-section-equality` (secondary)
- **Fix**: Standardized on "validation AUC-PR" across all three loci and code comments; added a phrase-level cross-section sweep with the regex `early[- ]?stop(?:ping)?[^\n]{0,80}?(AUC[- ]?(?:PR|ROC)?)` to the claim-trace harness.
- **Generalization**: Cross-section checks must cover phrase-level tokens, not just numerics. "Validation X" where X is a metric name is one class; "trained for N epochs" where N drifts is another; "evaluated on dataset Y" where Y renames across sections is another. Any domain with a training-loop story is exposed to this.

## 2026-06-30 — "Anonymous Submission" placeholder shipped

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: manuscript/main.tex line 3 (`\author{Anonymous Submission}`); acknowledgments section (`% TODO: add acks after de-anonymization`).
- **Issue**: A template placeholder `\author{Anonymous Submission}` and a stub acknowledgments block were about to ship in a camera-ready-track manuscript. In double-blind mode the placeholder is fine; in camera-ready it is a hard failure of submission requirements. A related class: `\todo{...}` macros and `XXX` markers left in prose.
- **Axis that caught it**: `no-placeholder` (also `no-anonymous-placeholder`)
- **Fix**: Wired author list and acknowledgments; added a format-expert grep pass for `Anonymous Submission`, `\todo`, `XXX`, `TBD`, `TODO`, `FIXME`, `\textcolor{red}` in prose.
- **Generalization**: Every LaTeX template ships with placeholder tokens. They must be swept before every submission, in every domain. The failure mode is not writing them (they come from the template) — it is forgetting to remove them. This is a checklist item, not a judgment call.

## 2026-06-30 — `\ref{sec:prelim}` undefined + duplicate `\label{thm:variance}`

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: sections/04_theory.tex line 12 (`\ref{sec:prelim}` with no matching `\label`); sections/04_theory.tex line 88 and sections/06_analysis.tex line 21 (both `\label{thm:variance}`).
- **Issue**: The compiled PDF showed a `??` for the missing preliminaries reference. Separately, two theorems shared the label `thm:variance`, so every `\ref{thm:variance}` resolved to whichever was last defined — silently, without a warning at the default LaTeX verbosity. The compile log had both issues buried among 40+ font warnings.
- **Axis that caught it**: `xref-resolved` and `label-unique`
- **Fix**: Added a preliminaries section with an explicit `\label{sec:prelim}`; renamed the analysis-section theorem to `thm:variance-analysis`; format-expert now greps the LaTeX aux/log for `LaTeX Warning: Reference` and `Label ... multiply defined` and blocks on either.
- **Generalization**: The LaTeX compiler is verbose enough to hide xref bugs in log noise. Every domain needs an explicit log-grep gate at `-halt-on-warning` strictness for the two known-blocking classes: undefined reference and duplicate label. Do not rely on humans reading the log.

## 2026-06-30 — Bold cell in tab:stability contradicts main-results table

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: sections/05_experiments.tex Table 2 (`tab:main_results`, bolded the "full model" column on Bitcoin-Alpha); sections/05_experiments.tex Table 4 (`tab:stability`, ablation bolded the "no-ego" column on Bitcoin-Alpha, i.e. the wrong direction).
- **Issue**: The main results table bolded "full model" as best; the stability ablation bolded "no-ego" as best on the same dataset with numerically indistinguishable values, but the narrative around the ablation still claimed "full model wins uniformly". The bold marker in the ablation table silently contradicted the story. A reviewer would either catch the contradiction or catch the ablation and disbelieve the main result.
- **Axis that caught it**: `ablation-narrative-consistency`
- **Fix**: Recomputed with 5 seeds, confirmed full model wins by 0.4 AUC-PR (not statistically indistinguishable), rebolded the ablation table; added an ablation-coherence check that reads bold-cell winners from both tables and diffs them against the paragraph-level "wins uniformly / mixed / loses" claim.
- **Generalization**: Bold cells in tables are load-bearing narrative claims — reviewers use them as a fast summary. Any ablation whose bolded winner disagrees with the main-results bolded winner needs an explicit narrative acknowledgment, or one of the two is wrong. Every domain with more than one results table needs this cross-table bold-winner consistency check.
