# Proyecto: Crossmatch entre Córdoba-Durchmusterung y Gaia DR3

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

    notebooks/
        exploracion_inicial.ipynb

    src/
        obtain_data/
            cd_catalog.py
            process_cd_catalog.py
            gaia_crossmatch.py
        utils/
            logger.py   # logger de mensajes en consola
         


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

#### Autenticación

Requiere un archivo `.env` con usuario y password del archivo de Gaia.

Ejemplo de contenido del archivo `.env`:

    GAIA_USER=...
    GAIA_PASSWORD=...



#### Procedimiento

1. login en el archivo Gaia  
2. subida del catálogo CD (`ra`, `dec`) como tabla  
3. ejecución de queries en bins de declinación  


#### Parámetros utilizados

- número de bins en declinación: 40  
- radio de búsqueda: 90 arcsec  
- límite de magnitud: G < 15  

El rango de declinación se divide en 40 intervalos para evitar queries excesivamente pesadas, mejorar la estabilidad del servidor y facilitar la ejecución secuencial. 

El catálogo CD presenta errores posicionales del orden de 20–30 arcsec, por lo que se adopta un radio de 90 arcsec
con el objetivo de construir un crossmatch amplio, que evite perder candidatos verdaderos.


Teniendo en cuenta el límite en magnitud (12) de CD, y dado que utiliza magnitudes visuales mientras Gaia utiliza el sistema fotométrico G, BP, RP, se adopta un criterio conservador de phot_g_mean_mag < 15.
Considerando que Gaia DR3 alcanza aproximadamente G ≈ 20–21, este filtro reduce de forma sustancial el volumen de datos, mientras que evita descartar posibles matches reales.

En esta etapa no se busca una identificación definitiva, sino generar un conjunto de candidatos para análisis posterior.



#### Output

Cada bin genera un archivo:

    data/gaia_bins/bin_i.fits

que contiene fuentes de Gaia dentro del radio de búsqueda con parámetros astrométricos y fotométricos y separación angular respecto a la posición del catálogo CD.

---

## Enfoque metodológico

El pipeline está diseñado en etapas:

1. Crossmatch amplio  
   Generación de candidatos con criterios poco restrictivos  

2. Filtrado posterior  
   Reducción de falsos positivos mediante criterios adicionales  

3. Análisis estadístico  
   Evaluación de la calidad del match y de los posibles sesgos.