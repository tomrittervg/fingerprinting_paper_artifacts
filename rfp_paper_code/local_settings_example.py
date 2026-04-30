"""Shareable default settings for the fingerprinting analysis toolkit.

This file is committed to the repository and is safe to share. It
defines every setting the code needs, with defaults that either come
from environment variables or are harmless placeholders.

To override values for your own machine, create `local_settings.py`
next to this file. `local_settings.py` is git-ignored. Anything it
defines overrides the defaults here. See the pattern in `settings.py`.

Environment variables honored (override the hardcoded defaults in this
file, but are themselves overridden by `local_settings.py`):
    BQ_PROJECT_ID           BigQuery project for bq.py / correlation.py
    RFP_CACHE_DIR           Default --cache-dir for analyze.py
    RFP_OUTPUT_DIR          Default -o output base for analyze.py / run_all.sh
    RFP_MIN_SET_AGG_PATH    Path to a prior run's metric aggregation .bin
"""

import os

# BigQuery project. Used by bq.py, validate_combined_hashes.py, and
# the correlation configs. Dataset names are kept literal in the
# per-config files since they describe which data each config uses.
BQ_PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "YOUR_BQ_PROJECT_ID")

# Default cache directory for analyze.py and run_all.sh.
DEFAULT_CACHE_DIR = os.environ.get("RFP_CACHE_DIR", "./simulated-cache")

# Default output directory base. analyze.py appends a timestamp.
DEFAULT_OUTPUT_DIR = os.environ.get("RFP_OUTPUT_DIR", "./simulated-output")

# Path to a prior metric_aggregation_output.bin file. Required only
# by the min_set_top* configs that consume a previous run's output.
MIN_SET_METRIC_AGGREGATION_PATH = os.environ.get(
    "RFP_MIN_SET_AGG_PATH",
    "./cache/metric_aggregation_output.bin",
)
