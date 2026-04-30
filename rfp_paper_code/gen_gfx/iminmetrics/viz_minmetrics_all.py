#!/usr/bin/env python3
"""MinMetrics viz #1c: 3x1 vertical grid, one panel per fingerprinter, 4 OS lines each.

Each panel shows one fingerprinter with four lines (one per OS). Panels are
stacked vertically so the x-axes align for comparison.

Usage:
    ./shortcuts/viz_minmetrics_1c.py <dir> [output.png]
"""

import csv
import os
import re
import sys
import time

os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OS_ORDER  = ['Android', 'Darwin', 'Linux', 'WINNT']
OS_LABEL  = {'Android': 'Android', 'Darwin': 'macOS', 'Linux': 'Linux', 'WINNT': 'Windows'}
OS_COLORS = {'Android': '#2ca02c', 'Darwin': '#ff7f0e', 'Linux': '#d62728', 'WINNT': '#1f77b4'}
OS_MARKERS = {'Android': '^', 'Darwin': 's', 'Linux': 'D', 'WINNT': 'o'}


def load_minmetrics(csv_path):
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            rows.append({
                'k':      int(r['K']),
                'pct':    float(r['PercentUnique']),
                'new':    int(r['NewlyUnique']),
            })
    return rows


def parse_txt_header(txt_path):
    info = {'total': None, 'plateau': None}
    if not os.path.exists(txt_path):
        return info
    with open(txt_path) as f:
        for line in f:
            if line.startswith('Total users:'):
                info['total'] = int(line.split(':', 1)[1].strip().replace(',', ''))
            elif line.startswith('Baseline unique'):
                if '(' in line and '%' in line:
                    pct = line.rsplit('(', 1)[1].rstrip().rstrip(')').rstrip('%')
                    try:
                        info['plateau'] = float(pct)
                    except ValueError:
                        pass
    return info


def discover(dirs):
    out = {}
    for input_dir in dirs:
        for f in os.listdir(input_dir):
            if not f.endswith('.csv'):
                continue
            if f.startswith('iterative_minmetrics_'):
                base = f[len('iterative_minmetrics_'):-len('.csv')]
            elif f.startswith('minmetrics_'):
                base = f[len('minmetrics_'):-len('.csv')]
            else:
                continue
            m = re.match(r'(.+?)_os_([A-Za-z]+)$', base)
            if not m:
                continue
            fp, os_name = m.group(1), m.group(2)
            csv_p = os.path.join(input_dir, f)
            txt_p = csv_p[:-4] + '.txt'
            out.setdefault(fp, {})[os_name] = (csv_p, txt_p)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    dirs = [a for a in sys.argv[1:] if os.path.isdir(a)]
    out_path = next((a for a in sys.argv[1:] if a.endswith('.png')), None)
    if not dirs:
        print("No directories specified", file=sys.stderr)
        sys.exit(1)
    if not out_path:
        out_path = os.path.join(os.getcwd(), 'viz_minmetrics_1c.png')

    fps = discover(dirs)
    if not fps:
        print(f'No per-OS minmetrics files found in {input_dir}', file=sys.stderr)
        sys.exit(1)

    fp_order = sorted(fps)
    n_fp = len(fp_order)

    # Global max K for shared x-axis
    max_k = 0
    for fp in fp_order:
        for _, (csv_p, _) in fps[fp].items():
            rows = load_minmetrics(csv_p)
            if rows:
                max_k = max(max_k, max(r['k'] for r in rows))

    fig, axes = plt.subplots(n_fp, 1, figsize=(11, 5 * n_fp),
                             sharex=True, sharey=True, squeeze=False)

    fp_display_names = {
        'FPJSv2':   'Fingerprint Pro',
        'AkamaiV2': 'Akamai',
        'Signifyd': 'SignifyD',
    }
    for row_idx, fp in enumerate(fp_order):
        ax = axes[row_idx][0]
        fp_raw = fp.replace('_Realistic', '')
        display_fp = fp_display_names.get(fp_raw, fp_raw)

        _pct_table = []  # [(os_label, color, k50, k90, k99)]
        for osn in OS_ORDER:
            entry = fps[fp].get(osn)
            if not entry:
                continue
            csv_p, txt_p = entry
            rows = load_minmetrics(csv_p)
            info = parse_txt_header(txt_p)
            if not rows:
                continue

            ks = [r['k'] for r in rows]
            pct = [r['pct'] for r in rows]
            plateau = info['plateau'] if info['plateau'] is not None else max(pct)
            # Normalize: pct / plateau * 100 so curve approaches 100%
            norm = [100 * p / plateau if plateau else 0 for p in pct]
            color = OS_COLORS.get(osn, '#999')
            marker = OS_MARKERS.get(osn, 'o')
            os_label = OS_LABEL.get(osn, osn)

            ax.plot(ks, norm, marker=marker, markersize=3.5, linewidth=2,
                    color=color, label=f"{os_label} (baseline {plateau:.1f}%)")

            # Stars at P50, P80, P99 (no labels)
            _k50 = _k80 = _k99 = '-'
            for p_target, attr, ms in [(50, '_k50', 160), (80, '_k80', 200), (99, '_k99', 250)]:
                for i, p in enumerate(norm):
                    if p >= p_target:
                        ax.scatter([ks[i]], [p], marker='*', s=ms, color=color,
                                   edgecolor='black', linewidth=0.7, zorder=5)
                        if p_target == 50: _k50 = ks[i]
                        elif p_target == 80: _k80 = ks[i]
                        elif p_target == 99: _k99 = ks[i]
                        break
            _pct_table.append((os_label, color, _k50, _k80, _k99))

        ax.set_xlim(0, 30)
        ax.set_ylim(0, 105)
        # Relabel the rightmost tick "30" → "30+" to signal the curve
        # continues beyond the visible window.
        _xticks = list(ax.get_xticks())
        if _xticks and _xticks[-1] == 30:
            ax.set_xticks(_xticks)
            ax.set_xticklabels([
                f"{int(t)}+" if t == 30 else f"{int(t) if t == int(t) else t}"
                for t in _xticks
            ])
        for pct_line in [50, 80, 99]:
            ax.axhline(pct_line, color='gray', linestyle=':', linewidth=0.8, alpha=0.4)
        ax.grid(True, alpha=0.3)
        ax.set_ylabel('% of baseline unique')
        ax.text(0.5, 0.68, display_fp,
                transform=ax.transAxes, fontsize=16, fontweight='bold',
                ha='center', va='center', alpha=0.15)

        # Percentile table in center
        _header = f"{'':8s}  {'P50':>4s}  {'P80':>4s}  {'P99':>4s}"
        _table_lines = [_header]
        for _os_label, _color, _k50, _k80, _k99 in _pct_table:
            _table_lines.append(f"{_os_label:8s}  {str(_k50):>4s}  {str(_k80):>4s}  {str(_k99):>4s}")
        _table_text = '\n'.join(_table_lines)
        ax.text(0.5, 0.35, _table_text,
                transform=ax.transAxes, fontsize=11, fontfamily='monospace',
                ha='center', va='center', alpha=0.6,
                bbox=dict(facecolor='white', edgecolor='#ccc', alpha=0.7, pad=4))

        ax.legend(loc='lower right', fontsize=9)

    axes[-1][0].set_xlabel('K (number of metrics in prefix)')

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f'Saved: {out_path}')

    # Write provenance log
    log_path = os.path.join(os.path.dirname(out_path), 'run.log')
    write_run_log(log_path, dirs, fps, fp_order, out_path)


def write_run_log(log_path, dirs, fps, fp_order, out_path):
    fp_display_names = {
        'FPJSv2':   'Fingerprint Pro',
        'AkamaiV2': 'Akamai',
        'Signifyd': 'SignifyD',
    }
    lines = []
    lines.append('=' * 60)
    lines.append('viz_minmetrics_all — Provenance Log')
    lines.append(f'Generated: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}')
    lines.append('=' * 60)
    lines.append('')
    lines.append('SOURCE DIRECTORIES')
    for d in dirs:
        lines.append(f'  {d}')
    lines.append('')
    lines.append(f'FINGERPRINTERS: {len(fp_order)}')
    for fp in fp_order:
        fp_raw = fp.replace('_Realistic', '')
        display = fp_display_names.get(fp_raw, fp_raw)
        lines.append(f'  {fp} ({display})')
    lines.append('')
    lines.append('PER-OS DATA')
    for fp in fp_order:
        fp_raw = fp.replace('_Realistic', '')
        display = fp_display_names.get(fp_raw, fp_raw)
        lines.append(f'  {display} ({fp}):')
        for osn in OS_ORDER:
            entry = fps[fp].get(osn)
            if not entry:
                continue
            csv_p, txt_p = entry
            info = parse_txt_header(txt_p)
            total = f'{info["total"]:,}' if info['total'] else 'unknown'
            plateau = f'{info["plateau"]:.2f}%' if info['plateau'] is not None else 'unknown'
            lines.append(f'    {OS_LABEL.get(osn, osn):8s}  users={total:>12s}  baseline_unique={plateau}')
            lines.append(f'             csv: {csv_p}')
        lines.append('')
    lines.append('OUTPUT')
    lines.append(f'  {out_path}')
    lines.append('')

    with open(log_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote: {log_path}')


if __name__ == '__main__':
    main()
