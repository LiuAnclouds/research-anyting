# Expert Memory Skeleton

This file is a placeholder for an audit expert's chronological memory.
Append entries in the schema below as the expert encounters issues.

```
## YYYY-MM-DD — <one-line summary>
- **Project**: <repo/idea slug>
- **Phase / round**: <phase> r<N>
- **Locus**: <file:line list>
- **Issue**: <what was wrong>
- **Axis that caught it**: <axis name>
- **Fix**: <what was changed>
- **Generalization**: <what this teaches about future runs>
```

Memory is read on each invocation; old entries are kept (no rotation in P1).
P2 will add semantic retrieval (sentence-transformers) so the expert
auto-surfaces relevant past entries instead of re-reading the whole file.


---

<!-- seeded from _seed/generic-canonical-failures.md -->
## Seeded canonical failures (domain-agnostic)

The following class-of-bug lessons were pre-loaded from `knowledge-base/experts/_seed/generic-canonical-failures.md` on this domain's provisioning. They exist so this expert recognizes the general class of failure even before the current domain has encountered its own concrete instance.

## 2026-06-30 — Venue monoculture in survey

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: EXPLORE r0
- **Locus**: literature/survey.md citation table (30 Tier-1 papers); shared/references/domain-quality-gates.md (venue distribution reference).
- **Issue**: Literature survey pulled 30 Tier-1 papers but 24/30 (80%) came from ICLR + NeurIPS. Missed a whole line of work published at TKDD, TPAMI, and Nature Communications. Field-specific venues systematically under-searched because the initial query set was seeded from PapersWithCode alone.
- **Axis that caught it**: `survey-bias-low`
- **Fix**: bias-auditor cross-tabulates the survey's venue histogram vs. the field's known venue distribution (per `shared/references/domain-quality-gates.md`) and flags when the top-3 venues account for >60% of citations.
- **Generalization**: PapersWithCode / OpenReview are dominant for LLM/CV but not for time-series (M4/M5 are workshop-only), medical imaging (MICCAI is field-native but under-indexed on those platforms), symbolic reasoning (JAIR is journal-only). Every domain has a "true venue distribution" that search-by-popularity biases against.

