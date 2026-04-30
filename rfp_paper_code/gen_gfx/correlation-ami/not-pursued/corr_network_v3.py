#!/usr/bin/env python3
"""Network graph of highly-correlated metric pairs with all nodes labeled.

Same as corr_network.py (EDGE_THRESHOLD=0.70) but labels ALL nodes in the
graph using short prefix stripping.  font_size=5.

Prefix substitutions:
  combined_        -> c.
  clientrects_     -> cr.
  webgl2_          -> wgl2.
  webgl_           -> wgl.
  screen_          -> scr.
  fonts_variant_   -> fv.
  canvas_canvasdata -> cv.
  canvassoftware_  -> cvs.

Outputs corr_network_labeled.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx
from pathlib import Path

from _corr_utils import load_rows, load_per_metric, get_category, \
                        CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE

OUT_PATH       = HERE / f'corr_network_labeled{FILTER_SUFFIX}.png'
EDGE_THRESHOLD = 0.70

print("Loading pairs…")
rows = load_rows()
_, max_ami = load_per_metric(rows)

# ── Build graph ───────────────────────────────────────────────────────────────
print(f"Building graph  (threshold = {EDGE_THRESHOLD})…")
G = nx.Graph()
for r in rows:
    if r['ami'] >= EDGE_THRESHOLD:
        G.add_edge(r['metric1'], r['metric2'], weight=r['ami'])

# Discard isolated nodes
G.remove_nodes_from(list(nx.isolates(G)))

n_nodes = G.number_of_nodes()
n_edges = G.number_of_edges()
print(f"  {n_nodes} nodes, {n_edges} edges")

if n_nodes == 0:
    print("No edges above threshold — lower EDGE_THRESHOLD and retry.")
    raise SystemExit(1)

# ── Layout ────────────────────────────────────────────────────────────────────
print("Computing layout…")
if n_nodes <= 300:
    pos = nx.kamada_kawai_layout(G, weight='weight')
else:
    pos = nx.spring_layout(G, weight='weight', seed=42, iterations=50)

# ── Visual attributes ─────────────────────────────────────────────────────────
node_colors = [CATEGORY_COLORS[get_category(v)] for v in G.nodes()]
node_sizes  = [60 + 200 * max_ami.get(v, 0) ** 2 for v in G.nodes()]

edges     = list(G.edges(data='weight'))
edge_vals = [w for _, _, w in edges]
edge_widths = [0.3 + 3.5 * ((w - EDGE_THRESHOLD) / (1.0 - EDGE_THRESHOLD + 1e-9)) ** 1.5
               for w in edge_vals]
edge_colors = [plt.cm.Oranges(0.3 + 0.7 * (w - EDGE_THRESHOLD) /
               (1.0 - EDGE_THRESHOLD + 1e-9)) for w in edge_vals]


def shorten_label(v):
    """Apply short prefix substitutions for readable node labels."""
    s = v
    # Order matters: more-specific prefixes before less-specific ones
    s = s.replace('canvas_canvasdata', 'cv.')
    s = s.replace('canvassoftware_',   'cvs.')
    s = s.replace('fonts_variant_',    'fv.')
    s = s.replace('clientrects_',      'cr.')
    s = s.replace('webgl2_',           'wgl2.')
    s = s.replace('webgl_',            'wgl.')
    s = s.replace('screen_',           'scr.')
    s = s.replace('combined_',         'c.')
    return s


# ── Draw ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 14))

nx.draw_networkx_edges(
    G, pos, ax=ax,
    edgelist=[(u, v) for u, v, _ in edges],
    width=edge_widths, edge_color=edge_colors, alpha=0.6,
)
nx.draw_networkx_nodes(
    G, pos, ax=ax,
    node_color=node_colors, node_size=node_sizes,
    alpha=0.85, linewidths=0.3, edgecolors='#333333',
)

# Label ALL nodes in the graph with short labels
short_labels = {v: shorten_label(v) for v in G.nodes()}
nx.draw_networkx_labels(
    G, pos, labels=short_labels, ax=ax,
    font_size=5, font_color='#111111', alpha=0.8,
)

ax.set_title(
    f'Metric Correlation Network  (AMI >= {EDGE_THRESHOLD}, all nodes labeled)\n'
    f'{n_nodes} nodes · {n_edges} edges    '
    f'(node size ∝ max-AMI, edge width ∝ AMI above threshold)',
    fontsize=11,
)
ax.axis('off')

# Category legend
handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c) for c in CATEGORY_ORDER]
ax.legend(handles=handles, fontsize=8, loc='lower left', ncol=2,
          framealpha=0.9, title='Category')

plt.tight_layout()
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight')
print(f"Wrote {OUT_PATH}")
