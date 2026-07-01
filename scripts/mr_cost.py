#!/usr/bin/env python3
"""
mr_cost.py -- Pretty-printed `/mr cost` report.

Thin wrapper over ``audit_budget_report.build_report`` (the existing roll-up
logic that walks ``knowledge-base/audit-rounds/*.json`` and sums per-round
token + USD spend). This module adds:

  * A Markdown-style header banner.
  * A phase table in canonical pipeline order (EXPLORE -> DESIGN -> VALIDATE
    -> ANALYZE -> WRITE -> REVIEW) instead of alphabetical.
  * A budget-remaining line when ``--budget USD`` is supplied.
  * A nicely formatted total line.

The actual cost arithmetic, model-rate table, and token defaults are NOT
re-derived here -- they live in ``audit_budget_report.py`` and are imported.
This file is intentionally presentation-only so that the cost numbers
match ``audit_budget_report`` exactly (any divergence would be a bug).

CLI:
    python scripts/mr_cost.py [--audit-dir PATH] [--budget USD] [--out report.json]

Exit 0 on success, 2 if --audit-dir is missing.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Import the existing roll-up logic. This script is presentation-only.
try:
    from audit_budget_report import build_report
except ImportError:
    # When invoked as `python scripts/mr_cost.py` from the plugin root, the
    # `scripts/` directory isn't on sys.path automatically. Inject it.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_budget_report import build_report


# Canonical phase order used by the pipeline. Unknown phases are appended
# alphabetically after this list so we never silently drop rows.
PHASE_ORDER = ["EXPLORE", "DESIGN", "VALIDATE", "ANALYZE", "WRITE", "REVIEW"]


def _ordered_phases(per_phase: dict[str, Any]) -> list[str]:
    seen = set(per_phase.keys())
    out = [p for p in PHASE_ORDER if p in seen]
    out += sorted(p for p in seen if p not in PHASE_ORDER)
    return out


def _fmt_tokens(n: int) -> str:
    """Format a token count as `~123k` (no decimals for >=10k, 1dp otherwise)."""
    k = n / 1000.0
    if k >= 10:
        return f"~{k:>4.0f}k tokens"
    return f"~{k:>4.1f}k tokens"


def _fmt_cost(c: float) -> str:
    return f"~${c:.2f}"


def _project_root_hint(audit_dir: Path) -> str:
    """Best-effort: report the directory that contains ``knowledge-base/``.

    The audit-dir is typically ``<project>/knowledge-base/audit-rounds`` --
    walk up two levels. If that doesn't look right (path too short, no
    ``knowledge-base`` segment) just return the absolute audit-dir.
    """
    p = audit_dir.resolve()
    parts = p.parts
    if len(parts) >= 2 and parts[-2] == "knowledge-base":
        return str(Path(*parts[:-2]))
    if len(parts) >= 1 and parts[-1] == "knowledge-base":
        return str(Path(*parts[:-1]))
    return str(p)


def format_report(report: dict[str, Any], budget: float | None = None) -> str:
    """Render the human-readable `/mr cost` report."""
    lines: list[str] = []
    lines.append("                    /mr cost report")
    lines.append("                    " + ("─" * 16))

    project = _project_root_hint(Path(report["audit_dir"]))
    pt = report["project_total"]
    total_cost = pt["cost_usd"]
    n_rounds = pt["rounds"]

    lines.append(f"Project: {project}")
    lines.append(
        f"Total estimated cost: ${total_cost:.2f} USD "
        f"across {n_rounds} audit round{'s' if n_rounds != 1 else ''}"
    )

    if report.get("skipped"):
        lines.append(f"  (skipped {len(report['skipped'])} unreadable file(s))")

    lines.append("")
    lines.append("By phase:")

    if not report["per_phase"]:
        lines.append("  (no audit rounds found)")
    else:
        # Column widths
        phases = _ordered_phases(report["per_phase"])
        for phase in phases:
            agg = report["per_phase"][phase]
            n = agg["rounds"]
            round_word = "round " if n == 1 else "rounds"
            lines.append(
                f"  {phase:8s}  {n:>2} {round_word}  "
                f"{_fmt_tokens(agg['tokens_total']):14s}  "
                f"{_fmt_cost(agg['cost_usd']):>8s}"
            )

    if budget is not None:
        remaining = budget - total_cost
        lines.append("")
        if remaining >= 0:
            lines.append(
                f"Budget remaining (--budget ${budget:.2f} set): ${remaining:.2f}"
            )
        else:
            lines.append(
                f"Budget OVERSPENT (--budget ${budget:.2f} set): "
                f"-${abs(remaining):.2f}"
            )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Pretty-printed `/mr cost` report over knowledge-base/audit-rounds/*.json"
    )
    ap.add_argument(
        "--audit-dir",
        default="knowledge-base/audit-rounds",
        help="directory of per-round audit JSON files",
    )
    ap.add_argument(
        "--budget",
        type=float,
        default=None,
        help="optional budget cap in USD; prints remaining balance",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="path to write the full JSON report (text report still goes to stdout)",
    )
    args = ap.parse_args(argv)

    audit_dir = Path(args.audit_dir)
    if not audit_dir.is_dir():
        print(f"mr_cost: no such directory: {audit_dir}", file=sys.stderr)
        return 2

    report = build_report(audit_dir)

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"# wrote JSON report to {args.out}")

    print(format_report(report, budget=args.budget))
    return 0


if __name__ == "__main__":
    sys.exit(main())
