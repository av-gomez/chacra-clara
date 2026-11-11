# Guía de archivos: qué hace cada uno

Para explicar el código al profesor. Cada módulo de `chacra/` hace una sola tarea.

## La app

| Archivo | Qué hace | Funciones clave |
|---|---|---|
| `app.py` | La app de Streamlit. Cada página es una función (`pagina_inicio`, `pagina_ingresar`, `pagina_resultados`, `pagina_tablero`, `pagina_informe`, `pagina_guia`, `pagina_datos`), y al final `st.navigation` las une. Las parcelas viven en `st.session_state.parcelas`: no se guardan en ningún servidor. | `cargar()` valida y analiza un conjunto de parcelas. `detalle_parcela()` muestra el estado, la evidencia, las imágenes, la voz y las descargas. |
| `chacra/geometria.py` | **GeoPandas (sesión 06).** Lee las parcelas (GeoJSON, KML, CSV o Excel) y las valida con las reglas de la UE. | `leer_archivo()`, `desde_geojson()`, `validar()` (más de 4 ha exige polígono; 6 decimales; dentro del Perú; sin cruces, agujeros, duplicados ni superposiciones) y `area_ha()` (calcula en UTM, nunca en grados). |
| `chacra/satelite.py` | **Raster (sesión 07).** Cruza una parcela con las capas de su zona. Todas las capas están en la misma grilla, así que un píxel es el mismo lugar en todas. | `analizar()` recorta cada capa con `rasterio.mask`, mide el bosque 2020, la pérdida por fuente solo dentro del bosque 2020 y la pérdida en la que coinciden dos fuentes (`_dilatar` da 1 píxel de tolerancia). `hectareas_por_pixel()` pasa de píxeles a hectáreas según la latitud. |
| `chacra/estado.py` | Las **reglas y los umbrales**, a la vista. Convierte la evidencia en uno de tres estados con su confianza y sus razones en lenguaje claro. | `clasificar()`. Las constantes al inicio (`PERDIDA_MINIMA_HA`, `SIGNIFICATIVA_HA`…) se pueden cambiar. `ESTADOS` define texto, ícono, patrón y color de cada estado. |
| `chacra/mapas.py` | **Folium (sesión 06).** Mapa para dibujar (con `Draw`) y mapa de resultados con patrones (`StripePattern`, `CirclePattern`), capas raster superpuestas y capas del SERNANP. | `mapa_ingreso()`, `mapa_resultados()`, `recorte_imagen()` (corta el antes y el después de Sentinel-2 alrededor de la parcela y dibuja su contorno). |
| `chacra/cooperativa.py` | El tablero: analiza todas las parcelas, resume, alerta superposiciones con áreas protegidas y comunidades nativas, y ordena las visitas. | `analizar_todas()`, `resumen()` (días que faltan y % del volumen exportable), `prioridades()` (riesgo primero, luego la más cercana a la anterior). |
| `chacra/exportar.py` | Descargas: GeoJSON para el Sistema de Información de la UE, ficha PDF, reporte PDF y ZIP con todo. | `geojson_eudr()` (propiedades `ProducerName`, `ProducerCountry`, `ProductionPlace` y `Area`; 6 decimales), `ficha_pdf()`, `verificaciones()` (qué revisar en campo), `zip_todos_los_datos()`. |
| `chacra/informe.py` | **LLM con salida estructurada (sesión 08).** Informe para el comprador en español e inglés. | `InformeComprador` (esquema Pydantic), `informe_plantilla()` (sin API) e `informe_llm()` (Claude con `messages.parse`, costo calculado y tope por sesión). |
| `chacra/voz.py` | **Texto a voz (sesión 15), parte de la app.** Arma el texto de cada nota y busca el MP3 pregenerado. Lee `datos/traducciones.json` (quechua y aimara, vacías hasta que las valide un hablante). | `texto_nota()`, `audio_para()` (primero la nota personal de la parcela; si no existe, la general de su estado). |
| `chacra/rutas.py` | Las carpetas del proyecto, en un solo lugar. | — |

## Scripts (se corren una vez, fuera de la app)

| Archivo | Qué hace |
|---|---|
| `scripts/preparar_recortes.py` | Descarga y recorta las capas de las 3 zonas en una grilla común: JRC, Hansen, GLAD-S2, Impact Observatory, Geobosques, WorldCover, SERNANP y Sentinel-2. Lee solo la ventana de cada zona (`leer_ventana`) y reproyecta con `reproject` (vecino más cercano). |
| `scripts/elegir_parcelas.py` | Busca en los datos lugares reales para cada caso de prueba y arma polígonos irregulares de 1 a 3 ha. |
| `scripts/preparar_demo.py` | Elige 18 de esas parcelas (revisadas a ojo) para dos cooperativas ficticias y escribe el texto de sus notas de voz. |
| `scripts/validar_metodo.py` | Compara el estado de la app con el caso buscado y con mi revisión visual, y escribe `docs/validacion/resultados.md`. |
| `scripts/generar_voz.py` | Clona mi voz con Qwen3-TTS, mide el WER con Whisper, regenera si sale mal y guarda MP3 livianos en `audios/`. Va en un entorno aparte. |
| `scripts/probar_app.py` | Abre la app con Playwright en tamaño de celular, recorre el flujo, toma capturas y corre axe (accesibilidad). |
| `scripts/grabar_video.py` | `grabar()`: Playwright recorre la app y graba la pantalla, escena por escena, según lo que dura cada frase. `unir()`: ffmpeg pone cada frase de la narración en el segundo en que empieza su escena. |
| `scripts/hacer_video.py` | Un solo comando que hace todo el video desde cero: sintetiza la narración con mi voz clonada, levanta la app, graba, une y verifica que dure entre 60 y 90 s. Nadie graba nada a mano. |
| `tests/test_flujo.py` | Pruebas del flujo sin navegador: estados, fichas, reporte, ZIP, GeoJSON de la UE, informe y notas. |

## Datos

| Carpeta | Qué hay |
|---|---|
| `datos/recortes/<zona>/` | Una capa por archivo, todas en la misma grilla (~9 m): `jrc_bosque2020.tif` (1 = bosque), `*_perdida.tif` (año de pérdida menos 2000; 0 = sin pérdida; 255 = sin dato), `worldcover2020.tif`, `hansen_cobertura2000.tif`, `legalidad.geojson`, `s2_antes.jpg` y `s2_despues.jpg`. `zonas.json` lista las zonas y sus cajas. |
| `datos/parcelas/` | `candidatas.geojson` (89 parcelas de prueba) y `demo.geojson` (las 18 de las cooperativas de demo). |
| `datos/peru.geojson`, `datos/distritos.geojson` | Contorno del Perú y distritos, para validar que una parcela esté en el país. |
| `audios/` | Notas de voz en MP3 y `generadas.json` (texto, duración y WER de cada una). |
| `voz/voz_ref.txt` | El texto exacto de mi muestra de voz (la única grabación real; todo lo demás es sintético). El audio (`voz_ref.wav`) **no** se sube. |

## Una pregunta probable: «¿cómo decide el estado?»

1. `satelite.analizar()` recorta las capas con el polígono.
2. Mira qué píxeles eran bosque en 2020 (JRC).
3. Para cada fuente cuenta las hectáreas de pérdida después de 2020 **dentro** de ese bosque.
4. Cuenta dónde coinciden dos o más fuentes.
5. `estado.clasificar()` aplica los umbrales:
   - si ninguna fuente pasa 0,1 ha, la parcela queda **sin deforestación**;
   - si dos fuentes coinciden en una pérdida significativa (0,5 ha, o 0,2 ha que sean al menos el 10 % de la parcela), queda como **posible deforestación**;
   - cualquier otro caso va a **revisar**.

## Para practicar: 3 cambios que el profesor podría pedir

Cada uno toma menos de 5 minutos. Después de cambiar, corra `python tests/test_flujo.py` y `streamlit run app.py` para ver el efecto.

### 1. Cambiar un umbral: que una fuente «vea pérdida» desde 0,2 ha en vez de 0,1 ha

- **Dónde:** `chacra/estado.py`, **línea 20**: `PERDIDA_MINIMA_HA = 0.1`.
- **Cambio:** `PERDIDA_MINIMA_HA = 0.2`.
- **Efecto:** menos parcelas en «Revisar» (se ignoran pérdidas muy chicas) y más riesgo de falsos negativos. La Guía de la app y las razones de cada parcela se actualizan solas, porque leen esta constante.
- **Variante:** exigir que coincidan 3 fuentes en vez de 2 → **línea 25**: `FUENTES_MINIMAS_DE_ACUERDO = 3`.

### 2. Agregar (o quitar) una fuente satelital

- **Dónde:** `chacra/satelite.py`, **líneas 29 a 34**: la lista `FUENTES_PERDIDA`.
- **Quitar una fuente:** borrar su línea (por ejemplo, la de Impact Observatory, línea 32). La tabla de evidencia y el acuerdo entre fuentes se recalculan solos.
- **Agregar una fuente:** guardar un raster en `datos/recortes/<zona>/` con el mismo formato (año de pérdida menos 2000; 0 = sin pérdida; 255 = sin dato; misma grilla) y agregar una línea:
  `{"clave": "nueva", "nombre": "Nombre de la fuente", "archivo": "nueva_perdida.tif"},`
  Para descargarla, copiar el patrón de `hansen()` en `scripts/preparar_recortes.py`.

### 3. Cambiar un texto que ve el usuario

- **El consejo de un estado:** `chacra/estado.py`, **línea 34** (`"que_hacer"` de «Sin deforestación detectada»). Por ejemplo, agregar «Guarde la ficha por cinco años».
- **El nombre corto de un estado:** `chacra/estado.py`, **línea 36** (`"texto": "Revisar"`).
- **Una cifra de la portada:** `app.py`, **línea 119** y siguientes (las tarjetas de `cifras([...])`).
- **Una nota de voz:** el texto está en `chacra/voz.py` (`PLANTILLAS`). Si cambia, el audio viejo deja de coincidir: la app usa la nota general de ese estado (o solo el texto, si también cambió) hasta regenerarla con `scripts/generar_voz.py`.
