from astroquery.gaia import Gaia
from astropy.table import Table, vstack
from dotenv import load_dotenv
import numpy as np
import os
import time
from src.utils.logger import get_logger

logger = get_logger("gaia_crossmatch")

INPUT_FILE = "../../data/processed/cd_small.fits"
OUTPUT_DIR = "../../data/gaia_bins"

N_BINS = 40
RADIUS_DEG = 90 / 3600
MAG_LIMIT = 15

SLEEP_BETWEEN_QUERIES = 15

os.makedirs(OUTPUT_DIR, exist_ok=True)

load_dotenv()
user = os.getenv("GAIA_USER")
password = os.getenv("GAIA_PASSWORD")

logger.info("Login en Gaia")
Gaia.login(user=user, password=password)

table_name = f"cd_small_{int(time.time())}"
user_schema = f"user_{user}"

logger.info(f"Tabla a usar: {table_name}")

logger.info("Cargando catálogo CD")
cd = Table.read(INPUT_FILE)

try:
    logger.info("Subiendo tabla a Gaia")
    Gaia.upload_table(
        upload_resource=cd,
        table_name=table_name
    )
    logger.info("Upload completo")
except Exception as e:
    logger.error(f"Error subiendo tabla: {e}")
    raise

dec_min = np.min(cd["dec"])
dec_max = np.max(cd["dec"])

logger.info(f"DEC min: {dec_min}")
logger.info(f"DEC max: {dec_max}")

bins = np.linspace(dec_min, dec_max, N_BINS + 1)

for i in range(N_BINS):
    dec_lo = bins[i]
    dec_hi = bins[i + 1]

    logger.info(f"=== BIN {i+1}/{N_BINS} ===")
    logger.info(f"DEC: [{dec_lo}, {dec_hi})")

    output_file = os.path.join(OUTPUT_DIR, f"bin_{i}.fits")

    if os.path.exists(output_file):
        logger.info("Ya existe, salteando")
        continue

    query = f"""
    SELECT
        c.cd_id,

        g.source_id,
        g.ra, g.dec,
        g.pmra, g.pmra_error,
        g.pmdec, g.pmdec_error,
        g.phot_g_mean_mag,
        g.phot_bp_mean_mag,
        g.phot_rp_mean_mag,

        c.ra AS cd_ra,
        c.dec AS cd_dec,

        DISTANCE(
            POINT('ICRS', g.ra, g.dec),
            POINT('ICRS', c.ra, c.dec)
        ) AS ang_sep

    FROM {user_schema}.{table_name} AS c

    JOIN gaiadr3.gaia_source AS g
    ON CONTAINS(
        POINT('ICRS', g.ra, g.dec),
        CIRCLE('ICRS', c.ra, c.dec, {RADIUS_DEG})
    ) = 1

    WHERE c.dec >= {dec_lo}
      AND c.dec < {dec_hi}
      AND g.phot_g_mean_mag < {MAG_LIMIT}
    """

    try:
        logger.info("Query iniciada")
        job = Gaia.launch_job_async(query)

        logger.info("Obteniendo resultados")
        result = job.get_results()

        result.write(output_file, overwrite=True)
        logger.info(f"Guardado en {output_file}")

    except Exception as e:
        logger.error(f"Error en bin {i}: {e}")

    logger.info(f"Sleeping {SLEEP_BETWEEN_QUERIES}s")
    time.sleep(SLEEP_BETWEEN_QUERIES)

logger.info("Proceso terminado")