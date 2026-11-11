"""Pruebas del flujo principal sin navegador: python -m pytest tests/ (o python tests/test_flujo.py)."""
import io
import json
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from chacra import cooperativa, exportar, geometria, informe, mapas, voz  # noqa: E402


def demo(clave="puno"):
    datos = json.loads((RAIZ / "datos" / "parcelas" / "demo.geojson").read_text(encoding="utf-8"))
    datos["features"] = [f for f in datos["features"] if f["properties"]["cooperativa"] == clave]
    return cooperativa.analizar_todas(geometria.validar(geometria.desde_geojson(datos)))


def test_demo_tiene_los_tres_estados():
    for clave in ["puno", "sanmartin"]:
        gdf = demo(clave)
        assert set(gdf["estado"]) == {"sin", "revisar", "posible"}


def test_fichas_reporte_zip_y_geojson():
    gdf = demo()
    resumen = cooperativa.resumen(gdf)
    for _, fila in gdf.iterrows():
        pdf = exportar.ficha_pdf(fila, fila["analisis"])
        assert pdf[:4] == b"%PDF"
    assert exportar.reporte_cooperativa_pdf("Prueba", gdf, resumen)[:4] == b"%PDF"
    z = zipfile.ZipFile(io.BytesIO(exportar.zip_todos_los_datos(gdf, resumen)))
    assert "parcelas_eudr.geojson" in z.namelist()
    ue = json.loads(exportar.geojson_eudr(gdf))
    assert ue["type"] == "FeatureCollection"
    for f in ue["features"]:
        assert set(f["properties"]) >= {"ProducerName", "ProducerCountry", "ProductionPlace"}
        assert f["geometry"]["type"] in ("Point", "Polygon", "MultiPolygon")
        if f["geometry"]["type"] == "Point":
            assert isinstance(f["properties"]["Area"], float)


def test_ficha_con_imagenes():
    gdf = demo()
    fila = gdf.iloc[0]
    a = fila["analisis"]
    imgs = {"antes": mapas.recorte_imagen(a["zona"], "antes", fila.geometry),
            "despues": mapas.recorte_imagen(a["zona"], "despues", fila.geometry)}
    assert exportar.ficha_pdf(fila, a, imgs)[:4] == b"%PDF"


def test_informe_plantilla_y_ruta():
    gdf = demo()
    r = cooperativa.resumen(gdf)
    inf = informe.informe_plantilla(informe.datos_para_informe("Prueba", gdf, r))
    assert inf.nivel_riesgo == "alto"
    assert len(inf.hallazgos) == r["revisar"] + r["posible"]
    orden = cooperativa.prioridades(gdf, (-14.2238, -69.1527))
    assert list(orden["estado"])[0].startswith("Posible")


def test_notas_de_voz_existen_para_cada_estado():
    for estado in ["sin", "revisar", "posible"]:
        for cultivo in ["café", "cacao"]:
            ruta, _, _ = voz.audio_para("NUEVA-1", cultivo, estado)
            assert ruta is not None and ruta.exists()


def test_validacion_detecta_errores():
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"codigo_productor": "A", "area_ha": 6},
         "geometry": {"type": "Point", "coordinates": [-69.185402, -14.183311]}},
        {"type": "Feature", "properties": {"codigo_productor": "B", "area_ha": 1},
         "geometry": {"type": "Point", "coordinates": [-3.703790, 40.416775]}}]}
    v = geometria.validar(geometria.desde_geojson(fc))
    assert not v.loc[0, "valida"] and not v.loc[1, "valida"]


class Archivo:
    """Imita el archivo que entrega st.file_uploader."""
    def __init__(self, nombre, contenido):
        self.name = nombre
        self._contenido = contenido

    def getvalue(self):
        return self._contenido


def test_plantilla_csv_se_lee_y_analiza():
    gdf = geometria.leer_archivo(Archivo("plantilla.csv", geometria.plantilla_csv()))
    v = cooperativa.analizar_todas(geometria.validar(gdf))
    assert len(v) == 2 and v["valida"].all() and v["estado"].notna().all()


def test_kml_se_lee():
    kml = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>K-1</name><Polygon><outerBoundaryIs>
<LinearRing><coordinates>-69.150101,-14.200101,0 -69.148101,-14.200101,0 -69.148101,-14.198101,0
-69.150101,-14.198101,0 -69.150101,-14.200101,0</coordinates></LinearRing></outerBoundaryIs></Polygon>
</Placemark></Document></kml>"""
    v = geometria.validar(geometria.leer_archivo(Archivo("parcela.kml", kml)))
    assert v.loc[0, "codigo_parcela"] == "K-1" and v.loc[0, "valida"]
    assert 4 < v.loc[0, "area_calculada_ha"] < 5


if __name__ == "__main__":
    for nombre, prueba in list(globals().items()):
        if nombre.startswith("test_"):
            prueba()
            print("ok", nombre)
