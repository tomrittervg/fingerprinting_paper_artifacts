"""Top-level partition worker module for ProcessPoolExecutor.

process_partition in analyze.py was a closure capturing ~30 variables from
main().  Closures cannot be pickled, so they cannot be submitted to
ProcessPoolExecutor.  This module provides worker_init() (the pool initializer)
and partition_worker() (the top-level task function) as module-level callables.

Why processes instead of threads?
    pickle.load() on a ~470 MiB DataValues partition creates millions of Python
    objects.  Under concurrent threads — even with free-threaded Python 3.14t
    (no GIL) — pymalloc's per-thread arenas exhaust quickly, causing heavy
    contention on global allocation locks.  The result: 8 threads loading 8
    partitions in parallel is slower than loading them serially.  Separate
    processes each own their allocator and scale near-linearly (8 processes
    load 8 partitions in ~3.3 s vs ~18 s serial — 5.5× speedup).
"""

import csv
import hashlib
import os
import pickle
import sys
import queue
import random
import threading
import concurrent.futures
import time
import traceback
from collections import defaultdict

import config
from calculations import (
    calculate_aggregated_metrics,
    calculate_aggregated_metrics_grouped_by_metric,
    calculate_aggregated_metrics_impl,
    calculate_fingerprint_set,
    default_metric_aggregation_by_metric,
)
from data import load_partition_data
from datavalues import _validate_and_complete_default_subset
from fingerprinters import ALL_FINGERPRINTERS
from graphing import safe_filename
from modes import ALL_MODES


def _dd_int():
    """Picklable factory for defaultdict(_dd_int)."""
    return defaultdict(int)


# ── Per-process state ─────────────────────────────────────────────────────────
# Populated once by worker_init(); read (never written) by partition_worker().
_W: dict = {}


def worker_init(wc: dict) -> None:
    """ProcessPoolExecutor initializer: called once in each worker process.

    Sets config module globals and stashes all runtime configuration in _W so
    partition_worker() can access it without closure capture.
    """
    config.ANALYSIS_FOLDER = wc['analysis_folder']
    config.OUTPUT_FOLDER   = wc['output_folder']
    config.PATTERN_HASH    = wc['pattern_hash']
    from datavalues import DEFAULT_SUBSET as _DS
    _DS.update(wc['extra_default_subset'])
    _W.update(wc)

    # Set up per-worker log file so config.log() calls produce output.
    # Each worker writes to run_worker_<pid>.log in the output folder.
    pid = os.getpid()
    log_path = os.path.join(config.OUTPUT_FOLDER, f'run_worker_{pid}.log')
    log_file = open(log_path, 'w', buffering=1)
    config.run_log = config.CleanStream(log_file)
    config.start_log_thread()

    # Redirect stderr (both Python-level and fd 2) to the worker log so that
    # unexpected warnings from libraries (BigQuery, etc.) don't write to the
    # TTY and corrupt the progress display.
    sys.stderr = log_file
    os.dup2(log_file.fileno(), 2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _send(q, slot_idx: int, event: str, *args) -> None:
    """Post a progress event to the main-process bridge queue.  No-op if None."""
    if q is not None:
        try:
            q.put_nowait((slot_idx, event) + args)
        except Exception:
            pass  # drop rather than block the worker


def _get_rss_mb() -> int:
    """Return current process RSS in MB (Linux only, 0 on failure)."""
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) // 1024  # kB -> MB
    except Exception:
        pass
    return 0


def _send_rss(q, slot_idx: int) -> None:
    """Send current process RSS (MB) to the progress display."""
    if q is None:
        return
    _send(q, slot_idx, 'rss', _get_rss_mb())


def _rebuild_combined_hash_lookup(d, _combined_hash, _json) -> None:
    """Rebuild missing entries in config.COMBINED_HASH_LOOKUP from DataValues attributes."""
    _L = config.COMBINED_HASH_LOOKUP
    _N = lambda v: None if v == "None" else v
    _sep = (',', ':')

    # Direct passthrough: hash(source_string)
    _DIRECT = [
        ('combined_webgl1_params_hash', 'webgl_params'),
        ('combined_webgl1_params_sw_hash', 'webgl_params_software'),
        ('combined_webgl2_params_hash', 'webgl2_params'),
        ('combined_webgl2_params_sw_hash', 'webgl2_params_software'),
        ('combined_webgl_extensions_hash', 'webgl_params_extensions'),
        ('combined_webgl_extensions_sw_hash', 'webgl_params_extensions_software'),
        ('combined_webgl2_extensions_hash', 'webgl2_params_extensions'),
        ('combined_webgl2_extensions_sw_hash', 'webgl2_params_extensions_software'),
        ('combined_css_colors_hash', 'font_css_system_colors'),
        ('combined_css_fonts_hash', 'font_css_system_fonts'),
        ('combined_math_ops_diag_hash', 'math_ops_fdlibm_2'),
        ('combined_mathml_diag_hash', 'mathml_diag_values'),
    ]
    for hash_attr, src_attr in _DIRECT:
        h = getattr(d, hash_attr, "None")
        if h and h != "None" and h not in _L:
            val = getattr(d, src_attr, None)
            if val and val != "None":
                _combined_hash(val)

    # math_ops: hash of the JSON array of all math_op_* values
    h = getattr(d, 'combined_math_ops_hash', "None")
    if h and h != "None" and h not in _L:
        ops = []
        for i in range(200):
            v = getattr(d, f'math_op_{i}', None)
            if v is None:
                break
            ops.append(v)
        if ops:
            _combined_hash(_json.dumps(ops, separators=_sep))

    # math_ops_fdlibm: same structure
    h = getattr(d, 'combined_math_ops_fdlibm_hash', "None")
    if h and h != "None" and h not in _L:
        ops = []
        for i in range(200):
            v = getattr(d, f'math_op_fdlibm_{i}', None)
            if v is None:
                break
            if v == "None":
                break  # non-WINNT users have all "None"
            ops.append(v)
        if ops:
            _combined_hash(_json.dumps(ops, separators=_sep))

    # mathml: hash of [mathml_1..mathml_10]
    h = getattr(d, 'combined_mathml_hash', "None")
    if h and h != "None" and h not in _L:
        vals = [_N(getattr(d, f'mathml_{i}', "None")) for i in range(1, 11)]
        _combined_hash(_json.dumps(vals, separators=_sep))

    # media_capabilities: hash of 4 attributes
    h = getattr(d, 'combined_media_capabilities_hash', "None")
    if h and h != "None" and h not in _L:
        vals = [_N(v) for v in [
            getattr(d, 'media_capabilities_not_efficient', "None"),
            getattr(d, 'media_capabilities_not_smooth', "None"),
            getattr(d, 'media_capabilities_unsupported', "None"),
            getattr(d, 'media_h264', "None")]]
        _combined_hash(_json.dumps(vals, separators=_sep))

    # canvas hardware/software: hash of 13 canvas attrs each
    for prefix, hash_attr in [('canvas_canvasdata', 'combined_canvas_hardware_hash'),
                               ('canvassoftware_canvasdata', 'combined_canvas_software_hash')]:
        h = getattr(d, hash_attr, "None")
        if h and h != "None" and h not in _L:
            vals = []
            for i in range(1, 11):
                vals.append(_N(getattr(d, f'{prefix}{i:02d}', "None")))
            vals.append(_N(getattr(d, f'{prefix}11_webgl', "None")))
            vals.append(_N(getattr(d, f'{prefix}12_fingerprintjs1', "None")))
            vals.append(_N(getattr(d, f'{prefix}13_fingerprintjs2', "None")))
            _combined_hash(_json.dumps(vals, separators=_sep))

    # clientrects: 5 hashes from ranges of sub-attributes
    for cr_prefix, cr_range, cr_hash in [
        ('clientrects_element_gbcr_', range(1, 13), 'combined_clientrects_element_gbcr_hash'),
        ('clientrects_element_gcr_',  range(1, 13), 'combined_clientrects_element_gcr_hash'),
        ('clientrects_range_gbcr_',   range(1, 13), 'combined_clientrects_range_gbcr_hash'),
        ('clientrects_range_gcr_',    range(1, 13), 'combined_clientrects_range_gcr_hash'),
        ('clientrects_emoji_',        range(1, 7),  'combined_clientrects_emoji_hash'),
    ]:
        h = getattr(d, cr_hash, "None")
        if h and h != "None" and h not in _L:
            vals = [_N(getattr(d, f'{cr_prefix}{i:02d}', "None")) for i in cr_range]
            _combined_hash(_json.dumps(vals, separators=_sep))

    # fonts_variants: 2 hashes from variant a-i
    for suffix, hash_attr in [('allowlisted', 'combined_fonts_variants_allowlisted_hash'),
                               ('nonallowlisted', 'combined_fonts_variants_nonallowlisted_hash')]:
        h = getattr(d, hash_attr, "None")
        if h and h != "None" and h not in _L:
            vals = [_N(getattr(d, f'fonts_variant_{v}_{suffix}', "None"))
                    for v in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']]
            _combined_hash(_json.dumps(vals, separators=_sep))

    # wgpu: hash of all wgpu_* limit attributes (matches BQ process_02_03.sql.template)
    h = getattr(d, 'combined_wgpu_hash', "None")
    if h and h != "None" and h not in _L:
        wgpu_attrs = [
            'wgpu_maxtexturedimension1d', 'wgpu_maxtexturedimension2d', 'wgpu_maxtexturedimension3d',
            'wgpu_maxtexturearraylayers', 'wgpu_maxbindgroups', 'wgpu_maxbindgroupsplusvertexbuffers',
            'wgpu_maxbindingsperbindgroup', 'wgpu_maxdynamicuniformbuffersperpipelinelayout',
            'wgpu_maxdynamicstoragebuffersperpipelinelayout', 'wgpu_maxsampledtexturespershaderstage',
            'wgpu_maxsamplerspershaderstage', 'wgpu_maxstoragebufferspershaderstage',
            'wgpu_maxstoragetexturespershaderstage', 'wgpu_maxuniformbufferspershaderstage',
            'wgpu_maxuniformbufferbindingsize', 'wgpu_maxstoragebufferbindingsize',
            'wgpu_minuniformbufferoffsetalignment', 'wgpu_minstoragebufferoffsetalignment',
            'wgpu_maxvertexbuffers', 'wgpu_maxbuffersize', 'wgpu_maxvertexattributes',
            'wgpu_maxvertexbufferarraystride', 'wgpu_maxinterstageshadervariables',
            'wgpu_maxcolorattachments', 'wgpu_maxcolorattachmentbytespersample',
            'wgpu_maxcomputeworkgroupstoragesize', 'wgpu_maxcomputeinvocationsperworkgroup',
            'wgpu_maxcomputeworkgroupsizex', 'wgpu_maxcomputeworkgroupsizey',
            'wgpu_maxcomputeworkgroupsizez', 'wgpu_maxcomputeworkgroupsperdimension',
        ]
        vals = [_N(getattr(d, a, "None")) for a in wgpu_attrs]
        _combined_hash(_json.dumps(vals, separators=_sep))
        # Legacy (buggy) attribute list — store under its hash too so old lookups resolve
        wgpu_attrs_legacy = [
            'wgpu_maxtexturedimension1d', 'wgpu_maxtexturedimension2d', 'wgpu_maxtexturedimension3d',
            'wgpu_maxtexturearraylayers', 'wgpu_maxbindgroups', 'wgpu_maxbindgroupsplusvariablegroups',
            'wgpu_maxbindingsperbindgroup', 'wgpu_maxdynamicuniformbuffersperpipelinelayout',
            'wgpu_maxdynamicstoragebuffersperpipelinelayout', 'wgpu_maxsampledbufferspershaderstage',
            'wgpu_maxsamplespershaderstage', 'wgpu_maxstoragebufferspershaderstage',
            'wgpu_maxstoragetexturespershaderstage', 'wgpu_maxuniformbufferspershaderstage',
            'wgpu_maxuniformbufferbindingsize', 'wgpu_maxstoragebufferbindingsize',
            'wgpu_minuniformbufferoffsetalignment', 'wgpu_minstoragebufferoffsetalignment',
            'wgpu_maxvertexbuffers', 'wgpu_maxbuffersize', 'wgpu_maxvertexattributes',
            'wgpu_maxvertexbufferarraystride', 'wgpu_maxinterstageshadercomponents',
            'wgpu_maxinterstageshadervariables', 'wgpu_maxcolorattachments',
            'wgpu_maxcolorattachmentbytespersample', 'wgpu_maxcomputeworkgroupstoragesize',
            'wgpu_maxcomputeinvocationsperworkgroup', 'wgpu_maxcomputeworkgroupsizex',
            'wgpu_maxcomputeworkgroupsizey', 'wgpu_maxcomputeworkgroupsizez',
            'wgpu_maxcomputeworkgroupsperdimension',
        ]
        vals_legacy = [_N(getattr(d, a, "None")) for a in wgpu_attrs_legacy]
        _combined_hash(_json.dumps(vals_legacy, separators=_sep))


def _apply_post_pickle_corrections(data) -> None:
    # webGLParamMetricFilter is now applied during range cache build
    # (in apply_correction_filters). Only apply here for old caches
    # that predate that change.
    if not data:
        return
    from filters import webGLParamMetricFilter, cpuModelFilter, webglRendererRawFilter, machineModelFilter, CanvasSoftwareFillIn
    for d in data:
        if not any(type(f).__name__ == 'webGLParamMetricFilter' for f in d.filters):
            d.add_filter(webGLParamMetricFilter)

    # Fill in missing hardware canvas with software canvas values
    CanvasSoftwareFillIn.reset_counters()
    for d in data:
        if not any(type(f).__name__ == 'CanvasSoftwareFillIn' for f in d.filters):
            d.add_filter(CanvasSoftwareFillIn)

    # Re-derive classification fields from raw attributes using latest filter code.
    # The raw attributes (hw_cpu_model, webgl_renderer_raw, hw_machine_model) are
    # preserved in the range cache; only the derived fields need updating.
    _cpu = cpuModelFilter.__new__(cpuModelFilter)
    _gpu = webglRendererRawFilter.__new__(webglRendererRawFilter)
    _mm  = machineModelFilter.__new__(machineModelFilter)

    # Rebuild combined hash lookup: always check for missing entries.
    # Even if the lookup was partially loaded from a file, individual
    # partitions may have hashes not yet in it.
    from datavalues import _combined_hash
    import json as _json

    for d in data:
        # CPU model → manufacturer, family, microarch, model
        mfr, fam, micro, model = _cpu.normalize_cpu_model(d.hw_cpu_model)
        d.hw_cpu_model_manufacturer = mfr
        d.hw_cpu_model_family       = fam
        d.hw_cpu_model_microarch    = micro
        d.hw_cpu_model_model        = model
        # WebGL renderer → vendor, family, model, api
        raw = getattr(d, 'webgl_renderer_raw', None)
        v, fam, mod, api = _gpu.normalize_renderer(raw)
        d.webgl_renderer_raw_vendor = v
        d.webgl_renderer_raw_family = fam
        d.webgl_renderer_raw_model  = mod
        d.webgl_renderer_raw_api    = api
        # Machine model → vendor, category, family
        v, cat, fam = _mm.normalize(d.hw_machine_model)
        d.hw_machine_model_vendor   = v
        d.hw_machine_model_category = cat
        d.hw_machine_model_family   = fam

        # Screen outer - inner (browser chrome) — new derived metric
        try:
            ow = int(d.screen_web_outer_width)
            iw = int(d.screen_web_inner_width)
            oh = int(d.screen_web_outer_height)
            ih = int(d.screen_web_inner_height)
            d.screen_web_outer_inner_width_diff = str(ow - iw)
            d.screen_web_outer_inner_height_diff = str(oh - ih)
            d.screen_web_outer_inner_diff = d.screen_web_outer_inner_width_diff + "x" + d.screen_web_outer_inner_height_diff
        except (ValueError, AttributeError):
            d.screen_web_outer_inner_width_diff = "0"
            d.screen_web_outer_inner_height_diff = "0"
            d.screen_web_outer_inner_diff = "0x0"

        # Rebuild combined hash lookup: for each combined_*_hash attribute,
        # if the hash isn't already in the lookup, reconstruct from source attrs.
        _rebuild_combined_hash_lookup(d, _combined_hash, _json)


# Named factories so defaultdicts in the result dict are picklable
# (lambdas are not picklable across process boundaries).
_PROGRESS_CHUNKS = 20  # send an update every ~5% of a phase

def _chunked(data, n):
    """Yield successive n-sized slices of data."""
    for i in range(0, len(data), n):
        yield data[i:i + n]

def _di():
    return defaultdict(int)

def _ddi():
    return defaultdict(_di)

def _dddi():
    return defaultdict(_ddi)


# ── Main worker ───────────────────────────────────────────────────────────────

def partition_worker(partition, slot_idx: int):
    """Load and fully process one partition.  Returns the result dict.

    This is the process-pool equivalent of the old process_partition closure in
    analyze.py.  All configuration is read from _W (populated by worker_init).
    """
    try:
        return _partition_worker_impl(partition, slot_idx)
    except Exception:
        tb = traceback.format_exc()
        config.log(f"[{partition[0]}/{partition[1]}] CRASH:\n{tb}")
        config.stop_log_thread()
        raise


def _partition_worker_impl(partition, slot_idx: int):
    progress_queue = _W.get('progress_queue')
    wc           = _W
    sc           = wc['script_config']
    total_phases = wc['total_phases']
    n_threads    = wc['max_worker_threads']

    label = str(partition[0])[:8] if partition else '?'
    _send(progress_queue, slot_idx, 'start', label, total_phases)

    # ── Load ─────────────────────────────────────────────────────────────────
    _send(progress_queue, slot_idx, 'advance', 'Loading')
    t0 = time.time()

    def _source_cb(src):
        _send(progress_queue, slot_idx, 'rename', f'Loading ({src})')

    data, num_users, num_users_by_os, load_stats = load_partition_data(
        partition,
        wc['all_days'], wc['start_day'], wc['end_day'],
        wc['tiny'], wc['no_cache'], wc['rebuild_cache'], wc['minimize'],
        wc['partition_width'],
        raw_rows_only=False,
        quiet=True,
        source_cb=_source_cb,
        schema=wc['schema'],
        bq_counts=None if wc['tiny'] else wc['bq_counts'],
        bq_filtered_counts=None if wc['tiny'] else wc['bq_filtered_counts'],
        n_filter_threads=wc['max_worker_threads'],
    )
    load_elapsed = time.time() - t0
    _send_rss(progress_queue, slot_idx)

    result = {
        'num_users':       num_users,
        'num_users_by_os': dict(num_users_by_os),
        'load_elapsed':    load_elapsed,
        'source':          load_stats.get('source', 'unknown'),
        'cached_days':     load_stats.get('cached_days', 0),
        'queried_days':    load_stats.get('queried_days', 0),
        'load_timings': {
            'unpickle':    load_stats.get('unpickle_time', 0),
            'prefilter':   load_stats.get('prefilter_time', 0),
            'dedup':       load_stats.get('dedup_time', 0),
            'parse':       load_stats.get('parse_time', 0),
            'filter':      load_stats.get('filter_time', 0),
            'range_save':  load_stats.get('range_save_time', 0),
        },
        '_slot_idx':       slot_idx,
    }

    if not data:
        result['empty'] = True
        _send(progress_queue, slot_idx, 'finish')
        return result
    result['empty'] = False

    phase_times = {}   # phase_name -> elapsed seconds

    _t0 = time.time()
    _apply_post_pickle_corrections(data)
    # Log canvas fill-in stats
    from filters import CanvasSoftwareFillIn
    _canvas_report = CanvasSoftwareFillIn.report()
    if "replaced" in _canvas_report.lower() and "0 replaced ALL" not in _canvas_report:
        config.log(_canvas_report)
    _validate_and_complete_default_subset(data[0])

    # Exclude late-arriving users not in the frozen LatestSubmission dataset.
    # Each partition_exclude_XX.csv contains client IDs to drop.
    _exclude_dir = os.path.join(config.ANALYSIS_FOLDER,
                                'final-range-latest-submission-from-aggregatedata2')
    _prefix = partition[1] if partition else None
    if _prefix and os.path.isdir(_exclude_dir):
        _exc_path = os.path.join(_exclude_dir, f'partition_exclude_{_prefix}.csv')
        if os.path.exists(_exc_path):
            import csv as _csv_mod
            _exc_ids = set()
            with open(_exc_path, newline='') as _ef:
                for _row in _csv_mod.DictReader(_ef):
                    _exc_ids.add(_row['client_identifier'])
            if _exc_ids:
                _before = len(data)
                data = [dv for dv in data if dv.client_id not in _exc_ids]
                _dropped = _before - len(data)
                if _dropped:
                    num_users = len(data)
                    result['num_users'] = num_users
                    config.log(f"[{partition[0]}/{partition[1]}]   excluded {_dropped} "
                               f"late-arriving users ({_before} → {num_users})")

    phase_times['corrections'] = time.time() - _t0

    # Save hash lookup to range cache dir if not already there
    if config.COMBINED_HASH_LOOKUP:
        from data import get_hash
        _part_hash = get_hash([partition[0]])
        _range_hash = get_hash([str(wc['start_day']), str(wc['end_day'])])
        _rd = os.path.join(config.ANALYSIS_FOLDER, _part_hash, 'ranges',
                           f"schema{wc['schema']}", _range_hash)
        if os.path.isdir(_rd):
            _lp = os.path.join(_rd, "combined_hash_lookup.json")
            if not os.path.exists(_lp):
                try:
                    import json as _json_hl
                    with open(_lp, 'w') as _lf:
                        _json_hl.dump(config.COMBINED_HASH_LOOKUP, _lf)
                except OSError:
                    pass

    # ── OS filter: discard non-matching users early ─────────────────────────
    _os_filter = wc.get('os_filter')
    if _os_filter and data:
        data = [dv for dv in data if dv.os == _os_filter]
        num_users = len(data)
        result['num_users'] = num_users
        result['num_users_by_os'] = {_os_filter: num_users} if num_users else {}
        if not data:
            result['empty'] = True
            _send(progress_queue, slot_idx, 'finish')
            return result

    # ── Metric aggregation ───────────────────────────────────────────────────
    _do_metrics_by_os = sc['calculate_metrics_aggregated'] and sc['per_os_analysis'] in (True, 'only')

    # Check if any phase after metrics needs the data list
    _data_needed_later = (
        sc['fingerprint_archiving'] or sc['fingerprints'] or
        sc['fingerprint_buckets'] or sc['metric_buckets'] or
        sc['missing_fonts'] or sc['experiments'] or
        sc['calculate_metric_experiment_aggregated'] or
        sc['browser_modes'] or
        sc['perform_single_metric_removal_analysis'] or
        sc['perform_logical_metric_removal_analysis'] or
        sc['perform_min_set_combo_analysis'] or
        wc.get('CUSTOM_FUNCTIONS')
    )

    if sc['calculate_metrics_aggregated'] or _do_metrics_by_os:
        _send(progress_queue, slot_idx, 'advance', 'Metrics', len(data))
        _t0 = time.time()
        chunk_size = max(1, len(data) // _PROGRESS_CHUNKS)
        if _do_metrics_by_os:
            local_by_os = defaultdict(default_metric_aggregation_by_metric)
            done = 0
            for chunk in _chunked(data, chunk_size):
                calculate_aggregated_metrics_grouped_by_metric(
                    local_by_os, chunk, wc['metrics_to_visualize'], 'os',
                )
                done += len(chunk)
                _send(progress_queue, slot_idx, 'update', done)
            result['metric_aggregation_by_os'] = local_by_os
            if sc['calculate_metrics_aggregated']:
                result['metric_aggregation'] = {
                    m: local_by_os[m][0] for m in wc['metrics_to_visualize']
                }
        else:
            local_ma = {m: defaultdict(int) for m in wc['metrics_to_visualize']}
            done = 0
            if _data_needed_later:
                for chunk in _chunked(data, chunk_size):
                    calculate_aggregated_metrics(local_ma, chunk, wc['metrics_to_visualize'])
                    done += len(chunk)
                    _send(progress_queue, slot_idx, 'update', done)
            else:
                # Consume-and-discard: free DVs as we go to reduce peak memory
                total = len(data)
                while data:
                    chunk = data[:chunk_size]
                    del data[:chunk_size]
                    calculate_aggregated_metrics(local_ma, chunk, wc['metrics_to_visualize'])
                    done += len(chunk)
                    _send(progress_queue, slot_idx, 'update', done)
                del chunk
            result['metric_aggregation'] = local_ma
        phase_times['metrics'] = time.time() - _t0
        _send_rss(progress_queue, slot_idx)

    # ── Fingerprint archiving ────────────────────────────────────────────────
    if sc['fingerprint_archiving']:
        _t0 = time.time()
        part_id = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")
        n_calcs = len(wc['CALCULATIONS_FOR_ARCHIVING'])
        _send(progress_queue, slot_idx, 'advance', 'FP Archive', len(data) * n_calcs)
        local_fa_tracking = defaultdict(_di)
        for calc_idx, (title, expose_metrics, filter_set, fingerprinters_set) in \
                enumerate(wc['CALCULATIONS_FOR_ARCHIVING']):
            csv_path = os.path.join(
                config.OUTPUT_FOLDER,
                f"fingerprint_archive_{safe_filename(title)}_part_{part_id}.csv",
            )
            with open(csv_path, mode='w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(
                    list(expose_metrics) + [f"{title}-{n}" for n in fingerprinters_set]
                )
                for dv in data:
                    row = []
                    for metric in expose_metrics:
                        val = getattr(dv, metric, None)
                        if calc_idx == 0:
                            local_fa_tracking[metric][val] += 1
                        row.append(val)
                    for f in filter_set:
                        dv.add_filter(f)
                    for name, subset in fingerprinters_set.items():
                        row.append(dv.fingerprint(subset).hex())
                    for f in reversed(filter_set):
                        dv.pop_filter()
                    csv_writer.writerow(row)
        result['fingerprint_archive_tracking'] = local_fa_tracking
        phase_times['fp_archive'] = time.time() - _t0

    # ── Fingerprints ─────────────────────────────────────────────────────────
    # Format: {fp_name: {os: {hash: count}}} — OS-bucketed primary format.
    # Global analysis derives from combining OS keys; per-OS uses them directly.
    if sc['fingerprints']:
        _t0 = time.time()
        _send(progress_queue, slot_idx, 'advance', 'Fingerprints', len(data))
        fp_names = wc['FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS']
        local_fp_by_os = {name: defaultdict(_dd_int) for name in fp_names}
        local_fp_cat = {name: [] for name in fp_names}
        chunk_size = max(1, len(data) // _PROGRESS_CHUNKS)
        done = 0
        for name, subset in fp_names.items():
            _os_dict = local_fp_by_os[name]
            # Temporary global dict for calculate_fingerprint_set (categories need it)
            _tmp_global = defaultdict(int)
            for chunk in _chunked(data, chunk_size):
                calculate_fingerprint_set(
                    _tmp_global, local_fp_cat[name],
                    chunk, subset=subset, name=f'Default Data {name}',
                )
                for _dv in chunk:
                    _os_dict[_dv.os][_dv.fingerprint(subset)] += 1
                done += len(chunk)
                _send(progress_queue, slot_idx, 'update', done)
            del _tmp_global
        result['fingerprints_by_os'] = {name: dict(d) for name, d in local_fp_by_os.items()}
        result['fingerprints_by_category'] = local_fp_cat
        phase_times['fingerprints'] = time.time() - _t0

    # ── Fingerprint + metric buckets ─────────────────────────────────────────
    if sc['fingerprint_buckets'] or sc['metric_buckets']:
        _t0 = time.time()
        _send(progress_queue, slot_idx, 'advance', 'Buckets', len(data))
        _N_BINS = 40
        _do_fb_by_os = sc['fingerprint_buckets'] and sc['per_os_analysis'] in (True, 'only')

        # Compact bin-array format: {fp_name: {hash: [bin0, bin1, ..., bin39]}}
        # bin_i = users whose random value fell in ((i)*0.025, (i+1)*0.025]
        # (bin 0 = (0, 0.025], bin 39 = (0.975, 1.0])
        # Use FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS (config-selected subset)
        # instead of ALL_FINGERPRINTERS to avoid computing buckets for unused fingerprinters
        _bucket_fps = wc['FINGERPRINTERS_FOR_ALLDATA_FINGERPRINTS'] or ALL_FINGERPRINTERS
        if sc['fingerprint_buckets']:
            local_fb = {name: {} for name in _bucket_fps}
            if _do_fb_by_os:
                # {fp_name: {os: {hash: [bins]}}}
                local_fb_os = {name: defaultdict(dict) for name in _bucket_fps}
        if sc['metric_buckets']:
            local_mb = {metric: {} for metric in wc['metrics_to_run_bucketing_for']}

        for dv in data:
            rand_val = random.random()
            bin_idx = min(int(rand_val / 0.025), _N_BINS - 1)
            if sc['fingerprint_buckets']:
                _os_val = dv.os if _do_fb_by_os else None
                for name in _bucket_fps:
                    fp = dv.fingerprint(_bucket_fps[name])
                    bins = local_fb[name].get(fp)
                    if bins is None:
                        bins = [0] * _N_BINS
                        local_fb[name][fp] = bins
                    bins[bin_idx] += 1
                    if _do_fb_by_os:
                        _os_dict = local_fb_os[name][_os_val]
                        bins2 = _os_dict.get(fp)
                        if bins2 is None:
                            bins2 = [0] * _N_BINS
                            _os_dict[fp] = bins2
                        bins2[bin_idx] += 1
            if sc['metric_buckets']:
                for metric in wc['metrics_to_run_bucketing_for']:
                    val = getattr(dv, metric, None)
                    bins = local_mb[metric].get(val)
                    if bins is None:
                        bins = [0] * _N_BINS
                        local_mb[metric][val] = bins
                    bins[bin_idx] += 1

        phase_times['buckets_compute'] = time.time() - _t0

        # Spill to disk per fingerprinter/metric
        _spill_t0 = time.time()
        _bucket_spill = os.path.join(wc['analysis_folder'], '_bucket_spill')
        _part_label = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")
        if sc['fingerprint_buckets']:
            for name, fp_dict in local_fb.items():
                _sd = os.path.join(_bucket_spill, 'fp', safe_filename(name))
                os.makedirs(_sd, exist_ok=True)
                with open(os.path.join(_sd, f"{_part_label}.pkl"), 'wb') as f:
                    pickle.dump(fp_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
            if _do_fb_by_os:
                for name in _bucket_fps:
                    for _os_val, _os_dict in local_fb_os[name].items():
                        _sd = os.path.join(_bucket_spill, 'fp',
                                           safe_filename(name) + '_os_' + safe_filename(_os_val))
                        os.makedirs(_sd, exist_ok=True)
                        with open(os.path.join(_sd, f"{_part_label}.pkl"), 'wb') as f:
                            pickle.dump(_os_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
                del local_fb_os
            del local_fb
        if sc['metric_buckets']:
            for metric, val_dict in local_mb.items():
                _sd = os.path.join(_bucket_spill, 'metric', safe_filename(metric))
                os.makedirs(_sd, exist_ok=True)
                with open(os.path.join(_sd, f"{_part_label}.pkl"), 'wb') as f:
                    pickle.dump(val_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
            del local_mb
        phase_times['buckets_spill'] = time.time() - _spill_t0

    # ── Missing fonts ─────────────────────────────────────────────────────────
    if sc['missing_fonts']:
        _t0 = time.time()
        _send(progress_queue, slot_idx, 'advance', 'Fonts', len(data))
        local_mf = {
            'strings_counter':                 defaultdict(_di),
            'individual_counter':              defaultdict(_di),
            'by_version':                      defaultdict(_ddi),
            'by_locale':                       defaultdict(_ddi),
            'android_by_machine':              defaultdict(_di),
            'android_by_machine_version':      defaultdict(_di),
            'by_os_locale':                    defaultdict(_di),
            'by_os_version':                   defaultdict(_di),
            'by_os_machine_model':             defaultdict(_di),
            'by_os_machine_model_version':     defaultdict(_di),
        }
        for dv in data:
            if hasattr(dv, 'missing_fonts') and dv.missing_fonts:
                sorted_fonts = set(sorted(dv.missing_fonts))
                mv_key = f"{dv.hw_machine_model}____{dv.os_version}"
                local_mf['by_os_locale'][dv.os][dv.intl_intl_locale] += 1
                local_mf['by_os_machine_model'][dv.os][dv.hw_machine_model] += 1
                local_mf['by_os_machine_model_version'][dv.os][mv_key] += 1
                if getattr(dv, 'os_distro', None) is not None:
                    local_mf['by_os_version'][dv.os][dv.os_distro] += 1
                else:
                    local_mf['by_os_version'][dv.os][dv.os_version] += 1
                if sc['missing_font_sets']:
                    local_mf['strings_counter'][dv.os][','.join(sorted_fonts)] += 1
                for font in sorted_fonts:
                    local_mf['individual_counter'][dv.os][font] += 1
                    if sc['missing_fonts_by_version']:
                        if dv.os == 'Android':
                            local_mf['android_by_machine'][dv.hw_machine_model][font] += 1
                            local_mf['android_by_machine_version'][mv_key][font] += 1
                        if getattr(dv, 'os_distro', None) is not None:
                            local_mf['by_version'][dv.os][dv.os_distro][font] += 1
                        else:
                            local_mf['by_version'][dv.os][dv.os_version][font] += 1
                    if sc['missing_fonts_by_locale']:
                        if dv.intl_intl_locale:
                            local_mf['by_locale'][dv.os][dv.intl_intl_locale][font] += 1
        result['missing_fonts'] = local_mf
        phase_times['fonts'] = time.time() - _t0

    # ── Experiments ───────────────────────────────────────────────────────────
    if sc['experiments'] or sc['calculate_metric_experiment_aggregated']:
        _t0 = time.time()
        n_fp = len(wc['FINGERPRINTERS_FOR_EXPERIMENTS'])
        total_exp_calls = (
            len(wc['EXPERIMENTS_TO_RUN']) +
            sum(len(s) for s in wc['EXPERIMENTS_TO_RUN_ADDITIVE'])
        ) * n_fp
        _send(progress_queue, slot_idx, 'advance', 'Experiments',
              total_exp_calls * len(data))
        local_fp_exp     = {}
        local_fp_exp_cat = {}
        progress_offset  = 0

        if sc['calculate_metric_experiment_aggregated']:
            local_exp_ma = {
                exp_key: {metric: defaultdict(int) for metric in metrics}
                for exp_key, metrics in wc['METRIC_EXPERIMENTS_BY_KEY'].items()
            }

        fp_exp_names = wc['FINGERPRINTERS_FOR_EXPERIMENTS']
        n_threads    = wc['max_worker_threads']

        # Spill directory for this partition's experiment fingerprints
        part_id = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")
        _spill_dir = os.path.join(config.ANALYSIS_FOLDER, '_exp_spill', part_id)
        _spill_name_map = {}
        if sc['experiments']:
            os.makedirs(_spill_dir, exist_ok=True)

        for exp_name, exp_filters in wc['EXPERIMENTS_TO_RUN'].items():
            ef = exp_filters if isinstance(exp_filters, list) else [exp_filters]
            do_metric_exp = (sc['calculate_metric_experiment_aggregated'] and
                             exp_name in wc['METRIC_EXPERIMENTS_BY_KEY'])
            if sc['experiments']:
                local_fp_exp[exp_name]     = {n: defaultdict(_dd_int) for n in fp_exp_names}
                local_fp_exp_cat[exp_name] = {n: [] for n in fp_exp_names}

            chunk_size     = max(1, (len(data) + n_threads - 1) // n_threads)
            slices         = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
            thread_results = [None] * len(slices)

            def _exp_thread(idx, slice_data,
                            _ef=ef, _do_metric_exp=do_metric_exp,
                            _metric_cfg=wc['METRIC_EXPERIMENTS_BY_KEY'].get(exp_name, {})):
                # OS-bucketed: {fp_name: {os: {hash: count}}}
                tfp = {n: defaultdict(_dd_int) for n in fp_exp_names}
                tma = {m: defaultdict(int) for m in _metric_cfg} if _do_metric_exp else None
                for d in slice_data:
                    for f in _ef:
                        d.add_filter(f)
                    if sc['experiments']:
                        _os = d.os
                        for name, subset in fp_exp_names.items():
                            tfp[name][_os][d.fingerprint(subset)] += 1
                    if _do_metric_exp:
                        calculate_aggregated_metrics_impl(d, tma, _metric_cfg)
                    for f in reversed(_ef):
                        d.pop_filter()
                thread_results[idx] = (tfp, tma)

            threads = [threading.Thread(target=_exp_thread, args=(i, s))
                       for i, s in enumerate(slices)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            if sc['experiments']:
                for tfp, _ in thread_results:
                    for name in fp_exp_names:
                        for _os, _os_hashes in tfp[name].items():
                            _target = local_fp_exp[exp_name][name][_os]
                            for h, c in _os_hashes.items():
                                _target[h] += c
                # Spill immediately and free memory
                _safe = safe_filename(exp_name)
                _spill_name_map[exp_name] = _safe
                with open(os.path.join(_spill_dir, f"{_safe}.pkl"), 'wb') as _sf:
                    pickle.dump({n: {os_k: dict(os_v) for os_k, os_v in d.items()}
                                 for n, d in local_fp_exp[exp_name].items()},
                                _sf, protocol=pickle.HIGHEST_PROTOCOL)
                del local_fp_exp[exp_name]

            if do_metric_exp:
                for _, tma in thread_results:
                    for metric, counts in tma.items():
                        for val, c in counts.items():
                            local_exp_ma[exp_name][metric][val] += c

            progress_offset += len(data) * n_fp
            _send(progress_queue, slot_idx, 'update', progress_offset)

        if sc['experiments']:
            for additive_set in wc['EXPERIMENTS_TO_RUN_ADDITIVE']:
                exp_items = list(additive_set.items())
                # Process one additive experiment at a time: apply its filter(s),
                # fingerprint, spill, then leave filters applied for the next one.
                _additive_total_pops = 0
                for exp_name, exp_filters in exp_items:
                    ef = exp_filters if isinstance(exp_filters, list) else [exp_filters]
                    _additive_total_pops += len(ef)
                    local_fp_exp[exp_name] = {n: defaultdict(_dd_int) for n in fp_exp_names}
                    local_fp_exp_cat[exp_name] = {n: [] for n in fp_exp_names}

                    chunk_size = max(1, (len(data) + n_threads - 1) // n_threads)
                    slices = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
                    thread_results = [None] * len(slices)

                    def _add_one_thread(idx, slice_data, _ef=ef):
                        tfp = {n: defaultdict(_dd_int) for n in fp_exp_names}
                        for d in slice_data:
                            for f in _ef:
                                d.add_filter(f)
                            _os = d.os
                            for name, subset in fp_exp_names.items():
                                tfp[name][_os][d.fingerprint(subset)] += 1
                            # Do NOT pop filters — they accumulate for the next experiment
                        thread_results[idx] = tfp

                    threads = [threading.Thread(target=_add_one_thread, args=(i, s))
                               for i, s in enumerate(slices)]
                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join()

                    for tfp in thread_results:
                        for name in fp_exp_names:
                            for _os, _os_hashes in tfp[name].items():
                                _target = local_fp_exp[exp_name][name][_os]
                                for h, c in _os_hashes.items():
                                    _target[h] += c

                    # Spill immediately and free
                    _safe = safe_filename(exp_name)
                    _spill_name_map[exp_name] = _safe
                    with open(os.path.join(_spill_dir, f"{_safe}.pkl"), 'wb') as _sf:
                        pickle.dump({n: {os_k: dict(os_v) for os_k, os_v in d.items()}
                                     for n, d in local_fp_exp[exp_name].items()},
                                    _sf, protocol=pickle.HIGHEST_PROTOCOL)
                    del local_fp_exp[exp_name]

                    progress_offset += len(data) * n_fp
                    _send(progress_queue, slot_idx, 'update', progress_offset)

                # Pop all accumulated additive filters
                for d in data:
                    for _ in range(_additive_total_pops):
                        d.pop_filter()

            del local_fp_exp
            result['exp_spill_dir'] = _spill_dir
            result['exp_spill_names'] = _spill_name_map
            result['fingerprints_exp_by_category'] = local_fp_exp_cat

        if sc['calculate_metric_experiment_aggregated']:
            result['metric_aggregation_experiments'] = local_exp_ma
        phase_times['experiments'] = time.time() - _t0

    # ── Browser modes ─────────────────────────────────────────────────────────
    if sc['browser_modes']:
        _t0 = time.time()
        _send(progress_queue, slot_idx, 'advance', 'Modes', len(data))
        fp_mode_names = wc['FINGERPRINTERS_FOR_MODES']
        # OS-bucketed: {mode: {fp_name: {os: {hash: count}}}}
        local_modes     = {mn: {fpn: defaultdict(_dd_int) for fpn in fp_mode_names}
                           for mn in ALL_MODES}
        local_modes_cat = {mn: {fpn: [] for fpn in fp_mode_names}
                           for mn in ALL_MODES}
        for modename, filters in ALL_MODES.items():
            for f in filters:
                for d in data:
                    d.add_filter(f)
            # Temporary global dict for categories
            for name, subset in fp_mode_names.items():
                _tmp = defaultdict(int)
                calculate_fingerprint_set(
                    _tmp, local_modes_cat[modename][name],
                    data, subset=subset, filters=[],
                    name=f'{modename} {name}',
                )
                del _tmp
                _os_dict = local_modes[modename][name]
                for d in data:
                    _os_dict[d.os][d.fingerprint(subset)] += 1
            for f in reversed(filters):
                for d in data:
                    d.pop_filter()
        result['fingerprints_modes']             = local_modes
        result['fingerprints_modes_by_category'] = local_modes_cat
        phase_times['modes'] = time.time() - _t0

    # ── Custom functions ────────────────────────────────────────────────────────
    _custom_fns = wc.get('CUSTOM_FUNCTIONS')
    if _custom_fns:
        _t0 = time.time()
        _send(progress_queue, slot_idx, 'advance', 'Custom', len(data))
        for cf in _custom_fns:
            acc = cf['init']()
            for dv in data:
                cf['map'](dv, acc)
            result[f"custom_{cf['name']}"] = acc
        phase_times['custom'] = time.time() - _t0

    # ── Single metric removal ─────────────────────────────────────────────────
    if sc['perform_single_metric_removal_analysis']:
        _t0 = time.time()
        SMR_FP_NAMES = wc['SMR_FP_NAMES']
        total_smr_ops = sum(len(wc['smr_metric_lists'][fp]) for fp in SMR_FP_NAMES)
        _n_data = len(data)
        _send(progress_queue, slot_idx, 'advance', 'SMR', total_smr_ops * _n_data)
        _smr_global_offset = 0

        # Check if data is needed after SMR (LMR also serializes from data)
        _data_needed_after_smr = sc.get('perform_logical_metric_removal_analysis', False)
        part_id_smr = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")
        _smr_spill_base = os.path.join(config.ANALYSIS_FOLDER, '_smr_spill')

        _build_ismr_cache = wc.get('build_ismr_cache', set())  # set of fp_names to cache
        for fp_name in SMR_FP_NAMES:
            smr_metric_list = wc['smr_metric_lists'][fp_name]
            smr_attrs = sorted(a for a in vars(data[0]).keys() if a in wc['smr_subsets'][fp_name])
            # Always include 'os' for per-OS analysis support
            _cache_attrs = sorted(set(smr_attrs) | ({'os'} if hasattr(data[0], 'os') else set()))
            dv_serialized = [
                {attr: str(getattr(dv, attr)) for attr in _cache_attrs} for dv in data
            ]

            # Free DataValues if this is the last FP and no later phase needs them
            if not _data_needed_after_smr and fp_name == SMR_FP_NAMES[-1]:
                num_users = len(data)
                del data
                data = []
                _send_rss(progress_queue, slot_idx)

            # Spill global + per-OS caches
            if fp_name in _build_ismr_cache:
                _part_id = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")

                # Global cache
                _cache_dir = os.path.join(config.ANALYSIS_FOLDER, '_ismr_cache', safe_filename(fp_name))
                os.makedirs(_cache_dir, exist_ok=True)
                with open(os.path.join(_cache_dir, f"{_part_id}.pkl"), 'wb') as _f:
                    pickle.dump({'attrs': _cache_attrs, 'rows': dv_serialized},
                                _f, protocol=pickle.HIGHEST_PROTOCOL)

                # Per-OS caches
                _by_os = defaultdict(list)
                for _row in dv_serialized:
                    _by_os[_row.get('os', 'Unknown')].append(_row)
                for _os_val, _os_rows in _by_os.items():
                    _os_cache_dir = os.path.join(
                        config.ANALYSIS_FOLDER, '_ismr_cache',
                        f"{safe_filename(fp_name)}_os_{safe_filename(_os_val)}")
                    os.makedirs(_os_cache_dir, exist_ok=True)
                    with open(os.path.join(_os_cache_dir, f"{_part_id}.pkl"), 'wb') as _f:
                        pickle.dump({'attrs': _cache_attrs, 'rows': _os_rows},
                                    _f, protocol=pickle.HIGHEST_PROTOCOL)
                del _by_os

            # Process SMR for this fingerprinter into a local dict, then spill immediately
            _fp_smr = defaultdict(_ddi)

            # Pre-initialize all metric keys so threads never modify the outer dict structure.
            for metric in smr_metric_list:
                _fp_smr[metric if isinstance(metric, str) else str(metric)]

            # Work queue: one item per metric. Threads pull and process independently.
            _smr_q = queue.Queue()
            for smr_i, metric in enumerate(smr_metric_list):
                _smr_q.put((smr_i, metric))

            def _smr_worker(
                _q=_smr_q, _local=_fp_smr,
                _attrs=smr_attrs, _ser=dv_serialized,
                _offset=_smr_global_offset,
            ):
                while True:
                    try:
                        smr_i, metric = _q.get_nowait()
                    except queue.Empty:
                        return
                    key           = metric if isinstance(metric, str) else str(metric)
                    exclude       = {metric} if isinstance(metric, str) else set(metric)
                    attrs_without = [a for a in _attrs if a not in exclude]
                    _os_dict = _local[key]
                    for row in _ser:
                        combined = '|'.join(row[a] for a in attrs_without) + '|'
                        _os_dict[row.get('os', 'Unknown')][
                            hashlib.sha1(combined.encode('utf-8'), usedforsecurity=False).digest()
                        ] += 1
                    _send(progress_queue, slot_idx, 'update', (_offset + smr_i + 1) * _n_data)

            n_threads = wc['max_worker_threads']
            threads = [threading.Thread(target=_smr_worker) for _ in range(n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            _smr_global_offset += len(smr_metric_list)

            # Spill this fingerprinter's SMR data to disk immediately, then free
            _fp_safe = safe_filename(fp_name)
            _fp_dir = os.path.join(_smr_spill_base, _fp_safe)
            _key_map = {}
            for _mk, _os_hash_dict in _fp_smr.items():
                _mk_safe = safe_filename(str(_mk))
                _key_map[_mk_safe] = _mk
                _metric_dir = os.path.join(_fp_dir, _mk_safe)
                os.makedirs(_metric_dir, exist_ok=True)
                _spill_path = os.path.join(_metric_dir, f"{part_id_smr}.pkl")
                with open(_spill_path, 'wb') as _sf:
                    pickle.dump({os_k: dict(os_v) for os_k, os_v in _os_hash_dict.items()},
                                _sf, protocol=pickle.HIGHEST_PROTOCOL)
            _map_path = os.path.join(_fp_dir, '_key_map.pkl')
            if not os.path.exists(_map_path):
                with open(_map_path, 'wb') as _sf:
                    pickle.dump(_key_map, _sf, protocol=pickle.HIGHEST_PROTOCOL)
            del _fp_smr, dv_serialized
        phase_times['smr'] = time.time() - _t0

    # ── Logical metric removal ────────────────────────────────────────────────
    if sc['perform_logical_metric_removal_analysis'] and wc['LMR_FP_NAMES']:
        _t0 = time.time()
        total_lmr_units = sum(
            len(wc['lmr_unit_lists'][fp]) for fp in wc['LMR_FP_NAMES']
        )
        _send(progress_queue, slot_idx, 'advance', 'LMR',
              total_lmr_units * len(data))
        # OS-bucketed: {fp: {unit: {os: {hash: count}}}}
        local_lmr = {fp_name: defaultdict(_ddi) for fp_name in wc['LMR_FP_NAMES']}
        _lmr_done = 0
        n_threads = wc['max_worker_threads']
        for fp_name in wc['LMR_FP_NAMES']:
            fp_set    = ALL_FINGERPRINTERS[fp_name]
            fp_attrs  = sorted(a for a in vars(data[0]).keys() if a in fp_set)
            # Include os for per-OS bucketing
            _lmr_ser_attrs = sorted(set(fp_attrs) | ({'os'} if hasattr(data[0], 'os') else set()))
            fp_serialized = [
                {attr: str(getattr(dv, attr)) for attr in _lmr_ser_attrs} for dv in data
            ]

            _lmr_q = queue.Queue()
            _lmr_offset = _lmr_done
            for lmr_i, (unit_name, exclude_set) in enumerate(wc['lmr_unit_lists'][fp_name]):
                _lmr_q.put((lmr_i, unit_name, exclude_set))

            def _lmr_worker(
                _q=_lmr_q, _local=local_lmr[fp_name],
                _attrs=fp_attrs, _ser=fp_serialized,
                _offset=_lmr_offset,
            ):
                while True:
                    try:
                        lmr_i, unit_name, exclude_set = _q.get_nowait()
                    except queue.Empty:
                        return
                    attrs_without = [a for a in _attrs if a not in exclude_set]
                    _os_dict = _local[unit_name]
                    for row in _ser:
                        combined = '|'.join(row[a] for a in attrs_without) + '|'
                        _os_dict[row.get('os', 'Unknown')][
                            hashlib.sha1(combined.encode('utf-8'), usedforsecurity=False).digest()
                        ] += 1
                    _send(progress_queue, slot_idx, 'update', (_offset + lmr_i + 1) * len(data))

            threads = [threading.Thread(target=_lmr_worker) for _ in range(n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            _lmr_done += len(wc['lmr_unit_lists'][fp_name])
        # Spill LMR fingerprints to disk — one file per FP per unit.
        part_id_lmr = safe_filename(f"{partition[0]}_{partition[1] or 'all'}")
        _lmr_spill_base = os.path.join(config.ANALYSIS_FOLDER, '_lmr_spill')
        for _fp_name, _unit_dict in local_lmr.items():
            _fp_safe = safe_filename(_fp_name)
            _fp_dir = os.path.join(_lmr_spill_base, _fp_safe)
            _key_map = {}
            for _uk, _os_hash_dict in _unit_dict.items():
                _uk_safe = safe_filename(str(_uk))
                _key_map[_uk_safe] = _uk
                _unit_dir = os.path.join(_fp_dir, _uk_safe)
                os.makedirs(_unit_dir, exist_ok=True)
                _spill_path = os.path.join(_unit_dir, f"{part_id_lmr}.pkl")
                with open(_spill_path, 'wb') as _sf:
                    pickle.dump({os_k: dict(os_v) for os_k, os_v in _os_hash_dict.items()},
                                _sf, protocol=pickle.HIGHEST_PROTOCOL)
            _map_path = os.path.join(_fp_dir, '_key_map.pkl')
            if not os.path.exists(_map_path):
                with open(_map_path, 'wb') as _sf:
                    pickle.dump(_key_map, _sf, protocol=pickle.HIGHEST_PROTOCOL)
        del local_lmr
        phase_times['lmr'] = time.time() - _t0

    # Write combined hash lookup for this partition to a temp file.
    # Main process merges all partitions at the end.
    if config.COMBINED_HASH_LOOKUP:
        import json as _json_mod
        _lookup_dir = os.path.join(config.OUTPUT_FOLDER, '_hash_lookup_parts')
        os.makedirs(_lookup_dir, exist_ok=True)
        _part_id = f"{partition[0]}_{partition[1]}" if partition else "unknown"
        _lookup_path = os.path.join(_lookup_dir, f"{_part_id}.json")
        with open(_lookup_path, 'w') as _lf:
            _json_mod.dump(config.COMBINED_HASH_LOOKUP, _lf)

    result['phase_times'] = phase_times
    config.log(
        f"[{partition[0]}/{partition[1]}]   phase times (s): "
        + "  ".join(f"{k}={v:.2f}" for k, v in phase_times.items())
    )
    result['data_count'] = len(data) if data else num_users
    # DataValues are intentionally NOT included in the result.  Returning them
    # across the process boundary would re-pickle the entire array, negating the
    # malloc-isolation benefit.  quasi-sequential mode (persist_data=True) is
    # blocked before the pool is created (see analyze.py).
    del data

    _send(progress_queue, slot_idx, 'finish')
    return result


# =============================================================================
# ISMR iteration worker
# =============================================================================
# ISMR/ISMRP iteration workers with partition pinning
# =============================================================================

# Per-process state: latched on first call, reused across all iterations.
_ismr_worker_id = None           # worker index (0..N-1), set on first task
_ismr_partitions = []            # list of (part_id, attrs, rows) for pinned partitions


def _attr_hash(attr_name, value):
    """Deterministic 64-bit hash for one attribute name+value pair.
    Used as a building block for XOR-based fingerprinting."""
    return int.from_bytes(
        hashlib.sha1(f"{attr_name}|{value}".encode('utf-8'), usedforsecurity=False).digest()[:8],
        'little'
    )


def _ismr_ensure_loaded(worker_id, all_cache_paths, keep_metrics=None):
    """On first call, latch worker_id and load assigned partition slice into memory.
    On subsequent calls, return immediately (data already in memory).
    keep_metrics: if set, only retain these attributes (+ 'os') per row to save memory."""
    global _ismr_worker_id, _ismr_partitions
    if _ismr_worker_id is not None:
        return
    _ismr_worker_id = worker_id
    n_workers = _W.get('_ismr_num_workers', 16)
    # Round-robin assignment so each worker gets a mix of desktop/mobile partitions
    my_paths = all_cache_paths[worker_id::n_workers]
    _ismr_partitions = []
    for path in my_paths:
        part_id = os.path.splitext(os.path.basename(path))[0]
        with open(path, 'rb') as f:
            cached = pickle.load(f)
        if keep_metrics is not None:
            keep = set(keep_metrics) | {'os'}
            trimmed_attrs = [a for a in cached['attrs'] if a in keep]
            trimmed_rows = [{a: row[a] for a in trimmed_attrs if a in row}
                            for row in cached['rows']]
            _ismr_partitions.append((part_id, trimmed_attrs, trimmed_rows))
        else:
            _ismr_partitions.append((part_id, cached['attrs'], cached['rows']))


def ismr_iteration_worker(worker_id, all_cache_paths, excluded_metrics,
                          metric_list, spill_dir, slot_idx=None):
    """Worker for one ISMR iteration with partition pinning and XOR hashing.

    Uses XOR-based fingerprinting: precomputes a per-attribute hash for each
    user, XORs them into a total, then for each test metric XORs out that
    attribute's hash (O(1) per metric per user instead of O(attrs)).

    First call: latches worker_id, loads assigned partition slice into memory.
    Subsequent calls: pure compute, no disk reads.
    Spills per-metric fingerprint dicts to spill_dir/{metric_safe}/{part_id}.pkl.
    Returns list of part_ids processed.
    """
    _ismr_ensure_loaded(worker_id, all_cache_paths)
    progress_queue = _W.get('progress_queue')
    n_threads = _W['max_worker_threads']
    base_exclude = set(excluded_metrics)
    part_ids = []
    n_partitions = len(_ismr_partitions)

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'start',
              f"W{worker_id} ({n_partitions}p)", 1)
        _send(progress_queue, slot_idx, 'advance', 'Hashing', n_partitions)

    for _pi, (part_id, attrs, rows) in enumerate(_ismr_partitions):
        part_ids.append(part_id)
        base_attrs = [a for a in attrs if a not in base_exclude]
        metric_set = set(metric_list)

        # Precompute per-attribute hashes and total XOR for each user
        n_users = len(rows)
        user_totals = [0] * n_users
        per_attr_hashes = {}
        _hash_lock = threading.Lock()

        def _hash_attr(_a, _rows=rows, _n=n_users):
            col = [0] * _n
            for u in range(_n):
                col[u] = _attr_hash(_a, _rows[u][_a])
            return (_a, col)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as _tp:
            for _a, col in _tp.map(_hash_attr, base_attrs):
                for u in range(n_users):
                    user_totals[u] ^= col[u]
                if _a in metric_set:
                    per_attr_hashes[_a] = col

        # For each test metric, XOR out its hash → fingerprint, count occurrences
        # Each metric is independent — parallelize across threads
        def _count_metric(_metric):
            key = _metric if isinstance(_metric, str) else str(_metric)
            counts = defaultdict(int)
            col = per_attr_hashes[_metric]
            for u in range(n_users):
                fp = user_totals[u] ^ col[u]
                counts[fp] += 1
            return (key, counts)

        result = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as _tp:
            for key, counts in _tp.map(_count_metric, metric_list):
                result[key] = counts

        del user_totals, per_attr_hashes

        # Spill per-metric fingerprint dicts to disk
        def _spill_one(_item, _spill_dir=spill_dir, _pid=part_id):
            key, hashes = _item
            _mk_safe = safe_filename(str(key))
            _mk_dir = os.path.join(_spill_dir, _mk_safe)
            os.makedirs(_mk_dir, exist_ok=True)
            with open(os.path.join(_mk_dir, f"{_pid}.pkl"), 'wb') as f:
                pickle.dump(dict(hashes), f, protocol=pickle.HIGHEST_PROTOCOL)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as _tp:
            list(_tp.map(_spill_one, result.items()))
        del result
        if slot_idx is not None:
            _send(progress_queue, slot_idx, 'update', _pi + 1)

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'finish')
    return part_ids


def ismrp_iteration_worker(worker_id, all_cache_paths, locked_replacements,
                           metric_list, common_values, mode_map, spill_dir,
                           slot_idx=None):
    """Worker for one ISMRP iteration with partition pinning and XOR hashing.

    Uses XOR-based fingerprinting with value replacement:
    1. Precompute per-attr hashes with locked replacements applied
    2. Compute total XOR per user
    3. For each test metric: if value is NOT in common_values (i.e. rare),
       XOR out old hash and XOR in replacement hash

    common_values: {metric: set of non-rare values} — inverted from the old
    rare_values to minimize pickle size (common sets are tiny).

    Spills per-metric fingerprint dicts to spill_dir/{metric_safe}/{part_id}.pkl.
    Returns (part_ids, {metric_key: num_rows_replaced}).
    """
    _ismr_ensure_loaded(worker_id, all_cache_paths)
    progress_queue = _W.get('progress_queue')
    n_threads = _W['max_worker_threads']
    all_part_ids = []
    total_replaced = {(metric if isinstance(metric, str) else str(metric)): 0
                      for metric in metric_list}
    n_partitions = len(_ismr_partitions)

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'start',
              f"W{worker_id} ({n_partitions}p)", 1)
        _send(progress_queue, slot_idx, 'advance', 'Replacing', n_partitions)

    for _pi, (part_id, attrs, rows) in enumerate(_ismr_partitions):
        all_part_ids.append(part_id)
        n_users = len(rows)
        metric_set = set(metric_list)

        # Precompute per-attribute hashes with locked replacements applied
        user_totals = [0] * n_users
        per_attr_hashes = {}
        per_attr_vals = {}

        def _hash_attr_rp(_a, _rows=rows, _n=n_users,
                          _locked=locked_replacements, _ms=metric_set):
            col_h = [0] * _n
            is_test = _a in _ms
            col_v = [None] * _n if is_test else None
            for u in range(_n):
                val = _rows[u][_a]
                if _a in _locked:
                    _common, _mode = _locked[_a]
                    if val not in _common:
                        val = _mode
                col_h[u] = _attr_hash(_a, val)
                if is_test:
                    col_v[u] = val
            return (_a, col_h, col_v, is_test)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as _tp:
            for _a, col_h, col_v, is_test in _tp.map(_hash_attr_rp, attrs):
                for u in range(n_users):
                    user_totals[u] ^= col_h[u]
                if is_test:
                    per_attr_hashes[_a] = col_h
                    per_attr_vals[_a] = col_v

        # For each test metric: XOR out old hash, XOR in replacement hash if rare
        def _count_metric_rp(_metric):
            key = _metric if isinstance(_metric, str) else str(_metric)
            test_common = common_values.get(key, set())
            test_mode = mode_map.get(key)
            counts = defaultdict(int)
            local_replaced = 0
            col_h = per_attr_hashes[_metric]
            col_v = per_attr_vals[_metric]
            mode_hash = _attr_hash(_metric, test_mode) if test_mode is not None else None
            for u in range(n_users):
                old_h = col_h[u]
                val = col_v[u]
                if val not in test_common and mode_hash is not None:
                    fp = user_totals[u] ^ old_h ^ mode_hash
                    local_replaced += 1
                else:
                    fp = user_totals[u]
                counts[fp] += 1
            return (key, counts, local_replaced)

        result = {}
        replaced_result = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as _tp:
            for key, counts, local_replaced in _tp.map(_count_metric_rp, metric_list):
                result[key] = counts
                replaced_result[key] = local_replaced

        del user_totals, per_attr_hashes, per_attr_vals

        # Spill and accumulate replaced counts
        def _spill_one_rp(_item, _spill_dir=spill_dir, _pid=part_id):
            key, hashes = _item
            _mk_safe = safe_filename(str(key))
            _mk_dir = os.path.join(_spill_dir, _mk_safe)
            os.makedirs(_mk_dir, exist_ok=True)
            with open(os.path.join(_mk_dir, f"{_pid}.pkl"), 'wb') as f:
                pickle.dump(dict(hashes), f, protocol=pickle.HIGHEST_PROTOCOL)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as _tp:
            list(_tp.map(_spill_one_rp, result.items()))
        for key in result:
            total_replaced[key] += replaced_result[key]
        del result, replaced_result
        if slot_idx is not None:
            _send(progress_queue, slot_idx, 'update', _pi + 1)

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'finish')
    return (all_part_ids, total_replaced)


# =============================================================================
# Minimum Identifying Set Per User worker
# =============================================================================

def min_set_combo_worker(worker_id, all_cache_paths, combo_list, spill_dir, slot_idx=None):
    """Worker for min-set combo analysis with partition pinning and pre-merge.

    Accumulates {fingerprint: count} across ALL assigned partitions before
    spilling — one file per combo per worker, not per partition. This reduces
    spill files from (partitions × combos) to (workers × combos).

    Also tracks {fingerprint: (part_id, row_idx)} for worker-unique entries
    (count==1 across this worker's partitions). Entries that become count>1
    as more partitions are processed are removed.

    combo_list: list of tuples of attribute names
    spill_dir: directory for spill files
    slot_idx: progress display slot index (optional)

    Returns list of part_ids processed.
    """
    import time as _time
    _t_load_start = _time.monotonic()
    # Only keep metrics needed by the combo analysis to save memory
    _keep = _W.get('_combo_keep_metrics')
    _ismr_ensure_loaded(worker_id, all_cache_paths, keep_metrics=_keep)
    _t_load = _time.monotonic() - _t_load_start

    progress_queue = _W.get('progress_queue')
    n_threads = _W['max_worker_threads']
    n_partitions = len(_ismr_partitions)
    n_combos = len(combo_list)
    total_work = n_partitions * n_combos
    part_ids = []

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'start',
              f"W{worker_id} ({n_partitions}p×{n_combos}c)", 1)
        _send(progress_queue, slot_idx, 'advance', 'Combos', total_work)

    # Merged dicts across all partitions — one per combo
    merged_counts = {combo: defaultdict(int) for combo in combo_list}
    merged_uidx = {combo: {} for combo in combo_list}  # {fp: (part_id, row_idx)}

    _t_hash_total = 0.0
    _t_combo_total = 0.0
    _done = 0
    for _pi, (part_id, attrs, rows) in enumerate(_ismr_partitions):
        part_ids.append(part_id)
        n_users = len(rows)
        attr_set = set(attrs)

        # Precompute per-attribute hashes once for this partition (threaded)
        _t_hash_start = _time.monotonic()
        per_attr = {}
        _hash_q = queue.Queue()
        for a in attrs:
            _hash_q.put(a)
        _hash_results = {}
        _hash_lock = threading.Lock()

        def _hash_worker(_q=_hash_q, _rows=rows, _n=n_users, _res=_hash_results, _lk=_hash_lock):
            while True:
                try:
                    a = _q.get_nowait()
                except queue.Empty:
                    return
                col = [0] * _n
                for u, row in enumerate(_rows):
                    col[u] = _attr_hash(a, row[a])
                with _lk:
                    _res[a] = col

        _hash_threads = [threading.Thread(target=_hash_worker) for _ in range(n_threads)]
        for t in _hash_threads:
            t.start()
        for t in _hash_threads:
            t.join()
        per_attr = _hash_results
        _t_hash_total += _time.monotonic() - _t_hash_start

        valid_combos = [c for c in combo_list if all(a in attr_set for a in c)]

        # Thread work: accumulate into merged dicts
        _t_combo_start = _time.monotonic()
        _q = queue.Queue()
        for i, combo in enumerate(valid_combos):
            _q.put((i, combo))

        def _worker(_q=_q, _per_attr=per_attr, _n_users=n_users,
                    _merged_counts=merged_counts, _merged_uidx=merged_uidx,
                    _part_id=part_id):
            while True:
                try:
                    _, combo = _q.get_nowait()
                except queue.Empty:
                    return
                m_counts = _merged_counts[combo]
                m_uidx = _merged_uidx[combo]
                for u in range(_n_users):
                    fp = 0
                    for a in combo:
                        fp ^= _per_attr[a][u]
                    m_counts[fp] += 1
                    c = m_counts[fp]
                    if c == 1:
                        m_uidx[fp] = (_part_id, u)
                    elif c == 2 and fp in m_uidx:
                        del m_uidx[fp]

        threads = [threading.Thread(target=_worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        _t_combo_total += _time.monotonic() - _t_combo_start

        del per_attr

        _done += len(valid_combos)
        if slot_idx is not None:
            _send(progress_queue, slot_idx, 'update', _done)

    # Spill one file per combo (pre-merged across all partitions)
    _t_spill_start = _time.monotonic()
    _wid = f"w{worker_id}"
    for combo in combo_list:
        combo_name = '+'.join(combo)
        _mk_safe = safe_filename(combo_name)
        _mk_dir = os.path.join(spill_dir, _mk_safe)
        os.makedirs(_mk_dir, exist_ok=True)
        with open(os.path.join(_mk_dir, f"{_wid}_counts.pkl"), 'wb') as f:
            pickle.dump(dict(merged_counts[combo]), f, protocol=pickle.HIGHEST_PROTOCOL)
        if merged_uidx[combo]:
            with open(os.path.join(_mk_dir, f"{_wid}_uidx.pkl"), 'wb') as f:
                pickle.dump(merged_uidx[combo], f, protocol=pickle.HIGHEST_PROTOCOL)
    _t_spill = _time.monotonic() - _t_spill_start

    del merged_counts, merged_uidx

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'finish')
    return {
        'part_ids': part_ids,
        'worker_id': worker_id,
        't_load': _t_load,
        't_hash': _t_hash_total,
        't_combo': _t_combo_total,
        't_spill': _t_spill,
    }


# =============================================================================
# MinMetrics prefix worker
# =============================================================================

def minmetrics_prefix_worker(worker_id, all_cache_paths, metric_order, spill_dir, slot_idx=None):
    """Worker for MinMetrics analysis with incremental XOR fingerprinting.

    For each K from 1..len(metric_order), the fingerprint is the XOR of
    per-attribute hashes for the first K metrics. Uses the incremental trick:
    fp_K = fp_{K-1} XOR attr_hash(metric_K). Total XOR work per user is O(N),
    not O(N^2).

    Memory strategy: spill per-partition per-K as compact (values, counts)
    numpy arrays immediately. Worker memory peaks at one partition's
    per_attr matrix (max_k × n_users × 8 bytes) — not 52 growing dicts.
    Main process merges all partition spills per K with np.unique + bincount.
    """
    import time as _time
    import numpy as np

    progress_queue = _W.get('progress_queue')
    n_threads = _W['max_worker_threads']
    n_workers_total = _W.get('_ismr_num_workers', 16)
    max_k = len(metric_order)
    my_partition_count = len(all_cache_paths[worker_id::n_workers_total])

    # Announce the worker slot BEFORE loading partitions so the user sees
    # "Loading" progress during cache read. total_phases counts Loading
    # + one phase per partition.
    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'start', f"W{worker_id}", my_partition_count + 1)
        _send(progress_queue, slot_idx, 'advance', 'Loading', 0)

    _t_load_start = _time.monotonic()
    _keep = _W.get('_minmetrics_keep_metrics')
    _ismr_ensure_loaded(worker_id, all_cache_paths, keep_metrics=_keep)
    _t_load = _time.monotonic() - _t_load_start

    n_partitions = len(_ismr_partitions)
    part_ids = []

    _wid = f"w{worker_id}"
    # Pre-create per-K spill directories (cheap, done once)
    for k in range(1, max_k + 1):
        os.makedirs(os.path.join(spill_dir, f"k{k:03d}"), exist_ok=True)

    _t_hash_total = 0.0
    _t_xor_total = 0.0
    _t_spill_total = 0.0
    for _pi, (part_id, attrs, rows) in enumerate(_ismr_partitions):
        part_ids.append(part_id)
        n_users = len(rows)
        attr_set = set(attrs)

        if slot_idx is not None:
            _send(progress_queue, slot_idx, 'advance', 'Hashing', max_k)

        _missing = [m for m in metric_order if m not in attr_set]
        if _missing:
            raise RuntimeError(
                f"MinMetrics w{worker_id} part {part_id}: missing metrics "
                f"{_missing[:5]}{'...' if len(_missing) > 5 else ''}")

        # Pre-hash each metric column into a uint64 numpy array (threaded)
        _t_hash_start = _time.monotonic()
        per_attr = {}
        _hash_q = queue.Queue()
        for a in metric_order:
            _hash_q.put(a)
        _hash_lock = threading.Lock()

        def _hash_worker(_q=_hash_q, _rows=rows, _n=n_users, _res=per_attr, _lk=_hash_lock):
            while True:
                try:
                    a = _q.get_nowait()
                except queue.Empty:
                    return
                col = np.empty(_n, dtype=np.uint64)
                for u, row in enumerate(_rows):
                    col[u] = _attr_hash(a, row[a])
                with _lk:
                    _res[a] = col

        _hash_threads = [threading.Thread(target=_hash_worker) for _ in range(n_threads)]
        for t in _hash_threads:
            t.start()
        for t in _hash_threads:
            t.join()
        _t_hash_total += _time.monotonic() - _t_hash_start

        # Incremental XOR (vectorized) + per-K spill of (values, counts)
        fp = np.zeros(n_users, dtype=np.uint64)
        for k, a in enumerate(metric_order, start=1):
            _t_xor_start = _time.monotonic()
            fp ^= per_attr[a]                                   # vectorized XOR
            values, counts = np.unique(fp, return_counts=True)  # per-partition tally
            _t_xor_total += _time.monotonic() - _t_xor_start

            _t_sp = _time.monotonic()
            _spill_path = os.path.join(spill_dir, f"k{k:03d}",
                                       f"{_wid}_p{_pi:04d}.npz")
            np.savez(_spill_path, values=values,
                     counts=counts.astype(np.uint32))
            _t_spill_total += _time.monotonic() - _t_sp

            if slot_idx is not None:
                _send(progress_queue, slot_idx, 'rename', f'K={k}')
                _send(progress_queue, slot_idx, 'update', k)

        del per_attr, fp
        # Signal partition completion to drive the overall progress bar.
        _send(progress_queue, 0, 'part_done')

    if slot_idx is not None:
        _send(progress_queue, slot_idx, 'finish')
    return {
        'part_ids': part_ids,
        'worker_id': worker_id,
        't_load': _t_load,
        't_hash': _t_hash_total,
        't_xor': _t_xor_total,
        't_spill': _t_spill_total,
    }

