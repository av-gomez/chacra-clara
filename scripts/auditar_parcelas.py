"""Auditoría de las parcelas de ejemplo: método anterior (versión 1) contra el método nuevo (versión 2).

Escribe docs/auditoria-parcelas.md con una fila por parcela: área, cobertura de bosque 2020 según el JRC,
bosque natural 2020, probabilidad de café o cacao, altura del dosel, pérdida por fuente y año,
estado anterior, estado nuevo y por qué cambió. El estado anterior sale de docs/validacion/estados_antes.json,
guardado antes de cambiar las reglas.

Uso: python scripts/auditar_parcelas.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from chacra import cooperativa, geometria  # noqa: E402
from chacra.estado import ESTADOS  # noqa: E402
from chacra.formato import num  # noqa: E402

CORTO = {"sin": "Sin deforestación detectada", "revisar": "Revisar", "posible": "Posible deforestación"}
ABREV = {"Hansen": "Hansen", "Geobosques": "Geobosques", "Alertas GLAD-S2": "GLAD-S2", "Impact Observatory": "IO"}

# Revisión visual con Sentinel-2 (2020 contra 2025, 10 m) de las parcelas que quedan en «Posible deforestación»
REVISION_VISUAL = {
    "SAN-01": "2020: dosel continuo con textura de bosque, sin estructura de chacra; 2025: claros y una trocha nueva. "
              "Coincide con conversión de bosque. A 10 m no se descarta del todo un cafetal antiguo muy denso, pero "
              "el dosel medía 32 m en 2020.",
    "CAR-01": "2020: bosque junto al río; 2025: parche de suelo desnudo muy brillante. **Puede ser un deslizamiento "
              "junto al río** y no una conversión a cultivo: el técnico debe verificarlo.",
    "AMY-01": "2020: vegetación arbórea (en parte más clara); 2025: pasto o cultivo uniforme. Coincide con conversión.",
}


def cargar_demo():
    datos = json.loads((RAIZ / "datos" / "parcelas" / "demo.geojson").read_text(encoding="utf-8"))
    gdf = geometria.desde_geojson(datos)
    gdf["cooperativa"] = [f["properties"]["cooperativa"] for f in datos["features"]]
    return cooperativa.analizar_todas(geometria.validar(gdf))


def perdidas(a):
    partes = []
    for e in a["evidencias"]:
        nombre = next((v for k, v in ABREV.items() if e["fuente"].startswith(k)), e["fuente"])
        if e.get("sin_datos_periodo"):
            partes.append(f"{nombre}: sin datos para el periodo")
        elif e["perdida_en_bosque_ha"] >= 0.05:
            anios = ", ".join(f"{k} {num(v)}" for k, v in sorted(e["anios"].items()) if v >= 0.05)
            partes.append(f"{nombre}: {num(e['perdida_en_bosque_ha'])} ({anios})")
    return "; ".join(partes) or "ninguna"


def por_que(antes, a):
    if antes["estado"] == a["estado"]:
        return "Sin cambio. " + a["motivo"] + "."
    return f"{a['motivo']}."


def main():
    antes = json.loads((RAIZ / "docs" / "validacion" / "estados_antes.json").read_text(encoding="utf-8"))
    gdf = cargar_demo()
    filas = ["| Parcela | Área (ha) | Bosque JRC 2020 | Bosque natural 2020 | Prob. café o cacao | Dosel 2020 | "
             "Pérdida por fuente (ha, año) | Estado anterior | Estado nuevo | Por qué |",
             "|---|---:|---:|---:|---|---:|---|---|---|---|"]
    cambios = 0
    for _, f in gdf.iterrows():
        a, n = f["analisis"], f["analisis"]["natural"]
        previo = antes[f["codigo_parcela"]]
        cambios += previo["estado"] != a["estado"]
        altura = f"{num(n['altura_dosel_2020_m'], 0)} m" if n.get("altura_dosel_2020_m") is not None else "—"
        filas.append(
            f"| {f['codigo_parcela']} | {num(a['area_analizada_ha'])} | {num(a['bosque_2020_ha'])} ha "
            f"({num(a['bosque_2020_pct'], 0)} %) | {num(n.get('bosque_natural_2020_ha', 0))} ha | sin acceso | "
            f"{altura} | {perdidas(a)} | {CORTO[previo['estado']]} | **{CORTO[a['estado']]}** | {por_que(previo, a)} |")
    lineas = [
        "# Auditoría de las parcelas de ejemplo",
        "",
        "Generado por `scripts/auditar_parcelas.py`. Compara el método anterior (versión 1: JRC como verdad y fuentes "
        "contadas por nombre) con el nuevo (versión 2: bosque natural, altura del dosel, fuentes por tipo de sensor, "
        "periodos sin datos y renovación declarada). Ver «Método» en el README.",
        "",
        f"**{cambios} de {len(gdf)} parcelas cambiaron de estado.** Las 12 primeras (SAN y CAR) son la cooperativa de "
        "ejemplo de Puno; las 6 AMY, la de San Martín. Las ubicaciones son reales y fueron elegidas a propósito para "
        "cubrir todos los casos: es un escenario de prueba, no una cooperativa típica.",
        "",
        "- **Bosque JRC 2020:** cobertura de bosque según el mapa de referencia de la UE (no vinculante).",
        "- **Bosque natural 2020:** píxeles con probabilidad ≥ 50 % en Natural Forests of the World 2020 (WRI y "
        "Google DeepMind). Ojo: en Sandia y Carabaya marca el 83 % al 96 % de toda la zona como natural, cafetales "
        "incluidos; sus autores advierten que falla con agroforestería bajo sombra. Por eso se usa también la altura.",
        "- **Prob. café o cacao:** los modelos del Forest Data Partnership están en un bucket de Google que exige una "
        "cuenta con facturación (*requester pays*); no hubo acceso anónimo.",
        "- **Dosel 2020:** altura promedio del dosel en 2020 (ETH Global Canopy Height, 10 m) donde hubo pérdida (o en "
        "el bosque JRC de la parcela si no hubo). Menos de 20 m = probable sombra de cultivo.",
        "- **Pérdida por fuente:** hectáreas de pérdida después de 2020 dentro del bosque JRC, por año.",
        "",
    ] + filas + ["", "## Revisión visual de las parcelas que quedan en «Posible deforestación»", ""]
    for _, f in gdf[gdf["estado"] == "posible"].iterrows():
        lineas.append(f"- **{f['codigo_parcela']}:** {REVISION_VISUAL.get(f['codigo_parcela'], 'Pendiente.')}")
    lineas += ["", "Imágenes: Copernicus Sentinel-2 L2A, mediana de junio a octubre de 2020 y de 2025. A 10 m la "
               "revisión visual no reemplaza la visita de campo."]
    salida = RAIZ / "docs" / "auditoria-parcelas.md"
    salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    _ = ESTADOS


if __name__ == "__main__":
    main()
