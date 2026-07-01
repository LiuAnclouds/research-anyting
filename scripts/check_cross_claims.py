#!/usr/bin/env python3
"""
check_cross_claims.py — Cross-claim contradiction checker.

Scans three sources for the SAME (metric, dataset, model) triple and flags
any numeric/phrase disagreement:

  1. manuscript/**/*.tex
  2. knowledge-base/insights/**/*.md
  3. experiments/** (json, csv) — values are the canonical ground truth.

When a disagreement is found, the manuscript/insight value MUST yield to
the experiments cell (locus-1 in the Three-Times Rule). This script
reports the disagreement; the writer agent fixes it.

Generalizes the static claim-trace stand-in inside
`tests/regression/p0_smoke.py` to operate at full repo scope (not just
section files in a single manuscript).

Usage:
  python scripts/check_cross_claims.py
      --manuscript D:/repo/GNN-dynamic/manuscript
      --insights   C:/.../plugins/research-anything/knowledge-base/insights
      --experiments D:/repo/GNN-dynamic/experiments
      [--out report.json]

Exit codes:
  0  no disagreements
  1  one or more disagreements
  2  bad arguments / missing roots
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from datetime import datetime, timezone


NUMERIC_RE = re.compile(r"(?P<num>[-+]?\d+\.\d+)(?P<pct>\s*\\?%)?")
JSON_CANDIDATE_KEYS = (
    "auc_roc", "auc-roc", "aucroc", "auc_pr", "auc-pr", "aucpr",
    "f1", "macro_f1", "precision", "recall", "ap", "average_precision",
    "pearson_r", "spearman_r", "kendall_tau",
    "heterophily", "anomaly_rate",
)


def _left(line: str, num_str: str, width: int = 40) -> str:
    i = line.find(num_str)
    return line[max(0, i - width): i] if i >= 0 else line[:width]


def _classify_metric(ctx: str) -> str | None:
    cl = ctx.lower()
    for kw, tag in (
        ("pearson", "pearson_r"),
        ("spearman", "spearman_r"),
        ("kendall", "kendall_tau"),
        (r"\\mu_2", "mu2"),
        ("|\\mu_2|", "mu2"),
        ("heterophily", "h"),
        ("$h=", "h"), ("$h ", "h"),
        ("anomaly rate", "anomaly_pct"),
        ("anomaly %", "anomaly_pct"),
        ("auc-roc", "auc_roc"),
        ("auc-pr", "auc_pr"),
        ("macro-f1", "macro_f1"),
        ("ap std", "ap_std"),
        ("std", "std"),
    ):
        if kw in cl:
            return tag
    return None


def _classify_dataset(ctx: str, metric: str | None) -> str | None:
    cl = ctx.lower()
    if "bitcoin-alpha" in cl or ("alpha" in cl and "bitcoin" in cl): return "alpha"
    if "bitcoin-otc"   in cl or ("otc"   in cl and "bitcoin" in cl): return "otc"
    if "uci" in cl or "collegemsg" in cl: return "uci"
    if "reddit" in cl: return "reddit"
    if "elliptic" in cl: return "elliptic"
    if "cora" in cl: return "cora"
    if "citeseer" in cl: return "citeseer"
    if metric in {"pearson_r", "spearman_r", "kendall_tau", "mu2"}:
        return "_global_"
    return None


def _classify_model(ctx: str) -> str | None:
    cl = ctx.lower()
    for kw, tag in (
        ("ego-only", "ego-only"), ("hat-dyad-dual", "hat-dyad-dual"),
        ("hat-dyad", "hat-dyad"),
        ("taddy-ne", "taddy-ne"), ("taddy-faithful", "taddy"),
        ("taddy", "taddy"),
        ("gcn-vanilla", "gcn-vanilla"), ("addgraph", "addgraph"),
        ("generaldyg", "generaldyg"), ("h2gcn", "h2gcn"),
    ):
        if kw in cl: return tag
    return None


def _scan_text(text: str, source: str) -> list[dict]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in NUMERIC_RE.finditer(line):
            num_str = m.group("num")
            try: val = float(num_str)
            except ValueError: continue
            left = _left(line, num_str)
            ctx = line[max(0, m.start() - 80): m.end() + 80]
            metric  = _classify_metric(left) or _classify_metric(ctx)
            dataset = _classify_dataset(ctx, metric)
            model   = _classify_model(ctx)
            if not metric or not dataset:
                continue
            out.append({
                "metric": metric, "dataset": dataset, "model": model,
                "value": val,
                "source": "tex" if source.endswith(".tex") else "md",
                "loc": f"{source}:{i}",
                "ctx": ctx[:160].strip(),
            })
    return out


def _scan_json(payload, source: str, _path=()) -> list[dict]:
    """Walk a JSON dump from experiments/**. Heuristic: any leaf number
    keyed by a recognized metric name is a triple candidate; dataset and
    model come from path keys."""
    out = []
    if isinstance(payload, dict):
        for k, v in payload.items():
            kp = _path + (str(k),)
            out.extend(_scan_json(v, source, kp))
    elif isinstance(payload, list):
        for i, v in enumerate(payload):
            out.extend(_scan_json(v, source, _path + (f"[{i}]",)))
    elif isinstance(payload, (int, float)):
        # find the metric/dataset/model in _path
        keys = [k.lower() for k in _path]
        metric = next((_classify_metric(k) for k in keys
                       if _classify_metric(k)), None)
        dataset = next((_classify_dataset(k, metric) for k in keys
                        if _classify_dataset(k, metric)), None)
        model = next((_classify_model(k) for k in keys
                      if _classify_model(k)), None)
        if metric and dataset:
            out.append({
                "metric": metric, "dataset": dataset, "model": model,
                "value": float(payload),
                "source": "json",
                "loc": f"{source}:" + ".".join(_path),
                "ctx": ".".join(_path),
            })
    return out


def collect(manuscript: Path | None, insights: Path | None,
            experiments: Path | None) -> tuple[list[dict], list[dict]]:
    """Scan the three source trees for numeric claims.

    Returns (observations, skipped) where `skipped` is a list of
    {file, reason} dicts for files that could not be read or parsed.
    Previously these failures were swallowed silently — now they surface
    in the final report so the caller can see why a file was ignored."""
    obs: list[dict] = []
    skipped: list[dict] = []
    if manuscript and manuscript.exists():
        for f in sorted(manuscript.rglob("*.tex")):
            try:
                obs.extend(_scan_text(f.read_text(encoding="utf-8", errors="replace"),
                                      str(f)))
            except Exception as e:
                skipped.append({"file": str(f), "reason": f"tex read/scan failed: {e}"})
    if insights and insights.exists():
        for f in sorted(insights.rglob("*.md")):
            try:
                obs.extend(_scan_text(f.read_text(encoding="utf-8", errors="replace"),
                                      str(f)))
            except Exception as e:
                skipped.append({"file": str(f), "reason": f"md read/scan failed: {e}"})
    if experiments and experiments.exists():
        for f in sorted(experiments.rglob("*.json")):
            try:
                obs.extend(_scan_json(json.loads(f.read_text(encoding="utf-8",
                                                             errors="replace")),
                                      str(f)))
            except Exception as e:
                skipped.append({"file": str(f), "reason": f"json parse/scan failed: {e}"})
    return obs, skipped


def diff(obs: list[dict]) -> list[dict]:
    buckets: dict[tuple, list[dict]] = {}
    for o in obs:
        k = (o["metric"], o["dataset"], o.get("model") or "_any_")
        buckets.setdefault(k, []).append(o)

    findings = []
    for (metric, dataset, model), rows in buckets.items():
        # group by value within tolerance
        groups: list[tuple[float, list[dict]]] = []
        for r in rows:
            placed = False
            for sv, g in groups:
                tol = max(0.005, abs(sv) * 0.005)
                if abs(r["value"] - sv) <= tol:
                    g.append(r); placed = True; break
            if not placed:
                groups.append((r["value"], [r]))
        if len(groups) > 1:
            # which group(s) include experiments/** loci?
            canonical = [v for v, g in groups
                         if any(o["source"] == "json" for o in g)]
            findings.append({
                "metric": metric, "dataset": dataset, "model": model,
                "values": [v for v, _ in groups],
                "canonical_from_experiments": canonical,
                "loci": [{"value": v, "n": len(g),
                           "locs": [o["loc"] for o in g][:6],
                           "ctx": g[0]["ctx"][:160],
                           "sources": sorted({o["source"] for o in g})}
                          for v, g in groups],
            })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript",  type=Path, default=None)
    ap.add_argument("--insights",    type=Path, default=None)
    ap.add_argument("--experiments", type=Path, default=None)
    ap.add_argument("--out",         type=Path, default=None)
    args = ap.parse_args()
    if not any([args.manuscript, args.insights, args.experiments]):
        ap.error("provide at least one of --manuscript / --insights / --experiments")

    obs, skipped = collect(args.manuscript, args.insights, args.experiments)
    findings = diff(obs)

    report = {
        "$schema": "moon-research/cross-claims-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_observations": len(obs),
        "n_disagreements": len(findings),
        "by_source": {
            "tex":  sum(1 for o in obs if o["source"] == "tex"),
            "md":   sum(1 for o in obs if o["source"] == "md"),
            "json": sum(1 for o in obs if o["source"] == "json"),
        },
        "skipped_files": skipped,
        "disagreements": findings,
    }
    s = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(s, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(s + "\n")

    print(f"\n{len(obs)} observations across "
          f"tex={report['by_source']['tex']} md={report['by_source']['md']} "
          f"json={report['by_source']['json']}; "
          f"{len(findings)} disagreement bucket(s); "
          f"{len(skipped)} file(s) skipped", file=sys.stderr)
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
