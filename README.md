# Artifact: Large-Scale Measurement and Real-World Mitigation of Web Browser Fingerprinting in the Wild

Supporting artifact for the CCS '26 paper
([10.1145/3830454.3846585](https://doi.org/10.1145/3830454.3846585)).

The paper measures browser fingerprintability across ~25 million Firefox
Release clients over a 23-day window, models three commercial
fingerprinting services against that population, and evaluates the
anti-fingerprinting protections shipped in Firefox 143.

## Contents

### `rfp_fingerprinters_tracking/`

Reverse engineering of the three modeled fingerprinting services:
obfuscated and deobfuscated scripts, captured payloads, Firefox Profiler
traces, per-vendor Web API inventories, and some analyses of each vendor's
collected signals against Firefox's protections.

- `akamai/` — Akamai Bot Manager
- `fingerprintpro/` — FingerprintJS Pro v3.12.6 (~164 signals)
- `signifyd/` — Signifyd: `lite.js` (a CreepJS fork, ~385 fields) and
  `check.js` (a bundled ThreatMetrix profiler)
- `profiler_scripts/` — extracts and categorizes Web API calls from
  Profiler traces

See `rfp_fingerprinters_tracking/README.md` for the per-vendor directory
layout.

Some script-source URLs in this copy are generalized to
"researcher-controlled test host", and exploratory working notes are
trimmed relative to the internal repository. The scripts, payloads, traces
and analyses themselves are unmodified.

### `rfp_paper_code/`

The Python analysis toolkit: reads Firefox telemetry, computes per-vendor
fingerprints, measures uniqueness and cohort structure (Simpson Index),
and simulates the effect of each candidate protection.

See `rfp_paper_code/README.md` for setup and a walkthrough.

## Data availability

The raw telemetry behind the paper's numbers is **not public**: it is
per-client Firefox measurement data that cannot be released.

### Aggregate data

The aggregate data derived from that telemetry *is* public, at
<https://storage.googleapis.com/fingerprinting-aggregate-data/> — roughly
6.2 GiB across 5,037 objects, served as a public GCS bucket (browse it via
the XML listing, or fetch individual keys directly). It comes in two forms.

**Whole-population fingerprint archives** at the bucket root, one per
protection state:

- `fingerprint_archive_anonymized_shuffled_Baseline.csv.zst`
- `fingerprint_archive_anonymized_shuffled_Phase_0.csv.zst`
- `fingerprint_archive_anonymized_shuffled_Phase_3.csv.zst`

Each is a zstd-compressed CSV of about 1.5–1.6 GB (4.6 GiB in total) with
one row per client: operating system, locale, and the fingerprint hash that
each of the three modeled services would have computed for that client
under that protection state, e.g. `os, intl_intl_locale,
Phase 3-FPJSv2_Realistic, Phase 3-AkamaiV2_Realistic,
Phase 3-Signifyd_Realistic`. 

**Per-metric value distributions**, under `Windows/`, `Mac/`, `Linux/` and
`Android/`, as sharded gzipped CSV (BigQuery export shards):

- `UserCharacteristics_<OS>_x_tbl/` — marginal distributions, one row per
  metric value: `metric1, value1, occurrences, total_occurrences,
  percentage`
- `UserCharacteristics_<OS>_x_by_y_tbl/` — pairwise joint distributions
  (the bulk of the shards, ~1.6 GiB): `metric1, value1, metric2, value2,
  occurrences, total_occurrences_for_value1, percentage`. These are the
  input to the correlation and conditional-entropy analyses.

Values too rare to release are collapsed to the literal string
`ANONYMIZED`, so counts remain correct while the underlying value is
withheld.

### Canvas Data Explorer

<https://storage.googleapis.com/canvas-comparison/index.html> is an
interactive companion page for the canvas results. It covers the 26 canvas
recipes Firefox measures (at 250×250, 240×128 and 128×128), drawn from
telemetry between 2026-03-12 and 2026-06-06 across Windows, macOS, Linux
and Android — some 684 million canvas submissions in aggregate.

For each recipe it reports submissions, distinct hashes, and how much of
the population the most common hashes cover, and it decodes the stored
pixel data so you can see the rendered images behind those hashes rather
than just their digests. Because 13 of the recipes were also captured with
software rendering forced on, the *Hardware*, *Software* and *HW vs SW*
views let you compare the two side by side — this is the entropy reduction
behind the Software Canvas protection evaluated in the paper. A *Yours*
control re-runs the same recipes in your own browser, so you can locate
your own output within the measured distribution.

### Test Data

In this repository is data that allows you to reproduce similar analyses
performed in the paper:

- `simulated-cache/` — a ~900-user sample dataset with the same schema and
  metrics as production, so the full pipeline can be run end to end. It was
  built from telemetry submissions by 6 volunteer Firefox Nightly users
  (Windows, macOS, Linux, Android); each submission was duplicated 100
  times with unique client identifiers and independently perturbed
  (WebGL strings, CSS system colors and fonts, `Accept-Language`, storage
  quota, CPU core count, canvas). The procedure is implemented in
  `generate_simulated_data.py` and can be re-run from
  `simulated-cache/source-pings/`.
- `real-output-data/` — the aggregate outputs computed from the real
  dataset, which is what the paper's figures and tables are drawn from.

Numbers produced from the sample dataset will not match the paper; it
exists to validate the methodology, not to reproduce the results.