#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
DATE="${DATE:-simulated}"
BASE="${BASE:-${RFP_OUTPUT_DIR:-./simulated-output}}"
CACHE="${CACHE:-${RFP_CACHE_DIR:-./simulated-cache}}"
ANALYZE="./run.sh"
COMMON_ARGS="--cache-dir $CACHE --per-os=true --force --partition-width 1"
EXTRA_ARGS=("$@")

# ── Helpers ──────────────────────────────────────────────────────────────────
run() {
    local name="$1"; shift
    local config="$1"; shift
    local outdir="${BASE}/${name}_${DATE}"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "  $name  ($config)"
    echo "  → $outdir"
    echo "════════════════════════════════════════════════════════════════"
    $ANALYZE -o "$outdir" -c "$config" $COMMON_ARGS "${EXTRA_ARGS[@]}" "$@"
}

# ── Runs ─────────────────────────────────────────────────────────────────────
# Fingerprint buckets
run buckets                     configs/fingerprint_buckets_realistic.py

# Shannon/HHI individual metrics
run shannon_hhi                 configs/paper_indvmetrics_shannon_hhi.py

# SMR per fingerprinter
run smr_akamaiV2                configs/paper_indvmetrics_smr_akamaiV2_realistic.py
run smr_fpjsV2                  configs/paper_indvmetrics_smr_fpjsV2_realistic.py
run smr_signifyd                configs/paper_indvmetrics_smr_signifyd_realistic.py

# Fingerprints + experiments (uniqueness tables)
run exp_add         configs/paper_uniqueness_tables_additive_realistic.py
run exp_ind         configs/paper_uniqueness_tables_individual_realistic.py

# Quick min-set (combos 1–3 only)
#run minset_quick_top15            configs/quickminset_top15.py
#run minset_quick_top17            configs/quickminset_top17.py
#run minset_quick_top20            configs/quickminset_top20.py

# MinMetrics (prefix uniqueness curve — all 3 fingerprinters, SMR ordering)
#run minmetrics_all_smr           configs/minmetrics_all_smr_ordering.py  # done

# MinMetrics (marginal contribution ordering from prior minmetrics run)
#run minmetrics_all_reordered     configs/minmetrics_all_minmetrics_ordering.py  # done

# Iterative MinMetrics (greedy forward selection — optimal ordering)
run iterative_minmetrics_akamaiV2  configs/iterative_minmetrics_akamaiV2.py
run iterative_minmetrics_fpjsV2   configs/iterative_minmetrics_fpjsV2.py
run iterative_minmetrics_signifyd configs/iterative_minmetrics_signifyd.py

# Min-set analyses (SMR ordering, per-OS)
#run minset_top5_smr             configs/min_set_top5_smr.py            # done
#run minset_top7_smr             configs/min_set_top7_smr.py            # done
#run minset_top8_smr_Android     configs/min_set_top8_smr_Android.py
#run minset_top8_smr_Darwin      configs/min_set_top8_smr_Darwin.py
#run minset_top8_smr_Linux       configs/min_set_top8_smr_Linux.py
#run minset_top8_smr_WINNT       configs/min_set_top8_smr_WINNT.py
#run minset_top9_smr_Android     configs/min_set_top9_smr_Android.py
#run minset_top9_smr_Darwin      configs/min_set_top9_smr_Darwin.py
#run minset_top9_smr_Linux       configs/min_set_top9_smr_Linux.py
#run minset_top9_smr_WINNT       configs/min_set_top9_smr_WINNT.py
#run minset_top10_smr_Android    configs/min_set_top10_smr_Android.py   # done
#run minset_top10_smr_Darwin     configs/min_set_top10_smr_Darwin.py    # done
#run minset_top10_smr_Linux      configs/min_set_top10_smr_Linux.py     # done
#run minset_top10_smr_WINNT      configs/min_set_top10_smr_WINNT.py     # done
#run minset_top11_smr_Linux      configs/min_set_top11_smr_Linux.py
#run minset_top11_smr_Android    configs/min_set_top11_smr_Android.py
#run minset_top11_smr_Darwin     configs/min_set_top11_smr_Darwin.py
#run minset_top11_smr_WINNT      configs/min_set_top11_smr_WINNT.py
#run minset_top12_smr_Android    configs/min_set_top12_smr_Android.py
#run minset_top12_smr_Darwin     configs/min_set_top12_smr_Darwin.py
#run minset_top12_smr_Linux      configs/min_set_top12_smr_Linux.py
#run minset_top12_smr_WINNT      configs/min_set_top12_smr_WINNT.py
#run minset_top13_smr_Android    configs/min_set_top13_smr_Android.py
#run minset_top13_smr_Darwin     configs/min_set_top13_smr_Darwin.py
#run minset_top13_smr_Linux      configs/min_set_top13_smr_Linux.py
#run minset_top13_smr_WINNT      configs/min_set_top13_smr_WINNT.py
#run minset_top14_smr_Android    configs/min_set_top14_smr_Android.py
#run minset_top14_smr_Darwin     configs/min_set_top14_smr_Darwin.py
#run minset_top14_smr_Linux      configs/min_set_top14_smr_Linux.py
#run minset_top14_smr_WINNT      configs/min_set_top14_smr_WINNT.py
#run minset_top15_smr            configs/min_set_top15_smr.py
#run minset_top20_smr            configs/min_set_top20_smr.py
#run minset_top20_combo4_smr     configs/min_set_top20_combo4_smr.py

# ISMR / ISMRP
#run ismr                        configs/ismr.py                       # done
#run ismrp                       configs/ismrp.py                      # OOM
#run ismrp_Android               configs/ismrp_Android.py
#run ismrp_Darwin                configs/ismrp_Darwin.py
#run ismrp_Linux                 configs/ismrp_Linux.py
#run ismrp_WINNT                 configs/ismrp_WINNT.py

# LMR per fingerprinter
#run lmr_akamaiV2                configs/paper_indvmetrics_lmr_akamaiV2.py
#run lmr_fpjsV2                  configs/paper_indvmetrics_lmr_fpjsV2.py  # done
#run lmr_signifyd                configs/paper_indvmetrics_lmr_signifyd.py

# Min-set analyses (ISMR ordering - less effective)
#run minset_top5_ismr            configs/min_set_top5_ismr.py
#run minset_top10_ismr           configs/min_set_top10_ismr.py
#run minset_top20_ismr           configs/min_set_top20_ismr.py
#run minset_top20_combo4_ismr    configs/min_set_top20_combo4_ismr.py

# Correlation
#run correlation                 configs/paper_correlation.py


echo ""
echo "All runs complete."
