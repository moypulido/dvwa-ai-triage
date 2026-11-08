# dvwa-ai-triage

**English** | [Español](README.es.md)

> ⚠️ **THIS IS A DEMO.** This code is **intentionally vulnerable**.
> **It is never deployed**: not to production, not to staging, not to any
> internet-reachable server. It only runs locally, inside Docker, for
> educational purposes and to test AI-assisted vulnerability triage.

## What it is

A trimmed-down version of [DVWA (Damn Vulnerable Web Application)](https://github.com/digininja/DVWA)
used as a controlled target to practice triaging security findings with AI tools.

## What changed from the original

- **New repository, not a fork**: `digininja/DVWA` was cloned, its `.git`
  history was removed and the code was pushed as an independent repository.
- **Only 4 vulnerable modules** in `vulnerabilities/`:
  - `sqli` – SQL Injection
  - `exec` – Command Injection
  - `upload` – File Upload
  - `bac` – Broken Access Control

  All other modules (brute, csrf, fi, captcha, xss_*, csp, javascript, api,
  etc.) were removed. The shared helper files (`view_source.php`,
  `view_help.php`, `view_source_all.php`, `help.css`, `help.js`) are kept
  because the modules depend on them.
- **Menu adjusted**: `dvwa/includes/dvwaPage.inc.php` only lists the 4 kept
  modules (and enables `bac`, which was commented out in the original).
- **Removed**: translated READMEs, `CHANGELOG.md`, `SECURITY.md`,
  `security.txt`, `docs/`, `tests/` and the `.github/` workflows and templates.
- **Kept**: `dvwa/includes/`, `Dockerfile`, `compose.yml` and `COPYING.txt`.
- **Added**: this README (in English and Spanish) and the scope file `.security/scope.txt`.

## Scope

The paths approved for analysis are listed in [`.security/scope.txt`](.security/scope.txt).
Anything not listed there is out of scope.

## Running locally

```bash
docker compose up -d
```

Open <http://localhost:4280>, log in with `admin` / `password` and click
**Create / Reset Database**. To stop it:

```bash
docker compose down
```

## Credits and license

Based on **DVWA – Damn Vulnerable Web Application** by Robin Wood
([@digininja](https://github.com/digininja)) and contributors:
<https://github.com/digininja/DVWA>.

Like the original, this project is licensed under the
**GNU General Public License v3.0 (GPL-3.0)**. See [`COPYING.txt`](COPYING.txt).
