# format-expert — memory

Append-only log of LaTeX format/compile encounters.

---

## 2026-06-30 — Broken \\ref{sec:prelim}, preliminaries commented out (AUDIT #4)

- **Project**: gnn-dynamic
- **Manuscript locus**: 01_introduction.tex line 20 (roadmap); 04_preliminaries.tex commented out in main.tex.
- **Axis that caught it**: `xref-resolved`. The static-check stand-in collects every `\\label{...}` and every `\\ref{...}` and diffs.
- **Fix**: Rewrote the roadmap to cite the actual sections that exist; deleted the sec:prelim sentence.
- **Generalization**: The label-vs-ref diff is one of the cheapest, most reliable checks. Should run on every WRITE round before the panel even starts (it's a wasted round if the manuscript doesn't compile cleanly).

## 2026-06-30 — Duplicate \\label{thm:variance} across method and theory (AUDIT #5)

- **Project**: gnn-dynamic
- **Manuscript locus**: 03_method.tex line 76 (Method preview); 04_theory.tex line 13 (Theory full).
- **Issue**: Same label on two different theorem statements; the bounds differ (Method omits the $\\|W\\|_2^2$ factor).
- **Axis that caught it**: `label-unique`. The static-check stand-in groups labels and reports any with >1 file:line.
- **Fix**: Renamed the Method preview to `prop:variance-preview` and downgraded it to a remark.
- **Generalization**: Cross-file label uniqueness is mandatory; pdflatex emits a "multiply defined" warning that the static check converts into a blocking finding.

## 2026-06-30 — TikZ architecture figure clipped: "ego-MLP" → "ego-MI", "+X skip" → "+X sk"

- **Project**: gnn-dynamic
- **Issue**: `minimum width=18mm` in the TikZ node was too narrow for the longest label string.
- **Axis that caught it (P0)**: `no-clipping` on `figure-vision-critic`. The format-expert can't catch this; only the per-figure vision pass on the rendered PNG can.
- **Fix**: Set `minimum width` to `width("longest label string") + 2mm` rather than a fixed mm; added 200 DPI PNG rasterization + Read+inspection.
- **Generalization**: TikZ width values pinned in mm are a smell. Prefer string-width-derived widths. This is documented in `agents/figure-renderer.md` "Anti-clipping defense" section.

## 2026-06-30 — "Anonymous Submission" placeholder shipped in early title

- **Issue**: Template placeholder reached PDF compile.
- **Axis that caught it**: `no-placeholder` regex sweep.
- **Generalization**: Every WRITE round runs the placeholder sweep before the panel; cheap to detect, expensive to ship.
