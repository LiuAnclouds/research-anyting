#!/usr/bin/env python3
"""
ci_validate.py — Aggregate regression runner for the research-anything plugin.

Runs every blocking regression check in sequence, captures pass/fail per
step, and writes an aggregated JSON report. Designed to be wired in as a
pre-commit hook (see ``tests/regression/CI.md``).

Sequence (fail-fast: each step has a 5-min timeout):

  1. ``scripts/migrate_agent_frontmatter.py --dry-run``
     → must report 0 changes (every agent already has current frontmatter).
  2. ``scripts/kb_audit_status_check.py``
     → KB consistency (verification fields + wikilink resolution).
  3. ``scripts/lint_rigor.py <manuscript>``
     → optional; SKIPPED when the fixture path is missing or not provided.
  4. ``tests/regression/p0_smoke.py --no-network``
     → must pass 7/7 injections.
  5. ``tests/regression/audit_loop_sim.py``
     → must pass all 3 scenarios.

Usage:
  python scripts/ci_validate.py [--plugin-root PATH] [--manuscript PATH]
                                [--out PATH]

Exit codes:
  0  all blocking steps green (skipped steps do not count as red)
  1  one or more blocking steps failed
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT_DEFAULT = HERE.parent

STEP_TIMEOUT_SEC = 5 * 60  # 5 minutes per subprocess


def _run(cmd: list[str], cwd: Path) -> dict:
    """Run a subprocess with the standard timeout, capturing stdout/stderr.

    Returns a dict describing the outcome; never raises (caller decides
    pass/fail based on returncode).
    """
    t0 = time.time()
    record = {
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": None,
        "duration_sec": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "timed_out": False,
        "spawn_error": None,
    }
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                              text=True, timeout=STEP_TIMEOUT_SEC,
                              encoding="utf-8", errors="replace")
        record["returncode"] = proc.returncode
        record["stdout_tail"] = _tail(proc.stdout, 4000)
        record["stderr_tail"] = _tail(proc.stderr, 4000)
    except subprocess.TimeoutExpired as e:
        record["timed_out"] = True
        record["returncode"] = 124
        record["stdout_tail"] = _tail(e.stdout or "", 4000)
        record["stderr_tail"] = _tail(e.stderr or "", 4000)
    except FileNotFoundError as e:
        record["spawn_error"] = f"executable not found: {e}"
        record["returncode"] = 127
    except Exception as e:
        record["spawn_error"] = f"{type(e).__name__}: {e}"
        record["returncode"] = 1
    record["duration_sec"] = round(time.time() - t0, 3)
    return record


def _tail(s: str, n: int) -> str:
    if not s:
        return ""
    return s if len(s) <= n else "..." + s[-n:]


# ---------- step definitions ---------------------------------------------

def step_migrate_dry_run(plugin_root: Path) -> dict:
    cmd = [sys.executable,
           str(plugin_root / "scripts" / "migrate_agent_frontmatter.py"),
           "--dry-run",
           "--root", str(plugin_root)]
    run = _run(cmd, plugin_root)
    # Per migrate_agent_frontmatter.main: returns 0 if (apply or n_changed==0).
    # In dry-run, exit 0 means "no changes pending". Exit 1 means changes
    # would be applied → blocking failure for CI.
    ok = run["returncode"] == 0
    return {"name": "migrate_agent_frontmatter --dry-run",
            "ok": ok,
            "blocking": True,
            "skipped": False,
            "run": run,
            "summary": "0 changes pending" if ok else "frontmatter changes pending (run --apply)"}


def step_kb_audit(plugin_root: Path) -> dict:
    cmd = [sys.executable,
           str(plugin_root / "scripts" / "kb_audit_status_check.py"),
           "--kb-root", str(plugin_root / "knowledge-base")]
    run = _run(cmd, plugin_root)
    ok = run["returncode"] == 0
    if run["returncode"] == 2:
        summary = "harness error"
    elif ok:
        summary = "KB clean"
    else:
        summary = "KB consistency issues (see kb_audit_status_report.json)"
    return {"name": "kb_audit_status_check",
            "ok": ok,
            "blocking": True,
            "skipped": False,
            "run": run,
            "summary": summary}


def step_lint_rigor(plugin_root: Path, manuscript: Path | None) -> dict:
    if manuscript is None or not Path(manuscript).is_dir():
        return {"name": "lint_rigor",
                "ok": True,
                "blocking": False,
                "skipped": True,
                "run": None,
                "summary": f"skipped (manuscript path not provided or missing: {manuscript})"}
    cmd = [sys.executable,
           str(plugin_root / "scripts" / "lint_rigor.py"),
           str(manuscript)]
    run = _run(cmd, plugin_root)
    # lint_rigor.py is soft-fail (exit 0 with findings allowed) — only
    # treat returncode != 0 as a hard fail (harness error / crash).
    ok = run["returncode"] == 0
    return {"name": "lint_rigor",
            "ok": ok,
            "blocking": True,
            "skipped": False,
            "run": run,
            "summary": "linted manuscript" if ok else "lint_rigor errored"}


def step_p0_smoke(plugin_root: Path, manuscript: Path | None) -> dict:
    cmd = [sys.executable,
           str(plugin_root / "tests" / "regression" / "p0_smoke.py"),
           "--no-network"]
    if manuscript is not None and Path(manuscript).is_dir():
        cmd += ["--manuscript", str(manuscript)]
    run = _run(cmd, plugin_root)
    ok = run["returncode"] == 0
    if run["returncode"] == 2:
        summary = "harness error (missing fixtures?)"
    elif ok:
        summary = "all expected detections fired"
    else:
        summary = "one or more expected detections missed"
    return {"name": "p0_smoke --no-network",
            "ok": ok,
            "blocking": True,
            "skipped": False,
            "run": run,
            "summary": summary}


def step_audit_loop_sim(plugin_root: Path) -> dict:
    cmd = [sys.executable,
           str(plugin_root / "tests" / "regression" / "audit_loop_sim.py")]
    run = _run(cmd, plugin_root)
    ok = run["returncode"] == 0
    return {"name": "audit_loop_sim",
            "ok": ok,
            "blocking": True,
            "skipped": False,
            "run": run,
            "summary": "3/3 scenarios pass" if ok else "scenario failure (see report)"}


# ---------- driver -------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plugin-root", type=Path, default=PLUGIN_ROOT_DEFAULT,
                    help="research-anything plugin root")
    ap.add_argument("--manuscript", type=Path, default=None,
                    help="Manuscript fixture root (skipped if absent)")
    ap.add_argument("--out", type=Path,
                    default=PLUGIN_ROOT_DEFAULT / "tests" / "regression" / "ci_validate_report.json",
                    help="JSON report destination")
    args = ap.parse_args()

    plugin_root: Path = args.plugin_root.resolve()
    if not plugin_root.is_dir():
        print(f"[ci-validate] ERROR: --plugin-root not a directory: {plugin_root}",
              file=sys.stderr)
        return 1

    steps = []
    # Fail-fast: stop on first blocking failure to keep pre-commit responsive.
    pipeline = [
        ("migrate", lambda: step_migrate_dry_run(plugin_root)),
        ("kb_audit", lambda: step_kb_audit(plugin_root)),
        ("lint_rigor", lambda: step_lint_rigor(plugin_root, args.manuscript)),
        ("p0_smoke", lambda: step_p0_smoke(plugin_root, args.manuscript)),
        ("audit_loop_sim", lambda: step_audit_loop_sim(plugin_root)),
    ]
    aborted_after: str | None = None
    for label, fn in pipeline:
        print(f"\n[ci-validate] >>> {label}")
        result = fn()
        steps.append(result)
        status = ("SKIP" if result["skipped"]
                  else ("PASS" if result["ok"] else "FAIL"))
        dur = (result["run"] or {}).get("duration_sec", 0.0)
        print(f"[ci-validate] <<< {label}: {status} ({dur}s) — {result['summary']}")
        if result["blocking"] and not result["ok"]:
            aborted_after = label
            break

    # Skipped tail steps (when fail-fast aborts) are recorded as not-run so
    # the summary table is the full pipeline regardless of where we stopped.
    for label, _ in pipeline:
        prefix = label_map(label)
        if not any(s["name"].startswith(prefix) for s in steps):
            steps.append({"name": prefix, "ok": False, "blocking": True,
                          "skipped": True, "run": None,
                          "summary": "not run (fail-fast aborted)"})

    n_pass    = sum(1 for s in steps if s["ok"] and not s["skipped"])
    n_fail    = sum(1 for s in steps if (not s["ok"]) and not s["skipped"])
    n_skipped = sum(1 for s in steps if s["skipped"])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plugin_root": str(plugin_root),
        "manuscript": str(args.manuscript) if args.manuscript else None,
        "aborted_after": aborted_after,
        "n_pass": n_pass,
        "n_fail": n_fail,
        "n_skipped": n_skipped,
        "steps": steps,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    # Summary table
    print("\n" + "=" * 68)
    print(f"{'STEP':<36} {'STATUS':<6} {'DURATION':<10} SUMMARY")
    print("-" * 68)
    for s in steps:
        status = ("SKIP" if s["skipped"]
                  else ("PASS" if s["ok"] else "FAIL"))
        dur = ((s["run"] or {}).get("duration_sec") or 0.0) if s["run"] else 0.0
        name = s["name"][:35]
        print(f"{name:<36} {status:<6} {dur:<10.2f} {s['summary']}")
    print("=" * 68)
    print(f"pass={n_pass} fail={n_fail} skipped={n_skipped} "
          f"report={args.out}")

    return 0 if n_fail == 0 else 1


def label_map(label: str) -> str:
    """Map our internal short label to the prefix used in step names."""
    return {
        "migrate":        "migrate_agent_frontmatter",
        "kb_audit":       "kb_audit_status_check",
        "lint_rigor":     "lint_rigor",
        "p0_smoke":       "p0_smoke",
        "audit_loop_sim": "audit_loop_sim",
    }.get(label, label)


if __name__ == "__main__":
    sys.exit(main())
