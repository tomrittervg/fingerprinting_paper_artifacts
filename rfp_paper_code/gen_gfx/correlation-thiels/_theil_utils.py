"""Shared utilities for Theil's U visualization scripts.

Environment variables (same convention as correlation/):
  THEIL_CSV=path/to/theil_u.csv         Theil's U pairwise data file (required)
  THEIL_OUT_DIR=path/to/output/         Output directory (default: script dir)
  THEIL_FILTER=phase2|nowebglparams|noparams|allfp
  THEIL_ALLOWLIST=path/to/mapping.txt   Restrict to listed metrics
  THEIL_ANALYZE_DIR=path/to/analyze/    For per-metric entropy/HHI
"""
import os
os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

import csv
import sys
from pathlib import Path
from collections import defaultdict

# Reuse pair rules and category metadata from correlation/
_CORR_DIR = Path(__file__).parent.parent / 'correlation'
sys.path.insert(0, str(_CORR_DIR))
from _pair_rules import is_valid_metric_pair_for_comparison
sys.path.pop(0)

_SCRIPT_CONFIGS = Path(__file__).parents[3] / 'code' / 'configs'
sys.path.insert(0, str(_SCRIPT_CONFIGS))
from metadata_metric_categories import METRIC_CATEGORIES, CATEGORY_ORDER, CATEGORY_COLORS
sys.path.pop(0)

HERE = Path(os.environ.get('THEIL_OUT_DIR', Path(__file__).parent))
_csv_default = None  # no default — must be provided
CSV_PATH = Path(os.environ.get('THEIL_CSV', ''))

if not CSV_PATH.exists():
    print(f"""\
Error: Theil's U CSV file not found: {CSV_PATH}

Usage: set environment variables before running any theil_*.py script.

  Required:
    THEIL_CSV=path/to/theil_u.csv        Pairwise Theil's U data file

  Optional:
    THEIL_OUT_DIR=path/to/output/         Output directory (default: script dir)
    THEIL_FILTER=phase2                   Metric filter (same as CORR_FILTER)
    THEIL_ALLOWLIST=path/to/mapping.txt   Restrict to listed metrics
    THEIL_ANALYZE_DIR=path/to/analyze/    analyze.py output for entropy/HHI
""", file=sys.stderr)
    sys.exit(1)


# ── Filters (reuse logic from correlation) ────────────────────────────────────

_FILTER = os.environ.get('THEIL_FILTER', '')
EXCLUDE_WEBGL_PARAMS = _FILTER in ('nowebglparams', 'noparams', 'allfp')
EXCLUDE_MATH_OPS     = _FILTER in ('noparams', 'allfp')
EXCLUDE_CSS_COLORS   = _FILTER in ('allfp',)
RESTRICT_TO_ALLFP    = _FILTER == 'allfp'
FILTER_SUFFIX        = f'_{_FILTER}' if _FILTER else ''

_MAPPING_FILE = Path(__file__).parents[3] / 'code' / 'configs' / 'metadata_metric_name_mapping.txt'
_ALLFP_ALLOWLIST = None
if RESTRICT_TO_ALLFP:
    _allfp = set()
    with open(_MAPPING_FILE) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith('#'):
                continue
            _parts = _line.split()
            # Format: datavalues_name  db_name  phase2fp  combination_metric
            if len(_parts) >= 3 and _parts[2] == '1':
                _allfp.add(_parts[1])
    _ALLFP_ALLOWLIST = _allfp

_ALLOWLIST_PATH = os.environ.get('THEIL_ALLOWLIST', '')
_CUSTOM_ALLOWLIST = None
if _ALLOWLIST_PATH:
    with open(_ALLOWLIST_PATH) as _f:
        _raw = [line.strip() for line in _f if line.strip() and not line.startswith('#')]
    _parsed = []
    for line in _raw:
        parts = line.split()
        # Format: datavalues_name  db_name  phase2fp  combination_metric
        name = parts[1] if len(parts) >= 2 else parts[0]
        if not name.startswith('~'):
            _parsed.append(name)
    _CUSTOM_ALLOWLIST = set(_parsed)


def _is_webgl_individual_param(m):
    if m.startswith('webgl_params_'):
        return True
    if m.startswith('webgl2_params_') and not m.endswith(('_json', '_sw_json')):
        return True
    return False


def _is_math_individual_op(m):
    return m.startswith('math_op_')


def _is_css_individual_color(m):
    return m.startswith('css_color_')


# ── Category assignment ───────────────────────────────────────────────────────
# Build DB-name → DataValues-name lookup for category resolution
_DB_TO_DV = {}
if _MAPPING_FILE.exists():
    with open(_MAPPING_FILE) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith('#'):
                continue
            _parts = _line.split()
            if len(_parts) >= 2 and _parts[0] != _parts[1]:
                _DB_TO_DV[_parts[1]] = _parts[0]

def get_category(m):
    cat = METRIC_CATEGORIES.get(m)
    if cat is not None:
        return cat
    dv_name = _DB_TO_DV.get(m)
    if dv_name is not None:
        cat = METRIC_CATEGORIES.get(dv_name)
        if cat is not None:
            return cat
    return 'Other'


# ── CSV loading ───────────────────────────────────────────────────────────────

def load_rows():
    """Return list of dicts from the Theil's U CSV, honouring active filters.

    Each dict has: metric1, metric2, u_1to2, u_2to1, mi, h1, h2, support_N,
                   distinct_1, distinct_2.
    """
    rows = []
    with open(CSV_PATH) as f:
        for r in csv.DictReader(f):
            m1, m2 = r['metric1'], r['metric2']
            if EXCLUDE_WEBGL_PARAMS and (
                _is_webgl_individual_param(m1) or _is_webgl_individual_param(m2)
            ):
                continue
            if EXCLUDE_MATH_OPS and (
                _is_math_individual_op(m1) or _is_math_individual_op(m2)
            ):
                continue
            if EXCLUDE_CSS_COLORS and (
                _is_css_individual_color(m1) or _is_css_individual_color(m2)
            ):
                continue
            if RESTRICT_TO_ALLFP and (
                m1 not in _ALLFP_ALLOWLIST or m2 not in _ALLFP_ALLOWLIST
            ):
                continue
            if _CUSTOM_ALLOWLIST is not None and (
                m1 not in _CUSTOM_ALLOWLIST or m2 not in _CUSTOM_ALLOWLIST
            ):
                continue
            if not is_valid_metric_pair_for_comparison(m1, m2):
                continue
            rows.append({
                'metric1':   m1,
                'metric2':   m2,
                'u_1to2':    float(r['theil_u_1to2']),
                'u_2to1':    float(r['theil_u_2to1']),
                'mi':        float(r['mi']),
                'h1':        float(r['h_metric1']),
                'h2':        float(r['h_metric2']),
                'support_N': int(r['support_N']),
                'distinct_1': int(r['distinct_1']),
                'distinct_2': int(r['distinct_2']),
            })
    return rows


def load_per_metric(rows=None, pair_scope='all'):
    """Per-metric aggregates from Theil's U data.

    pair_scope: 'all' (default), 'same' (same-category pairs only),
                'cross' (cross-category pairs only).

    Returns dict keyed by metric:
      { 'h': entropy, 'max_u_predicts': max U(metric→other),
        'max_u_predicted_by': max U(other→metric),
        'mean_u_predicts': mean, 'mean_u_predicted_by': mean,
        'n_pairs': count }
    """
    if rows is None:
        rows = load_rows()
    if pair_scope == 'same':
        rows = [r for r in rows if get_category(r['metric1']) == get_category(r['metric2'])]
    elif pair_scope == 'cross':
        rows = [r for r in rows if get_category(r['metric1']) != get_category(r['metric2'])]
    stats = defaultdict(lambda: {
        'h': 0.0,
        'predicts': [], 'predicted_by': [],
        'predicts_partners': [], 'predicted_by_partners': [],
        'best_support': -1, 'pair_h': 0.0,
    })
    for r in rows:
        m1, m2 = r['metric1'], r['metric2']
        n = r['support_N']
        # u_1to2 = MI/H(m1): how well m1 predicts m2
        # u_2to1 = MI/H(m2): how well m2 predicts m1
        stats[m1]['predicts'].append(r['u_1to2'])
        stats[m1]['predicts_partners'].append(m2)
        stats[m1]['predicted_by'].append(r['u_2to1'])
        stats[m1]['predicted_by_partners'].append(m2)
        stats[m2]['predicts'].append(r['u_2to1'])
        stats[m2]['predicts_partners'].append(m1)
        stats[m2]['predicted_by'].append(r['u_1to2'])
        stats[m2]['predicted_by_partners'].append(m1)
        if n > stats[m1]['best_support']:
            stats[m1]['best_support'] = n
            stats[m1]['pair_h'] = r['h1']
        if n > stats[m2]['best_support']:
            stats[m2]['best_support'] = n
            stats[m2]['pair_h'] = r['h2']

    result = {}
    for m, s in stats.items():
        if s['predicts']:
            max_pred_i = max(range(len(s['predicts'])), key=lambda i: s['predicts'][i])
            max_pred_by_i = max(range(len(s['predicted_by'])), key=lambda i: s['predicted_by'][i])
        else:
            max_pred_i = max_pred_by_i = None
        result[m] = {
            'h': s['pair_h'],
            'max_u_predicts': s['predicts'][max_pred_i] if max_pred_i is not None else 0,
            'max_u_predicts_partner': s['predicts_partners'][max_pred_i] if max_pred_i is not None else '',
            'max_u_predicted_by': s['predicted_by'][max_pred_by_i] if max_pred_by_i is not None else 0,
            'max_u_predicted_by_partner': s['predicted_by_partners'][max_pred_by_i] if max_pred_by_i is not None else '',
            'mean_u_predicts': sum(s['predicts']) / len(s['predicts']) if s['predicts'] else 0,
            'mean_u_predicted_by': sum(s['predicted_by']) / len(s['predicted_by']) if s['predicted_by'] else 0,
            'n_pairs': len(s['predicts']),
        }
    return result


# ── Per-metric entropy/HHI from analyze.py output ────────────────────────────

_ANALYZE_DIR = Path(os.environ.get('THEIL_ANALYZE_DIR', '')) if os.environ.get('THEIL_ANALYZE_DIR') else None


def load_true_entropy():
    if not _ANALYZE_DIR:
        return {}
    p = _ANALYZE_DIR / 'metric_shannon_entropy.csv'
    if not p.exists():
        return {}
    entropy = {}
    with open(p) as f:
        for r in csv.DictReader(f):
            entropy[r['Metric']] = float(r['Entropy'])
    return entropy


def load_true_hhi():
    if not _ANALYZE_DIR:
        return {}
    p = _ANALYZE_DIR / 'metric_hhi.csv'
    if not p.exists():
        return {}
    hhi = {}
    with open(p) as f:
        for r in csv.DictReader(f):
            hhi[r['Metric']] = float(r['HHI'])
    return hhi
