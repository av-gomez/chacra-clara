# Fuentes verificadas: EUDR, cifras de Perú y mercado

Fecha de verificación: **2026-11-10** (todas las URL se consultaron en esa fecha).

Leyenda:
- **VERIFICADO**: la cifra o el dato aparece en la fuente indicada.
- **VERIFICADO CON MATIZ**: aparece, pero con otro alcance, periodo o fuente.
- **NO VERIFICADO**: no aparece en la fuente indicada. Se anota lo que la fuente sí dice.

Las citas textuales van entre comillas en el idioma original. Si no hay comillas, es paráfrasis.

---

## A. EUDR: Reglamento (UE) 2023/1115 y su modificación

Fuentes base:
- Texto original del Reglamento (UE) 2023/1115 (DO L 150, 9.6.2023): https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1115 (versión ES: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32023R1115)
- Reglamento (UE) 2025/2650, de 19 de diciembre de 2025, que modifica el 2023/1115 (DO L, 23.12.2025): https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32025R2650
- Comunicación de la Comisión C/2025/4524, *Guidance Document for Regulation (EU) 2023/1115* (DO C, 12.8.2025), no vinculante: https://eur-lex.europa.eu/eli/C/2025/4524
- Comisión Europea, *Frequently Asked Questions – Implementation of the EU Deforestation Regulation*, versión 5, abril de 2026 (documento de trabajo, no vinculante): https://transition-pathways.europa.eu/system/files/media/document/2026-08/FAQ-UPDATE-5th-Iteration-EN.pdf

### A1. Definición de bosque (art. 2.4), uso agrícola (art. 2.5) y agroforestería

- **Afirmación:** más de 0,5 ha, árboles de más de 5 m y cubierta de copa de más del 10 %, o árboles capaces de alcanzar esos umbrales in situ, excluyendo la tierra de uso predominantemente agrícola o urbano.
- **Estado:** VERIFICADO.
- **Art. 2(4):** "'forest' means land spanning more than 0,5 hectares with trees higher than 5 metres and a canopy cover of more than 10 %, or trees able to reach those thresholds in situ, excluding land that is predominantly under agricultural or urban land use;"
- **Art. 2(5):** "'agricultural use' means the use of land for the purpose of agriculture, including for agricultural plantations and set-aside agricultural areas, and for rearing livestock;"
- **Art. 2(6), clave para café y cacao:** "'agricultural plantation' means land with tree stands in agricultural production systems, such as fruit tree plantations, oil palm plantations, olive orchards and agroforestry systems where crops are grown under tree cover; it includes all plantations of relevant commodities other than wood; agricultural plantations are excluded from the definition of 'forest';"
- **Considerando 37:** "In line with FAO definitions, agroforestry systems, including where crops are grown under tree cover, as well as agrisilvicultural, silvopastoral and agrosilvopastoral systems, should not be considered forests, but as constituting agricultural use."
- **Guía C/2025/4524, sección 4.d:** "if a land is predominantly used under 'agroforestry systems' for the purposes spelled out by Recital (37), it cannot be considered as 'forest'. In this case and for the purpose of the Regulation, this land must be considered as being under 'agricultural use'."
- **Guía C/2025/4524, sección 4.b. Matiz importante para café bajo bosque:** "'agricultural use' should not be considered predominant for example in case of small-scale production of side products (e.g. coffee), and occasional extensive or occasionally small-scale grazing in forests as long as the production and related activities do not have detrimental effect on the habitat of the forest." Es decir, si se recolecta café de forma marginal dentro de un bosque natural, esa tierra sigue siendo bosque.
- **Guía C/2025/4524, sección 5, parcelas mixtas:** si una parcela tiene una parte de bosque y otra agrícola, las dos se evalúan por separado. El ejemplo de la guía: en una propiedad de 10 ha con 2 ha de bosque, esas 2 ha siguen siendo bosque aunque sean solo el 20 % del total. Además, "the actual forest properties should prevail over the designation in land registers and cadastral maps".
- **FAQ v5, 4.14 (caucho, aplicable por analogía a toda plantación de un producto básico distinto de la madera):** la sustitución de un bosque por una plantación agrícola "would be considered as deforestation under the Regulation".
- **Plantaciones establecidas antes de 2020:** ni la ley ni la guía tienen un artículo específico sobre esto. Se deduce de las definiciones de los arts. 2(3), 2(6) y 2(13): una tierra que al 31-12-2020 ya era plantación o sistema agroforestal de uso agrícola no era "bosque", así que mantener ese uso no constituye deforestación. Lo que descalifica es convertir bosque en uso agrícola después del 31-12-2020. Esta lectura es **inferencia propia a partir del texto legal**; no encontré una cita literal de la Comisión que lo diga con esas palabras.

### A2. Deforestación, degradación forestal y fecha de corte

- **Estado:** VERIFICADO.
- **Art. 2(3):** "'deforestation' means the conversion of forest to agricultural use, whether human-induced or not;"
- **Art. 2(7):** "'forest degradation' means structural changes to forest cover, taking the form of the conversion of: (a) primary forests or naturally regenerating forests into plantation forests or into other wooded land; or (b) primary forests into planted forests;"
- **Art. 2(13), libre de deforestación:** "(a) ... produced on land that has not been subject to deforestation after 31 December, 2020; and (b) in the case of relevant products that contain or have been made using wood, that the wood has been harvested from the forest without inducing forest degradation after 31 December, 2020;"
- **Nota:** para café y cacao el criterio relevante es la deforestación. La degradación aplica a los productos de madera (art. 2(13)(b)).

### A3. Geolocalización (art. 2(28))

- **Afirmación:** polígono obligatorio en parcelas de más de 4 ha (salvo ganado), un punto permitido en parcelas de hasta 4 ha, al menos 6 decimales y WGS84.
- **Estado:** VERIFICADO. WGS84 no figura en el reglamento; está en la FAQ y en la especificación del sistema de información.
- **Art. 2(28):** "'geolocation' means the geographical location of a plot of land described by means of latitude and longitude coordinates corresponding to at least one latitude and one longitude point and using at least six decimal digits; for plots of land of more than four hectares used for the production of the relevant commodities other than cattle, this shall be provided using polygons with sufficient latitude and longitude points to describe the perimeter of each plot of land;"
- **FAQ v5:** "For plots of land under 4 hectares, operators can use a polygon or a single point of latitude and longitude of six decimal digits". La FAQ también indica que las coordenadas pueden tomarse con teléfonos móviles o GNSS sin cobertura de red.
- **FAQ v5, 7.8:** "The format of the supported files in the Information System is GeoJson. The Information System supports currently WGS-84 coordinate format, with EPSG-4326 projection."
- **Art. 9(1)(d):** exige la geolocalización de todas las parcelas y la fecha o el rango de producción. Cualquier deforestación en una parcela "shall automatically disqualify all relevant commodities and relevant products from those plots".
- **Novedad del Reg. 2025/2650 (nuevo art. 9.5):** los "micro or small primary operators" pueden reemplazar la geolocalización por la dirección postal. Según el nuevo art. 2(15a), solo califican los operadores "established in a country classified as low risk". **Perú es riesgo estándar, así que esta exención no aplica a productores peruanos.**

### A4. Formato GeoJSON aceptado por el Sistema de Información EUDR (TRACES)

- **Fuente oficial:** *EUDR Information System – GeoJSON File Description*, página de la Comisión (indica "Updated 17 August 2026"): https://eudr.webcloud.ec.europa.eu/tracesnt/help/eudr-documentation/operator/geojson-description.html. Hay una versión PDF anterior, v1.5 del 5-5-2025, replicada en https://nli.gov.cz/wp-content/uploads/EUDR-EUDR-GEOJSON-FILE-DESCRIPTION-1.5_.pdf (no la abrí; solo la vi en los resultados de búsqueda).
- **Estado:** VERIFICADO en la página oficial. Resumen:
  - **Estándar:** GeoJSON según RFC 7946. Los nombres de tipo y de propiedad distinguen mayúsculas de minúsculas.
  - **Estructura:** `FeatureCollection` de `Feature`, cada una con su geometría y `properties`.
  - **Geometrías aceptadas:** Point, MultiPoint, Polygon y MultiPolygon. LineString y MultiLineString "will not be accepted/processed". La página no dice expresamente si acepta GeometryCollection.
  - **Sistema de referencia:** WGS 84 (EPSG:4326), grados decimales, en orden [longitud, latitud]. Otros CRS se deben convertir antes de subir.
  - **Precisión:** "The information system will truncate coordinate points to 6 decimal places before storing". Si dos vértices solo difieren a partir del sexto decimal, quedan duplicados y la geometría resulta inválida.
  - **Propiedades:**
    - `ProductionPlace` (texto, opcional pero recomendada).
    - `Area` (número en hectáreas, aplica a Point; si falta se asume 4; si va entre comillas, como `"3"`, se interpreta como área 0).
    - `ProducerName` (texto).
    - `ProducerCountry` (código ISO2; un código inválido provoca el rechazo).
    - Las propiedades no listadas se ignoran.
  - **Tipos de archivo:**
    - Tipo I: un solo productor.
    - Tipo II: varios productores, agrupados por `ProducerName` y `ProducerCountry`; cada Feature debe llevar `ProducerCountry`.
  - **Reglas de polígono:** al menos 4 posiciones, con la primera igual a la última (anillo cerrado). No se aceptan agujeros, autointersecciones, lados superpuestos ni formas degeneradas en línea. La página no especifica el orden de giro.
  - **Límite de tamaño:** 25 MB por declaración de diligencia debida, sumando todos los GeoJSON. No se indica un límite de vértices ni de features.
  - **Errores comunes listados:** propiedad mal escrita (por ejemplo, "productionplace"), coordenadas fuera de rango, archivo protegido con contraseña y formatos PDF o TXT, entre otros.
- **Discrepancia interna de la página:** el ejemplo de Point aparece anidado (`[[-105.029865, 40.622831]]`), lo que contradice el texto que describe una sola posición. Conviene probar contra el sistema real o el entorno de aceptación: https://acceptance.eudr.webcloud.ec.europa.eu/tracesnt/help/eudr-documentation/operator/geojson-description.html

### A5. Fechas de aplicación tras la modificación

- **Afirmación:** 30-12-2026 para operadores grandes y medianos, y 30-06-2027 para micro y pequeños.
- **Estado:** VERIFICADO.
- **Reg. 2025/2650, nuevo art. 38.2:** "Articles 3 to 13, Articles 16 to 24 and Articles 26, 31 and 32 shall apply from 30 December 2026."
- **Nuevo art. 38.3:** para operadores que sean personas físicas o micro o pequeñas empresas (Directiva 2013/34/UE) "who were established as such by 31 December 2024", los mismos artículos "shall apply from 30 June 2027". Ojo: la fecha de 2027 depende de que la empresa estuviera constituida a esa fecha.
- **AGRINFO (ES)**, https://agrinfo.eu/book-of-reports/review-of-eu-deforestation-regulation-simplification/translate/es: "la aplicación de los requisitos EUDR se pospone hasta el 30 de diciembre de 2026" y "Para los micro y pequeños operadores, la fecha de aplicación es el 30 de junio de 2027". También recoge otras simplificaciones:
  - solo presenta la declaración de diligencia debida quien comercializa el producto por primera vez;
  - los operadores aguas abajo ya no presentan declaración propia;
  - hay una declaración simplificada única para micro y pequeños productores primarios;
  - la Comisión debía informar antes del 30-4-2026.
- **Actualización 2026:** la Comisión publicó la revisión de simplificación COM(2026) 191 el 4-5-2026 y, según las fuentes secundarias, concluyó que no hacía falta modificar el texto base. Solo actualizó la guía y la FAQ y aprobó el Reglamento Delegado (UE) 2026/2102 sobre el ámbito de productos, que añade por ejemplo el café soluble. Para esos productos añadidos la obligación aplica desde el 30-12-2027. Fuentes: AGRINFO (13-5-2026, revisado 21-9-2026), https://agrinfo.eu/book-of-reports/eu-deforestation-regulation-eudr-clarifications-may-2026/ , y el resumen de Baker McKenzie, https://www.bakermckenzie.com/en/insight/publications/2026/05/eu-commission-publishes-simplification-review-of-eudr . No leí el texto completo de COM(2026) 191.

### A6. Perú como país de riesgo estándar (Reglamento de Ejecución 2025/1093) e implicancias

- **Estado:** VERIFICADO.
- **Reglamento de Ejecución (UE) 2025/1093, de 22-5-2025 (DO L 23.5.2025):** https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32025R1093
  - Art. 1.2: "A standard level shall be maintained for all countries not listed in the Annex."
  - Perú no figura entre los países de riesgo bajo ni entre los de riesgo alto (los de riesgo alto son Belarús, Corea del Norte, Myanmar y Rusia). Por tanto, Perú queda en riesgo estándar.
- **Art. 16.8 (en la redacción del Reg. 2025/2650):** los controles anuales deben cubrir "at least 3 % of the operators, non-SME downstream operators and non-SME traders" que comercialicen productos de países de riesgo estándar. Para riesgo alto es 9 % de operadores y 9 % de la cantidad; para riesgo bajo, 1 %.
- **MIDAGRI, nota de prensa del 22-5-2025**, https://www.gob.pe/institucion/midagri/noticias/1173367-midagri-the-european-commission-has-classified-peru-as-a-standard-risk-country-under-the-eudr : "Peru was classified as a 'standard risk' country, along with other countries in the region such as Brazil, Argentina, Colombia, Ecuador, El Salvador, and Guatemala." Y también: "inspection, i.e., verification of due diligence records, will be carried out on 3% of importers, a significantly lower percentage if Peru had been classified as a 'high-risk' country (9%)."
- **Matiz:** MIDAGRI dice "importers". La norma dice "operators" (y, tras la modificación, también operadores aguas abajo y comerciantes que no sean PYME). Riesgo estándar significa además que no aplica la diligencia simplificada del art. 13 ni la declaración simplificada para micro y pequeños productores primarios, que está reservada a países de riesgo bajo.

### A7. Requisito de legalidad (art. 2(40))

- **Estado:** VERIFICADO.
- **Art. 2(40):** "'relevant legislation of the country of production' means the laws applicable in the country of production concerning the legal status of the area of production in terms of:"
  - (a) land use rights;
  - (b) environmental protection;
  - (c) forest-related rules, including forest management and biodiversity conservation, where directly related to wood harvesting;
  - (d) third parties' rights;
  - (e) labour rights;
  - (f) human rights protected under international law;
  - (g) the principle of free, prior and informed consent (FPIC), including as set out in the UN Declaration on the Rights of Indigenous Peoples;
  - (h) tax, anti-corruption, trade and customs regulations.
- **Art. 3(b):** exige que los productos se hayan producido conforme a esa legislación.

### A8. ¿El mapa JRC GFC2020 es no vinculante?

- **Estado:** VERIFICADO.
- **JRC, publicación "GFC2020: a global map of forest land use for year 2020 to support the EU Deforestation Regulation"** (metadato 2026-02-25), https://publications.jrc.ec.europa.eu/repository/handle/JRC142855 : "it is a non-exclusive, non-mandatory, and not legally binding source."
- **Guía C/2025/4524, sección 5:** "The EU Observatory provided by the Commission is a free to use tool for all stakeholders to determine the global forest cover of 2020. However, the Observatory is non-exclusive, non-mandatory and carries no legal value. Public and private stakeholders can use any maps that they see fit for the purpose of their due diligence exercise or checks."
- **Nota:** la versión vigente es la V4 (catálogo de Google Earth Engine: https://developers.google.com/earth-engine/datasets/catalog/JRC_GFC2020_V4 ). Según ese catálogo, el mapa puede revisarse.

---

## B. Cifras de Perú

### B1. Café: familias, hectáreas, tamaño de finca, asociatividad y exportaciones 2025

- **URL:** https://agraria.pe/noticias/exportaciones-peruanas-de-cafe-sumaron-us-131-3-millones-ent-42180 (Agraria.pe, 05-05-2026).
- **Estado:** VERIFICADO (las seis cifras).
- **Citas:**
  - "producido por 223 mil familias de pequeños productores"
  - "en 427.000 hectáreas (2023)". Ojo: el dato es de 2023.
  - "16 regiones a nivel nacional que producen café"
  - "El 85% del total de caficultores son pequeños productores que manejan entre 1 y 5 hectáreas"
  - "solo un 30%, están asociados -principalmente- en cooperativas"
  - exportaciones 2025: "alcanzó los US$ 1.796 millones". La frase está mal redactada en la fuente, pero la cifra es clara.

### B2. La UE como destino del café: ~40 % y ~US$ 726 millones en 2025

- **URL:** https://www.expreso.com.pe/opinion/cafe-y-cacao-el-reto-europa/ (columna de opinión).
- **Estado:** VERIFICADO CON MATIZ. La página devolvió HTTP 403 al acceso directo, así que el texto se verificó solo a través del extracto del buscador.
- **Extracto:** "En 2025, nuestras exportaciones de café a la Unión Europea alcanzaron US$ 726,1 millones, el 40,3 % de las ventas mundiales. En cacao y derivados, aproximadamente US$ 618,8 millones se dirigieron a ese mercado entre enero y noviembre de 2025."
- **Contraste:** el informe CIEN-ADEX de marzo de 2026 (https://cien.adexperu.org.pe/wp-content/uploads/2026/04/CIEN_RT_Mar2026_vf.pdf ) asocia US$ 726,0 millones al **café verde** (partida 0901119000) en un contexto de exportaciones a la UE. Solo lo vi como extracto del buscador; no abrí el PDF.

### B3. Pobreza, ingreso digno y tamaño medio de parcela

- **URL:** https://agraria.pe/noticias/cafe-crece-por-expansion-del-area-sembrada-y-no-por-aumento--41533 (Agraria.pe, 23-01-2026).
- **Estado:** VERIFICADO.
- **Origen de los datos:** José Yturrios Padilla, director de la División de Agricultura y Cambio Climático de la consultora Recursos, citado en el artículo.
- **Citas:**
  - "el 35% de las familias cafeteras seguían en situación de pobreza en 2024"
  - "75.3% no alcanzaba el ingreso digno, medido según la metodología del Instituto Anker"
  - "un tamaño medio de parcela de 1.9 hectáreas por familia."

### B4. Cacao: exportaciones 2025, la UE como destino, familias y asociatividad

- **URL indicada:** https://agraria.pe/noticias/a-noviembre-de-2025-se-registraron-323-exportadores-de-cacao-41577 (Agraria.pe, 30-01-2026).
- **US$ 1.619 millones: NO VERIFICADO en esa URL.** La fuente dice, para enero a noviembre de 2025: "las exportaciones peruanas de cacao y derivados registraron un nuevo máximo histórico alcanzando los US$ 1.547 millones". También indica "la Unión Europea (40% del total exportado)" y "se registraron 323 exportadores".
- **La cifra de US$ 1.619 millones sí aparece en otra fuente.** El Peruano (16-07-2026), citando al titular de MINCETUR: "sumaron US$ 1 619 millones", con un crecimiento del 26 %. https://elperuano.pe/noticia/300463-peru-es-el-segundo-mayor-exportador-de-cacao-en-grano-de-latinoamerica-y-el-sexto-del-mundo
- **Otras fuentes dan cifras distintas para 2025:** Promperú, US$ 1.565 millones; ADEX, US$ 1.567,8 millones (según resultados de búsqueda que no abrí). **Recomendación:** citar "US$ 1.547 millones (enero a noviembre de 2025, Agraria.pe)" o "US$ 1.619 millones (año 2025, MINCETUR vía El Peruano)", pero no atribuir los US$ 1.619 millones a la URL de Agraria.
- **Familias de cacao:** AVSF y ETHIQUABLE, *Nota de posición "Para un EUDR operativo, eficiente e inclusivo"* (PDF de octubre de 2025), https://www.avsf.org/app/uploads/2025/10/Posicion-AVSF-Ethiquable-EUDR.pdf
  - **Estado:** VERIFICADO.
  - **Cita:** "En Perú, con una estimación de 100 000 familias productoras de cacao, de las cuales el 30% son socios de asociaciones o cooperativas, unas 70 000 familias comercializan de forma individual su cacao a compradores locales, sin ninguna garantía de trazabilidad."
  - **Dato adicional del mismo PDF:** "solo unos 100 000 productores, de un total de 2 millones, disponen hasta la fecha de parcelas geolocalizadas". El documento también menciona una propuesta del Estado de fines de 2024 de exigir "más de 40 criterios" de legalidad por lote.

### B5. AgroDigital: 184.281 parcelas en 13 regiones (diciembre de 2025)

- **URL:** https://agraria.pe/noticias/peru-supera-metas-de-geolocalizacion-y-refuerza-el-cumplimie-41356 (Agraria.pe, 22-12-2025).
- **Estado:** VERIFICADO CON MATIZ. La cifra es correcta, pero **el artículo no menciona "AgroDigital"**. La atribuye a MIDAGRI (DGESEP/DEIA).
- **Citas:**
  - "184,281 parcelas geolocalizadas en 13 regiones del país"
  - de ellas, 150.163 polígonos son del sector, que equivalen a "un 132.30 % de la meta anual establecida", y más de 34.000 provienen de entidades cooperantes y organizaciones.
  - cultivos: café, cacao y palma aceitera.
- **Cifras distintas en otras fuentes:**
  - El documento de MIDAGRI "Perú: Hacia el cumplimiento del EUDR" (https://cdn.www.gob.pe/uploads/document/file/9425111/6513789-peru-hacia-el-cumplimiento-del-reglamento-de-la-union-europea-para-productos-libres-de-deforestacion-eudr.pdf ) dice "se han geolocalizado 181 731 polígonos", con nota "A diciembre de 2025", frente a una meta de 113.500. Ese mismo documento sí vincula la cifra al aplicativo AgroDigital.
  - Agraria.pe (14-10-2026) habla de "más de 181 mil parcelas geolocalizadas" a marzo de 2026.

### B6. 160 mil predios de café sin geolocalizar, meta de 400 mil y 240 mil reportados

- **URL:** https://agraria.pe/noticias/contrarreloj-160-mil-predios-de-cafe-aun-no-son-geolocalizad-43334 (Agraria.pe, 23-10-2026).
- **Estado:** VERIFICADO CON MATIZ.
- **Citas:**
  - Meta, según Delky Gutiérrez (presidente de la Junta Nacional del Café): "una meta estimada de 400 mil polígonos en cultivos de café, cacao y palma aceitera a ser geolocalizados". **La meta incluye café, cacao y palma; no es solo café.**
  - "MIDAGRI reporta un avance de 240 mil polígonos, equivalente al 60%"
  - "quedando pendientes 160 mil predios (40%) a ser geolocalizados en los próximos meses". El titular habla de "predios de café", pero la resta 400 − 240 corresponde a la meta total de los tres cultivos.
  - "desde hace varios meses se vienen condicionando embarques de café a Europa bajo tal normativa"
  - Queja de las organizaciones (en la bajada del artículo; el cuerpo no lo desarrolla): "falta de plataforma adecuada y confiable para subir información para la EUDR"

### B7. Riesgos sociales (nota AVSF y ETHIQUABLE de diciembre de 2025)

- **URL:** https://www.avsf.org/app/uploads/2025/12/note-avsf-ethiquable-RDUE_ES.pdf
- **Estado:** VERIFICADO.
- **Riesgos que identifica el documento (citas):**
  - "La exclusión del mercado europeo de los productores no organizados (no socios de cooperativas), así como de las organizaciones de productores, que no dispongan de elementos de trazabilidad ni de legalidad de sus producciones en el momento de la entrada en vigor del reglamento."
  - "El acaparamiento de los datos de los productores por parte de las grandes empresas exportadoras, acentuando así mismo su dependencia de estas últimas."
  - "Sistemas estatales de trazabilidad y/o legalidad demasiado complejos (por ejemplo, Perú, Ecuador, Costa de Marfil), a menudo inadaptados a la realidad de los productores y aún no operativos."
  - Sobre la propiedad de los datos: "no está sistemáticamente garantizada a los productores".
  - Costos: "hasta 107 €/tonelada de cacao en Costa de Marfil".
- **Sobre Perú:** el registro agrario nacional "incluye información sobre 38 variables y datos de geolocalización", y los sistemas estatales "carecen de garantías de interoperabilidad con los desplegados por las empresas importadoras y la UE".

### B8. Geobosques: ~3,2 millones de ha perdidas (2001–2024) y 78 % en parches de 5 ha o menos

- **Fuente primaria:** plataforma Geobosques del MINAM, módulo "Bosque y pérdida de bosque", https://geobosques.minam.gob.pe/geobosque/view/perdida.php . Los datos nacionales se obtuvieron del servicio que alimenta esa página (`https://geobosques.minam.gob.pe/geobosque/controller/consulta.php`, nivel nacional), tipo de bosque 1 (bosque húmedo amazónico).
- **3,2 millones de ha (2001–2024): VERIFICADO.** La suma anual 2001–2024 da **3.203.884 ha**. Coincide con Canal N citando a Geobosques: "el Perú ha perdido 3,2 millones de hectáreas de bosques amazónicos" ( https://canaln.pe/actualidad/peru-perdio-32-millones-hectareas-bosques-23-anos-n488132 ).
- **Ya hay dato de 2025:** pérdida 2025 = 114.231 ha; acumulado 2001–2025 = **3.318.114 ha** (≈3,3 millones de ha).
- **Pérdida 2024:** 150.601 ha.
- **78 % en parches de 5 ha o menos: NO VERIFICADO.** Con los rangos de tamaño de Geobosques (<1 ha, 1–5 ha, 5–50 ha, 50–500 ha y >500 ha), para 2001–2024 resulta:
  - <1 ha: 1.282.125 ha (40,0 %);
  - 1–5 ha: 1.145.236 ha (35,7 %);
  - **5 ha o menos: 75,8 %**;
  - para 2001–2025: 75,4 %;
  - solo el año 2024: 67,1 %.
- **El 75,8 % es cálculo propio** sobre los datos de Geobosques. Otras cifras publicadas: Agraria.pe da "un 80%" para 2001–2021, y una nota de prensa da 66 % para 2022. **Recomendación:** usar "~76 % (2001–2024, Geobosques)" y citar el cálculo.

### B9. Puno: más de 8.800 productores de café y cacao

- **URL:** https://andina.pe/ingles/noticia-peru-midagri-fosters-implementation-of-eudr-at-puno-regional-workshop-1051927.aspx (Andina, 14-11-2025).
- **Estado:** VERIFICADO.
- **Cita:** "Puno is home to more than 8,800 coffee and cacao producers, mainly in Sandia and Carabaya provinces." El taller se realizó en el distrito de San Juan del Oro.

### B10. INEI: acceso a TIC en el segundo trimestre de 2026

- **URL:** https://www.inei.gob.pe/media/MenuRecursivo/boletines/boletin-tic-iit2026.pdf (Encuesta Nacional de Hogares, cifras preliminares).
- **Estado:** VERIFICADO.
- **Internet en el hogar:** "Durante el segundo trimestre de 2026, el 64,5% de los hogares del país contaba con servicio de Internet. Por área de residencia, en Lima Metropolitana, el 84,7% de los hogares disponía del servicio; en el resto urbano, el 66,2%; mientras que, en el área rural solo el 27,1% tenía acceso."
- **Telefonía móvil en el hogar:** "cobertura del 95,9%. Por área de residencia, la mayor incidencia se observó en Lima Metropolitana con 98,1%, seguido de resto urbano con 97,1% y del área rural con 89,2%."
- **Uso de internet (población de 6 años o más):** 84,2 % a nivel nacional y 63,7 % en el área rural.
- **Implicancia de diseño:** en zonas rurales, menos de 3 de cada 10 hogares tienen internet fijo, pero alrededor de 9 de cada 10 tienen celular. Conviene diseñar para móvil y con capacidad offline.

---

## C. Mercado y competencia (herramientas de cribado satelital de parcelas)

| Herramienta | Qué hace (según la fuente) | Precio público | Fuente |
|---|---|---|---|
| **Whisp** (FAO, Forest Data Partnership, AIM4Forests) | "What is in that plot?". Herramienta **de código abierto** que combina varios mapas satelitales ("convergencia de evidencias") para estimar el riesgo de deforestación respecto al 31-12-2020. Se accede por API; hay paquete Python `openforis-whisp`. | No se indica precio. Es código abierto, y MIDAGRI la ofrece a los productores "de forma gratuita". | https://www.fao.org/transparent-supply-chains/news---events/news/detail/supporting-eudr-compliance-with-whisp/en (13-05-2024); https://pypi.org/project/openforis-whisp/ ; https://www.fao.org/fileadmin/user_upload/faoweb/NFM/WhispOverview.pdf (no lo abrí) |
| **Global Forest Watch Pro** (WRI) | Análisis y monitoreo de áreas de abastecimiento. Su propia web dice que "no es una plataforma de trazabilidad". | Gratis para productores y cooperativas en Perú: WRI provee "free access to its Global Forest Watch (GFW) Pro platform" en una alianza con el Ministerio de Agricultura. No encontré tarifas para empresas. | https://pro-news.globalforestwatch.org/news-events/collaborating-deforestation-free-agricultural-exports (fechado "Jun 25", sin año) |
| **Satelligence** | Monitoreo satelital de parcelas; alianza con Fairtrade para organizaciones de productores. | No publica precios. Según una reseña de terceros, el precio depende de la superficie, el número de proveedores y los productos. | https://www.fairtrade.net/en/get-involved/news/fairtrade-and-satelligence-join-forces-for-farmers-to-meet-eu-deforestation-rules.html |
| **osapiens** | Cribado satelital automatizado (radar y óptico) integrado con gestión de casos y ERP. | No encontré precio público. | https://osapiens.com/en/solutions/supplier-intelligence/eudr/eudr-satellite-risk-management |
| **Koltiva** | Mapeo de polígonos con agentes de campo, cribado de riesgo y envío de la declaración de diligencia debida. | No encontré precio público. | https://www.koltiva.com/latin-america |
| **TraceX** | Plataforma EUDR (trazabilidad y riesgo). | No lo verifiqué en la fuente. La página para empresas de alimentos dice que el precio es a medida ("tailored quote") y ofrece una prueba gratuita de 15 días. Un buscador mostró tarifas de €40 a €50 por proveedor y mes más un costo de alta, pero la URL devolvió 404. | https://tracextech.com/eudr-for-food-companies/ |
| **Meridia** | No pude verificarlo. | No pude verificarlo. | — |
| **Preferred by Nature** | No pude verificarlo. | No pude verificarlo. | — |
| **LiveEO TradeAware** (referencia) | Plataforma EUDR. | Tiene una página de precios (https://www.live-eo.com/tradeaware-pricing ). No verifiqué las cifras. | — |

**AgroDigital (MIDAGRI):**
- **Qué es.** Agraria.pe (01-10-2025, https://agraria.pe/noticias/benefician-a-400-mil-productores-de-cafe-y-cacao-con-nueva-a-40880 ) la describe como "una aplicación móvil que permite a los agricultores acceder a servicios agrarios, asistencia técnica y soluciones digitales". Sus funciones incluyen "geolocalización de parcelas, monitoreo satelital, consulta de precios, alertas técnicas".
- **Flujo según MIDAGRI.** El documento de MIDAGRI sobre el EUDR describe cuatro pasos: Inscripción, Acceso, Geolocalización con AgroDigital y Reporte de cumplimiento. También describe alianzas con WRI (GFW) y con la FAO (Whisp) para que los productores accedan "a un reporte de evaluación de libre de deforestación de forma gratuita".
- **Relación con el PPA.** Agraria.pe (14-10-2026, https://agraria.pe/noticias/peru-avanza-en-trazabilidad-de-cacao-y-cafe-pero-aun-no-cier-43277 ) la llama "la plataforma usada para geolocalizar parcelas de cacao, café y palma". Según esa nota, el Padrón de Productores Agrarios (PPA) "ya supera los 2,1 millones de productores registrados". Un experto citado propone integrar PPA, AgroDigital, la evaluación de deforestación, la transacción comercial y el lote de exportación.
- **Exportación GeoJSON o shapefile: NO VERIFICADO.** Ninguna de las fuentes revisadas (Agraria.pe, Andina y el documento de MIDAGRI) dice que AgroDigital exporte GeoJSON, shapefile o KML, ni qué campos exportaría. MIDAGRI menciona un tablero de avance de polígonos (portal PPA, sección EUDR) que no revisé. Hay que confirmarlo directamente con MIDAGRI (DEIA).
