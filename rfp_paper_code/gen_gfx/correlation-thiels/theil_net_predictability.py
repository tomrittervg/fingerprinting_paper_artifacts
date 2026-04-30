#!/usr/bin/env python3
"""Net predictability bar charts using Theil's U.

Chart types:
  "net"   — single axis, bars left (redundant) and right (independent)
            net = agg U(m->other) - agg U(other->m)
  "bidir" — top half: most predicted (bars left), bottom half: best predictors (bars right)
            Red labels = metric appears in both halves.

Aggregations: "max" or "mean" across pairs.

Pair scopes: "all", "same" (same-category), "cross" (cross-category).

Outputs (2 types x 2 aggs x 3 scopes = 12 PNGs):
  predictability_net_max_all.png    predictability_bidir_max_all.png
  predictability_net_mean_all.png   predictability_bidir_mean_all.png
  predictability_net_max_same.png   predictability_bidir_max_same.png
  predictability_net_mean_same.png  predictability_bidir_mean_same.png
  predictability_net_max_cross.png  predictability_bidir_max_cross.png
  predictability_net_mean_cross.png predictability_bidir_mean_cross.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from _theil_utils import (load_rows, load_per_metric, get_category,
                          CATEGORY_ORDER, CATEGORY_COLORS, FILTER_SUFFIX, HERE)


def shorten(m, n=35):
    return m if len(m) <= n else m[:n - 1] + '\u2026'


N_SHOW = 25
_ALL_SCOPES = [
    ('all',   'All Pairs'),
    ('same',  'Same-Category Pairs'),
    ('cross', 'Cross-Category Pairs'),
]
# THEIL_SCOPES env var: comma-separated list of scopes to generate.
# Default: all scopes. Example: THEIL_SCOPES=all,cross
_requested = os.environ.get('THEIL_SCOPES', '')
if _requested:
    _req_set = set(_requested.split(','))
    PAIR_SCOPES = [(s, l) for s, l in _ALL_SCOPES if s in _req_set]
else:
    PAIR_SCOPES = _ALL_SCOPES

# THEIL_CHARTS env var: comma-separated list of chart types to generate.
# Options: net, bidir. Default: both.
_req_charts = os.environ.get('THEIL_CHARTS', '')
GENERATE_NET = True
GENERATE_BIDIR = True
if _req_charts:
    _chart_set = set(_req_charts.split(','))
    GENERATE_NET = 'net' in _chart_set
    GENERATE_BIDIR = 'bidir' in _chart_set
AGGS = [
    {
        'key_pred': 'max_u_predicts',
        'key_pred_by': 'max_u_predicted_by',
        'key_pred_partner': 'max_u_predicts_partner',
        'key_pred_by_partner': 'max_u_predicted_by_partner',
        'name': 'max',
        'label': 'Max',
        'net_xlabel': "Net Predictability:  max U(m\u2192other) \u2212 max U(other\u2192m)",
        'bidir_xlabel': "Max Theil's U",
    },
    {
        'key_pred': 'mean_u_predicts',
        'key_pred_by': 'mean_u_predicted_by',
        'key_pred_partner': None,
        'key_pred_by_partner': None,
        'name': 'mean',
        'label': 'Mean',
        'net_xlabel': "Net Predictability:  mean U(m\u2192other) \u2212 mean U(other\u2192m)",
        'bidir_xlabel': "Mean Theil's U",
    },
]

rows = load_rows()

for scope, scope_label in PAIR_SCOPES:
    per_metric = load_per_metric(rows, pair_scope=scope)
    if not per_metric:
        print(f"  Skipping scope={scope}: no data")
        continue

    metrics = sorted(per_metric.keys())
    cats    = [get_category(m) for m in metrics]
    colors  = [CATEGORY_COLORS.get(c, '#888888') for c in cats]

    for agg in AGGS:
        pred    = np.array([per_metric[m][agg['key_pred']] for m in metrics])
        pred_by = np.array([per_metric[m][agg['key_pred_by']] for m in metrics])
        net     = pred - pred_by
        n_show  = min(N_SHOW, len(metrics) // 2)
        has_partners = agg['key_pred_partner'] is not None

        # ── Net chart ─────────────────────────────────────────────────────────
        if GENERATE_NET:
            sorted_idx = np.argsort(net)
            show_idx = list(sorted_idx[:n_show]) + list(sorted_idx[-n_show:])

            fig, ax = plt.subplots(figsize=(12, 12))
            y = np.arange(len(show_idx))
            bar_vals_net = [net[i] for i in show_idx]

            ax.barh(y, bar_vals_net,
                    color=[colors[i] for i in show_idx],
                    height=0.72, edgecolor='none', alpha=0.85)

            if has_partners:
                for yi, idx in enumerate(show_idx):
                    m = metrics[idx]
                    v = bar_vals_net[yi]
                    if v >= 0:
                        partner = per_metric[m][agg['key_pred_partner']]
                    else:
                        partner = per_metric[m][agg['key_pred_by_partner']]
                    if partner:
                        ha = 'left' if v >= 0 else 'right'
                        x_off = 0.005 if v >= 0 else -0.005
                        ax.text(x_off if v >= 0 else v + x_off, yi,
                                f' {shorten(partner, 25)}',
                                ha=ha, va='center', fontsize=4.5, alpha=0.6,
                                style='italic')

            ax.set_yticks(y)
            ax.set_yticklabels([shorten(metrics[i]) for i in show_idx], fontsize=6.5)
            ax.axvline(0, color='black', lw=0.8)
            ax.set_xlabel(agg['net_xlabel'], fontsize=10)
            ax.set_title(f"Net Predictability by Metric \u2014 {agg['label']} (Theil's U)\n"
                         f"\u2190 Redundant (predicted by others)     "
                         f"Independent predictor \u2192\n[{scope_label}]",
                         fontsize=12)
            ax.grid(axis='x', lw=0.3, alpha=0.5)

            ax.axhline(n_show - 0.5, color='gray', lw=1, ls=':', alpha=0.5)
            gap_count = len(metrics) - 2 * n_show
            if gap_count > 0:
                ax.text(0.01, n_show - 0.5,
                        f'\u2500 gap ({gap_count} metrics) \u2500',
                        transform=ax.get_yaxis_transform(),
                        ha='left', va='center', fontsize=7, alpha=0.5, style='italic')

            handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c)
                       for c in CATEGORY_ORDER]
            ax.legend(handles=handles, fontsize=6.5, loc='lower right', ncol=2,
                      framealpha=0.9)

            plt.tight_layout()
            out = HERE / f'predictability_net_{agg["name"]}_{scope}{FILTER_SUFFIX}.png'
            fig.savefig(out, dpi=150, bbox_inches='tight')
            print(f"Wrote {out}")
            plt.close(fig)

        # ── Bidir chart ───────────────────────────────────────────────────────
        if GENERATE_BIDIR:
            top_pred_idx = list(np.argsort(-pred)[:n_show])
            top_pred_by_idx = list(np.argsort(-pred_by)[:n_show])

            top_pred_names = {metrics[i] for i in top_pred_idx}
            top_pred_by_names = {metrics[i] for i in top_pred_by_idx}
            overlap = top_pred_names & top_pred_by_names

            show_pred_by = top_pred_by_idx                   # descending: biggest at top
            show_pred = list(reversed(top_pred_idx))         # ascending: biggest at bottom

            fig, ax = plt.subplots(figsize=(12, 12))

            y_pos = 0
            y_positions = []
            bar_vals = []
            bar_colors_list = []
            bar_labels = []
            label_text_colors = []
            bar_partners = []

            for idx in show_pred_by:
                m = metrics[idx]
                y_positions.append(y_pos)
                bar_vals.append(-pred_by[idx])
                bar_colors_list.append(colors[idx])
                bar_labels.append(shorten(m))
                label_text_colors.append('red' if m in overlap else 'black')
                bar_partners.append(
                    per_metric[m].get(agg['key_pred_by_partner'], '') if has_partners else '')
                y_pos += 1

            gap_y = y_pos - 0.5
            y_pos += 1

            for idx in show_pred:
                m = metrics[idx]
                y_positions.append(y_pos)
                bar_vals.append(pred[idx])
                bar_colors_list.append(colors[idx])
                bar_labels.append(shorten(m))
                label_text_colors.append('red' if m in overlap else 'black')
                bar_partners.append(
                    per_metric[m].get(agg['key_pred_partner'], '') if has_partners else '')
                y_pos += 1

            ax.barh(y_positions, bar_vals, color=bar_colors_list, height=0.72,
                    edgecolor='none', alpha=0.85)

            if has_partners:
                for yi, (yp, v, partner) in enumerate(zip(y_positions, bar_vals, bar_partners)):
                    if partner:
                        if v >= 0:
                            ax.text(0.005, yp, f' {shorten(partner, 25)}',
                                    ha='left', va='center', fontsize=4.5,
                                    alpha=0.6, style='italic')
                        else:
                            ax.text(v + 0.005, yp, f' {shorten(partner, 25)}',
                                    ha='left', va='center', fontsize=4.5,
                                    alpha=0.6, style='italic')

            ax.set_yticks(y_positions)
            ax.set_yticklabels(bar_labels, fontsize=6.5)
            for tick_label, color in zip(ax.get_yticklabels(), label_text_colors):
                tick_label.set_color(color)
                if color == 'red':
                    tick_label.set_fontweight('bold')

            ax.axvline(0, color='black', lw=0.8)
            ax.axhline(gap_y, color='gray', lw=1, ls=':', alpha=0.5)

            ax.set_xlabel(agg['bidir_xlabel'], fontsize=10)
            ax.set_title(f"{agg['label']} Predictability by Metric (Theil's U)\n"
                         f"\u2190 Most predicted by others          "
                         f"Best predictors of others \u2192\n"
                         f"Red = appears in both halves  [{scope_label}]",
                         fontsize=12)
            ax.grid(axis='x', lw=0.3, alpha=0.5)

            handles = [mpatches.Patch(color=CATEGORY_COLORS[c], label=c)
                       for c in CATEGORY_ORDER]
            handles.append(mpatches.Patch(facecolor='white', edgecolor='red',
                           linewidth=1.5, label=f'In both halves ({len(overlap)})'))
            ax.legend(handles=handles, fontsize=6.5, loc='lower right', ncol=2,
                      framealpha=0.9)

            plt.tight_layout()
            out = HERE / f'predictability_bidir_{agg["name"]}_{scope}{FILTER_SUFFIX}.png'
            fig.savefig(out, dpi=150, bbox_inches='tight')
            print(f"Wrote {out}  ({len(overlap)} in both halves)")
            plt.close(fig)
