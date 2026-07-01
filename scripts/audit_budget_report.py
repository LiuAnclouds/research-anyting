#!/usr/bin/env python3
"""
audit_budget_report.py — Per-phase + per-project token/USD rollup over
audit-round JSON files.

Reads knowledge-base/audit-rounds/*.json (one file per round, as written
by workflows/audit-loop.js) and emits a cost report:
  - per-round    : tokens_in / tokens_out / cost_usd
  - per-phase    : sum across rounds of the same phase name
  - project_total: grand total

Token accounting uses a three-tier fallback (recorded in each row's
`source` field):
  1. "measured"  -- audit.meta.cost_breakdown is present. This is the
                    canonical shape written by workflows/audit-loop.js
                    (P4-B): {executor:{tokens_in,tokens_out,cost_usd,model},
                    experts:[{name,tokens_in,tokens_out,cost_usd,model}],
                    experts_subtotal:{...}}.
  2. "partial"   -- cost_breakdown absent, but the legacy per-verdict
                    `expert.meta.tokens.{input,output}` /
                    `audit.meta.executor_tokens` shape supplies some real
                    numbers (downstream tools may still write that shape).
  3. "estimated" -- nothing measured; fall back to _budget.js defaults
                    (8k in / 2k out per expert, 12k in / 4k out per executor).

CLI:
  python scripts/audit_budget_report.py [--audit-dir PATH] [--out report.json]

NOTE: The MODEL_RATES table below is duplicated from workflows/_budget.js.
KEEP IN SYNC: if you edit per-million prices here, edit them there too
(or vice versa). The two cannot import each other (JS vs Python), so
this duplication is intentional.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# KEEP IN SYNC with workflows/_budget.js MODEL_RATES.
# USD per 1M tokens, 2026-era Anthropic list pricing.
# "inherit" resolves to the dispatching agent's model; estimated as Sonnet.
# ---------------------------------------------------------------------------
MODEL_RATES: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6":  {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5":   {"input":  1.00, "output":  5.00},
    "claude-opus-4-8":    {"input": 15.00, "output": 75.00},
    "claude-fable-5":     {"input":  2.00, "output": 10.00},
    "inherit":            {"input":  3.00, "output": 15.00},
}
DEFAULT_MODEL = "claude-sonnet-4-6"

# Fallback token estimates when meta.tokens is absent. Match _budget.js.
EXEC_DEFAULT_IN, EXEC_DEFAULT_OUT     = 12000, 4000
EXPERT_DEFAULT_IN, EXPERT_DEFAULT_OUT = 8000,  2000


def rate_for(model: str | None) -> dict[str, float]:
    if not model:
        return MODEL_RATES[DEFAULT_MODEL]
    return MODEL_RATES.get(model, MODEL_RATES[DEFAULT_MODEL])


def tokens_to_usd(tok_in: int, tok_out: int, model: str | None) -> float:
    r = rate_for(model)
    return (tok_in / 1e6) * r["input"] + (tok_out / 1e6) * r["output"]


def _extract_expert_tokens_legacy(expert: dict[str, Any]) -> tuple[int, int, bool]:
    """Legacy fallback: read tokens from `expert.meta.tokens.{input,output}`.
    Return (tokens_in, tokens_out, was_measured)."""
    meta = expert.get("meta") or {}
    tokens = meta.get("tokens") or {}
    tin = tokens.get("input")
    tout = tokens.get("output")
    if isinstance(tin, (int, float)) and isinstance(tout, (int, float)):
        return int(tin), int(tout), True
    return EXPERT_DEFAULT_IN, EXPERT_DEFAULT_OUT, False


def _extract_executor_tokens_legacy(audit: dict[str, Any]) -> tuple[int, int, bool]:
    """Legacy fallback: read from `audit.meta.executor_tokens` /
    `audit.meta.executor.tokens`."""
    meta = audit.get("meta") or {}
    exec_tokens = (meta.get("executor_tokens")
                   or (meta.get("executor") or {}).get("tokens")
                   or {})
    tin = exec_tokens.get("input")
    tout = exec_tokens.get("output")
    if isinstance(tin, (int, float)) and isinstance(tout, (int, float)):
        return int(tin), int(tout), True
    return EXEC_DEFAULT_IN, EXEC_DEFAULT_OUT, False


def cost_round(audit: dict[str, Any]) -> dict[str, Any]:
    """Compute per-round cost from a single audit-round JSON.

    Three-tier fallback for token extraction:
      1. MEASURED  -- audit.meta.cost_breakdown present (what workflows/audit-loop.js
                      P4-B actually writes: {executor:{tokens_in,tokens_out,cost_usd,model},
                      experts:[{name,tokens_in,tokens_out,cost_usd,model}], experts_subtotal:{...}})
      2. PARTIAL   -- fall back to legacy `expert.meta.tokens` /
                      `audit.meta.executor_tokens` (downstream tools may still write this)
      3. ESTIMATED -- defaults from _budget.js (12k/4k executor, 8k/2k per expert)

    The `source` field ("measured"|"partial"|"estimated") records which tier
    was used for the row.
    """
    phase = audit.get("panel") or audit.get("phase") or "unknown"
    round_no = audit.get("round")
    meta = audit.get("meta") or {}
    cost_breakdown = meta.get("cost_breakdown")

    # ---------- tier 1: MEASURED via cost_breakdown ------------------------
    if isinstance(cost_breakdown, dict):
        cb_exec = cost_breakdown.get("executor") or {}
        exec_in = int(cb_exec.get("tokens_in") or 0)
        exec_out = int(cb_exec.get("tokens_out") or 0)
        exec_model = (cb_exec.get("model")
                      or meta.get("executor_model")
                      or audit.get("executor_model")
                      or DEFAULT_MODEL)
        # Prefer explicit cost_usd from breakdown if numeric; else recompute.
        cb_exec_cost = cb_exec.get("cost_usd")
        exec_cost = (float(cb_exec_cost)
                     if isinstance(cb_exec_cost, (int, float))
                     else tokens_to_usd(exec_in, exec_out, exec_model))
        exec_measured = True

        experts_out = []
        e_in_total = e_out_total = 0
        e_cost_total = 0.0
        measured_experts = 0
        for e in (cost_breakdown.get("experts") or []):
            model = e.get("model") or "inherit"
            tin = int(e.get("tokens_in") or 0)
            tout = int(e.get("tokens_out") or 0)
            c_val = e.get("cost_usd")
            c = (float(c_val) if isinstance(c_val, (int, float))
                 else tokens_to_usd(tin, tout, model))
            experts_out.append({
                "name": e.get("name"),
                "model": model,
                "tokens_in": tin,
                "tokens_out": tout,
                "cost_usd": round(c, 4),
                "measured": True,
            })
            e_in_total += tin
            e_out_total += tout
            e_cost_total += c
            measured_experts += 1

        source = "measured"

    else:
        # ---------- tiers 2 & 3: PARTIAL / ESTIMATED via legacy shape ------
        exec_model = (meta.get("executor_model")
                      or audit.get("executor_model")
                      or DEFAULT_MODEL)
        exec_in, exec_out, exec_measured = _extract_executor_tokens_legacy(audit)
        exec_cost = tokens_to_usd(exec_in, exec_out, exec_model)

        experts_out = []
        e_in_total = e_out_total = 0
        e_cost_total = 0.0
        measured_experts = 0
        for e in audit.get("experts", []) or []:
            model = ((e.get("meta") or {}).get("model")
                     or e.get("model")
                     or "inherit")
            tin, tout, measured = _extract_expert_tokens_legacy(e)
            c = tokens_to_usd(tin, tout, model)
            experts_out.append({
                "name": e.get("name"),
                "model": model,
                "tokens_in": tin,
                "tokens_out": tout,
                "cost_usd": round(c, 4),
                "measured": measured,
            })
            e_in_total += tin
            e_out_total += tout
            e_cost_total += c
            if measured:
                measured_experts += 1

        # "partial" = at least one measured slot; "estimated" = all defaults
        any_measured = exec_measured or measured_experts > 0
        all_measured = exec_measured and measured_experts == len(experts_out) and len(experts_out) > 0
        if all_measured:
            source = "partial"   # still not the preferred breakdown shape
        elif any_measured:
            source = "partial"
        else:
            source = "estimated"

    tokens_total = exec_in + exec_out + e_in_total + e_out_total
    cost_total = exec_cost + e_cost_total

    return {
        "phase": phase,
        "round": round_no,
        "source": source,
        "tokens_in":  exec_in + e_in_total,
        "tokens_out": exec_out + e_out_total,
        "tokens_total": tokens_total,
        "cost_usd": round(cost_total, 4),
        "executor": {
            "model": exec_model,
            "tokens_in": exec_in,
            "tokens_out": exec_out,
            "cost_usd": round(exec_cost, 4),
            "measured": exec_measured,
        },
        "experts": experts_out,
        "measured_experts": measured_experts,
        "total_experts": len(experts_out),
    }


def aggregate_phase(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tin = sum(r["tokens_in"]  for r in rows)
    tout = sum(r["tokens_out"] for r in rows)
    cost = sum(r["cost_usd"]   for r in rows)
    return {
        "rounds":      len(rows),
        "tokens_in":   tin,
        "tokens_out":  tout,
        "tokens_total": tin + tout,
        "cost_usd":    round(cost, 4),
    }


def build_report(audit_dir: Path) -> dict[str, Any]:
    files = sorted(audit_dir.glob("*.json"))
    per_round: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for f in files:
        # Skip explicit escalation summaries -- they re-cite the last three
        # rounds and would double-count.
        if "ESCALATION" in f.name:
            continue
        try:
            audit = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            skipped.append({"file": f.name, "error": str(e)})
            continue
        if not isinstance(audit, dict) or "experts" not in audit:
            skipped.append({"file": f.name, "error": "not an audit-round JSON"})
            continue
        row = cost_round(audit)
        row["file"] = f.name
        per_round.append(row)

    by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in per_round:
        by_phase[r["phase"]].append(r)
    per_phase = {p: aggregate_phase(rs) for p, rs in by_phase.items()}

    total_in   = sum(r["tokens_in"]  for r in per_round)
    total_out  = sum(r["tokens_out"] for r in per_round)
    total_cost = sum(r["cost_usd"]   for r in per_round)

    source_counts: dict[str, int] = defaultdict(int)
    for r in per_round:
        source_counts[r.get("source", "estimated")] += 1

    return {
        "audit_dir":   str(audit_dir),
        "files_scanned": len(files),
        "rounds_costed": len(per_round),
        "skipped":     skipped,
        "per_round":   per_round,
        "per_phase":   per_phase,
        "source_counts": dict(source_counts),
        "project_total": {
            "rounds":      len(per_round),
            "tokens_in":   total_in,
            "tokens_out":  total_out,
            "tokens_total": total_in + total_out,
            "cost_usd":    round(total_cost, 4),
        },
        "rate_table_version": "2026-budget-v1",
        "model_rates": MODEL_RATES,
    }


def _format_human(report: dict[str, Any]) -> str:
    lines = []
    lines.append(f"Audit-budget report  ({report['audit_dir']})")
    lines.append(f"  files scanned : {report['files_scanned']}")
    lines.append(f"  rounds costed : {report['rounds_costed']}")
    if report["skipped"]:
        lines.append(f"  skipped       : {len(report['skipped'])}")
    src = report.get("source_counts") or {}
    if src:
        lines.append(f"  sources       : "
                     f"measured={src.get('measured', 0)} "
                     f"partial={src.get('partial', 0)} "
                     f"estimated={src.get('estimated', 0)}")
    lines.append("")
    lines.append("Per phase:")
    for phase, agg in sorted(report["per_phase"].items()):
        ktok = agg["tokens_total"] / 1000
        lines.append(f"  {phase:30s}  rounds={agg['rounds']:>2}  "
                     f"~{ktok:>6.0f}k tok  ${agg['cost_usd']:>7.2f}")
    lines.append("")
    pt = report["project_total"]
    lines.append(f"PROJECT TOTAL: {pt['rounds']} rounds  "
                 f"~{pt['tokens_total']/1000:.0f}k tok  ${pt['cost_usd']:.2f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else "")
    ap.add_argument("--audit-dir", default="knowledge-base/audit-rounds",
                    help="directory of per-round audit JSON files")
    ap.add_argument("--out", default=None,
                    help="path to write the JSON report (default: stdout text)")
    args = ap.parse_args(argv)

    audit_dir = Path(args.audit_dir)
    if not audit_dir.is_dir():
        print(f"audit_budget_report: no such directory: {audit_dir}", file=sys.stderr)
        return 2

    report = build_report(audit_dir)

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {args.out}  "
              f"({report['rounds_costed']} rounds, "
              f"${report['project_total']['cost_usd']:.2f} total)")
    else:
        print(_format_human(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
