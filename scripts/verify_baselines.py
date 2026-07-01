#!/usr/bin/env python3
"""
verify_baselines.py — Baseline existence + code-repo liveness auditor.

For every baseline listed in a YAML file, verify that:
  (a) The named paper exists on at least one of {Semantic Scholar, arXiv,
      DBLP, CrossRef} via scripts/paper_fetcher.py.
  (b) The associated GitHub/Gitee repo (if any) returns HTTP 200 on a HEAD
      request and (for GitHub) the API exposes a recent pushed_at timestamp.

Catches the "made-up baseline name" failure mode (the GNN-dynamic paper had
a few cite keys whose titles looked plausible but whose authors didn't
exist; baselines have the same risk).

YAML input shape:
  baselines:
    - name: GADY
      paper_hint: "Wang 2024 GADY dynamic graph anomaly"
      repo: https://github.com/owner/GADY        # optional
    - name: TADDY
      paper_hint: "Liu 2021 TADDY transformer dynamic graph anomaly"
      repo: null

Output JSON shape:
  {
    baselines: [
      { name, paper_status: found|missing, paper_url, paper_similarity,
        repo_status: reachable|404|skipped|error, repo_http, last_commit_age_days,
        sources_queried: [...], reason }
    ],
    summary: { total, paper_found, paper_missing, repo_reachable, repo_dead, repo_unknown }
  }

Usage:
  python verify_baselines.py <yaml> [--out <json>] [--no-network]
                              [--source semantic_scholar|arxiv|dblp|crossref|all]

Exit codes:
  0  all baselines have a found paper AND every declared repo is reachable
  1  any paper missing
  2  any repo dead
  3  both
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER_FETCHER = HERE / "paper_fetcher.py"
DEFAULT_CACHE = HERE.parent / "knowledge-base" / "cache" / "verify_baselines"


# ---------- minimal YAML parser (no external dep) ---------------------------
# Supports the strict shape above (list of dicts with scalar fields). For
# anything more complex, the caller can pre-convert to JSON.

def parse_yaml_baselines(text: str) -> list[dict]:
    """Parse a tiny subset of YAML: top-level 'baselines:' list of dicts."""
    out: list[dict] = []
    lines = text.splitlines()
    in_list = False
    current: dict | None = None

    def commit():
        nonlocal current
        if current is not None:
            out.append(current)
            current = None

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^baselines:\s*$", raw):
            in_list = True
            continue
        if not in_list:
            continue
        m = re.match(r"^(\s*)- (\w+):\s*(.*)$", raw)
        if m:
            commit()
            current = {}
            key, val = m.group(2), m.group(3)
            current[key] = _yaml_scalar(val)
            continue
        m = re.match(r"^\s+(\w+):\s*(.*)$", raw)
        if m and current is not None:
            current[m.group(1)] = _yaml_scalar(m.group(2))
            continue
    commit()
    return out


def _yaml_scalar(v: str):
    v = v.strip()
    if v == "" or v.lower() == "null" or v == "~":
        return None
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


# ---------- paper lookup (reuses paper_fetcher.py) --------------------------

def _cache_key(query: str, kind: str) -> str:
    return hashlib.sha1(f"{kind}::{query}".encode("utf-8")).hexdigest() + ".json"


def _cached(cache_dir: Path, query: str, kind: str):
    p = cache_dir / _cache_key(query, kind)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _store(cache_dir: Path, query: str, kind: str, payload: dict):
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / _cache_key(query, kind)).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _normalize(t: str) -> str:
    t = re.sub(r"[^a-z0-9\s]+", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(_normalize(a).split()), set(_normalize(b).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def lookup_paper(name: str, hint: str, source: str, cache_dir: Path, no_network: bool) -> dict:
    q = hint or name
    if not q.strip():
        return {"hits": [], "best_similarity": 0.0, "skipped": "empty query"}
    cached = _cached(cache_dir, q, f"paper.{source}")
    if cached:
        return cached
    if no_network:
        return {"hits": [], "best_similarity": 0.0, "skipped": "no-network"}

    import tempfile
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as tf:
        tmp = Path(tf.name)
    try:
        cmd = [sys.executable, str(PAPER_FETCHER),
               "--query", q, "--sources", source, "--max", "5", "--output", str(tmp)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45,
                              encoding="utf-8", errors="replace")
        hits = []
        if proc.returncode == 0:
            try:
                raw = json.loads(tmp.read_text(encoding="utf-8"))
                hits = raw.get("papers", []) if isinstance(raw, dict) else (raw or [])
            except Exception:
                hits = []
        best = 0.0
        best_hit = None
        for h in hits:
            sim = max(_jaccard(name, h.get("title", "")), _jaccard(q, h.get("title", "")))
            if sim > best:
                best, best_hit = sim, h
        out = {"hits": hits[:5], "best_similarity": round(best, 3),
               "best_url": (best_hit or {}).get("doi") or (best_hit or {}).get("arxiv_id") or "",
               "best_title": (best_hit or {}).get("title", "")}
        if proc.returncode != 0:
            out["error"] = (proc.stderr or "").strip()[:300]
        _store(cache_dir, q, f"paper.{source}", out)
        return out
    except subprocess.TimeoutExpired:
        return {"hits": [], "best_similarity": 0.0, "error": "timeout"}
    finally:
        try: tmp.unlink()
        except Exception: pass


# ---------- repo check (HEAD + GitHub pushed_at) ----------------------------

def check_repo(url: str, no_network: bool, cache_dir: Path) -> dict:
    if not url:
        return {"status": "skipped", "reason": "no repo URL provided"}
    cached = _cached(cache_dir, url, "repo")
    if cached:
        return cached
    if no_network:
        return {"status": "skipped", "reason": "no-network"}

    out = {"url": url, "status": "unknown"}
    # 1. HEAD
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Moon-Research/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            out["http_status"] = resp.status
            out["status"] = "reachable" if 200 <= resp.status < 400 else "dead"
    except urllib.error.HTTPError as e:
        out["http_status"] = e.code
        out["status"] = "404" if e.code == 404 else f"http_{e.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        out["status"] = "error"
        out["error"] = str(e)[:200]

    # 2. GitHub API for pushed_at if applicable
    m = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", url)
    if m and out["status"] == "reachable":
        owner, repo = m.group(1), m.group(2).rstrip(".git")
        api = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            req = urllib.request.Request(api, headers={
                "User-Agent": "Moon-Research/1.0", "Accept": "application/vnd.github+json",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
            pushed = meta.get("pushed_at")
            out["pushed_at"] = pushed
            if pushed:
                pdt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - pdt).days
                out["last_commit_age_days"] = age
            out["stars"] = meta.get("stargazers_count")
            out["default_branch"] = meta.get("default_branch")
            out["archived"] = meta.get("archived", False)
        except Exception as e:
            out["github_api_error"] = str(e)[:200]
    _store(cache_dir, url, "repo", out)
    return out


# ---------- main ------------------------------------------------------------

DEFAULT_SOURCES = ["dblp", "semantic_scholar", "crossref", "arxiv"]


def audit(yaml_path: Path, source: str, no_network: bool, cache_dir: Path) -> dict:
    text = yaml_path.read_text(encoding="utf-8", errors="replace")
    baselines = parse_yaml_baselines(text)
    if not baselines:
        return {"baselines": [], "summary": {"total": 0}, "error": "no baselines parsed from YAML"}

    sources = DEFAULT_SOURCES if source == "all" else [source]
    rows = []
    paper_found = paper_missing = 0
    repo_reachable = repo_dead = repo_unknown = 0

    for b in baselines:
        name = b.get("name", "")
        hint = b.get("paper_hint", "") or ""
        repo = b.get("repo")

        best_sim = 0.0
        best_record = None
        per_src = []
        for s in sources:
            r = lookup_paper(name, hint, s, cache_dir, no_network)
            per_src.append({"source": s, "best_similarity": r.get("best_similarity", 0.0),
                            "n_hits": len(r.get("hits", [])), "error": r.get("error"),
                            "skipped": r.get("skipped")})
            if r.get("best_similarity", 0.0) > best_sim:
                best_sim, best_record = r["best_similarity"], r

        paper_status = "found" if best_sim >= 0.5 else "missing"
        paper_url = (best_record or {}).get("best_url", "")
        paper_title = (best_record or {}).get("best_title", "")
        if paper_status == "found": paper_found += 1
        else: paper_missing += 1

        repo_info = check_repo(repo, no_network, cache_dir) if repo else {"status": "skipped"}
        rs = repo_info.get("status", "skipped")
        if rs == "reachable": repo_reachable += 1
        elif rs in ("404", "dead", "error"): repo_dead += 1
        else: repo_unknown += 1

        rows.append({
            "name": name, "paper_hint": hint, "repo": repo,
            "paper_status": paper_status,
            "paper_similarity": best_sim,
            "paper_url": paper_url,
            "paper_matched_title": paper_title,
            "sources_queried": per_src,
            "repo_info": repo_info,
            "reason": (
                f"paper similarity {best_sim:.2f} < 0.5 across {len(sources)} sources"
                if paper_status == "missing" else None
            ),
        })

    return {
        "$schema": "moon-research/verify-baselines-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "yaml_file": str(yaml_path),
        "baselines": rows,
        "summary": {
            "total": len(rows),
            "paper_found": paper_found,
            "paper_missing": paper_missing,
            "repo_reachable": repo_reachable,
            "repo_dead": repo_dead,
            "repo_unknown": repo_unknown,
        },
        "config": {"source": source, "no_network": no_network,
                   "cache_dir": str(cache_dir), "similarity_threshold": 0.5},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("yaml", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--source", default="all",
                    choices=["all", "semantic_scholar", "arxiv", "dblp", "crossref"])
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()

    if not args.yaml.exists():
        print(f"error: {args.yaml} not found", file=sys.stderr)
        sys.exit(4)

    result = audit(args.yaml, args.source, args.no_network, args.cache_dir)
    out_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(out_json, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(out_json + "\n")

    s = result.get("summary", {})
    code = 0
    if s.get("paper_missing", 0) > 0: code |= 1
    if s.get("repo_dead", 0) > 0: code |= 2
    sys.exit(code)


if __name__ == "__main__":
    main()
