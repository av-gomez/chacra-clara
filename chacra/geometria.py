"""Ingreso y validación de parcelas con GeoPandas (sesión 06 del curso).

Tres formas de ingresar parcelas:
  1. Dibujarlas en el mapa (Folium Draw devuelve un GeoJSON).
  2. Subir un GeoJSON o un KML.
  3. Subir un Excel o CSV con código de productor, coordenadas y área (hay una plantilla).

Reglas de validación (Reglamento UE 2023/1115, art. 2, punto 28, y art. 9):
  - Parcelas de más de 4 ha: deben ser un polígono. Las de 4 ha o menos pueden ser un punto.
  - Coordenadas en WGS84 (EPSG:4326) con al menos 6 decimales.
  - Dentro del Perú, polígonos válidos (que no se crucen consigo mismos), sin duplicados
    y sin superponerse con otras parcelas.
"""
import io
import json
import re

import geopandas as gpd
import pandas as pd
from lxml import etree
from shapely.geometry import Point, Polygon, MultiPolygon, shape
from shapely.validation import explain_validity

from chacra.rutas import DATOS

LIMITE_PUNTO_HA = 4.0          # más de 4 ha exige polígono
DECIMALES_MINIMOS = 6          # precisión mínima de las coordenadas
AREA_MAXIMA_HA = 200.0         # más que esto es casi seguro un error para un pequeño productor
SUPERPOSICION_MINIMA_M2 = 100  # se avisa si dos parcelas comparten más de 100 m²
TOLERANCIA_FRONTERA_GRADOS = 0.02  # el contorno del Perú está simplificado: ~2 km de margen

COLUMNAS_PLANTILLA = ["codigo_productor", "codigo_parcela", "cultivo", "latitud", "longitud",
                      "area_ha", "produccion_kg_anual"]


def plantilla_csv():
    """Plantilla descargable para cargar parcelas desde Excel o CSV."""
    ejemplo = pd.DataFrame([
        {"codigo_productor": "PR-001", "codigo_parcela": "PR-001-A", "cultivo": "café",
         "latitud": -14.183311, "longitud": -69.185402, "area_ha": 1.8, "produccion_kg_anual": 1100},
        {"codigo_productor": "PR-002", "codigo_parcela": "PR-002-A", "cultivo": "cacao",
         "latitud": -14.172520, "longitud": -69.176655, "area_ha": 2.5, "produccion_kg_anual": 1500},
    ], columns=COLUMNAS_PLANTILLA)
    return ejemplo.to_csv(index=False).encode("utf-8-sig")


def contar_decimales(valor):
    texto = str(valor).strip()
    if "e" in texto.lower():
        return 0
    if "." not in texto:
        return 0
    return len(texto.split(".")[1])


def decimales_minimos_de(geom_dict):
    """Cuenta los decimales de cada coordenada de un GeoJSON y devuelve el mínimo."""
    numeros = re.findall(r"-?\d+(?:\.\d+)?", json.dumps(geom_dict.get("coordinates", [])))
    if not numeros:
        return 0
    return min(contar_decimales(n) for n in numeros)


def _normalizar_columnas(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    sinonimos = {"lat": "latitud", "latitude": "latitud", "y": "latitud",
                 "lon": "longitud", "lng": "longitud", "long": "longitud", "longitude": "longitud", "x": "longitud",
                 "area": "area_ha", "hectareas": "area_ha", "ha": "area_ha", "superficie_ha": "area_ha",
                 "productor": "codigo_productor", "id_productor": "codigo_productor",
                 "parcela": "codigo_parcela", "id_parcela": "codigo_parcela",
                 "produccion": "produccion_kg_anual", "produccion_kg": "produccion_kg_anual"}
    df = df.rename(columns={c: sinonimos[c] for c in df.columns if c in sinonimos})
    return df


def leer_tabla(archivo, nombre):
    """Lee un CSV o Excel con una fila por parcela (punto con latitud y longitud)."""
    if nombre.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(archivo, dtype=str)
    else:
        df = pd.read_csv(archivo, dtype=str, sep=None, engine="python", encoding="utf-8-sig")
    df = _normalizar_columnas(df)
    faltan = [c for c in ["codigo_productor", "latitud", "longitud"] if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas en el archivo: {', '.join(faltan)}. Use la plantilla.")
    filas = []
    for i, fila in df.iterrows():
        lat_txt = str(fila["latitud"]).replace(",", ".")
        lon_txt = str(fila["longitud"]).replace(",", ".")
        geom = Point(float(lon_txt), float(lat_txt))
        filas.append({
            "codigo_productor": str(fila["codigo_productor"]).strip(),
            "codigo_parcela": str(fila.get("codigo_parcela") or f"{fila['codigo_productor']}-{i + 1}").strip(),
            "cultivo": str(fila.get("cultivo") or "café").strip().lower(),
            "area_declarada_ha": pd.to_numeric(str(fila.get("area_ha", "")).replace(",", "."), errors="coerce"),
            "produccion_kg_anual": pd.to_numeric(fila.get("produccion_kg_anual"), errors="coerce"),
            "decimales": min(contar_decimales(lat_txt), contar_decimales(lon_txt)),
            "geometry": geom,
        })
    return gpd.GeoDataFrame(filas, geometry="geometry", crs="EPSG:4326")


def _propiedad(props, *claves, defecto=None):
    """Busca una propiedad sin importar mayúsculas (AgroDigital y TRACES usan nombres distintos)."""
    minusculas = {str(k).lower(): v for k, v in (props or {}).items()}
    for clave in claves:
        if clave.lower() in minusculas and minusculas[clave.lower()] not in (None, ""):
            return minusculas[clave.lower()]
    return defecto


def desde_geojson(datos_geojson):
    """Convierte un GeoJSON (FeatureCollection, Feature o geometría) en parcelas."""
    if datos_geojson.get("type") == "FeatureCollection":
        features = datos_geojson.get("features", [])
    elif datos_geojson.get("type") == "Feature":
        features = [datos_geojson]
    else:
        features = [{"type": "Feature", "properties": {}, "geometry": datos_geojson}]
    filas = []
    for i, f in enumerate(features):
        if not f.get("geometry"):
            continue
        props = f.get("properties") or {}
        codigo_productor = _propiedad(props, "codigo_productor", "ProducerName", "productor", "cod_productor",
                                      "dni_hash", defecto=f"SIN-CODIGO-{i + 1}")
        filas.append({
            "codigo_productor": str(codigo_productor),
            "codigo_parcela": str(_propiedad(props, "codigo_parcela", "ProductionPlace", "parcela", "id",
                                             defecto=f"{codigo_productor}-{i + 1}")),
            "cultivo": str(_propiedad(props, "cultivo", "commodity", defecto="café")).lower(),
            "area_declarada_ha": pd.to_numeric(_propiedad(props, "area_ha", "Area", "area"), errors="coerce"),
            "produccion_kg_anual": pd.to_numeric(_propiedad(props, "produccion_kg_anual", "produccion"),
                                                 errors="coerce"),
            "decimales": decimales_minimos_de(f["geometry"]),
            "geometry": shape(f["geometry"]),
        })
    if not filas:
        raise ValueError("El archivo no tiene geometrías.")
    return gpd.GeoDataFrame(filas, geometry="geometry", crs="EPSG:4326")


def leer_kml(contenido):
    """Lee puntos y polígonos de un KML (por ejemplo, exportado de Google Earth o de un GPS)."""
    raiz = etree.fromstring(contenido)
    ns = {"k": raiz.nsmap.get(None, "http://www.opengis.net/kml/2.2")}
    features = []
    for marca in raiz.iter("{%s}Placemark" % ns["k"]):
        nombre = marca.findtext("k:name", default="", namespaces=ns).strip()
        for poligono in marca.iter("{%s}Polygon" % ns["k"]):
            texto = poligono.findtext(".//k:outerBoundaryIs//k:coordinates", namespaces=ns)
            anillo = [[float(v) for v in par.split(",")[:2]] for par in texto.split()]
            features.append({"type": "Feature", "properties": {"codigo_parcela": nombre},
                             "geometry": {"type": "Polygon", "coordinates": [anillo]}})
        for punto in marca.iter("{%s}Point" % ns["k"]):
            texto = punto.findtext("k:coordinates", namespaces=ns)
            lon, lat = [float(v) for v in texto.strip().split(",")[:2]]
            features.append({"type": "Feature", "properties": {"codigo_parcela": nombre},
                             "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    # Los decimales se cuentan sobre el texto original del KML
    coordenadas = re.findall(r"-?\d+\.\d+", contenido.decode("utf-8", errors="ignore"))
    decimales_kml = min((contar_decimales(c) for c in coordenadas), default=0)
    gdf = desde_geojson({"type": "FeatureCollection", "features": features})
    gdf["decimales"] = decimales_kml
    return gdf


def leer_archivo(archivo_subido):
    """Detecta el formato por la extensión y devuelve un GeoDataFrame de parcelas."""
    nombre = archivo_subido.name
    contenido = archivo_subido.getvalue()
    if nombre.lower().endswith((".geojson", ".json")):
        return desde_geojson(json.loads(contenido.decode("utf-8-sig")))
    if nombre.lower().endswith(".kml"):
        return leer_kml(contenido)
    if nombre.lower().endswith((".csv", ".txt", ".xlsx", ".xls")):
        return leer_tabla(io.BytesIO(contenido), nombre)
    raise ValueError("Formato no reconocido. Use GeoJSON, KML, CSV o Excel.")


def area_ha(gdf):
    """Área en hectáreas: se calcula en metros (UTM), nunca en grados (EPSG:4326)."""
    utm = gdf.estimate_utm_crs()
    return gdf.to_crs(utm).area / 10_000


def validar(gdf):
    """Agrega la columna 'problemas' (lista de textos) y 'valida' (sin errores graves)."""
    gdf = gdf.copy().reset_index(drop=True)
    peru = gpd.read_file(DATOS / "peru.geojson").geometry.union_all().buffer(TOLERANCIA_FRONTERA_GRADOS)
    gdf["area_calculada_ha"] = area_ha(gdf).round(3)
    errores, avisos = [], []
    for i, fila in gdf.iterrows():
        e, a = [], []
        geom = fila.geometry
        es_punto = isinstance(geom, Point)
        area_ref = fila["area_declarada_ha"] if es_punto else fila["area_calculada_ha"]
        if not isinstance(geom, (Point, Polygon, MultiPolygon)):
            e.append("Tipo de geometría no aceptado (use punto o polígono).")
        if not geom.is_valid:
            e.append(f"El polígono se cruza consigo mismo o está mal cerrado ({explain_validity(geom)}).")
        if not peru.contains(geom.centroid):
            e.append("La parcela está fuera del Perú.")
        if es_punto and pd.notna(area_ref) and area_ref > LIMITE_PUNTO_HA:
            e.append(f"Tiene {area_ref:.1f} ha: más de 4 ha exige un polígono, no un punto.")
        if es_punto and pd.isna(area_ref):
            a.append("Falta el área: un punto solo vale para parcelas de 4 ha o menos.")
        if fila["decimales"] < DECIMALES_MINIMOS:
            a.append(f"Coordenadas con {fila['decimales']} decimales: la EUDR pide al menos 6.")
        if not es_punto and fila["area_calculada_ha"] > AREA_MAXIMA_HA:
            e.append(f"Área de {fila['area_calculada_ha']:.0f} ha: revise si el polígono es correcto.")
        if not es_punto and pd.notna(fila["area_declarada_ha"]) and fila["area_declarada_ha"] > 0:
            diferencia = abs(fila["area_calculada_ha"] - fila["area_declarada_ha"]) / fila["area_declarada_ha"]
            if diferencia > 0.25:
                a.append(f"El área dibujada ({fila['area_calculada_ha']:.2f} ha) difiere en más de 25 % "
                         f"del área declarada ({fila['area_declarada_ha']:.2f} ha).")
        errores.append(e)
        avisos.append(a)

    # Duplicados y superposiciones entre parcelas (en metros)
    metrico = gdf.to_crs(gdf.estimate_utm_crs())
    claves = gdf.geometry.apply(lambda g: g.normalize().wkt if g.is_valid else g.wkt)
    for i in range(len(gdf)):
        for j in range(i + 1, len(gdf)):
            if claves[i] == claves[j] or gdf.loc[i, "codigo_parcela"] == gdf.loc[j, "codigo_parcela"]:
                avisos[j].append(f"Parece duplicada de {gdf.loc[i, 'codigo_parcela']}.")
                continue
            gi, gj = metrico.geometry[i], metrico.geometry[j]
            if gi.geom_type != "Point" and gj.geom_type != "Point" and gi.is_valid and gj.is_valid:
                comun = gi.intersection(gj).area
                if comun > SUPERPOSICION_MINIMA_M2:
                    texto = f"Se superpone {comun:.0f} m² con {gdf.loc[j, 'codigo_parcela']}."
                    avisos[i].append(texto)
                    avisos[j].append(f"Se superpone {comun:.0f} m² con {gdf.loc[i, 'codigo_parcela']}.")
    gdf["errores"] = errores
    gdf["avisos"] = avisos
    gdf["valida"] = [len(e) == 0 for e in errores]
    return gdf
