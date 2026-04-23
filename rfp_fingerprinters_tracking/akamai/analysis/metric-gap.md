# Akamai Bot Manager Fingerprint — Metric Gap Analysis

Analysis of fingerprinting data collected by Akamai Bot Manager scripts,
cross-referenced against Firefox's RFP telemetry in
`toolkit/components/resistfingerprinting/metrics.yaml`.

Data source: `akamai/analysis/data.json` (collected via `xfinity.raw.html` harness)

## All Collected Metrics — Fingerprinting Entropy Classification

### Provides fingerprinting entropy

| Akamai Field | Entropy | Description |
|---|---|---|
| `canvas_fingerprint_hash` | High | SHA-1 of canvas 2D rendering (text + rectangles) |
| `navigator_properties.userAgent` | High | Full user agent string |
| `plugin_hashes` | High | Hashes of plugin name/description/filename/MIME |
| `navigator_properties.plugins` | High | Enumerated plugin name list |
| `detected_fonts` / `font_hash` | High (when available) | Font enumeration (null in test — no plugin) |
| `screen_dimensions.total_screen` | Medium | screen.width, screen.height |
| `screen_dimensions.available_screen` | Medium | screen.availWidth, screen.availHeight |
| `screen_dimensions.color_depth` | Medium | screen.colorDepth |
| `screen_dimensions.pixel_depth` | Medium | screen.pixelDepth |
| `navigator_properties.hardwareConcurrency` | Medium | CPU core count |
| `navigator_properties.language` | Medium | Primary language (e.g. en-US) |
| `navigator_properties.languages` | Medium | Ordered language preference list |
| `navigator_properties.platform` | Medium | OS identification (e.g. "MacIntel") |
| `navigator_properties.oscpu` | Medium | Firefox-specific OS + architecture string |
| `navigator_properties.buildID` | Medium | Firefox build identifier |
| `navigator_properties.doNotTrack` | Low-Medium | DNT header preference |
| `navigator_properties.maxTouchPoints` | Low-Medium | Touch device capability |
| `browser_name` | Low | Browser name from feature detection |
| `screen_dimensions.inner_window` | Low | window.innerWidth, window.innerHeight |
| `screen_dimensions.outer_window` | Low | window.outerWidth, window.outerHeight |
| `navigator_properties.vendor` | Low | Browser vendor string |
| `navigator_properties.productSub` | Low | Product sub-version string |
| `navigator_properties.appVersion` | Low | App version (subset of UA) |
| `navigator_properties.cookieEnabled` | Low | Cookie support boolean |
| `chrome_runtime_check` | Low | window.chrome object presence |
| `local_time_and_timezone` | Partial | Timezone offset provides entropy; timestamp does not |

### Does NOT provide fingerprinting entropy

| Akamai Field | Reasoning |
|---|---|
| `performance_timing` (all sub-fields) | Ephemeral timing data — varies every page load |
| `screen_dimensions.scroll_offset` | Current scroll position — ephemeral |
| `screen_dimensions.screen_position` | Window position on screen — ephemeral |
| `screen_dimensions.body_client_area` | Depends on page content, not user/device |
| `bot_detection.flags_xor_key` | Same for all users on site when no bot detected |
| `bot_detection.has_xpath_result` | Anti-bot mechanism |
| `bot_detection.chrome_without_runtime` | Anti-bot mechanism |
| `bot_detection_property_indices` | Anti-bot mechanism |
| `site_key_hash` | Site configuration — same for all visitors |
| `site_identifier` | Site configuration — same for all visitors |
| `permissions_api_states` | Removed from analysis — not a fingerprinting vector |
| `battery_status` | Removed from analysis — API blocked in modern browsers |
| `apng_support` | Removed from analysis — universal in modern browsers |
| `flash_version` | Removed from analysis — dead technology |
| `silverlight_versions` | Removed from analysis — dead technology |
| `ie_userdata_storage` | Removed from analysis — IE-only, irrelevant |
| `pdf_viewer_version` | Removed from analysis — ActiveX-based, irrelevant |
| `persistent_storage` | Removed from analysis — near-universal |
| `navigator_properties.webdriver` | Removed from analysis — automation flag |
| `navigator_properties.vibrate` | Removed from analysis — API presence only |
| `dom_feature_detection` | Removed from analysis — browser engine identification |
| `javascript_version` | Removed from analysis — browser engine identification |

## Mapping to Firefox RFP Metrics

### Certain matches

| Akamai Data Point | Firefox RFP Metric | Notes |
|---|---|---|
| `canvas_fingerprint_hash` | `canvasdata12_fingerprintjs1`, `canvasdata13_fingerprintjs2`, `canvasdata1`–`10` | Same surface (canvas 2D hash); Firefox tests multiple drawing operations |
| `navigator_properties.userAgent` | `user_agent` | Direct match |
| `detected_fonts` / `font_hash` | `fonts_fpjs_*`, `fonts_variant_*`, `missing_fonts` | Firefox covers font enumeration via multiple techniques |
| `screen_dimensions.total_screen` | `screen_width` + `screen_height` | Direct match |
| `screen_dimensions.available_screen` | `avail_width` + `avail_height` | Direct match |
| `screen_dimensions.color_depth` | `screens` JSON (`colorDepth` field) | Embedded in screens JSON blob |
| `screen_dimensions.pixel_depth` | `screens` JSON (`pixelDepth` field) | Embedded in screens JSON blob |
| `navigator_properties.hardwareConcurrency` | `processor_count` | Direct match |
| `navigator_properties.language` | `languages` (first element of array) | Direct match |
| `navigator_properties.languages` | `languages` | Direct match; also `prefs_intl_accept_languages` |
| `navigator_properties.platform` | `platform` | Direct match |
| `navigator_properties.oscpu` | `oscpu` | Direct match |
| `navigator_properties.doNotTrack` | `prefs_privacy_donottrackheader_enabled` | Boolean pref vs string "1"/"unspecified" |
| `navigator_properties.maxTouchPoints` | `max_touch_points` | Direct match |
| `screen_dimensions.inner_window` | `inner_width` + `inner_height` | Direct match |
| `screen_dimensions.outer_window` | `outer_width` + `outer_height` | Direct match |
| `local_time_and_timezone` | `timezone_offset_web` | Timezone offset in minutes; also `timezone` and `timezone_web` |

### Likely matches

| Akamai Data Point | Firefox RFP Metric | Notes |
|---|---|---|
| `navigator_properties.buildID` | `build_date` | Same source (`appBuildID`), stored as unix timestamp rather than raw string |

### Possible matches

| Akamai Data Point | Firefox RFP Metric | Notes |
|---|---|---|
| `navigator_properties.cookieEnabled` | `prefs_network_cookie_cookiebehavior` | Related but different granularity — pref integer vs boolean |

### No match in metrics.yaml

| Akamai Data Point | Why No Match |
|---|---|
| `plugin_hashes` | `navigator.plugins` is deprecated; near-zero entropy in modern browsers |
| `navigator_properties.plugins` | Same as above |
| `navigator_properties.vendor` | Constant `""` in Firefox — zero intra-Firefox entropy |
| `navigator_properties.productSub` | Constant `"20100101"` in Firefox — zero intra-Firefox entropy |
| `navigator_properties.appVersion` | Subset of `userAgent` data (already covered by `user_agent`) |
| `browser_name` | Always "Firefox" within Firefox population — zero intra-Firefox entropy |
| `chrome_runtime_check` | `window.chrome` never exists in Firefox — zero intra-Firefox entropy |

## Summary

- **26 fingerprinting-relevant data points** collected by Akamai
- **17 Certain** matches to Firefox RFP metrics
- **1 Likely** match
- **1 Possible** match
- **7 No match** — all are constants or irrelevant within the Firefox user population

Firefox's RFP metrics fully cover all high and medium entropy vectors that
Akamai collects. The unmatched items differentiate *between* browsers but
provide zero entropy *among* Firefox users.
