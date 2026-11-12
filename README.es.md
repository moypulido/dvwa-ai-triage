# dvwa-ai-triage

[English](README.md) | **Español**

> ⚠️ **ESTO ES UNA DEMO.** Este código es **intencionalmente vulnerable**.
> **Nunca se despliega**: ni en producción, ni en staging, ni en ningún servidor
> accesible desde internet. Solo se ejecuta en local, dentro de Docker, con fines
> educativos y para probar el triage de vulnerabilidades asistido por IA.

## Por qué este proyecto

Muchos de los análisis automáticos que corren en los pull requests buscan CVEs
conocidos en las dependencias. El código que introduce el propio pull request
recibe mucha menos atención: se confía en el desarrollador. Ataques a la cadena
de suministro como la puerta trasera de xz (2024) mostraron que el cambio de un
colaborador de confianza puede ser el ataque.

Este proyecto pone la revisión en el cambio mismo. Cada pull request se
escanea, una IA da una primera opinión y una persona toma la decisión final,
que queda registrada. No detiene a un atacante decidido. Asegura que alguien
mire y que la decisión deje rastro.

Lo hice para mi portafolio porque la ciberseguridad es el área que más me gusta.

## Qué hace

**Los escáneres encuentran, una IA sugiere, una persona decide y cada decisión
queda registrada.** Corre en cada pull request sobre una copia recortada de
[DVWA](https://github.com/digininja/DVWA), una aplicación vulnerable a
propósito. El análisis es solo estático: cada hallazgo es un candidato, no una
vulnerabilidad confirmada.

El objetivo es medir la **calidad de la decisión, no el volumen de alertas**.
Los números son públicos, solo como agregados:
<https://moypulido.github.io/dvwa-ai-triage/>

## Cómo funciona

1. **Encontrar.** GitHub Actions escanea solo los archivos en alcance con
   gitleaks, semgrep y trivy, y une los reportes en uno.
2. **Clasificar.** n8n descarta lo ya conocido, pide una sugerencia a una IA
   para lo nuevo (nunca para secretos) y manda un correo por pull request.
3. **Decidir.** Cada hallazgo trae un link firmado a una página con el código.
   La persona registra disposición, severidad y razón.
4. **Demostrar.** n8n calcula las métricas, manda un reporte ejecutivo y
   publica el dashboard.

El diagrama, las capturas y los flujos de n8n están en el [README en inglés](README.md).

## Ejecutarlo en local

```bash
docker compose up -d
```

Abre <http://localhost:4280>, entra con `admin` / `password` y da clic en
**Create / Reset Database**. Para detenerlo: `docker compose down`.

## Créditos y licencia

Basado en **DVWA – Damn Vulnerable Web Application** de Robin Wood
([@digininja](https://github.com/digininja)) y colaboradores:
<https://github.com/digininja/DVWA>.

Igual que el original, este proyecto usa la licencia
**GNU General Public License v3.0 (GPL-3.0)**. Ver [`COPYING.txt`](COPYING.txt).
