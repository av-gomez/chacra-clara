"""Reglas que convierten la evidencia de cada fuente satelital en uno de tres estados.

Los umbrales están aquí, a la vista, para que un técnico pueda revisarlos y cambiarlos.
Por qué estos valores:
  - PERDIDA_MINIMA_HA = 0.1 ha: es poco más que un píxel de Landsat (30 m x 30 m = 0.09 ha) y diez píxeles
    de Sentinel-2 (10 m). Por debajo de eso la señal se confunde con bordes y con errores de registro.
  - Pérdida SIGNIFICATIVA: 0.5 ha (el área mínima de "bosque" en la EUDR) o, en parcelas chicas,
    0.2 ha que sean al menos el 10 % de la parcela. La parcela cafetalera media en el Perú tiene 1.9 ha:
    talar 0.3 ha de bosque en ella sí importa aunque no llegue a 0.5 ha.
  - ACUERDO: para "Posible deforestación" se necesitan al menos dos fuentes independientes que vean
    pérdida dentro de lo que era bosque en 2020. Una sola fuente manda la parcela a "Revisar".
  - PÉRDIDA FUERA DEL BOSQUE 2020: si nadie ve pérdida en bosque, pero sí hay pérdida significativa de árboles
    donde en 2020 no había bosque, la parcela va a "Revisar" (renovación, poda o quema de una chacra existente).
  - CHACRA_PREVIA = 50 %: si la mitad o más de la pérdida cae en píxeles que ESA WorldCover 2020
    marcó como cultivo, pasto o arbustal, lo más probable es una renovación, poda de sombra o quema
    de una chacra existente. No es deforestación según la EUDR (no había bosque), pero se revisa.
"""
from dataclasses import dataclass, field

PERDIDA_MINIMA_HA = 0.1
SIGNIFICATIVA_HA = 0.5
SIGNIFICATIVA_CHICA_HA = 0.2
SIGNIFICATIVA_CHICA_PCT = 10.0
CHACRA_PREVIA_PCT = 50.0
FUENTES_MINIMAS_DE_ACUERDO = 2

SIN = "sin"
REVISAR = "revisar"
POSIBLE = "posible"

ESTADOS = {
    SIN: {"texto": "Sin deforestación detectada", "corto": "Lista", "icono": "✓", "patron": "liso",
          "color": "#1B7A5A", "fondo": "#E3F2EC",
          "que_hacer": "Las fuentes coinciden en que no hubo bosque convertido después de 2020. "
                       "Puede ir en la declaración de debida diligencia. Guarde la evidencia."},
    REVISAR: {"texto": "Revisar", "corto": "Revisar", "icono": "!", "patron": "rayado",
              "color": "#8A5A00", "fondo": "#FFF1D6",
              "que_hacer": "Las fuentes no coinciden, la pérdida es pequeña o puede ser sombra de café, "
                           "renovación, poda o quema de una chacra que ya existía. Un técnico debe visitarla."},
    POSIBLE: {"texto": "Posible deforestación después de 2020", "corto": "Posible deforestación", "icono": "✕",
              "patron": "punteado", "color": "#A12C2C", "fondo": "#F9E1E1",
              "que_hacer": "Dos o más fuentes ven pérdida significativa de bosque después de 2020. "
                           "No la incluya en un envío a Europa hasta que un técnico la verifique en campo."},
}


@dataclass
class Evidencia:
    """Lo que dice una fuente sobre una parcela."""
    fuente: str
    disponible: bool
    perdida_en_bosque_ha: float = 0.0     # pérdida después de 2020 en píxeles que eran bosque en 2020 (JRC)
    perdida_total_ha: float = 0.0         # pérdida después de 2020 en toda la parcela
    anios: dict = field(default_factory=dict)  # {2022: 0.31, ...} hectáreas por año
    nota: str = ""


@dataclass
class Resultado:
    estado: str
    confianza: str
    razones: list
    bosque_2020_ha: float
    bosque_2020_pct: float
    perdida_acordada_ha: float
    anio_principal: int | None


def es_significativa(perdida_ha, area_parcela_ha):
    if perdida_ha >= SIGNIFICATIVA_HA:
        return True
    pct = 100 * perdida_ha / area_parcela_ha if area_parcela_ha > 0 else 0
    return perdida_ha >= SIGNIFICATIVA_CHICA_HA and pct >= SIGNIFICATIVA_CHICA_PCT


def clasificar(area_parcela_ha, bosque_2020_ha, evidencias, perdida_acordada_ha,
               perdida_en_chacra_2020_pct, es_punto, perdida_fuera_bosque_ha=0.0):
    """Devuelve el estado, la confianza y las razones en lenguaje claro.

    perdida_acordada_ha: pérdida en bosque 2020 donde al menos dos fuentes coinciden píxel a píxel.
    perdida_en_chacra_2020_pct: % de la pérdida que cae en cultivo/pasto/arbustal según WorldCover 2020.
    perdida_fuera_bosque_ha: la mayor pérdida (entre fuentes) en partes que NO eran bosque en 2020.
    """
    razones = []
    disponibles = [e for e in evidencias if e.disponible]
    detectan = [e for e in disponibles if e.perdida_en_bosque_ha >= PERDIDA_MINIMA_HA]
    mayor = max([e.perdida_en_bosque_ha for e in disponibles], default=0.0)
    bosque_pct = 100 * bosque_2020_ha / area_parcela_ha if area_parcela_ha > 0 else 0.0

    anios = {}
    for e in detectan:
        for anio, ha in e.anios.items():
            anios[anio] = anios.get(anio, 0) + ha
    anio_principal = max(anios, key=anios.get) if anios else None

    if bosque_2020_ha < PERDIDA_MINIMA_HA:
        razones.append("En 2020 casi no había bosque en la parcela según el mapa de referencia de la UE (JRC).")
    else:
        razones.append(f"En 2020 había {bosque_2020_ha:.2f} ha de bosque ({bosque_pct:.0f} % de la parcela) "
                       "según el mapa de referencia de la UE (JRC).")

    if not detectan and es_significativa(perdida_fuera_bosque_ha, area_parcela_ha):
        estado = REVISAR
        razones.append(f"Hay {perdida_fuera_bosque_ha:.2f} ha con pérdida de árboles después de 2020 en partes que "
                       "en 2020 no eran bosque. Si era chacra, no es deforestación según la EUDR: puede ser renovación "
                       "del cafetal, poda de sombra o quema. Hay que confirmarlo.")
    elif not detectan:
        estado = SIN
        razones.append("Ninguna fuente ve pérdida de bosque después de 2020 por encima de "
                       f"{PERDIDA_MINIMA_HA} ha.")
        if bosque_pct > 60:
            razones.append("La parcela se ve como bosque. Si es café o cacao bajo sombra, guarde pruebas de que el "
                           "sistema agroforestal existía antes de 2021 (fotos, constancias).")
    elif (len(detectan) >= FUENTES_MINIMAS_DE_ACUERDO
          and es_significativa(perdida_acordada_ha, area_parcela_ha)
          and perdida_en_chacra_2020_pct < CHACRA_PREVIA_PCT):
        estado = POSIBLE
        nombres = ", ".join(e.fuente for e in detectan)
        razones.append(f"{len(detectan)} fuentes ({nombres}) coinciden en {perdida_acordada_ha:.2f} ha de "
                       "pérdida de bosque después de 2020.")
    else:
        estado = REVISAR
        if len(detectan) < FUENTES_MINIMAS_DE_ACUERDO:
            razones.append(f"Solo {detectan[0].fuente} ve pérdida ({detectan[0].perdida_en_bosque_ha:.2f} ha); "
                           "las otras fuentes no la confirman.")
        elif not es_significativa(perdida_acordada_ha, area_parcela_ha):
            razones.append(f"Las fuentes coinciden solo en {perdida_acordada_ha:.2f} ha: es una pérdida "
                           "marginal (puede ser poda de sombra, un árbol caído o un borde).")
        if perdida_en_chacra_2020_pct >= CHACRA_PREVIA_PCT:
            razones.append(f"El {perdida_en_chacra_2020_pct:.0f} % de la pérdida cae donde en 2020 ya había "
                           "cultivo o pasto (ESA WorldCover): puede ser renovación del cafetal, poda o quema "
                           "de una chacra existente.")
        if bosque_pct > 60:
            razones.append("Gran parte de la parcela se ve como bosque: puede ser café o cacao bajo sombra "
                           "(sistema agroforestal). Hay que confirmarlo en campo.")

    # Confianza: cuántas fuentes había y qué tan de acuerdo están
    faltan = [e.fuente for e in evidencias if not e.disponible]
    if estado == SIN:
        confianza = "alta" if not faltan and mayor < PERDIDA_MINIMA_HA / 2 else "media"
    elif estado == POSIBLE:
        confianza = "alta" if perdida_acordada_ha >= 0.5 * mayor and not faltan else "media"
    else:
        confianza = "baja" if len(detectan) == 1 and mayor >= SIGNIFICATIVA_HA else "media"
    if es_punto:
        razones.append("La parcela es un punto: se analizó un círculo con el área declarada. "
                       "Un polígono daría un resultado más preciso.")
        if confianza == "alta":
            confianza = "media"
    if faltan:
        razones.append(f"Sin datos de: {', '.join(faltan)}.")
    return Resultado(estado, confianza, razones, round(bosque_2020_ha, 3), round(bosque_pct, 1),
                     round(perdida_acordada_ha, 3), anio_principal)
