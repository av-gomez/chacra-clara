# Parcela real (opcional, solo con consentimiento)

> **Estado: VACÍO.** Este archivo queda listo para agregar **una** parcela real de un productor o productora, si se consigue su consentimiento en una de las conversaciones. Sin nombres, DNI ni datos personales.

## Consentimiento

- [ ] La persona entiende para qué se usará la ubicación de su parcela (un demo académico público).
- [ ] La persona aceptó de forma explícita (anote la fecha y el medio, sin nombre):
- [ ] Se acordó qué tan precisa puede ser la ubicación publicada (exacta o desplazada unos cientos de metros).

## Datos de la parcela (sin datos personales)

| Campo | Valor |
|---|---|
| Código ficticio | `REAL-01` |
| Cultivo | café / cacao |
| Región y provincia | |
| Área declarada (ha) | |
| Producción anual aproximada (kg) | |
| Geometría | punto o polígono (pegar abajo en GeoJSON) |
| Desde cuándo se cultiva | |
| ¿Tiene sombra? | |

```json
{"type": "Feature", "properties": {"codigo_productor": "REAL-01", "codigo_parcela": "REAL-01-A", "cultivo": "café", "area_ha": 0},
 "geometry": {"type": "Point", "coordinates": [0.000000, 0.000000]}}
```

## Cómo agregarla al demo

1. Guarde el GeoJSON de arriba como `datos/parcelas/real.geojson`.
2. Si la parcela cae dentro de una de las zonas precalculadas, la app la analiza al subir el archivo.
3. Si queda fuera, agregue su zona en `scripts/preparar_recortes.py`, vuelva a correrlo y suba los recortes nuevos.

## Lo que dijo el productor o la productora sobre su resultado

-
