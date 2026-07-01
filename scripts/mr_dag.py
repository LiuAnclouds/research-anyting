#!/usr/bin/env python3
"""
mr_dag.py -- Render the 6-phase x 5-expert Moon-Research pipeline as an
ASCII tree.

The DAG is hardcoded here (not introspected) -- it mirrors the audit
panels declared in ``agents/moon-pipeline.md``. The temperature-rotation
table is ported from ``workflows/audit-loop.js`` (TEMP_ANCHORS,
TEMP_ADVERSARIES) so the annotations match what the audit loop actually
applies at runtime.

If ``knowledge-base/_state.json`` is present and contains a recognizable
phase pointer (``state.current_phase`` or ``state.phase``), the matching
phase row is marked with ``◀── HERE`` (or ``<-- HERE`` when --no-color).

CLI:
    python scripts/mr_dag.py [--state PATH] [--no-color]

Exit 0.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Temperature-rotation table -- PORT of workflows/audit-loop.js
# (TEMP_ANCHORS / TEMP_ADVERSARIES). KEEP IN SYNC. Everything not in either
# set is a default critic at T=0.5 and receives no annotation.
# ---------------------------------------------------------------------------
TEMP_ANCHORS = {
    "statistics",
    "format-expert",
    "claim-trace-expert",
    "cross-section-consistency",
    "hallucination-expert",
    "complexity",
    "protocol-reproducibility",
}
TEMP_ADVERSARIES = {
    "devils-advocate",
    "bias-auditor",
}


def temp_role(name: str) -> tuple[str, float] | None:
    """Return (annotation, temperature) for special-role experts; None for critics."""
    if name in TEMP_ANCHORS:
        return ("anchor", 0.2)
    if name in TEMP_ADVERSARIES:
        return ("adversary", 0.9)
    return None


# ---------------------------------------------------------------------------
# Pipeline DAG -- mirrors agents/moon-pipeline.md panels verbatim.
# Each phase: (name, gate_label, next_phase, [(expert, weight, [critical_axes])])
# ---------------------------------------------------------------------------
PIPELINE: list[dict[str, Any]] = [
    {
        "phase": "EXPLORE",
        "gate":  "G1: panel >=90",
        "next":  "DESIGN",
        "experts": [
            ("survey-completeness",  30, ["tier1-coverage"]),
            ("gap-identification",   25, ["gap-novelty"]),
            ("taxonomy",             20, ["mece-coverage"]),
            ("bias-auditor",         15, ["survey-bias-low"]),
            ("kb-integrator",        10, ["kb-frontmatter-valid"]),
        ],
    },
    {
        "phase": "DESIGN",
        "gate":  "G2: panel >=90",
        "next":  "VALIDATE",
        "experts": [
            ("novelty",               25, ["novelty-delta"]),
            ("theoretical-soundness", 25, ["assumption-realism", "theorem-arch-match"]),
            ("motivation-coherence",  20, ["motivation-alignment"]),
            ("complexity",            15, ["complexity-stated"]),
            ("feasibility",           15, ["budget-fit"]),
        ],
    },
    {
        "phase": "VALIDATE",
        "gate":  "G3: panel >=90",
        "next":  "ANALYZE",
        "experts": [
            ("experimental-design",      25, ["ablation-coverage"]),
            ("baseline-selection",       25, ["baseline-strength", "baseline-fidelity"]),
            ("metric-validity",          20, ["metric-fitness"]),
            ("dataset-fitness",          15, ["dataset-claim-fit"]),
            ("protocol-reproducibility", 15, ["protocol-stated"]),
        ],
    },
    {
        "phase": "ANALYZE",
        "gate":  "G4: panel >=90",
        "next":  "WRITE",
        "experts": [
            ("statistics",                30, ["stat-test-correctness"]),
            ("claim-evidence",            25, ["recompute-match", "claim-cell-traceability"]),
            ("ablation-coherence",        15, ["ablation-narrative-consistency"]),
            ("failure-case",              15, ["failure-coverage"]),
            ("cross-section-consistency", 15, ["cross-section-equality"]),
        ],
    },
    {
        "phase": "WRITE",
        "gate":  "G5: panel >=90",
        "next":  "REVIEW",
        "experts": [
            ("figure-expert",         25, ["figure-count", "figure-vision-pass"]),
            ("hallucination-expert",  25, ["cite-resolves", "baseline-resolves", "dataset-resolves"]),
            ("format-expert",         20, ["latex-compile-clean", "xref-resolved", "label-unique", "no-placeholder"]),
            ("claim-trace-expert",    20, ["cross-section-equality", "traceable-to-experiments"]),
            ("prose-rigor-expert",    10, ["no-anonymous-placeholder"]),
        ],
    },
    {
        "phase": "REVIEW",
        "gate":  "G6: panel >=90",
        "next":  "DONE",
        "experts": [
            ("r1-methodology",  25, ["soundness", "novelty"]),
            ("r2-experiments",  25, ["empirical-rigor", "ablation-coverage"]),
            ("eic",             20, ["scope-fit", "presentation"]),
            ("reproducibility", 15, ["code-availability", "data-availability"]),
            ("devils-advocate", 15, ["counterexample", "ablation-attack"]),
        ],
    },
]


def _load_state(state_path: Path | None) -> str | None:
    """Return the current phase name from a state file, if any."""
    if state_path is None or not state_path.is_file():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for key in ("current_phase", "phase", "active_phase"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    # Nested under "state": {...}
    nested = data.get("state")
    if isinstance(nested, dict):
        for key in ("current_phase", "phase", "active_phase"):
            v = nested.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip().upper()
    return None


def _format_axes(axes: list[str]) -> str:
    return ", ".join(axes)


def _format_expert_line(name: str, weight: int, axes: list[str],
                        is_last: bool) -> str:
    branch = "└" if is_last else "├"
    role = temp_role(name)
    role_tag = ""
    if role is not None:
        kind, temp = role
        role_tag = f"        [{kind} T={temp}]"
    return (
        f"    │           {branch} {name:<22s} ({weight}, CRIT: {_format_axes(axes)})"
        f"{role_tag}"
    )


def render(pipeline: list[dict[str, Any]], current_phase: str | None,
           use_color: bool) -> str:
    here_token = "◀── HERE" if use_color else "<-- HERE"
    lines: list[str] = []
    lines.append("                    /mr dag — pipeline graph")
    lines.append("                    " + ("─" * 24))
    lines.append("")

    for i, ph in enumerate(pipeline):
        is_current = (current_phase is not None
                      and ph["phase"] == current_phase)
        marker = f"  {here_token}" if is_current else ""
        header = f"  {ph['phase']:<8s} ──▶  [{ph['gate']}]  ──▶  {ph['next']}{marker}"
        lines.append(header)
        for j, (name, weight, axes) in enumerate(ph["experts"]):
            last = (j == len(ph["experts"]) - 1)
            lines.append(_format_expert_line(name, weight, axes, last))
        # Spacer between phases except after the last one.
        if i != len(pipeline) - 1:
            lines.append("    │")

    lines.append("")
    lines.append("Legend:")
    lines.append("  (weight, CRIT: axes)   weighted vote + critical-axis veto list")
    lines.append("  [anchor T=0.2]         low-temp deterministic auditor")
    lines.append("  [adversary T=0.9]      high-temp dissenting auditor")
    lines.append("  (no tag)               default critic, T=0.5")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Render the Moon-Research pipeline DAG as ASCII tree."
    )
    ap.add_argument(
        "--state",
        default="knowledge-base/_state.json",
        help="path to pipeline state file (default: knowledge-base/_state.json)",
    )
    ap.add_argument(
        "--no-color",
        action="store_true",
        help="suppress unicode arrows in the 'HERE' marker (still uses unicode "
             "for the box drawing chars in the tree)",
    )
    args = ap.parse_args(argv)

    state_path = Path(args.state) if args.state else None
    current = _load_state(state_path)

    print(render(PIPELINE, current, use_color=not args.no_color))
    return 0


if __name__ == "__main__":
    # Force UTF-8 on Windows stdout so the box-drawing chars (└├) and the
    # HERE-marker arrow (◀) don't crash under cp936/gbk. Best-effort.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
