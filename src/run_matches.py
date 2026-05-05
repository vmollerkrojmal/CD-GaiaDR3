from astropy.table import Table, join

from process_data.magnitudes  import add_estimated_cd_magnitude
from process_data.propagation import propagate_gaia_coords
from matching.match import positional_match
from matching.filter import apply_magnitude_filter
from analysis.metrics import compute_metrics, print_summary_table, metrics_to_table
from analysis.plots import plot_separation_distributions, plot_quality_metrics, plot_pm_effect, plot_summary_table
from src.utils.logger import get_logger

from pathlib import Path

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
        - Crossmatch
        - Cálculo de métricas del resultado
        - Generación y guardado de tablas y plots del resultado

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
    # Cargar tablas
    cd = Table.read("../data/processed/cd_catalog_icrs_full.fits")
    gaia = Table.read("../data/processed/gaia_merge.fits")

    # Agregar cd_mag
    cd_mag = cd['cd_id', 'mag']
    cd_mag.rename_column('mag', 'cd_mag')
    gaia = join(gaia, cd_mag, keys='cd_id', join_type='left')

    # Preprocesar Gaia
    gaia = add_estimated_cd_magnitude(gaia)
    gaia = propagate_gaia_coords(gaia)

    param_label = f'r = {TOLERANCE:.0f}"  —  Δmag = {DELTA_MAG}'

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

    # Guardar matches
    matches_dir = Path("../data/matches")
    matches_dir.mkdir(parents=True, exist_ok=True)

    for name, table in [("match1", match1), ("match2", match2),
                        ("match3", match3), ("match4", match4)]:
        path = matches_dir / f"{name}.fits"
        table.write(str(path), overwrite=True)
        logger.info(f"Guardado {path} ({len(table)} filas)")

    # Calcular métricas
    matches = {
        "1: pos. sin pm": match1,
        "2: pos.+mag sin pm": match2,
        "3: pos. con pm": match3,
        "4: pos.+mag con pm": match4,
    }

    metrics_list = [compute_metrics(t, gaia, l) for l, t in matches.items()]

    # Guardar CSV de tabla de métricas
    results_dir = Path("../results")
    results_dir.mkdir(exist_ok=True)
    metrics_table = metrics_to_table(metrics_list)
    metrics_table.write(results_dir / f"metrics_r{TOLERANCE:.0f}_dm{DELTA_MAG}.csv", format='csv', overwrite=True)

    # Guardar imagen de tabla de métricas
    fig_table = plot_summary_table(metrics_list)
    fig_table.suptitle(param_label, fontsize=11, color='gray', y=1.01)
    fig_table.savefig(results_dir / f"metrics_table_r{TOLERANCE:.0f}_dm{DELTA_MAG}.png", dpi=150, bbox_inches='tight')

    # Print en consola de tabla de métricas
    print_summary_table(metrics_list)

    # Generar y guardar plots
    fig1 = plot_separation_distributions(matches, param_label=param_label)
    fig1.savefig(results_dir / f"separation_distributions_r{TOLERANCE:.0f}_dm{DELTA_MAG}.png", dpi=150)

    fig2 = plot_quality_metrics(matches, gaia, param_label=param_label)
    fig2.savefig(results_dir / f"quality_metrics_r{TOLERANCE:.0f}_dm{DELTA_MAG}.png", dpi=150)

    fig_pm_1_3 = plot_pm_effect(
        match1, match3,
        label_no_pm="pos. sin pm",
        label_with_pm="pos. con pm",
        pm_threshold_mas=50,
        param_label=param_label
    )
    fig_pm_1_3.savefig(results_dir / f"pm_effect_1_3_r{TOLERANCE:.0f}_dm{DELTA_MAG}.png", dpi=150)

    fig_pm_2_4 = plot_pm_effect(
        match2, match4,
        label_no_pm="pos.+mag sin pm",
        label_with_pm="pos.+mag con pm",
        pm_threshold_mas=50,
        param_label=param_label
    )
    fig_pm_2_4.savefig(results_dir / f"pm_effect_2_4_r{TOLERANCE:.0f}_dm{DELTA_MAG}.png", dpi=150)

if __name__ == "__main__":
    main()