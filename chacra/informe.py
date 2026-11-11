"""Informe de riesgo para el comprador europeo, en español y en inglés (sesión 08: LLM con salida estructurada).

Dos modos:
  - PLANTILLA (por defecto, sin internet ni clave): arma el informe con reglas fijas a partir de los números.
  - LLM (opcional): Claude redacta el resumen. La respuesta se valida contra el esquema InformeComprador
    (Pydantic). Los números NO los inventa el modelo: se le pasan calculados y se vuelven a escribir
    desde los datos después de validar.
Tope de gasto: LLM_TOPE_USD por sesión de la app (por defecto 0.50 USD). Al llegar al tope, usa la plantilla.
"""
import json
import os
from typing import Literal

from pydantic import BaseModel, Field

from chacra.formato import num, pct

MODELO = os.getenv("LLM_MODELO", "claude-opus-5-5")
# Dólares por millón de tokens (entrada, salida). Fuente: precios públicos de Anthropic, noviembre de 2026.
PRECIOS = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}


class Hallazgo(BaseModel):
    parcela: str
    estado: Literal["sin", "revisar", "posible"]
    explicacion_es: str = Field(description="Una frase en español claro")
    explanation_en: str = Field(description="One sentence in plain English")


class InformeComprador(BaseModel):
    nivel_riesgo: Literal["bajo", "medio", "alto"]
    resumen_es: str = Field(description="3 a 5 frases en español, sin jerga")
    summary_en: str = Field(description="3 to 5 sentences in English for an EU importer")
    hallazgos: list[Hallazgo]
    mitigacion_es: list[str] = Field(description="Acciones concretas de mitigación de riesgo")
    mitigation_en: list[str]
    limitaciones_es: list[str]
    limitations_en: list[str]


def datos_para_informe(nombre, parcelas, resumen):
    filas = []
    for _, f in parcelas.iterrows():
        a = f["analisis"]
        if not a or a.get("error"):
            continue
        filas.append({"parcela": f["codigo_parcela"], "cultivo": f["cultivo"], "estado": a["estado"],
                      "confianza": a["confianza"], "area_ha": a["area_analizada_ha"], "motivo": a.get("motivo", ""),
                      "bosque_2020_ha": a["bosque_2020_ha"], "perdida_acordada_ha": a["perdida_acordada_ha"],
                      "anio": a["anio_principal"], "razones": a["razones"], "legalidad": a.get("legalidad", [])})
    return {"organizacion": nombre, "pais": "Perú", "resumen": resumen, "parcelas": filas}


def nivel(resumen):
    if resumen["posible"] > 0:
        return "alto"
    if resumen["revisar"] > 0:
        return "medio"
    return "bajo"


MOTIVOS_EN = {
    "Renovación declarada en el año de la pérdida": "coffee renewal declared in the year of the loss",
    "Solo un tipo de sensor": "only one sensor type detects the loss",
    "Pérdida marginal": "marginal loss",
    "Probable café o cacao bajo sombra": "probable shade-grown coffee or cocoa (renewal or pruning)",
    "La pérdida cae en chacra existente": "loss falls on existing farmland",
    "Sin capa de bosque natural para confirmar": "no natural-forest layer to confirm",
    "Pérdida de árboles en chacra existente": "tree loss on existing farmland (possible renewal or pruning)",
}


def informe_plantilla(datos):
    """Informe sin API: reglas fijas, siempre disponible."""
    r = datos["resumen"]
    riesgo = nivel(r)
    hallazgos = []
    for p in datos["parcelas"]:
        if p["estado"] == "sin":
            continue
        if p["estado"] == "posible":
            es = (f"Dos tipos de sensor (Landsat y Sentinel-2) coinciden en {num(p['perdida_acordada_ha'])} ha de pérdida "
                  f"en bosque natural después de 2020 (año principal: {p['anio']}). Visita recomendada con prioridad "
                  "alta; excluida del envío hasta verificar en campo.")
            en = (f"Two sensor types (Landsat and Sentinel-2) agree on {p['perdida_acordada_ha']:.2f} ha of loss in "
                  f"natural forest after 2020 (main year: {p['anio']}). High-priority field visit recommended; "
                  "excluded from shipment until verified.")
        else:
            es = f"Revisar: {p['motivo'].lower()}. Visita recomendada."
            en = f"Under review: {MOTIVOS_EN.get(p['motivo'].split(' (')[0], 'inconclusive evidence')}. Field visit recommended."
        hallazgos.append(Hallazgo(parcela=p["parcela"], estado=p["estado"], explicacion_es=es, explanation_en=en))
    e = r["por_estado"]
    return InformeComprador(
        nivel_riesgo=riesgo,
        resumen_es=(f"{datos['organizacion']} revisó {r['total']} parcelas de café y cacao en el Perú con fuentes "
                    f"satelitales abiertas de dos tipos de sensor y capas de bosque natural. {e['sin']['parcelas']} "
                    f"parcelas ({pct(e['sin']['pct_kg'])} del volumen estimado) no muestran deforestación después del "
                    f"31/12/2020; su legalidad está pendiente de verificar. {e['revisar']['parcelas']} están en revisión "
                    f"y {e['posible']['parcelas']} muestran posible deforestación ({pct(e['posible']['pct_kg'])} del "
                    f"volumen). Valor de exportación en riesgo: US$ {num(r['usd_en_riesgo'], 0)} al año."),
        summary_en=(f"{datos['organizacion']} screened {r['total']} coffee and cocoa plots in Peru (standard-risk country "
                    f"under Regulation (EU) 2023/1115) with open satellite data from two sensor types and natural-forest "
                    f"layers. {e['sin']['parcelas']} plots ({e['sin']['pct_kg']:.0f}% of estimated volume) show no "
                    f"deforestation after 31 Dec 2020; legality is still to be verified. {e['revisar']['parcelas']} are "
                    f"under review and {e['posible']['parcelas']} show possible deforestation "
                    f"({e['posible']['pct_kg']:.0f}% of volume). Export value at risk: US$ {r['usd_en_riesgo']:,.0f} per year."),
        hallazgos=hallazgos,
        mitigacion_es=["Solo se declaran lotes de parcelas sin deforestación detectada.",
                       "Las parcelas en revisión o con posible deforestación se visitan con fotos georreferenciadas "
                       "y testimonio del productor antes de cualquier envío.",
                       "Se conserva el expediente (fichas, GeoJSON y evidencia) por al menos cinco años."],
        mitigation_en=["Only lots from plots with no deforestation detected are declared.",
                       "Plots under review or with possible deforestation are field-verified (geotagged photos, "
                       "producer statement) before any shipment.",
                       "The due diligence file (plot sheets, GeoJSON, evidence) is kept for at least five years."],
        limitaciones_es=["Es un tamizaje satelital, no una certificación: un técnico valida el resultado final.",
                         "El café y cacao bajo sombra pueden verse como bosque en los satélites.",
                         "No evalúa por completo la legalidad (tenencia, derechos laborales ni consulta previa)."],
        limitations_en=["This is satellite screening, not a certification: a technician validates the final result.",
                        "Shade-grown coffee and cocoa can look like forest in satellite data.",
                        "Legality (land tenure, labour rights, free prior informed consent) is not fully assessed."],
    )


def informe_llm(datos, gastado_usd, tope_usd):
    """Pide a Claude el informe validado con el esquema. Devuelve (informe, costo_usd)."""
    import anthropic
    if gastado_usd >= tope_usd:
        raise RuntimeError(f"Se alcanzó el tope de gasto de {num(tope_usd)} USD en esta sesión.")
    cliente = anthropic.Anthropic()
    instrucciones = (
        "Eres analista de debida diligencia del Reglamento (UE) 2023/1115 (EUDR). Redacta un informe de riesgo para "
        "un importador europeo a partir de los datos JSON. Reglas: usa SOLO los números del JSON, no inventes cifras "
        "ni fuentes; di que es un tamizaje satelital y no una certificación; frases cortas; el texto en español debe "
        "entenderlo un gerente de cooperativa sin formación técnica. Incluye un hallazgo por cada parcela que no esté "
        "en estado 'sin'.")
    respuesta = cliente.messages.parse(
        model=MODELO,
        max_tokens=4000,
        output_config={"effort": "low"},
        system=instrucciones,
        messages=[{"role": "user", "content": json.dumps(datos, ensure_ascii=False, default=str)}],
        output_format=InformeComprador,
    )
    entrada, salida = PRECIOS.get(MODELO, (4.00, 20.00))
    costo = (respuesta.usage.input_tokens * entrada + respuesta.usage.output_tokens * salida) / 1_000_000
    informe = respuesta.parsed_output
    # Los estados de cada parcela se fuerzan desde los datos, por si el modelo se equivoca
    estados = {p["parcela"]: p["estado"] for p in datos["parcelas"]}
    informe.hallazgos = [h for h in informe.hallazgos if h.parcela in estados]
    for h in informe.hallazgos:
        h.estado = estados[h.parcela]
    informe.nivel_riesgo = nivel(datos["resumen"])
    return informe, costo
