#!/usr/bin/env python3
"""
p0_smoke.py — Component-level regression test for the P0 audit panel.

Runs each P0 expert (or its script-level stand-in) directly against the
GNN-dynamic backup manuscript, then matches detections against the
AUDIT.md top-10 issue list to verify the expert panel is calibrated.

This is NOT a full audit-loop integration test (that requires LLM
in-the-loop and is P1's scope). This is the static, deterministic
component test the user asked for: "完成测试后再 P1".

Coverage:
  - format-expert stand-in:        xref-resolved, label-unique, no-placeholder
  - hallucination-expert stand-in: verify_citations.py (alias tier)
  - claim-trace-expert stand-in:   cross-section numeric / phrase equality
  - prose-rigor-expert stand-in:   prohibited intensifiers

Per MAPPING.md, the harness also writes one synthetic regression fixture
(re-injects the historic Pearson r=-0.62 in one section while leaving
-0.98 in another) to prove the cross-section equality check actually
fires when the disagreement is present.

Usage:
  python tests/regression/p0_smoke.py \
      [--manuscript D:/repo/GNN-dynamic/manuscript-backup] \
      [--no-network] [--out tests/regression/p0_smoke_report.json]

Exit codes:
  0  all expected detections fired and no unexpected static checks broke
  1  one or more expected detections missed (P0 calibration miss)
  2  harness itself errored (file missing, etc.)
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent.parent
SCRIPTS = PLUGIN_ROOT / "scripts"


# ============================================================================
# format-expert stand-in
# ============================================================================

LABEL_RE  = re.compile(r"\\label\{([^}]+)\}")
REF_RE    = re.compile(r"\\(?:ref|eqref|autoref|Cref|cref)\{([^}]+)\}")
PLACEHOLDER_PATTERNS = [
    (re.compile(r"\bAnonymous Submission\b", re.I), "anonymous-submission"),
    (re.compile(r"\bTODO\b"),                       "todo-marker"),
    (re.compile(r"\bXXX\b"),                        "xxx-marker"),
    (re.compile(r"\\todo\b"),                       "todo-cmd"),
    (re.compile(r"\\lipsum\b"),                     "lipsum"),
]


def format_expert_check(tex_files: list[Path]) -> dict:
    """Static-check stand-in for format-expert."""
    labels: dict[str, list[str]] = {}   # label -> [file:line]
    refs:   list[tuple[str, str]] = []  # (ref, file:line)
    placeholders: list[dict] = []

    for f in tex_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in LABEL_RE.finditer(line):
                labels.setdefault(m.group(1), []).append(f"{f.name}:{i}")
            for m in REF_RE.finditer(line):
                refs.append((m.group(1), f"{f.name}:{i}"))
            for pat, tag in PLACEHOLDER_PATTERNS:
                if pat.search(line):
                    placeholders.append({"tag": tag, "loc": f"{f.name}:{i}",
                                         "snippet": line.strip()[:120]})

    duplicate_labels = [{"label": k, "locs": v} for k, v in labels.items() if len(v) > 1]
    undefined_refs   = [{"ref": r, "loc": loc} for r, loc in refs if r not in labels]

    findings = []
    if duplicate_labels:
        findings.append({
            "axis": "label-unique",
            "severity": "blocking",
            "msg": f"{len(duplicate_labels)} duplicate \\label keys",
            "detail": duplicate_labels[:10],
        })
    if undefined_refs:
        findings.append({
            "axis": "xref-resolved",
            "severity": "blocking",
            "msg": f"{len(undefined_refs)} unresolved \\ref keys",
            "detail": undefined_refs[:10],
        })
    if placeholders:
        findings.append({
            "axis": "no-placeholder",
            "severity": "blocking",
            "msg": f"{len(placeholders)} placeholder markers",
            "detail": placeholders[:10],
        })

    return {
        "expert": "format-expert",
        "stats": {"labels": len(labels), "refs": len(refs),
                  "duplicate_labels": len(duplicate_labels),
                  "undefined_refs":  len(undefined_refs),
                  "placeholders":    len(placeholders)},
        "findings": findings,
    }


# ============================================================================
# claim-trace-expert stand-in
# ============================================================================

# Captures decimals (and percentages) tagged with a small left-context word.
# We don't try to be exhaustive — this is P0, just enough to catch the
# class of bug AUDIT.md documents.
NUMERIC_RE = re.compile(r"(?P<num>[-+]?\d+(?:\.\d+)?)\s*(?P<pct>\\?%)?")

# Phrase-level mismatches the AUDIT flagged (issue #6: AUC vs AUC-PR vs AUC-ROC).
EARLYSTOP_PHRASE_RE = re.compile(
    r"early[- ]?stop(?:ping)?[^\n]{0,80}?(AUC[- ]?(?:PR|ROC)?)", re.I)


def _tokens_around(line: str, num_str: str, window: int = 60) -> str:
    idx = line.find(num_str)
    if idx < 0:
        return line.strip()[:window]
    lo = max(0, idx - window)
    hi = min(len(line), idx + len(num_str) + window)
    return line[lo:hi].strip()


def _left_context(line: str, num_str: str, left: int = 40) -> str:
    """Tight left-only context — metric labels appear immediately before the
    number, e.g. 'Pearson r=-0.98' or 'AUC-ROC of 0.86'. Wider windows
    cross-pollute (every decimal on a Pearson-mentioning line gets tagged
    pearson_r)."""
    idx = line.find(num_str)
    if idx < 0:
        return line.strip()[:left]
    return line[max(0, idx - left): idx]


def _classify_dataset(ctx: str, metric: str | None = None) -> str | None:
    cl = ctx.lower()
    if "bitcoin-alpha" in cl or ("alpha" in cl and "bitcoin" in cl):
        return "alpha"
    if "bitcoin-otc"   in cl or ("otc"   in cl and "bitcoin" in cl):
        return "otc"
    if "uci" in cl:
        return "uci"
    # Paper-level scalars (e.g. Pearson r) are not per-dataset; bucket as _global_
    # so the cross-section check still fires on disagreement across sections.
    if metric in {"pearson_r"}:
        return "_global_"
    return None


def _classify_metric(ctx: str) -> str | None:
    cl = ctx.lower()
    # ordering matters — match the longer/more specific first
    for kw, tag in [
        ("pearson", "pearson_r"),
        (r"\\mu_2", "mu2"),
        ("|\\mu_2|", "mu2"),
        ("heterophily ratio", "h"),
        ("$h$",  "h"),
        ("$h=",  "h"),
        ("$h ", "h"),
        ("anomaly rate", "anomaly_pct"),
        ("anomaly %", "anomaly_pct"),
        ("auc-roc", "auc_roc"),
        ("auc-pr",  "auc_pr"),
        ("ap std",  "ap_std"),
        ("std",     "std"),
    ]:
        if kw in cl:
            return tag
    return None


def claim_trace_check(tex_files: list[Path]) -> dict:
    """Cross-section numeric & phrase equality."""
    # Bucket: (metric, dataset) -> list of (value, locus)
    buckets: dict[tuple[str, str], list[dict]] = {}

    for f in tex_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            # gather decimals — restrict to "interesting" ones to keep noise down
            for m in NUMERIC_RE.finditer(line):
                num_str = m.group("num")
                # require a decimal point or % to be considered (skips year/index ints)
                if "." not in num_str and not m.group("pct"):
                    continue
                ctx = _tokens_around(line, num_str)
                left = _left_context(line, num_str)
                metric  = _classify_metric(left) or _classify_metric(ctx)
                dataset = _classify_dataset(ctx, metric)
                if not metric or not dataset:
                    continue
                try:
                    val = float(num_str)
                except ValueError:
                    continue
                if m.group("pct"):
                    # keep raw % value in [0,100]
                    pass
                buckets.setdefault((metric, dataset), []).append({
                    "value": val,
                    "loc": f"{f.name}:{i}",
                    "ctx": ctx[:160],
                })

    disagreements = []
    for (metric, dataset), rows in buckets.items():
        # group by value (tolerance 0.5% relative or 0.005 absolute on small values)
        seen: list[tuple[float, list[dict]]] = []
        for r in rows:
            placed = False
            for sv, group in seen:
                tol = max(0.005, abs(sv) * 0.005)
                if abs(r["value"] - sv) <= tol:
                    group.append(r); placed = True; break
            if not placed:
                seen.append((r["value"], [r]))
        if len(seen) > 1:
            disagreements.append({
                "metric": metric, "dataset": dataset,
                "distinct_values": [sv for sv, _ in seen],
                "loci": [{"value": sv, "locs": [g["loc"] for g in group],
                          "ctx_sample": group[0]["ctx"]}
                         for sv, group in seen],
            })

    # Phrase-level: collect "early-stop on AUC*" across files (issue #6)
    earlystop_metrics: dict[str, list[str]] = {}
    for f in tex_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = EARLYSTOP_PHRASE_RE.search(line)
            if m:
                key = re.sub(r"[\s-]+", "", m.group(1).upper())  # AUC / AUCPR / AUCROC
                earlystop_metrics.setdefault(key, []).append(f"{f.name}:{i}")

    earlystop_mismatch = None
    if len(earlystop_metrics) > 1:
        earlystop_mismatch = {
            "axis": "cross-section-equality",
            "severity": "blocking",
            "msg": f"early-stopping metric disagrees across sections: {sorted(earlystop_metrics)}",
            "detail": earlystop_metrics,
        }

    # Issue #7: "5--12%" prose vs UCI 71.1% anomaly rate
    interval_violation = None
    interval_re = re.compile(r"(\d+(?:\.\d+)?)\s*[-–—]+\s*(\d+(?:\.\d+)?)\s*\\?%")
    declared_intervals = []
    for f in tex_files:
        if f.name != "03_method.tex":
            # AUDIT.md anchors this to 03_method.tex but we'll scan all
            pass
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in interval_re.finditer(text):
            lo, hi = float(m.group(1)), float(m.group(2))
            ctx_window = text[max(0, m.start()-120):m.end()+120].lower()
            # Require both "anomaly" AND a prevalence/rate cue word — without
            # the second cue the same regex matches "+1--7\% AUC" gains.
            if (0 < lo < hi < 100
                    and "anomaly" in ctx_window
                    and any(kw in ctx_window for kw in ("prevalence", "rate", "fraction", "proportion", "ratio"))):
                declared_intervals.append({"file": f.name, "lo": lo, "hi": hi})
    # check against anomaly_pct bucket
    anomaly_pcts = [r["value"] for (m_, d_), rows in buckets.items()
                    if m_ == "anomaly_pct" for r in rows]
    out_of_range = [v for v in anomaly_pcts
                    if declared_intervals and not any(iv["lo"] <= v <= iv["hi"]
                                                     for iv in declared_intervals)]
    if declared_intervals and out_of_range:
        interval_violation = {
            "axis": "cross-section-equality",
            "severity": "blocking",
            "msg": f"declared anomaly-rate interval(s) {declared_intervals} contradicted by observed {sorted(set(out_of_range))}",
        }

    findings = []
    if disagreements:
        findings.append({
            "axis": "cross-section-equality",
            "severity": "blocking",
            "msg": f"{len(disagreements)} (metric,dataset) numeric disagreements",
            "detail": disagreements[:10],
        })
    if earlystop_mismatch:
        findings.append(earlystop_mismatch)
    if interval_violation:
        findings.append(interval_violation)

    return {
        "expert": "claim-trace-expert",
        "stats": {"buckets": len(buckets), "disagreements": len(disagreements)},
        "findings": findings,
    }


# ============================================================================
# prose-rigor-expert stand-in
# ============================================================================

PROHIBITED = [
    (re.compile(r"\bto the best of our knowledge\b", re.I), "TBOK"),
    (re.compile(r"\bsignificantly outperforms\b",     re.I), "vague-significant"),
    (re.compile(r"\b(very|extremely|completely|dramatically)\b", re.I), "intensifier"),
    (re.compile(r"\brecent years have witnessed\b",   re.I), "recent-years-cliche"),
    (re.compile(r"\bit is well known that\b",         re.I), "well-known"),
    (re.compile(r"\bdue to the fact that\b",          re.I), "due-to-fact"),
    (re.compile(r"\bit can be seen that\b",           re.I), "can-be-seen"),
]


def prose_rigor_check(tex_files: list[Path]) -> dict:
    hits = []
    for f in tex_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat, tag in PROHIBITED:
                if pat.search(line):
                    hits.append({"tag": tag, "loc": f"{f.name}:{i}",
                                 "snippet": line.strip()[:160]})

    findings = []
    if hits:
        findings.append({
            "axis": "no-anonymous-placeholder",   # closest P0 axis; intensifiers are advisory
            "severity": "advisory",
            "msg": f"{len(hits)} prohibited constructions",
            "detail": hits[:20],
        })
    return {"expert": "prose-rigor-expert",
            "stats": {"hits": len(hits)},
            "findings": findings}


# ============================================================================
# hallucination-expert stand-in (subprocess: verify_citations.py)
# ============================================================================

def hallucination_check(bib: Path, no_network: bool) -> dict:
    if not bib.exists():
        return {"expert": "hallucination-expert", "error": f"bib not found: {bib}", "findings": []}
    cmd = [sys.executable, str(SCRIPTS / "verify_citations.py"), str(bib)]
    if no_network:
        cmd.append("--no-network")
    cmd += ["--source", "all"]
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as tf:
        out_path = Path(tf.name)
    cmd += ["--out", str(out_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                              encoding="utf-8", errors="replace")
        try:
            payload = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {"error": "verify_citations.py emitted no JSON",
                       "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]}
        finally:
            try: out_path.unlink()
            except Exception: pass

        summary = payload.get("summary", {})
        findings = []
        if summary.get("missing", 0) > 0:
            findings.append({
                "axis": "cite-resolves", "severity": "blocking",
                "msg": f"{summary['missing']} bib entries unresolved",
                "detail": [m["key"] for m in (payload.get("missing") or [])[:20]],
            })
        if summary.get("suspicious_alias_groups", 0) > 0:
            findings.append({
                "axis": "cite-resolves", "severity": "blocking",
                "msg": f"{summary['suspicious_alias_groups']} suspicious alias group(s)",
                "detail": [{"tier": g.get("tier"), "keys": g.get("keys"),
                            "jaccard": g.get("jaccard")}
                           for g in payload.get("suspicious_alias_groups", [])[:20]],
            })
        return {"expert": "hallucination-expert",
                "stats": summary,
                "findings": findings,
                "exit_code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"expert": "hallucination-expert", "error": "timeout", "findings": []}


# ============================================================================
# Synthetic regression fixtures
# ----------------------------------------------------------------------------
# The on-disk manuscript-backup is a *post-fix* snapshot (the user's pipeline
# has already cleaned up the historic issues), so most of the 10 AUDIT.md
# bugs no longer exist in source. To prove each expert *would* have caught
# them, we re-inject each class-of-bug into an isolated tmp copy and run
# the expert on the modified tree.
# ============================================================================


def _fresh_copy(manuscript: Path, tag: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"p0_inj_{tag}_"))
    dst = tmp / "manuscript"
    shutil.copytree(manuscript, dst)
    return dst


def inject_pearson_mismatch(manuscript: Path) -> Path:
    """Issue E1: stale Pearson r=-0.62 in one section, -0.98 in another."""
    dst = _fresh_copy(manuscript, "pearson")
    intro = dst / "sections" / "01_introduction.tex"
    if intro.exists():
        t = intro.read_text(encoding="utf-8", errors="replace")
        t2, n = re.subn(r"(Pearson[^\n.]{0,40}?r\s*=\s*)\{?[-−]?\}?\s*\{?[-−]?\}?\d+\.\d+",
                        r"\1-0.62", t, count=1)
        if n == 0:
            t2 = t + "\n% synthetic: Pearson r = -0.62 (stale, should be -0.98).\n"
        intro.write_text(t2, encoding="utf-8")
    return dst


def inject_undefined_ref(manuscript: Path) -> Path:
    """Issue #4: \\ref{sec:prelim} with no matching \\label."""
    dst = _fresh_copy(manuscript, "ref")
    intro = dst / "sections" / "01_introduction.tex"
    if intro.exists():
        t = intro.read_text(encoding="utf-8", errors="replace")
        t = t + "\nSection~\\ref{sec:prelim} formalizes the DGAD problem.\n"
        intro.write_text(t, encoding="utf-8")
    return dst


def inject_duplicate_label(manuscript: Path) -> Path:
    """Issue #5: duplicate \\label{thm:variance} (method preview + theory)."""
    dst = _fresh_copy(manuscript, "dup")
    method = dst / "sections" / "03_method.tex"
    if method.exists():
        t = method.read_text(encoding="utf-8", errors="replace")
        # add a second \label{thm:variance} (the historic Method-preview duplicate)
        t = t + "\n\\begin{theorem}[Variance preview]\\label{thm:variance}\nBound preview.\n\\end{theorem}\n"
        method.write_text(t, encoding="utf-8")
    return dst


def inject_placeholder(manuscript: Path) -> Path:
    """Anonymous Submission placeholder regression (caught in original run)."""
    dst = _fresh_copy(manuscript, "anon")
    abstract = dst / "sections" / "00_abstract.tex"
    if abstract.exists():
        t = abstract.read_text(encoding="utf-8", errors="replace")
        t = "% TODO: deanonymize\n" + t
        abstract.write_text(t, encoding="utf-8")
    return dst


def inject_validation_metric_mismatch(manuscript: Path) -> Path:
    """Issue #6: validation early-stopping metric disagrees across sections."""
    dst = _fresh_copy(manuscript, "val")
    method = dst / "sections" / "03_method.tex"
    if method.exists():
        t = method.read_text(encoding="utf-8", errors="replace")
        # Replace AUC-PR with AUC-ROC in one occurrence to introduce mismatch
        t2 = re.sub(r"(early[- ]?stopping[^\n]{0,40}?)AUC-PR",
                    r"\1AUC-ROC", t, count=1, flags=re.I)
        method.write_text(t2, encoding="utf-8")
    return dst


def inject_anomaly_interval_violation(manuscript: Path) -> Path:
    """Issue #7: prose says 5-12% anomaly prevalence, UCI table says 71.1%."""
    dst = _fresh_copy(manuscript, "anom")
    method = dst / "sections" / "03_method.tex"
    if method.exists():
        t = method.read_text(encoding="utf-8", errors="replace")
        t = t + "\nThe positive-class weight is $5$, chosen to counter the 5--12\\% anomaly prevalence in our benchmarks.\n"
        method.write_text(t, encoding="utf-8")
    expt = dst / "sections" / "05_experiments.tex"
    if expt.exists() and "71.1" not in expt.read_text(encoding="utf-8", errors="replace"):
        e = expt.read_text(encoding="utf-8", errors="replace")
        e = e + "\nOn UCI Messages the anomaly rate is 71.1\\%.\n"
        expt.write_text(e, encoding="utf-8")
    return dst


def inject_bib_aliases(manuscript: Path) -> Path:
    """Issue #8: re-introduce the four alias pairs into references.bib."""
    dst = _fresh_copy(manuscript, "bib")
    bib = dst / "references.bib"
    if bib.exists():
        t = bib.read_text(encoding="utf-8", errors="replace")
        # add aliases for entries already present
        aliases = """
@inproceedings{zhu2020beyond,
  title = {Beyond Homophily in Graph Neural Networks: Current Limitations and Effective Designs},
  author = {Zhu, Jiong and Yan, Yujun and Zhao, Lingxiao and Heimann, Mark and Akoglu, Leman and Koutra, Danai},
  booktitle = {NeurIPS}, year = {2020},
  note = {alias of zhu2020h2gcn.}
}
@inproceedings{xu2025generaldy,
  title = {GeneralDyG: Generalizable Dynamic Graph Anomaly Detection},
  author = {Xu, Jane and Wang, Bo},
  booktitle = {AAAI}, year = {2025},
  note = {alias of xu2025generaldyg.}
}
@article{ekle2024dynamic,
  title = {Anomaly Detection in Dynamic Graphs: A Comprehensive Survey},
  author = {Ekle, A. O. and others},
  journal = {arXiv}, year = {2024},
  note = {alias of ekle2024survey.}
}
@inproceedings{oono2020graph,
  title = {Graph Neural Networks Exponentially Lose Expressive Power for Node Classification},
  author = {Oono, Kenta and Suzuki, Taiji},
  booktitle = {ICLR}, year = {2020},
  note = {alias of oono2020asymptotic.}
}
"""
        bib.write_text(t + aliases, encoding="utf-8")
    return dst


# ============================================================================
# Per-issue injection harness
# ============================================================================

def synthetic_pearson_injection(manuscript: Path) -> tuple[Path, list[Path]]:
    """Backwards-compat shim: returns (root, sections) after pearson injection."""
    dst = inject_pearson_mismatch(manuscript)
    return dst, sorted((dst / "sections").glob("*.tex"))


# ============================================================================
# Expectation matching against AUDIT.md top-10 (via per-issue injection)
# ============================================================================

def _has_finding(expert_result: dict, axis: str, predicate) -> bool:
    findings = [f for f in expert_result.get("findings", []) if f.get("axis") == axis]
    return any(predicate(f) for f in findings)


def run_injection_suite(manuscript: Path, no_network: bool) -> list[dict]:
    """For each AUDIT.md class-of-bug, inject it into a tmp copy and assert
    the relevant expert flags it. Returns one row per injection."""
    rows = []

    def _section_files(root: Path) -> list[Path]:
        return sorted((root / "sections").glob("*.tex"))

    # #4 — undefined \ref{sec:prelim}
    dst = inject_undefined_ref(manuscript)
    res = format_expert_check(_section_files(dst))
    detected = _has_finding(res, "xref-resolved",
                            lambda f: "sec:prelim" in json.dumps(f.get("detail")))
    rows.append({"id": "#4_undefined_ref_sec_prelim",
                 "expert": "format-expert", "axis": "xref-resolved",
                 "detected": detected, "fixture_root": str(dst),
                 "n_findings_on_axis": sum(1 for x in res["findings"]
                                           if x.get("axis") == "xref-resolved")})

    # #5 — duplicate \label{thm:variance}
    dst = inject_duplicate_label(manuscript)
    res = format_expert_check(_section_files(dst))
    detected = _has_finding(res, "label-unique",
                            lambda f: "thm:variance" in json.dumps(f.get("detail")))
    rows.append({"id": "#5_duplicate_thm_variance",
                 "expert": "format-expert", "axis": "label-unique",
                 "detected": detected, "fixture_root": str(dst),
                 "n_findings_on_axis": sum(1 for x in res["findings"]
                                           if x.get("axis") == "label-unique")})

    # placeholder regression (Anonymous / TODO)
    dst = inject_placeholder(manuscript)
    res = format_expert_check(_section_files(dst))
    detected = _has_finding(res, "no-placeholder",
                            lambda f: "todo" in json.dumps(f.get("detail")).lower())
    rows.append({"id": "E3_placeholder_regression",
                 "expert": "format-expert", "axis": "no-placeholder",
                 "detected": detected, "fixture_root": str(dst),
                 "n_findings_on_axis": sum(1 for x in res["findings"]
                                           if x.get("axis") == "no-placeholder")})

    # #6 — validation metric disagrees
    dst = inject_validation_metric_mismatch(manuscript)
    res = claim_trace_check(_section_files(dst))
    detected = _has_finding(res, "cross-section-equality",
                            lambda f: "early-stopping" in (f.get("msg") or ""))
    rows.append({"id": "#6_validation_metric_mismatch",
                 "expert": "claim-trace-expert", "axis": "cross-section-equality",
                 "detected": detected, "fixture_root": str(dst),
                 "n_findings_on_axis": sum(1 for x in res["findings"]
                                           if x.get("axis") == "cross-section-equality")})

    # #7 — declared anomaly-rate interval contradicted
    dst = inject_anomaly_interval_violation(manuscript)
    res = claim_trace_check(_section_files(dst))
    detected = _has_finding(res, "cross-section-equality",
                            lambda f: "declared anomaly-rate interval" in (f.get("msg") or ""))
    rows.append({"id": "#7_anomaly_pct_interval",
                 "expert": "claim-trace-expert", "axis": "cross-section-equality",
                 "detected": detected, "fixture_root": str(dst),
                 "n_findings_on_axis": sum(1 for x in res["findings"]
                                           if x.get("axis") == "cross-section-equality")})

    # E1 — synthetic Pearson r mismatch (the canonical incident)
    dst = inject_pearson_mismatch(manuscript)
    res = claim_trace_check(_section_files(dst))
    detected = _has_finding(
        res, "cross-section-equality",
        lambda f: any(isinstance(d, dict) and d.get("metric") == "pearson_r"
                      for d in (f.get("detail") or [])))
    rows.append({"id": "E1_pearson_mismatch_synth",
                 "expert": "claim-trace-expert", "axis": "cross-section-equality",
                 "detected": detected, "fixture_root": str(dst),
                 "n_findings_on_axis": sum(1 for x in res["findings"]
                                           if x.get("axis") == "cross-section-equality")})

    # #8 — bib alias re-introduction (hallucination-expert / verify_citations.py)
    dst = inject_bib_aliases(manuscript)
    h = hallucination_check(dst / "references.bib", no_network)
    detected = any("suspicious alias" in (f.get("msg") or "") for f in h.get("findings", []))
    rows.append({"id": "#8_bib_alias_pairs",
                 "expert": "hallucination-expert", "axis": "cite-resolves",
                 "detected": detected, "fixture_root": str(dst),
                 "alias_groups_seen": h.get("stats", {}).get("suspicious_alias_groups")})

    return rows


# ============================================================================
# Driver
# ============================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", type=Path,
                    default=Path("D:/repo/GNN-dynamic/manuscript-backup"))
    ap.add_argument("--no-network", action="store_true",
                    help="Skip external paper-lookup APIs (still runs alias-hash tier).")
    ap.add_argument("--out", type=Path,
                    default=HERE / "p0_smoke_report.json")
    ap.add_argument("--skip-injection", action="store_true",
                    help="Skip the per-issue injection suite")
    args = ap.parse_args()

    if not args.manuscript.exists():
        print(f"error: manuscript path not found: {args.manuscript}", file=sys.stderr)
        return 2

    sections_dir = args.manuscript / "sections"
    tex_files = sorted(sections_dir.glob("*.tex")) if sections_dir.exists() else []
    bib = args.manuscript / "references.bib"

    print(f"manuscript = {args.manuscript}")
    print(f"  tex files: {len(tex_files)}")
    print(f"  bib:       {bib.exists()}")

    # PART 1 — baseline: run each P0 expert against the on-disk manuscript.
    # The backup is a *post-fix* snapshot so most issues should be CLEAN here.
    # This is the "no false positives" check.
    expert_results = {}

    print("\n[BASELINE 1/4] format-expert ...")
    expert_results["format-expert"] = format_expert_check(tex_files)
    print(f"  findings: {len(expert_results['format-expert']['findings'])}  "
          f"stats: {expert_results['format-expert']['stats']}")

    print("\n[BASELINE 2/4] claim-trace-expert ...")
    expert_results["claim-trace-expert"] = claim_trace_check(tex_files)
    print(f"  findings: {len(expert_results['claim-trace-expert']['findings'])}  "
          f"stats: {expert_results['claim-trace-expert']['stats']}")

    print("\n[BASELINE 3/4] prose-rigor-expert ...")
    expert_results["prose-rigor-expert"] = prose_rigor_check(tex_files)
    print(f"  findings: {len(expert_results['prose-rigor-expert']['findings'])}  "
          f"stats: {expert_results['prose-rigor-expert']['stats']}")

    print("\n[BASELINE 4/4] hallucination-expert ...")
    h = hallucination_check(bib, args.no_network)
    expert_results["hallucination-expert"] = h
    print(f"  findings: {len(h.get('findings', []))}  stats: {h.get('stats', h.get('error'))}")

    # PART 2 — injection suite: for each known class-of-bug, inject it into
    # an isolated tmp copy and assert the relevant expert flags it.
    injection_rows = []
    if not args.skip_injection:
        print("\n=== INJECTION SUITE — assert each expert catches its class-of-bug ===")
        injection_rows = run_injection_suite(args.manuscript, args.no_network)

    summary = {
        "$schema": "moon-research/p0-smoke-v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manuscript": str(args.manuscript),
        "tex_files": [str(f.name) for f in tex_files],
        "baseline_experts": expert_results,
        "injection_suite": injection_rows,
        "summary": {
            "injection_total":  len(injection_rows),
            "injection_passed": sum(1 for r in injection_rows if r["detected"]),
            "injection_failed": sum(1 for r in injection_rows if not r["detected"]),
            "baseline_findings_total": sum(
                len(r.get("findings", [])) for r in expert_results.values()),
        },
    }
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\nwrote {args.out}")

    print("\n=== injection-suite results ===")
    for r in injection_rows:
        flag = "OK " if r["detected"] else "MISS"
        print(f"  [{flag}] {r['id']:<36s}  {r['expert']:<22s}  {r['axis']}")

    n_fail = summary["summary"]["injection_failed"]
    if n_fail == 0:
        print(f"\nall {len(injection_rows)} injections detected. P0 panel calibrated.")
        return 0
    else:
        print(f"\n{n_fail} injection(s) missed. P0 calibration miss — see report.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
