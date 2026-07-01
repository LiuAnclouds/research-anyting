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

## 2026-06-30 — Code repo dead / archived at review time

- **Project**: gnn-dynamic (seed lesson)
- **Phase / round**: REVIEW r0
- **Locus**: manuscript/main.tex code-availability footnote (GitHub URL); the linked repository at review time.
- **Issue**: Paper cited a code URL that returned 404 (repo deleted) or was archived / read-only. Reproducibility auditor's HEAD-check catches it. Related failure mode: repo exists but `pushed_at` > 2 years ago, README empty, dependencies unpinned — technically alive, practically dead.
- **Axis that caught it**: `code-availability`
- **Fix**: `verify_baselines.py`-style HTTP HEAD + GitHub API `pushed_at` check on every reviewed manuscript; refuse the code-availability axis ≥60 without a live repo AND a README AND recent activity (< 2 years).
- **Generalization**: Cite-me-and-you-can-run-me is a hard promise. Every domain needs a scheduled repo-liveness scan since HEAD status decays with time. The check is cheap; the failure is expensive.

