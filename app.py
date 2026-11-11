"""Chacra Clara: tamizaje satelital de parcelas de café y cacao para la EUDR.

Para correrlo:  streamlit run app.py
Cada página es una función. La lógica está en la carpeta chacra/ (una tarea por archivo).
"""
import base64
import json
import os

import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import shape
from streamlit_folium import st_folium

from chacra import cooperativa, exportar, geometria, informe, mapas, voz
from chacra.estado import ESTADOS, PERDIDA_MINIMA_HA, SIGNIFICATIVA_CHICA_HA, SIGNIFICATIVA_HA
from chacra.rutas import PARCELAS, RAIZ
from chacra.satelite import zonas_disponibles

st.set_page_config(page_title="Chacra Clara · EUDR para cooperativas", page_icon="🌱", layout="centered",
                   initial_sidebar_state="collapsed")

ONE_LINER = ("Hacemos que el café y el cacao de los pequeños productores peruanos puedan seguir entrando a Europa, "
             "para cooperativas y exportadoras, mediante un tamizaje satelital abierto de cada parcela que se "
             "convierte en el expediente de debida diligencia que pide la EUDR.")
# Cooperativas de demo (ficticias): nombre y oficina desde donde sale el técnico (plaza del pueblo)
COOPERATIVAS_DEMO = {
    "puno": {"nombre": "Central Demo Valle Alto, Puno (ficticia)", "oficina": (-14.2238, -69.1527)},
    "sanmartin": {"nombre": "Cooperativa Demo Alto Mayo, San Martín (ficticia)", "oficina": (-6.0346, -76.9717)},
}


# ---------- estado de la sesión ----------

def iniciar():
    if "parcelas" not in st.session_state:
        st.session_state.parcelas = None       # GeoDataFrame con las parcelas cargadas y analizadas
    if "gasto_llm" not in st.session_state:
        st.session_state.gasto_llm = 0.0
    if "ligero" not in st.session_state:
        st.session_state.ligero = False


def css():
    estilo = (RAIZ / "assets" / "estilo.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{estilo}</style>", unsafe_allow_html=True)
    st.markdown('<a class="saltar" href="#contenido">Saltar al contenido</a><span id="contenido"></span>',
                unsafe_allow_html=True)


def insignia(estado):
    """Estado con ícono, texto y patrón: se entiende sin ver colores."""
    if estado not in ESTADOS:
        return '<span class="estado">Fuera de las zonas del demo</span>'
    e = ESTADOS[estado]
    return (f'<span class="estado estado-{estado}" role="status"><span class="icono" aria-hidden="true">'
            f'{e["icono"]}</span>{e["texto"]}</span>')


def cifras(items):
    tarjetas = "".join(f'<div class="cifra"><div class="valor">{v}</div><div class="rotulo">{r}</div></div>'
                       for v, r in items)
    st.markdown(f'<div class="cifras">{tarjetas}</div>', unsafe_allow_html=True)


def aviso_tamizaje():
    st.markdown('<div class="aviso"><strong>Importante:</strong> Chacra Clara es una herramienta de tamizaje y de '
                'apoyo a la debida diligencia. <strong>No es una certificación oficial.</strong> '
                'El resultado final lo valida un técnico.</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def parcelas_demo(cooperativa_demo):
    """Lee la demo con el mismo lector que un GeoJSON subido por el usuario (mismas columnas y validación)."""
    datos = json.loads((PARCELAS / "demo.geojson").read_text(encoding="utf-8"))
    datos["features"] = [f for f in datos["features"] if f["properties"]["cooperativa"] == cooperativa_demo]
    return geometria.desde_geojson(datos)


def cargar_demo(clave):
    st.session_state.cooperativa = clave
    cargar(parcelas_demo(clave))


def nombre_cooperativa():
    clave = st.session_state.get("cooperativa")
    return COOPERATIVAS_DEMO[clave]["nombre"] if clave in COOPERATIVAS_DEMO else "Su cooperativa"


def cargar(gdf):
    """Valida y analiza un conjunto de parcelas y lo guarda en la sesión."""
    validadas = geometria.validar(gdf)
    with st.spinner("Cruzando cada parcela con las fuentes satelitales…"):
        analizadas = cooperativa.analizar_todas(validadas)
    st.session_state.parcelas = analizadas


def agregar(gdf):
    actuales = st.session_state.parcelas
    if actuales is None:
        cargar(gdf)
        return
    base = actuales.drop(columns=["analisis", "estado", "texto_estado", "confianza", "zona", "errores", "avisos",
                                  "valida", "area_calculada_ha"], errors="ignore")
    juntas = gpd.GeoDataFrame(pd.concat([base, gdf], ignore_index=True), crs="EPSG:4326")
    cargar(juntas)


# ---------- páginas ----------

def pagina_inicio():
    st.markdown(f'<div class="portada"><span class="etiqueta">Reglamento (UE) 2023/1115 · EUDR</span>'
                f'<h1>Chacra Clara</h1><p>{ONE_LINER}</p></div>', unsafe_allow_html=True)
    hoy = cooperativa.resumen(pd.DataFrame({"estado": [], "produccion_kg_anual": []}))
    cifras([(f"{hoy['dias_grandes']}", "días para el 30/12/2026 (exportadoras grandes y medianas)"),
            (f"{hoy['dias_pequenos']}", "días para el 30/06/2027 (micro y pequeñas empresas)"),
            ("160 mil", "predios de café aún sin geolocalizar, según la Junta Nacional del Café"),
            ("40 %", "del café peruano exportado en valor va a la Unión Europea")])
    st.markdown("## Cómo funciona, en tres pasos")
    st.markdown(
        "1. **Ingrese sus parcelas.** Dibújelas en el mapa, suba un GeoJSON o KML, o un Excel con coordenadas.\n"
        "2. **Las cruzamos con cinco fuentes satelitales abiertas**: el mapa de bosques 2020 que usa la Unión Europea "
        "(JRC), Hansen/UMD, las alertas GLAD de Sentinel-2, Impact Observatory y Geobosques del MINAM.\n"
        "3. **Reciba el estado de cada parcela con su evidencia**, la lista de visitas para el técnico, la ficha "
        "en PDF, el GeoJSON para la declaración y una nota de voz para el productor.")
    st.markdown("## Pruébelo")
    col1, col2, col3 = st.columns(3)
    if col1.button("Demo Puno (Sandia y Carabaya)", type="primary", use_container_width=True):
        cargar_demo("puno")
        st.switch_page(PAGINAS["resultados"])
    if col2.button("Demo San Martín (Alto Mayo)", use_container_width=True):
        cargar_demo("sanmartin")
        st.switch_page(PAGINAS["resultados"])
    if col3.button("Ingresar mis parcelas", use_container_width=True):
        st.switch_page(PAGINAS["ingresar"])
    aviso_tamizaje()
    st.caption("Las parcelas de demo usan ubicaciones reales de zonas cafetaleras de Puno y San Martín con productores "
               "ficticios. Las capas satelitales son datos reales.")


def pagina_ingresar():
    st.title("Ingresar parcelas")
    st.write("Elija una forma. Todas terminan en el mismo análisis.")
    zonas = zonas_disponibles()
    forma = st.radio("¿Cómo quiere ingresar las parcelas?",
                     ["Dibujar en el mapa", "Subir archivo (GeoJSON, KML, Excel o CSV)"], horizontal=True)
    if forma == "Dibujar en el mapa":
        nombres = {z["nombre"]: k for k, z in zonas.items()}
        zona_nombre = st.selectbox("Zona del mapa", list(nombres))
        zona = zonas[nombres[zona_nombre]]
        oeste, sur, este, norte = zona["bbox"]
        st.markdown("Use el botón del **pentágono** para dibujar el contorno (haga clic en cada esquina y cierre en "
                    "el primer punto) o el del **marcador** para una parcela de 4 ha o menos. El recuadro amarillo "
                    "punteado es la zona con datos.")
        m = mapas.mapa_ingreso([(sur + norte) / 2, (oeste + este) / 2], 14, st.session_state.parcelas,
                               st.session_state.ligero)
        salida = st_folium(m, height=460, use_container_width=True, key=f"dibujo_{nombres[zona_nombre]}",
                           returned_objects=["last_active_drawing"])
        dibujo = (salida or {}).get("last_active_drawing")
        with st.form("datos_parcela"):
            c1, c2 = st.columns(2)
            productor = c1.text_input("Código del productor", value="PR-NUEVO",
                                      help="Use un código, no el nombre ni el DNI.")
            parcela = c2.text_input("Código de la parcela", value="PR-NUEVO-A")
            c3, c4, c5 = st.columns(3)
            cultivo = c3.selectbox("Cultivo", ["café", "cacao"])
            area = c4.number_input("Área declarada (ha)", min_value=0.0, value=2.0, step=0.1,
                                   help="Obligatoria si marca un punto.")
            produccion = c5.number_input("Producción al año (kg)", min_value=0, value=1200, step=100)
            enviar = st.form_submit_button("Analizar esta parcela", type="primary")
        if enviar:
            if not dibujo:
                st.error("Primero dibuje la parcela en el mapa.")
                return
            gdf = geometria.desde_geojson({"type": "FeatureCollection", "features": [{
                "type": "Feature", "geometry": dibujo["geometry"],
                "properties": {"codigo_productor": productor, "codigo_parcela": parcela, "cultivo": cultivo,
                               "area_ha": area, "produccion_kg_anual": produccion}}]})
            agregar(gdf)
            st.session_state.seleccion = parcela
            st.switch_page(PAGINAS["resultados"])
    else:
        st.download_button("Descargar plantilla de Excel/CSV", geometria.plantilla_csv(),
                           file_name="plantilla_parcelas.csv", mime="text/csv")
        st.caption("Columnas: codigo_productor, codigo_parcela, cultivo, latitud, longitud, area_ha, "
                   "produccion_kg_anual. Coordenadas en grados decimales (WGS84) con 6 decimales.")
        archivo = st.file_uploader("Archivo de parcelas", type=["geojson", "json", "kml", "csv", "xlsx"])
        if archivo is not None:
            try:
                gdf = geometria.leer_archivo(archivo)
            except Exception as error:
                st.error(f"No pudimos leer el archivo: {error}")
                return
            st.success(f"Leímos {len(gdf)} parcelas.")
            if st.button("Validar y analizar", type="primary"):
                agregar(gdf)
                st.switch_page(PAGINAS["resultados"])
    st.caption("Zonas con datos precalculados en este demo: " + "; ".join(z["nombre"] for z in zonas.values()) + ".")


def tabla_validacion(gdf):
    problemas = gdf[(gdf["errores"].apply(len) > 0) | (gdf["avisos"].apply(len) > 0)]
    if len(problemas) == 0:
        st.success("Todas las geometrías pasaron la validación (punto o polígono según el área, 6 decimales, "
                   "dentro del Perú, sin cruces, agujeros ni duplicados).")
        return
    hay_errores = bool(gdf["errores"].apply(len).sum())
    with st.expander(f"Validación de geometrías: {len(problemas)} parcelas con observaciones", expanded=hay_errores):
        filas = [{"Parcela": f["codigo_parcela"], "Errores (impiden el análisis)": " ".join(f["errores"]) or "—",
                  "Avisos": " ".join(f["avisos"]) or "—"} for _, f in problemas.iterrows()]
        st.table(pd.DataFrame(filas).set_index("Parcela"))


def pagina_resultados():
    st.title("Resultados por parcela")
    gdf = st.session_state.parcelas
    if gdf is None:
        st.info("Aún no hay parcelas. Cargue la cooperativa de demo o ingrese las suyas.")
        if st.button("Cargar la demo de Puno", type="primary"):
            cargar_demo("puno")
            st.rerun()
        return
    r = cooperativa.resumen(gdf)
    st.markdown(f"**Resumen:** de {r['total']} parcelas analizadas, {r['sin']} no muestran deforestación, "
                f"{r['revisar']} hay que revisarlas y {r['posible']} muestran posible deforestación después de 2020."
                + (f" {r['fuera']} quedaron sin analizar (fuera de zona o con errores)." if r["fuera"] else ""))
    tabla_validacion(gdf)

    codigos = list(gdf["codigo_parcela"])
    inicial = st.session_state.get("seleccion")
    indice = codigos.index(inicial) if inicial in codigos else 0
    elegida = st.selectbox("Parcela", codigos, index=indice,
                           format_func=lambda c: f"{c} · {gdf.loc[gdf.codigo_parcela == c, 'texto_estado'].iloc[0] or 'sin analizar'}")
    st.session_state.seleccion = elegida

    analizadas = gdf[gdf["estado"].notna()]
    if len(analizadas):
        st.markdown("## Mapa")
        st.caption("Liso = sin deforestación detectada · rayado = revisar · punteado = posible deforestación. "
                   "En magenta, la pérdida de bosque después de 2020. Use el botón de capas (arriba a la derecha) "
                   "para ver cada fuente. La tabla de abajo tiene la misma información.")
        m = mapas.mapa_resultados(gdf, st.session_state.ligero, seleccion=elegida)
        st_folium(m, height=440, use_container_width=True, returned_objects=[], key=f"res_{elegida}")
        st.markdown("## Tabla de parcelas")
        filas = []
        for _, f in gdf.iterrows():
            a = f["analisis"] or {}
            filas.append({"Parcela": f["codigo_parcela"],
                          "Estado": (ESTADOS[f["estado"]]["icono"] + " " + ESTADOS[f["estado"]]["corto"])
                          if f["estado"] else "Sin analizar", "Confianza": f["confianza"] or "—",
                          "Pérdida (ha)": f"{a.get('perdida_acordada_ha', 0):.2f}" if f["estado"] else "—"})
        st.table(pd.DataFrame(filas).set_index("Parcela"))

    fila = gdf[gdf["codigo_parcela"] == elegida].iloc[0]
    detalle_parcela(fila)


def detalle_parcela(fila):
    a = fila["analisis"]
    st.markdown(f"## Parcela {fila['codigo_parcela']}")
    if not a or a.get("error"):
        st.warning(a.get("error") if a else "Sin análisis.")
        return
    st.markdown(insignia(a["estado"]) + f" &nbsp; Confianza **{a['confianza']}**", unsafe_allow_html=True)
    st.write(ESTADOS[a["estado"]]["que_hacer"])
    st.markdown("**Por qué:**")
    st.markdown("\n".join(f"- {r}" for r in a["razones"]))
    if a.get("legalidad"):
        st.markdown("**Alertas de legalidad (SERNANP):**")
        st.markdown("\n".join(f"- {x}" for x in a["legalidad"]))

    st.markdown("### Evidencia por fuente")
    filas = []
    for e in a["evidencias"]:
        if not e["disponible"]:
            filas.append({"Fuente": e["fuente"], "¿Ve pérdida?": "sin datos", "Hectáreas por año": "—"})
            continue
        detecta = "Sí" if e["perdida_en_bosque_ha"] >= PERDIDA_MINIMA_HA else "No"
        filas.append({"Fuente": e["fuente"], "¿Ve pérdida?": f"{detecta} ({e['perdida_en_bosque_ha']:.2f} ha)",
                      "Hectáreas por año": ", ".join(f"{k}: {v:.2f}" for k, v in sorted(e["anios"].items())) or "—"})
    st.table(pd.DataFrame(filas).set_index("Fuente"))
    st.caption(f"Área analizada {a['area_analizada_ha']:.2f} ha · bosque en 2020 (JRC) {a['bosque_2020_ha']:.2f} ha "
               f"({a['bosque_2020_pct']:.0f} %) · pérdida en la que coinciden dos o más fuentes "
               f"{a['perdida_acordada_ha']:.2f} ha. Una fuente «detecta» desde {PERDIDA_MINIMA_HA} ha.")

    imagenes = None
    if not st.session_state.ligero:
        geom = shape(a["geometria_analizada"]) if fila.geometry.geom_type == "Point" else fila.geometry
        antes = mapas.recorte_imagen(a["zona"], "antes", geom)
        despues = mapas.recorte_imagen(a["zona"], "despues", geom)
        if antes and despues:
            imagenes = {"antes": antes, "despues": despues}
            st.markdown("### Imágenes Sentinel-2: antes y después")
            b1 = base64.b64encode(antes).decode()
            b2 = base64.b64encode(despues).decode()
            st.markdown(
                f'<div class="evidencia"><figure><img src="data:image/png;base64,{b1}" alt="Imagen satelital Sentinel-2 '
                f'de la parcela {fila["codigo_parcela"]} en la estación seca de 2020, con su contorno en amarillo">'
                f'<figcaption>2020 (antes de la fecha de corte)</figcaption></figure><figure>'
                f'<img src="data:image/png;base64,{b2}" alt="Imagen satelital Sentinel-2 de la misma parcela en la '
                f'estación seca de 2025"><figcaption>2025 (después)</figcaption></figure></div>', unsafe_allow_html=True)
            st.caption("Copernicus Sentinel-2 L2A (ESA), mediana de junio a octubre. Contorno amarillo: la parcela.")

    st.markdown("### Nota de voz para el productor")
    ruta, texto, personal = voz.audio_para(fila["codigo_parcela"], fila["cultivo"], a["estado"])
    if ruta:
        st.audio(str(ruta), format="audio/mpeg")
        st.caption(("Nota personal de esta parcela" if personal else "Nota general para este resultado") +
                   ", con la voz de Amanda clonada con IA (Qwen3-TTS). Pesa menos de 200 KB: se puede reenviar "
                   "por WhatsApp.")
        st.download_button("Descargar el audio (MP3)", ruta.read_bytes(), file_name=f"nota_{fila['codigo_parcela']}.mp3",
                           mime="audio/mpeg")
    else:
        st.caption("El audio de esta nota se genera en la versión local (scripts/generar_voz.py).")
    with st.expander("Texto de la nota (transcripción)"):
        st.write(texto)
        trad = voz.traducciones()
        for codigo in ["qu", "ay"]:
            idioma = trad.get(codigo, {})
            validado = idioma.get(a["estado"], {}).get("texto")
            st.markdown(f"**{voz.IDIOMAS[codigo]}:** " + (validado if validado else
                        "pendiente: lo debe escribir y validar una persona hablante (no usamos traducción automática)."))

    st.markdown("### Descargas")
    c1, c2 = st.columns(2)
    c1.download_button("Ficha PDF de la parcela", exportar.ficha_pdf(fila, a, imagenes),
                       file_name=f"ficha_{fila['codigo_parcela']}.pdf", mime="application/pdf", type="primary",
                       use_container_width=True)
    unica = gpd.GeoDataFrame([fila], geometry="geometry", crs="EPSG:4326")
    c2.download_button("GeoJSON para la declaración (UE)", exportar.geojson_eudr(unica),
                       file_name=f"{fila['codigo_parcela']}_eudr.geojson", mime="application/geo+json",
                       use_container_width=True)
    st.markdown("**Qué verificar en campo:**")
    st.markdown("\n".join(f"- {p}" for p in exportar.verificaciones(a)))
    st.markdown("### Siguiente paso")
    c1, c2 = st.columns(2)
    if c1.button("Ver el tablero y la ruta de visitas", use_container_width=True):
        st.switch_page(PAGINAS["tablero"])
    if c2.button("Preparar el informe para el comprador", use_container_width=True):
        st.switch_page(PAGINAS["informe"])


def pagina_tablero():
    st.title("Tablero de la cooperativa")
    gdf = st.session_state.parcelas
    if gdf is None:
        st.info("Cargue parcelas primero.")
        if st.button("Cargar la demo de Puno", type="primary"):
            cargar_demo("puno")
            st.rerun()
        return
    r = cooperativa.resumen(gdf)
    st.markdown(f"**{nombre_cooperativa()}**")
    cifras([(f"{r['sin']}", "✓ listas: sin deforestación detectada"),
            (f"{r['revisar']}", "! por revisar en campo"),
            (f"{r['posible']}", "✕ con posible deforestación"),
            (f"{r['pct_volumen']:.0f} %", f"del volumen podría ir hoy a Europa ({r['kg_listos']:,.0f} de {r['kg_total']:,.0f} kg)"),
            (f"{r['dias_grandes']}", "días para el 30/12/2026"),
            (f"{r['dias_pequenos']}", "días para el 30/06/2027")])
    st.caption("Fechas del Reglamento (UE) 2025/2650: 30/12/2026 para operadores grandes y medianos, 30/06/2027 "
               "para micro y pequeñas empresas. El porcentaje de volumen usa la producción declarada de cada parcela.")

    st.markdown("## Visitas de campo, en orden")
    clave = st.session_state.get("cooperativa")
    if clave in COOPERATIVAS_DEMO:
        base = COOPERATIVAS_DEMO[clave]["oficina"]
    else:
        base = (gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean())
    orden = cooperativa.prioridades(gdf, base)
    if len(orden) == 0:
        st.success("No hay parcelas por visitar.")
    else:
        st.write("Primero las de posible deforestación y luego las de revisar. Dentro de cada grupo, la más cercana "
                 "a la anterior, saliendo de la oficina de la cooperativa (distancia en línea recta).")
        mostrar = orden[["orden", "codigo_parcela", "estado", "km_desde_anterior"]].copy()
        cortos = {ESTADOS[k]["texto"]: ESTADOS[k]["icono"] + " " + ESTADOS[k]["corto"] for k in ESTADOS}
        mostrar["estado"] = mostrar["estado"].map(cortos)
        mostrar.columns = ["N.º", "Parcela", "Estado", "Km desde la anterior"]
        st.table(mostrar.set_index("N.º"))
        st.download_button("Descargar la ruta (CSV con coordenadas)", orden.to_csv(index=False).encode("utf-8-sig"),
                           file_name="ruta_visitas.csv", mime="text/csv")
        st.markdown("**Qué llevar a cada visita:** celular con GPS para fotos con fecha y ubicación, la ficha PDF "
                    "impresa o en el celular, y un formato para el testimonio del productor y de un vecino. "
                    "Pida imágenes o documentos de antes de 2021 (fotos, constancias de posesión).")
    st.markdown("## Reporte de la cooperativa")
    st.download_button("Descargar reporte PDF", exportar.reporte_cooperativa_pdf(nombre_cooperativa(), gdf, r),
                       file_name="reporte_cooperativa.pdf", mime="application/pdf", type="primary")


def pagina_informe():
    st.title("Informe para el comprador europeo")
    gdf = st.session_state.parcelas
    if gdf is None:
        st.info("Cargue parcelas primero.")
        return
    r = cooperativa.resumen(gdf)
    datos = informe.datos_para_informe(nombre_cooperativa(), gdf, r)
    hay_clave = cargar_clave_api()
    tope = float(os.getenv("LLM_TOPE_USD", "0.50"))
    modo = st.radio("Cómo redactarlo", ["Plantilla (sin internet, siempre disponible)",
                                        "Con IA (Claude, salida validada con un esquema)"],
                    help="El modo con IA necesita una clave de API. Tiene un tope de gasto por sesión.")
    resultado, nota = None, ""
    if modo.startswith("Con IA"):
        if not hay_clave:
            st.warning("Este despliegue no tiene clave de API: se usa la plantilla.")
        elif st.button("Redactar con IA", type="primary"):
            try:
                with st.spinner("Redactando…"):
                    resultado, costo = informe.informe_llm(datos, st.session_state.gasto_llm, tope)
                st.session_state.gasto_llm += costo
                nota = f"Redactado por {informe.MODELO}. Costo: {costo:.4f} USD (acumulado {st.session_state.gasto_llm:.3f} de {tope:.2f})."
            except Exception as error:
                st.warning(f"No se pudo usar la IA ({error}). Se usa la plantilla.")
    if resultado is None:
        resultado = informe.informe_plantilla(datos)
        nota = nota or "Redactado con la plantilla (modo sin API)."
    st.caption(nota)
    pestana_es, pestana_en = st.tabs(["Español", "English"])
    with pestana_es:
        st.markdown(f"**Nivel de riesgo:** {resultado.nivel_riesgo}")
        st.write(resultado.resumen_es)
        for h in resultado.hallazgos:
            st.markdown(f"- {insignia(h.estado)} **{h.parcela}**: {h.explicacion_es}", unsafe_allow_html=True)
        st.markdown("**Mitigación:**\n" + "\n".join(f"- {x}" for x in resultado.mitigacion_es))
        st.markdown("**Límites:**\n" + "\n".join(f"- {x}" for x in resultado.limitaciones_es))
    with pestana_en:
        st.markdown(f"**Risk level:** {dict(bajo='low', medio='medium', alto='high')[resultado.nivel_riesgo]}")
        st.write(resultado.summary_en)
        for h in resultado.hallazgos:
            st.markdown(f"- **{h.parcela}**: {h.explanation_en}")
        st.markdown("**Mitigation:**\n" + "\n".join(f"- {x}" for x in resultado.mitigation_en))
        st.markdown("**Limitations:**\n" + "\n".join(f"- {x}" for x in resultado.limitations_en))
    st.download_button("Descargar el informe (JSON validado)", resultado.model_dump_json(indent=2),
                       file_name="informe_comprador.json", mime="application/json")


def cargar_clave_api():
    """Busca la clave en el entorno (.env) o en los secretos de Streamlit Cloud. Nunca está en el repo."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return True
    try:
        clave = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        clave = ""
    if clave:
        os.environ["ANTHROPIC_API_KEY"] = clave
    return bool(clave)


def pagina_guia():
    st.title("Guía en lenguaje claro")
    st.markdown("""
## ¿Qué pide Europa?
Desde el **30 de diciembre de 2026**, las empresas grandes y medianas que vendan café o cacao en la Unión Europea
deben demostrar que no viene de tierras donde se cortó bosque **después del 31 de diciembre de 2020**.
Las micro y pequeñas empresas tienen hasta el **30 de junio de 2027**. La norma es el Reglamento (UE) 2023/1115,
conocido como **EUDR** (por sus siglas en inglés: *EU Deforestation Regulation*).

## ¿Qué hay que entregar?
- **La ubicación de cada parcela.** Si mide **más de 4 hectáreas**, hay que dar su contorno (un polígono).
  Si mide 4 hectáreas o menos, basta un punto. Las coordenadas van con **6 decimales**.
- **Que no hubo deforestación** después de 2020 y que se cumplió la ley peruana (por ejemplo, permisos y
  derechos de comunidades).
- El Perú está en la categoría de **riesgo estándar**: el comprador debe evaluar y reducir el riesgo,
  y las autoridades revisan al 3 % de los importadores.

## ¿Qué es «bosque» para la norma?
Un área de **más de media hectárea** con árboles de **más de 5 metros** que cubren **más del 10 %** del suelo.
**No** cuenta como bosque la tierra de uso agrícola. Los sistemas agroforestales (como el café bajo sombra) se
consideran uso agrícola. Pero en el satélite el café bajo sombra puede **parecer** bosque: por eso esos casos van a «Revisar».

## ¿Qué significa cada estado?
""")
    for clave in ["sin", "revisar", "posible"]:
        st.markdown(f"{insignia(clave)}", unsafe_allow_html=True)
        st.write(ESTADOS[clave]["que_hacer"])
    st.markdown(f"""
## ¿Cómo decide Chacra Clara?
- Una fuente **ve pérdida** si encuentra al menos **{PERDIDA_MINIMA_HA} ha** perdidas después de 2020 donde en 2020 había bosque.
- **Posible deforestación:** dos o más fuentes coinciden, en el mismo lugar, en una pérdida **significativa**:
  {SIGNIFICATIVA_HA} ha o más, o {SIGNIFICATIVA_CHICA_HA} ha que sean al menos el 10 % de la parcela.
- **Revisar:** solo una fuente ve la pérdida, la pérdida es pequeña, o la mitad o más cae donde en 2020 ya había
  cultivo o pasto (renovación, poda o quema de una chacra existente).
- **Confianza:** alta si están todas las fuentes y coinciden; media o baja si falta alguna, si la parcela es un
  punto o si las fuentes no se ponen de acuerdo.

## Fuentes de datos
| Fuente | Qué dice | Resolución |
|---|---|---|
| JRC Global Forest Cover 2020 (Comisión Europea) | Dónde había bosque en 2020 | 10 m |
| Hansen / UMD Global Forest Change v1.13 | Año de pérdida de cobertura arbórea hasta 2025 | 30 m |
| Alertas GLAD-S2 (UMD) | Alertas de pérdida con Sentinel-2, confianza media y alta | 10 m |
| Impact Observatory (uso del suelo anual) | Cambio de árboles a cultivo o pasto entre 2020 y 2023 | 10 m |
| Geobosques (MINAM) | Pérdida de bosque húmedo amazónico, dato oficial peruano | 30 m |
| ESA WorldCover 2020 | Uso del suelo en 2020 (cultivo, pasto, árboles) | 10 m |
| SERNANP | Áreas protegidas, zonas de amortiguamiento y comunidades nativas | vector |

El mapa del JRC es una referencia: la propia Comisión dice que no es obligatorio ni legalmente vinculante.
""")
    aviso_tamizaje()


def pagina_datos():
    st.title("Sus datos son suyos")
    st.markdown("""
- **La cooperativa es dueña de sus datos y de los de sus socios.** Chacra Clara solo los procesa para el tamizaje.
- **Puede exportarlo todo en cualquier momento**, en formatos abiertos (GeoJSON, CSV, JSON), y llevarlo a otra
  herramienta o a la plataforma del Estado.
- **Cada productor recibe su propia ficha y su nota de voz.** Nadie más usa su información sin permiso de la cooperativa.
- Este demo **no guarda nada en un servidor**: los datos viven solo en su sesión del navegador y se borran al cerrarla.
- Use **códigos** de productor, no nombres ni DNI. Para la declaración, la cooperativa decide si completa el nombre.
""")
    gdf = st.session_state.parcelas
    if gdf is None:
        st.info("Cuando cargue parcelas, aquí podrá descargarlas todas.")
        return
    r = cooperativa.resumen(gdf)
    st.download_button("Descargar todos mis datos (ZIP)", exportar.zip_todos_los_datos(gdf, r),
                       file_name="chacra_clara_mis_datos.zip", mime="application/zip", type="primary")
    st.download_button("Descargar solo el GeoJSON para la declaración (UE)", exportar.geojson_eudr(gdf),
                       file_name="parcelas_eudr.geojson", mime="application/geo+json")
    if st.button("Borrar mis datos de esta sesión"):
        st.session_state.parcelas = None
        st.success("Listo: se borraron.")


# ---------- navegación ----------

iniciar()
css()
PAGINAS = {
    "inicio": st.Page(pagina_inicio, title="Inicio", icon=":material/home:", default=True, url_path="inicio"),
    "ingresar": st.Page(pagina_ingresar, title="1. Ingresar parcelas", icon=":material/edit_location_alt:",
                        url_path="ingresar"),
    "resultados": st.Page(pagina_resultados, title="2. Resultados", icon=":material/satellite_alt:",
                          url_path="resultados"),
    "tablero": st.Page(pagina_tablero, title="3. Tablero y visitas", icon=":material/dashboard:", url_path="tablero"),
    "informe": st.Page(pagina_informe, title="4. Informe para el comprador", icon=":material/description:",
                       url_path="informe"),
    "guia": st.Page(pagina_guia, title="Guía EUDR", icon=":material/menu_book:", url_path="guia"),
    "datos": st.Page(pagina_datos, title="Sus datos", icon=":material/lock:", url_path="datos"),
}
navegacion = st.navigation(list(PAGINAS.values()), position="top")
with st.sidebar:
    st.markdown("**Chacra Clara**")
    st.toggle("Modo ligero (sin imágenes satelitales)", key="ligero",
              help="Para celulares con poca señal: quita las imágenes de fondo y las capas raster.")
navegacion.run()
st.markdown('<div class="pie">Chacra Clara · proyecto académico (Q-Lab PUCP, 2026) · Datos: JRC, UMD/Hansen, '
            'GLAD-S2, Impact Observatory, ESA WorldCover, Geobosques (MINAM), SERNANP, Copernicus Sentinel-2 · '
            'Herramienta de tamizaje, no certificación oficial.</div>', unsafe_allow_html=True)
