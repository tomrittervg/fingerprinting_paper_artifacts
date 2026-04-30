"""Analysis configuration for generating SMR (Single Metric Removal) data
for the Individual Metric Analysis table in the paper.

Enables only SMR and the FingerprintJS baseline fingerprint (required by SMR).
HHI and Shannon entropy are handled by configs/paper_indvmetrics_shannon_hhi.py —
run that first (it's much cheaper), then run this for the SMR columns.

Run with:
  GOOGLE_APPLICATION_CREDENTIALS=/work/code/application_default_credentials.json \
  ./analyze.py --start-day YYYYMMDD --end-day YYYYMMDD \\
    -o /home/sandbox/tmp --cache-dir /work/sandbox-cache \\
    --partition-width 2 \\
    -c configs/paper_indvmetrics_smr.py --skip-progress-bars

Test with 16 partitions first to verify memory usage:
  ... -w "0?" ...

Note on parallelism: SMR is CPU-bound (SHA1 per user per metric, ~85 metrics
total in FPSET_FINGERPRINTJS_V1). The GIL-free python3 build can saturate
all cores. max_procs=8 is set conservatively — increase to 16 if
RAM allows (each worker holds ~15-20 KB/user × 43K users/partition).
"""


script_config = {
    'per_os_analysis':              True,
    'print_x_by_os_aggregate_graphs':                    False,
    'raw_rows_only':                 False,
    'max_procs':               8,    # conservative: 8 workers × ~650 MB/partition = ~5 GB peak DataValues
    'max_worker_threads':    None,  # threads per worker for parallelizing operations; None = auto (floor(100 / max_procs))
    'max_threads_graph_export':      8,
    'max_threads_experiment_merging': 4,

    # -------------------
    # Metric aggregation disabled — HHI/Shannon already covered by paper_individual_metrics.py
    'calculate_metrics_aggregated':     False,
    'calculate_metric_experiment_aggregated': False,
    # -------------------
    # -------------------
    # fingerprints=True is auto-enabled by SMR (see analyze.py ~line 322), but
    # explicit here for clarity.  Only FingerprintJS is needed.
    'fingerprints':                     True,
    'fingerprints_output':              False,
    'browser_modes':                    False,
    'experiments':                      False,
    'print_cohort_size_tables':         False,

    # -------------------
    'fingerprint_buckets':              False,
    'metric_buckets':                   False,

    # -------------------
    'fingerprint_archiving':            False,

    # -------------------
    'missing_fonts':                    False,
    'missing_font_sets':                False,

    # -------------------
    'perform_segmentation_shitty':              False,
    'perform_segmentation_decision_tree':       False,

    # -------------------
    'perform_single_metric_removal_analysis':             False,
    'perform_iterative_single_metric_removal_analysis':   False,
    'perform_iterative_single_metric_replacement_analysis': False,
    'perform_min_set_combo_analysis':       False,

    # -------------------
    # Logical Metric Removal — runs against AkamaiV2, FPJSv2, Signifyd
    'perform_logical_metric_removal_analysis':            True,
    'lmr_output':                                         False,
    'lmr_fingerprinters':                                 {'AkamaiV2', 'FPJSv2', 'Signifyd'},

    # -------------------
    # Segmentation (disabled)
    # -------------------
    # Correlation analysis (disabled)
    'correlation_analysis':               False,
}


def num_modes_enabled(sc):
    return sum([
        sc['fingerprints'],
        sc['browser_modes'],
        sc['experiments'],
        sc['fingerprint_buckets'],
        sc['metric_buckets'],
        sc['fingerprint_archiving'],
        sc['missing_fonts'],
        sc['perform_segmentation_shitty'],
        sc['perform_segmentation_decision_tree'],
        sc['perform_single_metric_removal_analysis'],
        sc['perform_iterative_single_metric_removal_analysis'],
        sc.get('perform_logical_metric_removal_analysis', False),
    ])


def should_keep_sequencing(sc):
    return num_modes_enabled(sc) > 1


# =============================================================================
# Fingerprinter / experiment / archiving constants
# =============================================================================

# The SMR baseline fingerprinter is auto-added to FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS
# by analyze.py when perform_single_metric_removal_analysis is True, so this can stay empty.
FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS = {}

METRIC_EXPERIMENTS = []
METRIC_EXPERIMENTS_BY_KEY = {}
CALCULATIONS_FOR_ARCHIVING = []
FINGERPRINTERS_FOR_EXPERIMENTS = {}
FINGERPRINTERS_FOR_MODES = {}
EXPERIMENTS_TO_RUN = {}
EXPERIMENTS_TO_RUN_ADDITIVE = []
EXPERIMENT_LONG_NAMES = {}