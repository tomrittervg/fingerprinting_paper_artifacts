# Browser Fingerprinting Script Analysis

This repository contains scripts, deobfuscated sources, captured payloads,
and Web API inventories for three commercial browser fingerprinting
services. The data supports an analysis of the signals each service
collects and the extent to which Firefox's anti-fingerprinting protections
cover them.

## Repository Layout

Each vendor directory follows the same internal structure:

- **`<vendor>/`**
  - **`script_urls.txt`** - source URLs of the collected scripts
  - **`sample_scripts/`**
    - **`raw/`** - original, obfuscated scripts
    - **`deobfs/`** (or **`deobs/`**) - deobfuscated sources
    - **`logging/`** - HTML harnesses and payloads (Signifyd only)
  - **`analysis/`**
    - **`data.json`** - captured fingerprint payload
    - **`web-api-inventory.md`** - Web APIs accessed by the script
    - **`metric-gap*.md`** - collected signals vs. Firefox RFP coverage
    - **`profile-gap*.md`** - gap analysis from Firefox Profiler traces
    - **`*.html`** - HTML harnesses used to execute the scripts
    - **`*.json.gz`** - Firefox Profiler traces (gzipped JSON)
    - **`*.txt`** - field-level data dumps

### Vendors

- **`akamai/`** - Akamai Bot Manager. Bot-detection script served from
  `/akam/13/` paths on customer domains.
- **`fingerprintpro/`** - FingerprintJS Pro v3.12.6. Visitor-identification
  service collecting approximately 164 signals across the `id`, `bd`, and
  `ex` modules.
- **`signifyd/`** - Signifyd fraud-prevention suite. `lite.js` is a fork
  of CreepJS (approximately 385 fields); `check.js` is a bundled
  ThreatMetrix profiler.

### Utility Scripts

- **`profiler_scripts/parse_profile.py`** parses Firefox Profiler JSON
  traces to extract and categorize the Web API calls made by a
  fingerprinting script.
