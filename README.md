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

- **New repository, not a fork**: `digininja/DVWA` was cloned at upstream
  commit [`a1978a2`](https://github.com/digininja/DVWA/commit/a1978a2), its
  `.git` history was removed and the code was pushed as an independent
  repository.
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
- **Dockerfile**: removed the `vulnerabilities/api` Composer install step, which
  no longer exists after trimming the modules and broke the build.
- **compose.yml**: set `pull_policy: build` and `image: dvwa-ai-triage:local`
  so the container is built from this trimmed source instead of pulling the
  official DVWA image (which ships every module). The published port stays
  bound to `127.0.0.1` only.
- **Removed**: translated READMEs, `CHANGELOG.md`, `SECURITY.md`,
  `security.txt`, `docs/`, `tests/`, the `.github/` workflows and templates,
  and `external/` (only used by the removed `captcha` module).
- **Kept** (needed to run the app and the 4 modules):
  - `dvwa/` (core includes, CSS, JS, images)
  - `config/`, `database/`, `hackable/`
  - `vulnerabilities/` shared helpers: `view_source.php`, `view_help.php`,
    `view_source_all.php`, `help.css`, `help.js`
  - top-level pages: `index.php`, `login.php`, `logout.php`, `setup.php`,
    `security.php`, `instructions.php`, `about.php`, `phpinfo.php`
  - `Dockerfile`, `compose.yml`, `php.ini`, `COPYING.txt`, `favicon.ico`,
    `robots.txt`
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
