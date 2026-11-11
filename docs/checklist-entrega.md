# Checklist de entrega

Estado al cierre del trabajo del agente. ✅ = cumplido · ⏳ = en curso · 🙋 = te toca a ti, Amanda.

| # | Punto del enunciado | Estado | Dónde / qué falta |
|---|---|---|---|
| 1 | Repo público | ✅ | https://github.com/av-gomez/chacra-clara |
| 2 | Link en el issue #204 antes del martes 10/11, 11:59 p. m. | ✅ | Comentado el 10/11 a las 8:37 p. m. Hay que actualizarlo con la URL pública y el video. |
| 3 | README con las 9 partes | ✅ / 🙋 | Están las 9 partes. 🙋 Completar **2. Founder** y el resumen de las conversaciones en **3. Problema**. |
| 4 | LICENSE | ✅ | MIT |
| 5 | `.env.example` | ✅ | `ANTHROPIC_API_KEY` (opcional) y `LLM_TOPE_USD` |
| 6 | `.gitignore` (sin `.env`, sin tu voz, sin video crudo) | ✅ | `.env`, `*.m4a`, `voz/*.wav`, `video/crudo/` |
| 7 | `requirements.txt` | ✅ | Versiones fijadas |
| 8 | `docs/research/` con 3 conversaciones | 🙋 | Las plantillas están listas (`conversacion-1.md` a `-3.md`). **Faltan las conversaciones reales.** El agente no inventó respuestas. |
| 9 | Demo en URL pública | 🙋 | Hay que desplegarla en Streamlit Community Cloud (pide tu inicio de sesión). Los pasos están en el resumen final del agente y abajo. |
| 10 | Flujo principal en vivo con datos reales | ✅ | Probado en local con Playwright: dibujar → 5 fuentes → estado, mapa y tabla → ficha PDF y GeoJSON → nota de voz. ⏳ Falta probarlo en la URL pública. |
| 11 | Dos herramientas del curso dentro del producto | ✅ | Raster (07), GeoPandas y Folium (06), texto a voz con tu voz (15); extra: LLM con salida estructurada (08). README, parte 8. |
| 12 | Commits en varios días | ⏳ | Martes 10: varios commits. Miércoles 11: seguir con commits pequeños (correcciones, URL, video). |
| 13 | Sin claves en el repo | ✅ | Revisado con `git log -p` (api_key, secret, token): solo aparecen nombres de variables vacías. |
| 14 | Video de respaldo de 60 a 90 s, con su código en el repo | ⏳ | `scripts/grabar_video.py`, con narración en `video/narracion.json`. Sale en `video/demo_respaldo.mp4`. |
| 15 | Guion de 3 minutos (≤ 380 palabras) | ✅ | `docs/guion-presentacion.md` (351 palabras habladas) |
| 16 | Ensayo con cronómetro | 🙋 | Dos ensayos completos con la URL pública antes de las 6:00 p. m. del miércoles. |
| 17 | Accesibilidad revisada con herramienta automática | ✅ | axe-core: 0 violaciones en Inicio y Resultados (`docs/validacion/axe.json`) |
| 18 | Validación del método | ✅ | `docs/validacion/resultados.md` |
| 19 | Guía de archivos para explicar el código | ✅ | `docs/guia-archivos.md` |
| 20 | Parcela real con consentimiento (opcional) | 🙋 | `docs/research/parcela-real.md`, si la consigues |
| 21 | Congelamiento: miércoles 11, 3:00 p. m. (sin funciones nuevas) y demo estable a las 6:00 p. m. | 🙋 | Desde las 3:00 p. m., solo correcciones. |

## Desplegar en Streamlit Community Cloud (5 minutos)

1. Entra a https://share.streamlit.io y elige **Continue with GitHub** con la cuenta `av-gomez`.
2. Haz clic en **Create app** → **Deploy a public app from GitHub** y completa:
   - Repository: `av-gomez/chacra-clara`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: `chacra-clara`
3. En **Advanced settings**, elige **Python 3.12**. Los secretos van vacíos (la plantilla del informe no necesita clave).
4. Pulsa **Deploy** y espera de 3 a 5 minutos.
5. Prueba en el celular: Inicio → Demo Puno → SAN-01 → audio → ficha PDF → Tablero.

## Actualizar el comentario del issue

Con la URL y el video listos, edita el comentario en https://github.com/d2cml-ai/Data-Science-Python/issues/204: menú «···» del comentario → **Edit**. O pídeselo al agente.
