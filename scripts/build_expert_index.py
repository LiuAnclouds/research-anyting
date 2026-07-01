#!/usr/bin/env python3
"""
build_expert_index.py — Build a per-expert retrieval index.

For a given expert, walks `knowledge-base/experts/<name>/{memory.md, corpus/}`
and emits an index at `knowledge-base/experts/<name>/index.json`. The index
holds chunked passages + their embeddings.

Two backends are supported, automatically chosen by what's installed:

  - sentence-transformers (preferred): all-MiniLM-L6-v2 (80 MB, CPU, no API key).
  - TF-IDF fallback: scikit-learn TfidfVectorizer; works out of the box on any
    machine with sklearn installed.

The fallback is good enough to validate retrieval pipelines end-to-end
without the heavy dependency. Install `sentence-transformers` later for
better recall.

Usage:
  python scripts/build_expert_index.py <expert_name>
  python scripts/build_expert_index.py --all
  python scripts/build_expert_index.py <expert_name> --backend tfidf|st

Exit codes:
  0  built successfully
  4  no backend available (need sklearn at minimum)
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
EXPERTS_ROOT = PLUGIN_ROOT / "knowledge-base" / "experts"

CHUNK_SIZE = 500          # characters
CHUNK_STRIDE = 350        # ~30% overlap


def _chunks(text: str, source: str) -> list[dict]:
    text = re.sub(r"\s+", " ", text).strip()
    out, i = [], 0
    while i < len(text):
        chunk = text[i: i + CHUNK_SIZE]
        if len(chunk) >= 80:
            cid = hashlib.sha1(f"{source}::{i}::{chunk[:60]}".encode()).hexdigest()[:12]
            out.append({"chunk_id": cid, "source": source, "offset": i, "text": chunk})
        i += CHUNK_STRIDE
    return out


def _gather(expert_dir: Path) -> list[dict]:
    chunks: list[dict] = []
    candidates = [expert_dir / "memory.md"]
    corpus = expert_dir / "corpus"
    if corpus.exists():
        candidates += sorted(corpus.rglob("*.md")) + sorted(corpus.rglob("*.txt"))
    for f in candidates:
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        chunks.extend(_chunks(text, str(f.relative_to(EXPERTS_ROOT))))
    return chunks


def _backend(name: str | None):
    """Return (backend_id, vectorize_fn). Falls back through:
       sentence-transformers → sklearn TF-IDF → pure-Python hashed bag-of-words.
    The hashed BoW fallback works on a bare Python install (no sklearn, no
    sentence-transformers); recall is worse but the pipeline always runs."""
    if name in (None, "st", "sentence-transformers"):
        try:
            from sentence_transformers import SentenceTransformer
            m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2",
                                     device="cpu")
            def vec(texts):
                arr = m.encode(texts, normalize_embeddings=True,
                               show_progress_bar=False).tolist()
                return arr
            return ("sentence-transformers/all-MiniLM-L6-v2", vec)
        except Exception:
            if name in ("st", "sentence-transformers"):
                raise
    if name in (None, "tfidf", "auto"):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.preprocessing import normalize
            state = {"vectorizer": None}
            def vec(texts):
                if state["vectorizer"] is None:
                    state["vectorizer"] = TfidfVectorizer(
                        max_features=4096, ngram_range=(1, 2), sublinear_tf=True)
                    X = state["vectorizer"].fit_transform(texts)
                else:
                    X = state["vectorizer"].transform(texts)
                X = normalize(X, norm="l2", axis=1)
                return X.toarray().tolist()
            return ("tfidf-1-2gram-l2", vec)
        except Exception:
            if name == "tfidf":
                raise

    # Pure-Python hashed bag-of-words fallback (no deps beyond stdlib).
    import math, hashlib as _hl
    DIM = 1024
    TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
    def _tok(t: str) -> list[str]:
        return [w.lower() for w in TOKEN_RE.findall(t) if len(w) > 2]
    def _hash(t: str) -> int:
        return int(_hl.sha1(t.encode()).hexdigest()[:8], 16) % DIM
    def vec(texts):
        # IDF estimate from the corpus itself.
        docs = [_tok(t) for t in texts]
        df = [0] * DIM
        for d in docs:
            seen = set()
            for w in d:
                h = _hash(w)
                if h not in seen:
                    df[h] += 1; seen.add(h)
        N = max(1, len(docs))
        idf = [math.log((1 + N) / (1 + c)) + 1.0 for c in df]
        out = []
        for d in docs:
            v = [0.0] * DIM
            for w in d:
                v[_hash(w)] += 1.0
            # tf * idf
            v = [tf * idf[i] for i, tf in enumerate(v)]
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out
    return ("hashed-bow-1024-l2", vec)


def build_one(expert: str, backend: str | None) -> dict:
    expert_dir = EXPERTS_ROOT / expert
    if not expert_dir.exists():
        raise FileNotFoundError(f"expert dir not found: {expert_dir}")
    chunks = _gather(expert_dir)
    if not chunks:
        return {"expert": expert, "n_chunks": 0, "skipped": "no content"}
    b = _backend(backend)
    if b is None:
        return {"expert": expert, "n_chunks": len(chunks), "error": "no-backend"}
    backend_id, vectorize = b
    embeddings = vectorize([c["text"] for c in chunks])
    for c, e in zip(chunks, embeddings):
        c["embedding"] = e
    index = {
        "$schema": "moon-research/expert-index-v1",
        "expert": expert,
        "backend": backend_id,
        "chunk_size": CHUNK_SIZE,
        "chunk_stride": CHUNK_STRIDE,
        "n_chunks": len(chunks),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "chunks": chunks,
    }
    out = expert_dir / "index.json"
    out.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return {"expert": expert, "n_chunks": len(chunks), "out": str(out),
            "backend": backend_id}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expert", nargs="?", help="Expert name (dir under knowledge-base/experts/)")
    ap.add_argument("--all",     action="store_true", help="Index every expert")
    ap.add_argument("--backend", choices=["st", "tfidf", "auto"], default="auto")
    args = ap.parse_args()
    backend = None if args.backend == "auto" else args.backend

    if args.all:
        results = []
        for d in sorted(EXPERTS_ROOT.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                try:
                    r = build_one(d.name, backend)
                except Exception as e:
                    r = {"expert": d.name, "error": str(e)}
                results.append(r); print(json.dumps(r), file=sys.stderr)
        print(json.dumps({"results": results,
                          "summary": {"total": len(results),
                                       "ok": sum(1 for r in results if "error" not in r and "skipped" not in r)}},
                         indent=2))
        return 0
    if not args.expert:
        ap.error("provide an expert name or --all")
    r = build_one(args.expert, backend)
    print(json.dumps(r, indent=2))
    return 0 if "error" not in r else 4


if __name__ == "__main__":
    sys.exit(main())
