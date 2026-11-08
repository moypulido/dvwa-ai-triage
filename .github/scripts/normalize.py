#!/usr/bin/env python3
"""Normalize SARIF reports from gitleaks, semgrep and trivy into one JSON.

This is the Phase 2 -> Phase 3 contract. It reads the SARIF files written by
the scan steps and emits scan/findings.json with:
  - PR metadata (repo, PR number, commit range, run URL, timestamp, pattern,
    evidence ceiling),
  - stats (raw records shown, unique findings, duplicates, and per tool /
    category / severity breakdowns over unique findings),
  - one normalized record per unique finding: id, tool, category, rule,
    severity, file, line, module, DVWA level, in_scope, message, a +/-2 line
    snippet (capped) and status "candidate"; plus occurrences = how many raw
    records collapsed into it.
Secrets (gitleaks) carry no snippet.

Stable ID (pendiente #4): hashed from tool+rule+file, the tool-marked lines
with whitespace normalized, and an ordinal that separates identical content at
different places in the same file (e.g. low.php lines 10 and 31). It does NOT
use the +/-2 snippet or the absolute line number, so adding a comment above a
finding does not change its ID and a suppressed finding stays suppressed.

Pure stdlib; no third-party imports. Reads tool output and repo files as data
only. Re-check the schema against the plan's section 6 before relying on it.
"""

import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

SCAN_DIR = "scan"
OUT_PATH = os.path.join(SCAN_DIR, "findings.json")
SCOPE_PATH = os.path.join(".security", "scope.txt")
SCHEMA_VERSION = "0.1"
SNIPPET_MAX = 600

# Map each SARIF file to the tool and category that produced it. Driver names
# vary between versions, so the labels are fixed here, not read from the SARIF.
SARIF_SOURCES = {
    "gitleaks": {"path": os.path.join(SCAN_DIR, "gitleaks.sarif"), "category": "secrets"},
    "semgrep": {"path": os.path.join(SCAN_DIR, "semgrep.sarif"), "category": "sast"},
    "trivy": {"path": os.path.join(SCAN_DIR, "trivy.sarif"), "category": "iac"},
}

DVWA_LEVELS = {"low", "medium", "high", "impossible"}
MODULE_RE = re.compile(r"^vulnerabilities/([^/]+)/")
LEVEL_RE = re.compile(r"^vulnerabilities/[^/]+/source/([a-z]+)\.php$")
WS_RE = re.compile(r"\s+")


def load_sarif(path):
    """Return the parsed SARIF dict, or an empty-runs stub if the file is
    missing. A present-but-malformed file raises (a broken tool must be seen)."""
    if not os.path.exists(path):
        return {"runs": []}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_scope():
    """Return the scope entries (comments/blanks stripped)."""
    entries = []
    if not os.path.exists(SCOPE_PATH):
        return entries
    with open(SCOPE_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.append(line)
    return entries


def in_scope(path, scope):
    if not path:
        return False
    for entry in scope:
        if entry.endswith("/"):
            if path.startswith(entry):
                return True
        elif path == entry:
            return True
    return False


def module_of(path):
    m = MODULE_RE.match(path or "")
    return m.group(1) if m else None


def dvwa_level_of(path):
    m = LEVEL_RE.match(path or "")
    if m and m.group(1) in DVWA_LEVELS:
        return m.group(1)
    return None


def read_lines(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def marked_text(lines, start_line, end_line):
    """Normalized text of the tool-marked region (used for the stable ID)."""
    if not lines or not start_line:
        return None
    end_line = end_line or start_line
    if start_line < 1 or start_line > len(lines):
        return None
    chunk = lines[start_line - 1:min(len(lines), end_line)]
    return WS_RE.sub(" ", " ".join(chunk)).strip() or None


def display_snippet(lines, line, radius=2):
    """+/-radius lines around `line`, capped at SNIPPET_MAX chars."""
    if not lines or not line or line < 1 or line > len(lines):
        return None
    start = max(0, line - 1 - radius)
    end = min(len(lines), line + radius)
    text = "\n".join(lines[start:end])
    if len(text) > SNIPPET_MAX:
        text = text[:SNIPPET_MAX - 1] + "…"
    return text


def stable_id(tool, rule, path, anchor, ordinal):
    raw = "\x1f".join([tool, rule or "", path or "", anchor or "", str(ordinal)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def severity_of(result):
    props = result.get("properties") or {}
    for key in ("security-severity", "Severity", "severity"):
        val = props.get(key)
        if val not in (None, ""):
            return str(val)
    return result.get("level") or "unknown"


def message_of(result):
    return (result.get("message") or {}).get("text")


def first_location(result):
    locs = result.get("locations") or []
    if not locs:
        return (None, None, None, None)
    phys = locs[0].get("physicalLocation", {})
    uri = (phys.get("artifactLocation") or {}).get("uri")
    region = phys.get("region") or {}
    inline = (region.get("snippet") or {}).get("text")
    return (uri, region.get("startLine"), region.get("endLine"), inline)


def collect_raw(scope):
    """Read every SARIF result into a flat list of raw records."""
    raw = []
    file_cache = {}
    for tool, src in SARIF_SOURCES.items():
        sarif = load_sarif(src["path"])
        category = src["category"]
        for run in sarif.get("runs", []):
            for result in run.get("results", []):
                uri, start, end, inline = first_location(result)
                if uri not in file_cache:
                    file_cache[uri] = read_lines(uri)
                lines = file_cache[uri]

                if tool == "gitleaks":
                    # Never put secret material (even hashed) into the ID or
                    # the output; a constant anchor + ordinal separates secrets.
                    anchor = "secret"
                    snippet = None
                else:
                    anchor = marked_text(lines, start, end) \
                        or (WS_RE.sub(" ", inline).strip() if inline else None) \
                        or ("L%s" % (start if start else "?"))
                    snippet = display_snippet(lines, start) or (
                        inline[:SNIPPET_MAX] if inline else None)

                raw.append({
                    "tool": tool,
                    "category": category,
                    "rule": result.get("ruleId"),
                    "severity": severity_of(result),
                    "file": uri,
                    "line": start,
                    "module": module_of(uri),
                    "dvwa_level": dvwa_level_of(uri),
                    "in_scope": in_scope(uri, scope),
                    "message": message_of(result),
                    "snippet": snippet,
                    "status": "candidate",
                    "_group": (tool, result.get("ruleId"), uri, anchor),
                })
    return raw


def assign_ordinals(raw):
    """Ordinal per distinct start line within an identical-content group, so
    identical content at different places gets distinct (but stable) IDs."""
    group_lines = defaultdict(set)
    for rec in raw:
        group_lines[rec["_group"]].add(rec["line"])
    line_ordinal = {}
    for group, lines in group_lines.items():
        ordered = sorted(ln for ln in lines if ln is not None)
        for idx, ln in enumerate(ordered):
            line_ordinal[(group, ln)] = idx
    for rec in raw:
        rec["_ordinal"] = line_ordinal.get((rec["_group"], rec["line"]), 0)


def normalize():
    scope = load_scope()
    raw = collect_raw(scope)
    assign_ordinals(raw)

    unique = {}
    by_tool = defaultdict(int)
    by_category = defaultdict(int)
    by_severity = defaultdict(int)

    for rec in raw:
        tool, rule, uri, anchor = rec["_group"]
        fid = stable_id(tool, rule, uri, anchor, rec["_ordinal"])
        if fid in unique:
            unique[fid]["occurrences"] += 1
            continue
        public = {k: v for k, v in rec.items() if not k.startswith("_")}
        public = {"id": fid, **public, "occurrences": 1}
        unique[fid] = public
        by_tool[tool] += 1
        by_category[rec["category"]] += 1
        by_severity[str(rec["severity"])] += 1

    findings = list(unique.values())
    report = {
        "schema_version": SCHEMA_VERSION,
        "pr": {
            "repo": os.environ.get("REPO"),
            "number": _int_or_none(os.environ.get("PR_NUMBER")),
            "base_sha": os.environ.get("BASE_SHA"),
            "head_sha": os.environ.get("HEAD_SHA"),
            "merge_base": os.environ.get("MERGE_BASE"),
            "run_url": _run_url(),
            "generated_at": datetime.now(timezone.utc)
                .replace(microsecond=0).isoformat(),
            "pattern": "review-code-changes",
            "evidence_ceiling": "static-only, no runtime",
        },
        "stats": {
            "raw_records": len(raw),
            "unique_findings": len(findings),
            "duplicates": len(raw) - len(findings),
            "by_tool": dict(by_tool),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
        },
        "findings": findings,
    }

    os.makedirs(SCAN_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return report


def _run_url():
    server = os.environ.get("SERVER_URL")
    repo = os.environ.get("REPO")
    run_id = os.environ.get("RUN_ID")
    if server and repo and run_id:
        return "%s/%s/actions/runs/%s" % (server, repo, run_id)
    return None


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    rep = normalize()
    print("Normalized %d raw records into %d unique findings (%d duplicates)."
          % (rep["stats"]["raw_records"], rep["stats"]["unique_findings"],
             rep["stats"]["duplicates"]))
    sys.exit(0)
