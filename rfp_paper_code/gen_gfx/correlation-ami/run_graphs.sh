#!/usr/bin/env bash
# =============================================================================
# run_graphs.sh — Generate per-OS correlation visualization PNGs.
#
# Usage:
#   ./run_graphs.sh [--accepted | --all]
#
#   --accepted  (default) Run only accepted/promoted invocations
#   --all       Run all invocations, including experimental ones
#
# Runs each visualization script once per OS (Mac, Android, Linux, Windows),
# outputting to per-OS subdirectories.
#
# Parameters can be overridden via environment variables.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# =============================================================================
# Parameters
# =============================================================================
CORR_BASE="${CORR_BASE:-/work/sandbox-analyses/final-range}"
ALLOWLIST="${CORR_ALLOWLIST:-/work/code/configs/metadata_metric_name_mapping.txt}"
ANALYZE_DIR="${CORR_ANALYZE_DIR:-/work/sandbox-analyses/final-range/shannon_hhi_final_1776420279}"
OUT_BASE="${CORR_OUT_DIR:-/work/sandbox-cache/corr_per_os_graphs}"
IMG_CACHE="${IMG_CACHE:-/work/sandbox-cache/000-img}"
PYTHON="${PYTHON:-/home/sandbox/venv314t/bin/python3}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/mpl}"

mkdir -p "$IMG_CACHE" "$MPLCONFIGDIR"

# =============================================================================
# Per-OS CSV paths (latest correlation runs)
# Auto-discovers CSVs, trying both flat and nested directory layouts,
# and case variants (correlation_Mac, correlation_mac, etc.)
# =============================================================================
declare -A OS_CSV
for OS in Mac Android Linux Windows All; do
    os_lower=$(echo "$OS" | tr '[:upper:]' '[:lower:]')
    csv=""
    # Try multiple patterns (case-insensitive path match for All/all)
    csv="$(find "$CORR_BASE" -maxdepth 3 -ipath "*correlation*${os_lower}*" -name "ami_threshold_10.csv" -print 2>/dev/null | sort -r | head -1 || true)"
    if [[ -z "$csv" ]]; then
        echo "ERROR: No AMI CSV found for $OS in $CORR_BASE/" >&2
        exit 1
    fi
    OS_CSV[$OS]="$csv"
done

# =============================================================================
# Accepted invocations — promote a script+options here to make it canonical.
# Format: "[KEY=VAL ...] script.py"
# =============================================================================
ACCEPTED=(
    "CORR_LOWER_ONLY=1 corr_all_heatmap_v1.py"
    "CORR_THRESHOLD=0.6 CORR_LOWER_ONLY=1 corr_all_heatmap_v1.py"
    "corr_category_heatmap_split.py"
)

# =============================================================================
# All invocations — includes experimental/exploratory scripts.
# =============================================================================
ALL=(
    "${ACCEPTED[@]}"
    "corr_scatter_maxami.py"
    "corr_scatter_4panel.py"
)

# =============================================================================
# Arg parsing
# =============================================================================
MODE="${1:---accepted}"
case "$MODE" in
    --accepted) INVOCATIONS=("${ACCEPTED[@]}") ;;
    --all)      INVOCATIONS=("${ALL[@]}") ;;
    *) echo "Usage: $0 [--accepted | --all]" >&2; exit 1 ;;
esac

# =============================================================================
# Runner
# =============================================================================
run_invocation() {
    local inv="$1"
    local csv="$2"
    local out_dir="$3"
    local extra=()
    local script=""
    for tok in $inv; do
        if [[ "$tok" == *=* && -z "$script" ]]; then
            extra+=("$tok")
        else
            script="$tok"
        fi
    done
    echo "  $inv"
    env CORR_CSV="$csv" \
        CORR_OUT_DIR="$out_dir" \
        CORR_FILTER="allfp" \
        CORR_ALLOWLIST="$ALLOWLIST" \
        CORR_ANALYZE_DIR="$ANALYZE_DIR" \
        MPLCONFIGDIR="$MPLCONFIGDIR" \
        "${extra[@]+"${extra[@]}"}" \
        "$PYTHON" "$SCRIPT_DIR/$script"
}

# =============================================================================
# Run per OS
# =============================================================================
echo "=== Correlation graphs ($MODE) ==="
echo ""

START_TS=$(date +%s)

for OS in Mac Android Linux Windows All; do
    CSV="${OS_CSV[$OS]}"
    OUT_DIR="$OUT_BASE/$OS"
    mkdir -p "$OUT_DIR"

    echo "--- $OS ---"
    echo "CSV: $CSV"
    echo "Out: $OUT_DIR"
    echo ""

    for inv in "${INVOCATIONS[@]}"; do
        run_invocation "$inv" "$CSV" "$OUT_DIR"
    done
    echo ""
done

# =============================================================================
# Copy freshly generated PNGs to image cache
# =============================================================================
echo "=== Copying to $IMG_CACHE ==="
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
count=0
for OS in Mac Android Linux Windows; do
    for f in "$OUT_BASE/$OS"/*.png; do
        [[ -f "$f" ]] || continue
        if [[ $(stat -c %Y "$f") -ge $START_TS ]]; then
            dest="${TIMESTAMP}_${OS}_$(basename "$f")"
            cp "$f" "$IMG_CACHE/$dest"
            echo "  $dest"
            count=$((count + 1))
        fi
    done
done

echo ""
echo "Done. $count PNG(s) copied to $IMG_CACHE"
