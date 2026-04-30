#!/usr/bin/env python3
"""Build a 3-column LaTeX table comparing the metrics collected by each
fingerprinter (Akamai, Fingerprint Pro, SignifyD), aligned by metric.

The set of metrics each fingerprinter collects comes from the
`FPSET_*_REALISTIC` sets in `fingerprinters.py` — i.e. the canonical
fingerprinter definition, not whatever happened to land in the CSV.

The row order comes from the *Overall* iterative SMR rankings supplied
via a directory (`iterative_minmetrics_<FP>_Realistic.csv` files,
without `_os_<OS>` in the name). The directory may contain the CSVs
directly or in immediate per-fingerprinter subdirectories. Each metric
is sorted by its rank in Fingerprint Pro first, then SignifyD, then
Akamai (∞ for "not in this ranking"), so the metric that's highest in
the most-comprehensive available fingerprinter rises to the top.

Reads `name_mapping.txt` if present (same format as the iminmetrics
table script); appends any newly-encountered metrics so the file stays
in sync.

Usage:
    python3 build_table.py <dir> [--output table.tex] [--name-mapping PATH]
"""

import argparse
import csv
import importlib.util
import re
import sys
from pathlib import Path


# (raw fingerprinter key, display name, LaTeX colour name, FPSET module attr)
FP_DEFS = [
    ('AkamaiV2_Realistic', 'Akamai',          'teal',    'FPSET_AKAMAI_V2_REALISTIC'),
    ('FPJSv2_Realistic',   'Fingerprint Pro', 'red',     'FPSET_FINGERPRINTJS_V2_REALISTIC'),
    ('Signifyd_Realistic', 'SignifyD',        'magenta', 'FPSET_SIGNIFYD_REALISTIC'),
]
COLUMN_ORDER   = ['AkamaiV2_Realistic', 'FPJSv2_Realistic', 'Signifyd_Realistic']
SORT_PRIORITY  = ['FPJSv2_Realistic', 'Signifyd_Realistic', 'AkamaiV2_Realistic']
KNOWN_FPS      = {k for k, _, _, _ in FP_DEFS}

# combined_wgpu_hash is a SHA over these 31 GPU adapter limits — see
# datavalues.py:_wgpu_limits. Whenever we encounter it in a fingerprinter's
# set or in an iterative ranking we expand it into its components so the
# table shows the underlying metrics individually.
WGPU_INDIVIDUAL_METRICS = [
    'wgpu_maxtexturedimension1d',
    'wgpu_maxtexturedimension2d',
    'wgpu_maxtexturedimension3d',
    'wgpu_maxtexturearraylayers',
    'wgpu_maxbindgroups',
    'wgpu_maxbindgroupsplusvertexbuffers',
    'wgpu_maxbindingsperbindgroup',
    'wgpu_maxdynamicuniformbuffersperpipelinelayout',
    'wgpu_maxdynamicstoragebuffersperpipelinelayout',
    'wgpu_maxsampledtexturespershaderstage',
    'wgpu_maxsamplerspershaderstage',
    'wgpu_maxstoragebufferspershaderstage',
    'wgpu_maxstoragetexturespershaderstage',
    'wgpu_maxuniformbufferspershaderstage',
    'wgpu_maxuniformbufferbindingsize',
    'wgpu_maxstoragebufferbindingsize',
    'wgpu_minuniformbufferoffsetalignment',
    'wgpu_minstoragebufferoffsetalignment',
    'wgpu_maxvertexbuffers',
    'wgpu_maxbuffersize',
    'wgpu_maxvertexattributes',
    'wgpu_maxvertexbufferarraystride',
    'wgpu_maxinterstageshadervariables',
    'wgpu_maxcolorattachments',
    'wgpu_maxcolorattachmentbytespersample',
    'wgpu_maxcomputeworkgroupstoragesize',
    'wgpu_maxcomputeinvocationsperworkgroup',
    'wgpu_maxcomputeworkgroupsizex',
    'wgpu_maxcomputeworkgroupsizey',
    'wgpu_maxcomputeworkgroupsizez',
    'wgpu_maxcomputeworkgroupsperdimension',
]


def expand_wgpu(fp_sets, rankings):
    """Replace combined_wgpu_hash with its 31 components in every FP set
    and ranking that contains it. Components inherit the original rank."""
    for fp, members in fp_sets.items():
        if 'combined_wgpu_hash' in members:
            members.discard('combined_wgpu_hash')
            members.update(WGPU_INDIVIDUAL_METRICS)
    for fp, rank in rankings.items():
        if 'combined_wgpu_hash' in rank:
            r = rank.pop('combined_wgpu_hash')
            for m in WGPU_INDIVIDUAL_METRICS:
                rank.setdefault(m, r)


def load_overall_ranking(path):
    """Return {metric: rank} from an iterative_minmetrics CSV."""
    out = {}
    with path.open() as f:
        for r in csv.DictReader(f):
            out[r['MetricAdded']] = int(r['K'])
    return out


def load_name_mapping(path):
    """Read a `metric = display name` file. Missing file is fine."""
    if not path.exists():
        return {}
    mapping = {}
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        if key:
            mapping[key] = value
    return mapping


def discover(directory):
    """Find iterative_minmetrics_<FP>_Realistic.csv (no `_os_`) per known FP.

    Looks in `directory` directly first, then in immediate subdirectories.
    Returns {fp_key: Path}. First match per FP wins.
    """
    out = {}
    pattern = re.compile(r'^iterative_minmetrics_(.+?)\.csv$')

    def consider(p):
        m = pattern.match(p.name)
        if not m:
            return
        stem = m.group(1)
        if '_os_' in stem:
            return
        if stem in KNOWN_FPS and stem not in out:
            out[stem] = p

    for f in sorted(directory.iterdir()):
        if f.is_file():
            consider(f)
    if len(out) < len(KNOWN_FPS):
        for sub in sorted(directory.iterdir()):
            if not sub.is_dir():
                continue
            for f in sorted(sub.iterdir()):
                if f.is_file():
                    consider(f)
    return out


def latex_metric(name):
    return name.replace('_', r'\_')


def render(fp_sets, rankings, name_mapping=None):
    """Build the LaTeX 3-column table.

    Each column lists that fingerprinter's metrics in its own iterative
    SMR rank order — independent of the other columns. Colours flag
    cross-fingerprinter overlap:
      - red  : metric is in all three fingerprinters
      - blue : metric is in Fingerprint Pro and SignifyD (but not Akamai)

    fp_sets:   {fp_key: set(metrics)}  — from fingerprinters.py
    rankings:  {fp_key: {metric: rank}} — from iterative_minmetrics CSVs
    """
    name_mapping = name_mapping or {}
    INF = float('inf')

    ak_set = fp_sets.get('AkamaiV2_Realistic', set())
    fp_set = fp_sets.get('FPJSv2_Realistic', set())
    sn_set = fp_sets.get('Signifyd_Realistic', set())

    def overlap_color(m):
        in_ak, in_fp, in_sn = m in ak_set, m in fp_set, m in sn_set
        if in_ak and in_fp and in_sn:
            return 'red'
        if in_fp and in_sn:
            return 'blue'
        return None

    def display(m):
        label = latex_metric(name_mapping.get(m, m))
        c = overlap_color(m)
        if c:
            return f'\\textcolor{{{c}}}{{{label}}}'
        return label

    # Per-column ordered metric lists, sorted by each FP's own iterative
    # SMR rank (∞ for metrics in the FP set but absent from the ranking).
    columns = []
    for fp in COLUMN_ORDER:
        rank = rankings.get(fp, {})
        members = list(fp_sets.get(fp, set()))
        members.sort(key=lambda m: (rank.get(m, INF), m))
        columns.append(members)

    n_rows = max((len(c) for c in columns), default=0)

    # Headers: plain coloured + bold, sharing the same `l` alignment as
    # the body cells so they line up vertically with the metric names
    # below them.
    headers = []
    for fp in COLUMN_ORDER:
        display_name, color = next(
            (d, c) for k, d, c, _ in FP_DEFS if k == fp)
        headers.append(f'\\textbf{{\\textcolor{{{color}}}{{{display_name}}}}}')
    header_row = ' & '.join(headers) + r' \\'

    caption = (
        r'\caption{Metrics collected by each modeled fingerprinter '
        r'(\textit{Akamai}, \textit{Fingerprint Pro}, \textit{SignifyD}); '
        r'each column is sorted by that fingerprinter\textquotesingle s '
        r'iterative SMR rank. \textcolor{red}{Red}: metric is collected '
        r'by all three fingerprinters. \textcolor{blue}{Blue}: metric is '
        r'collected by Fingerprint Pro and SignifyD but not Akamai.}'
    )

    out = []
    out.append(r'{\scriptsize')
    out.append(r'\begin{longtable}{l | l | l}')
    out.append(caption + r' \label{tab:fingerprinter_metrics} \\')
    out.append(r'\Xhline{2\arrayrulewidth}')
    out.append(header_row)
    out.append(r'\Xhline{2\arrayrulewidth}')
    out.append(r'\endfirsthead')
    out.append(r'\multicolumn{3}{c}{\textit{(continued)}} \\')
    out.append(r'\Xhline{2\arrayrulewidth}')
    out.append(header_row)
    out.append(r'\Xhline{2\arrayrulewidth}')
    out.append(r'\endhead')
    out.append(r'\Xhline{2\arrayrulewidth}')
    out.append(r'\endfoot')
    out.append(r'\Xhline{2\arrayrulewidth}')
    out.append(r'\endlastfoot')

    for i in range(n_rows):
        cells = []
        for col in columns:
            cells.append(display(col[i]) if i < len(col) else '')
        out.append(' & '.join(cells) + r' \\')

    out.append(r'\end{longtable}')
    out.append(r'}')
    return '\n'.join(out) + '\n'


def load_fp_sets():
    """Import fingerprinters.py (sibling-of-sibling: ../../) and pull the
    realistic FP sets out of it."""
    fp_path = (Path(__file__).resolve().parent.parent.parent
               / 'fingerprinters.py')
    if not fp_path.is_file():
        sys.exit(f'ERROR: {fp_path} does not exist')
    spec = importlib.util.spec_from_file_location('fingerprinters', fp_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = {}
    for key, _, _, attr in FP_DEFS:
        if not hasattr(mod, attr):
            sys.exit(f'ERROR: {fp_path} has no attribute {attr}')
        out[key] = set(getattr(mod, attr))
    return out


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('directory',
                        help='Directory with iterative_minmetrics_<FP>_Realistic.csv '
                             '(searched directly, then 1 level of subdirs)')
    parser.add_argument('--output', default='table.tex',
                        help='Output LaTeX file (default: ./table.tex)')
    parser.add_argument('--name-mapping',
                        default=str(Path.cwd() / 'name_mapping.txt'),
                        help='Optional `metric = display name` file '
                             '(default: ./name_mapping.txt; missing file ok)')
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        sys.exit(f'ERROR: not a directory: {directory}')

    fp_sets = load_fp_sets()
    print('Fingerprinter metric sets (from fingerprinters.py):')
    for fp in COLUMN_ORDER:
        print(f'  {fp}: {len(fp_sets[fp])} metrics')

    files = discover(directory)
    if not files:
        sys.exit(f'ERROR: no iterative_minmetrics_<FP>_Realistic.csv files '
                 f'found under {directory}')

    rankings = {fp: load_overall_ranking(p) for fp, p in files.items()}
    print(f'Loaded {len(rankings)} iterative SMR ranking(s):')
    for fp in COLUMN_ORDER:
        if fp in files:
            print(f'  {fp}: {len(rankings[fp])} ranked  ({files[fp]})')

    # Expand combined_wgpu_hash → 31 underlying wgpu_* metrics.
    expand_wgpu(fp_sets, rankings)

    mapping_path = Path(args.name_mapping)
    name_mapping = load_name_mapping(mapping_path)
    if name_mapping:
        print(f'Loaded {len(name_mapping)} display-name overrides from '
              f'{mapping_path}')

    # Append metrics that appear in the table but aren't in the mapping yet.
    # The displayed metrics are the union of the fingerprinter SETS (from
    # fingerprinters.py); ordering uses the iterative-SMR rankings.
    union = set()
    for s in fp_sets.values():
        union |= s
    INF = float('inf')

    def sort_key(m):
        return tuple(
            rankings.get(fp, {}).get(m, INF)
            for fp in SORT_PRIORITY
        )

    table_metrics = sorted(union, key=sort_key)
    new_entries = [m for m in table_metrics if m not in name_mapping]
    if new_entries:
        file_existed = mapping_path.exists()
        with mapping_path.open('a', encoding='utf-8') as f:
            if not file_existed:
                f.write('# Display-name overrides for build_table.py\n')
                f.write('# Format: metric_name = display name\n')
                f.write('# Lines starting with `#` and blank lines are '
                        'ignored.\n\n')
            elif name_mapping:
                f.write('\n')
            for m in new_entries:
                f.write(f'{m} = {m}\n')
                name_mapping[m] = m
        print(f'Appended {len(new_entries)} new metric(s) to {mapping_path}')

    text = render(fp_sets, rankings, name_mapping)
    out_path = Path(args.output)
    out_path.write_text(text, encoding='utf-8')
    print(f'Wrote {out_path.resolve()}')


if __name__ == '__main__':
    main()
