#!/usr/bin/env python3
"""Generate EXPERIMENTS_TO_RUN, EXPERIMENTS_TO_RUN_ADDITIVE, and
EXPERIMENT_LONG_NAMES from experiments.csv.

Usage:
    python3 gen_experiments.py [experiments.csv]   # print Python to stdout

Also importable:
    from gen_experiments import generate_experiments
    exp, additive, long_names, meta = generate_experiments('experiments.csv')
"""

import csv
import re
import sys
from pathlib import Path


def _slugify(name):
    """Convert a short experiment name to a filename-safe slug component."""
    return re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')


# ── Filter discovery ─────────────────────────────────────────────────────────

def _discover_known_filters():
    """Return the set of filter class names available in experiments.py."""
    try:
        import experiments as _exp
    except ImportError:
        return set()
    return {
        name for name in dir(_exp)
        if isinstance(getattr(_exp, name, None), type)
        and name[0].islower()
    }


_known_filters_cache = None

def _get_known_filters():
    global _known_filters_cache
    if _known_filters_cache is None:
        _known_filters_cache = _discover_known_filters()
    return _known_filters_cache


# ── CSV parsing ──────────────────────────────────────────────────────────────

def _parse_csv(csv_path):
    """Parse experiments.csv into a list of row dicts."""
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            phase = r['phase'].strip()
            visible = int(r['visible'].strip())
            ic = r['ic'].strip().lower()
            short_name = r['short_name'].strip()
            long_name = r.get('long_name', '').strip()
            filters_str = r['filters'].strip()
            filters = [f.strip() for f in filters_str.split('|') if f.strip()]

            known = _get_known_filters()
            if known:
                for filt in filters:
                    if filt not in known:
                        raise ValueError(f"Unknown filter '{filt}' in row: {r}")
            if ic not in ('i', 'c', 'ic'):
                raise ValueError(f"Invalid ic value '{ic}' in row: {r}")

            if not short_name:
                short_name = ', '.join(filters)
            if not long_name:
                long_name = short_name

            rows.append({
                'phase': phase,
                'visible': visible,
                'ic': ic,
                'short_name': short_name,
                'long_name': long_name,
                'filters': filters,
            })
    return rows


# ── Filter resolution ────────────────────────────────────────────────────────

def _resolve_filters(experiments, filter_map):
    """Replace filter name strings with actual filter objects."""
    return {name: [filter_map[f] for f in flist]
            for name, flist in experiments.items()}


def _resolve_additive(additive, filter_map):
    """Replace filter name strings with actual filter objects in additive list."""
    return [{name: [filter_map[f] for f in flist]
             for name, flist in d.items()}
            for d in additive]


# ── Main generator ───────────────────────────────────────────────────────────

def generate_experiments(csv_path, resolve=True):
    """Generate experiment data structures from CSV.

    Returns:
        experiments_to_run: dict {short_key: [filters]}
        experiments_to_run_additive: list of [ordered_dict]
        experiment_long_names: dict {short_key: long_name_string}
        metadata: dict with 'commented_out' and 'rows'
    """
    rows = _parse_csv(csv_path)

    p0_rows = [r for r in rows if r['phase'] == '0']
    p1plus_rows = [r for r in rows if r['phase'] not in ('0', 'Z')]
    pz_rows = [r for r in rows if r['phase'] == 'Z']

    all_p0_filters = []
    for r in p0_rows:
        all_p0_filters.extend(r['filters'])

    experiments_to_run = {}
    long_names = {}
    commented_out = []

    # Slug map: {exp_key: "C-PX-NN-Short_Name"} for ALL experiments (active + commented-out).
    # Equivalents: {commented_out_key: active_key} — only where there is an active equivalent.
    slug_map = {}
    equivalents = {}
    _global_n = [0]   # mutable counter for EXPERIMENTS_TO_RUN ordering
    _phase_n  = {}    # per-phase counter for additive cumulative

    def _slug_etr(key, ic_char, phase, short_name):
        """Assign next global-N slug for an EXPERIMENTS_TO_RUN entry."""
        _global_n[0] += 1
        c = 'C' if ic_char == 'c' else 'I'
        slug_map[key] = f"{c}-P{phase}-{_global_n[0]:02d}-{_slugify(short_name)}"

    def _slug_additive(key, phase, short_name):
        """Assign per-phase-N slug for an additive cumulative entry."""
        _phase_n.setdefault(phase, 0)
        _phase_n[phase] += 1
        slug_map[key] = f"C-P{phase}-{_phase_n[phase]:02d}-{_slugify(short_name)}"

    # ── Baseline-Raw: equivalent to All-Data (raw values already baked in) ──
    baseline_key = 'Baseline-Raw'
    long_names[baseline_key] = 'Baseline-Raw'
    slug_map[baseline_key] = 'C-P0-00-Baseline-Raw'
    equivalents[baseline_key] = 'All-Data'
    commented_out.append((baseline_key, [], 'Baseline-Raw',
                          'identical to All-Data (Phase 0 filters baked into range cache)', 'All-Data'))

    # ── Phase 0 individual (each applies one inverse/protection filter) ──
    for r in p0_rows:
        if 'i' in r['ic']:
            key = f"P0-I: {r['short_name']}"
            experiments_to_run[key] = list(r['filters'])
            long_names[key] = f"P0-I: {r['long_name']}"
            _slug_etr(key, 'i', '0', r['short_name'])

    # ── Phase 1+ individual ──
    first_in_phase = {}
    for r in p1plus_rows:
        if r['phase'] not in first_in_phase and 'c' in r['ic']:
            first_in_phase[r['phase']] = r['short_name']

        if 'i' in r['ic']:
            key = f"P{r['phase']}-I: {r['short_name']}"
            long = f"P{r['phase']}-I: {r['long_name']}"
            _slug_etr(key, 'i', r['phase'], r['short_name'])
            experiments_to_run[key] = list(r['filters'])
            long_names[key] = long

    # ── Phase Z individual ──
    for r in pz_rows:
        key = f"PZ-I: {r['short_name']}"
        experiments_to_run[key] = list(r['filters'])
        long_names[key] = f"PZ-I: {r['long_name']}"
        _slug_etr(key, 'i', 'Z', r['short_name'])

    # ── EXPERIMENTS_TO_RUN_ADDITIVE: Phase 0 (additive protection) + Phase 1+ cumulative ──
    additive_dict = {}
    cumulative_names = []

    # Phase 0 cumulative: each step adds one more protection filter
    for r in p0_rows:
        if 'c' not in r['ic']:
            continue
        cumulative_names.append(r['long_name'])
        key = f"P0-C: {r['short_name']}"
        long = f"P0-C: {', '.join(cumulative_names)}"
        additive_dict[key] = list(r['filters'])
        long_names[key] = long
        _slug_additive(key, '0', r['short_name'])

    # Phase 1+ cumulative: each step adds one more experiment filter
    prev_phase = '0'
    for r in p1plus_rows:
        if 'c' not in r['ic']:
            continue
        # When entering a new phase, collapse prior phases into "P{n}"
        if r['phase'] != prev_phase:
            cumulative_names = [f"P{prev_phase}"]
        cumulative_names.append(r['long_name'])
        prev_phase = r['phase']

        key = f"P{r['phase']}-C: {r['short_name']}"
        long = f"P{r['phase']}-C: {', '.join(cumulative_names)}"
        additive_dict[key] = list(r['filters'])
        long_names[key] = long
        _slug_additive(key, r['phase'], r['short_name'])

    experiments_to_run_additive = [additive_dict]

    # Resolve filter name strings to actual filter objects
    if resolve:
        import experiments as exp_module
        known = _get_known_filters()
        filter_map = {name: getattr(exp_module, name) for name in known}
        experiments_to_run = _resolve_filters(experiments_to_run, filter_map)
        experiments_to_run_additive = _resolve_additive(experiments_to_run_additive, filter_map)

    return experiments_to_run, experiments_to_run_additive, long_names, {
        'commented_out': commented_out,
        'rows': rows,
        'slug_map': slug_map,
        'equivalents': equivalents,
    }


def build_metric_experiments(experiments_to_run, experiments_to_run_additive):
    """Auto-build METRIC_EXPERIMENTS_BY_KEY from filter affected_metrics().

    For each experiment (individual and additive), unions the affected_metrics()
    of all its filters. Returns {experiment_key: [metric_names]}.
    Only includes experiments that affect at least one metric.
    """
    result = {}
    all_experiments = dict(experiments_to_run)
    for d in experiments_to_run_additive:
        all_experiments.update(d)
    for key, filters in all_experiments.items():
        metrics = []
        seen = set()
        for f in filters:
            for m in f.affected_metrics():
                if m not in seen:
                    seen.add(m)
                    metrics.append(m)
        if metrics:
            result[key] = metrics
    return result


# ── CLI output ───────────────────────────────────────────────────────────────

def _format_filter_list(filters):
    if not filters:
        return '[]'
    if len(filters) == 1:
        return f'[{filters[0]}]'
    return '[' + ', '.join(filters) + ']'


def print_python(csv_path):
    """Print all three exported data structures as Python."""
    exp, additive, long_names, meta = generate_experiments(csv_path, resolve=False)

    # Collect all filter names used
    all_filters = set()
    for flist in exp.values():
        all_filters.update(flist)
    for d in additive:
        for flist in d.values():
            all_filters.update(flist)
    for _, flist, _, _ in meta['commented_out']:
        all_filters.update(flist)

    print("from experiments import (")
    for f in sorted(all_filters):
        print(f"    {f},")
    print(")")
    print()

    # ── EXPERIMENTS_TO_RUN ──
    print("EXPERIMENTS_TO_RUN = {")
    for name, filters in exp.items():
        print(f"    {name!r}: {_format_filter_list(filters)},")
    if meta['commented_out']:
        print()
        print("    # ── Commented-out duplicates ──")
        for name, filters, _, reason in meta['commented_out']:
            print(f"    # {name!r}: {_format_filter_list(filters)},  # {reason}")
    print("}")
    print()

    # ── EXPERIMENTS_TO_RUN_ADDITIVE ──
    print("EXPERIMENTS_TO_RUN_ADDITIVE = [")
    for d in additive:
        print("    {")
        for name, filters in d.items():
            print(f"        {name!r}: {_format_filter_list(filters)},")
        print("    },")
    print("]")
    print()

    # ── EXPERIMENT_LONG_NAMES ──
    print("EXPERIMENT_LONG_NAMES = {")
    for key, long in long_names.items():
        if key == long:
            continue  # skip trivial mappings to reduce clutter
        print(f"    {key!r}:")
        print(f"        {long!r},")
    if meta['commented_out']:
        for name, _, long, reason in meta['commented_out']:
            print(f"    # {name!r}:")
            print(f"    #     {long!r},  # {reason}")
    print("}")
    print()

    # ── Summary ──
    print(f"# {len(meta['rows'])} experiments parsed from CSV")
    print(f"# {len(exp)} in EXPERIMENTS_TO_RUN")
    print(f"# {sum(len(d) for d in additive)} in EXPERIMENTS_TO_RUN_ADDITIVE")
    print(f"# {len(long_names)} in EXPERIMENT_LONG_NAMES")
    print(f"# {len(meta['commented_out'])} commented-out duplicates")


def main():
    csv_path = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            csv_path = arg
            break

    if csv_path is None:
        default = Path(__file__).parent / 'experiments.csv'
        if default.exists():
            csv_path = str(default)
        else:
            print(f"Usage: {sys.argv[0]} [experiments.csv]", file=sys.stderr)
            sys.exit(1)

    try:
        print_python(csv_path)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
