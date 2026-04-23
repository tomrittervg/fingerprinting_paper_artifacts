#!/usr/bin/env python3
"""
Validate that every combined_*_hash value present in BigQuery's
DoubleExploded_tbl has a corresponding entry in a combined_hash_lookup.json
mapping file produced by analyze.py.

Usage:
    ./validate_combined_hashes.py --dataset DATASET --lookup PATH/combined_hash_lookup.json

    DATASET is the fully-qualified BigQuery dataset, e.g.
    <your-bq-project>.rfp_analysis_20260301 (the project component must match
    the BQ_PROJECT_ID configured in settings / local_settings.py).

Options:
    --dataset   DATASET    BigQuery dataset containing DoubleExploded_tbl (required)
    --lookup    FILE       Path to combined_hash_lookup.json (required)
    --table     NAME       Override table name (default: DoubleExploded_tbl)
    --verbose              Print all missing hashes, not just per-metric counts
"""

import sys
import os
import json
import argparse
import warnings

warnings.filterwarnings("ignore", message="Your application has authenticated using end user credentials")

from settings import BQ_PROJECT_ID as PROJECT_ID


def query_distinct_hashes(dataset: str, table: str) -> dict[str, set[str]]:
    """
    Returns {metric: set_of_distinct_hash_values} for all combined_*_hash metrics
    in the given DoubleExploded_tbl, excluding 'None' values.
    """
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)

    sql = f"""
    SELECT metric, value
    FROM `{dataset}.{table}`
    WHERE metric LIKE 'combined_%_hash'
      AND value IS NOT NULL
      AND value != 'None'
    GROUP BY metric, value
    """

    print(f"Querying {dataset}.{table} ...", file=sys.stderr)
    job = client.query(sql)
    results = job.result()

    by_metric: dict[str, set[str]] = {}
    for row in results:
        by_metric.setdefault(row['metric'], set()).add(row['value'])

    return by_metric


def main():
    parser = argparse.ArgumentParser(
        description='Validate combined_*_hash values in BQ against combined_hash_lookup.json')
    parser.add_argument('--dataset', required=True,
                        help='BigQuery dataset (PROJECT.DATASET or bare DATASET, e.g. rfp_analysis_20260301)')
    parser.add_argument('--lookup', required=True,
                        help='Path to combined_hash_lookup.json produced by analyze.py')
    parser.add_argument('--table', default='DoubleExploded_tbl',
                        help='Table name within the dataset (default: DoubleExploded_tbl)')
    parser.add_argument('--verbose', action='store_true',
                        help='Print every missing hash, not just per-metric summary')
    args = parser.parse_args()

    # Load the mapping file
    print(f"Loading lookup: {args.lookup}", file=sys.stderr)
    with open(args.lookup) as f:
        lookup: dict[str, str] = json.load(f)
    print(f"  {len(lookup)} entries in mapping file", file=sys.stderr)

    # Query BQ
    by_metric = query_distinct_hashes(args.dataset, args.table)

    if not by_metric:
        print("ERROR: no combined_*_hash metrics found in table — check dataset/table name", file=sys.stderr)
        sys.exit(1)

    # Compare
    total_hashes = 0
    total_missing = 0
    all_pass = True

    metrics_sorted = sorted(by_metric)
    col_w = max(len(m) for m in metrics_sorted)

    header = f"{'metric':<{col_w}}  {'distinct':>8}  {'missing':>8}  {'coverage':>9}"
    print()
    print(header)
    print('-' * len(header))

    missing_by_metric: dict[str, list[str]] = {}

    for metric in metrics_sorted:
        hashes = by_metric[metric]
        missing = [h for h in hashes if h not in lookup]
        missing_by_metric[metric] = missing

        total_hashes += len(hashes)
        total_missing += len(missing)

        coverage = (len(hashes) - len(missing)) / len(hashes) if hashes else 1.0
        flag = '  *** MISSING ***' if missing else ''
        print(f"{metric:<{col_w}}  {len(hashes):>8}  {len(missing):>8}  {coverage:>8.1%}{flag}")

        if missing:
            all_pass = False
            if args.verbose:
                for h in sorted(missing):
                    print(f"    {h}")

    print('-' * len(header))
    total_coverage = (total_hashes - total_missing) / total_hashes if total_hashes else 1.0
    print(f"{'TOTAL':<{col_w}}  {total_hashes:>8}  {total_missing:>8}  {total_coverage:>8.1%}")
    print()

    if all_pass:
        print("PASS — all BQ hashes have entries in the mapping file")
        sys.exit(0)
    else:
        print(f"FAIL — {total_missing} hash(es) across "
              f"{sum(1 for m in missing_by_metric if missing_by_metric[m])} metric(s) "
              f"are missing from the mapping file.")
        print()
        print("Possible causes:")
        print("  1. The lookup was produced by an analyze.py run that used cached DataValues")
        print("     (cache does not re-execute _combined_hash, so lookup stays empty).")
        print("     Fix: clear the cache and re-run analyze.py, or run with a fresh date range.")
        print("  2. Python and SQL compute different hash values for the same data")
        print("     (separators mismatch, encoding difference, etc.).")
        print("     Fix: compare the JSON string stored in BQ against what Python would produce.")
        print("  3. The mapping file is from a different analysis run / date range than the BQ table.")
        sys.exit(1)


if __name__ == '__main__':
    main()
