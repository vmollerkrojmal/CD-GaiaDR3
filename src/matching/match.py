import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from src.utils.logger import get_logger

logger = get_logger("match")

def positional_match(gaia, tolerance_arcsec,
                     col_ra_gaia='ra', col_dec_gaia='dec',
                     label=""):
    logger.info(f"Match {label}")
    logger.info(f"Tolerancia posicional: {tolerance_arcsec}\"")
    logger.info(f"Columnas Gaia usadas: {col_ra_gaia}, {col_dec_gaia}")

    # Si se usan coordenadas propagadas, excluir filas sin pm
    if col_ra_gaia == 'ra_prop' or col_dec_gaia == 'dec_prop':
        table = gaia[gaia['has_pm']]
        logger.info(f"Filas con pm disponible: {len(table)} de {len(gaia)}")
    else:
        table = gaia
        logger.info(f"Filas en tabla: {len(table)}")

    # Forzar unidades a deg para evitar conflictos post-join
    cd_coords = SkyCoord(
        ra=np.array(table['cd_ra'],        dtype=float) * u.deg,
        dec=np.array(table['cd_dec'],      dtype=float) * u.deg
    )
    gaia_coords = SkyCoord(
        ra=np.array(table[col_ra_gaia],   dtype=float) * u.deg,
        dec=np.array(table[col_dec_gaia], dtype=float) * u.deg
    )

    sep = cd_coords.separation(gaia_coords).arcsec

    mask  = sep <= tolerance_arcsec
    pairs = table[mask].copy()
    pairs['sep_arcsec'] = sep[mask]

    logger.info(f"Pares dentro de la tolerancia: {len(pairs)}")
    return pairs