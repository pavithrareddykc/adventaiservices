/*
Cookie Consent and Utilities for Advent AI
-----------------------------------------
Features:
- Minimal, accessible cookie consent banner
- Preferences dialog for toggling analytics (default off)
- Utilities: setCookie, getCookie, deleteCookie

Consent keys:
- consent.functional: always true (required for site operation)
- consent.analytics: user-controlled; default false until accepted

Storage:
- Stores a JSON string in cookie "adventai_consent" with SameSite=Lax
*/

(function () {
  const CONSENT_COOKIE_NAME = "adventai_consent";
  const CONSENT_MAX_AGE_DAYS = 180; // 6 months

  function setCookie(name, value, days, options = {}) {
    try {
      const date = new Date();
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
      let cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Expires=${date.toUTCString()}; Path=/; SameSite=Lax`;
      if (options.secure === true || location.protocol === 'https:') cookie += '; Secure';
      document.cookie = cookie;
    } catch (_) {}
  }

  function getCookie(name) {
    try {
      const target = encodeURIComponent(name) + '=';
      const parts = document.cookie.split(';');
      for (let part of parts) {
        part = part.trim();
        if (part.indexOf(target) === 0) return decodeURIComponent(part.substring(target.length));
      }
    } catch (_) {}
    return null;
  }

  function deleteCookie(name) {
    try {
      document.cookie = `${encodeURIComponent(name)}=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; SameSite=Lax`;
    } catch (_) {}
  }

  function readConsent() {
    try {
      const raw = getCookie(CONSENT_COOKIE_NAME);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (typeof parsed !== 'object' || parsed === null) return null;
      return parsed;
    } catch (_) { return null; }
  }

  function writeConsent(consent) {
    try {
      const sanitized = {
        functional: true,
        analytics: !!consent.analytics,
      };
      setCookie(CONSENT_COOKIE_NAME, JSON.stringify(sanitized), CONSENT_MAX_AGE_DAYS);
    } catch (_) {}
  }

  function ensureBaseStyles() {
    if (document.getElementById('adventai-consent-styles')) return;
    const style = document.createElement('style');
    style.id = 'adventai-consent-styles';
    style.textContent = `
      .adventai-consent-shadow { box-shadow: 0 10px 25px rgba(0,0,0,0.15); }
      .adventai-consent-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display:none; }
      .adventai-consent-modal { position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%); max-width: 32rem; width: 92vw; background: #ffffff; color: #334155; border-radius: 0.75rem; padding: 1rem; display:none; }
      .adventai-consent-hidden { display: none !important; }
      #cookie-consent-banner { padding-bottom: env(safe-area-inset-bottom); }
      #cookie-consent-banner .adventai-consent-actions { display:flex; gap:0.5rem; align-items:stretch; }
      #cookie-consent-banner .adventai-consent-actions > button { flex: 1 1 auto; }
      @media (max-width: 640px) {
        #cookie-consent-banner { left: 50%; transform: translateX(-50%); width: calc(100vw - 1.5rem); }
        #cookie-consent-banner .adventai-consent-actions { flex-direction: column; }
        #cookie-consent-banner .adventai-consent-actions > button { width: 100%; }
      }
    `;
    document.head.appendChild(style);
  }

  function buildBanner() {
    const container = document.createElement('div');
    container.id = 'cookie-consent-banner';
    container.setAttribute('role', 'dialog');
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-label', 'Cookie consent');
    container.style.position = 'fixed';
    container.style.bottom = '1rem';
    container.style.left = '50%';
    container.style.transform = 'translateX(-50%)';
    container.style.zIndex = '10000';
    container.style.maxWidth = '56rem';
    container.style.width = '92vw';

    container.innerHTML = `
      <div class="adventai-consent-shadow" style="background:#ffffff;color:#334155;border-radius:0.75rem;padding:1rem 1.25rem;border:1px solid #e2e8f0;">
        <div style="display:flex;gap:1rem;align-items:flex-start;flex-wrap:wrap;">
          <div style="flex:1 1 16rem;min-width:16rem;">
            <p style="margin:0 0 0.5rem 0;font-weight:600;">We use cookies</p>
            <p style="margin:0;color:#64748b;">We use essential cookies to make this site work. We’d also like to use analytics cookies to understand usage and improve our services. You can accept all, reject non‑essential, or set preferences.</p>
          </div>
          <div class="adventai-consent-actions" style="display:flex;gap:0.5rem;align-items:center;">
            <button id="cookie-accept-all" style="background:#6C47FF;color:#ffffff;border:none;border-radius:9999px;padding:0.5rem 1rem;font-weight:600;cursor:pointer;">Accept all</button>
            <button id="cookie-reject" style="background:transparent;color:#334155;border:1px solid #cbd5e1;border-radius:9999px;padding:0.5rem 1rem;font-weight:600;cursor:pointer;">Reject non‑essential</button>
            <button id="cookie-preferences" style="background:transparent;color:#334155;border:1px solid #cbd5e1;border-radius:9999px;padding:0.5rem 1rem;font-weight:600;cursor:pointer;">Preferences</button>
          </div>
        </div>
      </div>
    `;
    return container;
  }

  function buildPreferencesModal(initial) {
    const backdrop = document.createElement('div');
    backdrop.className = 'adventai-consent-backdrop';
    backdrop.id = 'cookie-prefs-backdrop';

    const modal = document.createElement('div');
    modal.className = 'adventai-consent-modal';
    modal.id = 'cookie-prefs-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'cookie-prefs-title');

    modal.innerHTML = `
      <div>
        <h2 id="cookie-prefs-title" style="font-size:1.25rem;font-weight:700;">Cookie preferences</h2>
        <p style="margin:0.25rem 0 1rem 0;color:#64748b;">Manage which cookies we use. Functional cookies are always on as they are required for the site to work.</p>

        <div style="border:1px solid #e2e8f0;border-radius:0.5rem;padding:0.75rem;margin-bottom:0.75rem;background:#f8fafc;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">
            <div>
              <div style="font-weight:600;">Functional cookies</div>
              <div style="color:#64748b;">Required for basic site functionality. Always on.</div>
            </div>
            <input type="checkbox" checked disabled aria-label="Functional cookies always enabled" />
          </div>
        </div>

        <div style="border:1px solid #e2e8f0;border-radius:0.5rem;padding:0.75rem;margin-bottom:1rem;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">
            <div>
              <div style="font-weight:600;">Analytics cookies</div>
              <div style="color:#64748b;">Help us understand site usage. Optional.</div>
            </div>
            <label style="display:inline-flex;align-items:center;gap:0.5rem;">
              <input id="cookie-analytics-toggle" type="checkbox" ${initial.analytics ? 'checked' : ''} />
              <span id="cookie-analytics-label">${initial.analytics ? 'On' : 'Off'}</span>
            </label>
          </div>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:0.5rem;">
          <button id="cookie-prefs-save" style="background:#6C47FF;color:#ffffff;border:none;border-radius:9999px;padding:0.5rem 1rem;font-weight:600;cursor:pointer;">Save</button>
          <button id="cookie-prefs-cancel" style="background:transparent;color:#334155;border:1px solid #cbd5e1;border-radius:9999px;padding:0.5rem 1rem;font-weight:600;cursor:pointer;">Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(backdrop);
    document.body.appendChild(modal);

    const toggle = modal.querySelector('#cookie-analytics-toggle');
    const label = modal.querySelector('#cookie-analytics-label');
    if (toggle && label) {
      toggle.addEventListener('change', () => {
        label.textContent = toggle.checked ? 'On' : 'Off';
      });
    }

    return { backdrop, modal };
  }

  function showPreferences(initial) {
    const refs = buildPreferencesModal(initial);
    refs.backdrop.style.display = 'block';
    refs.modal.style.display = 'block';

    function close() {
      refs.modal.remove();
      refs.backdrop.remove();
    }

    return new Promise((resolve) => {
      const saveBtn = document.getElementById('cookie-prefs-save');
      const cancelBtn = document.getElementById('cookie-prefs-cancel');
      const toggle = document.getElementById('cookie-analytics-toggle');
      const onCancel = () => { close(); resolve(null); };
      const onSave = () => { close(); resolve({ analytics: !!(toggle && toggle.checked) }); };
      if (cancelBtn) cancelBtn.addEventListener('click', onCancel, { once: true });
      if (saveBtn) saveBtn.addEventListener('click', onSave, { once: true });
      refs.backdrop.addEventListener('click', onCancel, { once: true });
    });
  }

  function applyAnalyticsConsent(allowed) {
    // Place analytics init here if used in the future. Keep disabled by default.
    if (!allowed) {
      // Example: clear any prior analytics identifiers if needed.
      // deleteCookie('_ga'); // if GA used
    }
  }

  function hideBanner() {
    const banner = document.getElementById('cookie-consent-banner');
    if (banner) banner.remove();
  }

  function renderBannerIfNeeded() {
    ensureBaseStyles();
    const existing = readConsent();
    if (existing && typeof existing.analytics === 'boolean') {
      applyAnalyticsConsent(existing.analytics);
      return; // Consent already provided; no banner needed
    }

    if (document.getElementById('cookie-consent-banner')) return;

    const banner = buildBanner();
    document.body.appendChild(banner);

    const acceptBtn = document.getElementById('cookie-accept-all');
    const rejectBtn = document.getElementById('cookie-reject');
    const prefsBtn = document.getElementById('cookie-preferences');

    if (acceptBtn) acceptBtn.addEventListener('click', () => {
      writeConsent({ analytics: true });
      applyAnalyticsConsent(true);
      hideBanner();
    });

    if (rejectBtn) rejectBtn.addEventListener('click', () => {
      writeConsent({ analytics: false });
      applyAnalyticsConsent(false);
      hideBanner();
    });

    if (prefsBtn) prefsBtn.addEventListener('click', async () => {
      const res = await openPreferences();
      const current = readConsent();
      if (res || (current && typeof current.analytics === 'boolean')) {
        hideBanner();
      }
    });
  }

  async function openPreferences() {
    ensureBaseStyles();
    const existing = readConsent() || { analytics: false };
    const res = await showPreferences(existing);
    if (res) {
      writeConsent({ analytics: !!res.analytics });
      applyAnalyticsConsent(!!res.analytics);
    }
    return res;
  }

  // Expose minimal API
  window.AdventCookies = {
    setCookie,
    getCookie,
    deleteCookie,
    readConsent,
    writeConsent,
    openPreferences,
  };

  // Initialize as soon as DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderBannerIfNeeded);
  } else {
    renderBannerIfNeeded();
  }
})();


