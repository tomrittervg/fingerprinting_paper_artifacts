#!/usr/bin/env python3
"""
Build metric_table.csv and run.log from analyze.py output directories.

Usage:
    python3 build_csv.py \
        --shannon-hhi  <path/to/shannon_hhi_XXXXXXXXXX> \
        --smr          <path/to/smr_XXXXXXXXXX>         \
        --output-dir   <path/to/output/dir>

The shannon-hhi directory must contain:
    metric_shannon_entropy.csv  (columns: Metric, Entropy)
    metric_hhi.csv              (columns: Metric, HHI)
    run.log

The smr directory must contain:
    smr_results.csv             (columns: Metric, UniqueUsersWhenRemoved,
                                          CohortFitnessWhenRemoved)
    run.log
If --smr is omitted, the SMR columns are left empty.

Outputs written to --output-dir (default: same directory as this script):
    metric_table.csv
    run.log
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv_as_dict(path: Path, key_col: str) -> dict:
    """Return {key_col_value: row_dict} for every row in the CSV."""
    result = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = row[key_col].strip()
            result[k] = {col: val.strip() for col, val in row.items()}
    return result


def extract_provenance(run_log: Path) -> dict:
    """
    Parse the run.log written by analyze.py and extract provenance fields:
        output_dir, date_start, date_end, num_users, schema_floor
    """
    info = {
        "output_dir": str(run_log.parent),
        "date_start": None,
        "date_end": None,
        "num_users": None,
        "schema_floor": "30",   # hardcoded in data.py:350 as of 2026-03-18
    }
    with run_log.open(encoding="utf-8") as f:
        for line in f:
            # "Date range:    2026-02-20 to 2026-03-18 (26 day(s))"
            m = re.search(r"Date range:\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})", line)
            if m:
                info["date_start"] = m.group(1)
                info["date_end"]   = m.group(2)
            # "  Parallel processing: 291,660 DataValues across …"
            m = re.search(r"Parallel processing:\s+([\d,]+)\s+DataValues", line)
            if m:
                info["num_users"] = m.group(1).replace(",", "")
    return info


def extract_smr_metric_provenance(smr_dir: Path) -> dict:
    """
    Parse smr_provenance.txt written by smr.py alongside smr_results.csv.

    Lines:
        SMR fingerprinter: AllFingerprinters
        SMR metric count: 85
        SMR metrics: metric1, metric2, ...
    """
    info = {"fp_name": None, "metric_count": None, "metrics": []}
    prov_file = smr_dir / "smr_provenance.txt"
    if not prov_file.exists():
        return info
    with prov_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            m = re.match(r"SMR fingerprinter:\s*(.+)", line)
            if m:
                info["fp_name"] = m.group(1).strip()
            m = re.match(r"SMR metric count:\s*(\d+)", line)
            if m:
                info["metric_count"] = m.group(1)
            m = re.match(r"SMR metrics:\s*(.+)", line)
            if m:
                info["metrics"] = [x.strip() for x in m.group(1).split(",")]
    return info


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--shannon-hhi", required=True, metavar="DIR",
                        help="Output directory from paper_indvmetrics_shannon_hhi config")
    parser.add_argument("--smr", default=None, metavar="DIR",
                        help="Output directory from paper_indvmetrics_smr config (optional)")
    parser.add_argument("--smr-fp", default="FPJSv2_Realistic", metavar="FP",
                        help="Fingerprinter slug for smr_results_<slug>.csv (default: FPJSv2_Realistic)")
    parser.add_argument("--output-dir", default=None, metavar="DIR",
                        help="Directory to write metric_table.csv and run.log "
                             "(default: directory of this script)")
    args = parser.parse_args()

    sh_dir  = Path(args.shannon_hhi).resolve()
    smr_dir = Path(args.smr).resolve() if args.smr else None
    out_dir = Path(args.output_dir).resolve() if args.output_dir \
              else Path.cwd().resolve()

    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load shannon entropy
    # ------------------------------------------------------------------
    entropy_file = sh_dir / "metric_shannon_entropy.csv"
    if not entropy_file.exists():
        sys.exit(f"ERROR: {entropy_file} not found")
    entropy = read_csv_as_dict(entropy_file, "Metric")

    # ------------------------------------------------------------------
    # Load Simpson Index
    # ------------------------------------------------------------------
    simpson_file = sh_dir / "metric_hhi.csv"
    if not simpson_file.exists():
        sys.exit(f"ERROR: {simpson_file} not found")
    simpson = read_csv_as_dict(simpson_file, "Metric")

    # ------------------------------------------------------------------
    # Load SMR (optional)
    # ------------------------------------------------------------------
    def _fp_slug(fp_name):
        return {
            "AkamaiV2": "akamai_v2", "FPJSv2": "fpjs_v2", "Signifyd": "signifyd",
            "FPJSv2_Realistic": "fpjsv2_realistic",
            "Signifyd_Realistic": "signifyd_realistic",
            "AkamaiV2_Realistic": "akamaiv2_realistic",
        }.get(fp_name, fp_name.lower())

    smr = {}
    smr_metric_prov = {}
    if smr_dir is not None:
        slug = _fp_slug(args.smr_fp)
        smr_file = smr_dir / f"smr_results_{slug}.csv"
        if not smr_file.exists():
            sys.exit(f"ERROR: {smr_file} not found.")
        smr = read_csv_as_dict(smr_file, "Metric")
        smr_metric_prov = extract_smr_metric_provenance(smr_dir)

    # ------------------------------------------------------------------
    # Extract provenance
    # ------------------------------------------------------------------
    sh_prov  = extract_provenance(sh_dir / "run.log")
    smr_prov = extract_provenance(smr_dir / "run.log") if smr_dir else None

    # ------------------------------------------------------------------
    # Merge: all metrics from entropy (superset); Simpson added where present
    # ------------------------------------------------------------------
    all_metrics = sorted(set(entropy) | set(simpson))

    out_csv = out_dir / "metric_table.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Simpson Index", "Shannon Entropy",
                         "SMR Removal (Uniqueness)", "SMR Removal (Cohort)"])
        for metric in all_metrics:
            simpson_val = simpson.get(metric, {}).get("HHI", "")
            entropy_val = entropy.get(metric, {}).get("Entropy", "")
            smr_row     = smr.get(metric, {})
            smr_uniq    = smr_row.get("UniqueUsersWhenRemoved", "")
            smr_cohort  = smr_row.get("CohortFitnessWhenRemoved", "")
            # If SMR ran but this metric wasn't in the fingerprinter subset,
            # cohort cell stays empty; mark uniqueness as n/a only if cohort
            # was explicitly "n/a" (baseline == removal fitness)
            if smr_dir and not smr_uniq:
                smr_cohort = "n/a"
            writer.writerow([metric, simpson_val, entropy_val, smr_uniq, smr_cohort])

    print(f"Wrote {len(all_metrics)} rows to {out_csv}")

    # ------------------------------------------------------------------
    # Write provenance run.log
    # ------------------------------------------------------------------
    prov_log = out_dir / "run.log"
    with prov_log.open("w", encoding="utf-8") as f:
        def w(line=""):
            f.write(line + "\n")

        w("=" * 70)
        w("metric_table.csv — Provenance Log")
        w(f"Generated: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} UTC")
        w("=" * 70)
        w()
        w("SHANNON ENTROPY + SIMPSON INDEX SOURCE")
        w(f"  Config:         paper_indvmetrics_shannon_hhi")
        w(f"  Output dir:     {sh_prov['output_dir']}")
        w(f"  Date range:     {sh_prov['date_start']} to {sh_prov['date_end']}")
        w(f"  Rows (users):   {sh_prov['num_users']}")
        w(f"  Schema floor:   >= {sh_prov['schema_floor']}")
        w()
        if smr_prov:
            w("SMR SOURCE")
            w(f"  Config:             paper_indvmetrics_smr")
            w(f"  Output dir:         {smr_prov['output_dir']}")
            w(f"  Date range:         {smr_prov['date_start']} to {smr_prov['date_end']}")
            w(f"  Rows (users):       {smr_prov['num_users']}")
            w(f"  Schema floor:       >= {smr_prov['schema_floor']}")
            fp_name = smr_metric_prov.get("fp_name") or "unknown"
            w(f"  Fingerprinter set:  {fp_name}")
            mc = smr_metric_prov.get("metric_count") or str(len(smr_metric_prov.get("metrics", [])))
            w(f"  Metric count:       {mc}")
            metrics_list = smr_metric_prov.get("metrics", [])
            if metrics_list:
                w(f"  Metrics:")
                for chunk_start in range(0, len(metrics_list), 6):
                    chunk = metrics_list[chunk_start:chunk_start + 6]
                    w("    " + ", ".join(chunk))
        else:
            w("SMR SOURCE")
            w("  (not provided — SMR columns are empty)")
        w()
        w("OUTPUT")
        w(f"  {out_csv}")
        w(f"  Metrics in table: {len(all_metrics)}")
        smr_count = sum(1 for m in all_metrics if smr.get(m, {}).get("UniqueUsersWhenRemoved"))
        w(f"  Metrics with SMR data: {smr_count}")
        w()
        w("NOTES")
        w("  Schema floor (>= 30) is hardcoded in data.py:350 as of 2026-03-18.")
        w("  SMR is computed over the fingerprinter set named above.")
        w("  Metrics not in that subset have empty SMR columns.")

    print(f"Wrote provenance log to {prov_log}")


if __name__ == "__main__":
    main()
