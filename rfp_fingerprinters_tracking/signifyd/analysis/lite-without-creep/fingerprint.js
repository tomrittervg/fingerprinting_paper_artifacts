/**
 * Signifyd lite.js - Non-CreepJS Features
 *
 * This file contains fingerprinting checks from Signifyd's lite.js that are
 * either NOT in CreepJS or represent significant architectural changes.
 *
 * Feature Origins:
 * 1. detectIncognito - EXTERNAL LIBRARY (Joe12387/detectIncognito v1.4.1)
 * 2. Navigator anomaly detection - INHERITED FROM CREEPJS (not unique to Signifyd)
 * 3. Worker context fingerprinting - SIGNIFYD ADDITION (genuinely new architecture)
 * 4. In-app WebView detection - SIGNIFYD ADDITION
 * 5. Cookie monster - SIGNIFYD ADDITION
 *
 * NOTE: The navigator anomaly detection (#2) uses the same [native code] checking
 * pattern that existed in CreepJS at the fork point. It is included here for
 * completeness but is NOT unique to Signifyd.
 *
 * For analysis purposes only.
 */

(function() {
    'use strict';

    const results = {
        incognito: null,
        navigatorAnomalies: null,
        workerComparison: null,
        inAppWebView: null,
        cookieMonster: null
    };

    // =========================================================================
    // 1. INCOGNITO DETECTION
    // Based on detectIncognito v1.4.1 by Joe Rutkowski
    // https://github.com/Joe12387/detectIncognito
    // =========================================================================

    async function detectIncognito() {
        return new Promise((resolve, reject) => {
            let browserName = "Unknown";

            function callback(isPrivate) {
                resolve({
                    isPrivate: isPrivate,
                    browserName: browserName
                });
            }

            function getEngineIdentifier() {
                let f = 0;
                const h = parseInt("-1");
                try {
                    h.toFixed(h);
                } catch (m) {
                    f = m.message.length;
                }
                return f;
            }

            function isIE() {
                return navigator.msSaveBlob !== undefined && eval.toString().length === 39;
            }

            // Firefox detection
            function firefoxCheck() {
                callback(navigator.serviceWorker === undefined);
            }

            // Safari detection (macOS/iOS)
            function safariCheck() {
                if (navigator.maxTouchPoints !== undefined) {
                    // iOS Safari
                    chromiumCheck();
                } else {
                    // macOS Safari - use openDatabase
                    const openDatabase = window.openDatabase;
                    const localStorage = window.localStorage;
                    try {
                        openDatabase(null, null, null, null);
                    } catch {
                        callback(true);
                        return;
                    }
                    try {
                        localStorage.setItem("test", "1");
                        localStorage.removeItem("test");
                    } catch {
                        callback(true);
                        return;
                    }
                    callback(false);
                }
            }

            // Chromium-based browsers
            function chromiumCheck() {
                const testId = String(Math.random());
                try {
                    const request = window.indexedDB.open(testId, 1);
                    request.onupgradeneeded = function(event) {
                        const db = event.target?.result;
                        try {
                            db.createObjectStore("test", { autoIncrement: true }).put(new Blob());
                        } catch (e) {
                            const message = e.message ?? e;
                            if (typeof message === "string" && message.includes("BlobURLs are not yet supported")) {
                                callback(true);
                                return;
                            }
                        } finally {
                            db.close();
                            window.indexedDB.deleteDatabase(testId);
                            checkStorageQuota();
                        }
                    };
                } catch {
                    callback(false);
                }
            }

            function checkStorageQuota() {
                if (navigator.storage?.estimate) {
                    navigator.storage.estimate().then((estimate) => {
                        const quota = estimate.quota;
                        callback(!!(quota && quota < 2e9)); // Less than 2GB suggests incognito
                    }).catch(() => {
                        callback(false);
                    });
                } else {
                    callback(false);
                }
            }

            function chromiumLegacyCheck() {
                if (self.Promise !== undefined && self.Promise.allSettled !== undefined) {
                    // Modern Chromium
                    navigator.webkitTemporaryStorage.queryUsageAndQuota(
                        (usage, quota) => {
                            const heapLimit = window.performance?.memory?.jsHeapSizeLimit ?? 1073741824;
                            callback(Math.round(quota / 1048576) < 2 * Math.round(heapLimit / 1048576));
                        },
                        (error) => {
                            reject(new Error("detectIncognito storage quota query failed: " + error.message));
                        }
                    );
                } else {
                    // Legacy Chromium
                    window.webkitRequestFileSystem(0, 1,
                        () => callback(false),
                        () => callback(true)
                    );
                }
            }

            // Determine browser and run appropriate check
            const engineId = getEngineIdentifier();
            if (engineId === 44) {
                // Safari (JavaScriptCore)
                browserName = "Safari";
                safariCheck();
            } else if (engineId === 51) {
                // Chromium (V8)
                const ua = navigator.userAgent;
                if (ua.match(/Chrome/)) {
                    if (navigator.brave !== undefined) {
                        browserName = "Brave";
                    } else if (ua.match(/Edg/)) {
                        browserName = "Edge";
                    } else if (ua.match(/OPR/)) {
                        browserName = "Opera";
                    } else {
                        browserName = "Chrome";
                    }
                } else {
                    browserName = "Chromium";
                }
                chromiumLegacyCheck();
            } else if (engineId === 25) {
                // Firefox (SpiderMonkey)
                browserName = "Firefox";
                firefoxCheck();
            } else if (isIE()) {
                browserName = "Internet Explorer";
                callback(window.indexedDB === undefined);
            } else {
                reject(new Error("detectIncognito cannot determine the browser"));
            }
        });
    }

    // iOS in-app browser detection
    function detectiOSBrowser() {
        const ua = navigator.userAgent;
        if (/CriOS/.test(ua)) return "Chrome";
        if (/FxiOS/.test(ua)) return "Firefox";
        if (/EdgiOS/.test(ua)) return "Edge";
        if (/OPiOS/.test(ua)) return "Opera";
        if (/DuckDuckGo/.test(ua)) return "DuckDuckGo";
        if (/YaBrowser/.test(ua)) return "Yandex";
        return "Safari";
    }

    // =========================================================================
    // 2. NAVIGATOR ANOMALY DETECTION
    // Detects tampered/non-native navigator properties
    //
    // NOTE: This pattern is NOT unique to Signifyd - it came from CreepJS.
    // The hasKnownToString() and [native code] detection patterns existed in
    // CreepJS at the May 2023 fork point. CreepJS uses this as part of its
    // lie detection module (documentLie()). Signifyd uses the same approach.
    // Included here for completeness but should not be considered a Signifyd
    // addition.
    // =========================================================================

    function detectNavigatorAnomalies(obj = navigator) {
        if (typeof obj !== 'object' || obj === null) return [];

        const anomalies = [];

        // Check property descriptors for non-native getters/setters
        function checkDescriptors(target) {
            const descriptors = Object.getOwnPropertyDescriptors(target);
            return Object.entries(descriptors)
                .filter(([, desc]) => desc.get || desc.set)
                .filter(([, desc]) => {
                    try {
                        const str = desc.get?.toString() || desc.set?.toString();
                        return str && !str.includes('[native code]');
                    } catch {
                        return true; // If we can't check, assume anomalous
                    }
                })
                .map(([name]) => name);
        }

        // Check function properties for non-native implementations
        function checkFunctions(target) {
            return Object.keys(target).filter(key => {
                try {
                    const value = Reflect.get(target, key);
                    if (typeof value !== 'function') return false;
                    try {
                        return !Reflect.apply(value.toString, value, []).includes('[native code]');
                    } catch {
                        return true; // If toString fails, likely tampered
                    }
                } catch {
                    return true;
                }
            });
        }

        anomalies.push(...checkDescriptors(obj));
        anomalies.push(...checkFunctions(obj));

        return [...new Set(anomalies)]; // Remove duplicates
    }

    // =========================================================================
    // 3. WORKER CONTEXT FINGERPRINTING
    // Compares navigator properties across main thread, web worker, shared worker
    //
    // NOTE: This IS genuinely new Signifyd code - architecturally different from
    // CreepJS's approach. CreepJS uses documentLie() to flag specific mismatches,
    // while lite.js has a completely separate inline worker script that collects
    // full navigator profiles independently and compares them.
    // =========================================================================

    // Worker code as a string (will be turned into a blob)
    const workerCode = `
        const PRIVACY_SIGNALS = Object.freeze({
            '1': true, 'true': true, 'yes': true,
            '0': true, 'false': true, 'no': true,
            'unspecified': true, 'null': true, 'undefined': true
        });

        const PERMISSIONS_LIST = [
            'accelerometer', 'ambient-light-sensor', 'background-fetch',
            'background-sync', 'bluetooth', 'camera', 'clipboard-read',
            'clipboard-write', 'device-info', 'display-capture', 'gamepad',
            'geolocation', 'gyroscope', 'magnetometer', 'microphone', 'midi',
            'nfc', 'notifications', 'persistent-storage', 'push',
            'screen-wake-lock', 'speaker', 'speaker-selection', 'local-fonts',
            'idle-detection', 'media-session', 'presentation', 'serial',
            'storage-access', 'window-placement', 'web-share', 'file-handling',
            'screen-capture', 'usb', 'payment-handler', 'accessibility-events',
            'file-system-access', 'battery', 'sensors'
        ];

        function detectAnomalies(obj) {
            if (typeof obj !== 'object' || obj === null) return [];
            const anomalies = [];

            const descriptors = Object.getOwnPropertyDescriptors(obj);
            Object.entries(descriptors)
                .filter(([, desc]) => desc.get || desc.set)
                .filter(([, desc]) => {
                    try {
                        const str = desc.get?.toString() || desc.set?.toString();
                        return str && !str.includes('[native code]');
                    } catch { return true; }
                })
                .forEach(([name]) => anomalies.push(name));

            Object.keys(obj).forEach(key => {
                try {
                    const value = Reflect.get(obj, key);
                    if (typeof value === 'function') {
                        try {
                            if (!Reflect.apply(value.toString, value, []).includes('[native code]')) {
                                anomalies.push(key);
                            }
                        } catch { anomalies.push(key); }
                    }
                } catch { anomalies.push(key); }
            });

            return [...new Set(anomalies)];
        }

        async function getBluetoothAvailability() {
            if (!navigator.bluetooth?.getAvailability) return undefined;
            try {
                return await navigator.bluetooth.getAvailability();
            } catch {
                return false;
            }
        }

        async function getPermissions() {
            if (!navigator.permissions) return null;
            try {
                const results = await Promise.all(
                    PERMISSIONS_LIST.map(async name => {
                        try {
                            const result = await navigator.permissions.query({ name });
                            return { name, state: result.state };
                        } catch {
                            return { name, state: 'unknown' };
                        }
                    })
                );
                return results.reduce((acc, { name, state }) => {
                    acc[state] = acc[state] || [];
                    acc[state].push(name);
                    return acc;
                }, { granted: [], denied: [], prompt: [] });
            } catch {
                return null;
            }
        }

        function getWebGLInfo() {
            try {
                const canvas = typeof OffscreenCanvas !== 'undefined'
                    ? new OffscreenCanvas(256, 256)
                    : null;
                if (!canvas) return { webglVendor: null, webglRenderer: null };

                const gl = canvas.getContext('webgl');
                if (!gl) return { webglVendor: null, webglRenderer: null };

                const ext = gl.getExtension('WEBGL_debug_renderer_info');
                if (!ext) return { webglVendor: null, webglRenderer: null };

                return {
                    webglVendor: gl.getParameter(ext.UNMASKED_VENDOR_WEBGL),
                    webglRenderer: gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)
                };
            } catch {
                return { webglVendor: null, webglRenderer: null };
            }
        }

        async function collectProfile() {
            const nav = navigator;
            const uaData = nav.userAgentData && await nav.userAgentData.getHighEntropyValues([
                'brands', 'mobile', 'platform', 'architecture', 'bitness',
                'formFactor', 'fullVersionList', 'model', 'platformVersion',
                'uaFullVersion', 'wow64'
            ]).catch(() => ({}));

            return {
                context: 'unknown',
                timezone: new Date().getTimezoneOffset(),
                navigator: {
                    bluetoothAvailability: await getBluetoothAvailability(),
                    permissions: await getPermissions(),
                    platform: nav.platform,
                    userAgent: nav.userAgent,
                    appVersion: nav.appVersion,
                    hardwareConcurrency: nav.hardwareConcurrency,
                    deviceMemory: nav.deviceMemory || null,
                    language: nav.language,
                    userAgentData: {
                        ...uaData,
                        brands: nav.userAgentData?.brands || [],
                        mobile: nav.userAgentData?.mobile || false
                    },
                    webdriver: nav.webdriver,
                    maxTouchPoints: nav.maxTouchPoints ?? null,
                    vendor: nav.vendor,
                    oscpu: nav.oscpu,
                    webGL: getWebGLInfo()
                },
                intl: Intl.DateTimeFormat().resolvedOptions(),
                anomalies: detectAnomalies(navigator)
            };
        }

        // Shared Worker handler
        if (typeof SharedWorkerGlobalScope !== 'undefined' && self instanceof SharedWorkerGlobalScope) {
            self.onconnect = (e) => {
                const port = e.ports[0];
                port.onmessage = async () => {
                    const profile = await collectProfile();
                    profile.context = 'shared-worker';
                    port.postMessage(profile);
                };
                port.start();
            };
        }
        // Web Worker handler
        else if (typeof WorkerGlobalScope !== 'undefined' && self instanceof WorkerGlobalScope) {
            self.onmessage = async () => {
                const profile = await collectProfile();
                profile.context = 'web-worker';
                self.postMessage(profile);
            };
        }
    `;

    async function runWorkerFingerprint() {
        const results = {
            main: null,
            webWorker: null,
            sharedWorker: null,
            differences: []
        };

        // Main thread profile
        results.main = {
            context: 'main-thread',
            timezone: new Date().getTimezoneOffset(),
            navigator: {
                platform: navigator.platform,
                userAgent: navigator.userAgent,
                appVersion: navigator.appVersion,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory || null,
                language: navigator.language,
                webdriver: navigator.webdriver,
                maxTouchPoints: navigator.maxTouchPoints ?? null,
                vendor: navigator.vendor
            },
            anomalies: detectNavigatorAnomalies(navigator)
        };

        // Create Web Worker
        try {
            const blob = new Blob([workerCode], { type: 'application/javascript' });
            const url = URL.createObjectURL(blob);

            // Web Worker
            const webWorkerPromise = new Promise((resolve) => {
                try {
                    const worker = new Worker(url);
                    const timeout = setTimeout(() => {
                        worker.terminate();
                        resolve(null);
                    }, 5000);

                    worker.onmessage = (e) => {
                        clearTimeout(timeout);
                        worker.terminate();
                        resolve(e.data);
                    };
                    worker.onerror = () => {
                        clearTimeout(timeout);
                        worker.terminate();
                        resolve(null);
                    };
                    worker.postMessage('collect');
                } catch {
                    resolve(null);
                }
            });

            // Shared Worker
            const sharedWorkerPromise = new Promise((resolve) => {
                try {
                    const worker = new SharedWorker(url);
                    const timeout = setTimeout(() => {
                        resolve(null);
                    }, 5000);

                    worker.port.onmessage = (e) => {
                        clearTimeout(timeout);
                        resolve(e.data);
                    };
                    worker.onerror = () => {
                        clearTimeout(timeout);
                        resolve(null);
                    };
                    worker.port.start();
                    worker.port.postMessage('collect');
                } catch {
                    resolve(null);
                }
            });

            const [webWorkerResult, sharedWorkerResult] = await Promise.all([
                webWorkerPromise,
                sharedWorkerPromise
            ]);

            results.webWorker = webWorkerResult;
            results.sharedWorker = sharedWorkerResult;

            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('Worker fingerprint error:', e);
        }

        // Compare results for differences
        function compareObjects(obj1, obj2, path = '') {
            const diffs = [];
            if (!obj1 || !obj2) return diffs;

            const keys = new Set([...Object.keys(obj1), ...Object.keys(obj2)]);
            for (const key of keys) {
                const fullPath = path ? `${path}.${key}` : key;
                const val1 = obj1[key];
                const val2 = obj2[key];

                if (typeof val1 === 'object' && typeof val2 === 'object' && val1 && val2) {
                    diffs.push(...compareObjects(val1, val2, fullPath));
                } else if (JSON.stringify(val1) !== JSON.stringify(val2)) {
                    diffs.push({ path: fullPath, main: val1, worker: val2 });
                }
            }
            return diffs;
        }

        if (results.webWorker) {
            results.differences.push({
                comparison: 'main-vs-webworker',
                diffs: compareObjects(results.main.navigator, results.webWorker.navigator)
            });
        }
        if (results.sharedWorker) {
            results.differences.push({
                comparison: 'main-vs-sharedworker',
                diffs: compareObjects(results.main.navigator, results.sharedWorker.navigator)
            });
        }

        return results;
    }

    // =========================================================================
    // 4. IN-APP WEBVIEW DETECTION
    // Detects if running inside an in-app browser (iOS)
    // =========================================================================

    function detectInAppWebView() {
        const ua = navigator.userAgent;
        const result = {
            isInAppWebView: false,
            browser: null,
            indicators: []
        };

        // iOS in-app browser indicators
        if (/iPhone|iPad|iPod/.test(ua)) {
            if (/CriOS/.test(ua)) {
                result.browser = 'Chrome iOS';
            } else if (/FxiOS/.test(ua)) {
                result.browser = 'Firefox iOS';
            } else if (/EdgiOS/.test(ua)) {
                result.browser = 'Edge iOS';
            } else if (/OPiOS/.test(ua)) {
                result.browser = 'Opera iOS';
            } else if (/DuckDuckGo/.test(ua)) {
                result.browser = 'DuckDuckGo iOS';
            } else if (/YaBrowser/.test(ua)) {
                result.browser = 'Yandex iOS';
            } else if (/Safari/.test(ua)) {
                result.browser = 'Safari';
            } else {
                // Likely an in-app webview if no known browser identifier
                result.isInAppWebView = true;
                result.indicators.push('No known iOS browser identifier');
            }

            // Additional webview indicators
            if (/FBAN|FBAV/.test(ua)) {
                result.isInAppWebView = true;
                result.browser = 'Facebook WebView';
                result.indicators.push('Facebook app identifier');
            }
            if (/Instagram/.test(ua)) {
                result.isInAppWebView = true;
                result.browser = 'Instagram WebView';
                result.indicators.push('Instagram app identifier');
            }
            if (/Twitter/.test(ua)) {
                result.isInAppWebView = true;
                result.browser = 'Twitter WebView';
                result.indicators.push('Twitter app identifier');
            }
            if (/LinkedInApp/.test(ua)) {
                result.isInAppWebView = true;
                result.browser = 'LinkedIn WebView';
                result.indicators.push('LinkedIn app identifier');
            }
        }

        // Android WebView detection
        if (/Android/.test(ua)) {
            if (/; wv\)/.test(ua) || /Version\/[\d.]+.*Chrome/.test(ua)) {
                result.isInAppWebView = true;
                result.indicators.push('Android WebView indicator');
            }
        }

        // Check for missing features that indicate WebView
        if (typeof window.matchMedia === 'undefined') {
            result.indicators.push('Missing matchMedia');
        }
        if (typeof window.indexedDB === 'undefined') {
            result.indicators.push('Missing indexedDB');
        }

        return result;
    }

    // =========================================================================
    // 5. COOKIE MONSTER - Cookie manipulation tracking
    // =========================================================================

    function cookieMonster() {
        const result = {
            cookiesEnabled: false,
            thirdPartyCookiesEnabled: null,
            testCookieSet: false,
            testCookieRead: false,
            sessionStorageEnabled: false,
            localStorageEnabled: false,
            indexedDBEnabled: false
        };

        // Test cookies
        try {
            result.cookiesEnabled = navigator.cookieEnabled;

            // Set a test cookie
            const testValue = 'test_' + Math.random().toString(36).substr(2, 9);
            document.cookie = `__signifyd_test=${testValue}; path=/; SameSite=Lax`;
            result.testCookieSet = true;

            // Read it back
            const cookies = document.cookie.split(';').map(c => c.trim());
            const testCookie = cookies.find(c => c.startsWith('__signifyd_test='));
            result.testCookieRead = testCookie?.includes(testValue) || false;

            // Clean up
            document.cookie = '__signifyd_test=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
        } catch (e) {
            result.cookiesEnabled = false;
        }

        // Test sessionStorage
        try {
            const testKey = '__signifyd_ss_test';
            sessionStorage.setItem(testKey, 'test');
            result.sessionStorageEnabled = sessionStorage.getItem(testKey) === 'test';
            sessionStorage.removeItem(testKey);
        } catch {
            result.sessionStorageEnabled = false;
        }

        // Test localStorage
        try {
            const testKey = '__signifyd_ls_test';
            localStorage.setItem(testKey, 'test');
            result.localStorageEnabled = localStorage.getItem(testKey) === 'test';
            localStorage.removeItem(testKey);
        } catch {
            result.localStorageEnabled = false;
        }

        // Test IndexedDB
        try {
            result.indexedDBEnabled = typeof indexedDB !== 'undefined' && indexedDB !== null;
        } catch {
            result.indexedDBEnabled = false;
        }

        return result;
    }

    // =========================================================================
    // MAIN COLLECTION FUNCTION
    // =========================================================================

    async function collectFingerprint() {
        const startTime = performance.now();

        // 1. Incognito detection
        try {
            const incognitoResult = await detectIncognito();
            // Enhance with iOS browser detection
            if (incognitoResult.browserName === 'Safari' && /iPhone|iPad|iPod/.test(navigator.userAgent)) {
                incognitoResult.browserName = detectiOSBrowser();
            }
            results.incognito = incognitoResult;
        } catch (e) {
            results.incognito = { error: e.message };
        }

        // 2. Navigator anomalies
        try {
            results.navigatorAnomalies = detectNavigatorAnomalies(navigator);
        } catch (e) {
            results.navigatorAnomalies = { error: e.message };
        }

        // 3. Worker comparison
        try {
            results.workerComparison = await runWorkerFingerprint();
        } catch (e) {
            results.workerComparison = { error: e.message };
        }

        // 4. In-app WebView detection
        try {
            results.inAppWebView = detectInAppWebView();
        } catch (e) {
            results.inAppWebView = { error: e.message };
        }

        // 5. Cookie monster
        try {
            results.cookieMonster = cookieMonster();
        } catch (e) {
            results.cookieMonster = { error: e.message };
        }

        results.collectionTime = performance.now() - startTime;
        results.timestamp = new Date().toISOString();

        return results;
    }

    // Export for browser
    window.SignifydUniqueFingerprint = {
        collect: collectFingerprint,
        detectIncognito,
        detectNavigatorAnomalies,
        runWorkerFingerprint,
        detectInAppWebView,
        cookieMonster
    };

    // Auto-run if the page is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            collectFingerprint().then(r => {
                console.log('Signifyd-Unique Fingerprint collected:', r);
                window.dispatchEvent(new CustomEvent('signifyd-fingerprint-ready', { detail: r }));
            });
        });
    } else {
        collectFingerprint().then(r => {
            console.log('Signifyd-Unique Fingerprint collected:', r);
            window.dispatchEvent(new CustomEvent('signifyd-fingerprint-ready', { detail: r }));
        });
    }

})();
