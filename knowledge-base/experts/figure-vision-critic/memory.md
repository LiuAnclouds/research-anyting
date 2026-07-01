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
