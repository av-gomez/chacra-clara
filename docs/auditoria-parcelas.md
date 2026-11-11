# Auditoría de las parcelas de ejemplo

Generado por `scripts/auditar_parcelas.py`. Compara el método anterior (versión 1: JRC como verdad y fuentes contadas por nombre) con el nuevo (versión 2: bosque natural, altura del dosel, fuentes por tipo de sensor, periodos sin datos y renovación declarada). Ver «Método» en el README.

**1 de 18 parcelas cambiaron de estado.** Las 12 primeras (SAN y CAR) son la cooperativa de ejemplo de Puno; las 6 AMY, la de San Martín. Las ubicaciones son reales y fueron elegidas a propósito para cubrir todos los casos: es un escenario de prueba, no una cooperativa típica.

- **Bosque JRC 2020:** cobertura de bosque según el mapa de referencia de la UE (no vinculante).
- **Bosque natural 2020:** píxeles con probabilidad ≥ 50 % en Natural Forests of the World 2020 (WRI y Google DeepMind). Ojo: en Sandia y Carabaya marca el 83 % al 96 % de toda la zona como natural, cafetales incluidos; sus autores advierten que falla con agroforestería bajo sombra. Por eso se usa también la altura.
- **Prob. café o cacao:** los modelos del Forest Data Partnership están en un bucket de Google que exige una cuenta con facturación (*requester pays*); no hubo acceso anónimo.
- **Dosel 2020:** altura promedio del dosel en 2020 (ETH Global Canopy Height, 10 m) donde hubo pérdida (o en el bosque JRC de la parcela si no hubo). Menos de 20 m = probable sombra de cultivo.
- **Pérdida por fuente:** hectáreas de pérdida después de 2020 dentro del bosque JRC, por año.

| Parcela | Área (ha) | Bosque JRC 2020 | Bosque natural 2020 | Prob. café o cacao | Dosel 2020 | Pérdida por fuente (ha, año) | Estado anterior | Estado nuevo | Por qué |
|---|---:|---:|---:|---|---:|---|---|---|---|
| SAN-01 | 2,03 | 2,03 ha (100 %) | 2,03 ha | sin acceso | 32 m | Hansen: 1,10 (2024 0,32, 2025 0,79); Geobosques: 1,08 (2023 0,20, 2025 0,87); GLAD-S2: 0,84 (2024 0,09, 2025 0,70); IO: sin datos para el periodo | Posible deforestación | **Posible deforestación** | Sin cambio. Dos sensores ven pérdida en bosque natural. |
| SAN-02 | 1,45 | 1,45 ha (100 %) | 1,45 ha | sin acceso | 18 m | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| SAN-03 | 1,10 | 0,00 ha (0 %) | 0,00 ha | sin acceso | — | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| SAN-04 | 0,71 | 0,71 ha (100 %) | 0,71 ha | sin acceso | 19 m | Hansen: 0,41 (2021 0,17, 2024 0,11, 2025 0,13); IO: sin datos para el periodo | Revisar | **Revisar** | Sin cambio. Solo un tipo de sensor (Landsat) ve pérdida. |
| SAN-05 | 1,04 | 0,99 ha (95 %) | 1,04 ha | sin acceso | 16 m | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| SAN-06 | 1,65 | 1,65 ha (100 %) | 1,65 ha | sin acceso | 17 m | Hansen: 0,67 (2024 0,67); Geobosques: 0,26 (2023 0,18, 2024 0,07); GLAD-S2: 0,58 (2023 0,46, 2024 0,12); IO: sin datos para el periodo | Posible deforestación | **Revisar** | Renovación declarada en el año de la pérdida. |
| SAN-07 | 1,11 | 0,00 ha (0 %) | 0,01 ha | sin acceso | — | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| CAR-01 | 0,95 | 0,95 ha (100 %) | 0,95 ha | sin acceso | 21 m | Hansen: 0,56 (2023 0,23, 2024 0,29); Geobosques: 0,55 (2023 0,39, 2024 0,16); GLAD-S2: 0,33 (2023 0,17, 2024 0,11, 2025 0,05); IO: sin datos para el periodo | Posible deforestación | **Posible deforestación** | Sin cambio. Dos sensores ven pérdida en bosque natural. |
| CAR-02 | 0,22 | 0,22 ha (100 %) | 0,22 ha | sin acceso | 17 m | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| CAR-03 | 0,66 | 0,00 ha (0 %) | 0,40 ha | sin acceso | — | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| CAR-04 | 0,76 | 0,42 ha (55 %) | 0,74 ha | sin acceso | 18 m | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| CAR-05 | 1,53 | 1,53 ha (100 %) | 1,53 ha | sin acceso | 25 m | Hansen: 0,15 (2024 0,15); IO: sin datos para el periodo | Revisar | **Revisar** | Sin cambio. Solo un tipo de sensor (Landsat) ve pérdida. |
| AMY-01 | 1,36 | 1,36 ha (100 %) | 1,36 ha | sin acceso | 24 m | Hansen: 1,03 (2021 0,95, 2024 0,08); IO: 1,17 (2022 0,41, 2023 0,76) | Posible deforestación | **Posible deforestación** | Sin cambio. Dos sensores ven pérdida en bosque natural. |
| AMY-02 | 0,37 | 0,37 ha (100 %) | 0,37 ha | sin acceso | 27 m | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| AMY-03 | 1,02 | 0,00 ha (0 %) | 0,00 ha | sin acceso | — | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |
| AMY-04 | 2,05 | 0,00 ha (0 %) | 0,00 ha | sin acceso | — | ninguna | Revisar | **Revisar** | Sin cambio. Pérdida de árboles en chacra existente (posible renovación o poda). |
| AMY-05 | 1,84 | 1,84 ha (100 %) | 1,84 ha | sin acceso | 19 m | Hansen: 1,10 (2024 0,77, 2025 0,34); IO: sin datos para el periodo | Revisar | **Revisar** | Sin cambio. Solo un tipo de sensor (Landsat) ve pérdida. |
| AMY-06 | 1,50 | 0,00 ha (0 %) | 0,00 ha | sin acceso | — | ninguna | Sin deforestación detectada | **Sin deforestación detectada** | Sin cambio. Ninguna fuente ve pérdida de bosque después de 2020. |

## Revisión visual de las parcelas que quedan en «Posible deforestación»

- **SAN-01:** 2020: dosel continuo con textura de bosque, sin estructura de chacra; 2025: claros y una trocha nueva. Coincide con conversión de bosque. A 10 m no se descarta del todo un cafetal antiguo muy denso, pero el dosel medía 32 m en 2020.
- **CAR-01:** 2020: bosque junto al río; 2025: parche de suelo desnudo muy brillante. **Puede ser un deslizamiento junto al río** y no una conversión a cultivo: el técnico debe verificarlo.
- **AMY-01:** 2020: vegetación arbórea (en parte más clara); 2025: pasto o cultivo uniforme. Coincide con conversión.

Imágenes: Copernicus Sentinel-2 L2A, mediana de junio a octubre de 2020 y de 2025. A 10 m la revisión visual no reemplaza la visita de campo.
