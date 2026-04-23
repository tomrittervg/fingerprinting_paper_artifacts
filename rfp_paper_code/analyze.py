#!python3.14t

import os
import sys
if not os.environ.get('ANALYZE_VIA_WRAPPER'):
    print("ERROR: analyze.py must be run via ./run.sh (ensures PYTHON_GIL=0).", file=sys.stderr)
    sys.exit(1)

import gc
import hashlib
import shutil
import csv
import time
import argparse
import pickle
from math import log2
from collections import Counter, defaultdict, OrderedDict
import multiprocessing
from multiprocessing import Process, Queue
from partition_worker import worker_init, partition_worker

from datetime import date, timedelta

import threading
import tqdm
import concurrent.futures
import matplotlib.pyplot as plt


import config

from cohort import cohort_fitness, cohort_fitness_excluding_singletons, cohort_p50
from utility import validate_filters_update_combined_hashes
from datavalues import (
    parse_datavalues,
    DEFAULT_SUBSET, DEBUGPRINT_SUBSET,
    _validate_and_complete_default_subset,
)
from data import *
from webgl_constants import set_unknown_extensions_path
from settings import DEFAULT_CACHE_DIR
from fingerprinters import *
from filters import *
from experiments import *
from modes import *
from graphing import *
from calculations import *
from segmentation import *
from smr import output_smr, output_ismr, output_ismrp, run_lmr_analysis, LMR_FINGERPRINTERS_DEFAULT, build_lmr_unit_lists
from partition_worker import ismr_iteration_worker, ismrp_iteration_worker, min_set_combo_worker  # pinned workers
from output import (
    visualize_metrics_aggregated, visualize_metrics_by_os,
    process_fingerprint_archiving, print_fingerprint_results,
    print_fingerprint_bucket_results, print_metric_bucket_results,
    analyze_missing_fonts, run_segmentation,
)
from script_config import (
    validate_config, CONFIG_DEPENDENCIES,
    FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS, METRIC_EXPERIMENTS_BY_KEY,
    CALCULATIONS_FOR_ARCHIVING, FINGERPRINTERS_FOR_EXPERIMENTS,
    FINGERPRINTERS_FOR_MODES,
    EXPERIMENTS_TO_RUN, EXPERIMENTS_TO_RUN_ADDITIVE,
    EXPERIMENT_SLUG_MAP, EXPERIMENT_EQUIVALENTS,
)
import random
import numpy as np
from progress import ProgressDisplay


def merge_counter(target, source):
    """Recursively merge source counter dict into target. Works for nested defaultdict(int)."""
    for key, value in source.items():
        if isinstance(value, dict):
            merge_counter(target[key], value)
        else:
            target[key] += value


def collapse_os_layer(os_bucketed):
    """Collapse {os: {hash: count}} into {hash: count} by summing across OSes."""
    result = defaultdict(int)
    for _os_dict in os_bucketed.values():
        for h, c in _os_dict.items():
            result[h] += c
    return dict(result)


def _merge_fp_categories(target, source):
    """Merge fingerprinter→category-list structures.

    Both target and source are {fpname: [cat_list]} where each element
    of cat_list is [label, getter_fn, data_dict, count_dict].
    Categories are matched by index (both sides are produced by the same
    get_categories() call, so length and order are identical).
    """
    for fpname, src_cats in source.items():
        tgt_cats = target[fpname]
        for i, (_, _, src_data, src_counts) in enumerate(src_cats):
            _, _, tgt_data, tgt_counts = tgt_cats[i]
            merge_counter(tgt_data, src_data)
            merge_counter(tgt_counts, src_counts)


def _progress_bridge(queue, slots, stop_event) -> None:
    """Drain worker progress events and apply them to ProgressDisplay slots.

    Runs in a daemon thread in the main process.  Workers post phase-transition
    events (start/advance/rename/finish) and 5%-granularity update events.
    """
    import queue as _queue_mod
    while not stop_event.is_set() or not queue.empty():
        try:
            msg = queue.get(timeout=0.05)
        except _queue_mod.Empty:
            continue
        except Exception:
            continue
        slot_idx, event, *args = msg
        if slot_idx >= len(slots):
            continue
        slot = slots[slot_idx]
        if event == 'start':
            slot._start(*args)
        elif event == 'advance':
            slot.advance_phase(*args)
        elif event == 'rename':
            slot.rename_phase(*args)
        elif event == 'update':
            slot.update_progress(args[0])
        elif event == 'rss':
            slot.rss_mb = args[0]
        elif event == 'finish':
            slot.finish()


def apply_post_pickle_corrections(data):
    """Apply webGLParamMetricFilter to old caches missing expanded webGL attrs."""
    if data and not hasattr(data[0], 'webgl2_params_ALIASED_LINE_WIDTH_RANGE'):
        for d in data:
            d.add_filter(webGLParamMetricFilter)


def setup_subsets(metric_aggregation, metric_buckets):
    """Compute metrics_to_visualize, etc. from the static DEFAULT_SUBSET.

    Mutates metric_aggregation, metric_buckets, and DEFAULT_SUBSET dicts in-place.
    Returns (DEFAULT_SUBSET, DEBUGPRINT_SUBSET, metrics_to_visualize, metrics_to_run_bucketing_for).
    """
    DEFAULT_SUBSET.update({
        "hw_cpu_model_manufacturer", "hw_cpu_model_family",
        "hw_cpu_model_microarch", "hw_cpu_model_model",
        "webgl_renderer_raw_vendor", "webgl_renderer_raw_family",
        "webgl_renderer_raw_model", "webgl_renderer_raw_api",
        "hw_machine_model_vendor", "hw_machine_model_category",
        "hw_machine_model_family",
    })
    prefixes_to_remove = (
        "webgl_extensions_", "webgl_extensions_software_",
        "webgl2_extensions_", "webgl2_extensions_software_",
        "webgl_extensions_raw_", "webgl_extensions_raw_software_",
        "webgl2_extensions_raw_", "webgl2_extensions_raw_software_",
    )
    metrics_to_visualize = sorted(
        m for m in (
            set(DEFAULT_SUBSET) - {
                "screens", "missing_fonts", "hw_gamepads",
                "math_ops_fdlibm",
                "webgl_params_json", "webgl2_params_json",
                "webgl_params_json_software", "webgl2_params_json_software",
                'webgl_params_extensions_json', 'webgl_params_extensions_json_software',
                'webgl2_params_extensions_json', 'webgl2_params_extensions_json_software',
                "screen_scalings_list"
            }
        )
        if not any(m.startswith(prefix) for prefix in prefixes_to_remove)
    )
    print(f"{len(metrics_to_visualize)} metrics to visualize\n")

    for metric in metrics_to_visualize:
        metric_aggregation[metric] = defaultdict(int)

    # I don't expect to run metric bucketing again
    metrics_to_run_bucketing_for = set() #FPSET_FINGERPRINTJS_V1.union(FPSET_SIFT_SCIENCE).union(FPSET_AKAMAI_V2) - set(["math_ops", "math_ops_fdlibm"])
    for i in range(1, 41):
        likelihood = i * 0.025
        metric_buckets[likelihood] = {metric: [defaultdict(int), 0] for metric in metrics_to_run_bucketing_for}

    return DEFAULT_SUBSET, DEBUGPRINT_SUBSET, metrics_to_visualize, metrics_to_run_bucketing_for


# ==============================================================================
# --- Argument parsing
# ==============================================================================
def parse_args():
    p = argparse.ArgumentParser(
        description="Run the full fingerprinting-data analysis pipeline."
    )
    p.add_argument(
        "-o", "--output-folder",
        help=f"Where to write pickles & graphs"
    )
    p.add_argument(
        "-w", "--wildcard",
        nargs="+",
        default=["*"],
        help="String to substitute for the '*' in set-*-data.txt (default='*')"
    )
    p.add_argument(
        "--platform",
        choices=["desktop", "mobile"],
        help="Analyze only desktop or mobile data"
    )
    p.add_argument(
        "-m", "--minimize",
        action="store_true",
        help="Remove unnecessary data from DataValues to reduce memory usage"
    )
    p.add_argument(
        "-q", "--quasi-sequential",
        action="store_true",
        help="Run analysis in quasi-sequential mode, which reads and processes records in batches, but retains the entire DataValues array"
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable saving or loading cached data (always recompute, never write cache)"
    )
    p.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Ignore existing cache files and recompute from scratch, then write fresh cache"
    )
    p.add_argument(
        "--tiny",
        action="store_true",
        help="Enable tiny mode"
    )
    p.add_argument(
        "--start-day",
        default="2026-03-25",
        help="Start date inclusive (YYYY-MM-DD) [default: 2026-03-25]"
    )
    p.add_argument(
        "--end-day",
        default="2026-04-17",
        help="End date exclusive (YYYY-MM-DD) [default: 2026-04-17]"
    )
    p.add_argument(
        "--skip-progress-bars",
        action="store_true",
        help="Suppress auto-updating progress bars (useful for non-interactive / log output)"
    )
    p.add_argument(
        "--partition-width",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="Hex chars for document_id partitioning (0=none, 1=16, 2=256 partitions) [default: 2]"
    )
    p.add_argument(
        "-c", "--config",
        default=None,
        metavar="FILE",
        help="Python config file to use instead of script_config.py"
    )
    p.add_argument(
        "--cache-dir",
        default=None,
        metavar="DIR",
        help="Data/cache directory (default: settings.DEFAULT_CACHE_DIR if it exists, else /work/sandbox-cache)"
    )
    p.add_argument(
        "--schema",
        default="37",
        metavar="N",
        help="Minimum submission schema version to include (default: 37)"
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Bypass the concurrent-process safeguard check"
    )
    p.add_argument(
        "--per-os",
        choices=["true", "false", "only"],
        default=None,
        dest="per_os",
        help="Override per_os_analysis config: true, false, or only"
    )
    p.add_argument(
        "--os-filter",
        default=None,
        dest="os_filter",
        help="Restrict analysis to one OS (e.g. WINNT, Android, Darwin, Linux)"
    )
    return p.parse_args()

def get_os(d):
    return d.os

def get_os_arch(d):
    return f"{d.os}-{d.hw_cpu_arch}"

def get_mac_model(d):
    return "" if d.os != "Darwin" else d.hw_machine_model
# This is a list of categories of clients we want to calculate the fingerprints for, for special analysis
def get_categories(script_config, include_extras=False, include_os=False, include_os_arch=False):
    cats = []
    if include_extras or include_os:
        cats.append(["OS: ", get_os, defaultdict_defaultdict_int(), defaultdict(int)])
    if include_extras or include_os_arch:
        cats.append(["OS+Arch: ", get_os_arch, defaultdict_defaultdict_int(), defaultdict(int)])
    if include_extras:
        cats.append(["Mac Model: ", get_mac_model, defaultdict_defaultdict_int(), defaultdict(int)])
    return cats

# Names exported from script_config that need to be overridden when -c is used.
# Maps module -> list of names that module imports from script_config.
_SCRIPT_CONFIG_EXPORTS = {
    # analyze.py itself (globals())
    None: [
        'script_config',
        'FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS', 'METRIC_EXPERIMENTS_BY_KEY',
        'CALCULATIONS_FOR_ARCHIVING', 'FINGERPRINTERS_FOR_EXPERIMENTS',
        'FINGERPRINTERS_FOR_MODES',
        'EXPERIMENTS_TO_RUN', 'EXPERIMENTS_TO_RUN_ADDITIVE',
        'EXPERIMENT_LONG_NAMES',
    ],
    # output.py and smr.py import these from script_config too
    'output': ['script_config', 'METRIC_EXPERIMENTS_BY_KEY', 'CALCULATIONS_FOR_ARCHIVING'],
    'smr': ['script_config'],
}

def _ensure_toggle_deps(sc, toggle):
    """Ensure all CONFIG_DEPENDENCIES keys for a toggle exist in sc, defaulting to False."""
    for dep in CONFIG_DEPENDENCIES.get(toggle, []):
        sc.setdefault(dep, False)


def main():
    args = parse_args()

    # =============================================================================
    # Safeguards
    # =============================================================================

    # 1. Schema must be 37
    if args.schema != "37":
        print(f"ERROR: --schema must be 37 (got {args.schema!r}). "
              f"Omit --schema to use the default.", file=sys.stderr)
        sys.exit(1)

    # 2. No other python3.14t processes running
    if not args.force:
        _my_pid = os.getpid()
        _other_procs = []
        try:
            for _pid_str in os.listdir('/proc'):
                if not _pid_str.isdigit():
                    continue
                _pid = int(_pid_str)
                if _pid == _my_pid:
                    continue
                try:
                    with open(f'/proc/{_pid}/cmdline', 'rb') as _f:
                        _cmdline = _f.read().replace(b'\x00', b' ').decode('utf-8', errors='replace').strip()
                    if 'python3.14t' in _cmdline:
                        _other_procs.append((_pid, _cmdline))
                except (PermissionError, FileNotFoundError):
                    continue
        except FileNotFoundError:
            pass  # /proc not available — skip check
        if _other_procs:
            print("ERROR: other python3.14t process(es) are running:", file=sys.stderr)
            for _pid, _cmd in _other_procs:
                print(f"  PID {_pid}: {_cmd[:120]}", file=sys.stderr)
            print("Use --force to bypass this check.", file=sys.stderr)
            sys.exit(1)

    # 3. Cache must contain day data for 2026-03-30 (schema37) — confirms cache is populated
    _cache_check_dir = args.cache_dir or next(
        (p for p in [
            DEFAULT_CACHE_DIR,
            "/work/sandbox-cache",
        ] if os.path.isdir(p)),
        None,
    )
    if not _cache_check_dir or not os.path.isdir(_cache_check_dir):
        print("ERROR: no cache directory found.", file=sys.stderr)
        sys.exit(1)
    import glob as _glob
    _day_sentinel = os.path.join(_cache_check_dir, "*", "days", "schema37", "2026-03-30")
    if not _glob.glob(_day_sentinel):
        print(f"WARNING: cache directory {_cache_check_dir!r} has no day data for "
              f"2026-03-30 (schema37). Day caches will be fetched from BQ.", file=sys.stderr)
        print(f"  Searched: {_day_sentinel}", file=sys.stderr)

    # =============================================================================

    if not args.config:
        print("ERROR: -c CONFIG is required. No default config.", file=sys.stderr)
        sys.exit(1)

    import importlib.util
    import sys as _sys
    # Derive a stable, importable module name from the config path so that
    # functions defined in the config can be pickled/unpickled by forkserver workers.
    _cfg_path = os.path.abspath(args.config)
    _cfg_dir = os.path.dirname(_cfg_path)
    _cfg_mod_name = os.path.splitext(os.path.basename(_cfg_path))[0]
    # Ensure the config's directory is on sys.path so workers can import it
    if _cfg_dir not in _sys.path:
        _sys.path.insert(0, _cfg_dir)
    spec = importlib.util.spec_from_file_location(_cfg_mod_name, _cfg_path)
    if spec is None:
        print(f"ERROR: cannot load config file '{args.config}'", file=sys.stderr)
        sys.exit(1)
    cfg = importlib.util.module_from_spec(spec)
    _sys.modules[_cfg_mod_name] = cfg
    spec.loader.exec_module(cfg)
    for mod_name, names in _SCRIPT_CONFIG_EXPORTS.items():
        mod_globals = globals() if mod_name is None else vars(_sys.modules[mod_name])
        for name in names:
            if not hasattr(cfg, name):
                print(f"ERROR: config file '{args.config}' is missing '{name}'", file=sys.stderr)
                sys.exit(1)
            mod_globals[name] = getattr(cfg, name)

    # Optional overrides — only present in some configs
    for _opt_name in ('EXPERIMENT_SLUG_MAP', 'EXPERIMENT_EQUIVALENTS', 'CUSTOM_FUNCTIONS'):
        if hasattr(cfg, _opt_name):
            globals()[_opt_name] = getattr(cfg, _opt_name)

    # Validate config keys against the dependency map
    validate_config(script_config)

    # Validate and parse date arguments
    try:
        start_day = date.fromisoformat(args.start_day)
    except ValueError:
        print(f"ERROR: --start-day must be YYYY-MM-DD, got '{args.start_day}'", file=sys.stderr)
        sys.exit(1)
    try:
        end_day = date.fromisoformat(args.end_day)
    except ValueError:
        print(f"ERROR: --end-day must be YYYY-MM-DD, got '{args.end_day}'", file=sys.stderr)
        sys.exit(1)
    if end_day <= start_day:
        print(f"ERROR: --end-day ({end_day}) must be after --start-day ({start_day})", file=sys.stderr)
        sys.exit(1)
    _CANONICAL_START = date(2026, 3, 25)
    _CANONICAL_END   = date(2026, 4, 17)
    assert start_day == _CANONICAL_START, \
        f"--start-day must be {_CANONICAL_START}, got {start_day}"
    assert end_day == _CANONICAL_END, \
        f"--end-day must be {_CANONICAL_END}, got {end_day}"

    all_days = []
    d = start_day
    while d < end_day:
        all_days.append(d)
        d += timedelta(days=1)

    # Determine input & output folders
    args.output_folder = f"{args.output_folder}_{int(time.time())}"

    # Create output folder if needed
    os.makedirs(args.output_folder, exist_ok=True)

    platforms = [args.platform] if args.platform else ["desktop", "mobile"]

    # --------------------------------------------------------------------------
    # Monkey-patch our modules so they use the right folders
    # --------------------------------------------------------------------------
    _default_cache = next(
        p for p in [
            DEFAULT_CACHE_DIR,
            "/work/sandbox-cache",
        ] if os.path.isdir(p)
    ) if not args.cache_dir else args.cache_dir
    config.ANALYSIS_FOLDER = _default_cache
    config.OUTPUT_FOLDER = args.output_folder
    set_unknown_extensions_path(config.OUTPUT_FOLDER)

    output_log = open(os.path.join(config.OUTPUT_FOLDER, "run.log"), "a", buffering=1)  # line-buffered
    clean_output_log = config.CleanStream(output_log)

    sys.stdout = config.Tee(sys.stdout, clean_output_log)
    sys.stderr = config.Tee(sys.stderr, clean_output_log)  # uncaught exceptions go here

    # Store named channel refs for log-only and terminal-only routing.
    config.run_log  = clean_output_log
    config.terminal = sys.__stderr__
    config.start_log_thread()

    print(f"Started: {time.strftime('%m/%d/%y %I:%M:%S %p')}")

    # Validate that experiment filters update combined hashes when modifying components
    validate_filters_update_combined_hashes()

    # Populate global run metadata for pickle files
    _git_hash = config.get_git_hash()
    config.RUN_METADATA = {
        'datetime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'commandline': sys.argv,
        'git_hash': _git_hash,
        'output_dir': args.output_folder,
    }

    print("Reading data from:  Database")
    print(f"Command line:  {' '.join(sys.argv)}")
    print(f"Writing to:    {args.output_folder}")
    print(f"Git hash:      {_git_hash}")
    print(f"Date range:    {start_day} to {end_day} ({len(all_days)} day(s))")
    print(f"Tiny Mode:    {"ENABLED" if args.tiny else "DISABLED"}")
    print(f"Minimize Mode:    {"ENABLED" if args.minimize else "DISABLED"}")

    # CLI --per-os overrides the config value (must happen before worker dispatch)
    if args.per_os is not None:
        _per_os_map = {'true': True, 'false': False, 'only': 'only'}
        script_config['per_os_analysis'] = _per_os_map[args.per_os]
        config.log(f"  --per-os={args.per_os} overrides config per_os_analysis")

    # OS filter: restrict all analysis to a single OS
    _os_filter = args.os_filter or script_config.get('os_filter')
    if _os_filter:
        config.log(f"  OS filter: {_os_filter} (single-OS mode)")

    # Analysis configuration — see script_config.py
    # SMR force-enable is deferred to after ISMR cache check (see below).
    # If the cache is valid, no partition pass is needed for ISMR/ISMRP.
    if script_config['perform_single_metric_removal_analysis']:
        _ensure_toggle_deps(script_config, 'fingerprints')
        _ensure_toggle_deps(script_config, 'perform_single_metric_removal_analysis')
        script_config['fingerprints'] = True
        # Ensure ISMR/ISMRP fingerprinters are in the SMR set
        if script_config['perform_iterative_single_metric_removal_analysis']:
            _ismr_fp = script_config['ismr_fingerprinter']
            if _ismr_fp not in script_config['smr_fingerprinters']:
                script_config['smr_fingerprinters'] = set(script_config['smr_fingerprinters']) | {_ismr_fp}
        if script_config['perform_iterative_single_metric_replacement_analysis']:
            _ismrp_fp = script_config['ismrp_fingerprinter']
            if _ismrp_fp not in script_config['smr_fingerprinters']:
                script_config['smr_fingerprinters'] = set(script_config['smr_fingerprinters']) | {_ismrp_fp}
        for _smr_fp in script_config['smr_fingerprinters']:
            if _smr_fp not in ALL_FINGERPRINTERS:
                raise ValueError(f"smr_fingerprinters entry '{_smr_fp}' not found in ALL_FINGERPRINTERS. "
                                 f"Valid options: {sorted(ALL_FINGERPRINTERS)}")
            if _smr_fp not in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS:
                FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS[_smr_fp] = ALL_FINGERPRINTERS[_smr_fp]

    if script_config['perform_logical_metric_removal_analysis']:
        script_config['fingerprints'] = True
        _ensure_toggle_deps(script_config, 'fingerprints')
        for _lmr_fp in (script_config['lmr_fingerprinters'] or LMR_FINGERPRINTERS_DEFAULT):
            if _lmr_fp not in ALL_FINGERPRINTERS:
                raise ValueError(f"lmr_fingerprinters entry '{_lmr_fp}' not found in ALL_FINGERPRINTERS.")
            if _lmr_fp not in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS:
                FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS[_lmr_fp] = ALL_FINGERPRINTERS[_lmr_fp]

    partition_width = args.partition_width
    if partition_width == 0:
        print(f"Partition width:    0 (no partitioning)")
    else:
        print(f"Partition width:    {partition_width} ({16 ** partition_width} partitions)")

    print(f"Config file:   {args.config}")
    config.log(f"Script config:")
    for _k, _v in sorted(script_config.items()):
        config.log(f"  {_k} = {_v!r}")


    # Ensure that if 'missing_font_sets' is enabled, 'missing_fonts' is also enabled
    if script_config['missing_font_sets'] and not script_config['missing_fonts']:
        raise ValueError("If 'missing_font_sets' is enabled, 'missing_fonts' must also be enabled.")

    # ISMR/ISMRP: SMR force-on is deferred to after cache check (see below).
    if script_config['perform_iterative_single_metric_replacement_analysis']:
        if script_config['ismrp_replacement_strategy'] == 'random':
            raise ValueError("ismrp_replacement_strategy='random' is not yet implemented. Use 'mode'.")
        if script_config['ismrp_replacement_strategy'] not in ('mode', 'random'):
            raise ValueError(f"ismrp_replacement_strategy must be 'mode' or 'random', "
                             f"got {script_config['ismrp_replacement_strategy']!r}")

    execution_time = defaultdict(int)
    # =============================================================================
    # Variable Declarations
    # =============================================================================
    execution_time['total_tmp'] = time.time()
    if partition_width == 0:
        config.PATTERN_HASH = get_hash(list(platforms) + [str(start_day), str(end_day)])
    else:
        config.PATTERN_HASH = get_hash(
            list(get_database_partitions(platforms, args.wildcard, width=partition_width))
            + [str(start_day), str(end_day)])
    print(f"Pattern Hash: {config.PATTERN_HASH} - {config.get_analysis_hash_path(config.PATTERN_HASH)}\n")

    # Ensure the output path exists
    output_path = config.get_analysis_hash_path(config.PATTERN_HASH)
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    total_num_users = 0
    total_num_users_by_os = defaultdict(int)
    total_num_users_by_os_locale = defaultdict(lambda: defaultdict(int))
    total_num_users_by_os_version = defaultdict(lambda: defaultdict(int))
    total_num_users_by_os_machine_model = defaultdict(lambda: defaultdict(int))
    total_num_users_by_os_machine_model_version = defaultdict(lambda: defaultdict(int))

    metric_aggregation = OrderedDict()
    metric_aggregation_experiments = defaultdict()
    for name, metrics in METRIC_EXPERIMENTS_BY_KEY.items():
        metric_aggregation_experiments[name] = defaultdict()
        for metric in metrics:
            metric_aggregation_experiments[name][metric] = defaultdict(int)


    metric_aggregation_by_os_accumulating = defaultdict(default_metric_aggregation_by_metric)
    metric_aggregation_by_os = defaultdict(lambda: [None, None])

    fingerprint_archive_anonymizing_tracking = defaultdict(lambda: defaultdict(int))

    # Custom functions (optional, defined in config)
    CUSTOM_FUNCTIONS = globals().get('CUSTOM_FUNCTIONS', [])
    custom_accumulators = {}
    if CUSTOM_FUNCTIONS:
        for cf in CUSTOM_FUNCTIONS:
            custom_accumulators[cf['name']] = cf['init']()
        config.log(f"  Custom functions: {', '.join(cf['name'] for cf in CUSTOM_FUNCTIONS)}")

    fingerprints = {name: defaultdict(int) for name in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS}
    fingerprints_by_os = {name: defaultdict(lambda: defaultdict(int)) for name in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS}
    fingerprints_by_category = {name: get_categories(script_config) for name in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS}

    fingerprints_exp = {}
    fingerprints_exp_by_category = {}
    exp_spill_dirs = []      # paths to per-partition spill directories
    exp_spill_name_map = {}  # {exp_name: safe_filename} for spill file lookup
    def get_categories_for_experiments():
        return get_categories(script_config)

    fingerprints_modes = {name: {fpname: defaultdict(lambda: defaultdict(int)) for fpname in FINGERPRINTERS_FOR_MODES} for name in ALL_MODES}
    fingerprints_modes_by_category = {name: {fpname: get_categories(script_config) for fpname in FINGERPRINTERS_FOR_MODES} for name in ALL_MODES}

    fingerprints_buckets = {}
    metric_buckets = {}

    smr_fingerprints = {}  # populated after SMR_FP_NAMES is computed below

    missing_fonts_strings_counter = defaultdict(defaultdict_int)

    missing_fonts_individual_counter = defaultdict(defaultdict_int) #[os][fontname]
    missing_fonts_individual_counter_by_version = defaultdict(defaultdict_defaultdict_int) #[os][version][fontname]
    missing_fonts_individual_counter_by_locale = defaultdict(defaultdict_defaultdict_int) #[os][locale][fontname]
    missing_fonts_individual_android_counter_by_machine = defaultdict(defaultdict_int) #[machine][fontname]
    missing_fonts_individual_android_counter_by_machine_version = defaultdict(defaultdict_int) #[machine_version][fontname]

    canvas_metrics = [
        "canvas_canvasdata01",
        "canvas_canvasdata02",
        "canvas_canvasdata03",
        "canvas_canvasdata04",
        "canvas_canvasdata05",
        "canvas_canvasdata06",
        "canvas_canvasdata07",
        "canvas_canvasdata08",
        "canvas_canvasdata09",
        "canvas_canvasdata10",
        "canvas_canvasdata11_webgl",
        "canvas_canvasdata12_fingerprintjs1",
        "canvas_canvasdata13_fingerprintjs2",
        "canvassoftware_canvasdata01",
        "canvassoftware_canvasdata02",
        "canvassoftware_canvasdata03",
        "canvassoftware_canvasdata04",
        "canvassoftware_canvasdata05",
        "canvassoftware_canvasdata06",
        "canvassoftware_canvasdata07",
        "canvassoftware_canvasdata08",
        "canvassoftware_canvasdata09",
        "canvassoftware_canvasdata10",
        "canvassoftware_canvasdata11_webgl",
        "canvassoftware_canvasdata12_fingerprintjs1",
        "canvassoftware_canvasdata13_fingerprintjs2",
    ]
    # webgl_renderer_raw_vendor / _family / _model / _api are added above via DEFAULT_SUBSET.update

    # =============================================================================
    # Helper closures (capture args/config from main scope)
    # =============================================================================
    _bq_counts = None           # populated before workers if caches exist
    _bq_filtered_counts = None  # populated before workers if caches exist

    def _load(partition, *, raw_rows_only=False, quiet=False, source_cb=None):
        """Load data for a single partition. Returns (data, num_users, num_users_by_os, stats)."""
        data, num_users, num_users_by_os, stats = load_partition_data(
            partition, all_days, start_day, end_day,
            args.tiny, args.no_cache, args.rebuild_cache,
            args.minimize,
            partition_width, raw_rows_only, quiet=quiet, source_cb=source_cb,
            schema=args.schema,
            bq_counts=None if args.tiny else _bq_counts,
            bq_filtered_counts=None if args.tiny else _bq_filtered_counts,
            n_filter_threads=max_worker_threads,
        )
        if not quiet:
            if raw_rows_only:
                if stats.get('cache_bytes_written'):
                    print(f"  Cache: {stats['cache_bytes_written'] / (1024*1024):.1f} MB written")
            else:
                print(f"  Records: {stats['included']:,} included | {stats['skipped']:,} skipped")
            ue = stats.get('unexpected_errors', '').strip()
            if ue:
                error_log_path = os.path.join(config.OUTPUT_FOLDER, "unexpected_errors.log")
                with open(error_log_path, "a", buffering=1) as f:
                    f.write(ue + "\n")
        return data, num_users, num_users_by_os, stats

    # =============================================================================
    # Load Data
    # =============================================================================
    if script_config['perform_segmentation_shitty'] or script_config['perform_segmentation_decision_tree']:
        if not args.quasi_sequential:
            print("ERROR: Segmentation requires --quasi-sequential.", file=sys.stderr)
            sys.exit(-1)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    if partition_width == 0:
        all_partitions = [(p, None) for p in platforms]
    else:
        all_partitions = list(get_database_partitions(platforms, args.wildcard, width=partition_width))
        # Interleave platforms so workers get a mix of desktop/mobile partitions
        # instead of processing all desktop first then all mobile.
        from itertools import zip_longest
        by_platform = {}
        for p in all_partitions:
            by_platform.setdefault(p[0], []).append(p)
        if len(by_platform) > 1:
            all_partitions = [
                p for group in zip_longest(*by_platform.values())
                for p in group if p is not None
            ]

    # --- raw_rows_only: cache all partitions then exit early ---
    if script_config['raw_rows_only']:
        parallel_workers = script_config['max_procs']
        check_gil_status()
        def _cache_raw(partition):
            _load(partition, raw_rows_only=True, quiet=True)
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            list(tqdm.tqdm(
                executor.map(_cache_raw, all_partitions),
                total=len(all_partitions),
                desc="Caching raw rows",
                file=sys.__stderr__,
            ))
        print("Raw rows cached. Exiting.")
        return

    # --- Subset setup (no sample DataValues needed) ---
    metrics_to_visualize_fingerprinters = ALL_FINGERPRINTERS_UNION
    metrics_to_visualize_special = metrics_to_visualize_fingerprinters

    DEFAULT_SUBSET, DEBUGPRINT_SUBSET, metrics_to_visualize, metrics_to_run_bucketing_for = \
        setup_subsets(metric_aggregation, metric_buckets)

    SMR_FP_NAMES = list(script_config['smr_fingerprinters']) if script_config['perform_single_metric_removal_analysis'] else []
    smr_subsets = {}
    smr_metric_lists = {}
    for _fp in SMR_FP_NAMES:
        _fp_subset = ALL_FINGERPRINTERS[_fp]
        smr_subsets[_fp] = _fp_subset
        smr_metric_lists[_fp] = list(
            script_config['perform_single_metric_removal_analysis_override_set']
            or set(_fp_subset) - script_config['perform_single_metric_removal_analysis_exclude_set']
        )
    smr_fingerprints = {fp: defaultdict(defaultdict_int) for fp in SMR_FP_NAMES}
    smr_fingerprints_by_os = {}  # {fp: {os: {metric: histogram}}}

    LMR_FP_NAMES = []
    lmr_unit_lists = {}
    lmr_fingerprints = {}
    lmr_fingerprints_by_os = {}  # {fp: {os: {unit: histogram}}}
    if script_config['perform_logical_metric_removal_analysis']:
        LMR_FP_NAMES = list(script_config['lmr_fingerprinters'] or LMR_FINGERPRINTERS_DEFAULT)
        for _fp in LMR_FP_NAMES:
            lmr_unit_lists[_fp] = build_lmr_unit_lists(_fp, ALL_FINGERPRINTERS[_fp])
            lmr_fingerprints[_fp] = defaultdict(defaultdict_int)

    # --- ISMR cache: determine which fingerprinters need cache building ---
    _ismr_cache_base = os.path.join(config.ANALYSIS_FOLDER, '_ismr_cache')
    _build_ismr_cache = set()
    _valid_ismr_caches = {}  # {fp_name: cache_dir} for validated caches
    _ismr_cache_baselines = {}   # {fp_name: (num_users, num_unique, fitness)}
    _ismr_cache_baselines_by_os = {}  # {fp_name: {os: (num_users, num_unique, fitness)}}
    _ismr_cache_metric_lists = {}  # {fp_name: [metric_names]}
    _ismr_needed_fps = set(SMR_FP_NAMES)
    if script_config['perform_iterative_single_metric_removal_analysis']:
        _ismr_needed_fps.add(script_config['ismr_fingerprinter'])
    if script_config['perform_iterative_single_metric_replacement_analysis']:
        _ismr_needed_fps.add(script_config['ismrp_fingerprinter'])
    if script_config['perform_min_set_combo_analysis']:
        _ismr_needed_fps.add(script_config['min_set_combo_fingerprinter'])
    for _fp in sorted(_ismr_needed_fps):
        _fp_safe = safe_filename(_fp)
        _cache_dir = os.path.join(_ismr_cache_base, _fp_safe)
        _meta_path = os.path.join(_cache_dir, '_meta.json')
        _cache_valid = False
        if os.path.isdir(_cache_dir) and os.path.exists(_meta_path):
            try:
                import json as _json
                with open(_meta_path) as _mf:
                    _meta = _json.load(_mf)
                _pkl_count = sum(1 for f in os.listdir(_cache_dir) if f.endswith('.pkl'))
                _expected_parts = len(all_partitions)
                if (_meta.get('fingerprinter') == _fp
                    and _meta.get('start_day') == str(start_day)
                    and _meta.get('end_day') == str(end_day)
                    and _meta.get('partition_count') == _pkl_count
                    and _pkl_count == _expected_parts
                    and 'baseline_num_users' in _meta):
                    _cache_valid = True
                    _valid_ismr_caches[_fp] = _cache_dir
                    _ismr_cache_baselines[_fp] = (
                        _meta['baseline_num_users'],
                        _meta['baseline_num_unique'],
                        _meta['baseline_fitness'],
                    )
                    _ismr_cache_metric_lists[_fp] = _meta['metric_list']
                    # Load and validate per-OS baselines from per-OS cache metadata
                    _os_vals_avail = _meta.get('os_values_available', [])
                    if _os_vals_avail:
                        _ismr_cache_baselines_by_os[_fp] = {}
                        for _ov in _os_vals_avail:
                            _os_cd = os.path.join(_ismr_cache_base, f"{_fp_safe}_os_{safe_filename(_ov)}")
                            _os_mp = os.path.join(_os_cd, '_meta.json')
                            if not os.path.isdir(_os_cd) or not os.path.exists(_os_mp):
                                config.log(f"    {_ov}: no per-OS cache dir or metadata, skipping")
                                continue
                            with open(_os_mp) as _omf:
                                _os_m = _json.load(_omf)
                            _os_pkl_count = sum(1 for f in os.listdir(_os_cd) if f.endswith('.pkl'))
                            if (_os_m.get('fingerprinter') != _fp
                                or _os_m.get('start_day') != str(start_day)
                                or _os_m.get('end_day') != str(end_day)
                                or _os_m.get('partition_count') != _os_pkl_count
                                or 'baseline_num_users' not in _os_m):
                                config.log(f"    {_ov}: per-OS cache stale "
                                           f"(fp={_os_m.get('fingerprinter')}, "
                                           f"dates={_os_m.get('start_day')}..{_os_m.get('end_day')}, "
                                           f"parts={_os_m.get('partition_count')} vs {_os_pkl_count} on disk)")
                                continue
                            _ismr_cache_baselines_by_os[_fp][_ov] = (
                                _os_m['baseline_num_users'],
                                _os_m['baseline_num_unique'],
                                _os_m['baseline_fitness'],
                            )
                    config.log(f"  ISMR cache valid for {_fp}: {_cache_dir} "
                               f"({_pkl_count} partitions, "
                               f"{_meta['baseline_num_users']:,} users, "
                               f"{_meta['baseline_num_unique']:,} unique, "
                               f"OS: {_os_vals_avail}, "
                               f"built {_meta.get('created')})")
                else:
                    config.log(f"  ISMR cache stale for {_fp}: "
                               f"fp={_meta.get('fingerprinter')}, "
                               f"dates={_meta.get('start_day')}..{_meta.get('end_day')}, "
                               f"parts={_meta.get('partition_count')} on disk vs {_expected_parts} expected")
            except Exception as _e:
                config.log(f"  ISMR cache check failed for {_fp}: {_e}")
        if not _cache_valid:
            _build_ismr_cache.add(_fp)

    if _build_ismr_cache:
        config.log(f"  Will build ISMR cache for: {sorted(_build_ismr_cache)}")
        # Enable SMR + fingerprints to build the cache
        if not script_config['perform_single_metric_removal_analysis']:
            script_config['perform_single_metric_removal_analysis'] = True
            script_config['fingerprints'] = True
            _ensure_toggle_deps(script_config, 'fingerprints')
            _ensure_toggle_deps(script_config, 'perform_single_metric_removal_analysis')
            for _fp in _build_ismr_cache:
                if _fp not in SMR_FP_NAMES:
                    SMR_FP_NAMES.append(_fp)
                if _fp not in smr_subsets:
                    _fp_subset = ALL_FINGERPRINTERS[_fp]
                    smr_subsets[_fp] = _fp_subset
                    smr_metric_lists[_fp] = list(
                        script_config['perform_single_metric_removal_analysis_override_set']
                        or set(_fp_subset) - script_config['perform_single_metric_removal_analysis_exclude_set']
                    )
                    smr_fingerprints[_fp] = defaultdict(defaultdict_int)
                if _fp not in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS:
                    FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS[_fp] = ALL_FINGERPRINTERS[_fp]
                    fingerprints_by_os[_fp] = defaultdict(lambda: defaultdict(int))
                    fingerprints_by_category[_fp] = get_categories(script_config)
            config.log(f"  Enabling SMR + fingerprints to build ISMR cache")
    if _valid_ismr_caches:
        config.log(f"  Reusing ISMR cache for: {sorted(_valid_ismr_caches)}")

    # ISMR/ISMRP enter the SMR output section — ensure SMR deps exist even when
    # SMR wasn't directly enabled and the ISMR cache didn't need rebuilding.
    if script_config['perform_iterative_single_metric_removal_analysis'] or script_config['perform_iterative_single_metric_replacement_analysis']:
        _ensure_toggle_deps(script_config, 'perform_single_metric_removal_analysis')

    persisted_all_data_values = []

    persist_data = args.quasi_sequential
    if persist_data:
        # Cannot use process pool with quasi-sequential mode: workers would need
        # to return the full DataValues list across the process boundary via
        # pickle, re-introducing the very malloc contention we're trying to avoid
        # (plus the cost of a second serialization).  Options to fix this:
        #   (a) Write DataValues to temp files in the worker and mmap/unpickle
        #       them back in the main process after the pool finishes.
        #   (b) Use multiprocessing shared memory (requires a fixed-size layout).
        #   (c) Keep ThreadPoolExecutor only for quasi-sequential runs.
        print("ERROR: --quasi-sequential is incompatible with process-based workers.",
              file=sys.stderr)
        sys.exit(1)

    parallel_workers = script_config['max_procs']
    _raw_mwt = script_config['max_worker_threads']
    if _raw_mwt is None:
        # Budget: 100 total threads minus 1 for the main process and 1 primary
        # thread per worker, divided evenly across workers.
        max_worker_threads = max(1, (100 - 1 - parallel_workers) // parallel_workers)
    else:
        max_worker_threads = _raw_mwt

    # ----------------------------------------------------------
    # Pre-fetch BQ row counts for cache validation (single query)
    # ----------------------------------------------------------
    if not args.no_cache and not args.rebuild_cache and not args.tiny:
        print("Fetching BQ row counts for cache validation...")
        t0_bq = time.time()
        _bq_counts = query_bq_day_counts(platforms, args.schema, start_day, end_day, partition_width)
        _bq_filtered_counts = query_bq_filtered_counts(platforms, args.schema, start_day, end_day, partition_width)
        _bq_elapsed = time.time() - t0_bq
        print(f"  BQ row counts: {len(_bq_counts)} day-partition entries, {len(_bq_filtered_counts)} filtered partition entries in {_bq_elapsed:.1f}s")
        execution_time['bq_row_counts'] = _bq_elapsed

    # ----------------------------------------------------------
    # Worker config: everything partition_worker() needs, as plain picklable
    # values.  Sent once to each worker process via the pool initializer.
    # ----------------------------------------------------------

    # Phase list mirrors the enabled sections of partition_worker so the
    # display shows "Phase N/M: Name" with the correct total.
    _phase_list = ['Loading']
    if script_config['calculate_metrics_aggregated']:           _phase_list.append('Metrics')
    if script_config['fingerprint_archiving']:                     _phase_list.append('FP Archive')
    if script_config['fingerprints']:                              _phase_list.append('Fingerprints')
    if script_config['fingerprint_buckets'] or script_config['metric_buckets']:
                                                               _phase_list.append('Buckets')
    if script_config['missing_fonts']:                             _phase_list.append('Fonts')
    if script_config['experiments'] or script_config['calculate_metric_experiment_aggregated']:
                                                                   _phase_list.append('Experiments')
    if script_config['browser_modes']:                             _phase_list.append('Modes')
    if CUSTOM_FUNCTIONS:                                           _phase_list.append('Custom')
    if script_config['perform_single_metric_removal_analysis']:    _phase_list.append('SMR')
    if script_config['perform_logical_metric_removal_analysis'] and LMR_FP_NAMES:
                                                                   _phase_list.append('LMR')
    _total_phases = len(_phase_list)

    _skip_partition_pass = (len(_phase_list) == 1)  # only 'Loading', no actual work
    if _skip_partition_pass:
        config.log(f"  No partition processing needed — skipping worker pool")
        total_num_users = 0
        total_data_count = 0

    _worker_config = {
        # config module state
        'analysis_folder': config.ANALYSIS_FOLDER,
        'output_folder':   config.OUTPUT_FOLDER,
        'pattern_hash':    config.PATTERN_HASH,
        # run parameters
        'max_worker_threads': max_worker_threads,
        'all_days':        all_days,
        'start_day':       start_day,
        'end_day':         end_day,
        'schema':          args.schema,
        'partition_width': partition_width,
        'tiny':            args.tiny,
        'no_cache':        args.no_cache,
        'rebuild_cache':   args.rebuild_cache,
        'minimize':        args.minimize,
        # pre-fetched BQ counts (None when tiny or no-cache)
        'bq_counts':           _bq_counts,
        'bq_filtered_counts':  _bq_filtered_counts,
        # user config exports (from script_config.py or -c file)
        'script_config':                        script_config,
        'FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS': FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS,
        'FINGERPRINTERS_FOR_EXPERIMENTS':       FINGERPRINTERS_FOR_EXPERIMENTS,
        'FINGERPRINTERS_FOR_MODES':             FINGERPRINTERS_FOR_MODES,
        'EXPERIMENTS_TO_RUN':                   EXPERIMENTS_TO_RUN,
        'EXPERIMENTS_TO_RUN_ADDITIVE':          EXPERIMENTS_TO_RUN_ADDITIVE,
        'METRIC_EXPERIMENTS_BY_KEY':            METRIC_EXPERIMENTS_BY_KEY,
        'CALCULATIONS_FOR_ARCHIVING':           CALCULATIONS_FOR_ARCHIVING,
        # pre-computed derived values
        'metrics_to_visualize':         metrics_to_visualize,
        'metrics_to_run_bucketing_for': metrics_to_run_bucketing_for,
        'SMR_FP_NAMES':                 SMR_FP_NAMES,
        'smr_metric_lists':             smr_metric_lists,
        'smr_subsets':                  smr_subsets,
        'LMR_FP_NAMES':                 LMR_FP_NAMES,
        'lmr_unit_lists':               lmr_unit_lists,
        'total_phases':                 _total_phases,
        # DEFAULT_SUBSET is updated by setup_subsets() in the main process but
        # forkserver workers start fresh and don't inherit that update.
        'extra_default_subset':         set(DEFAULT_SUBSET),
        'build_ismr_cache':             _build_ismr_cache,
        'CUSTOM_FUNCTIONS':             CUSTOM_FUNCTIONS,
        'os_filter':                    _os_filter,
    }


    # ----------------------------------------------------------
    # Merge one worker's result into global accumulators
    # ----------------------------------------------------------
    def merge_result(r):
        nonlocal total_num_users
        total_num_users += r['num_users']
        for k, v in r['num_users_by_os'].items():
            total_num_users_by_os[k] += v

        execution_time['loading'] += r.get('load_elapsed', 0)

        if r.get('empty'):
            return

        if 'data' in r:
            persisted_all_data_values.extend(r['data'])

        if 'metric_aggregation' in r:
            merge_counter(metric_aggregation, r['metric_aggregation'])

        if 'metric_aggregation_experiments' in r:
            merge_counter(metric_aggregation_experiments, r['metric_aggregation_experiments'])

        if 'metric_aggregation_by_os' in r:
            # metric_aggregation_by_os_accumulating[metric] = [total_dict, by_os_dict]
            for metric, pair in r['metric_aggregation_by_os'].items():
                merge_counter(metric_aggregation_by_os_accumulating[metric][0], pair[0])
                merge_counter(metric_aggregation_by_os_accumulating[metric][1], pair[1])

        if 'fingerprint_archive_tracking' in r:
            merge_counter(fingerprint_archive_anonymizing_tracking, r['fingerprint_archive_tracking'])

        if 'fingerprints_by_os' in r:
            for _fpn, _os_dict in r['fingerprints_by_os'].items():
                for _os_val, _hash_dict in _os_dict.items():
                    merge_counter(fingerprints_by_os[_fpn][_os_val], _hash_dict)

        if 'fingerprints_by_category' in r:
            _merge_fp_categories(fingerprints_by_category, r['fingerprints_by_category'])

        # fingerprint/metric buckets now spill to disk — no in-memory merge

        if 'missing_fonts' in r:
            mf = r['missing_fonts']
            merge_counter(missing_fonts_strings_counter, mf['strings_counter'])
            merge_counter(missing_fonts_individual_counter, mf['individual_counter'])
            merge_counter(missing_fonts_individual_counter_by_version, mf['by_version'])
            merge_counter(missing_fonts_individual_counter_by_locale, mf['by_locale'])
            merge_counter(missing_fonts_individual_android_counter_by_machine, mf['android_by_machine'])
            merge_counter(missing_fonts_individual_android_counter_by_machine_version, mf['android_by_machine_version'])
            merge_counter(total_num_users_by_os_locale, mf['by_os_locale'])
            merge_counter(total_num_users_by_os_version, mf['by_os_version'])
            merge_counter(total_num_users_by_os_machine_model, mf['by_os_machine_model'])
            merge_counter(total_num_users_by_os_machine_model_version, mf['by_os_machine_model_version'])

        # Experiment fingerprints are spilled to disk by workers — collect
        # spill directory paths and merge categories only (small).
        if 'exp_spill_dir' in r:
            exp_spill_dirs.append(r['exp_spill_dir'])
            exp_spill_name_map.update(r['exp_spill_names'])

        if 'fingerprints_exp_by_category' in r:
            for exp_name, cat_dict in r['fingerprints_exp_by_category'].items():
                if exp_name not in fingerprints_exp_by_category:
                    fingerprints_exp_by_category[exp_name] = {name: get_categories(script_config) for name in FINGERPRINTERS_FOR_EXPERIMENTS}
                _merge_fp_categories(fingerprints_exp_by_category[exp_name], cat_dict)

        if 'fingerprints_modes' in r:
            merge_counter(fingerprints_modes, r['fingerprints_modes'])

        if 'fingerprints_modes_by_category' in r:
            for modename, cat_dict in r['fingerprints_modes_by_category'].items():
                _merge_fp_categories(fingerprints_modes_by_category[modename], cat_dict)

        # Custom function accumulators
        for cf in CUSTOM_FUNCTIONS:
            key = f"custom_{cf['name']}"
            if key in r:
                cf['merge'](custom_accumulators[cf['name']], r[key])

        # SMR/LMR fingerprints are spilled to disk by workers (paths are fixed).
        # Nothing to collect — spill paths are derived from config.ANALYSIS_FOLDER.

    # ----------------------------------------------------------
    # Process all partitions
    # ----------------------------------------------------------
    total_partitions = len(all_partitions)
    completed_partitions = 0
    total_data_count = 0
    agg_load_time = 0.0
    source_counts = defaultdict(int)  # 'range_cache', 'day_cache', 'database', 'mixed'
    agg_timings = {'unpickle': 0.0, 'prefilter': 0.0, 'dedup': 0.0,
                   'parse': 0.0, 'filter': 0.0, 'range_save': 0.0}

    # Clean up any stale spill directories from a previous crashed run
    # before workers start writing, to prevent double-counting.
    for _stale_dir in ('_exp_spill', '_smr_spill', '_lmr_spill',
                        '_ismr_iter_spill', '_ismrp_iter_spill', '_combo_spill',
                        '_bucket_spill'):
        _stale_path = os.path.join(config.ANALYSIS_FOLDER, _stale_dir)
        if os.path.isdir(_stale_path):
            config.log(f"  Cleaning stale spill directory: {_stale_path}")
            shutil.rmtree(_stale_path, ignore_errors=True)

    if _skip_partition_pass:
        # Jump past the entire partition processing block.
        # Post-processing sections (ISMR, ISMRP, min-set, LMR) handle their own data loading.
        pass
    else:  # ---- BEGIN PARTITION PASS ----
      print(f"\nProcessing {total_partitions} partitions with {parallel_workers} worker processes...")
      t_parallel = time.time()
      display = ProgressDisplay(tty=sys.__stderr__, total_partitions=total_partitions,
                                enabled=False if args.skip_progress_bars else None)
      display.start()

      # Bridge thread: forwards progress events from worker processes to the
      # ProgressDisplay slots that live in this (main) process.
      # The queue must be created from the forkserver context so it can be
      # inherited by worker processes (forkserver can't pickle a default-context Queue).
      _mp_ctx = multiprocessing.get_context('forkserver')
      _progress_queue = _mp_ctx.Queue()
      _worker_config['progress_queue'] = _progress_queue
      _bridge_stop    = threading.Event()
      _bridge_thread  = threading.Thread(
          target=_progress_bridge,
          args=(_progress_queue, display.slots, _bridge_stop),
          daemon=True,
          name='progress-bridge',
      )
      _bridge_thread.start()

      config.log(f"Worker logs: {config.OUTPUT_FOLDER}/run_worker_<pid>.log (one per worker process)")

      try:
        executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=parallel_workers,
            mp_context=_mp_ctx,
            initializer=worker_init,
            initargs=(_worker_config,),
        )
        futures = {
            executor.submit(partition_worker, p, slot_idx): p
            for slot_idx, p in enumerate(all_partitions)
        }
        t_last_partition = time.time()
        try:
            for future in as_completed(futures):
                partition_info = futures[future]
                try:
                    r = future.result()
                except Exception as _worker_exc:
                    display.stop()  # clear progress bars first
                    _p_label = f"{partition_info[0]}/{partition_info[1]}" if partition_info[1] else partition_info[0]
                    _exc_type = type(_worker_exc).__name__
                    _crash_msg = (
                        f"\n{'='*60}\n"
                        f"WORKER CRASH on partition {_p_label}\n"
                        f"  {_exc_type}: {_worker_exc}\n"
                        f"  Completed {completed_partitions}/{total_partitions} partitions before crash.\n"
                        f"  Worker logs: {config.OUTPUT_FOLDER}/run_worker_*.log\n"
                        f"{'='*60}"
                    )
                    print(_crash_msg, file=sys.stderr, flush=True)
                    config.log(_crash_msg)
                    raise

                merge_result(r)
                display.release_slot(display.slots[r['_slot_idx']])

                completed_partitions += 1
                total_data_count += r.get('data_count', 0)
                agg_load_time += r.get('load_elapsed', 0)
                source_counts[r.get('source', 'unknown')] += 1
                for k, v in r.get('load_timings', {}).items():
                    agg_timings[k] = agg_timings.get(k, 0.0) + v
                for k, v in r.get('phase_times', {}).items():
                    agg_timings[k] = agg_timings.get(k, 0.0) + v

                if args.skip_progress_bars:
                    now = time.time()
                    ts = time.strftime("%H:%M:%S", time.localtime(now))
                    print(f"  [{ts}] Loaded {completed_partitions}/{total_partitions} partitions, {now - t_last_partition:.1f}s since last")
                    t_last_partition = now
                else:
                    # Print a milestone line every 10% even when progress bars are shown
                    prev_pct = (completed_partitions - 1) * 100 // total_partitions
                    curr_pct = completed_partitions * 100 // total_partitions
                    if curr_pct // 10 > prev_pct // 10 or completed_partitions == total_partitions:
                        now = time.time()
                        ts = time.strftime("%H:%M:%S", time.localtime(now))
                        elapsed = now - t_parallel
                        print(f"  [{ts}] {completed_partitions}/{total_partitions} partitions ({curr_pct}%) in {elapsed:.0f}s")
        except BaseException:
            display.stop()
            raise
      except BaseException:
          display.stop()
          executor.shutdown(wait=False, cancel_futures=True)
          raise
      finally:
          _bridge_stop.set()
          _bridge_thread.join(timeout=2)

      elapsed_parallel = time.time() - t_parallel
      execution_time['parallel_processing'] = elapsed_parallel
      display.stop()
      executor.shutdown(wait=False)

      # Build source summary
      source_parts = []
      if source_counts.get('range_cache'):
          source_parts.append(f"{source_counts['range_cache']} from range cache")
      if source_counts.get('day_cache'):
          source_parts.append(f"{source_counts['day_cache']} from day cache")
      if source_counts.get('mixed'):
          source_parts.append(f"{source_counts['mixed']} mixed (cache + database)")
      if source_counts.get('database'):
          source_parts.append(f"{source_counts['database']} from database")
      source_summary = " | ".join(source_parts) if source_parts else "unknown"

      print(f"  Parallel processing: {total_data_count:,} DataValues across {total_partitions} partitions in {elapsed_parallel:.1f}s ({agg_load_time:.0f}s loading)")
      print(f"  Data sources: {source_summary}")
      load_keys   = ['unpickle', 'prefilter', 'dedup', 'parse', 'filter', 'range_save']
      compute_keys = ['corrections', 'metrics', 'fp_archive', 'fingerprints',
                      'buckets_compute', 'buckets_spill', 'fonts', 'experiments', 'modes', 'smr', 'lmr']
      def _fmt_timings(keys):
          return "  ".join(f"{k}={agg_timings[k]:.0f}" for k in keys if k in agg_timings and agg_timings[k] > 0)
      print(f"  Load breakdown (worker-seconds):    {_fmt_timings(load_keys)}")
      print(f"  Compute breakdown (worker-seconds): {_fmt_timings(compute_keys)}\n")

      # Frozen dataset assertion — data range is locked, user count must not change
      _EXPECTED_USERS = 24_871_013
      if total_data_count != _EXPECTED_USERS:
          print(f"\n{'='*60}", file=sys.stderr)
          print(f"ABORT: Expected {_EXPECTED_USERS:,} users but got {total_data_count:,}.", file=sys.stderr)
          print(f"The dataset (2026-03-25 to 2026-04-17) is frozen.", file=sys.stderr)
          print(f"If the data has legitimately changed, update _EXPECTED_USERS in analyze.py.", file=sys.stderr)
          print(f"{'='*60}", file=sys.stderr)
          sys.exit(1)

      if total_data_count == 0:
          print("All partitions empty — nothing to process.")

    # Per-OS analysis flags (--per-os override already applied above, before worker dispatch)
    _per_os = script_config['per_os_analysis']
    _do_global = _per_os in (False, True)
    _do_per_os = _per_os in (True, 'only')

    # --- Save caches ---
    if script_config['calculate_metrics_aggregated'] :
        if not (args.no_cache or args.tiny or args.minimize):
            pickle_data(metric_aggregation, "metric_aggregation.bin", config.PATTERN_HASH)
    if script_config['calculate_metrics_aggregated'] and _do_per_os:
        if not (args.no_cache or args.tiny or args.minimize):
            pickle_data(metric_aggregation_by_os_accumulating, "metric_aggregation_by_os_accumulating.bin", config.PATTERN_HASH)

    # (ISMR cache metadata written after baselines are computed — see below)

    # --- Pickle metric aggregation data to output dir for deferred generation ---
    if script_config['calculate_metrics_aggregated'] or script_config['calculate_metric_experiment_aggregated']:
        _ma_config_key_names = [
            'calculate_metrics_aggregated', 'calculate_metric_experiment_aggregated',
            'show_special_metrics_aggregated', 'show_all_metrics_aggregated',
            'print_x_aggregate_tables', 'print_x_aggregate_graphs',
            'print_x_aggregate_entropy', 'print_x_hhi_index',
            'print_log_scale_also', 'max_threads_graph_export',
        ]
        if _do_per_os:
            _ma_config_key_names.extend([
                'print_x_by_os_aggregate_graphs', 'calculate_metrics_by_os',
            ])
        _ma_config_keys = {k: script_config.get(k, False) for k in _ma_config_key_names}
        _ma_payload = {
            'metric_aggregation': dict(metric_aggregation),
            'metric_aggregation_experiments': dict(metric_aggregation_experiments),
            'metric_experiments': list(METRIC_EXPERIMENTS_BY_KEY.items()),
            'metrics_to_visualize': list(metrics_to_visualize),
            'metrics_to_visualize_special': list(metrics_to_visualize_special),
            'canvas_metrics': list(canvas_metrics),
            'config_keys': _ma_config_keys,
            'run_metadata': dict(config.RUN_METADATA),
        }
        if _do_per_os and metric_aggregation_by_os_accumulating:
            _ma_payload['metric_aggregation_by_os'] = dict(metric_aggregation_by_os_accumulating)
        pickle_data(_ma_payload, "metric_aggregation_output.bin", hash=None, override_dir=config.OUTPUT_FOLDER)

    # --- Merge per-partition archive shards ---
    if script_config['fingerprint_archiving']:
        for title, expose_metrics, filter_set, fingerprinters_set in CALCULATIONS_FOR_ARCHIVING:
            combined_path = os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_{safe_filename(title)}.csv")
            with open(combined_path, 'w', newline='') as out:
                writer = csv.writer(out)
                header_written = False
                for partition in all_partitions:
                    part_id = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")
                    shard = os.path.join(config.OUTPUT_FOLDER, f"fingerprint_archive_{safe_filename(title)}_part_{part_id}.csv")
                    if not os.path.exists(shard):
                        continue   # empty partition produced no shard
                    with open(shard, 'r', newline='') as inp:
                        reader = csv.reader(inp)
                        header = next(reader)
                        if not header_written:
                            writer.writerow(header)
                            header_written = True
                        for row in reader:
                            writer.writerow(row)
                    os.remove(shard)

    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # =============================================================================
    # Final Analysis
    # =============================================================================
    # =============================================================================

    if args.quasi_sequential:
        all_data_values = persisted_all_data_values

    # =============================================================================
    # Metrics aggregated
    # =============================================================================
    if script_config['calculate_metrics_aggregated'] or script_config['calculate_metric_experiment_aggregated']:
        if script_config['metrics_aggregated_output']:
            visualize_metrics_aggregated(
                metric_aggregation, metric_aggregation_experiments,
                metrics_to_visualize, metrics_to_visualize_special, canvas_metrics
            )
        del metric_aggregation, metric_aggregation_experiments
        gc.collect()

    # =============================================================================
    # Metrics aggregated by OS
    # =============================================================================
    if script_config['calculate_metrics_aggregated'] and _do_per_os:
        if script_config['metrics_aggregated_output']:
            visualize_metrics_by_os(
                metric_aggregation_by_os_accumulating, metric_aggregation_by_os,
                metrics_to_visualize, metrics_to_visualize_special, canvas_metrics
            )
        del metric_aggregation_by_os_accumulating, metric_aggregation_by_os
        gc.collect()

    # =============================================================================
    # Fingerprint Archiving with Anonymization
    # =============================================================================
    if script_config['fingerprint_archiving']:
        process_fingerprint_archiving(fingerprint_archive_anonymizing_tracking)

    # =============================================================================
    # Print fingerprint & cohort analysis
    # =============================================================================
    # Derive global fingerprints from OS-bucketed data
    fingerprints = {}
    for _fpn in fingerprints_by_os:
        fingerprints[_fpn] = defaultdict(int)
        for _os_dict in fingerprints_by_os[_fpn].values():
            for _h, _c in _os_dict.items():
                fingerprints[_fpn][_h] += _c

    # Discover OS values from fingerprint data, or from ISMR cache metadata
    _os_values = sorted(set().union(*(d.keys() for d in fingerprints_by_os.values()))) if fingerprints_by_os else []
    if not _os_values and _do_per_os and _ismr_cache_baselines_by_os:
        _os_values = sorted(set().union(*(d.keys() for d in _ismr_cache_baselines_by_os.values())))
    if _do_per_os and _os_values:
        config.log(f"  Per-OS analysis enabled for: {_os_values}")

    _smr_baselines = {}
    _smr_baselines_by_os = {}  # {fp: {os: (n_users, n_unique, fitness)}}
    _lmr_baselines = {}
    _lmr_baselines_by_os = {}  # {fp: {os: (n_users, n_unique, fitness)}}
    if script_config['fingerprints']:
        # Pickle each fingerprinter individually before any output generation
        start = time.time()
        _alldata_fp_names = list(FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS.keys())
        _alldata_payload = {
            'type': 'alldata',
            'fingerprinter_names': _alldata_fp_names,
            'total_num_users': total_num_users,
            'fp_counters': dict(fingerprints),
            'fp_categories': fingerprints_by_category,
            'run_metadata': dict(config.RUN_METADATA),
        }
        if _do_per_os and fingerprints_by_os:
            _alldata_payload['fp_counters_by_os'] = {
                fpn: {os_val: dict(hashes) for os_val, hashes in os_dict.items()}
                for fpn, os_dict in fingerprints_by_os.items()
            }
        pickle_data(_alldata_payload, "alldata.bin", hash=None, override_dir=config.OUTPUT_FOLDER)
        elapsed = time.time() - start
        config.log(f"  Elapsed time for fingerprints pickling: {elapsed:.2f} seconds")
        execution_time['fingerprints_pickling'] = elapsed

        if script_config['fingerprints_output']:
            start = time.time()
            if _do_global:
                print_fingerprint_results("All-Data", total_num_users, fingerprints, fingerprints_by_category, FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS)
            if _do_per_os:
                for _os_val in _os_values:
                    _os_fp_counters = {fpn: fingerprints_by_os[fpn].get(_os_val, {})
                                       for fpn in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS}
                    _first_fp = next(iter(_os_fp_counters.values()), {})
                    _os_n_users = sum(_first_fp.values()) if _first_fp else 0
                    _os_empty_cats = {fpn: [] for fpn in FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS}
                    print_fingerprint_results(
                        f"All-Data-{_os_val}", _os_n_users, _os_fp_counters,
                        _os_empty_cats, FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS,
                        display_label=f"All-Data ({_os_val})")
            elapsed = time.time() - start
            config.log(f"  Elapsed time for fingerprints output: {elapsed:.2f} seconds")
            execution_time['fingerprints_analysis'] = elapsed

        # Pre-compute per-fp SMR baseline scalars before freeing the full fingerprints dict
        _baselines_start = time.time()
        for _fp in SMR_FP_NAMES:
            _t0 = time.time()
            _fp_data = fingerprints[_fp]
            _n_users, _n_unique, _, _ = get_fingerprint_analysis(total_num_users, _fp_data)
            _smr_baselines[_fp] = (_n_users, _n_unique, cohort_fitness(_fp_data),
                                   cohort_fitness_excluding_singletons(_fp_data),
                                   cohort_p50(_fp_data))
            config.log(f"  SMR baseline {_fp}: {time.time() - _t0:.1f}s ({_n_users} users, {_n_unique} unique)")
            # Per-OS baselines
            if _fp in fingerprints_by_os:
                _smr_baselines_by_os[_fp] = {}
                for _os_val, _os_fp_data in fingerprints_by_os[_fp].items():
                    _os_n = sum(_os_fp_data.values())
                    _os_u = sum(1 for v in _os_fp_data.values() if v == 1)
                    _smr_baselines_by_os[_fp][_os_val] = (_os_n, _os_u, cohort_fitness(_os_fp_data),
                                                          cohort_fitness_excluding_singletons(_os_fp_data),
                                                          cohort_p50(_os_fp_data))
                _os_summary = ', '.join(f"{_o}={_v[0]:,}" for _o, _v in sorted(_smr_baselines_by_os[_fp].items()))
                config.log(f"    Per-OS: {_os_summary}")

        # Pre-compute LMR baseline stats before freeing the full fingerprints dict
        if script_config['perform_logical_metric_removal_analysis'] and LMR_FP_NAMES:
            for _fp in LMR_FP_NAMES:
                _t0 = time.time()
                _fp_data = fingerprints[_fp]
                _n_users, _n_unique, _, _ = get_fingerprint_analysis(total_num_users, _fp_data)
                _lmr_baselines[_fp] = (_n_users, _n_unique, cohort_fitness(_fp_data),
                                       cohort_fitness_excluding_singletons(_fp_data),
                                       cohort_p50(_fp_data))
                config.log(f"  LMR baseline {_fp}: {time.time() - _t0:.1f}s ({_n_users} users, {_n_unique} unique)")
                if _do_per_os and _fp in fingerprints_by_os:
                    _lmr_baselines_by_os[_fp] = {}
                    for _os_val, _os_fp_data in fingerprints_by_os[_fp].items():
                        _os_n = sum(_os_fp_data.values())
                        _os_u = sum(1 for v in _os_fp_data.values() if v == 1)
                        _lmr_baselines_by_os[_fp][_os_val] = (_os_n, _os_u, cohort_fitness(_os_fp_data),
                                                              cohort_fitness_excluding_singletons(_os_fp_data),
                                                              cohort_p50(_os_fp_data))

        execution_time['baselines'] = time.time() - _baselines_start

        # --- Write ISMR cache metadata (includes baselines) ---
        if _build_ismr_cache:
            import json as _json
            for _fp in _build_ismr_cache:
                _fp_safe = safe_filename(_fp)
                _cache_dir = os.path.join(_ismr_cache_base, _fp_safe)
                if os.path.isdir(_cache_dir):
                    _pkl_count = sum(1 for f in os.listdir(_cache_dir) if f.endswith('.pkl'))
                    _bl = _smr_baselines.get(_fp, (0, 0, 0, 0, 0))
                    _n, _u, _f = _bl[0], _bl[1], _bl[2]

                    # Collect OS values from per-OS baselines
                    _os_baselines = _smr_baselines_by_os.get(_fp, {})
                    _os_values = sorted(_os_baselines.keys())

                    # Global metadata
                    _f2 = _bl[3] if len(_bl) > 3 else None
                    _p50 = _bl[4] if len(_bl) > 4 else None
                    _meta = {
                        'fingerprinter': _fp,
                        'start_day': str(start_day),
                        'end_day': str(end_day),
                        'partition_count': _pkl_count,
                        'metric_list': smr_metric_lists.get(_fp, []),
                        'total_num_users': total_num_users,
                        'baseline_num_users': _n,
                        'baseline_num_unique': _u,
                        'baseline_fitness': _f,
                        'baseline_fitness_hhi2': _f2,
                        'baseline_p50': _p50,
                        'os_values_available': _os_values,
                        'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    }
                    with open(os.path.join(_cache_dir, '_meta.json'), 'w') as _mf:
                        _json.dump(_meta, _mf, indent=2)
                    _valid_ismr_caches[_fp] = _cache_dir
                    config.log(f"  ISMR cache built for {_fp}: {_cache_dir} "
                               f"({_pkl_count} partitions, {_n:,} users, {_u:,} unique, "
                               f"OS: {_os_values})")

                    # Per-OS metadata
                    for _os_val in _os_values:
                        _os_cache_dir = os.path.join(
                            _ismr_cache_base,
                            f"{_fp_safe}_os_{safe_filename(_os_val)}")
                        if os.path.isdir(_os_cache_dir):
                            _os_pkl = sum(1 for f in os.listdir(_os_cache_dir) if f.endswith('.pkl'))
                            _os_bl = _os_baselines[_os_val]
                            _os_n, _os_u, _os_f = _os_bl[0], _os_bl[1], _os_bl[2]
                            _os_f2 = _os_bl[3] if len(_os_bl) > 3 else None
                            _os_p50 = _os_bl[4] if len(_os_bl) > 4 else None
                            _os_meta = {
                                'fingerprinter': _fp,
                                'os_value': _os_val,
                                'start_day': str(start_day),
                                'end_day': str(end_day),
                                'partition_count': _os_pkl,
                                'metric_list': smr_metric_lists.get(_fp, []),
                                'total_num_users': _os_n,
                                'baseline_num_users': _os_n,
                                'baseline_num_unique': _os_u,
                                'baseline_fitness': _os_f,
                                'baseline_fitness_hhi2': _os_f2,
                                'baseline_p50': _os_p50,
                                'created': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                            }
                            with open(os.path.join(_os_cache_dir, '_meta.json'), 'w') as _mf:
                                _json.dump(_os_meta, _mf, indent=2)
                            config.log(f"    {_os_val}: {_os_pkl} partitions, "
                                       f"{_os_n:,} users, {_os_u:,} unique")

        del fingerprints, fingerprints_by_category, fingerprints_by_os
        gc.collect()

    # =============================================================================
    # Print fingerprint buckets (merge from spill, one fp at a time)
    # =============================================================================
    _N_BINS = 40
    _bucket_spill_base = os.path.join(config.ANALYSIS_FOLDER, '_bucket_spill')

    def _merge_bucket_spill_dir(spill_dir):
        """Merge all .pkl files in spill_dir → {hash: [bin0..bin39]}."""
        merged = {}
        for pf in os.listdir(spill_dir):
            if not pf.endswith('.pkl'):
                continue
            with open(os.path.join(spill_dir, pf), 'rb') as f:
                part = pickle.load(f)
            for h, bins in part.items():
                if h in merged:
                    m = merged[h]
                    for i in range(_N_BINS):
                        m[i] += bins[i]
                else:
                    merged[h] = list(bins)
            del part
        return merged

    def _derive_bucket_likelihoods(merged):
        """Derive {likelihood: [hash→count_dict, total_users]} from merged bins."""
        fp_buckets = {}
        for k in range(1, _N_BINS + 1):
            lk = k * 0.025
            counts = {}
            total = 0
            for h, bins in merged.items():
                c = sum(bins[:k])
                if c > 0:
                    counts[h] = c
                    total += c
            fp_buckets[lk] = [counts, total]
        return fp_buckets

    def _restructure_for_output(buckets_by_fp, fp_names):
        """Restructure {fp_name: {lk: [counts, total]}} → {lk: {fp_name: [counts, total]}}."""
        out = {}
        for k in range(1, _N_BINS + 1):
            lk = k * 0.025
            out[lk] = {}
            for fp_name in fp_names:
                if fp_name in buckets_by_fp:
                    out[lk][fp_name] = buckets_by_fp[fp_name].get(lk, [{}, 0])
                else:
                    out[lk][fp_name] = [{}, 0]
        return out

    if script_config['fingerprint_buckets']:
        _fb_spill = os.path.join(_bucket_spill_base, 'fp')
        if os.path.isdir(_fb_spill):

            def _merge_one_fp(fp_name, spill_base):
                """Merge + derive likelihoods for one fingerprinter. Returns (fp_name, buckets)."""
                fp_dir = os.path.join(spill_base, safe_filename(fp_name))
                if not os.path.isdir(fp_dir):
                    return (fp_name, None)
                merged = _merge_bucket_spill_dir(fp_dir)
                buckets = _derive_bucket_likelihoods(merged)
                del merged
                return (fp_name, buckets)

            def _merge_one_fp_os(fp_name, os_val, spill_base):
                """Merge + derive likelihoods for one fingerprinter+OS. Returns (fp_name, os_val, buckets)."""
                os_dir = os.path.join(
                    spill_base,
                    safe_filename(fp_name) + '_os_' + safe_filename(os_val))
                if not os.path.isdir(os_dir):
                    return (fp_name, os_val, None)
                merged = _merge_bucket_spill_dir(os_dir)
                buckets = _derive_bucket_likelihoods(merged)
                del merged
                return (fp_name, os_val, buckets)

            _fb_all_t0 = time.time()
            _bucket_fps = FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS or ALL_FINGERPRINTERS
            _fp_names_sorted = sorted(_bucket_fps.keys())

            # ── Global fingerprint buckets ──
            if _do_global:
                config.log(f"  Merging fingerprint bucket spill files ({len(_fp_names_sorted)} fingerprinters)...")
                _fb_t0 = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(_fp_names_sorted), 8)) as _fb_pool:
                    _fb_futures = {
                        _fb_pool.submit(_merge_one_fp, _fpn, _fb_spill): _fpn
                        for _fpn in _fp_names_sorted
                    }
                    with tqdm.tqdm(total=len(_fb_futures), desc="  FP bucket merge",
                                   unit="fp", file=config.terminal) as _fb_pbar:
                        for fut in concurrent.futures.as_completed(_fb_futures):
                            _fpn, _buckets = fut.result()
                            if _buckets is not None:
                                fingerprints_buckets[_fpn] = _buckets
                            _fb_pbar.update(1)
                _fb_merge_elapsed = time.time() - _fb_t0
                config.log(f"  Fingerprint bucket merge: {_fb_merge_elapsed:.1f}s "
                           f"({len(fingerprints_buckets)} fingerprinters)")

                _fb_out_t0 = time.time()
                _fb_out = _restructure_for_output(fingerprints_buckets, _bucket_fps)
                print_fingerprint_bucket_results(_fb_out)
                _fb_out_elapsed = time.time() - _fb_out_t0
                config.log(f"  Fingerprint bucket output: {_fb_out_elapsed:.1f}s")
                del fingerprints_buckets, _fb_out
                gc.collect()

            # ── Per-OS fingerprint buckets ──
            if _do_per_os and _os_values:
                _n_os_tasks = len(_fp_names_sorted) * len(_os_values)
                config.log(f"  Merging per-OS fingerprint bucket spill files "
                           f"({len(_os_values)} OSes × {len(_fp_names_sorted)} fingerprinters)...")
                _fb_os_t0 = time.time()

                # Submit all (fingerprinter, OS) pairs in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(_n_os_tasks, 8)) as _fb_os_pool:
                    _fb_os_futures = [
                        _fb_os_pool.submit(_merge_one_fp_os, _fpn, _os_val, _fb_spill)
                        for _os_val in _os_values
                        for _fpn in _fp_names_sorted
                    ]
                    # Collect results grouped by OS
                    _os_results = {}  # {os_val: {fp_name: buckets}}
                    with tqdm.tqdm(total=len(_fb_os_futures), desc="  Per-OS bucket merge",
                                   unit="task", file=config.terminal) as _fb_os_pbar:
                        for fut in concurrent.futures.as_completed(_fb_os_futures):
                            _fpn, _os_val, _buckets = fut.result()
                            if _buckets is not None:
                                _os_results.setdefault(_os_val, {})[_fpn] = _buckets
                            _fb_os_pbar.update(1)

                _fb_os_merge_elapsed = time.time() - _fb_os_t0
                config.log(f"  Per-OS fingerprint bucket merge: {_fb_os_merge_elapsed:.1f}s")

                # Output per-OS results (sequential — each writes to a different file)
                _fb_os_out_t0 = time.time()
                for _os_val in _os_values:
                    _os_buckets = _os_results.get(_os_val, {})
                    if _os_buckets:
                        _fb_os_out = _restructure_for_output(_os_buckets, _bucket_fps)
                        print_fingerprint_bucket_results(
                            _fb_os_out, label=f"fingerprint_buckets_os_{_os_val}")
                        del _fb_os_out
                del _os_results
                gc.collect()
                _fb_os_out_elapsed = time.time() - _fb_os_out_t0
                config.log(f"  Per-OS fingerprint bucket output: {_fb_os_out_elapsed:.1f}s")

            _fb_all_elapsed = time.time() - _fb_all_t0
            config.log(f"  Fingerprint buckets total: {_fb_all_elapsed:.1f}s")
            execution_time['fingerprint_buckets'] = _fb_all_elapsed

    # =============================================================================
    # Print metric buckets (merge from spill, one metric at a time)
    # =============================================================================
    if script_config['metric_buckets']:
        _mb_spill = os.path.join(_bucket_spill_base, 'metric')
        if os.path.isdir(_mb_spill):
            _mb_metrics = [m for m in metrics_to_run_bucketing_for
                           if os.path.isdir(os.path.join(_mb_spill, safe_filename(m)))]
            config.log(f"  Merging metric bucket spill files ({len(_mb_metrics)} metrics)...")
            _mb_t0 = time.time()

            def _merge_one_metric(metric):
                m_dir = os.path.join(_mb_spill, safe_filename(metric))
                merged = _merge_bucket_spill_dir(m_dir)
                buckets = _derive_bucket_likelihoods(merged)
                del merged
                return (metric, buckets)

            # Restructure: {likelihood: {metric: [val→count, total]}}
            _mb_out = {_k * 0.025: {} for _k in range(1, _N_BINS + 1)}
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(_mb_metrics), 8)) as _mb_pool:
                with tqdm.tqdm(total=len(_mb_metrics), desc="  Metric bucket merge",
                               unit="metric", file=config.terminal) as _mb_pbar:
                    for _metric, _buckets in _mb_pool.map(_merge_one_metric, _mb_metrics):
                        for _lk, (_counts, _total) in _buckets.items():
                            _mb_out[_lk][_metric] = [_counts, _total]
                        _mb_pbar.update(1)

            _mb_elapsed = time.time() - _mb_t0
            config.log(f"  Metric bucket merge: {_mb_elapsed:.1f}s")

            _mb_out_t0 = time.time()
            print_metric_bucket_results(metrics_to_run_bucketing_for, _mb_out)
            _mb_out_elapsed = time.time() - _mb_out_t0
            config.log(f"  Metric bucket output: {_mb_out_elapsed:.1f}s")
            del _mb_out
            gc.collect()

    # Clean up bucket spill files
    if os.path.isdir(_bucket_spill_base):
        shutil.rmtree(_bucket_spill_base, ignore_errors=True)

    # =============================================================================
    # Experiment filters
    # =============================================================================
    if script_config['experiments']:
        start = time.time()
        # Build experiment name → filter list mapping for metadata
        _exp_filters = dict(EXPERIMENTS_TO_RUN)
        for _additive_set in EXPERIMENTS_TO_RUN_ADDITIVE:
            _cumulative = []
            for _aname, _afilts in _additive_set.items():
                _cumulative = _cumulative + _afilts
                _exp_filters[_aname] = list(_cumulative)

        # ── Merge experiment fingerprints from disk spill ────────────────────
        # Workers wrote per-partition per-experiment {fp: {hash→count}} files.
        # Merge one experiment at a time to avoid holding all experiments in RAM.
        # Threaded: each thread merges one experiment independently (~3 GB peak each).
        _fp_names = list(FINGERPRINTERS_FOR_EXPERIMENTS.keys())
        _exp_names = sorted(exp_spill_name_map.keys())
        _n_spill = len(exp_spill_dirs)
        _merge_threads = script_config['max_threads_experiment_merging']
        config.log(f"  Merging {len(_exp_names)} experiments from {_n_spill} "
                    f"partition spill dirs ({_merge_threads} threads)...")
        _merge_start = time.time()

        _exp_lock = threading.Lock()  # protects fingerprints_exp, pbar, pickle_data
        _fingerprints_exp_by_os = {}  # {exp_name: {os: {fp: {hash: count}}}}

        def _merge_one_experiment(_exp_name):
            _safe_name = exp_spill_name_map[_exp_name]

            # Merge OS-bucketed {fp: {os: {hash: count}}} across all partitions
            _merged = {fp: defaultdict(lambda: defaultdict(int)) for fp in _fp_names}
            for _sd in exp_spill_dirs:
                _spill_path = os.path.join(_sd, f"{_safe_name}.pkl")
                if os.path.exists(_spill_path):
                    with open(_spill_path, 'rb') as _sf:
                        _part_data = pickle.load(_sf)
                    for _fp in _fp_names:
                        if _fp in _part_data:
                            for _os, _os_hashes in _part_data[_fp].items():
                                _target = _merged[_fp][_os]
                                for _h, _c in _os_hashes.items():
                                    _target[_h] += _c
                    del _part_data

            # Convert to histogram — collapse OS for global
            _histograms = {}
            for _fp in _fp_names:
                _global = collapse_os_layer(_merged[_fp])
                _hist = defaultdict(int)
                for _cnt in _global.values():
                    _hist[_cnt] += 1
                _histograms[_fp] = dict(_hist)

            # Per-OS histograms (only if per-OS output is enabled)
            _os_hists = None
            if _do_per_os:
                _os_hists = {}  # {os: {fp: histogram}}
                _all_os = set()
                for _fp in _fp_names:
                    _all_os.update(_merged[_fp].keys())
                for _ov in _all_os:
                    _os_hists[_ov] = {}
                    for _fp in _fp_names:
                        _os_data = _merged[_fp].get(_ov, {})
                        _h = defaultdict(int)
                        for _cnt in _os_data.values():
                            _h[_cnt] += 1
                        _os_hists[_ov][_fp] = dict(_h)
            del _merged

            # Pickle this experiment
            _exp_payload = {
                'type': 'experiment',
                'exp_name': _exp_name,
                'display_label': EXPERIMENT_LONG_NAMES.get(_exp_name, _exp_name),
                'filters': [f.__name__ for f in _exp_filters.get(_exp_name, [])],
                'fingerprinter_names': _fp_names,
                'total_num_users': total_num_users,
                'fp_counters': _histograms,
                'fp_categories': fingerprints_exp_by_category.get(_exp_name, {}),
                'run_metadata': dict(config.RUN_METADATA),
                'format': 'histogram',
            }
            if _os_hists:
                _exp_payload['fp_counters_by_os'] = _os_hists
            with _exp_lock:
                pickle_data(_exp_payload, f"exp_{_exp_name}.bin", hash=None,
                            override_dir=config.OUTPUT_FOLDER, quiet=True)
                fingerprints_exp[_exp_name] = _histograms
                if _os_hists:
                    _fingerprints_exp_by_os[_exp_name] = _os_hists
                _exp_pbar.set_postfix_str(_exp_name[:40], refresh=False)
                _exp_pbar.update(1)
            del _exp_payload

        _exp_pbar = tqdm.tqdm(total=len(_exp_names), desc="  Experiments",
                              unit="exp", file=config.terminal,
                              disable=args.skip_progress_bars)
        if _merge_threads <= 1:
            for _exp_name in _exp_names:
                _merge_one_experiment(_exp_name)
        else:
            _merge_executor = concurrent.futures.ThreadPoolExecutor(max_workers=_merge_threads)
            _merge_futures = [_merge_executor.submit(_merge_one_experiment, n)
                              for n in _exp_names]
            for _f in concurrent.futures.as_completed(_merge_futures):
                _f.result()  # re-raise any exceptions
            _merge_executor.shutdown(wait=False)
        _exp_pbar.close()

        _merge_elapsed = time.time() - _merge_start
        config.log(f"  Merged and pickled {len(_exp_names)} experiments in {_merge_elapsed:.2f}s")
        execution_time['experiments_pickling'] = _merge_elapsed

        # Clean up spill files
        _spill_root = os.path.join(config.ANALYSIS_FOLDER, '_exp_spill')
        if os.path.isdir(_spill_root):
            shutil.rmtree(_spill_root, ignore_errors=True)
            config.log(f"  Cleaned up experiment spill directory")

        # Write slug manifest if this config provides one (configs using gen_experiments.py).
        if EXPERIMENT_SLUG_MAP:
            import json as _json
            _manifest = {
                'slug_map': EXPERIMENT_SLUG_MAP,
                'equivalents': EXPERIMENT_EQUIVALENTS,
            }
            _manifest_path = os.path.join(config.OUTPUT_FOLDER, 'experiment_manifest.json')
            with open(_manifest_path, 'w') as _f:
                _json.dump(_manifest, _f, indent=2)
            config.log(f"  Wrote experiment_manifest.json ({len(EXPERIMENT_SLUG_MAP)} slugs)")

        if script_config['experiments_output']:
            if _do_global:
                _pe = script_config['max_threads_graph_export']
                _names = list(fingerprints_exp.keys())
                _n = _pe + 1
                _chunks = [_names[i::_n] for i in range(_n)]
                _main, _workers = _chunks[0], _chunks[1:]
                print(f"Generating experiment cohort plots... (progress bar is partition 1/{_n})")
                _executor = concurrent.futures.ThreadPoolExecutor(max_workers=_pe)
                _futures = [_executor.submit(
                    lambda chunk: [print_fingerprint_results(n, total_num_users, fingerprints_exp[n], fingerprints_exp_by_category[n], FINGERPRINTERS_FOR_EXPERIMENTS, display_label=EXPERIMENT_LONG_NAMES.get(n), filters=_exp_filters.get(n, [])) for n in chunk],
                    chunk) for chunk in _workers if chunk]
                with tqdm.tqdm(total=len(_main), desc="  Cohort plots", file=config.terminal) as pbar:
                    for exp_name in _main:
                        print_fingerprint_results(exp_name, total_num_users, fingerprints_exp[exp_name], fingerprints_exp_by_category[exp_name], FINGERPRINTERS_FOR_EXPERIMENTS, display_label=EXPERIMENT_LONG_NAMES.get(exp_name), filters=_exp_filters.get(exp_name, []))
                        pbar.update(1)
                if _futures:
                    print("  Waiting for other groups to complete...")
                    for f in concurrent.futures.as_completed(_futures):
                        f.result()
                _executor.shutdown(wait=False)

            if _do_per_os and _fingerprints_exp_by_os:
                _os_empty_cats = {fpn: [] for fpn in FINGERPRINTERS_FOR_EXPERIMENTS}
                for _os_val in _os_values:
                    _os_exp_names = [n for n in fingerprints_exp if n in _fingerprints_exp_by_os and _os_val in _fingerprints_exp_by_os[n]]
                    if not _os_exp_names:
                        continue
                    config.log(f"  Generating per-OS experiment output for {_os_val} ({len(_os_exp_names)} experiments)...")
                    for _exp_name in _os_exp_names:
                        _os_fp_counters = _fingerprints_exp_by_os[_exp_name][_os_val]
                        _first_fp = next(iter(_os_fp_counters.values()), {})
                        _os_n = sum(sz * cnt for sz, cnt in _first_fp.items()) if _first_fp else 0
                        print_fingerprint_results(
                            f"{_exp_name}-{_os_val}", _os_n, _os_fp_counters,
                            _os_empty_cats, FINGERPRINTERS_FOR_EXPERIMENTS,
                            display_label=f"{EXPERIMENT_LONG_NAMES.get(_exp_name, _exp_name)} ({_os_val})",
                            filters=_exp_filters.get(_exp_name, []),
                            filename_label=f"{_exp_name}_os_{safe_filename(_os_val)}")

            elapsed = time.time() - start
            config.log(f"  Elapsed time for experiments output: {elapsed:.2f} seconds")
            execution_time['experiments_analysis'] = elapsed

        del fingerprints_exp, fingerprints_exp_by_category, _fingerprints_exp_by_os
        gc.collect()

    # =============================================================================
    # Browser modes
    # =============================================================================
    if script_config['browser_modes']:
        start = time.time()

        # Pickle each mode individually before any output generation
        start_pickle = time.time()
        _mode_fp_names = list(FINGERPRINTERS_FOR_MODES.keys())
        for _mode_name in fingerprints_modes:
            # Collapse OS layer for global output
            _mode_fp_global = {fpn: collapse_os_layer(os_dict)
                               for fpn, os_dict in fingerprints_modes[_mode_name].items()}
            _mode_payload = {
                'type': 'mode',
                'mode_name': _mode_name,
                'fingerprinter_names': _mode_fp_names,
                'total_num_users': total_num_users,
                'fp_counters': _mode_fp_global,
                'fp_categories': fingerprints_modes_by_category[_mode_name],
                'run_metadata': dict(config.RUN_METADATA),
            }
            if _do_per_os:
                _mode_payload['fp_counters_by_os'] = {
                    fpn: {os_val: dict(hashes) for os_val, hashes in os_dict.items()}
                    for fpn, os_dict in fingerprints_modes[_mode_name].items()
                }
            pickle_data(_mode_payload, f"mode_{_mode_name}.bin", hash=None,
                        override_dir=config.OUTPUT_FOLDER, quiet=True)
        elapsed_pickle = time.time() - start_pickle
        config.log(f"  Pickled {len(fingerprints_modes)} modes in {elapsed_pickle:.2f}s")
        execution_time['modes_pickling'] = elapsed_pickle

        if script_config['modes_output']:
            # Collapse OS layer for global output
            _modes_global = {mn: {fpn: collapse_os_layer(os_dict) for fpn, os_dict in fp_dict.items()}
                             for mn, fp_dict in fingerprints_modes.items()}

            if _do_global:
                _pe = script_config['max_threads_graph_export']
                _mode_names = list(ALL_MODES.keys())
                _n = _pe + 1
                _chunks = [_mode_names[i::_n] for i in range(_n)]
                _main, _workers = _chunks[0], _chunks[1:]
                print(f"Generating mode cohort plots... (progress bar is partition 1/{_n})")
                _executor = concurrent.futures.ThreadPoolExecutor(max_workers=_pe)
                _futures = [_executor.submit(
                    lambda chunk: [print_fingerprint_results(n, total_num_users, _modes_global[n], fingerprints_modes_by_category[n], FINGERPRINTERS_FOR_MODES) for n in chunk],
                    chunk) for chunk in _workers if chunk]
                with tqdm.tqdm(total=len(_main), desc="  Cohort plots", file=config.terminal) as pbar:
                    for modename in _main:
                        print_fingerprint_results(modename, total_num_users, _modes_global[modename], fingerprints_modes_by_category[modename], FINGERPRINTERS_FOR_MODES)
                        pbar.update(1)
                if _futures:
                    print("  Waiting for other groups to complete...")
                    for f in concurrent.futures.as_completed(_futures):
                        f.result()
                _executor.shutdown(wait=False)

            if _do_per_os:
                _os_empty_cats = {fpn: [] for fpn in FINGERPRINTERS_FOR_MODES}
                for _os_val in _os_values:
                    config.log(f"  Generating per-OS mode output for {_os_val}...")
                    for _mode_name in fingerprints_modes:
                        _os_fp_counters = {}
                        for fpn, os_dict in fingerprints_modes[_mode_name].items():
                            _os_fp_counters[fpn] = os_dict.get(_os_val, {})
                        _first_fp = next(iter(_os_fp_counters.values()), {})
                        _os_n = sum(_first_fp.values()) if _first_fp else 0
                        print_fingerprint_results(
                            f"{_mode_name}-{_os_val}", _os_n, _os_fp_counters,
                            _os_empty_cats, FINGERPRINTERS_FOR_MODES,
                            display_label=f"{_mode_name} ({_os_val})",
                            filename_label=f"{_mode_name}_os_{safe_filename(_os_val)}")

            elapsed = time.time() - start
            config.log(f"  Elapsed time for modes output: {elapsed:.2f} seconds")
            execution_time['modes_analysis'] = elapsed

        del fingerprints_modes, fingerprints_modes_by_category
        gc.collect()

    # =============================================================================
    # Font Analysis
    # =============================================================================
    if script_config['missing_fonts']:
        analyze_missing_fonts(
            font_counters={
                'strings': missing_fonts_strings_counter,
                'individual': missing_fonts_individual_counter,
                'by_version': missing_fonts_individual_counter_by_version,
                'by_locale': missing_fonts_individual_counter_by_locale,
                'android_by_machine': missing_fonts_individual_android_counter_by_machine,
                'android_by_machine_version': missing_fonts_individual_android_counter_by_machine_version,
            },
            user_counts={
                'by_os': total_num_users_by_os,
                'by_os_version': total_num_users_by_os_version,
                'by_os_locale': total_num_users_by_os_locale,
                'by_os_machine_model': total_num_users_by_os_machine_model,
                'by_os_machine_model_version': total_num_users_by_os_machine_model_version,
            },
        )

    _seg_any = script_config['perform_segmentation_shitty'] or script_config['perform_segmentation_decision_tree']
    if _seg_any:
        # Build and expand target_metrics against DEFAULT_SUBSET before either segmentation
        # function runs. Both functions receive a plain expanded list with no wildcards.
        import fnmatch as _fnmatch
        _raw_targets = script_config['segmentation_target_metrics'] or ["math_op_*", "math_op_diag_*"]
        _seen = set()
        segmentation_target_metrics = []
        for _pat in _raw_targets:
            if any(c in _pat for c in ('*', '?', '[')):
                candidates = sorted(m for m in DEFAULT_SUBSET if _fnmatch.fnmatch(m, _pat))
            else:
                candidates = [_pat]
            for _m in candidates:
                if _m not in _seen:
                    _seen.add(_m)
                    segmentation_target_metrics.append(_m)
        # Exclude math_op_fdlibm_* — they are identical to math_op_* after the fdlibm filter is applied
        segmentation_target_metrics = [m for m in segmentation_target_metrics if not m.startswith("math_op_fdlibm_")]

        segmentation_preferred_features = [
            "hw_cpu_arch",
            "hw_cpu_model_manufacturer",
            "os",
            "webgl_renderer_raw_vendor",
        ]

        # Apply fdlibm filter so math_op_* values reflect fdlibm results on all platforms.
        for dv in all_data_values:
            dv.add_filter(fdlibmFilter)

    # =============================================================================
    # Canvas 2 Segmentation
    # =============================================================================
    if script_config['perform_segmentation_shitty']:
        run_segmentation(all_data_values, segmentation_target_metrics, metrics_to_visualize, canvas_metrics)

    # =============================================================================
    # Canvas 2 Decision Tree Segmentation
    # =============================================================================
    if script_config['perform_segmentation_decision_tree']:
        from decision_tree import run_decision_tree_analysis
        all_data_values = run_decision_tree_analysis(
            all_data_values, DEFAULT_SUBSET, metrics_to_visualize, canvas_metrics,
            target_metrics=segmentation_target_metrics,
            preferred_features=segmentation_preferred_features,
            n_workers=script_config['parallel_segmentation'],
        )

    if _seg_any:
        for dv in all_data_values:
            dv.pop_filter()

    # =============================================================================
    # Single-metric removal analysis
    # =============================================================================
    if script_config['perform_single_metric_removal_analysis'] or script_config['perform_iterative_single_metric_removal_analysis'] or script_config['perform_iterative_single_metric_replacement_analysis']:
        # ── Load baselines from cache if partition pass didn't produce them ──
        if not _smr_baselines and _ismr_cache_baselines:
            _smr_baselines = dict(_ismr_cache_baselines)
            for _fp, _ml in _ismr_cache_metric_lists.items():
                if _fp not in smr_metric_lists:
                    smr_metric_lists[_fp] = _ml
            config.log(f"  Using baselines from ISMR cache: {sorted(_smr_baselines.keys())}")
        if not _smr_baselines_by_os and _ismr_cache_baselines_by_os:
            _smr_baselines_by_os = dict(_ismr_cache_baselines_by_os)
            config.log(f"  Using per-OS baselines from ISMR cache")

        # ── Merge SMR fingerprints from disk spill, one FP at a time ─────
        _smr_spill_base = os.path.join(config.ANALYSIS_FOLDER, '_smr_spill')
        config.log(f"  Merging SMR fingerprints from disk spill "
                    f"({len(SMR_FP_NAMES)} fingerprinters)...")
        _smr_merge_start = time.time()

        for _fp in SMR_FP_NAMES:
            _safe_fp = safe_filename(_fp)
            _fp_dir = os.path.join(_smr_spill_base, _safe_fp)
            if not os.path.isdir(_fp_dir):
                config.log(f"    {_fp}: no spill data found")
                continue

            # Load key map: {safe_name → original metric key}
            _map_path = os.path.join(_fp_dir, '_key_map.pkl')
            with open(_map_path, 'rb') as _sf:
                _key_map = pickle.load(_sf)

            _smr_metric_items = sorted(_key_map.items())
            _smr_n_workers = min(parallel_workers, len(_smr_metric_items))
            _smr_slot_counter = iter(range(_smr_n_workers))  # thread-safe via GIL-free atomics
            _smr_slot_map = {}  # thread_id -> slot_idx

            def _merge_one_smr_metric(_item, _fp_dir=_fp_dir):
                _metric_safe, _metric_key = _item
                _tid = threading.get_ident()
                if _tid not in _smr_slot_map:
                    _smr_slot_map[_tid] = next(_smr_slot_counter)
                _sidx = _smr_slot_map[_tid]
                _slot = _smr_display.slots[_sidx]
                _metric_path = os.path.join(_fp_dir, _metric_safe)
                if not os.path.isdir(_metric_path):
                    return None
                _part_files = [f for f in os.listdir(_metric_path) if f.endswith('.pkl')]
                _slot._start(_metric_key[:16], 1)
                _slot.advance_phase('Merging', len(_part_files))
                _merged_by_os = defaultdict(lambda: defaultdict(int))
                for _pi, _part_file in enumerate(_part_files):
                    with open(os.path.join(_metric_path, _part_file), 'rb') as _sf:
                        _part_data = pickle.load(_sf)
                    for _os_val, _os_hashes in _part_data.items():
                        _target = _merged_by_os[_os_val]
                        for _h, _c in _os_hashes.items():
                            _target[_h] += _c
                    del _part_data
                    _slot.update_progress(_pi + 1)
                _global = collapse_os_layer(_merged_by_os)
                _hist = defaultdict(int)
                for _cnt in _global.values():
                    _hist[_cnt] += 1
                _os_hists = None
                if _do_per_os:
                    _os_hists = {}
                    for _ov, _os_data in _merged_by_os.items():
                        _oh = defaultdict(int)
                        for _cnt in _os_data.values():
                            _oh[_cnt] += 1
                        _os_hists[_ov] = dict(_oh)
                _slot.finish()
                return (_metric_key, dict(_hist), _os_hists)

            _fp_histograms = {}
            _fp_histograms_by_os = {}
            _smr_display = ProgressDisplay(
                tty=sys.__stderr__, total_partitions=len(_smr_metric_items),
                enabled=False if args.skip_progress_bars else None)
            _smr_display.start()
            with concurrent.futures.ThreadPoolExecutor(max_workers=_smr_n_workers) as _smr_merge_pool:
                for _result in _smr_merge_pool.map(_merge_one_smr_metric, _smr_metric_items):
                    if _result is not None:
                        _metric_key, _hist, _os_hists = _result
                        _fp_histograms[_metric_key] = _hist
                        if _os_hists:
                            for _ov, _oh in _os_hists.items():
                                if _ov not in _fp_histograms_by_os:
                                    _fp_histograms_by_os[_ov] = {}
                                _fp_histograms_by_os[_ov][_metric_key] = _oh
                    _smr_display.completed += 1
            _smr_display.stop()

            smr_fingerprints[_fp] = _fp_histograms
            if _do_per_os:
                smr_fingerprints_by_os[_fp] = _fp_histograms_by_os
            config.log(f"    {_fp}: merged {len(_fp_histograms)} metrics")

        _smr_merge_elapsed = time.time() - _smr_merge_start
        config.log(f"  SMR merge + histogram conversion: {_smr_merge_elapsed:.2f}s")
        execution_time['smr_merge'] = _smr_merge_elapsed

        # Clean up spill files
        _smr_spill_root = os.path.join(config.ANALYSIS_FOLDER, '_smr_spill')
        if os.path.isdir(_smr_spill_root):
            shutil.rmtree(_smr_spill_root, ignore_errors=True)

        start = time.time()
        _smr_payload = {
            'smr_fingerprints':    dict(smr_fingerprints),
            'smr_metric_lists':    smr_metric_lists,
            'smr_baselines':       dict(_smr_baselines),
            'run_metadata':        dict(config.RUN_METADATA),
            'format':              'histogram',
        }
        if _do_per_os and smr_fingerprints_by_os:
            _smr_payload['smr_fingerprints_by_os'] = dict(smr_fingerprints_by_os)
            _smr_payload['smr_baselines_by_os'] = dict(_smr_baselines_by_os)
        pickle_data(_smr_payload, "smr.bin", hash=None, override_dir=config.OUTPUT_FOLDER)
        elapsed = time.time() - start
        config.log(f"  Elapsed time for SMR pickling: {elapsed:.2f} seconds")
        execution_time['smr_pickling'] = elapsed
        del _smr_payload
        gc.collect()

        if script_config['smr_output']:
            if _do_global:
                for _fp in SMR_FP_NAMES:
                    _bl = _smr_baselines[_fp]
                    output_smr(smr_fingerprints[_fp], smr_metric_lists[_fp], _bl[0], _bl[1],
                               _bl[2], _fp, baseline_fitness_hhi2=_bl[3],
                               baseline_p50=_bl[4] if len(_bl) > 4 else None)
            if _do_per_os:
                for _fp in SMR_FP_NAMES:
                    if _fp not in smr_fingerprints_by_os:
                        continue
                    for _os_val in _os_values:
                        if _os_val not in smr_fingerprints_by_os[_fp]:
                            continue
                        _os_bl = _smr_baselines_by_os.get(_fp, {}).get(_os_val, (0, 0, 0, 0, 0))
                        if _os_bl[0] == 0:
                            continue
                        _os_fp_name = f"{_fp} ({_os_val})"
                        output_smr(smr_fingerprints_by_os[_fp][_os_val], smr_metric_lists[_fp],
                                   _os_bl[0], _os_bl[1], _os_bl[2], _os_fp_name,
                                   baseline_fitness_hhi2=_os_bl[3] if len(_os_bl) > 3 else None,
                                   baseline_p50=_os_bl[4] if len(_os_bl) > 4 else None)

        # ── Iterative Single Metric Removal (ISMR) ───────────────────────
        def _run_ismr(fp_name, cache_dir, metric_list, n_users, n_unique, label=''):
            """Run ISMR iteration loop. Returns (removed_list, elapsed)."""
            _tag = f"ISMR{label}"
            _cache_files = sorted(
                os.path.join(cache_dir, f)
                for f in os.listdir(cache_dir) if f.endswith('.pkl')
            )
            config.log(f"  {_tag}: {fp_name}, {len(metric_list)} metrics, "
                        f"{len(_cache_files)} partition caches")

            _excluded = set()
            _removed = []
            _prev_unique = n_unique
            _start = time.time()

            _mp_ctx = multiprocessing.get_context('forkserver')
            _num_workers = min(parallel_workers, len(_cache_files))
            _worker_config['_ismr_num_workers'] = _num_workers
            _ismr_progress_queue = _mp_ctx.Queue()
            _worker_config['progress_queue'] = _ismr_progress_queue
            _executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=_num_workers,
                mp_context=_mp_ctx,
                initializer=worker_init,
                initargs=(_worker_config,),
            )
            _iteration = 0
            try:
              while True:
                _iteration += 1
                _remaining = [m for m in metric_list if m not in _excluded]
                if not _remaining:
                    config.log(f"  {_tag}: no metrics remaining")
                    break

                _msg = (f"  {_tag} iteration {_iteration}: testing {len(_remaining)} metrics "
                        f"({len(_excluded)} excluded)...")
                config.log_and_print(_msg)
                _iter_t0 = time.time()

                _spill = os.path.join(config.ANALYSIS_FOLDER, '_ismr_iter_spill')
                os.makedirs(_spill, exist_ok=True)

                _ismr_display = ProgressDisplay(
                    tty=sys.__stderr__, total_partitions=_num_workers,
                    enabled=False if args.skip_progress_bars else None)
                _ismr_display.start()
                _ismr_bridge_stop = threading.Event()
                _ismr_bridge_thread = threading.Thread(
                    target=_progress_bridge,
                    args=(_ismr_progress_queue, _ismr_display.slots, _ismr_bridge_stop),
                    daemon=True, name='ismr-progress-bridge',
                )
                _ismr_bridge_thread.start()

                _futures = [
                    _executor.submit(
                        ismr_iteration_worker, wid, _cache_files,
                        list(_excluded), _remaining, _spill, slot_idx=wid
                    )
                    for wid in range(_num_workers)
                ]

                _all_part_ids = []
                for fut in concurrent.futures.as_completed(_futures):
                    _all_part_ids.extend(fut.result())
                    _ismr_display.completed += 1

                _ismr_bridge_stop.set()
                _ismr_bridge_thread.join(timeout=2)
                _ismr_display.stop()
                _t_workers = time.time() - _iter_t0

                _t_merge_start = time.time()
                def _merge_one(_mk, _sp=_spill):
                    _mk_safe = safe_filename(str(_mk))
                    _mk_dir = os.path.join(_sp, _mk_safe)
                    _merged = defaultdict(int)
                    if os.path.isdir(_mk_dir):
                        for _pf in os.listdir(_mk_dir):
                            if _pf.endswith('.pkl'):
                                with open(os.path.join(_mk_dir, _pf), 'rb') as _sf:
                                    for _h, _c in pickle.load(_sf).items():
                                        _merged[_h] += _c
                    return (_mk, sum(1 for v in _merged.values() if v == 1))

                _best_metric = None
                _best_unique = None
                with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers) as _merge_pool:
                    for _mk, _unique in _merge_pool.map(_merge_one, _remaining):
                        if _best_unique is None or _unique < _best_unique:
                            _best_unique = _unique
                            _best_metric = _mk
                _t_merge = time.time() - _t_merge_start

                _t_cleanup_start = time.time()
                shutil.rmtree(_spill, ignore_errors=True)
                _t_cleanup = time.time() - _t_cleanup_start

                _iter_elapsed = time.time() - _iter_t0
                _msg = (f"  {_tag} iteration {_iteration}: remove '{_best_metric}' → "
                        f"{_best_unique} unique users "
                        f"({_best_unique / n_users * 100:.2f}%) "
                        f"[{_iter_elapsed:.1f}s: workers={_t_workers:.1f}s merge={_t_merge:.1f}s cleanup={_t_cleanup:.1f}s]")
                config.log_and_print(_msg)

                if _best_unique >= _prev_unique:
                    _msg = f"  {_tag}: converged — removing '{_best_metric}' does not reduce uniqueness"
                    config.log_and_print(_msg)
                    break

                _excluded.add(_best_metric)
                _removed.append((_best_metric, _best_unique))
                _prev_unique = _best_unique
            finally:
              _executor.shutdown(wait=False)

            _elapsed = time.time() - _start
            config.log(f"  {_tag} complete: {len(_removed)} metrics removed in {_elapsed:.1f}s")
            return _removed, _elapsed

        if script_config['perform_iterative_single_metric_removal_analysis']:
            _ismr_fp = script_config['ismr_fingerprinter']
            _ismr_metric_list = smr_metric_lists[_ismr_fp]
            _ismr_total_elapsed = 0

            if _os_filter:
                # Single-OS mode: use per-OS cache directly
                _fp_safe = safe_filename(_ismr_fp)
                _os_cache_dir = os.path.join(
                    _ismr_cache_base,
                    f"{_fp_safe}_os_{safe_filename(_os_filter)}")
                if not os.path.isdir(_os_cache_dir):
                    print(f"ERROR: No per-OS ISMR cache for ISMR {_ismr_fp} ({_os_filter})", file=sys.stderr)
                    sys.exit(1)
                _os_n, _os_u, _ = _smr_baselines_by_os[_ismr_fp][_os_filter]
                _ismr_removed, _ismr_elapsed = _run_ismr(
                    _ismr_fp, _os_cache_dir, _ismr_metric_list,
                    _os_n, _os_u, label=f" [{_os_filter}]")
                _os_fp_name = f"{_ismr_fp} ({_os_filter})"
                output_ismr(_os_fp_name, _os_n, _os_u, _ismr_removed)
                _ismr_total_elapsed += _ismr_elapsed
            elif _do_global:
                _ismr_n_users, _ismr_n_unique = _smr_baselines[_ismr_fp][:2]
                _ismr_cache_dir = _valid_ismr_caches[_ismr_fp]
                _ismr_removed, _ismr_elapsed = _run_ismr(
                    _ismr_fp, _ismr_cache_dir, _ismr_metric_list,
                    _ismr_n_users, _ismr_n_unique)
                output_ismr(_ismr_fp, _ismr_n_users, _ismr_n_unique, _ismr_removed)
                _ismr_total_elapsed += _ismr_elapsed

            if _do_per_os:
                _fp_safe = safe_filename(_ismr_fp)
                for _os_val in _os_values:
                    _os_cache_dir = os.path.join(
                        _ismr_cache_base,
                        f"{_fp_safe}_os_{safe_filename(_os_val)}")
                    if not os.path.isdir(_os_cache_dir):
                        config.log(f"  ISMR: no per-OS cache for {_os_val}, skipping")
                        continue
                    _os_n, _os_u, _ = _smr_baselines_by_os[_ismr_fp][_os_val]
                    _os_label = f" [{_os_val}]"
                    _os_removed, _os_elapsed = _run_ismr(
                        _ismr_fp, _os_cache_dir, _ismr_metric_list,
                        _os_n, _os_u, label=_os_label)
                    _os_fp_name = f"{_ismr_fp} ({_os_val})"
                    output_ismr(_os_fp_name, _os_n, _os_u, _os_removed)
                    _ismr_total_elapsed += _os_elapsed

            execution_time['ismr'] = _ismr_total_elapsed

        # ── Iterative Single Metric Replacement (ISMRP) ──────────────────
        def _run_ismrp(fp_name, cache_dir, metric_list, n_users, n_unique, threshold_pct, label=''):
            """Run ISMRP iteration loop. Returns (results_list, elapsed)."""
            _tag = f"ISMRP{label}"
            _cache_files = sorted(
                os.path.join(cache_dir, f)
                for f in os.listdir(cache_dir) if f.endswith('.pkl')
            )
            config.log(f"  {_tag}: {fp_name}, {len(metric_list)} metrics, "
                        f"{len(_cache_files)} partition caches, threshold={threshold_pct}%")

            # Compute value frequencies across all partitions
            config.log(f"  {_tag}: computing value frequencies...")
            _val_freq = {m: defaultdict(int) for m in metric_list}
            for _cf in _cache_files:
                with open(_cf, 'rb') as _f:
                    _cached = pickle.load(_f)
                for _row in _cached['rows']:
                    for _m in metric_list:
                        if _m in _row:
                            _val_freq[_m][_row[_m]] += 1
                del _cached

            _mode_map = {}
            _common_values = {}
            for _m in metric_list:
                _counts = _val_freq[_m]
                if not _counts:
                    _mode_map[_m] = None
                    _common_values[_m] = set()
                    continue
                _mode_map[_m] = max(_counts, key=_counts.get)
                _threshold_count = n_users * threshold_pct / 100.0
                _common_values[_m] = {v for v, c in _counts.items() if c >= _threshold_count}
            del _val_freq

            config.log(f"  {_tag}: common-value sets computed (threshold={threshold_pct}%)")
            for _m in sorted(metric_list):
                _n_common = len(_common_values[_m])
                config.log(f"    {_m}: {_n_common} common value(s), mode='{_mode_map[_m]}'")

            # Iteration loop with partition pinning
            _locked = {}
            _results = []
            _prev_unique = n_unique
            _start = time.time()

            _mp_ctx = multiprocessing.get_context('forkserver')
            _num_workers = min(parallel_workers, len(_cache_files))
            _worker_config['_ismr_num_workers'] = _num_workers
            _ismrp_progress_queue = _mp_ctx.Queue()
            _worker_config['progress_queue'] = _ismrp_progress_queue
            _executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=_num_workers,
                mp_context=_mp_ctx,
                initializer=worker_init,
                initargs=(_worker_config,),
            )
            _iteration = 0
            try:
              while True:
                _iteration += 1
                _remaining = [m for m in metric_list if m not in _locked]
                if not _remaining:
                    config.log(f"  {_tag}: no metrics remaining")
                    break

                _msg = (f"  {_tag} iteration {_iteration}: testing {len(_remaining)} metrics "
                        f"({len(_locked)} locked)...")
                config.log_and_print(_msg)
                _iter_t0 = time.time()

                _spill = os.path.join(config.ANALYSIS_FOLDER, '_ismrp_iter_spill')
                os.makedirs(_spill, exist_ok=True)

                _ismrp_display = ProgressDisplay(
                    tty=sys.__stderr__, total_partitions=_num_workers,
                    enabled=False if args.skip_progress_bars else None)
                _ismrp_display.start()
                _ismrp_bridge_stop = threading.Event()
                _ismrp_bridge_thread = threading.Thread(
                    target=_progress_bridge,
                    args=(_ismrp_progress_queue, _ismrp_display.slots, _ismrp_bridge_stop),
                    daemon=True, name='ismrp-progress-bridge',
                )
                _ismrp_bridge_thread.start()

                _futures = [
                    _executor.submit(
                        ismrp_iteration_worker, wid, _cache_files,
                        dict(_locked), _remaining, _common_values, _mode_map,
                        _spill, slot_idx=wid
                    )
                    for wid in range(_num_workers)
                ]

                _merged_replaced = {m: 0 for m in _remaining}
                for fut in concurrent.futures.as_completed(_futures):
                    _part_ids, _part_replaced = fut.result()
                    for _mk, _rc in _part_replaced.items():
                        _merged_replaced[_mk] += _rc
                    _ismrp_display.completed += 1

                _ismrp_bridge_stop.set()
                _ismrp_bridge_thread.join(timeout=2)
                _ismrp_display.stop()
                _t_workers = time.time() - _iter_t0

                _t_merge_start = time.time()
                def _merge_one(_mk, _sp=_spill):
                    _mk_safe = safe_filename(str(_mk))
                    _mk_dir = os.path.join(_sp, _mk_safe)
                    _merged = defaultdict(int)
                    if os.path.isdir(_mk_dir):
                        for _pf in os.listdir(_mk_dir):
                            if _pf.endswith('.pkl'):
                                with open(os.path.join(_mk_dir, _pf), 'rb') as _sf:
                                    for _h, _c in pickle.load(_sf).items():
                                        _merged[_h] += _c
                    return (_mk, sum(1 for v in _merged.values() if v == 1))

                _best_metric = None
                _best_unique = None
                _best_replaced = 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers) as _merge_pool:
                    for _mk, _unique in _merge_pool.map(_merge_one, _remaining):
                        if _best_unique is None or _unique < _best_unique:
                            _best_unique = _unique
                            _best_metric = _mk
                            _best_replaced = _merged_replaced[_mk]
                _t_merge = time.time() - _t_merge_start

                _t_cleanup_start = time.time()
                shutil.rmtree(_spill, ignore_errors=True)
                _t_cleanup = time.time() - _t_cleanup_start
                del _merged_replaced

                _iter_elapsed = time.time() - _iter_t0
                _msg = (f"  {_tag} iteration {_iteration}: replace rare in '{_best_metric}' → "
                        f"{_best_unique} unique users "
                        f"({_best_unique / n_users * 100:.2f}%), "
                        f"{_best_replaced} replaced ({_best_replaced / n_users * 100:.2f}%) "
                        f"[{_iter_elapsed:.1f}s: workers={_t_workers:.1f}s merge={_t_merge:.1f}s cleanup={_t_cleanup:.1f}s]")
                config.log_and_print(_msg)

                if _best_unique >= _prev_unique:
                    _msg = f"  {_tag}: converged — replacing rare in '{_best_metric}' does not reduce uniqueness"
                    config.log_and_print(_msg)
                    break

                _locked[_best_metric] = (_common_values[_best_metric], _mode_map[_best_metric])
                _results.append((_best_metric, _best_unique, _best_replaced))
                _prev_unique = _best_unique
            finally:
              _executor.shutdown(wait=False)

            _elapsed = time.time() - _start
            config.log(f"  {_tag} complete: {len(_results)} metrics replaced in {_elapsed:.1f}s")
            return _results, _elapsed

        if script_config['perform_iterative_single_metric_replacement_analysis']:
            _ismrp_fp = script_config['ismrp_fingerprinter']
            _ismrp_threshold = script_config['ismrp_rare_threshold_pct']
            _ismrp_metric_list = smr_metric_lists[_ismrp_fp]
            _ismrp_total_elapsed = 0

            if _os_filter:
                # Single-OS mode: use per-OS cache directly
                _fp_safe = safe_filename(_ismrp_fp)
                _os_cache_dir = os.path.join(
                    _ismr_cache_base,
                    f"{_fp_safe}_os_{safe_filename(_os_filter)}")
                if not os.path.isdir(_os_cache_dir):
                    print(f"ERROR: No per-OS ISMR cache for ISMRP {_ismrp_fp} ({_os_filter})", file=sys.stderr)
                    sys.exit(1)
                _os_n, _os_u, _ = _smr_baselines_by_os[_ismrp_fp][_os_filter]
                _ismrp_results, _ismrp_elapsed = _run_ismrp(
                    _ismrp_fp, _os_cache_dir, _ismrp_metric_list,
                    _os_n, _os_u, _ismrp_threshold, label=f" [{_os_filter}]")
                _os_fp_name = f"{_ismrp_fp} ({_os_filter})"
                output_ismrp(_os_fp_name, _os_n, _os_u, _ismrp_results, _ismrp_threshold)
                _ismrp_total_elapsed += _ismrp_elapsed
            elif _do_global:
                _ismrp_n_users, _ismrp_n_unique = _smr_baselines[_ismrp_fp][:2]
                _ismrp_cache_dir = _valid_ismr_caches[_ismrp_fp]
                _ismrp_results, _ismrp_elapsed = _run_ismrp(
                    _ismrp_fp, _ismrp_cache_dir, _ismrp_metric_list,
                    _ismrp_n_users, _ismrp_n_unique, _ismrp_threshold)
                output_ismrp(_ismrp_fp, _ismrp_n_users, _ismrp_n_unique, _ismrp_results, _ismrp_threshold)
                _ismrp_total_elapsed += _ismrp_elapsed

            if _do_per_os:
                _fp_safe = safe_filename(_ismrp_fp)
                for _os_val in _os_values:
                    _os_cache_dir = os.path.join(
                        _ismr_cache_base,
                        f"{_fp_safe}_os_{safe_filename(_os_val)}")
                    if not os.path.isdir(_os_cache_dir):
                        config.log(f"  ISMRP: no per-OS cache for {_os_val}, skipping")
                        continue
                    _os_n, _os_u, _ = _smr_baselines_by_os[_ismrp_fp][_os_val]
                    _os_results, _os_elapsed = _run_ismrp(
                        _ismrp_fp, _os_cache_dir, _ismrp_metric_list,
                        _os_n, _os_u, _ismrp_threshold, label=f" [{_os_val}]")
                    _os_fp_name = f"{_ismrp_fp} ({_os_val})"
                    output_ismrp(_os_fp_name, _os_n, _os_u, _os_results, _ismrp_threshold)
                    _ismrp_total_elapsed += _os_elapsed

            execution_time['ismrp'] = _ismrp_total_elapsed

    # =============================================================================
    # Minimum Identifying Set — Local combo analysis
    # =============================================================================
    if script_config['perform_min_set_combo_analysis']:
        import itertools
        from min_set_per_user import (ISMR_TOP_METRICS, ISMR_TOP_METRICS_BY_OS,
                                      SMR_TOP_METRICS, SMR_TOP_METRICS_BY_OS)
        import json as _json

        _metric_source = script_config.get('min_set_combo_metric_source', 'ismr')
        if _metric_source == 'smr':
            _TOP_METRICS = SMR_TOP_METRICS
            _TOP_METRICS_BY_OS = SMR_TOP_METRICS_BY_OS
            config.log(f"  Min-set combo using SMR metric ordering")
        else:
            _TOP_METRICS = ISMR_TOP_METRICS
            _TOP_METRICS_BY_OS = ISMR_TOP_METRICS_BY_OS
            config.log(f"  Min-set combo using ISMR metric ordering")

        _combo_fp = script_config['min_set_combo_fingerprinter']
        _combo_sizes = script_config['min_set_combo_sizes']  # {size: top_n}
        _sizes_desc = ', '.join(f'{k}-way top {v}' for k, v in sorted(_combo_sizes.items()))
        _combo_max_top_n = max(_combo_sizes.values())

        def _run_combo(cache_dir, fp_label, file_suffix='', label='', metric_order=None):
            """Run combo analysis against a cache dir. Returns elapsed time.
            metric_order: ordered list of metrics to use (default: selected _TOP_METRICS).
            """
            if metric_order is None:
                metric_order = _TOP_METRICS
            _tag = f"Combo{label}"
            _cache_files = sorted(
                os.path.join(cache_dir, f)
                for f in os.listdir(cache_dir) if f.endswith('.pkl')
            )

            # Verify metrics in cache and load baselines
            with open(os.path.join(cache_dir, '_meta.json')) as _mf:
                _meta = _json.load(_mf)
            _total_users = _meta.get('baseline_num_users', 0)
            _unique_users = _meta.get('baseline_num_unique', 0)
            _all_metrics = metric_order[:_combo_max_top_n]
            _cache_metrics = set(_meta['metric_list'])
            _missing = [m for m in _all_metrics if m not in _cache_metrics]
            if _missing:
                config.log(f"  {_tag}: metrics not in cache: {_missing}, skipping")
                return 0

            config.log_and_print(f"  {_tag}: {fp_label}, {_sizes_desc}, "
                                  f"{len(_cache_files)} partitions")

            _identified = {}  # {part_id: set of row_indices}
            _start = time.time()
            _all_results = []
            _dedup_by_size = {}

            def _write_combo_output():
                """Write/overwrite combo output files with results so far."""
                _elapsed_so_far = time.time() - _start
                _sorted_results = sorted(_all_results, key=lambda r: (-r['combo_size'], -r['combo_only_unique']))

                _sfx = file_suffix
                _txt_path = os.path.join(config.OUTPUT_FOLDER, f"min_set_combos{_sfx}.txt")
                with open(_txt_path, 'w') as _of:
                    _of.write(f"Min-set Approach 2.5: Local Combo Analysis ({fp_label})\n")
                    _of.write(f"{'=' * 60}\n")
                    _of.write(f"Total users: {_total_users:,}\n")
                    _of.write(f"Unique users (baseline): {_unique_users:,} ({_unique_users / _total_users * 100:.2f}%)\n" if _total_users else "")
                    _of.write(f"Top {_combo_max_top_n} metrics, sizes {', '.join(str(k) for k in sorted(_combo_sizes.keys()))}\n")
                    _of.write(f"Elapsed: {_elapsed_so_far:.1f}s\n\n")
                    _of.write(f"Deduplicated results by size:\n")
                    _cumul = 0
                    for _sz in sorted(_dedup_by_size):
                        _n = _dedup_by_size[_sz]
                        _cumul += _n
                        _of.write(f"  Size {_sz}: {_n:,} new users ({_cumul:,} cumulative)\n")
                    _of.write(f"\nPer-combo breakdown (top 30 per size):\n")
                    for _sz in sorted(_combo_sizes.keys()):
                        _sz_results = [r for r in _sorted_results if r['combo_size'] == _sz]
                        _sz_results.sort(key=lambda r: -r['combo_only_unique'])
                        if not _sz_results:
                            continue
                        _of.write(f"\n--- Size {_sz} ---\n")
                        _of.write(f"{'Combo':<65} {'Unique':>10} {'New':>10}\n")
                        _of.write("-" * 87 + "\n")
                        for r in _sz_results[:30]:
                            _of.write(f"{r['combo_name']:<65} {r['combo_unique']:>10,} {r['combo_only_unique']:>10,}\n")
                        if len(_sz_results) > 30:
                            _rest = sum(r['combo_only_unique'] for r in _sz_results[30:])
                            _of.write(f"{'... + ' + str(len(_sz_results) - 30) + ' more':<65} {'':>10} {_rest:>10,}\n")

                _csv_path = os.path.join(config.OUTPUT_FOLDER, f"min_set_combos{_sfx}.csv")
                with open(_csv_path, 'w', newline='') as _cf:
                    writer = csv.writer(_cf)
                    writer.writerow(['ComboName', 'ComboSize', 'ComboUnique', 'ComboOnlyUniqueNew'])
                    for r in _sorted_results:
                        writer.writerow([r['combo_name'], r['combo_size'], r['combo_unique'], r['combo_only_unique']])

                _dedup_csv_path = os.path.join(config.OUTPUT_FOLDER, f"min_set_combos_dedup{_sfx}.csv")
                with open(_dedup_csv_path, 'w', newline='') as _cf:
                    writer = csv.writer(_cf)
                    writer.writerow(['ComboSize', 'NewUsersIdentified', 'CumulativeTotal'])
                    _cumul = 0
                    for _sz in sorted(_dedup_by_size):
                        _n = _dedup_by_size[_sz]
                        _cumul += _n
                        writer.writerow([_sz, _n, _cumul])

                config.log(f"  Wrote {_txt_path}")
                config.log(f"  Wrote {_csv_path}")
                config.log(f"  Wrote {_dedup_csv_path}")

            # Compute union of all metrics needed across all orderings (overall + per-OS)
            _combo_needed_metrics = set(_TOP_METRICS[:_combo_max_top_n])
            for _os_metrics in _TOP_METRICS_BY_OS.values():
                _combo_needed_metrics.update(_os_metrics[:_combo_max_top_n])

            _mp_ctx = multiprocessing.get_context('forkserver')
            _num_workers = min(parallel_workers, len(_cache_files))
            _worker_config['_ismr_num_workers'] = _num_workers
            _worker_config['_combo_keep_metrics'] = _combo_needed_metrics
            _progress_queue = _mp_ctx.Queue()
            _worker_config['progress_queue'] = _progress_queue
            _executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=_num_workers,
                mp_context=_mp_ctx,
                initializer=worker_init,
                initargs=(_worker_config,),
            )

            try:
              for _size, _size_top_n in sorted(_combo_sizes.items()):
                _size_metrics = metric_order[:_size_top_n]
                _combos_this_size = list(itertools.combinations(_size_metrics, _size))
                if not _combos_this_size:
                    continue

                _size_t0 = time.time()
                _spill = os.path.join(config.ANALYSIS_FOLDER, '_combo_spill')
                os.makedirs(_spill, exist_ok=True)

                _BATCH_SIZE = 50
                _n_batches = (len(_combos_this_size) + _BATCH_SIZE - 1) // _BATCH_SIZE
                config.log_and_print(f"  {_tag} size {_size}: {len(_combos_this_size)} combos "
                                      f"({_n_batches} batch{'es' if _n_batches > 1 else ''})...")

                _batch_t0 = time.time()
                for _batch_idx in range(_n_batches):
                    _batch_start = _batch_idx * _BATCH_SIZE
                    _batch_combos = _combos_this_size[_batch_start : _batch_start + _BATCH_SIZE]
                    if _n_batches > 1:
                        _batch_elapsed = time.time() - _batch_t0
                        if _batch_idx > 0:
                            _batch_avg = _batch_elapsed / _batch_idx
                            _batch_eta = _batch_avg * (_n_batches - _batch_idx)
                            config.log_and_print(f"    Batch {_batch_idx + 1}/{_n_batches}: "
                                                 f"{len(_batch_combos)} combos "
                                                 f"[{_batch_elapsed:.0f}s elapsed, "
                                                 f"~{_batch_avg:.1f}s/batch, "
                                                 f"ETA ~{_batch_eta:.0f}s]")
                        else:
                            config.log_and_print(f"    Batch {_batch_idx + 1}/{_n_batches}: "
                                                 f"{len(_batch_combos)} combos")

                    _display = ProgressDisplay(
                        tty=sys.__stderr__, total_partitions=_num_workers,
                        enabled=False if args.skip_progress_bars else None)
                    _display.start()

                    _bridge_stop = threading.Event()
                    _bridge_thread = threading.Thread(
                        target=_progress_bridge,
                        args=(_progress_queue, _display.slots, _bridge_stop),
                        daemon=True, name='combo-progress-bridge',
                    )
                    _bridge_thread.start()

                    _futures = [
                        _executor.submit(
                            min_set_combo_worker, wid, _cache_files,
                            _batch_combos, _spill, slot_idx=wid
                        )
                        for wid in range(_num_workers)
                    ]

                    _batch_timings = []
                    for fut in concurrent.futures.as_completed(_futures):
                        _res = fut.result()
                        _display.completed += 1
                        if isinstance(_res, dict):
                            _batch_timings.append(_res)

                    _bridge_stop.set()
                    _bridge_thread.join(timeout=2)
                    _display.stop()

                    if _batch_timings:
                        _avg = lambda k: sum(t[k] for t in _batch_timings) / len(_batch_timings)
                        _mx = lambda k: max(t[k] for t in _batch_timings)
                        config.log(f"      workers: load={_avg('t_load'):.1f}s "
                                   f"hash={_avg('t_hash'):.1f}s "
                                   f"combo={_avg('t_combo'):.1f}s "
                                   f"spill={_avg('t_spill'):.1f}s (avg) | "
                                   f"max combo={_mx('t_combo'):.1f}s "
                                   f"max spill={_mx('t_spill'):.1f}s")

                _t_workers = time.time() - _size_t0

                # Merge per-combo from disk (threaded)
                _t_merge_start = time.time()
                _new_this_size = 0

                def _merge_one(_combo, _sp=_spill, _sz=_size):
                    combo_name = '+'.join(_combo)
                    _mk_safe = safe_filename(combo_name)
                    _mk_dir = os.path.join(_sp, _mk_safe)
                    if not os.path.isdir(_mk_dir):
                        return (combo_name, _sz, 0, 0, [])

                    merged_counts = defaultdict(int)
                    for _pf in os.listdir(_mk_dir):
                        if _pf.endswith('_counts.pkl'):
                            with open(os.path.join(_mk_dir, _pf), 'rb') as _sf:
                                for _h, _c in pickle.load(_sf).items():
                                    merged_counts[_h] += _c

                    unique_fps = {fp for fp, cnt in merged_counts.items() if cnt == 1}
                    combo_unique = len(unique_fps)
                    del merged_counts

                    if not unique_fps:
                        return (combo_name, _sz, 0, 0, [])

                    identified_users = []
                    for _pf in os.listdir(_mk_dir):
                        if _pf.endswith('_uidx.pkl'):
                            with open(os.path.join(_mk_dir, _pf), 'rb') as _sf:
                                _uidx = pickle.load(_sf)
                            for _fp, (_part_id, _ridx) in _uidx.items():
                                if _fp in unique_fps:
                                    identified_users.append((_part_id, _ridx))

                    return (combo_name, _sz, combo_unique, len(identified_users), identified_users)

                _merge_pbar = tqdm.tqdm(total=len(_combos_this_size),
                                        desc=f"    Merging size-{_size}",
                                        unit="combo", file=config.terminal)
                with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers) as _merge_pool:
                    for combo_name, combo_size, combo_unique, combo_id_count, identified_users in \
                            _merge_pool.map(_merge_one, _combos_this_size):
                        combo_only_new = 0
                        for _pid, _ridx in identified_users:
                            if _pid not in _identified:
                                _identified[_pid] = set()
                            if _ridx not in _identified[_pid]:
                                _identified[_pid].add(_ridx)
                                combo_only_new += 1

                        _all_results.append({
                            'combo_name': combo_name,
                            'combo_size': combo_size,
                            'combo_unique': combo_unique,
                            'combo_only_unique': combo_only_new,
                        })
                        _new_this_size += combo_only_new
                        _merge_pbar.update(1)
                _merge_pbar.close()
                _t_merge = time.time() - _t_merge_start

                _t_cleanup_start = time.time()
                shutil.rmtree(_spill, ignore_errors=True)
                _t_cleanup = time.time() - _t_cleanup_start

                _dedup_by_size[_size] = _new_this_size
                _total_id = sum(_dedup_by_size.values())
                _size_elapsed = time.time() - _size_t0
                config.log_and_print(
                    f"  {_tag} size {_size}: {_new_this_size:,} new users, "
                    f"{_total_id:,} cumulative "
                    f"[{_size_elapsed:.1f}s: workers={_t_workers:.1f}s merge={_t_merge:.1f}s cleanup={_t_cleanup:.1f}s]"
                )
                _write_combo_output()

            finally:
              _executor.shutdown(wait=False)

            _elapsed = time.time() - _start
            config.log_and_print(f"  {_tag} complete in {_elapsed:.1f}s")
            _write_combo_output()
            return _elapsed

        # Find global ISMR cache
        _combo_cache_dir = _valid_ismr_caches.get(_combo_fp)
        if not _combo_cache_dir:
            _combo_cache_dir = os.path.join(config.ANALYSIS_FOLDER, '_ismr_cache', safe_filename(_combo_fp))
        if not os.path.isdir(_combo_cache_dir):
            print(f"ERROR: No ISMR cache for {_combo_fp}", file=sys.stderr)
            sys.exit(1)

        _combo_total_elapsed = 0

        if _os_filter:
            # Single-OS mode: use per-OS cache directly instead of global
            _fp_safe = safe_filename(_combo_fp)
            _os_cache_dir = os.path.join(
                _ismr_cache_base,
                f"{_fp_safe}_os_{safe_filename(_os_filter)}")
            if not os.path.isdir(_os_cache_dir):
                print(f"ERROR: No per-OS ISMR cache for {_combo_fp} ({_os_filter})", file=sys.stderr)
                sys.exit(1)
            _os_sfx = f"_os_{safe_filename(_os_filter)}"
            _os_metric_order = _TOP_METRICS_BY_OS.get(_os_filter)
            if _os_metric_order:
                config.log(f"  Combo [{_os_filter}]: using per-OS {_metric_source.upper()} ordering "
                           f"({len(_os_metric_order)} metrics) [os_filter]")
            else:
                config.log(f"  Combo [{_os_filter}]: no per-OS ordering, "
                           f"falling back to global [os_filter]")
            _combo_total_elapsed += _run_combo(
                _os_cache_dir, f"{_combo_fp} ({_os_filter})",
                file_suffix=_os_sfx, label=f" [{_os_filter}]",
                metric_order=_os_metric_order)
        elif _do_global:
            _combo_total_elapsed += _run_combo(_combo_cache_dir, _combo_fp)

        if not _os_filter and _do_per_os:
            _fp_safe = safe_filename(_combo_fp)
            for _os_val in _os_values:
                _os_cache_dir = os.path.join(
                    _ismr_cache_base,
                    f"{_fp_safe}_os_{safe_filename(_os_val)}")
                if not os.path.isdir(_os_cache_dir):
                    config.log(f"  Combo: no per-OS cache for {_os_val}, skipping")
                    continue
                _os_sfx = f"_os_{safe_filename(_os_val)}"
                if script_config.get('min_set_combo_per_os_use_overall_metrics'):
                    _os_metric_order = None
                    config.log(f"  Combo [{_os_val}]: using overall {_metric_source.upper()} ordering "
                               f"(min_set_combo_per_os_use_overall_metrics=True)")
                else:
                    _os_metric_order = _TOP_METRICS_BY_OS.get(_os_val)
                    if _os_metric_order:
                        config.log(f"  Combo [{_os_val}]: using per-OS {_metric_source.upper()} ordering "
                                   f"({len(_os_metric_order)} metrics)")
                    else:
                        config.log(f"  Combo [{_os_val}]: no per-OS ordering, "
                                   f"falling back to global")
                _combo_total_elapsed += _run_combo(
                    _os_cache_dir, f"{_combo_fp} ({_os_val})",
                    file_suffix=_os_sfx, label=f" [{_os_val}]",
                    metric_order=_os_metric_order)

        execution_time['min_set_combo'] = _combo_total_elapsed
        gc.collect()

    if script_config['perform_logical_metric_removal_analysis'] and LMR_FP_NAMES:
        # ── Merge LMR fingerprints from disk spill, one FP at a time ─────
        _lmr_spill_base = os.path.join(config.ANALYSIS_FOLDER, '_lmr_spill')
        config.log(f"  Merging LMR fingerprints from disk spill "
                    f"({len(LMR_FP_NAMES)} fingerprinters)...")
        _lmr_merge_start = time.time()

        for _fp in LMR_FP_NAMES:
            _safe_fp = safe_filename(_fp)
            _fp_dir = os.path.join(_lmr_spill_base, _safe_fp)
            if not os.path.isdir(_fp_dir):
                config.log(f"    {_fp}: no spill data found")
                continue

            _map_path = os.path.join(_fp_dir, '_key_map.pkl')
            with open(_map_path, 'rb') as _sf:
                _key_map = pickle.load(_sf)

            _lmr_unit_items = sorted(_key_map.items())
            _lmr_n_workers = min(parallel_workers, len(_lmr_unit_items))
            _lmr_slot_counter = iter(range(_lmr_n_workers))
            _lmr_slot_map = {}

            def _merge_one_lmr_unit(_item, _fp_dir=_fp_dir):
                _unit_safe, _unit_key = _item
                _tid = threading.get_ident()
                if _tid not in _lmr_slot_map:
                    _lmr_slot_map[_tid] = next(_lmr_slot_counter)
                _sidx = _lmr_slot_map[_tid]
                _slot = _lmr_display.slots[_sidx]
                _unit_path = os.path.join(_fp_dir, _unit_safe)
                if not os.path.isdir(_unit_path):
                    return None
                _part_files = [f for f in os.listdir(_unit_path) if f.endswith('.pkl')]
                _slot._start(_unit_key[:16], 1)
                _slot.advance_phase('Merging', len(_part_files))
                _merged_by_os = defaultdict(lambda: defaultdict(int))
                for _pi, _part_file in enumerate(_part_files):
                    with open(os.path.join(_unit_path, _part_file), 'rb') as _sf:
                        _part_data = pickle.load(_sf)
                    for _os_val, _os_hashes in _part_data.items():
                        _target = _merged_by_os[_os_val]
                        for _h, _c in _os_hashes.items():
                            _target[_h] += _c
                    del _part_data
                    _slot.update_progress(_pi + 1)
                _global = collapse_os_layer(_merged_by_os)
                _hist = defaultdict(int)
                for _cnt in _global.values():
                    _hist[_cnt] += 1
                _os_hists = None
                if _do_per_os:
                    _os_hists = {}
                    for _ov, _os_data in _merged_by_os.items():
                        _oh = defaultdict(int)
                        for _cnt in _os_data.values():
                            _oh[_cnt] += 1
                        _os_hists[_ov] = dict(_oh)
                _slot.finish()
                return (_unit_key, dict(_hist), _os_hists)

            _fp_histograms = {}
            _fp_histograms_by_os = {}
            _lmr_display = ProgressDisplay(
                tty=sys.__stderr__, total_partitions=len(_lmr_unit_items),
                enabled=False if args.skip_progress_bars else None)
            _lmr_display.start()
            with concurrent.futures.ThreadPoolExecutor(max_workers=_lmr_n_workers) as _lmr_merge_pool:
                for _result in _lmr_merge_pool.map(_merge_one_lmr_unit, _lmr_unit_items):
                    if _result is not None:
                        _unit_key, _hist, _os_hists = _result
                        _fp_histograms[_unit_key] = _hist
                        if _os_hists:
                            for _ov, _oh in _os_hists.items():
                                if _ov not in _fp_histograms_by_os:
                                    _fp_histograms_by_os[_ov] = {}
                                _fp_histograms_by_os[_ov][_unit_key] = _oh
                    _lmr_display.completed += 1
            _lmr_display.stop()

            lmr_fingerprints[_fp] = _fp_histograms
            if _do_per_os:
                lmr_fingerprints_by_os[_fp] = _fp_histograms_by_os
            config.log(f"    {_fp}: merged {len(_fp_histograms)} units")

        _lmr_merge_elapsed = time.time() - _lmr_merge_start
        config.log(f"  LMR merge + histogram conversion: {_lmr_merge_elapsed:.2f}s")
        execution_time['lmr_merge'] = _lmr_merge_elapsed

        # Clean up spill files
        if os.path.isdir(_lmr_spill_base):
            shutil.rmtree(_lmr_spill_base, ignore_errors=True)

        start = time.time()
        _lmr_payload = {
            'lmr_fingerprints': dict(lmr_fingerprints),
            'lmr_unit_lists':   dict(lmr_unit_lists),
            'lmr_baselines':    dict(_lmr_baselines),
            'run_metadata':     dict(config.RUN_METADATA),
            'format':           'histogram',
        }
        if _do_per_os and lmr_fingerprints_by_os:
            _lmr_payload['lmr_fingerprints_by_os'] = dict(lmr_fingerprints_by_os)
            _lmr_payload['lmr_baselines_by_os'] = dict(_lmr_baselines_by_os)
        pickle_data(_lmr_payload, "lmr.bin", hash=None, override_dir=config.OUTPUT_FOLDER)
        elapsed = time.time() - start
        config.log(f"  Elapsed time for LMR pickling: {elapsed:.2f} seconds")
        execution_time['lmr_pickling'] = elapsed
        del _lmr_payload
        gc.collect()

        if script_config['lmr_output']:
            if _do_global:
                run_lmr_analysis(lmr_fingerprints, lmr_unit_lists, _lmr_baselines)
            if _do_per_os:
                for _os_val in _os_values:
                    _os_lmr_fps = {}
                    _os_lmr_baselines = {}
                    for _fp in LMR_FP_NAMES:
                        if _fp in lmr_fingerprints_by_os and _os_val in lmr_fingerprints_by_os[_fp]:
                            _os_lmr_fps[_fp] = lmr_fingerprints_by_os[_fp][_os_val]
                            _os_lmr_baselines[_fp] = _lmr_baselines_by_os.get(_fp, {}).get(_os_val, (0, 0, 0, 0, 0))
                    if _os_lmr_fps:
                        # Use modified fp names so output files get OS suffix
                        _os_lmr_fps_renamed = {f"{fp} ({_os_val})": data for fp, data in _os_lmr_fps.items()}
                        _os_lmr_baselines_renamed = {f"{fp} ({_os_val})": bl for fp, bl in _os_lmr_baselines.items()}
                        _os_unit_lists_renamed = {f"{fp} ({_os_val})": lmr_unit_lists[fp] for fp in _os_lmr_fps}
                        run_lmr_analysis(_os_lmr_fps_renamed, _os_unit_lists_renamed, _os_lmr_baselines_renamed)

        del lmr_fingerprints, lmr_fingerprints_by_os
        gc.collect()


    # ── Merge combined hash lookup from worker partitions ────────────────
    import json as _json
    _lookup_parts_dir = os.path.join(config.OUTPUT_FOLDER, '_hash_lookup_parts')
    if os.path.isdir(_lookup_parts_dir):
        for _fname in os.listdir(_lookup_parts_dir):
            if _fname.endswith('.json'):
                with open(os.path.join(_lookup_parts_dir, _fname)) as _lf:
                    config.COMBINED_HASH_LOOKUP.update(_json.load(_lf))
        import shutil as _shutil
        _shutil.rmtree(_lookup_parts_dir, ignore_errors=True)
    if config.COMBINED_HASH_LOOKUP:
        _lookup_path = os.path.join(config.OUTPUT_FOLDER, "combined_hash_lookup.json")
        with open(_lookup_path, "w") as _f:
            _json.dump(config.COMBINED_HASH_LOOKUP, _f)
        print(f"Wrote combined hash lookup ({len(config.COMBINED_HASH_LOOKUP)} entries): {_lookup_path}")

    # Custom function output
    if CUSTOM_FUNCTIONS:
        for cf in CUSTOM_FUNCTIONS:
            print(f"  Custom function output: {cf['name']}")
            cf['output'](custom_accumulators[cf['name']], config.OUTPUT_FOLDER)

    print("\nAll analysis complete.")
    print(f"Wrote to:    {args.output_folder}")
    print(f"Pattern Hash: {config.PATTERN_HASH} - {config.get_analysis_hash_path(config.PATTERN_HASH)}\n")
    config.log("Execution times (seconds):")
    for k, v in execution_time.items():
        if k != "total_tmp":
            config.log(f"  {k}: {v:.2f}")
    config.log(f"Total execution time: {time.time() - execution_time['total_tmp']:.2f} seconds\n")
    # =============================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback as _traceback
        _tb = _traceback.format_exc()
        config.log("CRASH:\n" + _tb)
        # Print crash summary to stderr (traceback may scroll off in terminal)
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"CRASH — see {config.OUTPUT_FOLDER}/run.log for full details", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr, flush=True)
        config.stop_log_thread()
        raise
