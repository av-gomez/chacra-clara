"""Notas de voz para cada productor, con la voz clonada de Amanda (sesión 15 del curso).

La app arma el texto de la nota (frases cortas, sin siglas, sin cifras difíciles).
El audio se genera con scripts/generar_voz.py (Qwen3-TTS en un entorno local) y queda en audios/.
En el servidor gratuito no se genera en vivo: el modelo pesa 2.3 GB y en CPU tarda unos 7 segundos
de cálculo por cada segundo de audio. Por eso las notas del demo vienen pregeneradas.

Quechua y aimara: el texto NO se traduce automáticamente. datos/traducciones.json tiene un campo por
idioma que solo se llena cuando un hablante lo escribe y lo valida.
"""
import json

from chacra.rutas import AUDIOS, DATOS

PLANTILLAS = {
    "sin": ("Hola. Le habla Chacra Clara, de parte de su cooperativa. "
            "Revisamos su parcela{codigo} con imágenes de satélite de varios años. "
            "No encontramos pérdida de bosque después del año 2020. "
            "Todavía falta revisar otros papeles, como la posesión de la tierra, antes de vender su {cultivo} a Europa. "
            "Guarde este audio. Si cambia el tamaño de su chacra, avise a su técnico."),
    "revisar": ("Hola. Le habla Chacra Clara, de parte de su cooperativa. "
                "Revisamos su parcela{codigo} con imágenes de satélite. "
                "Vemos un cambio en una parte de la chacra, pero no estamos seguros de qué es. "
                "Puede ser la sombra de su {cultivo}, una renovación o una poda. "
                "La cooperativa le recomienda la visita de un técnico. "
                "Si renovó o podó su chacra, cuénteselo y muéstrele fotos antiguas. No se preocupe: es solo una revisión."),
    "posible": ("Hola. Le habla Chacra Clara, de parte de su cooperativa. "
                "Revisamos su parcela{codigo} con imágenes de satélite. "
                "Varias fuentes muestran que una parte del bosque se cortó después del año 2020. "
                "Por ahora, el {cultivo} de esa parcela no debe ir a Europa. "
                "La cooperativa le recomienda con prioridad la visita de un técnico para confirmar qué pasó. "
                "Si la parte cortada ya era chacra antes, cuénteselo y muéstrele fotos o documentos."),
}

IDIOMAS = {"es": "Castellano", "qu": "Quechua", "ay": "Aimara"}


def cultivo_simple(cultivo):
    return "cacao" if "cacao" in str(cultivo) else "café"


def texto_nota(codigo_parcela, cultivo, estado):
    """Texto de la nota. Sin código de parcela, sirve como nota general para cualquier parcela nueva."""
    codigo = f" {_codigo_hablado(codigo_parcela)}" if codigo_parcela else ""
    return PLANTILLAS[estado].format(codigo=codigo, cultivo=cultivo_simple(cultivo))


def id_nota_general(estado, cultivo):
    return f"general_{estado}_{cultivo_simple(cultivo).replace('é', 'e')}"


def _codigo_hablado(codigo):
    """'SAN-03' se lee mejor como 'SAN 03' (sin guion)."""
    return str(codigo).replace("-", " ")


def traducciones():
    """Traducciones validadas por hablantes. Si un idioma no tiene texto validado, queda en None."""
    ruta = DATOS / "traducciones.json"
    if not ruta.exists():
        return {}
    return json.loads(ruta.read_text(encoding="utf-8"))


def audio_para(codigo_parcela, cultivo, estado):
    """Devuelve (ruta_mp3, texto, es_personal). Primero busca la nota de esa parcela;
    si no existe, la nota general de su estado y cultivo (pregenerada con la misma voz)."""
    texto = texto_nota(codigo_parcela, cultivo, estado)
    ruta = audio_de(codigo_parcela, texto)
    if ruta:
        return ruta, texto, True
    texto_general = texto_nota(None, cultivo, estado)
    return audio_de(id_nota_general(estado, cultivo), texto_general), texto_general, False


def audio_de(codigo_parcela, texto):
    """Ruta del MP3 pregenerado si existe y corresponde al mismo texto; si no, None."""
    import hashlib
    registro_ruta = AUDIOS / "generadas.json"
    if not registro_ruta.exists():
        return None
    registro = json.loads(registro_ruta.read_text(encoding="utf-8"))
    ruta = AUDIOS / f"{codigo_parcela}.mp3"
    huella = hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12]
    if codigo_parcela in registro and registro[codigo_parcela]["huella"] == huella and ruta.exists():
        return ruta
    return None
