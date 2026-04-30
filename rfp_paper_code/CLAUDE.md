# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Firefox browser fingerprinting analysis toolkit. It processes telemetry data (~200+ metrics per user) from Firefox clients, computes fingerprint hashes over configurable metric subsets, and analyzes uniqueness/cohort distributions. It also simulates proposed Firefox privacy protections (e.g. fdlibm math, font allowlists, processor count clamping) to measure their impact on fingerprint entropy.

## Running

```bash
./analyze.py --start-day YYYYMMDD --end-day YYYYMMDD \
  -o <output-dir> --cache-dir <cache-dir> [options]
```

The shebang (`#!/usr/bin/env python3`) invokes the free-threaded Python 3.14t build via a venv that has all required packages. Always use `./analyze.py` (not `python3 analyze.py`) to get GIL-free execution with all dependencies available.

**The venv at `/home/sandbox/venv314t` is ephemeral** — `/home/sandbox` is not persisted across sandbox restarts. If it is missing, recreate it:

```bash
# One-time venv setup (re-run after sandbox restart if ./analyze.py fails with ModuleNotFoundError)
python3.14t -m venv /home/sandbox/venv314t
/home/sandbox/venv314t/bin/pip install --only-binary :all: \
    numpy scikit-learn scipy tqdm matplotlib pillow
/home/sandbox/venv314t/bin/pip install setuptools
/home/sandbox/venv314t/bin/pip install --no-deps google-cloud-bigquery
/home/sandbox/venv314t/bin/pip install \
    google-auth google-api-core google-cloud-core db-dtypes \
    google-resumable-media
```

Notes:
- `grpcio` has no pre-built wheel for `cp314t` and its build is broken under python3.14t due to a multiprocessing pipe bug. It is intentionally excluded. The BigQuery usage here (standard query jobs via REST) does not require grpcio.
- `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `pillow` all have `cp314t` wheels on PyPI — use `--only-binary :all:` for them.
- After setup, confirm with: `/home/sandbox/venv314t/bin/python3.14t -c "import tqdm, numpy, sklearn, matplotlib; from google.cloud import bigquery; print('OK')"`

Key flags:
- `--start-day` / `--end-day`: date range (end is exclusive)
- `--cache-dir`: directory for BigQuery data cache and processed pickles
- `-o`: output directory (actual output goes to `<dir>_<timestamp>`)
- `-c FILE`: config file to use (default: `script_config.py`)
- `--platform desktop|mobile`: filter to one platform
- `-w`: hex partition prefix wildcard (e.g. `"0?"` = 16 partitions for testing)
- `-q` / `--quasi-sequential`: retain all DataValues in memory (needed for segmentation)
- `--partition-width 0|1|2`: partitioning granularity (0=none, 1=16, 2=256)
- `-m` (minimize memory), `--tiny` (tiny mode), `--skip-progress-bars`

### Configs

Analysis behavior is controlled by a `script_config` dict. The default is `script_config.py` in the repo root. Alternative configs live in `configs/`:
- `configs/metrics.py` — standard metrics/entropy/fingerprint analysis
- `configs/segment.py` — segmentation analysis (use with `-q`)

Pass with `-c configs/metrics.py`. These files import experiment/mode filters and define which analyses to run by toggling booleans in the `script_config` dict.

### Sandbox paths

When running in the sandbox environment:
- **Cache**: `--cache-dir /work/sandbox-cache` (persisted; use this when it exists)
- **Output / scratch**: `-o /work/tmp` or `-o /home/sandbox/tmp` (both writable; `/home/sandbox` is scratch space, `/work` is persisted)
- **Credentials**: `GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json`
- **Matplotlib**: `MPLCONFIGDIR=/tmp/claude-999/mpl` (prevents write errors in sandbox)

```bash
GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
./analyze.py --start-day 20260301 --end-day 20260310 \
  -o /home/sandbox/tmp --cache-dir /work/sandbox-cache \
  -c configs/metrics.py --skip-progress-bars \
  -w "0?"   # 16 partitions for testing; omit for full run
```

After changing filters, clear stale processed caches (keeps raw data):
```bash
find /work/sandbox-cache -type d -name ranges -exec rm -rf {} +
```

### BigQuery utility

`bq.py` is a standalone script for running read-only BigQuery queries directly (without going through `analyze.py`):

```bash
GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
/home/sandbox/venv314t/bin/python3.14t bq.py <sql_file>        # run a .sql file
/home/sandbox/venv314t/bin/python3.14t bq.py -q "SELECT ..."   # inline query
/home/sandbox/venv314t/bin/python3.14t bq.py -                 # read from stdin
```

Output flags: `--csv`, `--json`, `--limit N`, `--no-header`. Default output is TSV. Only `SELECT`/`WITH` queries are allowed; mutating statements are rejected.

No test suite exists.

## Architecture

### Data Pipeline

1. **Ingestion** (`data.py`): Reads raw records from pickle files or database partitions in `config.ANALYSIS_FOLDER`
2. **Parsing** (`datavalues.py`): `DataValues.__init__` parses a raw record dict into ~200+ typed attributes using `value_wrap`/`value_wrapi` helpers (return `"None"` string or `0` int for missing values)
3. **Filtering** (`filters.py`, `experiments.py`, `modes.py`): Filters modify `DataValues` in-place; applied via `DataValues.add_filter()` and removed via `DataValues.pop_filter()` in LIFO order
4. **Calculation** (`calculations.py`): Metric aggregation, entropy calculation, fingerprint computation, cohort analysis
5. **Output** (`graphing.py`, `segmentation.py`): Bar graphs, CDFs, stacked bars, aggregate tables, segmentation analysis → written to `config.OUTPUT_FOLDER`

### Filter System

Filters inherit from `Filter` (defined in `filters.py`). The pattern:
- `apply(dataValues)`: Modify attributes in-place, storing originals in `self.originals`
- `revert(dataValues)`: Restore saved originals
- `DataValues.add_filter(FilterClass)` pushes onto `self.applied_filters` stack
- `DataValues.pop_filter()` calls `revert()` and pops

Filter categories:
- **Correction filters** (`filters.py`): Fix data quality issues (HDR values, processor counts)
- **Display filters** (`filters.py`): Transform values for human readability (hex colors, WebGL constants)
- **Experiment filters** (`experiments.py`): Simulate proposed protections (fdlibm, font lists, timezone normalization, accept-language collapsing)
- **Mode filters** (`modes.py`): Simulate browser modes (RFP = resistFingerprinting, ETP = Enhanced Tracking Protection)

### Metric Subsets and Fingerprinters

`DEFAULT_SUBSET` in `datavalues.py` is defined as a static set (`_DEFAULT_SUBSET_BASE`) of all DataValues attribute names, excluding bookkeeping members listed in `_DEFAULT_IGNORE_SET`. Dynamic `math_op_*` attributes are added at runtime. A runtime assertion (`_validate_and_complete_default_subset`) kills the program if the static definition doesn't match `vars(dv)`, catching drift when new telemetry attributes are added to `DataValues.__init__` without updating `_DEFAULT_SUBSET_BASE`.

`fingerprinters.py` defines named subsets (AKAMAI_SUBSET, SIFT_SCIENCE_SUBSET, FINGERPRINTJS_SUBSET, etc.) approximating what real-world fingerprinting services collect.

`DataValues.fingerprint(subset, algorithm)` hashes the selected attributes using `SHA1Fingerprint` (default) or `ConcatFingerprint` (for debugging).

### Key Conventions

- Telemetry values that are missing use the string `"None"` (not Python `None`) via `value_wrap()`, or `0` via `value_wrapi()`. Code throughout checks `== "None"` as a sentinel.
- `config.py` holds global mutable state (`ANALYSIS_FOLDER`, `OUTPUT_FOLDER`, `PATTERN_HASH`, `FILESET_HASH`) that `analyze.py` monkey-patches at startup.
- `script_config.py` is the default analysis config; `configs/metrics.py` and `configs/segment.py` are alternatives passed via `-c`. All define a `script_config` dict of booleans controlling which analyses run.
- Pickle caching is used heavily — `DataValues` arrays and metric aggregations are pickled/unpickled keyed by hash values for performance. Cache layout: `<cache-dir>/<partition-hash>/days/<date>/` (raw rows) and `ranges/` (processed DataValues).
- `analyze.py` redirects stdout/stderr through `config.Tee` and `config.CleanStream` for logging.
