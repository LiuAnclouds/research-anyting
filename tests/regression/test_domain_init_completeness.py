#!/usr/bin/env python3
"""
test_domain_init_completeness.py — P5-G integration test.

End-to-end regression test for the /mr init-domain readiness pipeline
WITHOUT invoking any LLM agent.

Instead of routing through domain-researcher (which would burn tokens and
be non-deterministic), we synthesize a fake domain-research JSON blob
that conforms to `schemas/domain-research-v1.json`, then run each of the
deterministic Python scripts that domain-init.md orchestrates against
that blob. Finally we run mr_health against the synthetic domain and
assert the completeness score >= 90 (grade A).

Steps exercised (P5-A through P5-F in one pipeline):
  1. synthesize p5test_domain_research.json  (P5-A schema conformance)
  2. domain_init_extend_registry.py          (P5-B registry extend)
  3. write agent .md files + SKILL.md +
     references/*.md + quality-gates.md      (P5-C, P5-F outputs stubbed)
  4. domain_init_seed_memories.py            (P5-D memory seeding)
  5. build_expert_index.py --all             (P5-D RAG indexing)
  6. mr_health.py p5test                     (P5-E scoring)

All artifacts are cleaned up in a `finally` block so the repo is left
byte-identical to how it was before the test (with the exception of the
fixture JSON, which is committed intentionally so failures are
reproducible).

Usage:
  py tests/regression/test_domain_init_completeness.py \
      [--keep] [--out tests/regression/test_domain_init_completeness_report.json]

Exit codes:
  0  all assertions passed (mr_health score >= 90)
  1  one or more assertions failed
  2  harness itself errored (missing script, permission denied, etc.)
"""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys, traceback
from datetime import datetime, timezone
from pathlib import Path

HERE         = Path(__file__).resolve().parent
FIXTURES_DIR = HERE / "fixtures"
PLUGIN_ROOT  = HERE.parent.parent
SCRIPTS      = PLUGIN_ROOT / "scripts"
AGENTS_DIR   = PLUGIN_ROOT / "agents"
EXPERTS_ROOT = PLUGIN_ROOT / "knowledge-base" / "experts"
REGISTRY     = PLUGIN_ROOT / "shared" / "references" / "benchmark-registry.yaml"

DOMAIN       = "p5test"
DOMAIN_DIR   = PLUGIN_ROOT / DOMAIN
FIXTURE_JSON = FIXTURES_DIR / f"{DOMAIN}_domain_research.json"

REGISTRY_BLOCK_MARKER = f"# Added by domain-init for domain: {DOMAIN}"


# ============================================================================
# Step 1 — Synthetic domain-research JSON (schema-conformant)
# ============================================================================

def build_fixture_dict() -> dict:
    """Build a payload matching schemas/domain-research-v1.json.

    Every name is chosen to be collision-free with existing registry
    entries (P5TestDS-A ... P5TestDS-E) so re-running is idempotent
    from a fresh-checkout state.
    """
    datasets = []
    for tag in "ABCDE":
        datasets.append({
            "name":          f"P5TestDS-{tag}",
            "source":        "p5test-synthetic-lab",
            "url":           f"https://example.invalid/p5test-{tag.lower()}",
            "modality":      "temporal-graph",
            "license":       "CC-BY-4.0",
            "primary_paper": f"Doe et al., 2026, P5Test Corpus {tag}",
            "aliases":       [f"P5T-{tag}", f"p5test-{tag.lower()}-v1"],
            "notes":         f"Synthetic P5-G integration-test fixture entry {tag}. "
                             "Not a real dataset. Cleaned up by test harness.",
        })

    baselines = [
        {"name": "P5TestBaseline-Alpha",  "year": 2022,
         "venue": "NeurIPS 2022",
         "code_url": "https://github.com/example-invalid/p5test-alpha",
         "paper_hint": "Doe et al., 2022", "code_verified": None},
        {"name": "P5TestBaseline-Beta",   "year": 2023,
         "venue": "ICLR 2023",
         "code_url": "https://github.com/example-invalid/p5test-beta",
         "paper_hint": "Roe et al., 2023", "code_verified": None},
        {"name": "P5TestBaseline-Gamma",  "year": 2024,
         "venue": "ICML 2024",
         "code_url": None,
         "paper_hint": "Poe et al., 2024", "code_verified": None},
        {"name": "P5TestBaseline-Delta",  "year": 2025,
         "venue": "AAAI 2025",
         "code_url": "https://github.com/example-invalid/p5test-delta",
         "paper_hint": "Moe et al., 2025", "code_verified": None},
        {"name": "P5TestBaseline-Eps",    "year": 2026,
         "venue": "CVPR 2026",
         "code_url": "https://github.com/example-invalid/p5test-eps",
         "paper_hint": "Zoe et al., 2026", "code_verified": None},
    ]

    module_categories = [
        {"name": "temporal-encoder",
         "description": "Modules that produce time-aware node/edge embeddings "
                        "from event streams; consumed by scorers downstream."},
        {"name": "anomaly-scorer",
         "description": "Modules that map an embedding to a scalar score used "
                        "to rank candidate anomalies for evaluation."},
        {"name": "graph-aggregator",
         "description": "Modules that aggregate neighborhood context around a "
                        "target node; typically message-passing variants."},
        {"name": "calibration-head",
         "description": "Modules that rescale raw scores to well-calibrated "
                        "probabilities; needed to compare AUC-PR fairly."},
    ]

    venues = [
        {"name": "NeurIPS", "tier": "CCF-A", "category": "conference",
         "url": "https://neurips.cc",
         "notes": "Primary outlet for ML method papers."},
        {"name": "ICLR",    "tier": "CCF-A", "category": "conference",
         "url": "https://iclr.cc",
         "notes": "Open-review; strong representation-learning focus."},
        {"name": "AAAI",    "tier": "CCF-A", "category": "conference",
         "url": "https://aaai.org",
         "notes": "Broad AI venue; deadlines August."},
        {"name": "PAKDD",   "tier": "CCF-C", "category": "conference",
         "url": "https://pakdd.org",
         "notes": "Regional venue; useful for early prototypes."},
        {"name": "TKDD",    "tier": "CCF-B", "category": "journal",
         "url": "https://dl.acm.org/journal/tkdd",
         "notes": "ACM journal; extended DGAD work fits."},
    ]

    quality_gates = [
        {"id": "P5TEST-G1", "name": "seed-variance ceiling",
         "description": "Mean AUC-PR standard deviation across ≥3 seeds must "
                        "remain under 0.02 on the primary benchmark.",
         "axis": "evaluation_rigor", "threshold": 0.02,
         "rationale": "Guards against seed-cherry-picking, the canonical "
                      "failure documented in the Pearson-r incident."},
        {"id": "P5TEST-G2", "name": "temporal-leakage guard",
         "description": "No timestamp in the test partition may precede any "
                        "training timestamp; enforced by scripts.",
         "axis": "benchmark_integrity", "threshold": "no train-time overlap",
         "rationale": "Temporal leakage silently inflates AUC by up to 20 "
                      "points on continuous-time graphs."},
        {"id": "P5TEST-G3", "name": "code-URL live",
         "description": "Every claimed baseline code_url must return HTTP "
                        "200 on HEAD at panel time; else code_verified=false.",
         "axis": "reproducibility", "threshold": "HEAD 200",
         "rationale": "Blocks phantom-SOTA baselines lacking runnable code."},
    ]

    eval_protocols = [
        {"name": "5-seed-mean-std", "metric": "AUC-PR",
         "tolerance": 0.005,
         "notes": "Median seed used for scorecard; std reported alongside."},
        {"name": "temporal-split-eval", "metric": "AUC-ROC",
         "tolerance": 0.005,
         "notes": "Timestamps split 80/10/10 by chronological order."},
    ]

    canonical_failures = [
        {"name": "P5Test-Pearson-drift", "class": "numeric-drift",
         "description": "Cross-section Pearson-r disagrees between intro "
                        "and results; classic sign-flip class.",
         "caught_by_axis": "cross-section-equality"},
        {"name": "P5Test-phantom-baseline", "class": "hallucinated-baseline",
         "description": "Baseline cited with no code_url and no matching "
                        "bib entry; classic hallucinated-comparison bug.",
         "caught_by_axis": "cite-resolves"},
        {"name": "P5Test-time-leak", "class": "temporal-leakage",
         "description": "Test events precede train events; leaks future "
                        "information into evaluation.",
         "caught_by_axis": "benchmark_integrity"},
        {"name": "P5Test-metric-swap", "class": "metric-substitution",
         "description": "Early-stopping metric silently changed from "
                        "AUC-PR to AUC-ROC between draft revisions.",
         "caught_by_axis": "cross-section-equality"},
        {"name": "P5Test-ref-bib-drift", "class": "citation-fabrication",
         "description": "Bib entry alias duplicated with slightly different "
                        "author list; hallucination-expert must flag it.",
         "caught_by_axis": "cite-resolves"},
    ]

    return {
        "$schema":            "moon-research/domain-research-v1",
        "domain_short_name":  DOMAIN,
        "domain_description": "P5 integration test synthetic domain. Not a "
                              "real research field. Exists only so the "
                              "domain-init readiness pipeline can be "
                              "exercised end-to-end without invoking any "
                              "LLM agent.",
        "datasets":           datasets,
        "baselines":          baselines,
        "module_categories":  module_categories,
        "venues":             venues,
        "quality_gates":      quality_gates,
        "eval_protocols":     eval_protocols,
        "canonical_failures": canonical_failures,
        "generated_at":       "2026-07-01T00:00:00+00:00",
    }


# ============================================================================
# Step 4 — Stub agent files, SKILL.md, quality-gates.md, references
# ----------------------------------------------------------------------------
# Not through the actual agent — plain writes so the test is self-contained
# and deterministic.
# ============================================================================

def _agent_frontmatter(name: str, description: str,
                       critical_axes: list[str],
                       panel: str, weight: int) -> str:
    axes_inline = "[" + ", ".join(critical_axes) + "]"
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "model: inherit\n"
        "rigor_contract: three-times-verified\n"
        "parallelism_contract: max-fanout\n"
        f"panel: {panel}\n"
        f"weight: {weight}\n"
        f"critical_axes: {axes_inline}\n"
        "---\n\n"
    )


def write_domain_agents() -> list[Path]:
    """Write the three domain-specific agents with valid frontmatter."""
    written: list[Path] = []

    specs = [
        (
            f"{DOMAIN}-idea-broker",
            f"P5-G test idea broker for the {DOMAIN} synthetic domain. "
            "Generates candidate research directions with falsifiable "
            "hypotheses.",
            ["cross-section-equality", "cite-resolves"],
            "executor", 0,
        ),
        (
            f"{DOMAIN}-rapid-prototype",
            f"P5-G test rapid-prototype agent for {DOMAIN}. Produces "
            "minimal runnable code stubs for hypothesis testing.",
            ["evaluation_rigor", "reproducibility"],
            "executor", 0,
        ),
        (
            f"{DOMAIN}-insight-analyzer",
            f"P5-G test insight analyzer for {DOMAIN}. Distills experiment "
            "outputs into cross-section-consistent claims.",
            ["cross-section-equality", "evaluation_rigor"],
            "executor", 0,
        ),
    ]

    for name, desc, axes, panel, weight in specs:
        p = AGENTS_DIR / f"{name}.md"
        body = _agent_frontmatter(name, desc, axes, panel, weight)
        body += (
            f"# {name}\n\n"
            "Placeholder body written by "
            "`tests/regression/test_domain_init_completeness.py`. "
            "Cleaned up in the test's finally block.\n\n"
            "## Rigor contract\n\n"
            "Operates under `shared/references/audit-doctrine.md` — the "
            "Three-Times Rule. This is a P5-G test stub; no live claims.\n\n"
            "## Parallelism contract\n\n"
            "Operates under `shared/references/parallelism-doctrine.md`. "
            "This is a P5-G test stub; the placeholder does not dispatch "
            "real sub-work.\n"
        )
        p.write_text(body, encoding="utf-8")
        written.append(p)
    return written


def write_skill_md() -> Path:
    """Write DOMAIN/SKILL.md with /mr p5test routes."""
    DOMAIN_DIR.mkdir(exist_ok=True)
    p = DOMAIN_DIR / "SKILL.md"
    p.write_text(
        "---\n"
        f"name: mr-{DOMAIN}-research\n"
        f"description: P5-G integration test skill for {DOMAIN}. "
        f"All commands use the `/mr {DOMAIN}` prefix.\n"
        "---\n\n"
        f"# {DOMAIN} Research Domain Orchestrator (P5-G test)\n\n"
        "## Command Routing\n\n"
        "| Command | Agent Dispatched | Phase |\n"
        "|---------|------------------|-------|\n"
        f"| `/mr {DOMAIN} idea \"topic\"`         | {DOMAIN}-idea-broker      | Exploration  |\n"
        f"| `/mr {DOMAIN} prototype \"approach\"` | {DOMAIN}-rapid-prototype  | Construction |\n"
        f"| `/mr {DOMAIN} analyze <results>`     | {DOMAIN}-insight-analyzer | Validation   |\n",
        encoding="utf-8",
    )
    return p


def write_references() -> list[Path]:
    """Write DOMAIN/references/{papers,datasets,ideas}.md with >50 chars each."""
    refs_dir = DOMAIN_DIR / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, body in [
        ("papers.md",
         f"# {DOMAIN} — canonical papers (P5-G test fixture)\n\n"
         "- Doe et al., 2022, P5TestBaseline-Alpha, NeurIPS 2022.\n"
         "- Roe et al., 2023, P5TestBaseline-Beta, ICLR 2023.\n"
         "- Poe et al., 2024, P5TestBaseline-Gamma, ICML 2024.\n"
         "Placeholder body cleaned up by the P5-G test harness.\n"),
        ("datasets.md",
         f"# {DOMAIN} — canonical datasets (P5-G test fixture)\n\n"
         "- P5TestDS-A, P5TestDS-B, P5TestDS-C, P5TestDS-D, P5TestDS-E.\n"
         "All synthetic; not to be used outside the P5-G regression test.\n"),
        ("ideas.md",
         f"# {DOMAIN} — active idea board (P5-G test fixture)\n\n"
         "- Test-idea 1: verify domain-init readiness score >= 90.\n"
         "- Test-idea 2: verify cleanup is idempotent across reruns.\n"
         "Placeholder body cleaned up by the P5-G test harness.\n"),
    ]:
        p = refs_dir / name
        p.write_text(body, encoding="utf-8")
        written.append(p)
    return written


def write_quality_gates(payload: dict) -> Path:
    """Write DOMAIN/references/quality-gates.md as a table.

    mr_health counts `| <ID>-G<N> |` rows to score this axis.
    """
    refs_dir = DOMAIN_DIR / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    p = refs_dir / "quality-gates.md"
    lines = [
        f"# {DOMAIN} — domain-specific quality gates (P5-G test fixture)\n",
        "",
        "| Gate ID | Name | Axis | Threshold | Rationale |",
        "|---------|------|------|-----------|-----------|",
    ]
    for g in payload["quality_gates"]:
        lines.append(
            f"| {g['id']} | {g['name']} | {g['axis']} | "
            f"{g['threshold']} | {g['rationale']} |"
        )
    lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


# ============================================================================
# Step 3 — Registry extension
# ============================================================================

def run_registry_extend(dry_run: bool) -> dict:
    cmd = [sys.executable, str(SCRIPTS / "domain_init_extend_registry.py"),
           str(FIXTURE_JSON)]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace")
    # The script emits a JSON summary on stdout (last thing). Parse it.
    summary = _extract_trailing_json(proc.stdout) or {}
    return {
        "returncode": proc.returncode,
        "summary":    summary,
        "stdout":     proc.stdout,
        "stderr":     proc.stderr,
    }


def _extract_trailing_json(text: str) -> dict | None:
    """Find the last {...} JSON blob in the output."""
    if not text:
        return None
    # scan for the last '{' whose brace matches to EOF
    idx = text.rfind("\n{")
    if idx < 0:
        idx = text.find("{")
    if idx < 0:
        return None
    tail = text[idx:].strip()
    try:
        return json.loads(tail)
    except Exception:
        return None


# ============================================================================
# Step 5 — Seed memories
# ============================================================================

def run_seed_memories() -> dict:
    cmd = [sys.executable, str(SCRIPTS / "domain_init_seed_memories.py")]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace")
    summary = _extract_trailing_json(proc.stdout) or {}
    return {
        "returncode": proc.returncode,
        "summary":    summary,
        "stdout":     proc.stdout,
        "stderr":     proc.stderr,
    }


# ============================================================================
# Step 6 — Build expert index
# ============================================================================

def run_build_expert_index() -> dict:
    cmd = [sys.executable, str(SCRIPTS / "build_expert_index.py"), "--all"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                          encoding="utf-8", errors="replace")
    return {
        "returncode": proc.returncode,
        "stdout":     proc.stdout,
        "stderr":     proc.stderr,
    }


# ============================================================================
# Step 7 — mr_health scoring
# ============================================================================

def run_mr_health(out_path: Path) -> dict:
    cmd = [sys.executable, str(SCRIPTS / "mr_health.py"), DOMAIN,
           "--out", str(out_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                          encoding="utf-8", errors="replace")
    try:
        report = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception as e:
        report = {"error": f"could not parse mr_health output: {e}",
                  "stdout": proc.stdout, "stderr": proc.stderr}
    return {
        "returncode": proc.returncode,
        "report":     report,
        "stdout":     proc.stdout,
        "stderr":     proc.stderr,
    }


# ============================================================================
# Cleanup (idempotent + safe)
# ============================================================================

def cleanup(created_paths: list[Path], registry_snapshot: str | None) -> dict:
    """Remove all artifacts the test created. Idempotent — safe to call twice."""
    removed: list[str] = []
    errors:  list[str] = []

    # 1) delete created files
    for p in created_paths:
        try:
            if p.exists() and p.is_file():
                p.unlink()
                removed.append(str(p))
        except Exception as e:
            errors.append(f"unlink {p}: {e}")

    # 2) remove DOMAIN dir if empty-ish (only contains our created files)
    try:
        if DOMAIN_DIR.exists():
            # Recursively remove — but only if it looks like our own dir
            # (safety: it must be the exact DOMAIN we created).
            if DOMAIN_DIR.name == DOMAIN and DOMAIN_DIR.is_dir():
                shutil.rmtree(DOMAIN_DIR, ignore_errors=True)
                removed.append(str(DOMAIN_DIR))
    except Exception as e:
        errors.append(f"rmtree {DOMAIN_DIR}: {e}")

    # 3) strip the registry-append block. Prefer restoring the pre-test
    #    snapshot when we have one; else surgically remove the block.
    try:
        if REGISTRY.exists():
            if registry_snapshot is not None:
                REGISTRY.write_text(registry_snapshot, encoding="utf-8")
                removed.append(f"{REGISTRY} (restored from snapshot)")
            else:
                text = REGISTRY.read_text(encoding="utf-8", errors="replace")
                stripped = _strip_domain_block(text, DOMAIN)
                if stripped != text:
                    REGISTRY.write_text(stripped, encoding="utf-8")
                    removed.append(f"{REGISTRY} (block stripped)")
    except Exception as e:
        errors.append(f"registry restore: {e}")

    return {"removed": removed, "errors": errors}


def _strip_domain_block(text: str, domain: str) -> str:
    """Remove every registry entry whose `domain: <domain>` line matches, and
    the sentinel comment block domain_init_extend_registry.py inserted.

    Approach: walk the file line-by-line, tracking entry boundaries (each
    entry starts with `  - name:`). Drop any entry whose lines contain
    `domain: <domain>`. Also drop the marker banner + the two comment
    dashed lines around it.
    """
    lines = text.splitlines(keepends=False)
    out: list[str] = []
    i = 0
    n = len(lines)
    marker_body = f"# Added by domain-init for domain: {domain}"

    # First pass: drop the banner block (3 comment lines + surrounding blank).
    # The block looks like:
    #   (blank)
    #   "  # ------..."
    #   "  # Added by domain-init for domain: <domain>"
    #   "  # ------..."
    #   (blank)
    filtered: list[str] = []
    j = 0
    while j < n:
        line = lines[j]
        if marker_body in line:
            # walk back and forward to consume the surrounding dashed comments
            # and one blank line on each side
            # drop the two neighbours if they are dashed comment lines
            if filtered and filtered[-1].strip().startswith("# ---"):
                filtered.pop()
            # drop a preceding blank
            if filtered and filtered[-1].strip() == "":
                filtered.pop()
            # skip this line
            # skip a following dashed comment
            k = j + 1
            if k < n and lines[k].strip().startswith("# ---"):
                k += 1
            # skip a following blank
            if k < n and lines[k].strip() == "":
                k += 1
            j = k
            continue
        filtered.append(line)
        j += 1

    # Second pass: drop entries with matching domain.
    i = 0
    n = len(filtered)
    while i < n:
        line = filtered[i]
        # detect start of an entry: "  - name: ..."
        if re.match(r"^\s*-\s*name:\s*", line):
            # capture the whole entry (until next "  - name:" or dedent)
            j = i + 1
            while j < n:
                nxt = filtered[j]
                if re.match(r"^\s*-\s*name:\s*", nxt):
                    break
                # a fully-dedented non-blank line also ends the entry
                # (e.g. a new top-level key). But registry keeps everything
                # under `datasets:` so this rarely triggers.
                if nxt and not nxt.startswith(" ") and not nxt.startswith("\t") \
                        and not nxt.startswith("#") and nxt.strip() != "":
                    break
                j += 1
            block = filtered[i:j]
            body = "\n".join(block)
            if re.search(rf"^\s*domain:\s*{re.escape(domain)}\s*$",
                         body, re.MULTILINE):
                # drop
                i = j
                continue
            out.extend(block)
            i = j
        else:
            out.append(line)
            i += 1

    result = "\n".join(out)
    # collapse >2 blank lines to 1
    result = re.sub(r"\n{3,}", "\n\n", result)
    if not result.endswith("\n"):
        result += "\n"
    return result


# ============================================================================
# Driver
# ============================================================================

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true",
                    help="Skip cleanup — leave artifacts on disk for inspection.")
    ap.add_argument("--out",  type=Path,
                    default=HERE / "test_domain_init_completeness_report.json")
    args = ap.parse_args()

    # ------------------------------------------------------------------------
    # Pre-flight: skip if the domain already exists (safety)
    # ------------------------------------------------------------------------
    if DOMAIN_DIR.exists():
        print(f"SKIP: {DOMAIN_DIR} already exists — refusing to clobber. "
              f"Remove it manually and rerun.", file=sys.stderr)
        return 2
    existing_agent = AGENTS_DIR / f"{DOMAIN}-idea-broker.md"
    if existing_agent.exists():
        print(f"SKIP: {existing_agent} already exists — refusing to clobber.",
              file=sys.stderr)
        return 2

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    assertions: list[dict] = []
    created_paths: list[Path] = []
    registry_snapshot: str | None = None
    exit_code = 0

    def _assert(name: str, ok: bool, detail: str = "") -> None:
        assertions.append({"name": name, "ok": bool(ok), "detail": detail})
        icon = "PASS" if ok else "FAIL"
        print(f"  [{icon}] {name}: {detail}")

    print(f"=== P5-G integration test: /mr init-domain readiness pipeline ===")
    print(f"domain      = {DOMAIN}")
    print(f"plugin root = {PLUGIN_ROOT}")

    try:
        # ---------------------------------------------------------------
        # Snapshot the registry so cleanup can restore it byte-for-byte.
        # ---------------------------------------------------------------
        if REGISTRY.exists():
            registry_snapshot = REGISTRY.read_text(encoding="utf-8")
        else:
            print(f"ERROR: registry not found at {REGISTRY}", file=sys.stderr)
            return 2

        # ---------------------------------------------------------------
        # Step 1: synthesize fixture JSON
        # ---------------------------------------------------------------
        print("\n[1/7] Synthesizing fake domain-research JSON ...")
        payload = build_fixture_dict()
        FIXTURE_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        created_paths.append(FIXTURE_JSON)  # remove on cleanup
        _assert("fixture-json-written",
                FIXTURE_JSON.exists() and FIXTURE_JSON.stat().st_size > 100,
                f"{FIXTURE_JSON.name} ({FIXTURE_JSON.stat().st_size} B)")

        # ---------------------------------------------------------------
        # Step 2: dry-run registry extend
        # ---------------------------------------------------------------
        print("\n[2/7] domain_init_extend_registry.py --dry-run ...")
        dry = run_registry_extend(dry_run=True)
        added_dry = (dry["summary"] or {}).get("added", -1)
        collisions_dry = (dry["summary"] or {}).get("collisions", [])
        _assert("dry-run-adds-5", added_dry == 5,
                f"would add {added_dry} (expected 5)")
        _assert("dry-run-no-collisions", not collisions_dry,
                f"{len(collisions_dry)} collisions")

        # ---------------------------------------------------------------
        # Step 3: real registry extend
        # ---------------------------------------------------------------
        print("\n[3/7] domain_init_extend_registry.py (apply) ...")
        real = run_registry_extend(dry_run=False)
        added_real = (real["summary"] or {}).get("added", -1)
        _assert("registry-added-5", added_real == 5,
                f"added {added_real} (expected 5)")
        _assert("registry-block-marker-present",
                REGISTRY_BLOCK_MARKER in REGISTRY.read_text(encoding="utf-8",
                                                            errors="replace"),
                "marker line found")

        # ---------------------------------------------------------------
        # Step 4: write domain agents + SKILL + refs + quality-gates
        # ---------------------------------------------------------------
        print("\n[4/7] Writing agents / SKILL / refs / quality-gates ...")
        created_paths.extend(write_domain_agents())
        created_paths.append(write_skill_md())
        created_paths.extend(write_references())
        created_paths.append(write_quality_gates(payload))

        for name in [f"{DOMAIN}-idea-broker.md",
                     f"{DOMAIN}-rapid-prototype.md",
                     f"{DOMAIN}-insight-analyzer.md"]:
            _assert(f"agent-{name}",
                    (AGENTS_DIR / name).exists(),
                    f"{AGENTS_DIR / name}")
        _assert("skill-md",     (DOMAIN_DIR / "SKILL.md").exists(),
                str(DOMAIN_DIR / "SKILL.md"))
        _assert("quality-gates",
                (DOMAIN_DIR / "references" / "quality-gates.md").exists(),
                "table with 3 gates")
        for r in ("papers.md", "datasets.md", "ideas.md"):
            _assert(f"reference-{r}",
                    (DOMAIN_DIR / "references" / r).exists(),
                    f"{DOMAIN_DIR / 'references' / r}")

        # ---------------------------------------------------------------
        # Step 5: seed memories
        # ---------------------------------------------------------------
        print("\n[5/7] domain_init_seed_memories.py ...")
        seed = run_seed_memories()
        n_seeded  = (seed["summary"] or {}).get("n_experts_seeded", 0)
        skipped   = (seed["summary"] or {}).get("skipped", []) or []
        already   = sum(1 for s in skipped
                        if "already seeded" in str(s.get("reason", "")))
        # Success means: script ran cleanly AND EITHER seeded ≥1 expert
        # (first run on a fresh checkout) OR observed ≥1 already-seeded
        # expert (subsequent runs). Both prove the seed script exercised
        # its full loop.
        _assert("memories-seed-script-rc",
                seed["returncode"] == 0,
                f"rc={seed['returncode']}")
        _assert("memories-seeded-or-already",
                (n_seeded + already) >= 1,
                f"n_seeded={n_seeded}, n_already_seeded={already}")

        # ---------------------------------------------------------------
        # Step 6: build_expert_index --all
        # ---------------------------------------------------------------
        print("\n[6/7] build_expert_index.py --all ...")
        idx = run_build_expert_index()
        # count experts that got an index.json
        indexed = [d.name for d in EXPERTS_ROOT.iterdir()
                   if d.is_dir() and not d.name.startswith("_")
                   and (d / "index.json").exists()]
        candidates = [d.name for d in EXPERTS_ROOT.iterdir()
                      if d.is_dir() and not d.name.startswith("_")]
        _assert("build-expert-index-returncode",
                idx["returncode"] == 0,
                f"rc={idx['returncode']}")
        _assert("all-experts-indexed",
                len(indexed) == len(candidates) and len(candidates) >= 6,
                f"{len(indexed)}/{len(candidates)} experts indexed")

        # ---------------------------------------------------------------
        # Step 7: mr_health scoring
        # ---------------------------------------------------------------
        print("\n[7/7] mr_health.py p5test ...")
        health_out = HERE / f"{DOMAIN}_health.json"
        health = run_mr_health(health_out)
        rep = health["report"] or {}
        score = rep.get("score", -1)
        grade = rep.get("grade", "?")
        _assert("mr-health-score-ge-90", score >= 90,
                f"score={score}/100 grade={grade}")
        # per-check drill-down for debugging
        for name, check in (rep.get("checks") or {}).items():
            _assert(f"check-{name}",
                    check.get("status") in ("OK", "PARTIAL"),
                    f"{check.get('status')} {check.get('score')}/{check.get('max')}"
                    f" — {check.get('detail')}")

        # temp health file cleanup
        try: health_out.unlink()
        except Exception: pass

        # ---------------------------------------------------------------
        # Summary
        # ---------------------------------------------------------------
        n_pass = sum(1 for a in assertions if a["ok"])
        n_fail = sum(1 for a in assertions if not a["ok"])
        exit_code = 0 if n_fail == 0 else 1

        summary = {
            "$schema":       "moon-research/p5g-integration-v1",
            "generated_at":  datetime.now(timezone.utc).isoformat(),
            "domain":        DOMAIN,
            "assertions":    assertions,
            "counts":        {"pass": n_pass, "fail": n_fail,
                              "total": len(assertions)},
            "steps": {
                "registry_dry":  dry.get("summary"),
                "registry_real": real.get("summary"),
                "seed_memories": seed.get("summary"),
                "mr_health":     rep,
            },
        }
        args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                            encoding="utf-8")

        # Print an ASCII summary table
        print("\n" + "=" * 72)
        print(f"P5-G integration test — {n_pass}/{len(assertions)} assertions passed")
        print("=" * 72)
        col_w = max((len(a["name"]) for a in assertions), default=20)
        for a in assertions:
            icon = "PASS" if a["ok"] else "FAIL"
            print(f"  [{icon}] {a['name']:<{col_w}s}  {a['detail']}")
        print("=" * 72)
        print(f"mr_health score: {score}/100 (grade {grade})")
        print(f"report written:  {args.out}")

        if n_fail == 0:
            print("\nOK — domain-init readiness pipeline is calibrated.")
        else:
            print(f"\nFAIL — {n_fail} assertion(s) missed. See report.")

    except Exception as e:
        print(f"HARNESS ERROR: {e}", file=sys.stderr)
        traceback.print_exc()
        exit_code = 2

    finally:
        # -------- Cleanup (idempotent) --------
        if args.keep:
            print("\n--keep set — skipping cleanup.")
        else:
            print("\n=== Cleanup ===")
            cr = cleanup(created_paths, registry_snapshot)
            for r in cr["removed"]:
                print(f"  removed: {r}")
            for err in cr["errors"]:
                print(f"  cleanup-error: {err}", file=sys.stderr)
            # Re-run cleanup with no snapshot to confirm idempotence
            cr2 = cleanup([], registry_snapshot=None)
            if cr2["errors"]:
                for err in cr2["errors"]:
                    print(f"  cleanup-idem-error: {err}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
