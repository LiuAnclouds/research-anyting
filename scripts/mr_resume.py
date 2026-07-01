#!/usr/bin/env python3
"""
mr_resume.py -- print a human-friendly recovery plan from the Moon-Research
persistent state file (`knowledge-base/_state.json`, schema
`schemas/state-v1.json`).

Backs the `/mr resume` skill. Reads:
  1. `<kb-root>/_state.json`             (required; exit 4 if missing)
  2. The JSON pointed to by `last_audit_round_path` (or, if that path is
     missing, the most recent `*-<phase>-round*.json` under
     `<kb-root>/audit-rounds/` for the same phase).

Emits a structured recovery report to stdout (and optionally to JSON via
`--out`). Exit codes:

    0   normal (state read, plan printed)
    4   `_state.json` missing or unreadable
    5   `_state.json` present but malformed (missing required keys)

Usage:
    python scripts/mr_resume.py [--kb-root knowledge-base] [--out report.json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_NO_STATE = 4
EXIT_BAD_STATE = 5

REQUIRED_KEYS = ("project_root", "current_phase", "runStartedAt")


def _eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def load_state(kb_root: Path) -> dict[str, Any]:
    """Read _state.json or bail with exit 4 / 5."""
    sp = kb_root / "_state.json"
    if not sp.exists():
        _eprint(
            f"error: no Moon-Research state file at {sp}.\n"
            f"  This usually means no pipeline run has produced a verdict yet --\n"
            f"  run e.g. `/mr write` or `/mr auto` first, then re-invoke /mr resume."
        )
        sys.exit(EXIT_NO_STATE)
    try:
        state = json.loads(sp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        _eprint(f"error: failed to read/parse {sp}: {e}")
        sys.exit(EXIT_BAD_STATE)
    missing = [k for k in REQUIRED_KEYS if k not in state]
    if missing:
        _eprint(
            f"error: {sp} is missing required keys: {missing}\n"
            f"  See schemas/state-v1.json for the expected shape."
        )
        sys.exit(EXIT_BAD_STATE)
    return state


def _resolve_audit_path(
    state: dict[str, Any], kb_root: Path
) -> tuple[Path | None, str]:
    """Return (path, source-note) for the most recent audit-round JSON."""
    declared = state.get("last_audit_round_path")
    if declared:
        # `last_audit_round_path` is normally workspace-relative
        # (e.g. "knowledge-base/audit-rounds/2026-06-30-WRITE-round3.json").
        # Resolve it both relative to the project root and to cwd.
        candidates = [
            Path(declared),
            Path.cwd() / declared,
            kb_root.parent / declared,
        ]
        for c in candidates:
            if c.exists():
                return c, "from state.last_audit_round_path"
    # Fallback: scan knowledge-base/audit-rounds/*<phase>*round*.json.
    phase = state.get("current_phase", "")
    rd = kb_root / "audit-rounds"
    if not rd.exists():
        return None, f"no audit-rounds dir at {rd}"
    pat = re.compile(rf".*-{re.escape(phase)}-round(\d+)\.json$")
    matches: list[tuple[int, Path]] = []
    for p in rd.glob("*.json"):
        m = pat.match(p.name)
        if m:
            matches.append((int(m.group(1)), p))
    if not matches:
        return None, f"no *-{phase}-round*.json files under {rd}"
    matches.sort(key=lambda t: (t[0], t[1].stat().st_mtime), reverse=True)
    return matches[0][1], f"scanned {rd}, picked highest-round file"


def load_audit(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _format_findings(audit: dict[str, Any] | None, state: dict[str, Any]) -> list[str]:
    """Summarise unresolved blocking findings, grouped by axis."""
    src = (audit or {}).get("blocking_findings") or state.get(
        "blocking_findings_unresolved"
    ) or []
    if not src:
        return ["  (none)"]
    by_axis: dict[str, list[str]] = {}
    for f in src:
        axis = (f.get("axis") or "unknown") if isinstance(f, dict) else "unknown"
        msg = f.get("msg") if isinstance(f, dict) else str(f)
        by_axis.setdefault(axis, []).append(msg or "")
    lines = []
    for axis, msgs in sorted(by_axis.items()):
        head = msgs[0][:140] if msgs else ""
        suffix = f" (+{len(msgs)-1} more)" if len(msgs) > 1 else ""
        lines.append(f"  - axis={axis}: {head}{suffix}")
    return lines


def _format_vetoes(audit: dict[str, Any] | None, state: dict[str, Any]) -> list[str]:
    src = (audit or {}).get("vetoes_global") or state.get("vetoes_unresolved") or []
    if not src:
        return ["  (none)"]
    lines = []
    for v in src:
        if isinstance(v, dict):
            expert = v.get("expert", "?")
            axis = v.get("axis", "?")
            s = v.get("score_at_veto", "?")
            thr = v.get("threshold", 60)
            lines.append(f"  - {expert} / {axis} (score {s} < {thr})")
        else:
            lines.append(f"  - {v}")
    return lines


def _build_recommendation(
    state: dict[str, Any], audit: dict[str, Any] | None
) -> list[str]:
    """Lines for the 'Recommended next action' block."""
    phase = state.get("current_phase", "?")
    round_n = int(state.get("last_audit_round") or 0)
    rounds_remaining = max(0, 10 - round_n)
    decision = state.get("last_decision", "?")
    aggregate = state.get("last_aggregate")

    lines: list[str] = []

    if phase == "COMPLETE" or decision == "PASS":
        lines.append("  Pipeline reached PASS on its last audit round. Nothing to resume.")
        lines.append("  Inspect the manuscript and proceed to submission, or invoke")
        lines.append("  `/mr auto` again to advance to the next gate.")
        return lines

    if decision == "ESCALATED" or round_n >= 10:
        lines.append(
            "  Phase has spent all 10 rounds without reaching the target threshold."
        )
        lines.append(
            "  Recommended: do NOT keep looping. Either (a) abandon the phase and"
        )
        lines.append(
            "  invoke `/mr <next-phase> --legacy` to bypass, or (b) lower the"
        )
        lines.append(
            "  target via `--target N` (see suggestion below) if the remaining"
        )
        lines.append("  gap is acceptable for the venue tier.")
        return lines

    # Normal REVISE recovery.
    pipeline_cmd = {
        "EXPLORE": "py workflows/run-exploration-pipeline",
        "DESIGN":  "py workflows/run-design-pipeline",
        "VALIDATE": "py workflows/run-validate-pipeline",
        "ANALYZE": "py workflows/run-analyze-pipeline",
        "WRITE":   "py workflows/run-paper-writing-pipeline",
        "REVIEW":  "py workflows/run-review-pipeline",
    }.get(phase, f"py workflows/run-{phase.lower()}-pipeline")
    lines.append(f"  {pipeline_cmd} ... --target 90 --max-rounds {rounds_remaining}")
    lines.append(
        f"  ({round_n} round(s) already spent, {rounds_remaining} remaining of the"
        " 10-round cap)"
    )

    # --target N override suggestion: would the last aggregate already PASS at
    # a lower threshold?
    if isinstance(aggregate, (int, float)) and aggregate < 90:
        # Suggest the next 5-point step below the aggregate that still represents
        # a credible bar (e.g. 70 floor).
        suggestion = int(min(89, max(70, (aggregate // 5) * 5)))
        if suggestion < 90 and suggestion <= aggregate:
            lines.append("")
            lines.append(
                f"  To override target: --target {suggestion} (would PASS at"
                f" aggregate={aggregate} -> last round becomes acceptable; use only"
                f" when the venue tier permits a relaxed bar)"
            )
    return lines


def render_report(
    state: dict[str, Any], audit: dict[str, Any] | None, audit_source: str
) -> str:
    """Compose the human-friendly recovery plan as a single string."""
    lines: list[str] = []
    lines.append("=== /mr resume — recovery plan ===")
    lines.append(f"Project:       {state.get('project_root', '?')}")
    phase = state.get("current_phase", "?")
    round_n = state.get("last_audit_round", "?")
    lines.append(f"Last phase:    {phase}, round {round_n}")
    decision = state.get("last_decision", "?")
    aggregate = state.get("last_aggregate", "?")
    lines.append(f"Last decision: {decision}  (aggregate={aggregate})")
    cost = state.get("estimated_cost_usd_to_date")
    if isinstance(cost, (int, float)) and cost > 0:
        lines.append(f"Spend so far:  ~${cost:.2f}")
    if audit is None:
        lines.append(f"Audit JSON:    (unavailable -- {audit_source})")
    else:
        lines.append(f"Audit JSON:    {audit_source}")
    lines.append("")
    lines.append("Unresolved blocking findings:")
    lines.extend(_format_findings(audit, state))
    lines.append("Unresolved vetoes:")
    lines.extend(_format_vetoes(audit, state))
    lines.append("")
    lines.append("Recommended next action:")
    lines.extend(_build_recommendation(state, audit))
    return "\n".join(lines)


def build_machine_report(
    state: dict[str, Any], audit: dict[str, Any] | None, audit_source: str
) -> dict[str, Any]:
    return {
        "state": state,
        "audit_round_source": audit_source,
        "audit_round": audit,
        "summary": {
            "project_root": state.get("project_root"),
            "current_phase": state.get("current_phase"),
            "last_audit_round": state.get("last_audit_round"),
            "last_decision": state.get("last_decision"),
            "last_aggregate": state.get("last_aggregate"),
            "blocking_findings_count": len(
                (audit or {}).get("blocking_findings")
                or state.get("blocking_findings_unresolved")
                or []
            ),
            "vetoes_count": len(
                (audit or {}).get("vetoes_global")
                or state.get("vetoes_unresolved")
                or []
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mr_resume",
        description="Print a recovery plan from Moon-Research's _state.json.",
    )
    parser.add_argument(
        "--kb-root",
        default="knowledge-base",
        help="Knowledge-base root containing _state.json (default: knowledge-base)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to also write the structured report as JSON.",
    )
    args = parser.parse_args(argv)

    kb_root = Path(args.kb_root).resolve() if os.path.isabs(args.kb_root) else Path(
        args.kb_root
    )
    state = load_state(kb_root)
    audit_path, audit_source_note = _resolve_audit_path(state, kb_root)
    audit = load_audit(audit_path)
    audit_source = (
        f"{audit_path} ({audit_source_note})"
        if audit_path is not None
        else f"unresolved ({audit_source_note})"
    )

    print(render_report(state, audit, audit_source))

    if args.out:
        report = build_machine_report(state, audit, audit_source)
        try:
            Path(args.out).write_text(
                json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as e:
            _eprint(f"warning: failed to write --out {args.out}: {e}")

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
