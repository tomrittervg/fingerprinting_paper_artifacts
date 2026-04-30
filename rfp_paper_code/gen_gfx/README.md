# gen_gfx — Paper Figure & Table Generation

Each subdirectory generates one or more figures or tables. Some (not even most) were used in the paper. 
Most scripts read from analyze.py output directories; the correlation
directories read from correlation.py output instead.

## name_mapping.txt

Central mapping of metric identifiers to human-readable display names
(~132 entries). Referenced by `iminmetrics_table/`, `fingerprinters_tables/`,
`indv_metrics/`, `correlation-ami/`, and `correlation-thiels/` for
consistent labeling. Auto-updated when scripts encounter new metrics.

## Subdirectories

### buckets/
This is Figure 1, what we called the 'buckets' plot.  It creates 'buckets' of increasingly large random subsets of the data and calculates the uniqueness for that bucket.  
Data needs to be manually copied and then given to the script
Contains data in `realistic/` and `worstcase/` subdirectories, realistic is what we used (it ignored screen inner/outer).

### correlation-ami/
AMI (Adjusted Mutual Information) correlation visualizations.

Input: per-OS `ami_threshold_10.csv` from correlation.py. Columns:
metric1, metric2, ami, mi, mi_corrected, e_mi, h_metric1, h_metric2,
support_N, distinct_1, distinct_2, distinct_1_raw, distinct_2_raw.

`run_graphs.sh [--accepted|--all]` loops over OSes, auto-discovers
CSVs under CORR_BASE, and copies output PNGs to IMG_CACHE.

Env vars:
- `CORR_CSV` — path to ami_threshold_10.csv for one OS
- `CORR_OUT_DIR` — output directory (default: script dir)
- `CORR_FILTER` — metric filter (typically "allfp")
- `CORR_ALLOWLIST` — metric name mapping file
- `CORR_ANALYZE_DIR` — analyze.py output dir containing
  metric_shannon_entropy.csv and metric_hhi.csv (for annotation)

Preferred scripts (run by default):
- `corr_all_heatmap_v1.py` — Full AMI heatmap (with CORR_LOWER_ONLY=1,
  and again with CORR_THRESHOLD=0.6)
- `corr_category_heatmap_split.py` — AMI heatmap split by metric category

Additional (--all adds these):
- `corr_scatter_maxami.py` — Max-AMI per metric scatter
- `corr_scatter_4panel.py` — 4-panel AMI scatter (one per OS)

not-pursued/ (experimental, not considered to be good visuals):
- `corr_all_heatmap.py`, `_v2`, `_v3`, `_minami` — earlier heatmap iterations
- `corr_category_heatmap.py`, `_v1`, `_v2`, `_v3` — earlier category iterations
- `corr_category_profiles.py` — per-category AMI profiles
- `corr_chord.py` — chord diagram of inter-category AMI
- `corr_dendrogram_heatmap.py` — clustered heatmap with dendrogram
- `corr_distribution.py` — AMI value distribution histogram
- `corr_ami_distribution.py` — AMI distribution analysis
- `corr_arc_network.py` — arc-style network diagram
- `corr_network.py`, `_v1`, `_v2`, `_v3` — force-directed network (requires networkx)
- `corr_top_pairs.py`, `_v1`, `_v2`, `_v3` — top correlated pairs tables

Helpers: `_corr_utils.py`, `_pair_rules.py`, `_scatter_core.py`

### correlation-thiels/
Theil's U (asymmetric predictability) visualizations. Asymmetric:
U(A→B) measures how well knowing A predicts B.

Input: per-OS `theil_u.csv` from correlation.py.

`run_graphs.sh [--accepted|--all]` — same pattern as correlation-ami.

Env vars: same as AMI but prefixed `THEIL_` instead of `CORR_`
(`THEIL_CSV`, `THEIL_OUT_DIR`, `THEIL_FILTER`, `THEIL_ALLOWLIST`,
`THEIL_ANALYZE_DIR`).

Preferred scripts:
- `theil_net_predictability.py` — Net predictability ranking
  (default invocation: THEIL_SCOPES=all,cross THEIL_CHARTS=net)
- `theil_category_heatmap_split.py` — Theil's U by category
- `theil_all_heatmap.py` — Full heatmap (THEIL_HEATMAP_THRESHOLD=0.6)
- `theil_isolation.py` — Isolation analysis

not-pursued/:
- `theil_asymmetry_scatter.py` — U(A→B) vs U(B→A) scatter (requires adjustText)
- `theil_category_heatmap.py` — earlier category heatmap
- `theil_category_heatmap_diff.py` — category heatmap difference
- `theil_predictability.py` — predictability analysis
- `theil_top_pairs.py` — top Theil pairs table
- `theil_vs_ami.py` — compare Theil's U vs AMI (requires AMI_CSV env var
  pointing to the per-OS ami_threshold_10.csv)

Helpers: `_theil_utils.py` (also imports `_pair_rules.py` from
correlation-ami/, so both directories need to be on PYTHONPATH when
running Theil scripts outside of run_graphs.sh).

### experiment_table/
The main experiment results pipeline. Multi-step:
1. `01_build_csv.py` — Reads analyze.py cumulative/individual experiment
   outputs, produces `table1_baseline.csv`, `table3_experiments.csv`,
   `table3_overall.csv`, `table5_individual.csv`, `table5_overall.csv`.
   The `--table3-fp` flag selects which fingerprinter (default FPJSv2);
   run once per fingerprinter to get `table3_experiments_fpjs.csv`, etc.
2. `02_build_latex.py` — Converts CSVs to LaTeX table bodies, updates
   `fpp_paper.tex` in-place (tab:fingerprinters, tab:improvements,
   tab:individual, and their overall variants)
3. `03_graphs.py` — Phase endpoint line plots per OS (2x2 grid, not in paper)
4. `04_graph.py` — Individual protection impact bar chart
   (protections_individual.png, FPJSv2 weighted avg across OSes)
5. `05_graph.py` — Cumulative protection line charts (protection_overview.png,
   2x2 grid: overall weighted avg + one panel per fingerprinter)

### fingerprinters_tables/
Builds a LaTeX longtable comparing which metrics each fingerprinter service collects. Three columns (Akamai, Fingerprint Pro, SignifyD), each sorted by that fingerprinter's iterative SMR rank. Color-coded: red = all three, blue = Pro & SignifyD, black = single fingerprinter.

May not produce output formatted in the exact same way as the paper, we probably hand-edited the latex a bit.

### iminmetrics/
Cumulative uniqueness curve visualizations (how uniqueness grows as metrics are added one by one).
This is the greddy minimum number of metrics analysis from 3.6
- `viz_minmetrics_all.py` — 3x1 vertical grid, one panel per fingerprinter, four OS lines each
- `viz_minmetrics_weighted_avg.py` — Population-weighted average across OSes

Reads `iterative_minmetrics_*_os_*.csv` files and companion `.txt` metadata.

### iminmetrics_table/
Builds a LaTeX table of the top-20 metrics from iterative (greedy) minmetrics analysis, broken out by OS. Layout: Windows + macOS on top, Android + Linux on bottom. Color highlights indicate which metrics appear in the top-K (default 5) for each OS.

### indv_metrics/
Individual metric property tables and scatter plots. This is Figure 2 in the paper
1. `01_build_csv.py` — Merges Shannon entropy, HHI, and SMR removal data into `metric_table.csv`
2. `02_update_tex_table.py` — Updates LaTeX table in paper
3. `make_graph_scatter.py` — Scatter plot of SMR removal impact vs entropy/HHI

### minset/
Minimal metric set combination analysis and visualization. This analysis was not used in the paper.
(It's kind of confusing.  Pick N of the top M metrics.... what does that really mean? It's more an artifact of computational limits.)
One nice thing it does output was the single most impactful combination of metrics at different sizes.
That morphed in the iterative min metrics approach which can do it more efficiently.

Multiple viz types via decorator registry:
- `grid_waterfall.py` — Waterfall charts of deduplicated metric combinations
- `viz_top_combo_by_os.py` — Per-OS top combination line graphs
- `viz_minset.py` — Main entry point with viz registry (dedup_waterfall, cumulative_pct, metric_contribution)
- `viz_minset_common.py` — Shared data loading utilities

The positional arguments are analyze.py output directories from `perform_min_set_combo_analysis` runs. Because min-set computation is expensive, these are typically split across many separate runs — one per top-N metric count (top5, top10, top20) and sometimes per OS — so the scripts expect multiple directories as input and merge them.

`--metadata-dir` (required by `grid_waterfall.py` and `viz_minset.py`) points to an analyze.py output directory that contains an `os.txt` file — the per-OS user count table produced by the `perform_shannon_hhi_analysis` config. This provides total and per-OS user counts so the scripts can compute percentages. Example: `--metadata-dir /path/to/shannon_hhi_canvasfillin_final_1776808022`.
