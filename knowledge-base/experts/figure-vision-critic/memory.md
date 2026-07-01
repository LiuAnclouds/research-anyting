# figure-vision-critic — memory

Append-only log of figure visual-defect encounters.

---

## 2026-06-30 — TikZ architecture clipped (GNN-dynamic, fig:architecture)

- **Project**: gnn-dynamic
- **Slot**: fig:architecture, sections/03_method.tex
- **Defect**: `minimum width=18mm` too narrow; "ego-MLP" rendered as "ego-MI" and "+X skip" as "+X sk".
- **Axes that should have caught it**: `no-clipping` (CRIT, score<60) and `text-legibility` (CRIT).
- **Fix**: Width derived from longest-string width plus 2mm padding.
- **Generalization**: Always inspect the rendered PNG via Read. Never trust the source code alone — the renderer collapses Unicode metrics in ways the source doesn't reveal.

## 2026-06-30 — Only 2 figures in 20-page CCF-B manuscript

- **Project**: gnn-dynamic
- **Defect**: `figure-count` axis (on document-level figure-expert, not per-figure vision) flagged 2 < 6 for CCF-B.
- **Fix**: Expanded figure plan to 6 slots (architecture, main-results, ablation, sensitivity, correlation, qualitative).
- **Generalization**: CCF-B minimum is 6; CCF-A minimum is 8. Encoded in `schemas/figure-plan.json` `min_figures` field.


---

<!-- seeded from _seed/generic-canonical-failures.md -->
## Seeded canonical failures (domain-agnostic)

The following class-of-bug lessons were pre-loaded from `knowledge-base/experts/_seed/generic-canonical-failures.md` on this domain's provisioning. They exist so this expert recognizes the general class of failure even before the current domain has encountered its own concrete instance.

## 2026-06-30 — TikZ architecture figure text clipped ("ego-MLP" -> "ego-MI")

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: figures/architecture.tex node label at (3.2, -1.4); rendered `figures/architecture.pdf` bounding box.
- **Issue**: The node labeled "ego-MLP" in the architecture figure was clipped by the enclosing rectangle so the rendered PDF read "ego-MI". Two characters were silently truncated at compile time; the .tex source was fine. Every reviewer would read a made-up component name.
- **Axis that caught it**: `no-clipping` on figure-vision-critic (also `figure-vision-pass` on figure-expert)
- **Fix**: Widened the node's minimum width to `2.4cm` and re-rendered; added a vision-critic pass that OCRs the compiled PDF and diffs against the .tex-declared label set.
- **Generalization**: Do not trust the .tex source alone for figure content. The rendered artifact is the ground truth reviewers see. Every figure needs a post-render OCR-vs-declared-label check, in every domain — architecture diagrams, ROC curves with legends, box-plots with axis labels. Clipping and font substitution are silent failures.

