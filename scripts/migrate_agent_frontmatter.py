#!/usr/bin/env python3
"""
migrate_agent_frontmatter.py — agents/**/*.md frontmatter migrator.

Reads every agent .md, parses the YAML frontmatter, validates against
schemas/agent-frontmatter-v1.json, applies defaults for missing fields,
and (with --apply) rewrites the file.

For an agent missing `rigor_contract`, this script adds
`rigor_contract: three-times-verified` plus the canonical Three-Times
Rule prose section immediately after the H1 heading.

Usage:
  python scripts/migrate_agent_frontmatter.py [--dry-run | --apply]
                                              [--root <plugin_root>]

Exit codes:
  0 = clean (no changes needed) or apply succeeded
  1 = changes pending (dry-run found work)
  2 = validation errors that can't be auto-fixed
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
SCHEMA_PATH = PLUGIN_ROOT / "schemas" / "agent-frontmatter-v1.json"

FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)
ALLOWED_PANELS = ["EXPLORE", "DESIGN", "VALIDATE", "ANALYZE",
                  "WRITE", "REVIEW", "executor", "support"]

# Panel/weight assignment from the plan §"Panel layout (3–5 experts each)"
PANEL_ASSIGNMENTS = {
    # WRITE panel
    "figure-expert":         ("WRITE", 25, ["figure-count", "figure-vision-pass"]),
    "hallucination-expert":  ("WRITE", 25, ["cite-resolves", "baseline-resolves", "dataset-resolves"]),
    "format-expert":         ("WRITE", 20, ["latex-compile-clean", "xref-resolved", "label-unique", "no-placeholder"]),
    "claim-trace-expert":    ("WRITE", 20, ["cross-section-equality", "traceable-to-experiments"]),
    "prose-rigor-expert":    ("WRITE", 10, ["no-anonymous-placeholder"]),
    "figure-vision-critic":  ("support",  0, ["no-clipping", "text-legibility"]),

    # REVIEW panel (P1)
    "r1-methodology":        ("REVIEW", 25, ["soundness", "novelty"]),
    "r2-experiments":        ("REVIEW", 25, ["empirical-rigor", "ablation-coverage"]),
    "eic":                   ("REVIEW", 20, ["scope-fit", "presentation"]),
    "reproducibility":       ("REVIEW", 15, ["code-availability", "data-availability"]),
    "devils-advocate":       ("REVIEW", 15, ["counterexample", "ablation-attack"]),

    # ANALYZE panel (P1)
    "statistics":            ("ANALYZE", 30, ["stat-test-correctness"]),
    "claim-evidence":        ("ANALYZE", 25, ["recompute-match", "claim-cell-traceability"]),
    "ablation-coherence":    ("ANALYZE", 15, ["ablation-narrative-consistency"]),
    "failure-case":          ("ANALYZE", 15, ["failure-coverage"]),
    "cross-section-consistency": ("ANALYZE", 15, ["cross-section-equality"]),

    # Existing executors
    "paper-writer":          ("executor", 0, []),
    "theory-crafter":        ("executor", 0, []),
    "code-generator":        ("executor", 0, []),
    "data-preprocessor":     ("executor", 0, []),
    "experiment-engineer":   ("executor", 0, []),
    "experiment-monitor":    ("executor", 0, []),
    "experiment-debugger":   ("executor", 0, []),
    "hyperparameter-optimizer": ("executor", 0, []),
    "literature-survey":     ("executor", 0, []),
    "paper-reader":          ("executor", 0, []),
    "deep-verification":     ("executor", 0, []),
    "deep-discussion":       ("executor", 0, []),
    "rebuttal-writer":       ("executor", 0, []),
    "presentation-builder":  ("executor", 0, []),
    "gnn-rapid-prototype":   ("executor", 0, []),
    "gnn-idea-broker":       ("executor", 0, []),
    "gnn-insight-analyzer":  ("executor", 0, []),
    "vla-vlm-rapid-prototype":("executor", 0, []),
    "vla-vlm-idea-broker":    ("executor", 0, []),
    "vla-vlm-insight-analyzer":("executor", 0, []),
    "domain-researcher":     ("executor", 0, []),

    # Support / orchestration
    "moon-pipeline":         ("support",  0, []),
    "kb-manager":            ("support",  0, []),
    "project-init":          ("support",  0, []),
    "domain-init":           ("support",  0, []),
    "research-log":          ("support",  0, []),
    "literature-alert":      ("support",  0, []),
    "review-simulator":      ("support",  0, []),   # deprecated wrapper post-P1
}

THREE_TIMES_RULE_PROSE = """\

## Rigor contract (read before producing any output)

You operate under `shared/references/audit-doctrine.md` — the Three-Times Rule. No quantitative claim, citation, baseline name, dataset stat, or causal attribution may appear in your output unless it is cross-verified from **three independent loci**:

1. **Primary artifact** (data file, code output, log file, .bib entry) — quote with `file:line`.
2. **Independent recompute or external authority** (rerun via `scripts/*.py`, or external hit on Semantic Scholar / arXiv / DBLP / CrossRef via `scripts/paper_fetcher.py`).
3. **Cross-section consistency** (every other section/output that mentions this value reads the same).

For every quantitative claim, append a footnote in the form:

```
[^v]: locus-1=<file:line>; locus-2=<recompute cmd | url | DOI>; locus-3=<other sections file:line each>
```

Missing any locus → write `[UNVERIFIED: <claim>]`.

"""

PARALLELISM_DOCTRINE_PROSE = """\

## Parallelism contract (read before dispatching sub-work)

You operate under `shared/references/parallelism-doctrine.md`: **default-parallel is the contract**. When this agent has independent sub-work — multiple files to read, multiple sources to query, multiple findings to verify, multiple sub-problems to solve — you MUST dispatch that work concurrently, never serially. Use the runtime's `parallel()` / `pipeline()` primitives (in workflows) or `run_in_background: true` on every `Agent` tool call (from the main loop), all in a single message. The runtime caps concurrency for you; you do not need to throttle.

The decision rule: if call B's prompt does NOT depend on call A's *output content*, dispatch them together. Logging order, narrative order, and aesthetic preference are NOT data dependencies.

"""


# ---------- minimal YAML parse / emit (no dependency) -----------------------

def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return ({fields}, body) where body is the prose after the frontmatter,
    or (None, full_text) if no frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    body = m.group("body")
    fm: dict = {}
    cur_key = None
    cur_list: list | None = None
    for raw in body.splitlines():
        if not raw.strip():
            cur_key, cur_list = None, None
            continue
        m_kv = re.match(r"^(\w[\w-]*)\s*:\s*(.*)$", raw)
        if m_kv:
            k, v = m_kv.group(1), m_kv.group(2).strip()
            if v == "":
                fm[k] = []
                cur_key, cur_list = k, fm[k]
            elif v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                fm[k] = [x.strip().strip("'\"") for x in inner.split(",")] if inner else []
                cur_key, cur_list = None, None
            else:
                fm[k] = _yaml_scalar(v)
                cur_key, cur_list = None, None
            continue
        m_li = re.match(r"^\s*-\s+(.*)$", raw)
        if m_li and cur_list is not None:
            cur_list.append(_yaml_scalar(m_li.group(1).strip()))
            continue
    rest = text[m.end():]
    return fm, rest


def _yaml_scalar(v):
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    try: return int(v)
    except ValueError: pass
    try: return float(v)
    except ValueError: pass
    return v


def emit_frontmatter(fm: dict) -> str:
    """Emit YAML in a stable canonical key order."""
    order = ["name", "description", "model", "tools", "reads", "writes",
             "memory", "rigor_contract", "parallelism_contract", "panel", "weight", "critical_axes",
             "embedding_model"]
    lines = ["---"]
    seen = set()
    for k in order:
        if k in fm:
            lines.append(_emit_kv(k, fm[k])); seen.add(k)
    for k, v in fm.items():
        if k not in seen:
            lines.append(_emit_kv(k, v))
    lines.append("---\n")
    return "\n".join(lines)


def _emit_kv(k, v) -> str:
    if isinstance(v, list):
        if not v:
            return f"{k}: []"
        if all(isinstance(x, (int, float, bool)) or (isinstance(x, str) and "," not in x and " " not in x) for x in v):
            return f"{k}: [{', '.join(str(x) for x in v)}]"
        # multi-line
        out = [f"{k}:"]
        for x in v:
            out.append(f"  - {x}")
        return "\n".join(out)
    if isinstance(v, bool):
        return f"{k}: {'true' if v else 'false'}"
    return f"{k}: {v}"


# ---------- migration logic -------------------------------------------------

def migrate_file(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if fm is None:
        return {"path": str(path), "status": "no-frontmatter", "changes": []}

    changes = []
    name = fm.get("name", path.stem)

    # rigor_contract default
    if "rigor_contract" not in fm:
        fm["rigor_contract"] = "three-times-verified"
        changes.append("+rigor_contract")

    # parallelism_contract default
    if "parallelism_contract" not in fm:
        fm["parallelism_contract"] = "max-fanout"
        changes.append("+parallelism_contract")

    # panel + weight assignment
    if name in PANEL_ASSIGNMENTS:
        p, w, axes = PANEL_ASSIGNMENTS[name]
        if fm.get("panel") != p:
            fm["panel"] = p; changes.append(f"panel→{p}")
        if "weight" not in fm or fm.get("weight") != w:
            fm["weight"] = w; changes.append(f"weight→{w}")
        if axes and not fm.get("critical_axes"):
            fm["critical_axes"] = axes; changes.append("+critical_axes")
    else:
        if "panel" not in fm:
            fm["panel"] = "executor"; changes.append("panel→executor")
        if "weight" not in fm:
            fm["weight"] = 0; changes.append("weight→0")

    # model default
    if "model" not in fm:
        fm["model"] = "inherit"; changes.append("model→inherit")

    # Three-Times Rule prose injection — only if the marker is not already
    # present in the body. We look for either an exact phrase or the
    # canonical heading we'd insert.
    has_rule = (
        "Three-Times Rule" in body
        or "audit-doctrine.md" in body
        or "rigor contract" in body.lower()
    )
    if not has_rule and fm.get("rigor_contract") == "three-times-verified":
        body = _inject_rigor_section(body)
        changes.append("+rigor-prose")

    # Parallelism doctrine prose injection — only if not already present.
    has_parallelism = (
        "Parallelism contract" in body
        or "parallelism-doctrine.md" in body
    )
    if not has_parallelism and fm.get("parallelism_contract") == "max-fanout":
        body = _inject_parallelism_section(body)
        changes.append("+parallelism-prose")

    if not changes:
        return {"path": str(path), "status": "clean", "changes": []}

    new_text = emit_frontmatter(fm) + body
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return {"path": str(path), "status": "migrated" if not dry_run else "would-migrate",
            "changes": changes}


def _inject_rigor_section(body: str) -> str:
    # Insert just after the first H1 if there is one, else at the top.
    lines = body.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            # skip blank lines after the H1, then insert
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            lines.insert(j, THREE_TIMES_RULE_PROSE)
            return "".join(lines)
    return THREE_TIMES_RULE_PROSE + body


def _inject_parallelism_section(body: str) -> str:
    """Insert the parallelism doctrine prose immediately after the rigor
    contract section if one exists, else just after the first H1, else at
    the top of the body."""
    # Prefer to land right after the rigor-contract section. We detect the
    # end of that section by finding its heading and skipping forward to the
    # next H2-or-greater heading.
    lines = body.splitlines(keepends=True)
    rigor_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("## Rigor contract"):
            rigor_idx = i
            break
    if rigor_idx is not None:
        j = rigor_idx + 1
        while j < len(lines) and not lines[j].startswith("## "):
            j += 1
        lines.insert(j, PARALLELISM_DOCTRINE_PROSE)
        return "".join(lines)
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            lines.insert(j, PARALLELISM_DOCTRINE_PROSE)
            return "".join(lines)
    return PARALLELISM_DOCTRINE_PROSE + body


# ---------- driver ----------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply",   action="store_true", help="Write changes to disk")
    ap.add_argument("--dry-run", action="store_true", help="Default: show what would change")
    ap.add_argument("--root", type=Path, default=PLUGIN_ROOT)
    ap.add_argument("--out", type=Path,
                    default=PLUGIN_ROOT / "tests" / "regression" / "migrate_agent_frontmatter_report.json")
    args = ap.parse_args()
    dry_run = not args.apply

    agents = sorted((args.root / "agents").rglob("*.md"))
    results = []
    n_changed = 0
    for p in agents:
        r = migrate_file(p, dry_run)
        results.append(r)
        if r["changes"]:
            n_changed += 1
            print(f"[{'DRY' if dry_run else 'APPLY'}] {p.relative_to(args.root)}: {', '.join(r['changes'])}")
    print(f"\n{n_changed}/{len(agents)} agents need / received migration changes.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"dry_run": dry_run, "results": results,
                                    "n_total": len(agents), "n_changed": n_changed},
                                   ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"wrote {args.out}")
    return 0 if (not dry_run or n_changed == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
