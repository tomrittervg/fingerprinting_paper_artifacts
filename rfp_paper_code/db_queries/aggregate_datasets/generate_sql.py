#!/usr/bin/env python3
"""
Generate .sql files from .sql.template files in this directory.

Templates use {{PLACEHOLDER}} substitution. Run with --help for options.

Parameters filled into templates:
  DATASET           BigQuery destination dataset name
  SCHEMA            Minimum submission_schema version integer
  START_DATE        Start date YYYY-MM-DD (inclusive)
  END_DATE          End date YYYY-MM-DD (exclusive)
  METRICS_TO_IGNORE SQL-formatted list of metric names to exclude from
                    co-occurrence analyses (process_13, x_by_y_groupings_14)
  TBL_SUFFIX        Per-OS table suffix (e.g. _Windows, _Android)
  OS_FILTER         WHERE clause fragment to filter raw data by OS
  SOURCE_TABLE      Source telemetry table for the OS

Each template is rendered once per OS (Windows, Mac, Linux, Android),
producing per-OS SQL files (e.g. process_05_Windows.sql).

process_02 creates LatestSubmission (one row per client) from raw telemetry.
process_02_03.sql.template creates Exploded (deduplicated via JOIN to
LatestSubmission), rendered as process_03_{OS}.sql.

Pipeline execution order (two-phase, all 4 OSes in parallel):
  Phase 1 (per OS):
    process_00 (shared, once)
    process_01_{OS} (Exploded schema)
    process_02 (global LatestSubmission — dedup across all OSes/sources)
    process_03_{OS} (Exploded, deduplicated via JOIN to global LatestSubmission)
    process_05_{OS} (DoubleExploded schema)
    process_06_{OS} through process_11_{OS} (UNPIVOT into DoubleExploded)
    process_09b_{OS} (classify CPU/GPU models)
    process_12_{OS} (MetricSubmissionCounts)
    process_13_{OS} (MetricValueCounts)
    detect_identical_metrics_{OS}
  Phase 2 (per OS, after reviewing detected duplicates):
    x_groupings_13_{OS}, x_by_y_groupings_14_{OS}, validate_{OS}

Between phases, run detect_identical_metrics_{OS}.sql per OS and export
the dropped metrics, then re-run generate_sql.py with --identical-drop-{os}
to add them to the per-OS exclusion list before generating Phase 2 scripts.

Usage:
  python3 generate_sql.py
  python3 generate_sql.py --dataset my_dataset --schema 38 --start-date 2026-03-01 --end-date 2026-04-01
  python3 generate_sql.py --os Windows   # generate for one OS only
  python3 generate_sql.py --identical-drop-windows win_drops.txt --identical-drop-linux linux_drops.txt
  python3 generate_sql.py --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

SOURCE_TABLE_DESKTOP = "mozdata.firefox_desktop.user_characteristics"
SOURCE_TABLE_FENIX   = "mozdata.fenix.user_characteristics"

# OS configurations: each OS maps to one source table and one filter expression.
# Windows/Mac/Linux come from Desktop; Android comes from Fenix.
OS_CONFIGS = [
    {
        "name": "Windows",
        "suffix": "_Windows",
        "source": SOURCE_TABLE_DESKTOP,
        "os_filter": "AND d.metrics.string.characteristics_os_name = 'WINNT'",
    },
    {
        "name": "Mac",
        "suffix": "_Mac",
        "source": SOURCE_TABLE_DESKTOP,
        "os_filter": "AND d.metrics.string.characteristics_os_name = 'Darwin'",
    },
    {
        "name": "Linux",
        "suffix": "_Linux",
        "source": SOURCE_TABLE_DESKTOP,
        "os_filter": "AND d.metrics.string.characteristics_os_name = 'Linux'",
    },
    {
        "name": "Android",
        "suffix": "_Android",
        "source": SOURCE_TABLE_FENIX,
        "os_filter": "",  # all Fenix data is Android
    },
]

# Default list of high-cardinality / non-correlatable metrics excluded from
# cross-metric co-occurrence analyses (process_13, x_by_y_groupings_14).
DEFAULT_IGNORE_METRICS = [
    "combined_fonts_variants_nonallowlisted_hash",
    "fonts_variant_a_nonallowlisted",
    "screen_web_inner",
    "screen_web_outer",
    "screens",
    "screen_web_inner_diff",
    "screen_web_outer_diff",
    "ice_sd",
    "fonts_fpjs_nonallowlisted",
    "missing_fonts",
    "color_accentcolor",
    "js_errors",
    "screen_web_avail",
    "fonts_variant_b_nonallowlisted",
    "combined_fonts_variants_allowlisted_hash",
    "fonts_variant_a_allowlisted",
    "screen_primary_avail",
    "voices_sample",
    "clientrects_range_gcr_12",
    "clientrects_range_gcr_03",
    "clientrects_range_gcr_01",
    "clientrects_range_gcr_09",
    "clientrects_range_gcr_08",
    "clientrects_range_gcr_04",
    "clientrects_range_gcr_02",
    "clientrects_range_gcr_11",
    "clientrects_range_gcr_10",
    "clientrects_range_gcr_05",
    "clientrects_range_gcr_07",
    "clientrects_range_gcr_06",
    "clientrects_emoji_02",
    "clientrects_emoji_03",
    "clientrects_emoji_04",
    "clientrects_emoji_06",
    "clientrects_emoji_05",
    "clientrects_emoji_01",
    "screen_web_resolution",
    "audio_frames",
    "screen_primary_resolution",
    "clientrects_range_gbcr_08",
    "clientrects_range_gbcr_03",
    "clientrects_range_gbcr_01",
    "fonts_variant_e_nonallowlisted",
    "storage_quota",
    "screen_web_inner_width_diff",
    "screen_web_outer_width_diff",
    "machine_model_name",
    "combined_canvas_hardware_hash",
    "combined_canvas_software_hash",
    "gl_renderer_raw",
    "gl2_renderer_raw",
    "voices_local_ssdeep",
    "voices_all_ssdeep",
    "voices_sha1",
    "gamepads",
    "css_system_colors",
    "combined_css_colors_hash",
    "color_selecteditem",
    "css_color_accentcolor",
    "color_highlight",
    "css_color_highlight",
    # Media device counts — peripheral inventory, uncorrelated with display/GPU/fonts
    "camera_count",
    "microphone_count",
    "speaker_count",
    "group_count",
    "group_count_wo_speakers",
    # Sensor data — mobile sensor precision, no cross-metric mechanism
    "motion_decimals",
    "motion_freq",
    "orientation_angle",
    "orientation_decimals",
    "orientation_freq",
    "orientationabs_decimals",
    # Pointer/stylus — input device specifics
    "pointer_height",
    "pointer_width",
    "pointer_tiltx",
    "pointer_tilty",
    "pointer_twist",
    # Pipeline metadata — not fingerprinting signals
    "submission_schema",
    "build_date",
    "channel",
    "errors",
    # ICE/WebRTC — network topology
    "ice_order",
    # Audio detail — fingerprint hashes capture the signal; these are noise
    "audio_unique_samples",
    "audio_channels",
    "audio_rate",
    # User behavior
    "zoom_count",
    # Constant within per-OS tables
    "os_name",
    # Individual clientrect metrics (combined hashes kept)
    "clientrects_element_gbcr_01", "clientrects_element_gbcr_02", "clientrects_element_gbcr_03",
    "clientrects_element_gbcr_04", "clientrects_element_gbcr_05", "clientrects_element_gbcr_06",
    "clientrects_element_gbcr_07", "clientrects_element_gbcr_08", "clientrects_element_gbcr_09",
    "clientrects_element_gbcr_10", "clientrects_element_gbcr_11", "clientrects_element_gbcr_12",
    "clientrects_element_gcr_01", "clientrects_element_gcr_02", "clientrects_element_gcr_03",
    "clientrects_element_gcr_04", "clientrects_element_gcr_05", "clientrects_element_gcr_06",
    "clientrects_element_gcr_07", "clientrects_element_gcr_08", "clientrects_element_gcr_09",
    "clientrects_element_gcr_10", "clientrects_element_gcr_11", "clientrects_element_gcr_12",
    "clientrects_emoji_font_family",
    "clientrects_ghost_dimensions",
    "clientrects_known_dimensions",
    "clientrects_range_gbcr_02", "clientrects_range_gbcr_04", "clientrects_range_gbcr_05",
    "clientrects_range_gbcr_06", "clientrects_range_gbcr_07", "clientrects_range_gbcr_09",
    "clientrects_range_gbcr_10", "clientrects_range_gbcr_11", "clientrects_range_gbcr_12",
    "clientrects_text_font_family",
    # Individual wgpu params (combined hash, fallback adapter, missing features kept)
    "wgpu_maxbindgroups", "wgpu_maxbindgroupsplusvertexbuffers",
    "wgpu_maxbindingsperbindgroup", "wgpu_maxbuffersize",
    "wgpu_maxcolorattachmentbytespersample", "wgpu_maxcolorattachments",
    "wgpu_maxcomputeinvocationsperworkgroup", "wgpu_maxcomputeworkgroupsizex",
    "wgpu_maxcomputeworkgroupsizey", "wgpu_maxcomputeworkgroupsizez",
    "wgpu_maxcomputeworkgroupsperdimension", "wgpu_maxcomputeworkgroupstoragesize",
    "wgpu_maxdynamicstoragebuffersperpipelinelayout", "wgpu_maxdynamicuniformbuffersperpipelinelayout",
    "wgpu_maxinterstageshadervariables", "wgpu_maxsampledtexturespershaderstage",
    "wgpu_maxsamplerspershaderstage", "wgpu_maxstoragebufferbindingsize",
    "wgpu_maxstoragebufferspershaderstage", "wgpu_maxstoragetexturespershaderstage",
    "wgpu_maxtexturearraylayers", "wgpu_maxtexturedimension1d",
    "wgpu_maxtexturedimension2d", "wgpu_maxtexturedimension3d",
    "wgpu_maxuniformbufferbindingsize", "wgpu_maxuniformbufferspershaderstage",
    "wgpu_maxvertexattributes", "wgpu_maxvertexbufferarraystride",
    "wgpu_maxvertexbuffers", "wgpu_minstoragebufferoffsetalignment",
    "wgpu_minuniformbufferoffsetalignment",
    # Redundant with combined hashes or low-value for correlation
    "gl2_params_extensions_software",
    "gl_params_extensions_software",
    "gl2_params_extensions",
    "gl_params_extensions",
    "gl2_params_software",
    "gl2_params",
    "gl_params_software",
    "gl_params",
    "combined_media_capabilities_hash",
    "combined_mathml_hash",
    "mathml_diag_values",
    "math_ops_fdlibm_2",
    "math_ops_fdlibm",
    "math_ops",
    "css_system_fonts",
]

# Per-OS additions to the ignore list. These are appended to DEFAULT_IGNORE_METRICS
# for the specified OS only (e.g. metrics that are high-cardinality on Linux but
# not on other platforms).
PER_OS_IGNORE_METRICS = {
    "Windows": [],
    "Mac": [],
    "Linux": [
        "combined_webgl2_params_hash",
        "webgl2_params_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS",
        "webgl2_params_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS",
        "webgl2_params_MAX_UNIFORM_BLOCK_SIZE",
        "combined_clientrects_emoji_hash",
        "combined_clientrects_range_gcr_hash",
    ],
    "Android": [
        "prefs_intl_accept_languages",
        "languages",
    ],
}

# x_by_y chunk boundaries: the self-join is split into ~20 chunks by d1.metric
# range to keep individual query size manageable. Optimized for Windows (largest OS).
# Chunk 1 creates the table, chunks 2+ insert into it.
X_BY_Y_CHUNK_BOUNDARIES = [
    "canvasdata10",
    "canvasdata10software",
    "canvasdata12_fingerprintjs1",
    "canvasdata12_fingerprintjs1software",
    "canvasdata6",
    "canvasdata8",
    "canvasdata9",
    "canvasdata9software",
    "combined_clientrects_element_gbcr_hash",
    "combined_clientrects_element_gcr_hash",
    "combined_clientrects_emoji_hash",
    "combined_clientrects_range_gbcr_hash",
    "combined_clientrects_range_gcr_hash",
    "combined_mathml_hash",
    "font_name_monospace_western",
    "gl_renderer_raw_software",
    "languages",
    "outer_height",
    "screen_primary_avail_top",
    "webgl2_renderer_model",
]

# Templates that are rendered once globally (not per-OS)
GLOBAL_TEMPLATES = {"process_00.sql.template", "process_02.sql.template"}

# Templates rendered in chunks (special handling in rendering loop)
CHUNKED_TEMPLATES = {"x_by_y_groupings_14.sql.template"}

# Templates eliminated by per-OS split (their purpose is now served by
# per-OS tables directly)
ELIMINATED_TEMPLATES = {
    "process_14.sql.template",             # MetricValueCountsByOS_tbl — redundant
    "x_by_os_by_y_groupings_15.sql.template",  # x_by_os_by_y — redundant
}


def format_metrics_to_ignore(metrics: list[str]) -> str:
    """Format metric names as the body of a SQL IN (...) clause."""
    return ",\n".join(f"  '{m}'" for m in metrics)


def build_ignore_placeholders(metrics: list[str], dataset: str = "", tbl_suffix: str = "") -> dict:
    """Build all METRICS_TO_IGNORE-related template placeholders.

    Returns a dict of placeholder -> SQL fragment, handling the empty-list
    case gracefully (empty WHERE clauses, no UNNEST checks, etc.).
    """
    result = {
        "METRICS_TO_IGNORE": format_metrics_to_ignore(metrics),
    }
    if metrics:
        in_clause = format_metrics_to_ignore(metrics)
        result["METRICS_TO_IGNORE_WHERE"] = f"WHERE metric NOT IN (\n{in_clause}\n)"
        result["METRICS_TO_IGNORE_WHERE_D1_D2"] = (
            f"WHERE d1.metric NOT IN (\n{in_clause}\n)\n"
            f"AND d2.metric NOT IN (\n{in_clause}\n)"
        )
        # Validate checks that use UNNEST or IN on the ignore list
        # V-11 removed: MetricValueCounts no longer filters by exclusion list
        result["VALIDATE_IGNORE_CHECKS_11_12"] = (
            "-- V-12: Ignored metrics present in MetricSubmissionCounts{tbl_suffix}_tbl\n"
            "SELECT 'V-12', 'Ignored metrics all exist in MetricSubmissionCounts{tbl_suffix}_tbl',\n"
            "  CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,\n"
            "  CASE WHEN COUNT(*) = 0 THEN NULL\n"
            "    ELSE CONCAT(CAST(COUNT(*) AS STRING), ' ignored metric(s) missing: ',\n"
            "      STRING_AGG(metric ORDER BY metric LIMIT 5)) END\n"
            f"FROM UNNEST([\n{in_clause}\n]) AS metric\n"
            "WHERE metric NOT IN (SELECT metric FROM {dataset}.MetricSubmissionCounts{tbl_suffix}_tbl)\n"
            "\nUNION ALL\n"
        )
        result["VALIDATE_IGNORE_CHECKS_21_22"] = (
            "-- V-21: Every name in METRICS_TO_IGNORE exists in the data\n"
            "SELECT 'V-21', 'All METRICS_TO_IGNORE names exist in MetricSubmissionCounts{tbl_suffix}_tbl',\n"
            "  CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,\n"
            "  CASE WHEN COUNT(*) = 0 THEN NULL\n"
            "    ELSE CONCAT(CAST(COUNT(*) AS STRING), ' phantom name(s): ',\n"
            "      STRING_AGG(metric ORDER BY metric LIMIT 5)) END\n"
            f"FROM UNNEST([\n{in_clause}\n]) AS metric\n"
            "WHERE metric NOT IN (SELECT metric FROM {dataset}.MetricSubmissionCounts{tbl_suffix}_tbl)\n"
            "\nUNION ALL\n\n"
            "-- V-22: Ignored metrics absent from x_by_y_tbl\n"
            "SELECT 'V-22', 'Ignored metrics absent from UserCharacteristics{tbl_suffix}_x_by_y_tbl',\n"
            "  CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,\n"
            "  CASE WHEN COUNT(*) = 0 THEN NULL\n"
            "    ELSE CONCAT(CAST(COUNT(*) AS STRING), ' rows with ignored metric') END\n"
            "FROM {dataset}.UserCharacteristics{tbl_suffix}_x_by_y_tbl\n"
            f"WHERE metric1 IN (\n{in_clause}\n) OR metric2 IN (\n{in_clause}\n)\n"
            "\nUNION ALL\n"
        )
    else:
        result["METRICS_TO_IGNORE_WHERE"] = ""
        result["METRICS_TO_IGNORE_WHERE_D1_D2"] = ""
        result["VALIDATE_IGNORE_CHECKS_11_12"] = (
            "-- V-12: Skipped (no METRICS_TO_IGNORE configured)\n"
            "SELECT 'V-12', 'Ignored metrics checks skipped (empty ignore list)', 'SKIP', NULL\n"
            "\nUNION ALL\n"
        )
        result["VALIDATE_IGNORE_CHECKS_21_22"] = (
            "-- V-21/V-22: Skipped (no METRICS_TO_IGNORE configured)\n"
            "SELECT 'V-21', 'Ignored metrics checks skipped (empty ignore list)', 'SKIP', NULL\n"
            "UNION ALL\n"
            "SELECT 'V-22', 'Ignored metrics checks skipped (empty ignore list)', 'SKIP', NULL\n"
            "\nUNION ALL\n"
        )
    # Substitute {dataset} and {tbl_suffix} in generated validate check strings
    for key in ("VALIDATE_IGNORE_CHECKS_11_12", "VALIDATE_IGNORE_CHECKS_21_22"):
        if key in result:
            result[key] = result[key].format(dataset=dataset, tbl_suffix=tbl_suffix)
    return result


def render(content: str, params: dict, filename: str = "") -> str:
    for key, value in params.items():
        content = content.replace("{{" + key + "}}", value)
    remaining = re.findall(r"\{\{[A-Z_]+\}\}", content)
    if remaining:
        label = f" in {filename}" if filename else ""
        print(f"WARNING: unreplaced placeholders{label}: {remaining}", file=sys.stderr)
    return content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate per-OS .sql files from .sql.template files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset", default="aggregatedata2",
        help="BigQuery destination dataset (default: aggregatedata2)",
    )
    parser.add_argument(
        "--schema", type=int, default=37,
        help="Minimum submission_schema version (default: 37)",
    )
    parser.add_argument(
        "--start-date", default="2026-03-25",
        help="Start date YYYY-MM-DD inclusive (default: 2026-03-25)",
    )
    parser.add_argument(
        "--end-date", default="2026-04-17",
        help="End date YYYY-MM-DD exclusive (default: 2026-04-17)",
    )
    parser.add_argument(
        "--ignore-metrics", default="",
        help="Additional metrics to exclude, comma-separated (appended to defaults)",
    )
    parser.add_argument(
        "--replace-metrics", default="",
        help="Replace the default exclusion list entirely, comma-separated",
    )
    # Per-OS identical-drop files
    for os_cfg in OS_CONFIGS:
        os_lower = os_cfg["name"].lower()
        parser.add_argument(
            f"--identical-drop-{os_lower}", default=None, metavar="FILE",
            help=f"File with metric names to drop for {os_cfg['name']} (one per line), "
                 f"typically produced by detect_identical_metrics_{os_cfg['name']}.sql.",
        )
    parser.add_argument(
        "--identical-drop", default=None, metavar="FILE",
        help="File with metric names to drop for ALL OSes (one per line). "
             "Per-OS files take precedence if both are provided.",
    )
    parser.add_argument(
        "--os", default=None,
        help="Generate for a single OS only (e.g. --os Windows)",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to write .sql files (default: same directory as templates)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be generated without writing any files",
    )
    args = parser.parse_args()

    # Determine which OSes to generate for
    if args.os:
        os_names = [c["name"] for c in OS_CONFIGS]
        if args.os not in os_names:
            print(f"ERROR: --os must be one of {os_names}", file=sys.stderr)
            sys.exit(1)
        active_os_configs = [c for c in OS_CONFIGS if c["name"] == args.os]
    else:
        active_os_configs = list(OS_CONFIGS)

    # Build base ignored-metrics list
    if args.replace_metrics:
        base_metrics = [m.strip() for m in args.replace_metrics.split(",") if m.strip()]
    else:
        base_metrics = list(DEFAULT_IGNORE_METRICS)
        if args.ignore_metrics:
            base_metrics.extend(m.strip() for m in args.ignore_metrics.split(",") if m.strip())

    # Append shared identical-metric drops
    if args.identical_drop:
        drop_path = Path(args.identical_drop)
        if not drop_path.exists():
            print(f"ERROR: --identical-drop file not found: {drop_path}", file=sys.stderr)
            sys.exit(1)
        dropped = [line.strip() for line in drop_path.read_text().splitlines() if line.strip()]
        new_drops = [m for m in dropped if m not in base_metrics]
        if new_drops:
            base_metrics.extend(new_drops)
            print(f"Added {len(new_drops)} identical-metric drops from {drop_path}: {new_drops}")

    # Build per-OS metrics lists (base + per-OS hardcoded + per-OS drops)
    os_metrics = {}
    for os_cfg in active_os_configs:
        os_lower = os_cfg["name"].lower()
        os_specific = list(base_metrics)
        # Add per-OS hardcoded exclusions
        for m in PER_OS_IGNORE_METRICS.get(os_cfg["name"], []):
            if m not in os_specific:
                os_specific.append(m)
        drop_file = getattr(args, f"identical_drop_{os_lower}", None)
        if drop_file:
            drop_path = Path(drop_file)
            if not drop_path.exists():
                print(f"ERROR: --identical-drop-{os_lower} file not found: {drop_path}", file=sys.stderr)
                sys.exit(1)
            dropped = [line.strip() for line in drop_path.read_text().splitlines() if line.strip()]
            new_drops = [m for m in dropped if m not in os_specific]
            if new_drops:
                os_specific.extend(new_drops)
                print(f"Added {len(new_drops)} identical-metric drops for {os_cfg['name']} from {drop_path}: {new_drops}")
        os_metrics[os_cfg["name"]] = os_specific

    # Load the schema-version-aware WebGL params SQL (generated by gen_webgl_sql.py)
    webgl_params_path = SCRIPT_DIR / "webgl_params_versioned.sql"
    webgl_params_sql = webgl_params_path.read_text() if webgl_params_path.exists() else ""
    if not webgl_params_sql:
        print("WARNING: webgl_params_versioned.sql not found; WebGL params will be empty", file=sys.stderr)

    output_dir = Path(args.output_dir) if args.output_dir else SCRIPT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    templates = sorted(SCRIPT_DIR.glob("*.sql.template"))
    if not templates:
        print("No .sql.template files found.", file=sys.stderr)
        sys.exit(1)

    for tpl in templates:
        # Skip eliminated templates
        if tpl.name in ELIMINATED_TEMPLATES:
            if args.dry_run:
                print(f"[dry-run] SKIP {tpl.name} (eliminated by per-OS split)")
            else:
                print(f"SKIP {tpl.name} (eliminated by per-OS split)")
            continue

        raw = tpl.read_text()

        # Global templates: render once without OS suffix
        if tpl.name in GLOBAL_TEMPLATES:
            params = {
                "DATASET":              f"`{args.dataset}`",
                "SCHEMA":               str(args.schema),
                "START_DATE":           args.start_date,
                "END_DATE":             args.end_date,
                "SOURCE_TABLE_DESKTOP": SOURCE_TABLE_DESKTOP,
                "SOURCE_TABLE_FENIX":   SOURCE_TABLE_FENIX,
            }
            content = render(raw, params, tpl.name)
            out_path = output_dir / tpl.stem
            if args.dry_run:
                print(f"[dry-run] {tpl.name} -> {out_path.name}  (global)")
            else:
                out_path.write_text(content)
                print(f"{tpl.name} -> {out_path.name}  (global)")
            continue

        # Per-OS templates: render once per active OS
        for os_cfg in active_os_configs:
            os_name = os_cfg["name"]
            os_suffix = os_cfg["suffix"]
            dataset = f"`{args.dataset}`"

            ignore = build_ignore_placeholders(os_metrics[os_name], dataset, os_suffix)
            params = {
                "DATASET":          dataset,
                "SCHEMA":           str(args.schema),
                "START_DATE":       args.start_date,
                "END_DATE":         args.end_date,
                **ignore,
                "WEBGL_PARAMS_SQL": webgl_params_sql,
                "TBL_SUFFIX":       os_suffix,
                "OS_FILTER":        os_cfg["os_filter"],
                "SOURCE_TABLE":     os_cfg["source"],
            }

            if tpl.name in CHUNKED_TEMPLATES:
                # Render once per chunk: chunk 1 creates, chunks 2+ insert.
                tbl_name = f"{dataset}.UserCharacteristics{os_suffix}_x_by_y_tbl"
                n_chunks = len(X_BY_Y_CHUNK_BOUNDARIES) + 1
                for chunk_idx in range(n_chunks):
                    chunk_params = dict(params)

                    # Table action: CREATE for chunk 1, INSERT for rest
                    if chunk_idx == 0:
                        chunk_params["X_BY_Y_TBL_ACTION"] = \
                            f"CREATE OR REPLACE TABLE {tbl_name} AS"
                    else:
                        chunk_params["X_BY_Y_TBL_ACTION"] = \
                            f"INSERT INTO {tbl_name}"

                    # Metric1 range filter
                    has_ignore = bool(os_metrics[os_name])
                    conjunction = "AND" if has_ignore else "WHERE"
                    if chunk_idx == 0:
                        bound = X_BY_Y_CHUNK_BOUNDARIES[0]
                        chunk_params["METRIC1_CHUNK_FILTER"] = \
                            f"{conjunction} d1.metric < '{bound}'"
                    elif chunk_idx == n_chunks - 1:
                        bound = X_BY_Y_CHUNK_BOUNDARIES[-1]
                        chunk_params["METRIC1_CHUNK_FILTER"] = \
                            f"{conjunction} d1.metric >= '{bound}'"
                    else:
                        lo = X_BY_Y_CHUNK_BOUNDARIES[chunk_idx - 1]
                        hi = X_BY_Y_CHUNK_BOUNDARIES[chunk_idx]
                        chunk_params["METRIC1_CHUNK_FILTER"] = \
                            f"{conjunction} d1.metric >= '{lo}' AND d1.metric < '{hi}'"

                    chunk_num = chunk_idx + 1
                    out_name = f"x_by_y_groupings_14_{os_name}_chunk_{chunk_num:02d}.sql"
                    content = render(raw, chunk_params, tpl.name)
                    out_path = output_dir / out_name
                    if args.dry_run:
                        print(f"[dry-run] {tpl.name} -> {out_name}  ({os_name}, chunk {chunk_num}/{n_chunks})")
                    else:
                        out_path.write_text(content)
                        print(f"{tpl.name} -> {out_name}  ({os_name}, chunk {chunk_num}/{n_chunks})")

            elif tpl.name == "process_02_03.sql.template":
                # Renders as process_03 (Exploded with dedup JOIN to LatestSubmission).
                out_name = f"process_03_{os_name}.sql"
                content = render(raw, params, tpl.name)
                out_path = output_dir / out_name
                if args.dry_run:
                    print(f"[dry-run] {tpl.name} -> {out_name}  ({os_name})")
                else:
                    out_path.write_text(content)
                    print(f"{tpl.name} -> {out_name}  ({os_name})")

            else:
                # Standard per-OS rendering: append OS name to output filename
                base_name = tpl.stem  # e.g. "process_05.sql"
                stem = base_name.removesuffix(".sql")  # e.g. "process_05"
                out_name = f"{stem}_{os_name}.sql"
                content = render(raw, params, tpl.name)
                out_path = output_dir / out_name
                if args.dry_run:
                    print(f"[dry-run] {tpl.name} -> {out_name}  ({os_name})")
                else:
                    out_path.write_text(content)
                    print(f"{tpl.name} -> {out_name}  ({os_name})")


if __name__ == "__main__":
    main()
