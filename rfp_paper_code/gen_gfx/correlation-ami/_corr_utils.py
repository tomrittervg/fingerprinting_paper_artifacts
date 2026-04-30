"""Shared utilities for correlation visualization scripts."""
import os
os.environ.setdefault('MPLCONFIGDIR', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mpl'))

import csv
import sys
from pathlib import Path
from collections import defaultdict

from _pair_rules import is_valid_metric_pair_for_comparison

# Load authoritative metric→category mapping from script-configs/
_SCRIPT_CONFIGS = Path(__file__).parents[3] / 'code' / 'configs'
sys.path.insert(0, str(_SCRIPT_CONFIGS))
from metadata_metric_categories import METRIC_CATEGORIES, CATEGORY_ORDER, CATEGORY_COLORS
sys.path.pop(0)

HERE = Path(os.environ.get('CORR_OUT_DIR', Path(__file__).parent))
_csv_default = Path(__file__).parent / 'ami_threshold_30.csv'
CSV_PATH = Path(os.environ.get('CORR_CSV', _csv_default))

# ── Usage check ───────────────────────────────────────────────────────────────
if not CSV_PATH.exists():
    print(f"""\
Error: CSV file not found: {CSV_PATH}

Usage: set environment variables before running any corr_*.py script.

  Required:
    CORR_CSV=path/to/ami_threshold_30.csv    Pairwise AMI data file

  Optional:
    CORR_OUT_DIR=path/to/output/             Output directory (default: script dir)
    CORR_FILTER=phase2                       Metric filter:
                                               phase2       — phase2 allowlist only
                                               nowebglparams — drop individual WebGL params
                                               noparams      — also drop individual math ops
                                               allfp         — AllFingerprinters set only
    CORR_ALLOWLIST=path/to/mapping.txt       Restrict to listed metrics (3-col format)
    CORR_ANALYZE_DIR=path/to/analyze/out/    analyze.py output dir with
                                               metric_shannon_entropy.csv
                                               metric_hhi.csv

  Per-script:
    CORR_THRESHOLD=0.6    (corr_all_heatmap_v1.py) only metrics with max AMI >= threshold
    CORR_LOWER_ONLY=1     (corr_all_heatmap_v1.py) blank upper triangle (mirror of lower)
""", file=sys.stderr)
    sys.exit(1)

# ── Optional filters ──────────────────────────────────────────────────────────
# CORR_FILTER env var controls which individual-param metrics are dropped.
#
#   nowebglparams  — drop individual WebGL params; keep JSON dumps
#   noparams       — also drop individual math ops; keep aggregate math_ops* metrics
#
# Suffix is appended to each output PNG filename.

_FILTER = os.environ.get('CORR_FILTER', '')
EXCLUDE_WEBGL_PARAMS   = _FILTER in ('nowebglparams', 'noparams', 'allfp')
EXCLUDE_MATH_OPS       = _FILTER in ('noparams', 'allfp')
EXCLUDE_CSS_COLORS     = _FILTER in ('allfp',)
RESTRICT_TO_ALLFP      = _FILTER == 'allfp'
FILTER_SUFFIX          = f'_{_FILTER}' if _FILTER else ''

# Load AllFingerprinters allowlist from the mapping file's phase2fp column
_MAPPING_FILE = Path(__file__).parents[3] / 'code' / 'configs' / 'metadata_metric_name_mapping.txt'
_ALLFP_ALLOWLIST: set | None = None
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

# CORR_ALLOWLIST: path to a plain-text file (one metric per line) that restricts
# which metrics appear in the output, regardless of CORR_FILTER.
_ALLOWLIST_PATH = os.environ.get('CORR_ALLOWLIST', '')
_CUSTOM_ALLOWLIST: set | None = None
if _ALLOWLIST_PATH:
    with open(_ALLOWLIST_PATH) as _f:
        _raw = [line.strip() for line in _f if line.strip() and not line.startswith('#')]
    # Format: datavalues_name  db_name  phase2fp  combination_metric  (metadata_metric_name_mapping.txt)
    # "~name" in the db_name position means absent from this CSV run — skip.
    _parsed = []
    for line in _raw:
        parts = line.split()
        name = parts[1] if len(parts) >= 2 else parts[0]
        if not name.startswith('~'):
            _parsed.append(name)
    _CUSTOM_ALLOWLIST = set(_parsed)


def is_webgl_individual_param(m):
    """True for individual WebGL parameter metrics that should be excluded."""
    if m.startswith('webgl_params_'):
        return True   # all webgl1 individual params (none have _json suffix)
    if m.startswith('webgl2_params_') and not m.endswith(('_json', '_sw_json')):
        return True   # individual webgl2 params, but keep the JSON dumps
    return False


def is_css_individual_color(m):
    """True for individual css_color_* metrics (combined hash not in data)."""
    return m.startswith('css_color_')


def is_math_individual_op(m):
    """True for individual math operation metrics (math_op_N / math_op_diag_N etc.).

    Keeps aggregate metrics: math_ops, math_ops_json, math_ops_diag_json,
    math_ops_fdlibm, math_ops_fdlibm_json, math_ops_fdlibm_2.
    Those all start with 'math_ops' (plural); individuals start with 'math_op_'.
    """
    return m.startswith('math_op_')  # singular op + underscore, not math_ops*

# ── Category assignment ────────────────────────────────────────────────────────
# CATEGORY_ORDER, CATEGORY_COLORS, and METRIC_CATEGORIES are all defined in
# configs/metric_categories.py and imported above.
#
# Build a DB-name → DataValues-name lookup so we can resolve DB names
# (used in per-OS correlation CSVs) to categories.
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
    # Try resolving DB name → DataValues name
    dv_name = _DB_TO_DV.get(m)
    if dv_name is not None:
        cat = METRIC_CATEGORIES.get(dv_name)
        if cat is not None:
            return cat
    return 'Other'


# ── Per-metric entropy and HHI ─────────────────────────────────────────────────
# CORR_ANALYZE_DIR: path to an analyze.py output folder containing
#   metric_shannon_entropy.csv  (columns: Metric, Entropy)
#   metric_hhi.csv              (columns: Metric, HHI)
# If set, these files are used directly instead of x_tbl.csv.

_ANALYZE_DIR = Path(os.environ.get('CORR_ANALYZE_DIR', '')) if os.environ.get('CORR_ANALYZE_DIR') else None


def load_true_entropy():
    """Load true marginal entropy (bits) per metric.

    Source: CORR_ANALYZE_DIR/metric_shannon_entropy.csv (Metric, Entropy).
    Returns {} if CORR_ANALYZE_DIR is not set.
    """
    if not _ANALYZE_DIR:
        return {}
    entropy = {}
    with open(_ANALYZE_DIR / 'metric_shannon_entropy.csv') as f:
        for r in csv.DictReader(f):
            entropy[r['Metric']] = float(r['Entropy'])
    return entropy


def load_true_hhi():
    """Load Herfindahl-Hirschman Index per metric.

    HHI = sum(p_i^2).  Ranges from 1/n (perfectly uniform) to 1.0 (all one value).
    Low HHI → spread-out distribution (informative metric).
    High HHI → one value dominates (uninformative metric).
    Source: CORR_ANALYZE_DIR/metric_hhi.csv (Metric, HHI).
    Returns {} if CORR_ANALYZE_DIR is not set.
    """
    if not _ANALYZE_DIR:
        return {}
    hhi = {}
    with open(_ANALYZE_DIR / 'metric_hhi.csv') as f:
        for r in csv.DictReader(f):
            hhi[r['Metric']] = float(r['HHI'])
    return hhi


# ── CSV loading helpers ────────────────────────────────────────────────────────

def load_rows():
    """Return list of dicts from the AMI CSV, honouring active filters."""
    rows = []
    with open(CSV_PATH) as f:
        for r in csv.DictReader(f):
            m1, m2 = r['metric1'], r['metric2']
            if EXCLUDE_WEBGL_PARAMS and (
                is_webgl_individual_param(m1) or is_webgl_individual_param(m2)
            ):
                continue
            if EXCLUDE_MATH_OPS and (
                is_math_individual_op(m1) or is_math_individual_op(m2)
            ):
                continue
            if EXCLUDE_CSS_COLORS and (
                is_css_individual_color(m1) or is_css_individual_color(m2)
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
                'metric1':   r['metric1'],
                'metric2':   r['metric2'],
                'ami':       float(r['ami']),
                'h1':        float(r['h_metric1']),
                'h2':        float(r['h_metric2']),
                'support_N': int(r['support_N']),
            })
    return rows


def load_per_metric(rows=None):
    """Return dicts keyed by metric name: entropy and max_ami.

    Entropy source (in priority order):
      1. True marginal H from x_tbl.csv if CORR_XTBL is set — preferred.
      2. Pair-derived H from the highest-support_N pair in the AMI CSV — fallback.
    """
    if rows is None:
        rows = load_rows()
    true_entropy = load_true_entropy()
    best_support = {}
    pair_entropy = {}
    max_ami = defaultdict(float)
    for r in rows:
        m1, m2 = r['metric1'], r['metric2']
        n = r['support_N']
        if n > best_support.get(m1, -1):
            best_support[m1] = n
            pair_entropy[m1] = r['h1']
        if n > best_support.get(m2, -1):
            best_support[m2] = n
            pair_entropy[m2] = r['h2']
        max_ami[m1] = max(max_ami[m1], r['ami'])
        max_ami[m2] = max(max_ami[m2], r['ami'])
    # Merge: prefer true entropy where available, but only for metrics that
    # appeared in at least one filtered pair (pair_entropy keys).
    entropy = {m: true_entropy.get(m, h) for m, h in pair_entropy.items()}
    return entropy, max_ami
