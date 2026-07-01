"""
Python ports + tests of 4 JS modules from research-anything/workflows/.

Ports just enough public API to validate algorithm invariants. No pytest;
plain assert + try/except driver. Writes JSON report and exits 0/1.
"""

import json
import math
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Port: _schema.js
# ---------------------------------------------------------------------------

REQUIRED_KEYS = ["name", "weight", "axes", "score"]


def weightedMean(axes: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    keys = list(axes.keys())
    if len(keys) == 0:
        return 0
    num = 0.0
    den = 0.0
    for k in keys:
        w = 1
        if weights is not None and k in weights and weights[k] is not None:
            w = weights[k]
        num += w * axes[k]
        den += w
    return 0 if den == 0 else num / den


def validateExpertVerdict(v: Dict[str, Any], idx: int = 0) -> bool:
    for k in REQUIRED_KEYS:
        if k not in v or v[k] is None:
            raise ValueError(f"expert[{idx}] missing required key '{k}'")
    w = v["weight"]
    if not isinstance(w, (int, float)) or isinstance(w, bool) or w < 0 or w > 100:
        raise ValueError(f"expert[{idx}] '{v['name']}' weight out of [0,100]")
    recompute = weightedMean(v["axes"], v.get("axis_weights"))
    if abs(recompute - v["score"]) > 0.5:
        raise ValueError(
            f"expert[{idx}] '{v['name']}' score={v['score']} != weighted_mean(axes)={recompute:.2f}"
        )
    has_high_axis = any(s >= 80 for s in v["axes"].values())
    if has_high_axis and (not v.get("evidence") or len(v["evidence"]) == 0):
        raise ValueError(f"expert[{idx}] '{v['name']}' has axis >= 80 but emitted no evidence")
    return True


# ---------------------------------------------------------------------------
# Port: _args.js
# ---------------------------------------------------------------------------


def _clamp(o: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(o["target"], (int, float)) or isinstance(o["target"], bool) or math.isnan(o["target"]):
        o["target"] = 90
    if not isinstance(o["maxRounds"], (int, float)) or isinstance(o["maxRounds"], bool) or math.isnan(o["maxRounds"]):
        o["maxRounds"] = 10
    o["target"] = max(50, min(100, o["target"]))
    o["maxRounds"] = max(1, min(20, o["maxRounds"]))
    return o


def parseArgs(args: Any) -> Dict[str, Any]:
    out = {
        "noAudit": False,
        "target": 90,
        "maxRounds": 10,
        "legacy": False,
        "humanGates": False,
        "stopAt": None,
        "parallel": None,
        "raw": args,
    }
    if args is None:
        return out

    if isinstance(args, str):
        tokens = args.strip().split()
        i = 0
        while i < len(tokens):
            t = tokens[i]

            def next_tok():
                nonlocal i
                i += 1
                return tokens[i] if i < len(tokens) else None

            if t == "--no-audit":
                out["noAudit"] = True
            elif t == "--legacy":
                out["legacy"] = True
            elif t == "--human-gates":
                out["humanGates"] = True
            elif t == "--target":
                try:
                    out["target"] = int(next_tok())
                except (TypeError, ValueError):
                    out["target"] = float("nan")
            elif t == "--max-rounds":
                try:
                    out["maxRounds"] = int(next_tok())
                except (TypeError, ValueError):
                    out["maxRounds"] = float("nan")
            elif t == "--stop-at":
                out["stopAt"] = next_tok()
            elif t == "--parallel":
                try:
                    out["parallel"] = int(next_tok())
                except (TypeError, ValueError):
                    out["parallel"] = None
            i += 1
        return _clamp(out)

    if isinstance(args, dict):
        if args.get("noAudit") is True or args.get("no-audit") is True:
            out["noAudit"] = True
        if isinstance(args.get("target"), (int, float)) and not isinstance(args.get("target"), bool):
            out["target"] = args["target"]
        if isinstance(args.get("maxRounds"), (int, float)) and not isinstance(args.get("maxRounds"), bool):
            out["maxRounds"] = args["maxRounds"]
        if isinstance(args.get("max-rounds"), (int, float)) and not isinstance(args.get("max-rounds"), bool):
            out["maxRounds"] = args["max-rounds"]
        if args.get("legacy") is True:
            out["legacy"] = True
        if args.get("useLegacy") is True:
            out["legacy"] = True
        if args.get("useLegacyReview") is True:
            out["legacy"] = True
        if args.get("humanGates") is True:
            out["humanGates"] = True
        if isinstance(args.get("stopAt"), str):
            out["stopAt"] = args["stopAt"]
        if isinstance(args.get("stop-at"), str):
            out["stopAt"] = args["stop-at"]
        if isinstance(args.get("parallel"), (int, float)) and not isinstance(args.get("parallel"), bool):
            out["parallel"] = args["parallel"]

    return _clamp(out)


# ---------------------------------------------------------------------------
# Port: _budget.js
# ---------------------------------------------------------------------------

MODEL_RATES = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5":  {"input": 1.00, "output":  5.00},
    "claude-opus-4-8":   {"input": 15.00, "output": 75.00},
    "claude-fable-5":    {"input": 2.00, "output": 10.00},
    "inherit":           {"input": 3.00, "output": 15.00},
}

DEFAULT_MODEL = "claude-sonnet-4-6"


def _rate_for(model: Optional[str]) -> Dict[str, float]:
    if not model:
        return MODEL_RATES[DEFAULT_MODEL]
    return MODEL_RATES.get(model, MODEL_RATES[DEFAULT_MODEL])


def _tokens_to_usd(in_tok: int, out_tok: int, model: Optional[str]) -> float:
    r = _rate_for(model)
    return (in_tok / 1e6) * r["input"] + (out_tok / 1e6) * r["output"]


def _round4(n: float) -> float:
    return round(n * 10000) / 10000


def estimateRoundCost(
    panel: Optional[List[Dict[str, Any]]] = None,
    executorTokens: Optional[Dict[str, int]] = None,
    expertAvgTokens: Optional[Dict[str, int]] = None,
    executorModel: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    if not isinstance(panel, list):
        raise ValueError("estimateRoundCost: panel must be an array")
    if executorTokens is None:
        executorTokens = {"input": 12000, "output": 4000}
    if expertAvgTokens is None:
        expertAvgTokens = {"input": 8000, "output": 2000}

    exec_in = int(executorTokens["input"])
    exec_out = int(executorTokens["output"])
    exec_cost = _tokens_to_usd(exec_in, exec_out, executorModel)

    experts = []
    experts_in_total = 0
    experts_out_total = 0
    experts_cost = 0.0
    for p in panel:
        m = p.get("model") or "inherit"
        in_ = int(expertAvgTokens["input"])
        out_ = int(expertAvgTokens["output"])
        c = _tokens_to_usd(in_, out_, m)
        experts.append({
            "name": p["name"],
            "model": m,
            "tokens_in": in_,
            "tokens_out": out_,
            "cost_usd": _round4(c),
        })
        experts_in_total += in_
        experts_out_total += out_
        experts_cost += c

    tokens_total = exec_in + exec_out + experts_in_total + experts_out_total
    cost_usd = exec_cost + experts_cost

    return {
        "tokens_total": tokens_total,
        "cost_usd": _round4(cost_usd),
        "breakdown": {
            "executor": {
                "model": executorModel,
                "tokens_in": exec_in,
                "tokens_out": exec_out,
                "cost_usd": _round4(exec_cost),
            },
            "experts": experts,
            "experts_subtotal": {
                "tokens_in": experts_in_total,
                "tokens_out": experts_out_total,
                "cost_usd": _round4(experts_cost),
            },
        },
    }


# ---------------------------------------------------------------------------
# Port: _prompts.js
# ---------------------------------------------------------------------------


def renderRevisePrompt(audit: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("## Audit feedback (must address before next round)")
    lines.append(
        f"Round {audit['round']}; aggregate={audit['aggregate']}; decision={audit['decision']}."
    )
    if audit.get("vetoes_global"):
        lines.append("\n### Vetoes (critical-axis failures)")
        for v in audit["vetoes_global"]:
            lines.append(
                f"- [{v['expert']}] axis '{v['axis']}' = {v['score_at_veto']} "
                f"(< {v['threshold']}). {v['reason']}"
            )
    if audit.get("blocking_findings"):
        lines.append("\n### Blocking findings")
        for f in audit["blocking_findings"]:
            tail = f"  -> fix: {f['fix_hint']}" if f.get("fix_hint") else ""
            lines.append(f"- axis={f['axis']}: {f['msg']}{tail}")
    if audit.get("advisory_findings"):
        lines.append("\n### Advisory (consider fixing)")
        for f in audit["advisory_findings"]:
            lines.append(f"- axis={f['axis']}: {f['msg']}")
    lines.append(
        "\nApply the Three-Times Rule (see shared/references/audit-doctrine.md) "
        "when revising any quantitative claim."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_weighted_mean_basic():
    got = weightedMean({"a": 80, "b": 100}, {"a": 2, "b": 1})
    # (2*80 + 1*100) / 3 = 260/3 = 86.666...
    assert abs(got - 86.67) < 0.01, f"expected ~86.67, got {got}"


def test_weighted_mean_empty():
    assert weightedMean({}, {}) == 0
    assert weightedMean({}, None) == 0


def test_weighted_mean_no_weights():
    got = weightedMean({"a": 80, "b": 100}, None)
    assert abs(got - 90.0) < 1e-9, f"expected 90.0, got {got}"
    got2 = weightedMean({"a": 60, "b": 90, "c": 30})
    assert abs(got2 - 60.0) < 1e-9, f"expected 60.0, got {got2}"


def test_validate_missing_required():
    bad = {"name": "x", "weight": 50, "axes": {"a": 50}}  # missing score
    try:
        validateExpertVerdict(bad, 0)
    except ValueError as e:
        assert "missing required key" in str(e), str(e)
        return
    raise AssertionError("expected ValueError for missing required key")


def test_validate_score_mismatch():
    bad = {
        "name": "x",
        "weight": 50,
        "axes": {"a": 50, "b": 50},
        "score": 99,  # actual weighted mean is 50
    }
    try:
        validateExpertVerdict(bad, 1)
    except ValueError as e:
        assert "weighted_mean" in str(e), str(e)
        return
    raise AssertionError("expected ValueError for score mismatch")


def test_validate_high_axis_no_evidence():
    bad = {
        "name": "x",
        "weight": 50,
        "axes": {"a": 85, "b": 85},
        "score": 85,
        "evidence": [],
    }
    try:
        validateExpertVerdict(bad, 0)
    except ValueError as e:
        assert "axis >= 80" in str(e), str(e)
        return
    raise AssertionError("expected ValueError for high axis without evidence")


def test_validate_valid_verdict():
    good = {
        "name": "x",
        "weight": 50,
        "axes": {"a": 85, "b": 85},
        "score": 85,
        "evidence": [{"source": "foo", "claim": "bar"}],
    }
    assert validateExpertVerdict(good, 0) is True


def test_parse_args_string_target_rounds():
    a = parseArgs("--target 95 --max-rounds 5")
    assert a["target"] == 95, a
    assert a["maxRounds"] == 5, a


def test_parse_args_string_flags():
    a = parseArgs("--no-audit --legacy")
    assert a["noAudit"] is True, a
    assert a["legacy"] is True, a


def test_parse_args_object_mode():
    a = parseArgs({"target": 85})
    assert a["target"] == 85, a
    assert a["maxRounds"] == 10, a  # default


def test_parse_args_clamp_target():
    a = parseArgs("--target 200")
    assert a["target"] == 100, a
    b = parseArgs("--target 1")
    assert b["target"] == 50, b


def test_parse_args_none():
    a = parseArgs(None)
    assert a["target"] == 90, a
    assert a["maxRounds"] == 10, a
    assert a["noAudit"] is False, a
    assert a["legacy"] is False, a
    assert a["stopAt"] is None, a


def test_budget_panel_breakdown_length():
    panel = [{"name": f"e{i}"} for i in range(5)]
    est = estimateRoundCost(panel=panel)
    assert len(est["breakdown"]["experts"]) == 5, est["breakdown"]["experts"]


def test_budget_inherit_maps_to_sonnet():
    panel_inherit = [{"name": "a", "model": "inherit"}]
    panel_sonnet = [{"name": "a", "model": "claude-sonnet-4-6"}]
    e1 = estimateRoundCost(panel=panel_inherit)
    e2 = estimateRoundCost(panel=panel_sonnet)
    c1 = e1["breakdown"]["experts"][0]["cost_usd"]
    c2 = e2["breakdown"]["experts"][0]["cost_usd"]
    assert abs(c1 - c2) < 1e-9, f"inherit ({c1}) should match sonnet ({c2})"


def test_budget_heavier_executor_costs_more():
    panel = [{"name": "a", "model": "claude-haiku-4-5"}]
    cheap = estimateRoundCost(panel=panel, executorModel="claude-haiku-4-5")
    pricey = estimateRoundCost(panel=panel, executorModel="claude-opus-4-8")
    assert pricey["cost_usd"] > cheap["cost_usd"], (
        f"opus executor ({pricey['cost_usd']}) should cost more than "
        f"haiku ({cheap['cost_usd']})"
    )
    # And: expert cost stays constant when only executor model changes.
    e_cheap = cheap["breakdown"]["experts"][0]["cost_usd"]
    e_pricey = pricey["breakdown"]["experts"][0]["cost_usd"]
    assert abs(e_cheap - e_pricey) < 1e-9


def test_revise_prompt_blocking():
    audit = {
        "round": 2,
        "aggregate": 78,
        "decision": "revise",
        "vetoes_global": [],
        "blocking_findings": [
            {"axis": "rigor", "msg": "Pearson r unverified", "fix_hint": "rerun"}
        ],
        "advisory_findings": [],
    }
    out = renderRevisePrompt(audit)
    assert "Blocking findings" in out, out
    assert "Three-Times Rule" in out, out


def test_revise_prompt_vetoes():
    audit = {
        "round": 3,
        "aggregate": 60,
        "decision": "revise",
        "vetoes_global": [
            {"expert": "rigor", "axis": "stats", "score_at_veto": 40,
             "threshold": 70, "reason": "p-hacking"}
        ],
        "blocking_findings": [],
        "advisory_findings": [],
    }
    out = renderRevisePrompt(audit)
    assert "Vetoes" in out, out
    assert "p-hacking" in out, out


def test_revise_prompt_ends_with_three_times_rule():
    audit = {
        "round": 1,
        "aggregate": 90,
        "decision": "pass",
        "vetoes_global": [],
        "blocking_findings": [],
        "advisory_findings": [],
    }
    out = renderRevisePrompt(audit)
    assert out.rstrip().endswith(
        "when revising any quantitative claim."
    ), repr(out[-120:])


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

TESTS = [
    ("weightedMean_basic", test_weighted_mean_basic),
    ("weightedMean_empty", test_weighted_mean_empty),
    ("weightedMean_no_weights", test_weighted_mean_no_weights),
    ("validate_missing_required", test_validate_missing_required),
    ("validate_score_mismatch", test_validate_score_mismatch),
    ("validate_high_axis_no_evidence", test_validate_high_axis_no_evidence),
    ("validate_valid_verdict", test_validate_valid_verdict),
    ("parseArgs_string_target_rounds", test_parse_args_string_target_rounds),
    ("parseArgs_string_flags", test_parse_args_string_flags),
    ("parseArgs_object_mode", test_parse_args_object_mode),
    ("parseArgs_clamp_target", test_parse_args_clamp_target),
    ("parseArgs_none", test_parse_args_none),
    ("budget_panel_breakdown_length", test_budget_panel_breakdown_length),
    ("budget_inherit_maps_to_sonnet", test_budget_inherit_maps_to_sonnet),
    ("budget_heavier_executor_costs_more", test_budget_heavier_executor_costs_more),
    ("renderRevisePrompt_blocking", test_revise_prompt_blocking),
    ("renderRevisePrompt_vetoes", test_revise_prompt_vetoes),
    ("renderRevisePrompt_ends_with_3x_rule", test_revise_prompt_ends_with_three_times_rule),
]


def main() -> int:
    passed: List[str] = []
    failed: List[Dict[str, str]] = []
    for name, fn in TESTS:
        try:
            fn()
            print(f"[OK] {name}")
            passed.append(name)
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
            failed.append({"name": name, "error": str(e),
                           "traceback": traceback.format_exc()})

    n_pass = len(passed)
    n_fail = len(failed)
    print(f"\n{n_pass} passed / {n_fail} failed (of {len(TESTS)})")

    report = {
        "suite": "js_modules_unit",
        "total": len(TESTS),
        "passed": n_pass,
        "failed": n_fail,
        "passed_names": passed,
        "failures": failed,
    }
    report_path = (
        r"C:/Users/kangjie.xu/.claude/plugins/research-anything/"
        r"tests/regression/js_modules_unit_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"report -> {report_path}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
