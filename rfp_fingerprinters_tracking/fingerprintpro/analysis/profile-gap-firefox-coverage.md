# Profile-Gap Analysis: Firefox metrics.yaml Coverage

Cross-reference of the 7 gaps identified in `profile-gap-analysis.md` against
Firefox's `user-characteristics` ping, based on `metrics.yaml` definitions and
the collection code in `UserCharacteristicsPageService.sys.mjs` and
`usercharacteristics.js`.

For each gap, this document identifies whether Firefox collects the
corresponding data, and whether FPJS actually obtains any entropy from the API
surface (some APIs return hardcoded or empty values in Firefox).

---

## Gap 1: WebRTC SDP Fingerprinting — NOT COLLECTED

### What FPJS reads
9 WebRTC APIs to generate an SDP offer and collect ICE candidates. The
fingerprint comes from the SDP codec list (ordered audio/video codecs with
payload types, clock rates, format parameters), RTP header extensions, and
transport parameters.

### Firefox coverage
Firefox collects two ICE-related metrics:

- **`ice_order`** — unique ICE foundation ordering count across 10 runs
  (`usercharacteristics.js:1275-1367`)
- **`ice_sd`** — average standard deviation of ICE candidate emission latencies
  across 10 runs, multiplied by 1000

Neither metric captures SDP codec information. And neither provides meaningful
entropy:

- **`ice_order`** is almost always **1**. Foundation IDs are generated
  deterministically by `nr_ice_get_foundation()` (`ice_candidate.c:368-414`)
  based on base address, candidate type, and STUN server. The collection runs
  locally with no STUN/TURN, so the same network interfaces always produce the
  same order.
- **`ice_sd`** is system timing noise — scheduling jitter, GC pauses, transient
  load. It varies between runs on the same machine and does not correlate with
  stable user characteristics.

No `RFPTarget` exists for ICE/WebRTC.

### Entropy gap

The SDP codec list is a high-entropy fingerprinting signal. The ordered list of
codecs from `createOffer()` varies by OS version, hardware acceleration
capabilities, GPU drivers, and browser build. It is not captured by any existing
metric.

| Signal | Collected | Entropy |
|--------|-----------|---------|
| SDP media codec list + ordering | No | **High** |
| RTP header extensions | No | Medium |
| ICE candidate ordering | Yes (`ice_order`) | ~Zero |
| ICE candidate timing | Yes (`ice_sd`) | Zero |
| DTLS fingerprint | No | Zero (per-session, not stable) |
| Data channel parameters | No | Zero (uniform across Firefox) |

---

## Gap 2: WebGPU Adapter and Limits — COLLECTED

### What FPJS reads
`GPUAdapterInfo.description`, `GPUAdapterInfo.device`,
`GPUAdapterInfo.isFallbackAdapter`, and 31 `GPUSupportedLimits` properties.

### Firefox coverage
Firefox collects all WebGPU data that carries entropy via
`populateWebGPUProperties()` (`UserCharacteristicsPageService.sys.mjs:880-983`):

- **`wgpu_is_fallback_adapter`** — `adapter.isFallbackAdapter`
- **`wgpu_missing_features`** — bitset of missing WebGPU features
- **All 31 `GPUSupportedLimits`** — 1:1 match (e.g. `wgpu_maxtexturedimension1d`
  through `wgpu_maxcomputeworkgroupsperdimension`)

28 of the 31 limits are real hardware values from the GPU driver (without RFP).
Three are always spec constants regardless of hardware or RFP:
- `maxInterStageShaderVariables` = 16
- `maxColorAttachments` = 8
- `maxColorAttachmentBytesPerSample` = 32

With RFP enabled, all 31 limits are replaced with spec defaults via
`RFPTarget::WebGPULimits` (`Adapter.cpp:373-377`), and `isFallbackAdapter`
always reports `false` via `RFPTarget::WebGPUIsFallbackAdapter`.

### FPJS gets zero entropy from AdapterInfo

`GPUAdapterInfo.description`, `device`, `vendor`, and `architecture` all return
**empty strings** unconditionally in Firefox (`Adapter.h:61-64`):
```cpp
void GetVendor(nsString& s) const { s = nsString(); }
void GetArchitecture(nsString& s) const { s = nsString(); }
void GetDevice(nsString& s) const { s = nsString(); }
void GetDescription(nsString& s) const { s = nsString(); }
```
Real GPU identification is only available via ChromeOnly properties
(`wgpuName`, `wgpuVendor`, `wgpuDevice`, etc.) inaccessible to web content.

### Entropy gap

None. Firefox collects all 28 hardware-varying limits. The AdapterInfo
properties FPJS reads are empty strings with zero entropy.

---

## Gap 3: MediaCapabilities.decodingInfo — COLLECTED

### What FPJS reads
`MediaCapabilities.decodingInfo()` results — `supported`, `smooth`, and
`powerEfficient` flags for multiple codec/resolution combinations.

### Firefox coverage
Firefox collects via `populateMediaCapabilities()`
(`usercharacteristics.js:541-639`), calling `decodingInfo()` for 7
codec/container combinations (VP9, VP8, AV1, HEVC, H.264 across webm/mp4):

- **`media_capabilities_unsupported`** — codecs where `supported === false`
- **`media_capabilities_not_smooth`** — codecs where `smooth === false`
- **`media_capabilities_not_efficient`** — codecs where `powerEfficient === false`
- **`media_capabilities_h264`** — H.264 profile/level support matrix

Without RFP, `powerEfficient` reflects actual hardware acceleration via
`decoder->IsHardwareAccelerated()` — varies by GPU, driver, and OS. With RFP,
all video reports `smooth=true`, `powerEfficient=false` via
`RFPTarget::MediaCapabilities`.

Audio `powerEfficient` is always `true` regardless of RFP. Video < 480p
`powerEfficient` is always `true` regardless of RFP.

### Entropy gap

None. All three `decodingInfo()` flags are collected.

---

## Gap 4: EME/DRM System Probing — COVERED BY PREF

### What FPJS reads
`navigator.requestMediaKeySystemAccess()` — 7 calls probing Widevine,
FairPlay, PlayReady, and ClearKey availability, plus robustness levels and
session types.

### Firefox coverage
- **`prefs_media_eme_enabled`** (boolean) — value of `media.eme.enabled`. When
  `false`, the user has disabled DRM entirely and all
  `requestMediaKeySystemAccess()` calls will fail.

### Why the pref is sufficient

Firefox ships only Widevine + ClearKey on all platforms (Linux, Windows, macOS).
PlayReady requires Edge; FairPlay requires Safari. So for all Firefox users with
EME enabled, the `requestMediaKeySystemAccess()` results are **uniform** — same
key systems, same robustness levels, same session types. The only variable is
whether EME is on or off, which the pref captures.

### Entropy gap

None. The pref captures the only varying bit. The remaining DRM probe results
are constant across Firefox users.

---

## Gap 5: WebAuthn Client Capabilities — NOT COLLECTED

### What FPJS reads
`PublicKeyCredential.getClientCapabilities()` — a dictionary of ~9 boolean
capabilities including `conditionalCreate`, `conditionalGet`,
`hybridTransport`, `passkeyPlatformAuthenticator`, and
`userVerifyingPlatformAuthenticator`.

### Firefox coverage
No WebAuthn metrics exist in `metrics.yaml`.

### Entropy

The capabilities vary by platform authenticator hardware and user configuration:
- **Linux**: Most capabilities `false` (no platform authenticator in typical
  setups). Low entropy — nearly all Linux users look identical.
- **Windows**: Varies by Windows Hello configuration (TPM presence, biometric
  hardware, whether passkeys are enabled). Medium entropy.
- **macOS**: Varies by Touch ID availability and configuration. Medium entropy.

`os_name` (already collected) captures the platform dimension but not the
within-platform hardware authenticator variation.

### Entropy gap

Low-medium. Not collected. Entropy is platform-dependent — negligible on Linux,
meaningful on Windows/macOS where platform authenticator configurations vary.
Growing in importance as passkey adoption increases.

---

## Gap 6: StorageManager Quota Probing — NOT COLLECTED

### What FPJS reads
- `StorageManager.estimate()` — quota and usage values (3 calls)
- `StorageManager.getDirectory()` — OPFS availability check (1 call)

### Firefox coverage
No StorageManager metrics exist in `metrics.yaml`.

### Entropy

The quota value is derived from available disk space, bucketed by Firefox.
Users with different disk sizes get different quota allocations. However:
- Bucketing reduces granularity
- The value changes over time as disk usage fluctuates (not stable)
- Private browsing uses a fixed reduced quota

OPFS availability (`getDirectory()`) is a single boolean — nearly always `true`
in modern Firefox on secure contexts. Zero entropy.

### Entropy gap

Low. The quota value varies by disk configuration but is unstable over time.
Not collected.

---

## Gap 7: Extended Cookie Probing — COVERED BY PREF

### What FPJS reads
- `Document.cookie` — 5 samples (write/read/delete cycle)
- `Navigator.cookieEnabled` — 1 sample

### Firefox coverage
- **`prefs_network_cookie_cookiebehavior`** (quantity) — value of
  `network.cookie.cookieBehavior` (0=allow all, 1=block all, 2=block
  third-party, 3=reject trackers, 4=reject cross-site tracking, 5=reject
  cross-site with storage access exceptions).

### Why the pref is sufficient

The pref fully determines first-party cookie behavior. FPJS runs in a
first-party context where `navigator.cookieEnabled` returns `true` and
write/read/delete succeeds for all pref values except `1` (block all), which
is extremely rare. SameSite and Partitioned cookie behavior is
browser-version-dependent and uniform across users on the same Firefox version.

### Entropy gap

None. The pref captures all meaningful entropy from cookie probing.

---

## Summary

| # | Gap | Firefox Coverage | Entropy Gap |
|---|-----|-----------------|-------------|
| 1 | WebRTC SDP codec list | ICE metrics collected but ~zero entropy | **Yes — high entropy** |
| 2 | WebGPU limits | All 28 hardware-varying limits collected | No |
| 3 | MediaCapabilities | All decodingInfo flags collected | No |
| 4 | EME/DRM probing | `prefs_media_eme_enabled` covers the only variable | No |
| 5 | WebAuthn capabilities | Not collected | **Yes — low/medium entropy** |
| 6 | StorageManager quota | Not collected | **Yes — low entropy** |
| 7 | Cookie probing | `prefs_network_cookie_cookiebehavior` covers behavior | No |

### Uncollected signals with entropy

1. **SDP codec list** — **High entropy.** The ordered codec list from
   `RTCPeerConnection.createOffer()` varies by OS version, hardware
   acceleration, GPU drivers, and browser build. Not captured by any existing
   metric.

2. **WebAuthn client capabilities** — **Low-medium entropy.** The
   `getClientCapabilities()` dictionary varies by platform authenticator
   hardware (TPM, biometrics) and user configuration. Negligible on Linux,
   meaningful on Windows/macOS.

3. **StorageManager.estimate() quota** — **Low entropy.** Varies by disk size
   (bucketed). Unstable over time.
