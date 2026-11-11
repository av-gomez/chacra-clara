"""Cruce de cada parcela con los recortes satelitales (raster, sesión 07 del curso).

Todos los recortes de una zona están en la MISMA grilla (la de ESA WorldCover, 1/12000 de grado,
unos 9 m), así que un píxel (fila, columna) es el mismo lugar en todas las capas. Eso permite:
  - medir cuánto bosque había en 2020 dentro de la parcela (JRC GFC2020),
  - medir la pérdida de cada fuente solo donde había bosque en 2020,
  - medir dónde coinciden dos o más fuentes, píxel a píxel.

Igual que en la sesión 07: se recorta con rasterio.mask, se respeta el 'nodata' y las áreas se
calculan en metros (el tamaño del píxel en metros depende de la latitud), no en grados.
"""
import json
import math

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point, mapping

from chacra.estado import Evidencia, clasificar
from chacra.rutas import RECORTES

ANIO_CORTE = 2020          # fecha de corte de la EUDR: 31 de diciembre de 2020
CLASES_NO_BOSQUE_WC = [20, 30, 40, 50, 60]   # WorldCover: arbustal, pasto, cultivo, urbano, suelo desnudo
NODATA = 255

# Fuentes de pérdida. 'archivo' guarda el año de pérdida menos 2000 (21 = 2021); 0 = sin pérdida.
FUENTES_PERDIDA = [
    {"clave": "hansen", "nombre": "Hansen/UMD (Landsat, 30 m)", "archivo": "hansen_perdida.tif"},
    {"clave": "alertas", "nombre": "Alertas GLAD-S2 (Sentinel-2, 10 m)", "archivo": "alertas_perdida.tif"},
    {"clave": "io", "nombre": "Impact Observatory (Sentinel-2, 10 m)", "archivo": "io_perdida.tif"},
    {"clave": "geobosques", "nombre": "Geobosques MINAM (Landsat, 30 m)", "archivo": "geobosques_perdida.tif"},
]


def zonas_disponibles():
    """Lee datos/recortes/zonas.json: nombre, caja (bbox) y capas de cada zona precalculada."""
    ruta = RECORTES / "zonas.json"
    if not ruta.exists():
        return {}
    return json.loads(ruta.read_text(encoding="utf-8"))


def zona_de(geom):
    """Devuelve la clave de la zona precalculada que contiene la parcela, o None."""
    for clave, zona in zonas_disponibles().items():
        oeste, sur, este, norte = zona["bbox"]
        x, y = geom.centroid.x, geom.centroid.y
        if oeste <= x <= este and sur <= y <= norte:
            return clave
    return None


def geometria_de_analisis(geom, area_declarada_ha):
    """Un punto se analiza como un círculo con el área declarada (o 1 ha si no la tiene)."""
    if not isinstance(geom, Point):
        return geom
    area = area_declarada_ha if area_declarada_ha and area_declarada_ha > 0 else 1.0
    radio_m = math.sqrt(area * 10_000 / math.pi)
    serie = gpd.GeoSeries([geom], crs="EPSG:4326")
    utm = serie.estimate_utm_crs()
    return serie.to_crs(utm).buffer(radio_m, resolution=16).to_crs("EPSG:4326").iloc[0]


def leer_capa(zona, archivo, geom):
    """Recorta una capa con el polígono. Devuelve (arreglo, dentro) o (None, None) si no existe."""
    ruta = RECORTES / zona / archivo
    if not ruta.exists():
        return None, None
    with rasterio.open(ruta) as src:
        datos, _ = mask(src, [mapping(geom)], crop=True, all_touched=False, filled=False)
    banda = datos[0]
    dentro = ~np.ma.getmaskarray(banda)
    return np.ma.getdata(banda), dentro


def hectareas_por_pixel(zona, lat):
    """Área de un píxel en hectáreas a esa latitud (la grilla está en grados)."""
    with rasterio.open(RECORTES / zona / "jrc_bosque2020.tif") as src:
        dx, dy = src.res
    ancho_m = dx * 111_320 * math.cos(math.radians(lat))
    alto_m = dy * 110_574
    return ancho_m * alto_m / 10_000


def analizar(geom, area_declarada_ha=None):
    """Cruza una parcela con todas las capas de su zona y devuelve un diccionario con la evidencia."""
    zona = zona_de(geom)
    if zona is None:
        return {"zona": None, "error": "La parcela está fuera de las zonas precalculadas del demo "
                                        "(Sandia y Carabaya en Puno, Alto Mayo en San Martín)."}
    es_punto = isinstance(geom, Point)
    g = geometria_de_analisis(geom, area_declarada_ha)
    ha_px = hectareas_por_pixel(zona, g.centroid.y)

    bosque, dentro = leer_capa(zona, "jrc_bosque2020.tif", g)
    if bosque is None or dentro.sum() == 0:
        return {"zona": zona, "error": "La parcela es demasiado pequeña para la grilla de 10 m."}
    area_ha = dentro.sum() * ha_px
    es_bosque = dentro & (bosque == 1)
    bosque_ha = es_bosque.sum() * ha_px

    worldcover, _ = leer_capa(zona, "worldcover2020.tif", g)
    cobertura2000, _ = leer_capa(zona, "hansen_cobertura2000.tif", g)

    evidencias = []
    perdida_por_fuente = []
    for fuente in FUENTES_PERDIDA:
        anio, _ = leer_capa(zona, fuente["archivo"], g)
        if anio is None:
            evidencias.append(Evidencia(fuente["nombre"], disponible=False, nota="Sin datos en esta zona."))
            continue
        perdida = dentro & (anio > ANIO_CORTE - 2000) & (anio != NODATA)
        perdida_bosque = perdida & es_bosque
        anios = {}
        for a in np.unique(anio[perdida_bosque]):
            anios[int(a) + 2000] = round(float((perdida_bosque & (anio == a)).sum() * ha_px), 3)
        evidencias.append(Evidencia(fuente["nombre"], disponible=True,
                                    perdida_en_bosque_ha=round(float(perdida_bosque.sum() * ha_px), 3),
                                    perdida_total_ha=round(float(perdida.sum() * ha_px), 3), anios=anios))
        perdida_por_fuente.append(perdida_bosque)

    # Acuerdo píxel a píxel: donde al menos dos fuentes ven pérdida en bosque 2020.
    # Hansen y Geobosques son de 30 m: se acepta coincidencia con un píxel vecino (tolerancia de 1 píxel).
    if perdida_por_fuente:
        votos = sum(_dilatar(p).astype(int) for p in perdida_por_fuente)
        cualquiera = np.logical_or.reduce(perdida_por_fuente)
        acordada = cualquiera & (votos >= 2)
    else:
        acordada = np.zeros_like(dentro)
        cualquiera = acordada
    acordada_ha = float(acordada.sum() * ha_px)

    # ¿La pérdida cae en lo que ya era chacra en 2020? (WorldCover: cultivo, pasto, arbustal…)
    perdida_total = np.zeros_like(dentro)
    for fuente in FUENTES_PERDIDA:
        anio, _ = leer_capa(zona, fuente["archivo"], g)
        if anio is not None:
            perdida_total |= dentro & (anio > ANIO_CORTE - 2000) & (anio != NODATA)
    if worldcover is not None and perdida_total.sum() > 0:
        en_chacra = perdida_total & np.isin(worldcover, CLASES_NO_BOSQUE_WC)
        chacra_pct = 100 * en_chacra.sum() / perdida_total.sum()
    else:
        chacra_pct = 0.0

    fuera_bosque_ha = max([e.perdida_total_ha - e.perdida_en_bosque_ha for e in evidencias if e.disponible],
                          default=0.0)
    resultado = clasificar(area_ha, bosque_ha, evidencias, acordada_ha, chacra_pct, es_punto, fuera_bosque_ha)
    usos = {}
    if worldcover is not None:
        valores, cuentas = np.unique(worldcover[dentro], return_counts=True)
        usos = {int(v): round(float(c * ha_px), 3) for v, c in zip(valores, cuentas)}
    return {
        "zona": zona,
        "area_analizada_ha": round(float(area_ha), 3),
        "bosque_2020_ha": resultado.bosque_2020_ha,
        "bosque_2020_pct": resultado.bosque_2020_pct,
        "perdida_acordada_ha": resultado.perdida_acordada_ha,
        "perdida_chacra_2020_pct": round(float(chacra_pct), 1),
        "perdida_fuera_bosque_ha": round(float(fuera_bosque_ha), 3),
        "cobertura_arborea_2000_media": (round(float(cobertura2000[dentro].mean()), 1)
                                         if cobertura2000 is not None else None),
        "usos_worldcover_2020_ha": usos,
        "evidencias": [e.__dict__ for e in evidencias],
        "estado": resultado.estado,
        "confianza": resultado.confianza,
        "razones": resultado.razones,
        "anio_principal": resultado.anio_principal,
        "geometria_analizada": mapping(g),
    }


def _dilatar(arreglo):
    """Expande cada píxel verdadero a sus 8 vecinos (tolerancia de un píxel entre fuentes)."""
    salida = arreglo.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            salida |= np.roll(np.roll(arreglo, dy, axis=0), dx, axis=1)
    return salida
