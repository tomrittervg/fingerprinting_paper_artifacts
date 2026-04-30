#!/usr/bin/env python3
"""Combine the four scatter plots into a single 2×2 panel figure.

Generates the panels directly from data (not by stitching pre-saved PNGs),
so font sizes, annotations, and layout can be tuned here independently of
the individual-plot scripts.

Layout:
  [HHI – all pairs]        [Entropy – all pairs]
  [HHI – cross-cat only]   [Entropy – cross-cat only]

Output: corr_scatter_4panel.png
"""
import os
os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from _corr_utils import HERE
from _scatter_core import PLOTS, load_scatter_data, build_scatter_data, draw_scatter

OUT_PATH = HERE / 'corr_scatter_4panel.png'

data = load_scatter_data()

fig, axes = plt.subplots(2, 2, figsize=(20, 16))

for ax, spec in zip(axes.flat, PLOTS):
    panel_data = build_scatter_data(spec, data)
    if panel_data is None:
        ax.set_visible(False)
        continue
    draw_scatter(
        ax, panel_data,
        fontsize_axis=14,
        fontsize_title=13,
        fontsize_ticks=11,
        fontsize_legend=10,
        legend_title_fontsize=11,
        legend_ncol=1,
    )

fig.text(0.5, 0.01, 'Dotted lines indicate median values.',
         ha='center', fontsize=12, color='gray', style='italic')

plt.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
