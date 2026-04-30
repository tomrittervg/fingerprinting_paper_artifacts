# gen_outputs — Post-Processing Output Generators

These scripts regenerate graphs, tables, and CSVs from pickled `.bin` files produced by `analyze.py`. They exist because `analyze.py` saves intermediate results as pickles, allowing output regeneration without re-running the full pipeline. Each script checks for a `.done` sentinel file and skips work unless `-r`/`--regen` is passed.

All scripts take one or more analyze.py output directories as positional arguments.

## Scripts

### gen_alldata_output.py
Generates fingerprint analysis output (graphs, text, CSVs) from `alldata.bin`. Stratifies by OS when `fp_counters_by_os` is present in the payload. Sentinel: `alldata_output.done`.

### gen_experiment_output.py
The main experiment output generator. Processes `exp_*.bin` and `mode_*.bin` files, producing per-experiment graphs and tables via `print_fingerprint_results()`. Also generates summary visualizations: cumulative line graphs for C-P* (cumulative experiment chains) and individual bar graphs for I-P* (individual experiments). Handles per-OS stratification and combined OS+Overall line graphs. Uses `experiment_manifest.json` for slug mapping and experiment equivalents. Sentinel: per-bin `.done` files.

### gen_experiment_output_compare.py
Generates a comparison graph showing three perspectives on cumulative experiment results: overall global uniqueness, simple OS average, and population-weighted OS average. One subplot per fingerprinter. Expects `experiment_manifest.json` and baseline/per-OS CSVs in the output directory.

### gen_metrics_output.py
Generates metric aggregation visualizations from `metric_aggregation_output.bin`. Computes Shannon entropy and HHI, produces per-metric value distribution tables, and writes per-OS entropy/HHI CSVs (`metric_shannon_entropy_os_{OS}.csv`, `metric_hhi_os_{OS}.csv`). Sentinel: `metric_aggregation_output.done`.

### gen_smr_output.py
Generates Specific Metric Removal (SMR) analysis from `smr.bin`. Shows the impact of removing individual metrics from the fingerprint. Handles legacy histogram format conversion. Per-OS output when available. Sentinel: `smr_output.done`.

### gen_lmr_output.py
Generates Localization/Metric Removal (LMR) analysis from `lmr.bin`. Like SMR but organized by localization unit (groups of related metrics removed together). Per-OS output when available. Sentinel: `lmr_output.done`.

### run_ismr_ismrp_comparison.py
Generates a side-by-side visualization comparing ISMR (Iterative Specific Metric Removal) vs ISMRP (paired variant) rankings. Reads `ismr_results_*.csv` and `ismrp_results_*.csv`, draws arrows between panels showing rank changes (green = improved, red = degraded, black = same). Accepts one directory (both results co-located) or two (ISMR dir, ISMRP dir).

## Common Patterns

- **Sentinel files:** Each script writes a `.done` file on completion; skips processing if it exists unless `-r` is passed.
- **Logging:** Appends timestamped messages to `run.log` in the output directory.
- **OS stratification:** Most scripts handle `*_by_os` variants in the pickle payload, producing per-OS output files.
- **Format conversion:** SMR and LMR scripts auto-convert legacy histogram format on first run.
- **Memory:** Scripts call `gc.collect()` after processing large pickles.
