import numpy as np
from astropy.table import Table


def compute_metrics(pairs, gaia, label=""):
    """
    Dado un conjunto de pares, calcula las métricas de calidad.
    """
    total_cd_ids = np.unique(np.array(gaia['cd_id']))
    n_cd_total   = len(total_cd_ids)

    if pairs is None or len(pairs) == 0:
        return {
            'label':              label,
            'n_cd_total':         n_cd_total,
            'n_with_match':       0,
            'n_without_match':    n_cd_total,
            'n_unique':           0,
            'n_ambiguous':        0,
            'coverage':           0.0,
            'frac_unique':        0.0,
            'frac_ambiguous':     0.0,
            'sep_median':         np.nan,
            'sep_p90':            np.nan,
            'sep_unique_median':  np.nan,
            'sep_unique_p90':     np.nan,
        }

    ids_cd            = np.array(pairs['cd_id'])
    unique_ids, counts = np.unique(ids_cd, return_counts=True)

    n_with_match    = len(unique_ids)
    n_without_match = n_cd_total - n_with_match
    n_unique        = (counts == 1).sum()
    n_ambiguous     = (counts > 1).sum()

    coverage      = n_with_match / n_cd_total
    frac_unique   = n_unique   / n_with_match if n_with_match > 0 else 0
    frac_ambiguous= n_ambiguous/ n_with_match if n_with_match > 0 else 0

    sep = np.array(pairs['sep_arcsec'], dtype=float)
    sep_median = np.nanmedian(sep)
    sep_p90    = np.nanpercentile(sep, 90)

    # Separación solo para pares únicos
    count_map   = dict(zip(unique_ids, counts))
    mask_unique = np.array([count_map[i] == 1 for i in ids_cd])
    sep_unique  = sep[mask_unique]

    sep_unique_median = np.nanmedian(sep_unique)    if len(sep_unique) > 0 else np.nan
    sep_unique_p90    = np.nanpercentile(sep_unique, 90) if len(sep_unique) > 0 else np.nan

    return {
        'label':              label,
        'n_cd_total':         n_cd_total,
        'n_with_match':       n_with_match,
        'n_without_match':    n_without_match,
        'n_unique':           n_unique,
        'n_ambiguous':        n_ambiguous,
        'coverage':           coverage,
        'frac_unique':        frac_unique,
        'frac_ambiguous':     frac_ambiguous,
        'sep_median':         sep_median,
        'sep_p90':            sep_p90,
        'sep_unique_median':  sep_unique_median,
        'sep_unique_p90':     sep_unique_p90,
    }


def print_summary_table(metrics_list):
    print(f"\n{'─'*90}")
    print(f"{'Match':<35} {'Cover':>7} {'Unique':>8} {'Ambig':>8} "
          f"{'Sep med':>9} {'Sep p90':>9} {'SepU med':>10} {'SepU p90':>10}")
    print(f"{'─'*90}")

    for m in metrics_list:
        print(
            f"{m['label']:<35} "
            f"{m['coverage']:>7.1%} "
            f"{m['frac_unique']:>8.1%} "
            f"{m['frac_ambiguous']:>8.1%} "
            f"{m['sep_median']:>9.2f}\" "
            f"{m['sep_p90']:>9.2f}\" "
            f"{m['sep_unique_median']:>10.2f}\" "
            f"{m['sep_unique_p90']:>10.2f}\""
        )
    print(f"{'─'*90}")
    print("Cover = fracción de CD con al menos 1 candidato en Gaia")
    print("Unique = de los que tienen match, fracción con candidato único")
    print("Ambig = de los que tienen match, fracción con múltiples candidatos")
    print("Sep med = mediana de separación angular, todos los pares [arcsec]")
    print("Sep p90 = percentil 90 de separación angular, todos los pares [arcsec]")
    print("SepU med = mediana de separación angular, solo para pares con candidato único [arcsec]")
    print("SepU p90 = percentil 90 de separación angular, solo para pares con candidato único [arcsec]")


def metrics_to_table(metrics_list):
    """
    Convierte una lista de dicts de métricas a una astropy Table,
    para guardar como csv o fits.
    """
    return Table({
        'match':            [m['label']            for m in metrics_list],
        'n_cd_total':       [m['n_cd_total']        for m in metrics_list],
        'n_with_match':     [m['n_with_match']      for m in metrics_list],
        'n_without_match':  [m['n_without_match']   for m in metrics_list],
        'n_unique':         [m['n_unique']           for m in metrics_list],
        'n_ambiguous':      [m['n_ambiguous']        for m in metrics_list],
        'coverage':         [m['coverage']           for m in metrics_list],
        'frac_unique':      [m['frac_unique']        for m in metrics_list],
        'frac_ambiguous':   [m['frac_ambiguous']     for m in metrics_list],
        'sep_median':       [m['sep_median']         for m in metrics_list],
        'sep_p90':          [m['sep_p90']            for m in metrics_list],
        'sep_unique_median':[m['sep_unique_median']  for m in metrics_list],
        'sep_unique_p90':   [m['sep_unique_p90']     for m in metrics_list],
    })