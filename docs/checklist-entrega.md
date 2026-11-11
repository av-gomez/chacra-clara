# Checklist de entrega

Revisado contra el enunciado del issue #204. ✅ = hecho · 🙋 = te toca a ti, Amanda · ⏳ = en curso.

## Enunciado del curso

| # | Punto del enunciado | Estado | Dónde / qué falta |
|---|---|---|---|
| 1 | Individual, problema real, de preferencia en el Perú | ✅ | EUDR para café y cacao del Perú |
| 2 | Repo público con todo el código | ✅ | https://github.com/av-gomez/chacra-clara |
| 3 | Link en el issue #204 antes del martes 10/11, 11:59 p. m. | ✅ | Comentado el 10/11 a las 8:37 p. m. Actualizado con la URL pública y el video. |
| 4 | Demo en URL pública (7–8 puntos) | ✅ | https://chacra-clara.streamlit.app, desplegada el 10/11. Flujo completo probado en celular y laptop. axe: 0 violaciones. |
| 5 | Flujo principal de principio a fin con datos reales | ✅ | Probado en local con Playwright: dibujar o cargar el ejemplo → 5 fuentes → estado, mapa y tabla → ficha PDF y GeoJSON → nota de voz → tablero. |
| 6 | Plan B: corre en la laptop (4–6 puntos) | ✅ | `correr_local.bat` (Windows) o `sh correr_local.sh`: un solo comando. |
| 7 | Plan B: video de 60 a 90 s del software real, con su código en el repo | ✅ | `video/demo_respaldo.mp4` (63 s). **Automático, sin grabación manual:** Playwright graba la pantalla, Qwen3-TTS sintetiza la narración con tu voz clonada y ffmpeg une ambas. Se regenera con `python scripts/hacer_video.py --python-voz .venv-voz/Scripts/python --desde-cero`. |
| 8 | Dos herramientas del curso dentro del producto | ✅ | Raster (07), GeoPandas y Folium (06), texto a voz con tu voz (15); extra: LLM con salida estructurada (08). README, parte 8. |
| 9 | README con las 9 partes | ✅ / 🙋 | Están las 9 partes. 🙋 Responder las 5 preguntas de **2. Founder** y resumir las conversaciones en **3. Problema**. |
| 10 | 3 conversaciones con usuarios en `docs/research/` | 🙋 | Plantillas listas (`conversacion-1.md` a `-3.md`) y mensajes para pedirlas en `docs/research/mensajes-whatsapp.md`. **Faltan las conversaciones reales.** El agente no inventó respuestas. |
| 11 | Modelo de negocio: quién paga, precio y costo por usuario | ✅ | README, parte 7 |
| 12 | Commits en varios días | ⏳ | Martes 10: más de 20 commits. Miércoles 11: el agente sigue con commits pequeños. |
| 13 | Sin claves en el repo ni `.env` real | ✅ | Revisado con `git log -p` (api_key, secret, token): solo nombres de variables vacías. `.env` está en `.gitignore`. |
| 14 | No dejar el README del template | ✅ | README propio |
| 15 | Datos públicos, sintéticos o propios | ✅ | Capas satelitales públicas; parcelas en lugares reales con productores ficticios; tu voz, con tu consentimiento. |
| 16 | Tope de gasto si la app usa una API de pago | ✅ | `LLM_TOPE_USD` (0,50 USD por sesión) y modo sin API por defecto |
| 17 | Presentación de 3 minutos, sin diapositivas | 🙋 | `docs/guion-presentacion.md`: 209 palabras habladas, versión en letra grande, ruta de clics y plan si se corta. Ensayar dos veces con cronómetro. |

## Lo que pediste además

| Punto | Estado | Dónde |
|---|---|---|
| LICENSE, `.env.example`, `.gitignore`, `requirements.txt` | ✅ | Raíz del repo |
| Privacidad de tu voz: ni la muestra, ni el audio limpio, ni el modelo en el repo o en el historial | ✅ | Revisado en todos los commits. README, sección «Mi voz». |
| Nota de que las voces son sintéticas y con consentimiento | ✅ | README, al inicio y en «Mi voz» |
| Cabe en los límites gratuitos (memoria, tamaño, archivos de más de 100 MB) | ✅ | README, «¿Cabe en el plan gratuito?» |
| Secretos para Streamlit (solo nombres) y modo sin API | ✅ | `docs/secretos-streamlit.md` |
| Botón «Cargar cooperativa de ejemplo» | ✅ | En Inicio e Ingresar (y en Resultados y Tablero cuando no hay parcelas) |
| Accesibilidad revisada con herramienta automática | ✅ | axe-core: 0 violaciones en las 7 páginas (`docs/validacion/axe.json`) |
| Validación del método | ✅ | `docs/validacion/resultados.md` |
| Guía de archivos con 3 cambios para practicar | ✅ | `docs/guia-archivos.md` |
| Parcela real con consentimiento (opcional) | 🙋 | `docs/research/parcela-real.md`, si la consigues |

## Lo que te toca, con horas (miércoles 11)

| Hora | Qué |
|---|---|
| Antes de las 3:00 p. m. | Las 3 conversaciones (`mensajes-whatsapp.md`), completar `conversacion-1/2/3.md` y la sección Founder. |
| 3:00 p. m. | Congelamiento: sin funciones nuevas, solo correcciones. |
| 4:00 – 5:30 p. m. | Dos ensayos con cronómetro usando la URL pública. |
| 6:00 p. m. | Demo estable y sin cambios. |
| **6:30 p. m.** | **Abrir la URL para despertar la app** y pulsar «Cargar cooperativa de ejemplo» una vez. |
| 6:45 p. m. | Si es por Zoom: probar «Compartir sonido». |
| 7:00 p. m. | Conectarte con el demo abierto y probado. |
| 7:19 p. m. | Mientras presenta la n.º 6, recargar la URL y pulsar «Cargar cooperativa de ejemplo». |
| **~7:26 p. m.** | **Tu turno (7.ª en la lista).** Si alguien falta, se adelanta. |

## Desplegar en Streamlit Community Cloud (5 minutos)

1. Entra a https://share.streamlit.io y elige **Continue with GitHub** con la cuenta `av-gomez`.
2. Haz clic en **Create app** → **Deploy a public app from GitHub** y completa:
   - Repository: `av-gomez/chacra-clara`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: `chacra-clara`
3. En **Advanced settings**, elige **Python 3.12**. Los secretos son opcionales (`docs/secretos-streamlit.md`).
4. Pulsa **Deploy**, espera de 3 a 5 minutos y avisa al agente.
