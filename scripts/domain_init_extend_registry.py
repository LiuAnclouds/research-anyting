#!/usr/bin/env python3
"""domain_init_extend_registry.py

Append `datasets[]` from a domain-research JSON (per schemas/domain-research-v1.json)
into shared/references/benchmark-registry.yaml.

Usage:
    python scripts/domain_init_extend_registry.py <domain-research.json>
                                                  [--registry PATH]
                                                  [--dry-run]

Behavior:
    1. Read the domain-research JSON.
    2. Read benchmark-registry.yaml as text (comments preserved — we append,
       not rewrite).
    3. For each dataset in the JSON:
       - Normalize its keys to the registry entry shape
         (name/source/url/modality/n_*/license/primary_paper/aliases/domain).
       - Set `domain: <domain_short_name>` from the JSON's top-level field.
       - Set `verified_at: pending` — a marker for ci_validate to later run
         paper_fetcher against.
       - Check for alias/name collisions with existing entries; skip+warn if hit.
    4. Append new entries to the yaml file (before the trailing newline).
    5. `--dry-run` prints what would be added; without it, writes.

Exit codes:
    0 — ok (all new datasets appended or all skipped cleanly)
    1 — collisions found (nothing appended, or partial with skips)
    2 — IO error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Canonical order of keys in an entry. Optional keys are only emitted if present.
KEY_ORDER = [
    "name",
    "source",
    "url",
    "modality",
    "n_nodes",
    "n_edges",
    "n_samples",
    "anomaly_rate",
    "heterophily_h",
    "license",
    "primary_paper",
    "aliases",
    "domain",
    "verified_at",
]

# Aliases in the input JSON that map to registry keys.
KEY_SYNONYMS = {
    "size": "n_samples",
    "num_samples": "n_samples",
    "num_nodes": "n_nodes",
    "num_edges": "n_edges",
    "paper": "primary_paper",
    "bibkey": "primary_paper",
    "bib_key": "primary_paper",
    "homepage": "url",
    "link": "url",
    "host": "source",
}


def normalize_entry(raw: dict[str, Any], domain: str) -> dict[str, Any]:
    """Map raw dataset dict keys to registry shape and inject domain/verified_at."""
    out: dict[str, Any] = {}
    for k, v in raw.items():
        canonical = KEY_SYNONYMS.get(k, k)
        out[canonical] = v
    out["domain"] = domain
    out["verified_at"] = "pending"
    return out


# ------------------------------- YAML parsing --------------------------------
# We do a minimal parse of just the existing entry `name:` and `aliases:` fields
# so we can detect collisions without pulling in PyYAML. This keeps the tool
# dependency-free and preserves comments perfectly on write.

NAME_RE = re.compile(r"^\s*-\s*name:\s*(.+?)\s*$")
ALIASES_INLINE_RE = re.compile(r"^\s*aliases:\s*\[(.*)\]\s*$")


def existing_identifiers(registry_text: str) -> set[str]:
    """Return the set of lowercased names+aliases already in the registry."""
    ids: set[str] = set()
    for line in registry_text.splitlines():
        m = NAME_RE.match(line)
        if m:
            ids.add(_norm(m.group(1)))
            continue
        m = ALIASES_INLINE_RE.match(line)
        if m:
            body = m.group(1)
            for tok in body.split(","):
                tok = tok.strip().strip("'\"")
                if tok:
                    ids.add(_norm(tok))
    return ids


def _norm(s: str) -> str:
    return s.strip().strip("'\"").lower()


# ------------------------------- YAML emitting -------------------------------

def _scalar(v: Any) -> str:
    """Render a scalar as YAML."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # Quote if it contains characters that would confuse a YAML reader.
    if any(c in s for c in ":#[]{}&*!|>'\"%@`") or s.strip() != s:
        return json.dumps(s)  # produces valid double-quoted YAML
    return s


def render_entry(entry: dict[str, Any]) -> str:
    """Render a normalized entry as YAML text (2-space indent, one entry)."""
    lines: list[str] = []
    keys = [k for k in KEY_ORDER if k in entry]
    # Include any non-canonical keys (unknown) at the end, sorted.
    extras = sorted(k for k in entry if k not in KEY_ORDER)
    keys.extend(extras)
    first = True
    for k in keys:
        v = entry[k]
        prefix = "  - " if first else "    "
        first = False
        if isinstance(v, list):
            inline = "[" + ", ".join(_scalar(x) for x in v) + "]"
            lines.append(f"{prefix}{k}: {inline}")
        else:
            lines.append(f"{prefix}{k}: {_scalar(v)}")
    return "\n".join(lines) + "\n"


# ---------------------------------- main ------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Append domain-research datasets into benchmark-registry.yaml"
    )
    ap.add_argument("domain_json", type=Path, help="Path to domain-research JSON")
    ap.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Path to benchmark-registry.yaml (default: shared/references/benchmark-registry.yaml)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    # Default registry path lives at <plugin-root>/shared/references/benchmark-registry.yaml,
    # discovered relative to this script.
    if args.registry is None:
        registry_path = (
            Path(__file__).resolve().parent.parent
            / "shared"
            / "references"
            / "benchmark-registry.yaml"
        )
    else:
        registry_path = args.registry.resolve()

    # ---- Load domain JSON ----
    try:
        raw = json.loads(args.domain_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: domain-research JSON not found: {args.domain_json}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in {args.domain_json}: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: reading {args.domain_json}: {e}", file=sys.stderr)
        return 2

    domain = raw.get("domain_short_name")
    if not domain:
        print("error: domain-research JSON missing 'domain_short_name'", file=sys.stderr)
        return 2

    datasets = raw.get("datasets", [])
    if not isinstance(datasets, list):
        print("error: 'datasets' must be a list", file=sys.stderr)
        return 2

    # ---- Load registry text ----
    try:
        registry_text = registry_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"error: reading registry {registry_path}: {e}", file=sys.stderr)
        return 2

    existing_ids = existing_identifiers(registry_text)

    # ---- Detect collisions, normalize, and collect entries to append ----
    to_append: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []

    for ds in datasets:
        if not isinstance(ds, dict) or "name" not in ds:
            skipped.append({"reason": "malformed", "entry": ds})
            continue
        entry = normalize_entry(ds, domain)
        candidates = {_norm(entry["name"])}
        for a in entry.get("aliases", []) or []:
            candidates.add(_norm(a))
        hit = candidates & existing_ids
        if hit:
            collisions.append(
                {"name": entry["name"], "collides_with": sorted(hit)}
            )
            skipped.append({"reason": "collision", "name": entry["name"], "collides_with": sorted(hit)})
            print(
                f"warn: skipping '{entry['name']}' — alias/name collision with existing: {sorted(hit)}",
                file=sys.stderr,
            )
            continue
        to_append.append(entry)
        # Reserve these identifiers so a duplicate within the same JSON also collides.
        existing_ids |= candidates

    # ---- Render output ----
    if to_append:
        block_lines = [""]
        block_lines.append(
            f"  # -------------------------------------------------------------------------"
        )
        block_lines.append(f"  # Added by domain-init for domain: {domain}")
        block_lines.append(
            f"  # -------------------------------------------------------------------------"
        )
        block_lines.append("")
        rendered = "\n".join(block_lines) + "\n" + "\n".join(
            render_entry(e) for e in to_append
        )
    else:
        rendered = ""

    if args.dry_run:
        if rendered:
            print("--- would append to", registry_path, "---")
            print(rendered)
        else:
            print("--- nothing to append ---")
    else:
        if rendered:
            try:
                # Strip trailing whitespace/newlines, append block, keep one final newline.
                new_text = registry_text.rstrip() + "\n" + rendered
                if not new_text.endswith("\n"):
                    new_text += "\n"
                registry_path.write_text(new_text, encoding="utf-8")
            except OSError as e:
                print(f"error: writing {registry_path}: {e}", file=sys.stderr)
                return 2

    # ---- Emit JSON summary on stdout ----
    summary = {
        "added": len(to_append),
        "skipped": skipped,
        "collisions": collisions,
        "registry_path": str(registry_path),
    }
    print(json.dumps(summary, indent=2))

    return 1 if collisions else 0


if __name__ == "__main__":
    sys.exit(main())
