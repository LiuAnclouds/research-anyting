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


---

<!-- seeded from _seed/generic-canonical-failures.md -->
## Seeded canonical failures (domain-agnostic)

The following class-of-bug lessons were pre-loaded from `knowledge-base/experts/_seed/generic-canonical-failures.md` on this domain's provisioning. They exist so this expert recognizes the general class of failure even before the current domain has encountered its own concrete instance.

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

