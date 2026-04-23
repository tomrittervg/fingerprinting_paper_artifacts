# FingerprintJS Pro v3.12.6 — Profile-Based Gap Analysis

Gap analysis of FingerprintJS Pro fingerprinting surfaces discovered via Firefox
Profiler trace (`index.json.gz`) but not previously identified through static
source analysis or data intercept analysis.

**Method:** The Firefox Profiler records every DOM/Web API call made during page
execution. By filtering to page-originated stacks (excluding DevTools, extensions,
and browser-internal calls), we get a ground-truth list of every Web API the
fingerprinting script actually touches at runtime. Comparing this against the
~115 signals documented in `metric-analysis-from-deobs.md` reveals API surfaces
that the static analysis missed — typically because the relevant code paths are
hidden behind encrypted string tables (`Gi` hash dispatch, `Hi` XOR-decrypted
lookup tables) or runtime-constructed property names.

**Profile stats:** 662,178 samples across 3 threads, 2,081 functions, producing
476 unique page-originated Web APIs across 29 categories.

---

## Gap 1: WebRTC SDP Fingerprinting (9 APIs, likely s97)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `RTCPeerConnection.constructor` | 37 |
| `RTCPeerConnection.createOffer` | 41 |
| `RTCPeerConnection.setLocalDescription` | 5 |
| `RTCPeerConnection.createDataChannel` | 5 |
| `RTCPeerConnection.generateCertificate` | 1 |
| `RTCPeerConnection.close` | 3 |
| `RTCPeerConnection.connectionState` | 3 |
| `RTCIceCandidate.constructor` | 2 |
| `RTCPeerConnectionIceEvent.constructor` | 2 |

### What it fingerprints

The script creates an `RTCPeerConnection`, calls `createOffer()` to generate an
SDP (Session Description Protocol) offer, then sets it as the local description
and listens for ICE candidates. The SDP offer contains:

- **Media codecs and their parameters** — the ordered list of supported audio
  and video codecs (opus, VP8, VP9, H.264, AV1, etc.) with their payload types,
  clock rates, and format-specific parameters (e.g. `apt`, `rtx`, `fmtp` lines)
- **RTP header extensions** — which RTP extensions are supported and their URIs
- **DTLS fingerprint** — the certificate fingerprint used for DTLS-SRTP
  negotiation (this is per-session but the algorithm and format vary)
- **ICE candidates** — local IP addresses (mDNS-obfuscated in Firefox, but the
  candidate structure, priority values, and transport types still vary)
- **BUNDLE and RTCP-mux support** — transport capabilities
- **Data channel parameters** — SCTP port, max message size

This is a high-entropy fingerprint because the codec list and ordering is
determined by the browser version, OS media stack, and hardware acceleration
capabilities. Different OS versions ship different codec support (e.g. H.264
hardware decode availability varies by GPU and OS).

### Why static analysis missed it

Signal `s97` is described in `metric-analysis-based-on-data2.md` as:
> `Ba`: null. Async 500ms timeout; checks `Ga`, `Qc` conditions; heavily obfuscated

The 500ms timeout is the ICE gathering delay — `createOffer()` is async and the
script waits for ICE candidates to arrive before collecting the SDP. The function
body is obfuscated via encrypted property dispatch (`Gi` hash-based access),
making static identification of the `RTCPeerConnection` constructor impossible
without runtime execution.

The profile data returned `null` for s97 in the intercepted data, which is
consistent with Firefox's behavior when WebRTC is available but the SDP
fingerprint didn't complete within the timeout window, or when the mDNS/ICE
stack doesn't produce distinguishing results.

### Firefox metrics coverage

The `user-characteristics` ping does **not** currently collect SDP codec
information. The existing `media_codec_support_*` metrics cover some codec
detection via `MediaSource.isTypeSupported()`, but the SDP approach reveals
additional information:
- Codec ordering/priority (not just presence)
- RTP parameter negotiation details
- Hardware acceleration hints embedded in SDP attributes
- Data channel and transport parameters

**Recommendation:** Consider collecting a hash of the SDP offer's codec section
(m-lines and associated a-lines with session-specific values like ICE
credentials stripped).

---

## Gap 2: WebGPU Adapter and Limits Enumeration (37 APIs, likely exp_s1016)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `GPU.requestAdapter` | 2 |
| `GPUAdapter.info` | 1 |
| `GPUAdapter.limits` | 67 |
| `GPUAdapterInfo.description` | 1 |
| `GPUAdapterInfo.device` | 1 |
| `GPUAdapterInfo.isFallbackAdapter` | 1 |
| `GPUSupportedLimits.maxBindGroups` | 1 |
| `GPUSupportedLimits.maxBindGroupsPlusVertexBuffers` | 1 |
| `GPUSupportedLimits.maxBindingsPerBindGroup` | 1 |
| `GPUSupportedLimits.maxBufferSize` | 1 |
| `GPUSupportedLimits.maxColorAttachmentBytesPerSample` | 1 |
| `GPUSupportedLimits.maxColorAttachments` | 1 |
| `GPUSupportedLimits.maxComputeInvocationsPerWorkgroup` | 1 |
| `GPUSupportedLimits.maxComputeWorkgroupSizeX` | 1 |
| `GPUSupportedLimits.maxComputeWorkgroupSizeY` | 1 |
| `GPUSupportedLimits.maxComputeWorkgroupSizeZ` | 1 |
| `GPUSupportedLimits.maxComputeWorkgroupStorageSize` | 1 |
| `GPUSupportedLimits.maxComputeWorkgroupsPerDimension` | 1 |
| `GPUSupportedLimits.maxDynamicStorageBuffersPerPipelineLayout` | 1 |
| `GPUSupportedLimits.maxDynamicUniformBuffersPerPipelineLayout` | 1 |
| `GPUSupportedLimits.maxInterStageShaderVariables` | 1 |
| `GPUSupportedLimits.maxSampledTexturesPerShaderStage` | 1 |
| `GPUSupportedLimits.maxSamplersPerShaderStage` | 1 |
| `GPUSupportedLimits.maxStorageBufferBindingSize` | 1 |
| `GPUSupportedLimits.maxStorageBuffersPerShaderStage` | 1 |
| `GPUSupportedLimits.maxStorageTexturesPerShaderStage` | 1 |
| `GPUSupportedLimits.maxTextureArrayLayers` | 1 |
| `GPUSupportedLimits.maxTextureDimension1D` | 1 |
| `GPUSupportedLimits.maxTextureDimension2D` | 1 |
| `GPUSupportedLimits.maxTextureDimension3D` | 1 |
| `GPUSupportedLimits.maxUniformBufferBindingSize` | 1 |
| `GPUSupportedLimits.maxUniformBuffersPerShaderStage` | 1 |
| `GPUSupportedLimits.maxVertexAttributes` | 1 |
| `GPUSupportedLimits.maxVertexBufferArrayStride` | 1 |
| `GPUSupportedLimits.maxVertexBuffers` | 1 |
| `GPUSupportedLimits.minStorageBufferOffsetAlignment` | 1 |
| `GPUSupportedLimits.minUniformBufferOffsetAlignment` | 1 |

### What it fingerprints

The script calls `navigator.gpu.requestAdapter()` to obtain a `GPUAdapter`, then
reads:

1. **`GPUAdapterInfo`** — `description`, `device`, `isFallbackAdapter`. These
   identify the GPU hardware (similar to WebGL's `WEBGL_debug_renderer_info`
   but through the newer WebGPU API).

2. **31 `GPUSupportedLimits` properties** — each limit reflects the hardware
   capabilities of the GPU. Values like `maxBufferSize`,
   `maxTextureDimension2D`, and `maxComputeWorkgroupStorageSize` vary across
   GPU vendors, architectures, and driver versions. Together, these 31 integers
   form a high-entropy hardware fingerprint.

The 67 samples on `GPUAdapter.limits` (vs 1 sample each for individual limit
properties) indicates the script accesses the `limits` object once and then
reads all properties from it.

### Why static analysis missed it

The experimental module signal `exp_s1016` was identified in the data intercept
as `{"b": {"0": 2281898568, "1": 17054720}}` — a hash-based payload that gave
no indication of the underlying API. The deobs analysis only noted it as
"likely GPU detection" based on contextual clues. The encrypted string tables
used in the experimental module prevented identification of `navigator.gpu` or
`requestAdapter` in static analysis.

### Firefox metrics coverage

Firefox's `user-characteristics` ping already collects:
- `gl_renderer` / `gl_vendor` — WebGL GPU identification
- `wgpu_is_fallback_adapter` — whether WebGPU falls back to software

However, it does **not** collect:
- The WebGPU adapter info (`GPUAdapterInfo.description`, `device`)
- Any of the 31 `GPUSupportedLimits` values

**Recommendation:** The WebGPU limits are a significant new fingerprinting
vector. Each limit is a numeric value that varies by GPU hardware and driver
version, producing a 31-dimensional feature vector. Consider collecting a hash
of the full limits object, or adding the individual limit values as a JSON
metric similar to `screens`.

---

## Gap 3: MediaCapabilities.decodingInfo (8 samples, likely part of s209)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `Navigator.mediaCapabilities` | 9 |
| `MediaCapabilities.decodingInfo` | 8 |

### What it fingerprints

`MediaCapabilities.decodingInfo()` takes a media configuration (codec string,
resolution, bitrate, framerate) and returns whether the browser can decode it
**smoothly** and with **hardware acceleration** (`powerEfficient`). By probing
multiple codec/resolution combinations, the script builds a matrix of:

- Which codecs are supported (H.264, VP8, VP9, AV1, HEVC, etc.)
- At which resolutions (720p, 1080p, 4K)
- Whether decoding is hardware-accelerated or software-only

This is more granular than `MediaSource.isTypeSupported()` because it reveals
hardware acceleration capabilities, which vary by GPU, driver version, and OS.

### Why static analysis missed it

Signal `s209` was identified in `metric-analysis-from-deobs.md` as:
> Encrypted via `Al` string table — likely EME/DRM capability check

The `Al` encrypted string table obscured both the `mediaCapabilities` navigator
property access and the `decodingInfo` method call. The profile reveals that
`s209` (or a related signal) exercises both DRM probing (see Gap 4) and media
capabilities detection.

### Firefox metrics coverage

Firefox collects `media_codec_support_*` metrics for specific codecs, but does
**not** collect `decodingInfo()` results. The key difference is that
`decodingInfo()` reveals the `powerEfficient` flag (hardware acceleration),
which `isTypeSupported()` does not.

**Recommendation:** Consider collecting `decodingInfo()` results for a
representative set of codec/resolution combinations, particularly the
`powerEfficient` flag which is the primary additional information beyond what
`isTypeSupported()` provides.

---

## Gap 4: EME/DRM System Probing (7 samples, likely part of s209)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `Navigator.requestMediaKeySystemAccess` | 7 |

### What it fingerprints

`navigator.requestMediaKeySystemAccess()` probes for DRM (Digital Rights
Management) system support. The script likely tests multiple key system
identifiers:

- `com.widevine.alpha` — Google Widevine (Linux, Chrome, Firefox)
- `com.apple.fps` — Apple FairPlay (Safari, macOS/iOS)
- `com.microsoft.playready` — Microsoft PlayReady (Edge, Windows)
- `org.w3.clearkey` — W3C Clear Key (universal, not a real DRM)

For each, the API returns whether the key system is available and what
configurations it supports (audio/video content types, robustness levels,
persistence types). This reveals:

- Which DRM modules are installed (OS and browser dependent)
- The supported robustness levels (indicates DRM security tier)
- Supported session types (temporary vs persistent)

The combination of available DRM systems and their configurations is
OS-dependent (Widevine on Linux, PlayReady on Windows, FairPlay on macOS) and
can also vary by Firefox version and distribution packaging.

### Why static analysis missed it

This API is accessed through the same encrypted `Al` string table as
`MediaCapabilities.decodingInfo` (Gap 3), making the method name invisible to
static analysis. The `Gi` hash-dispatch mechanism hides the
`requestMediaKeySystemAccess` string behind a 32-bit hash.

### Firefox metrics coverage

Firefox does **not** collect any DRM/EME capability information in the
`user-characteristics` ping.

**Recommendation:** The DRM system availability is largely determined by OS
(already collected via `os_name`) and Firefox version (already collected via
`user_agent`). Consider whether the DRM robustness levels add entropy beyond
these existing signals before adding a new metric.

---

## Gap 5: WebAuthn Client Capabilities (1 sample, new signal)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `Navigator.credentials` | 1 |
| `PublicKeyCredential.getClientCapabilities` | 1 |

### What it fingerprints

`PublicKeyCredential.getClientCapabilities()` is a relatively new WebAuthn API
(added to Firefox in late 2024) that returns a dictionary of boolean
capabilities indicating what the browser/platform supports:

- `conditionalCreate` — passkey creation via autofill UI
- `conditionalGet` — passkey authentication via autofill UI
- `hybridTransport` — cross-device authentication (QR code + BLE)
- `passkeyPlatformAuthenticator` — platform authenticator (Touch ID, Windows Hello)
- `userVerifyingPlatformAuthenticator` — biometric/PIN verification
- `relatedOrigins` — related origins for passkey sharing
- `signalAllAcceptedCredentials` — signal-based credential management
- `signalCurrentUserDetails` — signal-based user details
- `signalUnknownCredential` — signal-based unknown credential handling

The combination of supported capabilities varies by:
- OS (Windows Hello vs Touch ID vs Linux security key support)
- Browser version (capabilities added incrementally)
- Platform authenticator availability (TPM, biometric hardware)
- User configuration (whether passkeys are enabled)

### Why static analysis missed it

This API does not appear in any of the previously documented signal lists. It
is likely a recently added signal (post v3.12.6 documentation, or hidden within
an encrypted code path). The single sample count suggests it's a quick probe —
just checking what capabilities are available.

### Firefox metrics coverage

Firefox does **not** collect WebAuthn capability information in the
`user-characteristics` ping.

**Recommendation:** This is a low-entropy signal on Firefox/Linux (limited
platform authenticator support) but potentially higher entropy on Windows and
macOS where platform authenticators vary. Monitor whether this signal gains
importance as passkey adoption increases.

---

## Gap 6: StorageManager Quota Probing (4 samples, new signal)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `StorageManager.estimate` | 3 |
| `StorageManager.getDirectory` | 1 |

### What it fingerprints

**`StorageManager.estimate()`** returns the total storage quota available to
the origin and how much is currently used. The quota value is derived from the
available disk space and varies by:
- Total disk size
- Free disk space
- OS-specific quota algorithms (Firefox uses a fraction of available space)
- Whether the user is in private browsing mode (reduced quota)

The exact quota value can distinguish users by their disk configuration. Even
with Firefox's bucketing of the quota value, users with different disk sizes
will receive different quota allocations.

**`StorageManager.getDirectory()`** returns a `FileSystemDirectoryHandle` for
the origin's private file system (OPFS). The script likely uses this to test
whether OPFS is available, which depends on browser version and context
(secure context required, not available in all contexts).

### Why static analysis missed it

These calls appear in the Storage category alongside the known `IDBFactory`
and `Storage` APIs used by documented signals (s10, s11, s12, s85), but
`StorageManager` specifically was not identified in the deobs analysis. The
access likely occurs through one of the encrypted code paths used for storage
probing.

### Firefox metrics coverage

Firefox does **not** collect `StorageManager.estimate()` results or OPFS
availability in the `user-characteristics` ping.

**Recommendation:** The quota value is a coarse proxy for disk size. Consider
whether this adds meaningful entropy beyond what OS and hardware identification
already provide. If disk-size fingerprinting is a concern, consider collecting
the quota bucket value.

---

## Gap 7: Extended Cookie Probing (5 samples, beyond s32)

### APIs observed in profile

| API | Samples |
|-----|---------|
| `Document.cookie` | 5 |
| `Navigator.cookieEnabled` | 1 |

### What it fingerprints

The known signal `s32` performs a simple cookie write/read/delete test with
`SameSite=Strict`. However, the 5 samples on `Document.cookie` (plus the
`Navigator.cookieEnabled` check) suggest additional cookie probing beyond the
basic functionality test:

- Testing different `SameSite` values (Strict, Lax, None)
- Testing `Secure` flag behavior
- Testing `Partitioned` cookie support (CHIPS)
- Testing cookie size limits
- Testing third-party cookie availability

The `Navigator.cookieEnabled` property is a separate signal that checks the
browser's cookie permission state, which varies based on user privacy settings,
Enhanced Tracking Protection mode, and container tab configuration in Firefox.

### Why this is a minor gap

The 5-sample count on `Document.cookie` is consistent with the known s32
write/read/delete cycle (set cookie = 1 write, read it back = 1 read, expire
it = 1 write, plus potential verification reads). The `cookieEnabled` check
adds one additional boolean signal. This gap is likely cosmetic — the profile
just reveals the implementation details of the already-documented s32.

### Firefox metrics coverage

The `user-characteristics` ping does not collect cookie behavior results, but
this is low-entropy in practice — virtually all Firefox users have the same
cookie behavior for first-party contexts.

---

## Summary

| # | Gap | APIs | Samples | Likely Signal | New Metric Needed? |
|---|-----|------|---------|---------------|-------------------|
| 1 | WebRTC SDP fingerprinting | 9 | 99 | s97 | Yes — SDP codec list |
| 2 | WebGPU adapter + 31 limits | 37 | 103 | exp_s1016 | Yes — limits vector |
| 3 | MediaCapabilities.decodingInfo | 2 | 17 | s209 (partial) | Maybe — powerEfficient flag |
| 4 | EME/DRM system probing | 1 | 7 | s209 (partial) | Maybe — DRM availability |
| 5 | WebAuthn client capabilities | 2 | 2 | New/unknown | Monitor |
| 6 | StorageManager quota probing | 2 | 4 | New/unknown | Maybe — quota bucket |
| 7 | Extended cookie probing | 2 | 6 | s32 (extended) | No |

### Priority ranking

1. **WebGPU limits** (Gap 2) — Highest priority. 31 numeric values that form a
   hardware fingerprint independent of WebGL. WebGPU is increasingly available
   and these limits are not currently mitigated by RFP.

2. **WebRTC SDP** (Gap 1) — High priority. The SDP codec list is a significant
   fingerprinting vector that reveals hardware capabilities not captured by
   other metrics.

3. **MediaCapabilities** (Gap 3) — Medium priority. The `powerEfficient` flag
   from `decodingInfo()` adds hardware acceleration information beyond
   `isTypeSupported()`.

4. **StorageManager quota** (Gap 6) — Low priority. Coarse proxy for disk size,
   limited additional entropy.

5. **EME/DRM probing** (Gap 4), **WebAuthn** (Gap 5), **Cookie probing**
   (Gap 7) — Lowest priority. Largely determined by OS and browser version
   already collected.
