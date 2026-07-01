#!/usr/bin/env python3
"""
audit_diff.py — Diff two audit-round JSON records.

Given round N and round N+1 audit JSONs (per schemas/audit-v1.json),
emit a structured diff:
  - axes_improved:     [{expert, axis, delta, from, to}, ...]
  - axes_regressed:    [{expert, axis, delta, from, to}, ...]
  - new_blocking:      [{expert, axis, msg}, ...]
  - resolved_blocking: [{expert, axis, msg}, ...]
  - aggregate_delta:   number
  - veto_status:       {prev_vetoes, curr_vetoes, newly_vetoed, newly_unvetoed}

Used by audit-loop.js to render revise-prompts, and by humans inspecting
why a round regressed.

Usage:
  python audit_diff.py <round_n.json> <round_n+1.json> [--out diff.json]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def diff_audits(prev: dict, curr: dict) -> dict:
    prev_by_expert = {e["name"]: e for e in prev.get("experts", [])}
    curr_by_expert = {e["name"]: e for e in curr.get("experts", [])}

    improved, regressed = [], []
    new_blocking, resolved_blocking = [], []
    newly_vetoed, newly_unvetoed = [], []

    for name, curr_e in curr_by_expert.items():
        prev_e = prev_by_expert.get(name, {})
        prev_axes = prev_e.get("axes", {})
        curr_axes = curr_e.get("axes", {})
        for axis, curr_val in curr_axes.items():
            prev_val = prev_axes.get(axis)
            if prev_val is None:
                continue
            delta = round(curr_val - prev_val, 2)
            if delta >= 5:
                improved.append({"expert": name, "axis": axis,
                                  "delta": delta, "from": prev_val, "to": curr_val})
            elif delta <= -5:
                regressed.append({"expert": name, "axis": axis,
                                   "delta": delta, "from": prev_val, "to": curr_val})

        prev_blocking = {(f.get("axis"), f.get("msg")) for f in prev_e.get("blocking_findings", [])}
        curr_blocking = {(f.get("axis"), f.get("msg")) for f in curr_e.get("blocking_findings", [])}
        for axis, msg in curr_blocking - prev_blocking:
            new_blocking.append({"expert": name, "axis": axis, "msg": msg})
        for axis, msg in prev_blocking - curr_blocking:
            resolved_blocking.append({"expert": name, "axis": axis, "msg": msg})

        prev_vetoes = set(prev_e.get("vetoes", []) or [])
        curr_vetoes = set(curr_e.get("vetoes", []) or [])
        for v in curr_vetoes - prev_vetoes:
            newly_vetoed.append({"expert": name, "axis": v})
        for v in prev_vetoes - curr_vetoes:
            newly_unvetoed.append({"expert": name, "axis": v})

    aggregate_delta = round(curr.get("aggregate", 0) - prev.get("aggregate", 0), 2)

    return {
        "from_round": prev.get("round"),
        "to_round": curr.get("round"),
        "phase": curr.get("panel") or curr.get("phase"),
        "aggregate_delta": aggregate_delta,
        "aggregate_from": prev.get("aggregate"),
        "aggregate_to": curr.get("aggregate"),
        "axes_improved":  sorted(improved,  key=lambda x: -x["delta"]),
        "axes_regressed": sorted(regressed, key=lambda x:  x["delta"]),
        "new_blocking":      new_blocking,
        "resolved_blocking": resolved_blocking,
        "newly_vetoed":   newly_vetoed,
        "newly_unvetoed": newly_unvetoed,
        "decision_from": prev.get("decision"),
        "decision_to":   curr.get("decision"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prev", type=Path, help="Round N audit JSON")
    ap.add_argument("curr", type=Path, help="Round N+1 audit JSON")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    prev = json.loads(args.prev.read_text(encoding="utf-8"))
    curr = json.loads(args.curr.read_text(encoding="utf-8"))
    d = diff_audits(prev, curr)

    s = json.dumps(d, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(s, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(s + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
