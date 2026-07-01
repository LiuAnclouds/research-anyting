#!/usr/bin/env python3
"""
verify_citations.py — Bib-entry hallucination + alias auditor.

For every entry in a BibTeX file:
  1. Parse the entry (title, first author, year).
  2. Normalize the title (lowercase, strip punctuation, collapse whitespace).
  3. Group entries by normalized-title hash. Any group with >1 key is flagged
     as a suspicious alias (the wang2024gady + gady2024 case).
  4. Call paper_fetcher.py to look up the title on Semantic Scholar / arXiv /
     DBLP / CrossRef. Require >= 1 hit whose title is a string-distance match.
  5. Emit JSON with {found, missing, suspicious_alias} buckets.

Reuses scripts/paper_fetcher.py for the actual API roundtrips so we don't
duplicate SSL/escape-hatch logic.

Usage:
  python verify_citations.py <bib_path> [--out <json>] [--no-network]
                              [--source semantic_scholar|arxiv|dblp|crossref|all]
                              [--cache-dir <dir>]

Exit codes:
  0  all entries resolved (no missing, no suspicious_alias)
  1  some missing
  2  some suspicious_alias
  3  both
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, textwrap, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER_FETCHER = HERE / "paper_fetcher.py"
DEFAULT_CACHE = HERE.parent / "knowledge-base" / "cache" / "verify_citations"


# ---------- bib parsing (minimal, dependency-free) -------------------------

ENTRY_RE = re.compile(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,(?P<body>.*?)\n\}\s*", re.DOTALL)
FIELD_RE = re.compile(r"(?P<field>\w+)\s*=\s*(?P<delim>[\{\"])(?P<value>.*?)(?P=delim)\s*,?", re.DOTALL)


def _strip_braces(s: str) -> str:
    # remove {...} groups but keep content; LaTeX accent commands left as-is
    return re.sub(r"\{|\}", "", s)


def parse_bib(text: str) -> list[dict]:
    """Return list of {key, type, title, authors, year, venue}."""
    out = []
    for m in ENTRY_RE.finditer(text):
        body = m.group("body")
        fields = {}
        # the regex above misses nested braces; do a tolerant pass instead
        # using a brace-balanced field walker
        i = 0
        while i < len(body):
            fm = re.search(r"(?P<f>\w+)\s*=\s*", body[i:])
            if not fm:
                break
            i += fm.end()
            if i >= len(body):
                break
            delim = body[i]
            if delim == "{":
                depth = 0
                j = i
                while j < len(body):
                    if body[j] == "{": depth += 1
                    elif body[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                value = body[i + 1:j]
                i = j + 1
            elif delim == '"':
                j = body.index('"', i + 1)
                value = body[i + 1:j]
                i = j + 1
            else:
                # bare number (e.g. year = 2024,)
                tail = re.search(r"[,\n}]", body[i:])
                value = body[i: i + (tail.start() if tail else 0)].strip()
                i += tail.start() if tail else 0
            fields[fm.group("f").lower()] = _strip_braces(value).strip()
            # advance past comma if any
            while i < len(body) and body[i] in ",\n\r\t ":
                i += 1

        title = fields.get("title", "")
        authors_raw = fields.get("author", "")
        authors = [a.strip() for a in re.split(r"\s+and\s+", authors_raw)] if authors_raw else []
        year = fields.get("year", "").strip()
        venue = fields.get("booktitle") or fields.get("journal") or ""
        out.append({
            "key": m.group("key"),
            "type": m.group("type").lower(),
            "title": title,
            "authors": authors,
            "first_author": authors[0] if authors else "",
            "year": year,
            "venue": venue,
        })
    return out


def normalize_title(t: str) -> str:
    """Lowercase, remove LaTeX commands and punctuation, collapse whitespace."""
    t = re.sub(r"\\[a-zA-Z]+\s*", " ", t)         # \emph{} etc.
    t = re.sub(r"[\{\}\$~]", " ", t)
    t = re.sub(r"[^a-z0-9\s]+", " ", t.lower())
    t = re.sub(r"\s+", " ", t).strip()
    return t


def title_hash(t: str) -> str:
    return hashlib.sha1(normalize_title(t).encode("utf-8")).hexdigest()[:12]


# ---------- external lookup via paper_fetcher.py ---------------------------

def _cache_key(query: str, source: str) -> str:
    return hashlib.sha1(f"{source}::{query}".encode("utf-8")).hexdigest() + ".json"


def _cached_lookup(cache_dir: Path, query: str, source: str) -> dict | None:
    p = cache_dir / _cache_key(query, source)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _store_lookup(cache_dir: Path, query: str, source: str, payload: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / _cache_key(query, source)).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _title_similarity(a: str, b: str) -> float:
    """Cheap Jaccard over normalized title tokens; good enough for fuzzy match."""
    na, nb = set(normalize_title(a).split()), set(normalize_title(b).split())
    if not na or not nb:
        return 0.0
    return len(na & nb) / len(na | nb)


def lookup_paper(entry: dict, source: str, cache_dir: Path, no_network: bool) -> dict:
    """Return {hits: [...], best_similarity: float, queried_source}."""
    query = entry["title"] or f"{entry['first_author']} {entry['year']}"
    if not query.strip():
        return {"hits": [], "best_similarity": 0.0, "queried_source": source, "skipped": "empty title"}

    cached = _cached_lookup(cache_dir, query, source)
    if cached:
        return cached
    if no_network:
        return {"hits": [], "best_similarity": 0.0, "queried_source": source, "skipped": "no-network"}

    cmd = [
        sys.executable, str(PAPER_FETCHER),
        "--query", query,
        "--sources", source,
        "--max", "5",
        "--output", "-",                       # paper_fetcher writes to file path; we use a temp
    ]
    # paper_fetcher.py's --output expects a file; we capture stdout JSON in our own way:
    # invoke it with a tempfile and read back.
    import tempfile
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as tf:
        tmp = Path(tf.name)
    try:
        cmd[-1] = str(tmp)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45,
                              encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            payload = {"hits": [], "best_similarity": 0.0, "queried_source": source,
                       "error": (proc.stderr or "").strip()[:500]}
        else:
            try:
                raw = json.loads(tmp.read_text(encoding="utf-8"))
            except Exception:
                raw = {}
            # paper_fetcher.py output shape: {"query":..., "papers":[{...},...]}
            hits = raw.get("papers") if isinstance(raw, dict) else raw
            hits = hits or []
            best = 0.0
            for h in hits:
                sim = _title_similarity(entry["title"], h.get("title", ""))
                if sim > best: best = sim
            payload = {"hits": hits[:5], "best_similarity": round(best, 3),
                       "queried_source": source}
    except subprocess.TimeoutExpired:
        payload = {"hits": [], "best_similarity": 0.0, "queried_source": source, "error": "timeout"}
    finally:
        try: tmp.unlink()
        except Exception: pass

    _store_lookup(cache_dir, query, source, payload)
    return payload


# ---------- main audit ------------------------------------------------------

DEFAULT_SOURCES = ["dblp", "semantic_scholar", "crossref", "arxiv"]


def audit(bib_path: Path, source: str, no_network: bool, cache_dir: Path) -> dict:
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    entries = parse_bib(text)

    # 1. alias detection
    #    Two tiers:
    #      (a) exact normalized-title hash collision  -> definitely_alias
    #      (b) token-Jaccard >= 0.7 across distinct keys -> likely_alias
    #          (catches "GADY: Unsupervised..." vs "GADY: Continuous-Discrete Unified..."
    #           which share the GADY token + much of the rest but aren't byte-identical)
    by_hash: dict[str, list[dict]] = {}
    for e in entries:
        by_hash.setdefault(title_hash(e["title"]), []).append(e)
    suspicious = []
    for h, group in by_hash.items():
        if len(group) > 1:
            suspicious.append({
                "tier": "definitely_alias",
                "normalized_title_hash": h,
                "normalized_title": normalize_title(group[0]["title"])[:120],
                "keys": [e["key"] for e in group],
                "authors_per_key": [{"key": e["key"], "first_author": e["first_author"]} for e in group],
                "reason": f"{len(group)} bib keys share normalized title; same paper aliased.",
            })

    # token-Jaccard tier
    titles_norm = [(e, set(normalize_title(e["title"]).split())) for e in entries]
    n = len(titles_norm)
    flagged_pairs: set[tuple[str, str]] = set()
    for i in range(n):
        for j in range(i + 1, n):
            ei, ti = titles_norm[i]
            ej, tj = titles_norm[j]
            if ei["key"] == ej["key"]:
                continue
            if title_hash(ei["title"]) == title_hash(ej["title"]):
                continue  # already in the hash tier
            if not ti or not tj:
                continue
            jac = len(ti & tj) / max(1, len(ti | tj))
            if jac >= 0.7:
                pair = tuple(sorted([ei["key"], ej["key"]]))
                if pair in flagged_pairs:
                    continue
                flagged_pairs.add(pair)
                suspicious.append({
                    "tier": "likely_alias",
                    "jaccard": round(jac, 3),
                    "keys": list(pair),
                    "titles_per_key": {ei["key"]: ei["title"], ej["key"]: ej["title"]},
                    "authors_per_key": [
                        {"key": ei["key"], "first_author": ei["first_author"]},
                        {"key": ej["key"], "first_author": ej["first_author"]},
                    ],
                    "reason": f"Token-Jaccard {jac:.2f} >= 0.7; likely same paper aliased.",
                })

    # 2. per-entry existence
    sources = DEFAULT_SOURCES if source == "all" else [source]
    found, missing = [], []
    for e in entries:
        # try sources in order; first satisfactory hit wins
        per_entry = {"key": e["key"], "title": e["title"], "first_author": e["first_author"],
                     "year": e["year"], "sources_queried": [], "best_similarity": 0.0,
                     "hits": []}
        best_overall = 0.0
        hit_record = None
        for s in sources:
            r = lookup_paper(e, s, cache_dir, no_network)
            per_entry["sources_queried"].append({"source": s, "best_similarity": r.get("best_similarity", 0.0),
                                                 "n_hits": len(r.get("hits", [])),
                                                 "error": r.get("error"), "skipped": r.get("skipped")})
            if r.get("best_similarity", 0.0) > best_overall:
                best_overall = r["best_similarity"]
                hit_record = r
        per_entry["best_similarity"] = best_overall
        per_entry["hits"] = (hit_record or {}).get("hits", [])

        # similarity threshold: 0.6 Jaccard ~= 60% token overlap. Empirical.
        if best_overall >= 0.6:
            found.append(per_entry)
        else:
            per_entry["status"] = "missing"
            per_entry["reason"] = (
                "no external source returned a title-similar hit (threshold=0.6 Jaccard)" if not no_network
                else "no-network mode; could not query external sources"
            )
            missing.append(per_entry)

    summary = {
        "$schema": "moon-research/verify-citations-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bib_file": str(bib_path),
        "total": len(entries),
        "found": found,
        "missing": missing,
        "suspicious_alias_groups": suspicious,
        "summary": {
            "found": len(found),
            "missing": len(missing),
            "suspicious_alias_groups": len(suspicious),
        },
        "config": {"source": source, "no_network": no_network,
                   "cache_dir": str(cache_dir), "similarity_threshold": 0.6},
    }
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib", type=Path, help="Path to references.bib")
    ap.add_argument("--out", type=Path, default=None, help="Output JSON path (default: stdout)")
    ap.add_argument("--source", default="all",
                    choices=["all", "semantic_scholar", "arxiv", "dblp", "crossref"],
                    help="Which external source to query (default: all)")
    ap.add_argument("--no-network", action="store_true",
                    help="Skip API calls; only run alias-hash and structural checks")
    ap.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE,
                    help=f"Cache directory (default: {DEFAULT_CACHE})")
    args = ap.parse_args()

    if not args.bib.exists():
        print(f"error: {args.bib} not found", file=sys.stderr)
        sys.exit(4)

    result = audit(args.bib, args.source, args.no_network, args.cache_dir)
    out_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(out_json, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(out_json + "\n")

    # exit code policy
    missing = result["summary"]["missing"]
    suspicious = result["summary"]["suspicious_alias_groups"]
    code = 0
    if missing: code |= 1
    if suspicious: code |= 2
    sys.exit(code)


if __name__ == "__main__":
    main()
