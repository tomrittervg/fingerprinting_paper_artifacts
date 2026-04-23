"""Shared data-loading functions for viz_minset scripts.

Not intended to be run directly.
"""

import csv
import os
import re


def _load_combo_csv_from_path(path):
    """Load a min_set_combos CSV file → list of dicts.

    Each dict: {combo_name, combo_size, combo_unique, combo_only_unique_new,
                metrics (list of str)}
    Sorted by combo_size asc, combo_only_unique_new desc.
    """
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            rows.append({
                'combo_name': r['ComboName'],
                'combo_size': int(r['ComboSize']),
                'combo_unique': int(r['ComboUnique']),
                'combo_only_unique_new': int(r['ComboOnlyUniqueNew']),
                'metrics': r['ComboName'].split('+'),
            })
    rows.sort(key=lambda r: (r['combo_size'], -r['combo_only_unique_new']))
    return rows


def load_combo_csv(output_dir):
    """Load min_set_combos.csv from output_dir."""
    return _load_combo_csv_from_path(os.path.join(output_dir, 'min_set_combos.csv'))


def _load_dedup_csv_from_path(path):
    """Load a min_set_combos_dedup CSV file → list of dicts.

    Each dict: {combo_size, new_users, cumulative_total}
    Sorted by combo_size asc.
    """
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            rows.append({
                'combo_size': int(r['ComboSize']),
                'new_users': int(r['NewUsersIdentified']),
                'cumulative_total': int(r['CumulativeTotal']),
            })
    rows.sort(key=lambda r: r['combo_size'])
    return rows


def load_dedup_csv(output_dir):
    """Load min_set_combos_dedup.csv from output_dir."""
    return _load_dedup_csv_from_path(os.path.join(output_dir, 'min_set_combos_dedup.csv'))


def discover_os_variants(output_dir):
    """Find per-OS CSV files and return {os_name: (combo_rows, dedup_rows)}.

    Looks for min_set_combos_os_<NAME>.csv and min_set_combos_dedup_os_<NAME>.csv.
    Returns empty dict if no per-OS files exist.
    """
    variants = {}
    for fname in os.listdir(output_dir):
        m = re.match(r'min_set_combos_os_(.+)\.csv$', fname)
        if m:
            os_name = m.group(1)
            if os_name not in variants:
                variants[os_name] = [None, None]
            variants[os_name][0] = _load_combo_csv_from_path(
                os.path.join(output_dir, fname))
    for fname in os.listdir(output_dir):
        m = re.match(r'min_set_combos_dedup_os_(.+)\.csv$', fname)
        if m:
            os_name = m.group(1)
            if os_name not in variants:
                variants[os_name] = [None, None]
            variants[os_name][1] = _load_dedup_csv_from_path(
                os.path.join(output_dir, fname))
    # Convert to tuples, defaulting missing data to []
    return {name: (combo or [], dedup or [])
            for name, (combo, dedup) in sorted(variants.items())}


def load_run_metadata(output_dir):
    """Extract metadata from run.log or min_set_combos.txt if available."""
    meta = {'total_users': 0, 'unique_users': 0, 'label': os.path.basename(output_dir)}

    # Try to get total/unique users from alldata CSV
    for fname in os.listdir(output_dir):
        if fname.startswith('All-Data-') and fname.endswith('.csv'):
            path = os.path.join(output_dir, fname)
            with open(path, newline='') as f:
                rows = list(csv.reader(f))
            if len(rows) >= 2:
                num_unique = int(rows[1][1])
                pct = float(rows[1][2])
                if pct > 0:
                    meta['total_users'] = round(num_unique / (pct / 100))
                    meta['unique_users'] = num_unique
                    meta['fp_name'] = fname[len('All-Data-'):-len('.csv')]
            break

    # Also try the txt file for unique baseline
    txt_path = os.path.join(output_dir, 'min_set_combos.txt')
    unique_from_txt = parse_unique_baseline_from_txt(txt_path)
    if unique_from_txt and not meta['unique_users']:
        meta['unique_users'] = unique_from_txt

    return meta


def load_metadata_from_os_txt(metadata_dir):
    """Parse os.txt from a metadata directory to get per-OS and total user counts.

    Returns {'total_users': int, 'os_users': {os_name: int}}.
    """
    import sys
    path = os.path.join(metadata_dir, 'os.txt')
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found", file=sys.stderr)
        return {'total_users': 0, 'os_users': {}}

    os_users = {}
    with open(path) as f:
        for line in f:
            m = re.match(r'\s+(\S+)\s+(\d+)\s+[\d.]+\s+[\d.]+', line)
            if m:
                os_name, count = m.group(1), int(m.group(2))
                if os_name not in ('Key',):
                    os_users[os_name] = count

    total = sum(os_users.values())
    print(f"  metadata-dir: {os.path.basename(metadata_dir)}/ → "
          f"{total:,} total users across {len(os_users)} OSes "
          f"({', '.join(f'{k}={v:,}' for k, v in sorted(os_users.items()))})")
    return {'total_users': total, 'os_users': os_users}


def parse_unique_baseline_from_txt(txt_path):
    """Parse 'Unique users (baseline): N (X%)' from a min_set_combos txt file.

    Returns the integer count, or None if not found.
    """
    if not os.path.exists(txt_path):
        return None
    with open(txt_path) as f:
        for line in f:
            m = re.search(r'Unique users \(baseline\):\s+([\d,]+)', line)
            if m:
                return int(m.group(1).replace(',', ''))
    return None


def parse_total_users_from_txt(txt_path):
    """Parse 'Total users: N' from a min_set_combos txt file.

    Returns the integer count, or None if not found.
    """
    if not os.path.exists(txt_path):
        return None
    with open(txt_path) as f:
        for line in f:
            m = re.search(r'Total users:\s+([\d,]+)', line)
            if m:
                return int(m.group(1).replace(',', ''))
    return None


def extract_top_n(dirname):
    """Extract the top-N value from a minset directory name.

    e.g. 'minset_top5_smr_0412_1775989080' → 5
    Returns None if not found.
    """
    m = re.search(r'top(\d+)', os.path.basename(dirname))
    return int(m.group(1)) if m else None
