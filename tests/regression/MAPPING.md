# P0 regression test — AUDIT.md issue → expert/axis mapping

Each row maps one of the 10 high-priority issues in
`D:/repo/GNN-dynamic/manuscript-backup/AUDIT.md` to which P0 expert and
axis should flag it. The regression harness (`p0_smoke.py`) implements
script-level stand-ins for each expert and runs them against the backup
manuscript; any "should-catch" row that fails to fire is a P0
calibration miss.

## High-priority issues (#1–#10)

| # | Issue (1-line) | Expert | Axis | P0 detection method | Expected outcome |
|---|---|---|---|---|---|
| 1 | Theorem 1 analyzes diff. architecture than Method (ego-MLP vs $[\hat A^K X W \| X]$) | (theory-expert, P1) | (architecture-equality) | none in P0 | **not-this-expert** — needs P1 theory panel |
| 2 | Theorem 2 worked-example numbers contradict $|\mu_2|=|1-2h|$ formula (h=0.05 vs 0.004; $\|\mu_2\|=0.9$ vs 0.992) | claim-trace-expert | cross-section-equality | scan numerics around "h" / "mu" tokens across `04_theory.tex` and `tab:datasets` in `05_experiments.tex`; flag a `(symbol, dataset)`-keyed value mismatch | **detect** at least the h=0.05 vs 0.004 disagreement |
| 3 | `tab:stability` bolds 0.013 as min but main-results has 0.009 | claim-trace-expert | cross-section-equality | numeric mismatch on Bitcoin-Alpha std (0.013 vs 0.009) across two tables | **detect** as numeric disagreement |
| 4 | `\ref{sec:prelim}` undefined (preliminaries section commented out) | format-expert | xref-resolved | regex collect `\label{...}` and `\ref{...}` keys, diff | **detect** as undefined reference |
| 5 | Duplicate `\label{thm:variance}` (Method and Theory both define it) | format-expert | label-unique | regex collect `\label{...}`, count duplicates | **detect** as duplicate label |
| 6 | Validation metric inconsistent (AUC vs AUC-PR vs AUC-ROC, three places) | claim-trace-expert | cross-section-equality | tokenized phrase match around "validation"+early-stop context | **detect** — phrase mismatch within same construct |
| 7 | UCI 71.1% contradicts "5–12% anomaly prevalence" rationale | claim-trace-expert | cross-section-equality | percentage extraction in dataset table vs the "5--12\%" string in `03_method.tex` | **detect** — 71.1% lies outside the [5,12] interval the prose declares |
| 8 | Bib aliases (zhu2020h2gcn↔zhu2020beyond, xu2025generaldy↔xu2025generaldyg, ekle2024dynamic↔ekle2024survey, oono2020graph↔oono2020asymptotic) | hallucination-expert | cite-resolves | `verify_citations.py` token-Jaccard tier (≥0.7) on title similarity | **detect** — 4 alias pairs |
| 9 | Theorem 1 proof unfaithful (linearization, normalization typo) | (theory-expert, P1) | (proof-soundness) | none in P0 | **not-this-expert** — needs P1 theory panel |
| 10 | "Outliers project onto high-frequency eigenvectors" hand-wavy, uncited | prose-rigor-expert | no-anonymous-placeholder (weakly) / (theory-expert) | regex for "we conjecture"+missing-cite is brittle in P0 | **not-this-expert** — needs P1 theory panel |

Plus extras the AUDIT.md mentions in passing but the P0 experts SHOULD also surface:

| # | Issue | Expert | Axis | Expected outcome |
|---|---|---|---|---|
| E1 | Pearson r=-0.62 stale, real value -0.98 / -0.95 (canonical Pearson incident) | claim-trace-expert | cross-section-equality | **detect** — would fire on a `(r, scope)`-keyed numeric mismatch between sections, BUT in the current backup the value has already been homogenized to -0.62 in all sections, so per-section equality holds. Detection requires a known-truth comparator (P1 RAG / data-file recompute). **P0 limitation: harness will instead inject a deliberate r=-0.62/-0.98 mismatch as a synthetic regression case to prove the cross-section check works.** |
| E2 | Eq. `eq:ego` duplicated across `03_method.tex` and `04_theory.tex` (L7) | format-expert | label-unique | **detect** — duplicate equation label |
| E3 | "Anonymous Submission" placeholder | format-expert | no-placeholder | placeholder regex | **detect** if present (was caught in last run; should be absent now — confirms cleanup) |

## Summary of expected P0 catches

- **format-expert** should catch: #4, #5, E2 (+ #14 placeholder, if seeded).
- **hallucination-expert / verify_citations.py** should catch: #8 (4 alias pairs).
- **claim-trace-expert** should catch: #2 (h numerics), #3 (std bold), #6 (val metric prose), #7 (71% vs 5-12%), E1 (synthetic Pearson injection).
- **figure-vision-critic**: not exercised against backup (no PNG diff harness for static fixture); covered separately if we re-render the TikZ.
- **prose-rigor-expert**: scans for "very/extremely/significantly outperforms"; backup AUDIT.md doesn't flag these as top-10 but the expert should still report any matches.

Issues that **cannot** be detected by P0 alone (require P1+ theory / soundness panels):
- #1 (architecture-vs-theory mismatch)
- #9 (proof linearization)
- #10 (hand-wavy uncited claim)

These are documented as P1 backlog items, not P0 misses.
