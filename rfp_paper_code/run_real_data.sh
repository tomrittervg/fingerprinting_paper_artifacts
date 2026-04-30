#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run_real_data.sh — Generate paper figures from real production data
#
# Uses pre-computed output in real-output-data/ (CSVs from the ~25M user
# production run). Runs only gen_gfx scripts — no analyze.py needed.
#
# Usage:
#   ./run_real_data.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DATA="real-output-data"
PYTHON="${PYTHON:-python3}"
EXPERIMENTS_CSV="configs/experiments.csv"

export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/mpl}"
mkdir -p "$MPLCONFIGDIR"

GFX_OUT="$DATA"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Generating paper figures from real production data         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# --- Individual metrics scatter (Figure: indvmetrics) ---
echo "  indv_metrics/01_build_csv.py"
"$PYTHON" gen_gfx/indv_metrics/01_build_csv.py \
    --shannon-hhi "$DATA/shannon_hhi" \
    --smr "$DATA/smr_fpjsV2" \
    --output-dir "$GFX_OUT" || true

if [[ -f "$GFX_OUT/metric_table.csv" ]]; then
    echo "  indv_metrics/make_graph_scatter.py"
    "$PYTHON" gen_gfx/indv_metrics/make_graph_scatter.py \
        --csv "$GFX_OUT/metric_table.csv" \
        --output "$GFX_OUT/metric_scatter.png" || true
fi

# --- Experiment tables and graphs (Tables 1,3,5; Figures 5,6) ---
ANALYZE_DIRS="--analyze-dir $DATA/exp_add $DATA/exp_ind"

for FP in FPJSv2_Realistic Signifyd_Realistic AkamaiV2_Realistic; do
    FP_LOWER=$(echo "$FP" | tr '[:upper:]' '[:lower:]' | sed 's/_realistic//')
    echo "  experiment_table/01_build_csv.py (${FP})"
    "$PYTHON" gen_gfx/experiment_table/01_build_csv.py \
        $ANALYZE_DIRS --experiments-csv "$EXPERIMENTS_CSV" \
        --output-dir "$GFX_OUT" --table3-fp "$FP" || true
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

# --- Fingerprint buckets plot (Figure: sufficientdata) ---
echo "  buckets/graph.py"
"$PYTHON" gen_gfx/buckets/graph.py "$DATA/buckets" || true

# --- Iterative minmetrics (Figures: minmetrics, minmetrics_all) ---
IMIN_DIRS="$DATA/iterative_minmetrics_fpjsV2 $DATA/iterative_minmetrics_akamaiV2 $DATA/iterative_minmetrics_signifyd"

echo "  iminmetrics/viz_minmetrics_weighted_avg.py"
"$PYTHON" gen_gfx/iminmetrics/viz_minmetrics_weighted_avg.py \
    $IMIN_DIRS "$GFX_OUT/viz_minmetrics_weighted_avg.png" || true

echo "  iminmetrics/viz_minmetrics_all.py"
"$PYTHON" gen_gfx/iminmetrics/viz_minmetrics_all.py \
    $IMIN_DIRS "$GFX_OUT/viz_minmetrics_all.png" || true

# --- Fingerprinter metrics table (Table: fingerprinter_metrics) ---
echo "  fingerprinters_tables/build_table.py"
"$PYTHON" gen_gfx/fingerprinters_tables/build_table.py \
    "$DATA/iterative_minmetrics_fpjsV2" \
    --output "$GFX_OUT/fingerprinter_metrics_table.tex" || true

# --- Iterative top-20 table (Table: iterative_top20_by_os) ---
echo "  iminmetrics_table/build_table.py"
"$PYTHON" gen_gfx/iminmetrics_table/build_table.py \
    "$DATA/iterative_minmetrics_fpjsV2" \
    --output "$GFX_OUT/iterative_top20_table.tex" || true

# --- Summary ---
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Done                                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Output: $GFX_OUT/"
echo ""
if [[ -d "$GFX_OUT" ]]; then
    PNG_COUNT=$(find "$GFX_OUT" -name "*.png" 2>/dev/null | wc -l)
    CSV_COUNT=$(find "$GFX_OUT" -name "*.csv" 2>/dev/null | wc -l)
    TEX_COUNT=$(find "$GFX_OUT" -name "*.tex" 2>/dev/null | wc -l)
    echo "  $PNG_COUNT PNG(s), $CSV_COUNT CSV(s), $TEX_COUNT LaTeX file(s) generated."
fi
