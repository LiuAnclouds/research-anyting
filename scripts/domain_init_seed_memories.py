#!/usr/bin/env python3
"""
domain_init_seed_memories.py — Seed audit-expert memories on new-domain init.

Reads `knowledge-base/experts/_seed/generic-canonical-failures.md`, splits
it into individual class-of-bug entries by `## YYYY-MM-DD` heading, and
appends each entry to every expert whose `critical_axes` overlaps with
that entry's declared `axis`.

Called by `agents/domain-init.md` Phase 2c. Ensures a brand-new domain's
audit panel has domain-agnostic class-of-bug awareness on day one — the
new domain's format-expert already knows `\\ref{...}` bugs happen, the
claim-trace-expert already knows Pearson-r-across-sections drifts, etc.

Usage:
  python scripts/domain_init_seed_memories.py [--seed PATH] [--dry-run]

Exit codes:
  0  ok
  2  IO error / seed file malformed
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
SEED_DEFAULT = PLUGIN_ROOT / "knowledge-base" / "experts" / "_seed" / "generic-canonical-failures.md"
EXPERTS_ROOT = PLUGIN_ROOT / "knowledge-base" / "experts"
AGENTS_ROOT  = PLUGIN_ROOT / "agents"

# Frontmatter parser (matches migrate_agent_frontmatter.py's minimal one)
FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)


def _parse_frontmatter_axes(md_text: str) -> list[str]:
    """Extract the `critical_axes` list from an agent .md's frontmatter."""
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return []
    body = m.group("body")
    for line in body.splitlines():
        m2 = re.match(r"^critical_axes:\s*\[(.*?)\]\s*$", line)
        if m2:
            inner = m2.group(1)
            return [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
    return []


def _load_expert_axes() -> dict[str, list[str]]:
    """Return {expert_name: [axes...]} from every agent .md file."""
    result: dict[str, list[str]] = {}
    for p in AGENTS_ROOT.rglob("*.md"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        axes = _parse_frontmatter_axes(text)
        # match filename slug ~ expert name (the frontmatter's name field would be more
        # canonical but the filename is a stable proxy)
        result[p.stem] = axes
    return result


def _split_seed(seed_text: str) -> list[dict]:
    """Split the seed .md into individual entries by `## YYYY-MM-DD` heading.
    Each entry: {title, axis, body}"""
    entries: list[dict] = []
    lines = seed_text.splitlines(keepends=True)
    current_start = None
    current_axis  = None
    current_title = None

    for i, line in enumerate(lines):
        m = re.match(r"^## (\d{4}-\d{2}-\d{2}) — (.+)$", line.rstrip("\n"))
        if m:
            if current_start is not None:
                body = "".join(lines[current_start:i])
                entries.append({
                    "title": current_title, "axis": current_axis, "body": body,
                })
            current_start = i
            current_title = line.strip()
            current_axis = None
            continue
        # Accept forms like "- **Axis that caught it**: `xref-resolved`" or plain
        m2 = re.match(r"^\s*-\s*\*\*Axis[^*]*\*\*:\s*`?([a-zA-Z0-9_-]+)`?", line)
        if m2 and current_start is not None and current_axis is None:
            current_axis = m2.group(1)
    # tail entry
    if current_start is not None:
        body = "".join(lines[current_start:])
        entries.append({
            "title": current_title, "axis": current_axis, "body": body,
        })
    # filter entries whose axis we could not parse
    return [e for e in entries if e["axis"]]


def _matches_expert(entry_axis: str, expert_axes: list[str]) -> bool:
    """Overlap on exact axis name."""
    return entry_axis in expert_axes


def seed_memories(seed_path: Path, dry_run: bool) -> dict:
    if not seed_path.exists():
        return {"error": f"seed not found: {seed_path}", "seeded": [], "skipped": []}
    seed = seed_path.read_text(encoding="utf-8", errors="replace")
    entries = _split_seed(seed)
    if not entries:
        return {"error": "no entries parsed from seed", "seeded": [], "skipped": []}

    expert_axes = _load_expert_axes()

    seeded: list[dict] = []
    skipped: list[dict] = []
    seed_marker = "<!-- seeded from _seed/generic-canonical-failures.md -->\n"

    for expert_dir in sorted(EXPERTS_ROOT.iterdir()):
        if not expert_dir.is_dir() or expert_dir.name.startswith("_"):
            continue
        axes = expert_axes.get(expert_dir.name, [])
        if not axes:
            skipped.append({"expert": expert_dir.name,
                            "reason": "no critical_axes in frontmatter"})
            continue
        matched = [e for e in entries if _matches_expert(e["axis"], axes)]
        if not matched:
            skipped.append({"expert": expert_dir.name,
                            "reason": "no seed entry matches critical_axes",
                            "axes": axes})
            continue
        memory_path = expert_dir / "memory.md"
        try:
            existing = memory_path.read_text(encoding="utf-8", errors="replace") if memory_path.exists() else ""
        except Exception as e:
            skipped.append({"expert": expert_dir.name, "reason": f"read failed: {e}"})
            continue
        if seed_marker in existing:
            skipped.append({"expert": expert_dir.name,
                            "reason": "already seeded (marker present)"})
            continue

        appended_titles = []
        addition_parts = ["\n\n---\n\n", seed_marker,
                          "## Seeded canonical failures (domain-agnostic)\n\n",
                          "The following class-of-bug lessons were pre-loaded from "
                          "`knowledge-base/experts/_seed/generic-canonical-failures.md` "
                          "on this domain's provisioning. They exist so this expert "
                          "recognizes the general class of failure even before the "
                          "current domain has encountered its own concrete instance.\n\n"]
        for e in matched:
            addition_parts.append(e["body"].rstrip() + "\n\n")
            appended_titles.append(e["title"])
        addition = "".join(addition_parts)

        if not dry_run:
            memory_path.write_text(existing + addition, encoding="utf-8")
        seeded.append({"expert": expert_dir.name,
                       "n_events": len(matched),
                       "titles": appended_titles})

    return {"seeded": seeded, "skipped": skipped,
            "n_entries_in_seed": len(entries),
            "n_experts_seeded": len(seeded),
            "n_experts_skipped": len(skipped)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed",    type=Path, default=SEED_DEFAULT,
                    help=f"path to the seed .md (default: {SEED_DEFAULT})")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be seeded without writing")
    ap.add_argument("--out",     type=Path, default=None,
                    help="write JSON report to this path")
    args = ap.parse_args()

    result = seed_memories(args.seed, args.dry_run)
    if "error" in result:
        print(f"error: {result['error']}", file=sys.stderr)
        return 2
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(payload + "\n")

    seeded, skipped = result["n_experts_seeded"], result["n_experts_skipped"]
    tag = "DRY" if args.dry_run else "APPLY"
    print(f"[{tag}] seeded {seeded} expert(s), skipped {skipped}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
