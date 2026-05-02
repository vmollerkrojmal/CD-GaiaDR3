from astroquery.vizier import Vizier
import os
from src.utils.logger import get_logger

logger = get_logger("cd_catalog")

OUTPUT_DIR = "../../data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sin límite de filas
Vizier.ROW_LIMIT = -1

# ID del catálogo Córdoba-Durchmusterung
catalog_id = "I/114/cd"

logger.info("Descargando catálogo CD desde VizieR")
catalogs = Vizier.get_catalogs(catalog_id)

cd = catalogs[0]

logger.info(f"Filas: {len(cd)}")
logger.info(f"Columnas: {cd.colnames}")

csv_path = os.path.join(OUTPUT_DIR, "cd_catalog.csv")
fits_path = os.path.join(OUTPUT_DIR, "cd_catalog.fits")

cd.write(csv_path, format="csv", overwrite=True)
cd.write(fits_path, format="fits", overwrite=True)

logger.info("Catálogo guardado en:")
logger.info(csv_path)
logger.info(fits_path)