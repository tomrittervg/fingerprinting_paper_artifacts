#!/usr/bin/env python3
"""Visualize min-set combo analysis results.

Reads min_set_combos.csv and min_set_combos_dedup.csv from output directories
and generates visualizations.

Usage:
    ./shortcuts/viz_minset.py <output_dir> [output_dir2 ...] [viz_name ...]

Arguments can be directories (containing min_set_combos.csv) or visualization
names. Directories and viz names are distinguished automatically.

Examples:
    # All default visualizations for one directory:
    ./shortcuts/viz_minset.py final-range/minset_025_0407ish_1775571780

    # Specific visualizations:
    ./shortcuts/viz_minset.py final-range/minset_* dedup_waterfall

    # List available visualizations:
    ./shortcuts/viz_minset.py --list
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Data loading — shared with viz_minset_2.py via viz_minset_common.py
from viz_minset_common import (
    load_combo_csv, load_dedup_csv, discover_os_variants,
    load_run_metadata, load_metadata_from_os_txt,
    parse_unique_baseline_from_txt, parse_total_users_from_txt,
)

# Global flag: when True, write a .csv alongside each .png
EMIT_CSV = False

# Optional filter: when set, only include top-N runs where N is in this set
METRICS_FILTER = None


def _matches_metrics_filter(dirname):
    """Return True if this directory's top-N value passes the --metrics filter."""
    if METRICS_FILTER is None:
        return True
    import re
    base = os.path.basename(os.path.abspath(dirname))
    m = re.search(r'top(\d+)', base)
    if not m:
        return True  # not a top-N directory, don't filter it out
    return int(m.group(1)) in METRICS_FILTER


def _write_csv(png_path, headers, rows):
    """Write a CSV file with the same base name as the PNG, if EMIT_CSV is set."""
    if not EMIT_CSV:
        return
    csv_path = png_path.rsplit('.png', 1)[0] + '.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"    wrote {csv_path}")


# =============================================================================
# Visualization registry
# =============================================================================

# {name: (function, description)}
_VISUALIZATIONS = {}


def viz(name, description):
    """Decorator to register a visualization function."""
    def decorator(fn):
        _VISUALIZATIONS[name] = (fn, description)
        return fn
    return decorator


# Default set — a curated subset of all registered visualizations
DEFAULT_VISUALIZATIONS = [
    'dedup_waterfall',
    'cumulative_pct',
    'metric_contribution',
]


# =============================================================================
# Visualizations
# =============================================================================

@viz('dedup_waterfall', 'Stacked bar: new users identified at each combo size')
def viz_dedup_waterfall(dedup_rows, combo_rows, meta, output_dir):
    """Bar chart showing new users identified at each combo size, stacked cumulatively."""
    if not dedup_rows:
        print(f"    [skip] no dedup data")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    sizes = [r['combo_size'] for r in dedup_rows]
    new_users = [r['new_users'] for r in dedup_rows]
    total_users = meta.get('total_users', 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(sizes, new_users, color='steelblue', edgecolor='white')

    # Cumulative line
    cumulative = [r['cumulative_total'] for r in dedup_rows]
    ax.plot(sizes, cumulative, 'o-', color='darkred', linewidth=2, label='Cumulative')

    if total_users:
        ax.axhline(y=total_users, color='gray', linestyle='--', alpha=0.5,
                    label=f'Total users ({total_users:,})')

    ax.set_xlabel('Combo Size (number of metrics)')
    ax.set_ylabel('Users')
    # ax.set_title(f'Users Uniquely Identified by Metric Combinations{title_suffix}')
    ax.set_xticks(sizes)
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_dedup_waterfall{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['ComboSize', 'NewUsers', 'CumulativeTotal'],
               list(zip(sizes, new_users, cumulative)))


@viz('cumulative_pct', 'Line chart: cumulative % of users identified vs combo size')
def viz_cumulative_pct(dedup_rows, combo_rows, meta, output_dir):
    """Shows diminishing returns — how much each additional combo size contributes."""
    if not dedup_rows:
        print(f"    [skip] no dedup data")
        return
    total_users = meta.get('total_users', 0)
    if not total_users:
        print(f"    [skip] no total_users in metadata")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    sizes = [0] + [r['combo_size'] for r in dedup_rows]
    cumul_pct = [0.0] + [100.0 * r['cumulative_total'] / total_users for r in dedup_rows]
    marginal_pct = [0.0] + [100.0 * r['new_users'] / total_users for r in dedup_rows]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(sizes, cumul_pct, 'o-', color='darkred', linewidth=2.5, markersize=8,
             label='Cumulative % identified', zorder=3)
    ax1.fill_between(sizes, cumul_pct, alpha=0.1, color='darkred')
    ax1.set_xlabel('Combo Size (number of metrics)')
    ax1.set_ylabel('% of Total Users')
    ax1.set_ylim(0, 105)
    ax1.set_xticks(sizes)

    # Marginal bars on secondary axis
    ax2 = ax1.twinx()
    bar_sizes = [r['combo_size'] for r in dedup_rows]
    ax2.bar(bar_sizes, marginal_pct[1:], alpha=0.3, color='steelblue',
            width=0.6, label='Marginal % (new at this size)')
    ax2.set_ylabel('Marginal % Identified (bars)')
    ax2.set_ylim(0, max(marginal_pct) * 1.5 if max(marginal_pct) > 0 else 100)

    # Annotate cumulative points
    for s, p in zip(sizes[1:], cumul_pct[1:]):
        ax1.annotate(f'{p:.1f}%', (s, p), textcoords='offset points',
                     xytext=(0, 12), ha='center', fontsize=9, fontweight='bold')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    # ax1.set_title(f'Diminishing Returns: Users Identified by Combo Size{title_suffix}')

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_cumulative_pct{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['ComboSize', 'CumulativePct', 'MarginalPct'],
               list(zip(sizes[1:], cumul_pct[1:], marginal_pct[1:])))


@viz('coverage_comparison', 'Horizontal bars: % users identified by different analysis scopes')
def viz_coverage_comparison(dedup_rows, combo_rows, meta, output_dir):
    """Horizontal bar chart comparing coverage of different metric set / combo size scopes.

    Each bar = a scope like "top-10 metrics, sizes 1-5" or "top-20, sizes 1-2".
    Coverage = sum of combo_only_unique_new for combos in that scope / total_users.
    """
    if not combo_rows or not dedup_rows:
        print(f"    [skip] no combo/dedup data")
        return
    total_users = meta.get('total_users', 0)
    if not total_users:
        print(f"    [skip] no total_users in metadata")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    # Derive metric ranking from size-1 combos (solo metrics, ordered by unique count)
    size1 = sorted([r for r in combo_rows if r['combo_size'] == 1],
                   key=lambda r: -r['combo_unique'])
    metric_rank = {r['metrics'][0]: i for i, r in enumerate(size1)}

    def _metrics_in_top_n(combo_metrics, n):
        return all(metric_rank.get(m, 999) < n for m in combo_metrics)

    # Build scopes: (label, filter_fn)
    # Coverage for each = sum of combo_only_unique_new for matching combos
    max_size = max(r['combo_size'] for r in combo_rows)
    scopes = []

    # Cumulative size scopes (from dedup — exact numbers)
    for dr in dedup_rows:
        sz = dr['combo_size']
        scopes.append((
            f'Sizes 1–{sz} (as run)',
            dr['cumulative_total'],
            True,  # exact from dedup
        ))

    # Cross-cutting: vary top-N and max size
    for top_n in [10, 15, 20, 30]:
        for max_sz in range(1, max_size + 1):
            # Skip scopes that match "as run" exactly (avoid duplicates)
            matching = [r for r in combo_rows
                        if r['combo_size'] <= max_sz and _metrics_in_top_n(r['metrics'], top_n)]
            if not matching:
                continue
            coverage = sum(r['combo_only_unique_new'] for r in matching)
            label = f'Top {top_n}, sizes 1–{max_sz}'
            scopes.append((label, coverage, False))

    # Deduplicate: remove cross-cutting entries that have same coverage as an "as run" entry
    exact_coverages = {c for _, c, exact in scopes if exact}
    scopes = [(l, c, e) for l, c, e in scopes if e or c not in exact_coverages]

    # Sort by coverage ascending (bottom-to-top for horizontal bars)
    scopes.sort(key=lambda x: x[1])

    # Only keep interesting scopes (remove near-duplicates within 0.1% of each other)
    filtered = []
    for label, coverage, exact in scopes:
        pct = 100.0 * coverage / total_users
        if not filtered or abs(pct - filtered[-1][1]) > 0.1 or exact:
            filtered.append((label, pct, exact))
    if len(filtered) > 20:
        # Keep all exact + top entries by spacing
        exact_entries = [(l, p, e) for l, p, e in filtered if e]
        approx_entries = [(l, p, e) for l, p, e in filtered if not e]
        # Keep every Nth approx to get ~15 total
        step = max(1, len(approx_entries) // (20 - len(exact_entries)))
        approx_sampled = approx_entries[::step]
        filtered = sorted(exact_entries + approx_sampled, key=lambda x: x[1])

    labels = [l for l, _, _ in filtered]
    pcts = [p for _, p, _ in filtered]
    colors = ['#2c7fb8' if e else '#7fcdbb' for _, _, e in filtered]

    fig, ax = plt.subplots(figsize=(12, max(5, len(filtered) * 0.4)))

    bars = ax.barh(range(len(filtered)), pcts, color=colors, edgecolor='white', height=0.7)

    # Annotate each bar with its percentage
    for i, (bar, pct) in enumerate(zip(bars, pcts)):
        ax.text(pct + 0.5, i, f'{pct:.1f}%', va='center', fontsize=9)

    ax.set_yticks(range(len(filtered)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 105)
    ax.set_xlabel('% of Total Users Identified')
    # ax.set_title(f'Coverage Comparison: Different Metric Scopes{title_suffix}')
    ax.axvline(x=100, color='gray', linestyle='--', alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color='#2c7fb8', label='Exact (from dedup)'),
                        Patch(color='#7fcdbb', label='Approximate (filtered combos)')],
              loc='lower right', fontsize=9)

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_coverage_comparison{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")


def _short_metric_name(name):
    """Shorten metric names for display: strip common prefixes, abbreviate."""
    for prefix in ('combined_', 'screen_web_', 'screen_primary_', 'screen_',
                   'canvas_canvasdata', 'fonts_fpjs_', 'intl_', 'locale_'):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


@viz('metric_frequency', 'Heatmap: how often each metric appears in top combos per size')
def viz_metric_frequency(dedup_rows, combo_rows, meta, output_dir):
    """For each combo size, count how many of the top-N combos each metric appears in."""
    if not combo_rows:
        print(f"    [skip] no combo data")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    TOP_N = 20  # top N combos per size by new-user contribution
    by_size = defaultdict(list)
    for r in combo_rows:
        by_size[r['combo_size']].append(r)

    sizes = sorted(by_size.keys())
    # Count metric appearances in top-N per size
    metric_counts = defaultdict(lambda: defaultdict(int))  # {metric: {size: count}}
    all_metrics = set()
    for sz in sizes:
        top = sorted(by_size[sz], key=lambda r: -r['combo_only_unique_new'])[:TOP_N]
        for r in top:
            for m in r['metrics']:
                metric_counts[m][sz] += 1
                all_metrics.add(m)

    # Order metrics by total appearances descending
    metrics_ordered = sorted(all_metrics,
                             key=lambda m: -sum(metric_counts[m].values()))

    # Build matrix
    matrix = []
    for m in metrics_ordered:
        matrix.append([metric_counts[m].get(sz, 0) for sz in sizes])

    fig, ax = plt.subplots(figsize=(max(8, len(sizes) * 2), max(8, len(metrics_ordered) * 0.4)))
    im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd', interpolation='nearest')

    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([f'Size {s}' for s in sizes])
    ax.set_yticks(range(len(metrics_ordered)))
    ax.set_yticklabels([_short_metric_name(m) for m in metrics_ordered], fontsize=9)

    # Annotate cells with counts
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val > 0:
                ax.text(j, i, str(val), ha='center', va='center', fontsize=8,
                        color='white' if val > TOP_N * 0.6 else 'black')

    # ax.set_title(f'Metric Frequency in Top-{TOP_N} Combos by Size{title_suffix}')
    fig.colorbar(im, ax=ax, label='Appearances in top combos', shrink=0.8)
    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_metric_frequency{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")


@viz('top_combos', 'Horizontal bar: top combos per size ranked by new users identified')
def viz_top_combos(dedup_rows, combo_rows, meta, output_dir):
    """One subplot per combo size showing the top-10 combos by new-user contribution."""
    if not combo_rows:
        print(f"    [skip] no combo data")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    TOP_N = 10
    by_size = defaultdict(list)
    for r in combo_rows:
        by_size[r['combo_size']].append(r)

    sizes = sorted(by_size.keys())
    n_sizes = len(sizes)
    fig, axes = plt.subplots(1, n_sizes, figsize=(6 * n_sizes, max(6, TOP_N * 0.5)),
                             sharey=False)
    if n_sizes == 1:
        axes = [axes]

    colors = plt.cm.tab10.colors

    for idx, (sz, ax) in enumerate(zip(sizes, axes)):
        top = sorted(by_size[sz], key=lambda r: -r['combo_only_unique_new'])[:TOP_N]
        top.reverse()  # bottom-to-top for horizontal bars
        labels = []
        for r in top:
            short = [_short_metric_name(m) for m in r['metrics']]
            labels.append(' + '.join(short))
        values = [r['combo_only_unique_new'] for r in top]

        bars = ax.barh(range(len(top)), values, color=colors[idx % len(colors)], alpha=0.8)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel('New Users Identified')
        # ax.set_title(f'Size {sz}')
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x / 1e6:.1f}M'
                                                        if x >= 1e6 else f'{x / 1e3:.0f}K'))

    # fig.suptitle(f'Top Metric Combinations by New Users Identified{title_suffix}', fontsize=13, y=1.01)
    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_top_combos{suffix}.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"    wrote {out_path}")


@viz('metric_cooccurrence', 'Heatmap: how often metric pairs co-occur in top combos')
def viz_metric_cooccurrence(dedup_rows, combo_rows, meta, output_dir):
    """Symmetric matrix showing co-occurrence of metric pairs across all top combos."""
    if not combo_rows:
        print(f"    [skip] no combo data")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    TOP_N = 30  # top combos per size to analyze
    by_size = defaultdict(list)
    for r in combo_rows:
        by_size[r['combo_size']].append(r)

    # Only look at combos of size >= 2
    cooccur = defaultdict(int)  # {(m1, m2): count}
    metric_total = defaultdict(int)
    for sz, rows in by_size.items():
        if sz < 2:
            continue
        top = sorted(rows, key=lambda r: -r['combo_only_unique_new'])[:TOP_N]
        for r in top:
            metrics = sorted(r['metrics'])
            for m in metrics:
                metric_total[m] += 1
            for i in range(len(metrics)):
                for j in range(i + 1, len(metrics)):
                    pair = (metrics[i], metrics[j])
                    cooccur[pair] += 1

    if not cooccur:
        print(f"    [skip] no pairs found")
        return

    # Top metrics by total appearances
    top_metrics = sorted(metric_total, key=lambda m: -metric_total[m])[:15]
    n = len(top_metrics)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            pair = tuple(sorted([top_metrics[i], top_metrics[j]]))
            val = cooccur.get(pair, 0)
            matrix[i][j] = val
            matrix[j][i] = val
        matrix[i][i] = metric_total[top_metrics[i]]

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(matrix, cmap='Blues', interpolation='nearest')

    short_labels = [_short_metric_name(m) for m in top_metrics]
    ax.set_xticks(range(n))
    ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(n))
    ax.set_yticklabels(short_labels, fontsize=8)

    # Annotate
    for i in range(n):
        for j in range(n):
            if matrix[i][j] > 0:
                ax.text(j, i, str(matrix[i][j]), ha='center', va='center',
                        fontsize=7, color='white' if matrix[i][j] > max(cooccur.values()) * 0.6 else 'black')

    # ax.set_title(f'Metric Co-occurrence in Top-{TOP_N} Combos (size >= 2){title_suffix}')
    fig.colorbar(im, ax=ax, label='Co-occurrences', shrink=0.8)
    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_metric_cooccurrence{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")


@viz('metric_contribution', 'Bar chart: total new users attributed to each metric across all combos')
def viz_metric_contribution(dedup_rows, combo_rows, meta, output_dir):
    """For each metric, sum combo_only_unique_new / combo_size for all combos it appears in.

    Dividing by combo_size apportions credit equally among the metrics in each combo.
    This gives a rough measure of each metric's marginal contribution to identification.
    """
    if not combo_rows:
        print(f"    [skip] no combo data")
        return

    os_name = meta.get('os_name')
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    contribution = defaultdict(float)
    for r in combo_rows:
        share = r['combo_only_unique_new'] / r['combo_size']
        for m in r['metrics']:
            contribution[m] += share

    # Sort descending
    ranked = sorted(contribution.items(), key=lambda x: -x[1])
    csv_rows = [(m, v) for m, v in ranked[:25]]
    top = ranked[:25]
    top.reverse()  # bottom-to-top

    labels = [_short_metric_name(m) for m, _ in top]
    values = [v for _, v in top]

    fig, ax = plt.subplots(figsize=(10, max(6, len(top) * 0.35)))
    ax.barh(range(len(top)), values, color='teal', alpha=0.85)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('Apportioned Users Identified (new_users / combo_size)')
    # ax.set_title(f'Per-Metric Contribution to Unique Identification{title_suffix}')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, p: f'{x / 1e6:.1f}M' if x >= 1e6 else f'{x / 1e3:.0f}K'))

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_metric_contribution{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['Metric', 'Contribution'],
               csv_rows)


# =============================================================================
# Comparison visualizations (multi-directory)
# =============================================================================

def _label_sort_key(label):
    """Sort key for run labels — extract numeric value from 'topN' pattern."""
    import re
    m = re.search(r'top(\d+)', label)
    return int(m.group(1)) if m else float('inf')


def _collect_run_labels(overall_runs, os_runs=None):
    """Collect unique run labels from overall_runs and optionally os_runs, sorted by topN."""
    seen = set()
    labels = []
    for label, _, _, _ in overall_runs:
        if label not in seen:
            labels.append(label)
            seen.add(label)
    if os_runs:
        for os_name in sorted(os_runs.keys()):
            for label, _, _, _ in os_runs[os_name]:
                if label not in seen:
                    labels.append(label)
                    seen.add(label)
    labels.sort(key=_label_sort_key)
    return labels


def _derive_short_label(dirname):
    """Extract a short label from a directory name like 'minset_top20_0408ish_...'."""
    import re
    base = os.path.basename(os.path.abspath(dirname))
    # Try to extract a "topN" pattern
    m = re.search(r'(top\d+)', base)
    if m:
        return m.group(1)
    # Fallback: first two underscore-delimited segments
    parts = base.split('_')
    return '_'.join(parts[:2]) if len(parts) >= 2 else base


def compare_dedup_waterfall(runs, output_dir, os_name=None):
    """Grouped bar chart: new users at each combo size + cumulative lines, one per run."""
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    # Collect all combo sizes across runs
    all_sizes = sorted({r['combo_size']
                        for _, dedup, _, _ in runs for r in dedup})
    if not all_sizes:
        return

    n_runs = len(runs)
    bar_width = 0.8 / n_runs
    colors = plt.cm.tab10.colors
    markers = ['o', 's', 'D', '^', 'v', 'P', 'X']

    # Get total_users for percentage conversion
    total_users = next((meta.get('total_users', 0)
                        for _, _, _, meta in runs if meta.get('total_users')), 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    csv_rows = []
    for i, (label, dedup, combo, meta) in enumerate(runs):
        size_to_new = {r['combo_size']: r['new_users'] for r in dedup}
        size_to_cumul = {r['combo_size']: r['cumulative_total'] for r in dedup}
        if total_users:
            values = [100.0 * size_to_new.get(s, 0) / total_users
                      for s in all_sizes]
        else:
            values = [size_to_new.get(s, 0) for s in all_sizes]
        positions = [s + (i - n_runs / 2 + 0.5) * bar_width for s in all_sizes]
        ax.bar(positions, values, width=bar_width, color=colors[i % len(colors)],
               edgecolor='white', alpha=0.7)

        # Cumulative line at bar center positions
        cumul_sizes = sorted(size_to_cumul.keys())
        cumul_positions = [s + (i - n_runs / 2 + 0.5) * bar_width for s in cumul_sizes]
        if total_users:
            cumul_values = [100.0 * size_to_cumul[s] / total_users
                            for s in cumul_sizes]
        else:
            cumul_values = [size_to_cumul[s] for s in cumul_sizes]
        ax.plot(cumul_positions, cumul_values,
                marker=markers[i % len(markers)], color=colors[i % len(colors)],
                linewidth=2, markersize=7, zorder=3)

        cumul_lookup = dict(zip(cumul_sizes, cumul_values))
        for s, v in zip(all_sizes, values):
            csv_rows.append((label, s, v, cumul_lookup.get(s, 0)))

    # Legend: one entry per run showing just the color + "Top N Metrics"
    from matplotlib.patches import Patch
    legend_handles = []
    for i, (label, _, _, _) in enumerate(runs):
        # Turn "top5" → "Top 5 Metrics", "top20" → "Top 20 Metrics"
        import re
        m = re.match(r'top(\d+)', label)
        nice_label = f'Top {m.group(1)} Metrics' if m else label
        legend_handles.append(Patch(color=colors[i % len(colors)], label=nice_label))
    ax.legend(handles=legend_handles, fontsize=9)

    ax.set_xlabel('Combo Size (number of metrics)')
    ax.set_ylabel('% of OS Users')
    # ax.set_title(f'New Users by Combo Size — Comparison{title_suffix}')
    ax.set_xticks(all_sizes)
    ax.set_xticklabels([str(s) for s in all_sizes])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_compare_dedup_waterfall{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['Run', 'ComboSize', 'NewUsersPct', 'CumulativePct'],
               csv_rows)


def compare_cumulative_pct(runs, output_dir, os_name=None):
    """Overlaid line chart: cumulative % identified vs combo size, one line per run."""
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    colors = plt.cm.tab10.colors
    markers = ['o', 's', 'D', '^', 'v', 'P', 'X']

    fig, ax = plt.subplots(figsize=(10, 6))
    has_data = False
    csv_rows = []

    for i, (label, dedup, combo, meta) in enumerate(runs):
        total_users = meta.get('total_users', 0)
        if not total_users or not dedup:
            continue
        has_data = True
        sizes = [0] + [r['combo_size'] for r in dedup]
        cumul_pct = [0.0] + [100.0 * r['cumulative_total'] / total_users for r in dedup]
        ax.plot(sizes, cumul_pct,
                marker=markers[i % len(markers)], color=colors[i % len(colors)],
                linewidth=2.5, markersize=8, label=label, zorder=3)
        # Annotate final point
        ax.annotate(f'{cumul_pct[-1]:.1f}%', (sizes[-1], cumul_pct[-1]),
                    textcoords='offset points', xytext=(8, 0),
                    fontsize=9, fontweight='bold', color=colors[i % len(colors)])
        for s, p in zip(sizes, cumul_pct):
            csv_rows.append((label, s, p))

    if not has_data:
        plt.close(fig)
        print(f"    [skip] no data for compare_cumulative_pct")
        return

    ax.set_xlabel('Combo Size (number of metrics)')
    ax.set_ylabel('% of Total Users Identified')
    ax.set_ylim(0, 105)
    # ax.set_title(f'Cumulative % Identified — Comparison{title_suffix}')
    ax.legend()

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_compare_cumulative_pct{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['Run', 'ComboSize', 'CumulativePct'],
               csv_rows)


def compare_metric_contribution(runs, output_dir, os_name=None):
    """Grouped horizontal bar chart: per-metric contribution across runs."""
    suffix = f'_os_{os_name}' if os_name else ''
    title_suffix = f' — {os_name}' if os_name else ''

    colors = plt.cm.tab10.colors
    n_runs = len(runs)

    # Compute contributions per run
    run_contributions = []
    all_metrics = set()
    for label, dedup, combo, meta in runs:
        contrib = defaultdict(float)
        for r in combo:
            share = r['combo_only_unique_new'] / r['combo_size']
            for m in r['metrics']:
                contrib[m] += share
        run_contributions.append(contrib)
        all_metrics.update(contrib.keys())

    if not all_metrics:
        return

    # Rank metrics by max contribution across any run, take top 20
    metric_max = {m: max(rc.get(m, 0) for rc in run_contributions) for m in all_metrics}
    top_metrics = sorted(metric_max, key=lambda m: -metric_max[m])[:20]
    top_metrics.reverse()  # bottom-to-top for horizontal bars

    bar_height = 0.8 / n_runs
    fig, ax = plt.subplots(figsize=(12, max(6, len(top_metrics) * 0.45)))

    for i, (label, dedup, combo, meta) in enumerate(runs):
        values = [run_contributions[i].get(m, 0) for m in top_metrics]
        positions = [j + (i - n_runs / 2 + 0.5) * bar_height for j in range(len(top_metrics))]
        ax.barh(positions, values, height=bar_height, color=colors[i % len(colors)],
                label=label, alpha=0.85)

    ax.set_yticks(range(len(top_metrics)))
    ax.set_yticklabels([_short_metric_name(m) for m in top_metrics], fontsize=9)
    ax.set_xlabel('Apportioned Users Identified (new_users / combo_size)')
    # ax.set_title(f'Per-Metric Contribution — Comparison{title_suffix}')
    ax.legend(loc='lower right')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, p: f'{x / 1e6:.1f}M' if x >= 1e6 else f'{x / 1e3:.0f}K'))

    fig.tight_layout()
    out_path = os.path.join(output_dir, f'viz_compare_metric_contribution{suffix}.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    csv_rows = []
    for i, (label, dedup, combo, meta) in enumerate(runs):
        for m in reversed(top_metrics):  # descending order (top_metrics is reversed)
            csv_rows.append((label, m, run_contributions[i].get(m, 0)))
    _write_csv(out_path,
               ['Run', 'Metric', 'Contribution'],
               csv_rows)


def compare_os_coverage(os_runs, overall_runs, output_dir, max_combo_size=3):
    """Grouped bar chart: coverage at ≤max_combo_size.

    Groups = runs (Top 5, Top 10, Top 20).
    Bars within each group = Overall + each OS.
    Shows how expanding the overall metric pool captures more users per platform.
    """
    import re

    # Scope display names and colors
    scope_display = {'Overall': 'Overall', 'WINNT': 'Windows', 'Darwin': 'macOS',
                     'Linux': 'Linux', 'Android': 'Android'}
    scope_order = ['Overall', 'Android', 'Darwin', 'Linux', 'WINNT']
    scope_colors = {'Overall': '#2c7fb8', 'Android': '#7fcdbb', 'Darwin': '#f0ad4e',
                    'Linux': '#d9534f', 'WINNT': '#5cb85c'}

    # Collect run labels in order
    run_labels = _collect_run_labels(overall_runs, os_runs)

    # Determine actual max combo size per run from dedup data
    run_max_size = {}
    for label, dedup, combo, meta in overall_runs:
        if dedup:
            run_max_size[label] = max(r['combo_size'] for r in dedup)

    # Build data: {label: {scope: pct}}
    data = {}
    for label, dedup, combo, meta in overall_runs:
        total = meta.get('total_users', 0)
        if not total or not dedup:
            continue
        cumul = max((r['cumulative_total'] for r in dedup), default=0)
        data.setdefault(label, {})['Overall'] = 100.0 * cumul / total

    for os_name in scope_order:
        if os_name == 'Overall':
            continue
        for label, dedup, combo, meta in os_runs.get(os_name, []):
            total = meta.get('total_users', 0)
            if not total or not dedup:
                continue
            cumul = max((r['cumulative_total'] for r in dedup), default=0)
            data.setdefault(label, {})[os_name] = 100.0 * cumul / total

    if not data:
        return

    # Filter scope_order to only scopes with data
    scopes = [s for s in scope_order if any(s in data.get(l, {}) for l in run_labels)]
    n_scopes = len(scopes)
    n_groups = len(run_labels)
    bar_width = 0.8 / n_scopes

    fig, ax = plt.subplots(figsize=(max(10, n_groups * 3.5), 7))

    for i, scope in enumerate(scopes):
        values = [data.get(label, {}).get(scope, 0) for label in run_labels]
        positions = [g + (i - n_scopes / 2 + 0.5) * bar_width for g in range(n_groups)]

        ax.bar(positions, values, width=bar_width,
               color=scope_colors.get(scope, '#999999'),
               label=scope_display.get(scope, scope),
               edgecolor='white', alpha=0.85)

        for pos, val in zip(positions, values):
            if val > 0:
                ax.text(pos, val + 0.8, f'{val:.1f}%', ha='center', va='bottom',
                        fontsize=8, fontweight='bold')

    # X-axis: group labels
    nice_group_labels = []
    for label in run_labels:
        m = re.match(r'top(\d+)', label)
        x = run_max_size.get(label, '?')
        if m:
            nice_group_labels.append(f'N={m.group(1)}, X={x}')
        else:
            nice_group_labels.append(label)

    ax.set_xticks(range(n_groups))
    ax.set_xticklabels(nice_group_labels, fontsize=11)
    ax.set_xlabel('Top N Overall Metrics, X-Metric Combinations')
    ax.set_ylabel('% of Unique Users Described')
    ax.set_ylim(0, 105)
    # ax.set_title('Percent of Unique Users Described by N-Metric Combinations')
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

    fig.tight_layout()
    out_path = os.path.join(output_dir, 'viz_compare_os_coverage.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    csv_rows = []
    for label in run_labels:
        for scope in scopes:
            csv_rows.append((label, scope, data.get(label, {}).get(scope, 0)))
    _write_csv(out_path,
               ['Run', 'OS', 'CoveragePct'],
               csv_rows)


def compare_os_grid_waterfall(os_runs, overall_runs, output_dir, out_name=None):
    """Small-multiples 2x2 grid: one subplot per OS, each showing the multi-run
    waterfall (grouped bars for new users + cumulative lines) for that OS.

    Lets you scan across all OSes at once while comparing runs within each.
    """
    import re

    os_display = {'WINNT': 'Windows', 'Darwin': 'macOS',
                  'Linux': 'Linux', 'Android': 'Android'}
    os_order = [n for n in ['Android', 'Darwin', 'Linux', 'WINNT']
                if n in os_runs]
    if len(os_order) < 2:
        return

    # Collect run labels in order
    run_labels = _collect_run_labels(overall_runs, os_runs)

    colors = plt.cm.tab10.colors
    markers = ['o', 's', 'D', '^', 'v', 'P', 'X']

    ncols = 2
    nrows = (len(os_order) + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 5.5 * nrows),
                              sharey=False)
    if nrows == 1:
        axes = [axes]
    axes_flat = [ax for row in axes for ax in (row if hasattr(row, '__len__') else [row])]
    csv_rows = []

    for idx, os_name in enumerate(os_order):
        ax = axes_flat[idx]
        runs = os_runs[os_name]

        # Build lookup: label → dedup data
        run_data = {}
        for label, dedup, combo, meta in runs:
            run_data[label] = dedup

        all_sizes = sorted({r['combo_size']
                            for label in run_labels if label in run_data
                            for r in run_data[label]})
        if not all_sizes:
            continue

        n_runs = len(run_labels)
        bar_width = 0.8 / n_runs

        total_users = next(
            (meta.get('total_users', 0)
             for _, _, _, meta in runs if meta.get('total_users')), 0)

        for i, label in enumerate(run_labels):
            dedup = run_data.get(label, [])
            size_to_new = {r['combo_size']: r['new_users'] for r in dedup}
            size_to_cumul = {r['combo_size']: r['cumulative_total'] for r in dedup}

            if total_users:
                values = [100.0 * size_to_new.get(s, 0) / total_users
                          for s in all_sizes]
            else:
                values = [size_to_new.get(s, 0) for s in all_sizes]
            positions = [s + (i - n_runs / 2 + 0.5) * bar_width for s in all_sizes]
            ax.bar(positions, values, width=bar_width,
                   color=colors[i % len(colors)], alpha=0.7, edgecolor='white')

            cumul_sizes = sorted(size_to_cumul.keys())
            cumul_positions = [s + (i - n_runs / 2 + 0.5) * bar_width for s in cumul_sizes]
            if total_users:
                cumul_values = [100.0 * size_to_cumul[s] / total_users
                                for s in cumul_sizes]
            else:
                cumul_values = [size_to_cumul[s] for s in cumul_sizes]
            ax.plot(cumul_positions, cumul_values,
                    marker=markers[i % len(markers)], color=colors[i % len(colors)],
                    linewidth=2, markersize=6, zorder=3)

            cumul_lookup = dict(zip(cumul_sizes, cumul_values))
            for s, v in zip(all_sizes, values):
                csv_rows.append((os_name, label, s, v, cumul_lookup.get(s, 0)))

        # ax.set_title(os_display.get(os_name, os_name), fontsize=12, fontweight='bold')
        ax.set_xticks(all_sizes)
        ax.set_xticklabels([str(s) for s in all_sizes])
        ax.set_xlabel('Combo Size')
        ax.set_ylabel('% of OS Users')
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

    # Hide unused subplots
    for idx in range(len(os_order), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    # Shared legend
    from matplotlib.patches import Patch
    legend_handles = []
    for i, label in enumerate(run_labels):
        m = re.match(r'top(\d+)', label)
        nice = f'Top {m.group(1)} Metrics' if m else label
        legend_handles.append(Patch(color=colors[i % len(colors)], label=nice))
    fig.legend(handles=legend_handles, loc='upper center',
               ncol=len(run_labels), fontsize=10,
               bbox_to_anchor=(0.5, 1.02))

    # fig.suptitle('New Users by Combo Size — All OSes', fontsize=14, y=1.05)
    fig.tight_layout()
    fname = out_name if out_name else 'viz_compare_os_grid_waterfall.png'
    out_path = os.path.join(output_dir, fname)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['OS', 'Run', 'ComboSize', 'NewUsersPct', 'CumulativePct'],
               csv_rows)


def compare_os_cumulative_lines(os_runs, overall_runs, output_dir):
    """One chart per run: overlaid cumulative % lines for each OS + overall.

    Shows how different platforms diverge as combo size grows within each
    metric pool. Color = OS, one figure per run (top5, top10, top20).
    """
    import re

    os_display = {'WINNT': 'Windows', 'Darwin': 'macOS',
                  'Linux': 'Linux', 'Android': 'Android', 'Overall': 'Overall'}
    os_colors = {'Overall': '#2c7fb8', 'Android': '#7fcdbb', 'Darwin': '#f0ad4e',
                 'Linux': '#d9534f', 'WINNT': '#5cb85c'}
    os_markers = {'Overall': 'o', 'Android': 's', 'Darwin': 'D',
                  'Linux': '^', 'WINNT': 'v'}
    scope_order = ['Overall', 'Android', 'Darwin', 'Linux', 'WINNT']

    # Build per-run data: {label: {scope: (sizes, cumul_pcts)}}
    run_labels = _collect_run_labels(overall_runs, os_runs)

    run_data = {}
    for label, dedup, combo, meta in overall_runs:
        total = meta.get('total_users', 0)
        if not total or not dedup:
            continue
        run_data.setdefault(label, {})
        sizes = [0] + [r['combo_size'] for r in dedup]
        pcts = [0.0] + [100.0 * r['cumulative_total'] / total for r in dedup]
        run_data[label]['Overall'] = (sizes, pcts)

    for os_name in scope_order:
        if os_name == 'Overall':
            continue
        for label, dedup, combo, meta in os_runs.get(os_name, []):
            total = meta.get('total_users', 0)
            if not total or not dedup:
                continue
            run_data.setdefault(label, {})
            sizes = [0] + [r['combo_size'] for r in dedup]
            pcts = [0.0] + [100.0 * r['cumulative_total'] / total for r in dedup]
            run_data[label][os_name] = (sizes, pcts)

    for label in run_labels:
        if label not in run_data:
            continue
        m = re.match(r'top(\d+)', label)
        nice_label = f'Top {m.group(1)} Metrics' if m else label

        fig, ax = plt.subplots(figsize=(10, 6))
        csv_rows = []

        for scope in scope_order:
            if scope not in run_data[label]:
                continue
            sizes, pcts = run_data[label][scope]
            lw = 3 if scope == 'Overall' else 2
            ls = '-' if scope == 'Overall' else '--'
            ax.plot(sizes, pcts,
                    marker=os_markers.get(scope, 'o'),
                    color=os_colors.get(scope, '#999'),
                    linewidth=lw, linestyle=ls, markersize=8,
                    label=os_display.get(scope, scope), zorder=3)
            # Annotate final point
            ax.annotate(f'{pcts[-1]:.1f}%', (sizes[-1], pcts[-1]),
                        textcoords='offset points', xytext=(8, 0),
                        fontsize=9, fontweight='bold',
                        color=os_colors.get(scope, '#999'))
            for s, p in zip(sizes, pcts):
                csv_rows.append((label, scope, s, p))

        ax.set_xlabel('Combo Size (number of metrics)')
        ax.set_ylabel('% of Users Uniquely Identified')
        ax.set_ylim(0, 105)
        # ax.set_title(f'Cumulative % Identified by OS — {nice_label}')
        ax.legend(fontsize=10)

        fig.tight_layout()
        out_path = os.path.join(
            output_dir, f'viz_compare_os_cumulative_{label}.png')
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"    wrote {out_path}")
        _write_csv(out_path,
                   ['Run', 'OS', 'ComboSize', 'CumulativePct'],
                   csv_rows)


def compare_os_average_waterfall(os_runs, overall_runs, output_dir,
                                 weighted=False, out_name=None):
    """Single-panel waterfall showing the average percentage across all OSes.

    For each run and combo size, averages the per-OS percentages (new users %
    and cumulative %) then plots grouped bars + cumulative lines.
    If weighted=True, weights each OS by its share of total users.
    """
    import re

    colors = plt.cm.tab10.colors
    markers = ['o', 's', 'D', '^', 'v', 'P', 'X']

    run_labels = _collect_run_labels(overall_runs, os_runs)

    # Collect per-OS totals for weighting
    os_totals = {}
    for os_name, runs in os_runs.items():
        for _, _, _, meta in runs:
            t = meta.get('total_users', 0)
            if t:
                os_totals[os_name] = t
                break
    total_all = sum(os_totals.values()) if weighted else 0

    # Compute average % across OSes for each run and combo size
    # {label: {combo_size: [(pct_new, pct_cumul, weight), ...]}}
    size_data = {}
    for os_name, runs in os_runs.items():
        w = os_totals.get(os_name, 0) / total_all if weighted and total_all else 1.0
        for label, dedup, combo, meta in runs:
            total = meta.get('total_users', 0)
            if not total or not dedup:
                continue
            size_data.setdefault(label, {})
            for r in dedup:
                sz = r['combo_size']
                size_data[label].setdefault(sz, [])
                size_data[label][sz].append((
                    100.0 * r['new_users'] / total,
                    100.0 * r['cumulative_total'] / total,
                    w,
                ))

    if not size_data:
        return

    all_sizes = sorted({sz for label_data in size_data.values()
                        for sz in label_data})
    n_runs = len(run_labels)
    bar_width = 0.8 / n_runs

    fig, ax = plt.subplots(figsize=(10, 6))
    csv_rows = []

    for i, label in enumerate(run_labels):
        ld = size_data.get(label, {})

        def _avg(entries, idx):
            if weighted:
                w_sum = sum(e[2] for e in entries)
                return sum(e[idx] * e[2] for e in entries) / w_sum
            return sum(e[idx] for e in entries) / len(entries)

        avg_new = [_avg(ld[s], 0) if s in ld else 0 for s in all_sizes]

        positions = [s + (i - n_runs / 2 + 0.5) * bar_width for s in all_sizes]
        ax.bar(positions, avg_new, width=bar_width,
               color=colors[i % len(colors)], alpha=0.7, edgecolor='white')

        cumul_sizes = [s for s in all_sizes if s in ld]
        cumul_positions = [s + (i - n_runs / 2 + 0.5) * bar_width
                           for s in cumul_sizes]
        cumul_values = [_avg(ld[s], 1) for s in cumul_sizes]
        ax.plot(cumul_positions, cumul_values,
                marker=markers[i % len(markers)], color=colors[i % len(colors)],
                linewidth=2, markersize=6, zorder=3)

        cumul_lookup = dict(zip(cumul_sizes, cumul_values))
        for s, v in zip(all_sizes, avg_new):
            csv_rows.append((label, s, v, cumul_lookup.get(s, 0)))

    mode = 'Weighted OS Average' if weighted else 'OS Average'
    # ax.set_title(mode, fontsize=12, fontweight='bold')
    ax.set_xticks(all_sizes)
    ax.set_xticklabels([str(s) for s in all_sizes])
    ax.set_xlabel('Combo Size')
    ax.set_ylabel(f'% of OS Users ({"weighted " if weighted else ""}avg)')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

    # Legend
    from matplotlib.patches import Patch
    legend_handles = []
    for i, label in enumerate(run_labels):
        m = re.match(r'top(\d+)', label)
        nice = f'Top {m.group(1)} Metrics' if m else label
        legend_handles.append(Patch(color=colors[i % len(colors)], label=nice))
    ax.legend(handles=legend_handles, fontsize=10)

    fig.tight_layout()
    if out_name:
        fname = out_name
    else:
        suffix = '_weighted' if weighted else ''
        fname = f'viz_compare_os_average{suffix}_waterfall.png'
    out_path = os.path.join(output_dir, fname)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"    wrote {out_path}")
    _write_csv(out_path,
               ['Run', 'ComboSize', 'NewUsersPct', 'CumulativePct'],
               csv_rows)


def _extract_total_users_from_txt(output_dir):
    """Extract total users from min_set_combos.txt if present."""
    import re
    txt_path = os.path.join(output_dir, 'min_set_combos.txt')
    if not os.path.exists(txt_path):
        return None
    with open(txt_path) as f:
        for line in f:
            m = re.match(r'Total users:\s+([\d,]+)', line)
            if m:
                return int(m.group(1).replace(',', ''))
    return None


def _merge_same_label_runs(runs):
    """Merge entries with the same label if their combo sizes don't overlap.

    Takes a list of (label, dedup_rows, combo_rows, meta) tuples.
    Returns a new list where same-label entries with non-overlapping combo
    sizes are combined into a single entry.
    """
    from collections import OrderedDict
    groups = OrderedDict()
    for label, dedup, combo, meta in runs:
        groups.setdefault(label, []).append((dedup, combo, meta))

    merged = []
    for label, entries in groups.items():
        if len(entries) == 1:
            dedup, combo, meta = entries[0]
            merged.append((label, dedup, combo, meta))
            continue

        # Check for overlap in combo sizes across dedup rows
        all_sizes = []
        for dedup, combo, meta in entries:
            sizes = {r['combo_size'] for r in dedup}
            all_sizes.append(sizes)

        total_sizes = sum(len(s) for s in all_sizes)
        union_sizes = len(set().union(*all_sizes))
        if total_sizes != union_sizes:
            # Overlap — report which sizes conflict and abort
            overlap = set()
            for i, s in enumerate(all_sizes):
                for j in range(i + 1, len(all_sizes)):
                    overlap |= s & all_sizes[j]
            dir_names = [e[2].get('label', '?') for e in entries]
            print(f"    ERROR: {len(entries)} '{label}' directories have "
                  f"overlapping combo sizes {sorted(overlap)}:",
                  file=sys.stderr)
            for dn, sizes in zip(dir_names, all_sizes):
                print(f"      {dn}: sizes {sorted(sizes)}", file=sys.stderr)
            print(f"    Remove one of the conflicting directories and re-run.",
                  file=sys.stderr)
            sys.exit(1)

        # No overlap — merge
        # Sort entries by minimum combo size (smaller sizes first)
        entries.sort(key=lambda e: min(r['combo_size'] for r in e[0]) if e[0] else 0)

        merged_dedup = []
        merged_combo = []
        merged_meta = dict(entries[0][2])  # use first entry's meta as base
        prior_cumul = 0
        for dedup, combo, meta in entries:
            sorted_dedup = sorted(dedup, key=lambda r: r['combo_size'])
            # This entry's max cumulative = total users identified by all
            # sizes in this entry. Users identified by smaller sizes are a
            # strict subset, so marginal = entry_max - prior_cumul.
            entry_max = max(r['cumulative_total'] for r in sorted_dedup) if sorted_dedup else 0
            entry_marginal = entry_max - prior_cumul

            if len(sorted_dedup) == 1:
                # Single size: marginal is exact
                merged_dedup.append({
                    'combo_size': sorted_dedup[0]['combo_size'],
                    'new_users': entry_marginal,
                    'cumulative_total': prior_cumul + entry_marginal,
                })
            else:
                # Multiple sizes: internal dedup is correct, just shift
                # cumulative totals to account for prior entries
                for r in sorted_dedup:
                    merged_dedup.append({
                        'combo_size': r['combo_size'],
                        'new_users': r['new_users'],
                        'cumulative_total': prior_cumul + r['cumulative_total'],
                    })
            prior_cumul += entry_marginal
            merged_combo.extend(combo)

        merged_combo.sort(key=lambda r: (r['combo_size'], -r['combo_only_unique_new']))

        sizes_str = '+'.join(str(r['combo_size']) for r in merged_dedup)
        print(f"    merged {len(entries)} '{label}' directories "
              f"(sizes {sizes_str}) into one dataset")
        merged.append((label, merged_dedup, merged_combo, merged_meta))

    return merged


def run_comparisons(dirs, ext_metadata=None, run_all=False):
    """Load all directories and generate comparison visualizations."""
    # Output goes to the current working directory.
    output_dir = os.getcwd()
    print(f"\n  Comparison graphs → {output_dir}/")

    # Load all runs: (label, dedup_rows, combo_rows, meta)
    overall_runs = []
    # {os_name: [(label, dedup, combo, meta), ...]}
    os_runs = defaultdict(list)

    for d in dirs:
        label = _derive_short_label(d)
        if not _matches_metrics_filter(d):
            continue
        combo = load_combo_csv(d)
        dedup = load_dedup_csv(d)

        # Load overall (global) data if present
        has_overall = combo or dedup
        if has_overall:
            meta = load_run_metadata(d)
            if ext_metadata and ext_metadata['total_users'] and not meta['total_users']:
                meta['total_users'] = ext_metadata['total_users']
            # Use unique_users as percentage denominator
            meta['all_users'] = meta['total_users']
            if meta.get('unique_users'):
                meta['total_users'] = meta['unique_users']
            overall_runs.append((label, dedup, combo, meta))

        # Per-OS: discover from this directory
        os_users = ext_metadata['os_users'] if ext_metadata else {}
        os_variants = discover_os_variants(d)

        # If no global data but we have per-OS data, build meta from the per-OS txt
        if not has_overall and not os_variants:
            continue

        for os_name, (os_combo, os_dedup) in os_variants.items():
            if not os_combo and not os_dedup:
                continue
            os_meta = {}
            os_meta['label'] = label
            os_meta['os_name'] = os_name
            txt_path = os.path.join(d, f'min_set_combos_os_{os_name}.txt')
            os_unique = parse_unique_baseline_from_txt(txt_path)
            os_total = parse_total_users_from_txt(txt_path)
            if os_total:
                os_meta['all_users'] = os_total
            if os_unique:
                os_meta['total_users'] = os_unique
                os_meta['unique_users'] = os_unique
            elif os_name in os_users:
                os_meta['total_users'] = os_users[os_name]
            elif os_total:
                os_meta['total_users'] = os_total
            elif os_dedup:
                os_meta['total_users'] = max(r['cumulative_total'] for r in os_dedup)
            else:
                os_meta['total_users'] = 0
            os_runs[os_name].append((label, os_dedup, os_combo, os_meta))

    # Provenance check: verify directories from the same run type have same user count
    # (skip for per-OS-only directories which intentionally have different counts)
    _user_counts = {}
    for d in dirs:
        n = _extract_total_users_from_txt(d)
        if n is not None:
            _user_counts[os.path.basename(d)] = n
    if _user_counts:
        _unique_counts = set(_user_counts.values())
        if len(_unique_counts) > 1:
            print(f"    provenance: directories have different total user counts "
                  f"(expected for per-OS runs)")
            for dirname, n in sorted(_user_counts.items()):
                print(f"      {dirname}: {n:,}")
        else:
            print(f"    provenance: {len(_user_counts)} directories, "
                  f"all {next(iter(_unique_counts)):,} total users ✓")

    # Merge same-label directories with non-overlapping combo sizes
    overall_runs = _merge_same_label_runs(overall_runs)
    for os_name in os_runs:
        os_runs[os_name] = _merge_same_label_runs(os_runs[os_name])

    if not overall_runs and not os_runs:
        print("    [skip] no data found")
        return

    # Always generate the two key graphs with paper-friendly names
    if os_runs and len(os_runs) >= 2:
        compare_os_grid_waterfall(os_runs, overall_runs, output_dir,
                                  out_name='minset_waterfall_grid.png')
        compare_os_average_waterfall(os_runs, overall_runs, output_dir,
                                     weighted=True,
                                     out_name='minset_waterfall_weighted-average.png')

    if run_all:
        # Overall comparisons (only if we have overall data)
        if len(overall_runs) >= 2:
            compare_dedup_waterfall(overall_runs, output_dir)
            compare_cumulative_pct(overall_runs, output_dir)
            compare_metric_contribution(overall_runs, output_dir)

        # Cross-OS comparisons (with original names)
        if os_runs and len(os_runs) >= 2:
            compare_os_coverage(os_runs, overall_runs, output_dir)
            compare_os_grid_waterfall(os_runs, overall_runs, output_dir)
            compare_os_average_waterfall(os_runs, overall_runs, output_dir)
            compare_os_average_waterfall(os_runs, overall_runs, output_dir, weighted=True)
            compare_os_cumulative_lines(os_runs, overall_runs, output_dir)

        # Per-OS comparisons
        for os_name in sorted(os_runs):
            if len(os_runs[os_name]) < 2:
                continue
            compare_dedup_waterfall(os_runs[os_name], output_dir, os_name=os_name)
            compare_cumulative_pct(os_runs[os_name], output_dir, os_name=os_name)
            compare_metric_contribution(os_runs[os_name], output_dir, os_name=os_name)


# =============================================================================
# Main
# =============================================================================

def process_directory(output_dir, viz_names, ext_metadata=None):
    """Load data from one directory and run requested visualizations.

    ext_metadata: optional dict from load_metadata_from_os_txt() with
                  'total_users' and 'os_users' keys.
    """
    dirname = os.path.basename(os.path.abspath(output_dir))
    print(f"  {dirname}/")

    if not os.path.isdir(output_dir):
        print(f"    ERROR: not a directory")
        return

    combo_rows = load_combo_csv(output_dir)
    dedup_rows = load_dedup_csv(output_dir)

    if not combo_rows and not dedup_rows:
        print(f"    no min_set_combos data — skipping")
        return

    meta = load_run_metadata(output_dir)
    # Override total_users from external metadata if available and local is missing
    if ext_metadata and ext_metadata['total_users'] and not meta['total_users']:
        meta['total_users'] = ext_metadata['total_users']
    # Use unique_users as the percentage denominator (stored as total_users
    # so all downstream viz functions automatically use it)
    meta['all_users'] = meta['total_users']
    if meta.get('unique_users'):
        meta['total_users'] = meta['unique_users']
    print(f"    {len(combo_rows)} combos, {len(dedup_rows)} sizes, "
          f"{meta.get('unique_users', '?'):,} unique users (of {meta.get('all_users', '?'):,} total)")

    save_dir = os.getcwd()
    for name in viz_names:
        if name not in _VISUALIZATIONS:
            print(f"    [warn] unknown visualization: {name}")
            continue
        fn, desc = _VISUALIZATIONS[name]
        fn(dedup_rows, combo_rows, meta, save_dir)

    # Per-OS visualizations
    os_variants = discover_os_variants(output_dir)
    os_users = ext_metadata['os_users'] if ext_metadata else {}
    if os_variants:
        print(f"    per-OS data found: {', '.join(os_variants.keys())}")
        for os_name, (os_combo, os_dedup) in os_variants.items():
            if not os_combo and not os_dedup:
                continue
            os_meta = dict(meta)
            os_meta['label'] = f"{meta['label']} ({os_name})"
            os_meta['os_name'] = os_name
            # Get unique_users for this OS from txt file
            txt_path = os.path.join(output_dir, f'min_set_combos_os_{os_name}.txt')
            os_unique = parse_unique_baseline_from_txt(txt_path)
            if os_unique:
                os_meta['total_users'] = os_unique
                os_meta['unique_users'] = os_unique
            elif os_name in os_users:
                os_meta['total_users'] = os_users[os_name]
            elif os_dedup:
                os_meta['total_users'] = max(r['cumulative_total'] for r in os_dedup)
            elif os_combo:
                size1 = [r for r in os_combo if r['combo_size'] == 1]
                if size1:
                    os_meta['total_users'] = max(r['combo_unique'] for r in size1)
            print(f"    [{os_name}] {len(os_combo)} combos, {len(os_dedup)} sizes, "
                  f"{os_meta.get('total_users', '?'):,} unique users")
            for name in viz_names:
                if name not in _VISUALIZATIONS:
                    continue
                fn, desc = _VISUALIZATIONS[name]
                fn(os_dedup, os_combo, os_meta, save_dir)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'args', nargs='*',
        help='Directories and/or visualization names (auto-detected)',
    )
    parser.add_argument(
        '--list', action='store_true',
        help='List available visualizations and exit',
    )
    parser.add_argument(
        '--metadata-dir', metavar='DIR',
        help='Directory containing os.txt with per-OS user counts '
             '(e.g. a shannon_hhi output dir). Provides total_users for '
             'percentage-based visualizations.',
    )
    parser.add_argument(
        '--csv', action='store_true',
        help='Also output a .csv file alongside each .png with the graph data',
    )
    parser.add_argument(
        '--all', action='store_true',
        help='Output all visualizations. Without this flag, only outputs '
             'minset_waterfall_grid.png and minset_waterfall_weighted-average.png',
    )
    parser.add_argument(
        '--metrics', metavar='N,N,...',
        help='Only include combos with these many metrics, e.g. "5,6,7,8"',
    )
    parsed = parser.parse_args()

    if parsed.csv:
        global EMIT_CSV
        EMIT_CSV = True

    if parsed.metrics:
        global METRICS_FILTER
        METRICS_FILTER = {int(x.strip()) for x in parsed.metrics.split(',')}
        print(f"Filtering to metric counts: {sorted(METRICS_FILTER)}")

    if parsed.list:
        print("Available visualizations:")
        for name, (fn, desc) in sorted(_VISUALIZATIONS.items()):
            default = ' (default)' if name in DEFAULT_VISUALIZATIONS else ''
            print(f"  {name:<30} {desc}{default}")
        return

    # Separate directories from visualization names
    dirs = []
    viz_names = []
    for arg in parsed.args:
        if os.path.isdir(arg):
            dirs.append(arg)
        elif arg in _VISUALIZATIONS:
            viz_names.append(arg)
        else:
            print(f"Warning: '{arg}' is not a directory or known visualization, skipping",
                  file=sys.stderr)

    if not dirs:
        print("No directories specified.", file=sys.stderr)
        sys.exit(1)

    if not viz_names:
        viz_names = list(DEFAULT_VISUALIZATIONS)

    # Load external metadata if provided
    ext_metadata = None
    if parsed.metadata_dir:
        ext_metadata = load_metadata_from_os_txt(parsed.metadata_dir)

    if getattr(parsed, 'all', False):
        print(f"viz_minset — {len(dirs)} directory(ies), {len(viz_names)} visualization(s): "
              f"{', '.join(viz_names)}")
        for d in dirs:
            process_directory(d, viz_names, ext_metadata=ext_metadata)
    else:
        print(f"viz_minset — {len(dirs)} directory(ies), default output only "
              f"(use --all for everything)")

    # Comparison graphs when multiple directories provided
    if len(dirs) >= 2:
        run_comparisons(dirs, ext_metadata=ext_metadata, run_all=getattr(parsed, 'all', False))

    # Write provenance log
    log_path = os.path.join(os.getcwd(), 'run_viz_minset.log')
    write_run_log(log_path, dirs, ext_metadata, parsed)


def write_run_log(log_path, dirs, ext_metadata, parsed):
    lines = []
    lines.append('=' * 60)
    lines.append('viz_minset — Provenance Log')
    lines.append(f'Generated: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}')
    lines.append('=' * 60)
    lines.append('')
    if ext_metadata:
        lines.append('METADATA SOURCE')
        lines.append(f'  {parsed.metadata_dir}')
        lines.append(f'  Total users: {ext_metadata["total_users"]:,}')
        for os_name in sorted(ext_metadata.get('os_users', {})):
            lines.append(f'    {os_name:8s}  {ext_metadata["os_users"][os_name]:>12,}')
        lines.append('')
    lines.append(f'DATA DIRECTORIES: {len(dirs)}')
    for d in dirs:
        meta = load_run_metadata(d)
        unique = meta.get('unique_users', 0)
        total = meta.get('total_users', 0)
        fp = meta.get('fp_name', 'unknown')
        unique_str = f'{unique:,}' if unique else 'unknown'
        total_str = f'{total:,}' if total else 'unknown'
        lines.append(f'  {d}')
        lines.append(f'    fingerprinter={fp}  unique={unique_str}  total={total_str}')
        os_variants = discover_os_variants(d)
        if os_variants:
            for os_name in sorted(os_variants):
                os_combo, os_dedup = os_variants[os_name]
                txt_path = os.path.join(d, f'min_set_combos_os_{os_name}.txt')
                baseline = parse_unique_baseline_from_txt(txt_path)
                baseline_str = f'{baseline:,}' if baseline else 'unknown'
                n_combos = len(os_combo) if os_combo else 0
                lines.append(f'    {os_name:8s}  baseline_unique={baseline_str}  combos={n_combos}')
    lines.append('')
    if getattr(parsed, 'metrics', None):
        lines.append(f'METRICS FILTER: {parsed.metrics}')
        lines.append('')
    lines.append('OUTPUT DIRECTORY')
    lines.append(f'  {os.getcwd()}')
    lines.append('')

    with open(log_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote: {log_path}')


if __name__ == '__main__':
    main()
