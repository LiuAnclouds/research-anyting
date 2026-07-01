# CI validation harness

`scripts/ci_validate.py` is the single entry point that runs every blocking
regression check in the research-anything plugin. It aggregates the five
existing checks into one fail-fast pipeline and emits a JSON report at
`tests/regression/ci_validate_report.json` plus a summary table on stdout.

## What it runs

| # | Step | Source | Expected outcome on green |
|---|---|---|---|
| 1 | `migrate_agent_frontmatter.py --dry-run` | `scripts/` | **0 changes pending** — every agent already has current `panel`, `weight`, `rigor_contract`, `parallelism_contract`, and embedded prose. Exit 1 means an agent file drifted; run with `--apply` to fix. |
| 2 | `kb_audit_status_check.py` | `scripts/` | **KB clean** — every paper in `knowledge-base/papers/**/*.md` has a non-null `external_verified` field, with `verification_evidence` + ISO-8601 `verified_at` when verified, and every `[[wikilink]]` resolves to an entry on disk. |
| 3 | `lint_rigor.py <manuscript>` | `scripts/` | **Soft-fail lint pass** — checks the manuscript fixture (e.g. `D:/repo/GNN-dynamic/manuscript-backup`) for Three-Times Rule violations. Skipped if no manuscript is provided / the path is missing. Findings are informational; only a non-zero exit blocks. |
| 4 | `p0_smoke.py --no-network` | `tests/regression/` | **7/7 injections detected** — re-runs the static P0 panel against synthetic regressions (missing `\label`, duplicate labels, placeholder rows, cross-section r=-0.62 drift, etc.). |
| 5 | `audit_loop_sim.py` | `tests/regression/` | **3/3 scenarios pass** — exercises the audit-loop runtime (clean convergence, critical-axis veto, escalation) without making any LLM call. |

The runner gives each subprocess a hard 5-minute timeout and stops on the
first blocking failure (fail-fast). Skipped steps (e.g. `lint_rigor` with
no manuscript) do not count as red.

## Invoking manually

```bash
python scripts/ci_validate.py
python scripts/ci_validate.py --manuscript D:/repo/GNN-dynamic/manuscript-backup
python scripts/ci_validate.py --plugin-root C:/Users/kangjie.xu/.claude/plugins/research-anything
```

Exit `0` = green, `1` = at least one blocking step failed.

## Wiring as a pre-commit hook

There are two common ways; pick whichever matches the repo you commit
from. Both run from the repo root, so an absolute `--plugin-root`
keeps the hook portable.

### Option A — repo-local `.git/hooks/pre-commit`

Drop this in `.git/hooks/pre-commit` and `chmod +x` it:

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${RA_PLUGIN_ROOT:-$HOME/.claude/plugins/research-anything}"
MANUSCRIPT="${RA_MANUSCRIPT:-}"   # optional fixture override
ARGS=( --plugin-root "$PLUGIN_ROOT" )
[[ -n "$MANUSCRIPT" ]] && ARGS+=( --manuscript "$MANUSCRIPT" )
python "$PLUGIN_ROOT/scripts/ci_validate.py" "${ARGS[@]}"
```

This is per-clone (not versioned), but it has the fewest moving parts.

### Option B — versioned `.githooks/pre-commit`

Commit the hook script in-tree so every clone gets it after one
config line:

```bash
# In repo root, one-time setup:
git config core.hooksPath .githooks
```

Then add `.githooks/pre-commit`:

```bash
#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${RA_PLUGIN_ROOT:-$HOME/.claude/plugins/research-anything}"
exec python "$PLUGIN_ROOT/scripts/ci_validate.py" --plugin-root "$PLUGIN_ROOT" "$@"
```

`chmod +x .githooks/pre-commit` and commit both files.

### Bypass

Use `git commit --no-verify` only when the failure is unrelated to the
commit (e.g. a known-broken upstream manuscript fixture). Anything CI
blocks is meant to block.

## Expected outcome per check

When everything is healthy, the summary table should look like:

```
STEP                                 STATUS DURATION   SUMMARY
--------------------------------------------------------------------
migrate_agent_frontmatter --dry-run  PASS   1.2        0 changes pending
kb_audit_status_check                PASS   0.4        KB clean
lint_rigor                           SKIP   0.0        skipped (manuscript path not provided ...)
p0_smoke --no-network                PASS   3.8        all expected detections fired
audit_loop_sim                       PASS   0.3        3/3 scenarios pass
====================================================================
pass=4 fail=0 skipped=1 report=tests/regression/ci_validate_report.json
```

If any blocking step fails, the runner stops there, marks downstream
steps as `skipped (not run)`, and returns exit code 1 — the pre-commit
hook blocks the commit.
