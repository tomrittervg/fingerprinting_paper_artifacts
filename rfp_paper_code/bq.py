#!/usr/bin/env python3
"""
Interactive BigQuery query utility.

Usage:
    python bq.py <sql_file>           # run a .sql file
    python bq.py -q "SELECT ..."      # run an inline query
    python bq.py -                    # read query from stdin

Output is printed as a TSV table by default.
Flags:
    --csv           Output as CSV
    --json          Output as JSON (one object per line)
    --limit N       Stop after N rows (default: no limit)
    --no-header     Suppress header row
"""

import sys
import os
import csv
import json
import argparse
import warnings

warnings.filterwarnings("ignore", message="Your application has authenticated using end user credentials")

from settings import BQ_PROJECT_ID as PROJECT_ID

# Keywords that indicate a mutating statement
_MUTATING_KEYWORDS = {
    'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'REPLACE',
    'CREATE', 'DROP', 'ALTER', 'TRUNCATE',
    'CALL', 'EXECUTE', 'EXPORT',
}


def _strip_sql_comments(sql: str) -> str:
    """Remove -- line comments and /* block comments */ from SQL."""
    import re
    sql = re.sub(r'--[^\n]*', ' ', sql)
    sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
    return sql


def assert_select_only(sql: str) -> None:
    """
    Raise ValueError if the SQL is not a read-only SELECT query.
    Checks:
      1. First meaningful keyword must be SELECT or WITH.
      2. No mutating keywords anywhere in the statement (outside string literals).
    """
    clean = _strip_sql_comments(sql)

    # Tokenise: split on whitespace and punctuation, uppercase
    import re
    tokens = [t.upper() for t in re.split(r'[\s;,()\[\]]+', clean) if t]

    if not tokens:
        raise ValueError("Query is empty.")

    # Rule 1: must start with SELECT or WITH (CTE prefix)
    if tokens[0] not in ('SELECT', 'WITH'):
        raise ValueError(
            f"Query must start with SELECT or WITH, got '{tokens[0]}'."
        )

    # Rule 2: no mutating keywords anywhere
    found = _MUTATING_KEYWORDS & set(tokens)
    if found:
        raise ValueError(
            f"Query contains disallowed keyword(s): {', '.join(sorted(found))}."
        )


def run_query(sql: str, limit: int = None) -> tuple[list[str], list[dict]]:
    """Run a SQL query and return (field_names, rows)."""
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    job = client.query(sql)
    results = job.result()
    field_names = [f.name for f in results.schema]
    rows = []
    for i, row in enumerate(results):
        if limit is not None and i >= limit:
            break
        rows.append(dict(row))
    return field_names, rows


def run_execute(sql: str) -> None:
    """Run a DDL/DML/scripting statement and print job status.

    Uses Jobs.get polling instead of getQueryResults, which is required for
    multi-statement scripting queries (DECLARE / EXECUTE IMMEDIATE).
    """
    import time
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    job = client.query(sql)
    print(f"  job ID: {job.job_id}", file=sys.stderr)
    while job.state != 'DONE':
        time.sleep(3)
        job = client.get_job(job.job_id, location=job.location)
    if job.errors:
        raise RuntimeError(f"Job failed: {job.errors}")
    affected = getattr(job, 'num_dml_affected_rows', None)
    if affected is not None:
        print(f"OK — {affected} row(s) affected.", file=sys.stderr)
    else:
        print("OK", file=sys.stderr)


def print_tsv(field_names, rows, header=True):
    w = csv.writer(sys.stdout, delimiter='\t')
    if header:
        w.writerow(field_names)
    for row in rows:
        w.writerow([row.get(f, '') for f in field_names])


def print_csv(field_names, rows, header=True):
    w = csv.writer(sys.stdout)
    if header:
        w.writerow(field_names)
    for row in rows:
        w.writerow([row.get(f, '') for f in field_names])


def print_json(field_names, rows):
    for row in rows:
        print(json.dumps({f: row.get(f) for f in field_names}, default=str))


def main():
    parser = argparse.ArgumentParser(description='Run a BigQuery SQL query and print results.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('sql_file', nargs='?', help='Path to a .sql file, or - for stdin')
    group.add_argument('-q', '--query', help='Inline SQL query string')

    parser.add_argument('--csv',       action='store_true', help='Output as CSV')
    parser.add_argument('--json',      action='store_true', help='Output as JSON (one object per line)')
    parser.add_argument('--limit',     type=int, default=None, help='Max rows to print')
    parser.add_argument('--no-header', action='store_true', help='Suppress header row')
    parser.add_argument('--execute',   action='store_true', help='Run DDL/DML/scripting (skips SELECT-only check, no result output)')
    args = parser.parse_args()

    if args.query:
        sql = args.query
    elif args.sql_file == '-':
        sql = sys.stdin.read()
    else:
        with open(args.sql_file) as f:
            sql = f.read()

    if args.execute:
        print(f"Executing...", file=sys.stderr)
        run_execute(sql)
        return

    try:
        assert_select_only(sql)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Running query...", file=sys.stderr)
    field_names, rows = run_query(sql, limit=args.limit)
    print(f"{len(rows)} row(s) returned.", file=sys.stderr)

    if args.json:
        print_json(field_names, rows)
    elif args.csv:
        print_csv(field_names, rows, header=not args.no_header)
    else:
        print_tsv(field_names, rows, header=not args.no_header)


if __name__ == '__main__':
    main()
