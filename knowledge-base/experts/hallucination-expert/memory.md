# hallucination-expert — memory

Append-only log of citation/baseline/dataset hallucination encounters.

---

## 2026-06-30 — Bib aliases: 4 pairs of same-paper-different-key (AUDIT #8)

- **Project**: gnn-dynamic
- **Bib file**: `D:/repo/GNN-dynamic/manuscript-backup/references.bib` (pre-fix snapshot)
- **Pairs detected**:
  - `zhu2020h2gcn` ↔ `zhu2020beyond` — same NeurIPS 2020 H2GCN paper.
  - `xu2025generaldy` ↔ `xu2025generaldyg` — same GeneralDyG paper.
  - `ekle2024dynamic` ↔ `ekle2024survey` — same Ekle dynamic-GAD survey.
  - `oono2020graph` ↔ `oono2020asymptotic` — same Oono & Suzuki over-smoothing paper.
- **Axis that caught it**: `cite-resolves` via `verify_citations.py`'s **token-Jaccard tier** (Jaccard ≥0.7 across normalized titles). Hash-collision tier did NOT catch these because the titles differ in subtitle.
- **Fix**: Pick one canonical key per paper; sweep `sections/*.tex` for the alias keys and rewrite.
- **Generalization**: The two-tier detection (hash + Jaccard) is what makes this expert robust. Even-more-different-subtitle aliases (Jaccard <0.7) need LLM-level inspection — not script-level. Add an LLM-callback path in P2.

## 2026-06-30 — Made-up baseline names

- **Project**: gnn-dynamic
- **Issue**: Two synthesized-looking entries — both with author lists not findable on Semantic Scholar/arXiv/DBLP — survived to manuscript:
  - `chen2024dudi` (DuDi)
  - `wang2024gady` (GADY synonyms)
- **Axis that caught it**: `cite-resolves` via paper_fetcher.py cross-checks (CrossRef and Semantic Scholar both returned no match within 0.6 Jaccard).
- **Fix**: Deleted the orphan bib entries.
- **Generalization**: Any new bib entry must hit at least one of {SS, arXiv, DBLP, CrossRef} with Jaccard ≥0.6 before being accepted. Network rate-limits on SS make CrossRef the primary fallback.

## 2026-06-30 — Semantic Scholar 429 rate-limits

- **Issue**: Anonymous bursts against the public Semantic Scholar API return HTTP 429 across 26 bib entries.
- **Mitigation**: Use `--source crossref` as primary on bulk runs; CrossRef has no anonymous burst limit.
- **P1 backlog**: Add SS API key support to `paper_fetcher.py`.


---

<!-- seeded from _seed/generic-canonical-failures.md -->
## Seeded canonical failures (domain-agnostic)

The following class-of-bug lessons were pre-loaded from `knowledge-base/experts/_seed/generic-canonical-failures.md` on this domain's provisioning. They exist so this expert recognizes the general class of failure even before the current domain has encountered its own concrete instance.

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

