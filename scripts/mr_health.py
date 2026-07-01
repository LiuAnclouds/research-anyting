#!/usr/bin/env python3
"""
mr_health.py — Score how complete a domain is (0-100).

Usage:
  python scripts/mr_health.py <domain-short-name> [--out report.json]
  python scripts/mr_health.py --all

Domain completeness rubric (7 checks, weighted):

  benchmark_registry  25 pts  ≥5 entries with domain=<name> in shared/references/benchmark-registry.yaml
  domain_agents       20 pts  <name>-idea-broker.md + <name>-rapid-prototype.md + <name>-insight-analyzer.md all present, each with valid frontmatter
  quality_gates       15 pts  <name>/references/quality-gates.md exists and lists ≥3 gates
  expert_memory       15 pts  ≥6 audit-panel experts have their memory.md non-skeleton (contain the seed marker or a real entry)
  rag_indices         10 pts  ≥6 audit-panel experts have index.json (built by build_expert_index.py)
  skill_routes         5 pts  <name>/SKILL.md exists with routing table
  references           5 pts  <name>/references/{papers,datasets,ideas}.md all present and non-empty
  frontmatter          5 pts  ci_validate's migrate --dry-run reports 0 changes pending

Total 100. Scorecard emitted with per-check status + suggested fix.

Exit codes:
  0  score >= 90
  1  score 70-89 (partial)
  2  score < 70 (broken)
  3  domain not found
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent

BENCHMARK_REGISTRY = PLUGIN_ROOT / "shared" / "references" / "benchmark-registry.yaml"
AGENTS_ROOT        = PLUGIN_ROOT / "agents"
EXPERTS_ROOT       = PLUGIN_ROOT / "knowledge-base" / "experts"

CHECKS = [
    ("benchmark_registry", 25),
    ("domain_agents",      20),
    ("quality_gates",      15),
    ("expert_memory",      15),
    ("rag_indices",        10),
    ("skill_routes",        5),
    ("references",          5),
    ("frontmatter",         5),
]


def _count_registry_entries(domain: str) -> int:
    if not BENCHMARK_REGISTRY.exists():
        return 0
    text = BENCHMARK_REGISTRY.read_text(encoding="utf-8", errors="replace")
    # matches "domain: <name>" on its own line
    return len(re.findall(rf"^\s*domain:\s*{re.escape(domain)}\s*$",
                          text, re.MULTILINE))


def _check_domain_agents(domain: str) -> tuple[int, list[str]]:
    """Return (n_present, list_of_missing)."""
    expected = [
        f"{domain}-idea-broker.md",
        f"{domain}-rapid-prototype.md",
        f"{domain}-insight-analyzer.md",
    ]
    missing = [e for e in expected if not (AGENTS_ROOT / e).exists()]
    return len(expected) - len(missing), missing


def _check_quality_gates(domain: str) -> tuple[int, str]:
    """Return (n_gates, path_or_reason)."""
    candidates = [
        PLUGIN_ROOT / domain / "references" / "quality-gates.md",
        PLUGIN_ROOT / "shared" / "references" / f"{domain}-quality-gates.md",
    ]
    for p in candidates:
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            # count table rows that look like <ID>-G<N>; accept optional **bold** wrap
            n = len(re.findall(r"\|\s*\*{0,2}[A-Z0-9]+-G\d+\*{0,2}\s*\|", text))
            return n, str(p)
    return 0, "not found"


def _check_expert_memory() -> tuple[int, list[str]]:
    """Count audit-panel experts whose memory.md has real content
    (contains seed marker OR at least one dated entry)."""
    if not EXPERTS_ROOT.exists():
        return 0, []
    seeded_marker = "<!-- seeded from _seed/generic-canonical-failures.md -->"
    date_re = re.compile(r"^## \d{4}-\d{2}-\d{2} — ", re.MULTILINE)
    ok, empty = [], []
    for expert_dir in sorted(EXPERTS_ROOT.iterdir()):
        if not expert_dir.is_dir() or expert_dir.name.startswith("_"):
            continue
        memory = expert_dir / "memory.md"
        if not memory.exists():
            empty.append(expert_dir.name); continue
        text = memory.read_text(encoding="utf-8", errors="replace")
        if seeded_marker in text or date_re.search(text):
            ok.append(expert_dir.name)
        else:
            empty.append(expert_dir.name)
    return len(ok), empty


def _check_rag_indices() -> tuple[int, list[str]]:
    if not EXPERTS_ROOT.exists():
        return 0, []
    indexed, missing = [], []
    for expert_dir in sorted(EXPERTS_ROOT.iterdir()):
        if not expert_dir.is_dir() or expert_dir.name.startswith("_"):
            continue
        if (expert_dir / "index.json").exists():
            indexed.append(expert_dir.name)
        else:
            missing.append(expert_dir.name)
    return len(indexed), missing


def _check_skill_routes(domain: str) -> tuple[bool, str]:
    for p in [PLUGIN_ROOT / domain / "SKILL.md",
              PLUGIN_ROOT / "skills" / domain / "SKILL.md"]:
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if re.search(rf"/mr\s+{re.escape(domain)}\s+", text):
                return True, str(p)
            return False, f"{p} exists but no `/mr {domain}` routes"
    return False, "not found"


def _check_references(domain: str) -> tuple[int, list[str]]:
    root = PLUGIN_ROOT / domain / "references"
    if not root.exists():
        return 0, ["papers.md", "datasets.md", "ideas.md"]
    ok, missing = 0, []
    for name in ("papers.md", "datasets.md", "ideas.md"):
        p = root / name
        if p.exists() and len(p.read_text(encoding="utf-8", errors="replace").strip()) > 50:
            ok += 1
        else:
            missing.append(name)
    return ok, missing


def _check_frontmatter() -> tuple[bool, str]:
    """Run migrate_agent_frontmatter --dry-run; 0 changes → PASS."""
    try:
        proc = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "scripts" / "migrate_agent_frontmatter.py"),
             "--dry-run"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace")
    except Exception as e:
        return False, f"could not run migrator: {e}"
    tail = (proc.stdout or "").strip().splitlines()[-2:]
    text = "\n".join(tail)
    ok = ("0/" in text) or ("0 agents" in text)
    return ok, text[:120]


def score_domain(domain: str) -> dict:
    n_registry = _count_registry_entries(domain)
    n_agents,  missing_agents  = _check_domain_agents(domain)
    n_gates,   gates_note      = _check_quality_gates(domain)
    n_memory,  empty_memory    = _check_expert_memory()
    n_rag,     missing_rag     = _check_rag_indices()
    skill_ok,  skill_note      = _check_skill_routes(domain)
    n_refs,    missing_refs    = _check_references(domain)
    fm_ok,     fm_note         = _check_frontmatter()

    checks = {
        "benchmark_registry": {
            "score": min(25, n_registry * 5),
            "max": 25, "status": "OK" if n_registry >= 5 else "PARTIAL" if n_registry > 0 else "FAIL",
            "detail": f"{n_registry} entries with domain={domain}",
            "fix": f"add ≥5 datasets via `py scripts/domain_init_extend_registry.py`" if n_registry < 5 else None,
        },
        "domain_agents": {
            "score": (n_agents * 20) // 3 if n_agents else 0,
            "max": 20, "status": "OK" if n_agents == 3 else "FAIL",
            "detail": f"{n_agents}/3 domain-specific agents present",
            "fix": f"missing: {missing_agents}" if missing_agents else None,
        },
        "quality_gates": {
            "score": 15 if n_gates >= 3 else (n_gates * 5) if n_gates else 0,
            "max": 15, "status": "OK" if n_gates >= 3 else "PARTIAL" if n_gates > 0 else "FAIL",
            "detail": f"{n_gates} gate(s) at {gates_note}",
            "fix": "create <domain>/references/quality-gates.md with ≥3 gates" if n_gates < 3 else None,
        },
        "expert_memory": {
            "score": 15 if n_memory >= 6 else (n_memory * 15) // 6,
            "max": 15, "status": "OK" if n_memory >= 6 else "PARTIAL",
            "detail": f"{n_memory} experts with real memory (out of {n_memory + len(empty_memory)})",
            "fix": "run `py scripts/domain_init_seed_memories.py`" if n_memory < 6 else None,
        },
        "rag_indices": {
            "score": 10 if n_rag >= 6 else (n_rag * 10) // 6,
            "max": 10, "status": "OK" if n_rag >= 6 else "PARTIAL",
            "detail": f"{n_rag} indices built (out of {n_rag + len(missing_rag)})",
            "fix": "run `py scripts/build_expert_index.py --all`" if n_rag < 6 else None,
        },
        "skill_routes": {
            "score": 5 if skill_ok else 0,
            "max": 5, "status": "OK" if skill_ok else "FAIL",
            "detail": skill_note,
            "fix": "create <domain>/SKILL.md with /mr <domain> routes" if not skill_ok else None,
        },
        "references": {
            "score": (n_refs * 5) // 3,
            "max": 5, "status": "OK" if n_refs == 3 else "PARTIAL" if n_refs > 0 else "FAIL",
            "detail": f"{n_refs}/3 reference files non-empty",
            "fix": f"populate: {missing_refs}" if missing_refs else None,
        },
        "frontmatter": {
            "score": 5 if fm_ok else 0,
            "max": 5, "status": "OK" if fm_ok else "FAIL",
            "detail": fm_note,
            "fix": "run `py scripts/migrate_agent_frontmatter.py --apply`" if not fm_ok else None,
        },
    }
    total = sum(c["score"] for c in checks.values())
    max_total = sum(c["max"] for c in checks.values())
    return {
        "domain": domain,
        "score": total,
        "max": max_total,
        "grade": "A" if total >= 90 else "B" if total >= 70 else "C" if total >= 50 else "F",
        "checks": checks,
    }


def _list_domains() -> list[str]:
    """Detect existing domains via <domain>/SKILL.md."""
    found = set()
    for p in PLUGIN_ROOT.iterdir():
        if p.is_dir() and (p / "SKILL.md").exists():
            found.add(p.name)
    skills_dir = PLUGIN_ROOT / "skills"
    if skills_dir.exists():
        for p in skills_dir.iterdir():
            if p.is_dir() and (p / "SKILL.md").exists() and p.name != "mr":
                found.add(p.name)
    return sorted(found)


def _print_scorecard(report: dict) -> None:
    d = report["domain"]
    print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║  /mr health {d:<57s} ║")
    print(f"╠══════════════════════════════════════════════════════════════════════╣")
    print(f"║  Score: {report['score']:>3d}/{report['max']}    Grade: {report['grade']}                                       ║")
    print(f"╠══════════════════════════════════════════════════════════════════════╣")
    for name, w in CHECKS:
        c = report["checks"][name]
        icon = "✓" if c["status"] == "OK" else "~" if c["status"] == "PARTIAL" else "✗"
        line = f"║  {icon} {name:<20s}  {c['score']:>2d}/{c['max']:<2d}   {c['detail'][:33]:<33s}  ║"
        print(line)
    print(f"╠══════════════════════════════════════════════════════════════════════╣")
    fixes = [(k, v["fix"]) for k, v in report["checks"].items() if v.get("fix")]
    if fixes:
        print(f"║  Suggested fixes:                                                    ║")
        for k, fix in fixes:
            print(f"║   [{k}] {fix[:56]:<56s} ║")
    else:
        print(f"║  All checks passed. This domain is fully provisioned.                ║")
    print(f"╚══════════════════════════════════════════════════════════════════════╝\n")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("domain", nargs="?", default=None)
    ap.add_argument("--all",  action="store_true")
    ap.add_argument("--out",  type=Path, default=None)
    args = ap.parse_args()

    if args.all:
        domains = _list_domains()
        if not domains:
            print("no domains found (looking for <domain>/SKILL.md)", file=sys.stderr)
            return 3
        reports = [score_domain(d) for d in domains]
        for r in reports:
            _print_scorecard(r)
        if args.out:
            args.out.write_text(json.dumps({"reports": reports}, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        min_score = min(r["score"] for r in reports)
        return 0 if min_score >= 90 else 1 if min_score >= 70 else 2

    if not args.domain:
        domains = _list_domains()
        print(f"available domains: {', '.join(domains) or '(none)'}", file=sys.stderr)
        print("usage: py scripts/mr_health.py <domain> | --all", file=sys.stderr)
        return 3

    report = score_domain(args.domain)
    _print_scorecard(report)
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return 0 if report["score"] >= 90 else 1 if report["score"] >= 70 else 2


if __name__ == "__main__":
    sys.exit(main())
