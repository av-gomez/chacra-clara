"""Descarga y recorta las capas satelitales de cada zona del demo en una misma grilla.

Reproducible: cualquiera puede volver a correrlo y obtener los mismos archivos de datos/recortes/.
Sigue la forma de trabajo de las sesiones 07 y 14: lectura por ventanas (solo la caja de la zona),
reproyección a una grilla común con rasterio y nada de descargar teselas enteras.

Grilla común: la de ESA WorldCover (EPSG:4326, 1/12000 de grado, unos 9 m en el Perú).
Las capas de 30 m (Hansen, Geobosques) se pasan a esa grilla con vecino más cercano: no se inventa detalle,
cada píxel de 30 m se repite en 3 x 3 píxeles de 10 m.

Uso:
  python scripts/preparar_recortes.py                 # todas las zonas y capas
  python scripts/preparar_recortes.py --zona sandia   # una zona
  python scripts/preparar_recortes.py --capa s2       # una capa
"""
import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds

RAIZ = Path(__file__).resolve().parent.parent
RECORTES = RAIZ / "datos" / "recortes"
RES = 1 / 12000  # grados por píxel (grilla de ESA WorldCover)
NODATA = 255

ZONAS = {
    "sandia": {"nombre": "Sandia (Puno): San Juan del Oro y Putina Punco",
               "region": "Puno", "cultivo": "café", "bbox": [-69.25, -14.30, -69.05, -14.10]},
    "carabaya": {"nombre": "Carabaya (Puno): San Gabán",
                 "region": "Puno", "cultivo": "café y cacao", "bbox": [-70.48, -13.50, -70.33, -13.35]},
    "altomayo": {"nombre": "Alto Mayo (San Martín): Moyobamba y Rioja",
                 "region": "San Martín", "cultivo": "café", "bbox": [-77.20, -5.95, -77.00, -5.75]},
}


def grilla(bbox):
    """Transformación y tamaño de la grilla común para una caja [oeste, sur, este, norte]."""
    oeste, sur, este, norte = bbox
    ancho = int(round((este - oeste) / RES))
    alto = int(round((norte - sur) / RES))
    return from_origin(oeste, norte, RES, RES), ancho, alto


def guardar(arreglo, bbox, ruta, nodata=NODATA, descripcion=""):
    transform, ancho, alto = grilla(bbox)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    perfil = {"driver": "GTiff", "dtype": "uint8", "count": 1, "width": ancho, "height": alto,
              "crs": "EPSG:4326", "transform": transform, "nodata": nodata, "compress": "deflate",
              "predictor": 2, "tiled": True, "blockxsize": 256, "blockysize": 256}
    with rasterio.open(ruta, "w", **perfil) as dst:
        dst.write(arreglo.astype("uint8"), 1)
        dst.update_tags(descripcion=descripcion)
    print(f"  {ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1e6:.1f} MB")


def leer_ventana(fuente_ruta, bbox, banda=1):
    """Lee solo la ventana de la zona (con un margen) de un raster local o remoto (/vsicurl/)."""
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        with rasterio.open(fuente_ruta) as src:
            margen = 0.002
            caja = transform_bounds("EPSG:4326", src.crs, bbox[0] - margen, bbox[1] - margen,
                                    bbox[2] + margen, bbox[3] + margen)
            ventana = rasterio.windows.from_bounds(*caja, transform=src.transform).round_offsets().round_lengths()
            try:
                ventana = ventana.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            except rasterio.errors.WindowError:
                return None, None, None, None
            datos = src.read(banda, window=ventana)
            return datos, src.window_transform(ventana), src.crs, src.nodata


def a_grilla(fuente_ruta, bbox, convertir=None, resampling=Resampling.nearest, banda=1):
    """Lleva la ventana de un raster a la grilla común. 'convertir' transforma los valores antes
    (por ejemplo, de días desde 2018 a año menos 2000) y debe devolver uint8 con 255 como nodata."""
    transform, ancho, alto = grilla(bbox)
    destino = np.full((alto, ancho), NODATA, dtype="uint8")
    datos, src_transform, src_crs, src_nodata = leer_ventana(fuente_ruta, bbox, banda)
    if datos is None:
        return destino
    if convertir is not None:
        datos = convertir(datos)
        src_nodata = NODATA
    reproject(datos, destino, src_transform=src_transform, src_crs=src_crs,
              dst_transform=transform, dst_crs="EPSG:4326", resampling=resampling,
              src_nodata=src_nodata, dst_nodata=NODATA)
    return destino


def combinar(capas):
    """Une varias teselas: donde una no tiene dato, usa la siguiente."""
    combinado = capas[0]
    for c in capas[1:]:
        combinado = np.where(combinado == NODATA, c, combinado)
    return combinado


# ---------- JRC, Hansen y GLAD (lectura por ventanas sobre HTTP) ----------

JRC_COG = "/vsicurl/https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/FOREST/GFC2020/LATEST/single-cog/JRC_GFC2020_V4_COG.tif"
HANSEN = "/vsicurl/https://storage.googleapis.com/earthenginepartners-hansen/GFC-2025-v1.13/Hansen_GFC-2025-v1.13_{capa}_{tesela}.tif"
GLAD_S2 = "/vsicurl/https://storage.googleapis.com/earthenginepartners-hansen/S2alert/{capa}/{tesela}.tif"
CONFIANZA_MINIMA_GLAD_S2 = 3   # 3 = confianza media, 4 = alta. Se descartan 1 y 2 (no confirmadas o baja).


def tesela_hansen(bbox):
    """Teselas de 10 x 10 grados nombradas por su esquina superior izquierda (ej. 10S_070W)."""
    lat = int(np.ceil(bbox[3] / 10) * 10)
    lon = int(np.floor(bbox[0] / 10) * 10)
    lat_txt = f"{abs(lat):02d}{'N' if lat >= 0 else 'S'}"
    lon_txt = f"{abs(lon):03d}{'E' if lon >= 0 else 'W'}"
    return f"{lat_txt}_{lon_txt}"


def tesela_glad_s2(bbox):
    """Teselas GLAD-S2 nombradas lon_min, lat_min, lon_max, lat_max (ej. 070W_20S_060W_10S)."""
    lon0 = int(np.floor(bbox[0] / 10) * 10)
    lat0 = int(np.floor(bbox[1] / 10) * 10)

    def lon(v):
        return f"{abs(v):03d}{'E' if v >= 0 else 'W'}"

    def lat(v):
        return f"{abs(v):02d}{'N' if v >= 0 else 'S'}"
    return f"{lon(lon0)}_{lat(lat0)}_{lon(lon0 + 10)}_{lat(lat0 + 10)}"


def jrc(clave, zona):
    """JRC Global Forest Cover 2020 V4 (10 m): 1 = bosque, 0 = no bosque. Mapa de referencia de la UE."""
    capa = a_grilla(JRC_COG, zona["bbox"])
    guardar(capa, zona["bbox"], RECORTES / clave / "jrc_bosque2020.tif",
            descripcion="JRC GFC2020 V4 (CC BY 4.0)")


def hansen(clave, zona):
    """Hansen/UMD Global Forest Change v1.13 (30 m): año de pérdida (1 = 2001 … 25 = 2025) y cobertura 2000."""
    tesela = tesela_hansen(zona["bbox"])
    perdida = a_grilla(HANSEN.format(capa="lossyear", tesela=tesela), zona["bbox"])
    guardar(perdida, zona["bbox"], RECORTES / clave / "hansen_perdida.tif",
            descripcion="Hansen GFC-2025 v1.13 lossyear (CC BY 4.0)")
    cobertura = a_grilla(HANSEN.format(capa="treecover2000", tesela=tesela), zona["bbox"])
    guardar(cobertura, zona["bbox"], RECORTES / clave / "hansen_cobertura2000.tif",
            descripcion="Hansen GFC-2025 v1.13 treecover2000 (CC BY 4.0)")


def glad_s2(clave, zona):
    """Alertas GLAD-S2 (UMD, Sentinel-2, 10 m) desde 2019. Se guarda el año de la alerta menos 2000,
    solo para alertas de confianza media o alta."""
    from datetime import date, timedelta
    tesela = tesela_glad_s2(zona["bbox"])
    confianza, *_ = leer_ventana(GLAD_S2.format(capa="alert", tesela=tesela), zona["bbox"])
    origen = date(2018, 12, 31)
    # año de cada número de días desde el 31/12/2018 (tabla de búsqueda para no recorrer píxel por píxel)
    tabla = np.zeros(4000, dtype="uint8")
    for dias in range(1, 4000):
        tabla[dias] = (origen + timedelta(days=dias)).year - 2000

    def a_anio(dias):
        anio = tabla[np.clip(dias, 0, 3999)]
        anio[(dias == 0) | (confianza < CONFIANZA_MINIMA_GLAD_S2)] = 0
        return anio.astype("uint8")
    capa = a_grilla(GLAD_S2.format(capa="alertDate", tesela=tesela), zona["bbox"], convertir=a_anio)
    guardar(capa, zona["bbox"], RECORTES / clave / "alertas_perdida.tif",
            descripcion="GLAD-S2 alerts UMD, confianza media y alta (CC BY 4.0)")


# ---------- Geobosques (MINAM): imagen por año del servicio oficial ----------

GEOBOSQUES = "https://gis.bosques.gob.pe/server/rest/services/Interoperabilidad/perdida_bosque_humedo_2001_2025/MapServer/export"
CAPAS_GEOBOSQUES = {2021: 41, 2022: 42, 2023: 43, 2024: 44, 2025: 25}   # 2025: solo pérdida antrópica


def geobosques(clave, zona):
    """Pérdida de bosque húmedo amazónico de Geobosques (MINAM), 2021 a 2025.

    El raster original pide registro, así que se usa el servicio de mapas público: se pide una imagen
    por año, del tamaño de la grilla de 30 m, y todo píxel pintado (no transparente) cuenta como pérdida.
    Es una máscara renderizada, no el valor original: se documenta como tal.
    """
    import io
    import requests
    from PIL import Image
    oeste, sur, este, norte = zona["bbox"]
    ancho = int(round((este - oeste) / (RES * 3)))
    alto = int(round((norte - sur) / (RES * 3)))
    anio_perdida = np.zeros((alto, ancho), dtype="uint8")
    for anio, capa in CAPAS_GEOBOSQUES.items():
        parametros = {"bbox": f"{oeste},{sur},{este},{norte}", "bboxSR": 4326, "imageSR": 4326,
                      "size": f"{ancho},{alto}", "format": "png32", "transparent": "true",
                      "layers": f"show:{capa}", "f": "image"}
        respuesta = requests.get(GEOBOSQUES, params=parametros, timeout=120)
        respuesta.raise_for_status()
        alfa = np.array(Image.open(io.BytesIO(respuesta.content)).convert("RGBA"))[:, :, 3]
        nuevo = (alfa > 0) & (anio_perdida == 0)
        anio_perdida[nuevo] = anio - 2000
        print(f"  Geobosques {anio}: {int((alfa > 0).sum())} píxeles de 30 m con pérdida")
    transform30 = from_origin(oeste, norte, RES * 3, RES * 3)
    transform, ancho10, alto10 = grilla(zona["bbox"])
    destino = np.full((alto10, ancho10), NODATA, dtype="uint8")
    reproject(anio_perdida, destino, src_transform=transform30, src_crs="EPSG:4326", dst_transform=transform,
              dst_crs="EPSG:4326", resampling=Resampling.nearest)
    guardar(destino, zona["bbox"], RECORTES / clave / "geobosques_perdida.tif",
            descripcion="Geobosques MINAM, pérdida de bosque húmedo 2021-2025 (servicio de mapas)")


# ---------- Capas de legalidad (SERNANP y SERFOR, vectores) ----------

SERNANP = "https://geoservicios.sernanp.gob.pe/arcgis/rest/services/sernanp_visor/servicio_descarga/MapServer/{id}/query"
CAPAS_LEGALIDAD = {
    "anp": (1, "Área Natural Protegida"),
    "zona_reservada": (2, "Zona Reservada"),
    "acr": (3, "Área de Conservación Regional"),
    "acp": (4, "Área de Conservación Privada"),
    "amortiguamiento": (8, "Zona de amortiguamiento de un área protegida"),
    "reserva_indigena": (29, "Reserva Indígena"),
    "comunidad_nativa": (39, "Comunidad Nativa"),
    "bpp": (62, "Bosque de Producción Permanente"),
}


def legalidad(clave, zona):
    """Descarga en GeoJSON las capas del SERNANP que tocan la zona (consulta por caja)."""
    import geopandas as gpd
    import pandas as pd
    import requests
    oeste, sur, este, norte = zona["bbox"]
    partes = []
    for tipo, (id_capa, nombre) in CAPAS_LEGALIDAD.items():
        parametros = {"geometry": f"{oeste},{sur},{este},{norte}", "geometryType": "esriGeometryEnvelope",
                      "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
                      "outSR": 4326, "f": "geojson"}
        respuesta = requests.get(SERNANP.format(id=id_capa), params=parametros, timeout=120)
        respuesta.raise_for_status()
        gdf = gpd.read_file(io_texto(respuesta.text))
        print(f"  SERNANP {nombre}: {len(gdf)}")
        if len(gdf) == 0:
            continue
        columna_nombre = next((c for c in gdf.columns if c.lower() in
                               ("anp_nomb", "nombre", "nom_cn", "nomb_comun", "za_nomb", "nom_comuni")), None)
        gdf["nombre"] = gdf[columna_nombre] if columna_nombre else nombre
        gdf["tipo"] = nombre
        partes.append(gdf[["tipo", "nombre", "geometry"]])
    ruta = RECORTES / clave / "legalidad.geojson"
    if partes:
        todo = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs="EPSG:4326")
        todo["geometry"] = todo.geometry.simplify(0.0002)
        todo.to_file(ruta, driver="GeoJSON")
    else:
        ruta.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
    print(f"  {ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1e6:.2f} MB")


def io_texto(texto):
    import io
    return io.StringIO(texto)


# ---------- Planetary Computer (como en la sesión 14) ----------

def catalogo():
    import planetary_computer
    import pystac_client
    return pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                     modifier=planetary_computer.sign_inplace)


def worldcover(clave, zona):
    """ESA WorldCover 2020 (v100), 10 m. Clases: 10 árboles, 20 arbustal, 30 pasto, 40 cultivo…"""
    cat = catalogo()
    items = list(cat.search(collections=["esa-worldcover"], bbox=zona["bbox"], datetime="2020").items())
    combinado = combinar([a_grilla(it.assets["map"].href, zona["bbox"]) for it in items])
    guardar(combinado, zona["bbox"], RECORTES / clave / "worldcover2020.tif",
            descripcion="ESA WorldCover 2020 v100 (CC BY 4.0)")


def impact_observatory(clave, zona):
    """Impact Observatory, uso del suelo anual de 10 m (Sentinel-2), 2017-2023.

    Se convierte en una capa de pérdida: píxeles que eran 'árboles' (clase 2) en 2020 y que en un año
    posterior pasan a cultivo (5), suelo desnudo (8) o pastizal (11). Se guarda el PRIMER año del cambio
    y se exige que el cambio siga en el último año disponible (para no contar una nube o un error de un año).
    """
    cat = catalogo()
    anuales = {}
    for anio in range(2020, 2024):
        items = list(cat.search(collections=["io-lulc-annual-v02"], bbox=zona["bbox"],
                                datetime=str(anio)).items())
        anuales[anio] = combinar([a_grilla(it.assets["data"].href, zona["bbox"]) for it in items])
        print(f"  IO {anio}: clases {np.unique(anuales[anio]).tolist()}")
    arboles_2020 = anuales[2020] == 2
    ultimo = max(anuales)
    sigue_cambiado = np.isin(anuales[ultimo], [5, 8, 11])
    perdida = np.zeros_like(anuales[2020])
    for anio in sorted(anuales):
        if anio == 2020:
            continue
        cambio = arboles_2020 & np.isin(anuales[anio], [5, 8, 11]) & sigue_cambiado & (perdida == 0)
        perdida[cambio] = anio - 2000
    guardar(perdida, zona["bbox"], RECORTES / clave / "io_perdida.tif",
            descripcion="Impact Observatory LULC anual v02: árboles 2020 a cultivo/suelo/pasto (CC BY 4.0)")


def sentinel2(clave, zona):
    """Mosaicos Sentinel-2 L2A en color verdadero de 2020 (antes) y del último año seco (después).

    Se usa la mediana de las escenas con menos nubes de la estación seca (junio a septiembre)
    y la máscara SCL (nubes 8, 9, 10; sombra 3) como en la sesión 14. Se guardan como JPEG livianos.
    """
    from odc.stac import load
    from PIL import Image
    cat = catalogo()
    oeste, sur, este, norte = zona["bbox"]
    for nombre, rango in [("antes", "2020-06-01/2020-10-31"), ("despues", "2025-06-01/2025-10-31")]:
        items = list(cat.search(collections=["sentinel-2-l2a"], bbox=zona["bbox"], datetime=rango,
                                query={"eo:cloud_cover": {"lt": 40}}).items())
        items = sorted(items, key=lambda i: i.properties["eo:cloud_cover"])[:12]
        # Desde el procesamiento 04.00 (enero de 2022) la reflectancia trae +1000 (BOA_ADD_OFFSET).
        # Para no mezclar, se usan solo las escenas con el mismo tipo de procesamiento que la mayoría.
        nuevas = [i for i in items if float(i.properties.get("s2:processing_baseline", "0")) >= 4]
        viejas = [i for i in items if float(i.properties.get("s2:processing_baseline", "0")) < 4]
        items = nuevas if len(nuevas) >= len(viejas) else viejas
        desfase = 1000 if items is nuevas else 0
        print(f"  S2 {nombre}: {len(items)} escenas, desfase {desfase}")
        ds = load(items, bands=["B04", "B03", "B02", "SCL"], bbox=zona["bbox"], crs="EPSG:4326",
                  resolution=RES, chunks={"x": 2048, "y": 2048})
        malo = ds.SCL.isin([0, 1, 3, 8, 9, 10])
        rgb = []
        for banda in ["B04", "B03", "B02"]:
            valores = ds[banda].where(~malo).astype("float32")
            valores = (valores - desfase).clip(min=0)
            rgb.append(valores.median(dim="time").compute().values)
        rgb = np.stack(rgb, axis=-1)
        rgb = np.nan_to_num(rgb, nan=0)
        imagen = np.clip(rgb / 1500 * 255, 0, 255).astype("uint8")   # estiramiento fijo, igual en antes y después
        ruta = RECORTES / clave / f"s2_{nombre}.jpg"
        Image.fromarray(imagen).save(ruta, quality=80, optimize=True)
        print(f"  {ruta.relative_to(RAIZ)}  {ruta.stat().st_size / 1e6:.1f} MB")


CAPAS = {"jrc": jrc, "worldcover": worldcover, "hansen": hansen, "alertas": glad_s2, "io": impact_observatory,
         "geobosques": geobosques, "legalidad": legalidad, "s2": sentinel2}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--zona", default=None)
    p.add_argument("--capa", default=None)
    args = p.parse_args()
    for clave, zona in ZONAS.items():
        if args.zona and clave != args.zona:
            continue
        print(f"== {zona['nombre']}")
        for nombre, funcion in CAPAS.items():
            if args.capa and nombre != args.capa:
                continue
            try:
                funcion(clave, zona)
            except Exception as error:   # una fuente caída no debe frenar las demás
                print(f"  ERROR en {nombre}: {error}")
    # Índice de zonas que lee la app
    indice = {}
    for clave, zona in ZONAS.items():
        carpeta = RECORTES / clave
        if carpeta.exists():
            indice[clave] = {**zona, "capas": sorted(p.name for p in carpeta.iterdir())}
    (RECORTES / "zonas.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
