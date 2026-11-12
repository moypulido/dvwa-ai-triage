# n8n workflows

Sanitized exports of the three workflows (built on n8n 2.46.6). Hosts, ids,
addresses and names are replaced by placeholders, and no credential is included.

| File | What it does | Trigger |
|---|---|---|
| `flow-1-intake.json` | Receives the scan, deduplicates, asks the AI, stores the rows, sends the triage email with signed links | Webhook called by GitHub Actions |
| `flow-2-decision.json` | Verifies the signed link, shows the decision page, writes the audit log and the decision | Form opened from the email |
| `flow-3-metrics.json` | Computes the metrics, emails the readout, publishes `metrics.json` to `gh-pages` | Manual |

## Placeholders to replace

| Placeholder | Where | Replace with |
|---|---|---|
| `YOUR_SHEET_ID` | Every Google Sheets node, and the record links in the emails | The id of your Google Sheet |
| `YOUR_N8N_HOST` | `build email` (flow 1), `test link url` (flow 2) | The public host of your n8n |
| `YOUR_WEBHOOK_PATH` | `Webhook` (flow 1) | Any path; the full URL goes in a GitHub Actions secret |
| `sender@example.com`, `reviewer@example.com` | The two email nodes | Your addresses |

## Credentials to create

| Name in the export | n8n credential type | Used for |
|---|---|---|
| `X-Scan-Token-gitHub` | Header Auth | The token GitHub Actions sends with each scan |
| `Google Service Account account` | Google Service Account | Reading and writing the Sheet |
| `gemini-api` | Google Gemini (PaLM) API | Primary AI |
| `Groq account` | Groq | Fallback AI |
| `decision-links` | Crypto (HMAC secret) | Signing and verifying decision links |
| `SMTP account` | SMTP | Emails |
| `github-pages-metrics` | GitHub API | Fine-grained token: this repository only, contents read and write |

## Google Sheet

One spreadsheet with these tabs and header rows. Every write uses raw cell format.

- **findings**: `id, status, first_seen_at, last_seen_at, first_pr, last_pr, seen_count, origin, group_key, tool, category, rule, severity, severity_source, file, line, module, dvwa_level, in_scope, message, snippet, ai_provider, ai_status, ai_severity, ai_source_fact, ai_inference, ai_proof_gaps, ai_reason, disposition, final_severity, reason, reviewer, decided_at, time_to_decision_h`
- **occurrences**: `seen_at, run_id, pr, finding_id, line, introduced_by_pr, occurrences`
- **runs**: `received_at, run_id, run_url, repo, pr, head_sha, merge_base, schema_version, raw_records, unique_findings, duplicates, new_findings, known_findings, ai_failures, email_sent`
- **decisions_log**: `logged_at, finding_id, pr, previous_status, new_status, disposition, final_severity, reason, reviewer, source` (append-only)

## Notes

- Flow 1 and flow 2 must be published to receive production traffic; flow 3 runs by hand.
- `Mint test link` and `Reopen findings` in flow 2 are manual helpers, not part of the form path.
- The injection patterns in `finalize AI` are one layer of several. Publishing them
  does not weaken the design: the human decision is the last defence.
