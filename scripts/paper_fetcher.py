#!/usr/bin/env python3
"""
Paper Fetcher — Multi-source academic paper search and retrieval.
Supports: Semantic Scholar, arXiv, DBLP, CrossRef, and OpenReview APIs.
Usage: python paper_fetcher.py --query "topic" --sources all --max 100 --output results.json
"""
import argparse, json, sys, time, urllib.request, urllib.parse, urllib.error, ssl, os
from datetime import datetime

# SSL context: use system certificates by default, allow override for restricted environments
def _create_ssl_context():
    """Create SSL context. If MOON_INSECURE_SSL is set, skip verification (for restricted networks)."""
    if os.environ.get("MOON_INSECURE_SSL", "").lower() in ("1", "true", "yes"):
        print("  [WARNING] SSL verification disabled (MOON_INSECURE_SSL=1)", file=sys.stderr)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()

ssl_ctx = _create_ssl_context()

def fetch_semantic_scholar(query, max_results=100, year_start=None, year_end=None):
    """Search Semantic Scholar API."""
    base = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "title,authors,year,venue,publicationDate,citationCount,externalIds,openAccessPdf,abstract"
    }
    if year_start:
        params["year"] = f"{year_start}-{year_end or datetime.now().year}"
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Moon-Research/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode())
        papers = []
        for p in data.get("data", []):
            papers.append({
                "source": "semantic_scholar",
                "title": p.get("title", ""),
                "authors": [a.get("name", "") for a in p.get("authors", [])],
                "year": p.get("year"),
                "venue": p.get("venue", ""),
                "citations": p.get("citationCount", 0),
                "doi": p.get("externalIds", {}).get("DOI", ""),
                "arxiv_id": p.get("externalIds", {}).get("ArXiv", ""),
                "pdf_url": p.get("openAccessPdf", {}).get("url", "") if p.get("openAccessPdf") else "",
                "abstract": p.get("abstract", "")[:500] if p.get("abstract") else ""
            })
        return papers
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, OSError) as e:
        print(f"  [Semantic Scholar] Error: {e}", file=sys.stderr)
        return []

def fetch_arxiv(query, max_results=50):
    """Search arXiv API."""
    base = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Moon-Research/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            data = resp.read().decode()
        import xml.etree.ElementTree as ET
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(data)
        papers = []
        for entry in root.findall("atom:entry", ns):
            papers.append({
                "source": "arxiv",
                "title": (entry.find("atom:title", ns).text or "").strip().replace("\n", " "),
                "authors": [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None],
                "year": entry.find("atom:published", ns).text[:4] if entry.find("atom:published", ns) is not None else "",
                "arxiv_id": entry.find("atom:id", ns).text.split("/")[-1] if entry.find("atom:id", ns) is not None else "",
                "abstract": (entry.find("atom:summary", ns).text or "")[:500].strip().replace("\n", " "),
                "pdf_url": "",
                "venue": "arXiv preprint",
                "citations": 0
            })
        return papers
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, OSError) as e:
        print(f"  [arXiv] Error: {e}", file=sys.stderr)
        return []

def fetch_dblp(query, max_results=50):
    """Search DBLP API."""
    base = "https://dblp.org/search/publ/api"
    params = {"q": query, "format": "json", "h": max_results}
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Moon-Research/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode())
        papers = []
        for hit in data.get("result", {}).get("hits", {}).get("hit", []):
            info = hit.get("info", {})
            papers.append({
                "source": "dblp",
                "title": info.get("title", ""),
                "authors": [a.get("text", "") for a in info.get("authors", {}).get("author", [])] if isinstance(info.get("authors", {}).get("author", []), list) else [info.get("authors", {}).get("author", {}).get("text", "")] if info.get("authors", {}).get("author") else [],
                "year": info.get("year", ""),
                "venue": info.get("venue", ""),
                "doi": info.get("doi", ""),
                "citations": 0,
                "dblp_url": info.get("url", "")
            })
        return papers
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, OSError) as e:
        print(f"  [DBLP] Error: {e}", file=sys.stderr)
        return []

def fetch_crossref(query, max_results=50):
    """Search CrossRef API for DOI-verified papers."""
    base = "https://api.crossref.org/works"
    params = {"query": query, "rows": max_results, "filter": "type:journal-article"}
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Moon-Research/1.0 (mailto:research@example.com)"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode())
        papers = []
        for item in data.get("message", {}).get("items", []):
            papers.append({
                "source": "crossref",
                "title": item.get("title", [""])[0] if item.get("title") else "",
                "authors": [f"{a.get('given','')} {a.get('family','')}" for a in item.get("author", [])],
                "year": item.get("created", {}).get("date-parts", [[0]])[0][0],
                "venue": item.get("container-title", [""])[0] if item.get("container-title") else "",
                "doi": item.get("DOI", ""),
                "citations": item.get("is-referenced-by-count", 0),
                "publisher": item.get("publisher", "")
            })
        return papers
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, OSError) as e:
        print(f"  [CrossRef] Error: {e}", file=sys.stderr)
        return []

def classify_venue_tier(venue, year):
    """Classify paper venue into CCF tier based on venue name."""
    venue_lower = (venue or "").lower()
    # CCF-A conferences
    ccf_a_conf = ["aaai", "neurips", "nips", "icml", "iclr", "kdd", "www", "ijcai", "cvpr", "iccv", "acl", "sigmod", "sigir", "mobicom", "sosp", "osdi", "stoc", "focs", "isca", "micro", "hpca", "sc", "siggraph"]
    # CCF-A journals
    ccf_a_jour = ["tpami", "tkde", "ijcv", "jmlr", "tods", "tois", "vldb", "ai journal", "artificial intelligence"]
    # CCF-B conferences
    ccf_b_conf = ["cikm", "icdm", "ecml", "pkdd", "sdm", "eccv", "emnlp", "naacl", "coling", "rss", "corl", "icra", "recsys", "wsdm", "cikm", "icde", "middleware", "sensys", "ipsn", "eurosys", "fast", "usenix atc", "ccs", "ndss", "esorics", "raid", "asiacrypt", "crypto", "eurocrypt"]
    # CCF-B journals
    ccf_b_jour = ["tkdd", "tnnls", "neural networks", "pattern recognition", "information sciences", "dmkd", "kais", "machine learning", "jair", "cviu", "tcyb", "tfs", "tec", "tac", "taslp", "ijar", "dke", "tweb", "ipm", "is journal", "jasist", "jws", "neural computation", "evolutionary computation"]
    # CCF-C conferences
    ccf_c_conf = ["iros", "wacv", "icann", "ijcnn", "iconip", "pakdd", "dasefaa"]
    # CCF-C journals
    ccf_c_jour = ["neurocomputing", "applied intelligence", "neural processing letters", "eaai", "pattern analysis and applications"]

    for conf in ccf_a_conf:
        if conf in venue_lower:
            return "CCF-A"
    for jour in ccf_a_jour:
        if jour in venue_lower:
            return "CCF-A"
    for conf in ccf_b_conf:
        if conf in venue_lower:
            return "CCF-B"
    for jour in ccf_b_jour:
        if jour in venue_lower:
            return "CCF-B"
    for conf in ccf_c_conf:
        if conf in venue_lower:
            return "CCF-C"
    for jour in ccf_c_jour:
        if jour in venue_lower:
            return "CCF-C"
    if "arxiv" in venue_lower or "preprint" in venue_lower:
        return "Preprint"
    return "Unknown"

def deduplicate(papers):
    """Deduplicate papers by title similarity."""
    seen = set()
    unique = []
    for p in papers:
        title_key = p["title"].lower().strip()[:80]
        if title_key not in seen:
            seen.add(title_key)
            unique.append(p)
    return unique

def rank_papers(papers, prefer_ccf_a=True, prefer_code=True, prefer_recent=True):
    """Rank papers by venue tier, citations, recency, and code availability."""
    def score(p):
        s = 0
        tier = p.get("ccf_tier", "Unknown")
        if tier == "CCF-A": s += 100
        elif tier == "CCF-B": s += 60
        elif tier == "CCF-C": s += 30
        elif tier == "Preprint": s += 10
        s += min(p.get("citations", 0) / 10, 50)  # Cap at 50 for citation score
        if prefer_recent and p.get("year"):
            try:
                year = int(p["year"])
                if year >= 2024: s += 30
                elif year >= 2022: s += 20
                elif year >= 2020: s += 10
            except: pass
        return s
    return sorted(papers, key=score, reverse=True)

def main():
    p = argparse.ArgumentParser(description="Multi-Source Academic Paper Fetcher")
    p.add_argument("--query", required=True, help="Search query")
    p.add_argument("--sources", default="all", help="Comma-separated: semantic_scholar,arxiv,dblp,crossref,all")
    p.add_argument("--max", type=int, default=100, help="Max results per source")
    p.add_argument("--year-start", type=int, help="Start year filter")
    p.add_argument("--year-end", type=int, help="End year filter")
    p.add_argument("--output", default="papers.json", help="Output JSON file")
    p.add_argument("--classify", action="store_true", help="Classify papers by CCF tier")
    p.add_argument("--ccf-only", type=str, help="Filter by CCF tier: A,B,C (comma-separated)")
    args = p.parse_args()

    sources = args.sources.split(",")
    if "all" in sources:
        sources = ["semantic_scholar", "arxiv", "dblp", "crossref"]

    all_papers = []

    print(f"Searching for: {args.query}")
    print(f"Sources: {', '.join(sources)}")
    print("-" * 60)

    for source in sources:
        source = source.strip()
        print(f"\n[{source}] Searching...")
        if source == "semantic_scholar":
            papers = fetch_semantic_scholar(args.query, args.max, args.year_start, args.year_end)
        elif source == "arxiv":
            papers = fetch_arxiv(args.query, min(args.max, 50))
        elif source == "dblp":
            papers = fetch_dblp(args.query, min(args.max, 50))
        elif source == "crossref":
            papers = fetch_crossref(args.query, min(args.max, 50))
        else:
            print(f"  Unknown source: {source}")
            continue

        print(f"  Found: {len(papers)} papers")
        all_papers.extend(papers)

    # Deduplicate
    all_papers = deduplicate(all_papers)
    print(f"\nAfter deduplication: {len(all_papers)} unique papers")

    # Classify by CCF tier
    if args.classify or args.ccf_only:
        for paper in all_papers:
            paper["ccf_tier"] = classify_venue_tier(paper.get("venue", ""), paper.get("year", 0))

    # Filter by CCF tier
    if args.ccf_only:
        tiers = [t.strip().upper() for t in args.ccf_only.split(",")]
        all_papers = [p for p in all_papers if p.get("ccf_tier", "") in tiers]
        print(f"After CCF filter ({args.ccf_only}): {len(all_papers)} papers")

    # Rank
    all_papers = rank_papers(all_papers)

    # Summary by source
    sources_count = {}
    for p in all_papers:
        src = p["source"]
        sources_count[src] = sources_count.get(src, 0) + 1

    print(f"\n=== Results Summary ===")
    print(f"Total unique papers: {len(all_papers)}")
    for src, cnt in sorted(sources_count.items()):
        print(f"  {src}: {cnt}")

    if args.classify:
        tiers_count = {}
        for p in all_papers:
            t = p.get("ccf_tier", "Unknown")
            tiers_count[t] = tiers_count.get(t, 0) + 1
        print(f"\nBy CCF Tier:")
        for t, cnt in sorted(tiers_count.items()):
            print(f"  {t}: {cnt}")

    # Save
    output = {
        "query": args.query,
        "date": datetime.now().isoformat(),
        "sources": sources,
        "total": len(all_papers),
        "papers": all_papers
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {args.output}")

if __name__ == "__main__":
    main()