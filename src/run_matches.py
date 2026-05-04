from astropy.table import Table, join

from process_data.magnitudes  import add_estimated_cd_magnitude
from process_data.propagation import propagate_gaia_coords
from matching.match import positional_match
from matching.filter import apply_magnitude_filter
from src.utils.logger import get_logger

import os

logger = get_logger("run_matches")

# Parámetros utilizados
TOLERANCE = 30.0
DELTA_MAG = 1.5

def main():
    """
    Función principal para ejecutar el flujo, incluyendo:
        - Procesamiento de los catálogos de entrada
        - Crossmatch
        - Filtrado

    PRECONDICIÓN:

    Asume que ya se cuenta con los catálogos de entrada:
    ../data/processed/cd_catalog_icrs_full.fits
    ../data/processed/gaia_merge.fits

    Estos catálogos se obtienen ejecutando en orden:
    ../src/obtain_data/cd_catalog.py
    ../src/obtain_data/process_cd_catalog.py
    ../src/obtain_data/gaia_crossmatch.py
    ../src/obtain_data/merge_gaia_bins.py
    """
    # Cargar
    cd = Table.read("../data/processed/cd_catalog_icrs_full.fits")
    gaia = Table.read("../data/processed/gaia_merge.fits")

    # Agregar cd_mag
    cd_mag = cd['cd_id', 'mag']
    cd_mag.rename_column('mag', 'cd_mag')
    gaia = join(gaia, cd_mag, keys='cd_id', join_type='left')

    # Preprocesar
    gaia = add_estimated_cd_magnitude(gaia)
    gaia = propagate_gaia_coords(gaia)

    # Matches
    match1 = positional_match(gaia, TOLERANCE,
                              col_ra_gaia='ra', col_dec_gaia='dec',
                              label="1 — posición sin propagar")

    match2 = apply_magnitude_filter(match1, DELTA_MAG,
                                    label="2 — posición + magnitud sin propagar")

    match3 = positional_match(gaia, TOLERANCE,
                              col_ra_gaia='ra_prop', col_dec_gaia='dec_prop',
                              label="3 — posición con propagación")

    match4 = apply_magnitude_filter(match3, DELTA_MAG,
                                    label="4 — posición + magnitud con propagación")

    # Guardar
    os.makedirs("../data/matches", exist_ok=True)
    for name, table in [("match1", match1), ("match2", match2),
                         ("match3", match3), ("match4", match4)]:
        path = f"../data/matches/{name}.fits"
        table.write(path, overwrite=True)
        logger.info(f"Guardado {path} ({len(table)} filas)")


if __name__ == "__main__":
    main()