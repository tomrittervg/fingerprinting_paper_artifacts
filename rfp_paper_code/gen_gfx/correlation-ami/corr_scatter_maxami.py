#!/usr/bin/env python3
"""Generate the four per-metric scatter plots (individual PNGs).

Outputs:
  corr_scatter_hhi_maxami_all.png
  corr_scatter_entropy_maxami_all.png
  corr_scatter_hhi_maxami_crosscat.png
  corr_scatter_entropy_maxami_crosscat.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from _corr_utils import HERE
from _scatter_core import PLOTS, load_scatter_data, build_scatter_data, draw_scatter

data = load_scatter_data()

for spec in PLOTS:
    panel_data = build_scatter_data(spec, data)
    if panel_data is None:
        print(f"Skipping {spec.out_name}: CORR_XTBL not set (no HHI data)")
        continue

    fig, ax = plt.subplots(figsize=(9, 7))
    draw_scatter(ax, panel_data)
    fig.text(0.5, -0.01, 'Dotted lines indicate median values.',
             ha='center', fontsize=11, color='gray', style='italic')
    plt.tight_layout()
    out_path = HERE / spec.out_name
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Wrote {out_path}")
