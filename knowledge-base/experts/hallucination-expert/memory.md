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
