"""
photon_issue_isolator.py  (v2 — git-status-driven, no base repo needed)

Isolates SonarQube issues to just your photon transport work, using git
itself to figure out what changed — no second clone, no manual file list.

How it works:
  1. Runs `git status --porcelain` in your repo (optionally scoped to
     specific paths) to find:
       - MODIFIED files (existing neutron files you edited to add photon
         hooks) -> these get LINE-LEVEL scoping via `git diff` against HEAD.
       - NEW / UNTRACKED files (files that don't exist in the base repo at
         all, e.g. the standalone photon_*.py files) -> EVERY issue in these
         counts, no line filtering needed.
  2. Pulls all open issues for your SonarQube project via the read-only
     issues search API.
  3. For modified files: keeps only issues whose line falls inside a
     changed hunk (from `git diff`).
     For new files: keeps every issue in that file automatically.
  4. Prints and saves a summary: counts by severity/type, restricted to
     your photon-touched code.

SAFETY: Read-only throughout. `git status` and `git diff` do not modify
anything. All SonarQube calls are GET requests. The only file written is
the report at --out.

Requirements:
    pip install requests

Usage (scoped to specific paths, recommended so you skip .sonar/, data/, etc.):
    python photon_issue_isolator.py \
        --repo-dir "C:\\Projects\\MCDC" \
        --paths mcdc/mcdc_get mcdc/mcdc_set mcdc/object_ mcdc/transport/physics/photon test/unit/transport/physics validate_energy_deposition.py validate_fluorescence.py validate_photon_xs.py visualize_output.py \
        --sonar-url http://localhost:9000 \
        --sonar-token sqp_xxx \
        --project-key mcdc_photon_transport \
        --out photon_issue_report.txt

If you omit --paths, it scans git status for the whole repo (noisier —
you'll want to exclude things like .sonar/ yourself afterward).
"""

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

import requests


HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


# ---------------------------------------------------------------------------
# git status parsing
# ---------------------------------------------------------------------------

def run_git(repo_dir: str, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", repo_dir] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def discover_changed_files(repo_dir: str, paths: list[str]) -> tuple[list[str], list[str]]:
    """
    Returns (modified_files, new_files), both as repo-relative paths using
    forward slashes. Directories in `paths` are expanded to individual files
    by walking untracked directories that git reports as a whole.
    """
    status_args = ["status", "--porcelain"]
    if paths:
        status_args += ["--"] + paths

    output = run_git(repo_dir, status_args)

    modified: list[str] = []
    new: list[str] = []

    for line in output.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        rel_path = line[3:].strip()
        if rel_path.startswith('"') and rel_path.endswith('"'):
            rel_path = rel_path[1:-1]

        if code.strip() == "M":
            modified.append(rel_path)
        elif code.strip() == "??":
            full_path = os.path.join(repo_dir, rel_path)
            if os.path.isdir(full_path):
                for root, _, files in os.walk(full_path):
                    for fname in files:
                        if fname.endswith(".py"):
                            abs_f = os.path.join(root, fname)
                            rel_f = os.path.relpath(abs_f, repo_dir).replace("\\", "/")
                            new.append(rel_f)
            else:
                if rel_path.endswith(".py"):
                    new.append(rel_path)

    return modified, new


# ---------------------------------------------------------------------------
# git diff parsing (modified files only)
# ---------------------------------------------------------------------------

def get_changed_ranges(repo_dir: str, rel_path: str) -> list[tuple[int, int]]:
    diff_output = run_git(repo_dir, ["diff", "--unified=0", "--", rel_path])

    ranges: list[tuple[int, int]] = []
    for line in diff_output.splitlines():
        match = HUNK_HEADER_RE.match(line)
        if not match:
            continue
        plus_start = int(match.group(3))
        plus_count = int(match.group(4)) if match.group(4) is not None else 1
        if plus_count == 0:
            continue
        ranges.append((plus_start, plus_start + plus_count - 1))
    return ranges


def line_in_ranges(line_number: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line_number <= end for start, end in ranges)


# ---------------------------------------------------------------------------
# SonarQube API
# ---------------------------------------------------------------------------

@dataclass
class SonarIssue:
    key: str
    rule: str
    severity: str
    issue_type: str
    component: str
    line: Optional[int]
    message: str = ""


def fetch_all_issues(sonar_url: str, token: str, project_key: str) -> list[SonarIssue]:
    issues: list[SonarIssue] = []
    page = 1
    page_size = 500

    while True:
        resp = requests.get(
            f"{sonar_url}/api/issues/search",
            auth=(token, ""),
            params={"componentKeys": project_key, "ps": page_size, "p": page},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        for raw in data.get("issues", []):
            issues.append(
                SonarIssue(
                    key=raw.get("key", ""),
                    rule=raw.get("rule", ""),
                    severity=raw.get("severity", "UNKNOWN"),
                    issue_type=raw.get("type", "UNKNOWN"),
                    component=raw.get("component", ""),
                    line=raw.get("line"),
                    message=raw.get("message", ""),
                )
            )

        total = data.get("paging", {}).get("total", 0)
        if page * page_size >= total:
            break
        page += 1

    return issues


def component_matches_file(component: str, relative_file: str, project_key: str) -> bool:
    prefix = f"{project_key}:"
    if not component.startswith(prefix):
        return False
    comp_path = component[len(prefix):].replace("\\", "/")
    target_path = relative_file.replace("\\", "/")
    return comp_path == target_path or comp_path.endswith("/" + target_path)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-dir", required=True, help="Path to your git repo, e.g. C:\\Projects\\MCDC")
    parser.add_argument("--paths", nargs="*", default=[], help="Optional: restrict git status to these paths (files or dirs)")
    parser.add_argument("--sonar-url", required=True)
    parser.add_argument("--sonar-token", required=True)
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--out", default="photon_issue_report.txt")
    args = parser.parse_args()

    print("Discovering modified and new files via git status...")
    modified_files, new_files = discover_changed_files(args.repo_dir, args.paths)
    print(f"Modified files ({len(modified_files)}): {modified_files}")
    print(f"New/untracked files ({len(new_files)}): {new_files}")

    print("\nComputing changed line ranges for modified files...")
    changed_ranges_by_file: dict[str, list[tuple[int, int]]] = {}
    for rel_path in modified_files:
        ranges = get_changed_ranges(args.repo_dir, rel_path)
        changed_ranges_by_file[rel_path] = ranges
        print(f"  {rel_path}: {ranges}")

    print("\nFetching issues from SonarQube...")
    all_issues = fetch_all_issues(args.sonar_url, args.sonar_token, args.project_key)
    print(f"Total issues fetched (whole project): {len(all_issues)}")

    filtered: list[SonarIssue] = []

    for issue in all_issues:
        matched_new = False
        for rel_path in new_files:
            if component_matches_file(issue.component, rel_path, args.project_key):
                filtered.append(issue)
                matched_new = True
                break
        if matched_new:
            continue

        if issue.line is None:
            continue
        for rel_path, ranges in changed_ranges_by_file.items():
            if component_matches_file(issue.component, rel_path, args.project_key):
                if line_in_ranges(issue.line, ranges):
                    filtered.append(issue)
                break

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for issue in filtered:
        by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
        by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1

    lines_out = []
    lines_out.append("=" * 70)
    lines_out.append("Photon-transport-scoped SonarQube issue report")
    lines_out.append("=" * 70)
    lines_out.append(f"Modified files scanned: {modified_files}")
    lines_out.append(f"New files scanned: {new_files}")
    lines_out.append(f"Total issues in project (all code): {len(all_issues)}")
    lines_out.append(f"Issues attributable to photon work: {len(filtered)}")
    lines_out.append("")
    lines_out.append("-- By severity --")
    for sev, count in sorted(by_severity.items(), key=lambda x: -x[1]):
        lines_out.append(f"  {sev}: {count}")
    lines_out.append("")
    lines_out.append("-- By type --")
    for typ, count in sorted(by_type.items(), key=lambda x: -x[1]):
        lines_out.append(f"  {typ}: {count}")
    lines_out.append("")
    lines_out.append("-- Full issue list --")
    for issue in filtered:
        lines_out.append(
            f"  [{issue.severity}] [{issue.issue_type}] {issue.component}:{issue.line} "
            f"({issue.rule}) - {issue.message}"
        )

    report = "\n".join(lines_out)
    print("\n" + report)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport written to: {args.out}")


if __name__ == "__main__":
    main()
