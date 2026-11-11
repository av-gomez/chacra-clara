"""Reglas que convierten la evidencia satelital en uno de tres estados. Umbrales a la vista.

Principios (versión 2, 11/11/2026):
  1. El mapa JRC GFC2020 NO es la verdad: la propia Comisión Europea dice que no es obligatorio ni vinculante,
     y en la selva alta confunde café y cacao bajo sombra con bosque. Para "Posible deforestación" se exige
     además evidencia de BOSQUE NATURAL en 2020 (capa Natural Forests of the World 2020 y altura del dosel).
  2. Las fuentes se cuentan por TIPO DE SENSOR, no por nombre: Hansen y Geobosques usan Landsat con métodos
     parecidos (una sola confirmación); GLAD-S2 e Impact Observatory usan Sentinel-2. Se necesitan dos sensores.
  3. Una fuente que no cubre el año de la pérdida dice "sin datos para ese periodo" y no cuenta en contra.
  4. Si la cooperativa declaró una renovación del cafetal en el año de la pérdida (±1 año), va a "Revisar".
  5. "Sin deforestación detectada" no significa que pueda ir a Europa: la legalidad queda pendiente.

Umbrales:
  - PERDIDA_MINIMA_HA = 0,1 ha: poco más que un píxel de Landsat (0,09 ha); por debajo se confunde con bordes.
  - Pérdida SIGNIFICATIVA: 0,5 ha (área mínima de "bosque" en la EUDR) o 0,2 ha que sean al menos el 10 % de
    la parcela (la parcela cafetalera media mide 1,9 ha).
  - CHACRA_PREVIA = 50 %: si la mitad de la pérdida cae donde ESA WorldCover 2020 ya marcaba cultivo o pasto.
"""
from dataclasses import dataclass, field

from chacra.formato import ha, num, pct

PERDIDA_MINIMA_HA = 0.1
SIGNIFICATIVA_HA = 0.5
SIGNIFICATIVA_CHICA_HA = 0.2
SIGNIFICATIVA_CHICA_PCT = 10.0
CHACRA_PREVIA_PCT = 50.0
SENSORES_MINIMOS = 2
TOLERANCIA_RENOVACION_ANIOS = 1

SIN = "sin"
REVISAR = "revisar"
POSIBLE = "posible"

ESTADOS = {
    SIN: {"texto": "Sin deforestación detectada", "corto": "Sin deforestación detectada", "icono": "✓",
          "patron": "liso", "color": "#1B6B4F", "fondo": "#E3F2EC",
          "que_hacer": "Las fuentes satelitales no ven bosque convertido después de 2020. Esto no basta para "
                       "vender a Europa: falta verificar la legalidad (tenencia, permisos, derechos de terceros). "
                       "Guarde la evidencia en el expediente."},
    REVISAR: {"texto": "Revisar", "corto": "Revisar", "icono": "!", "patron": "rayado",
              "color": "#7A4F00", "fondo": "#FFF1D6",
              "que_hacer": "Visita recomendada. Las fuentes no alcanzan para decidir: puede ser café o cacao bajo "
                           "sombra, una renovación, una poda o una pérdida pequeña. El motivo concreto está abajo."},
    POSIBLE: {"texto": "Posible deforestación después de 2020", "corto": "Posible deforestación", "icono": "✕",
              "patron": "punteado", "color": "#A12C2C", "fondo": "#F9E1E1",
              "que_hacer": "Visita recomendada con prioridad alta. Dos tipos de sensor ven pérdida significativa "
                           "en lo que era bosque natural en 2020. No la incluya en un envío a Europa hasta que un "
                           "técnico la verifique en campo."},
}


@dataclass
class Evidencia:
    """Lo que dice una fuente de pérdida sobre una parcela."""
    fuente: str
    sensor: str
    disponible: bool
    cubre_hasta: int = 2025
    perdida_en_bosque_ha: float = 0.0     # pérdida después de 2020 donde el JRC marcaba bosque en 2020
    perdida_total_ha: float = 0.0
    anios: dict = field(default_factory=dict)
    sin_datos_periodo: bool = False       # la pérdida ocurrió después del último año que cubre esta fuente
    nota: str = ""


@dataclass
class Natural:
    """Evidencia de bosque natural en 2020 (para no confundirlo con café o cacao bajo sombra)."""
    disponible: bool = False
    bosque_natural_ha: float = 0.0        # parte de la parcela que era bosque natural en 2020
    perdida_en_natural_ha: float = 0.0    # pérdida acordada que cae en bosque natural
    altura_media_m: float | None = None   # altura del dosel 2020 donde hubo pérdida
    sombra_probable: bool = False
    razones_sombra: list = field(default_factory=list)


@dataclass
class Resultado:
    estado: str
    confianza: str
    razones: list
    motivo: str
    bosque_2020_ha: float
    bosque_2020_pct: float
    perdida_acordada_ha: float
    anio_principal: int | None


def es_significativa(perdida_ha, area_parcela_ha):
    if perdida_ha >= SIGNIFICATIVA_HA:
        return True
    porcentaje = 100 * perdida_ha / area_parcela_ha if area_parcela_ha > 0 else 0
    return perdida_ha >= SIGNIFICATIVA_CHICA_HA and porcentaje >= SIGNIFICATIVA_CHICA_PCT


def clasificar(area_parcela_ha, bosque_2020_ha, evidencias, perdida_acordada_ha, perdida_en_chacra_2020_pct,
               es_punto, perdida_fuera_bosque_ha, natural, renovacion_anio=None):
    """Devuelve el estado, la confianza, las razones en lenguaje claro y el motivo corto."""
    razones = []
    utiles = [e for e in evidencias if e.disponible and not e.sin_datos_periodo]
    detectan = [e for e in utiles if e.perdida_en_bosque_ha >= PERDIDA_MINIMA_HA]
    sensores = sorted({e.sensor for e in detectan})
    mayor = max([e.perdida_en_bosque_ha for e in utiles], default=0.0)
    bosque_pct = 100 * bosque_2020_ha / area_parcela_ha if area_parcela_ha > 0 else 0.0

    anios = {}
    for e in detectan:
        for anio, hectareas in e.anios.items():
            anios[anio] = anios.get(anio, 0) + hectareas
    anio_principal = max(anios, key=anios.get) if anios else None

    if bosque_2020_ha < PERDIDA_MINIMA_HA:
        razones.append("En 2020 casi no había cobertura de bosque en la parcela según el mapa JRC de la UE.")
    else:
        razones.append(f"El mapa JRC de la UE marca {ha(bosque_2020_ha)} de cobertura de bosque en 2020 "
                       f"({pct(bosque_pct)} de la parcela). Ese mapa no es vinculante y puede confundir café o "
                       "cacao bajo sombra con bosque.")

    renovo = (renovacion_anio is not None and anio_principal is not None
              and abs(int(renovacion_anio) - anio_principal) <= TOLERANCIA_RENOVACION_ANIOS)

    if not detectan:
        if es_significativa(perdida_fuera_bosque_ha, area_parcela_ha):
            estado, motivo = REVISAR, "Pérdida de árboles en chacra existente (posible renovación o poda)"
            razones.append(f"Hay {ha(perdida_fuera_bosque_ha)} con pérdida de árboles después de 2020 en partes que "
                           "en 2020 no eran bosque. Si era chacra, no es deforestación según la EUDR: puede ser "
                           "renovación del cafetal, poda de sombra o quema. Hay que confirmarlo.")
        else:
            estado, motivo = SIN, "Ninguna fuente ve pérdida de bosque después de 2020"
            razones.append(f"Ninguna fuente ve pérdida de bosque después de 2020 por encima de "
                           f"{ha(PERDIDA_MINIMA_HA, 1)}.")
            if bosque_pct > 60:
                razones.append("Si la parcela es café o cacao bajo sombra, guarde pruebas de que el sistema "
                               "agroforestal existía antes de 2021 (fotos, constancias).")
    else:
        dos_sensores = len(sensores) >= SENSORES_MINIMOS and es_significativa(perdida_acordada_ha, area_parcela_ha)
        bosque_natural = (natural.disponible and not natural.sombra_probable
                          and es_significativa(natural.perdida_en_natural_ha, area_parcela_ha))
        chacra = perdida_en_chacra_2020_pct >= CHACRA_PREVIA_PCT
        if dos_sensores and bosque_natural and not chacra and not renovo:
            estado, motivo = POSIBLE, "Dos sensores ven pérdida en bosque natural"
            razones.append(f"Dos tipos de sensor ({' y '.join(sensores)}) coinciden en {ha(perdida_acordada_ha)} de "
                           "pérdida después de 2020.")
            razones.append(f"De esa pérdida, {ha(natural.perdida_en_natural_ha)} cae en bosque natural según "
                           "Natural Forests of the World 2020"
                           + (f" (dosel de {num(natural.altura_media_m, 0)} m en 2020)." if natural.altura_media_m
                              else "."))
        else:
            estado = REVISAR
            motivos = []
            if renovo:
                motivos.append("Renovación declarada en el año de la pérdida")
                razones.append(f"La cooperativa declaró una renovación del cafetal en {renovacion_anio}, el mismo "
                               f"periodo de la pérdida ({anio_principal}). Una renovación no es deforestación: "
                               "el técnico debe confirmarla con fotos y el testimonio del productor.")
            if not natural.disponible:
                motivos.append("Sin capa de bosque natural para confirmar")
                razones.append("No hay datos de bosque natural para esta zona: no se puede descartar café bajo sombra.")
            elif natural.sombra_probable or not es_significativa(natural.perdida_en_natural_ha, area_parcela_ha):
                motivos.append("Probable café o cacao bajo sombra")
                detalle = "; ".join(natural.razones_sombra) or (
                    f"solo {ha(natural.perdida_en_natural_ha)} de la pérdida cae en bosque natural")
                razones.append(f"Probable café o cacao bajo sombra: {detalle}. La pérdida puede ser renovación o "
                               "poda, que no son deforestación.")
            if len(sensores) < SENSORES_MINIMOS:
                motivos.append(f"Solo un tipo de sensor ({sensores[0]}) ve pérdida")
                nombres = ", ".join(f"{e.fuente} ({ha(e.perdida_en_bosque_ha)})" for e in detectan)
                razones.append(f"Solo un tipo de sensor ({sensores[0]}) ve pérdida: {nombres}. Falta la confirmación "
                               "de otro sensor.")
            elif not es_significativa(perdida_acordada_ha, area_parcela_ha):
                motivos.append("Pérdida marginal")
                razones.append(f"Los dos sensores coinciden solo en {ha(perdida_acordada_ha)}: es una pérdida "
                               "marginal (poda de sombra, un árbol caído o un borde).")
            if chacra:
                motivos.append("La pérdida cae en chacra existente")
                razones.append(f"El {pct(perdida_en_chacra_2020_pct)} de la pérdida cae donde en 2020 ya había "
                               "cultivo o pasto (ESA WorldCover): puede ser renovación, poda o quema de una chacra.")
            prioridad = ["Renovación", "Solo un tipo", "Pérdida marginal", "Probable café", "La pérdida cae", "Sin capa"]
            motivos.sort(key=lambda m: next((i for i, p in enumerate(prioridad) if m.startswith(p)), 99))
            motivo = motivos[0] if motivos else "Evidencia insuficiente"

    sin_datos = [e.fuente for e in evidencias if e.disponible and e.sin_datos_periodo]
    if sin_datos:
        razones.append(f"Sin datos para ese periodo (no cuentan en contra): {', '.join(sin_datos)}.")

    # Confianza
    faltan = [e.fuente for e in evidencias if not e.disponible]
    if estado == SIN:
        confianza = "alta" if not faltan and mayor < PERDIDA_MINIMA_HA / 2 and natural.disponible else "media"
    elif estado == POSIBLE:
        confianza = "alta" if perdida_acordada_ha >= 0.5 * mayor and len(detectan) >= 3 else "media"
    else:
        confianza = "baja" if len(sensores) == 1 and mayor >= SIGNIFICATIVA_HA else "media"
    if es_punto:
        razones.append("La parcela es un punto: se analizó un círculo con el área declarada. Un polígono sería "
                       "más preciso.")
        if confianza == "alta":
            confianza = "media"
    if faltan:
        razones.append(f"Sin datos de: {', '.join(faltan)}.")
    if estado == SIN:
        razones.append("Legalidad pendiente de verificar (tenencia, permisos y derechos de terceros).")
    return Resultado(estado, confianza, razones, motivo, round(bosque_2020_ha, 3), round(bosque_pct, 1),
                     round(perdida_acordada_ha, 3), anio_principal)
