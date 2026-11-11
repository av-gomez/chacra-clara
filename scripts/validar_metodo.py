"""Valida las reglas de Chacra Clara contra dos referencias y escribe docs/validacion/resultados.md.

Referencia 1, "caso buscado": el criterio con que se eligió cada lugar (scripts/elegir_parcelas.py).
  Es en parte circular, porque usa las mismas capas: sirve para comprobar que las reglas hacen lo que dicen.
Referencia 2, "revisión visual": interpretación a ojo de Sentinel-2 (2020 contra 2025, 10 m), hecha sin mirar
  el estado que da la app (docs/validacion/revision_visual.csv). Es independiente de las reglas, pero NO es
  verdad de campo: a 10 m no se ve la tala selectiva ni se distingue bien el café bajo sombra.

Uso: python scripts/validar_metodo.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from chacra import satelite  # noqa: E402

# Qué estado se espera para cada caso buscado
ESPERADO = {"perdida_clara": {"posible"}, "una_fuente": {"revisar", "sin"}, "intacto": {"sin"},
            "chacra_antigua": {"sin"}, "sombra": {"sin", "revisar"}, "renovacion": {"revisar", "sin"}}


def main():
    candidatas = gpd.read_file(RAIZ / "datos" / "parcelas" / "candidatas.geojson")
    visual = pd.read_csv(RAIZ / "docs" / "validacion" / "revision_visual.csv")
    filas = []
    for _, c in candidatas.iterrows():
        a = satelite.analizar(c.geometry)
        filas.append({"candidata": c["candidata"], "caso_buscado": c["caso_esperado"], "estado": a["estado"],
                      "confianza": a["confianza"], "perdida_acordada_ha": a["perdida_acordada_ha"]})
    res = pd.DataFrame(filas).merge(visual[["candidata", "referencia_visual", "nota"]], on="candidata")
    res["acierta_caso"] = res.apply(lambda f: f["estado"] in ESPERADO[f["caso_buscado"]], axis=1)
    res.to_csv(RAIZ / "docs" / "validacion" / "resultados.csv", index=False)

    lineas = ["# Validación del método", "",
              "Generado por `scripts/validar_metodo.py`. Cada fila es una parcela de prueba en un lugar real.", ""]
    lineas += ["## 1. Contra el caso buscado (comprueba que las reglas hacen lo que dicen)", "",
               pd.crosstab(res["caso_buscado"], res["estado"]).to_markdown(), "",
               f"Aciertos: **{res['acierta_caso'].sum()} de {len(res)}** "
               f"({100 * res['acierta_caso'].mean():.0f} %). Para «una fuente», «sombra» y «renovación» se aceptan "
               "dos estados (ver `ESPERADO` en el script).", ""]

    claras = res[res["referencia_visual"] != "dudoso"].copy()
    claras["referencia"] = claras["referencia_visual"].map(
        {"deforestacion_visible": "pérdida visible", "sin_perdida_de_bosque_visible": "sin pérdida visible"})
    tabla = pd.crosstab(claras["referencia"], claras["estado"])
    positivos = claras[claras["referencia"] == "pérdida visible"]
    negativos = claras[claras["referencia"] == "sin pérdida visible"]
    detectadas = positivos["estado"].isin(["posible", "revisar"]).sum()
    marcadas_posible = positivos["estado"].eq("posible").sum()
    falsas_posible = negativos["estado"].eq("posible").sum()
    falsas_revisar = negativos["estado"].eq("revisar").sum()
    lineas += ["## 2. Contra la revisión visual de Sentinel-2 (independiente de las reglas)", "",
               tabla.to_markdown(), "",
               f"- Pérdidas visibles: {len(positivos)}. La app las marca como «Posible deforestación» en "
               f"**{marcadas_posible}** y como «Posible» o «Revisar» en **{detectadas}** "
               f"(falsos negativos: {len(positivos) - detectadas}).",
               f"- Parcelas sin pérdida visible: {len(negativos)}. La app marca **{falsas_posible}** como «Posible "
               f"deforestación» (falsos positivos fuertes) y **{falsas_revisar}** como «Revisar» (alarmas que se "
               "resuelven con una visita).",
               f"- Casos dudosos a ojo (excluidos del cálculo): {len(res) - len(claras)}.", "",
               "### Desacuerdos con la revisión visual", "",
               "| Parcela | Caso buscado | Referencia visual | Estado de la app | Nota |", "|---|---|---|---|---|"]
    for _, f in claras.iterrows():
        mal = ((f["referencia"] == "pérdida visible" and f["estado"] == "sin")
               or (f["referencia"] == "sin pérdida visible" and f["estado"] == "posible"))
        if mal:
            lineas.append(f"| {f['candidata']} | {f['caso_buscado']} | {f['referencia']} | {f['estado']} | "
                          f"{f['nota'] if isinstance(f['nota'], str) else ''} |")
    (RAIZ / "docs" / "validacion" / "resultados.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
