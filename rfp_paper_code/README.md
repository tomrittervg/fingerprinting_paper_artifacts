Note to Reviewers
=================

This repository contains the analysis toolkit used to produce the
results in the paper. The paper's results were computed on ~25 million
Firefox Release users over a 23-day window. For artifact review, the
repository ships with a small sample dataset so you can run the full
pipeline yourself and verify the methodology.

Data: The sample dataset in simulated-cache/ was constructed from
real telemetry submissions from 6 volunteer Firefox Nightly users
(across Windows, macOS, Linux, and Android). Each volunteer's
submission was duplicated 100 times with unique client identifiers,
and random perturbations were applied independently to subsets of
the duplicates to create realistic variation:

- WebGL renderer string modified in 50% of duplicates
- WebGL vendor string modified in 5% of duplicates
- WebGL renderer (sanitized) modified in 20% of duplicates
- CSS system colors modified in 50% (changes the combined hash)
- CSS system fonts modified in 30% (changes the combined hash)
- Accept-language changed to a random language tag in 10%
- Storage quota randomized in 10%
- CPU core count randomized in 20%
- FingerprintJS canvas image modified in 30%

This produces ~900 simulated users with the same schema and metrics
as the production dataset. The perturbation process is documented
in generate_simulated_data.py and can be re-run to regenerate the
cache from the source pings in simulated-cache/source-pings/.

To run:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    ./run_all.sh

This runs the complete pipeline end-to-end: data analysis, post-
processing, and paper figure generation. Output goes to
simulated-output/. It should take a few minutes.

Use `./run_all.sh --skip-data` to re-generate only the output
tables and figures without re-running the analysis.

Requirements: Python 3.12+ and the packages in requirements.txt
(matplotlib, numpy, tqdm). No BigQuery access needed.

What the run produces (these are the analyses used for the paper):

- Shannon entropy and HHI per metric
- SMR (Single-Metric-Removal) importance rankings for 3 fingerprinters
- Fingerprint bucket distribution (how uniqueness changes with dataset size)
- Cumulative and individual protection experiment tables
- Iterative minmetrics (greedy forward metric selection) for 3 fingerprinters

Because the sample is ~900 simulated users (from 6 real sources), the
absolute numbers (uniqueness percentages, cohort scores) will differ
substantially from the paper.
The purpose is to demonstrate that the pipeline runs correctly and
produces the same types of output — not to reproduce the exact figures.

The codebase also contains analyses not included in run_all.sh:
correlation (AMI/Theil's U), ISMR/ISMRP/LMR, and min-set
combinations. These analyses were NOT used in the paper, but were
used to explore the data before settling on the best analyses to
present. Some require separate BigQuery aggregate tables, but the
code is present if you want to review it.

What was changed for artifact sharing:

- BigQuery dependency removed — the pipeline reads from a pre-primed
  cache of pickled telemetry rows rather than querying BigQuery.
- Python 3.14 free-threaded build no longer required — runs on any
  Python 3.12+. (Free-threaded builds still give better parallelism.)
- run_all.sh orchestrates the full pipeline (analysis → post-processing
  → figure generation) in a single command.
- Identifying information (project IDs, filesystem paths) has been
  removed or replaced with generic defaults.

Scripts:

  run_all.sh         Full pipeline on simulated data (analysis +
                     post-processing + figure generation)
  run_real_data.sh   Regenerate paper figures from real production
                     CSVs in real-output-data/


  run_data_full.sh   Batch runner for all analysis configs (reference;
                     includes commented-out exploratory analyses)
  run.sh             Wrapper for running individual analyze.py configs

Reproducing the paper's figures from real data:

The repository also includes real-output-data/, which contains the
pre-computed CSV output from the production analysis on ~25 million
users. To regenerate the paper's figures and tables from this data:

    ./run_real_data.sh

This produces PNGs and LaTeX table fragments in real-output-data/.
Requires matplotlib and numpy (same venv as run_all.sh). The output
corresponds to the figures and tables in the paper:

  - metric_scatter.png            (individual metric impact)
  - protection_overview.png       (cumulative protection line charts)
  - protections_individual.png    (individual protection bar chart)
  - viz_minmetrics_weighted_avg.png (cumulative uniqueness curve)
  - viz_minmetrics_all.png        (per-fingerprinter per-OS curves)
  - table1_baseline.csv           (baseline uniqueness by fingerprinter)
  - table3_experiments_*.csv      (cumulative improvement per OS)
  - table5_individual.csv         (individual improvement per OS)
  - fingerprinter_metrics_table.tex (metrics per fingerprinter)
  - iterative_top20_table.tex     (top-20 metrics by OS)

The generated images will not be byte-identical to those in the paper
due to matplotlib rendering differences across environments (font
hinting, anti-aliasing), but the underlying data values match.

Running individual configs (with simulated data):

    ./run.sh -o ./simulated-output/test --cache-dir ./simulated-cache \
        -c configs/paper_indvmetrics_shannon_hhi.py \
        --per-os=true --skip-progress-bars

The rest of this README documents the toolkit as used for the
production analysis (BigQuery access, full dataset, etc.).

================================================================

Python toolkit that reads Firefox telemetry from BigQuery, computes
per-vendor fingerprint hashes, measures per-metric entropy, and
simulates proposed countermeasures (fdlibm math, font allowlists,
processor-count clamping, timezone normalization, accept-language
collapsing, WebGL sanitization, and others).

Requirements:

- Python 3.14 free-threaded (python3.14t). Always use ./run.sh; it
  sets PYTHON_GIL=0 and ANALYZE_VIA_WRAPPER=1. Calling analyze.py
  directly aborts.
- Packages in requirements.txt. grpcio is intentionally excluded (no
  cp314t wheel; the REST BigQuery path does not need it).

Setup:

    python3.14t -m venv .venv
    .venv/bin/pip install -r requirements.txt

    export GOOGLE_APPLICATION_CREDENTIALS=/abs/path/creds.json
    export BQ_PROJECT_ID=<project>
    export RFP_CACHE_DIR=./cache RFP_OUTPUT_DIR=./output

Or copy local_settings_example.py to local_settings.py and set
BQ_PROJECT_ID there. Environment variables in local_settings_example.py
are the defaults; local_settings.py overrides them.

Run:

    # Smoke test: 16 of 256 partitions.
    ./run.sh -o $RFP_OUTPUT_DIR/smoke --cache-dir $RFP_CACHE_DIR \
        -c configs/paper_indvmetrics_shannon_hhi.py \
        --per-os=true --skip-progress-bars -w "0?"

    # Full run: drop -w "0?".


Paper Tables and Figures
========================

Three-stage pipeline:

1. analyze.py (via run_all.sh) produces output directories with
   pickled .bin files. correlation.py produces AMI/Theil CSVs.
2. gen_outputs/ scripts post-process the pickles into CSVs and
   text files within each output directory.
3. gen_gfx/ scripts consume those CSVs to produce final paper
   artifacts (PNGs, LaTeX table bodies). See gen_gfx/README.md
   for per-script documentation.

gen_outputs/ scripts (run manually on each output directory):

  gen_outputs/gen_alldata_output.py <output_dir>
    Reads alldata.bin, produces per-fingerprinter CSVs and graphs.
  gen_outputs/gen_experiment_output.py <output_dir>
    Reads exp_*.bin and mode_*.bin, produces per-experiment CSVs.
  gen_outputs/gen_experiment_output_compare.py <output_dir>
    Reads experiment CSVs, produces Overall vs OS Average comparison.
  gen_outputs/gen_metrics_output.py <output_dir>
    Reads metric_aggregation_output.bin, produces entropy/HHI CSVs.
  gen_outputs/gen_smr_output.py <output_dir>
    Reads smr.bin, produces SMR importance CSVs and graphs.
  gen_outputs/gen_lmr_output.py <output_dir>
    Reads lmr.bin, produces LMR importance CSVs and graphs.
  gen_outputs/run_ismr_ismrp_comparison.py <dir> [<dir2>]
    Compares ISMR vs ISMRP rankings side by side.

All are idempotent (sentinel files prevent re-generation).

The paper tex file is at ../rfp_paper/fpp_paper.tex; graphics are
referenced from its graphics/ directory.

Table (tab:fingerprinters) — Baseline uniqueness by fingerprinter and OS
  Data:   gen_gfx/experiment_table/01_build_csv.py -> table1_baseline.csv
  LaTeX:  gen_gfx/experiment_table/02_build_latex.py (updates tex in-place)
  Config: paper_uniqueness_tables_additive_realistic.py (baseline row)

Table (tab:webapis) — Fingerprinting techniques and proposed protections
  Manual table in fpp_paper.tex.

Table (tab:improvements) — Cumulative improvement per OS
  Data:   gen_gfx/experiment_table/01_build_csv.py -> table3_experiments.csv
  LaTeX:  gen_gfx/experiment_table/02_build_latex.py
  Note:   01_build_csv.py --table3-fp selects fingerprinter (default FPJSv2_Realistic).

Table (tab:improvements_overall) — Cumulative improvement, weighted avg
  Data:   gen_gfx/experiment_table/01_build_csv.py -> table3_overall.csv
  LaTeX:  gen_gfx/experiment_table/02_build_latex.py

Table (tab:individual) — Individual improvement per OS
  Data:   gen_gfx/experiment_table/01_build_csv.py -> table5_individual.csv
  LaTeX:  gen_gfx/experiment_table/02_build_latex.py
  Config: paper_uniqueness_tables_individual_realistic.py

Table (tab:individual_overall) — Individual improvement, weighted avg
  Data:   gen_gfx/experiment_table/01_build_csv.py -> table5_overall.csv
  LaTeX:  gen_gfx/experiment_table/02_build_latex.py

Table (tab:investigate_causes) — Conjectured causes for per-platform outliers
  Manual table in fpp_paper.tex.

Table (tab:fingerprinter_metrics) — Metrics collected by each fingerprinter
  Script: gen_gfx/fingerprinters_tables/build_table.py -> table.tex
  Input:  iterative_minmetrics_*_Realistic.csv from iterative_minmetrics runs
  Config: iterative_minmetrics_fpjsV2.py, _akamaiV2.py, _signifyd.py

Table (tab:iterative_top20_by_os) — Top 20 metrics by iterative construction
  Script: gen_gfx/iminmetrics_table/build_table.py -> table.tex
  Input:  iterative_minmetrics_*_os_<OS>.csv from iterative_minmetrics runs
  Config: iterative_minmetrics_fpjsV2.py, _akamaiV2.py, _signifyd.py

Figure (fig:sufficientdata) — Effect of dataset size on uniqueness
  Script: gen_gfx/buckets/graph.py -> fingerprint_buckets_plot.png
  Input:  fingerprint_buckets.csv (copied from analyze.py output
          into buckets/realistic/ or buckets/worstcase/)

Figure (fig:indvmetrics) — Individual measurement impact (scatter + table)
  Data:   gen_gfx/indv_metrics/01_build_csv.py -> metric_table.csv
  Graph:  gen_gfx/indv_metrics/make_graph_scatter.py -> metric_scatter.png
  Table:  gen_gfx/indv_metrics/02_update_tex_table.py (updates tex in-place)
  Config: paper_indvmetrics_shannon_hhi.py, paper_indvmetrics_smr_*_realistic.py

Figure (fig:minmetrics) — Cumulative uniqueness, weighted avg across OSes
  Script: gen_gfx/iminmetrics/viz_minmetrics_weighted_avg.py -> viz_minmetrics_1.png
  Input:  iterative_minmetrics_*.csv from iterative_minmetrics runs
  Config: iterative_minmetrics_fpjsV2.py, _akamaiV2.py, _signifyd.py

Figure (fig:cumulative_improvement) — Cumulative protection impact (2x2 grid)
  Script: gen_gfx/experiment_table/05_graph.py -> protection_overview.png
  Input:  table3_experiments.csv, table3_overall.csv

Figure (fig:individual_improvement) — Individual protection impact (bar chart)
  Script: gen_gfx/experiment_table/04_graph.py -> protections_individual.png
  Input:  table5_overall.csv

Figure (fig:minmetrics_all) — Cumulative uniqueness per fingerprinter per OS
  Script: gen_gfx/iminmetrics/viz_minmetrics_all.py -> viz_minmetrics_1c.png
  Input:  iterative_minmetrics_*.csv from iterative_minmetrics runs
  Config: iterative_minmetrics_fpjsV2.py, _akamaiV2.py, _signifyd.py

Other gen_gfx scripts (not directly in paper):
  gen_gfx/experiment_table/03_graphs.py -> phase_endpoints_by_os.png
    Per-OS phase endpoint comparison (2x2 grid).
  gen_gfx/minset/viz_minset.py
    Min-set combination analysis (dedup_waterfall, cumulative_pct, etc.)
  gen_gfx/minset/viz_top_combo_by_os.py -> viz_top_combo_by_os.png
    Best combo per size, per OS line graph.
  gen_gfx/minset/grid_waterfall.py -> minset_waterfall_grid.png
    Waterfall charts of deduplicated metric combinations.
  gen_gfx/correlation-ami/, gen_gfx/correlation-thiels/
    AMI and Theil's U correlation visualizations.
    See gen_gfx/README.md for details.

BigQuery Aggregate Pipeline (db_queries/)
==========================================

db_queries/aggregate_datasets/ contains a template-based SQL pipeline
that builds per-OS aggregate tables in BigQuery. These tables feed
correlation.py (AMI / Theil's U) and ad-hoc analysis via bq.py.

generate_sql.py renders .sql.template files into per-OS .sql files
using {{PLACEHOLDER}} substitution. Generated .sql files are
gitignored — regenerate them with:

    cd db_queries/aggregate_datasets
    python3 generate_sql.py                      # defaults
    python3 generate_sql.py --dataset mydata     # override dataset
    python3 generate_sql.py --os Windows         # one OS only
    python3 generate_sql.py --dry-run            # list output files

The pipeline runs in two phases (all 4 OSes can run in parallel):

  Phase 1:
    process_00            — CREATE SCHEMA (global, once)
    process_02            — LatestSubmission_tbl (global dedup across
                            Desktop + Fenix by latest submission)
    process_01_{OS}       — Exploded table schema (typed columns)
    process_03_{OS}       — Populate Exploded (JOIN to LatestSubmission)
    process_05_{OS}       — DoubleExploded schema (metric/value pairs)
    process_06-11_{OS}    — UNPIVOT by data type into DoubleExploded
    process_09b_{OS}      — CPU/GPU model classification
    process_12_{OS}       — MetricSubmissionCounts
    process_13_{OS}       — MetricValueCounts
    detect_identical_{OS} — Find metrics with identical distributions

  [Pause: review identical metrics, optionally re-run generate_sql.py
   with --identical-drop-{os} files to exclude them]

  Note: on the aggregatedata2 run, detect_identical_metrics produced
  empty results on all OSes because the STRING_AGG fingerprint
  exceeded BigQuery's 100MB row limit for high-cardinality metrics.
  The template has since been fixed (SHA256 wrapping). The current
  aggregate tables contain ~36 redundant identical-metric pairs per
  OS in x_by_y (e.g. gl_precision_fragment = gl_precision_vertex,
  STENCIL_BACK_* = STENCIL_*, MAX_RENDERBUFFER = MAX_TEXTURE). These
  don't affect correctness but inflate the correlation data slightly.

  Phase 2:
    x_groupings_13_{OS}          — Single-metric value distributions
    x_by_y_groupings_14_{OS}     — Cross-metric co-occurrence (chunked
                                    into ~21 pieces to manage BQ cost)
    validate_{OS}                — 28-check validation suite

Per-OS table naming: Exploded_Windows_tbl, DoubleExploded_Android_tbl,
UserCharacteristics_Linux_x_by_y_tbl, etc.

Excluded metrics:

x_by_y_groupings_14 (the cross-metric self-join) excludes ~174
metrics to keep the table size manageable. The exclusion list in
generate_sql.py was manually curated by reviewing cardinality from
MetricValueCounts — generally metrics with >50k distinct values on
Windows. Excluded categories:

  - Individual clientrects (kept: combined hashes)
  - Individual WebGL/wgpu parameters (kept: fallback_adapter,
    missing_features)
  - Individual gl_params and gl2_params
  - Sensor data (motion/orientation decimals and frequencies)
  - Device peripherals (camera/mic/speaker counts, voices)
  - Canvas data blobs and font variant raw hashes
  - Metadata (submission_schema, build_date, channel, errors,
    os_name — redundant since tables are per-OS)

Per-OS additions: Linux excludes WebGL2 extensions and clientrects
emoji hashes; Android excludes languages and accept_languages.

Excluded metrics remain in MetricValueCounts and x_groupings
(single-metric distributions); only x_by_y filters them out.

db_queries/debugging/ has ad-hoc diagnostic queries (schema counts,
missing os_name clients, legacy column checks, new metric sanity).

Correlation visualizations live in gen_gfx/correlation-ami/ and
gen_gfx/correlation-thiels/; see gen_gfx/README.md for details.
