from astropy.table import Table
from astropy.coordinates import SkyCoord, FK5
import astropy.units as u
import os
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("process_cd_catalog")

INPUT_FILE = "../../data/raw/cd_catalog.fits"
OUTPUT_DIR = "../../data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

logger.info("Leyendo catálogo descargado")
cd_table = Table.read(INPUT_FILE)

logger.info("Interpretando coordenadas")
coords_old = SkyCoord(
    ra=cd_table['RA1875'],
    dec=cd_table['DE1875'],
    unit=(u.hourangle, u.deg),
    frame=FK5(equinox="J1875")
)

coords_icrs = coords_old.icrs
logger.info("Coordenadas transformadas a ICRS")

cd_table["ra_icrs"] = coords_icrs.ra.deg
cd_table["dec_icrs"] = coords_icrs.dec.deg

cd_table["cd_id"] = np.arange(len(cd_table), dtype=np.int64)

csv_full_path = os.path.join(OUTPUT_DIR, "cd_catalog_icrs_full.csv")
fits_full_path = os.path.join(OUTPUT_DIR, "cd_catalog_icrs_full.fits")

cd_table.write(csv_full_path, format="csv", overwrite=True)
cd_table.write(fits_full_path, format="fits", overwrite=True)
logger.info("Catálogo CD en ICRS full guardado en:")
logger.info(csv_full_path)
logger.info(fits_full_path)

cd_small = cd_table[["cd_id", "ra_icrs", "dec_icrs"]]
cd_small.rename_columns(["ra_icrs", "dec_icrs"], ["ra", "dec"])

csv_small_path = os.path.join(OUTPUT_DIR, "cd_small.csv")
fits_small_path = os.path.join(OUTPUT_DIR, "cd_small.fits")

cd_small.write(csv_small_path, format="csv", overwrite=True)
cd_small.write(fits_small_path, format="fits", overwrite=True)
logger.info("Catálogo CD en ICRS small guardado en:")
logger.info(csv_small_path)
logger.info(fits_small_path)