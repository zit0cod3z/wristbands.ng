/**
 * WristbandsNG PWA Scanner – Offline-capable QR check-in
 * Completely rewritten offline engine — bulletproof cache + lookup
 */

const DB_NAME     = 'wristbandsng_scanner_v2';  // bumped version to force fresh DB
const DB_VERSION  = 1;
const STORE_REGS  = 'registrations';
const STORE_QUEUE = 'offline_queue';
const STORE_REG_QUEUE = 'offline_reg_queue';  // NEW: offline registration queue

let db           = null;
let stream       = null;
let scanning     = false;
let facingMode   = 'environment';
let lastCode     = '';
let lastCodeTime = 0;
let isOnline     = navigator.onLine;
let EVENT_PK, SCAN_URL, OFFLINE_REGS_URL, SYNC_URL, SYNC_REG_URL, STATS_URL, CSRF_TOKEN;

// ── Bootstrap ─────────────────────────────────────────────────────────────
window.forceRefreshCache = async function() {
    updateCacheInfo(0, null, 'Refreshing…');
    await refreshRegistrationCache();
};

window.initScanner = function(config) {
    EVENT_PK         = config.event_pk;
    SCAN_URL         = config.scan_url;
    OFFLINE_REGS_URL = config.offline_regs_url;
    SYNC_URL         = config.sync_url;
    SYNC_REG_URL     = config.sync_reg_url;
    STATS_URL        = config.stats_url;
    CSRF_TOKEN       = config.csrf_token;

    openDB().then(async () => {
        // Step 1: seed IndexedDB from preloaded page data immediately
        if (config.preloaded_regs && config.preloaded_regs.length > 0) {
            await seedCacheFromPreloaded(config.preloaded_regs);
        }

        await loadCachedStats();
        updateOnlineStatus();

        // Step 2: also try to refresh from server if online (gets latest data)
        if (navigator.onLine) {
            refreshRegistrationCache();  // non-blocking
            flushRegQueue();             // flush any pending offline registrations
        }

        startCamera();
        startPolling();
        registerServiceWorker();
    });

    window.addEventListener('online', async () => {
        isOnline = true;
        updateOnlineStatus();
        await refreshRegistrationCache();
        await flushQueue();
        await flushRegQueue();   // also flush offline registrations
    });
    window.addEventListener('offline', () => {
        isOnline = false;
        updateOnlineStatus();
    });

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', e => {
            if (e.data && e.data.type === 'FLUSH_QUEUE') flushQueue();
        });
    }
};

// ── IndexedDB helpers ─────────────────────────────────────────────────────
function openDB() {
    return new Promise((resolve) => {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = e => {
            const d = e.target.result;
            if (!d.objectStoreNames.contains(STORE_REGS)) {
                const s = d.createObjectStore(STORE_REGS, { keyPath: 'code' });
                s.createIndex('by_id', 'id', { unique: false });
            }
            if (!d.objectStoreNames.contains(STORE_QUEUE)) {
                d.createObjectStore(STORE_QUEUE, { autoIncrement: true });
            }
            if (!d.objectStoreNames.contains(STORE_REG_QUEUE)) {
                d.createObjectStore(STORE_REG_QUEUE, { autoIncrement: true });
            }
        };
        req.onsuccess = e => { db = e.target.result; resolve(); };
        req.onerror   = () => { console.warn('IndexedDB unavailable'); resolve(); };
    });
}

function dbTx(store, mode, fn) {
    return new Promise((resolve) => {
        if (!db) return resolve(null);
        try {
            const tx  = db.transaction(store, mode);
            const req = fn(tx.objectStore(store));
            if (req) {
                req.onsuccess = () => resolve(req.result ?? null);
                req.onerror   = () => resolve(null);
            } else {
                tx.oncomplete = () => resolve(true);
                tx.onerror    = () => resolve(null);
            }
        } catch(e) { resolve(null); }
    });
}

const dbGet    = (store, key)   => dbTx(store, 'readonly',  s => s.get(key));
const dbGetAll = (store)        => dbTx(store, 'readonly',  s => s.getAll()).then(r => r || []);
const dbCount  = (store)        => dbTx(store, 'readonly',  s => s.count()).then(r => r || 0);
const dbPut    = (store, value) => dbTx(store, 'readwrite', s => { s.put(value); return null; });
const dbAdd    = (store, value) => dbTx(store, 'readwrite', s => { s.add(value); return null; });
const dbClear  = (store)        => dbTx(store, 'readwrite', s => { s.clear(); return null; });

// ── Registration cache ────────────────────────────────────────────────────
async function seedCacheFromPreloaded(regs) {
    // Called on every page load with data embedded directly in the HTML
    // This guarantees the cache is always populated — no network fetch needed
    await dbClear(STORE_REGS);
    for (const reg of regs) {
        await dbPut(STORE_REGS, {
            code:           (reg.code || '').trim(),
            id:             (reg.id   || '').trim(),
            external_qr_id: (reg.external_qr_id || '').trim(),
            name:           reg.name  || '',
            email:          reg.email || '',
            checked_in:     !!reg.checked_in,
            checked_in_at:  reg.checked_in_at || null,
        });
    }
    console.log('[WBNG] Seeded', regs.length, 'registrations from page data');
    updateCacheInfo(regs.length, new Date().toISOString());
}

async function refreshRegistrationCache() {
    try {
        const res = await fetch(OFFLINE_REGS_URL, { credentials: 'include' });
        if (!res.ok) {
            console.warn('[WBNG] Cache refresh failed, status:', res.status);
            return;
        }
        const data = await res.json();
        if (!data.registrations || !Array.isArray(data.registrations)) return;

        await dbClear(STORE_REGS);

        for (const reg of data.registrations) {
            // Normalise — store code, id AND external_qr_id for robust lookup
            await dbPut(STORE_REGS, {
                code:           (reg.code || '').trim(),
                id:             (reg.id   || '').trim(),
                external_qr_id: (reg.external_qr_id || '').trim(),
                name:           reg.name  || '',
                email:          reg.email || '',
                checked_in:     !!reg.checked_in,
                checked_in_at:  reg.checked_in_at || null,
            });
        }

        const count = data.registrations.length;
        console.log(`[WBNG] Cached ${count} registrations. Sample:`,
            data.registrations.slice(0,3).map(r => r.code));

        updateCacheInfo(count, data.cached_at);
        updateStats(data.registrations.filter(r => r.checked_in).length, count);

    } catch(e) {
        console.warn('[WBNG] Cache refresh error:', e.message);
    }
}

async function loadCachedStats() {
    const all = await dbGetAll(STORE_REGS);
    if (all.length) {
        updateStats(all.filter(r => r.checked_in).length, all.length);
        updateCacheInfo(all.length, null);
    } else {
        updateCacheInfo(0, null);
    }
    const ciQueue  = await dbCount(STORE_QUEUE);
    const regQueue = await dbCount(STORE_REG_QUEUE);
    updateQueueBadge(ciQueue, regQueue);
}

// ── QR code parser ────────────────────────────────────────────────────────
function parseQR(rawCode) {
    // Format: WRISTBANDSNG|<uuid>|<reg_code>|<event_title>
    //      or EVENTPRO|<uuid>|<reg_code>|<event_title>   (legacy)
    //      or plain reg_code (manual entry)
    const raw = (rawCode || '').trim();
    if (raw.startsWith('WRISTBANDSNG|') || raw.startsWith('EVENTPRO|')) {
        const parts = raw.split('|');
        return {
            id:   (parts[1] || '').trim(),
            code: (parts[2] || '').trim(),
            raw,
        };
    }
    return { id: null, code: raw, raw };
}

// ── Core scan logic ───────────────────────────────────────────────────────
async function processCode(rawCode) {
    scanning = false;  // pause while processing

    // Always try online first — but with a short timeout
    // If it fails for ANY reason (no internet, session expired, etc.) → offline
    let handled = false;

    if (navigator.onLine) {
        handled = await processOnline(rawCode);
    }

    if (!handled) {
        await processOffline(rawCode);
    }

    setTimeout(() => {
        if (stream) { scanning = true; requestAnimationFrame(tick); }
    }, 2500);
}

// Returns true if handled online, false if should fall to offline
async function processOnline(rawCode) {
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000); // 8s timeout

        const res = await fetch(SCAN_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'include',
            body: JSON.stringify({ code: rawCode }),
            signal: controller.signal,
        });
        clearTimeout(timeout);

        if (res.redirected || res.status === 302 || res.status === 403 || res.status === 401) {
            showToast('error', '🔒', 'Session Expired', 'Please log in again', rawCode);
            setTimeout(() => { window.location.href = '/accounts/login/?next=' + window.location.pathname; }, 2000);
            return true; // handled (with error)
        }

        const ct = res.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
            // Not JSON — session redirect, fall to offline
            return false;
        }

        const data = await res.json();
        handleResult(data.status, data.message, data.data || {}, rawCode, false);

        // Keep local cache in sync after successful online scan
        if (data.status === 'success' && data.data) {
            const { id, code } = parseQR(rawCode);
            const lookupKey = data.data.code || code;
            const cached = await dbGet(STORE_REGS, lookupKey);
            if (cached) {
                cached.checked_in    = true;
                cached.checked_in_at = data.data.checked_in_at;
                await dbPut(STORE_REGS, cached);
            }
        }
        if (data.checked_in_total !== undefined) {
            updateStats(data.checked_in_total, data.total);
        }
        return true;

    } catch(e) {
        // AbortError = timeout, TypeError = no network
        console.warn('[WBNG] Online scan failed, falling to offline:', e.message);
        return false;
    }
}

async function processOffline(rawCode) {
    const { id, code } = parseQR(rawCode);

    console.log('[WBNG] Offline lookup — id:', id, 'code:', code);

    // Get all cached registrations for debugging
    const all = await dbGetAll(STORE_REGS);
    console.log('[WBNG] Cache size:', all.length, '| Sample codes:', all.slice(0,5).map(r=>r.code));

    if (all.length === 0) {
        showToast('not_found', '📵', 'Cache Empty',
            'No guests cached. Open scanner while online first to download the guest list, then you can scan offline.',
            code);
        return;
    }

    let reg = null;

    // 1. Exact code match (primary key — WristbandsNG reg code)
    if (code) reg = await dbGet(STORE_REGS, code);

    // 2. External QR ID exact match — THE KEY STRATEGY for imported guests
    // When staff scans the original external QR, this finds the imported guest
    if (!reg && code) {
        reg = all.find(r => r.external_qr_id && r.external_qr_id === code) || null;
    }

    // 3. Case-insensitive code match
    if (!reg && code) {
        const lower = code.toLowerCase();
        reg = all.find(r => r.code && r.code.toLowerCase() === lower) || null;
    }

    // 4. Case-insensitive external QR ID match
    if (!reg && code) {
        const lower = code.toLowerCase();
        reg = all.find(r => r.external_qr_id && r.external_qr_id.toLowerCase() === lower) || null;
    }

    // 5. UUID id match
    if (!reg && id) {
        reg = all.find(r => r.id && r.id === id) || null;
    }

    // 6. UUID case-insensitive
    if (!reg && id) {
        const lower = id.toLowerCase();
        reg = all.find(r => r.id && r.id.toLowerCase() === lower) || null;
    }

    // 7. EXT- prefix strip: "EXT-51" → look for external_qr_id="51"
    if (!reg && code && code.toUpperCase().startsWith('EXT-')) {
        const stripped = code.substring(4).trim();
        reg = all.find(r => r.external_qr_id && r.external_qr_id === stripped) || null;
        if (!reg) {
            const lower = stripped.toLowerCase();
            reg = all.find(r => r.external_qr_id && r.external_qr_id.toLowerCase() === lower) || null;
        }
    }

    // 8. Partial code match (last resort)
    if (!reg && code && code.length >= 4) {
        reg = all.find(r => r.code && (r.code.includes(code) || code.includes(r.code))) || null;
    }

    console.log('[WBNG] Lookup result:', reg ? `Found: ${reg.name} (${reg.code})` : 'NOT FOUND');

    if (!reg) {
        showToast('not_found', '❌', 'Not Found',
            `Guest not in offline cache (${all.length} cached). Code scanned: ${code}. Tap ↺ Refresh to update cache.`,
            code);
        return;
    }

    if (reg.checked_in) {
        showToast('duplicate', '⚠️', reg.name,
            `Already checked in at ${reg.checked_in_at || '—'}`, reg.code);
        addRecent('dup', reg.name, new Date().toLocaleTimeString(), true);
        return;
    }

    // Mark checked in locally
    reg.checked_in    = true;
    reg.checked_in_at = new Date().toLocaleTimeString();
    await dbPut(STORE_REGS, reg);

    // Queue for server sync
    await dbAdd(STORE_QUEUE, {
        code:       rawCode,
        scanned_at: new Date().toISOString(),
        event_pk:   EVENT_PK,
    });

    const ciQueue = await dbCount(STORE_QUEUE);
    updateQueueBadge(ciQueue, undefined);

    const updated = await dbGetAll(STORE_REGS);
    updateStats(updated.filter(r => r.checked_in).length, updated.length);

    showToast('offline_queued', '📶', reg.name,
        'Checked in offline — will sync when online', reg.code);
    addRecent('ok', reg.name, new Date().toLocaleTimeString(), true);

    if (navigator.vibrate) navigator.vibrate([80, 40, 80]);
}

// ── Flush offline queue ───────────────────────────────────────────────────
async function flushQueue() {
    const queue = await dbGetAll(STORE_QUEUE);
    if (!queue.length) return;

    updateStatusBar('syncing', `Syncing ${queue.length} offline check-in${queue.length !== 1 ? 's' : ''}…`);

    try {
        const res  = await fetch(SYNC_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            credentials: 'include',
            body: JSON.stringify({ queue }),
        });
        const data = await res.json();
        if (data.synced !== undefined) {
            await dbClear(STORE_QUEUE);
            updateQueueBadge(0, undefined);
            updateStats(data.checked_in_total, data.total);
            updateStatusBar('online', `Synced ${data.synced} check-in${data.synced !== 1 ? 's' : ''} ✓`);
            addRecent('ok', `Synced ${data.synced} offline check-ins`, new Date().toLocaleTimeString(), false);
            await refreshRegistrationCache();
        }
    } catch(e) {
        updateStatusBar('offline', 'Sync failed — will retry when online');
    }
}

// ── Offline Registration ──────────────────────────────────────────────────

window.openOfflineRegModal = function() {
    document.getElementById('offlineRegModal').classList.add('open');
    document.getElementById('regName').focus();
};

window.closeOfflineRegModal = function() {
    document.getElementById('offlineRegModal').classList.remove('open');
    document.getElementById('offlineRegForm').reset();
};

window.submitOfflineReg = async function(e) {
    e.preventDefault();
    const name  = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();

    if (!name || !email) return;

    // Check if already in local cache (duplicate prevention)
    const all = await dbGetAll(STORE_REGS);
    const duplicate = all.find(r => r.email && r.email.toLowerCase() === email.toLowerCase());
    if (duplicate) {
        showToast('duplicate', '⚠️', name, 'This email is already registered for this event.', email);
        closeOfflineRegModal();
        return;
    }

    const offlineId = 'offline_' + Date.now() + '_' + Math.random().toString(36).substr(2,6);

    if (navigator.onLine) {
        // Online — register directly via server
        await registerOnline(name, email, offlineId);
    } else {
        // Offline — queue it
        await registerOffline(name, email, offlineId);
    }

    closeOfflineRegModal();
};

async function registerOnline(name, email, offlineId) {
    try {
        const res = await fetch(SYNC_REG_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'include',
            body: JSON.stringify({ registrations: [{ name, email, offline_id: offlineId, fields: {} }] }),
        });

        const ct = res.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
            // Session expired — queue offline instead
            await registerOffline(name, email, offlineId);
            return;
        }

        const data = await res.json();
        const result = data.results && data.results[0];

        if (result && result.status === 'created') {
            // Add to local cache so they can be scanned immediately
            await dbPut(STORE_REGS, {
                code:        result.code,
                id:          offlineId,
                name:        name,
                email:       email,
                checked_in:  false,
                checked_in_at: null,
            });
            showToast('success', '✅', name, `Registered! Code: ${result.code}. Confirmation email sent.`, result.code);
            addRecent('ok', `Registered: ${name}`, new Date().toLocaleTimeString(), false);
            if (navigator.vibrate) navigator.vibrate([80, 40, 80]);
        } else if (result && result.status === 'duplicate') {
            showToast('duplicate', '⚠️', name, 'Already registered with this email.', email);
        } else {
            showToast('error', '❌', name, 'Registration failed. Queued for retry.', email);
            await registerOffline(name, email, offlineId);
        }
    } catch(e) {
        // Network error — queue offline
        await registerOffline(name, email, offlineId);
    }
}

async function registerOffline(name, email, offlineId) {
    // Save to offline registration queue
    await dbAdd(STORE_REG_QUEUE, {
        offline_id:  offlineId,
        name:        name,
        email:       email,
        event_pk:    EVENT_PK,
        queued_at:   new Date().toISOString(),
        fields:      {},
    });

    // Add a temporary entry to the local cache so they can be scanned immediately
    const tempCode = 'TEMP-' + offlineId.substr(-6).toUpperCase();
    await dbPut(STORE_REGS, {
        code:        tempCode,
        id:          offlineId,
        name:        name,
        email:       email,
        checked_in:  false,
        checked_in_at: null,
        is_temp:     true,
    });

    const qCount = await dbCount(STORE_REG_QUEUE);
    updateQueueBadge(undefined, qCount);

    showToast('offline_queued', '📶', name,
        `Queued offline — will register & send QR when online. Temp code: ${tempCode}`,
        tempCode);
    addRecent('queued', `Queued: ${name}`, new Date().toLocaleTimeString(), true);
    if (navigator.vibrate) navigator.vibrate([80, 40, 80]);
}

async function flushRegQueue() {
    const queue = await dbGetAll(STORE_REG_QUEUE);
    if (!queue.length) return;

    updateStatusBar('syncing', `Syncing ${queue.length} offline registration${queue.length !== 1 ? 's' : ''}…`);

    try {
        const payload = queue.map(item => ({
            name:       item.name,
            email:      item.email,
            offline_id: item.offline_id,
            fields:     item.fields || {},
        }));

        const res = await fetch(SYNC_REG_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            credentials: 'include',
            body: JSON.stringify({ registrations: payload }),
        });

        const data = await res.json();

        if (data.results) {
            // Remove temp entries and replace with real codes
            for (const result of data.results) {
                if (result.status === 'created' && result.offline_id) {
                    // Remove temp entry
                    const tempCode = 'TEMP-' + result.offline_id.substr(-6).toUpperCase();
                    const tempEntry = await dbGet(STORE_REGS, tempCode);
                    if (tempEntry) {
                        // Delete temp, add real
                        const tx = db.transaction(STORE_REGS, 'readwrite');
                        tx.objectStore(STORE_REGS).delete(tempCode);
                        await new Promise(r => { tx.oncomplete = r; tx.onerror = r; });
                    }
                    // Add real registration to cache
                    await dbPut(STORE_REGS, {
                        code:        result.code,
                        id:          result.offline_id,
                        name:        result.name,
                        email:       result.email,
                        checked_in:  false,
                        checked_in_at: null,
                    });
                }
            }

            await dbClear(STORE_REG_QUEUE);
            updateQueueBadge(undefined, 0);
            updateStatusBar('online',
                `Synced ${data.created} registration${data.created !== 1 ? 's' : ''} ✓`);
            addRecent('ok',
                `Synced ${data.created} offline registration${data.created !== 1 ? 's' : ''}`,
                new Date().toLocaleTimeString(), false);
            await refreshRegistrationCache();
        }
    } catch(e) {
        updateStatusBar('offline', 'Reg sync failed — will retry when online');
    }
}

// ── Camera ────────────────────────────────────────────────────────────────
window.startCamera = async function() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showCameraBlockedUI(); return;
    }
    try {
        if (stream) stream.getTracks().forEach(t => t.stop());
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        const video = document.getElementById('pwaVideo');
        video.srcObject = stream;
        video.play();
        scanning = true;
        document.getElementById('btnCamToggle').classList.add('active');
        const blocked = document.getElementById('cameraBlockedMsg');
        if (blocked) blocked.style.display = 'none';
        requestAnimationFrame(tick);
    } catch(e) {
        if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
            showCameraPermissionDeniedUI();
        } else {
            showCameraBlockedUI();
        }
    }
};

function showCameraBlockedUI() {
    scanning = false;
    const wrap = document.getElementById('cameraWrap');
    if (!wrap) return;
    const isHttp = location.protocol === 'http:' && !['localhost','127.0.0.1'].includes(location.hostname);
    wrap.innerHTML = `
      <div id="cameraBlockedMsg" style="background:rgba(172,35,118,.1);border:2px dashed rgba(172,35,118,.4);
           border-radius:14px;padding:24px 20px;text-align:center;margin:12px">
        <div style="font-size:36px;margin-bottom:10px">🔒</div>
        <div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:8px">
          ${isHttp ? 'HTTPS Required for Camera' : 'Camera Not Available'}
        </div>
        <div style="font-size:12px;color:#b09aa8;line-height:1.7;text-align:left">
          ${isHttp
            ? 'Browsers block camera on HTTP. Use HTTPS on your live domain, or enable the Chrome flag for local testing.<br><br><strong style="color:#fff">Manual entry still works</strong> — type the registration code below.'
            : 'Camera unavailable. Use manual entry below.'}
        </div>
        <button onclick="window.startCamera()" style="margin-top:12px;background:linear-gradient(135deg,#ac2376,#e6573f);
          color:#fff;border:none;border-radius:8px;padding:8px 16px;font-weight:700;cursor:pointer">↺ Retry</button>
      </div>`;
}

function showCameraPermissionDeniedUI() {
    scanning = false;
    const wrap = document.getElementById('cameraWrap');
    if (!wrap) return;
    wrap.innerHTML = `
      <div style="background:rgba(239,68,68,.1);border:2px dashed rgba(239,68,68,.3);
           border-radius:14px;padding:24px 20px;text-align:center;margin:12px">
        <div style="font-size:36px;margin-bottom:10px">🚫</div>
        <div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:8px">Camera Permission Denied</div>
        <div style="font-size:12px;color:#b09aa8;line-height:1.7">
          Tap the 🔒 in your browser bar → Site Settings → Camera → Allow, then retry.
        </div>
        <button onclick="window.startCamera()" style="margin-top:14px;background:linear-gradient(135deg,#ac2376,#e6573f);
          color:#fff;border:none;border-radius:8px;padding:8px 16px;font-weight:700;cursor:pointer">↺ Retry</button>
      </div>`;
}

window.stopCamera = function() {
    scanning = false;
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    const btn = document.getElementById('btnCamToggle');
    if (btn) btn.classList.remove('active');
};

window.toggleCamera = function() { scanning ? window.stopCamera() : window.startCamera(); };
window.flipCamera   = function() {
    facingMode = facingMode === 'environment' ? 'user' : 'environment';
    if (scanning) window.startCamera();
};

function tick() {
    if (!scanning) return;
    const video  = document.getElementById('pwaVideo');
    const canvas = document.getElementById('pwaCanvas');
    if (video && video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width  = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        const img  = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(img.data, img.width, img.height, { inversionAttempts: 'dontInvert' });
        if (code) {
            const now = Date.now();
            if (code.data !== lastCode || now - lastCodeTime > 3000) {
                lastCode = code.data;
                lastCodeTime = now;
                processCode(code.data);
            }
        }
    }
    requestAnimationFrame(tick);
}

// ── Result display ────────────────────────────────────────────────────────
function handleResult(status, message, reg, rawCode, offline) {
    const icons = { success:'✅', duplicate:'⚠️', denied:'🚫', not_found:'❌', offline_queued:'📶', error:'⚠️' };
    showToast(status, icons[status] || '❓', reg.name || '—', message, reg.code || rawCode);
    if (navigator.vibrate) {
        if (status === 'success' || status === 'offline_queued') navigator.vibrate([80,40,80]);
        else if (status === 'duplicate') navigator.vibrate(250);
        else navigator.vibrate([150,80,150]);
    }
    const dotClass = (status === 'success' || status === 'offline_queued') ? 'ok'
                   : status === 'duplicate' ? 'dup' : 'bad';
    addRecent(dotClass, reg.name || rawCode, new Date().toLocaleTimeString(), offline);
}

function showToast(type, icon, name, msg, code) {
    const t = document.getElementById('resultToast');
    if (!t) return;
    t.className = `result-toast ${type}`;
    t.style.display = 'block';
    t.querySelector('.r-icon').textContent = icon;
    t.querySelector('.r-name').textContent = name;
    t.querySelector('.r-msg').textContent  = msg;
    t.querySelector('.r-code').textContent = code || '';
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => { t.style.display = 'none'; }, 5000);
}

function addRecent(dotClass, name, time, offline) {
    const list = document.getElementById('recentList');
    if (!list) return;
    const el = document.createElement('div');
    el.className = 'scan-item';
    el.innerHTML = `
      <div class="scan-dot ${dotClass}"></div>
      <div class="scan-name">${name}</div>
      ${offline ? '<span class="scan-offline-tag">OFFLINE</span>' : ''}
      <div class="scan-time">${time}</div>`;
    list.insertBefore(el, list.firstChild);
    if (list.children.length > 15) list.removeChild(list.lastChild);
}

// ── UI helpers ────────────────────────────────────────────────────────────
function updateStats(ci, total) {
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set('statCI',        ci);
    set('statTotal',     total);
    set('statRemaining', total - ci);
    set('statPct',       total ? Math.round(ci / total * 100) + '%' : '0%');
}

function updateOnlineStatus() {
    if (isOnline) {
        updateStatusBar('online', 'Online — scans sync instantly');
    } else {
        updateStatusBar('offline', 'Offline — scans queued locally');
    }
}

function updateStatusBar(state, text) {
    const dot = document.getElementById('statusDot');
    const txt = document.getElementById('statusText');
    if (dot) dot.className = `status-indicator ${state}`;
    if (txt) txt.textContent = text;
}

function updateQueueBadge(ciCount, regCount) {
    const badge = document.getElementById('queueBadge');
    if (!badge) return;
    const ci  = ciCount  !== undefined ? ciCount  : parseInt(badge.dataset.ci  || '0');
    const reg = regCount !== undefined ? regCount : parseInt(badge.dataset.reg || '0');
    badge.dataset.ci  = ci;
    badge.dataset.reg = reg;
    const total = ci + reg;
    badge.textContent = total === 1 ? '1 queued' : `${total} queued`;
    badge.classList.toggle('show', total > 0);
}

function updateCacheInfo(count, cachedAt, overrideText) {
    const el = document.getElementById('cacheInfo');
    if (!el) return;
    if (overrideText) { el.textContent = overrideText; el.style.color = ''; return; }
    if (count === 0) {
        el.textContent = '⚠️ No guests cached — open scanner while online, then tap ↺ Refresh';
        el.style.color = '#fbbf24';
    } else {
        el.style.color = '';
        el.textContent = `✓ ${count} guest${count !== 1 ? 's' : ''} cached for offline scanning`;
        if (cachedAt) {
            el.textContent += ` · ${new Date(cachedAt).toLocaleTimeString()}`;
        }
    }
}

window.submitManual = function() {
    const input = document.getElementById('manualInput');
    const val   = (input.value || '').trim();
    if (!val) return;
    processCode(val);
    input.value = '';
};

// ── Polling ───────────────────────────────────────────────────────────────
function startPolling() {
    setInterval(async () => {
        if (!navigator.onLine) return;
        try {
            const r = await fetch(STATS_URL, { credentials: 'include' });
            const d = await r.json();
            updateStats(d.checked_in, d.total);
        } catch(e) {}
    }, 15000);
}

// ── Service Worker ────────────────────────────────────────────────────────
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then(reg => {
                console.log('[WBNG] SW registered');
                if ('sync' in reg) {
                    window.addEventListener('offline', () => {
                        reg.sync.register('flush-checkins').catch(() => {});
                    });
                }
            })
            .catch(e => console.warn('[WBNG] SW failed:', e));
    }
}

// PWA install is handled by pwa-install.js — loaded separately
