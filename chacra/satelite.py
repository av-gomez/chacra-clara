"""Cruce de cada parcela con los recortes satelitales (raster, sesión 07 del curso).

Todos los recortes de una zona están en la MISMA grilla (la de ESA WorldCover, 1/12000 de grado, unos 9 m),
así que un píxel (fila, columna) es el mismo lugar en todas las capas. Eso permite:
  - medir la cobertura de bosque 2020 según el JRC y, aparte, el BOSQUE NATURAL 2020;
  - medir la pérdida de cada fuente solo donde había bosque en 2020;
  - medir dónde coinciden dos TIPOS DE SENSOR, píxel a píxel.

Área en que "coinciden" los sensores (perdida_acordada_ha):
  INTERSECCIÓN con tolerancia de un píxel = píxeles con pérdida según Landsat (Hansen o Geobosques) que tienen
  pérdida según Sentinel-2 (GLAD-S2 o Impact Observatory) a 10 m o menos. Nunca es mayor que la pérdida vista
  por Landsat. La tolerancia existe porque Landsat tiene píxeles de 30 m y Sentinel-2 de 10 m.

Igual que en la sesión 07: se recorta con rasterio.mask, se respeta el 'nodata' y las áreas se calculan en
metros (el tamaño del píxel en metros depende de la latitud), no en grados.
"""
import json
import math

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point, mapping

from chacra.estado import Evidencia, Natural, clasificar
from chacra.formato import num, pct
from chacra.rutas import RECORTES

ANIO_CORTE = 2020          # fecha de corte de la EUDR: 31 de diciembre de 2020
CLASES_NO_BOSQUE_WC = [20, 30, 40, 50, 60]   # WorldCover: arbustal, pasto, cultivo, urbano, suelo desnudo
NODATA = 255

# Fuentes de pérdida. 'archivo' guarda el año de pérdida menos 2000 (21 = 2021); 0 = sin pérdida.
# 'hasta' es el último año que cubre la fuente; 'sensor' agrupa las fuentes que NO son independientes.
FUENTES_PERDIDA = [
    {"clave": "hansen", "nombre": "Hansen/UMD v1.13 (Landsat, 30 m)", "sensor": "Landsat", "hasta": 2025,
     "archivo": "hansen_perdida.tif"},
    {"clave": "geobosques", "nombre": "Geobosques MINAM (Landsat, 30 m)", "sensor": "Landsat", "hasta": 2025,
     "archivo": "geobosques_perdida.tif"},
    {"clave": "alertas", "nombre": "Alertas GLAD-S2 (Sentinel-2, 10 m)", "sensor": "Sentinel-2", "hasta": 2026,
     "archivo": "alertas_perdida.tif"},
    {"clave": "io", "nombre": "Impact Observatory (Sentinel-2, 10 m, hasta 2023)", "sensor": "Sentinel-2",
     "hasta": 2023, "archivo": "io_perdida.tif"},
]

# Capas para distinguir bosque natural de café o cacao bajo sombra (si existen en la zona)
NATURAL_MIN = 50          # natural2020.tif: probabilidad de bosque natural (0-100); 50 o más = bosque natural
ALTURA_SOMBRA_MAX_M = 20  # altura2020.tif: dosel promedio < 20 m donde hubo pérdida = probable sombra de cultivo (criterio prudente)
CULTIVO_MIN = 50          # cultivo2020.tif: probabilidad de café o cacao (0-100); 50 o más = probable cultivo


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


def _dilatar(arreglo):
    """Expande cada píxel verdadero a sus 8 vecinos (tolerancia de un píxel entre sensores)."""
    salida = arreglo.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            salida |= np.roll(np.roll(arreglo, dy, axis=0), dx, axis=1)
    return salida


def evidencia_natural(zona, g, dentro, es_bosque, acordada, ha_px):
    """Bosque natural 2020, altura del dosel y probabilidad de cultivo en la parcela y en la pérdida."""
    natural, _ = leer_capa(zona, "natural2020.tif", g)
    altura, _ = leer_capa(zona, "altura2020.tif", g)
    cultivo, _ = leer_capa(zona, "cultivo2020.tif", g)
    resultado = Natural(disponible=natural is not None)
    if natural is None:
        return resultado, {}
    valido = dentro & (natural != NODATA)
    es_natural = valido & (natural >= NATURAL_MIN)
    resultado.bosque_natural_ha = round(float(es_natural.sum() * ha_px), 3)
    resultado.perdida_en_natural_ha = round(float((acordada & es_natural).sum() * ha_px), 3)
    datos = {"bosque_natural_2020_ha": resultado.bosque_natural_ha,
             "natural_prob_media": round(float(natural[valido].mean()), 1) if valido.any() else None}
    # Donde se mide la sombra: la pérdida acordada; si no hay, el bosque JRC de la parcela
    zona_medida = acordada if acordada.any() else es_bosque
    if altura is not None:
        validos = zona_medida & (altura != NODATA)
        if validos.any():
            resultado.altura_media_m = round(float(altura[validos].mean()), 1)
        datos["altura_dosel_2020_m"] = resultado.altura_media_m
    if cultivo is not None:
        validos = zona_medida & (cultivo != NODATA)
        prob = round(float(cultivo[validos].mean()), 1) if validos.any() else None
        datos["cultivo_prob_media"] = prob
        if prob is not None and prob >= CULTIVO_MIN:
            resultado.sombra_probable = True
            resultado.razones_sombra.append(f"probabilidad media de café o cacao de {pct(prob)}")
    if resultado.altura_media_m is not None and resultado.altura_media_m < ALTURA_SOMBRA_MAX_M:
        resultado.sombra_probable = True
        resultado.razones_sombra.append(f"el dosel de 2020 mide en promedio {num(resultado.altura_media_m, 0)} m, "
                                        f"menos que un bosque natural de la zona ({ALTURA_SOMBRA_MAX_M} m o más)")
    if zona_medida.any():
        natural_pct = 100 * (zona_medida & es_natural).sum() / zona_medida.sum()
        datos["natural_pct_en_perdida"] = round(float(natural_pct), 1)
        if natural_pct < 50:
            resultado.sombra_probable = True
            resultado.razones_sombra.append(f"solo el {pct(natural_pct)} de esa área era bosque natural en 2020 "
                                            "según Natural Forests of the World")
    return resultado, datos


def analizar(geom, area_declarada_ha=None, renovacion_anio=None):
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

    evidencias, perdidas = [], {}
    for fuente in FUENTES_PERDIDA:
        anio, _ = leer_capa(zona, fuente["archivo"], g)
        if anio is None:
            evidencias.append(Evidencia(fuente["nombre"], fuente["sensor"], disponible=False, cubre_hasta=fuente["hasta"],
                                        nota="Sin datos en esta zona."))
            continue
        perdida = dentro & (anio > ANIO_CORTE - 2000) & (anio != NODATA)
        perdida_bosque = perdida & es_bosque
        anios = {}
        for a in np.unique(anio[perdida_bosque]):
            anios[int(a) + 2000] = round(float((perdida_bosque & (anio == a)).sum() * ha_px), 3)
        evidencias.append(Evidencia(fuente["nombre"], fuente["sensor"], disponible=True, cubre_hasta=fuente["hasta"],
                                    perdida_en_bosque_ha=round(float(perdida_bosque.sum() * ha_px), 3),
                                    perdida_total_ha=round(float(perdida.sum() * ha_px), 3), anios=anios))
        perdidas[fuente["clave"]] = (fuente["sensor"], perdida, perdida_bosque)

    # Una fuente sin pérdida que no cubre el último año con pérdida (según otras fuentes): "sin datos para ese periodo"
    anios_con_perdida = [a for e in evidencias for a, h in e.anios.items() if h >= 0.05]
    if anios_con_perdida:
        ultimo = max(anios_con_perdida)
        for e in evidencias:
            if e.disponible and e.perdida_en_bosque_ha < 0.05 and e.cubre_hasta < ultimo:
                e.sin_datos_periodo = True
                e.nota = f"Sin datos para ese periodo: cubre solo hasta {e.cubre_hasta}."

    # Intersección por tipo de sensor (Landsat contra Sentinel-2), con tolerancia de un píxel
    vacio = np.zeros_like(dentro)
    landsat = np.logical_or.reduce([p[2] for p in perdidas.values() if p[0] == "Landsat"] or [vacio])
    sentinel = np.logical_or.reduce([p[2] for p in perdidas.values() if p[0] == "Sentinel-2"] or [vacio])
    acordada = landsat & _dilatar(sentinel)
    acordada_ha = float(acordada.sum() * ha_px)

    # ¿La pérdida cae en lo que ya era chacra en 2020? (WorldCover: cultivo, pasto, arbustal…)
    perdida_total = np.logical_or.reduce([p[1] for p in perdidas.values()] or [vacio])
    if worldcover is not None and perdida_total.sum() > 0:
        chacra_pct = 100 * (perdida_total & np.isin(worldcover, CLASES_NO_BOSQUE_WC)).sum() / perdida_total.sum()
    else:
        chacra_pct = 0.0
    fuera_bosque_ha = max([e.perdida_total_ha - e.perdida_en_bosque_ha for e in evidencias if e.disponible],
                          default=0.0)

    natural, datos_naturales = evidencia_natural(zona, g, dentro, es_bosque, acordada, ha_px)
    resultado = clasificar(area_ha, bosque_ha, evidencias, acordada_ha, chacra_pct, es_punto, fuera_bosque_ha,
                           natural, renovacion_anio)
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
        "perdida_landsat_ha": round(float(landsat.sum() * ha_px), 3),
        "perdida_sentinel2_ha": round(float(sentinel.sum() * ha_px), 3),
        "perdida_chacra_2020_pct": round(float(chacra_pct), 1),
        "perdida_fuera_bosque_ha": round(float(fuera_bosque_ha), 3),
        "natural": {"disponible": natural.disponible, "perdida_en_natural_ha": natural.perdida_en_natural_ha,
                    "sombra_probable": natural.sombra_probable, **datos_naturales},
        "renovacion_anio": renovacion_anio,
        "usos_worldcover_2020_ha": usos,
        "evidencias": [e.__dict__ for e in evidencias],
        "estado": resultado.estado,
        "confianza": resultado.confianza,
        "motivo": resultado.motivo,
        "razones": resultado.razones,
        "anio_principal": resultado.anio_principal,
        "geometria_analizada": mapping(g),
    }
