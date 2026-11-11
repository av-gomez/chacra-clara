"""Descargas: GeoJSON para la declaración de debida diligencia, ficha PDF por productor,
reporte PDF de la cooperativa y un ZIP con TODOS los datos (la cooperativa es dueña de sus datos)."""
import io
import json
import zipfile
from datetime import date

from fpdf import FPDF
from shapely.geometry import Point, mapping

from chacra.estado import ESTADOS
from chacra.formato import ha, num, pct
from chacra.rutas import RAIZ

FUENTES = RAIZ / "assets" / "fuentes"
CAFE = (59, 42, 32)
GRIS = (90, 84, 78)
AVISO = ("Herramienta de tamizaje y apoyo a la debida diligencia. No es una certificación oficial: "
         "el resultado final lo valida un técnico.")


def _redondear(coordenadas, decimales=6):
    """Redondea a 6 decimales (unos 11 cm), la precisión que pide la EUDR."""
    if isinstance(coordenadas, (int, float)):
        return round(coordenadas, decimales)
    return [_redondear(c, decimales) for c in coordenadas]


def geojson_eudr(parcelas, pais="PE"):
    """FeatureCollection en WGS84 con 6 decimales, como la acepta el Sistema de Información de la UE.

    Propiedades según la descripción del archivo GeoJSON de la Comisión Europea:
    ProducerName, ProducerCountry, ProductionPlace y Area (en ha; obligatoria para los puntos).
    El nombre del productor se reemplaza por su código: la cooperativa decide si lo completa.
    """
    features = []
    for _, fila in parcelas.iterrows():
        geom = mapping(fila.geometry)
        geom["coordinates"] = _redondear(geom["coordinates"])
        propiedades = {
            "ProducerName": fila["codigo_productor"],
            "ProducerCountry": pais,
            "ProductionPlace": fila["codigo_parcela"],
        }
        if isinstance(fila.geometry, Point):
            propiedades["Area"] = round(float(fila.get("area_declarada_ha") or 0), 2)
        features.append({"type": "Feature", "properties": propiedades, "geometry": geom})
    return json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1)


def geojson_completo(parcelas):
    """GeoJSON con el resultado del tamizaje (para la cooperativa, no para la UE)."""
    columnas = [c for c in parcelas.columns if c not in ("errores", "avisos", "analisis")]
    copia = parcelas[columnas].copy()
    for c in copia.columns:
        if copia[c].dtype == object and c != "geometry":
            copia[c] = copia[c].astype(str)
    return copia.to_json(ensure_ascii=False, indent=1)


class Documento(FPDF):
    def __init__(self, titulo):
        super().__init__(format="A4")
        self.titulo = titulo
        self.add_font("Public", "", str(FUENTES / "PublicSans-Regular.ttf"))
        self.add_font("Public", "B", str(FUENTES / "PublicSans-Bold.ttf"))
        self.set_auto_page_break(True, margin=18)
        self.set_margins(18, 16, 18)
        self.set_title(titulo)
        self.set_lang("es-PE")
        self.set_author("Chacra Clara")

    def header(self):
        self.set_font("Public", "B", 10)
        self.set_text_color(*CAFE)
        self.cell(0, 6, "Chacra Clara", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 190, 175)
        self.line(18, self.get_y() + 1, 192, self.get_y() + 1)
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Public", "", 7.5)
        self.set_text_color(*GRIS)
        self.multi_cell(0, 3.5, f"{AVISO}  ·  Página {self.page_no()}", align="C")

    def titulo_seccion(self, texto):
        self.ln(2)
        self.set_font("Public", "B", 12)
        self.set_text_color(*CAFE)
        self.cell(0, 7, texto, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Public", "", 10)
        self.set_text_color(30, 30, 30)

    def parrafo(self, texto, alto=5):
        self.set_font("Public", "", 10)
        self.multi_cell(0, alto, texto, new_x="LMARGIN", new_y="NEXT")


def ficha_pdf(fila, analisis, imagenes=None):
    """Ficha de una parcela: estado, evidencia por fuente, qué hacer y, si hay, antes y después."""
    estado = ESTADOS[analisis["estado"]]
    doc = Documento(f"Ficha de parcela {fila['codigo_parcela']}")
    doc.add_page()
    doc.set_font("Public", "B", 18)
    doc.set_text_color(*CAFE)
    doc.cell(0, 10, f"Parcela {fila['codigo_parcela']}", new_x="LMARGIN", new_y="NEXT")
    doc.set_font("Public", "", 10)
    doc.set_text_color(*GRIS)
    doc.cell(0, 5, f"Productor: {fila['codigo_productor']}  ·  Cultivo: {fila['cultivo']}  ·  "
                   f"Revisado el {date.today():%d/%m/%Y}", new_x="LMARGIN", new_y="NEXT")
    doc.ln(3)

    # Estado: recuadro con ícono en texto, nombre y color (nunca solo color)
    doc.set_fill_color(*[int(estado["fondo"][i:i + 2], 16) for i in (1, 3, 5)])
    doc.set_text_color(*[int(estado["color"][i:i + 2], 16) for i in (1, 3, 5)])
    doc.set_font("Public", "B", 14)
    marca = {"sin": "[OK]", "revisar": "[!]", "posible": "[X]"}[analisis["estado"]]
    doc.cell(0, 11, f"  {marca}  {estado['texto']}   (confianza {analisis['confianza']})",
             fill=True, new_x="LMARGIN", new_y="NEXT")
    doc.set_text_color(30, 30, 30)
    doc.ln(1)
    doc.parrafo(estado["que_hacer"])

    doc.titulo_seccion("Por qué")
    for razon in analisis["razones"]:
        doc.parrafo(f"•  {razon}")

    doc.titulo_seccion("Evidencia por fuente")
    doc.set_fill_color(241, 233, 220)
    doc.set_font("Public", "", 9)
    with doc.table(col_widths=(62, 22, 30, 60), text_align=("LEFT", "LEFT", "RIGHT", "LEFT"),
                   line_height=5.5) as tabla:
        tabla.row(["Fuente", "Sensor", "Pérdida en bosque JRC 2020 (ha)", "Hectáreas por año"])
        for e in analisis["evidencias"]:
            if not e["disponible"]:
                tabla.row([e["fuente"], e["sensor"], "sin datos", ""])
                continue
            if e.get("sin_datos_periodo"):
                tabla.row([e["fuente"], e["sensor"], "sin datos para ese periodo", f"cubre hasta {e['cubre_hasta']}"])
                continue
            anios = "; ".join(f"{a}: {num(h)}" for a, h in sorted(e["anios"].items())) or "—"
            tabla.row([e["fuente"], e["sensor"], num(e["perdida_en_bosque_ha"]), anios])
    doc.ln(2)
    nat = analisis.get("natural", {})
    doc.parrafo(f"Área analizada: {ha(analisis['area_analizada_ha'])}. Cobertura de bosque 2020 según el mapa JRC "
                f"(no vinculante): {ha(analisis['bosque_2020_ha'])} ({pct(analisis['bosque_2020_pct'])})."
                + (f" Bosque natural 2020 (Natural Forests of the World): {ha(nat.get('bosque_natural_2020_ha', 0))}."
                   if nat.get("disponible") else "")
                + (f" Altura del dosel 2020: {num(nat['altura_dosel_2020_m'], 0)} m."
                   if nat.get("altura_dosel_2020_m") is not None else ""))
    doc.parrafo(f"Área en que coinciden los sensores: {ha(analisis['perdida_acordada_ha'])}. Se calcula como la "
                f"INTERSECCIÓN entre la pérdida vista por Landsat (Hansen o Geobosques: "
                f"{ha(analisis.get('perdida_landsat_ha', 0))}) y la vista por Sentinel-2 (GLAD-S2 o Impact Observatory), "
                "con una tolerancia de un píxel (10 m) porque Landsat usa píxeles de 30 m. Nunca supera lo que ve "
                "Landsat. Hansen y Geobosques usan el mismo satélite y cuentan como una sola confirmación.")
    if analisis.get("legalidad"):
        doc.titulo_seccion("Alertas de legalidad (capas del SERNANP)")
        for alerta in analisis["legalidad"]:
            doc.parrafo(f"•  {alerta}")

    if imagenes:
        doc.titulo_seccion("Sentinel-2: antes (2020) y después (2025)")
        y = doc.get_y()
        doc.image(imagenes["antes"], x=18, y=y, w=62, alt_text="Imagen satelital de la parcela en 2020")
        doc.image(imagenes["despues"], x=86, y=y, w=62, alt_text="Imagen satelital de la parcela en 2025")
        doc.set_y(y + 63)
        doc.set_font("Public", "", 8)
        doc.cell(0, 4, "Contorno amarillo: la parcela. Fuente: Copernicus Sentinel-2 L2A (ESA), mediana de la "
                       "estación seca.", new_x="LMARGIN", new_y="NEXT")

    doc.titulo_seccion("Qué verificar en campo")
    for paso in verificaciones(analisis):
        doc.parrafo(f"•  {paso}")
    return bytes(doc.output())


def verificaciones(analisis):
    """Lista de lo que el técnico debe verificar y qué evidencia recoger, según el caso."""
    pasos = []
    if analisis["estado"] == "sin":
        pasos.append("Confirmar con el productor que el contorno es correcto (caminar el lindero si hay dudas).")
        pasos.append("Verificar la legalidad: documento de posesión o propiedad, permisos y que no haya conflictos "
                     "con terceros.")
        pasos.append("Guardar esta ficha y el GeoJSON en el expediente de debida diligencia.")
        return pasos
    if analisis.get("renovacion_anio"):
        pasos.append(f"Confirmar la renovación declarada ({analisis['renovacion_anio']}): plantas nuevas en hileras, "
                     "tocones de café viejo y facturas o registros de plantones.")
    pasos.append("Tomar fotos con fecha y ubicación (GPS activado) de la zona marcada y de los cuatro lados.")
    pasos.append("Preguntar al productor qué había antes de 2021 en esa parte y desde cuándo la cultiva.")
    if analisis["bosque_2020_pct"] > 60:
        pasos.append("Revisar si es café o cacao bajo sombra: contar árboles de sombra y medir su altura.")
    if analisis["perdida_chacra_2020_pct"] >= 50:
        pasos.append("Buscar señales de renovación, poda de sombra o quema de una chacra que ya existía "
                     "(tocones viejos, plantas de café nuevas en hileras).")
    pasos.append("Conseguir una imagen de antes de 2021 (Google Earth histórico, fotos propias, constancia de "
                 "posesión) que muestre el uso de la tierra.")
    pasos.append("Registrar el testimonio del productor y de un vecino o autoridad local.")
    return pasos


def reporte_cooperativa_pdf(nombre, parcelas, resumen):
    """Reporte de toda la cooperativa: conteos, volumen exportable y lista de parcelas."""
    doc = Documento(f"Reporte de {nombre}")
    doc.add_page()
    doc.set_font("Public", "B", 18)
    doc.set_text_color(*CAFE)
    doc.cell(0, 10, f"Reporte EUDR: {nombre}", new_x="LMARGIN", new_y="NEXT")
    doc.set_font("Public", "", 10)
    doc.set_text_color(*GRIS)
    doc.cell(0, 5, f"Generado el {date.today():%d/%m/%Y} con Chacra Clara", new_x="LMARGIN", new_y="NEXT")
    doc.set_text_color(30, 30, 30)
    doc.titulo_seccion("Resumen")
    doc.parrafo(f"{resumen['total']} parcelas analizadas: {resumen['sin']} sin deforestación detectada, "
                f"{resumen['revisar']} por revisar y {resumen['posible']} con posible deforestación después de 2020.")
    e = resumen["por_estado"]
    doc.parrafo(f"Volumen estimado en parcelas sin deforestación detectada: {pct(e['sin']['pct_kg'])} "
                f"({num(e['sin']['kg'], 0)} de {num(resumen['kg_total'], 0)} kg al año); su legalidad está pendiente "
                f"de verificar. Valor de exportación en riesgo (revisar y posible deforestación): "
                f"US$ {num(resumen['usd_en_riesgo'], 0)} al año.")
    doc.parrafo("Supuestos: rendimiento café 671 kg/ha (JNC 2025) y cacao 678 kg/ha (Recursos 2026) cuando no hay "
                "producción declarada; precio café US$ 7,30/kg (US$ 336 por quintal FOB 2025, Agraria.pe) y cacao "
                "US$ 8,11/kg (CIEN-ADEX 2025).")
    doc.parrafo(f"La EUDR rige para importadores y comerciantes de la UE desde el 30/12/2026 (grandes y medianos, "
                f"faltan {resumen['dias_grandes']} días) y el 30/06/2027 (micro y pequeños). La cooperativa entrega la "
                "evidencia cuando su comprador la pide.")
    doc.titulo_seccion("Parcelas")
    doc.set_fill_color(241, 233, 220)
    doc.set_font("Public", "", 9)
    with doc.table(col_widths=(28, 24, 18, 52, 20, 22), line_height=5,
                   text_align=("LEFT", "LEFT", "RIGHT", "LEFT", "LEFT", "RIGHT")) as tabla:
        tabla.row(["Parcela", "Productor", "Área (ha)", "Estado", "Confianza", "Coinciden (ha)"])
        for _, fila in parcelas.iterrows():
            a = fila["analisis"]
            if not a or a.get("error"):
                tabla.row([fila["codigo_parcela"], fila["codigo_productor"], "", "Fuera de zona", "", ""])
                continue
            tabla.row([fila["codigo_parcela"], fila["codigo_productor"], num(a["area_analizada_ha"]),
                       ESTADOS[a["estado"]]["texto"], a["confianza"], num(a["perdida_acordada_ha"])])
    return bytes(doc.output())


def zip_todos_los_datos(parcelas, resumen, extra=None):
    """Todo lo que la cooperativa cargó y obtuvo, en formatos abiertos (CSV, GeoJSON, JSON)."""
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEAME.txt", "Datos de su cooperativa exportados de Chacra Clara.\n"
                               "Son suyos: puede llevarlos a otra herramienta cuando quiera.\n"
                               "parcelas_eudr.geojson: listo para la declaración de debida diligencia.\n"
                               "parcelas_resultado.geojson y parcelas.csv: resultado del tamizaje.\n"
                               "analisis.json: la evidencia completa por fuente.\n")
        z.writestr("parcelas_eudr.geojson", geojson_eudr(parcelas))
        z.writestr("parcelas_resultado.geojson", geojson_completo(parcelas))
        tabla = parcelas.drop(columns=["geometry", "analisis"], errors="ignore").copy()
        tabla["wkt"] = parcelas.geometry.to_wkt(rounding_precision=6)
        z.writestr("parcelas.csv", tabla.to_csv(index=False))
        analisis = {f["codigo_parcela"]: f["analisis"] for _, f in parcelas.iterrows()}
        z.writestr("analisis.json", json.dumps(analisis, ensure_ascii=False, indent=1, default=str))
        z.writestr("resumen.json", json.dumps(resumen, ensure_ascii=False, indent=1, default=str))
        for nombre, contenido in (extra or {}).items():
            z.writestr(nombre, contenido)
    return memoria.getvalue()
