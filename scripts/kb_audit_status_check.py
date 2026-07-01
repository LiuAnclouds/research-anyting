#!/usr/bin/env python3
"""
kb_audit_status_check.py — KB consistency scanner.

Walks ``knowledge-base/papers/**/*.md`` and reports any of the following
issues per the KB_SCHEMA contract (see ``knowledge-base/KB_SCHEMA.md``):

  1. Missing or ``null`` ``external_verified`` field in YAML frontmatter.
  2. ``external_verified: true`` without a populated ``verification_evidence``
     block.
  3. ``external_verified: true`` without a ``verified_at`` ISO-8601 timestamp.
  4. Wikilinks (``[[slug]]`` / ``[[slug|alias]]``) that do not resolve to an
     existing KB entry on disk under ``knowledge-base/``.

The YAML frontmatter is parsed with the minimal in-house parser pattern
borrowed from ``scripts/migrate_agent_frontmatter.py`` so there is no
PyYAML dependency.

Usage:
  python scripts/kb_audit_status_check.py [--kb-root PATH] [--out PATH]

Default ``--kb-root`` is ``<plugin_root>/knowledge-base``.
Default ``--out``     is ``<plugin_root>/tests/regression/kb_audit_status_report.json``.

Exit codes:
  0  scan clean (no issues found)
  1  one or more issues reported
  2  harness error (e.g. KB root missing, unreadable file)
"""
from __future__ import annotations
import argparse, json, re, sys, traceback
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent

FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)
# Wikilink: [[slug]] or [[slug|display text]]. The slug is everything before
# an optional "|" pipe alias. We allow forward slashes (e.g.
# "modules/gnn/encoders/gcn-encoder") and basic word chars + dashes.
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")


# ---------- minimal YAML parse (no dependency) -----------------------------

def _yaml_scalar(v: str):
    """Coerce a scalar token to bool / int / float / str / None.

    Treats the literal tokens ``null`` and ``~`` as Python ``None`` so the
    audit can distinguish "field absent" from "field explicitly null".
    """
    s = v.strip()
    low = s.lower()
    if low in ("null", "~", ""):
        return None
    if low in ("true", "false"):
        return low == "true"
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return ({fields}, body) or (None, text) when no frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    body = m.group("body")
    fm: dict = {}
    cur_key: str | None = None
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
            elif v.startswith("[[") or "[[" in v:
                # A line like ``modules: [[a]], [[b]]`` is NOT a YAML list — it's
                # a comma-separated set of wikilinks. Store the raw string so the
                # caller can still scan for wikilinks via the global regex.
                fm[k] = v
                cur_key, cur_list = None, None
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
        # block scalar / mapping continuation — ignored for our purposes
    rest = text[m.end():]
    return fm, rest


# ---------- wikilink resolution -------------------------------------------

def _build_kb_index(kb_root: Path) -> set[str]:
    """Return a set of normalized slugs that exist on disk.

    A slug is the path of a markdown file relative to ``kb_root``, with the
    trailing ``.md`` stripped and slashes normalized to forward slashes.
    INDEX.md files are also indexed at their directory slug (e.g.
    ``papers/gnn`` resolves to ``papers/gnn/INDEX.md``).
    """
    slugs: set[str] = set()
    for p in kb_root.rglob("*.md"):
        rel = p.relative_to(kb_root).as_posix()
        if rel.endswith(".md"):
            stem = rel[:-3]
            slugs.add(stem)
            if stem.endswith("/INDEX"):
                slugs.add(stem[: -len("/INDEX")])
    return slugs


def _slug_from_wikilink(target: str) -> str:
    """Strip ``|alias`` and any leading/trailing whitespace; normalize slashes."""
    s = target.split("|", 1)[0].strip()
    # Drop a trailing ``.md`` if the author wrote one.
    if s.endswith(".md"):
        s = s[:-3]
    return s.replace("\\", "/").strip("/")


def _resolve(slug: str, kb_index: set[str], paper_path: Path, kb_root: Path) -> bool:
    """A slug resolves if it matches an indexed entry, either as an absolute
    KB slug or as a sibling of the calling paper."""
    if slug in kb_index:
        return True
    # Allow same-directory relative refs (rare in this KB but harmless).
    sibling = (paper_path.parent / f"{slug}.md")
    try:
        sibling.relative_to(kb_root)
    except ValueError:
        return False
    return sibling.exists()


# ---------- per-paper audit -----------------------------------------------

def audit_paper(path: Path, kb_root: Path, kb_index: set[str]) -> list[dict]:
    """Return a list of issue dicts; empty if the paper is clean."""
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"read failed: {path}: {e}") from e

    fm, body = parse_frontmatter(text)
    rel = path.relative_to(kb_root).as_posix()

    if fm is None:
        issues.append({"file": rel, "kind": "no-frontmatter",
                       "msg": "paper has no YAML frontmatter"})
        return issues

    # 1. external_verified presence
    if "external_verified" not in fm:
        issues.append({"file": rel, "kind": "missing-external_verified",
                       "msg": "frontmatter has no `external_verified` field"})
    else:
        ev = fm["external_verified"]
        if ev is None:
            issues.append({"file": rel, "kind": "null-external_verified",
                           "msg": "`external_verified` is null — run /mr verify"})
        elif ev is True:
            # 2. verification_evidence must be populated when verified
            evi = fm.get("verification_evidence")
            if not evi:
                issues.append({"file": rel,
                               "kind": "missing-verification_evidence",
                               "msg": "`external_verified: true` but no `verification_evidence`"})
            # 3. verified_at timestamp required
            vat = fm.get("verified_at")
            if not vat:
                issues.append({"file": rel, "kind": "missing-verified_at",
                               "msg": "`external_verified: true` but no `verified_at` timestamp"})
            else:
                # cheap ISO-8601 sanity check
                try:
                    datetime.fromisoformat(str(vat).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    issues.append({"file": rel, "kind": "bad-verified_at",
                                   "msg": f"`verified_at` is not ISO-8601: {vat!r}"})

    # 4. Wikilink resolution — scan the *entire* file (frontmatter + body)
    # because frontmatter fields like ``modules:`` and ``connections:`` carry
    # wikilinks too, and the minimal parser stores them as raw strings.
    seen_targets: set[str] = set()
    for m in WIKILINK_RE.finditer(text):
        slug = _slug_from_wikilink(m.group(1))
        if not slug or slug in seen_targets:
            continue
        seen_targets.add(slug)
        if not _resolve(slug, kb_index, path, kb_root):
            issues.append({"file": rel, "kind": "broken-wikilink",
                           "target": slug,
                           "msg": f"wikilink [[{slug}]] does not resolve under {kb_root.name}/"})

    return issues


# ---------- driver --------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kb-root", type=Path,
                    default=PLUGIN_ROOT / "knowledge-base",
                    help="Root of the KB tree (default: <plugin_root>/knowledge-base)")
    ap.add_argument("--out", type=Path,
                    default=PLUGIN_ROOT / "tests" / "regression" / "kb_audit_status_report.json",
                    help="JSON report destination")
    args = ap.parse_args()

    kb_root: Path = args.kb_root.resolve()
    if not kb_root.is_dir():
        print(f"[kb-audit] ERROR: --kb-root not a directory: {kb_root}", file=sys.stderr)
        return 2

    papers_root = kb_root / "papers"
    if not papers_root.is_dir():
        print(f"[kb-audit] ERROR: no papers/ subdir under {kb_root}", file=sys.stderr)
        return 2

    try:
        kb_index = _build_kb_index(kb_root)
    except Exception as e:
        print(f"[kb-audit] ERROR building KB index: {e}", file=sys.stderr)
        traceback.print_exc()
        return 2

    all_issues: list[dict] = []
    n_papers = 0
    n_clean = 0
    read_errors: list[dict] = []
    for p in sorted(papers_root.rglob("*.md")):
        # Skip INDEX.md — the schema constraints apply to entry papers, not
        # to manually-maintained directory indexes.
        if p.name == "INDEX.md":
            continue
        n_papers += 1
        try:
            issues = audit_paper(p, kb_root, kb_index)
        except RuntimeError as e:
            read_errors.append({"file": str(p), "error": str(e)})
            continue
        if not issues:
            n_clean += 1
        else:
            all_issues.extend(issues)
            for it in issues:
                print(f"[{it['kind']}] {it['file']}: {it['msg']}")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kb_root": str(kb_root),
        "n_papers_scanned": n_papers,
        "n_papers_clean": n_clean,
        "n_issues": len(all_issues),
        "issues": all_issues,
        "read_errors": read_errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n[kb-audit] scanned {n_papers} papers, {n_clean} clean, "
          f"{len(all_issues)} issue(s); report -> {args.out}")

    if read_errors:
        print(f"[kb-audit] {len(read_errors)} read error(s)", file=sys.stderr)
        return 2
    return 0 if not all_issues else 1


if __name__ == "__main__":
    sys.exit(main())
