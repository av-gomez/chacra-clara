# Validación del método

Generado por `scripts/validar_metodo.py`. Cada fila es una parcela de prueba en un lugar real.

## 1. Contra el caso buscado (comprueba que las reglas hacen lo que dicen)

| caso_buscado   |   posible |   revisar |   sin |
|:---------------|----------:|----------:|------:|
| chacra_antigua |         0 |         0 |    13 |
| intacto        |         0 |         0 |    18 |
| perdida_clara  |        12 |         6 |     0 |
| renovacion     |         0 |         7 |     4 |
| sombra         |         0 |         0 |    11 |
| una_fuente     |         0 |        11 |     7 |

Aciertos: **83 de 89** (93 %). Para «una fuente», «sombra» y «renovación» se aceptan dos estados (ver `ESPERADO` en el script).

## 2. Contra la revisión visual de Sentinel-2 (independiente de las reglas)

| referencia          |   posible |   revisar |   sin |
|:--------------------|----------:|----------:|------:|
| pérdida visible     |         5 |         4 |     0 |
| sin pérdida visible |         2 |         9 |    52 |

- Pérdidas visibles: 9. La app las marca como «Posible deforestación» en **5** y como «Posible» o «Revisar» en **9** (falsos negativos: 0).
- Parcelas sin pérdida visible: 63. La app marca **2** como «Posible deforestación» (falsos positivos fuertes) y **9** como «Revisar» (alarmas que se resuelven con una visita).
- Casos dudosos a ojo (excluidos del cálculo): 17.

### Desacuerdos con la revisión visual

| Parcela | Caso buscado | Referencia visual | Estado de la app | Nota |
|---|---|---|---|---|
| CAR-PER-35 | perdida_clara | sin pérdida visible | posible |  |
| ALT-PER-63 | perdida_clara | sin pérdida visible | posible |  |
