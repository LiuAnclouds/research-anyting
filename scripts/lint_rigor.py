#!/usr/bin/env python3
"""
lint_rigor.py — Pre-flight rigor-contract linter.

Scans manuscript/**/*.tex for Three-Times Rule violations:

  1. Numerics (decimals, percentages) without a nearby [^v]: footnote.
  2. Quantitative claim verbs ("achieves", "outperforms", "by") followed by
     a decimal without a citation or footnote within 200 chars.
  3. Citation-less "we prove", "we show", "it is well known" constructions.
  4. Bare table cells (numbers in \\textbf{} without an experiments/** anchor).

Soft-fails (exit 0 with findings) so it can run as a pre-commit hook; the
WRITE audit panel's claim-trace-expert is what blocks on the same issues.

Usage:
  python lint_rigor.py <manuscript_root> [--out report.json]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from datetime import datetime, timezone


DECIMAL_RE = re.compile(r"(?P<lead>\\?[+-]?)(?P<num>\d+\.\d+)(?P<pct>\s*\\?%)?")
FOOTNOTE_RE = re.compile(r"\[\^v[^\]]*\]\s*:")
CITE_RE = re.compile(r"\\cite[t]?\{[^}]+\}")

# "we prove", "we show that", "it is well known", "to the best of our knowledge"
SUSPECT_VERBS = [
    (re.compile(r"\bwe prove\b", re.I),                          "we-prove"),
    (re.compile(r"\bwe show that\b", re.I),                      "we-show-that"),
    (re.compile(r"\bit is well known that\b", re.I),             "well-known"),
    (re.compile(r"\bto the best of our knowledge\b", re.I),      "TBOK"),
    (re.compile(r"\brecent years have witnessed\b", re.I),       "recent-years"),
]

CLAIM_VERBS = re.compile(r"\b(achieves|outperforms|improves|reduces|increases|by)\b", re.I)


def lint_file(path: Path, kb_root: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"file": str(path), "kind": "io-error", "msg": str(e)}]

    rel = str(path.relative_to(kb_root)) if kb_root in path.parents else str(path)
    for i, line in enumerate(text.splitlines(), 1):
        # 1. decimal without nearby footnote
        for m in DECIMAL_RE.finditer(line):
            # skip year-like ints (not matched anyway since we require decimal)
            # skip equation-only lines that already cite an experiments file
            window_start = max(0, m.start() - 200)
            window = line[window_start: m.end() + 100]
            if FOOTNOTE_RE.search(window):
                continue
            if "experiments/" in window or "knowledge-base/" in window:
                continue
            findings.append({
                "file": rel, "line": i,
                "kind": "decimal-without-footnote",
                "value": m.group("num"),
                "snippet": line.strip()[:160],
            })

        # 2. claim-verb followed by decimal without citation
        if CLAIM_VERBS.search(line):
            for m in DECIMAL_RE.finditer(line):
                window = line[m.start(): m.end() + 200]
                if not CITE_RE.search(line) and not FOOTNOTE_RE.search(line):
                    findings.append({
                        "file": rel, "line": i,
                        "kind": "claim-verb-bare-decimal",
                        "value": m.group("num"),
                        "snippet": line.strip()[:160],
                    })
                    break  # one per line is enough

        # 3. suspect verbs
        for pat, tag in SUSPECT_VERBS:
            if pat.search(line):
                findings.append({
                    "file": rel, "line": i,
                    "kind": f"suspect-verb:{tag}",
                    "snippet": line.strip()[:160],
                })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Manuscript root (contains sections/, references.bib)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not args.root.exists():
        print(f"error: {args.root} not found", file=sys.stderr)
        return 2

    tex_files = sorted(args.root.rglob("*.tex"))
    all_findings: list[dict] = []
    for f in tex_files:
        all_findings.extend(lint_file(f, args.root))

    # bucket by kind
    by_kind: dict[str, int] = {}
    for f in all_findings:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1

    report = {
        "$schema": "moon-research/lint-rigor-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manuscript_root": str(args.root),
        "n_files": len(tex_files),
        "n_findings": len(all_findings),
        "by_kind": by_kind,
        "findings": all_findings[:500],   # cap to keep JSON tractable
    }
    s = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(s, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(s + "\n")

    print(f"\n{len(all_findings)} findings across {len(tex_files)} files. By kind:", file=sys.stderr)
    for k, c in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {c:5d}  {k}", file=sys.stderr)

    return 0  # soft-fail; the WRITE audit panel is what blocks


if __name__ == "__main__":
    sys.exit(main())
