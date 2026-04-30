#!/usr/bin/env python3
"""Correlation analysis: Adjusted Mutual Information (AMI) and Theil's U.

Standalone script that:
  1. Downloads and caches contingency data from BigQuery (per-metric1 .npy files)
  2. Computes AMI (with optional rare-value binning and Miller-Madow correction)
  3. Computes Theil's U (asymmetric, both directions per pair)

Usage:
  # Cache only (download data, no analysis):
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \\
  ./correlation.py --cache-dir /work/sandbox-cache -c configs/paper_correlation.py --cache-only

  # Full run (cache + analyze):
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \\
  ./correlation.py --cache-dir /work/sandbox-cache -c configs/paper_correlation.py \\
    -o /home/sandbox/tmp

Can also be invoked from analyze.py when correlation_analysis or
correlation_cache_only is True in script_config.
"""

import argparse
import csv
import json
import os
import pickle
import shutil
import sys
import time
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import numpy as np

from progress import ProgressDisplay
from settings import BQ_PROJECT_ID

# ---------------------------------------------------------------------------
# Per-OS cache directory helper
# ---------------------------------------------------------------------------

def _correlation_cache_dir(cache_dir, bq_table=None):
    """Return the per-OS correlation cache directory.

    Derives the OS suffix from the BQ table name (e.g.
    '...UserCharacteristics_Windows_x_by_y_tbl' -> 'correlation_Windows').
    Falls back to 'correlation' if no OS suffix is found.
    """
    os_suffix = ""
    if bq_table:
        tbl_name = bq_table.rsplit(".", 1)[-1]
        for tag in ("_Windows", "_Mac", "_Linux", "_Android", "_All"):
            if tag in tbl_name:
                os_suffix = tag
                break
    return os.path.join(cache_dir, f"correlation{os_suffix}")


# ---------------------------------------------------------------------------
# Config loading helpers
# ---------------------------------------------------------------------------

def _load_config(config_path):
    """Load a config file and return the module object."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_corr_config", config_path)
    if spec is None:
        print(f"ERROR: cannot load config file '{config_path}'", file=sys.stderr)
        sys.exit(1)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    return cfg


def _get_config(cfg_module):
    """Extract correlation-relevant settings from a loaded config module."""
    sc = cfg_module.script_config
    return {
        'bq_table':                getattr(cfg_module, 'CORRELATION_BQ_TABLE', None),
        'metric_set':              getattr(cfg_module, 'CORRELATION_METRIC_SET', None),
        'cache_only':              sc.get('correlation_cache_only', False),
        'parallel_downloads':      sc.get('correlation_parallel_downloads', 8),
        'parallel_workers':        sc.get('correlation_parallel_workers', 40),
        'missing_values':          sc.get('correlation_missing_values', {'None'}),
        'ami_enabled':             sc.get('correlation_ami', True),
        'ami_bin_rare':            sc.get('correlation_ami_bin_rare_values', True),
        'ami_bin_thresholds':      sc.get('correlation_ami_bin_thresholds', [30]),
        'ami_miller_madow':        sc.get('correlation_ami_miller_madow', False),
        'theil_u_enabled':         sc.get('correlation_theil_u', True),
    }


# =============================================================================
# Phase 1: Cache management — download contingency data from BQ
# =============================================================================

def _load_manifest(cache_dir):
    """Load manifest.json or return empty structure."""
    path = os.path.join(cache_dir, "manifest.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"bq_table": None, "all_metrics": [], "cached_metrics": {}}


def _save_manifest(cache_dir, manifest):
    """Write manifest.json atomically."""
    path = os.path.join(cache_dir, "manifest.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _save_metric_cache(pairs_dir, metric1_name, metric2_arr, value1_arr, value2_arr, n_arr):
    """Save one metric1's contingency data as .npy files."""
    d = os.path.join(pairs_dir, metric1_name)
    os.makedirs(d, exist_ok=True)

    # Encode strings as integer codes + vocabulary
    vocab_m2, codes_m2 = np.unique(metric2_arr, return_inverse=True)
    vocab_v1, codes_v1 = np.unique(value1_arr, return_inverse=True)
    vocab_v2, codes_v2 = np.unique(value2_arr, return_inverse=True)

    np.save(os.path.join(d, "metric2_codes.npy"), codes_m2.astype(np.int32))
    np.save(os.path.join(d, "value1_codes.npy"), codes_v1.astype(np.int32))
    np.save(os.path.join(d, "value2_codes.npy"), codes_v2.astype(np.int32))
    np.save(os.path.join(d, "n.npy"), n_arr.astype(np.int32))
    np.save(os.path.join(d, "vocab_metric2.npy"), vocab_m2)
    np.save(os.path.join(d, "vocab_value1.npy"), vocab_v1)
    np.save(os.path.join(d, "vocab_value2.npy"), vocab_v2)

    return len(n_arr)


def _load_metric_cache(pairs_dir, metric1_name):
    """Load one metric1's cached data. Returns (metric2[], value1[], value2[], n[])."""
    d = os.path.join(pairs_dir, metric1_name)
    codes_m2 = np.load(os.path.join(d, "metric2_codes.npy"))
    codes_v1 = np.load(os.path.join(d, "value1_codes.npy"))
    codes_v2 = np.load(os.path.join(d, "value2_codes.npy"))
    n = np.load(os.path.join(d, "n.npy"))
    vocab_m2 = np.load(os.path.join(d, "vocab_metric2.npy"), allow_pickle=True)
    vocab_v1 = np.load(os.path.join(d, "vocab_value1.npy"), allow_pickle=True)
    vocab_v2 = np.load(os.path.join(d, "vocab_value2.npy"), allow_pickle=True)
    return vocab_m2[codes_m2], vocab_v1[codes_v1], vocab_v2[codes_v2], n


def _fetch_metric_list(client, bq_table):
    """Get sorted list of all distinct metric1 values from the BQ contingency table."""
    sql = f"""
    SELECT DISTINCT metric1
    FROM `{bq_table}`
    WHERE metric1 < metric2
    ORDER BY metric1
    """
    rows = client.query(sql).result()
    return sorted(r.metric1 for r in rows)


def _fetch_metric_row_counts(client, bq_table, metrics):
    """Get estimated row counts per metric1 for balanced chunk creation."""
    placeholders = ", ".join(f"'{m}'" for m in metrics)
    sql = f"""
    SELECT metric1, COUNT(*) AS row_count
    FROM `{bq_table}`
    WHERE metric1 IN ({placeholders})
      AND metric1 < metric2
    GROUP BY metric1
    """
    rows = client.query(sql).result()
    return {r.metric1: r.row_count for r in rows}


def _create_balanced_chunks(metrics, row_counts, n_chunks):
    """Create balanced chunks using greedy bin-packing.

    Sorts metrics by row count descending, assigns each to the chunk
    with the smallest current total. Guarantees within 4/3 of optimal.
    """
    # Sort by size descending
    sized = [(m, row_counts.get(m, 0)) for m in metrics]
    sized.sort(key=lambda x: -x[1])

    chunks = [[] for _ in range(n_chunks)]
    chunk_totals = [0] * n_chunks

    for metric, size in sized:
        # Assign to lightest chunk
        min_idx = chunk_totals.index(min(chunk_totals))
        chunks[min_idx].append(metric)
        chunk_totals[min_idx] += size

    # Remove empty chunks
    chunks = [c for c in chunks if c]
    return chunks


def _download_batch(client, bq_table, metric_batch, pairs_dir, manifest, slot):
    """Download one batch of metrics from BQ and save to cache."""
    slot._start(f"Batch ({len(metric_batch)} metrics)", 2)
    slot.advance_phase("Querying BQ")

    # Build parameterized query
    placeholders = ", ".join(f"'{m}'" for m in metric_batch)
    sql = f"""
    SELECT metric1, value1, metric2, value2, SUM(occurrences) AS n
    FROM `{bq_table}` t
    WHERE metric1 IN ({placeholders})
      AND metric1 < metric2
    GROUP BY metric1, value1, metric2, value2
    """

    result = client.query(sql).result()

    # Accumulate rows per metric1
    by_metric1 = defaultdict(lambda: ([], [], [], []))
    for row in result:
        m2, v1, v2, n = by_metric1[row.metric1]
        m2.append(row.metric2)
        v1.append(row.value1)
        v2.append(row.value2)
        n.append(row.n)

    slot.advance_phase("Saving metrics", len(by_metric1))
    saved = 0
    now_str = datetime.now().isoformat(timespec='seconds')
    for i, (m1, (m2_list, v1_list, v2_list, n_list)) in enumerate(sorted(by_metric1.items())):
        nrows = _save_metric_cache(
            pairs_dir, m1,
            np.array(m2_list, dtype=object),
            np.array(v1_list, dtype=object),
            np.array(v2_list, dtype=object),
            np.array(n_list, dtype=np.int64),
        )
        manifest["cached_metrics"][m1] = {"rows": nrows, "cached_at": now_str}
        saved += 1
        slot.update_progress(i + 1)

    slot.finish()
    return saved


def ensure_cache(cache_dir, bq_table, metric_set, parallel_downloads=8,
                 force_rebuild=False, skip_progress_bars=False):
    """Download and cache contingency data from BQ for the requested metrics."""
    from google.cloud import bigquery

    corr_dir = _correlation_cache_dir(cache_dir, bq_table)
    pairs_dir = os.path.join(corr_dir, "pairs")
    os.makedirs(pairs_dir, exist_ok=True)

    manifest = _load_manifest(corr_dir)
    client = bigquery.Client(project=bq_table.split(".")[0])

    # Invalidate cache if the BQ table changed since the last run
    old_table = manifest.get("bq_table")
    if old_table and old_table != bq_table:
        n_stale = len(manifest.get("cached_metrics", {}))
        print(f"  BQ table changed ({old_table} → {bq_table}), "
              f"invalidating {n_stale} cached metrics")
        if os.path.isdir(pairs_dir):
            shutil.rmtree(pairs_dir)
            os.makedirs(pairs_dir, exist_ok=True)
        manifest = {"bq_table": None, "all_metrics": [], "cached_metrics": {}}

    # Step 1: get full metric list from BQ (or from manifest if already populated)
    if manifest.get("all_metrics") and manifest.get("bq_table") == bq_table:
        all_metrics = manifest["all_metrics"]
        print(f"Using cached metric list: {len(all_metrics)} metrics")
    else:
        print("Fetching metric list from BQ...")
        t0 = time.time()
        all_metrics = _fetch_metric_list(client, bq_table)
        print(f"  {len(all_metrics)} distinct metric1 values ({time.time() - t0:.1f}s)")
        manifest["bq_table"] = bq_table
        manifest["all_metrics"] = all_metrics

    # Step 2: determine which metrics to download
    if metric_set is not None:
        all_metrics_set = set(all_metrics)
        target_metrics = sorted(m for m in metric_set if m in all_metrics_set)
        missing = metric_set - all_metrics_set
        if missing:
            print(f"  Warning: {len(missing)} requested metrics not found in BQ: {sorted(missing)[:5]}...")
    else:
        target_metrics = all_metrics

    # Skip already-cached metrics (unless force rebuild)
    if not force_rebuild:
        cached = set(
            m for m in manifest.get("cached_metrics", {})
            if os.path.isdir(os.path.join(pairs_dir, m))
        )
        uncached = [m for m in target_metrics if m not in cached]
        if len(uncached) < len(target_metrics):
            print(f"  {len(target_metrics) - len(uncached)} metrics already cached, "
                  f"{len(uncached)} to download")
        target_metrics = uncached

    if not target_metrics:
        print("  All requested metrics are cached. Nothing to download.")
        _save_manifest(corr_dir, manifest)
        return

    # Step 3: create balanced chunks using row count estimates
    n_chunks = 3 * parallel_downloads
    print(f"  Estimating row counts for balanced chunking ({n_chunks} chunks)...")
    t0 = time.time()

    # Try to get estimates from manifest first, fall back to BQ query
    row_counts = {}
    for m in target_metrics:
        info = manifest.get("cached_metrics", {}).get(m, {})
        if "rows" in info:
            row_counts[m] = info["rows"]

    uncounted = [m for m in target_metrics if m not in row_counts]
    if uncounted:
        bq_counts = _fetch_metric_row_counts(client, bq_table, uncounted)
        row_counts.update(bq_counts)

    batches = _create_balanced_chunks(target_metrics, row_counts, n_chunks)
    batch_sizes = [sum(row_counts.get(m, 0) for m in b) for b in batches]
    print(f"  Created {len(batches)} balanced chunks "
          f"(range: {min(batch_sizes):,} – {max(batch_sizes):,} est. rows, "
          f"{time.time() - t0:.1f}s)")

    print(f"\nDownloading {len(target_metrics)} metrics in {len(batches)} chunks "
          f"({parallel_downloads} workers)...")

    display = ProgressDisplay(
        tty=sys.__stderr__,
        total_partitions=len(batches),
        enabled=False if skip_progress_bars else None,
    )
    display.start()

    total_saved = 0
    completed = 0
    t_start = time.time()

    try:
        with ThreadPoolExecutor(max_workers=parallel_downloads) as executor:
            futures = {}
            for batch_idx, batch in enumerate(batches):
                slot = display.slots[batch_idx] if batch_idx < len(display.slots) else display.slots[0]
                future = executor.submit(
                    _download_batch, client, bq_table, batch, pairs_dir, manifest, slot
                )
                futures[future] = (batch_idx, slot)

            for future in as_completed(futures):
                batch_idx, slot = futures[future]
                saved = future.result()
                total_saved += saved
                completed += 1
                display.release_slot(slot)
                # Save manifest after each batch so progress survives crashes
                _save_manifest(corr_dir, manifest)

                if skip_progress_bars:
                    ts = time.strftime("%H:%M:%S")
                    print(f"  [{ts}] Chunk {completed}/{len(batches)} done, "
                          f"{saved} metrics saved ({total_saved} total)")
    finally:
        display.stop()
        # Final save in case of partial completion
        _save_manifest(corr_dir, manifest)

    elapsed = time.time() - t_start
    print(f"  Downloaded {total_saved} metrics in {elapsed:.1f}s")


# =============================================================================
# Phase 1b: Merge per-OS caches into a combined "All" cache
# =============================================================================

def merge_os_caches(cache_dir, os_names=('Windows', 'Mac', 'Linux', 'Android')):
    """Merge per-OS correlation caches into a combined 'correlation_All' cache.

    For each metric1, loads contingency data from each OS cache, sums
    co-occurrence counts for matching (metric2, value1, value2) tuples,
    and saves the merged result. Skips metrics already merged.
    """
    import tqdm

    combined_dir = os.path.join(cache_dir, "correlation_All")
    combined_pairs = os.path.join(combined_dir, "pairs")
    os.makedirs(combined_pairs, exist_ok=True)

    combined_manifest = _load_manifest(combined_dir)
    already_merged = set(combined_manifest.get("cached_metrics", {}).keys())

    # Collect all available metrics across OS caches
    os_dirs = {}
    all_metrics = set()
    for os_name in os_names:
        os_tag = f"_{os_name}"
        corr_dir = os.path.join(cache_dir, f"correlation{os_tag}")
        manifest = _load_manifest(corr_dir)
        cached = set(manifest.get("cached_metrics", {}).keys())
        os_dirs[os_name] = (os.path.join(corr_dir, "pairs"), cached)
        all_metrics |= cached

    # Use intersection — only merge metrics available in ALL OSes
    common_metrics = all_metrics.copy()
    for os_name, (pairs_dir, cached) in os_dirs.items():
        common_metrics &= cached

    to_merge = sorted(common_metrics - already_merged)
    if not to_merge:
        print(f"  All {len(common_metrics)} metrics already merged.")
        combined_manifest["all_metrics"] = sorted(common_metrics)
        combined_manifest["bq_table"] = f"{BQ_PROJECT_ID}.aggregatedata2.UserCharacteristics_All_x_by_y_tbl"
        _save_manifest(combined_dir, combined_manifest)
        return

    print(f"  Merging {len(to_merge)} metrics across {len(os_names)} OSes "
          f"({len(already_merged)} already merged)...")

    now_str = datetime.now().isoformat(timespec='seconds')
    for m1 in tqdm.tqdm(to_merge, desc="  Merging", file=sys.stderr):
        # Load from each OS and accumulate
        combined = defaultdict(int)  # (metric2, value1, value2) -> sum(n)
        for os_name, (pairs_dir, cached) in os_dirs.items():
            if m1 not in cached:
                continue
            m2_arr, v1_arr, v2_arr, n_arr = _load_metric_cache(pairs_dir, m1)
            for i in range(len(n_arr)):
                combined[(str(m2_arr[i]), str(v1_arr[i]), str(v2_arr[i]))] += int(n_arr[i])

        if not combined:
            continue

        # Convert back to arrays
        keys = sorted(combined.keys())
        m2_out = np.array([k[0] for k in keys], dtype=object)
        v1_out = np.array([k[1] for k in keys], dtype=object)
        v2_out = np.array([k[2] for k in keys], dtype=object)
        n_out = np.array([combined[k] for k in keys], dtype=np.int64)

        nrows = _save_metric_cache(combined_pairs, m1, m2_out, v1_out, v2_out, n_out)
        combined_manifest.setdefault("cached_metrics", {})[m1] = {
            "rows": nrows, "cached_at": now_str
        }

        # Save manifest periodically
        if len(combined_manifest["cached_metrics"]) % 50 == 0:
            combined_manifest["all_metrics"] = sorted(common_metrics)
            combined_manifest["bq_table"] = f"{BQ_PROJECT_ID}.aggregatedata2.UserCharacteristics_All_x_by_y_tbl"
            _save_manifest(combined_dir, combined_manifest)

    combined_manifest["all_metrics"] = sorted(common_metrics)
    combined_manifest["bq_table"] = f"{BQ_PROJECT_ID}.aggregatedata2.UserCharacteristics_All_x_by_y_tbl"
    _save_manifest(combined_dir, combined_manifest)
    print(f"  Merged {len(to_merge)} metrics into {combined_dir}")


# =============================================================================
# Phase 2: Load cached data into memory
# =============================================================================

def load_pair_data(cache_dir, metric_set, missing_values, bq_table=None):
    """Load cached contingency data for the given metric subset.

    Returns:
        pairs: list of (metric1, metric2, value1_arr, value2_arr, n_arr)
            sorted by estimated complexity descending (heavy pairs first)
        pair_metrics: sorted list of metrics actually loaded
    """
    corr_dir = _correlation_cache_dir(cache_dir, bq_table)
    pairs_dir = os.path.join(corr_dir, "pairs")
    manifest = _load_manifest(corr_dir)

    if metric_set is None:
        metric_set = set(manifest.get("all_metrics", []))

    # Check what's cached
    cached = set(manifest.get("cached_metrics", {}).keys())
    available = sorted(metric_set & cached)
    not_cached = metric_set - cached
    if not_cached:
        print(f"  Warning: {len(not_cached)} metrics not cached: {sorted(not_cached)[:5]}...")

    print(f"  Loading {len(available)} cached metrics...")
    t0 = time.time()

    # Validate that all "available" metrics actually exist on disk
    missing_dirs = [m for m in available if not os.path.isdir(os.path.join(pairs_dir, m))]
    if missing_dirs:
        raise FileNotFoundError(
            f"{len(missing_dirs)} metric(s) listed in manifest but missing from disk: "
            f"{missing_dirs[:5]}{'...' if len(missing_dirs) > 5 else ''}. "
            f"Re-run with --force-rebuild or delete {os.path.join(corr_dir, 'manifest.json')}"
        )

    pairs = []
    import tqdm
    for m1 in tqdm.tqdm(available, desc="  Loading metrics", file=sys.stderr):
        metric2_arr, value1_arr, value2_arr, n_arr = _load_metric_cache(pairs_dir, m1)

        # Filter to only metric2 values in our set
        m2_mask = np.array([m in metric_set for m in metric2_arr], dtype=bool)
        if not m2_mask.any():
            continue

        metric2_arr = metric2_arr[m2_mask]
        value1_arr = value1_arr[m2_mask]
        value2_arr = value2_arr[m2_mask]
        n_arr = n_arr[m2_mask]

        # Filter missing values
        if missing_values:
            mv_mask = np.ones(len(n_arr), dtype=bool)
            for mv in missing_values:
                mv_mask &= (value1_arr != mv) & (value2_arr != mv)
            if not mv_mask.all():
                metric2_arr = metric2_arr[mv_mask]
                value1_arr = value1_arr[mv_mask]
                value2_arr = value2_arr[mv_mask]
                n_arr = n_arr[mv_mask]

        if len(n_arr) == 0:
            continue

        # Split by metric2 to get individual pairs
        unique_m2 = np.unique(metric2_arr)
        for m2 in unique_m2:
            pair_mask = metric2_arr == m2
            pairs.append((
                m1, str(m2),
                value1_arr[pair_mask],
                value2_arr[pair_mask],
                n_arr[pair_mask],
            ))

    # Sort by estimated complexity descending (heavy pairs first for better
    # load balancing when submitted to the thread pool)
    print(f"  Sorting {len(pairs):,} pairs by complexity...", flush=True)
    pairs.sort(key=lambda p: len(p[4]) * len(np.unique(p[2])) * len(np.unique(p[3])),
               reverse=True)

    elapsed = time.time() - t0
    pair_metrics = sorted(available)
    print(f"  Loaded {len(pairs)} pairs from {len(available)} metrics in {elapsed:.1f}s")
    return pairs, pair_metrics


# =============================================================================
# Phase 3a: AMI computation
# =============================================================================

def _bin_rare_values(value1, value2, n, threshold):
    """Collapse values with marginal count < threshold into __OTHER__.

    Returns (binned_v1, binned_v2, binned_n, raw_distinct_1, raw_distinct_2).
    """
    raw_d1 = len(np.unique(value1))
    raw_d2 = len(np.unique(value2))

    if threshold <= 0:
        return value1, value2, n, raw_d1, raw_d2

    v1 = value1.copy()
    v2 = value2.copy()
    n_arr = n.copy().astype(np.float64)

    # Vectorized binning for v1: identify all rare labels at once, replace in one pass
    v1_labels, v1_inv = np.unique(v1, return_inverse=True)
    v1_marginals = np.bincount(v1_inv, weights=n_arr)
    rare_v1 = set(v1_labels[(v1_marginals < threshold) & (v1_labels != "__OTHER__")])
    if rare_v1:
        mask = np.array([val in rare_v1 for val in v1], dtype=bool)
        v1 = v1.copy()
        v1[mask] = "__OTHER__"

    # Vectorized binning for v2
    v2_labels, v2_inv = np.unique(v2, return_inverse=True)
    v2_marginals = np.bincount(v2_inv, weights=n_arr)
    rare_v2 = set(v2_labels[(v2_marginals < threshold) & (v2_labels != "__OTHER__")])
    if rare_v2:
        mask = np.array([val in rare_v2 for val in v2], dtype=bool)
        v2 = v2.copy()
        v2[mask] = "__OTHER__"

    # Reaggregate using _build_contingency_matrix pattern (avoids string concat)
    v1_labels_new, v1_inv_new = np.unique(v1, return_inverse=True)
    v2_labels_new, v2_inv_new = np.unique(v2, return_inverse=True)
    R, C = len(v1_labels_new), len(v2_labels_new)
    contingency = np.zeros((R, C), dtype=np.float64)
    np.add.at(contingency, (v1_inv_new, v2_inv_new), n_arr)

    # Flatten back to sparse representation (only non-zero cells)
    nz = contingency > 0
    row_idx, col_idx = np.where(nz)
    binned_v1 = v1_labels_new[row_idx]
    binned_v2 = v2_labels_new[col_idx]
    binned_n = contingency[nz]

    return binned_v1, binned_v2, binned_n, raw_d1, raw_d2


def _entropy(counts):
    """Shannon entropy in bits from an array of counts."""
    N = counts.sum()
    if N == 0:
        return 0.0
    p = counts / N
    mask = p > 0
    return -np.sum(p[mask] * np.log2(p[mask]))


def _mutual_information(v1, v2, n):
    """Compute MI(X, Y) in bits from contingency arrays.

    Returns (mi, h_x, h_y, N, marginals_x, marginals_y).
    """
    n = n.astype(np.float64)
    N = n.sum()
    if N == 0:
        return 0.0, 0.0, 0.0, 0.0, np.array([]), np.array([])

    v1_labels, v1_inv = np.unique(v1, return_inverse=True)
    v2_labels, v2_inv = np.unique(v2, return_inverse=True)

    marginals_x = np.bincount(v1_inv, weights=n)
    marginals_y = np.bincount(v2_inv, weights=n)

    h_x = _entropy(marginals_x)
    h_y = _entropy(marginals_y)

    # MI = sum p_ij * log2(p_ij / (p_i * p_j))
    p_ij = n / N
    p_i = marginals_x[v1_inv] / N
    p_j = marginals_y[v2_inv] / N
    p_exp = p_i * p_j

    mask = p_ij > 0
    mi = np.sum(p_ij[mask] * np.log2(p_ij[mask] / p_exp[mask]))
    mi = max(0.0, float(mi))  # guard against floating-point noise

    return mi, h_x, h_y, N, marginals_x, marginals_y


def _build_contingency_matrix(v1, v2, n):
    """Build a dense contingency matrix from sparse (v1, v2, n) arrays.

    Returns (contingency_matrix, v1_labels, v2_labels).
    """
    v1_labels, v1_inv = np.unique(v1, return_inverse=True)
    v2_labels, v2_inv = np.unique(v2, return_inverse=True)
    R, C = len(v1_labels), len(v2_labels)
    contingency = np.zeros((R, C), dtype=np.int64)
    np.add.at(contingency, (v1_inv, v2_inv), n.astype(np.int64))
    return contingency, v1_labels, v2_labels


def _precompute_gammaln_table(max_n):
    """Precompute gammaln(0..max_n+1) lookup table.

    This table is shared across all pairs in a run, avoiding redundant
    recomputation.  For N=11M, costs 0.13s and 88 MB.
    """
    from scipy.special import gammaln
    return gammaln(np.arange(max_n + 2, dtype=np.float64))


def _expected_mi(contingency, N, gln_table=None):
    """Compute E[MI] with memoized inner loops and precomputed gammaln table.

    The EMI formula sums over all cells (i,j) of the contingency matrix,
    and for each cell sums over a range of nij values (the hypergeometric
    support).  The inner nij sum depends ONLY on the marginals (a_i, b_j, N),
    not on which cell (i,j) it is.  Many cells share the same marginals,
    especially after binning (e.g. hundreds of GL renderer strings each with
    count=1 after binning all have the same marginal).

    This implementation:
      1. Uses a precomputed gammaln lookup table (eliminates lgamma calls).
         If gln_table is None, builds one (slower — use shared table).
      2. Groups cells by unique (a_i, b_j) pairs
      3. Computes the nij inner loop once per unique pair (numpy-vectorized)
      4. Multiplies by the cell count sharing that pair

    For the worst pair (canvasdata12 x gl_renderer_raw on 11M users):
      R*C = 46.6M cells, but only 2.7M unique marginal pairs (5.8%)
      -> 17x fewer inner loop evaluations
    """
    R, C = contingency.shape
    a = np.ravel(contingency.sum(axis=1).astype(np.int64))
    b = np.ravel(contingency.sum(axis=0).astype(np.int64))
    N = int(N)

    if len(a) <= 1 or len(b) <= 1:
        return 0.0

    # Use shared table if provided, otherwise build one
    if gln_table is not None and len(gln_table) >= N + 2:
        gln = gln_table
    else:
        from scipy.special import gammaln
        gln = gammaln(np.arange(N + 2, dtype=np.float64))

    # Precompute log lookup for nij values
    max_nij = int(max(np.max(a), np.max(b))) + 1
    log_nij = np.zeros(max_nij + 1, dtype=np.float64)
    log_nij[1:] = np.log(np.arange(1, max_nij + 1, dtype=np.float64))

    log_N = np.log(N)
    gln_N1 = gln[N + 1]

    # --- Unique marginals and their multiplicities ---
    unique_a, counts_a = np.unique(a, return_counts=True)
    unique_b, counts_b = np.unique(b, return_counts=True)

    # Precompute per-marginal constants
    gln_ua = gln[unique_a + 1]
    gln_Nua = gln[N - unique_a + 1]
    log_ua = np.log(unique_a.astype(np.float64))
    # Guard log(0) for zero marginals (shouldn't happen but be safe)
    log_ua[unique_a == 0] = 0.0

    gln_ub = gln[unique_b + 1]
    gln_Nub = gln[N - unique_b + 1]
    log_ub = np.log(unique_b.astype(np.float64))
    log_ub[unique_b == 0] = 0.0

    # --- Memoized double loop over unique marginal pairs ---
    emi = 0.0
    for ia in range(len(unique_a)):
        a_val = int(unique_a[ia])
        if a_val == 0:
            continue
        ca = int(counts_a[ia])
        g_a = gln_ua[ia]
        g_Na = gln_Nua[ia]
        l_a = log_ua[ia]
        fixed_a = g_a + g_Na

        for ib in range(len(unique_b)):
            b_val = int(unique_b[ib])
            if b_val == 0:
                continue

            start = max(1, a_val + b_val - N)
            end = min(a_val, b_val) + 1
            if start >= end:
                continue

            multiplicity = ca * int(counts_b[ib])

            # Vectorized nij inner loop
            nij = np.arange(start, end, dtype=np.int64)

            term1 = nij / N
            term2 = log_N + log_nij[nij] - l_a - log_ub[ib]

            g = (fixed_a + gln_ub[ib] + gln_Nub[ib]
                 - gln[nij + 1] - gln_N1
                 - gln[a_val - nij + 1]
                 - gln[b_val - nij + 1]
                 - gln[N - a_val - b_val + nij + 1])
            term3 = np.exp(g)

            contribution = np.sum(term1 * term2 * term3)
            emi += multiplicity * contribution

    # Return in bits (sklearn convention is nats; we use log not log2 above,
    # so result is in nats — convert to bits)
    return float(emi / np.log(2))


def _compute_ami_pair(v1, v2, n, threshold, miller_madow, gln_table=None,
                      binning_cache=None, cache_idx=None):
    """Compute AMI for a single pair. Returns (result_dict, timing_dict).

    If gln_table is provided, passes it to _expected_mi to avoid redundant
    gammaln table construction.
    If binning_cache is provided (a dict), stores the binned arrays at
    binning_cache[cache_idx] for reuse by Theil's U.
    """
    timing = {}

    # Bin rare values
    t0 = time.time()
    bv1, bv2, bn, raw_d1, raw_d2 = _bin_rare_values(v1, v2, n, threshold)
    timing['binning'] = time.time() - t0

    # Cache binned arrays for Theil's U reuse
    if binning_cache is not None and cache_idx is not None:
        binning_cache[cache_idx] = (bv1, bv2, bn, raw_d1, raw_d2)

    # Build contingency matrix
    t0 = time.time()
    contingency, v1_labels, v2_labels = _build_contingency_matrix(bv1, bv2, bn)
    d1, d2 = contingency.shape
    N = float(contingency.sum())
    timing['contingency'] = time.time() - t0

    # Compute MI and entropies
    t0 = time.time()
    marginals_x = contingency.sum(axis=1).astype(np.float64)
    marginals_y = contingency.sum(axis=0).astype(np.float64)
    h_x = _entropy(marginals_x)
    h_y = _entropy(marginals_y)
    mi, _, _, _, _, _ = _mutual_information(bv1, bv2, bn)
    timing['mi'] = time.time() - t0

    # Miller-Madow correction
    mi_corrected = mi
    if miller_madow and N > 0:
        correction = ((d1 - 1) * (d2 - 1)) / (2.0 * N * np.log(2))
        mi_corrected = max(0.0, mi - correction)

    # E[MI]
    t0 = time.time()
    if d1 <= 1 or d2 <= 1 or N == 0:
        e_mi = 0.0
        ami = 0.0
    else:
        e_mi = _expected_mi(contingency, N, gln_table=gln_table)
        mean_h = 0.5 * (h_x + h_y)
        denom = mean_h - e_mi
        if abs(denom) < 1e-15:
            ami = 0.0 if abs(mi_corrected - e_mi) < 1e-15 else 1.0
        else:
            ami_val = (mi_corrected - e_mi) / denom
            ami = float(np.clip(ami_val, 0.0, 1.0))
    timing['emi'] = time.time() - t0

    result = {
        'ami': ami,
        'mi': mi,
        'mi_corrected': mi_corrected,
        'e_mi': e_mi,
        'h_metric1': h_x,
        'h_metric2': h_y,
        'support_N': int(N),
        'distinct_1': d1,
        'distinct_2': d2,
        'distinct_1_raw': raw_d1,
        'distinct_2_raw': raw_d2,
    }
    return result, timing


def _compute_theil_u_pair(v1, v2, n, threshold, binning_cache=None, cache_idx=None):
    """Compute Theil's U for a single pair. Returns (result_dict, timing_dict).

    If binning_cache is provided and cache_idx is in it, reuses the pre-binned
    arrays from AMI instead of re-binning.
    """
    timing = {}

    # Reuse cached binning from AMI if available
    if binning_cache is not None and cache_idx is not None and cache_idx in binning_cache:
        bv1, bv2, bn, raw_d1, raw_d2 = binning_cache.pop(cache_idx)  # pop to free memory
        timing['binning'] = 0.0
    else:
        t0 = time.time()
        bv1, bv2, bn, raw_d1, raw_d2 = _bin_rare_values(v1, v2, n, threshold)
        timing['binning'] = time.time() - t0

    t0 = time.time()
    mi, h_x, h_y, N, _, _ = _mutual_information(bv1, bv2, bn)
    timing['mi'] = time.time() - t0

    u_1to2 = float(mi / h_y) if h_y > 0 else 0.0
    u_2to1 = float(mi / h_x) if h_x > 0 else 0.0

    result = {
        'theil_u_1to2': float(np.clip(u_1to2, 0.0, 1.0)),
        'theil_u_2to1': float(np.clip(u_2to1, 0.0, 1.0)),
        'mi': mi,
        'h_metric1': h_x,
        'h_metric2': h_y,
        'support_N': int(N),
        'distinct_1': len(np.unique(bv1)),
        'distinct_2': len(np.unique(bv2)),
    }
    return result, timing


# =============================================================================
# Phase 3b: Per-pair parallel computation with work-queue model
# =============================================================================

def _run_parallel_per_pair(pairs, compute_fn, compute_args, n_workers,
                           skip_progress_bars, label, binning_cache=None):
    """Run compute_fn on each pair individually using a thread pool work queue.

    compute_fn signature: compute_fn(v1, v2, n, *compute_args, binning_cache, cache_idx)
                          -> (result_dict, timing_dict)
    pairs: list of (metric1, metric2, v1, v2, n) — should be pre-sorted heavy-first.
    binning_cache: if provided, passed to compute_fn for caching/reusing binned arrays.

    Returns (results_list, wall_elapsed, aggregate_timing).
    """
    total = len(pairs)

    # Thread-safe progress counter
    completed_count = [0]
    count_lock = threading.Lock()

    # Aggregate timing accumulators (per-thread, merged at end)
    thread_timings = defaultdict(lambda: defaultdict(float))

    display = ProgressDisplay(
        tty=sys.__stderr__,
        total_partitions=1,  # single overall bar
        enabled=False if skip_progress_bars else None,
    )
    # Use the first slot as an overall progress bar
    overall_slot = display.slots[0]
    overall_slot._start(label, 1)
    overall_slot.advance_phase(label, total)
    display.start()

    all_results = [None] * total  # preserve order for deterministic output
    t_wall_start = time.time()

    def _process_one(idx):
        m1, m2, v1, v2, n = pairs[idx]
        tid = threading.get_ident()
        t_start = time.time()

        result, timing = compute_fn(v1, v2, n, *compute_args,
                                    binning_cache=binning_cache, cache_idx=idx)
        result['metric1'] = m1
        result['metric2'] = m2

        elapsed = time.time() - t_start
        # Accumulate timing for this thread
        tt = thread_timings[tid]
        tt['n_pairs'] += 1
        tt['total'] += elapsed
        for k, v in timing.items():
            tt[k] += v

        all_results[idx] = result

        with count_lock:
            completed_count[0] += 1
            overall_slot.update_progress(completed_count[0])

    try:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(_process_one, i): i for i in range(total)}
            for future in as_completed(futures):
                future.result()  # raise exceptions

                if skip_progress_bars and completed_count[0] % 1000 == 0:
                    ts = time.strftime("%H:%M:%S")
                    print(f"  [{ts}] {label}: {completed_count[0]:,}/{total:,} pairs done")
    finally:
        display.release_slot(overall_slot)
        display.stop()

    wall_elapsed = time.time() - t_wall_start

    # Merge thread timings
    agg_timing = defaultdict(float)
    n_threads_used = len(thread_timings)
    for tid, tt in thread_timings.items():
        for k, v in tt.items():
            agg_timing[k] += v
    agg_timing['n_threads'] = n_threads_used

    print(f"  {label}: {total:,} pairs in {wall_elapsed:.1f}s "
          f"({total / wall_elapsed:.0f} pairs/s, {n_threads_used} threads)")

    # Print timing breakdown
    total_thread_time = agg_timing.get('total', 0)
    if total_thread_time > 0:
        parts = []
        for key in ['binning', 'contingency', 'mi', 'emi']:
            t = agg_timing.get(key, 0)
            if t > 0:
                parts.append(f"{key}={t:.1f}s ({100*t/total_thread_time:.0f}%)")
        if parts:
            print(f"    Thread-time breakdown: {', '.join(parts)}")
            print(f"    Total thread-time: {total_thread_time:.1f}s "
                  f"(wall={wall_elapsed:.1f}s, parallelism={total_thread_time/wall_elapsed:.1f}x)")

    return all_results, wall_elapsed, dict(agg_timing)


# =============================================================================
# Phase 4: Output
# =============================================================================

AMI_CSV_FIELDS = [
    'metric1', 'metric2', 'ami', 'mi', 'mi_corrected', 'e_mi',
    'h_metric1', 'h_metric2', 'support_N',
    'distinct_1', 'distinct_2', 'distinct_1_raw', 'distinct_2_raw',
]

THEIL_CSV_FIELDS = [
    'metric1', 'metric2', 'theil_u_1to2', 'theil_u_2to1',
    'mi', 'h_metric1', 'h_metric2', 'support_N',
    'distinct_1', 'distinct_2',
]


def _write_csv(results, fields, filepath):
    """Write results as CSV."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in sorted(results, key=lambda x: (-x.get('ami', 0), -x.get('theil_u_1to2', 0))):
            writer.writerow(r)
    print(f"  Wrote {filepath} ({len(results)} rows)")


def _write_pickle(results, filepath):
    """Write results as pickle."""
    with open(filepath, 'wb') as f:
        pickle.dump(results, f)
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  Wrote {filepath} ({size_mb:.1f} MB)")


def _fetch_identical_metrics(bq_table):
    """Query IdenticalMetrics_tbl from the same BQ dataset as the contingency table.

    Returns list of (metric_kept, metric_dropped, n_users) or None if the
    table doesn't exist.
    """
    try:
        from google.cloud import bigquery
        # Extract dataset from fully-qualified table name: project.dataset.table
        parts = bq_table.split(".")
        if len(parts) < 2:
            return None
        project = parts[0]
        dataset = parts[1]
        table_ref = f"{project}.{dataset}.IdenticalMetrics_tbl"

        client = bigquery.Client(project=project)
        sql = f"SELECT metric_kept, metric_dropped, n_users FROM `{table_ref}` ORDER BY metric_kept, metric_dropped"
        rows = list(client.query(sql).result())
        if not rows:
            return []
        return [(r.metric_kept, r.metric_dropped, r.n_users) for r in rows]
    except Exception:
        return None


def _write_run_log(output_dir, conf, pair_metrics, total_pairs, cache_dir,
                   results_info, phase_timing):
    """Write run.log with bookkeeping and timing information."""
    manifest = _load_manifest(os.path.join(cache_dir, "correlation"))

    # Check for identical-metric exclusions in BQ
    identical_metrics = _fetch_identical_metrics(conf['bq_table'])

    lines = []
    lines.append("=== Correlation Analysis Run ===")
    lines.append(f"Date:             {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"BQ Table:         {conf['bq_table']}")
    lines.append(f"Cache Dir:        {_correlation_cache_dir(cache_dir, conf['bq_table'])}")
    lines.append(f"Metric Set:       {len(pair_metrics)} metrics")
    lines.append(f"Total Pairs:      {total_pairs:,}")
    lines.append(f"Workers:          {conf['parallel_workers']}")
    lines.append(f"Missing Values:   {conf['missing_values']}")
    lines.append(f"AMI Enabled:      {conf['ami_enabled']}")
    if conf['ami_enabled']:
        lines.append(f"  Bin Rare:       {conf['ami_bin_rare']}")
        lines.append(f"  Bin Thresholds: {conf['ami_bin_thresholds']}")
        lines.append(f"  Miller-Madow:   {conf['ami_miller_madow']}")
    lines.append(f"Theil's U:        {conf['theil_u_enabled']}")
    lines.append("")

    # Identical metric exclusions
    if identical_metrics is None:
        lines.append("--- Identical Metric Exclusions ---")
        lines.append("  (IdenticalMetrics_tbl not found in dataset — detection not run)")
        lines.append("")
    elif len(identical_metrics) == 0:
        lines.append("--- Identical Metric Exclusions ---")
        lines.append("  No identical metrics detected.")
        lines.append("")
    else:
        lines.append(f"--- Identical Metric Exclusions ({len(identical_metrics)} pairs) ---")
        lines.append("  The following metrics were excluded from the contingency table")
        lines.append("  because they are identical to another metric for all users.")
        lines.append("  (Detected by detect_identical_metrics.sql)")
        lines.append("")
        lines.append(f"  {'Metric dropped':<50s}  {'Identical to':<50s}  {'Users':>12s}")
        lines.append(f"  {'-'*50}  {'-'*50}  {'-'*12}")
        for kept, dropped, n_users in identical_metrics:
            lines.append(f"  {dropped:<50s}  {kept:<50s}  {n_users:>12,}")
        lines.append("")

    # Phase timing
    lines.append("--- Phase Timing ---")
    for phase, elapsed in phase_timing.items():
        if isinstance(elapsed, (int, float)):
            lines.append(f"  {phase}: {elapsed:.1f}s")
    lines.append("")

    # Per-analysis timing breakdown
    for entry in results_info:
        label = entry['label']
        agg = entry.get('timing', {})
        if agg:
            lines.append(f"--- {label} Thread-Time Breakdown ---")
            total_tt = agg.get('total', 0)
            for key in ['binning', 'contingency', 'mi', 'emi']:
                t = agg.get(key, 0)
                if t > 0:
                    pct = 100 * t / total_tt if total_tt > 0 else 0
                    lines.append(f"  {key}: {t:.1f}s ({pct:.0f}%)")
            lines.append(f"  total thread-time: {total_tt:.1f}s")
            lines.append(f"  wall time: {entry['wall_elapsed']:.1f}s")
            lines.append(f"  threads used: {int(agg.get('n_threads', 0))}")
            lines.append(f"  pairs: {int(agg.get('n_pairs', 0))}")
            lines.append("")

    lines.append("--- Cache Files Used ---")
    for m in sorted(pair_metrics):
        info = manifest.get("cached_metrics", {}).get(m, {})
        rows = info.get("rows", "?")
        cached_at = info.get("cached_at", "?")
        lines.append(f"  pairs/{m}/  (cached: {cached_at}, {rows} rows)")
    lines.append("")

    log_path = os.path.join(output_dir, "run.log")
    with open(log_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"  Wrote {log_path}")


# =============================================================================
# Main entry point
# =============================================================================

def run_correlation_analysis(cache_dir, output_dir, conf, skip_progress_bars=False):
    """Run AMI and/or Theil's U analysis on cached contingency data."""
    os.makedirs(output_dir, exist_ok=True)
    phase_timing = {}

    # Load data
    print("\nLoading cached contingency data...")
    t0 = time.time()
    pairs, pair_metrics = load_pair_data(
        cache_dir, conf['metric_set'], conf['missing_values'],
        bq_table=conf.get('bq_table'),
    )
    phase_timing['data_load'] = time.time() - t0

    if not pairs:
        print("  No pairs to analyze. Check metric set and cache.")
        return

    results_info = []
    n_workers = conf['parallel_workers']

    # Shared binning cache: AMI stores binned arrays here, Theil's U reuses them.
    theil_threshold = conf['ami_bin_thresholds'][0] if conf['ami_bin_rare'] else 0
    use_binning_cache = (conf['ami_enabled'] and conf['theil_u_enabled']
                         and theil_threshold in (conf['ami_bin_thresholds'] if conf['ami_bin_rare'] else [0]))
    binning_cache = {} if use_binning_cache else None

    # Precompute shared gammaln table for E[MI] — one table covers all pairs.
    # Without this, each pair rebuilds gammaln(0..N+1) independently,
    # wasting ~63 minutes on aggregatedata (28K pairs × 0.13s each).
    gln_table = None
    if conf['ami_enabled']:
        t0 = time.time()
        max_N = max(int(p[4].sum()) for p in pairs)
        gln_table = _precompute_gammaln_table(max_N)
        gln_elapsed = time.time() - t0
        phase_timing['gammaln_table'] = gln_elapsed
        print(f"  Precomputed shared gammaln table (0..{max_N+1}): "
              f"{gln_table.nbytes / 1e6:.1f} MB in {gln_elapsed:.2f}s")

    # --- AMI ---
    if conf['ami_enabled']:
        thresholds = conf['ami_bin_thresholds'] if conf['ami_bin_rare'] else [0]
        for threshold in thresholds:
            cache_for_this = binning_cache if (use_binning_cache and threshold == theil_threshold) else None

            label = f"AMI (threshold={threshold})"
            print(f"\nComputing {label}...")
            if cache_for_this is not None:
                print(f"    (caching binned arrays for Theil's U reuse)")
            t0 = time.time()
            ami_results, wall_elapsed, agg_timing = _run_parallel_per_pair(
                pairs, _compute_ami_pair,
                (threshold, conf['ami_miller_madow'], gln_table),
                n_workers, skip_progress_bars, label,
                binning_cache=cache_for_this,
            )
            phase_timing[f'ami_t{threshold}'] = time.time() - t0

            suffix = f"_threshold_{threshold}" if threshold > 0 else ""
            csv_path = os.path.join(output_dir, f"ami{suffix}.csv")
            bin_path = os.path.join(output_dir, f"ami{suffix}.bin")

            t0 = time.time()
            _write_csv(ami_results, AMI_CSV_FIELDS, csv_path)
            _write_pickle(ami_results, bin_path)
            phase_timing[f'ami_t{threshold}_write'] = time.time() - t0

            results_info.append({
                'label': label,
                'wall_elapsed': wall_elapsed,
                'timing': agg_timing,
                'csv_path': csv_path,
            })

    if binning_cache is not None:
        cache_size_mb = sum(
            sum(a.nbytes for a in entry[:3])  # bv1, bv2, bn
            for entry in binning_cache.values()
        ) / (1024 * 1024)
        print(f"    Binning cache: {len(binning_cache)} entries, {cache_size_mb:.1f} MB")

    # --- Theil's U ---
    if conf['theil_u_enabled']:
        label = "Theil's U"
        if binning_cache:
            print(f"\nComputing {label} (reusing {len(binning_cache)} cached binnings)...")
        else:
            print(f"\nComputing {label}...")
        t0 = time.time()
        theil_results, wall_elapsed, agg_timing = _run_parallel_per_pair(
            pairs, _compute_theil_u_pair,
            (theil_threshold,),
            n_workers, skip_progress_bars, label,
            binning_cache=binning_cache,
        )
        phase_timing['theil_u'] = time.time() - t0

        csv_path = os.path.join(output_dir, "theil_u.csv")
        bin_path = os.path.join(output_dir, "theil_u.bin")

        t0 = time.time()
        _write_csv(theil_results, THEIL_CSV_FIELDS, csv_path)
        _write_pickle(theil_results, bin_path)
        phase_timing['theil_u_write'] = time.time() - t0

        results_info.append({
            'label': label,
            'wall_elapsed': wall_elapsed,
            'timing': agg_timing,
            'csv_path': csv_path,
        })

    # --- run.log ---
    _write_run_log(output_dir, conf, pair_metrics, len(pairs), cache_dir,
                   results_info, phase_timing)

    # Print overall timing summary
    print(f"\n--- Timing Summary ---")
    for phase, elapsed in phase_timing.items():
        if isinstance(elapsed, (int, float)):
            print(f"  {phase}: {elapsed:.1f}s")
    total = sum(v for v in phase_timing.values() if isinstance(v, (int, float)))
    print(f"  TOTAL: {total:.1f}s")

    print(f"\nCorrelation analysis complete. Output: {output_dir}")


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description="Correlation analysis: AMI and Theil's U on BQ contingency data."
    )
    p.add_argument(
        "-c", "--config", required=True, metavar="FILE",
        help="Python config file (must export CORRELATION_BQ_TABLE and optionally CORRELATION_METRIC_SET)"
    )
    p.add_argument(
        "--cache-dir", required=True, metavar="DIR",
        help="Base cache directory (correlation/ subdirectory used)"
    )
    p.add_argument(
        "-o", "--output-dir", default=None, metavar="DIR",
        help="Output directory for results (required unless --cache-only)"
    )
    p.add_argument(
        "--cache-only", action="store_true",
        help="Download and cache data, skip analysis"
    )
    p.add_argument(
        "--force-rebuild", action="store_true",
        help="Re-download cached metrics"
    )
    p.add_argument(
        "--skip-progress-bars", action="store_true",
        help="Suppress progress bars (log lines instead)"
    )
    return p.parse_args()


def main():
    args = parse_args()

    cfg = _load_config(args.config)
    conf = _get_config(cfg)

    # CLI overrides
    if args.cache_only:
        conf['cache_only'] = True

    if conf['bq_table'] is None:
        print("ERROR: config must export CORRELATION_BQ_TABLE", file=sys.stderr)
        sys.exit(1)

    if not conf['cache_only'] and args.output_dir is None:
        print("ERROR: --output-dir is required unless --cache-only", file=sys.stderr)
        sys.exit(1)

    # Phase 1: ensure cache
    ensure_cache(
        cache_dir=args.cache_dir,
        bq_table=conf['bq_table'],
        metric_set=conf['metric_set'],
        parallel_downloads=conf['parallel_downloads'],
        force_rebuild=args.force_rebuild,
        skip_progress_bars=args.skip_progress_bars,
    )

    # Phase 2+3+4: run analysis
    if not conf['cache_only']:
        # Create timestamped output subdirectory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(args.output_dir, f"correlation_{ts}")
        run_correlation_analysis(
            cache_dir=args.cache_dir,
            output_dir=out_dir,
            conf=conf,
            skip_progress_bars=args.skip_progress_bars,
        )


if __name__ == "__main__":
    main()
