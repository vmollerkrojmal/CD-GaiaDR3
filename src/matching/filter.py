import numpy as np
from src.utils.logger import get_logger

logger = get_logger("filter")

def apply_magnitude_filter(pairs, delta_mag, label=""):
    logger.info(f"Filtro magnitud {label} (Δm = {delta_mag})")
    logger.info(f"Pares antes del filtro: {len(pairs)}")

    diff_mag = np.abs(
        np.array(pairs['cd_mag'],     dtype=float) -
        np.array(pairs['mag_cd_est'], dtype=float)
    )

    has_conversion = np.isfinite(diff_mag)
    passes         = has_conversion & (diff_mag <= delta_mag)

    n_missing = (~has_conversion).sum()
    if n_missing > 0:
        logger.info(f"Pares sin conversión de magnitud (excluidos): {n_missing}")

    filtered_pairs = pairs[passes].copy()
    logger.info(f"Pares después del filtro: {len(filtered_pairs)}")
    return filtered_pairs