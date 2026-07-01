# claim-trace-expert — memory

Chronological log of class-of-bug encounters and the axis/finding that
caught them. Append-only; the expert re-reads this on each invocation as
long-term experience.

Schema per entry:

```
## YYYY-MM-DD — <one-line summary>
- **Project**: <repo/idea slug>
- **Phase / round**: <phase> r<N>
- **Manuscript locus**: <file:line list>
- **Issue**: <what was wrong>
- **Axis that caught it**: <axis name>
- **Fix**: <what was changed>
- **Generalization**: <what this teaches about future runs>
```

---

## 2026-06-30 — Pearson r=-0.62 stale in 7 sections; raw data said r=-0.98

- **Project**: gnn-dynamic
- **Phase / round**: WRITE r0 (pre-audit, manual post-mortem)
- **Manuscript locus**:
  - sections/00_abstract.tex
  - sections/01_introduction.tex (lead-paragraph and C4 bullet)
  - sections/02_related_work.tex (positioning)
  - sections/04_theory.tex §4.3
  - sections/05_experiments.tex §5.4
  - sections/07_conclusion.tex
- **Issue**: The Pearson correlation between heterophily $h$ and ego-advantage was reported as $r=-0.62$ in seven places, but recomputing from raw `experiments/path_a/*.json` gave $r=-0.98$ vs GCN-vanilla and $r=-0.95$ vs TADDY-NE. The stale value lived across the entire .tex tree because no agent diffs numerics across sections.
- **Axis that caught it**: `cross-section-equality`. The per-issue regression-test harness at `tests/regression/p0_smoke.py` proved this axis catches it: when the synthetic injection rewrites one section's $r$ value to $-0.62$ while another reads $-0.98$, the script-level claim-trace stand-in fires a blocking `pearson_r / _global_` finding with both loci.
- **Fix**: Replaced $-0.62$ with $-0.98$/$-0.95$ in all 7 loci in a single sweep.
- **Generalization**: Paper-level scalars (a single $r$, a single $|\mu_2|$, a single anomaly-rate interval) need a `_global_` dataset bucket because they aren't per-dataset. Without it the cross-section check silently drops them. See `tests/regression/p0_smoke.py:_classify_dataset` for the heuristic.

## 2026-06-30 — Three different validation metrics named in three places (AUDIT #6)

- **Project**: gnn-dynamic
- **Phase / round**: WRITE pre-audit
- **Manuscript locus**:
  - sections/03_method.tex line 128 ("validation AUC")
  - sections/05_experiments.tex line 34 ("validation AUC-PR")
  - Algorithm 1 caption ("validation AUC-ROC")
- **Issue**: Three different metrics named in three places for the same early-stopping signal. Reviewers treat this as either sloppiness or evidence of cherry-picking.
- **Axis that caught it**: `cross-section-equality` via the `EARLYSTOP_PHRASE_RE` sweep in the claim-trace stand-in.
- **Fix**: Standardized on "validation AUC-PR" everywhere.
- **Generalization**: Phrase-level cross-section checks (not just numeric) belong in claim-trace-expert. The pattern `early[- ]?stop(?:ping)?[^\n]{0,80}?(AUC[- ]?(?:PR|ROC)?)` is a starter; expand as more phrase-mismatches surface.

## 2026-06-30 — UCI 71% anomaly rate contradicts "5–12% prevalence" rationale (AUDIT #7)

- **Project**: gnn-dynamic
- **Phase / round**: WRITE pre-audit
- **Manuscript locus**: 03_method.tex lines 120-121 ("5--12\% anomaly prevalence") vs. 05_experiments.tex line 20 (UCI anomaly 71.1%).
- **Issue**: The pos_weight=5 rationale only makes sense for the two Bitcoin datasets; on UCI, anomalies are 71% (majority class), so the same `pos_weight` is wildly inappropriate.
- **Axis that caught it**: `cross-section-equality` via the declared-interval-violation check (a number outside the prose's declared interval is a contradiction).
- **Fix**: Added per-dataset pos_weight discussion in §3.5 and reframed the rationale.
- **Generalization**: Whenever the prose names a percentage RANGE, every dataset's actual percentage must fall inside that range. Encoded as the `interval_violation` finding in claim-trace stand-in.


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

