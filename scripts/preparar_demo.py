"""Arma la cooperativa de demo (datos/parcelas/demo.geojson) con candidatas revisadas a ojo.

- Ubicaciones REALES (salen de scripts/elegir_parcelas.py y se revisaron con Sentinel-2 antes y después).
- Productores FICTICIOS: solo códigos, sin nombres ni datos personales.
- Producción: área x rendimiento promedio citado (café 671 kg/ha, JNC 2025; cacao 678 kg/ha, Recursos 2026), con variación de ±20 %.
También escribe audios/notas.json con el texto de la nota de voz de cada parcela de demo.

Uso: python scripts/preparar_demo.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np

import sys
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from chacra import satelite, voz  # noqa: E402

# candidata -> (código de parcela, cultivo, ¿entregar como punto?)
ELEGIDAS = {
    "SAN-PER-0": ("SAN-01", "café", False),
    "SAN-INT-12": ("SAN-02", "café", False),
    "SAN-CHA-19": ("SAN-03", "café", True),
    "SAN-UNA-8": ("SAN-04", "café", False),
    "SAN-SOM-27": ("SAN-05", "café", False),
    "SAN-PER-4": ("SAN-06", "café", False),
    "SAN-CHA-22": ("SAN-07", "café", False),
    "CAR-PER-36": ("CAR-01", "cacao", False),
    "CAR-INT-43": ("CAR-02", "cacao", True),
    "CAR-REN-56": ("CAR-03", "café", False),
    "CAR-SOM-52": ("CAR-04", "cacao", False),
    "CAR-UNA-40": ("CAR-05", "café", False),
    "ALT-PER-61": ("AMY-01", "café", False),
    "ALT-INT-70": ("AMY-02", "café", False),
    "ALT-CHA-77": ("AMY-03", "café", False),
    "ALT-REN-85": ("AMY-04", "café", False),
    "ALT-UNA-69": ("AMY-05", "café", False),
    "ALT-CHA-80": ("AMY-06", "café", True),
}
from chacra.cooperativa import RENDIMIENTO_KG_HA as RENDIMIENTO  # noqa: E402  (671 y 678 kg/ha, citados)
# Año de siembra o de la última renovación declarado por la cooperativa (ficticio): muestra la regla de renovación
RENOVACION = {"SAN-06": 2024}
# Dos cooperativas ficticias: una central en Puno (Sandia y Carabaya) y una en San Martín (Alto Mayo)
COOPERATIVA = {"sandia": "puno", "carabaya": "puno", "altomayo": "sanmartin"}


def main():
    rng = np.random.default_rng(11)
    candidatas = gpd.read_file(RAIZ / "datos" / "parcelas" / "candidatas.geojson").set_index("candidata")
    filas, notas = [], {}
    for n, (candidata, (codigo, cultivo, como_punto)) in enumerate(ELEGIDAS.items(), start=1):
        c = candidatas.loc[candidata]
        area = float(gpd.GeoSeries([c.geometry], crs=4326).to_crs(gpd.GeoSeries([c.geometry], crs=4326)
                                                                   .estimate_utm_crs()).area.iloc[0] / 10_000)
        geom = c.geometry.centroid if como_punto else c.geometry
        if como_punto:
            geom = type(geom)(round(geom.x, 6), round(geom.y, 6))
        produccion = int(round(area * RENDIMIENTO[cultivo] * rng.uniform(0.8, 1.2), -1))
        filas.append({"codigo_productor": f"PR-{100 + n}", "codigo_parcela": codigo, "cultivo": cultivo,
                      "area_ha": round(area, 2), "produccion_kg_anual": produccion,
                      "anio_renovacion": RENOVACION.get(codigo), "cooperativa": COOPERATIVA[c["zona"]], "caso_esperado": c["caso_esperado"],
                      "candidata": candidata, "geometry": geom})
    gdf = gpd.GeoDataFrame(filas, crs="EPSG:4326")
    gdf.to_file(RAIZ / "datos" / "parcelas" / "demo.geojson", driver="GeoJSON")

    # Notas de voz: texto según el estado que obtiene cada parcela
    for _, f in gdf.iterrows():
        renovacion = f["anio_renovacion"] if f["anio_renovacion"] == f["anio_renovacion"] else None
        analisis = satelite.analizar(f.geometry, f["area_ha"], int(renovacion) if renovacion else None)
        notas[f["codigo_parcela"]] = voz.texto_nota(f["codigo_parcela"], f["cultivo"], analisis["estado"])
        print(f"{f['codigo_parcela']:8} {f['caso_esperado']:15} -> {analisis['estado']:8} ({analisis['confianza']})")
    ruta_notas = RAIZ / "audios" / "notas.json"
    existentes = json.loads(ruta_notas.read_text(encoding="utf-8")) if ruta_notas.exists() else {}
    existentes.update(notas)
    ruta_notas.write_text(json.dumps(existentes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(gdf)} parcelas de demo y {len(notas)} notas de voz por generar")


if __name__ == "__main__":
    main()
