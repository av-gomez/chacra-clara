# Texto para el comentario del issue #204

Comentario publicado el 10/11/2026: https://github.com/d2cml-ai/Data-Science-Python/issues/204#issuecomment-6784395678

Versión publicada:

```
Nombre: Amanda Gomez
Startup y one-liner: **Chacra Clara**. Hacemos que el café y el cacao de los pequeños productores peruanos puedan seguir entrando a Europa, para cooperativas y exportadoras, mediante un tamizaje satelital abierto de cada parcela que se convierte en el expediente de debida diligencia que pide la EUDR.
Link del demo (URL pública, o "corre en local"): https://chacra-clara.streamlit.app
Link del repo: https://github.com/av-gomez/chacra-clara
Herramientas del curso que usa: raster y datos satelitales (sesión 07: chacra/satelite.py), GeoPandas y Folium (sesión 06: chacra/geometria.py y chacra/mapas.py), texto a voz con mi voz clonada (sesión 15: scripts/generar_voz.py y chacra/voz.py); extra: LLM con salida estructurada (sesión 08: chacra/informe.py)
Video de respaldo: https://github.com/av-gomez/chacra-clara/blob/main/video/demo_respaldo.mp4
```

Para editarlo desde la terminal:

```bash
gh api -X PATCH repos/d2cml-ai/Data-Science-Python/issues/comments/6784395678 -f body="$(sed -n '/^```$/,/^```$/p' docs/issue-comentario.md | sed '1d;$d' | head -7)"
```
