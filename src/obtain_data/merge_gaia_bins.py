from astropy.table import Table, vstack
import os
from src.utils.logger import get_logger

logger = get_logger("merge_gaia_bins")

INPUT_DIR = "../../data/gaia_bins"
OUTPUT_DIR = "../../data/processed"

files = sorted([
    os.path.join(INPUT_DIR, f)
    for f in os.listdir(INPUT_DIR)
    if f.endswith(".fits") and f.startswith("bin_")
])

if len(files) == 0:
    raise RuntimeError("No se encontraron bins")

bin_sizes = []
tables = []

for f in files:
    t = Table.read(f)
    n = len(t)
    bin_sizes.append(n)
    tables.append(t)

total_bins = sum(bin_sizes)
logger.info(f"Suma total de filas en bins: {total_bins}")

logger.info(f"Iniciando merge")
full = vstack(tables)

merge_size = len(full)
logger.info(f"Filas en bins: {merge_size}")

output_path = os.path.join(OUTPUT_DIR, "gaia_merge.fits")
full.write(output_path, format="fits", overwrite=True)
logger.info("Merge de bins de Gaia guardado en:")
logger.info(output_path)