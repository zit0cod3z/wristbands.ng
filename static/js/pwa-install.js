/**
 * WristbandsNG – Cross-platform PWA Install Helper
 * Works on: Android Chrome, Samsung Internet, Edge, iOS Safari, iPadOS, PDA browsers
 *
 * Usage: include this script, then call initPWAInstall({ appName, iconUrl })
 * It injects an install button/banner into any element with id="pwaInstallMount"
 */

(function() {
  'use strict';

  let deferredPrompt = null;   // Android/Chrome beforeinstallprompt event
  let installMounted = false;

  // ── Detect platform ──────────────────────────────────────────────────────
  const ua = navigator.userAgent || '';
  const isIOS     = /iphone|ipad|ipod/i.test(ua);
  const isAndroid = /android/i.test(ua);
  const isSafari  = /safari/i.test(ua) && !/chrome/i.test(ua);
  const isChrome  = /chrome/i.test(ua) && !/edg/i.test(ua);
  const isEdge    = /edg\//i.test(ua);
  const isFirefox = /firefox/i.test(ua);
  const isSamsung = /samsungbrowser/i.test(ua);

  // Already installed as PWA?
  const isStandalone = (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true ||   // iOS
    document.referrer.includes('android-app://')
  );

  // ── Capture Android install prompt ───────────────────────────────────────
  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    showInstallUI();
  });

  // If already installed, hide everything
  window.addEventListener('appinstalled', function() {
    deferredPrompt = null;
    hideInstallUI();
    showInstalledToast();
  });

  // ── Public API ────────────────────────────────────────────────────────────
  window.initPWAInstall = function(opts) {
    opts = opts || {};
    window._pwaInstallOpts = opts;

    if (isStandalone) return;   // already running as app — no button needed

    // Mount the install UI into #pwaInstallMount if it exists
    const mount = document.getElementById('pwaInstallMount');
    if (!mount) return;

    if (isIOS) {
      mountIOSBanner(mount, opts);
    } else if (deferredPrompt) {
      mountAndroidBanner(mount, opts);
    } else {
      // Browser hasn't fired beforeinstallprompt yet — mount a placeholder
      // that becomes active when the event fires
      mountAndroidBanner(mount, opts);
    }
    installMounted = true;
  };

  window.triggerPWAInstall = function() {
    if (isIOS) {
      showIOSModal();
      return;
    }
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function(choice) {
        deferredPrompt = null;
        if (choice.outcome === 'accepted') {
          hideInstallUI();
        }
      });
    } else {
      // Fallback: show manual instructions
      showManualInstructions();
    }
  };

  // ── Android / Chrome banner ───────────────────────────────────────────────
  function mountAndroidBanner(mount, opts) {
    const appName = opts.appName || 'WristbandsNG';
    mount.innerHTML = `
      <div id="pwaInstallBanner" style="
        display:flex; align-items:center; gap:12px;
        background:linear-gradient(135deg,rgba(172,35,118,.22),rgba(230,87,63,.12));
        border:1px solid rgba(172,35,118,.35); border-radius:14px;
        padding:14px 16px; margin:10px 12px;
        animation: fadeInDown .3s ease;
      ">
        <img src="${opts.iconUrl || '/static/img/icon-192.png'}"
             style="width:44px;height:44px;border-radius:10px;flex-shrink:0" alt="App icon"/>
        <div style="flex:1;min-width:0">
          <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:2px">
            Install ${appName}
          </div>
          <div style="font-size:11px;color:rgba(255,255,255,.6);line-height:1.4">
            Add to home screen for faster access &amp; full offline support
          </div>
        </div>
        <button onclick="triggerPWAInstall()" id="pwaInstallBtn" style="
          background:linear-gradient(135deg,#ac2376,#e6573f);
          color:#fff; border:none; border-radius:9px;
          padding:9px 14px; font-size:12px; font-weight:700;
          cursor:pointer; white-space:nowrap; flex-shrink:0;
          display:flex; align-items:center; gap:5px;
        ">
          <i class="bi bi-download"></i> Install
        </button>
        <button onclick="dismissInstallBanner()" style="
          background:none; border:none; color:rgba(255,255,255,.4);
          font-size:18px; cursor:pointer; padding:0 0 0 4px; line-height:1;
        " title="Dismiss">×</button>
      </div>`;
  }

  // ── iOS Safari banner ─────────────────────────────────────────────────────
  function mountIOSBanner(mount, opts) {
    const appName = opts.appName || 'WristbandsNG';
    mount.innerHTML = `
      <div id="pwaInstallBanner" style="
        display:flex; align-items:center; gap:12px;
        background:linear-gradient(135deg,rgba(172,35,118,.22),rgba(230,87,63,.12));
        border:1px solid rgba(172,35,118,.35); border-radius:14px;
        padding:14px 16px; margin:10px 12px;
      ">
        <img src="${opts.iconUrl || '/static/img/icon-192.png'}"
             style="width:44px;height:44px;border-radius:10px;flex-shrink:0" alt="App icon"/>
        <div style="flex:1;min-width:0">
          <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:2px">
            Install ${appName}
          </div>
          <div style="font-size:11px;color:rgba(255,255,255,.6);line-height:1.4">
            Tap below for step-by-step instructions
          </div>
        </div>
        <button onclick="triggerPWAInstall()" style="
          background:linear-gradient(135deg,#ac2376,#e6573f);
          color:#fff; border:none; border-radius:9px;
          padding:9px 14px; font-size:12px; font-weight:700;
          cursor:pointer; white-space:nowrap; flex-shrink:0;
          display:flex; align-items:center; gap:5px;
        ">
          <i class="bi bi-plus-square"></i> How to Install
        </button>
        <button onclick="dismissInstallBanner()" style="
          background:none; border:none; color:rgba(255,255,255,.4);
          font-size:18px; cursor:pointer; padding:0 0 0 4px; line-height:1;
        " title="Dismiss">×</button>
      </div>`;
  }

  // ── iOS step-by-step modal ────────────────────────────────────────────────
  function showIOSModal() {
    const appName = (window._pwaInstallOpts || {}).appName || 'WristbandsNG';
    const existing = document.getElementById('iosInstallModal');
    if (existing) { existing.style.display = 'flex'; return; }

    const modal = document.createElement('div');
    modal.id = 'iosInstallModal';
    modal.style.cssText = `
      position:fixed; inset:0; z-index:9999;
      background:rgba(0,0,0,.75); display:flex;
      align-items:flex-end; justify-content:center;
    `;
    modal.innerHTML = `
      <div style="
        background:#1a1418; border:1px solid rgba(172,35,118,.35);
        border-radius:20px 20px 0 0; width:100%; max-width:480px;
        padding:0; animation:slideUp .25s ease; max-height:85vh; overflow-y:auto;
      ">
        <div style="
          display:flex; align-items:center; justify-content:space-between;
          padding:18px 20px 14px; border-bottom:1px solid rgba(172,35,118,.2);
        ">
          <div style="font-size:16px;font-weight:800;color:#fff">
            📲 Install ${appName}
          </div>
          <button onclick="document.getElementById('iosInstallModal').style.display='none'"
                  style="background:rgba(255,255,255,.1);border:none;color:#fff;
                         width:30px;height:30px;border-radius:50%;font-size:16px;
                         cursor:pointer;display:flex;align-items:center;justify-content:center">
            ×
          </button>
        </div>
        <div style="padding:20px">
          <p style="font-size:13px;color:rgba(255,255,255,.65);margin-bottom:20px;line-height:1.6">
            Safari on iPhone/iPad doesn't support automatic install prompts.
            Follow these 3 steps to add the app to your home screen:
          </p>

          <!-- Step 1 -->
          <div style="display:flex;gap:14px;margin-bottom:18px;align-items:flex-start">
            <div style="
              width:36px;height:36px;border-radius:50%;
              background:linear-gradient(135deg,#ac2376,#e6573f);
              display:flex;align-items:center;justify-content:center;
              font-size:15px;font-weight:800;color:#fff;flex-shrink:0
            ">1</div>
            <div>
              <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:4px">
                Tap the Share button
              </div>
              <div style="font-size:12px;color:rgba(255,255,255,.55);line-height:1.5">
                At the bottom of Safari, tap the
                <span style="
                  display:inline-flex;align-items:center;gap:3px;
                  background:rgba(255,255,255,.12);border-radius:5px;
                  padding:2px 7px;font-size:11px;color:#fff;font-weight:600
                ">
                  <svg width="12" height="14" viewBox="0 0 12 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 9V1M6 1L3 4M6 1L9 4M1 10v2a1 1 0 001 1h8a1 1 0 001-1v-2" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Share
                </span>
                icon
              </div>
            </div>
          </div>

          <!-- Step 2 -->
          <div style="display:flex;gap:14px;margin-bottom:18px;align-items:flex-start">
            <div style="
              width:36px;height:36px;border-radius:50%;
              background:linear-gradient(135deg,#ac2376,#e6573f);
              display:flex;align-items:center;justify-content:center;
              font-size:15px;font-weight:800;color:#fff;flex-shrink:0
            ">2</div>
            <div>
              <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:4px">
                Tap "Add to Home Screen"
              </div>
              <div style="font-size:12px;color:rgba(255,255,255,.55);line-height:1.5">
                Scroll down in the share sheet and tap
                <strong style="color:#fff">"Add to Home Screen"</strong>
                <span style="font-size:14px"> ＋</span>
              </div>
            </div>
          </div>

          <!-- Step 3 -->
          <div style="display:flex;gap:14px;margin-bottom:24px;align-items:flex-start">
            <div style="
              width:36px;height:36px;border-radius:50%;
              background:linear-gradient(135deg,#ac2376,#e6573f);
              display:flex;align-items:center;justify-content:center;
              font-size:15px;font-weight:800;color:#fff;flex-shrink:0
            ">3</div>
            <div>
              <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:4px">
                Tap "Add"
              </div>
              <div style="font-size:12px;color:rgba(255,255,255,.55);line-height:1.5">
                Confirm by tapping <strong style="color:#fff">"Add"</strong> in the top-right corner.
                The app icon will appear on your home screen.
              </div>
            </div>
          </div>

          <button onclick="document.getElementById('iosInstallModal').style.display='none'"
                  style="
                    width:100%;background:linear-gradient(135deg,#ac2376,#e6573f);
                    color:#fff;border:none;border-radius:12px;padding:14px;
                    font-size:14px;font-weight:700;cursor:pointer
                  ">
            Got it!
          </button>
        </div>
      </div>`;
    document.body.appendChild(modal);
    // Close on backdrop click
    modal.addEventListener('click', function(e) {
      if (e.target === modal) modal.style.display = 'none';
    });
  }

  // ── Generic manual instructions (non-iOS, no prompt available) ───────────
  function showManualInstructions() {
    const appName = (window._pwaInstallOpts || {}).appName || 'WristbandsNG';
    let steps = '';
    if (isChrome || isEdge) {
      steps = `
        <li>Tap the <strong style="color:#fff">⋮ menu</strong> (three dots) in the top-right corner of Chrome</li>
        <li>Tap <strong style="color:#fff">"Add to Home screen"</strong> or <strong style="color:#fff">"Install app"</strong></li>
        <li>Tap <strong style="color:#fff">"Add"</strong> to confirm</li>`;
    } else if (isSamsung) {
      steps = `
        <li>Tap the <strong style="color:#fff">⋮ menu</strong> in Samsung Internet</li>
        <li>Tap <strong style="color:#fff">"Add page to"</strong> → <strong style="color:#fff">"Home screen"</strong></li>
        <li>Tap <strong style="color:#fff">"Add"</strong> to confirm</li>`;
    } else if (isFirefox) {
      steps = `
        <li>Tap the <strong style="color:#fff">⋮ menu</strong> in Firefox</li>
        <li>Tap <strong style="color:#fff">"Install"</strong> or <strong style="color:#fff">"Add to Home Screen"</strong></li>`;
    } else {
      steps = `
        <li>Open your browser's <strong style="color:#fff">menu</strong></li>
        <li>Look for <strong style="color:#fff">"Add to Home Screen"</strong> or <strong style="color:#fff">"Install App"</strong></li>
        <li>Confirm the installation</li>`;
    }

    const existing = document.getElementById('genericInstallModal');
    if (existing) { existing.style.display = 'flex'; return; }

    const modal = document.createElement('div');
    modal.id = 'genericInstallModal';
    modal.style.cssText = `
      position:fixed; inset:0; z-index:9999;
      background:rgba(0,0,0,.75); display:flex;
      align-items:flex-end; justify-content:center;
    `;
    modal.innerHTML = `
      <div style="
        background:#1a1418; border:1px solid rgba(172,35,118,.35);
        border-radius:20px 20px 0 0; width:100%; max-width:480px;
        padding:0; animation:slideUp .25s ease;
      ">
        <div style="
          display:flex; align-items:center; justify-content:space-between;
          padding:18px 20px 14px; border-bottom:1px solid rgba(172,35,118,.2);
        ">
          <div style="font-size:16px;font-weight:800;color:#fff">📲 Install ${appName}</div>
          <button onclick="document.getElementById('genericInstallModal').style.display='none'"
                  style="background:rgba(255,255,255,.1);border:none;color:#fff;
                         width:30px;height:30px;border-radius:50%;font-size:16px;
                         cursor:pointer;display:flex;align-items:center;justify-content:center">×</button>
        </div>
        <div style="padding:20px">
          <ol style="font-size:13px;color:rgba(255,255,255,.65);line-height:2;padding-left:20px">
            ${steps}
          </ol>
          <button onclick="document.getElementById('genericInstallModal').style.display='none'"
                  style="
                    width:100%;margin-top:20px;
                    background:linear-gradient(135deg,#ac2376,#e6573f);
                    color:#fff;border:none;border-radius:12px;padding:14px;
                    font-size:14px;font-weight:700;cursor:pointer
                  ">
            Got it!
          </button>
        </div>
      </div>`;
    document.body.appendChild(modal);
    modal.addEventListener('click', function(e) {
      if (e.target === modal) modal.style.display = 'none';
    });
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function showInstallUI() {
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) banner.style.display = 'flex';
    // If not mounted yet, try mounting now
    if (!installMounted && window._pwaInstallOpts) {
      window.initPWAInstall(window._pwaInstallOpts);
    }
  }

  function hideInstallUI() {
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) banner.style.display = 'none';
  }

  function showInstalledToast() {
    const t = document.createElement('div');
    t.style.cssText = `
      position:fixed; bottom:90px; left:50%; transform:translateX(-50%);
      background:rgba(16,185,129,.2); border:1px solid #10b981;
      border-radius:12px; padding:12px 20px; color:#fff;
      font-size:13px; font-weight:700; z-index:9999;
      animation:fadeInDown .3s ease;
    `;
    t.textContent = '✅ App installed successfully!';
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3500);
  }

  window.dismissInstallBanner = function() {
    hideInstallUI();
    // Remember dismissal for this session
    try { sessionStorage.setItem('pwa_install_dismissed', '1'); } catch(e) {}
  };

  // Add required keyframe animations to document
  if (!document.getElementById('pwaInstallStyles')) {
    const style = document.createElement('style');
    style.id = 'pwaInstallStyles';
    style.textContent = `
      @keyframes fadeInDown {
        from { opacity:0; transform:translateY(-10px); }
        to   { opacity:1; transform:translateY(0); }
      }
      @keyframes slideUp {
        from { transform:translateY(100%); }
        to   { transform:translateY(0); }
      }
    `;
    document.head.appendChild(style);
  }

})();
