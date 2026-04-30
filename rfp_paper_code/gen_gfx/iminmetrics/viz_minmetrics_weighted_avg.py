#!/usr/bin/env python3
"""MinMetrics viz #1: cumulative uniqueness curves overlaid by fingerprinter.

Overlays the K-vs-%-unique curves from multiple MinMetrics runs on a single
axes. Each curve ends at that fingerprinter's baseline plateau (dashed
reference line shown for each).

Usage:
    ./shortcuts/viz_minmetrics_1.py <dir1> [dir2 dir3 ...] [output.png]
"""

import csv
import os
import sys
import time

os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_minmetrics(csv_path):
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            rows.append({
                'k':       int(r['K']),
                'metric':  r['MetricAdded'],
                'unique':  int(r['UniqueFingerprints']),
                'pct':     float(r['PercentUnique']),
                'new':     int(r['NewlyUnique']),
                'cum_new': int(r['CumulativeNewlyUnique']),
            })
    return rows


def parse_txt_header(txt_path):
    info = {'fp': None, 'total': None, 'plateau': None}
    if not os.path.exists(txt_path):
        return info
    with open(txt_path) as f:
        for line in f:
            if line.startswith('MinMetrics:') or line.startswith('Iterative MinMetrics'):
                # "MinMetrics: FPJSv2_Realistic (...)" or
                # "Iterative MinMetrics (Greedy): FPJSv2_Realistic"
                rest = line.split(':', 1)[1].strip()
                if rest.startswith('('):
                    rest = line.split(':', 2)[2].strip()
                info['fp'] = rest.split(' ')[0].split('(')[0].strip()
            elif line.startswith('Total users:'):
                info['total'] = int(line.split(':', 1)[1].strip().replace(',', ''))
            elif line.startswith('Baseline unique'):
                # "Baseline unique (all fingerprinter metrics): 18,816,141 (75.65%)"
                if '(' in line and '%' in line:
                    pct = line.rsplit('(', 1)[1].rstrip().rstrip(')').rstrip('%')
                    try:
                        info['plateau'] = float(pct)
                    except ValueError:
                        pass
    return info


def parse_args(argv):
    dirs, out_path = [], None
    for a in argv[1:]:
        if a.endswith('.png'):
            out_path = a
        else:
            dirs.append(a)
    return dirs, out_path


def main():
    dirs, out_path = parse_args(sys.argv)
    if not dirs:
        print(__doc__)
        sys.exit(1)

    runs = []
    for d in dirs:
        # Try single-file format first, then discover per-fingerprinter CSVs
        single = os.path.join(d, 'minmetrics.csv')
        if os.path.exists(single):
            rows = load_minmetrics(single)
            info = parse_txt_header(os.path.join(d, 'minmetrics.txt'))
            runs.append((d, rows, info))
        else:
            for f in sorted(os.listdir(d)):
                if (f.startswith('minmetrics_') or f.startswith('iterative_minmetrics_')) and f.endswith('.csv') and '_os_' not in f:
                    rows = load_minmetrics(os.path.join(d, f))
                    info = parse_txt_header(os.path.join(d, f.replace('.csv', '.txt')))
                    runs.append((d, rows, info))

    if out_path is None:
        suffix = '_combined' if len(runs) > 1 else ''
        out_path = os.path.join(os.getcwd(), f'viz_minmetrics_1{suffix}.png')

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    fig, ax = plt.subplots(figsize=(7, 4.5))
    max_k = max(max(r['k'] for r in rows) for _, rows, _ in runs)

    fp_display_names = {
        'FPJSv2':   'Fingerprint Pro',
        'AkamaiV2': 'Akamai',
        'Signifyd': 'SignifyD',
    }
    for i, (_, rows, info) in enumerate(runs):
        c = colors[i % len(colors)]
        ks  = [r['k']   for r in rows]
        pct = [r['pct'] for r in rows]
        fp_raw = (info['fp'] or os.path.basename(dirs[i])).replace('_Realistic', '')
        fp_name = fp_display_names.get(fp_raw, fp_raw)
        plateau = info['plateau'] if info['plateau'] is not None else max(pct)
        label = f"{fp_name} ({plateau:.1f}%)"

        ax.plot(ks, pct, marker='o', markersize=5, linewidth=2.5, color=c, label=label)
        ax.axhline(plateau, color=c, linestyle='--', linewidth=0.8, alpha=0.35)

        # Stars at 50%, 80%, and 99% of plateau
        for p_target, ms in ((50, 200), (80, 260), (99, 320)):
            threshold = plateau * p_target / 100
            for r in rows:
                if r['pct'] >= threshold:
                    ax.scatter([r['k']], [r['pct']], marker='*', s=ms,
                               color=c, edgecolor='black', linewidth=0.7, zorder=5)
                    # Position labels to avoid overlap (branch on raw name,
                    # not the display name)
                    if 'FPJSv2' in fp_raw:
                        _xoff, _yoff, _ha = (-6, 8, 'center')
                        _text = f"K={r['k']}\n\n{p_target}%"
                    elif 'Signifyd' in fp_raw and p_target == 50:
                        _xoff, _yoff, _ha = (10, -34, 'left')
                        _text = f"{p_target}%\n\nK={r['k']}"
                    else:
                        _xoff, _yoff, _ha = (0, -34, 'center')
                        _text = f"{p_target}%\n\nK={r['k']}"
                    ax.annotate(_text,
                                (r['k'], r['pct']),
                                textcoords='offset points', xytext=(_xoff, _yoff),
                                fontsize=10, fontweight='bold', color=c, ha=_ha,
                                linespacing=0.8)
                    break

    ax.set_xlabel('K (number of metrics in fingerprint)', fontsize=12)
    ax.set_ylabel('% of users uniquely identified', fontsize=12)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 100)
    ax.tick_params(labelsize=11)
    # Relabel the rightmost tick "30" → "30+" to signal the curve continues
    # beyond the visible window.
    _xticks = list(ax.get_xticks())
    if _xticks and _xticks[-1] == 30:
        ax.set_xticks(_xticks)
        ax.set_xticklabels([
            f"{int(t)}+" if t == 30 else f"{int(t) if t == int(t) else t}"
            for t in _xticks
        ])
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=11)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f'Saved: {out_path}')

    # Write provenance log
    log_path = os.path.join(os.path.dirname(out_path), 'run_weighted_avg.log')
    write_run_log(log_path, dirs, runs, out_path)


def write_run_log(log_path, dirs, runs, out_path):
    fp_display_names = {
        'FPJSv2':   'Fingerprint Pro',
        'AkamaiV2': 'Akamai',
        'Signifyd': 'SignifyD',
    }
    lines = []
    lines.append('=' * 60)
    lines.append('viz_minmetrics_weighted_avg — Provenance Log')
    lines.append(f'Generated: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}')
    lines.append('=' * 60)
    lines.append('')
    lines.append('SOURCE DIRECTORIES')
    for d in dirs:
        lines.append(f'  {d}')
    lines.append('')
    lines.append(f'RUNS: {len(runs)}')
    for d, rows, info in runs:
        fp_raw = (info['fp'] or '?').replace('_Realistic', '')
        display = fp_display_names.get(fp_raw, fp_raw)
        total = f'{info["total"]:,}' if info['total'] else 'unknown'
        plateau = f'{info["plateau"]:.2f}%' if info['plateau'] is not None else 'unknown'
        k_max = max(r['k'] for r in rows) if rows else 0
        lines.append(f'  {display} ({info["fp"] or "?"}):')
        lines.append(f'    users={total}  baseline_unique={plateau}  K=1..{k_max}')
        lines.append(f'    source: {d}')
    lines.append('')
    lines.append('OUTPUT')
    lines.append(f'  {out_path}')
    lines.append('')

    with open(log_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote: {log_path}')


if __name__ == '__main__':
    main()
