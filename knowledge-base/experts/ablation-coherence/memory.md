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

## 2026-06-30 — Bold cell in tab:stability contradicts main-results table

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0
- **Locus**: sections/05_experiments.tex Table 2 (`tab:main_results`, bolded the "full model" column on Bitcoin-Alpha); sections/05_experiments.tex Table 4 (`tab:stability`, ablation bolded the "no-ego" column on Bitcoin-Alpha, i.e. the wrong direction).
- **Issue**: The main results table bolded "full model" as best; the stability ablation bolded "no-ego" as best on the same dataset with numerically indistinguishable values, but the narrative around the ablation still claimed "full model wins uniformly". The bold marker in the ablation table silently contradicted the story. A reviewer would either catch the contradiction or catch the ablation and disbelieve the main result.
- **Axis that caught it**: `ablation-narrative-consistency`
- **Fix**: Recomputed with 5 seeds, confirmed full model wins by 0.4 AUC-PR (not statistically indistinguishable), rebolded the ablation table; added an ablation-coherence check that reads bold-cell winners from both tables and diffs them against the paragraph-level "wins uniformly / mixed / loses" claim.
- **Generalization**: Bold cells in tables are load-bearing narrative claims — reviewers use them as a fast summary. Any ablation whose bolded winner disagrees with the main-results bolded winner needs an explicit narrative acknowledgment, or one of the two is wrong. Every domain with more than one results table needs this cross-table bold-winner consistency check.

