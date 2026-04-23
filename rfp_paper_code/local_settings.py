"""Author-specific settings overrides. GIT-IGNORED. Delete before sharing.

This file overrides the safe defaults in `local_settings_example.py`
with the real values used on the author's machine (BigQuery project,
cache/output directories, etc.).

It is listed in .gitignore and MUST NOT be committed. For artifact
sharing: simply delete this file; the code falls back to
`local_settings_example.py` and the reviewer copies the example to
`local_settings.py` to plug in their own values.
"""

BQ_PROJECT_ID = "moz-fx-dev-tritter-fpanalysis"

DEFAULT_CACHE_DIR = "/home/tom/moz/fingerprinting-data/sandbox-cache"
DEFAULT_OUTPUT_DIR = "/home/tom/moz/fingerprinting-data/sandbox-analyses"

MIN_SET_METRIC_AGGREGATION_PATH = (
    "/home/tom/moz/fingerprinting-data/sandbox-analyses/final-range/"
    "shannon_0405_1775405874/metric_aggregation_output.bin"
)
