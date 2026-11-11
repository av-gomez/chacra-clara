"""Mapas con Folium (sesión 06 del curso).

- Mapa de ingreso: imagen satelital de fondo, las zonas del demo y la herramienta de dibujo.
- Mapa de resultados: cada parcela con su estado en color Y patrón (liso, rayado, punteado),
  capas de bosque 2020 y pérdida después de 2020, y alertas de legalidad del SERNANP.
Todo mapa va acompañado en la app de una tabla equivalente y un resumen en texto.
"""
import base64
import io

import folium
import geopandas as gpd
import numpy as np
import rasterio
from folium.plugins import Draw, Fullscreen
from folium.plugins.pattern import CirclePattern, StripePattern
from PIL import Image

from chacra.estado import ESTADOS
from chacra.rutas import RECORTES
from chacra.satelite import zonas_disponibles

SATELITE = ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
ATRIBUCION_SATELITE = "Imágenes: Esri, Maxar, Earthstar Geographics"


def mapa_base(centro, zoom, ligero=False):
    m = folium.Map(location=centro, zoom_start=zoom, tiles=None, control_scale=True)
    if not ligero:
        folium.TileLayer(SATELITE, attr=ATRIBUCION_SATELITE, name="Imagen satelital", max_zoom=19).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Mapa de calles (más liviano)", show=ligero).add_to(m)
    Fullscreen(title="Pantalla completa", title_cancel="Salir de pantalla completa").add_to(m)
    return m


def agregar_zonas(m):
    for clave, zona in zonas_disponibles().items():
        oeste, sur, este, norte = zona["bbox"]
        folium.Rectangle([[sur, oeste], [norte, este]], color="#F2C14E", weight=2, fill=False, dash_array="6 6",
                         tooltip=f"Zona con datos precalculados: {zona['nombre']}").add_to(m)


def mapa_ingreso(centro, zoom, parcelas=None, ligero=False):
    """Mapa para dibujar. Se encuadra a nivel de chacra (~1 km) para que el polígono tenga pocas hectáreas."""
    m = mapa_base(centro, zoom, ligero)
    m.fit_bounds([[centro[0] - 0.0045, centro[1] - 0.006], [centro[0] + 0.0045, centro[1] + 0.006]])
    agregar_zonas(m)
    if parcelas is not None and len(parcelas):
        folium.GeoJson(parcelas[["codigo_parcela", "geometry"]].to_json(), name="Parcelas cargadas",
                       style_function=lambda f: {"color": "#FFFFFF", "weight": 2, "fillOpacity": 0.1},
                       marker=folium.CircleMarker(radius=6, color="#FFFFFF", fill=True),
                       tooltip=folium.GeoJsonTooltip(["codigo_parcela"], aliases=["Parcela"])).add_to(m)
    Draw(export=False, position="topleft",
         draw_options={"polyline": False, "rectangle": False, "circle": False, "circlemarker": False,
                       "polygon": {"allowIntersection": False, "showArea": True,
                                   "shapeOptions": {"color": "#F2C14E", "weight": 3}},
                       "marker": True},
         edit_options={"edit": False, "remove": False}).add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    return m


def _patrones(m):
    """Un patrón distinto por estado, para que se distingan sin ver colores."""
    rayado = StripePattern(angle=45, weight=3, space_weight=4, color=ESTADOS["revisar"]["color"],
                           space_color="#ffffff", opacity=0.9, space_opacity=0.25)
    punteado = CirclePattern(width=10, height=10, radius=3, fill_color=ESTADOS["posible"]["color"],
                             color=ESTADOS["posible"]["color"], fill_opacity=1, opacity=1)
    rayado.add_to(m)
    punteado.add_to(m)
    return {"revisar": rayado, "posible": punteado}


def imagen_capa(zona, archivo, colorear):
    """Convierte un recorte en una imagen PNG transparente para superponerla en el mapa."""
    ruta = RECORTES / zona / archivo
    if not ruta.exists():
        return None, None
    with rasterio.open(ruta) as src:
        datos = src.read(1)
        b = src.bounds
    rgba = colorear(datos)
    buffer = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buffer, format="PNG", optimize=True)
    url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    return url, [[b.bottom, b.left], [b.top, b.right]]


def _color_bosque(datos):
    rgba = np.zeros(datos.shape + (4,), dtype="uint8")
    rgba[datos == 1] = (16, 120, 80, 110)
    return rgba


def _color_perdida(datos):
    rgba = np.zeros(datos.shape + (4,), dtype="uint8")
    rgba[(datos > 20) & (datos != 255)] = (255, 0, 200, 150)   # magenta: distinto de los tres estados
    return rgba


def agregar_capas_raster(m, zona, ligero=False):
    if ligero:
        return
    capas = [("jrc_bosque2020.tif", "Bosque en 2020 (JRC, mapa de referencia de la UE)", _color_bosque, False),
             ("hansen_perdida.tif", "Pérdida después de 2020: Hansen/UMD (30 m)", _color_perdida, True),
             ("alertas_perdida.tif", "Pérdida después de 2020: alertas GLAD-S2 (10 m)", _color_perdida, False),
             ("io_perdida.tif", "Pérdida después de 2020: Impact Observatory (10 m)", _color_perdida, False),
             ("geobosques_perdida.tif", "Pérdida después de 2020: Geobosques MINAM (30 m)", _color_perdida, False)]
    for archivo, nombre, colorear, visible in capas:
        url, limites = imagen_capa(zona, archivo, colorear)
        if url:
            folium.raster_layers.ImageOverlay(url, bounds=limites, name=nombre, show=visible,
                                              interactive=False).add_to(m)


def agregar_legalidad(m, zona):
    ruta = RECORTES / zona / "legalidad.geojson"
    if not ruta.exists():
        return
    capa = gpd.read_file(ruta)
    if len(capa) == 0:
        return
    folium.GeoJson(capa.to_json(), name="Áreas protegidas y comunidades nativas (SERNANP)", show=True,
                   style_function=lambda f: {"color": "#7FB3FF", "weight": 2, "dashArray": "2 6",
                                             "fillOpacity": 0.05},
                   tooltip=folium.GeoJsonTooltip(["tipo", "nombre"], aliases=["Tipo", "Nombre"])).add_to(m)


def mapa_resultados(parcelas, ligero=False, seleccion=None):
    """parcelas: GeoDataFrame con columnas codigo_parcela, estado, texto_estado, confianza."""
    elegida = parcelas[parcelas["codigo_parcela"] == seleccion]
    if len(elegida) == 0 or elegida["zona"].isna().all():
        elegida = parcelas[parcelas["zona"].notna()].head(1)
    oeste, sur, este, norte = elegida.total_bounds
    m = mapa_base([(sur + norte) / 2, (oeste + este) / 2], 15, ligero)
    # Solo las capas de la zona de la parcela elegida: menos datos para un celular con poca señal
    for zona in elegida["zona"].dropna().unique():
        agregar_capas_raster(m, zona, ligero)
        agregar_legalidad(m, zona)
    patrones = _patrones(m)

    def estilo(feature):
        estado = feature["properties"]["estado"]
        color = ESTADOS[estado]["color"] if estado in ESTADOS else "#666666"
        elegido = feature["properties"]["codigo_parcela"] == seleccion
        base = {"color": "#FFFFFF" if elegido else color, "weight": 5 if elegido else 3, "fillOpacity": 0.55,
                "fillColor": color}
        if estado in patrones:
            base["fillPattern"] = patrones[estado]
        return base

    datos = parcelas[["codigo_parcela", "codigo_productor", "estado", "texto_estado", "confianza",
                      "geometry"]].copy()
    datos["estado"] = datos["estado"].fillna("fuera")
    datos["texto_estado"] = datos["texto_estado"].fillna("Fuera de las zonas del demo")
    datos["confianza"] = datos["confianza"].fillna("—")
    poligonos = datos[datos.geometry.geom_type != "Point"]
    puntos = datos[datos.geometry.geom_type == "Point"]
    campos = ["codigo_parcela", "texto_estado", "confianza"]
    alias = ["Parcela", "Estado", "Confianza"]
    if len(poligonos):
        folium.GeoJson(poligonos.to_json(), name="Parcelas", style_function=estilo,
                       tooltip=folium.GeoJsonTooltip(campos, aliases=alias)).add_to(m)
    for _, fila in puntos.iterrows():
        estado = ESTADOS.get(fila["estado"], {"color": "#666666", "icono": "?"})
        html = (f'<div style="background:{estado["color"]};color:#fff;border:2px solid #fff;border-radius:50%;'
                f'width:26px;height:26px;display:flex;align-items:center;justify-content:center;'
                f'font-weight:700;font-size:15px" aria-hidden="true">{estado["icono"]}</div>')
        folium.Marker([fila.geometry.y, fila.geometry.x], icon=folium.DivIcon(html=html, icon_size=(26, 26),
                                                                               icon_anchor=(13, 13)),
                      tooltip=f"{fila['codigo_parcela']}: {fila['texto_estado']}").add_to(m)
    margen = 0.002   # unos 220 m alrededor de la parcela elegida, para ver su entorno
    m.fit_bounds([[sur - margen, oeste - margen], [norte + margen, este + margen]])
    folium.LayerControl(collapsed=True).add_to(m)
    return m


def recorte_imagen(zona, cuando, geom, margen=0.0025, tam=360):
    """Recorta el mosaico Sentinel-2 (antes o después) alrededor de la parcela y dibuja su contorno."""
    from PIL import ImageDraw
    ruta = RECORTES / zona / f"s2_{cuando}.jpg"
    zonas = zonas_disponibles()
    if not ruta.exists() or zona not in zonas:
        return None
    oeste, sur, este, norte = zonas[zona]["bbox"]
    imagen = Image.open(ruta)
    ancho, alto = imagen.size

    def a_pixel(x, y):
        return (x - oeste) / (este - oeste) * ancho, (norte - y) / (norte - sur) * alto
    gx0, gy0, gx1, gy1 = geom.bounds
    lado = max(gx1 - gx0, gy1 - gy0) / 2 + margen
    cx, cy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
    px0, py0 = a_pixel(cx - lado, cy + lado)
    px1, py1 = a_pixel(cx + lado, cy - lado)
    recorte = imagen.crop((int(px0), int(py0), int(px1), int(py1))).resize((tam, tam), Image.NEAREST)
    dibujo = ImageDraw.Draw(recorte)
    escala = tam / (px1 - px0)
    contornos = [geom] if geom.geom_type in ("Polygon", "Point") else list(geom.geoms)
    for g in contornos:
        if g.geom_type == "Point":
            x, y = a_pixel(g.x, g.y)
            x, y = (x - px0) * escala, (y - py0) * escala
            dibujo.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(255, 214, 10), width=3)
            continue
        puntos = [((a_pixel(x, y)[0] - px0) * escala, (a_pixel(x, y)[1] - py0) * escala)
                  for x, y in g.exterior.coords]
        dibujo.line(puntos, fill=(255, 214, 10), width=3)
    buffer = io.BytesIO()
    recorte.save(buffer, format="PNG")
    return buffer.getvalue()
