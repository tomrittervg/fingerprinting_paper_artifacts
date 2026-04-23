#!/usr/bin/env python3
"""
Parse Firefox Profiler JSON traces and extract Web API usage by category.

Reads a .json.gz profile (as produced by the Firefox Profiler) and reports
which Web APIs were called, grouped into fingerprinting-relevant categories.

The profiler records every DOM/Web API call as a function in the funcTable
with names like "(DOM) CanvasRenderingContext2D.fillText".  We extract these,
filter out internal/chrome-only interfaces, and classify them.

Key modes:
  --page-only   Only report APIs called from page scripts (not DevTools/extensions)
  --sample-counts  Show how many samples each API appears in
"""

import argparse
import gzip
import json
import re
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Web API taxonomy
#
# Each category maps to a set of interface prefixes (matched against the
# interface part of "Interface.member").  Order matters: first match wins.
# ---------------------------------------------------------------------------
WEB_API_CATEGORIES = {
    "Canvas 2D": [
        "CanvasRenderingContext2D",
        "HTMLCanvasElement",
        "OffscreenCanvas",
        "OffscreenCanvasRenderingContext2D",
        "ImageData",
        "CanvasGradient",
        "CanvasPattern",
        "Path2D",
        "TextMetrics",
    ],
    "WebGL": [
        "WebGLRenderingContext",
        "WebGL2RenderingContext",
        "WebGLProgram",
        "WebGLShader",
        "WebGLBuffer",
        "WebGLTexture",
        "WebGLFramebuffer",
        "WebGLRenderbuffer",
        "WebGLUniformLocation",
        "WebGLActiveInfo",
        "WebGLShaderPrecisionFormat",
        "WEBGL_",
        "EXT_",
        "OES_",
    ],
    "Web Audio": [
        "AudioContext",
        "BaseAudioContext",
        "OfflineAudioContext",
        "OfflineAudioCompletionEvent",
        "OscillatorNode",
        "AnalyserNode",
        "GainNode",
        "AudioBuffer",
        "AudioBufferSourceNode",
        "AudioDestinationNode",
        "DynamicsCompressorNode",
        "BiquadFilterNode",
        "ScriptProcessorNode",
        "AudioWorklet",
        "AudioNode",
        "AudioParam",
        "AudioScheduledSourceNode",
    ],
    "Web Crypto": [
        "Crypto",
        "SubtleCrypto",
        "CryptoKey",
    ],
    "Encoding": [
        "TextEncoder",
        "TextDecoder",
    ],
    "DOM Core": [
        "Document",
        "HTMLDocument",
        "Node",
        "Element",
        "HTMLElement",
        "Text",
        "DocumentType",
        "DocumentFragment",
        "Attr",
        "NamedNodeMap",
        "NodeList",
        "HTMLCollection",
        "DOMTokenList",
        "DOMImplementation",
        "TreeWalker",
        "NodeIterator",
        "Range",
        "Comment",
        "Selection",
    ],
    "DOM Geometry": [
        "DOMRect",
        "DOMRectReadOnly",
        "DOMRectList",
        "DOMPoint",
        "DOMPointReadOnly",
        "DOMQuad",
        "DOMMatrix",
        "DOMMatrixReadOnly",
    ],
    "Events": [
        "Event",
        "EventTarget",
        "CustomEvent",
        "MouseEvent",
        "KeyboardEvent",
        "TouchEvent",
        "PointerEvent",
        "FocusEvent",
        "WheelEvent",
        "InputEvent",
        "CompositionEvent",
        "UIEvent",
        "AnimationEvent",
        "TransitionEvent",
        "MessageEvent",
        "MutationObserver",
        "MutationRecord",
        "ResizeObserver",
        "IntersectionObserver",
        "PerformanceObserver",
        "AbortController",
        "AbortSignal",
    ],
    "Window / Navigator": [
        "Window",
        "Navigator",
        "Screen",
        "Location",
        "History",
        "BarProp",
    ],
    "URL": [
        "URL",
        "URLSearchParams",
        "URLSearchParamsIterator",
    ],
    "CSS / Style": [
        "CSS",
        "CSSStyleDeclaration",
        "CSSStyleProperties",
        "CSSStyleSheet",
        "CSSRule",
        "CSSStyleRule",
        "StyleSheet",
        "StyleSheetList",
        "MediaQueryList",
        "MediaList",
        "CustomElementRegistry",
        "ShadowRoot",
        "AnonymousContent",
    ],
    "Images / Media Elements": [
        "Image",
        "HTMLImageElement",
        "HTMLVideoElement",
        "HTMLAudioElement",
        "HTMLMediaElement",
        "HTMLSourceElement",
        "MediaSource",
        "SourceBuffer",
    ],
    "Specific HTML Elements": [
        "HTMLLinkElement",
        "HTMLScriptElement",
        "HTMLFormElement",
        "HTMLInputElement",
        "HTMLSelectElement",
        "HTMLTextAreaElement",
        "HTMLDetailsElement",
        "HTMLDialogElement",
        "HTMLMetaElement",
        "HTMLButtonElement",
        "HTMLTemplateElement",
    ],
    "Performance / Timing": [
        "Performance",
        "PerformanceTiming",
        "PerformanceNavigation",
        "PerformanceEntry",
        "PerformanceMark",
        "PerformanceMeasure",
        "PerformanceResourceTiming",
        "PerformanceNavigationTiming",
    ],
    "Storage": [
        "Storage",
        "localStorage",
        "sessionStorage",
        "StorageManager",
        "IDBFactory",
        "IDBDatabase",
        "IDBTransaction",
        "IDBObjectStore",
        "IDBRequest",
        "IDBOpenDBRequest",
        "IDBCursor",
        "IDBIndex",
        "IDBKeyRange",
        "CacheStorage",
        "Cache",
        "DOMStringList",
    ],
    "Network / Fetch": [
        "XMLHttpRequest",
        "Fetch",
        "Request",
        "Response",
        "Headers",
        "FormData",
        "Blob",
        "File",
        "FileReader",
        "FileList",
        "WebSocket",
    ],
    "Workers / Messaging": [
        "Worker",
        "SharedWorker",
        "ServiceWorker",
        "ServiceWorkerRegistration",
        "MessageChannel",
        "MessagePort",
        "BroadcastChannel",
        "WorkerGlobalScope",
        "DedicatedWorkerGlobalScope",
        "SharedWorkerGlobalScope",
        "WorkerNavigator",
        "Worklet",
    ],
    "Notifications / Permissions": [
        "Notification",
        "Permissions",
        "PermissionStatus",
    ],
    "Geolocation": [
        "Geolocation",
        "GeolocationPosition",
    ],
    "Media Devices / WebRTC": [
        "MediaDevices",
        "MediaStream",
        "MediaStreamTrack",
        "RTCPeerConnection",
        "RTCPeerConnectionIceEvent",
        "RTCSessionDescription",
        "RTCIceCandidate",
        "RTCDataChannel",
        "RTCCertificate",
    ],
    "Battery": [
        "BatteryManager",
    ],
    "Gamepad": [
        "Gamepad",
        "GamepadEvent",
    ],
    "Speech": [
        "SpeechSynthesis",
        "SpeechSynthesisUtterance",
        "SpeechRecognition",
    ],
    "Clipboard": [
        "Clipboard",
        "ClipboardEvent",
        "DataTransfer",
    ],
    "Page Lifecycle Events": [
        "PageTransitionEvent",
        "NotifyPaintEvent",
    ],
    "Plugins (legacy)": [
        "Plugin",
        "PluginArray",
        "MimeType",
        "MimeTypeArray",
    ],
    "Console": [
        "console",
    ],
    "WebGPU": [
        "GPU",
        "GPUAdapter",
        "GPUAdapterInfo",
        "GPUSupportedLimits",
        "GPUSupportedFeatures",
        "GPUDevice",
        "GPUQueue",
        "GPUBuffer",
        "GPUTexture",
        "GPUTextureView",
        "GPUSampler",
        "GPUBindGroup",
        "GPUBindGroupLayout",
        "GPUPipelineLayout",
        "GPUShaderModule",
        "GPUComputePipeline",
        "GPURenderPipeline",
        "GPUCommandEncoder",
        "GPUComputePassEncoder",
        "GPURenderPassEncoder",
        "GPUCommandBuffer",
        "GPURenderBundle",
        "GPURenderBundleEncoder",
        "GPUQuerySet",
        "GPUCanvasContext",
        "GPUError",
        "GPUValidationError",
        "GPUOutOfMemoryError",
    ],
    "Fonts": [
        "FontFace",
        "FontFaceSet",
    ],
    "Streams": [
        "ReadableStream",
        "ReadableStreamDefaultReader",
        "ReadableStreamBYOBReader",
        "WritableStream",
        "WritableStreamDefaultWriter",
        "TransformStream",
        "CompressionStream",
        "DecompressionStream",
    ],
    "Media Capabilities / DRM": [
        "MediaCapabilities",
        "MediaKeySystemAccess",
        "MediaKeySystemConfiguration",
    ],
    "WebAuthn / Credentials": [
        "PublicKeyCredential",
        "CredentialsContainer",
        "AuthenticatorResponse",
    ],
    "Visibility / Fullscreen": [
        "VisualViewport",
    ],
    "SVG": [
        "SVGElement",
        "SVGSVGElement",
        "SVGGraphicsElement",
        "SVGTextContentElement",
        "SVGRect",
        "SVGPoint",
        "SVGMatrix",
        "SVGAnimatedLength",
        "SVGAnimatedRect",
        "SVGAnimatedString",
        "SVGAnimatedNumber",
        "SVGAnimatedTransformList",
        "SVGLength",
        "SVGPathElement",
        "SVGLineElement",
        "SVGCircleElement",
        "SVGRectElement",
        "SVGPolygonElement",
        "SVGPolylineElement",
        "SVGEllipseElement",
        "SVGGElement",
        "SVGDefsElement",
        "SVGUseElement",
        "SVGImageElement",
        "SVGTextElement",
        "SVGTSpanElement",
    ],
    "IFrame": [
        "HTMLIFrameElement",
    ],
}

# Interfaces that are internal to Firefox / DevTools and should be excluded
# from Web API reporting.
INTERNAL_PREFIXES = (
    "nsI",
    "mozI",
    "ChromeUtils",
    "InspectorUtils",
    "JSWindowActorChild",
    "JSProcessActorChild",
    "WindowGlobalChild",
    "BrowsingContext",
    "WindowContext",
    "DebuggerNotification",
    "CallbackDebuggerNotification",
    "EventCallbackDebuggerNotification",
    "XPCComponents",
    "ContentProcessMessageManager",
    "MozSharedMap",
    "PeerConnectionImpl",
    "PeerConnectionObserver",
    "CreateOfferRequest",
    "FrameLoader",
    "inIDeepTreeWalker",
    "xpcIJSWeakReference",
    "InspectorFontFace",
    "InspectorCSSParser",
    "Exception",
    # DevTools Grid Inspector APIs (Element.getGridFragments() etc.)
    "Grid",
    "GridDimension",
    "GridLine",
    "GridLines",
    "GridTrack",
    "GridTracks",
)

DOM_RE = re.compile(r"^\(DOM\)\s+(.+)$")


def parse_profile(path):
    """Load a .json.gz or .json Firefox profile."""
    if path.endswith(".gz"):
        with gzip.open(path, "rt") as f:
            return json.load(f)
    else:
        with open(path, "r") as f:
            return json.load(f)


def parse_dom_name(raw_name):
    """
    Parse a funcTable name like "(DOM) CanvasRenderingContext2D.fillText"
    or "(DOM) set Node.textContent".

    Returns (interface, member) or None if not a DOM function.
    """
    m = DOM_RE.match(raw_name)
    if not m:
        return None
    qualified = m.group(1)
    # Strip get/set prefix
    qualified = re.sub(r"^(get|set)\s+", "", qualified)
    parts = qualified.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return qualified, ""


def is_internal(interface):
    """True if this interface is a Firefox/DevTools internal, not a Web API."""
    return any(interface.startswith(p) for p in INTERNAL_PREFIXES)


def find_page_resource_ids(profile, thread):
    """
    Find resource IDs that correspond to the actual page (not extensions,
    devtools, libxul, or self-hosted code).

    Page resources have type=3 (subresource) with a host, or type=1 (webhost)
    but NOT extension (type=2) or native (type=1 with lib).
    """
    string_table = profile["shared"]["stringArray"]
    rt = thread["resourceTable"]
    page_ids = set()
    for i in range(rt["length"]):
        rtype = rt["type"][i]
        name = string_table[rt["name"][i]]
        # type 3 = "webhost" in the profiler format — these are page origins
        # type 2 = extension, type 1 = library, type 5 = addon/chrome resource
        if rtype == 3:
            page_ids.add(i)
    return page_ids


def find_page_func_ids(profile, thread):
    """Return set of func indices that belong to page scripts."""
    page_resources = find_page_resource_ids(profile, thread)
    ft = thread["funcTable"]
    page_funcs = set()
    for i in range(ft["length"]):
        if ft["resource"][i] in page_resources:
            page_funcs.add(i)
    return page_funcs


def collect_page_dom_apis(profile, thread_idx=0):
    """
    Walk all sample stacks. For any stack that contains a page function,
    collect all DOM API functions in that stack.

    Returns Counter mapping func_idx -> sample count (only for DOM funcs
    reachable from page code).
    """
    thread = profile["threads"][thread_idx]
    string_table = profile["shared"]["stringArray"]
    ft = thread["funcTable"]
    samples = thread["samples"]
    stack_table = thread["stackTable"]
    frame_table = thread["frameTable"]
    page_funcs = find_page_func_ids(profile, thread)

    # Pre-compute which funcs are DOM calls (avoids regex per sample)
    dom_func_set = set()
    for i in range(ft["length"]):
        name = string_table[ft["name"][i]]
        if DOM_RE.match(name):
            dom_func_set.add(i)

    # Pre-compute frame -> func mapping as a list for fast lookup
    frame_funcs = frame_table["func"]
    stack_frames = stack_table["frame"]
    stack_prefixes = stack_table["prefix"]
    sample_stacks = samples["stack"]

    # Pre-expand each unique stack into its set of func indices,
    # and whether it contains a page func.  Stacks are shared across
    # many samples via the stackTable, so caching is a big win.
    num_stacks = stack_table["length"]
    # For each stack node, compute (set_of_dom_funcs, has_page_func)
    # bottom-up (prefix first).
    stack_dom_funcs = [None] * num_stacks  # set of dom func indices
    stack_has_page = [False] * num_stacks

    for si in range(num_stacks):
        func_idx = frame_funcs[stack_frames[si]]
        prefix = stack_prefixes[si]

        if prefix is not None:
            # Inherit from prefix
            inherited_dom = stack_dom_funcs[prefix]
            inherited_page = stack_has_page[prefix]
        else:
            inherited_dom = frozenset()
            inherited_page = False

        is_dom = func_idx in dom_func_set
        is_page = func_idx in page_funcs

        if is_dom:
            stack_dom_funcs[si] = inherited_dom | {func_idx}
        else:
            stack_dom_funcs[si] = inherited_dom

        stack_has_page[si] = inherited_page or is_page

    # Now walk samples and accumulate counts
    dom_counts = Counter()
    num_samples = samples["length"]
    for si in range(num_samples):
        stack_idx = sample_stacks[si]
        if stack_idx is None:
            continue
        if not stack_has_page[stack_idx]:
            continue
        for f in stack_dom_funcs[stack_idx]:
            dom_counts[f] += 1

    return dom_counts


def extract_dom_functions(profile, page_only=False):
    """
    Return a list of (interface, member, func_index, thread_idx) for every
    DOM function in the profile, excluding internal interfaces.

    If page_only is True, only include functions that appear in stacks
    containing page script frames.
    """
    string_table = profile["shared"]["stringArray"]

    if page_only:
        # Collect the set of DOM func indices reachable from page code
        page_dom_funcs = set()
        for ti, thread in enumerate(profile["threads"]):
            if thread.get("isMainThread"):
                counts = collect_page_dom_apis(profile, ti)
                page_dom_funcs.update(counts.keys())

    results = []
    for ti, thread in enumerate(profile["threads"]):
        ft = thread["funcTable"]
        for i in range(ft["length"]):
            if page_only and i not in page_dom_funcs:
                continue
            name = string_table[ft["name"][i]]
            parsed = parse_dom_name(name)
            if not parsed:
                continue
            interface, member = parsed
            if is_internal(interface):
                continue
            results.append((interface, member, i, ti))
    return results


def classify(interface):
    """Return the category name for a given interface, or 'Uncategorized'."""
    for category, prefixes in WEB_API_CATEGORIES.items():
        for prefix in prefixes:
            if interface == prefix or interface.startswith(prefix):
                return category
    return "Uncategorized"


def count_samples_per_func(profile, thread_idx=0):
    """Count how many samples each function appears in (any position in stack)."""
    thread = profile["threads"][thread_idx]
    samples = thread["samples"]
    stack_table = thread["stackTable"]
    frame_table = thread["frameTable"]
    counts = Counter()
    for si in range(samples["length"]):
        stack_idx = samples["stack"][si]
        seen = set()
        while stack_idx is not None:
            frame_idx = stack_table["frame"][stack_idx]
            func_idx = frame_table["func"][frame_idx]
            if func_idx not in seen:
                seen.add(func_idx)
                counts[func_idx] += 1
            stack_idx = stack_table["prefix"][stack_idx]
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Extract Web API usage from a Firefox Profiler trace"
    )
    parser.add_argument("profile", help="Path to .json.gz or .json profile")
    parser.add_argument(
        "--page-only",
        action="store_true",
        help="Only report APIs called from page scripts (filters out "
        "DevTools, extensions, and browser internals)",
    )
    parser.add_argument(
        "--category",
        help="Only show APIs in this category",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all taxonomy categories and exit",
    )
    parser.add_argument(
        "--sample-counts",
        action="store_true",
        help="Include sample counts (slower, walks all stacks)",
    )
    args = parser.parse_args()

    if args.list_categories:
        for cat, interfaces in WEB_API_CATEGORIES.items():
            print(f"  {cat}")
            for iface in interfaces:
                print(f"    - {iface}")
        return

    profile = parse_profile(args.profile)
    dom_funcs = extract_dom_functions(profile, page_only=args.page_only)

    # Build category -> [(interface, member, func_idx)] mapping
    by_category = defaultdict(list)
    for interface, member, func_idx, thread_idx in dom_funcs:
        cat = classify(interface)
        by_category[cat].append((interface, member, func_idx))

    # Optionally compute sample counts
    sample_counts = None
    if args.sample_counts:
        if args.page_only:
            # Already computed during page-only filtering; recompute for display
            for ti, thread in enumerate(profile["threads"]):
                if thread.get("isMainThread"):
                    sample_counts = collect_page_dom_apis(profile, ti)
                    break
        else:
            sample_counts = count_samples_per_func(profile)

    # Print report
    categories_to_show = sorted(by_category.keys())
    if args.category:
        categories_to_show = [
            c for c in categories_to_show if c.lower() == args.category.lower()
        ]
        if not categories_to_show:
            print(f"No APIs found in category '{args.category}'")
            return

    for cat in categories_to_show:
        entries = by_category[cat]
        # Deduplicate by (interface, member)
        seen = {}
        for interface, member, func_idx in entries:
            key = (interface, member)
            if key not in seen:
                seen[key] = func_idx

        print(f"\n{'=' * 60}")
        print(f"  {cat} ({len(seen)} unique APIs)")
        print(f"{'=' * 60}")

        for (interface, member), func_idx in sorted(seen.items()):
            label = f"{interface}.{member}" if member else interface
            if sample_counts is not None:
                count = sample_counts.get(func_idx, 0)
                print(f"  {label:<50s}  (samples: {count})")
            else:
                print(f"  {label}")

    # Summary
    total = sum(len(set((i, m) for i, m, _ in entries))
                for entries in by_category.values())
    print(f"\n--- Total: {total} unique Web APIs across "
          f"{len(by_category)} categories ---")


if __name__ == "__main__":
    main()
