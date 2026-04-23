import csv
import hashlib
import os
import pickle
import time
from collections import defaultdict

from calculations import get_fingerprint_analysis
from cohort import cohort_fitness, cohort_fitness_from_histogram, cohort_fitness_from_histogram_excluding_singletons, cohort_p50_from_histogram
import config
from script_config import script_config

METRICS_TO_COMBINE = {
    # ── Canvas ────────────────────────────────────────────────────────────────
    'canvas-akamai_v2': [
        "canvas_canvasdata12_fingerprintjs1",
        "canvas_canvasdata13_fingerprintjs2",
    ],
    'canvas-fpjs_v2': [
        "canvas_canvasdata12_fingerprintjs1",
        "canvas_canvasdata13_fingerprintjs2",
        "canvas_canvasdata11_webgl",
    ],
    'canvas-signifyd': [
        "canvas_canvasdata13_fingerprintjs2",
        "canvas_canvasdata01",
        "canvas_canvasdata02",
        "canvas_canvasdata07",
        "canvas_canvasdata08",
        "canvassoftware_canvasdata01",
        "canvassoftware_canvasdata02",
        "canvassoftware_canvasdata13_fingerprintjs2",
    ],

    # ── Screen ────────────────────────────────────────────────────────────────
    'screen-akamai_v2': [
        "screen_primary_resolution",
        "screen_primary_avail",
        "screen_primary_color_depth",
        "screen_primary_pixel_depth",
        "screen_web_inner",
        "screen_web_outer",
    ],
    'screen-fpjs_v2': [
        "screen_primary_resolution",
        "screen_primary_avail",
        "screen_primary_color_depth",
        "screen_web_inner",
        "screen_web_outer",
        "screen_web_avail_top",
        "screen_web_avail_left",
        "screen_web_pixel_ratio",
    ],
    'screen-signifyd': [
        "screen_primary_resolution",
        "screen_primary_avail",
        "screen_primary_color_depth",
        "screen_primary_pixel_depth",
        "screen_web_inner",
        "screen_web_pixel_ratio",
    ],

    # ── ClientRects ───────────────────────────────────────────────────────────
    'clientrect': [  # signifyd
        "combined_clientrects_element_gbcr_hash",
        "combined_clientrects_element_gcr_hash",
        "combined_clientrects_emoji_hash",
        "clientrects_ghost_dimensions",
        "clientrects_known_dimensions",
        "combined_clientrects_range_gbcr_hash",
        "combined_clientrects_range_gcr_hash",
    ],

    # ── WebGL Metadata ────────────────────────────────────────────────────────
    'webgl metadata': [  # fpjs_v2
        "webgl_vendor",
        "webgl2_vendor",
        "webgl_vendor_raw",
        "webgl2_vendor_raw",
        "webgl_renderer",
        "webgl2_renderer",
    ],
    'webgl metadata-signifyd': [
        "webgl_vendor",
        "webgl_vendor_raw",
        "webgl_renderer",
    ],

    # ── WebGL Params ──────────────────────────────────────────────────────────
    'webgl params': [  # fpjs_v2
        "webgl_precision_fragment",
        "webgl2_precision_fragment",
        "webgl_precision_vertex",
        "webgl2_precision_vertex",
        "webgl_extensions",
        "combined_webgl1_params_hash",
        "combined_webgl_extensions_hash",
    ],

    # ── Language ──────────────────────────────────────────────────────────────
    'language-akamai_v2': [
        "locale_accept_language",
        "locale_languages",
    ],
    'language-fpjs_v2_signifyd': [
        "locale_accept_language",
        "intl_intl_locale",
    ],

    # ── Timezone ──────────────────────────────────────────────────────────────
    'timezone': [  # fpjs_v2, signifyd
        "intl_timezone_web",
        "intl_timezone_offset_web",
    ],

    # ── WebGPU ────────────────────────────────────────────────────────────────
    'wgpu-full': [  # fpjs_v2
        "wgpu_is_fallback_adapter",
        "wgpu_missing_features",
        "combined_wgpu_hash",
    ],
    'wgpu-full-signifyd': [
        "wgpu_is_fallback_adapter",
        "wgpu_missing_features",
    ],
    'wgpu-partial': [  # signifyd
        "wgpu_missing_features",
        "wgpu_is_fallback_adapter",
        "wgpu_maxtexturedimension1d",
        "wgpu_maxtexturedimension2d",
        "wgpu_maxtexturedimension3d",
        "wgpu_maxbindgroups",
        "wgpu_maxdynamicuniformbuffersperpipelinelayout",
        "wgpu_maxdynamicstoragebuffersperpipelinelayout",
        "wgpu_maxbuffersize",
        "wgpu_maxcolorattachments",
        "wgpu_maxcomputeworkgroupstoragesize",
        "wgpu_maxcomputeinvocationsperworkgroup",
        "wgpu_maxstoragebufferspershaderstage",
        "wgpu_maxuniformbufferbindingsize",
        "wgpu_maxvertexbuffers",
        "wgpu_maxvertexattributes",
    ],
    'wgpu-partial-fpjs_v2': [
        "wgpu_missing_features",
        "wgpu_is_fallback_adapter",
    ],

    # ── Audio ─────────────────────────────────────────────────────────────────
    'audio': [  # fpjs_v2
        "audio_fingerprint",
    ],
    'audio-full': [  # signifyd
        "audio_compressor_gain_reduction",
        "audio_fingerprint2",
        "audio_unique_samples",
        "audio_float_frequency_sum",
        "audio_float_time_domain_sum",
    ],

    # ── Fonts ─────────────────────────────────────────────────────────────────
    'fonts_fpjs_allowlisted': [  # fpjs_v2
        "fonts_fpjs_allowlisted",
    ],
    'fonts_fpjs_nonallowlisted': [  # fpjs_v2
        "fonts_fpjs_allowlisted",
        "fonts_fpjs_nonallowlisted",
    ],
    'fonts_signifyd_allowlisted': [  # signifyd
        "fonts_variant_f_allowlisted",
        "fonts_variant_g_allowlisted",
        "fonts_variant_h_allowlisted",
        "fonts_variant_i_allowlisted",
        "svg_emoji_set",
        "clientrects_emoji_font_family",
        "clientrects_text_font_family",
    ],
    'fonts_signifyd_nonallowlisted': [  # signifyd
        "fonts_variant_f_allowlisted",
        "fonts_variant_f_nonallowlisted",
        "fonts_variant_g_allowlisted",
        "fonts_variant_g_nonallowlisted",
        "fonts_variant_h_allowlisted",
        "fonts_variant_h_nonallowlisted",
        "fonts_variant_i_allowlisted",
        "fonts_variant_i_nonallowlisted",
        "svg_emoji_set",
        "clientrects_emoji_font_family",
        "clientrects_text_font_family",
    ],

    # ── System Font / Colors ──────────────────────────────────────────────────
    'system font/colors': [  # fpjs_v2, signifyd
        "combined_css_colors_hash",
        "combined_css_fonts_hash",
        "prefs_use_document_colors",
    ],

    # ── Media / Codecs ────────────────────────────────────────────────────────
    'media + codecs': [  # fpjs_v2
        "combined_media_capabilities_hash",
        "sdp_codec_list",
    ],

    # ── SVG ───────────────────────────────────────────────────────────────────
    'svg': [  # signifyd
        "svg_bbox",
        "svg_computed_text_length",
        "svg_extent_of_char",
        "svg_substring_length",
    ],

    # ── Pointer Type ──────────────────────────────────────────────────────────
    'pointer type': [  # signifyd
        "hw_pointer_type",
        "hw_any_pointer_type",
    ],

}




def output_smr(smr_fingerprints, smr_metric_list, num_users, num_unique_users, baseline_fitness, fp_name, baseline_fitness_hhi2=None, baseline_p50=None):
    """
    Produces SMR output: uniqueness results and cohort tables for one fingerprinter.
    num_users, num_unique_users, and baseline_fitness are pre-computed from the
    baseline fingerprint counter.
    """
    slug = _fp_slug(fp_name)
    # Truncate output files so -r doesn't append duplicates
    for _f in (f"smr_uniqueness_results_{slug}.txt", f"smr_cohort_results_{slug}.txt"):
        _p = os.path.join(config.OUTPUT_FOLDER, _f)
        if os.path.exists(_p):
            open(_p, 'w').close()
    print(f"Single-metric removal analysis ({fp_name})...")
    t0 = time.time()

    uniqueness_results = {}
    fitness_vals = {}
    fitness_vals_hhi2 = {}
    p50_vals = {}
    cohort_counts = {}
    cohort_sizes = {}

    for metric in smr_metric_list:
        key = metric if isinstance(metric, str) else str(metric)
        hist = smr_fingerprints[key]  # {cohort_size: num_cohorts} histogram

        uniqueness_results[key] = hist.get(1, 0)
        fitness_vals[key] = cohort_fitness_from_histogram(hist)
        fitness_vals_hhi2[key] = cohort_fitness_from_histogram_excluding_singletons(hist)
        p50_vals[key] = cohort_p50_from_histogram(hist)

        cohort_counts[key] = dict(hist)  # num_cohorts per cohort_size
        cohort_sizes[key] = {size: size * count for size, count in hist.items()}

    print(f"  Done in {time.time()-t0:.2f}s\n")

    sorted_keys = sorted(uniqueness_results, key=uniqueness_results.get)
    config.log_and_file(f"smr_uniqueness_results_{slug}.txt", f"  Uniqueness Results ({fp_name}):")
    for k in sorted_keys:
        if num_unique_users - uniqueness_results[k] != 0:
            config.log_and_file(f"smr_uniqueness_results_{slug}.txt", "   ", num_unique_users - uniqueness_results[k], "fewer unique users when ignoring", k)
    print()

    config.log_and_file(f"smr_cohort_results_{slug}.txt", f"  Cohort Results:")
    config.log_and_file(f"smr_cohort_results_{slug}.txt", f"  This is sorted by the frequency of the cohort size, not by the total number of users in the cohort\n")
    config.log_and_file(f"smr_cohort_results_{slug}.txt", f"  Our baseline is that there are {num_unique_users} unique users, or {num_unique_users / num_users * 100:.2f}% out of {num_users} users")
    config.log_and_file(f"smr_cohort_results_{slug}.txt", f"  Our baseline cohort fitness score is", baseline_fitness, "(higher is better)")
    if baseline_fitness_hhi2 is not None:
        config.log_and_file(f"smr_cohort_results_{slug}.txt", f"  Our baseline HHI2 (excl. singletons) is", baseline_fitness_hhi2)
    if baseline_p50 is not None:
        config.log_and_file(f"smr_cohort_results_{slug}.txt", f"  Our baseline P50 (median cohort, non-unique) is", baseline_p50)
    config.log_and_file(f"smr_cohort_results_{slug}.txt", f"")

    cohort_fitness_values = {k: fitness_vals[k] for k in sorted_keys}
    num_unique_users_ignoring = {k: uniqueness_results[k] for k in sorted_keys}
    cohort_size_frequency = {k: cohort_counts[k] for k in sorted_keys}
    cohort_size_users = {k: cohort_sizes[k] for k in sorted_keys}

    PRINT_MAX_LINES = 10

    for metric in sorted(cohort_fitness_values, key=cohort_fitness_values.get, reverse=True):
        metric_key = metric if isinstance(metric, str) else str(metric)
        if cohort_fitness_values[metric_key] == baseline_fitness:
            continue

        config.log_and_file(f"smr_cohort_results_{slug}.txt", "  Ignoring", metric)
        config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", "-" * 20)
        config.log_and_file(f"smr_cohort_results_{slug}.txt", f"    There are {num_unique_users_ignoring[metric_key]} unique users, or {num_unique_users_ignoring[metric_key] / num_users * 100:.2f}% out of {num_users} users")
        config.log_and_file(f"smr_cohort_results_{slug}.txt", "    Our cohort fitness score is", cohort_fitness_values[metric_key])
        config.log_and_file(f"smr_cohort_results_{slug}.txt", "    Our HHI2 (excl. singletons) is", fitness_vals_hhi2.get(metric_key, 0))
        config.log_and_file(f"smr_cohort_results_{slug}.txt", "    Our P50 (median cohort, non-unique) is", p50_vals.get(metric_key, 0))

        data_keys = sorted(
            cohort_size_frequency[metric_key],
            key=cohort_size_frequency[metric_key].get,
            reverse=True
        )

        max_key_length = max(
            len(str(max(data_keys, key=lambda x: len(str(x))))),
            len("XXXXX Other Values")
        )

        config.log_and_file(f"smr_cohort_results_{slug}.txt", "    cohort_size".ljust(max_key_length), "    | # of cohorts     | # of users     | % of users")
        config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", "-" * 60)

        num_shown = 0
        cohort_remainder_aggregate = 0
        cohort_user_aggregate = 0
        for k in data_keys:
            if num_shown >= PRINT_MAX_LINES:
                cohort_user_aggregate += cohort_size_users[metric_key][k]
                cohort_remainder_aggregate += cohort_size_frequency[metric_key][k]
            else:
                config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", str(k).ljust(max_key_length), "| ", end="")
                config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", str(cohort_size_frequency[metric_key][k]).ljust(len("# of cohorts")), "| ", end="")
                config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", str(cohort_size_users[metric_key][k]).ljust(len("# of users")), "| ", end="")
                config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", f"{cohort_size_users[metric_key][k] / num_users * 100:.2f} %")
            num_shown += 1
        if num_shown > PRINT_MAX_LINES:
            config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", (str(num_shown - PRINT_MAX_LINES) + " Other Values").ljust(max_key_length), "| ", end="")
            config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", str(cohort_remainder_aggregate).ljust(len("# of cohorts")), "| ", end="")
            config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", str(cohort_user_aggregate).ljust(len("# of users")), "| ", end="")
            config.log_and_file(f"smr_cohort_results_{slug}.txt", "   ", f"{cohort_user_aggregate / num_users * 100:.2f} %")

        config.log_and_file(f"smr_cohort_results_{slug}.txt", "\n")

    # Write machine-readable CSV for downstream merge scripts
    csv_path = os.path.join(config.OUTPUT_FOLDER, f"smr_results_{slug}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "UniqueUsersWhenRemoved", "CohortFitnessWhenRemoved", "CohortFitnessHHI2WhenRemoved", "P50WhenRemoved"])
        for k in sorted(uniqueness_results):
            fitness = fitness_vals[k]
            fitness2 = fitness_vals_hhi2[k]
            p50 = p50_vals[k]
            writer.writerow([k,
                             uniqueness_results[k],
                             fitness if fitness != baseline_fitness else "",
                             fitness2 if fitness2 != (baseline_fitness_hhi2 or 0) else "",
                             p50 if p50 != (baseline_p50 or 0) else ""])
    print(f"  SMR CSV written to {csv_path}")

    # Write fingerprinter name and metric list to a separate provenance file
    prov_path = os.path.join(config.OUTPUT_FOLDER, f"smr_provenance_{slug}.txt")
    sorted_metrics = sorted(str(m) for m in smr_metric_list)
    with open(prov_path, "w", encoding="utf-8") as pf:
        pf.write(f"SMR fingerprinter: {fp_name}\n")
        pf.write(f"SMR metric count: {len(sorted_metrics)}\n")
        pf.write("SMR metrics: " + ", ".join(sorted_metrics) + "\n")
    print(f"  SMR provenance written to {prov_path}")


def output_ismr(fp_name, num_users, num_unique_users, removed_metrics):
    """
    Write ISMR results to ismr_analysis.txt and ismr_results.csv.

    Args:
        fp_name: fingerprinter name used for ISMR
        num_users: total user count
        num_unique_users: baseline unique users (before any removal)
        removed_metrics: list of (metric_name, unique_users_after_removal) tuples
            in removal order
    """
    slug = _fp_slug(fp_name)
    fname = f"ismr_analysis_{slug}.txt"

    # Truncate on regeneration
    _p = os.path.join(config.OUTPUT_FOLDER, fname)
    if os.path.exists(_p):
        open(_p, 'w').close()

    config.log_and_file(fname, f"Iterative Single-Metric Removal Analysis ({fp_name})")
    config.log_and_file(fname, f"  Baseline: {num_unique_users} unique users "
                        f"({num_unique_users / num_users * 100:.2f}%) out of {num_users}")
    config.log_and_file(fname, "")

    for i, (metric, unique_after) in enumerate(removed_metrics, 1):
        config.log_and_file(fname, f"  {i}. Remove '{metric}' → {unique_after} unique users "
                            f"({unique_after / num_users * 100:.2f}%)")

    config.log_and_file(fname, "")
    config.log_and_file(fname, f"  Total metrics removed: {len(removed_metrics)}")
    if removed_metrics:
        final_unique = removed_metrics[-1][1]
        config.log_and_file(fname, f"  Final: {final_unique} unique users "
                            f"({final_unique / num_users * 100:.2f}%), "
                            f"reduced from {num_unique_users} "
                            f"({(num_unique_users - final_unique) / num_users * 100:.2f}% reduction)")

    # CSV
    csv_path = os.path.join(config.OUTPUT_FOLDER, f"ismr_results_{slug}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Order", "MetricRemoved", "UniqueUsersAfter", "PctUnique", "BaselineUniqueUsers"])
        for i, (metric, unique_after) in enumerate(removed_metrics, 1):
            writer.writerow([i, metric, unique_after,
                             round(unique_after / num_users * 100, 4),
                             num_unique_users])
    print(f"  ISMR results written to {fname} and {csv_path}")


def output_ismrp(fp_name, num_users, num_unique_users, removed_metrics, threshold_pct):
    """
    Write ISMRP results to ismrp_analysis.txt and ismrp_results.csv.

    Args:
        fp_name: fingerprinter name used for ISMRP
        num_users: total user count
        num_unique_users: baseline unique users (before any replacement)
        removed_metrics: list of (metric_name, unique_users_after, num_replaced) tuples
            in replacement order
        threshold_pct: the rare-value threshold used
    """
    slug = _fp_slug(fp_name)
    fname = f"ismrp_analysis_{slug}.txt"

    _p = os.path.join(config.OUTPUT_FOLDER, fname)
    if os.path.exists(_p):
        open(_p, 'w').close()

    config.log_and_file(fname, f"Iterative Single-Metric Replacement Analysis ({fp_name})")
    config.log_and_file(fname, f"  Baseline: {num_unique_users} unique users "
                        f"({num_unique_users / num_users * 100:.2f}%) out of {num_users}")
    config.log_and_file(fname, f"  Rare-value threshold: {threshold_pct}%")
    config.log_and_file(fname, f"  Replacement strategy: mode (most common value)")
    config.log_and_file(fname, "")

    for i, (metric, unique_after, num_replaced) in enumerate(removed_metrics, 1):
        pct_replaced = num_replaced / num_users * 100
        config.log_and_file(fname, f"  {i}. Replace rare in '{metric}' → {unique_after} unique users "
                            f"({unique_after / num_users * 100:.2f}%) "
                            f"[{num_replaced} users replaced ({pct_replaced:.2f}%)]")

    config.log_and_file(fname, "")
    config.log_and_file(fname, f"  Total metrics with replacements: {len(removed_metrics)}")
    if removed_metrics:
        final_unique = removed_metrics[-1][1]
        config.log_and_file(fname, f"  Final: {final_unique} unique users "
                            f"({final_unique / num_users * 100:.2f}%), "
                            f"reduced from {num_unique_users} "
                            f"({(num_unique_users - final_unique) / num_users * 100:.2f}% reduction)")

    # CSV
    csv_path = os.path.join(config.OUTPUT_FOLDER, f"ismrp_results_{slug}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Order", "MetricReplaced", "UniqueUsersAfter", "PctUnique",
                         "UsersReplaced", "PctReplaced", "BaselineUniqueUsers"])
        for i, (metric, unique_after, num_replaced) in enumerate(removed_metrics, 1):
            writer.writerow([i, metric, unique_after,
                             round(unique_after / num_users * 100, 4),
                             num_replaced,
                             round(num_replaced / num_users * 100, 4),
                             num_unique_users])
    print(f"  ISMRP results written to {fname} and {csv_path}")


# =============================================================================
# Logical Metric Removal (LMR)
# =============================================================================

# Maps fingerprinter name (ALL_FINGERPRINTERS key) → ordered list of
# METRICS_TO_COMBINE keys that are logical removal units for that fingerprinter.
LMR_GROUPS = {
    "AkamaiV2": [
        "canvas-akamai_v2",
        "screen-akamai_v2",
        "language-akamai_v2",
    ],
    "FPJSv2": [
        "canvas-fpjs_v2",
        "screen-fpjs_v2",
        "webgl metadata",
        "webgl params",
        "language-fpjs_v2_signifyd",
        "timezone",
        "wgpu-full",
        "audio",
        "fonts_fpjs_allowlisted",
        "fonts_fpjs_nonallowlisted",
        "system font/colors",
        "media + codecs",
    ],
    "Signifyd": [
        "canvas-signifyd",
        "screen-signifyd",
        "clientrect",
        "webgl metadata-signifyd",
        "language-fpjs_v2_signifyd",
        "timezone",
        "wgpu-partial",
        "audio-full",
        "fonts_signifyd_allowlisted",
        "fonts_signifyd_nonallowlisted",
        "system font/colors",
        "svg",
        "pointer type",
    ],

}

LMR_FINGERPRINTERS_DEFAULT = list(LMR_GROUPS.keys())


def _fp_slug(fp_name):
    return {"AkamaiV2": "akamai_v2", "FPJSv2": "fpjs_v2", "Signifyd": "signifyd"}.get(
        fp_name, fp_name.lower()
    )


def build_lmr_unit_lists(fp_name, fp_set):
    """
    Build the LMR unit list for one fingerprinter.

    Returns a list of (unit_name, frozenset_of_metrics_to_exclude) tuples.
    Groups from LMR_GROUPS are listed first (intersected with fp_set).
    Metrics in fp_set not covered by any group are appended individually.
    """
    units = []
    covered = set()

    for key in LMR_GROUPS.get(fp_name, []):
        group_metrics = frozenset(METRICS_TO_COMBINE[key]) & fp_set
        if not group_metrics:
            continue
        units.append((key, group_metrics))
        covered.update(group_metrics)

    for metric in sorted(fp_set - covered):
        units.append((metric, frozenset({metric})))

    return units


def output_lmr(lmr_fingerprints_for_fp, lmr_unit_list, num_users, num_unique_users,
               baseline_fitness, fp_name, baseline_fitness_hhi2=None, baseline_p50=None):
    """
    Produce LMR output files for one fingerprinter.

    lmr_fingerprints_for_fp: dict[unit_name → {cohort_size: num_cohorts}]
    lmr_unit_list:           list of (unit_name, frozenset_of_metrics_in_unit)
    num_users, num_unique_users, baseline_fitness: pre-computed baseline scalars
    fp_name:                 fingerprinter name (used in filenames)
    """
    slug = _fp_slug(fp_name)
    # Truncate output files so -r doesn't append duplicates
    for _f in (f"lmr_uniqueness_results_{slug}.txt", f"lmr_cohort_results_{slug}.txt"):
        _p = os.path.join(config.OUTPUT_FOLDER, _f)
        if os.path.exists(_p):
            open(_p, 'w').close()
    print(f"Logical-metric removal analysis ({fp_name})...")
    t0 = time.time()

    uniqueness_results = {}
    fitness_vals = {}
    fitness_vals_hhi2 = {}
    p50_vals = {}
    cohort_counts = {}
    cohort_sizes = {}

    for unit_name, _ in lmr_unit_list:
        hist = lmr_fingerprints_for_fp.get(unit_name)
        if not hist:
            continue
        uniqueness_results[unit_name] = hist.get(1, 0)
        fitness_vals[unit_name] = cohort_fitness_from_histogram(hist)
        fitness_vals_hhi2[unit_name] = cohort_fitness_from_histogram_excluding_singletons(hist)
        p50_vals[unit_name] = cohort_p50_from_histogram(hist)
        cohort_counts[unit_name] = dict(hist)
        cohort_sizes[unit_name] = {size: size * count for size, count in hist.items()}

    print(f"  Done in {time.time()-t0:.2f}s\n")

    sorted_keys = sorted(uniqueness_results, key=uniqueness_results.get)
    uniq_fname = f"lmr_uniqueness_results_{slug}.txt"
    config.log_and_file(uniq_fname, f"  LMR Uniqueness Results ({fp_name}):")
    for k in sorted_keys:
        if num_unique_users - uniqueness_results[k] != 0:
            config.log_and_file(uniq_fname, "   ", num_unique_users - uniqueness_results[k],
                                "fewer unique users when ignoring", k)
    print()

    cohort_fname = f"lmr_cohort_results_{slug}.txt"
    config.log_and_file(cohort_fname, f"  LMR Cohort Results ({fp_name}):")
    config.log_and_file(cohort_fname,
        "  This is sorted by the frequency of the cohort size, not the total number of users\n")
    config.log_and_file(cohort_fname,
        f"  Baseline: {num_unique_users} unique users "
        f"({num_unique_users / num_users * 100:.2f}%) out of {num_users} users")
    config.log_and_file(cohort_fname,
        "  Baseline cohort fitness score:", baseline_fitness, "(higher is better)")
    if baseline_fitness_hhi2 is not None:
        config.log_and_file(cohort_fname,
            "  Baseline HHI2 (excl. singletons):", baseline_fitness_hhi2)
    if baseline_p50 is not None:
        config.log_and_file(cohort_fname,
            "  Baseline P50 (median cohort, non-unique):", baseline_p50)
    config.log_and_file(cohort_fname, "")

    cohort_fitness_values = {k: fitness_vals[k] for k in sorted_keys}
    num_unique_users_ignoring = {k: uniqueness_results[k] for k in sorted_keys}
    cohort_size_frequency = {k: cohort_counts[k] for k in sorted_keys}
    cohort_size_users = {k: cohort_sizes[k] for k in sorted_keys}

    PRINT_MAX_LINES = 10
    for unit in sorted(cohort_fitness_values, key=cohort_fitness_values.get, reverse=True):
        if cohort_fitness_values[unit] == baseline_fitness:
            continue

        config.log_and_file(cohort_fname, "  Ignoring", unit)
        config.log_and_file(cohort_fname, "   ", "-" * 20)
        config.log_and_file(cohort_fname,
            f"    {num_unique_users_ignoring[unit]} unique users "
            f"({num_unique_users_ignoring[unit] / num_users * 100:.2f}%) out of {num_users} users")
        config.log_and_file(cohort_fname, "    Cohort fitness:", cohort_fitness_values[unit])
        config.log_and_file(cohort_fname, "    HHI2 (excl. singletons):", fitness_vals_hhi2.get(unit, 0))
        config.log_and_file(cohort_fname, "    P50 (median cohort, non-unique):", p50_vals.get(unit, 0))

        data_keys = sorted(cohort_size_frequency[unit], key=cohort_size_frequency[unit].get, reverse=True)
        if not data_keys:
            continue
        max_key_length = max(
            len(str(max(data_keys, key=lambda x: len(str(x))))),
            len("XXXXX Other Values"),
        )

        config.log_and_file(cohort_fname, "    cohort_size".ljust(max_key_length),
                            "    | # of cohorts     | # of users     | % of users")
        config.log_and_file(cohort_fname, "   ", "-" * 60)

        num_shown = 0
        cohort_remainder_aggregate = 0
        cohort_user_aggregate = 0
        for k in data_keys:
            if num_shown >= PRINT_MAX_LINES:
                cohort_user_aggregate += cohort_size_users[unit][k]
                cohort_remainder_aggregate += cohort_size_frequency[unit][k]
            else:
                config.log_and_file(cohort_fname, "   ", str(k).ljust(max_key_length), "| ", end="")
                config.log_and_file(cohort_fname, "   ",
                                    str(cohort_size_frequency[unit][k]).ljust(len("# of cohorts")), "| ", end="")
                config.log_and_file(cohort_fname, "   ",
                                    str(cohort_size_users[unit][k]).ljust(len("# of users")), "| ", end="")
                config.log_and_file(cohort_fname, "   ",
                                    f"{cohort_size_users[unit][k] / num_users * 100:.2f} %")
            num_shown += 1
        if num_shown > PRINT_MAX_LINES:
            config.log_and_file(cohort_fname, "   ",
                                (str(num_shown - PRINT_MAX_LINES) + " Other Values").ljust(max_key_length), "| ", end="")
            config.log_and_file(cohort_fname, "   ",
                                str(cohort_remainder_aggregate).ljust(len("# of cohorts")), "| ", end="")
            config.log_and_file(cohort_fname, "   ",
                                str(cohort_user_aggregate).ljust(len("# of users")), "| ", end="")
            config.log_and_file(cohort_fname, "   ", f"{cohort_user_aggregate / num_users * 100:.2f} %")

        config.log_and_file(cohort_fname, "\n")

    # Machine-readable CSV
    csv_path = os.path.join(config.OUTPUT_FOLDER, f"lmr_results_{slug}.csv")
    unit_metrics_map = dict(lmr_unit_list)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Unit", "MetricsInUnit", "UniqueUsersWhenRemoved",
                         "CohortFitnessWhenRemoved", "CohortFitnessHHI2WhenRemoved",
                         "P50WhenRemoved",
                         "BaselineUniqueUsers", "BaselineFitness", "BaselineFitnessHHI2",
                         "BaselineP50"])
        for k in sorted(uniqueness_results):
            fitness = fitness_vals[k]
            fitness2 = fitness_vals_hhi2.get(k, 0)
            p50 = p50_vals.get(k, 0)
            unit_metrics = sorted(unit_metrics_map.get(k, set()))
            writer.writerow([
                k,
                "|".join(unit_metrics),
                uniqueness_results[k],
                fitness if fitness != baseline_fitness else "",
                fitness2 if fitness2 != (baseline_fitness_hhi2 or 0) else "",
                p50 if p50 != (baseline_p50 or 0) else "",
                num_unique_users,
                baseline_fitness,
                baseline_fitness_hhi2 or "",
                baseline_p50 or "",
            ])
    print(f"  LMR CSV written to {csv_path}")

    # Provenance
    prov_path = os.path.join(config.OUTPUT_FOLDER, f"lmr_provenance_{slug}.txt")
    with open(prov_path, "w", encoding="utf-8") as pf:
        pf.write(f"LMR fingerprinter: {fp_name}\n")
        pf.write(f"LMR unit count: {len(lmr_unit_list)}\n")
        for unit_name, metrics in lmr_unit_list:
            pf.write(f"  {unit_name}: {', '.join(sorted(metrics))}\n")
    print(f"  LMR provenance written to {prov_path}")

    return num_users, num_unique_users


def graph_lmr_combined(fp_names):
    """
    Generate a combined LMR lollipop chart from the per-fingerprinter CSVs
    already written to config.OUTPUT_FOLDER.  Units with < 5% impact for all
    present fingerprinters are excluded.  Saves lmr_graph_combined.png next to
    the CSVs and copies it to /work/sandbox-cache/000-img/ if that dir exists.
    """
    import datetime
    import shutil
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  WARNING: matplotlib not available, skipping LMR combined graph")
        return

    FP_COLORS = {"AkamaiV2": "#E91E63", "FPJSv2": "#2196F3", "Signifyd": "#4CAF50"}
    FP_SLUGS = ["fpjs_v2_signifyd", "akamai_v2", "fpjs_v2", "signifyd"]
    QUALIFIER_SUFFIXES = ["-full", "-partial"]
    UNIT_REMAPS = {"intl_timezone_offset_web": "timezone"}
    THRESHOLD = 5.0

    def _base_name(name):
        for slug in FP_SLUGS:
            if name.endswith(f"-{slug}"):
                name = name[: -len(slug) - 1]
                break
        for qual in QUALIFIER_SUFFIXES:
            if name.endswith(qual):
                name = name[: -len(qual)]
                break
        return UNIT_REMAPS.get(name, name)

    INDIVIDUAL_OVERRIDES = {"fonts_fpjs_nonallowlisted"}

    def _is_group(unit_name, metrics):
        if unit_name in INDIVIDUAL_OVERRIDES:
            return False
        return len(metrics) > 1 or unit_name != metrics[0]

    LABEL_RENAMES = {
        "hw_processor_count":      "CPU Count",
        "fonts_fpjs_nonallowlisted": "Font Enumeration",
    }

    def _y_label(base):
        is_grp = any(_is_group(base, e["metrics"]) for e in combined[base].values())
        name = LABEL_RENAMES.get(base, base.replace("_", " ").title())
        return f"{name} Metrics" if is_grp else name

    # Read each fingerprinter's CSV
    combined = {}   # base → {fp_name: {pct, metrics}}
    for fp_name in fp_names:
        slug = _fp_slug(fp_name)
        csv_path = os.path.join(config.OUTPUT_FOLDER, f"lmr_results_{slug}.csv")
        if not os.path.exists(csv_path):
            continue
        rows = {}
        with open(csv_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                metrics = [m for m in r["MetricsInUnit"].split("|") if m]
                bl_uniq_raw = r.get("BaselineUniqueUsers", "").strip()
                rows[r["Unit"]] = {
                    "metrics": metrics,
                    "uniq": int(r["UniqueUsersWhenRemoved"]),
                    "bl_uniq": int(bl_uniq_raw) if bl_uniq_raw else None,
                }
        if not rows:
            continue
        first = next(iter(rows.values()))
        baseline = first["bl_uniq"] if first["bl_uniq"] else max(e["uniq"] for e in rows.values())
        for unit_name, entry in rows.items():
            entry["pct"] = (baseline - entry["uniq"]) / baseline * 100.0
            base = _base_name(unit_name)
            if base not in combined:
                combined[base] = {}
            if fp_name not in combined[base]:
                combined[base][fp_name] = entry

    # Filter rows where all values < threshold
    combined = {
        base: fps for base, fps in combined.items()
        if any(v["pct"] >= THRESHOLD for v in fps.values())
    }
    if not combined:
        print("  LMR combined graph: no rows above threshold, skipping")
        return

    sorted_bases = sorted(
        combined.keys(),
        key=lambda b: max(v["pct"] for v in combined[b].values()),
        reverse=True,
    )

    offsets = [-0.20, 0.0, 0.20]
    n = len(sorted_bases)
    fig_h = max(4, n * 0.30 + 1.5)
    fig, ax = plt.subplots(figsize=(10, fig_h))

    for row_idx, base in enumerate(sorted_bases):
        for j, fp_name in enumerate(fp_names):
            if fp_name not in combined[base]:
                continue
            color = FP_COLORS.get(fp_name, "#888888")
            y = row_idx + offsets[j]
            x = combined[base][fp_name]["pct"]
            ax.hlines(y, 0, x, colors=color, linewidths=1.1, alpha=0.82)
            ax.scatter(x, y, color=color, s=22, zorder=3)

    ax.set_yticks(range(n))
    ax.set_yticklabels([_y_label(b) for b in sorted_bases], fontsize=7.5)
    ax.invert_yaxis()
    for tick, base in zip(ax.get_yticklabels(), sorted_bases):
        group = any(_is_group(base, e["metrics"]) for e in combined[base].values())
        tick.set_color("#1565C0" if group else "#616161")

    ax.set_xlabel("% of unique users no longer unique when metric removed", fontsize=9)
    ax.set_title("Logical Metric Removal", fontsize=11)
    ax.grid(True, axis="x", linestyle="--", alpha=0.28, zorder=0)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    fig.text(
        0.5, 0.01,
        "Metrics or groups with < 5% impact for all fingerprinters excluded.",
        ha="center", va="bottom", fontsize=7.5, color="#757575", style="italic",
    )

    fp_handles = [
        plt.Line2D([0], [0], color=FP_COLORS.get(fp, "#888"), marker="o",
                   markersize=5, linewidth=1.4, label=fp)
        for fp in fp_names if fp in FP_COLORS
    ]
    style_handles = [
        mpatches.Patch(color="#1565C0", label="Logical group (label)"),
        mpatches.Patch(color="#616161", label="Individual metric (label)"),
    ]
    ax.legend(handles=fp_handles + style_handles, fontsize=7.5, loc="lower right")

    fig.tight_layout()
    out_path = os.path.join(config.OUTPUT_FOLDER, "lmr_graph_combined.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  LMR combined graph written to {out_path}")

    img_dir = "/work/sandbox-cache/000-img"
    if os.path.isdir(img_dir):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(img_dir, f"{ts}_lmr_combined.png")
        shutil.copy(out_path, dst)
        print(f"  Copied to {dst}")


def graph_lmr_combined_fitness_v1(fp_names):
    """
    Like graph_lmr_combined but overlays dashed lines on a secondary (top) x-axis
    showing % improvement in cohort fitness when each unit is removed.
    Baseline fitness per fingerprinter = min(CohortFitnessWhenRemoved).
    Saves lmr_graph_combined_fitness_v1.png.
    """
    import datetime
    import shutil
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import matplotlib.lines as mlines
    except ImportError:
        print("  WARNING: matplotlib not available, skipping LMR fitness graph")
        return

    FP_COLORS = {"AkamaiV2": "#E91E63", "FPJSv2": "#2196F3", "Signifyd": "#4CAF50"}
    FP_SLUGS = ["fpjs_v2_signifyd", "akamai_v2", "fpjs_v2", "signifyd"]
    QUALIFIER_SUFFIXES = ["-full", "-partial"]
    UNIT_REMAPS = {"intl_timezone_offset_web": "timezone"}
    THRESHOLD = 5.0

    def _base_name(name):
        for slug in FP_SLUGS:
            if name.endswith(f"-{slug}"):
                name = name[: -len(slug) - 1]
                break
        for qual in QUALIFIER_SUFFIXES:
            if name.endswith(qual):
                name = name[: -len(qual)]
                break
        return UNIT_REMAPS.get(name, name)

    INDIVIDUAL_OVERRIDES = {"fonts_fpjs_nonallowlisted"}

    def _is_group(unit_name, metrics):
        if unit_name in INDIVIDUAL_OVERRIDES:
            return False
        return len(metrics) > 1 or unit_name != metrics[0]

    LABEL_RENAMES = {
        "hw_processor_count":      "CPU Count",
        "fonts_fpjs_nonallowlisted": "Font Enumeration",
    }

    def _y_label(base):
        is_grp = any(_is_group(base, e["metrics"]) for e in combined[base].values())
        name = LABEL_RENAMES.get(base, base.replace("_", " ").title())
        return f"{name} Metrics" if is_grp else name

    # Read each fingerprinter's CSV — uniqueness and fitness
    combined = {}   # base → {fp_name: {pct, fit_pct, metrics}}
    for fp_name in fp_names:
        slug = _fp_slug(fp_name)
        csv_path = os.path.join(config.OUTPUT_FOLDER, f"lmr_results_{slug}.csv")
        if not os.path.exists(csv_path):
            continue
        rows = {}
        with open(csv_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                metrics = [m for m in r["MetricsInUnit"].split("|") if m]
                fit_raw = r.get("CohortFitnessWhenRemoved", "").strip()
                bl_uniq_raw = r.get("BaselineUniqueUsers", "").strip()
                bl_fit_raw  = r.get("BaselineFitness", "").strip()
                rows[r["Unit"]] = {
                    "metrics": metrics,
                    "uniq": int(r["UniqueUsersWhenRemoved"]),
                    "fitness": float(fit_raw) if fit_raw else None,
                    "bl_uniq": int(bl_uniq_raw) if bl_uniq_raw else None,
                    "bl_fit":  float(bl_fit_raw) if bl_fit_raw else None,
                }
        if not rows:
            continue
        first = next(iter(rows.values()))
        baseline_uniq = first["bl_uniq"] if first["bl_uniq"] else max(e["uniq"] for e in rows.values())
        baseline_fit  = first["bl_fit"]  if first["bl_fit"]  else (
            min(e["fitness"] for e in rows.values() if e["fitness"] is not None) or None)
        for unit_name, entry in rows.items():
            entry["pct"] = (baseline_uniq - entry["uniq"]) / baseline_uniq * 100.0
            if baseline_fit is not None and entry["fitness"] is not None:
                entry["fit_pct"] = (entry["fitness"] - baseline_fit) * 100.0
            else:
                entry["fit_pct"] = None
            base = _base_name(unit_name)
            if base not in combined:
                combined[base] = {}
            if fp_name not in combined[base]:
                combined[base][fp_name] = entry

    # Filter rows where all uniqueness values < threshold
    combined = {
        base: fps for base, fps in combined.items()
        if any(v["pct"] >= THRESHOLD for v in fps.values())
    }
    if not combined:
        print("  LMR fitness graph: no rows above threshold, skipping")
        return

    sorted_bases = sorted(
        combined.keys(),
        key=lambda b: max(v["pct"] for v in combined[b].values()),
        reverse=True,
    )

    # 6 sub-rows per metric: solid+dashed pair for each of 3 FPs, vertically separated
    fp_offsets = {
        fp_names[0]: (-0.38, -0.22),
        fp_names[1]: (-0.08,  0.08),
        fp_names[2]: ( 0.22,  0.38),
    } if len(fp_names) >= 3 else {
        fp: (i * 0.33 - 0.17, i * 0.33 - 0.05)
        for i, fp in enumerate(fp_names)
    }
    n = len(sorted_bases)
    fig_h = max(4, n * 0.45 + 1.8)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    ax2 = ax.twiny()   # will be repositioned to bottom
    ax2.xaxis.set_ticks_position("bottom")
    ax2.xaxis.set_label_position("bottom")
    ax2.spines["bottom"].set_position(("axes", -0.17))
    ax2.spines["top"].set_visible(False)
    ax2.spines["bottom"].set_linewidth(0.8)
    ax2.spines["bottom"].set_color("#555555")

    # Collect all fit_pct values to set secondary axis range
    all_fit_pcts = [
        v["fit_pct"]
        for fps in combined.values()
        for v in fps.values()
        if v.get("fit_pct") is not None
    ]
    fit_max = max(all_fit_pcts) * 1.05 if all_fit_pcts else 100.0

    for row_idx, base in enumerate(sorted_bases):
        for fp_name in fp_names:
            if fp_name not in combined[base]:
                continue
            entry = combined[base][fp_name]
            color = FP_COLORS.get(fp_name, "#888888")
            y_solid, y_dashed = (row_idx + fp_offsets[fp_name][0],
                                 row_idx + fp_offsets[fp_name][1])

            # Solid stem: uniqueness loss (bottom axis)
            ax.hlines(y_solid, 0, entry["pct"], colors=color, linewidths=1.1, alpha=0.82)
            ax.scatter(entry["pct"], y_solid, color=color, s=22, zorder=3)

            # Dashed stem: fitness improvement (top axis)
            if entry.get("fit_pct") is not None:
                ax2.hlines(y_dashed, 0, entry["fit_pct"],
                           colors=color, linewidths=1.1, alpha=0.55,
                           linestyle="--")
                ax2.scatter(entry["fit_pct"], y_dashed,
                            color=color, s=16, zorder=3,
                            marker="D", alpha=0.70)

    # Y-axis labels
    ax.set_yticks(range(n))
    ax.set_yticklabels([_y_label(b) for b in sorted_bases], fontsize=7.5)
    ax.invert_yaxis()
    ax2.set_ylim(ax.get_ylim())
    for tick, base in zip(ax.get_yticklabels(), sorted_bases):
        group = any(_is_group(base, e["metrics"]) for e in combined[base].values())
        tick.set_color("#1565C0" if group else "#616161")

    # Primary axis (bottom) — explicitly start at 0 so it aligns with secondary axis
    uniq_max = max(
        v["pct"] for fps in combined.values() for v in fps.values()
    ) * 1.05
    ax.set_xlim(0, uniq_max)
    ax.set_xlabel("% unique users no longer unique when metric removed", fontsize=9)
    ax.grid(True, axis="x", linestyle="--", alpha=0.18, zorder=0)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    # Secondary axis (top)
    ax2.set_xlim(0, fit_max)
    ax2.set_xlabel("cohort fitness improvement (×100)", fontsize=9,
                   labelpad=8)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.tick_params(axis="x", labelsize=7.5)

    ax.set_title("Logical Metric Removal — Uniqueness & Cohort Fitness", fontsize=11)
    fig.text(0.5, -0.015, "Shown if uniqueness ≥ 5% or fitness improvement ≥ 50%.",
             ha="center", va="bottom", fontsize=7, color="#757575", style="italic")

    # Legend
    fp_solid = [
        mlines.Line2D([0], [0], color=FP_COLORS.get(fp, "#888"), marker="o",
                      markersize=5, linewidth=1.4, label=fp)
        for fp in fp_names if fp in FP_COLORS
    ]
    style_handles = [
        mlines.Line2D([0], [0], color="#444", linewidth=1.3,
                      label="Solid = uniqueness loss"),
        mlines.Line2D([0], [0], color="#444", linewidth=1.3, linestyle="--",
                      label="Dashed = fitness improvement"),
        mpatches.Patch(color="#1565C0", label="Logical group (label)"),
        mpatches.Patch(color="#616161", label="Individual metric (label)"),
    ]
    ax.legend(handles=fp_solid + style_handles, fontsize=7, loc="lower right")

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)
    out_path = os.path.join(config.OUTPUT_FOLDER, "lmr_graph_combined_fitness_v1.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  LMR fitness v1 graph written to {out_path}")

    img_dir = "/work/sandbox-cache/000-img"
    if os.path.isdir(img_dir):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(img_dir, f"{ts}_lmr_combined_fitness_v1.png")
        shutil.copy(out_path, dst)
        print(f"  Copied to {dst}")


def graph_lmr_combined_fitness_v2(fp_names):
    """
    Two stacked subplots sharing the y-axis:
      Top:    uniqueness loss % (solid lines, one per FP)
      Bottom: cohort fitness improvement % (dashed lines, one per FP)
    Y-axis labels (metric names) repeat on both subplots.
    Baseline fitness per fingerprinter = min(CohortFitnessWhenRemoved).
    Saves lmr_graph_combined_fitness_v2.png.
    """
    import datetime
    import shutil
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import matplotlib.lines as mlines
    except ImportError:
        print("  WARNING: matplotlib not available, skipping LMR fitness v2 graph")
        return

    FP_COLORS = {"AkamaiV2": "#E91E63", "FPJSv2": "#2196F3", "Signifyd": "#4CAF50"}
    FP_SLUGS = ["fpjs_v2_signifyd", "akamai_v2", "fpjs_v2", "signifyd"]
    QUALIFIER_SUFFIXES = ["-full", "-partial"]
    UNIT_REMAPS = {"intl_timezone_offset_web": "timezone"}

    def _base_name(name):
        for slug in FP_SLUGS:
            if name.endswith(f"-{slug}"):
                name = name[: -len(slug) - 1]
                break
        for qual in QUALIFIER_SUFFIXES:
            if name.endswith(qual):
                name = name[: -len(qual)]
                break
        return UNIT_REMAPS.get(name, name)

    INDIVIDUAL_OVERRIDES = {"fonts_fpjs_nonallowlisted"}

    def _is_group(unit_name, metrics):
        if unit_name in INDIVIDUAL_OVERRIDES:
            return False
        return len(metrics) > 1 or unit_name != metrics[0]

    LABEL_RENAMES = {
        "hw_processor_count":      "CPU Count",
        "fonts_fpjs_nonallowlisted": "Font Enumeration",
    }

    def _y_label(base):
        is_grp = any(_is_group(base, e["metrics"]) for e in combined[base].values())
        name = LABEL_RENAMES.get(base, base.replace("_", " ").title())
        return f"{name} Metrics" if is_grp else name

    # ── Load ──────────────────────────────────────────────────────────────────
    combined = {}
    for fp_name in fp_names:
        slug = _fp_slug(fp_name)
        csv_path = os.path.join(config.OUTPUT_FOLDER, f"lmr_results_{slug}.csv")
        if not os.path.exists(csv_path):
            continue
        rows = {}
        with open(csv_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                metrics = [m for m in r["MetricsInUnit"].split("|") if m]
                fit_raw    = r.get("CohortFitnessWhenRemoved", "").strip()
                bl_uniq_raw = r.get("BaselineUniqueUsers", "").strip()
                bl_fit_raw  = r.get("BaselineFitness", "").strip()
                rows[r["Unit"]] = {
                    "metrics": metrics,
                    "uniq": int(r["UniqueUsersWhenRemoved"]),
                    "fitness": float(fit_raw) if fit_raw else None,
                    "bl_uniq": int(bl_uniq_raw) if bl_uniq_raw else None,
                    "bl_fit":  float(bl_fit_raw) if bl_fit_raw else None,
                }
        if not rows:
            continue
        first = next(iter(rows.values()))
        baseline_uniq = first["bl_uniq"] if first["bl_uniq"] else max(e["uniq"] for e in rows.values())
        baseline_fit  = first["bl_fit"]  if first["bl_fit"]  else (
            min(e["fitness"] for e in rows.values() if e["fitness"] is not None) or None)
        for unit_name, entry in rows.items():
            entry["pct"] = (baseline_uniq - entry["uniq"]) / baseline_uniq * 100.0
            entry["fit_pct"] = (
                (entry["fitness"] - baseline_fit) * 100.0
                if baseline_fit is not None and entry["fitness"] is not None else None
            )
            base = _base_name(unit_name)
            if base not in combined:
                combined[base] = {}
            if fp_name not in combined[base]:
                combined[base][fp_name] = entry

    UNIQ_THRESHOLD = 5.0
    FIT_THRESHOLD  = 50.0
    combined = {
        base: fps for base, fps in combined.items()
        if any(v["pct"] >= UNIQ_THRESHOLD for v in fps.values())
        or any(v.get("fit_pct") is not None and v["fit_pct"] >= FIT_THRESHOLD
               for v in fps.values())
    }
    if not combined:
        print("  LMR fitness v2 graph: no rows above threshold, skipping")
        return

    sorted_bases = sorted(
        combined.keys(),
        key=lambda b: (
            max(v["pct"] for v in combined[b].values()),
            max((v.get("fit_pct") or 0.0) for v in combined[b].values()),
        ),
        reverse=True,
    )

    all_fit_pcts = [
        v["fit_pct"] for fps in combined.values()
        for v in fps.values() if v.get("fit_pct") is not None
    ]
    fit_max = max(all_fit_pcts) * 1.05 if all_fit_pcts else 100.0
    uniq_max = max(
        v["pct"] for fps in combined.values() for v in fps.values()
    ) * 1.05

    offsets = [-0.20, 0.0, 0.20]
    n = len(sorted_bases)
    fig_h = max(5, n * 0.55 + 2.5)
    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(10, fig_h), sharey=True,
        gridspec_kw={"hspace": 0.12},
    )

    # ── Plot ──────────────────────────────────────────────────────────────────
    for row_idx, base in enumerate(sorted_bases):
        for j, fp_name in enumerate(fp_names):
            if fp_name not in combined[base]:
                continue
            entry = combined[base][fp_name]
            color = FP_COLORS.get(fp_name, "#888888")
            y = row_idx + offsets[j]

            # Top: uniqueness loss
            ax_top.hlines(y, 0, entry["pct"], colors=color, linewidths=1.1, alpha=0.82)
            ax_top.scatter(entry["pct"], y, color=color, s=22, zorder=3)

            # Bottom: fitness improvement
            if entry.get("fit_pct") is not None:
                ax_bot.hlines(y, 0, entry["fit_pct"],
                              colors=color, linewidths=1.1, alpha=0.75, linestyle="--")
                ax_bot.scatter(entry["fit_pct"], y,
                               color=color, s=18, zorder=3, marker="D")

    # ── Y-axis labels (both subplots) ─────────────────────────────────────────
    y_labels = [_y_label(b) for b in sorted_bases]
    ax_top.set_yticks(range(n))
    ax_top.set_yticklabels(y_labels, fontsize=7.5)
    ax_top.invert_yaxis()   # sharey propagates to ax_bot
    _yb, _yt = ax_top.get_ylim()
    ax_top.set_ylim(_yb, _yt - 0.4)  # extra top margin beneath subplot labels

    # Explicitly show labels on the bottom subplot too
    ax_bot.tick_params(labelleft=True)
    ax_bot.set_yticklabels(y_labels, fontsize=7.5)

    def _color_labels(ax):
        for tick, base in zip(ax.get_yticklabels(), sorted_bases):
            group = any(_is_group(base, e["metrics"]) for e in combined[base].values())
            tick.set_color("#1565C0" if group else "#616161")

    _color_labels(ax_top)
    _color_labels(ax_bot)

    # ── Top subplot axes ──────────────────────────────────────────────────────
    ax_top.set_xlim(0, uniq_max)
    ax_top.set_xlabel("% unique users no longer unique when metric removed", fontsize=9)
    ax_top.grid(True, axis="x", linestyle="--", alpha=0.18, zorder=0)
    ax_top.axvline(0, color="black", linewidth=0.5)
    ax_top.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax_top.set_title("Logical Metric Removal — Uniqueness & Cohort Fitness", fontsize=11)
    ax_top.text(0.01, 0.99, "Uniqueness Improvement", transform=ax_top.transAxes,
                fontsize=8.5, fontweight="bold", va="top", color="#333333")

    # ── Bottom subplot axes ───────────────────────────────────────────────────
    ax_bot.set_xlim(0, fit_max)
    ax_bot.set_xlabel("cohort fitness improvement (×100)",
                      fontsize=9, color="#555555")
    ax_bot.text(0.01, 0.99, "Cohort Fitness Improvement", transform=ax_bot.transAxes,
                fontsize=8.5, fontweight="bold", va="top", color="#333333")
    ax_bot.grid(True, axis="x", linestyle="--", alpha=0.18, zorder=0)
    ax_bot.axvline(0, color="black", linewidth=0.5)
    ax_bot.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax_bot.tick_params(axis="x", labelsize=8, colors="#333333")

    # ── Legend (top subplot) ──────────────────────────────────────────────────
    fp_handles = [
        mlines.Line2D([0], [0], color=FP_COLORS.get(fp, "#888"), marker="o",
                      markersize=5, linewidth=1.4, label=fp)
        for fp in fp_names if fp in FP_COLORS
    ]
    style_handles = [
        mpatches.Patch(color="#1565C0", label="Logical group (label)"),
        mpatches.Patch(color="#616161", label="Individual metric (label)"),
    ]
    ax_top.legend(handles=fp_handles + style_handles, fontsize=7, loc="lower right")
    fig.text(0.5, 0, "Shown if uniqueness ≥ 5% or fitness improvement ≥ 50%.",
             ha="center", va="bottom", fontsize=7, color="#757575", style="italic")

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.08)
    out_path = os.path.join(config.OUTPUT_FOLDER, "lmr_graph_combined_fitness_v2.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  LMR fitness v2 graph written to {out_path}")

    img_dir = "/work/sandbox-cache/000-img"
    if os.path.isdir(img_dir):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(img_dir, f"{ts}_lmr_combined_fitness_v2.png")
        shutil.copy(out_path, dst)
        print(f"  Copied to {dst}")


# =============================================================================
# Top-level runners (called from analyze.py)
# =============================================================================

def run_lmr_analysis(lmr_fingerprints, lmr_unit_lists, lmr_baselines):
    """Run LMR output for each fingerprinter then generate combined graphs.

    lmr_baselines: dict[fp_name → (num_users, num_unique_users, baseline_fitness[, hhi2[, p50]])]
    """
    completed = []
    for fp_name, unit_list in lmr_unit_lists.items():
        if fp_name not in lmr_baselines:
            print(f"WARNING: No baseline for {fp_name}, skipping LMR output")
            continue
        _bl = lmr_baselines[fp_name]
        num_users, num_unique_users, baseline_fitness = _bl[0], _bl[1], _bl[2]
        baseline_fitness_hhi2 = _bl[3] if len(_bl) > 3 else None
        baseline_p50 = _bl[4] if len(_bl) > 4 else None
        output_lmr(
            lmr_fingerprints[fp_name],
            unit_list,
            num_users,
            num_unique_users,
            baseline_fitness,
            fp_name,
            baseline_fitness_hhi2=baseline_fitness_hhi2,
            baseline_p50=baseline_p50,
        )
        completed.append(fp_name)
    if completed:
        graph_lmr_combined(completed)
        graph_lmr_combined_fitness_v1(completed)
        graph_lmr_combined_fitness_v2(completed)


