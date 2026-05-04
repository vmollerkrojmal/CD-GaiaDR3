import numpy as np
from astropy.table import MaskedColumn, Table
import astropy.units as u
from src.utils.logger import get_logger

logger = get_logger("magnitudes")


def propagate_gaia_coords(gaia, epoch_target=1875.0, epoch_ref=2016.0):
    delta_t = epoch_target - epoch_ref
    factor  = 3.6e6 #convertir unidades de pm

    if hasattr(gaia['pmra'], 'mask'):
        has_pm = ~gaia['pmra'].mask & ~gaia['pmdec'].mask
    else:
        has_pm = np.ones(len(gaia), dtype=bool)

    ra_prop = np.where(
        has_pm,
        gaia['ra'] + gaia['pmra'].filled(0) * delta_t / factor,
        np.nan
    )
    dec_prop = np.where(
        has_pm,
        gaia['dec'] + gaia['pmdec'].filled(0) * delta_t / factor,
        np.nan
    )

    gaia['has_pm']   = has_pm
    gaia['ra_prop']  = MaskedColumn(ra_prop,  mask=~has_pm, unit=u.deg)
    gaia['dec_prop'] = MaskedColumn(dec_prop, mask=~has_pm, unit=u.deg)

    n_missing = (~has_pm).sum()
    logger.info(f"Sin movimiento propio: {n_missing} de {len(gaia)} ({100*n_missing/len(gaia):.1f}%)")
    return gaia