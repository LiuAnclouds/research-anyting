# Audit Doctrine — The Three-Times Rule

> The contract every Moon-Research agent operates under after v2 (panel-audit upgrade).
> Cite this file from every agent's frontmatter (`rigor_contract: three-times-verified`)
> and from every audit-loop prompt. Do not paraphrase the rule — quote it.

---

## The rule (canonical wording)

No quantitative claim, citation, baseline name, dataset statistic, or causal
attribution may appear in your output unless you have personally cross-verified
it from **three independent loci**, each from a distinct class:

1. **Primary artifact** — the source table cell, code output, log file, or
   `.bib` entry it originates from. Quote the exact value with `file:line`.
2. **Independent recompute or external authority** — either
   (a) re-derived from raw data (`scripts/*.py` rerun or KB experiment record),
   or (b) confirmed against an external source via
   `scripts/paper_fetcher.py` (Semantic Scholar / arXiv / DBLP / CrossRef)
   or `WebFetch` against a Tier-1 venue page.
3. **Cross-section consistency** — the same number appears identically in
   every other section / figure / caption of the manuscript that references
   it. If it appears in 7 places, all 7 must read the same value.

If any one locus is missing, write `[UNVERIFIED: <claim>]` instead of the
claim. Do not paraphrase loci 1 and 2 — quote them. The Pearson r=−0.62 /
−0.98 incident is the canonical failure this rule prevents.

---

## The locus checklist (append to every executor's OUTPUT section)

For each quantitative claim in your output, append a footnote:

```
[^v]: locus-1=<file:line or table cell>;
      locus-2=<recompute cmd | url | DOI>;
      locus-3=<other sections where this exact value appears, file:line each>
```

Missing footnotes → the claim is rewritten as `[UNVERIFIED]` and the
WRITE-panel claim-trace-expert will block the round.

---

## What "three independent" means in practice

- **Independent** means the loci cannot all come from your own re-typing of the
  same source. If you wrote the number into the abstract, into Table 3, and
  into the conclusion, **that is one locus three times**. You need a primary
  data file, an external check, and a cross-section reference.
- A KB entry citing a paper is locus-2 only if the entry's
  `external_verified: true` is set. Otherwise it is at most locus-1.
- A `\cite{key}` resolves as locus-2 only if `verify_citations.py` confirms
  the key against DBLP / CrossRef / Semantic Scholar / arXiv.

---

## What "applies to" means

The Three-Times Rule binds:

- Every numeric value mentioned in prose, tables, figures, captions.
- Every cite key.
- Every named baseline / benchmark / dataset.
- Every causal attribution ("ego preservation causes the +7.5 AUC gain").
- Every claim of novelty ("first work to ..."), comparison ("outperforms",
  "comparable to"), or temporal ordering ("recent work shows").

It does NOT bind:

- Generic prose statements without numbers or named entities.
- Sentence connectives ("therefore", "however") that don't carry truth claims.
- Conjectures explicitly marked as conjectures (e.g. "we conjecture that ...").

---

## Audit consequences

Every panel (EXPLORE / DESIGN / VALIDATE / ANALYZE / WRITE / REVIEW) scores
a `rigor_compliance` axis (weight ≥10, **CRIT veto at < 60**). The axis
specifically checks:

1. Are all numerics footnoted with three loci?
2. Do the cited loci resolve (files exist, URLs return 2xx, KB entries
   referenced exist)?
3. Does locus-3 actually find the same value, or does the agent claim
   consistency that isn't real?

A single unverified claim that the agent failed to mark as `[UNVERIFIED]`
is sufficient to trigger the veto.

---

## Why this rule

The GNN-dynamic manuscript shipped with Pearson `r=−0.62` in 7 sections
while the underlying experimental data said `r=−0.98`. Every single one of
those 7 occurrences was internally consistent with the others (cross-section
"consistency" was satisfied — they all said −0.62). What was missing was
locus-2: nobody re-derived the value from the data file. The Three-Times
Rule makes the absence of locus-2 a structural defect that the
claim-trace-expert can mechanically catch, instead of relying on a human
spot-check after the PDF is rendered.

The rule is deliberately strict. It will produce more `[UNVERIFIED]` markers
in early rounds. That is the intended behavior — those markers are the
revise prompt to the executor in the next loop iteration.
