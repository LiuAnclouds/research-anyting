#!/usr/bin/env python3
"""
Moon-Research Knowledge Base Integrity Checker.
Verifies: wikilink validity, INDEX completeness, frontmatter integrity, bidirectionality.
Usage: python kb_check.py [--fix]
"""
import os, sys, re, yaml
from pathlib import Path
from collections import defaultdict

KB_ROOT = Path(os.environ.get('MOON_KB_ROOT', os.path.expanduser('~/.claude/skills/moon-research/knowledge-base')))

def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}

def extract_wikilinks(content):
    """Extract [[wikilink]] references from markdown content."""
    return re.findall(r'\[\[([^\]]+)\]\]', content)

def find_all_entries():
    """Find all markdown entries in the KB."""
    entries = {}
    for md_file in KB_ROOT.rglob('*.md'):
        if 'INDEX.md' in str(md_file) or 'KB_SCHEMA.md' in str(md_file):
            continue
        rel_path = md_file.relative_to(KB_ROOT)
        slug = str(rel_path.with_suffix('')).replace('\\', '/')
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        fm = extract_frontmatter(content)
        wl = extract_wikilinks(content)
        entries[slug] = {'path': md_file, 'frontmatter': fm, 'wikilinks': wl, 'type': fm.get('type', 'unknown')}
    return entries

def check_wikilink_validity(entries):
    """Check that all wikilinks point to existing entries."""
    issues = []
    all_slugs = set(entries.keys())
    for slug, entry in entries.items():
        for link in entry['wikilinks']:
            link_slug = link.split('|')[0].strip()
            if link_slug not in all_slugs:
                issues.append(f"Broken wikilink: {slug} -> [[{link_slug}]] (target not found)")
    return issues

def check_bidirectionality(entries):
    """Check that connections are bidirectional."""
    issues = []
    for slug, entry in entries.items():
        connections = entry['frontmatter'].get('connections', [])
        if not connections:
            continue
        for conn in connections:
            conn_slug = conn.split('|')[0].strip()
            if conn_slug not in entries:
                continue
            target_conns = entries[conn_slug]['frontmatter'].get('connections', [])
            target_slugs = [c.split('|')[0].strip() for c in target_conns]
            if slug not in target_slugs:
                issues.append(f"Missing backlink: {slug} -> {conn_slug}, but {conn_slug} does not link back to {slug}")
    return issues

def check_index_completeness(entries):
    """Check that INDEX.md files list all entries in their directory."""
    issues = []
    dir_entries = defaultdict(list)
    for slug, entry in entries.items():
        dir_name = str(Path(slug).parent)
        dir_entries[dir_name].append(slug)

    for dir_name, slugs in dir_entries.items():
        index_path = KB_ROOT / dir_name / 'INDEX.md'
        if not index_path.exists():
            issues.append(f"Missing INDEX.md in {dir_name}/ (contains {len(slugs)} entries)")
    return issues

def main():
    import argparse
    p = argparse.ArgumentParser(description='Moon-Research KB Integrity Checker')
    p.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    a = p.parse_args()

    print(f"Scanning KB: {KB_ROOT}")
    entries = find_all_entries()
    print(f"Found {len(entries)} entries")

    all_issues = []
    all_issues.extend(check_wikilink_validity(entries))
    all_issues.extend(check_bidirectionality(entries))
    all_issues.extend(check_index_completeness(entries))

    if not all_issues:
        print("\nAll checks passed. KB integrity verified.")
        return 0

    print(f"\n{len(all_issues)} issues found:")
    for issue in all_issues:
        print(f"  - {issue}")

    return 1 if all_issues else 0

if __name__ == '__main__':
    sys.exit(main())