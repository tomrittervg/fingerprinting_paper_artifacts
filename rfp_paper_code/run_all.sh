#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run_all.sh — Full pipeline: analyze → gen_outputs → gen_gfx
#
# Runs the analysis configs, post-processes pickles into CSVs, and
# generates paper figures. Uses simulated-cache and simulated-output
# by default.
#
# Usage:
#   ./run_all.sh                  # run everything
#   ./run_all.sh --skip-data      # skip analyze.py, just re-run outputs/graphics
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CACHE="${RFP_CACHE_DIR:-./simulated-cache}"
OUT_BASE="${RFP_OUTPUT_DIR:-./simulated-output}"
PYTHON="${PYTHON:-python3}"
SKIP_DATA="${1:---run-data}"

export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/mpl}"
mkdir -p "$MPLCONFIGDIR"

# =============================================================================
# Phase 1: Run analyze.py configs (via run.sh)
# =============================================================================
if [[ "$SKIP_DATA" != "--skip-data" ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  Phase 1: Running analyze.py configs                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    COMMON="--cache-dir $CACHE --per-os=true --force --partition-width 1"

    run_config() {
        local name="$1"; shift
        local config="$1"; shift
        local outdir="$OUT_BASE/$name"
        echo "  [$name] $config → $outdir"
        ./run.sh -o "$outdir" -c "$config" $COMMON "$@"
    }

    run_config shannon_hhi     configs/paper_indvmetrics_shannon_hhi.py
    run_config smr_fpjsV2      configs/paper_indvmetrics_smr_fpjsV2_realistic.py
    run_config smr_akamaiV2    configs/paper_indvmetrics_smr_akamaiV2_realistic.py
    run_config smr_signifyd    configs/paper_indvmetrics_smr_signifyd_realistic.py
    run_config buckets         configs/fingerprint_buckets_realistic.py
    run_config exp_add         configs/paper_uniqueness_tables_additive_realistic.py
    run_config exp_ind         configs/paper_uniqueness_tables_individual_realistic.py
    run_config iterative_minmetrics_fpjsV2   configs/iterative_minmetrics_fpjsV2.py
    run_config iterative_minmetrics_akamaiV2 configs/iterative_minmetrics_akamaiV2.py
    run_config iterative_minmetrics_signifyd configs/iterative_minmetrics_signifyd.py
fi

# =============================================================================
# Discover output directories (analyze.py appends _<timestamp>)
# =============================================================================
find_output() {
    # Find the most recent output dir matching the pattern
    local pattern="$OUT_BASE/$1_*"
    local dir
    dir=$(ls -d $pattern 2>/dev/null | sort -r | head -1)
    if [[ -z "$dir" ]]; then
        echo "WARNING: no output found for $1 (looked for $pattern)" >&2
        return 1
    fi
    echo "$dir"
}

DIR_SHANNON=$(find_output shannon_hhi) || true
DIR_SMR_FPJS=$(find_output smr_fpjsV2) || true
DIR_SMR_AKAMAI=$(find_output smr_akamaiV2) || true
DIR_SMR_SIGNIFYD=$(find_output smr_signifyd) || true
DIR_BUCKETS=$(find_output buckets) || true
DIR_EXP_ADD=$(find_output exp_add) || true
DIR_EXP_IND=$(find_output exp_ind) || true
DIR_IMIN_FPJS=$(find_output iterative_minmetrics_fpjsV2) || true
DIR_IMIN_AKAMAI=$(find_output iterative_minmetrics_akamaiV2) || true
DIR_IMIN_SIGNIFYD=$(find_output iterative_minmetrics_signifyd) || true

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Phase 2: Post-processing (gen_outputs)                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

run_gen() {
    local script="$1"; shift
    echo "  $(basename $script) $@"
    "$PYTHON" "$script" "$@" || echo "    (returned non-zero, continuing)"
}

[[ -n "$DIR_SHANNON" ]]      && run_gen gen_outputs/gen_metrics_output.py "$DIR_SHANNON"
[[ -n "$DIR_SMR_FPJS" ]]     && run_gen gen_outputs/gen_smr_output.py "$DIR_SMR_FPJS"
[[ -n "$DIR_SMR_AKAMAI" ]]   && run_gen gen_outputs/gen_smr_output.py "$DIR_SMR_AKAMAI"
[[ -n "$DIR_SMR_SIGNIFYD" ]] && run_gen gen_outputs/gen_smr_output.py "$DIR_SMR_SIGNIFYD"
[[ -n "$DIR_BUCKETS" ]]      && run_gen gen_outputs/gen_alldata_output.py "$DIR_BUCKETS"
[[ -n "$DIR_EXP_ADD" ]]      && run_gen gen_outputs/gen_alldata_output.py "$DIR_EXP_ADD"
[[ -n "$DIR_EXP_ADD" ]]      && run_gen gen_outputs/gen_experiment_output.py "$DIR_EXP_ADD"
[[ -n "$DIR_EXP_IND" ]]      && run_gen gen_outputs/gen_alldata_output.py "$DIR_EXP_IND"
[[ -n "$DIR_EXP_IND" ]]      && run_gen gen_outputs/gen_experiment_output.py "$DIR_EXP_IND"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Phase 3: Paper figures (gen_gfx)                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

GFX_OUT="$OUT_BASE/gen_gfx_output"
mkdir -p "$GFX_OUT"

EXPERIMENTS_CSV="configs/experiments.csv"

# --- Individual metrics scatter ---
if [[ -n "$DIR_SHANNON" ]]; then
    echo "  indv_metrics/01_build_csv.py"
    INDV_ARGS="--shannon-hhi $DIR_SHANNON --output-dir $GFX_OUT"
    [[ -n "$DIR_SMR_FPJS" ]] && INDV_ARGS="$INDV_ARGS --smr $DIR_SMR_FPJS"
    "$PYTHON" gen_gfx/indv_metrics/01_build_csv.py $INDV_ARGS || true

    if [[ -f "$GFX_OUT/metric_table.csv" ]]; then
        echo "  indv_metrics/make_graph_scatter.py"
        "$PYTHON" gen_gfx/indv_metrics/make_graph_scatter.py \
            --csv "$GFX_OUT/metric_table.csv" \
            --output "$GFX_OUT/metric_scatter.png" || true
    fi
fi

# --- Experiment tables and graphs ---
if [[ -n "$DIR_EXP_ADD" && -n "$DIR_EXP_IND" ]]; then
    ANALYZE_DIRS="--analyze-dir $DIR_EXP_ADD $DIR_EXP_IND"

    for FP in FPJSv2_Realistic Signifyd_Realistic AkamaiV2_Realistic; do
        FP_LOWER=$(echo "$FP" | tr '[:upper:]' '[:lower:]' | sed 's/_realistic//')
        echo "  experiment_table/01_build_csv.py (${FP})"
        "$PYTHON" gen_gfx/experiment_table/01_build_csv.py \
            $ANALYZE_DIRS --experiments-csv "$EXPERIMENTS_CSV" \
            --output-dir "$GFX_OUT" --table3-fp "$FP" || true
        # Rename per-fingerprinter table3
        [[ -f "$GFX_OUT/table3_experiments.csv" ]] && \
            cp "$GFX_OUT/table3_experiments.csv" "$GFX_OUT/table3_experiments_${FP_LOWER}.csv"
    done

    echo "  experiment_table/04_graph.py"
    "$PYTHON" gen_gfx/experiment_table/04_graph.py \
        $ANALYZE_DIRS --experiments-csv "$EXPERIMENTS_CSV" \
        --output-dir "$GFX_OUT" --cohort || true

    echo "  experiment_table/05_graph.py"
    "$PYTHON" gen_gfx/experiment_table/05_graph.py \
        $ANALYZE_DIRS --experiments-csv "$EXPERIMENTS_CSV" \
        --output-dir "$GFX_OUT" --cohort || true
fi

# --- Fingerprint buckets plot ---
if [[ -n "$DIR_BUCKETS" ]]; then
    echo "  buckets/graph.py"
    "$PYTHON" gen_gfx/buckets/graph.py "$DIR_BUCKETS" || true
fi

# --- Iterative minmetrics ---
IMIN_DIRS=""
[[ -n "$DIR_IMIN_FPJS" ]]     && IMIN_DIRS="$IMIN_DIRS $DIR_IMIN_FPJS"
[[ -n "$DIR_IMIN_AKAMAI" ]]   && IMIN_DIRS="$IMIN_DIRS $DIR_IMIN_AKAMAI"
[[ -n "$DIR_IMIN_SIGNIFYD" ]] && IMIN_DIRS="$IMIN_DIRS $DIR_IMIN_SIGNIFYD"

if [[ -n "$IMIN_DIRS" ]]; then
    echo "  iminmetrics/viz_minmetrics_weighted_avg.py"
    "$PYTHON" gen_gfx/iminmetrics/viz_minmetrics_weighted_avg.py \
        $IMIN_DIRS "$GFX_OUT/viz_minmetrics_weighted_avg.png" || true

    echo "  iminmetrics/viz_minmetrics_all.py"
    "$PYTHON" gen_gfx/iminmetrics/viz_minmetrics_all.py \
        $IMIN_DIRS "$GFX_OUT/viz_minmetrics_all.png" || true

    echo "  fingerprinters_tables/build_table.py"
    "$PYTHON" gen_gfx/fingerprinters_tables/build_table.py \
        "$DIR_IMIN_FPJS" \
        --output "$GFX_OUT/fingerprinter_metrics_table.tex" || true

    echo "  iminmetrics_table/build_table.py"
    "$PYTHON" gen_gfx/iminmetrics_table/build_table.py \
        "$DIR_IMIN_FPJS" \
        --output "$GFX_OUT/iterative_top20_table.tex" || true
fi

# --- Summary ---
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Done                                                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Analysis outputs:  $OUT_BASE/*/"
echo "Graphics output:   $GFX_OUT/"
echo ""
if [[ -d "$GFX_OUT" ]]; then
    PNG_COUNT=$(find "$GFX_OUT" -name "*.png" 2>/dev/null | wc -l)
    CSV_COUNT=$(find "$GFX_OUT" -name "*.csv" 2>/dev/null | wc -l)
    echo "  $PNG_COUNT PNG(s), $CSV_COUNT CSV(s) generated."
fi
