#!/usr/bin/env python3
"""
expert_retrieve.py — Retrieve top-K passages from an expert's index.

Reads `knowledge-base/experts/<name>/index.json` (built by
build_expert_index.py), embeds the query with the same backend, and
returns the top-K cosine-similar chunks.

Falls back to TF-IDF if sentence-transformers is not installed; backend
choice is recorded in the index file's `backend` field, and this script
will refuse if the configured backend is unavailable.

Usage:
  python scripts/expert_retrieve.py <expert> --query "..." [--k 8] [--out json]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
EXPERTS_ROOT = PLUGIN_ROOT / "knowledge-base" / "experts"


def _embed_query(query: str, backend_id: str, corpus_texts: list[str]):
    """Return a 1-D vector matching the index's backend."""
    if backend_id.startswith("sentence-transformers"):
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(backend_id, device="cpu")
        return m.encode([query], normalize_embeddings=True,
                        show_progress_bar=False)[0].tolist()
    if backend_id.startswith("tfidf"):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize
        vec = TfidfVectorizer(max_features=4096, ngram_range=(1, 2),
                              sublinear_tf=True)
        vec.fit(corpus_texts)
        Q = normalize(vec.transform([query]), norm="l2", axis=1)
        return Q.toarray()[0].tolist()
    if backend_id.startswith("hashed-bow"):
        # Pure-Python fallback; recompute IDF from corpus to match index time.
        import math, hashlib as _hl, re
        DIM = 1024
        TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
        def _tok(t): return [w.lower() for w in TOKEN_RE.findall(t) if len(w) > 2]
        def _hash(t): return int(_hl.sha1(t.encode()).hexdigest()[:8], 16) % DIM
        docs = [_tok(t) for t in corpus_texts]
        df = [0] * DIM
        for d in docs:
            seen = set()
            for w in d:
                h = _hash(w)
                if h not in seen: df[h] += 1; seen.add(h)
        N = max(1, len(docs))
        idf = [math.log((1 + N) / (1 + c)) + 1.0 for c in df]
        v = [0.0] * DIM
        for w in _tok(query):
            v[_hash(w)] += 1.0
        v = [tf * idf[i] for i, tf in enumerate(v)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]
    raise ValueError(f"unknown backend: {backend_id}")


def _cosine(a: list[float], b: list[float]) -> float:
    # Already L2-normalized → cosine == dot.
    return sum(x * y for x, y in zip(a, b))


def retrieve(expert: str, query: str, k: int) -> dict:
    idx_path = EXPERTS_ROOT / expert / "index.json"
    if not idx_path.exists():
        return {"error": f"no index for {expert}; run build_expert_index.py first",
                "expected_path": str(idx_path)}
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    chunks = idx.get("chunks", [])
    if not chunks:
        return {"expert": expert, "query": query, "results": [], "note": "empty index"}

    corpus_texts = [c["text"] for c in chunks]
    qvec = _embed_query(query, idx["backend"], corpus_texts)
    scored = []
    for c in chunks:
        e = c.get("embedding")
        if not e: continue
        s = _cosine(qvec, e)
        scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    top = scored[:k]
    return {
        "expert": expert,
        "query": query,
        "k": k,
        "backend": idx.get("backend"),
        "results": [{"score": round(s, 4),
                      "source": c["source"],
                      "offset": c["offset"],
                      "text": c["text"]}
                     for s, c in top],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expert")
    ap.add_argument("--query", required=True)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    r = retrieve(args.expert, args.query, args.k)
    s = json.dumps(r, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(s, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(s + "\n")
    return 0 if "error" not in r else 4


if __name__ == "__main__":
    sys.exit(main())
