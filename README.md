# Crossmatch entre Córdoba-Durchmusterung y Gaia DR3

## Descripción

Este proyecto tiene como objetivo identificar las estrellas del catálogo Córdoba-Durchmusterung (CD) en Gaia DR3 y evaluar en qué medida los movimientos propios medidos por Gaia reproducen la cinemática estelar a lo largo de aproximadamente 150 años.

El enfoque consiste en construir un pipeline reproducible que permita:

- preparar y transformar los datos del catálogo histórico  
- realizar un crossmatch amplio con Gaia  
- refinar criterios de identificación y analizar resultados

---

## Estructura del repositorio

    data/
        raw/        # datos originales descargados
        processed/  # datos transformados (ICRS, subconjuntos)
        gaia_bins/  # resultados intermedios del crossmatch
        matches/    # resultados de los matches

    notebooks/
        exploracion_inicial.ipynb      # notebook con exploración inicial de CD
        exploracion_tolerancia.ipynb   # notebook con exploración para estimar radio de búsqueda

    src/

        obtain_data/
            cd_catalog.py           # descargar catálogo CD
            process_cd_catalog.py   # procesamiento inicial del catálogo CD
            gaia_crossmatch.py      # crossmatch amplio para obtener datos de Gaia
            merge_gaia_bins.py      # merge de bins de Gaia

        utils/
            logger.py   # logger de mensajes en consola

        process_data/
            magnitudes.py    # estimar magnitud CD a partir de magnitudes de Gaia
            propagation.py   # propagar coordenadas por movimiento propio

        matching/
            match.py    # match posicional
            filter.py   # filtro por magnitud

        analysis/
            metrics.py  # métricas de los resultados
            plots.py    # plots de los resultados

        run_matches.py  # script principal
         
    results/    # csv de métricas y plots de los resultados

---

## Exploración inicial del catálogo CD

La exploración se realiza en:

    notebooks/exploracion_inicial.ipynb

Incluye:

#### Descarga del catálogo CD desde VizieR

A partir del ID del catálogo de Córdoba-Durchmusterung.


#### Transformación de coordenadas

Aunque el catálogo descargado desde VizieR incluye coordenadas en ICRS, se decidió recalcularlas a partir de las coordenadas originales del catálogo CD.
Esto permite validar el proceso de transformación, mantener control sobre el preprocesamiento y evitar depender de productos derivados externos.

#### Generación de subconjuntos

Se generan dos versiones del catálogo:

- una versión completa con todas las columnas originales y las coordenadas transformadas  
- una versión reducida que contiene únicamente `ra` y `dec` en grados (ICRS)  

La versión reducida es la utilizada para realizar las queries en Gaia.

#### Análisis de rangos

Se analiza la distribución de declinación y magnitudes. 

En las magnitudes se detectaron valores extremos (hasta magnitud 50), que corresponden a valores faltantes o flags del catálogo. El análisis mediante histogramas mostró que el límite físico efectivo del catálogo es aproximadamente:

    mag ≈ 12

---

## Pipeline de obtención de datos

Los catálogos pueden obtenerse a través de distintos servicios, por lo cual la obtención de datos no se incluye como parte del pipeline principal.
Para realizar la obtención de los catálogos por este medio, el orden de ejecución es:
1. src/obtain_data/cd_catalog.py
2. src/obtain_data/process_cd_catalog.py
3. src/obtain_data/gaia_crossmatch.py
4. src/obtain_data/merge_gaia_bins.py

### 1. Descarga del catálogo CD

Script:

    src/obtain_data/cd_catalog.py

- descarga el catálogo original  
- lo guarda en `data/raw/`  

---

### 2. Procesamiento del catálogo CD

Script:

    src/obtain_data/process_cd_catalog.py

Realiza:

- conversión de coordenadas a ICRS  
- transformación de las coordenadas a float64  
- generación de catálogo completo con nuevas columnas y catálogo reducido (`ra`, `dec`)  

Salida:

    data/processed/

---

### 3. Crossmatch amplio inicial con Gaia

Script:

    src/obtain_data/gaia_crossmatch.py

Requiere un archivo `.env` con usuario y password del archivo de Gaia.

Ejemplo de contenido del archivo `.env`:

    GAIA_USER=...
    GAIA_PASSWORD=...

Procedimiento:

- login en el archivo Gaia
- subida del catálogo CD (`ra`, `dec`) como tabla
- ejecución de queries en bins de declinación  


Parámetros utilizados:

- número de bins en declinación: 40  
- radio de búsqueda: 90 arcsec  
- límite de magnitud: G < 15  

El rango de declinación se divide en 40 intervalos para evitar queries excesivamente pesadas, mejorar la estabilidad del servidor y facilitar la ejecución secuencial. 

El catálogo CD presenta errores posicionales del orden de 10–20 arcsec en algunas zonas del cielo, por lo que se adopta un radio de 90 arcsec
con el objetivo de construir un crossmatch amplio, que evite perder candidatos verdaderos.


Teniendo en cuenta el límite en magnitud (12) de CD, y dado que utiliza magnitudes visuales mientras Gaia utiliza el sistema fotométrico G, BP, RP, se adopta un criterio conservador de phot_g_mean_mag < 15.
Considerando que Gaia DR3 alcanza aproximadamente G ≈ 20–21, este filtro reduce de forma sustancial el volumen de datos, mientras que evita descartar posibles matches reales.

En esta etapa no se busca una identificación definitiva, sino generar un conjunto de candidatos para análisis posterior.

Output:

Cada bin genera un archivo:

    data/gaia_bins/bin_i.fits

que contiene fuentes de Gaia dentro del radio de búsqueda con parámetros astrométricos y fotométricos y separación angular respecto a la posición del catálogo CD.

### 3. Merge de los bins de Gaia

Script:

    src/obtain_data/merge_gaia_bins.py

Realiza un merge de los bins de Gaia para obtener el crossmatch amplio inicial completo.

---

## Exploración del match amplio para la estimación de la tolerancia

La exploración se realiza en:

    notebooks/exploracion_tolerancia.ipynb

El crossmatch amplio inicial se realizó con un radio de 90 arcsec para no perder candidatos verdaderos. El objetivo de esta exploración es analizar la distribución de separaciones angulares y la curva de matches vs. tolerancia para determinar un radio operativo razonable antes de pasar al matching definitivo.

#### Distribución de separaciones angulares

Se grafica la distribución de separaciones entre todos los pares CD-Gaia dentro del radio de búsqueda, tanto con coordenadas Gaia en época J2016 como propagadas a la época del CD (~1875). En un matching limpio se esperaría un pico pronunciado cerca de 0" (contrapartes reales) seguido de una cola plana (pares aleatorios). 

La ausencia de ese pico observada en el resultado indica que los errores posicionales del CD distribuyen las contrapartes reales a lo largo de un rango amplio de separaciones, mezclándolas con el fondo aleatorio. El quiebre visible alrededor de 80–90" en escala logarítmica sugiere que más allá de ese radio el fondo domina completamente.

#### Curva de matches vs. tolerancia

Se grafica el número de estrellas CD con al menos un candidato Gaia, con candidato único y con múltiples candidatos en función del radio de búsqueda. 

Se observa que la curva de ambiguos crece sostenidamente con el radio, mientras que la de únicos se aplana, lo que permite estimar el rango donde el trade-off entre completitud y ambigüedad es razonable. 

Las líneas verticales en 1σ ≈ 23", 2σ ≈ 46" y 3σ ≈ 69" marcan valores de referencia basados en el error posicional estimado del CD. 

Para el siguiente paso, se toman como candidatos los siguientes radios: 23", 30" y 46".

---

## Pipeline principal y funciones auxiliares

El pipeline principal se implementa en `src/run_matches.py` y orquesta el flujo completo desde la carga de datos hasta la generación de resultados. Está organizado en etapas implementadas en módulos independientes bajo `src/`.


### Preprocesamiento de Gaia (`src/process_data/`)

Antes de realizar cualquier match, la tabla de Gaia se enriquece con dos columnas calculadas.

#### `magnitudes.py` — `add_estimated_cd_magnitude`

Estima la magnitud en escala CD para cada fuente de Gaia mediante una cadena de conversión en dos pasos. Primero convierte las magnitudes G, BP y RP de Gaia a magnitud Johnson V usando la transformación estándar para Gaia DR3:

```text
V ≈ G − 0.0257 − 0.0924·(BP−RP) − 0.1623·(BP−RP)²
```
Luego convierte Johnson V a escala CD usando el polinomio cuadrático de Severin & Sevilla (2015), ajustado a partir del catálogo PPM sobre estrellas con identificación conocida en declinación −23°:

```text
mag_CD ≈ −0.01335368·V² + 1.076636·V + 0.2249828
```
La incerteza total de esta conversión es del orden de 0.3 mag, dominada por el ajuste polinomial (σ = 0.28 mag). Las fuentes sin medición de BP o RP quedan marcadas con `has_color = False` y son excluidas automáticamente cuando se aplica el filtro de magnitud.

#### `propagation.py` — `propagate_gaia_coords`

Propaga las coordenadas de cada fuente de Gaia desde la época de referencia J2016 a la época del CD (B1875) usando los movimientos propios reportados por Gaia DR3:

```text
ra_prop  = ra  + pmra  × (1875 − 2016) / 3.6×10⁶
dec_prop = dec + pmdec × (1875 − 2016) / 3.6×10⁶
```

donde pmra y pmdec están en mas/año y el factor 3.6×10⁶ convierte a grados. En Gaia DR3, `pmra` ya incluye el factor cos(δ). Se agregan como columnas nuevas `ra_prop` y `dec_prop`. Las fuentes sin movimiento propio reportado quedan marcadas con `has_pm = False` y son excluidas automáticamente en los matches que usan coordenadas propagadas.


### Matching (`src/matching/`)

#### `match.py` — `positional_match`

Realiza el match posicional entre el CD y Gaia. Recibe los nombres de las columnas de coordenadas a usar, lo que permite ejecutar el mismo match con coordenadas originales o propagadas sin duplicar la tabla ni cambiar la lógica.

Para cada par CD-Gaia ya formado en la tabla (producto del crossmatch amplio inicial), calcula la separación angular y retiene todos los pares dentro de la tolerancia especificada. El resultado es una tabla de pares donde una misma estrella del CD puede aparecer múltiples veces. La decisión de quedarse con un único candidato por estrella del CD se delega a etapas posteriores, para poder evaluar la ambigüedad antes y después de aplicar criterios adicionales.

#### `filter.py` — `apply_magnitude_filter`

Aplica un filtro de magnitud sobre una tabla de pares ya obtenida. Calcula la diferencia entre la magnitud reportada en el CD y la magnitud estimada en escala CD desde Gaia, y retiene solo los pares donde esa diferencia es menor que un umbral `delta_mag`. Los pares sin conversión de magnitud disponible (fuentes sin BP o RP en Gaia) son excluidos. La función opera sobre el resultado de `positional_match` sin necesidad de repetir la búsqueda espacial.


### Los cuatro matches

La combinación de estos dos pasos genera cuatro variantes de match que permiten evaluar el efecto de la propagación por movimiento propio y el efecto del filtro de magnitud:

| Match | Coordenadas Gaia        | Filtro magnitud |
|------|--------------------------|-----------------|
| 1    | J2016 (originales)       | No              |
| 2    | J2016 (originales)       | Sí              |
| 3    | B1875 (propagadas)       | No              |
| 4    | B1875 (propagadas)       | Sí              |

Comparar match 1 vs. match 3 (y match 2 vs. match 4) permite ver el efecto de la propagación. Comparar match 1 vs. match 2 (y match 3 vs. match 4) permite analizar el efecto del filtro de magnitud. 

Los parámetros utilizados inicialmente son un radio de búsqueda de 30" y una tolerancia de magnitud de Δmag = 1.5, justificados en el notebook `exploracion_tolerancia.ipynb`.
Posteriormente se utilizan radios de búsqueda de 23" y 46" para comparación.

### Análisis (`src/analysis/`)

#### `metrics.py`

Contiene tres funciones:

- `compute_metrics`: calcula las métricas de calidad de un match a partir de su tabla de pares:
  - cobertura (fracción de estrellas del CD con al menos un candidato)
  - fracción de identificaciones únicas y ambiguas
  - distribución de separaciones angulares (mediana y percentil 90, tanto para todos los pares como solo para los únicos)

- `metrics_to_table`: convierte una lista de dicts de métricas a una tabla exportable como CSV.

- `print_summary_table`: imprime la tabla comparativa en consola.

#### `plots.py`

Contiene funciones de visualización:

- `plot_separation_distributions`: compara las distribuciones de separación angular para los cuatro matches en dos paneles:
  - todos los pares
  - solo los pares con candidato único  
  Permite ver si los distintos criterios seleccionan pares más cercanos.

- `plot_quality_metrics`: muestra cobertura, fracción de únicos y fracción de ambiguos para cada match en un gráfico de barras agrupadas. Permite comparar entre los cuatro matches el trade-off entre completitud y ambigüedad.

- `plot_summary_table`: genera una imagen de la tabla de métricas formateada.

- `plot_pm_effect`: compara las distribuciones de separación angular entre dos matches separando las estrellas según su módulo de movimiento propio total. Permite evaluar si la propagación tiene un efecto diferencial sobre estrellas de alto movimiento propio. Se usa dos veces:
  - comparando match 1 vs. match 3 (sin filtro de magnitud)
  - comparando match 2 vs. match 4 (con filtro de magnitud)


---

## Análisis de resultados

Los resultados obtenidos (métricas de los matches) son analizados en `results/results.md`