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

## 2026-06-30 — Pearson r=-0.62 stale in 7 sections; raw data said r=-0.98

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: WRITE r0 (pre-audit, manual post-mortem)
- **Locus**: sections/00_abstract.tex; sections/01_introduction.tex; sections/02_related_work.tex; sections/04_theory.tex §4.3; sections/05_experiments.tex §5.4; sections/07_conclusion.tex; plus the C4 bullet in the intro lead paragraph.
- **Issue**: A single Pearson correlation `r=-0.62` between heterophily $h$ and ego-advantage was stated in seven places, all mutually consistent, none matching the raw `experiments/path_a/*.json` which recomputed to $r=-0.98$ vs GCN-vanilla and $r=-0.95$ vs TADDY-NE. No agent had been diffing numerics across sections, so the stale value propagated freely.
- **Axis that caught it**: `cross-section-equality`
- **Fix**: One sweep rewrote all seven loci to $-0.98$ / $-0.95$; added a `_global_` dataset bucket in the cross-section regression harness so paper-level scalars (single $r$, single $|\mu_2|$, single anomaly-rate interval) can no longer silently drop out of the cross-check.
- **Generalization**: Any headline scalar quoted in more than one section is a cross-section liability. The moment a value has no per-dataset home, it needs an explicit `_global_` bucket in the equality check, or the check silently skips it. Applies to every domain: single AUC, single accuracy, single latency number, single dollar cost — anything scalar-and-global.

