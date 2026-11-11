"""Rutas de las carpetas del proyecto, para no repetirlas en cada módulo."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
RECORTES = DATOS / "recortes"
PARCELAS = DATOS / "parcelas"
AUDIOS = RAIZ / "audios"
