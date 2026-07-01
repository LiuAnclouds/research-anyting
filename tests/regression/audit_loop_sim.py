#!/usr/bin/env python3
"""
audit_loop_sim.py — End-to-end simulator for workflows/audit-loop.js.

Ports the audit-loop control flow (weightedMean / validateExpertVerdict /
aggregate / runAuditLoop) to pure Python, then drives it with a mocked
agent() that returns scripted expert verdicts keyed by (round, panel-member).

The point: prove the runtime semantics (panel weight sum == 100, weighted
aggregate, critical-axis veto, REVISE/PASS decision, escalation after
maxRounds) are correct without paying for a single LLM call. Three
scenarios cover the three load-bearing branches of the loop:

  1. Clean convergence  — REVISE -> PASS in 2 rounds; verifies the schema
                          shape mirrors schemas/audit-v1.json.
  2. Critical-axis veto — aggregate above threshold but one critical axis
                          < 60; decision MUST be REVISE and vetoes_global
                          MUST be non-empty.
  3. Escalation         — every round below target; loop must exit with
                          status=ESCALATED and last_three_rounds populated.

The 5-expert WRITE panel definition is copied verbatim from
workflows/paper-writing-pipeline.js (figure-expert / hallucination-expert /
format-expert / claim-trace-expert / prose-rigor-expert with weights
25/25/20/20/10) and the runner enforces totalWeight == 100.

Usage:
  python tests/regression/audit_loop_sim.py [--out PATH]

Exit codes:
  0  all 3 scenarios pass
  1  one or more scenarios failed
  2  simulator itself errored (bug in this script)
"""
from __future__ import annotations
import argparse, json, sys, traceback
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
DEFAULT_REPORT = HERE / "audit_loop_sim_report.json"


# ---------------------------------------------------------------------------
# Ported audit-loop primitives (mirror workflows/audit-loop.js).
# ---------------------------------------------------------------------------

REQUIRED_KEYS = ("name", "weight", "axes", "score")


def weighted_mean(axes: dict[str, float], weights: dict[str, float] | None) -> float:
    """Mirror of weightedMean() in audit-loop.js: missing weight -> 1."""
    keys = list(axes.keys())
    if not keys:
        return 0.0
    num = 0.0
    den = 0.0
    for k in keys:
        w = (weights or {}).get(k, 1)
        num += w * axes[k]
        den += w
    return 0.0 if den == 0 else num / den


def validate_expert_verdict(v: dict[str, Any], idx: int) -> bool:
    """Mirror of validateExpertVerdict(). Raises on shape / score / evidence
    violations, returns True on success."""
    for k in REQUIRED_KEYS:
        if v.get(k) is None:
            raise ValueError(f"expert[{idx}] missing required key '{k}'")
    w = v["weight"]
    if not isinstance(w, (int, float)) or w < 0 or w > 100:
        raise ValueError(f"expert[{idx}] '{v.get('name')}' weight out of [0,100]")
    recompute = weighted_mean(v["axes"], v.get("axis_weights"))
    if abs(recompute - v["score"]) > 0.5:
        raise ValueError(
            f"expert[{idx}] '{v['name']}' score={v['score']} != "
            f"weighted_mean(axes)={recompute:.2f}"
        )
    has_high = any(s >= 80 for s in v["axes"].values())
    if has_high and not v.get("evidence"):
        raise ValueError(
            f"expert[{idx}] '{v['name']}' has axis >= 80 but emitted no evidence"
        )
    return True


def aggregate(
    phase_name: str,
    round_idx: int,
    executor: str,
    results: list[dict[str, Any]],
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """Mirror of aggregate() in audit-loop.js."""
    total_w = sum(r["weight"] for r in results)
    if total_w != 100:
        raise ValueError(f"panel weights must sum to 100; got {total_w}")
    for i, r in enumerate(results):
        validate_expert_verdict(r, i)

    agg = sum(r["score"] * r["weight"] for r in results) / 100.0

    vetoes: list[dict[str, Any]] = []
    for r in results:
        for axis in r.get("critical_axes", []) or []:
            s = r["axes"].get(axis)
            if s is not None and s < 60:
                vetoes.append(
                    {
                        "axis": axis,
                        "expert": r["name"],
                        "reason": f"critical axis '{axis}' scored {s} < 60",
                        "score_at_veto": s,
                        "threshold": 60,
                    }
                )
        if isinstance(r.get("vetoes"), list):
            vetoes.extend(r["vetoes"])

    blocking: list[dict[str, Any]] = []
    advisory: list[dict[str, Any]] = []
    for r in results:
        blocking.extend(r.get("blocking_findings") or [])
        advisory.extend(r.get("advisory_findings") or [])

    target = ctx.get("target", 90)
    decision = "PASS" if (agg >= target and not vetoes) else "REVISE"

    return {
        "panel": phase_name,
        "round": round_idx,
        "timestamp": ctx.get("runStartedAt"),
        "executor_agent": executor,
        "experts": results,
        "aggregate": round(agg * 10) / 10,
        "aggregate_formula": "sum(expert.score * expert.weight) / 100",
        "decision": decision,
        "vetoes_global": vetoes,
        "blocking_findings": blocking,
        "advisory_findings": advisory,
        "diff_vs_previous_round": None,
    }


# ---------------------------------------------------------------------------
# Simulator class. Drives the loop with a mock agent().
# ---------------------------------------------------------------------------


class AuditLoopSim:
    """Pure-Python re-implementation of runAuditLoop() with an injected agent().

    The mock agent() is a callable taking (round, panel_member_name) and
    returning a dict-shaped expert verdict (no executor call -- the
    simulator only models the audit half of each round, which is the
    half that determines PASS / REVISE / ESCALATE).
    """

    def __init__(
        self,
        phase_name: str,
        executor: str,
        panel: list[dict[str, Any]],
        agent_fn: Callable[[int, str], dict[str, Any]],
        target: int = 90,
        max_rounds: int = 10,
        context: dict[str, Any] | None = None,
    ):
        if not isinstance(panel, list) or not (3 <= len(panel) <= 5):
            raise ValueError(f"panel must have 3-5 experts; got {len(panel)}")
        total = sum(p["weight"] for p in panel)
        if total != 100:
            raise ValueError(f"panel weights must sum to 100; got {total}")
        self.phase_name = phase_name
        self.executor = executor
        self.panel = panel
        self.agent_fn = agent_fn
        self.target = target
        self.max_rounds = max_rounds
        self.context = dict(context or {})
        self.context.setdefault("target", target)

    def _normalize(self, raw: dict[str, Any], panel_entry: dict[str, Any]) -> dict[str, Any]:
        """Mirror of normalizeExpertVerdict() in audit-loop.js."""
        v = dict(raw)
        v.setdefault("name", panel_entry["name"])
        v.setdefault("weight", panel_entry["weight"])
        if "critical_axes" not in v and panel_entry.get("critical_axes"):
            v["critical_axes"] = list(panel_entry["critical_axes"])
        v.setdefault("vetoes", [])
        v.setdefault("evidence", [])
        v.setdefault("blocking_findings", [])
        v.setdefault("advisory_findings", [])
        return v

    def run(self) -> dict[str, Any]:
        trace = {
            "phase": self.phase_name,
            "target": self.target,
            "maxRounds": self.max_rounds,
            "rounds": [],
        }
        for round_idx in range(1, self.max_rounds + 1):
            expert_results = []
            for p in self.panel:
                raw = self.agent_fn(round_idx, p["name"])
                expert_results.append(self._normalize(raw, p))
            audit = aggregate(
                self.phase_name,
                round_idx,
                self.executor,
                expert_results,
                {**self.context, "target": self.target},
            )
            trace["rounds"].append(audit)
            if audit["decision"] == "PASS":
                return {
                    "status": "PASS",
                    "round": round_idx,
                    "audit": audit,
                    "trace": trace,
                }
        escalation = {
            "status": "ESCALATED",
            "reason": f"Failed to reach target {self.target} after {self.max_rounds} rounds",
            "phase": self.phase_name,
            "last_three_rounds": trace["rounds"][-3:],
        }
        return {"status": "ESCALATED", "escalation": escalation, "trace": trace}


# ---------------------------------------------------------------------------
# WRITE panel definition (mirror of workflows/paper-writing-pipeline.js).
# Only the (name, weight, critical_axes) tuples are load-bearing here --
# the prompts are LLM-side and don't run in the simulator.
# ---------------------------------------------------------------------------

WRITE_PANEL = [
    {
        "name": "figure-expert",
        "weight": 25,
        "critical_axes": ["figure-count", "figure-vision-pass"],
    },
    {
        "name": "hallucination-expert",
        "weight": 25,
        "critical_axes": ["cite-resolves", "baseline-resolves", "dataset-resolves"],
    },
    {
        "name": "format-expert",
        "weight": 20,
        "critical_axes": ["latex-compile-clean", "xref-resolved", "label-unique", "no-placeholder"],
    },
    {
        "name": "claim-trace-expert",
        "weight": 20,
        "critical_axes": ["cross-section-equality", "traceable-to-experiments"],
    },
    {
        "name": "prose-rigor-expert",
        "weight": 10,
        "critical_axes": ["no-anonymous-placeholder"],
    },
]

# Sanity: runner enforces this, but assert at import time too.
assert sum(p["weight"] for p in WRITE_PANEL) == 100, (
    "WRITE panel weights must sum to 100"
)

# Reusable evidence stub (required when any axis >= 80).
_EVIDENCE = [
    {"type": "file", "uri": "manuscript/main.tex", "snippet": "stub-for-simulator"}
]


def _flat_verdict(
    name: str,
    weight: int,
    score: float,
    critical_axes: list[str],
    extra_axes: dict[str, float] | None = None,
    blocking: list[dict[str, Any]] | None = None,
    advisory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a verdict where every axis == score, so weighted_mean == score
    exactly. Optionally splice in extra axes (used for the veto scenario)."""
    # Anchor axes: one per critical_axes entry, plus two generic axes so we
    # always have >= 1 axis (schema requires minProperties=1).
    axes = {a: score for a in critical_axes}
    axes.setdefault("overall-quality", score)
    if extra_axes:
        axes.update(extra_axes)
    has_high = any(s >= 80 for s in axes.values())
    verdict: dict[str, Any] = {
        "name": name,
        "weight": weight,
        "axes": axes,
        "score": weighted_mean(axes, None),
        "critical_axes": critical_axes,
        "evidence": _EVIDENCE if has_high else [],
        "blocking_findings": blocking or [],
        "advisory_findings": advisory or [],
        "vetoes": [],
    }
    # Round score to 1 dp to keep the JSON tidy; tolerance is +/- 0.5.
    verdict["score"] = round(verdict["score"], 2)
    return verdict


# ---------------------------------------------------------------------------
# Scenario builders.
# ---------------------------------------------------------------------------


def scenario_1_agent(round_idx: int, name: str) -> dict[str, Any]:
    """Clean convergence: round 1 = 72 with blocking on cite-resolves,
    round 2 = 91 with no blocking."""
    panel_entry = next(p for p in WRITE_PANEL if p["name"] == name)
    if round_idx == 1:
        score = 72
        blocking = (
            [
                {
                    "axis": "cite-resolves",
                    "msg": "3 of 41 \\cite keys do not resolve in references.bib",
                    "fix_hint": "Add missing entries or fix typos.",
                }
            ]
            if name == "hallucination-expert"
            else []
        )
        return _flat_verdict(
            name, panel_entry["weight"], score, panel_entry["critical_axes"],
            blocking=blocking,
        )
    # round >= 2: PASS
    return _flat_verdict(
        name, panel_entry["weight"], 91, panel_entry["critical_axes"],
    )


def scenario_2_agent(round_idx: int, name: str) -> dict[str, Any]:
    """Critical veto: aggregate above threshold but format-expert's
    label-unique critical axis is 55 (< 60). Decision MUST be REVISE."""
    panel_entry = next(p for p in WRITE_PANEL if p["name"] == name)
    if name == "format-expert":
        # 4 critical axes; force label-unique=55, rest at 99 so weighted
        # mean = (55+99+99+99)/4 = 88.0, matching everyone else.
        axes = {
            "label-unique": 55,
            "latex-compile-clean": 99,
            "xref-resolved": 99,
            "no-placeholder": 99,
        }
        v = {
            "name": name,
            "weight": panel_entry["weight"],
            "axes": axes,
            "score": round(weighted_mean(axes, None), 2),  # = 88.0
            "critical_axes": panel_entry["critical_axes"],
            "evidence": _EVIDENCE,
            "blocking_findings": [
                {
                    "axis": "label-unique",
                    "msg": "duplicate \\label{fig:overview} in sections/02 and sections/04",
                }
            ],
            "advisory_findings": [],
            "vetoes": [],
        }
        return v
    return _flat_verdict(
        name, panel_entry["weight"], 88, panel_entry["critical_axes"],
    )


def scenario_3_agent(round_idx: int, name: str) -> dict[str, Any]:
    """Escalation: every round stalls at aggregate=70. After 10 rounds the
    runner must escalate. Axes deliberately below 80 -> no evidence needed,
    so the verdict shape stays minimal."""
    panel_entry = next(p for p in WRITE_PANEL if p["name"] == name)
    return _flat_verdict(
        name, panel_entry["weight"], 70, panel_entry["critical_axes"],
    )


# ---------------------------------------------------------------------------
# Schema-shape sanity check (mirrors schemas/audit-v1.json top-level required).
# ---------------------------------------------------------------------------

AUDIT_REQUIRED = {
    "panel", "round", "experts", "aggregate", "decision", "aggregate_formula",
}
PANEL_ENUM = {"EXPLORE", "DESIGN", "VALIDATE", "ANALYZE", "WRITE", "REVIEW"}


def conforms_to_audit_v1(audit: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for k in AUDIT_REQUIRED:
        if k not in audit:
            errors.append(f"missing required key '{k}'")
    if audit.get("panel") not in PANEL_ENUM:
        errors.append(f"panel '{audit.get('panel')}' not in {sorted(PANEL_ENUM)}")
    if audit.get("decision") not in ("PASS", "REVISE"):
        errors.append(f"decision '{audit.get('decision')}' not PASS/REVISE")
    if audit.get("aggregate_formula") != "sum(expert.score * expert.weight) / 100":
        errors.append("aggregate_formula mismatch")
    experts = audit.get("experts") or []
    if not (3 <= len(experts) <= 5):
        errors.append(f"experts length {len(experts)} not in [3,5]")
    for i, e in enumerate(experts):
        for k in ("name", "weight", "axes", "score"):
            if k not in e:
                errors.append(f"experts[{i}] missing '{k}'")
    agg = audit.get("aggregate")
    if not isinstance(agg, (int, float)) or not (0 <= agg <= 100):
        errors.append(f"aggregate {agg} not in [0,100]")
    return (not errors), errors


# ---------------------------------------------------------------------------
# Scenario runners.
# ---------------------------------------------------------------------------


def run_scenario_1() -> dict[str, Any]:
    sim = AuditLoopSim(
        phase_name="WRITE",
        executor="paper-writer",
        panel=WRITE_PANEL,
        agent_fn=scenario_1_agent,
        target=90,
        max_rounds=10,
    )
    result = sim.run()
    ok = True
    notes: list[str] = []

    if result["status"] != "PASS":
        ok = False
        notes.append(f"expected status=PASS, got {result['status']}")
    if result.get("round") != 2:
        ok = False
        notes.append(f"expected round=2, got {result.get('round')}")
    audit = result.get("audit") or {}
    conforms, errs = conforms_to_audit_v1(audit)
    if not conforms:
        ok = False
        notes.append("audit-v1 conformance errors: " + "; ".join(errs))
    if abs(audit.get("aggregate", 0) - 91) > 0.5:
        ok = False
        notes.append(f"expected aggregate ~= 91, got {audit.get('aggregate')}")
    if audit.get("decision") != "PASS":
        ok = False
        notes.append(f"expected final decision=PASS, got {audit.get('decision')}")
    # Round 1 must have been REVISE with blocking findings on cite-resolves.
    r1 = result["trace"]["rounds"][0]
    if r1["decision"] != "REVISE":
        ok = False
        notes.append(f"round 1 expected REVISE, got {r1['decision']}")
    if not any(f.get("axis") == "cite-resolves" for f in r1["blocking_findings"]):
        ok = False
        notes.append("round 1 missing cite-resolves blocking finding")
    return {
        "name": "scenario_1_clean_convergence",
        "ok": ok,
        "notes": notes,
        "status": result["status"],
        "round": result.get("round"),
        "round1_aggregate": result["trace"]["rounds"][0]["aggregate"],
        "round2_aggregate": (
            result["trace"]["rounds"][1]["aggregate"]
            if len(result["trace"]["rounds"]) > 1 else None
        ),
        "final_decision": audit.get("decision"),
        "audit_v1_conforms": conforms,
    }


def run_scenario_2() -> dict[str, Any]:
    # Critical veto. Use target=85 so aggregate=88 is "above threshold" yet
    # the veto still forces REVISE. maxRounds=1 so we get the audit object
    # directly without the agent ever returning a different verdict.
    sim = AuditLoopSim(
        phase_name="WRITE",
        executor="paper-writer",
        panel=WRITE_PANEL,
        agent_fn=scenario_2_agent,
        target=85,
        max_rounds=1,
    )
    result = sim.run()
    ok = True
    notes: list[str] = []

    audit = result["trace"]["rounds"][0]
    if abs(audit["aggregate"] - 88) > 0.5:
        ok = False
        notes.append(f"expected aggregate ~= 88, got {audit['aggregate']}")
    if audit["aggregate"] < sim.target:
        ok = False
        notes.append(
            f"expected aggregate ({audit['aggregate']}) >= target ({sim.target}) "
            "to prove veto overrides high score"
        )
    if audit["decision"] != "REVISE":
        ok = False
        notes.append(
            f"expected decision=REVISE despite high aggregate, got {audit['decision']}"
        )
    if not audit["vetoes_global"]:
        ok = False
        notes.append("expected vetoes_global non-empty, got []")
    if not any(
        v["axis"] == "label-unique" and v["expert"] == "format-expert"
        for v in audit["vetoes_global"]
    ):
        ok = False
        notes.append("expected veto on label-unique from format-expert")
    return {
        "name": "scenario_2_critical_veto",
        "ok": ok,
        "notes": notes,
        "aggregate": audit["aggregate"],
        "target": sim.target,
        "decision": audit["decision"],
        "vetoes_global": audit["vetoes_global"],
    }


def run_scenario_3() -> dict[str, Any]:
    sim = AuditLoopSim(
        phase_name="WRITE",
        executor="paper-writer",
        panel=WRITE_PANEL,
        agent_fn=scenario_3_agent,
        target=90,
        max_rounds=10,
    )
    result = sim.run()
    ok = True
    notes: list[str] = []

    if result["status"] != "ESCALATED":
        ok = False
        notes.append(f"expected status=ESCALATED, got {result['status']}")
    esc = result.get("escalation") or {}
    last3 = esc.get("last_three_rounds") or []
    if len(last3) != 3:
        ok = False
        notes.append(f"expected last_three_rounds length=3, got {len(last3)}")
    if len(result["trace"]["rounds"]) != 10:
        ok = False
        notes.append(
            f"expected 10 rounds in trace, got {len(result['trace']['rounds'])}"
        )
    # All rounds should report aggregate ~= 70 and decision REVISE.
    for r in result["trace"]["rounds"]:
        if abs(r["aggregate"] - 70) > 0.5:
            ok = False
            notes.append(f"round {r['round']} aggregate {r['aggregate']} != 70")
            break
        if r["decision"] != "REVISE":
            ok = False
            notes.append(f"round {r['round']} decision {r['decision']} != REVISE")
            break
    return {
        "name": "scenario_3_escalation",
        "ok": ok,
        "notes": notes,
        "status": result["status"],
        "rounds_run": len(result["trace"]["rounds"]),
        "last_three_rounds_len": len(last3),
    }


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_REPORT),
                    help="path to write JSON summary report")
    args = ap.parse_args()

    scenarios = []
    overall_ok = True
    try:
        for fn in (run_scenario_1, run_scenario_2, run_scenario_3):
            try:
                res = fn()
            except Exception as e:
                res = {
                    "name": fn.__name__,
                    "ok": False,
                    "notes": [f"raised: {e}", *traceback.format_exc().splitlines()],
                }
            scenarios.append(res)
            overall_ok = overall_ok and res.get("ok", False)
    except Exception:
        traceback.print_exc()
        return 2

    report = {
        "tool": "audit_loop_sim",
        "ported_from": "workflows/audit-loop.js",
        "panel": "WRITE (5 experts, weights 25/25/20/20/10, total=100)",
        "overall_ok": overall_ok,
        "scenarios": scenarios,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for s in scenarios:
        flag = "PASS" if s.get("ok") else "FAIL"
        print(f"[{flag}] {s['name']}")
        for note in s.get("notes", []):
            print(f"        - {note}")
    print(f"\nReport written to {out_path}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
