"""Lógica del tablero de la cooperativa: analizar todas las parcelas, resumir y ordenar las visitas."""
import math
from datetime import date

import geopandas as gpd
import pandas as pd

from chacra import satelite
from chacra.estado import ESTADOS
from chacra.rutas import RECORTES

FECHA_GRANDES = date(2026, 12, 30)    # operadores grandes y medianos (Reglamento (UE) 2025/2650)
FECHA_PEQUENOS = date(2027, 6, 30)    # micro y pequeñas empresas
PESO_RIESGO = {"posible": 3, "revisar": 2, "sin": 0}


def alertas_legalidad(geom, zona):
    """Superposición con áreas protegidas, zonas de amortiguamiento, comunidades nativas o BPP."""
    ruta = RECORTES / zona / "legalidad.geojson"
    if not ruta.exists():
        return []
    capas = gpd.read_file(ruta)
    alertas = []
    for _, capa in capas.iterrows():
        if capa.geometry is not None and capa.geometry.intersects(geom):
            alertas.append(f"Se superpone con {capa['tipo']}: {capa['nombre']}. Verifique permisos y derechos de terceros.")
    return alertas


def analizar_todas(parcelas):
    """Agrega a cada parcela su análisis satelital y las columnas que usan los mapas y tablas."""
    gdf = parcelas.copy()
    analisis, estados, textos, confianzas, zonas = [], [], [], [], []
    for _, fila in gdf.iterrows():
        if not fila.get("valida", True):
            a = {"error": "Geometría con errores: corríjala antes de analizar."}
        else:
            a = satelite.analizar(fila.geometry, fila.get("area_declarada_ha"))
            if a.get("zona"):
                a["legalidad"] = alertas_legalidad(fila.geometry, a["zona"])
        analisis.append(a)
        estado = a.get("estado")
        estados.append(estado)
        textos.append(ESTADOS[estado]["texto"] if estado else None)
        confianzas.append(a.get("confianza"))
        zonas.append(a.get("zona"))
    gdf["analisis"] = analisis
    gdf["estado"] = estados
    gdf["texto_estado"] = textos
    gdf["confianza"] = confianzas
    gdf["zona"] = zonas
    return gdf


def resumen(gdf, hoy=None):
    hoy = hoy or date.today()
    analizadas = gdf[gdf["estado"].notna()]
    kg = pd.to_numeric(analizadas["produccion_kg_anual"], errors="coerce").fillna(0)
    kg_listos = float(kg[analizadas["estado"] == "sin"].sum())
    kg_total = float(kg.sum())
    return {
        "total": int(len(analizadas)),
        "sin": int((analizadas["estado"] == "sin").sum()),
        "revisar": int((analizadas["estado"] == "revisar").sum()),
        "posible": int((analizadas["estado"] == "posible").sum()),
        "fuera": int(gdf["estado"].isna().sum()),
        "kg_listos": kg_listos,
        "kg_total": kg_total,
        "pct_volumen": 100 * kg_listos / kg_total if kg_total > 0 else 0.0,
        "dias_grandes": (FECHA_GRANDES - hoy).days,
        "dias_pequenos": (FECHA_PEQUENOS - hoy).days,
    }


def centroides(gdf):
    """Centro de cada parcela calculado en metros (UTM) y devuelto en grados."""
    utm = gdf.estimate_utm_crs()
    return gdf.to_crs(utm).centroid.to_crs("EPSG:4326")


def distancia_km(a, b):
    """Distancia en línea recta (fórmula del haversine). Por camino suele ser mayor."""
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


# Pueblo desde donde sale el técnico en cada zona (coordenadas aproximadas de la plaza)
BASES = {"sandia": ("San Juan del Oro", (-14.2219, -69.1517)),
         "carabaya": ("San Gabán", (-13.4366, -70.4028)),
         "altomayo": ("Moyobamba", (-6.0342, -76.9717))}


def prioridades(gdf):
    """Orden de visitas por zona: primero mayor riesgo y, dentro del mismo riesgo, la más cercana a la anterior.

    Cada zona tiene su propia ruta, que sale de su pueblo base: no tiene sentido ir y volver entre valles.
    Las distancias son en línea recta; por camino suelen ser mayores.
    """
    pendientes = gdf[gdf["estado"].isin(["posible", "revisar"])].copy()
    if len(pendientes) == 0:
        return pd.DataFrame()
    centros = centroides(pendientes)
    pendientes["lat"] = centros.y
    pendientes["lon"] = centros.x
    pendientes["perdida_ha"] = pendientes["analisis"].apply(lambda a: a["perdida_acordada_ha"])
    orden = []
    for zona, de_zona in pendientes.groupby("zona"):
        nombre_base, actual = BASES.get(zona, ("centro de las parcelas", (de_zona["lat"].mean(), de_zona["lon"].mean())))
        for estado in ["posible", "revisar"]:
            grupo = de_zona[de_zona["estado"] == estado].copy()
            while len(grupo):
                grupo["dist"] = grupo.apply(lambda f: distancia_km(actual, (f["lat"], f["lon"])), axis=1)
                elegida = grupo.sort_values(["dist", "perdida_ha"], ascending=[True, False]).iloc[0]
                orden.append({"zona": zona, "base": nombre_base, "orden": len(orden) + 1,
                              "codigo_parcela": elegida["codigo_parcela"],
                              "codigo_productor": elegida["codigo_productor"], "estado": elegida["texto_estado"],
                              "perdida_ha": round(elegida["perdida_ha"], 2),
                              "km_desde_anterior": round(elegida["dist"], 1),
                              "lat": round(elegida["lat"], 6), "lon": round(elegida["lon"], 6)})
                actual = (elegida["lat"], elegida["lon"])
                grupo = grupo.drop(index=elegida.name)
    return pd.DataFrame(orden)
