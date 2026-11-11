"""Busca en los recortes lugares reales que sirvan como casos de prueba y arma parcelas de ejemplo.

Las ubicaciones son reales (zonas cafetaleras de Sandia, Carabaya y Alto Mayo); los productores son ficticios.
Cada caso se elige con un criterio de los datos y DESPUÉS se revisa a ojo con las imágenes Sentinel-2
de antes y después (scripts/hojas_revision.py). El caso esperado de cada parcela queda en 'caso_esperado'.

Casos:
  perdida_clara   bosque en 2020 (JRC) y pérdida 2021+ vista por Hansen y por otra fuente
  una_fuente      bosque en 2020 y pérdida 2021+ vista solo por Hansen
  intacto         bosque en 2020 sin ninguna pérdida y cobertura arbórea 2000 >= 90 %
  chacra_antigua  sin bosque en 2020 (JRC) y pasto/cultivo/arbustal en WorldCover 2020, sin pérdida
  sombra          mosaico de bosque y chacra: 50-90 % bosque JRC y cobertura arbórea 2000 media < 75 %
  renovacion      pérdida 2021+ (Hansen) donde en 2020 no había bosque (JRC) y WorldCover marcaba chacra

Uso: python scripts/elegir_parcelas.py  -> datos/parcelas/candidatas.geojson
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from shapely.geometry import Polygon

RAIZ = Path(__file__).resolve().parent.parent
RECORTES = RAIZ / "datos" / "recortes"
VENTANA = 15          # píxeles (~135 m de lado, ~1.8 ha)
POR_CASO = 2          # parcelas por caso y por zona
SEMILLA = 2026


def leer(zona, nombre):
    with rasterio.open(RECORTES / zona / nombre) as src:
        return src.read(1), src.transform


def bloques(arreglo, tam):
    """Promedio de cada bloque de tam x tam píxeles."""
    alto, ancho = arreglo.shape[0] // tam * tam, arreglo.shape[1] // tam * tam
    a = arreglo[:alto, :ancho].astype("float32")
    return a.reshape(alto // tam, tam, ancho // tam, tam).mean(axis=(1, 3))


def poligono_irregular(cx, cy, area_ha, rng):
    """Polígono de 6 a 8 vértices alrededor del centro, con el área aproximada pedida."""
    lado_m = np.sqrt(area_ha * 10_000)
    radio_lat = lado_m / 2 / 110_574
    radio_lon = lado_m / 2 / (111_320 * np.cos(np.radians(cy)))
    n = rng.integers(6, 9)
    angulos = np.sort(rng.uniform(0, 2 * np.pi, n))
    radios = rng.uniform(0.85, 1.25, n)
    puntos = [(round(cx + radio_lon * r * np.cos(a), 6), round(cy + radio_lat * r * np.sin(a), 6))
              for a, r in zip(angulos, radios)]
    return Polygon(puntos)


def main():
    rng = np.random.default_rng(SEMILLA)
    zonas = json.loads((RECORTES / "zonas.json").read_text(encoding="utf-8"))
    filas = []
    for zona in zonas:
        jrc, transform = leer(zona, "jrc_bosque2020.tif")
        hansen, _ = leer(zona, "hansen_perdida.tif")
        cobertura, _ = leer(zona, "hansen_cobertura2000.tif")
        wc, _ = leer(zona, "worldcover2020.tif")
        otras = np.zeros_like(jrc, dtype=bool)
        for nombre in ["alertas_perdida.tif", "io_perdida.tif", "geobosques_perdida.tif"]:
            capa, _ = leer(zona, nombre)
            otras |= (capa > 20) & (capa != 255)
        bosque = jrc == 1
        h_post = (hansen > 20) & (hansen != 255)
        alguna = h_post | otras
        chacra_wc = np.isin(wc, [20, 30, 40])
        b = {
            "bosque": bloques(bosque, VENTANA),
            "acuerdo": bloques(bosque & h_post & otras, VENTANA),
            "solo_hansen": bloques(bosque & h_post & ~otras, VENTANA),
            "otras": bloques(otras, VENTANA),
            "alguna": bloques(alguna, VENTANA),
            "cobertura": bloques(np.where(cobertura == 255, 0, cobertura), VENTANA),
            "chacra": bloques(chacra_wc, VENTANA),
            "renov": bloques(~bosque & chacra_wc & h_post, VENTANA),
        }
        criterios = {
            "perdida_clara": (b["acuerdo"] >= 0.25) & (b["bosque"] >= 0.5),
            "una_fuente": (b["solo_hansen"] >= 0.08) & (b["otras"] == 0) & (b["bosque"] >= 0.6),
            "intacto": (b["bosque"] >= 0.99) & (b["alguna"] == 0) & (b["cobertura"] >= 90),
            "chacra_antigua": (b["bosque"] <= 0.05) & (b["chacra"] >= 0.8) & (b["alguna"] == 0),
            "sombra": (b["bosque"] >= 0.5) & (b["bosque"] <= 0.9) & (b["cobertura"] < 75) & (b["alguna"] == 0)
                      & (b["chacra"] >= 0.1),
            "renovacion": (b["renov"] >= 0.08) & (b["bosque"] <= 0.1),
        }
        for caso, mascara in criterios.items():
            filas_ok, cols_ok = np.nonzero(mascara)
            print(f"{zona} {caso}: {len(filas_ok)} ventanas candidatas")
            if len(filas_ok) == 0:
                continue
            elegidas = rng.choice(len(filas_ok), size=min(POR_CASO * 3, len(filas_ok)), replace=False)
            for k in elegidas:
                fila_px = filas_ok[k] * VENTANA + VENTANA / 2
                col_px = cols_ok[k] * VENTANA + VENTANA / 2
                cx, cy = transform * (col_px, fila_px)
                area = float(rng.uniform(1.0, 3.0))
                filas.append({"zona": zona, "caso_esperado": caso, "area_objetivo_ha": round(area, 2),
                              "geometry": poligono_irregular(cx, cy, area, rng)})
    gdf = gpd.GeoDataFrame(filas, crs="EPSG:4326")
    gdf["candidata"] = [f"{z[:3].upper()}-{c[:3].upper()}-{i}" for i, (z, c) in enumerate(zip(gdf.zona, gdf.caso_esperado))]
    salida = RAIZ / "datos" / "parcelas" / "candidatas.geojson"
    salida.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(salida, driver="GeoJSON")
    print(f"{len(gdf)} candidatas -> {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
