import numpy as np
from src.utils.logger import get_logger

logger = get_logger("magnitudes")

def add_estimated_cd_magnitude(gaia):
    G = np.array(gaia['phot_g_mean_mag'], dtype=float)

    if 'bp_rp' in gaia.colnames:
        bp_rp = np.array(gaia['bp_rp'], dtype=float)
    else:
        bp_rp = (np.array(gaia['phot_bp_mean_mag'], dtype=float) -
                 np.array(gaia['phot_rp_mean_mag'], dtype=float))

    has_color = np.isfinite(G) & np.isfinite(bp_rp)

    V = np.where(
        has_color,
        G - 0.0257 - 0.0924 * bp_rp - 0.1623 * bp_rp**2,
        np.nan
    )

    A, B, C = -0.01335368, 1.076636, 0.2249828
    mag_cd_est = np.where(has_color, A*V**2 + B*V + C, np.nan)

    gaia['V_johnson']   = V
    gaia['mag_cd_est']  = mag_cd_est
    gaia['has_color']   = has_color

    n_missing = (~has_color).sum()
    logger.info(f"Sin color BP-RP: {n_missing} de {len(gaia)} ({100*n_missing/len(gaia):.1f}%)")
    return gaia