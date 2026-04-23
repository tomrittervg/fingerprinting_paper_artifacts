Python toolkit that reads Firefox telemetry from BigQuery, computes
per-vendor fingerprint hashes, measures per-metric entropy, and
simulates proposed countermeasures (fdlibm math, font allowlists,
processor-count clamping, timezone normalization, accept-language
collapsing, WebGL sanitization, and others).

One config per paper result, passed to analyze.py via -c:

- paper_indvmetrics_shannon_hhi.py: per-metric Shannon entropy and HHI.
- paper_indvmetrics_smr_<vendor>.py: Single-Metric-Removal per vendor
  (akamaiV2, fpjsV2, signifyd).
- paper_indvmetrics_lmr_<vendor>.py: Logical-Metric-Removal per vendor.
- ismr.py, ismrp_<OS>.py: iterative SMR and replacement.
- min_set_top*_smr*.py: min-set combinations, overall and per-OS.
- paper_uniqueness_tables_individual.py: uniqueness under individual
  protections.
- paper_uniqueness_tables_additive.py: uniqueness under cumulative
  protections.
- paper_correlation.py: pairwise correlation, run via correlation.py.

run_all.sh batches run.sh calls; uncomment the targets you want. Each
config's docstring names the table or figure it produces.

Requirements:

- Python 3.14 free-threaded (python3.14t). Always use ./run.sh; it
  sets PYTHON_GIL=0. Calling analyze.py directly aborts.
- Packages in requirements.txt. grpcio is skipped: no cp314t wheel,
  and the REST BigQuery path does not need it.
- CPU only.

Data: set GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON
with BigQuery read, and set BQ_PROJECT_ID. Or copy
local_settings_example.py to local_settings.py and edit.

Run:

    python3.14t -m venv .venv
    .venv/bin/pip install -r requirements.txt

    export GOOGLE_APPLICATION_CREDENTIALS=/abs/path/creds.json
    export BQ_PROJECT_ID=<project>
    export RFP_CACHE_DIR=./cache RFP_OUTPUT_DIR=./output

    # Smoke test: 16 of 256 partitions, finishes in minutes.
    ./run.sh --start-day 20260325 --end-day 20260417 \
        -o $RFP_OUTPUT_DIR/smoke --cache-dir $RFP_CACHE_DIR \
        -c configs/paper_indvmetrics_shannon_hhi.py \
        --partition-width 2 --per-os=true --skip-progress-bars \
        -w "0?"

    # Full run: drop -w "0?".
    ./run.sh --start-day 20260325 --end-day 20260417 \
        -o $RFP_OUTPUT_DIR/smr_akamaiV2 --cache-dir $RFP_CACHE_DIR \
        -c configs/paper_indvmetrics_smr_akamaiV2.py \
        --partition-width 2 --per-os=true --skip-progress-bars

Output goes to <output>_<timestamp>/: CSVs, PDF and PNG graphs,
pickles, and a log. The BigQuery cache is shared across configs;
prime it on the first run.

./run.sh --help lists all flags.
