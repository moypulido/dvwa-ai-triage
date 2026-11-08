# dvwa-ai-triage

[English](README.md) | **Español**

> ⚠️ **ESTO ES UNA DEMO.** Este código es **intencionalmente vulnerable**.
> **Nunca se despliega**: ni en producción, ni en staging, ni en ningún servidor
> accesible desde internet. Solo se ejecuta en local, dentro de Docker, con fines
> educativos y para probar el triage de vulnerabilidades asistido por IA.

## Qué es

Una versión recortada de [DVWA (Damn Vulnerable Web Application)](https://github.com/digininja/DVWA)
que sirve como objetivo controlado para practicar el triage de hallazgos de
seguridad con herramientas de IA.

## Qué cambió respecto al original

- **Repositorio nuevo, no fork**: se clonó `digininja/DVWA`, se eliminó su
  historial `.git` y se subió como repositorio independiente.
- **Solo 4 módulos vulnerables** en `vulnerabilities/`:
  - `sqli` – SQL Injection
  - `exec` – Command Injection
  - `upload` – File Upload
  - `bac` – Broken Access Control

  El resto de módulos (brute, csrf, fi, captcha, xss_*, csp, javascript, api,
  etc.) se eliminaron. Se conservan los archivos auxiliares compartidos
  (`view_source.php`, `view_help.php`, `view_source_all.php`, `help.css`,
  `help.js`) porque los módulos dependen de ellos.
- **Menú ajustado**: `dvwa/includes/dvwaPage.inc.php` solo muestra los 4
  módulos conservados (y habilita `bac`, que en el original estaba comentado).
- **Eliminados**: los README traducidos, `CHANGELOG.md`, `SECURITY.md`,
  `security.txt`, `docs/`, `tests/` y los workflows y plantillas de `.github/`.
- **Se conservan**: `dvwa/includes/`, `Dockerfile`, `compose.yml` y
  `COPYING.txt`.
- **Nuevo**: este README (en inglés y español) y el archivo de alcance
  `.security/scope.txt`.

## Alcance

Las rutas aprobadas para análisis están en [`.security/scope.txt`](.security/scope.txt).
Cualquier ruta que no aparezca ahí queda fuera de alcance.

## Ejecutar en local

```bash
docker compose up -d
```

Abre <http://localhost:4280>, entra con `admin` / `password` y pulsa
**Create / Reset Database**. Para apagarlo:

```bash
docker compose down
```

## Créditos y licencia

Basado en **DVWA – Damn Vulnerable Web Application**, de Robin Wood
([@digininja](https://github.com/digininja)) y colaboradores:
<https://github.com/digininja/DVWA>.

Como el original, este proyecto se distribuye bajo la licencia
**GNU General Public License v3.0 (GPL-3.0)**. Consulta [`COPYING.txt`](COPYING.txt).
