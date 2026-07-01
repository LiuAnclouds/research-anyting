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

## 2026-06-30 — Cherry-picked seeds inflate reported gap

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: ANALYZE r0
- **Locus**: sections/05_experiments.tex Table 2 caption ("mean ± std over 3 runs"); experiments/path_a/logs/ (5 completed seeds); hyperparameter-sweep log showing 5 finished runs.
- **Issue**: 5 seeds were run, only the 3 best were reported. The std reported was computed on the reported 3, hiding the actual seed variance. Cross-check against the hyperparameter-sweep logs showed 5 completed runs with std 3× the reported number. This is selective reporting, not a bookkeeping slip.
- **Axis that caught it**: `stat-test-correctness`
- **Fix**: Report ALL run seeds even if variance embarrasses; if some runs failed, state why explicitly. Statistics-expert now diffs the seed count in the results table against the run-log seed count and refuses ≥60 without a match.
- **Generalization**: Any domain reporting mean±std needs a companion "seeds actually reported" count. Selective reporting is a scientific-misconduct risk, not a stylistic choice — every panel with a statistics slot must gate on this.

