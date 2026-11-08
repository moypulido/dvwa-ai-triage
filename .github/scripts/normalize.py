#!/usr/bin/env python3
"""Normalize SARIF reports from gitleaks, semgrep and trivy into one JSON.

This is the Phase 2 -> Phase 3 contract. It reads the SARIF files written by
the scan steps and emits scan/findings.json with:
  - PR metadata (from env),
  - stats (raw records shown vs unique findings, plus per-tool counts),
  - one normalized record per finding: tool, rule, file, line, module,
    DVWA level, a +/-2 line snippet and status "candidate".
Secrets (gitleaks) carry no snippet.

Pure stdlib; no third-party imports. Reads tool output and repo files as data
only. Re-check the schema against the plan's section 6 before relying on it.
"""

import hashlib
import json
import os
import re
import sys

SCAN_DIR = "scan"
OUT_PATH = os.path.join(SCAN_DIR, "findings.json")
SCHEMA_VERSION = "0.1"

# Map each SARIF file to the tool that produced it. Driver names vary between
# versions, so the tool label is fixed here rather than read from the SARIF.
SARIF_FILES = {
    "gitleaks": os.path.join(SCAN_DIR, "gitleaks.sarif"),
    "semgrep": os.path.join(SCAN_DIR, "semgrep.sarif"),
    "trivy": os.path.join(SCAN_DIR, "trivy.sarif"),
}

DVWA_LEVELS = {"low", "medium", "high", "impossible"}
MODULE_RE = re.compile(r"^vulnerabilities/([^/]+)/")
LEVEL_RE = re.compile(r"^vulnerabilities/[^/]+/source/([a-z]+)\.php$")


def load_sarif(path):
    """Return the parsed SARIF dict, or an empty-runs stub if the file is
    missing. A present-but-malformed file raises (a broken tool must be seen)."""
    if not os.path.exists(path):
        return {"runs": []}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def module_of(path):
    m = MODULE_RE.match(path or "")
    return m.group(1) if m else None


def dvwa_level_of(path):
    m = LEVEL_RE.match(path or "")
    if m and m.group(1) in DVWA_LEVELS:
        return m.group(1)
    return None


def read_snippet(path, line, radius=2):
    """Return the +/-radius lines around `line` from the working-tree file, or
    None if unavailable. Snippets are evidence, read as data only."""
    if not path or not line or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    if line < 1 or line > len(lines):
        return None
    start = max(0, line - 1 - radius)
    end = min(len(lines), line + radius)
    return "\n".join(lines[start:end])


def stable_id(tool, rule, path, anchor):
    """Deterministic ID (pendiente #4). Built from tool+rule+file plus a content
    anchor (the snippet when available) so it survives line shifts; falls back
    to the line number when there is no snippet (e.g. redacted secrets)."""
    raw = "\x1f".join([tool, rule or "", path or "", anchor or ""])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def iter_results(sarif):
    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            yield result


def first_location(result):
    locs = result.get("locations") or []
    if not locs:
        return (None, None, None)
    phys = locs[0].get("physicalLocation", {})
    uri = (phys.get("artifactLocation") or {}).get("uri")
    region = phys.get("region") or {}
    start_line = region.get("startLine")
    inline_snippet = (region.get("snippet") or {}).get("text")
    return (uri, start_line, inline_snippet)


def normalize():
    findings = []
    by_tool = {}
    raw_records = 0

    for tool, path in SARIF_FILES.items():
        sarif = load_sarif(path)
        count = 0
        for result in iter_results(sarif):
            count += 1
            rule = result.get("ruleId")
            file_uri, line, inline = first_location(result)
            module = module_of(file_uri)
            level = dvwa_level_of(file_uri)

            if tool == "gitleaks":
                snippet = None  # secrets never carry a snippet
                anchor = "L%s" % (line if line else "?")
            else:
                snippet = read_snippet(file_uri, line) or inline
                anchor = snippet or ("L%s" % (line if line else "?"))

            findings.append({
                "id": stable_id(tool, rule, file_uri, anchor),
                "tool": tool,
                "rule": rule,
                "file": file_uri,
                "line": line,
                "module": module,
                "dvwa_level": level,
                "snippet": snippet,
                "status": "candidate",
            })
        by_tool[tool] = count
        raw_records += count

    # Deduplicate by stable ID (same finding reported more than once).
    unique = {}
    for f in findings:
        unique.setdefault(f["id"], f)
    unique_findings = list(unique.values())

    report = {
        "schema_version": SCHEMA_VERSION,
        "pr": {
            "repo": os.environ.get("REPO"),
            "number": _int_or_none(os.environ.get("PR_NUMBER")),
            "base_sha": os.environ.get("BASE_SHA"),
            "head_sha": os.environ.get("HEAD_SHA"),
            "merge_base": os.environ.get("MERGE_BASE"),
        },
        "stats": {
            "raw_records": raw_records,
            "unique_findings": len(unique_findings),
            "by_tool": by_tool,
        },
        "findings": unique_findings,
    }

    os.makedirs(SCAN_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return report


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    rep = normalize()
    print("Normalized %d raw records into %d unique findings."
          % (rep["stats"]["raw_records"], rep["stats"]["unique_findings"]))
    sys.exit(0)
