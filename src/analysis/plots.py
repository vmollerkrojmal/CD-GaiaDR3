import numpy as np
import matplotlib.pyplot as plt
from src.analysis.metrics import compute_metrics


def plot_separation_distributions(matches_dict, bins=80):
    """
    Compara las distribuciones de separación angular para los matches
    en dos paneles: todos los pares, y solo los pares únicos.
    """
    colors = ['steelblue', 'darkorange', 'seagreen', 'crimson']
    labels = list(matches_dict.keys())
    tables = list(matches_dict.values())

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Distribución de separaciones angulares por match', fontsize=13)

    for table, label, color in zip(tables, labels, colors):
        if table is None or len(table) == 0:
            continue

        sep = np.array(table['sep_arcsec'], dtype=float)
        ids_cd = np.array(table['cd_id'])

        axes[0].hist(sep, bins=bins, alpha=0.5, color=color,
                     label=label, density=True)

        count_map = dict(zip(*np.unique(ids_cd, return_counts=True)))
        mask_unique = np.array([count_map[i] == 1 for i in ids_cd])
        sep_unique = sep[mask_unique]

        if len(sep_unique) > 0:
            axes[1].hist(sep_unique, bins=bins, alpha=0.5, color=color,
                         label=label, density=True)

    for ax, title in zip(axes, ['Todos los pares', 'Solo pares únicos']):
        ax.set_xlabel('Separación angular [arcsec]')
        ax.set_ylabel('Densidad')
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_quality_metrics(matches_dict, gaia):
    """
    Muestra cobertura, fracción de únicos y fracción de ambiguos
    para cada match en un gráfico de barras agrupadas.
    """
    labels = list(matches_dict.keys())
    metrics = [compute_metrics(t, gaia, l)
               for l, t in matches_dict.items()]

    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - width, [m['coverage'] for m in metrics],
           width, label='Coverage', color='steelblue', alpha=0.8)
    ax.bar(x, [m['frac_unique'] for m in metrics],
           width, label='Frac. unique', color='seagreen', alpha=0.8)
    ax.bar(x + width, [m['frac_ambiguous'] for m in metrics],
           width, label='Frac. ambig.', color='crimson', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel('Fracción')
    ax.set_ylim(0, 1.05)
    ax.set_title('Métricas de calidad por match')
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    return fig


def plot_pm_effect(match_no_pm, match_with_pm,
                   label_no_pm="sin propagar",
                   label_with_pm="con propagación",
                   pm_threshold_mas=50, bins=60):
    """
    Compara las separaciones angulares entre dos matches separando
    las estrellas según su módulo de movimiento propio.
    """
    def add_pm_total(pairs):
        pmra  = np.array(pairs['pmra'],  dtype=float)
        pmdec = np.array(pairs['pmdec'], dtype=float)
        pairs['pm_total'] = np.sqrt(pmra**2 + pmdec**2)
        return pairs

    m_no_pm   = add_pm_total(match_no_pm.copy())
    m_with_pm = add_pm_total(match_with_pm.copy())

    mask_low_no_pm    = m_no_pm['pm_total']   <  pm_threshold_mas
    mask_high_no_pm   = m_no_pm['pm_total']   >= pm_threshold_mas
    mask_low_with_pm  = m_with_pm['pm_total'] <  pm_threshold_mas
    mask_high_with_pm = m_with_pm['pm_total'] >= pm_threshold_mas

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Efecto de la propagación según pm total '
                 f'(umbral = {pm_threshold_mas} mas/año)', fontsize=13)

    for ax, mask_no_pm, mask_with_pm, titulo in zip(
        axes,
        [mask_low_no_pm,   mask_high_no_pm],
        [mask_low_with_pm, mask_high_with_pm],
        [f'pm < {pm_threshold_mas} mas/año',
         f'pm ≥ {pm_threshold_mas} mas/año']
    ):
        sep_no_pm   = np.array(m_no_pm['sep_arcsec'][mask_no_pm],     dtype=float)
        sep_with_pm = np.array(m_with_pm['sep_arcsec'][mask_with_pm], dtype=float)

        ax.hist(sep_no_pm, bins=bins, alpha=0.5, density=True,
                color='steelblue',
                label=f'{label_no_pm} (n={len(sep_no_pm)})')
        ax.hist(sep_with_pm, bins=bins, alpha=0.5, density=True,
                color='crimson',
                label=f'{label_with_pm} (n={len(sep_with_pm)})')

        ax.axvline(np.nanmedian(sep_no_pm), color='steelblue', linestyle='--',
                   label=f'med {label_no_pm} = {np.nanmedian(sep_no_pm):.1f}"')
        ax.axvline(np.nanmedian(sep_with_pm), color='crimson', linestyle='--',
                   label=f'med {label_with_pm} = {np.nanmedian(sep_with_pm):.1f}"')

        ax.set_xlabel('Separación angular [arcsec]')
        ax.set_ylabel('Densidad')
        ax.set_title(titulo)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_summary_table(metrics_list):
    """
    Genera una figura con la tabla de métricas formateada,
    lista para guardar como imagen.
    """
    col_labels = [
        'Match', 'Cover', 'Unique', 'Ambig',
        'Sep med"', 'Sep p90"', 'SepU med"', 'SepU p90"'
    ]

    rows = []
    for m in metrics_list:
        rows.append([
            m['label'],
            f"{m['coverage']:.1%}",
            f"{m['frac_unique']:.1%}",
            f"{m['frac_ambiguous']:.1%}",
            f"{m['sep_median']:.2f}",
            f"{m['sep_p90']:.2f}",
            f"{m['sep_unique_median']:.2f}",
            f"{m['sep_unique_p90']:.2f}",
        ])

    n_rows = len(rows)
    n_cols = len(col_labels)

    legend_lines = [
        "Cover = fracción de CD con al menos 1 candidato en Gaia",
        "Unique = de los que tienen match, fracción con candidato único",
        "Ambig = de los que tienen match, fracción con múltiples candidatos",
        "Sep med = mediana de separación angular, todos los pares [arcsec]",
        "Sep p90 = percentil 90 de separación angular, todos los pares [arcsec]",
        "SepU med = mediana de separación angular, solo para pares con candidato único [arcsec]",
        "SepU p90 = percentil 90 de separación angular, solo para pares con candidato único [arcsec]",
    ]
    legend = "\n".join(legend_lines)
    n_legend_lines = len(legend_lines)

    # Altura proporcional: filas de tabla + líneas de leyenda
    fig_height = 0.5 * (n_rows + 1) + 0.22 * n_legend_lines + 0.5
    fig, ax = plt.subplots(figsize=(13, fig_height))
    ax.axis('off')

    # La tabla ocupa la parte superior, dejando espacio para la leyenda abajo
    legend_fraction = (0.22 * n_legend_lines) / fig_height
    table_bottom    = legend_fraction + 0.05

    t = ax.table(
        cellText=rows,
        colLabels=col_labels,
        cellLoc='center',
        loc='upper center',
        bbox=[0, table_bottom, 1, 1 - table_bottom]
    )
    t.auto_set_font_size(False)
    t.set_fontsize(10)
    t.auto_set_column_width(col=list(range(n_cols)))

    # Altura de las filas
    for (row, col), cell in t.get_celld().items():
        cell.set_height(0.08)

    for col in range(n_cols):
        t[0, col].set_facecolor('#2c5f8a')
        t[0, col].set_text_props(color='white', fontweight='bold')

    for row in range(1, n_rows + 1):
        color = '#f0f4f8' if row % 2 == 0 else 'white'
        for col in range(n_cols):
            t[row, col].set_facecolor(color)

    fig.text(0.5, legend_fraction / 2, legend,
             ha='center', va='center',
             fontsize=8, color='gray', family='monospace',
             linespacing=1.6)

    return fig