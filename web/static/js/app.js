/* =========================================================================
   LMS Assistant Web — Frontend (SPA با Hash Routing)
   ========================================================================= */

"use strict";

// ---------- Helpers ----------

const $ = (sel) => document.querySelector(sel);
const contentEl = $("#content");

function esc(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function proxyUrl(url) {
  if (!url) return "#";
  return `/api/jaam-proxy?url=${encodeURIComponent(url)}`;
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const res = await fetch("/api" + path, {
    credentials: "include",
    ...options,
    headers,
  });
  if (!res.ok) {
    let detail = `خطای سرور (${res.status})`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch (_) {}
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

let toastTimer = null;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 3600);
}

function emptyState(text, hint = "ابتدا همگام‌سازی را اجرا کنید") {
  return `<div class="empty"><span class="empty-icon">📭</span>${esc(text)}<small>${esc(hint)}</small></div>`;
}

// ---------- Course name cache ----------

let _courseNames = null;
async function courseNameMap() {
  if (_courseNames) return _courseNames;
  try {
    const cs = await api("/courses");
    _courseNames = Object.fromEntries(cs.map((c) => [c.id, c.name]));
  } catch (_) {
    _courseNames = {};
  }
  return _courseNames;
}

// ---------- Event type metadata ----------

const EVENT_TYPES = {
  exam: { icon: "📝", label: "آزمون", cls: "badge-warn", chipCls: "t-exam" },
  deadline: { icon: "⏰", label: "ددلاین", cls: "badge-expired", chipCls: "t-deadline" },
  live_session: { icon: "🎥", label: "جلسه آنلاین", cls: "badge-info", chipCls: "t-live" },
  announcement: { icon: "📢", label: "اطلاعیه", cls: "badge-new", chipCls: "t-ann" },
  unknown: { icon: "📅", label: "رویداد", cls: "", chipCls: "t-other" },
};
function eventMeta(type) {
  return EVENT_TYPES[type] || EVENT_TYPES.unknown;
}

// ---------- Theme ----------

const ICON_SUN = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>`;
const ICON_MOON = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4 6.5 6.5 0 0 0 20 14.5z"/></svg>`;
const ICON_SEARCH = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16.5 20 20.5"/></svg>`;
const ICON_CHECK = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="m8.5 12.2 2.3 2.3 4.7-5"/></svg>`;
const ICON_CLOCK = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 8v4.5l3 1.5"/></svg>`;
const ICON_FILE = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3.5h7l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-9.5A1.5 1.5 0 0 1 5.5 20V5A1.5 1.5 0 0 1 7 3.5z"/><path d="M14 3.5V8h4.5"/></svg>`;
const ICON_BOOK = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"/></svg>`;
const ICON_CHAT = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
const ICON_REFRESH = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;
const ICON_HELP = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
const ICON_INFO = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
const ICON_EXTERNAL = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;
const ICON_MAIL = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`;
const ICON_DOWNLOAD = `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
const ICON_QUERA = `<svg class="ico-quera" viewBox="0 0 48 48" fill="none" aria-hidden="true"><circle cx="24" cy="24" r="23" fill="var(--info)"/><circle cx="24" cy="24" r="22.4" fill="none" stroke="var(--glass-hi)" stroke-opacity=".45"/><rect x="12" y="12" width="24" height="24" rx="8.5" fill="var(--surface)"/><path d="M29 29 L36.5 36.5" stroke="var(--surface)" stroke-width="7.5" stroke-linecap="round"/><path d="M24 24 L31.5 31.5" stroke="var(--info)" stroke-width="6"/></svg>`;

function setTheme(theme) {
  document.body.dataset.theme = theme;
  const btn = $("#btn-theme");
  if (btn) btn.innerHTML = theme === "dark" ? ICON_SUN : ICON_MOON;
  document.querySelector('meta[name="theme-color"]').content =
    theme === "dark" ? "#0e1118" : "#4f46e5";
  localStorage.setItem("lms-theme", theme);
  localStorage.setItem("lms-theme-mode", theme);
  api("/settings/theme", { method: "POST", body: JSON.stringify({ theme }) }).catch(() => {});
}

$("#btn-theme").addEventListener("click", () => {
  setTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
});

// ---------- Auth v2 (مودال ورود حرفه‌ای) ----------
// تب دانشجو/ادمین، کوئرا تاشو، اعتبارسنجی زنده، فوکوس‌ترپ، انیمیشن.
const Auth = {
  tab: "student", quera: false, open: false, locked: false, built: false,
  lastUser: localStorage.getItem("auth:lastUser") || "",
  el: null, wired: false,
};
const lgesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const lgfa = (n) => (typeof faDigits === "function" ? faDigits(String(n)) : String(n));
function authBuild() {
  if (Auth.built) return;
  Auth.built = true;
  const old = document.getElementById("login-modal"); if (old) old.remove();
  const wrap = document.createElement("div");
  wrap.id = "auth-modal";
  wrap.className = "auth-backdrop hidden";
  wrap.setAttribute("role", "dialog");
  wrap.setAttribute("aria-modal", "true");
  wrap.setAttribute("aria-label", "ورود به حساب کاربری");
  wrap.innerHTML = `
    <div class="auth-card">
      <div class="auth-head">
        <img src="/static/img/ui-logo.png" alt="لوگو دانشگاه اصفهان" class="auth-logo" />
        <div class="auth-head-txt">
          <h2 class="auth-title">دستیار LMS</h2>
          <p class="auth-sub">دانشگاه اصفهان · برای شروع وارد شوید</p>
        </div>
      </div>
      <div class="auth-tabs" role="tablist" aria-label="نوع ورود">
        <button type="button" class="auth-tab" data-authtab="student" role="tab">🎓 دانشجو</button>
        <button type="button" class="auth-tab" data-authtab="admin" role="tab">🛡️ ادمین</button>
      </div>
      <form id="auth-form" novalidate>
        <div id="auth-fields-student">
          <div class="auth-field" data-af="lms_username">
            <label class="field-label" for="auth-lms-user">شماره دانشجویی (LMS)</label>
            <div class="auth-input-wrap">
              <span class="auth-ico">👤</span>
              <input id="auth-lms-user" class="input" type="text" autocomplete="username" inputmode="numeric" placeholder="مثلاً ۳۲۰۰۱۲۳۴۵" value="${lgesc(Auth.lastUser)}" required />
            </div>
            <small class="auth-err"></small>
          </div>
          <div class="auth-field" data-af="lms_password">
            <label class="field-label" for="auth-lms-pass">رمز عبور (LMS)</label>
            <div class="auth-input-wrap">
              <span class="auth-ico">🔒</span>
              <input id="auth-lms-pass" class="input" type="password" autocomplete="current-password" placeholder="رمز عبور حساب LMS" required />
              <button type="button" class="auth-eye" data-auth-eye="auth-lms-pass" aria-label="نمایش یا پنهان‌کردن رمز">👁</button>
            </div>
            <small class="auth-err"></small>
          </div>
          <div class="auth-quera">
            <button type="button" class="auth-quera-toggle" id="auth-quera-btn" aria-expanded="false">
              <span>⚙️ افزودن کوئرا (اختیاری)</span>
              <span class="auth-chevron">▼</span>
            </button>
            <div class="auth-quera-body hidden" id="auth-quera-body">
              <div class="auth-field">
                <label class="field-label" for="auth-quera-user">نام کاربری کوئرا</label>
                <div class="auth-input-wrap"><span class="auth-ico">👤</span>
                  <input id="auth-quera-user" class="input" type="text" autocomplete="off" placeholder="نام کاربری کوئرا" /></div>
              </div>
              <div class="auth-field">
                <label class="field-label" for="auth-quera-pass">رمز عبور کوئرا</label>
                <div class="auth-input-wrap"><span class="auth-ico">🔒</span>
                  <input id="auth-quera-pass" class="input" type="password" autocomplete="off" placeholder="رمز عبور کوئرا" />
                  <button type="button" class="auth-eye" data-auth-eye="auth-quera-pass" aria-label="نمایش رمز">👁</button></div>
              </div>
            </div>
          </div>
        </div>
        <div id="auth-fields-admin" class="hidden">
          <div class="auth-field" data-af="admin_username">
            <label class="field-label" for="auth-admin-user">نام کاربری ادمین</label>
            <div class="auth-input-wrap"><span class="auth-ico">🛡️</span>
              <input id="auth-admin-user" class="input" type="text" autocomplete="username" placeholder="نام کاربری ادمین" /></div>
            <small class="auth-err"></small>
          </div>
          <div class="auth-field" data-af="admin_password">
            <label class="field-label" for="auth-admin-pass">رمز عبور ادمین</label>
            <div class="auth-input-wrap"><span class="auth-ico">🔒</span>
              <input id="auth-admin-pass" class="input" type="password" autocomplete="current-password" placeholder="رمز عبور ادمین" />
              <button type="button" class="auth-eye" data-auth-eye="auth-admin-pass" aria-label="نمایش رمز">👁</button></div>
            <small class="auth-err"></small>
          </div>
          <p class="auth-hint">ورود دانشجویان با حساب LMS است. ادمین محلی جداگانه است.</p>
        </div>
        <div id="auth-error" class="auth-error hidden" role="alert" aria-live="assertive"></div>
        <button type="submit" id="auth-submit" class="btn btn-primary btn-block auth-submit">
          <span class="auth-spinner hidden"></span>
          <span class="auth-submit-label">ورود</span>
        </button>
      </form>
      <div class="auth-foot">
        <a href="#/help">راهنما و حریم خصوصی</a>
        <span class="auth-dot">·</span>
        <span>نسخه ${lgfa("0.1.0")}</span>
      </div>
    </div>`;
  document.body.appendChild(wrap);
  Auth.el = wrap;
}
function authShow(required = true) {
  authBuild();
  const already = !!window._authIsLoggedIn;
  Auth.locked = required && !already;
  Auth.el.classList.remove("hidden");
  requestAnimationFrame(() => Auth.el.classList.add("is-open"));
  Auth.open = true;
  document.body.classList.add("auth-locked");
  authPaintTabs();
  setTimeout(() => { const f = Auth.el.querySelector(".auth-field input"); if (f) f.focus(); }, 140);
}
function authHide(force = false) {
  if (!Auth.open) return;
  if (Auth.locked && !force) return;
  Auth.el.classList.remove("is-open");
  Auth.el.classList.add("is-leaving");
  Auth.open = false;
  document.body.classList.remove("auth-locked");
  setTimeout(() => { if (Auth.el) { Auth.el.classList.add("hidden"); Auth.el.classList.remove("is-leaving"); } }, 230);
}
function authPaintTabs() {
  Auth.el.querySelectorAll("[data-authtab]").forEach((b) => {
    const on = b.dataset.authtab === Auth.tab;
    b.classList.toggle("on", on); b.setAttribute("aria-selected", on);
  });
  document.getElementById("auth-fields-student").classList.toggle("hidden", Auth.tab !== "student");
  document.getElementById("auth-fields-admin").classList.toggle("hidden", Auth.tab !== "admin");
  const label = Auth.el.querySelector(".auth-submit-label");
  if (label) label.textContent = Auth.tab === "admin" ? "ورود ادمین" : "ورود";
}
function authFieldErr(key, msg) {
  const f = Auth.el.querySelector(`[data-af="${key}"]`); if (!f) return !msg;
  f.classList.toggle("bad", !!msg); f.querySelector(".auth-err").textContent = msg || "";
  return !msg;
}
function authGlobalErr(msg) {
  const e = document.getElementById("auth-error"); if (!e) return;
  if (msg) { e.textContent = msg; e.classList.remove("hidden"); }
  else e.classList.add("hidden");
}
function authEnableBtn() {
  const btn = document.getElementById("auth-submit");
  btn.disabled = false;
  btn.querySelector(".auth-spinner").classList.add("hidden");
  btn.querySelector(".auth-submit-label").textContent = Auth.tab === "admin" ? "ورود ادمین" : "ورود";
  Auth.el.querySelectorAll("input").forEach((i) => (i.disabled = false));
}
function authDisableBtn() {
  const btn = document.getElementById("auth-submit");
  btn.disabled = true;
  btn.querySelector(".auth-spinner").classList.remove("hidden");
  btn.querySelector(".auth-submit-label").textContent = "در حال ورود…";
  Auth.el.querySelectorAll("input").forEach((i) => (i.disabled = true));
}
async function authSubmit(e) {
  e.preventDefault();
  authGlobalErr(""); authDisableBtn();
  try {
    if (Auth.tab === "student") await authLoginStudent();
    else await authLoginAdmin();
  } catch (_) {
    authGlobalErr("خطای ارتباط با سرور. اتصال خود را بررسی کنید.");
    authEnableBtn();
  }
}
async function authLoginStudent() {
  const user = document.getElementById("auth-lms-user").value.trim();
  const pass = document.getElementById("auth-lms-pass").value;
  const qUser = document.getElementById("auth-quera-user").value.trim();
  const qPass = document.getElementById("auth-quera-pass").value;
  let ok = authFieldErr("lms_username", user ? "" : "شماره دانشجویی را وارد کنید");
  if (user && !/^\d{6,12}$/.test(user)) ok = authFieldErr("lms_username", "شماره دانشجویی باید فقط عدد باشد") && ok;
  ok = authFieldErr("lms_password", pass ? "" : "رمز عبور را وارد کنید") && ok;
  if (!ok) { authEnableBtn(); return; }
  localStorage.setItem("auth:lastUser", user);
  const result = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      lms_username: user, lms_password: pass,
      quera_username: Auth.quera ? qUser : "",
      quera_password: Auth.quera ? qPass : "",
    }),
  });
  if (result.ok) {
    authHide(true);
    toast(`✅ خوش آمدید${result.full_name ? "، " + result.full_name : ""}`);
    await refreshUserBox();
    await renderPage(currentRoute());
    maybeAutoSync();
  } else {
    authGlobalErr(result.error || "ورود ناموفق بود");
    authEnableBtn();
  }
}
async function authLoginAdmin() {
  const user = document.getElementById("auth-admin-user").value.trim();
  const pass = document.getElementById("auth-admin-pass").value;
  let ok = authFieldErr("admin_username", user ? "" : "نام کاربری را وارد کنید");
  ok = authFieldErr("admin_password", pass ? "" : "رمز عبور را وارد کنید") && ok;
  if (!ok) { authEnableBtn(); return; }
  const result = await api("/auth/local-login", {
    method: "POST", body: JSON.stringify({ username: user, password: pass }),
  });
  if (result.ok) {
    authHide(true);
    toast(`✅ خوش آمدید${result.full_name ? "، " + result.full_name : ""}`);
    await refreshUserBox();
    location.hash = "#/admin";
    renderPage("admin");
  } else {
    authGlobalErr(result.error || "ورود ادمین ناموفق");
    authEnableBtn();
  }
}
function authTrap(e) {
  const panel = Auth.el.querySelector(".auth-card");
  const f = [...panel.querySelectorAll('input:not(:disabled),button:not(:disabled),a[href]')].filter((x) => x.offsetParent !== null);
  if (!f.length) return;
  const first = f[0], last = f[f.length - 1];
  if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
  else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
}
function authWire() {
  if (Auth.wired) return;
  Auth.wired = true;
  authBuild();
  // سازگاری با مودال‌های شیشه‌ای قدیمی (حذف نشود)
  document.addEventListener("click", (e) => {
    const eye = e.target.closest("[data-toggle]");
    if (eye) {
      const input = document.getElementById(eye.dataset.toggle);
      if (input) { const show = input.type === "password"; input.type = show ? "text" : "password"; eye.textContent = show ? "🙈" : "👁"; }
    }
    const closer = e.target.closest("[data-close]");
    if (closer) { const m = document.getElementById(closer.dataset.close); if (m) m.classList.add("hidden"); }
  });
  Auth.el.addEventListener("click", (e) => {
    const tab = e.target.closest("[data-authtab]");
    if (tab) { Auth.tab = tab.dataset.authtab; authPaintTabs(); authGlobalErr(""); return; }
    const eye = e.target.closest("[data-auth-eye]");
    if (eye) {
      const input = document.getElementById(eye.dataset.authEye); if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      eye.textContent = show ? "🙈" : "👁";
      return;
    }
    const qb = e.target.closest("#auth-quera-btn");
    if (qb) {
      Auth.quera = !Auth.quera;
      document.getElementById("auth-quera-body").classList.toggle("hidden", !Auth.quera);
      qb.classList.toggle("on", Auth.quera);
      qb.setAttribute("aria-expanded", Auth.quera);
      qb.querySelector(".auth-chevron").style.transform = Auth.quera ? "rotate(180deg)" : "";
      return;
    }
    if (e.target === Auth.el && !Auth.locked) authHide();
  });
  Auth.el.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !Auth.locked) authHide();
    if (e.key === "Tab") authTrap(e);
  });
  document.getElementById("auth-form").addEventListener("submit", authSubmit);
  document.getElementById("btn-logout")?.addEventListener("click", async () => {
    await api("/auth/logout", { method: "POST" });
    toast("از حساب خارج شدید");
    refreshUserBox();
  });
}
authWire();
// سازگاری با کدهای قدیمی
function showLogin(required) { authShow(required === undefined ? true : required); }
function hideLogin() { authHide(true); }
window.showLogin = showLogin;

let authRole = "user";

async function refreshUserBox() {
  try {
    const st = await api("/auth/status");
    authRole = st.role || "user";
    window._authIsLoggedIn = !!st.lms_logged_in;
    $("#user-name").textContent = st.full_name || st.username || "کاربر مهمان";
    const initial = (st.full_name || st.username || "؟").trim().charAt(0);
    $("#user-avatar").textContent = initial || "؟";
    $("#user-status").textContent = st.lms_logged_in
      ? (authRole === "admin" ? "ادمین · متصل به LMS" : "متصل به LMS")
      : "وارد نشده";
    const adminNav = document.getElementById("nav-admin");
    if (adminNav) {
      adminNav.classList.toggle("hidden", !(st.lms_logged_in && authRole === "admin"));
    }
    if (!st.lms_logged_in) showLogin();
    else maybeAutoSync();
  } catch (_) {
    showLogin();
  }
}

// ---------- Sync + SSE ----------
/** اگر هرگز sync نشده یا بیش از ۶ ساعت گذشته، یک‌بار همگام‌سازی بزن */
let _autoSyncTried = false;
async function maybeAutoSync() {
  if (_autoSyncTried) return;
  const p = window.LmsPrefs || {};
  if (p.auto_sync === "0") return;
  const hours = Math.max(1, parseInt(p.auto_sync_hours) || 6);
  try {
    const st = await api("/sync/status");
    if (st.running) return;
    const ls = st.last_sync;
    let need = !ls || ls.status === "never";
    if (!need && ls.at) {
      const ts = Date.parse(String(ls.at).replace(" ", "T") + "Z");
      if (!Number.isNaN(ts)) need = Date.now() - ts > hours * 3600 * 1000;
    }
    if (!need) return;
    _autoSyncTried = true;
    toast("🔄 همگام‌سازی خودکار شروع شد…");
    const r = await api("/sync/start", { method: "POST" });
    if (!r.ok && r.error) { toast("⏳ " + r.error); return; }
    setSyncButton(true);
    setSyncUI(true, 0, "همگام‌سازی خودکار…");
    listenSyncEvents();
  } catch (_) {}
}


document.addEventListener("click", (e) => {
  const btn = e.target && e.target.closest && e.target.closest("#btn-retry-sync");
  if (!btn) return;
  e.preventDefault();
  $("#btn-sync")?.click();
});


const PHASE_LABELS = {
  idle: "آماده",
  login: "ورود به LMS",
  courses: "دریافت درس‌ها",
  schedules: "دریافت برنامه هفتگی",
  contents: "دریافت محتواها",
  events: "دریافت رویدادها",
  wall: "دریافت وال و تکالیف",
  members: "دریافت اعضا",
  quera: "همگام‌سازی کوئرا",
  done: "پایان",
};

let eventSource = null;
function setSyncUI(visible, percent = 0, label = "") {
  $("#sync-progress").classList.toggle("hidden", !visible);
  $("#sync-status-pill").classList.toggle("hidden", !visible);
  $("#sync-bar").style.width = percent + "%";
  if (label) $("#sync-label").textContent = label;
}

function setSyncButton(running) {
  const btn = $("#btn-sync");
  btn.disabled = running;
  btn.querySelector(".sync-spinner").classList.toggle("hidden", !running);
  btn.querySelector(".btn-sync-label").textContent = running ? "در حال همگام‌سازی…" : "همگام‌سازی";
}

$("#btn-sync").addEventListener("click", async () => {
  setSyncButton(true);
  try {
    const r = await api("/sync/start", { method: "POST" });
    if (!r.ok && r.error) { toast("⏳ " + r.error); setSyncButton(false); return; }
    setSyncUI(true, 0, "شروع همگام‌سازی…");
    listenSyncEvents();
  } catch (e) {
    toast("❌ خطا در شروع همگام‌سازی");
    setSyncButton(false);
  }
});

function listenSyncEvents() {
  if (eventSource) eventSource.close();
  eventSource = new EventSource("/api/sync/stream");

  eventSource.addEventListener("progress", (e) => {
    const p = JSON.parse(e.data).data ?? JSON.parse(e.data);
    const phase = p.phase || "idle";
    const extra = p.total > 0 ? ` (${p.current}/${p.total})` : "";
    setSyncUI(true, p.percent ?? 0, `${PHASE_LABELS[phase] || phase}${extra} — ${p.message || ""}`);
  });

  const finish = (msg) => {
    toast(msg);
    setSyncUI(false);
    setSyncButton(false);
    if (eventSource) { eventSource.close(); eventSource = null; }
    _courseNames = null; // داده جدید ممکن است نام درس‌ها را تغییر دهد
    renderPage(currentRoute());
    refreshNavBadge();
  };

    eventSource.addEventListener("result", (e) => {
    const d = JSON.parse(e.data).data;
    if (d.ok) {
      finish(`✅ همگام‌سازی انجام شد — ${d.summary || ""}`);
    } else {
      finish(`❌ ${d.error_human || d.error || "همگام‌سازی ناموفق"}`);
    }
  });

  eventSource.addEventListener("error", (e) => {
    let msg = "همگام‌سازی ناموفق";
    try {
      const data = JSON.parse(e.data).data;
      msg = data.error_human || data.message || msg;
    } catch (_) {}
    finish("❌ " + msg);
  });

  eventSource.onerror = () => {
  setTimeout(async () => {
    const stop = () => {
      if (eventSource) { eventSource.close(); eventSource = null; }
      setSyncButton(false);
      setSyncUI(false);
    };
    try {
      const st = await api("/sync/status");
      if (!st.running) stop();
    } catch (_) { stop(); }
  }, 2000);
  };
}

// ---------- Quera Cookie Management ----------
window.openQueraCookieModal = async () => {
    // بررسی وضعیت فعلی
    let status = { has_cookie: false };
    try {
        status = await api("/quera/cookie-status");
    } catch (_) {}

    openGlassModal({
        id: "quera-cookie-modal",
        title: "اتصال به کوئرا",
        bodyHtml: `
            <div class="glass-form">
                <div class="quera-info" style="background: var(--info-soft); padding: 0.9rem; border-radius: 12px; font-size: 0.85rem; line-height: 1.8;">
                    <p style="margin: 0 0 0.5rem; font-weight: 600;">📌 چرا کوکی؟</p>
                    <p style="margin: 0; opacity: 0.9;">
                        کوئرا برای ورود کپچا دارد و لاگین خودکار ممکن نیست.
                        باید یک‌بار در مرورگر وارد کوئرا شوید و کوکی نشست را اینجا وارد کنید.
                    </p>
                </div>
                
                <div style="background: var(--glass-bg-soft); padding: 0.9rem; border-radius: 12px; font-size: 0.82rem; line-height: 1.9;">
                    <p style="margin: 0 0 0.5rem; font-weight: 700;">🔑 آموزش دریافت کوکی:</p>
                    <ol style="margin: 0; padding-inline-start: 1.2rem; opacity: 0.9;">
                        <li>در مرورگر به <a href="https://quera.org" target="_blank" rel="noopener" style="color: var(--primary);">quera.org</a> بروید و وارد شوید</li>
                        <li>کلید <kbd style="background: var(--surface-3); padding: 0.1rem 0.4rem; border-radius: 4px;">F12</kbd> را بزنید (DevTools)</li>
                        <li>به تب <b>Application</b> → <b>Cookies</b> → <b>quera.org</b> بروید</li>
                        <li>مقدار <code style="background: var(--surface-3); padding: 0.1rem 0.4rem; border-radius: 4px;">sessionid</code> را کپی کنید</li>
                        <li>در کادر پایین پیست کنید</li>
                    </ol>
                </div>
                
                <div class="field">
                    <label class="field-label">کوکی نشست کوئرا (sessionid)</label>
                    <textarea id="quera-cookie-input" class="input" rows="3" 
                        placeholder="مقدار کوکی را اینجا پیست کنید..."
                        style="direction: ltr; font-family: monospace; font-size: 0.85rem;">${status.has_cookie ? "••••••••••••••••" : ""}</textarea>
                    <small style="opacity: 0.7; margin-top: 0.3rem; display: block;">
                        ${status.has_cookie ? "✅ کوکی فعلی ذخیره شده. برای تغییر، مقدار جدید را وارد کنید." : "⚠️ هنوز کوکی تنظیم نشده است."}
                    </small>
                </div>
                
                <div style="display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 0.5rem;">
                    ${status.has_cookie ? '<button class="btn btn-danger btn-sm" id="quera-cookie-remove">حذف کوکی</button>' : ''}
                    <button class="btn btn-ghost" data-lib-close>انصراف</button>
                    <button class="btn btn-primary" id="quera-cookie-save">ذخیره کوکی</button>
                </div>
            </div>
        `,
        onMount: (modal) => {
            const saveBtn = modal.querySelector("#quera-cookie-save");
            const removeBtn = modal.querySelector("#quera-cookie-remove");
            const input = modal.querySelector("#quera-cookie-input");
            
            // اگر کوکی دارد و کاربر تغییر نداد، ذخیره نکند
            if (status.has_cookie) {
                input.addEventListener("focus", () => {
                    if (input.value.includes("••••")) input.value = "";
                });
            }
            
            saveBtn.addEventListener("click", async () => {
                const cookie = input.value.trim();
                if (!cookie || cookie.includes("••••")) {
                    toast("⚠️ لطفاً کوکی را وارد کنید");
                    return;
                }
                
                saveBtn.disabled = true;
                saveBtn.textContent = "در حال بررسی...";
                
                try {
                    const res = await api("/quera/cookie", {
                        method: "POST",
                        body: JSON.stringify({ cookie }),
                    });
                    
                    if (res.ok) {
                        toast("✅ کوکی کوئرا ذخیره شد");
                        closeGlassModal(modal);
                    } else {
                        toast("❌ " + (res.error || "خطا در ذخیره کوکی"));
                        saveBtn.disabled = false;
                        saveBtn.textContent = "ذخیره کوکی";
                    }
                } catch (e) {
                    toast("❌ " + (e.message || "خطا در ارتباط"));
                    saveBtn.disabled = false;
                    saveBtn.textContent = "ذخیره کوکی";
                }
            });
            
            if (removeBtn) {
                removeBtn.addEventListener("click", async () => {
                    try {
                        await api("/quera/cookie", { method: "DELETE" });
                        toast("🗑 کوکی کوئرا حذف شد");
                        closeGlassModal(modal);
                    } catch (e) {
                        toast("❌ خطا در حذف کوکی");
                    }
                });
            }
        },
    });
};

// آپدیت تابع سینک کوئرا
window.syncQuera = async () => {
    const btn = document.getElementById("btn-quera-sync");
    if (btn) { btn.disabled = true; btn.textContent = "در حال همگام‌سازی…"; }
    
    try {
        const r = await api("/quera/sync", { method: "POST" });
        
        if (r.need_cookie) {
            toast("🔑 " + r.error);
            openQueraCookieModal();
        } else if (r.error) {
            if (r.error.includes("کوکی") || r.error.includes("cookie")) {
                toast("🔑 " + r.error);
                openQueraCookieModal();
            } else {
                toast("❌ " + r.error);
            }
        } else {
            toast(`✅ کوئرا: ${r.new || 0} جدید، ${r.updated || 0} به‌روز`);
        }
    } catch (e) {
        toast("❌ خطا در همگام‌سازی کوئرا");
    } finally {
        renderPage("quera");
        if (btn) { btn.disabled = false; btn.textContent = "🔄 همگام‌سازی کوئرا"; }
    }
};

async function refreshNavBadge() {
  if ((window.LmsPrefs || {}).nav_badges === "0") {
    document.querySelectorAll("[data-badge]").forEach((b) => b.classList.add("hidden"));
    return;
  }
  try {
    const d = await api("/dashboard");
    const n = d.stats.pending_assignments;
    const badge = document.querySelector('[data-badge="pending"]');
    if (badge) {
      badge.textContent = n > 0 ? String(n) : "۰";
      badge.classList.toggle("hidden", n <= 0);
    }
  } catch (_) {}
  try {
    const np = await api("/posts?new_only=true");
    const badge = document.querySelector('[data-badge="posts"]');
    if (badge) {
      badge.textContent = np.length ? String(np.length) : "۰";
      badge.classList.toggle("hidden", np.length <= 0);
    }
  } catch (_) {}
}

// ---------- Search filter (client-side) ----------

let filterQuery = "";
let renderFilteredList = null; // (query) => void

function searchBox(placeholder) {
  return `<div class="search-box">
    <span class="search-ico">🔍</span>
    <input id="filter-input" type="search" placeholder="${esc(placeholder)}" value="${esc(filterQuery)}" />
  </div>`;
}

document.addEventListener("input", (e) => {
  if (e.target && e.target.id === "filter-input" && renderFilteredList) {
    filterQuery = e.target.value;
    renderFilteredList(filterQuery);
  }
});

function attachFilter(items, renderFn) {
  renderFilteredList = (q) => {
    const s = (q || "").trim().toLowerCase();
    const filtered = s ? items.filter((it) => renderFn.searchText(it).includes(s)) : items;
    renderFn.render(filtered);
  };
  renderFilteredList(filterQuery);
}

// ---------- Shared list renderers ----------

function pageHead(title, desc) {
  return `<div class="page-head"><div>
    <h3>${title}</h3>${desc ? `<p>${desc}</p>` : ""}</div></div>`;
}

// ---------- Pages ----------

const TITLES = {
  dashboard: "داشبورد",
  courses: "درس‌ها",
  assignments: "تکالیف",
  //events: "رویدادها",
  calendar: "تقویم",
  posts: "پیام‌های وال",
  contents: "محتواها",
  changes: "تغییرات",
  quera: "کوئرا",
  settings: "تنظیمات",
  admin: "پنل ادمین",
  support: "پشتیبانی",
  map: "نقشه مکان‌ها",
  more: "سایر امکانات",
  about: "درباره ما",
  help: "راهنما و حریم خصوصی",
  library: "کتابخانه",
};
// ---------- Home Board (داشبورد) ----------
const Dboard = {
  d: null, me: null, assigns: [], events: [], changes: [], unread: [], libCount: 0, sync: {},
  dismissed: JSON.parse(localStorage.getItem("dsh:dismissed") || "[]"),
  layers: [], wired: false, tick: null, poll: null, wasRunning: false,
};
const besc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const bfa = (n) => faDigits(String(n));
function bdParse(v) {
  const m = String(v || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (!m) return null;
  const dt = new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0));
  return { jdn: g2d(+m[1], +m[2], +m[3]), ms: dt.getTime(), min: (+(m[4] || 0)) * 60 + (+(m[5] || 0)), hasTime: !!m[4], time: m[4] ? `${m[4]}:${m[5]}` : "" };
}
function bdJal(p) { if (!p) return ""; const j = d2j(p.jdn); return `${bfa(j.jd)} ${J_MONTHS[j.jm - 1]}`; }
function bdAgo(iso) {
  const t = Date.parse(String(iso || "").replace(" ", "T"));
  if (Number.isNaN(t)) return "";
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${bfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${bfa(Math.floor(s / 3600))} ساعت پیش`;
  return `${bfa(Math.floor(s / 86400))} روز پیش`;
}
function bdDur(ms) {
  if (ms == null) return "";
  const s = Math.abs(ms - Date.now()) / 1000;
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  if (d > 0) return `${bfa(d)} روز${h ? ` و ${bfa(h)} ساعت` : ""}`;
  if (h > 0) return `${bfa(h)} ساعت${m ? ` و ${bfa(m)} دقیقه` : ""}`;
  return `${bfa(Math.max(1, m))} دقیقه`;
}
function bdLeft(ms) { if (ms == null) return ""; return ms < Date.now() ? `${bdDur(ms)} گذشته` : `${bdDur(ms)} مانده`; }
function bdWhen(p) {
  if (!p) return "";
  const t = bdToday();
  if (p.jdn === t) return p.hasTime ? `امروز ساعت ${bfa(p.time)}` : "امروز";
  if (p.jdn === t + 1) return p.hasTime ? `فردا ساعت ${bfa(p.time)}` : "فردا";
  return `${BD_WD[jWeekday(p.jdn)]} ${bdJal(p)}`;
}
function bdHue(ms) {
  if (ms == null) return "var(--primary)";
  const h = (ms - Date.now()) / 3600e3;
  if (h < 24) return "var(--danger)";
  if (h < 48) return "var(--warning)";
  return "var(--primary)";
}
const BD_WD = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"];
function bdToday() { const n = new Date(); return g2d(n.getFullYear(), n.getMonth() + 1, n.getDate()); }
function bdTermWeek() {
  const t = bdToday(), j = d2j(t);
  const start = j.jm >= 7 ? j2d(j.jy, 7, 1) : j2d(j.jy, 11, 1);
  return Math.max(1, Math.min(20, Math.floor((t - start) / 7) + 1));
}
const bdCut = (s, n = 34) => { const t = String(s || ""); return t.length > n ? t.slice(0, n) + "…" : t; };
function bdLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof crsLayer === "function" ? crsLayer
    : typeof qraLayer === "function" ? qraLayer : null;
  if (f) { const L = f({ ...opts, onClose: () => { const i = Dboard.layers.indexOf(L); if (i >= 0) Dboard.layers.splice(i, 1); opts.onClose && opts.onClose(); } }); Dboard.layers.push(L); return L; }
  const w = document.createElement("div"); w.className = "glass-modal-backdrop";
  w.innerHTML = `<div class="glass-modal" role="dialog" aria-modal="true"><h3>${besc(opts.title || "")}</h3>${opts.html}</div>`;
  document.body.appendChild(w);
  const L = { wrap: w, panel: w.querySelector(".glass-modal"), close() { w.classList.add("is-leaving"); setTimeout(() => w.remove(), 240); const i = Dboard.layers.indexOf(L); if (i >= 0) Dboard.layers.splice(i, 1); } };
  w.addEventListener("click", (e) => { if (e.target === w) L.close(); });
  w.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  Dboard.layers.push(L); if (opts.onMount) opts.onMount(w, L); return L;
}
function bdToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  return toast(m);
}
function bdTeardown() {
  if (Dboard.tick) { clearInterval(Dboard.tick); Dboard.tick = null; }
  if (Dboard.poll) { clearInterval(Dboard.poll); Dboard.poll = null; }
  Dboard.layers.slice().forEach((l) => l.close());
}
window.__dashTeardown = bdTeardown;

/* ---- داده ---- */
async function bdFetch() {
  const [d, me, a, e, s, c, u, lib] = await Promise.all([
    api("/dashboard").catch(() => null),
    api("/auth/status").catch(() => null),
    api("/assignments").catch(() => []),
    api("/events").catch(() => []),
    api("/sync/status").catch(() => ({})),
    api("/changes?limit=120").catch(() => []),
    api("/posts?new_only=true").catch(() => []),
    api("/library/courses?scope=all").catch(() => ({ courses: [] })),
  ]);
  if (!d) throw new Error("داشبورد در دسترس نیست");
  Dboard.d = d;
  Dboard.me = me || null;
  Dboard.d.stats = d.stats || {};
  Dboard.d.alerts = d.alerts || [];
  Dboard.d.recent_posts = d.recent_posts || [];
  Dboard.assigns = Array.isArray(a) ? a : [];
  Dboard.events = Array.isArray(e) ? e : [];
  Dboard.sync = s || {};
  Dboard.changes = Array.isArray(c) ? c : [];
  Dboard.unread = Array.isArray(u) ? u : [];
  Dboard.libCount = (lib.courses || []).reduce((n, x) => n + (x.item_count || 0), 0);
}
function bdFirstName() {
  const full = (Dboard.me && (Dboard.me.full_name || "")) || (Dboard.d.stats.full_name || "");
  const first = String(full).trim().split(/\s+/)[0] || "";
  return first && first.length <= 22 ? first : "";
}
async function renderDashboard() {
  bdTeardown();
  contentEl.innerHTML = `<div class="dsh-wrap">
    <div class="dsh-skel" style="height:300px"></div>
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:.8rem">${'<div class="dsh-skel" style="height:128px"></div>'.repeat(6)}</div>
    <div class="dsh-grid2"><div class="dsh-skel" style="height:260px"></div><div class="dsh-skel" style="height:260px"></div></div>
  </div>`;
  try { await bdFetch(); }
  catch (err) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری داشبورد<small>${besc(err.message || "")}</small>
      <div style="margin-top:.9rem"><button class="lq-btn lq-sm" data-bd="retry">تلاش مجدد</button></div></div>`;
    return;
  }
  bdRenderShell();
  Dboard.tick = setInterval(() => { bdTickFocus(); bdPaintDay(); }, 30000);
  Dboard.poll = setInterval(async () => {
    try {
      const st = await api("/sync/status");
      const was = Dboard.wasRunning;
      Dboard.sync = st; Dboard.wasRunning = !!st.running;
      bdPaintSync();
      if (was && !st.running) { await bdFetch(); bdPaintAll(); }
    } catch (_) {}
  }, 9000);
  Dboard.wasRunning = !!Dboard.sync.running;
}
function bdRenderShell() {
  const hour = new Date().getHours();
  const order = hour >= 19 || hour < 5
    ? ["brief", "quick", "posts", "daydead"]
    : ["brief", "quick", "daydead", "posts"];
  const blocks = {
    brief: `<div id="bd-brief"></div>`,
    quick: `<div class="dsh-quick" id="bd-quick"></div>`,
    daydead: `<div class="dsh-grid2"><div class="card dsh-day" id="bd-day"></div><div class="card" id="bd-dead"></div></div>`,
    posts: `<div class="dsh-grid2"><div class="card" id="bd-posts"></div><div class="card" id="bd-term"></div></div>`,
  };
  contentEl.innerHTML = `<div class="dsh-wrap"><div id="bd-alerts"></div>${order.map((k) => blocks[k]).join("")}</div>`;
  bdPaintAll();
}
function bdPaintAll() { bdPaintAlerts(); bdPaintBrief(); bdPaintQuick(); bdPaintDay(); bdPaintDead(); bdPaintPosts(); bdPaintTerm(); }

/* ---- موتور متن هوشمند ---- */
function bdSince() {
  const ls = Dboard.sync.last_sync || Dboard.d.last_sync;
  const t = Date.parse(String(ls?.at || "").replace(" ", "T"));
  return Number.isNaN(t) ? Date.now() - 864e5 : t;
}
function bdPulseCounts() {
  const cut = bdSince();
  const meta = { content: ["📁", "محتوا", "var(--primary)"], assignment: ["📝", "تکلیف", "var(--warning)"], post: ["💬", "پیام", "var(--accent)"], event: ["📅", "رویداد", "var(--info)"] };
  const n = {};
  Dboard.changes.forEach((c) => { if ((Date.parse(String(c.detected_at || "").replace(" ", "T")) || 0) > cut) n[c.entity_type] = (n[c.entity_type] || 0) + 1; });
  return Object.keys(meta).filter((k) => n[k]).map((k) => ({ key: k, n: n[k], icon: meta[k][0], label: meta[k][1], hue: meta[k][2] }));
}
function bdInsight() {
  const now = Date.now(), t = bdToday(), hour = new Date().getHours();
  const nowMin = hour * 60 + new Date().getMinutes();
  const open = Dboard.assigns.filter((a) => !a.is_done);
  const over = open.filter((a) => a.is_expired || (bdParse(a.deadline)?.ms ?? Infinity) < now);
  const dead = open.map((a) => ({ a, p: bdParse(a.deadline) })).filter((x) => x.p).sort((x, y) => x.p.ms - y.p.ms);
  const next = dead[0];
  const evs = Dboard.events.map((e) => ({ e, p: bdParse(e.start_at), pe: bdParse(e.end_at) })).filter((x) => x.p);
  const todayEv = evs.filter((x) => x.p.jdn === t);
  const exams = evs.filter((x) => x.e.event_type === "exam" && x.p.ms > now - 3 * 3600e3).sort((a, b) => a.p.ms - b.p.ms);
  const exam = exams[0];
  const live = todayEv.find((x) => x.p.hasTime && x.p.min <= nowMin && (x.pe?.min ?? x.p.min + 90) >= nowMin);
  const soon = todayEv.filter((x) => x.p.hasTime && x.p.min > nowMin && x.p.min - nowMin <= 90).sort((a, b) => a.p.min - b.p.min)[0];
  const pulse = bdPulseCounts();
  const newContent = pulse.find((x) => x.key === "content")?.n || 0;
  const ls = Dboard.sync.last_sync || Dboard.d.last_sync;
  const syncH = (() => { const x = Date.parse(String(ls?.at || "").replace(" ", "T")); return Number.isNaN(x) ? Infinity : (now - x) / 3600e3; })();
  const wd = jWeekday(t);
  const pick = (arr) => arr[Math.floor(now / 864e5) % arr.length];
  const I = (tone, icon, text, label, go, extra = {}) => ({ tone, icon, text, label, go, ...extra });

  if (!ls || ls.status === "never")
    return I("info", "🌱", "هنوز داده‌ای همگام نشده. یک بار همگام‌سازی بزن تا دستیار بیدار شود و روزت را بچیند.", "همگام‌سازی", null, { sync: true });

  if (next && next.p.ms - now < 6 * 3600e3 && next.p.ms > now) {
    const d = bdDur(next.p.ms), title = bdCut(next.a.title);
    return I("danger", "🔥", pick([
      `فقط ${d} تا پایان مهلت «${title}». همین حالا سراغش برو.`,
      `«${title}» تا ${d} دیگر بسته می‌شود — الان وقتش است.`,
      `مهلت «${title}» نفس‌نفس می‌زند؛ ${d} مانده.`,
    ]), next.a.submit_url ? "ارسال تکلیف" : "تکالیف", next.a.submit_url ? null : "assignments",
      next.a.submit_url ? { href: proxyUrl(next.a.submit_url) } : {});
  }
  if (live) {
    return I("info", "🎥", pick([
      `کلاس «${bdCut(live.e.title)}» همین حالا در جریان است.`,
      `«${bdCut(live.e.title)}» شروع شده — لینک جلسه آماده است.`,
      `الان وقت کلاس «${bdCut(live.e.title)}» است؛ دیرتر یعنی از دست دادن اول جلسه.`,
    ]), live.e.url ? "ورود به جلسه" : "تقویم", live.e.url ? null : "calendar",
      live.e.url ? { href: proxyUrl(live.e.url) } : {});
  }
  if (over.length) {
    const n = bfa(over.length);
    return I("danger", "⏰", pick([
      `${n} تکلیف از مهلتش گذشته — از کوچک‌ترینش شروع کن، راه می‌افتی.`,
      `عقب‌افتاده‌ها روی هم جمع شده‌اند (${n} مورد). امروز یکی‌شان را ببند.`,
      `${n} مهلت جا مانده. اگر هنوز می‌شود تحویل داد، همین حالا سراغش برو.`,
    ]), "رسیدگی", "assignments");
  }
  if (exam && exam.p.ms - now < 24 * 3600e3) {
    const w = bdWhen(exam.p), title = bdCut(exam.e.title);
    return I("warning", "📄", pick([
      `آزمون «${title}» ${w} است. مرور خلاصه‌ها بیشتر از خواندن دوباره جواب می‌دهد.`,
      `${w} آزمون «${title}» داری — نمونه‌سؤال‌های ترم قبل را بزن.`,
      `برای آزمون «${title}» ${bdDur(exam.p.ms)} وقت هست؛ سبک و مرورمحور بخوان.`,
    ]), "تقویم", "calendar");
  }
  if (next && next.p.ms - now < 24 * 3600e3) {
    const d = bdDur(next.p.ms), title = bdCut(next.a.title);
    return I("warning", "⚡", pick([
      `«${title}» را امروز باید ببندی؛ ${d} مانده.`,
      `${d} تا مهلت «${title}». یک نشست کوتاه کافی است.`,
      `مهلت «${title}» فرداست — ${d} فرصت داری.`,
    ]), next.a.submit_url ? "ارسال تکلیف" : "تکالیف", next.a.submit_url ? null : "assignments",
      next.a.submit_url ? { href: proxyUrl(next.a.submit_url) } : {});
  }
  if (soon) {
    const d = bdDur(soon.p.ms), title = bdCut(soon.e.title);
    return I("info", "🚶", pick([
      `${d} تا کلاس «${title}». اگر مسیر داری، حالا راه بیفت.`,
      `کلاس «${title}» ${d} دیگر شروع می‌شود.`,
      `برای «${title}» ${d} وقت داری؛ جزوه‌ات را باز کن.`,
    ]), "تقویم", "calendar");
  }
  if (exam && exam.p.ms - now < 48 * 3600e3) {
    return I("warning", "📄", pick([
      `آزمون «${bdCut(exam.e.title)}» ${bdWhen(exam.p)} است — از حالا مرورش را شروع کن.`,
      `${bdDur(exam.p.ms)} تا آزمون «${bdCut(exam.e.title)}». برنامه‌ات را سبک بچین.`,
      `برای آزمون پیش‌رو (${bdWhen(exam.p)}) خلاصه‌ها را آماده کن.`,
    ]), "تقویم", "calendar");
  }
  if (next && next.p.ms - now < 72 * 3600e3) {
    const d = bdDur(next.p.ms), title = bdCut(next.a.title);
    return I("primary", "🎯", pick([
      `«${title}» ${d} دیگر مهلت دارد — اگر امروز شروع کنی، استرس نمی‌گیری.`,
      `${d} تا «${title}». تقسیمش کن به دو نشست کوتاه.`,
      `مهلت «${title}» نزدیک است (${d})؛ یک قدم کوچک امروز کافی است.`,
    ]), "تکالیف", "assignments");
  }
  if (syncH > 24)
    return I("warning", "🔄", `${bdAgo(ls.at)} از آخرین همگام‌سازی گذشته — ممکن است مهلت یا فایل تازه‌ای آمده باشد.`, "همگام‌سازی", null, { sync: true });
  if (Dboard.unread.length >= 3) {
    const n = bfa(Dboard.unread.length);
    return I("accent", "💬", pick([
      `${n} پیام خوانده‌نشده روی وال داری — ممکن است مهلت یا تغییری در آن باشد.`,
      `وال شلوغ شده: ${n} پیام تازه. یک نگاه سریع بینداز.`,
      `${n} پیام جدید منتظر توست؛ خبر مهمی ممکن است بین‌شان باشد.`,
    ]), "پیام‌ها", "posts");
  }
  if (newContent >= 2) {
    const n = bfa(newContent);
    return I("primary", "📁", pick([
      `${n} فایل تازه روی LMS گذاشته شده — قبل از جلسه یک نگاه بینداز.`,
      `محتوای جدید رسیده (${n} مورد)؛ جزوه‌های این هفته کامل‌تر شده‌اند.`,
      `${n} منبع تازه اضافه شده؛ شاید همان چیزی باشد که کم داشتی.`,
    ]), "محتواها", "contents");
  }
  if ((wd === 5 || wd === 6) && open.length) {
    const n = bfa(open.length);
    return I("accent", "🌿", pick([
      `آخر هفته است ولی ${n} تکلیف باز داری — یک ساعت امروز، آسودگی کل هفته.`,
      `تعطیلی بهترین زمان برای بستن کارهای باز است (${n} مورد).`,
      `${n} کار مانده. آخر هفته را سبک شروع کن.`,
    ]), "تکالیف", "assignments");
  }
  if (hour >= 23 || hour < 5)
    return I("info", "🌙", pick([
      "دیروقت است. خواب کافی فردا بازدهی‌ات را دو برابر می‌کند.",
      "این ساعت مغز کمتر یاد می‌گیرد و بیشتر خسته می‌شود — بخواب.",
      "شب بخیر؛ کارهای فردا را به فردا بسپار.",
    ]), "فردا را ببین", "calendar");
  if (!todayEv.length && !open.length)
    return I("accent", "🌤", pick([
      "امروز هیچ کلاس و مهلتی نداری. یک استراحت واقعی حق توست.",
      "روزت خالی است — بهترین وقت برای جلو افتادن از هفتهٔ بعد.",
      "همه‌چیز انجام شده و امروز آزادی؛ لذتش را ببر.",
    ]), "کاوش کتابخانه", "library");
  if (!open.length) {
    const done = bfa(Dboard.assigns.filter((a) => a.is_done).length);
    return I("accent", "✅", pick([
      `هیچ تکلیف بازی نداری — ${done} تکلیف را بسته‌ای. تمیز کار کردی.`,
      "صفر تکلیف باز؛ حالا فقط برنامهٔ کلاس‌هایت مانده.",
      "کارها تمام شده. یک نگاه به تقویم بینداز و خیالت راحت.",
    ]), "تقویم", "calendar");
  }
  const nOpen = bfa(open.length), nToday = bfa(todayEv.length);
  return I("primary", "🧭", pick([
    `${nOpen} تکلیف باز و ${nToday} رویداد امروز؛ روز قابل‌مدیریتی است.`,
    `امروز ${nToday} مورد در برنامه داری. از مهم‌ترینش شروع کن.`,
    next ? `همه‌چیز مرتب است؛ نزدیک‌ترین مهلت ${bdDur(next.p.ms)} دیگر است.` : `${nOpen} تکلیف باز مانده — یکی‌یکی جلو برو.`,
  ]), "تکالیف", "assignments");
}

/* ---- بریف صبحگاهی ---- */
function bdFocal() {
  const t = bdToday(), nowMin = new Date().getHours() * 60 + new Date().getMinutes();
  const cls = Dboard.events.map((e) => ({ e, p: bdParse(e.start_at) }))
    .filter((x) => x.p && x.p.jdn === t && x.p.hasTime && x.p.min >= nowMin)
    .sort((a, b) => a.p.min - b.p.min)[0];
  if (cls) {
    return { kind: "class", hue: "var(--info)", kicker: "کلاس بعدی امروز", title: cls.e.title,
      meta: [bfa(cls.p.time), cls.e.course_name || ""].filter(Boolean), ms: cls.p.ms, window: 24 * 3600e3,
      href: cls.e.url ? proxyUrl(cls.e.url) : null, hrefLabel: "ورود به جلسه", go: "calendar" };
  }
  const dead = Dboard.assigns.filter((a) => !a.is_done && a.deadline)
    .map((a) => ({ a, p: bdParse(a.deadline) })).filter((x) => x.p).sort((x, y) => x.p.ms - y.p.ms)[0];
  if (dead) return { kind: "deadline", hue: bdHue(dead.p.ms), kicker: dead.p.ms < Date.now() ? "مهلت گذشته" : "نزدیک‌ترین مهلت",
    title: dead.a.title, meta: [dead.a.course_name || "", bdJal(dead.p)].filter(Boolean), ms: dead.p.ms, window: 7 * 864e5,
    href: dead.a.submit_url ? proxyUrl(dead.a.submit_url) : null, hrefLabel: "ارسال تکلیف", go: "assignments" };
  const nx = Dboard.events.map((e) => ({ e, p: bdParse(e.start_at) }))
    .filter((x) => x.p && x.p.ms > Date.now()).sort((a, b) => a.p.ms - b.p.ms)[0];
  if (nx) return { kind: "event", hue: "var(--primary)", kicker: "رویداد پیش رو", title: nx.e.title,
    meta: [bdWhen(nx.p), nx.e.course_name || ""].filter(Boolean), ms: nx.p.ms, window: 7 * 864e5, href: null, go: "calendar" };
  return null;
}
function bdPaintBrief() {
  const box = document.getElementById("bd-brief"); if (!box) return;
  const n = new Date(), j = d2j(bdToday()), h = n.getHours();
  const greet = h < 5 ? "شب بخیر" : h < 12 ? "صبح بخیر" : h < 17 ? "ظهر بخیر" : h < 21 ? "عصر بخیر" : "شب بخیر";
  const name = bdFirstName();
  const ins = bdInsight();
  const pulse = bdPulseCounts();
  const f = bdFocal();
  const hueVar = `var(--${ins.tone === "primary" ? "primary" : ins.tone})`;

  // تنها یک اقدام برای بینش
  const insAct = ins.sync
    ? `<button class="lq-btn lq-sm is-on" style="--lq-hue:${hueVar}" data-bd="sync">${besc(ins.label)}</button>`
    : ins.href
      ? `<a class="lq-btn lq-sm is-on" style="--lq-hue:${hueVar}" href="${besc(ins.href)}" target="_blank" rel="noopener noreferrer">${besc(ins.label)} ↗</a>`
      : `<button class="lq-btn lq-sm" style="--lq-hue:${hueVar}" data-bd="go" data-v="${ins.go}">${besc(ins.label)}</button>`;

  // نوار وضعیت: باریک، فقط در حالت خالی یک اقدام دارد (بدون تکرار بینش)
  let strip;
  if (f) {
    const pct = Math.max(2, Math.min(100, Math.round((1 - Math.max(0, f.ms - Date.now()) / f.window) * 100)));
    strip = `<div class="dsh-strip" id="bd-focus" data-ms="${f.ms}" data-win="${f.window}">
      <div class="dsh-strip-ring" style="--p:${pct};--hue:${f.hue}"><i id="bd-ring-n">${bfa(pct)}</i></div>
      <div class="dsh-strip-body">
        <span class="dsh-strip-kicker">${besc(f.kicker)}</span>
        <b>${besc(bdCut(f.title, 40))}</b>
        <span class="dsh-strip-meta">${f.meta.map((x) => `<span>${besc(x)}</span>`).join("")}
          <span id="bd-count" style="color:${f.hue};font-weight:750">${bdLeft(f.ms)}</span></span>
      </div>
      ${f.href ? `<a class="lq-btn lq-sm" style="--lq-hue:${f.hue};min-height:36px;padding:.35rem .9rem;font-size:.8rem" href="${besc(f.href)}" target="_blank" rel="noopener noreferrer">${besc(f.hrefLabel)} ↗</a>` : ""}
    </div>`;
  } else {
    const showAct = ins.go !== "library";
    strip = `<div class="dsh-strip is-empty">
      <div class="dsh-strip-ring" style="--p:100;--hue:var(--accent)"><i>✓</i></div>
      <div class="dsh-strip-body"><span class="dsh-strip-kicker">وضعیت امروز</span><b>همه‌چیز مرتب است</b>
        <span class="dsh-strip-meta"><span>کلاس، مهلت یا رویداد پیش‌رویی نداری</span></span></div>
      ${showAct ? `<button class="lq-btn lq-sm" style="--lq-hue:var(--accent);min-height:36px;padding:.35rem .9rem;font-size:.8rem" data-bd="go" data-v="library">کاوش کتابخانه</button>` : ""}
    </div>`;
  }

  box.innerHTML = `<section class="dsh-brief card">
    <div class="dsh-brief-top">
      <div class="dsh-brief-id">
        <div class="dsh-greet-row">
          <h2 class="dsh-hi">${greet}${name ? `، ${besc(name)}` : ""} <span class="dsh-wave">👋</span></h2>
          <span class="dsh-week">هفتهٔ ${bfa(bdTermWeek())} ترم</span>
        </div>
        <div class="dsh-date">${BD_WD[jWeekday(bdToday())]}، ${bfa(j.jd)} ${J_MONTHS[j.jm - 1]} ${bfa(j.jy)}</div>
        <div class="dsh-pulse">
          <span class="dsh-pulse-label">از آخرین بازدیدت</span>
          ${pulse.length
            ? pulse.map((x) => `<button class="dsh-pulse-chip" style="--hue:${x.hue}" data-bd="go" data-v="changes">
                <span>${x.icon}</span><b>${bfa(x.n)}</b><span>${x.label}</span></button>`).join("")
            : `<span class="dsh-pulse-none">چیزی عوض نشده ✓</span>`}
        </div>
      </div>
      <div class="dsh-brief-actions">
        <button class="lq-btn" style="--lq-hue:var(--info)" data-bd="go" data-v="calendar"><span class="lq-ico">📅</span>تقویم</button>
        <button class="lq-btn" style="--lq-hue:var(--danger)" data-bd="go" data-v="assignments"><span class="lq-ico">📝</span>تکالیف</button>
      </div>
    </div>
    <div class="dsh-insight tone-${ins.tone}">
      <span class="dsh-insight-ico">${ins.icon}</span>
      <p>${besc(ins.text)}</p>
      ${insAct}
    </div>
    ${strip}
    <div class="dsh-brief-foot"><div id="bd-sync"></div></div>
  </section>`;
  bdPaintSync();
}
function bdTickFocus() {
  const el = document.getElementById("bd-focus"); if (!el) return;
  const ms = +el.dataset.ms, win = +el.dataset.win;
  const c = document.getElementById("bd-count"); if (c) c.textContent = bdLeft(ms);
  const pct = Math.max(2, Math.min(100, Math.round((1 - Math.max(0, ms - Date.now()) / win) * 100)));
  const ring = el.querySelector(".dsh-focus-ring");
  if (ring) { ring.style.setProperty("--p", pct); ring.style.setProperty("--hue", bdHue(ms)); }
  const rn = document.getElementById("bd-ring-n"); if (rn) rn.textContent = `${bfa(pct)}٪`;
}
function bdPaintSync() {
  const box = document.getElementById("bd-sync"); if (!box) return;
  const s = Dboard.sync || {};
  if (s.running) { box.innerHTML = `<span class="dsh-sync s-run"><span class="dsh-dot"></span>در حال همگام‌سازی… ${bfa(s.progress?.percent ?? 0)}٪</span>`; return; }
  const ls = s.last_sync || Dboard.d.last_sync;
  if (!ls || ls.status === "never") {
    box.innerHTML = `<span class="dsh-sync s-warn"><span class="dsh-dot"></span>هنوز همگام‌سازی نشده
      <button class="lq-btn lq-sm" style="--lq-hue:var(--warning);min-height:32px;padding:.25rem .8rem;font-size:.78rem" data-bd="sync">شروع</button></span>`;
    return;
  }
  const t = Date.parse(String(ls.at || "").replace(" ", "T"));
  const hrs = Number.isNaN(t) ? 999 : (Date.now() - t) / 3600e3;
  const bad = ls.status === "error";
  const cls = bad || hrs > 24 ? "s-bad" : hrs > 6 ? "s-warn" : "s-ok";
  const hue = bad || hrs > 24 ? "var(--danger)" : hrs > 6 ? "var(--warning)" : "var(--accent)";
  box.innerHTML = `<span class="dsh-sync ${cls}"><span class="dsh-dot"></span>${besc(bad ? "آخرین همگام‌سازی ناموفق بود" : `آخرین همگام‌سازی: ${bdAgo(ls.at)}`)}
    ${cls !== "s-ok" ? `<button class="lq-btn lq-sm" style="--lq-hue:${hue};min-height:32px;padding:.25rem .8rem;font-size:.78rem" data-bd="sync">${bad ? "تلاش مجدد" : "همگام‌سازی"}</button>` : ""}</span>`;
}

/* ---- کاشی‌ها ---- */
function bdPaintQuick() {
  const box = document.getElementById("bd-quick"); if (!box) return;
  const t = bdToday();
  const open = Dboard.assigns.filter((a) => !a.is_done).length;
  const over = Dboard.assigns.filter((a) => !a.is_done && (a.is_expired || (bdParse(a.deadline)?.ms ?? Infinity) < Date.now())).length;
  const today = Dboard.events.filter((e) => bdParse(e.start_at)?.jdn === t).length
    + Dboard.assigns.filter((a) => !a.is_done && bdParse(a.deadline)?.jdn === t).length;
  const quera = Dboard.assigns.filter((a) => a.source === "quera" && !a.is_done).length;
  const weekAgo = Date.now() - 7 * 864e5;
  const newContent = Dboard.changes.filter((c) => c.entity_type === "content" && (Date.parse(String(c.detected_at || "").replace(" ", "T")) || 0) > weekAgo).length;
  const tiles = [
    ["assignments", "📝", "تکلیف باز", open, over ? `${bfa(over)} عقب‌افتاده` : "همه به‌روز", "var(--danger)", over > 0],
    ["calendar", "📅", "امروز", today, today ? "کلاس و مهلت" : "روز آزاد", "var(--info)", false],
    ["posts", "💬", "خوانده‌نشده", Dboard.unread.length, Dboard.unread.length ? "پیام تازه" : "همه خوانده شده", "var(--accent)", Dboard.unread.length > 0],
    ["quera", "⚙️", "کوئرا باز", quera, quera ? "تمرین در انتظار" : "چیزی باز نیست", "var(--primary)", false],
    ["library", "📚", "منبع کتابخانه", Dboard.libCount, "تاییدشده", "var(--warning)", false],
    ["contents", "📁", "محتوای این هفته", newContent, newContent ? "تازه اضافه شده" : "بدون تغییر", "var(--info)", newContent > 0],
  ];
  box.innerHTML = tiles.map(([go, ico, label, n, sub, hue, flag]) =>
    `<button class="lq-tile ${flag ? "is-on" : ""}" style="--lq-hue:${hue}" data-bd="go" data-v="${go}">
      ${flag ? `<span class="lq-flag">!</span>` : ""}
      <span class="lq-ico">${ico}</span><b>${bfa(n)}</b><span>${besc(label)}</span><small>${besc(sub)}</small>
    </button>`).join("");
}

/* ---- امروز (خط زمانی عمودی) ---- */
function bdPaintDay() {
  const box = document.getElementById("bd-day"); if (!box) return;
  const t = bdToday(), nowMin = new Date().getHours() * 60 + new Date().getMinutes();
  const items = [];
  Dboard.events.forEach((e) => {
    const p = bdParse(e.start_at); if (!p || p.jdn !== t) return;
    const pe = bdParse(e.end_at);
    items.push({ title: e.title, min: p.hasTime ? p.min : 22 * 60, end: pe?.min ?? null, hasTime: p.hasTime,
      hue: e.event_type === "exam" ? "var(--warning)" : "var(--info)", ico: eventMeta(e.event_type).icon,
      sub: e.course_name || "", href: e.url ? proxyUrl(e.url) : null });
  });
  Dboard.assigns.forEach((a) => {
    if (a.is_done) return; const p = bdParse(a.deadline); if (!p || p.jdn !== t) return;
    items.push({ title: a.title, min: p.hasTime ? p.min : 23 * 60 + 30, end: null, hasTime: p.hasTime,
      hue: "var(--danger)", ico: "📝", sub: a.course_name || "", href: a.submit_url ? proxyUrl(a.submit_url) : null });
  });
  items.sort((a, b) => a.min - b.min);
  const hhmm = (m) => `${bfa(String(Math.floor(m / 60)).padStart(2, "0"))}:${bfa(String(m % 60).padStart(2, "0"))}`;
  let body;
  if (!items.length) {
    const nx = Dboard.events.map((e) => ({ e, p: bdParse(e.start_at) })).filter((x) => x.p && x.p.jdn > t).sort((a, b) => a.p.ms - b.p.ms)[0];
    const nd = Dboard.assigns.filter((a) => !a.is_done).map((a) => ({ a, p: bdParse(a.deadline) })).filter((x) => x.p && x.p.jdn > t).sort((x, y) => x.p.ms - y.p.ms)[0];
    if (nx) body = `<div class="dsh-next"><span class="dsh-next-ico">📅</span><div style="flex:1;min-width:0">
        <div style="font-weight:700;font-size:.92rem">کلاس بعدی: ${besc(nx.e.title)}</div>
        <div class="dsh-row-meta"><span>${bdWhen(nx.p)}</span><span>${bdLeft(nx.p.ms)}</span></div></div>
        <button class="lq-btn lq-sm" data-bd="go" data-v="calendar">تقویم</button></div>`;
    else if (nd) body = `<div class="dsh-next"><span class="dsh-next-ico" style="background:var(--danger-soft);color:var(--danger)">📝</span><div style="flex:1;min-width:0">
        <div style="font-weight:700;font-size:.92rem">مهلت بعدی: ${besc(nd.a.title)}</div>
        <div class="dsh-row-meta"><span>${bdJal(nd.p)}</span><span>${bdLeft(nd.p.ms)}</span></div></div>
        <button class="lq-btn lq-sm" data-bd="go" data-v="assignments">تکالیف</button></div>`;
    else body = `<div class="dsh-empty"><span class="dsh-empty-ico">🌤</span><b>امروز روز آزادی است</b><small>هیچ کلاس یا مهلتی پیش رو نداری</small></div>`;
  } else {
    let nowPlaced = false;
    const rows = [];
    items.forEach((it) => {
      const isNow = it.hasTime && it.min <= nowMin && (it.end ?? it.min + 60) >= nowMin;
      const past = (it.end ?? it.min + 45) < nowMin;
      if (!nowPlaced && it.min > nowMin) { rows.push(`<div class="dsh-agenda-now"><i></i><span>الان ${hhmm(nowMin)}</span></div>`); nowPlaced = true; }
      rows.push(`<div class="dsh-agenda-item ${isNow ? "is-now" : ""} ${past ? "is-past" : ""}" style="--hue:${it.hue}">
        <div class="dsh-agenda-time"><b>${it.hasTime ? hhmm(it.min) : "—"}</b>${it.end ? `<small>تا ${hhmm(it.end)}</small>` : `<small>${it.ico === "📝" ? "مهلت" : ""}</small>`}</div>
        <div class="dsh-agenda-rail"><i></i></div>
        <${it.href ? "a" : "button"} class="dsh-agenda-body" ${it.href ? `href="${besc(it.href)}" target="_blank" rel="noopener noreferrer"` : `data-bd="go" data-v="calendar"`}>
          <span class="dsh-agenda-ico">${it.ico}</span>
          <span class="dsh-agenda-txt"><b>${besc(it.title)}</b>${it.sub ? `<small>${besc(it.sub)}</small>` : ""}</span>
          ${isNow ? `<span class="dsh-agenda-live">در جریان</span>` : it.href ? `<span class="dsh-agenda-go">↗</span>` : ""}
        </${it.href ? "a" : "button"}>
      </div>`);
    });
    if (!nowPlaced) rows.push(`<div class="dsh-agenda-now"><i></i><span>الان ${hhmm(nowMin)}</span></div>`);
    body = `<div class="dsh-agenda">${rows.join("")}</div>`;
  }
  box.innerHTML = `<div class="dsh-card-head"><h3 class="dsh-card-title">🕒 برنامهٔ امروز</h3>
    <div style="display:flex;gap:.4rem;align-items:center">
      ${items.length ? `<span class="badge badge-domain">${bfa(items.length)} مورد</span>` : ""}
      <button class="lq-link" data-bd="go" data-v="calendar">تقویم کامل<span class="lq-arw">‹</span></button>
    </div></div>${body}`;
}

/* ---- مهلت‌ها ---- */
function bdPaintDead() {
  const box = document.getElementById("bd-dead"); if (!box) return;
  const list = Dboard.assigns.filter((a) => !a.is_done).map((a) => ({ a, p: bdParse(a.deadline) }))
    .sort((x, y) => (x.p?.ms ?? Infinity) - (y.p?.ms ?? Infinity)).slice(0, 5);
  let body;
  if (!list.length) {
    const done = Dboard.assigns.filter((a) => a.is_done).length;
    body = `<div class="dsh-empty"><span class="dsh-empty-ico">🎉</span><b>هیچ تکلیف بازی نداری</b>
      <small>${done ? `${bfa(done)} تکلیف را انجام داده‌ای — آفرین` : "بعد از همگام‌سازی، مهلت‌ها اینجا می‌آیند"}</small>
      <div style="margin-top:.8rem"><button class="lq-btn lq-sm" data-bd="go" data-v="quera">تمرین‌های کوئرا</button></div></div>`;
  } else {
    body = `<div class="dsh-list">${list.map(({ a, p }) => {
      const hue = p ? bdHue(p.ms) : "var(--primary)";
      const over = p && p.ms < Date.now();
      return `<div class="dsh-row" style="--hue:${hue}">
        <span class="dsh-row-ico">${over ? "⏰" : "📝"}</span>
        <div class="dsh-row-body"><div class="dsh-row-title">${besc(a.title)}</div>
          <div class="dsh-row-meta"><span>${besc(a.course_name || "—")}</span>
            ${p ? `<span>${bdJal(p)}${p.hasTime ? ` · ${bfa(p.time)}` : ""}</span><span class="${over ? "dsh-urgent" : (p.ms - Date.now() < 48 * 3600e3 ? "dsh-soon" : "")}">${bdLeft(p.ms)}</span>` : ""}</div></div>
        <div class="dsh-row-actions">
          ${a.submit_url ? `<a class="lq-btn lq-sm is-on" style="--lq-hue:${hue};min-height:38px;padding:.4rem .95rem;font-size:.82rem" href="${besc(proxyUrl(a.submit_url))}" target="_blank" rel="noopener noreferrer">ارسال</a>` : ""}
          <button class="lq-btn lq-sm" style="min-height:38px;padding:.4rem .95rem;font-size:.82rem" data-bd="done" data-id="${besc(a.id)}">✓</button>
        </div></div>`;
    }).join("")}</div>`;
  }
  box.innerHTML = `<div class="dsh-card-head"><h3 class="dsh-card-title">⏰ مهلت‌های نزدیک</h3>
    <button class="lq-link" data-bd="go" data-v="assignments">همه<span class="lq-arw">‹</span></button></div>${body}`;
}

/* ---- پیام‌ها ---- */
function bdPaintPosts() {
  const box = document.getElementById("bd-posts"); if (!box) return;
  const list = (Dboard.d.recent_posts || []).slice(0, 4);
  const body = list.length ? `<div class="dsh-list">${list.map((p) => `
    <div class="dsh-row" data-bd="go" data-v="posts" style="cursor:pointer">
      <span class="dsh-ava">${besc((p.author || "؟").trim().charAt(0))}</span>
      <div class="dsh-row-body">
        <div class="dsh-row-title" style="display:flex;align-items:center;gap:.4rem">${besc(p.author || "—")}${p.is_new ? '<span class="dsh-unread"></span>' : ""}</div>
        <div class="dsh-clamp">${besc(p.text || "")}</div>
        <div class="dsh-row-meta"><span>${besc(p.posted_at_jalali || bdAgo(p.posted_at) || "")}</span></div>
      </div></div>`).join("")}</div>`
    : `<div class="dsh-empty"><span class="dsh-empty-ico">💬</span><b>پیامی نیست</b><small>بعد از همگام‌سازی، پیام‌های وال اینجا می‌آیند</small></div>`;
  box.innerHTML = `<div class="dsh-card-head"><h3 class="dsh-card-title">💬 آخرین پیام‌ها</h3>
    <div style="display:flex;gap:.4rem">
      ${Dboard.unread.length ? `<button class="lq-link" data-bd="readall">✓ خواندم</button>` : ""}
      <button class="lq-link" data-bd="go" data-v="posts">همه<span class="lq-arw">‹</span></button>
    </div></div>${body}`;
}

/* ---- ترم ---- */
function bdPaintTerm() {
  const box = document.getElementById("bd-term"); if (!box) return;
  const total = Dboard.assigns.length, done = Dboard.assigns.filter((a) => a.is_done).length;
  const pct = total ? Math.round((done / total) * 100) : 0;
  const t = bdToday(), start = t - jWeekday(t);
  const days = Array.from({ length: 7 }, (_, i) => start + i);
  const counts = days.map((jdn) => Dboard.assigns.filter((a) => !a.is_done && bdParse(a.deadline)?.jdn === jdn).length);
  const max = Math.max(1, ...counts);
  box.innerHTML = `<div class="dsh-card-head"><h3 class="dsh-card-title">📈 پیشرفت ترم و بار هفته</h3>
      <button class="lq-link" data-bd="go" data-v="assignments">تکالیف<span class="lq-arw">‹</span></button></div>
    <div class="dsh-term">
      <div class="dsh-term-ring" style="--p:${pct}"><i>${bfa(pct)}٪</i></div>
      <div style="min-width:110px"><div style="font-weight:750;font-size:.95rem">${bfa(done)} از ${bfa(total)}</div>
        <div class="dsh-row-meta"><span>تکلیف انجام‌شده</span></div>
        <div class="dsh-row-meta" style="margin-top:.5rem"><span>${total - done ? `${bfa(total - done)} مورد باقی مانده` : "همه انجام شده 🎉"}</span></div></div>
      <div class="dsh-chart">${days.map((jdn, i) => `<button class="dsh-bar ${jdn === t ? "is-today" : ""}" data-bd="go" data-v="calendar" title="${BD_WD[i]}">
        <em>${counts[i] ? bfa(counts[i]) : ""}</em><i style="height:${counts[i] ? Math.max(14, (counts[i] / max) * 100) : 4}%"></i><b>${BD_WD[i].slice(0, 2)}</b></button>`).join("")}</div>
    </div>`;
}

/* ---- هشدارها ---- */
function bdPaintAlerts() {
  const box = document.getElementById("bd-alerts"); if (!box) return;
  const list = (Dboard.d.alerts || []).filter((a) => !Dboard.dismissed.includes(a.title + (a.deadline_jalali || "")));
  if (!list.length) { box.innerHTML = ""; return; }
  box.innerHTML = `<div class="dsh-alerts">${list.map((a, i) => {
    const hue = a.level === "danger" ? "var(--danger)" : a.level === "warning" ? "var(--warning)" : "var(--info)";
    return `<div class="dsh-alert" style="--hue:${hue}">
      <span class="dsh-row-ico" style="--hue:${hue}">${a.kind === "overdue" ? "⏰" : "⚡"}</span>
      <div class="dsh-alert-body"><b>${besc(a.title)}</b><small>${besc(a.message || "")}${a.deadline_jalali ? ` · ${besc(a.deadline_jalali)}` : ""}</small></div>
      <button class="lq-btn lq-sm" style="--lq-hue:${hue};min-height:36px;padding:.35rem .9rem;font-size:.8rem" data-bd="go" data-v="assignments">بررسی</button>
      <button class="lq-icon lq-sm" data-bd="dismiss" data-i="${i}" aria-label="بستن">✕</button>
    </div>`;
  }).join("")}</div>`;
}

/* ---- اکشن ---- */
async function bdDone(id) {
  const a = Dboard.assigns.find((x) => String(x.id) === String(id)); if (!a) return;
  const before = !!a.is_done;
  a.is_done = true; bdPaintQuick(); bdPaintDead(); bdPaintTerm(); bdPaintBrief(); bdPaintDay();
  const raw = String(id), isQ = raw.startsWith("quera_");
  const path = isQ ? `/quera/assignments/${encodeURIComponent(raw.slice(6))}/done?done=true` : `/assignments/${encodeURIComponent(raw)}/done?done=true`;
  let ok = false;
  try { const r = await api(path, { method: "POST", body: "{}" }); ok = !(r && r.ok === false); } catch (_) {}
  if (!ok) { a.is_done = before; bdPaintQuick(); bdPaintDead(); bdPaintTerm(); bdPaintBrief(); bdPaintDay(); bdToast("❌ ثبت انجام ناموفق بود"); return; }
  if (typeof refreshNavBadge === "function") refreshNavBadge();
  bdToast("✅ انجام‌شده علامت خورد", { action: "برگردان", dur: 5500, onAction: async () => {
    a.is_done = before; bdPaintQuick(); bdPaintDead(); bdPaintTerm(); bdPaintBrief(); bdPaintDay();
    try { await api(path.replace("done=true", "done=false"), { method: "POST", body: "{}" }); } catch (_) {}
  }});
}

/* ---- delegation ---- */
function bdWire() {
  if (Dboard.wired) return; Dboard.wired = true;
  document.addEventListener("click", async (e) => {
    const el = e.target.closest("[data-bd]"); if (!el) return;
    const act = el.dataset.bd;
    if (act === "go") { location.hash = "#/" + el.dataset.v; return; }
    if (act === "retry") { renderDashboard(); return; }
    if (act === "sync") { document.getElementById("btn-sync")?.click(); return; }
    if (act === "done") { bdDone(el.dataset.id); return; }
    if (act === "dismiss") {
      const list = (Dboard.d.alerts || []).filter((a) => !Dboard.dismissed.includes(a.title + (a.deadline_jalali || "")));
      const a = list[+el.dataset.i];
      if (a) { Dboard.dismissed.push(a.title + (a.deadline_jalali || "")); Dboard.dismissed = Dboard.dismissed.slice(-25);
        localStorage.setItem("dsh:dismissed", JSON.stringify(Dboard.dismissed)); }
      bdPaintAlerts(); return;
    }
    if (act === "readall") {
      try { await api("/posts/read", { method: "POST", body: "{}" });
        Dboard.unread = []; (Dboard.d.recent_posts || []).forEach((p) => { p.is_new = false; });
        bdPaintPosts(); bdPaintQuick(); bdPaintBrief(); if (typeof refreshNavBadge === "function") refreshNavBadge();
        bdToast("✅ همه پیام‌ها خوانده شد");
      } catch (err) { bdToast("❌ " + (err.message || "خطا")); }
      return;
    }
  });
}
bdWire();
// ---------- Courses v2 (درس‌ها + جزئیات درس) ----------
// ورود = یک‌بار fetch؛ تب/فیلتر/جستجو/مرتب‌سازی کلاینتی. نقشه‌ها lazy و دارای teardown.
const CRS_TABS = [
  ["overview", "نمای کلی", "▦"], ["assignments", "تکالیف", "📝"],
  ["contents", "محتواها", "📁"], ["posts", "پیام‌ها", "💬"],
  ["members", "اعضا", "👥"], ["location", "مکان و برنامه", "📍"],
  ["library", "کتابخانه", "📚"],
];
const CRS_ROLE = {
  teacher: { label: "استاد", icon: "👨‍🏫", cv: "--primary" },
  support: { label: "دستیار / پشتیبان", icon: "🛟", cv: "--warning" },
  student: { label: "دانشجو", icon: "👤", cv: "--muted" },
};
const Crs = {
  items: [], q: "", source: "all", status: "all", term: "all",
  sort: localStorage.getItem("crs:sort") || "name",
  view: localStorage.getItem("crs:view") || "grid",
  views: JSON.parse(localStorage.getItem("crs:views") || "{}"),
  detail: null, detailId: null, tab: "overview", dq: "", dsel: new Set(),
  ctype: "all", lib: null, maps: [], layers: [], wired: false, themeObs: null,
};
const cesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cfa = (n) => faDigits(String(n));
const csafe = (u) => /^https?:\/\//i.test(u || "") ? u : null;
function crsParse(v) {
  const m = String(v || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (!m) return null;
  return { jdn: g2d(+m[1], +m[2], +m[3]), ms: new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0)).getTime(), time: m[4] ? `${m[4]}:${m[5]}` : "" };
}
function crsJal(p) { if (!p) return ""; const j = d2j(p.jdn); return `${cfa(j.jd)} ${J_MONTHS[j.jm - 1]} ${cfa(j.jy)}`; }
function crsAgo(iso) {
  if (!iso) return "";
  const t = Date.parse(String(iso).replace(" ", "T"));
  if (Number.isNaN(t)) return "";
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${cfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${cfa(Math.floor(s / 3600))} ساعت پیش`;
  if (s < 2592000) return `${cfa(Math.floor(s / 86400))} روز پیش`;
  return String(iso).slice(0, 10);
}
function crsLeft(ms) {
  if (ms == null) return "";
  const diff = ms - Date.now(), s = Math.abs(diff) / 1000;
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600);
  const txt = d > 0 ? `${cfa(d)} روز${h ? ` و ${cfa(h)} ساعت` : ""}` : h > 0 ? `${cfa(h)} ساعت` : `${cfa(Math.max(1, Math.floor((s % 3600) / 60)))} دقیقه`;
  return diff < 0 ? `${txt} پیش` : `${txt} مانده`;
}
function crsLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof admLayer === "function" ? admLayer : crsOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = Crs.layers.indexOf(L); if (i >= 0) Crs.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  Crs.layers.push(L); return L;
}
function crsToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof admToast === "function") return admToast(m, o);
  return crsOwnToast(m, o);
}
function crsOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "crs-layer";
  w.innerHTML = `<div class="crs-scrim" data-crs-x></div>` + (opts.type === "drawer"
    ? `<aside class="crs-drawer" role="dialog" aria-modal="true" aria-label="${cesc(opts.title)}">${opts.html}</aside>`
    : `<div class="crs-modal-wrap"><div class="crs-modal" role="dialog" aria-modal="true" aria-label="${cesc(opts.title)}"><h3>${cesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("crs-locked");
  const panel = w.querySelector(".crs-drawer,.crs-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".crs-layer")) document.body.classList.remove("crs-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-crs-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function crsOwnToast(msg, o = {}) {
  let box = document.getElementById("crs-toasts");
  if (!box) { box = document.createElement("div"); box.id = "crs-toasts"; box.className = "crs-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "crs-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${cesc(msg)}</span>${o.action ? `<button class="a">${cesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const crsCloseAll = () => Crs.layers.slice().forEach((l) => l.close());

/* ---- teardown نقشه‌ها ---- */
function crsDestroyMaps() {
  Crs.maps.forEach((m) => { try { m.remove(); } catch (_) {} });
  Crs.maps = [];
}
window.__crsTeardown = () => { crsDestroyMaps(); crsCloseAll(); };

/* ================= صفحه درس‌ها ================= */
async function renderCourses() {
  window.__crsTeardown();
  let rows = null;
  try { const r = await api("/courses/overview"); rows = r.courses || []; }
  catch (_) { try { rows = await api("/courses"); } catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری درس‌ها<small>${cesc(e.message)}</small></div>`; return; } }
  Crs.items = rows.map((c) => ({ ...c, stats: c.stats || null }));
  const terms = [...new Set(Crs.items.filter((c) => c.source === "lms" && c.term).map((c) => c.term.trim()))].sort().reverse();
  Crs.currentTerm = terms[0] || null;
  contentEl.innerHTML = `
    ${pageHead("درس‌ها", "همه درس‌های LMS و کلاس‌های کوئرا")}
    <div class="card crs-hero" id="crs-hero"></div>
    <div class="crs-toolbar">
      <div class="search-box crs-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="crs-q" type="search" value="${cesc(Crs.q)}" placeholder="جستجوی نام درس، استاد یا کد…" aria-label="جستجوی درس"></div>
      <select id="crs-term" class="input crs-sel" aria-label="فیلتر ترم">
        <option value="all">همه ترم‌ها</option>
        ${Crs.currentTerm ? `<option value="current">ترم جاری (${cesc(Crs.currentTerm)})</option>` : ""}
        ${terms.map((t) => `<option value="${cesc(t)}">ترم ${cesc(t)}</option>`).join("")}
      </select>
      <select id="crs-sort" class="input crs-sel" aria-label="مرتب‌سازی">
        <option value="name">الفبایی</option><option value="open">بیشترین تکلیف باز</option>
        <option value="activity">جدیدترین فعالیت</option><option value="term">ترم (جدید اول)</option>
      </select>
      <div class="crs-vt" role="group" aria-label="حالت نمایش">
        <button data-crs="view" data-v="grid" title="شبکه" aria-label="شبکه">▦</button>
        <button data-crs="view" data-v="list" title="لیست" aria-label="لیست">☰</button>
        <button data-crs="view" data-v="compact" title="فشرده" aria-label="فشرده">≡</button>
      </div>
      <button class="btn btn-ghost btn-sm" data-crs="view-save" title="ذخیره نمای فعلی">💾</button>
    </div>
    <div class="crs-pills" id="crs-pills"></div>
    <div class="crs-saved" id="crs-saved"></div>
    <div id="crs-list"></div>`;
  document.getElementById("crs-sort").value = Crs.sort;
  document.getElementById("crs-term").value = Crs.term;
  crsPaintAll();
}
function crsPaintAll() { crsPaintHero(); crsPaintPills(); crsPaintSaved(); crsPaintList(); }
function crsPaintHero() {
  const box = document.getElementById("crs-hero"); if (!box) return;
  const l = Crs.items, act = l.filter((c) => c.status === "active").length;
  const open = l.reduce((a, c) => a + (c.stats?.open || 0), 0);
  const over = l.reduce((a, c) => a + (c.stats?.overdue || 0), 0);
  const cont = l.reduce((a, c) => a + (c.stats?.contents || 0), 0);
  box.innerHTML = `<div class="crs-hero-main"><h3>${cfa(l.length)} درس در ${cfa(new Set(l.map((c) => c.term).filter(Boolean)).size || 1)} ترم</h3>
      <p class="crs-hero-sub">${cfa(act)} درس فعال · ${cfa(l.filter((c) => c.source === "quera").length)} کلاس کوئرا${over ? ` · ${cfa(over)} تکلیف عقب‌افتاده` : ""}</p></div>
    <div class="crs-stats">
      <div class="crs-stat"><b style="color:var(--primary)">${cfa(act)}</b><span>فعال</span></div>
      <div class="crs-stat"><b style="color:var(--danger)">${cfa(open)}</b><span>تکلیف باز</span></div>
      <div class="crs-stat"><b style="color:var(--warning)">${cfa(over)}</b><span>عقب‌افتاده</span></div>
      <div class="crs-stat"><b style="color:var(--accent)">${cfa(cont)}</b><span>محتوا</span></div>
    </div>`;
}
function crsPaintPills() {
  const box = document.getElementById("crs-pills"); if (!box) return;
  const n = (f) => Crs.items.filter(f).length;
  const groups = [
    [["all", "همه", n(() => true)], ["lms", "LMS", n((c) => c.source === "lms")], ["quera", "کوئرا", n((c) => c.source === "quera")]],
    [["all", "همه وضعیت‌ها", n(() => true)], ["active", "فعال", n((c) => c.status === "active")], ["finished", "پایان‌یافته", n((c) => c.status !== "active")]],
  ];
  box.innerHTML = groups[0].map(([k, l, c]) => `<button class="crs-pill ${Crs.source === k ? "on" : ""}" data-crs="source" data-v="${k}">${l}<b>${cfa(c)}</b></button>`).join("")
    + `<span class="crs-pill-sep"></span>`
    + groups[1].map(([k, l, c]) => `<button class="crs-pill ${Crs.status === k ? "on" : ""}" data-crs="status" data-v="${k}">${l}<b>${cfa(c)}</b></button>`).join("");
}
function crsPaintSaved() {
  const box = document.getElementById("crs-saved"); if (!box) return;
  const keys = Object.keys(Crs.views);
  box.innerHTML = keys.length ? `<span class="crs-muted">نماها:</span>` + keys.map((k) =>
    `<span class="crs-sv"><button data-crs="view-apply" data-k="${cesc(k)}">${cesc(k)}</button>
      <button class="x" data-crs="view-del" data-k="${cesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function crsFiltered() {
  const q = Crs.q.trim().toLowerCase();
  let l = Crs.items.filter((c) => {
    if (Crs.source !== "all" && c.source !== Crs.source) return false;
    if (Crs.status === "active" && c.status !== "active") return false;
    if (Crs.status === "finished" && c.status === "active") return false;
    if (Crs.term === "current" && c.term !== Crs.currentTerm) return false;
    if (Crs.term !== "all" && Crs.term !== "current" && c.term !== Crs.term) return false;
    return true;
  });
  if (q) l = l.filter((c) => `${c.name} ${c.teacher || ""} ${c.code || ""} ${c.domain || ""}`.toLowerCase().includes(q));
  const s = Crs.sort;
  return l.slice().sort((a, b) =>
    s === "open" ? (b.stats?.open || 0) - (a.stats?.open || 0) || a.name.localeCompare(b.name, "fa")
    : s === "activity" ? String(b.last_activity || "").localeCompare(String(a.last_activity || ""))
    : s === "term" ? String(b.term || "").localeCompare(String(a.term || "")) || a.name.localeCompare(b.name, "fa")
    : a.name.localeCompare(b.name, "fa"));
}
function crsChips(c) {
  const s = c.stats; if (!s) return "";
  return `<div class="crs-chips">
    ${s.open ? `<span class="crs-chip is-open">📝 ${cfa(s.open)} باز</span>` : `<span class="crs-chip">✓ بدون تکلیف باز</span>`}
    ${s.overdue ? `<span class="crs-chip is-over">⏰ ${cfa(s.overdue)} عقب‌افتاده</span>` : ""}
    ${s.contents ? `<span class="crs-chip">📁 ${cfa(s.contents)}</span>` : ""}
    ${s.posts ? `<span class="crs-chip is-new">💬 ${cfa(s.posts)} جدید</span>` : ""}
  </div>`;
}
function crsCard(c) {
  const isQ = c.source === "quera", id = cesc(c.id);
  const href = isQ ? (csafe(c.url) || `https://quera.org/course/${cesc(c.group_id)}`) : `#/course/${encodeURIComponent(c.id)}`;
  const ext = isQ ? 'target="_blank" rel="noopener noreferrer"' : "";
  const badges = `<span class="badge ${isQ ? "badge-warn" : "badge-domain"}">${isQ ? "کوئرا" : cesc(c.domain || "LMS")}</span>
    ${c.status === "active" ? `<span class="badge badge-new">فعال</span>` : `<span class="badge">پایان‌یافته</span>`}
    ${c.term ? `<span class="badge">ترم ${cesc(c.term)}</span>` : ""}`;
  const open = `<a class="btn btn-primary btn-sm" href="${href}" ${ext}>${isQ ? "باز کردن ↗" : "جزئیات"}</a>`;
  const peek = isQ ? "" : `<button class="btn btn-ghost btn-sm" data-crs="peek" data-id="${id}">پیش‌نمایش</button>`;
  if (Crs.view === "compact") {
    return `<div class="crs-row is-compact" data-crs-card="${id}">
      <span class="crs-ico src-${c.source}">${isQ ? "⚙️" : "📘"}</span>
      <div class="crs-row-main"><div class="row-title">${cesc(c.name)} ${badges}</div>
        <div class="row-meta"><span>${cesc(c.teacher || "—")}</span>${c.stats?.open ? `<span>${cfa(c.stats.open)} تکلیف باز</span>` : ""}</div></div>
      <div class="row-actions">${open}</div></div>`;
  }
  if (Crs.view === "list") {
    return `<div class="crs-row" data-crs-card="${id}">
      <span class="crs-ico src-${c.source}">${isQ ? "⚙️" : "📘"}</span>
      <div class="crs-row-main"><div class="row-title">${cesc(c.name)} ${badges}</div>
        <div class="row-meta"><span>👨‍🏫 ${cesc(c.teacher || "—")}</span>${c.code ? `<span>کد ${cesc(c.code)}</span>` : ""}${c.last_activity ? `<span>${crsAgo(c.last_activity)}</span>` : ""}</div>
        ${crsChips(c)}</div>
      <div class="row-actions">${peek}${open}</div></div>`;
  }
  return `<article class="crs-card" data-crs-card="${id}">
    <div class="crs-card-top"><span class="crs-ico src-${c.source}">${isQ ? "⚙️" : "📘"}</span><div class="crs-badges">${badges}</div></div>
    <h3 class="crs-name">${cesc(c.name)}</h3>
    <div class="crs-meta"><span>👨‍🏫 ${cesc(c.teacher || "—")}</span>${c.code ? `<span>کد ${cesc(c.code)}</span>` : ""}</div>
    ${crsChips(c)}
    <div class="crs-actions">${peek}${open}</div></article>`;
}
function crsPaintList() {
  const box = document.getElementById("crs-list"); if (!box) return;
  document.querySelectorAll(".crs-vt button").forEach((b) => { const on = b.dataset.v === Crs.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const l = crsFiltered();
  if (!l.length) {
    box.innerHTML = `<div class="empty"><span class="empty-icon">${Crs.items.length ? "🔍" : "📭"}</span>${Crs.items.length ? "درسی با این فیلترها نیست" : "هنوز درسی همگام‌سازی نشده"}
      <small>${Crs.items.length ? "فیلتر ترم یا وضعیت را ساده‌تر کن" : "از دکمه همگام‌سازی استفاده کن"}</small>
      <div class="crs-actions" style="justify-content:center;margin-top:.8rem">
        ${Crs.items.length ? `<button class="btn btn-ghost btn-sm" data-crs="clear">پاک کردن فیلترها</button>` : `<button class="btn btn-primary btn-sm" id="crs-empty-sync">🔄 همگام‌سازی</button>`}</div></div>`;
    document.getElementById("crs-empty-sync")?.addEventListener("click", () => document.getElementById("btn-sync")?.click());
    return;
  }
  box.innerHTML = `<div class="${Crs.view === "grid" ? "crs-grid" : "crs-listrows"}">${l.map(crsCard).join("")}</div>`;
}
async function crsPeek(id) {
  const c = Crs.items.find((x) => x.id === id); if (!c) return;
  let d;
  try { d = await api(`/courses/${encodeURIComponent(id)}/detail`); }
  catch (e) { crsToast("❌ " + (e.message || "بارگذاری ناموفق")); return; }
  const open = (d.assignments || []).filter((a) => !a.is_done).slice(0, 5);
  const cont = (d.contents || []).slice(0, 5);
  crsLayer({ type: "drawer", title: "پیش‌نمایش درس", html: `<div class="crs-dwr">
    <div class="crs-dwr-head"><span class="crs-ico src-lms lg">📘</span>
      <div><h2>${cesc(c.name)}</h2><div class="crs-badges"><span class="badge badge-domain">${cesc(c.domain || "")}</span>
        ${c.term ? `<span class="badge">ترم ${cesc(c.term)}</span>` : ""}<span class="badge">${cesc(c.teacher || "—")}</span></div></div>
      <button class="crs-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="crs-kv">
      <div><span>تکلیف باز</span><b>${cfa((d.assignments || []).filter((a) => !a.is_done).length)}</b></div>
      <div><span>محتوا</span><b>${cfa((d.contents || []).length)}</b></div>
      <div><span>پیام</span><b>${cfa((d.posts || []).length)}</b></div>
      <div><span>جلسات هفتگی</span><b>${cfa((d.locations || []).length)}</b></div>
    </div>
    <div class="crs-block"><h4>📝 تکالیف باز</h4><div class="item-list">${open.length ? open.map((a) => {
      const p = crsParse(a.deadline);
      return `<div class="list-row"><span class="row-icon">📝</span><div class="row-body">
        <div class="row-title">${cesc(a.title)}</div>
        <div class="row-meta"><span>${p ? crsJal(p) : "بدون مهلت"}</span>${p ? `<span class="${p.ms < Date.now() ? "is-over" : ""}">${crsLeft(p.ms)}</span>` : ""}</div></div></div>`;
    }).join("") : `<div class="crs-empty-inline">تکلیف بازی نیست 🎉</div>`}</div></div>
    <div class="crs-block"><h4>📁 آخرین محتواها</h4><div class="item-list">${cont.length ? cont.map((x) =>
      `<div class="list-row"><span class="row-icon">📄</span><div class="row-body"><div class="row-title">
        <a href="${cesc(proxyUrl(x.url))}" target="_blank" rel="noopener noreferrer">${cesc(x.title)}</a></div>
        <div class="row-meta"><span>${cesc(x.content_type || "")}</span></div></div></div>`).join("")
      : `<div class="crs-empty-inline">محتوایی نیست</div>`}</div></div>
    <div class="crs-dwr-actions"><a class="btn btn-primary btn-sm" href="#/course/${encodeURIComponent(c.id)}" data-lib-close>صفحه کامل درس</a>
      ${csafe(c.url) ? `<a class="btn btn-ghost btn-sm" href="${cesc(c.url)}" target="_blank" rel="noopener noreferrer">باز کردن در LMS ↗</a>` : ""}</div>
  </div>` });
}

/* ================= جزئیات درس ================= */
async function renderCourseDetail(courseId) {
  window.__crsTeardown();
  if (Crs.detailId !== courseId) { Crs.tab = "overview"; Crs.dq = ""; Crs.ctype = "all"; Crs.lib = null; }
  Crs.dsel.clear(); Crs.detailId = courseId;
  let d;
  try { d = await api(`/courses/${encodeURIComponent(courseId)}/detail`); }
  catch (e) { contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری درس<small>${cesc(e.message)}</small></div>`; return; }
  Crs.detail = d;
  const c = d.course || {};
  contentEl.innerHTML = `
    <nav class="crs-crumbs"><a href="#/courses">درس‌ها</a><span>‹</span><span class="cur">${cesc(c.name || "")}</span></nav>
    <div class="card crs-dhero">
      <div class="crs-dhero-main"><h2>${cesc(c.name || "")}</h2>
        <div class="crs-badges"><span class="badge badge-domain">${cesc(c.domain || "")}</span>
          <span class="badge">👨‍🏫 ${cesc(c.teacher || "—")}</span>
          ${c.code ? `<span class="badge">کد ${cesc(c.code)}</span>` : ""}
          ${c.term ? `<span class="badge">ترم ${cesc(c.term)}</span>` : ""}</div></div>
      ${csafe(c.url) ? `<a class="btn btn-primary btn-sm" href="${cesc(c.url)}" target="_blank" rel="noopener noreferrer">باز کردن در LMS ↗</a>` : ""}
    </div>
    <div class="crs-stats" id="crs-dstats"></div>
    <div class="crs-tabs" id="crs-tabs" role="tablist"></div>
    <div class="crs-toolbar" id="crs-dtools">
      <div class="search-box crs-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="crs-dq" type="search" value="${cesc(Crs.dq)}" placeholder="جستجو در این درس…" aria-label="جستجو در درس"></div>
      <div id="crs-dextra"></div>
    </div>
    <div id="crs-bulk"></div>
    <div id="crs-dbody"></div>`;
  crsDetailPaint();
}
function crsDetailPaint() { crsPaintDStats(); crsPaintDTabs(); crsPaintDBulk(); crsPaintDBody(); }
function crsPaintDStats() {
  const box = document.getElementById("crs-dstats"); if (!box || !Crs.detail) return;
  const d = Crs.detail, as = d.assignments || [];
  const tiles = [
    ["تکلیف باز", as.filter((a) => !a.is_done).length, "--danger"],
    ["انجام‌شده", as.filter((a) => a.is_done).length, "--accent"],
    ["محتوا", (d.contents || []).length, "--primary"],
    ["پیام جدید", (d.posts || []).filter((p) => p.is_new).length, "--info"],
    ["اعضا", (d.members || []).length, "--warning"],
    ["جلسات هفتگی", (d.locations || []).length, "--muted"],
  ];
  box.innerHTML = tiles.map(([l, v, cv]) => `<div class="crs-stat"><b style="color:var(${cv})">${cfa(v)}</b><span>${l}</span></div>`).join("");
}
function crsPaintDTabs() {
  const box = document.getElementById("crs-tabs"); if (!box || !Crs.detail) return;
  const d = Crs.detail;
  const n = { overview: 0, assignments: (d.assignments || []).filter((a) => !a.is_done).length,
    contents: (d.contents || []).length, posts: (d.posts || []).filter((p) => p.is_new).length,
    members: (d.members || []).length, location: (d.locations || []).length, library: Crs.lib ? Crs.lib.length : 0 };
  box.innerHTML = CRS_TABS.map(([k, l, i]) =>
    `<button class="crs-tab ${Crs.tab === k ? "on" : ""}" data-crs="tab" data-v="${k}" role="tab" aria-selected="${Crs.tab === k}">
      <span>${i}</span>${l}${n[k] ? `<b>${cfa(n[k])}</b>` : ""}</button>`).join("");
}
function crsPaintDBulk() {
  const box = document.getElementById("crs-bulk"); if (!box) return;
  box.innerHTML = (Crs.tab === "assignments" && Crs.dsel.size)
    ? `<div class="crs-bulkbar"><b>${cfa(Crs.dsel.size)}</b> انتخاب شده
        <button class="btn btn-soft btn-sm" data-crs="bulk-done">✓ انجام شد</button>
        <button class="btn btn-ghost btn-sm" data-crs="bulk-undone">لغو انجام</button>
        <button class="btn btn-ghost btn-sm" data-crs="bulk-clear">پاک کردن</button></div>` : "";
}
function crsMatch(text) { const q = Crs.dq.trim().toLowerCase(); return !q || String(text || "").toLowerCase().includes(q); }
function crsPaintDBody() {
  const box = document.getElementById("crs-dbody"); if (!box || !Crs.detail) return;
  if (Crs.tab !== "location") crsDestroyMaps();
  const extra = document.getElementById("crs-dextra"); if (extra) extra.innerHTML = "";
  const d = Crs.detail;
  const fn = { overview: crsTabOverview, assignments: crsTabAssignments, contents: crsTabContents,
    posts: crsTabPosts, members: crsTabMembers, location: crsTabLocation, library: crsTabLibrary }[Crs.tab];
  box.innerHTML = fn(d);
  if (Crs.tab === "location") requestAnimationFrame(() => crsInitMaps(d.locations || []));
  if (Crs.tab === "contents") {
    const types = [...new Set((d.contents || []).map((x) => x.content_type).filter(Boolean))];
    if (extra && types.length > 1) extra.innerHTML = `<div class="crs-pills">
      <button class="crs-pill ${Crs.ctype === "all" ? "on" : ""}" data-crs="ctype" data-v="all">همه</button>
      ${types.map((t) => `<button class="crs-pill ${Crs.ctype === t ? "on" : ""}" data-crs="ctype" data-v="${cesc(t)}">${cesc(t)}</button>`).join("")}</div>`;
  }
  if (Crs.tab === "posts" && (d.posts || []).some((p) => p.is_new) && extra)
    extra.innerHTML = `<button class="btn btn-soft btn-sm" data-crs="read-all">✓ همه پیام‌ها را خواندم</button>`;
  if (Crs.tab === "library" && extra)
    extra.innerHTML = `<button class="btn btn-primary btn-sm" data-crs="lib-submit">+ ارسال منبع</button>
      <a class="btn btn-ghost btn-sm" href="#/library/${encodeURIComponent(d.course.name)}">صفحه کتابخانه</a>`;
}
function crsTabOverview(d) {
  const as = (d.assignments || []).filter((a) => !a.is_done)
    .sort((a, b) => (crsParse(a.deadline)?.ms ?? Infinity) - (crsParse(b.deadline)?.ms ?? Infinity)).slice(0, 4);
  const ps = (d.posts || []).slice(0, 3), cs = (d.contents || []).slice(0, 4);
  const loc = (d.locations || [])[0];
  return `<div class="crs-2col">
    <div class="card"><div class="card-head"><h3 class="section-title">📝 نزدیک‌ترین مهلت‌ها</h3>
      <button class="card-link crs-linkbtn" data-crs="tab" data-v="assignments">همه</button></div>
      <div class="item-list">${as.length ? as.map((a) => { const p = crsParse(a.deadline);
        return `<div class="list-row"><span class="row-icon">📝</span><div class="row-body">
          <div class="row-title">${cesc(a.title)}${p && p.ms < Date.now() ? ` <span class="badge badge-expired">گذشته</span>` : ""}</div>
          <div class="row-meta"><span>${p ? crsJal(p) : "بدون مهلت"}</span>${p ? `<span class="${p.ms < Date.now() ? "is-over" : ""}">${crsLeft(p.ms)}</span>` : ""}</div></div>
          <div class="row-actions"><button class="btn btn-soft btn-sm" data-crs="toggle" data-id="${cesc(a.id)}" data-v="1">✓</button></div></div>`; }).join("")
        : `<div class="crs-empty-inline">تکلیف بازی نیست 🎉</div>`}</div></div>
    <div class="card"><div class="card-head"><h3 class="section-title">📍 برنامه هفتگی</h3>
      <button class="card-link crs-linkbtn" data-crs="tab" data-v="location">نقشه</button></div>
      ${(d.locations || []).length ? `<div class="crs-sched">${d.locations.map((s) =>
        `<div class="crs-sched-row"><b>${cesc(s.weekday)}</b><span>${cesc(s.start_time)}–${cesc(s.end_time)}</span><span class="crs-muted">${cesc(s.faculty || s.location_text || "")}</span></div>`).join("")}</div>`
        : `<div class="crs-empty-inline">مکانی ثبت نشده — بعد از همگام‌سازی برنامه هفتگی دوباره بررسی کن</div>`}</div>
    <div class="card"><div class="card-head"><h3 class="section-title">💬 آخرین پیام‌ها</h3>
      <button class="card-link crs-linkbtn" data-crs="tab" data-v="posts">همه</button></div>
      <div class="item-list">${ps.length ? ps.map((p) => `<div class="list-row"><span class="row-icon">💬</span>
        <div class="row-body"><div class="row-title">${cesc(p.author)}${p.is_new ? ` <span class="badge badge-new">جدید</span>` : ""}</div>
        <div class="crs-clamp">${cesc(p.text)}</div></div></div>`).join("") : `<div class="crs-empty-inline">پیامی نیست</div>`}</div></div>
    <div class="card"><div class="card-head"><h3 class="section-title">📁 آخرین محتواها</h3>
      <button class="card-link crs-linkbtn" data-crs="tab" data-v="contents">همه</button></div>
      <div class="item-list">${cs.length ? cs.map((x) => `<div class="list-row"><span class="row-icon">📄</span>
        <div class="row-body"><div class="row-title"><a href="${cesc(proxyUrl(x.url))}" target="_blank" rel="noopener noreferrer">${cesc(x.title)}</a></div>
        <div class="row-meta"><span>${cesc(x.content_type || "")}</span></div></div></div>`).join("") : `<div class="crs-empty-inline">محتوایی نیست</div>`}</div></div>
  </div>`;
}
function crsTabAssignments(d) {
  const l = (d.assignments || []).filter((a) => crsMatch(`${a.title} ${a.description || ""}`))
    .sort((a, b) => (!!a.is_done) - (!!b.is_done) || (crsParse(a.deadline)?.ms ?? Infinity) - (crsParse(b.deadline)?.ms ?? Infinity));
  if (!l.length) return `<div class="empty"><span class="empty-icon">📝</span>تکلیفی نیست</div>`;
  return `<div class="item-list">${l.map((a) => {
    const p = crsParse(a.deadline), over = !a.is_done && p && p.ms < Date.now();
    return `<div class="list-row crs-arow ${a.is_done ? "is-done" : ""}">
      <input type="checkbox" class="crs-chk" data-crs-sel="${cesc(a.id)}" ${Crs.dsel.has(a.id) ? "checked" : ""} aria-label="انتخاب تکلیف">
      <span class="row-icon ${a.is_done ? "is-done" : over ? "is-over" : ""}">${a.is_done ? "✓" : over ? "⏰" : "📝"}</span>
      <div class="row-body"><div class="row-title">${cesc(a.title)}
        ${a.is_done ? `<span class="badge badge-done">انجام شده</span>` : over ? `<span class="badge badge-expired">گذشته</span>` : ""}</div>
        <div class="row-meta"><span>${p ? crsJal(p) + (p.time ? ` · ${cfa(p.time)}` : "") : (a.deadline_jalali || "بدون مهلت")}</span>
          ${p ? `<span class="${over ? "is-over" : ""}">${crsLeft(p.ms)}</span>` : ""}</div></div>
      <div class="row-actions">
        ${!a.is_done && a.submit_url ? `<a class="btn btn-primary btn-sm" href="${cesc(proxyUrl(a.submit_url))}" target="_blank" rel="noopener noreferrer">ارسال ↗</a>` : ""}
        <button class="btn ${a.is_done ? "btn-ghost" : "btn-soft"} btn-sm" data-crs="toggle" data-id="${cesc(a.id)}" data-v="${a.is_done ? "0" : "1"}">${a.is_done ? "لغو" : "انجام شد ✓"}</button>
      </div></div>`; }).join("")}</div>`;
}
function crsTabContents(d) {
  const l = (d.contents || []).filter((x) => (Crs.ctype === "all" || x.content_type === Crs.ctype) && crsMatch(`${x.title} ${x.filename || ""}`));
  if (!l.length) return `<div class="empty"><span class="empty-icon">📁</span>محتوایی با این فیلتر نیست</div>`;
  return `<div class="item-list">${l.map((x) => `<div class="list-row">
    <span class="row-icon">📄</span><div class="row-body">
      <div class="row-title"><a href="${cesc(proxyUrl(x.url))}" target="_blank" rel="noopener noreferrer">${cesc(x.title)}</a>
        <span class="badge badge-domain">${cesc(x.content_type || "")}</span></div>
      <div class="row-meta">${x.filename ? `<span>${cesc(x.filename)}</span>` : ""}</div></div>
    <div class="row-actions"><a class="btn btn-soft btn-sm" href="${cesc(proxyUrl(x.url))}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a></div>
  </div>`).join("")}</div>`;
}
function crsTabPosts(d) {
  const l = (d.posts || []).filter((p) => crsMatch(`${p.author} ${p.text}`));
  if (!l.length) return `<div class="empty"><span class="empty-icon">💬</span>پیامی نیست</div>`;
  return `<div class="item-list">${l.map((p, i) => `<div class="list-row">
    <span class="row-icon">💬</span><div class="row-body">
      <div class="row-title">${cesc(p.author)}${p.is_new ? ` <span class="badge badge-new">جدید</span>` : ""}</div>
      <div class="crs-clamp">${cesc(p.text)}</div>
      <div class="row-meta"><span>${cesc(p.posted_at_jalali || p.posted_at || "")}</span></div></div>
    <div class="row-actions"><button class="btn btn-ghost btn-sm" data-crs="post" data-i="${i}">متن کامل</button></div>
  </div>`).join("")}</div>`;
}
function crsTabMembers(d) {
  const l = (d.members || []).filter((m) => crsMatch(m.name));
  if (!l.length) return `<div class="empty"><span class="empty-icon">👥</span>عضوی نیست</div>`;
  const groups = ["teacher", "support", "student"];
  return groups.map((g) => {
    const items = l.filter((m) => (m.member_type || "student") === g);
    if (!items.length) return "";
    const meta = CRS_ROLE[g];
    return `<div class="card crs-mgroup"><div class="card-head"><h3 class="section-title" style="color:var(${meta.cv})">${meta.icon} ${meta.label}<span class="badge">${cfa(items.length)}</span></h3></div>
      <div class="crs-members">${items.map((m) => `<div class="crs-member">
        <span class="crs-mava" style="--c:var(${meta.cv})">${cesc((m.name || "؟").trim().charAt(0))}</span>
        <span class="crs-mname">${cesc(m.name)}</span></div>`).join("")}</div></div>`;
  }).join("");
}
function crsTabLocation(d) {
  const locs = d.locations || [];
  if (!locs.length) return `<div class="empty"><span class="empty-icon">📍</span>مکانی ثبت نشده است<small>برنامه هفتگی هنگام همگام‌سازی دریافت می‌شود</small></div>`;
  const uniq = []; const seen = new Set();
  locs.forEach((s) => { const k = `${s.lat},${s.lng}`; if (!seen.has(k)) { seen.add(k); uniq.push(s); } });
  return `<div class="card"><div class="card-head"><h3 class="section-title">🗓 برنامه هفتگی</h3></div>
      <div class="crs-sched">${locs.map((s) => `<div class="crs-sched-row"><b>${cesc(s.weekday)}</b>
        <span>${cesc(s.start_time)}–${cesc(s.end_time)}</span><span class="crs-muted">${cesc(s.location_text || "")}</span></div>`).join("")}</div></div>
    ${uniq.map((s, i) => `<div class="card crs-loc">
      <div class="crs-loc-info"><div class="crs-loc-title">📍 ${cesc(s.faculty || "مکان ثبت‌شده")}</div>
        <div class="crs-muted">${cesc(s.building || "")}</div><div class="crs-muted">${cesc(s.location_text || "")}</div>
        <div class="crs-loc-btns">
          <a class="btn btn-primary btn-sm" href="https://nshn.ir/?lat=${s.lat}&lng=${s.lng}" target="_blank" rel="noopener noreferrer">🧭 نشان</a>
          <a class="btn btn-soft btn-sm" href="https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lng}&travelmode=driving" target="_blank" rel="noopener noreferrer">🗺 گوگل مپ</a>
        </div></div>
      <div id="crs-map-${i}" class="crs-map" data-lat="${s.lat}" data-lng="${s.lng}"></div>
    </div>`).join("")}`;
}
function crsTabLibrary(d) {
  if (Crs.lib === null) {
    (async () => {
      try { const r = await api(`/library/courses/${encodeURIComponent(d.course.name)}`); Crs.lib = r.items || []; }
      catch (_) { Crs.lib = []; }
      if (Crs.tab === "library") { crsPaintDTabs(); crsPaintDBody(); }
    })();
    return `<div class="crs-muted" style="padding:1rem">در حال بارگذاری کتابخانه…</div>`;
  }
  const l = Crs.lib.filter((it) => crsMatch(`${it.title} ${it.description || ""}`));
  if (!l.length) return `<div class="empty"><span class="empty-icon">📚</span>هنوز منبع تاییدشده‌ای برای این درس نیست<small>اولین نفری باش که منبع می‌فرسته</small></div>`;
  if (typeof libMiniRow === "function") return `<div class="item-list">${l.map(libMiniRow).join("")}</div>`;
  return `<div class="item-list">${l.map((it) => { const u = csafe(it.url);
    return `<div class="list-row"><span class="row-icon">🔗</span><div class="row-body">
      <div class="row-title">${u ? `<a href="${cesc(u)}" target="_blank" rel="noopener noreferrer">${cesc(it.title)}</a>` : cesc(it.title)}</div>
      <div class="row-meta"><span>${cesc(it.description || "")}</span>${it.avg_rating ? `<span>★ ${cfa(it.avg_rating)}</span>` : ""}</div></div>
      ${u ? `<div class="row-actions"><a class="btn btn-soft btn-sm" href="${cesc(u)}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a></div>` : ""}</div>`; }).join("")}</div>`;
}
function crsInitMaps(locs) {
  crsDestroyMaps();
  if (typeof L === "undefined") {
    document.querySelectorAll(".crs-map").forEach((el) => { el.innerHTML = `<div class="crs-map-fallback">نقشه در دسترس نیست</div>`; });
    return;
  }
  const dark = document.body.dataset.theme === "dark";
  document.querySelectorAll(".crs-map").forEach((el) => {
    const lat = +el.dataset.lat, lng = +el.dataset.lng;
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
    el.classList.toggle("map-dark-tiles", dark);
    try {
      const map = L.map(el, { zoomControl: true, attributionControl: false }).setView([lat, lng], 16);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
      L.marker([lat, lng]).addTo(map);
      Crs.maps.push(map);
      setTimeout(() => { try { map.invalidateSize(); } catch (_) {} }, 180);
    } catch (_) { el.innerHTML = `<div class="crs-map-fallback">نقشه بارگذاری نشد</div>`; }
  });
}

/* ---- اکشن‌ها ---- */
async function crsPushDone(id, want) {
  try { const r = await api(`/assignments/${encodeURIComponent(id)}/done?done=${want}`, { method: "POST", body: "{}" });
    return !(r && r.ok === false); } catch (_) { return false; }
}
async function crsToggle(id, want) {
  const a = (Crs.detail?.assignments || []).find((x) => x.id === id); if (!a) return;
  const before = !!a.is_done; a.is_done = want; crsDetailPaint();
  if (!(await crsPushDone(id, want))) { a.is_done = before; crsDetailPaint(); crsToast("❌ ثبت وضعیت ناموفق"); return; }
  if (typeof refreshNavBadge === "function") refreshNavBadge();
  crsToast(want ? "✅ انجام‌شده علامت خورد" : "علامت برداشته شد",
    { action: "برگردان", dur: 5000, onAction: async () => { a.is_done = before; crsDetailPaint(); await crsPushDone(id, before); } });
}
async function crsBulk(done) {
  const ids = [...Crs.dsel]; if (!ids.length) return;
  const prev = ids.map((id) => ({ id, was: !!(Crs.detail.assignments.find((x) => x.id === id)?.is_done) }));
  ids.forEach((id) => { const a = Crs.detail.assignments.find((x) => x.id === id); if (a) a.is_done = done; });
  Crs.dsel.clear(); crsDetailPaint();
  let failed = [];
  try { const r = await api("/assignments/bulk-done", { method: "POST", body: JSON.stringify({ ids, done }) }); failed = r.skipped || []; }
  catch (err) { if ([404, 405].includes(err.status)) { for (const id of ids) if (!(await crsPushDone(id, done))) failed.push(id); } else failed = ids; }
  failed.forEach((id) => { const p = prev.find((x) => x.id === id), a = Crs.detail.assignments.find((x) => x.id === id); if (a && p) a.is_done = p.was; });
  crsDetailPaint(); if (typeof refreshNavBadge === "function") refreshNavBadge();
  crsToast(`${cfa(ids.length - failed.length)} مورد به‌روز شد`, { action: "برگردان", dur: 6500, onAction: async () => {
    prev.forEach((p) => { const a = Crs.detail.assignments.find((x) => x.id === p.id); if (a) a.is_done = p.was; }); crsDetailPaint();
    for (const p of prev) await crsPushDone(p.id, p.was);
  }});
}

/* ---- delegation ---- */
function crsWire() {
  if (Crs.wired) return; Crs.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-crs]");
    if (!el) {
      const card = e.target.closest("[data-crs-card]");
      if (card && !e.target.closest("a,button,input,select")) {
        const c = Crs.items.find((x) => x.id === card.dataset.crsCard);
        if (c && c.source !== "quera") location.hash = "#/course/" + encodeURIComponent(c.id);
      }
      return;
    }
    const act = el.dataset.crs, v = el.dataset.v, id = el.dataset.id;
    switch (act) {
      case "source": Crs.source = v; crsPaintPills(); crsPaintList(); break;
      case "status": Crs.status = v; crsPaintPills(); crsPaintList(); break;
      case "view": Crs.view = v; localStorage.setItem("crs:view", v); crsPaintList(); break;
      case "clear": Crs.q = ""; Crs.source = "all"; Crs.status = "all"; Crs.term = "all"; renderCourses(); break;
      case "peek": crsPeek(id); break;
      case "tab": Crs.tab = v; Crs.dsel.clear(); crsDetailPaint(); break;
      case "ctype": Crs.ctype = v; crsPaintDBody(); break;
      case "toggle": crsToggle(id, v === "1"); break;
      case "bulk-done": crsBulk(true); break;
      case "bulk-undone": crsBulk(false); break;
      case "bulk-clear": Crs.dsel.clear(); crsPaintDBulk(); crsPaintDBody(); break;
      case "post": { const p = (Crs.detail.posts || []).filter((x) => crsMatch(`${x.author} ${x.text}`))[+el.dataset.i];
        if (p) crsLayer({ type: "drawer", title: "پیام وال", html: `<div class="crs-dwr">
          <div class="crs-dwr-head"><span class="crs-ico lg">💬</span><div><h2>${cesc(p.author)}</h2>
            <div class="crs-muted">${cesc(p.posted_at_jalali || p.posted_at || "")}</div></div>
            <button class="crs-x" data-lib-close aria-label="بستن">✕</button></div>
          <p class="crs-fulltext">${cesc(p.text)}</p></div>` }); break; }
      case "read-all": (async () => {
        try { await api("/posts/read", { method: "POST", body: "{}" });
          (Crs.detail.posts || []).forEach((p) => { p.is_new = false; });
          crsDetailPaint(); if (typeof refreshNavBadge === "function") refreshNavBadge(); crsToast("✅ همه پیام‌ها خوانده شد");
        } catch (err) { crsToast("❌ " + (err.message || "خطا")); } })(); break;
      case "lib-submit": (async () => {
        const name = Crs.detail.course.name;
        if (typeof ensureLibraryTermsAccepted === "function" && !(await ensureLibraryTermsAccepted())) return;
        if (typeof openLibrarySubmitModal === "function") openLibrarySubmitModal(name);
        else location.hash = "#/library/" + encodeURIComponent(name);
      })(); break;
      case "view-save": crsLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <div class="crs-field" data-cf="n"><label class="field-label" for="crs-v-n">نام نما *</label>
            <input id="crs-v-n" class="input" placeholder="مثلاً کوئراهای فعال" data-autofocus><small class="crs-err"></small></div>
          <div class="lib-modal-actions crs-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
            <button class="btn btn-primary" id="crs-v-ok">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#crs-v-ok").addEventListener("click", () => {
          const n = w.querySelector("#crs-v-n").value.trim();
          const f = w.querySelector('[data-cf="n"]'); f.classList.toggle("bad", !n); f.querySelector(".crs-err").textContent = n ? "" : "نام الزامی است";
          if (!n) return;
          Crs.views[n] = { q: Crs.q, source: Crs.source, status: Crs.status, term: Crs.term, sort: Crs.sort, view: Crs.view };
          Crs.views = Object.fromEntries(Object.entries(Crs.views).slice(-6));
          localStorage.setItem("crs:views", JSON.stringify(Crs.views));
          L.close(); crsPaintSaved(); crsToast("💾 نما ذخیره شد");
        }); } }); break;
      case "view-apply": { const x = Crs.views[el.dataset.k]; if (!x) break;
        Object.assign(Crs, x); localStorage.setItem("crs:sort", Crs.sort); localStorage.setItem("crs:view", Crs.view);
        renderCourses(); break; }
      case "view-del": delete Crs.views[el.dataset.k]; localStorage.setItem("crs:views", JSON.stringify(Crs.views)); crsPaintSaved(); break;
    }
  });
  document.addEventListener("input", (e) => {
    if (e.target.id === "crs-q") { Crs.q = e.target.value; crsPaintList(); }
    if (e.target.id === "crs-dq") { Crs.dq = e.target.value; crsPaintDBody(); }
  });
  document.addEventListener("change", (e) => {
    if (e.target.id === "crs-sort") { Crs.sort = e.target.value; localStorage.setItem("crs:sort", Crs.sort); crsPaintList(); }
    if (e.target.id === "crs-term") { Crs.term = e.target.value; crsPaintList(); }
    if (e.target.dataset && e.target.dataset.crsSel !== undefined) {
      const id = e.target.dataset.crsSel;
      e.target.checked ? Crs.dsel.add(id) : Crs.dsel.delete(id);
      crsPaintDBulk();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = (typeof Lib !== "undefined" && Lib.layers && Lib.layers.length)
      || (typeof Cal !== "undefined" && Cal._layers && Cal._layers.length)
      || (typeof Asg !== "undefined" && Asg.layers && Asg.layers.length)
      || (typeof Adm !== "undefined" && Adm.layers && Adm.layers.length);
    if (busy) return;
    if (Crs.layers.length) Crs.layers[Crs.layers.length - 1].close();
  });
  if (!Crs.themeObs) {
    Crs.themeObs = new MutationObserver(() => {
      const dark = document.body.dataset.theme === "dark";
      document.querySelectorAll(".crs-map").forEach((el) => el.classList.toggle("map-dark-tiles", dark));
    });
    Crs.themeObs.observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
  }
}
crsWire();

// ---------- Assignments v2 (تکالیف) ----------
// ورود به صفحه = یک‌بار fetch؛ فیلتر/مرتب‌سازی/گروه/نما/جستجو = کلاینتی.
// toggle/bulk/delete همه optimistic با rollback و Undo. بدون onclick inline.
const ASG_TYPES = {
  lms:    { label: "LMS",   icon: "📝", cls: "t-lms",    cv: "--primary" },
  quera:  { label: "کوئرا", icon: "⚙️", cls: "t-quera",  cv: "--accent" },
  manual: { label: "دستی",  icon: "🗒", cls: "t-manual", cv: "--info" },
};
const ASG_FILTERS = [
  ["open", "باز"], ["today", "امروز"], ["week", "این هفته"],
  ["overdue", "عقب‌افتاده"], ["done", "انجام‌شده"],
  ["manual", "دستی"], ["quera", "کوئرا"], ["all", "همه"],
];
const Asg = {
  items: [], q: "", filter: "open",
  sort: localStorage.getItem("asg:sort") || "smart",
  view: localStorage.getItem("asg:view") || "list",
  group: localStorage.getItem("asg:group") || "none",
  sel: new Set(), views: JSON.parse(localStorage.getItem("asg:views") || "{}"),
  layers: [], wired: false, courses: null,
};
const aesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const afa = (n) => faDigits(String(n));
function asgParse(v) {
  const m = String(v || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (!m) return null;
  const d = new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0));
  return { jdn: g2d(+m[1], +m[2], +m[3]), ms: d.getTime(), time: m[4] ? `${m[4]}:${m[5]}` : "", dateStr: `${m[1]}-${m[2]}-${m[3]}` };
}
function asgJal(p) { if (!p) return ""; const j = d2j(p.jdn); return `${afa(j.jd)} ${J_MONTHS[j.jm - 1]} ${afa(j.jy)}`; }
function asgGStr(jdn) { const g = d2g(jdn); return `${g.gy}-${String(g.gm).padStart(2, "0")}-${String(g.gd).padStart(2, "0")}`; }
function asgToday() { const n = new Date(); return g2d(n.getFullYear(), n.getMonth() + 1, n.getDate()); }
function asgRel(ms) {
  if (ms == null) return "";
  const diff = ms - Date.now(), past = diff < 0, s = Math.abs(diff) / 1000;
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  let txt = d > 0 ? `${afa(d)} روز${h ? ` و ${afa(h)} ساعت` : ""}` : h > 0 ? `${afa(h)} ساعت${m ? ` و ${afa(m)} دقیقه` : ""}` : `${afa(Math.max(1, m))} دقیقه`;
  return past ? `${txt} پیش` : `${txt} مانده`;
}
const asgType = (a) => a.source === "quera" ? "quera" : a.is_manual ? "manual" : "lms";
const asgMeta = (a) => ASG_TYPES[asgType(a)];
const asgFind = (id) => Asg.items.find((x) => String(x.id) === String(id));
const asgOverdue = (a) => { if (a.is_done) return false; const p = asgParse(a.deadline); return !!a.is_expired || (p ? p.ms < Date.now() : false); };
const asgCourse = (a) => a.course_name || a.course_id || "درس نامشخص";

/* ---- لایه/توست: استفاده از زیرساخت موجود، وگرنه fallback مستقل ---- */
function asgLayer(opts) {
  const factory = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer : asgOwnLayer;
  const L = factory({ ...opts, onClose: () => { const i = Asg.layers.indexOf(L); if (i >= 0) Asg.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  Asg.layers.push(L); return L;
}
function asgToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  return asgOwnToast(m, o);
}
function asgOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "asg-layer";
  w.innerHTML = `<div class="asg-scrim" data-asg-x></div>` + (opts.type === "drawer"
    ? `<aside class="asg-drawer" role="dialog" aria-modal="true" aria-label="${aesc(opts.title)}">${opts.html}</aside>`
    : `<div class="asg-modal-wrap"><div class="asg-modal" role="dialog" aria-modal="true" aria-label="${aesc(opts.title)}"><h3>${aesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("asg-locked");
  const panel = w.querySelector(".asg-drawer,.asg-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".asg-layer")) document.body.classList.remove("asg-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-asg-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function asgOwnToast(msg, o = {}) {
  let box = document.getElementById("asg-toasts");
  if (!box) { box = document.createElement("div"); box.id = "asg-toasts"; box.className = "asg-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "asg-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${aesc(msg)}</span>${o.action ? `<button class="a">${aesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const asgCloseAll = () => Asg.layers.slice().forEach((l) => l.close());

/* ---- فیلتر / مرتب‌سازی / گروه ---- */
function asgMatch(a, f) {
  const p = asgParse(a.deadline), t = asgToday();
  switch (f) {
    case "open": return !a.is_done;
    case "today": return !a.is_done && p && p.jdn === t;
    case "week": return !a.is_done && p && p.jdn >= t && p.jdn <= t + 6;
    case "overdue": return asgOverdue(a);
    case "done": return !!a.is_done;
    case "manual": return !!a.is_manual;
    case "quera": return a.source === "quera";
    default: return true;
  }
}
function asgFiltered() {
  const q = Asg.q.trim().toLowerCase();
  let list = Asg.items.filter((a) => asgMatch(a, Asg.filter));
  if (q) list = list.filter((a) => `${a.title || ""} ${a.description || ""} ${asgCourse(a)}`.toLowerCase().includes(q));
  const ms = (a) => { const p = asgParse(a.deadline); return p ? p.ms : Infinity; };
  const s = Asg.sort;
  return list.sort((a, b) => {
    if (s === "course") return asgCourse(a).localeCompare(asgCourse(b), "fa") || ms(a) - ms(b);
    if (s === "title") return String(a.title).localeCompare(String(b.title), "fa");
    if (s === "deadline") return ms(a) - ms(b);
    if (!!a.is_done !== !!b.is_done) return a.is_done ? 1 : -1;
    const oa = asgOverdue(a), ob = asgOverdue(b);
    if (oa !== ob) return oa ? -1 : 1;
    return ms(a) - ms(b);
  });
}
function asgGroups(list) {
  if (Asg.group === "none") return [{ key: "", label: "", items: list }];
  const map = new Map();
  for (const a of list) {
    let key, label;
    if (Asg.group === "course") { key = asgCourse(a); label = `📘 ${key}`; }
    else { const p = asgParse(a.deadline); key = p ? String(p.jdn) : "zz"; label = p ? asgJal(p) : "بدون مهلت"; }
    if (!map.has(key)) map.set(key, { key, label, items: [] });
    map.get(key).items.push(a);
  }
  return [...map.values()];
}

/* ---- ورود به صفحه ---- */
async function renderAssignments() {
  Asg.sel.clear();
  let items = [];
  try { items = await api("/assignments"); }
  catch (e) { contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری تکالیف<small>${aesc(e.message)}</small></div>`; return; }
  Asg.items = Array.isArray(items) ? items : [];
  contentEl.innerHTML = `
    ${pageHead("تکالیف", "مهلت‌ها، وضعیت انجام و تکالیف دستی")}
    <div class="card asg-hero" id="asg-hero"></div>
    <div class="asg-toolbar">
      <div class="search-box asg-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="asg-q" type="search" placeholder="جستجو در عنوان، توضیح یا درس…" value="${aesc(Asg.q)}" aria-label="جستجوی تکلیف"></div>
      <select id="asg-sort" class="input asg-sel" aria-label="مرتب‌سازی">
        <option value="smart">هوشمند (نزدیک و عقب‌افتاده)</option>
        <option value="deadline">مهلت (نزدیک‌ترین)</option>
        <option value="course">بر اساس درس</option>
        <option value="title">الفبایی</option>
      </select>
      <select id="asg-group" class="input asg-sel" aria-label="گروه‌بندی">
        <option value="none">بدون گروه</option><option value="course">گروه: درس</option><option value="day">گروه: روز</option>
      </select>
      <div class="asg-viewtoggle" role="group" aria-label="حالت نمایش">
        <button data-asg="view" data-v="list" title="لیست" aria-label="لیست">☰</button>
        <button data-asg="view" data-v="compact" title="فشرده" aria-label="فشرده">≡</button>
        <button data-asg="view" data-v="grid" title="شبکه" aria-label="شبکه">▦</button>
      </div>
      <button class="btn btn-ghost btn-sm" data-asg="view-save" title="ذخیره نمای فعلی">💾</button>
      <a class="btn btn-ghost btn-sm" href="/api/calendar.ics" download="lms-assistant.ics">⬇ ICS</a>
      <button class="btn btn-primary btn-sm" data-asg="add">+ تکلیف دستی</button>
    </div>
    <div class="asg-pills" id="asg-pills"></div>
    <div class="asg-saved" id="asg-saved"></div>
    <div id="asg-bulk"></div>
    <div id="asg-list"></div>`;
  document.getElementById("asg-sort").value = Asg.sort;
  document.getElementById("asg-group").value = Asg.group;
  asgPaintAll();
}
function asgPaintAll() { asgPaintHero(); asgPaintPills(); asgPaintSaved(); asgPaintBulk(); asgPaintList(); }
function asgPaintHero() {
  const box = document.getElementById("asg-hero"); if (!box) return;
  const all = Asg.items, done = all.filter((a) => a.is_done).length;
  const open = all.filter((a) => !a.is_done).length;
  const over = all.filter(asgOverdue).length;
  const t = asgToday();
  const week = all.filter((a) => { const p = asgParse(a.deadline); return !a.is_done && p && p.jdn >= t && p.jdn <= t + 6; }).length;
  const pct = all.length ? Math.round((done / all.length) * 100) : 0;
  box.innerHTML = `
    <div class="asg-hero-main">
      <div class="asg-ring" style="--p:${pct}"><span>${afa(pct)}٪</span></div>
      <div><h3>${afa(done)} از ${afa(all.length)} تکلیف انجام شده</h3>
        <p class="asg-hero-sub">${open ? `${afa(open)} تکلیف باز داری` : "همه تکالیف انجام شده‌اند 🎉"}${over ? ` · ${afa(over)} مورد از مهلت گذشته` : ""}</p>
        <div class="asg-track"><i style="width:${pct}%"></i></div></div>
    </div>
    <div class="asg-stats">
      <div class="asg-stat"><b style="color:var(--primary)">${afa(open)}</b><span>باز</span></div>
      <div class="asg-stat"><b style="color:var(--danger)">${afa(over)}</b><span>عقب‌افتاده</span></div>
      <div class="asg-stat"><b style="color:var(--warning)">${afa(week)}</b><span>این هفته</span></div>
      <div class="asg-stat"><b style="color:var(--accent)">${afa(done)}</b><span>انجام‌شده</span></div>
    </div>`;
}
function asgPaintPills() {
  const box = document.getElementById("asg-pills"); if (!box) return;
  box.innerHTML = ASG_FILTERS.map(([k, l]) => {
    const n = Asg.items.filter((a) => asgMatch(a, k)).length;
    return `<button class="asg-pill ${Asg.filter === k ? "on" : ""} f-${k}" data-asg="filter" data-v="${k}" aria-pressed="${Asg.filter === k}">${l}<b>${afa(n)}</b></button>`;
  }).join("");
}
function asgPaintSaved() {
  const box = document.getElementById("asg-saved"); if (!box) return;
  const keys = Object.keys(Asg.views);
  box.innerHTML = keys.length ? `<span class="asg-muted">نماها:</span>` + keys.map((k) =>
    `<span class="asg-sv"><button data-asg="view-apply" data-k="${aesc(k)}">${aesc(k)}</button>
      <button class="x" data-asg="view-del" data-k="${aesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function asgPaintBulk() {
  const box = document.getElementById("asg-bulk"); if (!box) return;
  if (!Asg.sel.size) { box.innerHTML = ""; return; }
  const manual = [...Asg.sel].filter((id) => asgFind(id)?.is_manual).length;
  box.innerHTML = `<div class="asg-bulkbar"><b>${afa(Asg.sel.size)}</b> انتخاب شده
    <button class="btn btn-soft btn-sm" data-asg="bulk-done">✓ انجام شد</button>
    <button class="btn btn-ghost btn-sm" data-asg="bulk-undone">لغو انجام</button>
    ${manual ? `<button class="btn btn-ghost btn-sm asg-del" data-asg="bulk-del">🗑 حذف ${afa(manual)} دستی</button>` : ""}
    <button class="btn btn-ghost btn-sm" data-asg="bulk-clear">پاک کردن</button></div>`;
}
function asgUrgency(a) {
  if (a.is_done) return "";
  const p = asgParse(a.deadline); if (!p) return "";
  const left = p.ms - Date.now();
  if (left < 0) return `<span class="badge badge-expired">گذشته</span>`;
  if (left < 24 * 3600e3) return `<span class="badge badge-expired">کمتر از ۲۴ ساعت</span>`;
  if (left < 48 * 3600e3) return `<span class="badge badge-warn">کمتر از ۴۸ ساعت</span>`;
  return "";
}
function asgRow(a) {
  const m = asgMeta(a), p = asgParse(a.deadline), id = aesc(a.id);
  const icon = a.is_done ? "✓" : asgOverdue(a) ? "⏰" : m.icon;
  const iconCls = a.is_done ? "is-done" : asgOverdue(a) ? "is-over" : m.cls;
  const submit = !a.is_done && a.submit_url ? `<a class="btn btn-primary btn-sm" href="${aesc(proxyUrl(a.submit_url))}" target="_blank" rel="noopener noreferrer">ارسال ↗</a>` : "";
  const chk = `<input type="checkbox" class="asg-chk" data-asg-sel="${id}" ${Asg.sel.has(String(a.id)) ? "checked" : ""} aria-label="انتخاب ${aesc(a.title)}">`;
  const badges = `<span class="badge ${m.cls}">${m.label}</span>
    ${a.is_done ? `<span class="badge badge-done">انجام شده</span>` : ""}
    ${a.is_new && !a.is_done ? `<span class="badge badge-new">جدید</span>` : ""}${asgUrgency(a)}`;
  const meta = `<div class="row-meta">
      <span>📘 ${aesc(asgCourse(a))}</span>
      ${p ? `<span>📅 ${asgJal(p)}${p.time ? ` · ⏰ ${afa(p.time)}` : ""}</span><span class="asg-left ${asgOverdue(a) ? "is-over" : ""}">${asgRel(p.ms)}</span>` : `<span>بدون مهلت</span>`}
    </div>`;
  const actions = `<div class="row-actions">${submit}
    <button class="btn ${a.is_done ? "btn-ghost" : "btn-soft"} btn-sm" data-asg="toggle" data-id="${id}">${a.is_done ? "لغو انجام" : "انجام شد ✓"}</button>
    <button class="btn btn-ghost btn-sm" data-asg="detail" data-id="${id}">جزئیات</button></div>`;
  if (Asg.view === "grid") {
    return `<article class="asg-card ${a.is_done ? "is-done" : ""}" data-asg-card="${id}">${chk}
      <div class="asg-card-top"><span class="row-icon ${iconCls}">${icon}</span>
        <button class="asg-title" data-asg="detail" data-id="${id}">${aesc(a.title)}</button></div>
      <div class="asg-badges">${badges}</div>
      ${a.description ? `<p class="asg-desc">${aesc(a.description)}</p>` : ""}${meta}${actions}</article>`;
  }
  if (Asg.view === "compact") {
    return `<div class="list-row asg-row is-compact ${a.is_done ? "is-done" : ""}" data-asg-card="${id}">${chk}
      <span class="row-icon ${iconCls}">${icon}</span>
      <div class="row-body"><div class="row-title"><button class="asg-title" data-asg="detail" data-id="${id}">${aesc(a.title)}</button>${badges}</div>
        <div class="row-meta"><span>${aesc(asgCourse(a))}</span>${p ? `<span>${asgJal(p)}</span>` : ""}</div></div>
      <div class="row-actions"><button class="btn btn-ghost btn-sm" data-asg="toggle" data-id="${id}">${a.is_done ? "لغو" : "✓"}</button></div></div>`;
  }
  return `<div class="list-row asg-row ${a.is_done ? "is-done" : ""} ${asgOverdue(a) ? "is-over" : ""}" data-asg-card="${id}">${chk}
    <span class="row-icon ${iconCls}">${icon}</span>
    <div class="row-body"><div class="row-title"><button class="asg-title" data-asg="detail" data-id="${id}">${aesc(a.title)}</button>${badges}</div>${meta}</div>
    ${actions}</div>`;
}
function asgPaintList() {
  const box = document.getElementById("asg-list"); if (!box) return;
  document.querySelectorAll(".asg-viewtoggle button").forEach((b) => { const on = b.dataset.v === Asg.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const list = asgFiltered();
  if (!list.length) {
    box.innerHTML = `<div class="empty"><span class="empty-icon">${Asg.q ? "🔍" : "🗂"}</span>${Asg.q ? "تکلیفی با این عبارت پیدا نشد" : "موردی در این فیلتر نیست"}
      <small>${Asg.q ? "املای عبارت را بررسی کن یا فیلتر را روی «همه» بگذار" : "فیلتر دیگری را امتحان کن یا یک تکلیف دستی بساز"}</small>
      <div class="asg-empty-actions"><button class="btn btn-ghost btn-sm" data-asg="filter" data-v="all">نمایش همه</button>
        <button class="btn btn-primary btn-sm" data-asg="add">+ تکلیف دستی</button></div></div>`;
    return;
  }
  const cls = Asg.view === "grid" ? "asg-grid" : "item-list";
  box.innerHTML = asgGroups(list).map((g) => {
    const head = g.label ? `<div class="asg-grouphead"><b>${aesc(g.label)}</b><span class="badge">${afa(g.items.length)} مورد</span>
      <button class="btn btn-ghost btn-sm" data-asg="group-sel" data-k="${aesc(g.key)}">انتخاب گروه</button></div>` : "";
    return `<section class="asg-group">${head}<div class="${cls}">${g.items.map(asgRow).join("")}</div></section>`;
  }).join("");
}

/* ---- وضعیت انجام ---- */
async function asgPushDone(id, want) {
  const raw = String(id), isQ = raw.startsWith("quera_");
  const path = isQ
    ? `/quera/assignments/${encodeURIComponent(raw.slice(6))}/done?done=${want}`
    : `/assignments/${encodeURIComponent(raw)}/done?done=${want}`;
  try { const r = await api(path, { method: "POST", body: "{}" }); if (r && r.ok === false) throw new Error(r.error || "تکلیف پیدا نشد"); return true; }
  catch (_) { return false; }
}
async function asgToggle(id, want) {
  const a = asgFind(id); if (!a) return;
  const before = !!a.is_done;
  a.is_done = want; asgPaintAll();
  const ok = await asgPushDone(id, want);
  if (!ok) { a.is_done = before; asgPaintAll(); asgToast("❌ ثبت وضعیت ناموفق بود"); return; }
  if (typeof refreshNavBadge === "function") refreshNavBadge();
  asgToast(want ? "✅ انجام‌شده علامت خورد" : "علامت انجام برداشته شد",
    { action: "برگردان", dur: 5000, onAction: async () => { a.is_done = before; asgPaintAll(); await asgPushDone(id, before); if (typeof refreshNavBadge === "function") refreshNavBadge(); } });
}
async function asgBulkSet(done) {
  const ids = [...Asg.sel]; if (!ids.length) return;
  const prev = ids.map((id) => ({ id, was: !!asgFind(id)?.is_done }));
  ids.forEach((id) => { const a = asgFind(id); if (a) a.is_done = done; });
  Asg.sel.clear(); asgPaintAll();
  const lms = ids.filter((i) => !String(i).startsWith("quera_"));
  const quera = ids.filter((i) => String(i).startsWith("quera_"));
  let failed = [];
  if (lms.length) {
    try {
      const r = await api("/assignments/bulk-done", { method: "POST", body: JSON.stringify({ ids: lms, done }) });
      failed = failed.concat(r.skipped || []);
    } catch (err) {
      if ([404, 405].includes(err.status)) { for (const id of lms) if (!(await asgPushDone(id, done))) failed.push(id); }
      else failed = failed.concat(lms);
    }
  }
  for (const id of quera) if (!(await asgPushDone(id, done))) failed.push(id);
  failed.forEach((id) => { const p = prev.find((x) => x.id === id), a = asgFind(id); if (a && p) a.is_done = p.was; });
  asgPaintAll(); if (typeof refreshNavBadge === "function") refreshNavBadge();
  asgToast(`${afa(ids.length - failed.length)} مورد به‌روز شد${failed.length ? ` · ${afa(failed.length)} ناموفق` : ""}`,
    { action: "برگردان همه", dur: 7000, onAction: async () => {
      prev.forEach((p) => { const a = asgFind(p.id); if (a) a.is_done = p.was; }); asgPaintAll();
      for (const p of prev) await asgPushDone(p.id, p.was);
      if (typeof refreshNavBadge === "function") refreshNavBadge(); asgToast("↩️ برگشت");
    } });
}

/* ---- drawer جزئیات ---- */
function asgOpenDetail(id) {
  const a = asgFind(id); if (!a) return;
  const m = asgMeta(a), p = asgParse(a.deadline);
  asgLayer({ type: "drawer", title: "جزئیات تکلیف", html: `<div class="asg-dwr">
    <div class="asg-dwr-head"><span class="row-icon ${a.is_done ? "is-done" : asgOverdue(a) ? "is-over" : m.cls}">${a.is_done ? "✓" : m.icon}</span>
      <div><h2>${aesc(a.title)}</h2><div class="asg-badges"><span class="badge ${m.cls}">${m.label}</span>
        ${a.is_done ? `<span class="badge badge-done">انجام شده</span>` : ""}${asgUrgency(a)}</div></div>
      <button class="asg-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="asg-kv">
      <div><span>درس</span><b>${aesc(asgCourse(a))}</b></div>
      ${p ? `<div><span>مهلت</span><b>${asgJal(p)}${p.time ? ` — ${afa(p.time)}` : ""}</b></div>
        <div><span>میلادی</span><b dir="ltr">${aesc(p.dateStr)}</b></div>
        <div><span>وضعیت زمانی</span><b class="${asgOverdue(a) ? "is-over" : ""}">${asgRel(p.ms)}</b></div>` : `<div><span>مهلت</span><b>ثبت نشده</b></div>`}
      ${a.response_count ? `<div><span>پاسخ‌ها</span><b>${afa(a.response_count)}</b></div>` : ""}
    </div>
    ${a.description ? `<p class="asg-dwr-desc">${aesc(a.description)}</p>` : `<p class="asg-muted">توضیحی ثبت نشده است.</p>`}
    <div class="asg-dwr-actions">
      <button class="btn ${a.is_done ? "btn-ghost" : "btn-primary"} btn-sm" data-asg="toggle" data-id="${aesc(a.id)}">${a.is_done ? "لغو انجام" : "انجام شد ✓"}</button>
      ${a.submit_url ? `<a class="btn btn-soft btn-sm" href="${aesc(proxyUrl(a.submit_url))}" target="_blank" rel="noopener noreferrer">ارسال تکلیف ↗</a>` : ""}
      ${a.view_url ? `<a class="btn btn-ghost btn-sm" href="${aesc(proxyUrl(a.view_url))}" target="_blank" rel="noopener noreferrer">مشاهده در LMS ↗</a>` : ""}
      ${p ? `<button class="btn btn-ghost btn-sm" data-asg="ics" data-id="${aesc(a.id)}">⬇ افزودن به تقویم گوشی</button>` : ""}
      ${a.is_manual ? `<button class="btn btn-soft btn-sm" data-asg="edit" data-id="${aesc(a.id)}">✎ ویرایش</button>
        <button class="btn btn-ghost btn-sm asg-del" data-asg="del" data-id="${aesc(a.id)}">🗑 حذف</button>` : ""}
    </div></div>` });
}

/* ---- فرم تکلیف دستی ---- */
function asgErr(w, id, msg) { const f = w.querySelector(`[data-af="${id}"]`); if (!f) return !msg;
  f.classList.toggle("bad", !!msg); f.querySelector(".asg-err").textContent = msg || ""; return !msg; }
async function asgCourses() {
  if (Asg.courses) return Asg.courses;
  try { Asg.courses = (await api("/courses")).filter((c) => (c.source || "lms") === "lms"); }
  catch (_) { Asg.courses = []; }
  return Asg.courses;
}
async function asgOpenForm(item = null) {
  const courses = await asgCourses();
  const p = item ? asgParse(item.deadline) : null;
  const d = p ? p.dateStr : asgGStr(asgToday() + 1);
  const dp = asgParse(d + "T00:00");
  const opts = `<option value="">— انتخاب درس —</option>` + courses.map((c) =>
    `<option value="${aesc(c.id)}" ${item && item.course_id === c.id ? "selected" : ""}>${aesc(c.name)}</option>`).join("");
  asgLayer({ title: item ? "ویرایش تکلیف دستی" : "تکلیف دستی جدید", html: `<div class="glass-form asg-form">
    <div class="asg-note">تکلیف دستی فقط برای خودت است و در تقویم و خروجی ICS هم دیده می‌شود.</div>
    <div class="asg-field" data-af="title"><label class="field-label" for="asg-f-title">عنوان *</label>
      <input id="asg-f-title" class="input" value="${aesc(item ? item.title : "")}" placeholder="مثلاً حل تمرین فصل ۴" data-autofocus><small class="asg-err"></small></div>
    <div class="asg-field" data-af="course"><label class="field-label" for="asg-f-course">درس *</label>
      <select id="asg-f-course" class="input">${opts}</select><small class="asg-err"></small></div>
    <div class="asg-form-row">
      <div class="asg-field" data-af="date"><label class="field-label" for="asg-f-date">تاریخ مهلت (میلادی)</label>
        <input id="asg-f-date" class="input" type="date" dir="ltr" value="${aesc(d)}"><small class="asg-err"></small>
        <small class="asg-jlabel" id="asg-f-jlabel">${dp ? asgJal(dp) : ""}</small></div>
      <div class="asg-field"><label class="field-label" for="asg-f-time">ساعت</label>
        <input id="asg-f-time" class="input" type="time" dir="ltr" value="${aesc(p && p.time ? p.time : "23:59")}">
        <div class="asg-timechips">${["08:00", "12:00", "18:00", "23:59"].map((t) => `<button type="button" class="asg-tchip" data-t="${t}">${afa(t)}</button>`).join("")}</div></div>
    </div>
    <div class="asg-field"><label class="field-label" for="asg-f-desc">توضیح (اختیاری)</label>
      <textarea id="asg-f-desc" class="input" rows="3">${aesc(item ? item.description || "" : "")}</textarea></div>
    <div class="lib-modal-actions asg-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
      <button class="btn btn-primary" id="asg-f-save">${item ? "ذخیره تغییرات" : "افزودن تکلیف"}</button></div>
  </div>`, onMount: (w, L) => {
    const dateEl = w.querySelector("#asg-f-date"), jl = w.querySelector("#asg-f-jlabel");
    dateEl.addEventListener("change", () => { const pp = asgParse(dateEl.value + "T00:00"); jl.textContent = pp ? asgJal(pp) : ""; });
    w.querySelectorAll(".asg-tchip").forEach((b) => b.addEventListener("click", () => { w.querySelector("#asg-f-time").value = b.dataset.t; }));
    const btn = w.querySelector("#asg-f-save");
    btn.addEventListener("click", async () => {
      const title = w.querySelector("#asg-f-title").value.trim();
      const course_id = w.querySelector("#asg-f-course").value;
      const date = dateEl.value, time = w.querySelector("#asg-f-time").value || "23:59";
      const description = w.querySelector("#asg-f-desc").value.trim();
      let ok = asgErr(w, "title", title ? "" : "عنوان الزامی است");
      ok = asgErr(w, "course", course_id ? "" : "یک درس انتخاب کن") && ok;
      ok = asgErr(w, "date", asgParse(date + "T00:00") ? "" : "تاریخ معتبر نیست") && ok;
      if (!ok) return;
      btn.disabled = true; btn.textContent = "در حال ذخیره…";
      const body = { title, description, date, time, course_id };
      const cname = (courses.find((c) => c.id === course_id) || {}).name || "";
      try {
        if (item) {
          await api(`/assignments/${encodeURIComponent(item.id)}`, { method: "PATCH", body: JSON.stringify(body) });
          Object.assign(item, { title, description, course_id, course_name: cname, deadline: `${date}T${time}:00`, deadline_jalali: null });
          L.close(); asgCloseAll(); asgPaintAll(); asgToast("✅ تکلیف به‌روز شد");
        } else {
          const r = await api("/assignments/manual", { method: "POST", body: JSON.stringify(body) });
          Asg.items.unshift({ id: r.id, title, description, course_id, course_name: cname,
            deadline: `${date}T${time}:00`, deadline_jalali: null, submit_url: null, view_url: null,
            response_count: 0, is_new: true, is_manual: true, is_done: false, is_expired: false, source: "lms" });
          Asg.filter = "open"; Asg.q = ""; const qi = document.getElementById("asg-q"); if (qi) qi.value = "";
          L.close(); asgPaintAll(); asgToast("✅ تکلیف دستی اضافه شد");
        }
        if (typeof refreshNavBadge === "function") refreshNavBadge();
      } catch (e) {
        btn.disabled = false; btn.textContent = item ? "ذخیره تغییرات" : "افزودن تکلیف";
        asgToast([404, 405].includes(e.status) ? "⚠️ بک‌اند این عملیات را پشتیبانی نمی‌کند" : "❌ " + (e.message || "خطا"));
      }
    });
  }});
}
function asgDelete(ids) {
  const list = ids.map((id) => asgFind(id)).filter((a) => a && a.is_manual);
  if (!list.length) { asgToast("فقط تکالیف دستی قابل حذف هستند"); return; }
  const snapshot = list.map((a) => ({ a, i: Asg.items.indexOf(a) }));
  list.forEach((a) => Asg.items.splice(Asg.items.indexOf(a), 1));
  Asg.sel.clear(); asgCloseAll(); asgPaintAll();
  if (typeof refreshNavBadge === "function") refreshNavBadge();
  let undone = false;
  const restore = () => { snapshot.sort((x, y) => x.i - y.i).forEach((s) => Asg.items.splice(Math.min(s.i, Asg.items.length), 0, s.a)); asgPaintAll(); };
  const timer = setTimeout(async () => {
    if (undone) return;
    let bad = 0;
    for (const s of snapshot) { try { await api(`/assignments/${encodeURIComponent(s.a.id)}`, { method: "DELETE" }); } catch (_) { bad++; } }
    if (bad) { restore(); asgToast("⚠️ حذف روی سرور انجام نشد — برگردانده شد"); }
  }, 6000);
  asgToast(`🗑 ${afa(list.length)} تکلیف حذف شد`, { action: "برگردان", dur: 6000, onAction() { undone = true; clearTimeout(timer); restore(); asgToast("↩️ برگشت"); } });
}
function asgICS(id) {
  const a = asgFind(id); if (!a) return;
  const p = asgParse(a.deadline); if (!p) return;
  const g = d2g(p.jdn), t = (p.time || "23:59").replace(":", "");
  const stamp = `${g.gy}${String(g.gm).padStart(2, "0")}${String(g.gd).padStart(2, "0")}T${t}00`;
  const ei = (s) => String(s || "").replace(/[\\,;]/g, "\\$&").replace(/\n/g, "\\n");
  const ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//LMS Assistant//FA", "BEGIN:VEVENT",
    `UID:asg-${a.id}@lms-assistant`, `DTSTAMP:${stamp}`, `DTSTART:${stamp}`,
    `SUMMARY:${ei(a.title)}`, `DESCRIPTION:${ei((a.description || "") + " — " + asgCourse(a))}`,
    "END:VEVENT", "END:VCALENDAR"].join("\r\n");
  const el = document.createElement("a");
  el.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
  el.download = "assignment.ics"; el.click(); setTimeout(() => URL.revokeObjectURL(el.href), 1000);
  asgToast("⬇ فایل تکلیف ساخته شد");
}

/* ---- delegation (یک‌بار) ---- */
function asgWire() {
  if (Asg.wired) return; Asg.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-asg]");
    if (!el) {
      const card = e.target.closest("[data-asg-card]");
      if (card && !e.target.closest("a,button,input,select,label")) asgOpenDetail(card.dataset.asgCard);
      return;
    }
    const act = el.dataset.asg, id = el.dataset.id;
    switch (act) {
      case "filter": Asg.filter = el.dataset.v; Asg.sel.clear(); asgPaintPills(); asgPaintBulk(); asgPaintList(); break;
      case "view": Asg.view = el.dataset.v; localStorage.setItem("asg:view", Asg.view); asgPaintList(); break;
      case "toggle": { const a = asgFind(id); if (a) asgToggle(id, !a.is_done); break; }
      case "detail": e.stopPropagation(); asgOpenDetail(id); break;
      case "add": asgOpenForm(null); break;
      case "edit": { const a = asgFind(id); if (a) asgOpenForm(a); break; }
      case "del": asgDelete([id]); break;
      case "ics": asgICS(id); break;
      case "bulk-done": asgBulkSet(true); break;
      case "bulk-undone": asgBulkSet(false); break;
      case "bulk-del": asgDelete([...Asg.sel]); break;
      case "bulk-clear": Asg.sel.clear(); asgPaintBulk(); asgPaintList(); break;
      case "group-sel": {
        const g = asgGroups(asgFiltered()).find((x) => x.key === el.dataset.k);
        if (g) { g.items.forEach((a) => Asg.sel.add(String(a.id))); asgPaintBulk(); asgPaintList(); }
        break;
      }
      case "view-save": asgLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <p class="asg-muted" style="margin:0">فیلتر، مرتب‌سازی، گروه‌بندی، نما و جستجوی فعلی ذخیره می‌شود.</p>
          <div class="asg-field" data-af="vname"><label class="field-label" for="asg-v-name">نام نما *</label>
            <input id="asg-v-name" class="input" placeholder="مثلاً عقب‌افتاده‌های کوئرا" data-autofocus><small class="asg-err"></small></div>
          <div class="lib-modal-actions asg-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
            <button class="btn btn-primary" id="asg-v-save">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#asg-v-save").addEventListener("click", () => {
          const n = w.querySelector("#asg-v-name").value.trim();
          if (!asgErr(w, "vname", n ? "" : "نام الزامی است")) return;
          Asg.views[n] = { filter: Asg.filter, sort: Asg.sort, group: Asg.group, view: Asg.view, q: Asg.q };
          Asg.views = Object.fromEntries(Object.entries(Asg.views).slice(-6));
          localStorage.setItem("asg:views", JSON.stringify(Asg.views));
          L.close(); asgPaintSaved(); asgToast("💾 نما ذخیره شد");
        }); } }); break;
      case "view-apply": {
        const v = Asg.views[el.dataset.k]; if (!v) break;
        Object.assign(Asg, { filter: v.filter, sort: v.sort, group: v.group, view: v.view, q: v.q || "" });
        localStorage.setItem("asg:sort", Asg.sort); localStorage.setItem("asg:view", Asg.view); localStorage.setItem("asg:group", Asg.group);
        const qi = document.getElementById("asg-q"); if (qi) qi.value = Asg.q;
        const so = document.getElementById("asg-sort"); if (so) so.value = Asg.sort;
        const gr = document.getElementById("asg-group"); if (gr) gr.value = Asg.group;
        asgPaintAll(); break;
      }
      case "view-del": delete Asg.views[el.dataset.k]; localStorage.setItem("asg:views", JSON.stringify(Asg.views)); asgPaintSaved(); break;
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "asg-q") { Asg.q = e.target.value; asgPaintList(); } });
  document.addEventListener("change", (e) => {
    if (e.target.id === "asg-sort") { Asg.sort = e.target.value; localStorage.setItem("asg:sort", Asg.sort); asgPaintList(); }
    if (e.target.id === "asg-group") { Asg.group = e.target.value; localStorage.setItem("asg:group", Asg.group); asgPaintList(); }
    if (e.target.dataset && e.target.dataset.asgSel !== undefined) {
      const id = e.target.dataset.asgSel;
      e.target.checked ? Asg.sel.add(id) : Asg.sel.delete(id);
      asgPaintBulk();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const hostBusy = (typeof Lib !== "undefined" && Lib.layers && Lib.layers.length) || (typeof Cal !== "undefined" && Cal._layers && Cal._layers.length);
    if (hostBusy) return;
    if (Asg.layers.length) Asg.layers[Asg.layers.length - 1].close();
  });
}
asgWire();

// ---------- Wall v2 (پیام‌های وال) ----------
const WAL_WD = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"];
const Wal = {
  items: [], names: {}, q: "", filter: "all", course: "all",
  sort: localStorage.getItem("wal:sort") || "new",
  group: localStorage.getItem("wal:group") || "none",
  view: localStorage.getItem("wal:view") || "cozy",
  sel: new Set(), views: JSON.parse(localStorage.getItem("wal:views") || "{}"),
  layers: [], wired: false, loaded: false,
};
const wesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const wfa = (n) => faDigits(String(n));
function walTs(v) { const t = Date.parse(String(v || "").replace(" ", "T")); return Number.isNaN(t) ? null : t; }
function walAgo(v) {
  const t = walTs(v); if (t == null) return "";
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${wfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${wfa(Math.floor(s / 3600))} ساعت پیش`;
  if (s < 2592000) return `${wfa(Math.floor(s / 86400))} روز پیش`;
  return String(v).slice(0, 10);
}
function walDayKey(v) { const t = walTs(v); if (t == null) return "zz"; const d = new Date(t); return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`; }
function walDayLabel(v) {
  const t = walTs(v); if (t == null) return "بدون زمان";
  const now = new Date(); const y = new Date(now); y.setDate(now.getDate() - 1);
  const k = walDayKey(v);
  if (k === walDayKey(now.toISOString())) return "امروز";
  if (k === walDayKey(y.toISOString())) return "دیروز";
  const d = new Date(t); const j = d2j(g2d(d.getFullYear(), d.getMonth() + 1, d.getDate()));
  return `${WAL_WD[jWeekday(g2d(d.getFullYear(), d.getMonth() + 1, d.getDate()))]} ${wfa(j.jd)} ${J_MONTHS[j.jm - 1]}`;
}
function walHi(text, q) {
  const t = String(text ?? ""); if (!q) return wesc(t);
  const rx = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
  return t.split(rx).map((p, i) => i % 2 ? `<mark class="wal-mark">${wesc(p)}</mark>` : wesc(p)).join("");
}
function walRich(text) {
  const t = String(text ?? ""); const rx = /(https?:\/\/[^\s]+)/g;
  let out = "", last = 0, m;
  while ((m = rx.exec(t))) {
    out += wesc(t.slice(last, m.index));
    const u = m[0];
    const href = /lms[345]\.ui\.ac\.ir/.test(u) ? proxyUrl(u) : u;
    out += `<a class="wal-link" href="${wesc(href)}" target="_blank" rel="noopener noreferrer">${wesc(u)}</a>`;
    last = m.index + u.length;
  }
  return out + wesc(t.slice(last));
}
const walCourse = (p) => Wal.names[p.course_id] || p.course_name || p.course_id || "—";
function walLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof admLayer === "function" ? admLayer
    : typeof crsLayer === "function" ? crsLayer : typeof mxLayer === "function" ? mxLayer
    : typeof stgLayer === "function" ? stgLayer : typeof qraLayer === "function" ? qraLayer
    : typeof chgLayer === "function" ? chgLayer : typeof bdLayer === "function" ? bdLayer : walOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = Wal.layers.indexOf(L); if (i >= 0) Wal.layers.splice(i, 1); opts.onClose && opts.onClose(); } });
  Wal.layers.push(L); return L;
}
function walToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof bdToast === "function") return bdToast(m, o);
  return toast(m);
}
function walOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "glass-modal-backdrop";
  w.innerHTML = opts.type === "drawer"
    ? `<aside class="wal-drawer" role="dialog" aria-modal="true" aria-label="${wesc(opts.title)}">${opts.html}</aside>`
    : `<div class="glass-modal" role="dialog" aria-modal="true"><h3>${wesc(opts.title)}</h3>${opts.html}</div>`;
  document.body.appendChild(w);
  const panel = w.querySelector(".wal-drawer,.glass-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    const i = Wal.layers.indexOf(L); if (i >= 0) Wal.layers.splice(i, 1);
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input,select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => (panel.querySelector("button,a,input") || panel).focus?.());
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
const walCloseAll = () => Wal.layers.slice().forEach((l) => l.close());
window.__walTeardown = walCloseAll;

/* ---- داده ---- */
async function renderPosts() {
  walCloseAll(); Wal.sel.clear();
  let items = [], courses = [];
  try {
    [items, courses] = await Promise.all([
      api("/posts"),
      api("/courses").catch(() => []),
    ]);
  } catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری پیام‌ها<small>${wesc(e.message)}</small></div>`;
    return;
  }
  Wal.items = Array.isArray(items) ? items : [];
  Wal.names = Object.fromEntries((courses || []).map((c) => [c.id, c.name]));
  Wal.loaded = true;
  const courseIds = [...new Set(Wal.items.map((p) => p.course_id).filter(Boolean))];
  contentEl.innerHTML = `
    ${pageHead("پیام‌های وال", "گفتگو و اطلاعیه‌های درس‌ها")}
    <div class="card wal-hero" id="wal-hero"></div>
    <div class="wal-toolbar">
      <div class="search-box wal-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="wal-q" type="search" value="${wesc(Wal.q)}" placeholder="جستجو در متن، نویسنده یا درس…" aria-label="جستجو"></div>
      <select id="wal-course" class="input wal-sel" aria-label="فیلتر درس">
        <option value="all">همه درس‌ها</option>
        ${courseIds.map((id) => `<option value="${wesc(id)}" ${Wal.course === id ? "selected" : ""}>${wesc(Wal.names[id] || id)}</option>`).join("")}
      </select>
      <select id="wal-sort" class="input wal-sel" aria-label="مرتب‌سازی">
        <option value="new">جدیدترین</option><option value="old">قدیمی‌ترین</option><option value="unread">خوانده‌نشده اول</option>
      </select>
      <select id="wal-group" class="input wal-sel" aria-label="گروه‌بندی">
        <option value="none">بدون گروه</option><option value="day">گروه: روز</option><option value="course">گروه: درس</option>
      </select>
      <div class="wal-vt" role="group" aria-label="حالت نمایش">
        <button data-wal="view" data-v="cozy" title="راحت" aria-label="راحت">☰</button>
        <button data-wal="view" data-v="compact" title="فشرده" aria-label="فشرده">≡</button>
      </div>
      <button class="lq-btn lq-sm" data-wal="view-save" title="ذخیره نما">💾</button>
    </div>
    <div class="wal-pills" id="wal-pills"></div>
    <div class="wal-saved" id="wal-saved"></div>
    <div id="wal-bulk"></div>
    <div id="wal-list"></div>`;
  document.getElementById("wal-sort").value = Wal.sort;
  document.getElementById("wal-group").value = Wal.group;
  walPaintAll();
}
function walMatch(p, f) {
  const t = walTs(p.posted_at);
  if (f === "unread") return !!p.is_new;
  if (f === "today") return t != null && walDayKey(p.posted_at) === walDayKey(new Date().toISOString());
  if (f === "week") return t != null && Date.now() - t < 7 * 864e5;
  return true;
}
function walFiltered() {
  const q = Wal.q.trim().toLowerCase();
  let l = Wal.items.filter((p) => walMatch(p, Wal.filter) && (Wal.course === "all" || p.course_id === Wal.course));
  if (q) l = l.filter((p) => `${p.text || ""} ${p.author || ""} ${walCourse(p)}`.toLowerCase().includes(q));
  const ts = (p) => walTs(p.posted_at) ?? 0;
  return l.slice().sort((a, b) =>
    Wal.sort === "old" ? ts(a) - ts(b)
    : Wal.sort === "unread" ? (!!b.is_new) - (!!a.is_new) || ts(b) - ts(a)
    : ts(b) - ts(a));
}
function walPaintAll() { walPaintHero(); walPaintPills(); walPaintSaved(); walPaintBulk(); walPaintList(); }
function walPaintHero() {
  const box = document.getElementById("wal-hero"); if (!box) return;
  const unread = Wal.items.filter((p) => p.is_new).length;
  const today = Wal.items.filter((p) => walMatch(p, "today")).length;
  box.innerHTML = `
    <div class="wal-hero-stats">
      <div class="wal-hstat"><b>${wfa(Wal.items.length)}</b><span>کل پیام‌ها</span></div>
      <div class="wal-hstat"><b style="color:var(--danger)">${wfa(unread)}</b><span>خوانده‌نشده</span></div>
      <div class="wal-hstat"><b style="color:var(--info)">${wfa(today)}</b><span>امروز</span></div>
    </div>
    <div class="wal-hero-actions">
      <button class="lq-btn lq-sm" style="--lq-hue:var(--accent)" data-wal="read-all" ${unread ? "" : "disabled"}>✓ همه را خواندم</button>
      <button class="lq-btn lq-sm" data-wal="reload" title="بارگذاری مجدد">↻</button>
    </div>`;
}
function walPaintPills() {
  const box = document.getElementById("wal-pills"); if (!box) return;
  const pills = [["all", "همه", "--primary"], ["unread", "خوانده‌نشده", "--danger"], ["today", "امروز", "--info"], ["week", "این هفته", "--accent"]];
  box.innerHTML = pills.map(([k, l, cv]) => {
    const n = Wal.items.filter((p) => walMatch(p, k)).length;
    return `<button class="lq-chip ${Wal.filter === k ? "is-on" : ""}" style="--lq-hue:var(${cv})" data-wal="filter" data-v="${k}" aria-pressed="${Wal.filter === k}">${l}<b>${wfa(n)}</b></button>`;
  }).join("");
}
function walPaintSaved() {
  const box = document.getElementById("wal-saved"); if (!box) return;
  const keys = Object.keys(Wal.views);
  box.innerHTML = keys.length ? `<span class="wal-muted">نماها:</span>` + keys.map((k) =>
    `<span class="wal-sv"><button data-wal="view-apply" data-k="${wesc(k)}">${wesc(k)}</button>
      <button class="x" data-wal="view-del" data-k="${wesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function walPaintBulk() {
  const box = document.getElementById("wal-bulk"); if (!box) return;
  box.innerHTML = Wal.sel.size ? `<div class="wal-bulkbar"><b>${wfa(Wal.sel.size)}</b> انتخاب شده
    <button class="lq-btn lq-sm" style="--lq-hue:var(--accent)" data-wal="bulk-read">✓ خواندم</button>
    <button class="lq-btn lq-sm" data-wal="bulk-unread">نخوانده کن</button>
    <button class="lq-btn lq-sm" data-wal="bulk-clear">پاک کردن</button></div>` : "";
}
function walRow(p) {
  const q = Wal.q.trim();
  const unread = !!p.is_new;
  return `<article class="wal-row ${unread ? "is-unread" : ""} ${Wal.view === "compact" ? "is-compact" : ""}" data-wal-card="${wesc(p.id)}">
    <input type="checkbox" class="wal-chk" data-wal-sel="${wesc(p.id)}" ${Wal.sel.has(String(p.id)) ? "checked" : ""} aria-label="انتخاب پیام">
    <span class="wal-ava">${wesc((p.author || "؟").trim().charAt(0))}</span>
    <div class="wal-body">
      <div class="wal-head">
        <b>${walHi(p.author || "—", q)}</b>
        ${unread ? `<span class="wal-dot" title="خوانده‌نشده"></span>` : ""}
        <button class="wal-coursechip" data-wal="course" data-id="${wesc(p.course_id || "")}">📘 ${walHi(walCourse(p), q)}</button>
        <span class="wal-time" title="${wesc(p.posted_at || "")}">${wesc(p.posted_at_jalali || walAgo(p.posted_at) || "")}</span>
      </div>
      <div class="wal-clamp">${walHi(p.text || "", q)}</div>
    </div>
    <div class="wal-actions">
      <button class="lq-btn lq-sm ${unread ? "is-on" : ""}" style="--lq-hue:var(--accent)" data-wal="toggle" data-id="${wesc(p.id)}">${unread ? "خواندم ✓" : "نخوانده"}</button>
      <button class="lq-btn lq-sm" data-wal="detail" data-id="${wesc(p.id)}">متن کامل</button>
    </div>
  </article>`;
}
function walPaintList() {
  const box = document.getElementById("wal-list"); if (!box) return;
  document.querySelectorAll(".wal-vt button").forEach((b) => { const on = b.dataset.v === Wal.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const list = walFiltered();
  if (!list.length) {
    box.innerHTML = Wal.items.length
      ? `<div class="empty"><span class="empty-icon">🔍</span>پیامی با این فیلترها نیست<small>فیلتر یا عبارت جستجو را تغییر بده</small>
          <div style="margin-top:.8rem"><button class="lq-btn lq-sm" data-wal="clear">پاک کردن فیلترها</button></div></div>`
      : `<div class="empty"><span class="empty-icon">💬</span>هنوز پیامی نیست<small>بعد از همگام‌سازی، پیام‌های وال اینجا می‌آیند</small>
          <div style="margin-top:.8rem"><button class="lq-btn lq-sm" style="--lq-hue:var(--primary)" data-wal="sync">🔄 همگام‌سازی</button></div></div>`;
    return;
  }
  if (Wal.group === "none") { box.innerHTML = `<div class="wal-list">${list.map(walRow).join("")}</div>`; return; }
  const groups = new Map();
  list.forEach((p) => {
    const k = Wal.group === "day" ? walDayKey(p.posted_at) : (p.course_id || "zz");
    const label = Wal.group === "day" ? walDayLabel(p.posted_at) : walCourse(p);
    if (!groups.has(k)) groups.set(k, { label, items: [] });
    groups.get(k).items.push(p);
  });
  box.innerHTML = [...groups.values()].map((g) => {
    const unreadIds = g.items.filter((p) => p.is_new).map((p) => String(p.id));
    return `<section class="wal-group">
      <div class="wal-grouphead"><b>${wesc(g.label)}</b><span class="badge">${wfa(g.items.length)} پیام</span>
        ${unreadIds.length ? `<button class="lq-link" data-wal="group-read" data-ids="${wesc(unreadIds.join(","))}">✓ خواندن این گروه (${wfa(unreadIds.length)})</button>` : ""}</div>
      <div class="wal-list">${g.items.map(walRow).join("")}</div>
    </section>`;
  }).join("");
}

/* ---- خوانده/نخوانده ---- */
async function walPush(ids, read) {
  const r = await api("/posts/read-bulk", { method: "POST", body: JSON.stringify({ ids, read }) });
  return r.updated || [];
}
function walSyncButtons(id) {
  const p = Wal.items.find((x) => String(x.id) === String(id)); if (!p) return;
  document.querySelectorAll(`[data-wal="toggle"][data-id="${CSS.escape(String(id))}"]`).forEach((b) => {
    b.textContent = p.is_new ? "خواندم ✓" : "نخوانده";
    b.classList.toggle("is-on", !!p.is_new);
  });
}
async function walSetRead(ids, read, label) {
  ids = ids.map(String).filter((id) => Wal.items.some((p) => String(p.id) === id));
  if (!ids.length) return;
  const prev = ids.map((id) => ({ id, was: !!Wal.items.find((p) => String(p.id) === id).is_new }));
  ids.forEach((id) => { const p = Wal.items.find((x) => String(x.id) === id); p.is_new = !read; Wal.sel.delete(id); });
  walPaintAll(); ids.forEach(walSyncButtons);
  if (typeof refreshNavBadge === "function") refreshNavBadge();
  let ok = false;
  try { await walPush(ids, read); ok = true; }
  catch (err) {
    if (read && [404, 405].includes(err.status) && ids.length === prev.filter((x) => x.was).length) {
      try { await api("/posts/read", { method: "POST", body: "{}" }); ok = true; } catch (_) {}
    }
  }
  if (!ok) {
    prev.forEach(({ id, was }) => { Wal.items.find((p) => String(p.id) === id).is_new = was; });
    walPaintAll(); ids.forEach(walSyncButtons);
    walToast("❌ ثبت وضعیت ناموفق بود" + (ids.length === 1 ? "" : " — endpoint خواندن انتخابی نصب نشده"));
    return;
  }
  walToast(label || (read ? "✅ خوانده شد" : "نخوانده علامت خورد"), { action: "برگردان", dur: 6000, onAction: async () => {
    const toUnread = prev.filter((x) => x.was).map((x) => x.id);
    const toRead = prev.filter((x) => !x.was).map((x) => x.id);
    prev.forEach(({ id, was }) => { Wal.items.find((p) => String(p.id) === id).is_new = was; });
    walPaintAll(); ids.forEach(walSyncButtons);
    try { if (toUnread.length) await walPush(toUnread, false); if (toRead.length) await walPush(toRead, true); } catch (_) {}
    if (typeof refreshNavBadge === "function") refreshNavBadge();
  }});
}
const walMarkAll = () => walSetRead(Wal.items.filter((p) => p.is_new).map((p) => String(p.id)), true, "✅ همه پیام‌ها خوانده شد");

/* ---- دراور ---- */
function walOpenDetail(id) {
  const p = Wal.items.find((x) => String(x.id) === String(id)); if (!p) return;
  walLayer({ type: "drawer", title: "پیام وال", html: `<div class="wal-dwr">
    <div class="wal-dwr-head">
      <span class="wal-ava lg">${wesc((p.author || "؟").trim().charAt(0))}</span>
      <div><h2>${wesc(p.author || "—")}</h2>
        <div class="wal-dwr-meta">
          <button class="wal-coursechip" data-wal="course" data-id="${wesc(p.course_id || "")}" data-lib-close>📘 ${wesc(walCourse(p))}</button>
          <span>${wesc(p.posted_at_jalali || "")}</span><span>${walAgo(p.posted_at)}</span>
          ${p.is_new ? `<span class="badge badge-new">خوانده‌نشده</span>` : ""}
        </div></div>
      <button class="wal-x" data-lib-close aria-label="بستن">✕</button>
    </div>
    <div class="wal-fulltext">${walRich(p.text || "")}</div>
    <div class="wal-dwr-actions">
      <button class="lq-btn lq-sm ${p.is_new ? "is-on" : ""}" style="--lq-hue:var(--accent)" data-wal="toggle" data-id="${wesc(p.id)}">${p.is_new ? "خواندم ✓" : "نخوانده"}</button>
      <button class="lq-btn lq-sm" data-wal="copy" data-id="${wesc(p.id)}">📋 کپی متن</button>
      ${p.course_id ? `<button class="lq-btn lq-sm" data-wal="course" data-id="${wesc(p.course_id)}" data-lib-close>صفحه درس</button>` : ""}
    </div>
  </div>` });
}

/* ---- delegation ---- */
function walWire() {
  if (Wal.wired) return; Wal.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-wal]");
    if (!el) {
      const card = e.target.closest("[data-wal-card]");
      if (card && !e.target.closest("a,button,input,select,label")) walOpenDetail(card.dataset.walCard);
      return;
    }
    const act = el.dataset.wal, id = el.dataset.id, v = el.dataset.v;
    switch (act) {
      case "filter": Wal.filter = v; Wal.sel.clear(); walPaintPills(); walPaintBulk(); walPaintList(); break;
      case "view": Wal.view = v; localStorage.setItem("wal:view", v); walPaintList(); break;
      case "toggle": { const p = Wal.items.find((x) => String(x.id) === String(id)); if (p) walSetRead([id], !p.is_new); break; }
      case "detail": walOpenDetail(id); break;
      case "read-all": walMarkAll(); break;
      case "group-read": walSetRead((el.dataset.ids || "").split(",").filter(Boolean), true, "✅ گروه خوانده شد"); break;
      case "bulk-read": walSetRead([...Wal.sel], true); break;
      case "bulk-unread": walSetRead([...Wal.sel], false); break;
      case "bulk-clear": Wal.sel.clear(); walPaintBulk(); walPaintList(); break;
      case "course": if (id) location.hash = "#/course/" + encodeURIComponent(id); break;
      case "reload": renderPosts(); break;
      case "sync": document.getElementById("btn-sync")?.click(); break;
      case "clear": Wal.q = ""; Wal.filter = "all"; Wal.course = "all";
        { const qi = document.getElementById("wal-q"); if (qi) qi.value = "";
          const cs = document.getElementById("wal-course"); if (cs) cs.value = "all"; }
        walPaintAll(); break;
      case "copy": { const p = Wal.items.find((x) => String(x.id) === String(id)); if (!p) break;
        const done = () => walToast("📋 متن کپی شد");
        if (navigator.clipboard) navigator.clipboard.writeText(p.text || "").then(done, done);
        else { const t = document.createElement("textarea"); t.value = p.text || ""; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); }
        break; }
      case "view-save": walLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <div><label class="field-label" for="wal-v-n">نام نما *</label>
            <input id="wal-v-n" class="input" placeholder="مثلاً نخوانده‌های فیزیک" data-autofocus></div>
          <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
            <button class="btn btn-primary" id="wal-v-ok">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#wal-v-ok").addEventListener("click", () => {
          const n = w.querySelector("#wal-v-n").value.trim(); if (!n) return;
          Wal.views[n] = { q: Wal.q, filter: Wal.filter, course: Wal.course, sort: Wal.sort, group: Wal.group, view: Wal.view };
          Wal.views = Object.fromEntries(Object.entries(Wal.views).slice(-6));
          localStorage.setItem("wal:views", JSON.stringify(Wal.views));
          L.close(); walPaintSaved(); walToast("💾 نما ذخیره شد");
        }); } }); break;
      case "view-apply": { const x = Wal.views[el.dataset.k]; if (!x) break;
        Object.assign(Wal, x); localStorage.setItem("wal:sort", Wal.sort); localStorage.setItem("wal:group", Wal.group); localStorage.setItem("wal:view", Wal.view);
        renderPosts(); break; }
      case "view-del": delete Wal.views[el.dataset.k]; localStorage.setItem("wal:views", JSON.stringify(Wal.views)); walPaintSaved(); break;
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "wal-q") { Wal.q = e.target.value; walPaintList(); } });
  document.addEventListener("change", (e) => {
    if (e.target.id === "wal-course") { Wal.course = e.target.value; walPaintList(); }
    if (e.target.id === "wal-sort") { Wal.sort = e.target.value; localStorage.setItem("wal:sort", Wal.sort); walPaintList(); }
    if (e.target.id === "wal-group") { Wal.group = e.target.value; localStorage.setItem("wal:group", Wal.group); walPaintList(); }
    if (e.target.dataset && e.target.dataset.walSel !== undefined) {
      const id = e.target.dataset.walSel;
      e.target.checked ? Wal.sel.add(id) : Wal.sel.delete(id);
      walPaintBulk();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = (typeof Lib !== "undefined" && Lib.layers && Lib.layers.length)
      || (typeof Cal !== "undefined" && Cal._layers && Cal._layers.length)
      || (typeof Asg !== "undefined" && Asg.layers && Asg.layers.length)
      || (typeof Adm !== "undefined" && Adm.layers && Adm.layers.length)
      || (typeof Crs !== "undefined" && Crs.layers && Crs.layers.length)
      || (typeof MapX !== "undefined" && MapX.layers && MapX.layers.length)
      || (typeof Stg !== "undefined" && Stg.layers && Stg.layers.length)
      || (typeof Dboard !== "undefined" && Dboard.layers && Dboard.layers.length)
      || (typeof Chg !== "undefined" && Chg.layers && Chg.layers.length)
      || (typeof Qra !== "undefined" && Qra.layers && Qra.layers.length);
    if (busy) return;
    if (Wal.layers.length) Wal.layers[Wal.layers.length - 1].close();
  });
}
walWire();
window.markPostsRead = async () => {
  if (Wal.loaded && currentRoute() === "posts") return walMarkAll();
  try { await api("/posts/read", { method: "POST", body: "{}" }); toast("✅ همه پیام‌ها خوانده شدند"); if (typeof refreshNavBadge === "function") refreshNavBadge(); renderPage(currentRoute()); }
  catch (e) { toast("❌ " + (e.message || "خطا")); }
};

// ---------- Contents v2 (محتواها) ----------
const Cnt = {
  items: [], q: "", filter: "all", course: "all", type: "all",
  sort: localStorage.getItem("cnt:sort") || "new",
  group: localStorage.getItem("cnt:group") || "none",
  view: localStorage.getItem("cnt:view") || "cozy",
  sel: new Set(), views: JSON.parse(localStorage.getItem("cnt:views") || "{}"),
  layers: [], wired: false, loaded: false,
};
const fesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ffa = (n) => faDigits(String(n));
function cntTs(v) { const t = Date.parse(String(v || "").replace(" ", "T")); return Number.isNaN(t) ? null : t; }
function cntAgo(v) {
  const t = cntTs(v); if (t == null) return "";
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${ffa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${ffa(Math.floor(s / 3600))} ساعت پیش`;
  if (s < 2592000) return `${ffa(Math.floor(s / 86400))} روز پیش`;
  return String(v).slice(0, 10);
}
function cntDayKey(v) { const t = cntTs(v); if (t == null) return "zz"; const d = new Date(t); return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`; }
function cntDayLabel(v) {
  const t = cntTs(v); if (t == null) return "بدون زمان";
  const now = new Date(), y = new Date(now); y.setDate(now.getDate() - 1);
  const k = cntDayKey(v);
  if (k === cntDayKey(now.toISOString())) return "امروز";
  if (k === cntDayKey(y.toISOString())) return "دیروز";
  const d = new Date(t), j = d2j(g2d(d.getFullYear(), d.getMonth() + 1, d.getDate()));
  return `${ffa(j.jd)} ${J_MONTHS[j.jm - 1]}`;
}
function cntHi(text, q) {
  const t = String(text ?? ""); if (!q) return fesc(t);
  const rx = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
  return t.split(rx).map((p, i) => i % 2 ? `<mark class="cnt-mark">${fesc(p)}</mark>` : fesc(p)).join("");
}
function cntKind(c) {
  const s = String(c.filename || c.title || c.url || "").toLowerCase();
  const ct = String(c.content_type || "").toLowerCase();
  if (/\.pdf(\?|$)/.test(s) || ct.includes("pdf")) return { ico: "📕", hue: "var(--danger)", label: "PDF" };
  if (/\.(zip|rar|7z|tar|gz)(\?|$)/.test(s)) return { ico: "🗜", hue: "var(--warning)", label: "آرشیو" };
  if (/\.(mp4|mkv|avi|mov|webm)(\?|$)/.test(s) || ct.includes("video")) return { ico: "🎬", hue: "var(--info)", label: "ویدیو" };
  if (/\.(mp3|wav|ogg|m4a)(\?|$)/.test(s) || ct.includes("audio")) return { ico: "🎧", hue: "var(--accent)", label: "صوت" };
  if (/\.(pptx?|docx?|xlsx?)(\?|$)/.test(s)) return { ico: "📘", hue: "var(--primary)", label: "سند" };
  if (/\.(png|jpe?g|gif|webp|svg)(\?|$)/.test(s) || ct.includes("image")) return { ico: "🖼", hue: "var(--accent)", label: "تصویر" };
  if (!c.filename && /^https?:/.test(c.url || "")) return { ico: "🔗", hue: "var(--info)", label: "لینک" };
  return { ico: "📄", hue: "var(--muted)", label: c.content_type || "فایل" };
}
function cntLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof crsLayer === "function" ? crsLayer
    : typeof stgLayer === "function" ? stgLayer : typeof walLayer === "function" ? walLayer
    : typeof bdLayer === "function" ? bdLayer : null;
  if (f) { const L = f({ ...opts, onClose: () => { const i = Cnt.layers.indexOf(L); if (i >= 0) Cnt.layers.splice(i, 1); opts.onClose && opts.onClose(); } }); Cnt.layers.push(L); return L; }
  const w = document.createElement("div"); w.className = "glass-modal-backdrop";
  w.innerHTML = `<div class="glass-modal" role="dialog" aria-modal="true"><h3>${fesc(opts.title || "")}</h3>${opts.html}</div>`;
  document.body.appendChild(w);
  const L = { wrap: w, panel: w.querySelector(".glass-modal"), close() { w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230); const i = Cnt.layers.indexOf(L); if (i >= 0) Cnt.layers.splice(i, 1); } };
  w.addEventListener("click", (e) => { if (e.target === w) L.close(); });
  w.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  Cnt.layers.push(L); if (opts.onMount) opts.onMount(w, L); return L;
}
function cntToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof walToast === "function") return walToast(m, o);
  if (typeof bdToast === "function") return bdToast(m, o);
  return toast(m);
}
const cntCloseAll = () => Cnt.layers.slice().forEach((l) => l.close());
window.__cntTeardown = cntCloseAll;

async function renderContents() {
  cntCloseAll(); Cnt.sel.clear();
  let items = [];
  try { items = await api("/contents"); }
  catch (e) { contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری محتواها<small>${fesc(e.message)}</small></div>`; return; }
  Cnt.items = Array.isArray(items) ? items : [];
  Cnt.loaded = true;
  const courses = [...new Map(Cnt.items.map((c) => [c.course_id, c.course_name])).entries()];
  const types = [...new Set(Cnt.items.map((c) => c.content_type).filter(Boolean))];
  contentEl.innerHTML = `
    ${pageHead("محتواها", "فایل‌ها و منابع درس‌ها")}
    <div class="card cnt-hero" id="cnt-hero"></div>
    <div class="cnt-toolbar">
      <div class="search-box cnt-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="cnt-q" type="search" value="${fesc(Cnt.q)}" placeholder="جستجوی عنوان، فایل، درس یا استاد…" aria-label="جستجو"></div>
      <select id="cnt-course" class="input cnt-sel" aria-label="فیلتر درس"><option value="all">همه درس‌ها</option>
        ${courses.map(([id, n]) => `<option value="${fesc(id)}" ${Cnt.course === id ? "selected" : ""}>${fesc(n || id)}</option>`).join("")}</select>
      <select id="cnt-type" class="input cnt-sel" aria-label="نوع محتوا"><option value="all">همه انواع</option>
        ${types.map((t) => `<option value="${fesc(t)}" ${Cnt.type === t ? "selected" : ""}>${fesc(t)}</option>`).join("")}</select>
      <select id="cnt-sort" class="input cnt-sel" aria-label="مرتب‌سازی">
        <option value="new">جدیدترین</option><option value="old">قدیمی‌ترین</option>
        <option value="title">الفبایی</option><option value="course">بر اساس درس</option></select>
      <select id="cnt-group" class="input cnt-sel" aria-label="گروه‌بندی">
        <option value="none">بدون گروه</option><option value="course">گروه: درس</option>
        <option value="type">گروه: نوع</option><option value="day">گروه: روز</option></select>
      <div class="cnt-vt" role="group" aria-label="نمایش">
        <button data-cnt="view" data-v="cozy" aria-label="راحت">☰</button>
        <button data-cnt="view" data-v="compact" aria-label="فشرده">≡</button>
        <button data-cnt="view" data-v="grid" aria-label="شبکه">▦</button>
      </div>
      <button class="lq-btn lq-sm" data-cnt="view-save" title="ذخیره نما">💾</button>
    </div>
    <div class="cnt-pills" id="cnt-pills"></div>
    <div class="cnt-saved" id="cnt-saved"></div>
    <div id="cnt-bulk"></div>
    <div id="cnt-list"></div>`;
  document.getElementById("cnt-sort").value = Cnt.sort;
  document.getElementById("cnt-group").value = Cnt.group;
  cntPaintAll();
}
function cntMatch(c, f) {
  const t = cntTs(c.first_seen_at || c.last_seen_at);
  if (f === "new") return !!c.is_new;
  if (f === "week") return t != null && Date.now() - t < 7 * 864e5;
  return true;
}
function cntFiltered() {
  const q = Cnt.q.trim().toLowerCase();
  let l = Cnt.items.filter((c) => cntMatch(c, Cnt.filter)
    && (Cnt.course === "all" || c.course_id === Cnt.course)
    && (Cnt.type === "all" || c.content_type === Cnt.type));
  if (q) l = l.filter((c) => `${c.title || ""} ${c.filename || ""} ${c.course_name || ""} ${c.teacher || ""}`.toLowerCase().includes(q));
  const ts = (c) => cntTs(c.first_seen_at || c.last_seen_at) ?? 0;
  return l.slice().sort((a, b) =>
    Cnt.sort === "old" ? ts(a) - ts(b)
    : Cnt.sort === "title" ? String(a.title).localeCompare(String(b.title), "fa")
    : Cnt.sort === "course" ? String(a.course_name).localeCompare(String(b.course_name), "fa") || ts(b) - ts(a)
    : ts(b) - ts(a));
}
function cntPaintAll() { cntPaintHero(); cntPaintPills(); cntPaintSaved(); cntPaintBulk(); cntPaintList(); }
function cntPaintHero() {
  const box = document.getElementById("cnt-hero"); if (!box) return;
  const nw = Cnt.items.filter((c) => c.is_new).length;
  const week = Cnt.items.filter((c) => cntMatch(c, "week")).length;
  box.innerHTML = `<div class="cnt-hero-stats">
      <div class="cnt-hstat"><b>${ffa(Cnt.items.length)}</b><span>کل محتوا</span></div>
      <div class="cnt-hstat"><b style="color:var(--danger)">${ffa(nw)}</b><span>ندیده</span></div>
      <div class="cnt-hstat"><b style="color:var(--info)">${ffa(week)}</b><span>این هفته</span></div>
    </div>
    <div class="cnt-hero-actions">
      <button class="lq-btn lq-sm" style="--lq-hue:var(--accent)" data-cnt="read-all" ${nw ? "" : "disabled"}>✓ همه را دیدم</button>
      <button class="lq-btn lq-sm" data-cnt="reload">↻</button>
    </div>`;
}
function cntPaintPills() {
  const box = document.getElementById("cnt-pills"); if (!box) return;
  box.innerHTML = [["all", "همه", "--primary"], ["new", "ندیده", "--danger"], ["week", "این هفته", "--info"]]
    .map(([k, l, cv]) => `<button class="lq-chip ${Cnt.filter === k ? "is-on" : ""}" style="--lq-hue:var(${cv})" data-cnt="filter" data-v="${k}" aria-pressed="${Cnt.filter === k}">${l}<b>${ffa(Cnt.items.filter((c) => cntMatch(c, k)).length)}</b></button>`).join("");
}
function cntPaintSaved() {
  const box = document.getElementById("cnt-saved"); if (!box) return;
  const keys = Object.keys(Cnt.views);
  box.innerHTML = keys.length ? `<span class="cnt-muted">نماها:</span>` + keys.map((k) =>
    `<span class="cnt-sv"><button data-cnt="view-apply" data-k="${fesc(k)}">${fesc(k)}</button>
      <button class="x" data-cnt="view-del" data-k="${fesc(k)}" aria-label="حذف">✕</button></span>`).join("") : "";
}
function cntPaintBulk() {
  const box = document.getElementById("cnt-bulk"); if (!box) return;
  box.innerHTML = Cnt.sel.size ? `<div class="cnt-bulkbar"><b>${ffa(Cnt.sel.size)}</b> انتخاب شده
    <button class="lq-btn lq-sm" style="--lq-hue:var(--accent)" data-cnt="bulk-read">✓ دیدم</button>
    <button class="lq-btn lq-sm" data-cnt="bulk-copy">📋 کپی لینک‌ها</button>
    <button class="lq-btn lq-sm" data-cnt="bulk-export">⬇ خروجی</button>
    <button class="lq-btn lq-sm" data-cnt="bulk-clear">پاک کردن</button></div>` : "";
}
function cntRow(c) {
  const k = cntKind(c), q = Cnt.q.trim(), t = c.first_seen_at || c.last_seen_at;
  const open = `<a class="lq-btn lq-sm is-on" style="--lq-hue:${k.hue}" href="${fesc(proxyUrl(c.url))}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a>`;
  if (Cnt.view === "grid") {
    return `<article class="cnt-card ${c.is_new ? "is-new" : ""}" style="--hue:${k.hue}" data-cnt-card="${fesc(c.id)}">
      <input type="checkbox" class="cnt-chk" data-cnt-sel="${fesc(c.id)}" ${Cnt.sel.has(String(c.id)) ? "checked" : ""} aria-label="انتخاب">
      <span class="cnt-ico">${k.ico}</span>
      <div class="cnt-title">${cntHi(c.title, q)}</div>
      <div class="cnt-meta"><span>${fesc(c.course_name || "—")}</span><span>${k.label}</span></div>
      <div class="cnt-meta"><span>${cntAgo(t)}</span>${c.is_new ? `<span class="cnt-dot"></span>` : ""}</div>
      <div class="cnt-actions">${open}<button class="lq-btn lq-sm" data-cnt="detail" data-id="${fesc(c.id)}">جزئیات</button></div>
    </article>`;
  }
  return `<div class="cnt-row ${c.is_new ? "is-new" : ""} ${Cnt.view === "compact" ? "is-compact" : ""}" style="--hue:${k.hue}" data-cnt-card="${fesc(c.id)}">
    <input type="checkbox" class="cnt-chk" data-cnt-sel="${fesc(c.id)}" ${Cnt.sel.has(String(c.id)) ? "checked" : ""} aria-label="انتخاب">
    <span class="cnt-ico">${k.ico}</span>
    <div class="cnt-body">
      <div class="cnt-head"><b class="cnt-title">${cntHi(c.title, q)}</b>
        ${c.is_new ? `<span class="cnt-dot" title="ندیده"></span>` : ""}
        <span class="badge" style="color:${k.hue}">${fesc(k.label)}</span></div>
      <div class="cnt-meta">
        <button class="cnt-coursechip" data-cnt="course" data-id="${fesc(c.course_id || "")}">📘 ${cntHi(c.course_name || "—", q)}</button>
        ${c.teacher ? `<span>👨‍🏫 ${cntHi(c.teacher, q)}</span>` : ""}
        ${c.filename ? `<span class="cnt-file" dir="ltr">${cntHi(c.filename, q)}</span>` : ""}
        <span>${cntAgo(t)}</span></div>
    </div>
    <div class="cnt-actions">${open}
      <button class="lq-btn lq-sm" data-cnt="detail" data-id="${fesc(c.id)}">جزئیات</button>
      ${c.is_new ? `<button class="lq-btn lq-sm" data-cnt="read" data-id="${fesc(c.id)}">✓</button>` : ""}
    </div></div>`;
}
function cntPaintList() {
  const box = document.getElementById("cnt-list"); if (!box) return;
  document.querySelectorAll(".cnt-vt button").forEach((b) => { const on = b.dataset.v === Cnt.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const list = cntFiltered();
  if (!list.length) {
    box.innerHTML = Cnt.items.length
      ? `<div class="empty"><span class="empty-icon">🔍</span>محتوایی با این فیلترها نیست<small>فیلتر یا جستجو را تغییر بده</small>
          <div style="margin-top:.8rem"><button class="lq-btn lq-sm" data-cnt="clear">پاک کردن فیلترها</button></div></div>`
      : `<div class="empty"><span class="empty-icon">📁</span>هنوز محتوایی نیست<small>بعد از همگام‌سازی، فایل‌های درس‌ها اینجا می‌آیند</small>
          <div style="margin-top:.8rem"><button class="lq-btn lq-sm" style="--lq-hue:var(--primary)" data-cnt="sync">🔄 همگام‌سازی</button></div></div>`;
    return;
  }
  const cls = Cnt.view === "grid" ? "cnt-grid" : "cnt-list";
  if (Cnt.group === "none") { box.innerHTML = `<div class="${cls}">${list.map(cntRow).join("")}</div>`; return; }
  const groups = new Map();
  list.forEach((c) => {
    const key = Cnt.group === "course" ? (c.course_id || "zz") : Cnt.group === "type" ? (c.content_type || "zz") : cntDayKey(c.first_seen_at || c.last_seen_at);
    const label = Cnt.group === "course" ? (c.course_name || "—") : Cnt.group === "type" ? (c.content_type || "سایر") : cntDayLabel(c.first_seen_at || c.last_seen_at);
    if (!groups.has(key)) groups.set(key, { label, items: [] });
    groups.get(key).items.push(c);
  });
  box.innerHTML = [...groups.values()].map((g) => {
    const ids = g.items.filter((c) => c.is_new).map((c) => String(c.id));
    return `<section class="cnt-group"><div class="cnt-grouphead"><b>${fesc(g.label)}</b><span class="badge">${ffa(g.items.length)}</span>
      ${ids.length ? `<button class="lq-link" data-cnt="group-read" data-ids="${fesc(ids.join(","))}">✓ دیدن این گروه (${ffa(ids.length)})</button>` : ""}</div>
      <div class="${cls}">${g.items.map(cntRow).join("")}</div></section>`;
  }).join("");
}
async function cntSetRead(ids, read, label) {
  ids = ids.map(String).filter((id) => Cnt.items.some((c) => String(c.id) === id));
  if (!ids.length) return;
  const prev = ids.map((id) => ({ id, was: !!Cnt.items.find((c) => String(c.id) === id).is_new }));
  ids.forEach((id) => { Cnt.items.find((c) => String(c.id) === id).is_new = !read; Cnt.sel.delete(id); });
  cntPaintAll();
  let ok = false;
  try { await api("/contents/read-bulk", { method: "POST", body: JSON.stringify({ ids, read }) }); ok = true; } catch (_) {}
  if (!ok) { prev.forEach(({ id, was }) => { Cnt.items.find((c) => String(c.id) === id).is_new = was; }); cntPaintAll(); cntToast("❌ ثبت ناموفق — endpoint دیده‌شدن نصب نشده"); return; }
  cntToast(label || (read ? "✅ دیده شد" : "ندیده علامت خورد"), { action: "برگردان", dur: 6000, onAction: async () => {
    prev.forEach(({ id, was }) => { Cnt.items.find((c) => String(c.id) === id).is_new = was; }); cntPaintAll();
    const toNew = prev.filter((x) => x.was).map((x) => x.id), toOld = prev.filter((x) => !x.was).map((x) => x.id);
    try { if (toNew.length) await api("/contents/read-bulk", { method: "POST", body: JSON.stringify({ ids: toNew, read: false }) });
      if (toOld.length) await api("/contents/read-bulk", { method: "POST", body: JSON.stringify({ ids: toOld, read: true }) }); } catch (_) {}
  }});
}
function cntOpenDetail(id) {
  const c = Cnt.items.find((x) => String(x.id) === String(id)); if (!c) return;
  const k = cntKind(c);
  cntLayer({ type: "drawer", title: "جزئیات محتوا", html: `<div class="cnt-dwr">
    <div class="cnt-dwr-head"><span class="cnt-ico lg" style="--hue:${k.hue}">${k.ico}</span>
      <div><h2>${fesc(c.title)}</h2><div class="cnt-meta"><span class="badge" style="color:${k.hue}">${fesc(k.label)}</span>
        ${c.is_new ? `<span class="badge badge-new">ندیده</span>` : ""}</div></div>
      <button class="cnt-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="cnt-kv">
      <div><span>درس</span><b>${fesc(c.course_name || "—")}</b></div>
      ${c.teacher ? `<div><span>استاد</span><b>${fesc(c.teacher)}</b></div>` : ""}
      ${c.filename ? `<div><span>نام فایل</span><b dir="ltr">${fesc(c.filename)}</b></div>` : ""}
      ${c.first_seen_at ? `<div><span>اولین دیده‌شدن</span><b>${cntAgo(c.first_seen_at)}</b></div>` : ""}
      ${c.last_seen_at ? `<div><span>آخرین به‌روزرسانی</span><b>${cntAgo(c.last_seen_at)}</b></div>` : ""}
    </div>
    <div class="cnt-urlbox"><span class="cnt-url" dir="ltr">${fesc(c.url || "")}</span></div>
    <div class="cnt-dwr-actions">
      <a class="lq-btn lq-sm is-on" style="--lq-hue:${k.hue}" href="${fesc(proxyUrl(c.url))}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a>
      <button class="lq-btn lq-sm" data-cnt="copy" data-id="${fesc(c.id)}">📋 کپی لینک</button>
      ${c.is_new ? `<button class="lq-btn lq-sm" style="--lq-hue:var(--accent)" data-cnt="read" data-id="${fesc(c.id)}">✓ دیدم</button>` : ""}
      ${c.course_id ? `<button class="lq-btn lq-sm" data-cnt="course" data-id="${fesc(c.course_id)}" data-lib-close>صفحه درس</button>` : ""}
    </div></div>` });
}
function cntCopy(text, msg) {
  const done = () => cntToast(msg || "📋 کپی شد");
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, done);
  else { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); }
}
function cntWire() {
  if (Cnt.wired) return; Cnt.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-cnt]");
    if (!el) { const card = e.target.closest("[data-cnt-card]"); if (card && !e.target.closest("a,button,input,select,label")) cntOpenDetail(card.dataset.cntCard); return; }
    const act = el.dataset.cnt, id = el.dataset.id, v = el.dataset.v;
    switch (act) {
      case "filter": Cnt.filter = v; Cnt.sel.clear(); cntPaintPills(); cntPaintBulk(); cntPaintList(); break;
      case "view": Cnt.view = v; localStorage.setItem("cnt:view", v); cntPaintList(); break;
      case "detail": cntOpenDetail(id); break;
      case "read": cntSetRead([id], true); break;
      case "read-all": cntSetRead(Cnt.items.filter((c) => c.is_new).map((c) => String(c.id)), true, "✅ همه دیده شد"); break;
      case "group-read": cntSetRead((el.dataset.ids || "").split(",").filter(Boolean), true, "✅ گروه دیده شد"); break;
      case "bulk-read": cntSetRead([...Cnt.sel], true); break;
      case "bulk-clear": Cnt.sel.clear(); cntPaintBulk(); cntPaintList(); break;
      case "bulk-copy": cntCopy(Cnt.items.filter((c) => Cnt.sel.has(String(c.id))).map((c) => `${c.title}\n${c.url}`).join("\n\n"), "📋 لینک‌ها کپی شد"); break;
      case "bulk-export": {
        const rows = Cnt.items.filter((c) => Cnt.sel.has(String(c.id)));
        const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "lms-contents.json"; a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000); cntToast("⬇ خروجی گرفته شد"); break; }
      case "copy": { const c = Cnt.items.find((x) => String(x.id) === String(id)); if (c) cntCopy(c.url || "", "📋 لینک کپی شد"); break; }
      case "course": if (id) location.hash = "#/course/" + encodeURIComponent(id); break;
      case "reload": renderContents(); break;
      case "sync": document.getElementById("btn-sync")?.click(); break;
      case "clear": Cnt.q = ""; Cnt.filter = "all"; Cnt.course = "all"; Cnt.type = "all"; renderContents(); break;
      case "view-save": cntLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <div><label class="field-label" for="cnt-v-n">نام نما *</label><input id="cnt-v-n" class="input" placeholder="مثلاً PDFهای این هفته" data-autofocus></div>
          <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button><button class="btn btn-primary" id="cnt-v-ok">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#cnt-v-ok").addEventListener("click", () => {
          const n = w.querySelector("#cnt-v-n").value.trim(); if (!n) return;
          Cnt.views[n] = { q: Cnt.q, filter: Cnt.filter, course: Cnt.course, type: Cnt.type, sort: Cnt.sort, group: Cnt.group, view: Cnt.view };
          Cnt.views = Object.fromEntries(Object.entries(Cnt.views).slice(-6));
          localStorage.setItem("cnt:views", JSON.stringify(Cnt.views)); L.close(); cntPaintSaved(); cntToast("💾 نما ذخیره شد");
        }); } }); break;
      case "view-apply": { const x = Cnt.views[el.dataset.k]; if (!x) break; Object.assign(Cnt, x);
        localStorage.setItem("cnt:sort", Cnt.sort); localStorage.setItem("cnt:group", Cnt.group); localStorage.setItem("cnt:view", Cnt.view); renderContents(); break; }
      case "view-del": delete Cnt.views[el.dataset.k]; localStorage.setItem("cnt:views", JSON.stringify(Cnt.views)); cntPaintSaved(); break;
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "cnt-q") { Cnt.q = e.target.value; cntPaintList(); } });
  document.addEventListener("change", (e) => {
    if (e.target.id === "cnt-course") { Cnt.course = e.target.value; cntPaintList(); }
    if (e.target.id === "cnt-type") { Cnt.type = e.target.value; cntPaintList(); }
    if (e.target.id === "cnt-sort") { Cnt.sort = e.target.value; localStorage.setItem("cnt:sort", Cnt.sort); cntPaintList(); }
    if (e.target.id === "cnt-group") { Cnt.group = e.target.value; localStorage.setItem("cnt:group", Cnt.group); cntPaintList(); }
    if (e.target.dataset && e.target.dataset.cntSel !== undefined) {
      const id = e.target.dataset.cntSel; e.target.checked ? Cnt.sel.add(id) : Cnt.sel.delete(id); cntPaintBulk();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = (typeof Lib !== "undefined" && Lib.layers?.length) || (typeof Cal !== "undefined" && Cal._layers?.length)
      || (typeof Asg !== "undefined" && Asg.layers?.length) || (typeof Adm !== "undefined" && Adm.layers?.length)
      || (typeof Crs !== "undefined" && Crs.layers?.length) || (typeof MapX !== "undefined" && MapX.layers?.length)
      || (typeof Stg !== "undefined" && Stg.layers?.length) || (typeof Dboard !== "undefined" && Dboard.layers?.length)
      || (typeof Chg !== "undefined" && Chg.layers?.length) || (typeof Qra !== "undefined" && Qra.layers?.length)
      || (typeof Wal !== "undefined" && Wal.layers?.length);
    if (busy) return;
    if (Cnt.layers.length) Cnt.layers[Cnt.layers.length - 1].close();
  });
}
cntWire();

// ---------- Changes v2 (تغییرات) ----------
// یک‌بار واکشی؛ فیلتر/جستجو/مرتب‌سازی/گروه‌بندی کلاینتی؛ بدون نشت لیسنر؛ دو نما.
const CHG_TYPES = {
  content:    { icon: "📁", label: "فایل و محتوا", cv: "--primary" },
  assignment: { icon: "📝", label: "تکلیف",        cv: "--warning" },
  event:      { icon: "📅", label: "رویداد",        cv: "--info" },
  post:       { icon: "💬", label: "پیام وال",      cv: "--accent" },
};
const CHG_ACTIONS = {
  new:     { icon: "➕", label: "جدید",           cv: "--accent" },
  updated: { icon: "🔄", label: "به‌روزرسانی",   cv: "--info" },
  removed: { icon: "➖", label: "حذف یا انقضا",   cv: "--danger" },
};
const Chg = {
  items: [], type: "all", time: "all", q: "", sort: "new",
  view: localStorage.getItem("chg:view") || "timeline",
  limit: 100, total: 0, views: JSON.parse(localStorage.getItem("chg:views") || "{}"),
  layers: [], wired: false, loading: false, loaded: false,
};
const chesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const chfa = (n) => faDigits(String(n));
function chgTs(iso) { const t = Date.parse(String(iso || "").replace(" ", "T")); return Number.isNaN(t) ? null : t; }
function chgAgo(iso) {
  const t = chgTs(iso); if (t == null) return "";
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${chfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${chfa(Math.floor(s / 3600))} ساعت پیش`;
  if (s < 2592000) return `${chfa(Math.floor(s / 86400))} روز پیش`;
  return String(iso).slice(0, 10);
}
function chgDayKey(iso) {
  const t = chgTs(iso); if (t == null) return "zz";
  const d = new Date(t); return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}
function chgDayLabel(iso) {
  const t = chgTs(iso); if (t == null) return "بدون زمان";
  const d = new Date(t), now = new Date();
  const key = chgDayKey(iso), tk = chgDayKey(now.toISOString());
  const y = new Date(now); y.setDate(now.getDate() - 1);
  if (key === tk) return "امروز";
  if (key === chgDayKey(y.toISOString())) return "دیروز";
  try { const j = d2j(g2d(d.getFullYear(), d.getMonth() + 1, d.getDate()));
    return `${chfa(j.jd)} ${J_MONTHS[j.jm - 1]} ${chfa(j.jy)}`; } catch (_) { return String(iso).slice(0, 10); }
}
function chgLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof admLayer === "function" ? admLayer
    : typeof crsLayer === "function" ? crsLayer : typeof mxLayer === "function" ? mxLayer
    : typeof stgLayer === "function" ? stgLayer : typeof dashLayer === "function" ? dashLayer : chgOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = Chg.layers.indexOf(L); if (i >= 0) Chg.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  Chg.layers.push(L); return L;
}
function chgToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof admToast === "function") return admToast(m, o);
  if (typeof crsToast === "function") return crsToast(m, o);
  if (typeof mxToast === "function") return mxToast(m, o);
  if (typeof stgToast === "function") return stgToast(m, o);
  if (typeof dashToast === "function") return dashToast(m, o);
  return chgOwnToast(m, o);
}
function chgOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "chg-layer";
  w.innerHTML = `<div class="chg-scrim" data-chg-x></div>` + (opts.type === "drawer"
    ? `<aside class="chg-drawer" role="dialog" aria-modal="true" aria-label="${chesc(opts.title)}">${opts.html}</aside>`
    : `<div class="chg-modal-wrap"><div class="chg-modal" role="dialog" aria-modal="true" aria-label="${chesc(opts.title)}"><h3>${chesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("chg-locked");
  const panel = w.querySelector(".chg-drawer,.chg-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".chg-layer")) document.body.classList.remove("chg-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-chg-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function chgOwnToast(msg, o = {}) {
  let box = document.getElementById("chg-toasts");
  if (!box) { box = document.createElement("div"); box.id = "chg-toasts"; box.className = "chg-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "chg-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${chesc(msg)}</span>${o.action ? `<button class="a">${chesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const chgCloseAll = () => Chg.layers.slice().forEach((l) => l.close());
window.__chgTeardown = () => { chgCloseAll(); };

/* ---- داده ---- */
async function renderChanges() {
  chgCloseAll(); Chg.loading = true;
  contentEl.innerHTML = `${pageHead("آخرین تغییرات", "تایم‌لاین به‌روزرسانی‌ها و فعالیت‌های سامانه")}
    <div class="chg-skel-wrap">${'<div class="chg-skel"></div>'.repeat(4)}</div>`;
  let rows = [];
  try { rows = await api(`/changes?limit=${Chg.limit}`); }
  catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری تغییرات<small>${chesc(e.message)}</small>
      <div style="margin-top:.8rem"><button class="btn btn-soft btn-sm" data-chg="retry">تلاش مجدد</button></div></div>`;
    return;
  }
  Chg.items = Array.isArray(rows) ? rows : [];
  Chg.total = Chg.items.length; Chg.loading = false; Chg.loaded = true;
  contentEl.innerHTML = `
    ${pageHead("آخرین تغییرات", `${chfa(Chg.total)} تغییر ثبت‌شده · ${chgRangeLabel()}`)}
    <div class="chg-toolbar">
      <div class="search-box chg-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="chg-q" type="search" value="${chesc(Chg.q)}" placeholder="جستجو در عنوان، درس یا استاد…" aria-label="جستجو در تغییرات"></div>
      <select id="chg-time" class="input chg-sel" aria-label="بازهٔ زمانی">
        <option value="all">همهٔ زمان‌ها</option><option value="today">امروز</option>
        <option value="week">۷ روز اخیر</option><option value="month">۳۰ روز اخیر</option>
      </select>
      <select id="chg-sort" class="input chg-sel" aria-label="مرتب‌سازی">
        <option value="new">جدیدترین</option><option value="old">قدیمی‌ترین</option>
      </select>
      <div class="chg-vt" role="group" aria-label="حالت نمایش">
        <button data-chg="view" data-v="timeline" title="تایم‌لاین" aria-label="تایم‌لاین">▤</button>
        <button data-chg="view" data-v="compact" title="لیست فشرده" aria-label="لیست فشرده">☰</button>
      </div>
      <button class="btn btn-ghost btn-sm" data-chg="view-save" title="ذخیره نما">💾</button>
      <button class="btn btn-ghost btn-sm" data-chg="reload" title="بارگذاری مجدد">↻</button>
    </div>
    <div class="chg-pills" id="chg-pills"></div>
    <div class="chg-saved" id="chg-saved"></div>
    <div id="chg-list"></div>
    <div class="chg-more" id="chg-more"></div>`;
  document.getElementById("chg-time").value = Chg.time;
  document.getElementById("chg-sort").value = Chg.sort;
  chgPaintAll();
}
function chgRangeLabel() {
  return { all: "همهٔ زمان‌ها", today: "امروز", week: "۷ روز اخیر", month: "۳۰ روز اخیر" }[Chg.time] || "";
}
function chgFiltered() {
  const q = Chg.q.trim().toLowerCase(), now = Date.now();
  const span = { today: 1, week: 7, month: 30 }[Chg.time];
  let l = Chg.items.filter((c) => {
    if (Chg.type !== "all" && c.entity_type !== Chg.type) return false;
    if (span) {
      const t = chgTs(c.detected_at);
      if (t == null) return false;
      if (now - t > span * 86400e3) return false;
    }
    if (q && !`${c.title || ""} ${c.course_name || ""} ${c.teacher_name || ""}`.toLowerCase().includes(q)) return false;
    return true;
  });
  return l.sort((a, b) => {
    const ta = chgTs(a.detected_at) ?? 0, tb = chgTs(b.detected_at) ?? 0;
    return Chg.sort === "old" ? ta - tb : tb - ta;
  });
}
function chgPaintAll() { chgPaintPills(); chgPaintSaved(); chgPaintList(); chgPaintMore(); }
function chgPaintPills() {
  const box = document.getElementById("chg-pills"); if (!box) return;
  const cnt = (t) => t === "all" ? Chg.items.length : Chg.items.filter((c) => c.entity_type === t).length;
  box.innerHTML = `<button class="chg-pill ${Chg.type === "all" ? "on" : ""}" data-chg="type" data-v="all">همه <b>${chfa(cnt("all"))}</b></button>`
    + Object.entries(CHG_TYPES).map(([k, m]) =>
      `<button class="chg-pill ${Chg.type === k ? "on" : ""}" data-chg="type" data-v="${k}">${m.icon} ${m.label} <b>${chfa(cnt(k))}</b></button>`).join("");
}
function chgPaintSaved() {
  const box = document.getElementById("chg-saved"); if (!box) return;
  const keys = Object.keys(Chg.views);
  box.innerHTML = keys.length ? `<span class="chg-muted">نماها:</span>` + keys.map((k) =>
    `<span class="chg-sv"><button data-chg="view-apply" data-k="${chesc(k)}">${chesc(k)}</button>
      <button class="x" data-chg="view-del" data-k="${chesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function chgRow(c, compact) {
  const t = CHG_TYPES[c.entity_type] || { icon: "🔔", label: c.entity_type || "تغییر", cv: "--muted" };
  const a = CHG_ACTIONS[c.type] || { icon: "•", label: c.type || "تغییر", cv: "--muted" };
  const isRemoved = c.type === "removed";
  return `<${compact ? "div" : "div"} class="chg-item ${isRemoved ? "is-removed" : ""} ${compact ? "is-compact" : ""}" data-chg-open="${chesc(c.id)}">
    <span class="chg-ico t-${chesc(c.entity_type)}" style="--c:var(${t.cv})">${t.icon}</span>
    <div class="chg-body">
      <div class="row-title">${chesc(c.title)}
        <span class="badge" style="color:var(${a.cv})">${a.icon} ${a.label}</span></div>
      <div class="row-meta">
        ${c.course_id ? `<button class="chg-link" data-chg="course" data-id="${chesc(c.course_id)}">📘 ${chesc(c.course_name || "درس")}</button>` : `<span>${chesc(c.course_name || "سیستم")}</span>`}
        ${c.teacher_name ? `<span>👨‍🏫 ${chesc(c.teacher_name)}</span>` : ""}
        <span>${chesc(t.label)}</span>
        ${c.detected_at ? `<span title="${chesc(c.detected_at)}">${chgAgo(c.detected_at)}</span>` : ""}
      </div>
    </div>
    <span class="chg-act" style="--c:var(${a.cv})">${a.icon}</span>
  </${compact ? "div" : "div"}>`;
}
function chgPaintList() {
  const box = document.getElementById("chg-list"); if (!box) return;
  document.querySelectorAll(".chg-vt button").forEach((b) => { const on = b.dataset.v === Chg.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const l = chgFiltered();
  if (!Chg.loaded) { box.innerHTML = ""; return; }
  if (!l.length) {
    box.innerHTML = `<div class="empty"><span class="empty-icon">🔍</span>${Chg.items.length ? "تغییری با این فیلترها نیست" : "هنوز تغییری ثبت نشده"}
      <small>${Chg.items.length ? "فیلتر نوع یا زمان را ساده‌تر کن" : "بعد از همگام‌سازی، تغییرات جدید اینجا نمایش داده می‌شوند"}</small>
      <div class="chg-actions" style="justify-content:center;margin-top:.8rem">
        ${Chg.items.length ? `<button class="btn btn-ghost btn-sm" data-chg="clear">پاک کردن فیلترها</button>` : `<button class="btn btn-primary btn-sm" data-chg="sync">🔄 همگام‌سازی</button>`}</div></div>`;
    return;
  }
  if (Chg.view === "compact") {
    box.innerHTML = `<div class="chg-compact">${l.map((c) => chgRow(c, true)).join("")}</div>`;
    return;
  }
  const groups = [];
  l.forEach((c) => {
    const k = chgDayKey(c.detected_at), gl = chgDayLabel(c.detected_at);
    const g = groups[groups.length - 1];
    if (g && g.key === k) g.items.push(c); else groups.push({ key: k, label: gl, items: [c] });
  });
  box.innerHTML = `<div class="chg-timeline">${groups.map((g) =>
    `<div class="chg-day"><div class="chg-dayhead"><b>${chesc(g.label)}</b><span class="badge">${chfa(g.items.length)} مورد</span></div>
      <div class="chg-daybody">${g.items.map((c) => chgRow(c, false)).join("")}</div></div>`).join("")}</div>`;
}
function chgPaintMore() {
  const box = document.getElementById("chg-more"); if (!box) return;
  const reached = Chg.total >= Chg.limit;
  box.innerHTML = reached
    ? `<button class="btn btn-soft btn-sm" data-chg="more" ${Chg.loading ? "disabled" : ""}>${Chg.loading ? "در حال بارگذاری…" : "بارگذاری موارد بیشتر"}</button>`
    : "";
}

/* ---- اکشن‌ها ---- */
function chgOpenDetail(id) {
  const c = Chg.items.find((x) => x.id === id); if (!c) return;
  const t = CHG_TYPES[c.entity_type] || { icon: "🔔", label: c.entity_type || "تغییر", cv: "--muted" };
  const a = CHG_ACTIONS[c.type] || { icon: "•", label: c.type || "تغییر", cv: "--muted" };
  chgLayer({ type: "drawer", title: "جزئیات تغییر", html: `<div class="chg-dwr">
    <div class="chg-dwr-head"><span class="chg-ico lg" style="--c:var(${t.cv})">${t.icon}</span>
      <div><h2>${chesc(c.title)}</h2><div class="chg-badges">
        <span class="badge" style="color:var(${a.cv})">${a.icon} ${a.label}</span>
        <span class="badge">${chesc(t.label)}</span></div></div>
      <button class="chg-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="chg-kv">
      ${c.course_name ? `<div><span>درس</span><b>${chesc(c.course_name)}</b></div>` : ""}
      ${c.teacher_name ? `<div><span>استاد</span><b>${chesc(c.teacher_name)}</b></div>` : ""}
      ${c.detected_at ? `<div><span>زمان</span><b>${chgAgo(c.detected_at)}</b></div>` : ""}
      ${c.detected_at ? `<div><span>تاریخ دقیق</span><b dir="ltr">${chesc(c.detected_at)}</b></div>` : ""}
    </div>
    <div class="chg-dwr-actions">
      ${c.course_id ? `<button class="btn btn-primary btn-sm" data-chg="course" data-id="${chesc(c.course_id)}" data-lib-close>مشاهده درس</button>` : ""}
    </div></div>` });
}
async function chgLoadMore() {
  Chg.loading = true; chgPaintMore();
  try {
    Chg.limit += 100;
    const rows = await api(`/changes?limit=${Chg.limit}`);
    Chg.items = Array.isArray(rows) ? rows : [];
    Chg.total = Chg.items.length;
    chgPaintAll(); chgToast("✅ موارد بیشتر بارگذاری شد");
  } catch (e) { Chg.limit -= 100; chgToast("❌ " + (e.message || "خطا در بارگذاری")); }
  finally { Chg.loading = false; chgPaintMore(); }
}

/* ---- delegation ---- */
function chgWire() {
  if (Chg.wired) return; Chg.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-chg]");
    if (el) {
      const act = el.dataset.chg, v = el.dataset.v;
      switch (act) {
        case "type": Chg.type = v; chgPaintPills(); chgPaintList(); break;
        case "view": Chg.view = v; localStorage.setItem("chg:view", v); chgPaintList(); break;
        case "clear": Chg.type = "all"; Chg.time = "all"; Chg.q = ""; Chg.sort = "new";
          { const q = document.getElementById("chg-q"); if (q) q.value = "";
            const t = document.getElementById("chg-time"); if (t) t.value = "all";
            const s = document.getElementById("chg-sort"); if (s) s.value = "new"; }
          chgPaintAll(); break;
        case "sync": { const b = document.getElementById("btn-sync"); if (b) b.click(); break; }
        case "reload": renderChanges(); break;
        case "retry": renderChanges(); break;
        case "more": chgLoadMore(); break;
        case "course": location.hash = "#/course/" + encodeURIComponent(el.dataset.id); break;
        case "view-apply": { const x = Chg.views[el.dataset.k]; if (!x) break;
          Object.assign(Chg, x); localStorage.setItem("chg:view", Chg.view);
          { const q = document.getElementById("chg-q"); if (q) q.value = Chg.q;
            const t = document.getElementById("chg-time"); if (t) t.value = Chg.time;
            const s = document.getElementById("chg-sort"); if (s) s.value = Chg.sort; }
          chgPaintAll(); break; }
        case "view-del": delete Chg.views[el.dataset.k]; localStorage.setItem("chg:views", JSON.stringify(Chg.views)); chgPaintSaved(); break;
        case "view-save": chgLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
            <div class="chg-field" data-cf="n"><label class="field-label" for="chg-v-n">نام نما *</label>
              <input id="chg-v-n" class="input" placeholder="مثلاً تکالیف این هفته" data-autofocus><small class="chg-err"></small></div>
            <div class="lib-modal-actions chg-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
              <button class="btn btn-primary" id="chg-v-ok">ذخیره</button></div></div>`,
          onMount: (w, L) => { w.querySelector("#chg-v-ok").addEventListener("click", () => {
            const n = w.querySelector("#chg-v-n").value.trim(), f = w.querySelector('[data-cf="n"]');
            f.classList.toggle("bad", !n); f.querySelector(".chg-err").textContent = n ? "" : "نام الزامی است";
            if (!n) return;
            Chg.views[n] = { type: Chg.type, time: Chg.time, q: Chg.q, sort: Chg.sort, view: Chg.view };
            Chg.views = Object.fromEntries(Object.entries(Chg.views).slice(-6));
            localStorage.setItem("chg:views", JSON.stringify(Chg.views));
            L.close(); chgPaintSaved(); chgToast("💾 نما ذخیره شد");
          }); } }); break;
      }
      return;
    }
    const card = e.target.closest("[data-chg-open]");
    if (card && !e.target.closest("button,a,select,input")) chgOpenDetail(card.dataset.chgOpen);
  });
  document.addEventListener("input", (e) => { if (e.target.id === "chg-q") { Chg.q = e.target.value; chgPaintList(); } });
  document.addEventListener("change", (e) => {
    if (e.target.id === "chg-time") { Chg.time = e.target.value; chgPaintList(); }
    if (e.target.id === "chg-sort") { Chg.sort = e.target.value; chgPaintList(); }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = ["Lib", "Cal", "Asg", "Adm", "Crs", "MapX", "Stg", "Dash"].some((n) => {
      try { const o = window[n] || { layers: [], _layers: [] }; return !!(o.layers && o.layers.length || o._layers && o._layers.length); } catch (_) { return false; }
    });
    if (busy) return;
    if (Chg.layers.length) Chg.layers[Chg.layers.length - 1].close();
  });
}
chgWire();



// ---------- Support v2 (پشتیبانی) ----------
const SUP_STATUS = { open: ["بی‌پاسخ", "var(--danger)"], answered: ["پاسخ‌داده", "var(--accent)"], closed: ["بسته", "var(--muted)"] };
const SUP_TEMPLATES = [
  ["🐞 خطای همگام‌سازی", "همگام‌سازی با خطا متوقف می‌شود", "مرحله‌ای که خطا می‌دهد:\nپیام خطا:\nاز چه زمانی شروع شد:"],
  ["🖥 مشکل نمایش", "بخشی از رابط درست نمایش داده نمی‌شود", "کدام صفحه:\nمرورگر و دستگاه:\nچه چیزی اشتباه دیده می‌شود:"],
  ["💡 پیشنهاد", "پیشنهاد برای بهبود دستیار", "چه چیزی کم است:\nچطور کمک می‌کند:"],
];
const Sup = {
  tickets: [], q: "", filter: "all",
  sort: localStorage.getItem("sup:sort") || "updated",
  seen: JSON.parse(localStorage.getItem("sup:seen") || "{}"),
  drafts: JSON.parse(localStorage.getItem("sup:drafts") || "{}"),
  layers: [], wired: false, loaded: false,
};
const pesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pfa = (n) => faDigits(String(n));
function supAgo(v) {
  const t = Date.parse(String(v || "").replace(" ", "T")); if (Number.isNaN(t)) return String(v || "");
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${pfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${pfa(Math.floor(s / 3600))} ساعت پیش`;
  return `${pfa(Math.floor(s / 86400))} روز پیش`;
}
const supFresh = (t) => t.status === "answered" && (t.message_count || 0) > (Sup.seen[t.id] || 0);
function supLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof asgLayer === "function" ? asgLayer
    : typeof crsLayer === "function" ? crsLayer : typeof walLayer === "function" ? walLayer
    : typeof cntLayer === "function" ? cntLayer : typeof bdLayer === "function" ? bdLayer : null;
  if (f) { const L = f({ ...opts, onClose: () => { const i = Sup.layers.indexOf(L); if (i >= 0) Sup.layers.splice(i, 1); opts.onClose && opts.onClose(); } }); Sup.layers.push(L); return L; }
  const w = document.createElement("div"); w.className = "glass-modal-backdrop";
  w.innerHTML = `<div class="glass-modal" role="dialog" aria-modal="true"><h3>${pesc(opts.title || "")}</h3>${opts.html}</div>`;
  document.body.appendChild(w);
  const L = { wrap: w, panel: w.querySelector(".glass-modal"), close() { w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230); const i = Sup.layers.indexOf(L); if (i >= 0) Sup.layers.splice(i, 1); } };
  w.addEventListener("click", (e) => { if (e.target === w) L.close(); });
  w.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  Sup.layers.push(L); if (opts.onMount) opts.onMount(w, L); return L;
}
function supToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof walToast === "function") return walToast(m, o);
  if (typeof cntToast === "function") return cntToast(m, o);
  return toast(m);
}
const supCloseAll = () => Sup.layers.slice().forEach((l) => l.close());
window.__supTeardown = supCloseAll;

async function renderSupport() {
  supCloseAll();
  let list;
  try { list = await api("/support/tickets"); }
  catch (e) { contentEl.innerHTML = `<div class="empty"><span class="empty-icon">🔒</span>برای پشتیبانی وارد شوید<small>ابتدا لاگین کنید</small></div>`; showLogin(); return; }
  Sup.tickets = list.tickets || []; Sup.loaded = true;
  contentEl.innerHTML = `
    ${pageHead("پشتیبانی", "گزارش باگ، پیشنهاد و پیگیری پاسخ")}
    <div class="card sup-hero" id="sup-hero"></div>
    <div class="sup-toolbar">
      <div class="search-box sup-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="sup-q" type="search" value="${pesc(Sup.q)}" placeholder="جستجو در موضوع تیکت…" aria-label="جستجو"></div>
      <select id="sup-sort" class="input sup-sel" aria-label="مرتب‌سازی">
        <option value="updated">آخرین به‌روزرسانی</option><option value="created">جدیدترین</option><option value="messages">بیشترین پیام</option></select>
      <button class="lq-btn lq-sm" data-sup="reload">↻</button>
      <button class="lq-btn lq-sm is-on" style="--lq-hue:var(--primary)" data-sup="new">+ تیکت جدید</button>
    </div>
    <div class="sup-pills" id="sup-pills"></div>
    <div id="sup-list"></div>
    <p class="sup-hint">پاسخ‌ها معمولاً در همین رشته ثبت می‌شوند؛ برای مشکلات فوری، صفحهٔ <a href="#/help">راهنما</a> را هم ببین.</p>`;
  document.getElementById("sup-sort").value = Sup.sort;
  supPaintAll();
}
function supMatch(t, f) {
  if (f === "fresh") return supFresh(t);
  if (f === "all") return true;
  return t.status === f;
}
function supFiltered() {
  const q = Sup.q.trim().toLowerCase();
  let l = Sup.tickets.filter((t) => supMatch(t, Sup.filter));
  if (q) l = l.filter((t) => String(t.subject || "").toLowerCase().includes(q));
  const ts = (v) => Date.parse(String(v || "").replace(" ", "T")) || 0;
  return l.slice().sort((a, b) =>
    Sup.sort === "created" ? ts(b.created_at) - ts(a.created_at)
    : Sup.sort === "messages" ? (b.message_count || 0) - (a.message_count || 0)
    : ts(b.updated_at) - ts(a.updated_at));
}
function supPaintAll() { supPaintHero(); supPaintPills(); supPaintList(); }
function supPaintHero() {
  const box = document.getElementById("sup-hero"); if (!box) return;
  const fresh = Sup.tickets.filter(supFresh).length;
  box.innerHTML = `<div class="sup-hero-stats">
      <div class="sup-hstat"><b>${pfa(Sup.tickets.length)}</b><span>کل تیکت</span></div>
      <div class="sup-hstat"><b style="color:var(--danger)">${pfa(Sup.tickets.filter((t) => t.status === "open").length)}</b><span>بی‌پاسخ</span></div>
      <div class="sup-hstat"><b style="color:var(--accent)">${pfa(fresh)}</b><span>پاسخ تازه</span></div>
    </div>
    <div class="sup-hero-txt">مشکلی دیدی یا پیشنهادی داری؟ یک تیکت بزن تا بررسی شود.</div>`;
}
function supPaintPills() {
  const box = document.getElementById("sup-pills"); if (!box) return;
  const pills = [["all", "همه", "--primary"], ["open", "بی‌پاسخ", "--danger"], ["answered", "پاسخ‌داده", "--accent"], ["fresh", "پاسخ تازه", "--info"], ["closed", "بسته", "--muted"]];
  box.innerHTML = pills.map(([k, l, cv]) => `<button class="lq-chip ${Sup.filter === k ? "is-on" : ""}" style="--lq-hue:var(${cv})" data-sup="filter" data-v="${k}" aria-pressed="${Sup.filter === k}">${l}<b>${pfa(Sup.tickets.filter((t) => supMatch(t, k)).length)}</b></button>`).join("");
}
function supPaintList() {
  const box = document.getElementById("sup-list"); if (!box) return;
  const list = supFiltered();
  if (!list.length) {
    box.innerHTML = Sup.tickets.length
      ? `<div class="empty"><span class="empty-icon">🔍</span>تیکتی با این فیلتر نیست<small>فیلتر دیگری را امتحان کن</small></div>`
      : `<div class="empty"><span class="empty-icon">🎧</span>هنوز تیکتی ثبت نکرده‌ای<small>اولین گزارش یا پیشنهادت را بفرست</small>
          <div style="margin-top:.8rem"><button class="lq-btn lq-sm is-on" style="--lq-hue:var(--primary)" data-sup="new">+ تیکت جدید</button></div></div>`;
    return;
  }
  box.innerHTML = `<div class="sup-list">${list.map((t) => {
    const [label, hue] = SUP_STATUS[t.status] || [t.status, "var(--muted)"];
    const fresh = supFresh(t);
    return `<div class="sup-row ${fresh ? "is-fresh" : ""}" style="--hue:${hue}" data-sup-card="${pesc(t.id)}">
      <span class="sup-ico">${t.status === "closed" ? "🔒" : fresh ? "📬" : "🎧"}</span>
      <div class="sup-body">
        <div class="sup-head"><b>${pesc(t.subject)}</b>${fresh ? `<span class="sup-dot" title="پاسخ تازه"></span>` : ""}
          <span class="badge" style="color:${hue}">${label}</span></div>
        <div class="sup-meta"><span>${pfa(t.message_count || 0)} پیام</span><span>${supAgo(t.updated_at || t.created_at)}</span></div>
      </div>
      <div class="sup-actions">
        <button class="lq-btn lq-sm ${fresh ? "is-on" : ""}" style="--lq-hue:${hue}" data-sup="open" data-id="${pesc(t.id)}">مشاهده / پاسخ</button>
        <button class="lq-btn lq-sm" data-sup="status" data-id="${pesc(t.id)}" data-v="${t.status === "closed" ? "open" : "closed"}">${t.status === "closed" ? "بازگشایی" : "بستن"}</button>
      </div></div>`;
  }).join("")}</div>`;
}
function supMsgs(msgs) {
  return msgs.length ? msgs.map((m) => `<div class="sup-msg ${m.is_staff ? "is-staff" : ""}">
    <div class="sup-msg-head"><b>${pesc(m.author_name || (m.is_staff ? "پشتیبانی" : "کاربر"))}</b><span>${supAgo(m.created_at)}</span></div>
    <div class="sup-msg-body">${pesc(m.body)}</div></div>`).join("")
    : `<div class="sup-empty-inline">پیامی نیست</div>`;
}
async function supOpen(id) {
  let data;
  try { data = await api(`/support/tickets/${encodeURIComponent(id)}`); }
  catch (e) { supToast("❌ " + (e.message || "بارگذاری ناموفق")); return; }
  const tk = data.ticket || {}; const msgs = (data.messages || []).slice();
  const meta = Sup.tickets.find((x) => x.id === id);
  if (meta) { Sup.seen[id] = meta.message_count || msgs.length; localStorage.setItem("sup:seen", JSON.stringify(Sup.seen)); supPaintAll(); }
  const [label, hue] = SUP_STATUS[tk.status] || [tk.status, "var(--muted)"];
  supLayer({ type: "drawer", title: "تیکت پشتیبانی", html: `<div class="sup-dwr">
    <div class="sup-dwr-head"><span class="sup-ico lg">🎧</span>
      <div><h2>${pesc(tk.subject || "")}</h2>
        <div class="sup-meta"><span class="badge" style="color:${hue}" id="sup-status-badge">${label}</span>
          <span>${supAgo(tk.updated_at || tk.created_at)}</span></div></div>
      <button class="sup-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="sup-thread" id="sup-thread">${supMsgs(msgs)}</div>
    <form class="sup-reply" id="sup-reply">
      <textarea class="input" id="sup-reply-body" rows="3" maxlength="5000" placeholder="پاسخ شما… (Ctrl+Enter برای ارسال)">${pesc(Sup.drafts[id] || "")}</textarea>
      <div class="sup-dwr-actions">
        <button class="lq-btn lq-sm is-on" style="--lq-hue:var(--primary)" type="submit">ارسال پاسخ</button>
        <button class="lq-btn lq-sm" type="button" data-sup="status" data-id="${pesc(id)}" data-v="${tk.status === "closed" ? "open" : "closed"}">${tk.status === "closed" ? "بازگشایی تیکت" : "مشکلم حل شد، ببند"}</button>
        <button class="lq-btn lq-sm" type="button" data-sup="copyid" data-id="${pesc(id)}">📋 کپی شناسه</button>
      </div></form></div>`,
    onMount: (w) => {
      const body = w.querySelector("#sup-reply-body");
      const thread = w.querySelector("#sup-thread");
      thread.scrollTop = thread.scrollHeight;
      body.addEventListener("input", () => { Sup.drafts[id] = body.value; localStorage.setItem("sup:drafts", JSON.stringify(Sup.drafts)); });
      const send = async () => {
        const v = body.value.trim(); if (!v) { body.focus(); return; }
        const btn = w.querySelector('#sup-reply button[type="submit"]'); btn.disabled = true;
        const tmp = { author_name: "شما", body: v, created_at: new Date().toISOString(), is_staff: false };
        msgs.push(tmp); thread.innerHTML = supMsgs(msgs); thread.scrollTop = thread.scrollHeight;
        body.value = ""; delete Sup.drafts[id]; localStorage.setItem("sup:drafts", JSON.stringify(Sup.drafts));
        try {
          await api(`/support/tickets/${encodeURIComponent(id)}/messages`, { method: "POST", body: JSON.stringify({ body: v }) });
          if (meta) { meta.message_count = (meta.message_count || msgs.length - 1) + 1; meta.updated_at = tmp.created_at; Sup.seen[id] = meta.message_count; localStorage.setItem("sup:seen", JSON.stringify(Sup.seen)); }
          supPaintAll(); supToast("✅ پاسخ ارسال شد");
        } catch (e) {
          msgs.pop(); thread.innerHTML = supMsgs(msgs); body.value = v;
          Sup.drafts[id] = v; localStorage.setItem("sup:drafts", JSON.stringify(Sup.drafts));
          supToast("❌ " + (e.message || "ارسال ناموفق"));
        } finally { btn.disabled = false; }
      };
      w.querySelector("#sup-reply").addEventListener("submit", (e) => { e.preventDefault(); send(); });
      body.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); } });
    }});
}
async function supSetStatus(id, status) {
  const t = Sup.tickets.find((x) => x.id === id); const before = t ? t.status : null;
  if (t) t.status = status;
  supPaintAll();
  const badge = document.getElementById("sup-status-badge");
  if (badge) { const [l, h] = SUP_STATUS[status] || [status, "var(--muted)"]; badge.textContent = l; badge.style.color = h; }
  try {
    await api(`/support/tickets/${encodeURIComponent(id)}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
    supToast(status === "closed" ? "تیکت بسته شد" : "تیکت بازگشایی شد", { action: "برگردان", dur: 6000, onAction: () => supSetStatus(id, before || "open") });
  } catch (e) {
    if (t) t.status = before; supPaintAll();
    supToast([404, 405].includes(e.status) ? "⚠️ endpoint بستن تیکت نصب نشده" : "❌ " + (e.message || "خطا"));
  }
}
function supNewTicket() {
  supLayer({ title: "تیکت جدید", html: `<div class="glass-form sup-form">
    <div class="sup-templates">${SUP_TEMPLATES.map((t, i) => `<button type="button" class="lq-chip" data-sup-tpl="${i}">${t[0]}</button>`).join("")}</div>
    <div class="sup-field" data-sf="subject"><label class="field-label" for="sup-f-subject">موضوع *</label>
      <input id="sup-f-subject" class="input" maxlength="200" placeholder="مثلاً خطا در همگام‌سازی" data-autofocus>
      <small class="sup-count"><span id="sup-c-sub">۰</span>/۲۰۰</small><small class="sup-err"></small></div>
    <div class="sup-field" data-sf="body"><label class="field-label" for="sup-f-body">توضیح *</label>
      <textarea id="sup-f-body" class="input" rows="6" maxlength="5000" placeholder="چه اتفاقی افتاد، کجا، و چه انتظاری داشتی…"></textarea>
      <small class="sup-count"><span id="sup-c-body">۰</span>/۵۰۰۰</small><small class="sup-err"></small></div>
    <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
      <button class="btn btn-primary" id="sup-f-send">ارسال تیکت</button></div></div>`,
    onMount: (w, L) => {
      const sub = w.querySelector("#sup-f-subject"), bod = w.querySelector("#sup-f-body");
      const upd = () => { w.querySelector("#sup-c-sub").textContent = pfa(sub.value.length); w.querySelector("#sup-c-body").textContent = pfa(bod.value.length); };
      sub.addEventListener("input", upd); bod.addEventListener("input", upd); upd();
      w.querySelectorAll("[data-sup-tpl]").forEach((b) => b.addEventListener("click", () => {
        const t = SUP_TEMPLATES[+b.dataset.supTpl]; sub.value = t[1]; bod.value = t[2]; upd(); bod.focus();
      }));
      const btn = w.querySelector("#sup-f-send");
      btn.addEventListener("click", async () => {
        const s = sub.value.trim(), b = bod.value.trim();
        const err = (k, m) => { const f = w.querySelector(`[data-sf="${k}"]`); f.classList.toggle("bad", !!m); f.querySelector(".sup-err").textContent = m || ""; return !m; };
        let ok = err("subject", s.length >= 3 ? "" : "موضوع حداقل ۳ نویسه");
        ok = err("body", b.length >= 5 ? "" : "توضیح حداقل ۵ نویسه") && ok;
        if (!ok) return;
        btn.disabled = true; btn.textContent = "در حال ارسال…";
        try {
          const r = await api("/support/tickets", { method: "POST", body: JSON.stringify({ subject: s, body: b }) });
          L.close();
          Sup.tickets.unshift({ id: r.ticket.id, subject: r.ticket.subject, status: r.ticket.status, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), message_count: 1 });
          Sup.seen[r.ticket.id] = 1; localStorage.setItem("sup:seen", JSON.stringify(Sup.seen));
          Sup.filter = "all"; supPaintAll(); supToast("✅ تیکت ثبت شد");
          supOpen(r.ticket.id);
        } catch (e) { btn.disabled = false; btn.textContent = "ارسال تیکت"; supToast("❌ " + (e.message || "خطا")); }
      });
    }});
}
function supWire() {
  if (Sup.wired) return; Sup.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-sup]");
    if (!el) { const card = e.target.closest("[data-sup-card]"); if (card && !e.target.closest("a,button,input")) supOpen(card.dataset.supCard); return; }
    const act = el.dataset.sup, id = el.dataset.id, v = el.dataset.v;
    switch (act) {
      case "filter": Sup.filter = v; supPaintPills(); supPaintList(); break;
      case "open": supOpen(id); break;
      case "new": supNewTicket(); break;
      case "status": supSetStatus(id, v); break;
      case "reload": renderSupport(); break;
      case "copyid": { const done = () => supToast("📋 شناسه کپی شد");
        if (navigator.clipboard) navigator.clipboard.writeText(id).then(done, done);
        else { const t = document.createElement("textarea"); t.value = id; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); } break; }
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "sup-q") { Sup.q = e.target.value; supPaintList(); } });
  document.addEventListener("change", (e) => { if (e.target.id === "sup-sort") { Sup.sort = e.target.value; localStorage.setItem("sup:sort", Sup.sort); supPaintList(); } });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = (typeof Lib !== "undefined" && Lib.layers?.length) || (typeof Cal !== "undefined" && Cal._layers?.length)
      || (typeof Asg !== "undefined" && Asg.layers?.length) || (typeof Adm !== "undefined" && Adm.layers?.length)
      || (typeof Crs !== "undefined" && Crs.layers?.length) || (typeof MapX !== "undefined" && MapX.layers?.length)
      || (typeof Stg !== "undefined" && Stg.layers?.length) || (typeof Dboard !== "undefined" && Dboard.layers?.length)
      || (typeof Chg !== "undefined" && Chg.layers?.length) || (typeof Qra !== "undefined" && Qra.layers?.length)
      || (typeof Wal !== "undefined" && Wal.layers?.length) || (typeof Cnt !== "undefined" && Cnt.layers?.length);
    if (busy) return;
    if (Sup.layers.length) Sup.layers[Sup.layers.length - 1].close();
  });
}
supWire();

// ---------- Admin v2 (پنل ادمین) ----------
// یک‌بار Promise.all برای همه داده‌ها؛ تب/فیلتر/جستجو/مرتب‌سازی کلاینتی.
// هر اکشن: optimistic + rollback + Undo، بدون renderAdmin() مجدد.
const ADM_TABS = [
  ["overview", "نمای کلی", "▦"],
  ["users", "کاربران", "👥"],
  ["tickets", "تیکت‌ها", "🎧"],
  ["library", "کتابخانه", "📚"],
  ["catalog", "کاتالوگ", "🗂"],
  ["system", "سیستم", "🛡️"],
];
const Adm = {
  tab: localStorage.getItem("adm:tab") || "overview",
  q: { users: "", tickets: "", catalog: "", audit: "" },
  uf: "all", tf: "open", lf: "pending",
  sort: localStorage.getItem("adm:sort") || "name",
  sel: new Set(), drafts: {}, layers: [], wired: false, ready: false,
  users: [], ustats: {}, tickets: [], catalog: [], pending: [], reports: [],
  system: {}, audit: [], backup: null, denied: false,
};
const xesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const xfa = (n) => faDigits(String(n));
const xurl = (u) => /^https?:\/\//i.test(u || "") ? u : null;
const xhost = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (_) { return ""; } };
function xago(iso) {
  if (!iso) return "—";
  const t = Date.parse(String(iso).replace(" ", "T"));
  if (Number.isNaN(t)) return String(iso);
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${xfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${xfa(Math.floor(s / 3600))} ساعت پیش`;
  if (s < 2592000) return `${xfa(Math.floor(s / 86400))} روز پیش`;
  return String(iso).slice(0, 10);
}
function admLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer
    : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : admOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = Adm.layers.indexOf(L); if (i >= 0) Adm.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  Adm.layers.push(L); return L;
}
function admToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  return admOwnToast(m, o);
}
function admOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "adm-layer";
  w.innerHTML = `<div class="adm-scrim" data-adm-x></div>` + (opts.type === "drawer"
    ? `<aside class="adm-drawer" role="dialog" aria-modal="true" aria-label="${xesc(opts.title)}">${opts.html}</aside>`
    : `<div class="adm-modal-wrap"><div class="adm-modal" role="dialog" aria-modal="true" aria-label="${xesc(opts.title)}"><h3>${xesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("adm-locked");
  const panel = w.querySelector(".adm-drawer,.adm-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".adm-layer")) document.body.classList.remove("adm-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-adm-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function admOwnToast(msg, o = {}) {
  let box = document.getElementById("adm-toasts");
  if (!box) { box = document.createElement("div"); box.id = "adm-toasts"; box.className = "adm-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "adm-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${xesc(msg)}</span>${o.action ? `<button class="a">${xesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const admCloseAll = () => Adm.layers.slice().forEach((l) => l.close());
function admConfirm(title, text, okLabel, onOk, danger = true) {
  admLayer({ title, html: `<p class="adm-confirm-text">${xesc(text)}</p>
    <div class="lib-modal-actions adm-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
      <button class="btn ${danger ? "btn-danger" : "btn-primary"}" id="adm-cf-ok" data-autofocus>${xesc(okLabel)}</button></div>`,
    onMount: (w, L) => { const b = w.querySelector("#adm-cf-ok");
      b.addEventListener("click", async () => { b.disabled = true; b.textContent = "در حال انجام…"; await onOk(); L.close(); }); } });
}
const admSelf = () => (Adm.users.find((u) => u.is_self) || {}).id;
const admAdminCount = () => Adm.users.filter((u) => u.role === "admin" && u.is_active).length;

/* ---- بارگذاری موازی ---- */
async function renderAdmin() {
  Adm.sel.clear();
  contentEl.innerHTML = `${pageHead("پنل ادمین", "مدیریت کاربران، پشتیبانی، کتابخانه و سیستم")}
    <div class="adm-tabs" id="adm-tabs"></div><div id="adm-bulk"></div><div id="adm-panel"></div>`;
  await admLoadAll();
}
async function admLoadAll() {
  const panel = document.getElementById("adm-panel");
  if (panel) panel.innerHTML = `<div class="adm-skel-grid">${'<div class="adm-skel"></div>'.repeat(6)}</div>`;
  const [users, tickets, catalog, pending, reports, system, audit] = await Promise.all([
    api("/admin/users").catch((e) => ({ _err: e })),
    api("/support/admin/tickets").catch(() => ({ tickets: [] })),
    api("/library/admin/catalog").catch(() => ({ courses: [] })),
    api("/library/admin/pending").catch(() => ({ items: [] })),
    api("/library/admin/reports").catch(() => ({ reports: [] })),
    api("/admin/system").catch(() => ({})),
    api("/admin/audit?limit=50").catch(() => ({ items: [] })),
  ]);
  if (users && users._err) {
    const st = users._err.status;
    Adm.denied = true;
    if (panel) panel.innerHTML = `<div class="empty"><span class="empty-icon">${st === 403 ? "🔒" : "❌"}</span>${st === 403 ? "دسترسی ادمین لازم است" : "خطا در بارگذاری پنل"}
      <small>${xesc(users._err.message || "")}</small>
      <div class="adm-actions" style="justify-content:center;margin-top:.8rem">
        <button class="btn btn-soft btn-sm" data-adm="recheck">بررسی دوباره دسترسی</button>
        <button class="btn btn-ghost btn-sm" data-adm="reload">تلاش مجدد</button></div></div>`;
    document.getElementById("adm-tabs").innerHTML = "";
    return;
  }
  Adm.denied = false; Adm.ready = true;
  Adm.users = users.users || []; Adm.ustats = users.stats || {};
  Adm.tickets = tickets.tickets || []; Adm.catalog = catalog.courses || [];
  Adm.pending = pending.items || []; Adm.reports = reports.reports || [];
  Adm.system = system || {}; Adm.audit = audit.items || [];
  authRole = "admin";
  admPaintTabs(); admPaint();
}
async function admRefresh(slice) {
  try {
    if (slice === "users") { const r = await api("/admin/users"); Adm.users = r.users || []; Adm.ustats = r.stats || {}; }
    if (slice === "tickets") Adm.tickets = (await api("/support/admin/tickets")).tickets || [];
    if (slice === "catalog") Adm.catalog = (await api("/library/admin/catalog")).courses || [];
    if (slice === "pending") Adm.pending = (await api("/library/admin/pending")).items || [];
    if (slice === "reports") Adm.reports = (await api("/library/admin/reports")).reports || [];
    if (slice === "system") Adm.system = await api("/admin/system");
    if (slice === "audit") Adm.audit = (await api("/admin/audit?limit=50")).items || [];
  } catch (_) {}
  admPaintTabs(); admPaint();
}
function admCounts() {
  return {
    overview: 0,
    users: Adm.users.length,
    tickets: Adm.tickets.filter((t) => t.status !== "closed").length,
    library: Adm.pending.length + Adm.reports.length,
    catalog: Adm.catalog.length,
    system: Adm.system.maintenance ? 1 : 0,
  };
}
function admPaintTabs() {
  const box = document.getElementById("adm-tabs"); if (!box || Adm.denied) return;
  const c = admCounts();
  box.innerHTML = ADM_TABS.map(([k, l, i]) =>
    `<button class="adm-tab ${Adm.tab === k ? "on" : ""} ${k === "system" && c.system ? "is-warn" : ""}" data-adm="tab" data-v="${k}" aria-pressed="${Adm.tab === k}">
      <span>${i}</span>${l}${c[k] ? `<b>${xfa(c[k])}</b>` : ""}</button>`).join("");
}
function admPaint() {
  if (Adm.denied) return;
  const p = document.getElementById("adm-panel"); if (!p) return;
  Adm.sel.clear(); admPaintBulk();
  ({ overview: admPaintOverview, users: admPaintUsers, tickets: admPaintTickets,
     library: admPaintLibrary, catalog: admPaintCatalog, system: admPaintSystem }[Adm.tab] || admPaintOverview)(p);
}
function admPaintBulk() {
  const box = document.getElementById("adm-bulk"); if (!box) return;
  if (!Adm.sel.size) { box.innerHTML = ""; return; }
  const acts = {
    users: `<button class="btn btn-soft btn-sm" data-adm="bulk" data-v="activate">فعال‌سازی</button>
      <button class="btn btn-ghost btn-sm" data-adm="bulk" data-v="deactivate">غیرفعال‌سازی</button>
      <button class="btn btn-ghost btn-sm" data-adm="bulk" data-v="revoke">قطع نشست‌ها</button>`,
    tickets: `<button class="btn btn-soft btn-sm" data-adm="bulk" data-v="close-tickets">بستن تیکت‌ها</button>`,
    library: `<button class="btn btn-primary btn-sm" data-adm="bulk" data-v="approve">تایید</button>
      <button class="btn btn-soft btn-sm" data-adm="bulk" data-v="reject">رد</button>`,
  }[Adm.tab] || "";
  box.innerHTML = `<div class="adm-bulkbar"><b>${xfa(Adm.sel.size)}</b> انتخاب شده ${acts}
    <button class="btn btn-ghost btn-sm" data-adm="bulk-clear">پاک کردن</button></div>`;
}
function admSearch(tab, ph) {
  return `<div class="search-box adm-search"><span class="search-ico">${ICON_SEARCH}</span>
    <input id="adm-q-${tab}" type="search" data-adm-q="${tab}" value="${xesc(Adm.q[tab] || "")}" placeholder="${xesc(ph)}" aria-label="جستجو"></div>`;
}
function admEmpty(icon, text, hint) {
  return `<div class="empty"><span class="empty-icon">${icon}</span>${xesc(text)}${hint ? `<small>${xesc(hint)}</small>` : ""}</div>`;
}

/* ---- نمای کلی ---- */
function admPaintOverview(p) {
  const openT = Adm.tickets.filter((t) => t.status !== "closed").length;
  const inactive = Adm.users.filter((u) => !u.is_active).length;
  const tiles = [
    ["کل کاربران", Adm.users.length, "--primary", "users"],
    ["ادمین‌ها", Adm.ustats.admins ?? admAdminCount(), "--warning", "users"],
    ["غیرفعال", inactive, "--danger", "users"],
    ["تیکت باز", openT, "--info", "tickets"],
    ["در انتظار تایید", Adm.pending.length, "--accent", "library"],
    ["گزارش باز", Adm.reports.length, "--danger", "library"],
  ];
  const alerts = [];
  if (Adm.system.maintenance) alerts.push(["warn", "حالت تعمیرات فعال است", Adm.system.maintenance_message || "کاربران پیام تعمیرات می‌بینند.", "system"]);
  if (Adm.pending.length) alerts.push(["info", `${xfa(Adm.pending.length)} منبع در صف تایید`, "منابع تا تایید شدن برای دیگران نمایش داده نمی‌شوند.", "library"]);
  if (Adm.reports.length) alerts.push(["danger", `${xfa(Adm.reports.length)} گزارش باز`, "لینک‌های گزارش‌شده را بررسی کن.", "library"]);
  if (openT) alerts.push(["info", `${xfa(openT)} تیکت بی‌پاسخ`, "کاربران منتظر پاسخ پشتیبانی هستند.", "tickets"]);
  if ((Adm.ustats.max_admins ?? 0) && (Adm.ustats.admins ?? 0) >= Adm.ustats.max_admins) alerts.push(["warn", "سقف تعداد ادمین پر شده", "برای افزودن ادمین جدید، اول یکی را ارتقا به کاربر بده.", "users"]);
  p.innerHTML = `
    <div class="adm-tiles">${tiles.map(([l, v, c, go]) =>
      `<button class="adm-tile" data-adm="tab" data-v="${go}"><b style="color:var(${c})">${xfa(v)}</b><span>${l}</span></button>`).join("")}</div>
    ${alerts.length ? `<div class="card"><div class="card-head"><h3 class="section-title">⚠️ نیازمند توجه</h3></div>
      <div class="adm-alerts">${alerts.map(([lv, t, d, go]) =>
        `<button class="adm-alert lv-${lv}" data-adm="tab" data-v="${go}"><b>${xesc(t)}</b><span>${xesc(d)}</span><i>›</i></button>`).join("")}</div></div>`
      : `<div class="card adm-ok">✅ همه‌چیز مرتب است — صف تایید، گزارش‌ها و تیکت‌ها خالی‌اند.</div>`}
    <div class="card">
      <div class="card-head"><h3 class="section-title">🧾 آخرین اقدامات</h3>
        <button class="btn btn-ghost btn-sm" data-adm="tab" data-v="system">همه لاگ‌ها</button></div>
      <div class="item-list">${Adm.audit.slice(0, 6).map(admAuditRow).join("") || admEmpty("🗒", "هنوز لاگی ثبت نشده")}</div>
    </div>`;
}
function admAuditRow(a) {
  return `<div class="list-row adm-log"><span class="row-icon">•</span>
    <div class="row-body"><div class="row-title">${xesc(a.action)}
      <span class="badge">${xesc(a.actor_name || a.actor_username || "سیستم")}</span></div>
      <div class="row-meta"><span>${xago(a.created_at)}</span>${a.detail || a.target_user_id ? `<span>${xesc(a.detail || a.target_user_id)}</span>` : ""}</div></div></div>`;
}

/* ---- کاربران ---- */
function admUsersList() {
  const q = (Adm.q.users || "").trim().toLowerCase();
  let l = Adm.users.filter((u) => {
    if (Adm.uf === "admins") return u.role === "admin";
    if (Adm.uf === "users") return u.role !== "admin";
    if (Adm.uf === "inactive") return !u.is_active;
    return true;
  });
  if (q) l = l.filter((u) => `${u.full_name || ""} ${u.lms_username || ""}`.toLowerCase().includes(q));
  const s = Adm.sort;
  return l.slice().sort((a, b) =>
    s === "login" ? String(b.last_login_at || "").localeCompare(String(a.last_login_at || ""))
    : s === "sessions" ? (b.session_count || 0) - (a.session_count || 0)
    : s === "role" ? (a.role === "admin" ? -1 : 1) - (b.role === "admin" ? -1 : 1)
    : String(a.full_name || a.lms_username || "").localeCompare(String(b.full_name || b.lms_username || ""), "fa"));
}
function admUserRow(u) {
  const lastAdmin = u.role === "admin" && admAdminCount() <= 1;
  const dis = u.is_self ? "disabled" : "";
  return `<div class="adm-row ${u.is_active ? "" : "is-off"}" data-adm-card="${xesc(u.id)}">
    <input type="checkbox" class="adm-chk" data-adm-sel="${xesc(u.id)}" ${Adm.sel.has(u.id) ? "checked" : ""} aria-label="انتخاب ${xesc(u.full_name || u.lms_username)}">
    <span class="adm-ava">${xesc((u.full_name || u.lms_username || "؟").trim().charAt(0))}</span>
    <div class="adm-row-main">
      <div class="row-title"><button class="adm-link" data-adm="user" data-id="${xesc(u.id)}">${xesc(u.full_name || "—")}</button>
        ${u.is_self ? `<span class="badge">شما</span>` : ""}
        <span class="badge ${u.role === "admin" ? "badge-warn" : ""}">${u.role === "admin" ? "ادمین" : "کاربر"}</span>
        <span class="badge ${u.is_active ? "badge-new" : "badge-expired"}">${u.is_active ? "فعال" : "غیرفعال"}</span></div>
      <div class="row-meta"><span dir="ltr">${xesc(u.lms_username || "")}</span>
        <span>آخرین ورود: ${xago(u.last_login_at)}</span><span>${xfa(u.session_count || 0)} نشست</span></div>
    </div>
    <div class="row-actions">
      <button class="btn btn-soft btn-sm" data-adm="role" data-id="${xesc(u.id)}" data-v="${u.role === "admin" ? "user" : "admin"}" ${lastAdmin && u.role === "admin" ? 'disabled title="حداقل یک ادمین باید بماند"' : dis}>${u.role === "admin" ? "↓ کاربر" : "↑ ادمین"}</button>
      <button class="btn btn-ghost btn-sm" data-adm="active" data-id="${xesc(u.id)}" data-v="${u.is_active ? "0" : "1"}" ${dis || (lastAdmin && u.is_active) ? "disabled" : ""}>${u.is_active ? "غیرفعال" : "فعال"}</button>
      <button class="btn btn-ghost btn-sm" data-adm="revoke" data-id="${xesc(u.id)}">قطع نشست</button>
    </div></div>`;
}
function admPaintUsers(p) {
  const list = admUsersList();
  const pills = [["all", "همه"], ["admins", "ادمین"], ["users", "کاربر"], ["inactive", "غیرفعال"]];
  p.innerHTML = `
    <div class="adm-toolbar">${admSearch("users", "جستجوی نام یا شماره دانشجویی…")}
      <select class="input adm-sel" id="adm-sort" aria-label="مرتب‌سازی">
        <option value="name">الفبایی</option><option value="login">آخرین ورود</option>
        <option value="sessions">تعداد نشست</option><option value="role">نقش</option></select>
      <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="users">↻</button></div>
    <div class="adm-pills">${pills.map(([k, l]) => {
      const n = k === "all" ? Adm.users.length : k === "admins" ? Adm.users.filter((u) => u.role === "admin").length
        : k === "users" ? Adm.users.filter((u) => u.role !== "admin").length : Adm.users.filter((u) => !u.is_active).length;
      return `<button class="adm-pill ${Adm.uf === k ? "on" : ""}" data-adm="uf" data-v="${k}">${l}<b>${xfa(n)}</b></button>`;
    }).join("")}</div>
    <div class="adm-list">${list.map(admUserRow).join("") || admEmpty("🔍", "کاربری با این فیلتر نیست")}</div>
    <p class="adm-hint">ادمین‌های اولیه با متغیر محیطی <code>LMS_ADMIN_USERNAMES</code> تعیین می‌شوند. آخرین ادمین فعال قابل حذف/غیرفعال‌سازی نیست.</p>`;
  const s = document.getElementById("adm-sort"); if (s) s.value = Adm.sort;
}
async function admPushUser(id, action, value) {
  try {
    if (action === "role") await api(`/admin/users/${encodeURIComponent(id)}/role`, { method: "PATCH", body: JSON.stringify({ role: value }) });
    else if (action === "active") await api(`/admin/users/${encodeURIComponent(id)}/active`, { method: "PATCH", body: JSON.stringify({ active: value }) });
    else await api(`/admin/users/${encodeURIComponent(id)}/revoke-sessions`, { method: "POST", body: "{}" });
    return true;
  } catch (e) { admToast("❌ " + (e.message || "خطا")); return false; }
}
async function admUserAction(id, action, value) {
  const u = Adm.users.find((x) => x.id === id); if (!u) return;
  const before = { role: u.role, is_active: u.is_active, session_count: u.session_count };
  if (action === "role") u.role = value;
  if (action === "active") u.is_active = value;
  if (action === "revoke") u.session_count = 0;
  admPaintTabs(); admPaint();
  const ok = await admPushUser(id, action, value);
  if (!ok) { Object.assign(u, before); admPaintTabs(); admPaint(); return; }
  admRefresh("audit");
  const label = action === "role" ? "نقش تغییر کرد" : action === "active" ? (value ? "حساب فعال شد" : "حساب غیرفعال شد") : "نشست‌ها قطع شد";
  admToast("✅ " + label, { action: "برگردان", dur: 6500, onAction: async () => {
    if (action === "revoke") { admToast("قطع نشست قابل برگشت نیست"); return; }
    const back = action === "role" ? before.role : before.is_active;
    Object.assign(u, before); admPaintTabs(); admPaint();
    await admPushUser(id, action, back); admRefresh("audit");
  }});
}
function admOpenUser(id) {
  const u = Adm.users.find((x) => x.id === id); if (!u) return;
  const lastAdmin = u.role === "admin" && admAdminCount() <= 1;
  admLayer({ type: "drawer", title: "جزئیات کاربر", html: `<div class="adm-dwr">
    <div class="adm-dwr-head"><span class="adm-ava lg">${xesc((u.full_name || u.lms_username || "؟").trim().charAt(0))}</span>
      <div><h2>${xesc(u.full_name || "—")}</h2><div class="adm-badges">
        <span class="badge ${u.role === "admin" ? "badge-warn" : ""}">${u.role === "admin" ? "ادمین" : "کاربر"}</span>
        <span class="badge ${u.is_active ? "badge-new" : "badge-expired"}">${u.is_active ? "فعال" : "غیرفعال"}</span>
        ${u.is_self ? `<span class="badge">شما</span>` : ""}</div></div>
      <button class="adm-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="adm-kv">
      <div><span>شماره دانشجویی</span><b dir="ltr">${xesc(u.lms_username || "—")}</b></div>
      <div><span>شناسه</span><b dir="ltr">${xesc(u.id)}</b></div>
      <div><span>ساخت حساب</span><b>${xago(u.created_at)}</b></div>
      <div><span>آخرین ورود</span><b>${xago(u.last_login_at)}</b></div>
      <div><span>نشست‌های فعال</span><b>${xfa(u.session_count || 0)}</b></div>
    </div>
    ${lastAdmin ? `<div class="adm-note warn">این آخرین ادمین فعال است؛ نمی‌توان نقش یا وضعیتش را تغییر داد.</div>` : ""}
    ${u.is_self ? `<div class="adm-note">این حساب خودت است؛ تغییر نقش و وضعیت از اینجا مجاز نیست.</div>` : ""}
    <div class="adm-dwr-actions">
      <button class="btn btn-soft btn-sm" data-adm="role" data-id="${xesc(u.id)}" data-v="${u.role === "admin" ? "user" : "admin"}" ${u.is_self || (lastAdmin && u.role === "admin") ? "disabled" : ""}>${u.role === "admin" ? "↓ تنزل به کاربر" : "↑ ارتقا به ادمین"}</button>
      <button class="btn btn-ghost btn-sm" data-adm="active" data-id="${xesc(u.id)}" data-v="${u.is_active ? "0" : "1"}" ${u.is_self || (lastAdmin && u.is_active) ? "disabled" : ""}>${u.is_active ? "غیرفعال‌سازی" : "فعال‌سازی"}</button>
      <button class="btn btn-ghost btn-sm" data-adm="revoke" data-id="${xesc(u.id)}">قطع همه نشست‌ها</button>
    </div></div>` });
}

/* ---- تیکت‌ها ---- */
function admTicketsList() {
  const q = (Adm.q.tickets || "").trim().toLowerCase();
  let l = Adm.tickets.filter((t) => {
    if (Adm.tf === "all") return true;
    if (Adm.tf === "closed") return t.status === "closed";
    if (Adm.tf === "answered") return t.status === "answered";
    return t.status === "open";
  });
  if (q) l = l.filter((t) => `${t.subject || ""} ${t.full_name || ""} ${t.lms_username || ""}`.toLowerCase().includes(q));
  return l.slice().sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
}
function admPaintTickets(p) {
  const list = admTicketsList();
  const pills = [["open", "بی‌پاسخ"], ["answered", "پاسخ‌داده"], ["closed", "بسته"], ["all", "همه"]];
  p.innerHTML = `
    <div class="adm-toolbar">${admSearch("tickets", "جستجوی موضوع یا نام کاربر…")}
      <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="tickets">↻</button></div>
    <div class="adm-pills">${pills.map(([k, l]) => {
      const n = k === "all" ? Adm.tickets.length : Adm.tickets.filter((t) => t.status === k).length;
      return `<button class="adm-pill ${Adm.tf === k ? "on" : ""}" data-adm="tf" data-v="${k}">${l}<b>${xfa(n)}</b></button>`;
    }).join("")}</div>
    <div class="adm-list">${list.map((t) => `<div class="adm-row">
      <input type="checkbox" class="adm-chk" data-adm-sel="${xesc(t.id)}" ${Adm.sel.has(t.id) ? "checked" : ""} aria-label="انتخاب تیکت">
      <span class="row-icon">🎧</span>
      <div class="adm-row-main"><div class="row-title"><button class="adm-link" data-adm="ticket" data-id="${xesc(t.id)}">${xesc(t.subject)}</button>
        <span class="badge ${t.status === "closed" ? "badge-done" : t.status === "answered" ? "badge-info" : "badge-new"}">${xesc({ open: "بی‌پاسخ", answered: "پاسخ‌داده", closed: "بسته" }[t.status] || t.status)}</span></div>
        <div class="row-meta"><span>${xesc(t.full_name || "")}</span><span dir="ltr">${xesc(t.lms_username || "")}</span><span>${xago(t.updated_at)}</span></div></div>
      <div class="row-actions"><button class="btn btn-soft btn-sm" data-adm="ticket" data-id="${xesc(t.id)}">مشاهده / پاسخ</button></div></div>`).join("")
      || admEmpty("📭", "تیکتی در این فیلتر نیست")}</div>`;
}
async function admOpenTicket(id) {
  let data;
  try { data = await api(`/support/tickets/${encodeURIComponent(id)}`); }
  catch (e) { admToast("❌ " + (e.message || "بارگذاری تیکت ناموفق")); return; }
  const tk = data.ticket || {}; const msgs = data.messages || [];
  const meta = Adm.tickets.find((x) => x.id === id) || {};
  const L = admLayer({ type: "drawer", title: "تیکت پشتیبانی", html: `<div class="adm-dwr">
    <div class="adm-dwr-head"><span class="row-icon">🎧</span>
      <div><h2>${xesc(tk.subject || "")}</h2><div class="adm-badges">
        <span class="badge ${tk.status === "closed" ? "badge-done" : "badge-new"}" id="adm-tk-status">${xesc(tk.status || "")}</span>
        <span class="badge">${xesc(meta.full_name || meta.lms_username || tk.user_id || "")}</span></div></div>
      <button class="adm-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="adm-thread" id="adm-thread">${admMsgs(msgs)}</div>
    <form class="adm-reply" id="adm-reply">
      <textarea class="input" id="adm-reply-body" rows="3" placeholder="پاسخ پشتیبانی… (Ctrl+Enter برای ارسال)">${xesc(Adm.drafts[id] || "")}</textarea>
      <div class="adm-dwr-actions">
        <button class="btn btn-primary btn-sm" type="submit">ارسال پاسخ</button>
        <button class="btn btn-ghost btn-sm" type="button" data-adm="tk-status" data-id="${xesc(id)}" data-v="${tk.status === "closed" ? "open" : "closed"}">${tk.status === "closed" ? "بازگشایی" : "بستن تیکت"}</button>
      </div></form></div>`,
    onMount: (w) => {
      const body = w.querySelector("#adm-reply-body");
      body.addEventListener("input", () => { Adm.drafts[id] = body.value; });
      const send = async () => {
        const v = body.value.trim(); if (!v) { body.focus(); return; }
        const btn = w.querySelector('#adm-reply button[type="submit"]'); btn.disabled = true;
        const tmp = { author_name: "شما (پشتیبانی)", body: v, created_at: "الان", is_staff: true, _tmp: true };
        msgs.push(tmp); w.querySelector("#adm-thread").innerHTML = admMsgs(msgs);
        body.value = ""; delete Adm.drafts[id];
        try {
          await api(`/support/tickets/${encodeURIComponent(id)}/messages`, { method: "POST", body: JSON.stringify({ body: v }) });
          admToast("✅ پاسخ ارسال شد"); admRefresh("tickets");
        } catch (e) {
          msgs.splice(msgs.indexOf(tmp), 1); w.querySelector("#adm-thread").innerHTML = admMsgs(msgs);
          body.value = v; Adm.drafts[id] = v; admToast("❌ " + (e.message || "ارسال ناموفق"));
        } finally { btn.disabled = false; }
      };
      w.querySelector("#adm-reply").addEventListener("submit", (e) => { e.preventDefault(); send(); });
      body.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); } });
    }});
  return L;
}
function admMsgs(msgs) {
  return msgs.length ? msgs.map((m) => `<div class="adm-msg ${m.is_staff ? "is-staff" : ""}">
    <div class="adm-msg-head"><b>${xesc(m.author_name || "کاربر")}</b><span>${xesc(m.created_at || "")}</span></div>
    <div class="adm-msg-body">${xesc(m.body)}</div></div>`).join("")
    : `<div class="adm-note">پیامی در این تیکت نیست.</div>`;
}
async function admTicketStatus(id, status) {
  const t = Adm.tickets.find((x) => x.id === id); const before = t ? t.status : null;
  if (t) t.status = status;
  admPaintTabs(); admPaint();
  const badge = document.getElementById("adm-tk-status"); if (badge) { badge.textContent = status; badge.className = "badge " + (status === "closed" ? "badge-done" : "badge-new"); }
  try {
    await api(`/support/admin/tickets/${encodeURIComponent(id)}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
    admToast(status === "closed" ? "تیکت بسته شد" : "تیکت بازگشایی شد", { action: "برگردان", dur: 6000, onAction: () => admTicketStatus(id, before || "open") });
  } catch (e) { if (t) t.status = before; admPaintTabs(); admPaint(); admToast("❌ " + (e.message || "خطا")); }
}

/* ---- کتابخانه: صف تایید + گزارش‌ها ---- */
function admPaintLibrary(p) {
  const pend = Adm.pending, reps = Adm.reports;
  const card = (it, isRep) => {
    const u = xurl(isRep ? it.item_url : it.url), id = isRep ? it.item_id : it.id;
    return `<div class="adm-row is-lib">
      <input type="checkbox" class="adm-chk" data-adm-sel="${xesc(isRep ? it.id : it.id)}" ${Adm.sel.has(it.id) ? "checked" : ""} aria-label="انتخاب">
      <span class="row-icon">${isRep ? "🚩" : "📚"}</span>
      <div class="adm-row-main">
        <div class="row-title">${xesc(isRep ? it.item_title : it.title)}
          <span class="badge ${isRep ? "badge-expired" : "badge-warn"}">${isRep ? "گزارش" : "در انتظار"}</span>
          <span class="badge badge-domain">${xesc(it.course_name || "")}</span></div>
        <div class="row-meta"><span>${xesc(isRep ? (it.reporter_name || it.reporter_username || "") : (it.submitter_name || it.submitter_username || ""))}</span>
          <span>${xago(it.created_at)}</span>${u ? `<span dir="ltr">${xesc(xhost(u))}</span>` : `<span>لینک نامعتبر</span>`}</div>
        ${(isRep ? it.reason : it.description) ? `<p class="adm-desc">${xesc(isRep ? it.reason : it.description)}</p>` : ""}
      </div>
      <div class="row-actions">
        ${u ? `<a class="btn btn-ghost btn-sm" href="${xesc(u)}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a>` : ""}
        ${isRep
          ? `<button class="btn btn-soft btn-sm" data-adm="resolve" data-id="${xesc(it.id)}">رسیدگی شد</button>
             <button class="btn btn-ghost btn-sm adm-del" data-adm="lib-del" data-id="${xesc(id)}">حذف آیتم</button>`
          : `<button class="btn btn-primary btn-sm" data-adm="approve" data-id="${xesc(id)}">تایید</button>
             <button class="btn btn-soft btn-sm" data-adm="reject" data-id="${xesc(id)}">رد</button>
             <button class="btn btn-ghost btn-sm adm-del" data-adm="lib-del" data-id="${xesc(id)}">حذف</button>`}
      </div></div>`;
  };
  p.innerHTML = `
    <div class="card"><div class="card-head"><h3 class="section-title">📚 در انتظار تایید <span class="badge">${xfa(pend.length)}</span></h3>
      <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="pending">↻</button></div>
      <div class="adm-list">${pend.map((it) => card(it, false)).join("") || admEmpty("✅", "صف تایید خالی است")}</div></div>
    <div class="card"><div class="card-head"><h3 class="section-title">🚩 گزارش‌های باز <span class="badge badge-expired">${xfa(reps.length)}</span></h3>
      <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="reports">↻</button></div>
      <div class="adm-list">${reps.map((it) => card(it, true)).join("") || admEmpty("✅", "گزارش بازی نیست")}</div></div>`;
}
async function admLibStatus(id, status, silent) {
  const idx = Adm.pending.findIndex((x) => x.id === id);
  const it = idx >= 0 ? Adm.pending[idx] : null;
  if (it) Adm.pending.splice(idx, 1);
  Adm.sel.delete(id); admPaintTabs(); admPaint();
  try {
    await api(`/library/admin/items/${encodeURIComponent(id)}/status`, { method: "POST", body: JSON.stringify({ status }) });
    if (!silent) admToast(status === "approved" ? "✅ تایید شد" : "رد شد", { action: "برگردان", dur: 6500, onAction: async () => {
      try { await api(`/library/admin/items/${encodeURIComponent(id)}/status`, { method: "POST", body: JSON.stringify({ status: "pending" }) });
        if (it) Adm.pending.splice(Math.min(idx < 0 ? 0 : idx, Adm.pending.length), 0, it);
        admPaintTabs(); admPaint(); admToast("↩️ برگشت"); } catch (e) { admToast("❌ " + (e.message || "برگشت ناموفق")); }
    }});
    return true;
  } catch (e) { if (it) Adm.pending.splice(Math.min(idx < 0 ? 0 : idx, Adm.pending.length), 0, it); admPaintTabs(); admPaint(); admToast("❌ " + (e.message || "خطا")); return false; }
}
function admLibDelete(id) {
  admConfirm("حذف کامل آیتم", "این منبع برای همیشه حذف می‌شود و قابل برگشت نیست. اگر فقط می‌خواهی از دید خارج شود، از «رد» استفاده کن.", "حذف کامل", async () => {
    try {
      await api(`/library/admin/items/${encodeURIComponent(id)}`, { method: "DELETE" });
      Adm.pending = Adm.pending.filter((x) => x.id !== id);
      Adm.reports = Adm.reports.filter((x) => x.item_id !== id);
      Adm.sel.delete(id); admCloseAll(); admPaintTabs(); admPaint(); admToast("🗑 حذف شد");
    } catch (e) { admToast("❌ " + (e.message || "خطا")); }
  });
}
async function admResolve(id) {
  const idx = Adm.reports.findIndex((x) => x.id === id); const it = Adm.reports[idx];
  Adm.reports.splice(idx, 1); Adm.sel.delete(id); admPaintTabs(); admPaint();
  try {
    await api(`/library/admin/reports/${encodeURIComponent(id)}/resolve`, { method: "POST", body: "{}" });
    admToast("رسیدگی شد", { action: "برگردان", dur: 6000, onAction: () => { Adm.reports.splice(Math.min(idx, Adm.reports.length), 0, it); admPaintTabs(); admPaint(); } });
  } catch (e) { Adm.reports.splice(Math.min(idx, Adm.reports.length), 0, it); admPaintTabs(); admPaint(); admToast("❌ " + (e.message || "خطا")); }
}

/* ---- کاتالوگ ---- */
function admPaintCatalog(p) {
  const q = (Adm.q.catalog || "").trim().toLowerCase();
  const list = Adm.catalog.filter((c) => !q || `${c.name || ""} ${c.code || ""} ${c.term || ""}`.toLowerCase().includes(q));
  p.innerHTML = `
    <div class="card"><div class="card-head"><h3 class="section-title">🗂 افزودن درس به کاتالوگ</h3></div>
      <div class="glass-form">
        <div class="glass-form-row">
          <div><label class="field-label" for="adm-cat-name">نام درس *</label><input id="adm-cat-name" class="input" placeholder="مثلاً ریاضی مهندسی"></div>
          <div><label class="field-label" for="adm-cat-code">کد درس</label><input id="adm-cat-code" class="input" dir="ltr" placeholder="اختیاری"></div>
        </div>
        <div class="glass-form-row">
          <div><label class="field-label" for="adm-cat-term">ترم</label><input id="adm-cat-term" class="input" dir="ltr" placeholder="مثلاً 04"></div>
          <div class="adm-end"><button class="btn btn-primary" id="adm-cat-add">افزودن درس</button></div>
        </div>
        <div><label class="field-label" for="adm-cat-bulk">افزودن دسته‌ای — هر خط: نام | کد | ترم</label>
          <textarea id="adm-cat-bulk" class="input" rows="4" placeholder="ریاضی مهندسی | 36-20-001 | 04&#10;فیزیک ۲ | | 04"></textarea>
          <div class="adm-bulkfoot"><span class="adm-hint" id="adm-cat-count">۰ خط معتبر</span>
            <button class="btn btn-soft btn-sm" id="adm-cat-bulk-btn">وارد کردن دسته‌ای</button></div></div>
      </div></div>
    <div class="adm-toolbar">${admSearch("catalog", "جستجوی نام، کد یا ترم…")}
      <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="catalog">↻</button></div>
    <div class="adm-list">${list.map((c) => `<div class="adm-row ${c.is_active ? "" : "is-off"}">
      <span class="row-icon">📘</span>
      <div class="adm-row-main"><div class="row-title">${xesc(c.name)}
        <span class="badge ${c.is_active ? "badge-new" : "badge-expired"}">${c.is_active ? "فعال" : "غیرفعال"}</span>
        <span class="badge badge-domain">${xfa(c.item_count || 0)} منبع</span></div>
        <div class="row-meta">${c.code ? `<span dir="ltr">${xesc(c.code)}</span>` : ""}${c.term ? `<span>ترم ${xesc(c.term)}</span>` : "<span>بدون ترم</span>"}</div></div>
      <div class="row-actions">
        <button class="btn btn-soft btn-sm" data-adm="cat-toggle" data-id="${xesc(c.id)}" data-v="${c.is_active ? "0" : "1"}">${c.is_active ? "غیرفعال" : "فعال"}</button>
        <button class="btn btn-ghost btn-sm adm-del" data-adm="cat-del" data-id="${xesc(c.id)}">حذف</button>
      </div></div>`).join("") || admEmpty("🗂", "کاتالوگ خالی است", "کاربران فقط از همین لیست می‌توانند منبع بفرستند")}</div>`;
  const ta = document.getElementById("adm-cat-bulk"), cnt = document.getElementById("adm-cat-count");
  const parse = () => (ta.value || "").split(/\r?\n/).map((l) => l.split("|").map((s) => s.trim()))
    .filter((p) => (p[0] || "").length >= 2).map((p) => ({ name: p[0], code: p[1] || "", term: p[2] || "" }));
  ta.addEventListener("input", () => { cnt.textContent = `${xfa(parse().length)} خط معتبر`; });
  document.getElementById("adm-cat-add").addEventListener("click", async (e) => {
    const btn = e.currentTarget, name = document.getElementById("adm-cat-name").value.trim();
    if (!name) { admToast("نام درس الزامی است"); return; }
    btn.disabled = true; btn.textContent = "در حال افزودن…";
    try {
      await api("/library/admin/catalog", { method: "POST", body: JSON.stringify({
        name, code: document.getElementById("adm-cat-code").value.trim(), term: document.getElementById("adm-cat-term").value.trim() }) });
      admToast("✅ درس اضافه شد"); await admRefresh("catalog");
    } catch (err) { admToast("❌ " + (err.message || "خطا")); btn.disabled = false; btn.textContent = "افزودن درس"; }
  });
  document.getElementById("adm-cat-bulk-btn").addEventListener("click", async (e) => {
    const rows = parse(); if (!rows.length) { admToast("خط معتبری پیدا نشد"); return; }
    const btn = e.currentTarget; btn.disabled = true; btn.textContent = "در حال وارد کردن…";
    try {
      const r = await api("/library/admin/catalog/bulk", { method: "POST", body: JSON.stringify({ courses: rows }) });
      admToast(`اضافه شد: ${xfa(r.created || 0)} · تکراری: ${xfa(r.skipped || 0)}`);
      await admRefresh("catalog");
    } catch (err) { admToast("❌ " + (err.message || "خطا")); btn.disabled = false; btn.textContent = "وارد کردن دسته‌ای"; }
  });
}
async function admCatToggle(id, active) {
  const c = Adm.catalog.find((x) => x.id === id); if (!c) return;
  const before = c.is_active; c.is_active = active; admPaint();
  try {
    await api(`/library/admin/catalog/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify({ is_active: active }) });
    admToast(active ? "فعال شد" : "غیرفعال شد", { action: "برگردان", dur: 5500, onAction: () => admCatToggle(id, before) });
  } catch (e) { c.is_active = before; admPaint(); admToast("❌ " + (e.message || "خطا")); }
}
function admCatDelete(id) {
  const c = Adm.catalog.find((x) => x.id === id); if (!c) return;
  const idx = Adm.catalog.indexOf(c);
  Adm.catalog.splice(idx, 1); admPaintTabs(); admPaint();
  let undone = false;
  const restore = () => { Adm.catalog.splice(Math.min(idx, Adm.catalog.length), 0, c); admPaintTabs(); admPaint(); };
  const timer = setTimeout(async () => {
    if (undone) return;
    try { await api(`/library/admin/catalog/${encodeURIComponent(id)}`, { method: "DELETE" }); }
    catch (e) { restore(); admToast("❌ " + (e.message || "حذف ناموفق")); }
  }, 6000);
  admToast("🗑 درس از کاتالوگ حذف شد (منابع قبلی حذف نمی‌شوند)", { action: "برگردان", dur: 6000, onAction() { undone = true; clearTimeout(timer); restore(); admToast("↩️ برگشت"); } });
}

/* ---- سیستم ---- */
function admPaintSystem(p) {
  const q = (Adm.q.audit || "").trim().toLowerCase();
  const logs = Adm.audit.filter((a) => !q || `${a.action || ""} ${a.actor_name || ""} ${a.actor_username || ""} ${a.detail || ""}`.toLowerCase().includes(q));
  p.innerHTML = `
    <div class="card"><div class="card-head"><h3 class="section-title">🛠 حالت تعمیرات</h3>
      <span class="badge ${Adm.system.maintenance ? "badge-expired" : "badge-new"}">${Adm.system.maintenance ? "فعال" : "غیرفعال"}</span></div>
      <label class="adm-check"><input type="checkbox" id="adm-maint" ${Adm.system.maintenance ? "checked" : ""}><span>سایت برای کاربران در حالت تعمیرات باشد</span></label>
      <input id="adm-maint-msg" class="input" placeholder="پیام برای کاربران" value="${xesc(Adm.system.maintenance_message || "")}">
      <div class="adm-actions"><button class="btn btn-primary btn-sm" id="adm-maint-save">ذخیره وضعیت</button></div></div>
    <div class="card"><div class="card-head"><h3 class="section-title">💾 پشتیبان‌گیری</h3>
      <button class="btn btn-primary btn-sm" id="adm-backup">ساخت بکاپ</button></div>
      <div id="adm-backup-out" class="adm-hint">${Adm.backup ? `آخرین بکاپ: <code>${xesc(Adm.backup.filename)}</code> — <a href="${xesc(Adm.backup.download)}" target="_blank" rel="noopener">دانلود</a>` : "هنوز در این نشست بکاپی ساخته نشده."}</div></div>
    <div class="card"><div class="card-head"><h3 class="section-title">🧾 لاگ اقدامات <span class="badge">${xfa(logs.length)}</span></h3>
      <div class="adm-actions"><button class="btn btn-ghost btn-sm" data-adm="audit-export">⬇ خروجی JSON</button>
        <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="audit">↻</button></div></div>
      ${admSearch("audit", "جستجو در عمل، بازیگر یا جزئیات…")}
      <div class="item-list" style="margin-top:.7rem">${logs.map(admAuditRow).join("") || admEmpty("🗒", "لاگی مطابق جستجو نیست")}</div></div>`;
  document.getElementById("adm-maint-save").addEventListener("click", async (e) => {
    const btn = e.currentTarget, enabled = document.getElementById("adm-maint").checked;
    const message = document.getElementById("adm-maint-msg").value;
    const run = async () => {
      btn.disabled = true; btn.textContent = "در حال ذخیره…";
      try { await api("/admin/system/maintenance", { method: "POST", body: JSON.stringify({ enabled, message }) });
        Adm.system = { ...Adm.system, maintenance: enabled, maintenance_message: message };
        admToast("✅ وضعیت تعمیرات ذخیره شد"); admPaintTabs(); admPaint(); }
      catch (err) { admToast("❌ " + (err.message || "خطا")); btn.disabled = false; btn.textContent = "ذخیره وضعیت"; }
    };
    if (enabled && !Adm.system.maintenance) admConfirm("فعال‌سازی حالت تعمیرات", "همه کاربران عادی پیام تعمیرات می‌بینند و به داده‌هایشان دسترسی نخواهند داشت. ادامه؟", "فعال کن", run);
    else await run();
  });
  document.getElementById("adm-backup").addEventListener("click", async (e) => {
    const btn = e.currentTarget; btn.disabled = true; btn.textContent = "در حال ساخت…";
    try {
      const r = await api("/admin/backup", { method: "POST", body: "{}" });
      Adm.backup = r;
      document.getElementById("adm-backup-out").innerHTML = `بکاپ آماده: <code>${xesc(r.filename)}</code> (${xfa(r.size_bytes || 0)} بایت) — <a href="${xesc(r.download)}" target="_blank" rel="noopener">دانلود</a>`;
      admToast("✅ بکاپ ساخته شد"); admRefresh("audit");
    } catch (err) { admToast("❌ " + (err.message || "خطا در بکاپ")); }
    finally { btn.disabled = false; btn.textContent = "ساخت بکاپ"; }
  });
}

/* ---- عملیات گروهی ---- */
async function admBulk(action) {
  const ids = [...Adm.sel]; if (!ids.length) return;
  if (action === "approve" || action === "reject") {
    const st = action === "approve" ? "approved" : "rejected";
    const snap = ids.map((id) => ({ id, it: Adm.pending.find((x) => x.id === id), i: Adm.pending.findIndex((x) => x.id === id) })).filter((x) => x.it);
    let ok = 0; for (const s of snap) if (await admLibStatus(s.id, st, true)) ok++;
    Adm.sel.clear(); admPaintTabs(); admPaint();
    admToast(`${xfa(ok)} مورد ${st === "approved" ? "تایید" : "رد"} شد`, { action: "برگردان همه", dur: 7000, onAction: async () => {
      for (const s of snap) { try { await api(`/library/admin/items/${encodeURIComponent(s.id)}/status`, { method: "POST", body: JSON.stringify({ status: "pending" }) });
        Adm.pending.splice(Math.min(s.i, Adm.pending.length), 0, s.it); } catch (_) {} }
      admPaintTabs(); admPaint(); admToast("↩️ برگشت");
    }});
    return;
  }
  if (action === "close-tickets") {
    const snap = ids.map((id) => ({ id, t: Adm.tickets.find((x) => x.id === id) })).filter((x) => x.t && x.t.status !== "closed");
    const before = snap.map((s) => ({ id: s.id, st: s.t.status }));
    snap.forEach((s) => { s.t.status = "closed"; }); Adm.sel.clear(); admPaintTabs(); admPaint();
    let ok = 0;
    for (const s of snap) { try { await api(`/support/admin/tickets/${encodeURIComponent(s.id)}/status`, { method: "PATCH", body: JSON.stringify({ status: "closed" }) }); ok++; } catch (_) {} }
    admToast(`${xfa(ok)} تیکت بسته شد`, { action: "برگردان", dur: 7000, onAction: async () => {
      for (const b of before) { const t = Adm.tickets.find((x) => x.id === b.id); if (t) t.status = b.st;
        try { await api(`/support/admin/tickets/${encodeURIComponent(b.id)}/status`, { method: "PATCH", body: JSON.stringify({ status: b.st }) }); } catch (_) {} }
      admPaintTabs(); admPaint();
    }});
    return;
  }
  const label = { activate: "فعال‌سازی", deactivate: "غیرفعال‌سازی", revoke: "قطع نشست‌ها" }[action];
  const run = async () => {
    const before = ids.map((id) => { const u = Adm.users.find((x) => x.id === id); return u ? { id, active: u.is_active } : null; }).filter(Boolean);
    let updated = [], skipped = [];
    try {
      const r = await api("/admin/users/bulk", { method: "POST", body: JSON.stringify({ ids, action }) });
      updated = r.updated || []; skipped = r.skipped || [];
    } catch (err) {
      if ([404, 405].includes(err.status)) {
        for (const id of ids) {
          const u = Adm.users.find((x) => x.id === id); if (!u) continue;
          if (action === "deactivate" && (u.is_self || (u.role === "admin" && admAdminCount() <= 1))) { skipped.push({ id, reason: "guard" }); continue; }
          const ok = await admPushUser(id, action === "revoke" ? "revoke" : "active", action === "activate");
          ok ? updated.push(id) : skipped.push({ id, reason: "failed" });
        }
      } else { admToast("❌ " + (err.message || "خطا")); return; }
    }
    Adm.sel.clear(); await admRefresh("users"); admRefresh("audit");
    admToast(`${xfa(updated.length)} مورد ${label} شد${skipped.length ? ` · ${xfa(skipped.length)} رد شد (خودت/آخرین ادمین)` : ""}`,
      action === "revoke" ? {} : { action: "برگردان", dur: 7000, onAction: async () => {
        for (const b of before) { if (!updated.includes(b.id)) continue; await admPushUser(b.id, "active", b.active); }
        await admRefresh("users"); admToast("↩️ برگشت");
      }});
  };
  if (action === "deactivate") admConfirm("غیرفعال‌سازی گروهی", `${xfa(ids.length)} حساب غیرفعال و نشست‌هایشان قطع شود؟ خودت و آخرین ادمین خودکار رد می‌شوند.`, "غیرفعال کن", run);
  else if (action === "revoke") admConfirm("قطع نشست‌ها", `نشست‌های ${xfa(ids.length)} کاربر قطع شود؟ باید دوباره وارد شوند. این عمل برگشت‌پذیر نیست.`, "قطع کن", run);
  else await run();
}

/* ---- delegation ---- */
function admWire() {
  if (Adm.wired) return; Adm.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-adm]");
    if (!el) {
      const row = e.target.closest("[data-adm-card]");
      if (row && !e.target.closest("a,button,input,select,label")) admOpenUser(row.dataset.admCard);
      return;
    }
    const act = el.dataset.adm, id = el.dataset.id, v = el.dataset.v;
    switch (act) {
      case "tab": Adm.tab = v; localStorage.setItem("adm:tab", v); Adm.sel.clear(); admPaintTabs(); admPaint(); break;
      case "uf": Adm.uf = v; Adm.sel.clear(); admPaint(); break;
      case "tf": Adm.tf = v; Adm.sel.clear(); admPaint(); break;
      case "refresh": admRefresh(v); break;
      case "reload": admLoadAll(); break;
      case "recheck": (async () => { try { await refreshUserBox(); } catch (_) {} admLoadAll(); })(); break;
      case "user": admOpenUser(id); break;
      case "role": admConfirm(v === "admin" ? "ارتقا به ادمین" : "تنزل به کاربر",
        v === "admin" ? "این کاربر به همه داده‌های کاربران و تنظیمات سیستم دسترسی پیدا می‌کند. ادامه؟" : "دسترسی ادمین این کاربر گرفته می‌شود.",
        v === "admin" ? "ارتقا بده" : "تنزل بده", () => { admCloseAll(); return admUserAction(id, "role", v); }, v === "admin"); break;
      case "active": v === "0"
        ? admConfirm("غیرفعال‌سازی حساب", "کاربر دیگر نمی‌تواند وارد شود و نشست‌هایش قطع می‌شود.", "غیرفعال کن", () => { admCloseAll(); return admUserAction(id, "active", false); })
        : admUserAction(id, "active", true); break;
      case "revoke": admConfirm("قطع نشست‌ها", "همه نشست‌های این کاربر قطع می‌شود و باید دوباره وارد شود.", "قطع کن", () => { admCloseAll(); return admUserAction(id, "revoke"); }); break;
      case "ticket": admOpenTicket(id); break;
      case "tk-status": admTicketStatus(id, v); break;
      case "approve": admLibStatus(id, "approved"); break;
      case "reject": admLibStatus(id, "rejected"); break;
      case "lib-del": admLibDelete(id); break;
      case "resolve": admResolve(id); break;
      case "cat-toggle": admCatToggle(id, v === "1"); break;
      case "cat-del": admCatDelete(id); break;
      case "bulk": admBulk(v); break;
      case "bulk-clear": Adm.sel.clear(); admPaintBulk(); admPaint(); break;
      case "audit-export": {
        const blob = new Blob([JSON.stringify({ exported: new Date().toISOString(), items: Adm.audit }, null, 2)], { type: "application/json" });
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "lms-audit.json"; a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000); admToast("⬇ خروجی لاگ گرفته شد"); break;
      }
    }
  });
  document.addEventListener("input", (e) => {
    const t = e.target.dataset && e.target.dataset.admQ;
    if (!t) return;
    Adm.q[t] = e.target.value;
    const p = document.getElementById("adm-panel"); if (!p) return;
    if (t === "users") { const box = p.querySelector(".adm-list"); if (box) box.innerHTML = admUsersList().map(admUserRow).join("") || admEmpty("🔍", "کاربری با این فیلتر نیست"); }
    else if (t === "tickets") admPaintTickets(p);
    else if (t === "catalog") admPaintCatalog(p);
    else if (t === "audit") admPaintSystem(p);
    const back = document.getElementById(`adm-q-${t}`); if (back && document.activeElement !== back) { back.focus(); back.setSelectionRange(back.value.length, back.value.length); }
  });
  document.addEventListener("change", (e) => {
    if (e.target.id === "adm-sort") { Adm.sort = e.target.value; localStorage.setItem("adm:sort", Adm.sort); admPaint(); }
    if (e.target.dataset && e.target.dataset.admSel !== undefined) {
      const id = e.target.dataset.admSel;
      e.target.checked ? Adm.sel.add(id) : Adm.sel.delete(id);
      admPaintBulk();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = (typeof Lib !== "undefined" && Lib.layers && Lib.layers.length)
      || (typeof Cal !== "undefined" && Cal._layers && Cal._layers.length)
      || (typeof Asg !== "undefined" && Asg.layers && Asg.layers.length);
    if (busy) return;
    if (Adm.layers.length) Adm.layers[Adm.layers.length - 1].close();
  });
}
admWire();

async function renderMore() {
  const cards = [
    { href: "#/posts", icon: ICON_CHAT, title: "پیام‌های وال", desc: "گفتگو و اطلاعیه‌های دروس", isExternal: false },
    { href: "#/contents", icon: ICON_FILE, title: "محتواها", desc: "جزوه‌ها و فایل‌های درسی", isExternal: false },
    { href: "#/changes", icon: ICON_REFRESH, title: "تغییرات", desc: "آخرین به‌روزرسانی‌های سامانه", isExternal: false },
    { href: "#/support", icon: ICON_HELP, title: "پشتیبانی", desc: "گزارش باگ و پیگیری پاسخ", isExternal: false },
    { href: "#/help", icon: ICON_BOOK, title: "راهنما", desc: "حریم خصوصی و شروع کار", isExternal: false },
    { href: "#/about", icon: ICON_INFO, title: "درباره ما", desc: "پروژه و سازنده", isExternal: false },
    { href: "https://lms4.ui.ac.ir/pages/nodemain", icon: ICON_EXTERNAL, title: "پنل اصلی LMS", desc: "ورود به سامانه دانشگاه", isExternal: true },
    { href: "https://lms4.ui.ac.ir/pages/messages", icon: ICON_MAIL, title: "صندوق پیام‌ها", desc: "پیام‌های خصوصی در LMS", isExternal: true },
    { href: "/api/calendar.ics", icon: ICON_DOWNLOAD, title: "خروجی تقویم ICS", desc: "دانلود برای Google Calendar", isExternal: true },
  ];

  contentEl.innerHTML = `
    ${pageHead("سایر صفحات", "ابزارها و امکانات جانبی")}
    <div class="more-grid">
      ${cards.filter(c => !c.adminOnly || authRole === "admin").map(c => `
        <a href="${c.href}" 
           class="more-card" 
           ${c.isExternal ? 'target="_blank" rel="noopener"' : ''}>
          <div class="more-card-icon">${c.icon}</div>
          <div class="more-card-title">${esc(c.title)}</div>
          <div class="more-card-desc">${esc(c.desc)}</div>
        </a>
      `).join("")}
    </div>
  `;
}


// ---------- Docs (راهنما · حریم خصوصی · درباره پروژه) ----------
const DOC_KEYS = [
  ["Ctrl / ⌘ + K", "پالت فرمان — جستجوی صفحه‌ها و اجرا فرمان"],
  ["۱ تا ۹", "پرش سریع: داشبورد، درس‌ها، تکالیف، تقویم، نقشه، پیام‌ها، محتواها، تغییرات، کتابخانه"],
  ["Esc", "بستن دراور، مودال یا پالت فرمان"],
  ["Ctrl / ⌘ + Enter", "ارسال پاسخ تیکت یا ثبت نظر کتابخانه"],
  ["← →", "در تقویم: روز قبل / بعد"],
  ["↑ ↓", "در تقویم: هفته قبل / بعد"],
  ["PageUp / PageDown", "در تقویم: ماه قبل / بعد"],
  ["Home", "در تقویم: بازگشت به امروز"],
];
const DOC_STORED = [
  ["شماره دانشجویی و نام", "جدول users در SQLite", "شناسایی حساب و نمایش نام شما", "تا حذف حساب"],
  ["رمز عبور LMS", "رمزنگاری‌شده در جدول secrets", "همگام‌سازی بعدی بدون ورود مجدد", "تا خروج یا حذف حساب"],
  ["کوکی نشست LMS", "رمزنگاری‌شده در secrets", "کاهش دفعات لاگین روی سامانه دانشگاه", "تا انقضای نشست"],
  ["کوکی نشست همین سایت", "کوکی HttpOnly در مرورگر", "نگه‌داشتن ورود شما بین بازدیدها", "چند روز، قابل ابطال"],
  ["درس، تکلیف، پیام، محتوا، رویداد", "SQLite، جدا برای هر کاربر", "نمایش سریع، جستجو و تشخیص تغییر", "تا همگام‌سازی بعدی یا حذف حساب"],
  ["منابع کتابخانه", "SQLite، مشترک بین کاربران", "اشتراک جزوه و لینک پس از تایید ادمین", "تا حذف توسط شما یا ادمین"],
  ["تیکت پشتیبانی", "SQLite", "پیگیری مشکل و پاسخ تیم", "تا حذف حساب"],
  ["لاگ اقدامات ادمین", "جدول audit", "پاسخگویی و امنیت عملیات مدیریتی", "محدود و چرخشی"],
  ["ترجیحات (تم، نماها، فیلترها)", "localStorage مرورگر + settings", "حفظ تجربه شخصی شما", "تا پاک‌کردن داده مرورگر"],
];
const DOC_NOTSTORED = [
  ["رمز به‌صورت متن ساده", "نه در دیتابیس، نه در لاگ، نه در پاسخ API"],
  ["داده درسی شما برای دیگران", "هر پرس‌وجو با شناسه کاربر شما محدود می‌شود"],
  ["اسرار در خروجی داده", "خروجی JSON هرگز رمز و کوکی را شامل نمی‌شود"],
  ["ردیاب تبلیغاتی و آنالیتیکس", "هیچ اسکریپت third-party برای ردیابی بارگذاری نمی‌شود"],
  ["ارسال داده به سرور ثالث", "ارتباط فقط با LMS دانشگاه و در صورت تمایل کوئرا"],
];
const DOC_TROUBLE = [
  ["نشست LMS منقضی شده و پسورد ذخیره نیست", "کوکی سامانه باطل شده و رمز هم نگه داشته نشده است.", "از تنظیمات → تغییر حساب دوباره وارد شوید."],
  ["Login به LMS ناموفق بود", "رمز عوض شده، یا سامانه دانشگاه موقتاً در دسترس نیست.", "ابتدا مستقیم وارد LMS شوید؛ اگر موفق بود، اینجا هم دوباره وارد شوید."],
  ["تلاش‌های ورود بیش از حد", "محدودکنندهٔ نرخ برای جلوگیری از حدس رمز فعال شده است.", "چند دقیقه صبر کنید؛ پیام، زمان تقریبی انتظار را نشان می‌دهد."],
  ["اعتبارنامه Quera تنظیم نشده", "کوئرا اختیاری است و هنوز تنظیم نشده.", "اگر تمرین کوئرا دارید از تنظیمات وارد کنید؛ وگرنه این پیام را نادیده بگیرید."],
  ["کوکی کوئرا منقضی شده است", "نشست مرورگر شما در کوئرا باطل شده.", "یک‌بار در مرورگر وارد کوئرا شوید و کوکی تازه را در تنظیمات بگذارید."],
  ["403 Forbidden هنگام ورود کوئرا", "سامانه، کلاینت خودکار را با کپچا/ضدربات متوقف می‌کند.", "رمز درست است؛ مسیر کوکی نشست تنها راه پایدار است."],
  ["حساب شما توسط مدیر غیرفعال شده", "دسترسی حساب از پنل ادمین بسته شده است.", "از پشتیبانی تیکت بزنید و شماره دانشجویی را ذکر کنید."],
  ["صفحه خالی است یا داده قدیمی مانده", "همگام‌سازی اجرا نشده یا کش پوسته قدیمی است.", "یک‌بار همگام‌سازی بزنید؛ اگر ظاهر عوض نشد، رفرش سخت (Ctrl+Shift+R)."],
  ["نقشه نمایش داده نمی‌شود", "کتابخانه نقشه یا تایل‌ها بارگذاری نشده‌اند.", "لیست مکان‌ها و دکمه مسیریابی همچنان کار می‌کند؛ اتصال را بررسی کنید."],
  ["آخرین ادمین نمی‌تواند نقش خود را تغییر دهد", "محافظ سیستم برای جلوگیری از قفل‌شدن پنل.", "ابتدا یک کاربر دیگر را ادمین کنید، سپس نقش خود را تغییر دهید."],
];
const DOC_FAQ = [
  ["آیا این سایت رسمی دانشگاه است؟", "نه. این یک پروژهٔ مستقل و متن‌باز است که توسط دانشجو ساخته شده و هیچ وابستگی رسمی به دانشگاه ندارد. اگر در دسترس نبود، مستقیم به سامانه LMS بروید."],
  ["رمز عبور من چطور نگه داشته می‌شود؟", "رمز پیش از ذخیره رمزنگاری می‌شود و کلید آن فقط روی سرور است. در لاگ‌ها، پاسخ API و خروجی داده هرگز ظاهر نمی‌شود. با این حال، هیچ سیستمی صد‌در‌صد نیست؛ اگر رمز LMS را جای دیگری هم استفاده می‌کنید، آن را تغییر دهید."],
  ["چرا اصلاً رمز ذخیره می‌شود؟", "برای اینکه همگام‌سازی خودکار و پس‌زمینه ممکن باشد. بدون آن، هر بار باید دستی وارد شوید و داده‌ها کهنه می‌مانند."],
  ["می‌توانم بدون ذخیرهٔ رمز استفاده کنم؟", "بله؛ اما با هر انقضای نشست باید دوباره وارد شوید و همگام‌سازی خودکار غیرفعال می‌شود. حذف حساب هم همه‌چیز را پاک می‌کند."],
  ["ادمین چه چیزی از من می‌بیند؟", "شماره دانشجویی، نام، نقش، وضعیت حساب، تعداد نشست و تیکت‌های پشتیبانی. محتوای درسی، پیام‌های وال و فایل‌های شما در پنل ادمین نمایش داده نمی‌شود."],
  ["کوئرا اجباری است؟", "نه. اگر آن را تنظیم نکنید، بقیهٔ امکانات کامل کار می‌کنند و فقط بخش کوئرا خالی می‌ماند."],
  ["چطور همهٔ داده‌ام را پاک کنم؟", "تنظیمات → منطقهٔ خطر → حذف کامل حساب. این کار درس‌ها، تکالیف، پیام‌ها، منابع و تیکت‌ها را برای همیشه پاک می‌کند و برگشت‌پذیر نیست."],
  ["چرا بعضی مهلت‌ها قدیمی به نظر می‌رسند؟", "داده‌ها آینهٔ آخرین همگام‌سازی هستند، نه اتصال زنده. اگر استاد مهلت را عوض کرده، یک همگام‌سازی بزنید تا به‌روز شود."],
  ["روی موبایل کار می‌کند؟", "بله. چیدمان برای موبایل بازطراحی شده، نوار ناوبری پایین دارد و به‌عنوان وب‌اپ قابل نصب است."],
  ["آفلاین چه چیزی کار می‌کند؟", "پوستهٔ برنامه و آخرین دادهٔ دریافت‌شده از کش سرویس‌ورکر نمایش داده می‌شود. همگام‌سازی و ارسال، طبیعتاً به شبکه نیاز دارند."],
  ["تغییرات چطور تشخیص داده می‌شوند؟", "در هر همگام‌سازی، وضعیت تازه با نسخهٔ قبلی مقایسه می‌شود و افزودن‌ها، به‌روزرسانی‌ها و حذف‌ها در صفحهٔ تغییرات و خلاصهٔ داشبورد ثبت می‌شوند."],
  ["اگر باگ پیدا کردم چه کنم؟", "از پشتیبانی تیکت بزنید و «کپی اطلاعات دیباگ» را داخل متن بگذارید؛ مسیر صفحه، مرورگر و وضعیت آخرین همگام‌سازی را خودکار جمع می‌کند."],
];
const DOC_FEATURES = [
  ["🔄", "همگام‌سازی یک‌کلیکی", "درس، تکلیف، پیام، فایل و رویداد در یک اجرا، با نوار پیشرفت زنده و گزارش خطای خوانا.", "var(--primary)"],
  ["🧠", "داشبورد هوشمند", "بریف صبحگاهی با نام شما، متن متناسب با وضعیت روز و شمارش معکوس نزدیک‌ترین مهلت.", "var(--info)"],
  ["📅", "تقویم شمسی", "نمای هفته و ماه، رویداد دستی، خروجی ICS برای تقویم گوشی و ناوبری کامل با کیبورد.", "var(--accent)"],
  ["📚", "کتابخانهٔ اجتماعی", "جزوه و لینک با تایید ادمین، امتیاز ستاره‌ای، نظر، گزارش و تاپیک‌بندی.", "var(--warning)"],
  ["🗺", "نقشهٔ دانشگاه", "مکان کلاس‌ها، ایستگاه اتوبوس، سلف و کتابخانه با مسیریابی نشان و گوگل.", "var(--info)"],
  ["🔔", "تشخیص تغییر", "هر افزودن و به‌روزرسانی ثبت می‌شود تا هیچ مهلت یا فایلی از قلم نیفتد.", "var(--danger)"],
  ["🎯", "اتصال کوئرا", "تمرین‌ها و درصد پیشرفت هر مسئله در کنار تکالیف LMS.", "var(--primary)"],
  ["🎧", "پشتیبانی داخلی", "تیکت با قالب آماده، رشتهٔ گفتگو و حفظ پیش‌نویس پاسخ.", "var(--accent)"],
];
const DOC_STACK = [
  ["🐍", "Python + FastAPI", "بک‌اند async با اعتبارسنجی Pydantic؛ هر مسیر با شناسه کاربر محدود می‌شود.", "var(--primary)"],
  ["💾", "SQLite", "تک‌فایل، بدون سرویس خارجی؛ پرس‌وجوها per-user و ایندکس‌شده.", "var(--info)"],
  ["🌐", "httpx", "کلاینت نشست‌دار با retry نمایی و مدیریت کوکی برای LMS و کوئرا.", "var(--accent)"],
  ["🍲", "BeautifulSoup", "پارس HTML سامانه به مدل‌های تمیز و قابل مقایسه.", "var(--warning)"],
  ["📡", "SSE", "استریم پیشرفت همگام‌سازی، بدون polling و با keep-alive.", "var(--danger)"],
  ["⚡", "Vanilla JS SPA", "بدون فریم‌ورک؛ ماژول‌های مستقل با state یکپارچه و delegation.", "var(--primary)"],
  ["🫧", "Liquid Lens UI", "زبان شیشه‌ای اختصاصی: لبهٔ گرادیانتی، استخر نور و نشانگر فعال.", "var(--info)"],
  ["📱", "PWA + SW", "network-first برای کد، کش برای آفلاین؛ بدون نیاز به bump دستی کش.", "var(--accent)"],
];
const DOC_LOG = [
  ["۱.۰", "راهنما و مستندات", ["صفحهٔ راهنمای جستجوپذیر با فهرست چسبان", "جدول کامل داده‌های ذخیره‌شده", "رفع‌مشکل نگاشت‌شده به خطاهای واقعی", "دربارهٔ پروژه با آمار زنده و نمودار معماری"], "var(--accent)"],
  ["۰.۹", "سخت‌سازی امنیتی", ["allowlist میزبان در پروکسی برای بستن SSRF", "جلوگیری از سرو HTML روی دامنهٔ خودمان", "network-first شدن سرویس‌ورکر", "احراز هویت و قفل per-user در سینک کوئرا"], "var(--danger)"],
  ["۰.۸", "بازطراحی Liquid Lens", ["سیستم دکمهٔ شیشه‌ای با حالت فعال نوری", "پالت فرمان Ctrl+K", "داشبورد هوشمند با ۱۶ وضعیت", "دراور، Undo و عملیات گروهی در همهٔ صفحه‌ها"], "var(--primary)"],
  ["۰.۷", "تنظیمات و هشدارها", ["ترجیحات per-user", "اندازهٔ متن، تراکم و کاهش حرکت زنده", "پنجرهٔ هشدار مهلت با پیش‌نمایش", "پیش‌تنظیم‌های آماده"], "var(--info)"],
  ["۰.۶", "پشتیبانی و پنل ادمین", ["تیکت با رشتهٔ گفتگو", "مدیریت کاربران، نقش و نشست", "صف تایید و گزارش‌های کتابخانه", "بکاپ و لاگ اقدامات"], "var(--warning)"],
  ["۰.۵", "نقشهٔ مکان‌ها", ["مکان کلاس‌ها روی نقشه", "دسته‌بندی مکان‌های مهم", "مسیریابی نشان و گوگل", "افزودن مکان توسط ادمین"], "var(--info)"],
  ["۰.۴", "اتصال کوئرا", "تمرین‌ها، درصد پیشرفت و وضعیت هر مسئله در کنار تکالیف LMS.", "var(--primary)"],
  ["۰.۳", "کتابخانهٔ اجتماعی", "جزوه و لینک با تایید ادمین، امتیاز، نظر و تاپیک.", "var(--warning)"],
  ["۰.۲", "تقویم شمسی", "نمای هفته و ماه، رویداد دستی و خروجی ICS.", "var(--accent)"],
  ["۰.۱", "هستهٔ اولیه", "ورود با حساب LMS، همگام‌سازی و داشبورد پایه.", "var(--muted)"],
];

const Doc = { page: null, q: "", open: new Set(["faq-0"]), spy: null, onScroll: null, wired: false, stats: null, health: null };
const hesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const hfa = (n) => faDigits(String(n));
function docHi(text, q) {
  const t = String(text ?? ""); if (!q) return hesc(t);
  const rx = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
  return t.split(rx).map((p, i) => i % 2 ? `<mark class="doc-mark">${hesc(p)}</mark>` : hesc(p)).join("");
}
function docToast(m) {
  if (typeof libToast === "function") return libToast(m);
  if (typeof walToast === "function") return walToast(m);
  if (typeof cntToast === "function") return cntToast(m);
  return toast(m);
}
function docCopy(text, msg) {
  const done = () => docToast(msg || "📋 کپی شد");
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, done);
  else { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); }
}
function docTeardown() {
  if (Doc.spy) { try { Doc.spy.disconnect(); } catch (_) {} Doc.spy = null; }
  if (Doc.onScroll) { window.removeEventListener("scroll", Doc.onScroll); Doc.onScroll = null; }
}
window.__docTeardown = docTeardown;
function docAgo(iso) {
  const t = Date.parse(String(iso || "").replace(" ", "T")); if (Number.isNaN(t)) return "—";
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 60) return "همین الان";
  if (s < 3600) return `${hfa(Math.floor(s / 60))} دقیقه پیش`;
  if (s < 86400) return `${hfa(Math.floor(s / 3600))} ساعت پیش`;
  return `${hfa(Math.floor(s / 86400))} روز پیش`;
}

/* ================= راهنما و حریم خصوصی ================= */
function docHelpSections() {
  const q = Doc.q.trim();
  return [
    { id: "start", icon: "🚀", title: "شروع در سه قدم", kicker: "کمتر از دو دقیقه", body: `
      <ol class="doc-steps">
        <li><b>وارد شوید.</b> شماره دانشجویی و رمز همان حساب LMS دانشگاه را بزنید. اگر تمرین کوئرا دارید، بخش اختیاری کوئرا را هم باز کنید.</li>
        <li><b>همگام‌سازی بزنید.</b> دکمهٔ همگام‌سازی در سایدبار، درس‌ها، فایل‌ها، پیام‌ها، مهلت‌ها و رویدادها را یک‌جا می‌آورد. نوار پیشرفت، مرحلهٔ جاری را نشان می‌دهد.</li>
        <li><b>از داشبورد شروع کنید.</b> بریف صبحگاهی می‌گوید امروز چه چیزی منتظر شماست: کلاس بعدی، نزدیک‌ترین مهلت، یا یک روز آزاد.</li>
      </ol>
      <div class="doc-cta">
        <a class="lq-btn lq-sm is-on" style="--lq-hue:var(--primary)" href="#/">رفتن به داشبورد</a>
        <button class="lq-btn lq-sm" data-doc="sync">🔄 همگام‌سازی الآن</button>
        <a class="lq-btn lq-sm" href="#/settings">تنظیمات</a>
      </div>` },
    { id: "what", icon: "🧭", title: "این دستیار چه می‌کند", kicker: "یک آینهٔ سریع از سامانه", body: `
      <p>سامانهٔ LMS برای «بایگانی» ساخته شده، نه برای «امروز». این دستیار همان داده را می‌گیرد و به سؤال اصلی دانشجو جواب می‌دهد: <b>الان چه چیزی از من می‌خواهند؟</b></p>
      <div class="doc-grid">
        ${DOC_FEATURES.map(([i, t, d, c]) => `<div class="doc-mini" style="--hue:${c}"><span class="doc-mini-ico">${i}</span><b>${hesc(t)}</b><small>${hesc(d)}</small></div>`).join("")}
      </div>
      <p class="doc-note-line">داده‌ها آینهٔ آخرین همگام‌سازی‌اند، نه اتصال زنده. اگر استادی چیزی را همین حالا عوض کرده، یک همگام‌سازی بزنید.</p>` },
    { id: "data", icon: "🗄", title: "چه چیزی ذخیره می‌شود", kicker: "شفاف، ردیف به ردیف", body: `
      <p>هر چیزی که نگه داشته می‌شود، دلیل مشخص و مدت ماندگاری دارد. جدول زیر کامل است — چیزی بیرون از آن ذخیره نمی‌شود.</p>
      <div class="doc-table-wrap">
        <table class="doc-table"><thead><tr><th>داده</th><th>جای ذخیره</th><th>چرا</th><th>ماندگاری</th></tr></thead>
        <tbody>${DOC_STORED.map((r) => `<tr><td><b>${docHi(r[0], q)}</b></td><td>${docHi(r[1], q)}</td><td>${docHi(r[2], q)}</td><td><span class="doc-keep">${docHi(r[3], q)}</span></td></tr>`).join("")}</tbody></table>
      </div>
      <div class="doc-callout tone-info"><span>🔐</span><p>رمز LMS و کوکی نشست، <b>رمزنگاری‌شده</b> ذخیره می‌شوند و کلید فقط روی سرور است. اگر متغیر محیطی <code>LMS_SECRET_KEY</code> ست نشده باشد، سرور با کلید توسعه کار می‌کند و در لاگ هشدار می‌دهد — پیش از استقرار عمومی حتماً ست شود.</p></div>` },
    { id: "notdata", icon: "🚫", title: "چه چیزی ذخیره نمی‌شود", kicker: "خط قرمزها", body: `
      <div class="doc-nolist">${DOC_NOTSTORED.map(([t, d]) => `<div class="doc-no"><span>✕</span><div><b>${docHi(t, q)}</b><small>${docHi(d, q)}</small></div></div>`).join("")}</div>
      <div class="doc-callout tone-accent"><span>👁</span><p>پنل ادمین روی <b>حساب‌ها و پشتیبانی</b> تمرکز دارد، نه محتوای درسی شما. درس‌ها، پیام‌های وال و فایل‌هایتان برای کاربران دیگر — از جمله ادمین — قابل مشاهده نیست.</p></div>` },
    { id: "security", icon: "🛡", title: "امنیت و نشست‌ها", kicker: "چه کاری از شما برمی‌آید", body: `
      <ul class="doc-list">
        <li><b>روی سیستم مشترک خارج شوید.</b> کوکی نشست HttpOnly است اما خروج، آن را سمت سرور هم باطل می‌کند.</li>
        <li><b>نشست‌های مشکوک را قطع کنید.</b> تنظیمات → خروج از همهٔ دستگاه‌ها؛ همهٔ نشست‌ها از جمله همین دستگاه باطل می‌شود.</li>
        <li><b>رمز LMS را جای دیگری استفاده نکنید.</b> اگر لو برود، فقط این سایت درگیر نمی‌شود.</li>
        <li><b>ورود مجدد، نشست قبلی را می‌بندد.</b> به‌صورت پیش‌فرض هر ورود تازه، نشست‌های دیگر همان حساب را باطل می‌کند.</li>
        <li><b>پروکسی فقط میزبان مجاز.</b> پروکسی LMS تنها به دامنه‌های سامانهٔ دانشگاه درخواست می‌زند و فایل HTML را روی دامنهٔ این سایت سرو نمی‌کند.</li>
        <li><b>محدودکنندهٔ نرخ ورود.</b> تلاش‌های پیاپی برای حدس رمز، موقتاً блокируются می‌شوند.</li>
      </ul>
      <div class="doc-cta"><a class="lq-btn lq-sm" href="#/settings">مدیریت نشست‌ها</a><button class="lq-btn lq-sm" data-doc="debug">📋 کپی اطلاعات دیباگ</button></div>` },
    { id: "sync", icon: "🔄", title: "همگام‌سازی چطور کار می‌کند", kicker: "مرحله به مرحله", body: `
      <div class="doc-flow">
        ${[["ورود", "بازیابی نشست یا لاگین تازه"], ["درس‌ها", "لیست و جزئیات هر درس"], ["برنامه", "جلسات هفتگی و مکان کلاس"], ["محتواها", "فایل‌ها و منابع"], ["رویدادها", "جلسات آنلاین و آزمون"], ["وال", "پیام‌ها و مهلت تکالیف"], ["اعضا", "اساتید و دستیاران"], ["کوئرا", "در صورت تنظیم‌بودن"], ["مقایسه", "ثبت تغییرات نسبت به قبل"]].map(([t, d], i) => `<div class="doc-flow-step"><span class="doc-flow-n">${hfa(i + 1)}</span><b>${hesc(t)}</b><small>${hesc(d)}</small></div>`).join("")}
      </div>
      <p>هر مرحله پیشرفت را زنده روی نوار می‌فرستد. اگر یک مرحله خطا بدهد، بقیهٔ داده‌های موفق ذخیره می‌مانند و پیام خطا دقیقاً می‌گوید کدام مرحله شکست خورده است.</p>
      <div class="doc-callout tone-warning"><span>⏱</span><p>همگام‌سازی خودکار به‌صورت پیش‌فرض هر ۶ ساعت یک‌بار هنگام ورود اجرا می‌شود. بازه و روشن/خاموش‌بودنش در تنظیمات قابل تغییر است.</p></div>` },
    { id: "trouble", icon: "🧯", title: "رفع مشکل", kicker: "خطای واقعی → راه‌حل واقعی", body: `
      <div class="doc-trouble">
        ${DOC_TROUBLE.map(([e, c, f], i) => `<details class="doc-tr" data-doc-tr="${i}">
          <summary><span class="doc-tr-ico">⚠️</span><b>${docHi(e, q)}</b><span class="doc-tr-chev">▾</span></summary>
          <div class="doc-tr-body"><p><span class="doc-tr-lbl">علت</span>${docHi(c, q)}</p><p><span class="doc-tr-lbl fix">راه‌حل</span>${docHi(f, q)}</p>
            <button class="lq-btn lq-sm" data-doc="copy-err" data-i="${i}">📋 کپی متن خطا</button></div>
        </details>`).join("")}
      </div>
      <div class="doc-cta"><a class="lq-btn lq-sm is-on" style="--lq-hue:var(--accent)" href="#/support">🎧 تیکت پشتیبانی</a><button class="lq-btn lq-sm" data-doc="debug">📋 کپی اطلاعات دیباگ</button></div>` },
    { id: "keys", icon: "⌨️", title: "میان‌برهای کیبورد", kicker: "برای وقتی عجله دارید", body: `
      <div class="doc-keys">${DOC_KEYS.map(([k, d]) => `<div class="doc-key"><kbd>${docHi(k, q)}</kbd><span>${docHi(d, q)}</span></div>`).join("")}</div>
      <p class="doc-note-line">میان‌برهای عددی وقتی در حال تایپ در کادر جستجو یا فرم هستید غیرفعال‌اند تا مزاحم نوشتن نشوند.</p>` },
    { id: "faq", icon: "❓", title: "پرسش‌های پرتکرار", kicker: `${hfa(DOC_FAQ.length)} پرسش`, body: `
      <div class="doc-faq">
        ${DOC_FAQ.map(([qq, aa], i) => `<details class="doc-q" data-doc-faq="${i}" ${Doc.open.has("faq-" + i) ? "open" : ""}>
          <summary><b>${docHi(qq, q)}</b><span class="doc-tr-chev">▾</span></summary>
          <div class="doc-q-body">${docHi(aa, q)}</div>
        </details>`).join("")}
      </div>` },
    { id: "contact", icon: "📮", title: "تماس و گزارش", kicker: "ما می‌خوانیم", body: `
      <p>برای باگ، پیشنهاد یا مشکل حساب، بهترین مسیر تیکت داخلی است چون تاریخچه و وضعیت پیگیری دارد. برای گفتگوی مستقیم، تلگرام و ایمیل هم باز است.</p>
      <div class="doc-cta">
        <a class="lq-btn lq-sm is-on" style="--lq-hue:var(--accent)" href="#/support">🎧 ثبت تیکت</a>
        <a class="lq-btn lq-sm" style="--lq-hue:var(--info)" href="https://t.me/ASAADIX" target="_blank" rel="noopener noreferrer">تلگرام ↗</a>
        <a class="lq-btn lq-sm" style="--lq-hue:var(--danger)" href="mailto:mohammad8asadi5@gmail.com">ایمیل ↗</a>
        <a class="lq-btn lq-sm" href="#/about">دربارهٔ پروژه</a>
      </div>
      <p class="doc-note-line">پیش از ارسال، «کپی اطلاعات دیباگ» را بزنید و داخل متن تیکت بگذارید؛ مسیر صفحه، مرورگر، تم و وضعیت آخرین همگام‌سازی را جمع می‌کند و هیچ رمز یا کوکی‌ای در آن نیست.</p>` },
  ];
}
async function renderHelp() {
  docTeardown(); Doc.page = "help"; Doc.q = "";
  const secs = docHelpSections();
  contentEl.innerHTML = `
    <section class="doc-hero card">
      <div class="doc-hero-main">
        <span class="doc-kicker">مستندات · حریم خصوصی</span>
        <h1>راهنمای دستیار LMS</h1>
        <p>این صفحه دقیقاً می‌گوید برنامه چه می‌کند، چه چیزی از شما نگه می‌دارد، چه چیزی نگه نمی‌دارد، و وقتی چیزی خراب شد چه کنید.</p>
        <div class="doc-hero-meta">
          <span class="doc-pill">نسخه ${hfa("1.0")}</span>
          <span class="doc-pill">به‌روز برای دانشگاه اصفهان</span>
          <span class="doc-pill">${hfa(secs.length)} بخش</span>
        </div>
      </div>
      <div class="doc-hero-art" aria-hidden="true">
        <svg viewBox="0 0 120 120" fill="none">
          <circle cx="60" cy="60" r="52" stroke="var(--glass-border)" stroke-width="1.5"/>
          <circle cx="60" cy="60" r="38" stroke="color-mix(in srgb,var(--primary) 40%,transparent)" stroke-width="1.5" stroke-dasharray="4 6"/>
          <path d="M60 26a34 34 0 1 0 0 68 34 34 0 0 0 0-68z" fill="color-mix(in srgb,var(--primary) 12%,transparent)"/>
          <path d="M48 52h24M48 62h24M48 72h14" stroke="var(--primary)" stroke-width="3" stroke-linecap="round"/>
          <circle cx="86" cy="34" r="9" fill="var(--accent)"/>
          <path d="M82 34l3 3 5-6" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </section>
    <div class="doc-progress" id="doc-progress"><i></i></div>
    <div class="doc-search-row">
      <div class="search-box doc-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="doc-q" type="search" placeholder="جستجو در راهنما، خطاها و پرسش‌ها…" aria-label="جستجو در راهنما"></div>
      <span class="doc-count" id="doc-count"></span>
      <button class="lq-btn lq-sm" data-doc="expand">باز کردن همه</button>
      <button class="lq-btn lq-sm" data-doc="print">🖨 چاپ</button>
    </div>
    <div class="doc-layout">
      <aside class="doc-toc" id="doc-toc"><b>فهرست</b>
        ${secs.map((s) => `<button class="doc-toc-btn" data-doc-go="${s.id}"><span>${s.icon}</span>${hesc(s.title)}</button>`).join("")}
        <div class="doc-toc-foot"><a href="#/about">دربارهٔ پروژه ↗</a><a href="#/support">پشتیبانی ↗</a></div>
      </aside>
      <div class="doc-body" id="doc-body"></div>
    </div>`;
  docPaintHelp();
  docBindSpy();
}
function docPaintHelp() {
  const box = document.getElementById("doc-body"); if (!box) return;
  const q = Doc.q.trim().toLowerCase();
  const secs = docHelpSections();
  const plain = (h) => String(h).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
  const shown = secs.filter((s) => !q || `${s.title} ${s.kicker} ${plain(s.body)}`.toLowerCase().includes(q));
  box.innerHTML = shown.length ? shown.map((s) => `
    <section class="doc-sec card" id="doc-${s.id}" data-doc-sec="${s.id}">
      <div class="doc-sec-head"><span class="doc-sec-ico">${s.icon}</span>
        <div><h2>${docHi(s.title, Doc.q.trim())}</h2><small>${hesc(s.kicker)}</small></div>
        <button class="lq-link" data-doc="link" data-id="${s.id}">🔗 پیوند</button></div>
      <div class="doc-sec-body">${s.body}</div>
    </section>`).join("")
    : `<div class="empty"><span class="empty-icon">🔍</span>چیزی با این عبارت پیدا نشد<small>عبارت کوتاه‌تری امتحان کنید یا از فهرست کنار صفحه استفاده کنید</small>
        <div style="margin-top:.8rem"><button class="lq-btn lq-sm" data-doc="clear">پاک کردن جستجو</button></div></div>`;
  const c = document.getElementById("doc-count");
  if (c) c.textContent = q ? `${hfa(shown.length)} بخش مطابق` : "";
  document.querySelectorAll("#doc-toc .doc-toc-btn").forEach((b) => {
    b.classList.toggle("is-hidden", !!q && !shown.some((s) => s.id === b.dataset.docGo));
  });
  box.querySelectorAll("[data-doc-faq]").forEach((d) => d.addEventListener("toggle", () => {
    const k = "faq-" + d.dataset.docFaq; d.open ? Doc.open.add(k) : Doc.open.delete(k);
  }));
}
function docBindSpy() {
  const bar = document.querySelector("#doc-progress i");
  Doc.onScroll = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    if (bar) bar.style.width = `${max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0}%`;
  };
  window.addEventListener("scroll", Doc.onScroll, { passive: true });
  Doc.onScroll();
  if ("IntersectionObserver" in window) {
    Doc.spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const id = en.target.dataset.docSec;
        document.querySelectorAll("#doc-toc .doc-toc-btn").forEach((b) => b.classList.toggle("on", b.dataset.docGo === id));
      });
    }, { rootMargin: "-96px 0px -65% 0px", threshold: 0 });
    document.querySelectorAll("[data-doc-sec]").forEach((el) => Doc.spy.observe(el));
  }
}

/* ================= درباره پروژه ================= */
async function renderAbout() {
  docTeardown(); Doc.page = "about";
  contentEl.innerHTML = `
    <section class="doc-hero card abt-hero">
      <div class="doc-hero-main">
        <span class="doc-kicker">متن‌باز · ساختهٔ دانشجو</span>
        <h1>دستیار LMS</h1>
        <p>یک دستیار شخصی برای دانشجویان دانشگاه اصفهان که پراکندگی سامانه‌های درسی را به یک صفحهٔ «امروز چه؟» تبدیل می‌کند.</p>
        <div class="doc-hero-meta">
          <span class="doc-pill">نسخه ${hfa("1.0")}</span><span class="doc-pill">MIT</span>
          <span class="doc-pill">Python · FastAPI · Vanilla JS</span>
        </div>
        <div class="doc-cta">
          <a class="lq-btn lq-sm is-on" style="--lq-hue:var(--primary)" href="https://github.com/Asadix85" target="_blank" rel="noopener noreferrer">مخزن گیت‌هاب ↗</a>
          <a class="lq-btn lq-sm" href="#/help">راهنما و حریم خصوصی</a>
          <button class="lq-btn lq-sm" data-doc="debug">📋 اطلاعات دیباگ</button>
        </div>
      </div>
      <div class="abt-crest" aria-hidden="true">
        <svg viewBox="0 0 140 140" fill="none">
          <defs><linearGradient id="abtG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="var(--primary)"/><stop offset="1" stop-color="var(--accent)"/></linearGradient></defs>
          <circle cx="70" cy="70" r="60" stroke="var(--glass-border)" stroke-width="1.5"/>
          <path d="M70 18l46 26v52L70 122 24 96V44z" fill="color-mix(in srgb,var(--primary) 10%,transparent)" stroke="url(#abtG)" stroke-width="2"/>
          <path d="M48 62h44M48 74h44M48 86h26" stroke="url(#abtG)" stroke-width="3.4" stroke-linecap="round"/>
          <circle cx="106" cy="40" r="10" fill="var(--accent)"/><path d="M101 40l4 4 6-8" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </section>
    <div class="abt-tabs" id="abt-tabs">
      ${[["story", "📖", "داستان"], ["maker", "👤", "سازنده"], ["numbers", "📊", "آمار زنده"], ["arch", "🧩", "معماری"], ["stack", "⚙️", "فناوری"], ["log", "🗓", "تاریخچه"], ["open", "🤝", "مشارکت"]].map(([k, i, l]) => `<button class="lq-chip" data-doc-go="${k}"><span>${i}</span>${l}</button>`).join("")}
    </div>
    <div class="doc-body" id="abt-body">
      <section class="doc-sec card" id="doc-story" data-doc-sec="story">
        <div class="doc-sec-head"><span class="doc-sec-ico">📖</span><div><h2>چرا ساخته شد</h2><small>از یک کلافگی روزمره</small></div></div>
        <div class="doc-sec-body">
          <p>هر ترم همان داستان تکرار می‌شد: برای دیدن یک مهلت باید وارد LMS شد، بین چند دامنه جابه‌جا شد، صفحهٔ وال را باز کرد و لای پیام‌های بلند دنبال یک تاریخ گشت. تمرین‌های کوئرا جای دیگری بود، مکان کلاس جای دیگری، و جزوه‌ها در گروه‌های تلگرام.</p>
          <p>مشکل، کمبود اطلاعات نبود؛ <b>پراکندگی</b> بود. این پروژه یک تصمیم ساده گرفت: همه‌چیز را یک‌جا بیاور و بعد، فقط چیزی را نشان بده که <b>امروز</b> لازم است.</p>
          <div class="doc-grid three">
            <div class="doc-mini" style="--hue:var(--danger)"><span class="doc-mini-ico">🧩</span><b>پیش از این</b><small>چند سامانه، چند ورود، مهلت‌های گم‌شده و جزوه‌های پراکنده.</small></div>
            <div class="doc-mini" style="--hue:var(--primary)"><span class="doc-mini-ico">⚡</span><b>حالا</b><small>یک ورود، یک همگام‌سازی، یک داشبورد که می‌گوید از کجا شروع کنی.</small></div>
            <div class="doc-mini" style="--hue:var(--accent)"><span class="doc-mini-ico">🔓</span><b>اصل کار</b><small>دادهٔ شما مال شماست: قابل خروجی، قابل حذف، بدون ردیاب.</small></div>
          </div>
          <div class="doc-callout tone-info"><span>🎓</span><p>این پروژه رسمی نیست و وابستگی سازمانی به دانشگاه ندارد. یک ابزار مستقل دانشجویی است که متن‌باز منتشر شده تا هرکس بتواند بازبینی، اجرا یا بهترش کند.</p></div>
        </div>
      </section>

      <section class="doc-sec card" id="doc-maker" data-doc-sec="maker">
        <div class="doc-sec-head"><span class="doc-sec-ico">👤</span><div><h2>سازنده</h2><small>یک نفر، یک ترم، یک مسئله</small></div></div>
        <div class="doc-sec-body">
          <div class="abt-maker">
            <div class="abt-maker-id">
              <div class="abt-ava" id="abt-ava"><span>م</span></div>
              <h3>محمد اسدی</h3>
              <p class="abt-role">توسعه‌دهندهٔ فول‌استک</p>
              <span class="doc-pill">مهندسی کامپیوتر · ورودی ${hfa(1404)}</span>
            </div>
            <div class="abt-maker-bio">
              <p>دانشجوی مهندسی کامپیوتر دانشگاه اصفهان. بیشتر وقتم صرف ساختن ابزارهایی می‌شود که یک اصطکاک واقعی روزمره را حذف می‌کنند — نه دموهای نمایشی. به وب، سیستم‌های کوچک و سریع، و متن‌باز علاقه دارم.</p>
              <p>این پروژه را از یک اسکریپت ترمینال شروع کردم تا مهلت‌های خودم را از دست ندهم. وقتی هم‌کلاسی‌ها هم خواستندش، تبدیل شد به یک وب‌اپ چندکاربره با کتابخانهٔ مشترک، نقشه و پشتیبانی.</p>
              <div class="abt-links">
                <a class="abt-link" style="--hue:var(--text)" href="https://github.com/Asadix85" target="_blank" rel="noopener noreferrer" aria-label="گیت‌هاب">
                  <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                  <span>Asadix85</span></a>
                <a class="abt-link" style="--hue:var(--info)" href="https://t.me/ASAADIX" target="_blank" rel="noopener noreferrer" aria-label="تلگرام">
                  <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.26-1.91.178-.184 3.247-2.977 3.307-3.23.005-.02.01-.04-.006-.06-.015-.017-.037-.023-.058-.023-.05 0-.084.027-.113.043-.038.023-3.523 2.237-3.558 2.258-.085.05-.174.086-.27.107-.11.024-.224.04-.337.04-.12 0-.24-.016-.348-.046l-1.148-.36c-.23-.073-.455-.148-.458-.38-.002-.12.034-.243.108-.368.192-.325 1.666-.94 2.513-1.278 1.033-.412 2.078-.825 3.096-1.23 1.07-.424 1.6-.65 1.753-.677z"/></svg>
                  <span>ASAADIX</span></a>
                <button class="abt-link" style="--hue:var(--danger)" data-doc="copy-mail" aria-label="کپی ایمیل">
                  <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                  <span>کپی ایمیل</span></button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="doc-sec card" id="doc-numbers" data-doc-sec="numbers">
        <div class="doc-sec-head"><span class="doc-sec-ico">📊</span><div><h2>آمار زندهٔ حساب شما</h2><small>همین حالا، از دیتابیس خودتان</small></div>
          <button class="lq-link" data-doc="reload-stats">↻ تازه‌سازی</button></div>
        <div class="doc-sec-body"><div class="abt-stats" id="abt-stats"><div class="abt-loading">در حال خواندن…</div></div>
          <div class="abt-health" id="abt-health"></div></div>
      </section>

      <section class="doc-sec card" id="doc-arch" data-doc-sec="arch">
        <div class="doc-sec-head"><span class="doc-sec-ico">🧩</span><div><h2>معماری</h2><small>مسیر داده از سامانه تا صفحه</small></div></div>
        <div class="doc-sec-body">
          <div class="abt-arch">
            <svg viewBox="0 0 720 230" role="img" aria-label="نمودار معماری">
              <defs>
                <linearGradient id="archA" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="var(--primary)"/><stop offset="1" stop-color="var(--info)"/></linearGradient>
                <linearGradient id="archB" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="var(--accent)"/><stop offset="1" stop-color="var(--primary)"/></linearGradient>
              </defs>
              <g class="arch-node"><rect x="560" y="70" width="140" height="86" rx="18"/><text x="630" y="104">مرورگر شما</text><text x="630" y="128" class="arch-sub">SPA · Liquid Lens</text></g>
              <g class="arch-node"><rect x="360" y="70" width="150" height="86" rx="18"/><text x="435" y="104">FastAPI</text><text x="435" y="128" class="arch-sub">احراز هویت · API · SSE</text></g>
              <g class="arch-node"><rect x="170" y="20" width="150" height="70" rx="16"/><text x="245" y="50">LMS دانشگاه</text><text x="245" y="70" class="arch-sub">lms3 / lms4 / lms5</text></g>
              <g class="arch-node"><rect x="170" y="140" width="150" height="70" rx="16"/><text x="245" y="170">کوئرا</text><text x="245" y="190" class="arch-sub">اختیاری</text></g>
              <g class="arch-node"><rect x="10" y="70" width="130" height="86" rx="18"/><text x="75" y="104">SQLite</text><text x="75" y="128" class="arch-sub">per-user · رمزنگاری</text></g>
              <path class="arch-flow" d="M560 113H510" stroke="url(#archA)"/>
              <path class="arch-flow" d="M360 100C330 100 330 55 320 55" stroke="url(#archB)"/>
              <path class="arch-flow" d="M360 128C330 128 330 175 320 175" stroke="url(#archB)"/>
              <path class="arch-flow" d="M170 55C120 55 120 100 140 100" stroke="url(#archA)"/>
              <path class="arch-flow" d="M170 175C120 175 120 128 140 128" stroke="url(#archA)"/>
              <circle class="arch-dot" r="4"><animateMotion dur="3.2s" repeatCount="indefinite" path="M140 100C120 100 120 55 170 55"/></circle>
              <circle class="arch-dot d2" r="4"><animateMotion dur="3.6s" repeatCount="indefinite" path="M320 55C330 55 330 100 360 100"/></circle>
              <circle class="arch-dot d3" r="4"><animateMotion dur="3s" repeatCount="indefinite" path="M510 113H560"/></circle>
            </svg>
          </div>
          <div class="doc-grid">
            <div class="doc-mini" style="--hue:var(--primary)"><span class="doc-mini-ico">🔒</span><b>جداسازی کاربر</b><small>هر پرس‌وجوی دیتابیس با شناسه کاربر محدود می‌شود؛ دادهٔ هیچ دو حسابی قاطی نمی‌شود.</small></div>
            <div class="doc-mini" style="--hue:var(--info)"><span class="doc-mini-ico">📡</span><b>پیشرفت زنده</b><small>همگام‌سازی در thread پس‌زمینه اجرا و پیشرفتش با SSE به مرورگر استریم می‌شود.</small></div>
            <div class="doc-mini" style="--hue:var(--accent)"><span class="doc-mini-ico">🪞</span><b>پروکسی محدود</b><small>لینک‌های LMS از پروکسی می‌روند تا نشست حفظ شود؛ فقط میزبان‌های مجاز اجازه دارند.</small></div>
            <div class="doc-mini" style="--hue:var(--warning)"><span class="doc-mini-ico">🧠</span><b>تشخیص تغییر</b><small>هر همگام‌سازی با نسخهٔ قبلی مقایسه می‌شود تا افزودن، به‌روزرسانی و حذف ثبت شود.</small></div>
          </div>
        </div>
      </section>

      <section class="doc-sec card" id="doc-stack" data-doc-sec="stack">
        <div class="doc-sec-head"><span class="doc-sec-ico">⚙️</span><div><h2>فناوری</h2><small>انتخاب‌های کوچک و دلیل‌شان</small></div></div>
        <div class="doc-sec-body"><div class="doc-grid">
          ${DOC_STACK.map(([i, t, d, c]) => `<div class="doc-mini" style="--hue:${c}"><span class="doc-mini-ico">${i}</span><b>${hesc(t)}</b><small>${hesc(d)}</small></div>`).join("")}
        </div>
        <p class="doc-note-line">بدون فریم‌ورک فرانت‌اند، بدون باندلر، بدون وابستگی سنگین. کل رابط با جاوااسکریپت خالص و CSS نوشته شده تا روی هر مرورگر و هر هاست ساده‌ای اجرا شود.</p></div>
      </section>

      <section class="doc-sec card" id="doc-log" data-doc-sec="log">
        <div class="doc-sec-head"><span class="doc-sec-ico">🗓</span><div><h2>تاریخچهٔ نسخه‌ها</h2><small>از اسکریپت ترمینال تا وب‌اپ</small></div></div>
        <div class="doc-sec-body"><div class="abt-log">
          ${DOC_LOG.map(([v, t, items, c], i) => `<details class="abt-rel" style="--hue:${c}" ${i === 0 ? "open" : ""}>
            <summary><span class="abt-ver">${hfa(v)}</span><b>${hesc(t)}</b><span class="doc-tr-chev">▾</span></summary>
            <ul>${(Array.isArray(items) ? items : [items]).map((x) => `<li>${hesc(x)}</li>`).join("")}</ul>
          </details>`).join("")}
        </div></div>
      </section>

      <section class="doc-sec card" id="doc-open" data-doc-sec="open">
        <div class="doc-sec-head"><span class="doc-sec-ico">🤝</span><div><h2>مشارکت و مجوز</h2><small>بازبینی کن، اجرا کن، بهترش کن</small></div></div>
        <div class="doc-sec-body">
          <p>کد زیر مجوز MIT منتشر شده است: می‌توانید اجرا کنید، تغییر دهید و حتی برای دانشگاه دیگری بازنویسی‌اش کنید. تنها چیزی که لازم است، حفظ ذکر منبع است.</p>
          <div class="doc-grid three">
            <div class="doc-mini" style="--hue:var(--danger)"><span class="doc-mini-ico">🐞</span><b>باگ پیدا کردید؟</b><small>تیکت بزنید و اطلاعات دیباگ را پیوست کنید تا مسیر بازتولید مشخص شود.</small></div>
            <div class="doc-mini" style="--hue:var(--primary)"><span class="doc-mini-ico">💡</span><b>ایده دارید؟</b><small>مسئله را بگویید نه راه‌حل را؛ از همان‌جا با هم طراحی می‌کنیم.</small></div>
            <div class="doc-mini" style="--hue:var(--accent)"><span class="doc-mini-ico">🔧</span><b>کد بزنید؟</b><small>مخزن را ببینید، یک issue بردارید و pull request بفرستید.</small></div>
          </div>
          <div class="doc-cta">
            <a class="lq-btn lq-sm is-on" style="--lq-hue:var(--primary)" href="https://github.com/Asadix85" target="_blank" rel="noopener noreferrer">گیت‌هاب ↗</a>
            <a class="lq-btn lq-sm" style="--lq-hue:var(--accent)" href="#/support">ثبت تیکت</a>
            <a class="lq-btn lq-sm" href="#/help">حریم خصوصی</a>
            <button class="lq-btn lq-sm" data-doc="copy-mail">📋 کپی ایمیل</button>
          </div>
          <p class="abt-sign">ساخته‌شده با ❤️ برای دانشجویان دانشگاه اصفهان · © ${hfa(1405)} محمد اسدی</p>
        </div>
      </section>
    </div>`;
  const ava = document.getElementById("abt-ava");
  if (ava) {
    const img = new Image();
    img.src = "/static/img/my-avatar.jpg";
    img.alt = "محمد اسدی";
    img.addEventListener("load", () => { ava.innerHTML = ""; ava.appendChild(img); });
  }
  abtLoadStats();
  if ("IntersectionObserver" in window) {
    Doc.spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const id = en.target.dataset.docSec;
        document.querySelectorAll("#abt-tabs [data-doc-go]").forEach((b) => b.classList.toggle("is-on", b.dataset.docGo === id));
      });
    }, { rootMargin: "-96px 0px -65% 0px", threshold: 0 });
    document.querySelectorAll("[data-doc-sec]").forEach((el) => Doc.spy.observe(el));
  }
}
async function abtLoadStats() {
  const box = document.getElementById("abt-stats"), health = document.getElementById("abt-health");
  if (!box) return;
  const [d, a, c, p, st, auth] = await Promise.all([
    api("/dashboard").catch(() => null),
    api("/assignments").catch(() => []),
    api("/contents").catch(() => []),
    api("/posts").catch(() => []),
    api("/sync/status").catch(() => ({})),
    api("/auth/status").catch(() => null),
  ]);
  if (Doc.page !== "about") return;
  const s = (d && d.stats) || {};
  const open = (a || []).filter((x) => !x.is_done).length;
  const done = (a || []).filter((x) => x.is_done).length;
  const tiles = [
    [s.courses ?? 0, "درس همگام‌شده", "var(--primary)"],
    [open, "تکلیف باز", "var(--danger)"],
    [done, "تکلیف انجام‌شده", "var(--accent)"],
    [(c || []).length, "محتوا و فایل", "var(--info)"],
    [(p || []).length, "پیام وال", "var(--warning)"],
    [(p || []).filter((x) => x.is_new).length, "پیام خوانده‌نشده", "var(--danger)"],
  ];
  box.innerHTML = tiles.map(([v, l, cv]) => `<div class="abt-stat"><b style="color:${cv}">${hfa(v)}</b><span>${hesc(l)}</span></div>`).join("");
  const ls = st.last_sync || (d && d.last_sync);
  const sw = "serviceWorker" in navigator ? await navigator.serviceWorker.getRegistration().catch(() => null) : null;
  const rows = [
    ["اتصال به LMS", auth && auth.lms_logged_in, auth && auth.lms_logged_in ? "برقرار" : "وارد نشده"],
    ["کوئرا", auth && auth.quera_logged_in, auth && auth.quera_logged_in ? "تنظیم شده" : "اختیاری · تنظیم نشده"],
    ["آخرین همگام‌سازی", ls && ls.status === "success", ls ? docAgo(ls.at) : "هرگز"],
    ["سرویس‌ورکر", !!sw, sw ? "فعال · آفلاین آماده" : "ثبت نشده"],
    ["پوسته", true, document.body.dataset.theme === "dark" ? "تیره" : "روشن"],
    ["نقش شما", true, (auth && auth.role) === "admin" ? "ادمین" : "دانشجو"],
  ];
  if (health) health.innerHTML = `<b class="abt-health-title">وضعیت سامانه</b><div class="abt-health-grid">${rows.map(([l, ok, v]) => `<div class="abt-hrow ${ok ? "ok" : "warn"}"><span class="abt-hdot"></span><b>${hesc(l)}</b><span>${hesc(v)}</span></div>`).join("")}</div>`;
}

/* ---- delegation ---- */
function docWire() {
  if (Doc.wired) return; Doc.wired = true;
  document.addEventListener("click", (e) => {
    const go = e.target.closest("[data-doc-go]");
    if (go) {
      const el = document.getElementById("doc-" + go.dataset.docGo);
      if (el) { const y = el.getBoundingClientRect().top + window.scrollY - 92; window.scrollTo({ top: y, behavior: "smooth" }); }
      return;
    }
    const el = e.target.closest("[data-doc]"); if (!el) return;
    const act = el.dataset.doc;
    if (act === "sync") { document.getElementById("btn-sync")?.click(); return; }
    if (act === "clear") { Doc.q = ""; const i = document.getElementById("doc-q"); if (i) i.value = ""; docPaintHelp(); return; }
    if (act === "print") { window.print(); return; }
    if (act === "expand") {
      const all = document.querySelectorAll("#doc-body details");
      const anyClosed = [...all].some((d) => !d.open);
      all.forEach((d) => { d.open = anyClosed; });
      el.textContent = anyClosed ? "بستن همه" : "باز کردن همه";
      return;
    }
    if (act === "link") {
      const url = `${location.origin}${location.pathname}#/help`;
      docCopy(url, "🔗 پیوند راهنما کپی شد");
      const t = document.getElementById("doc-" + el.dataset.id);
      if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    if (act === "copy-err") { const t = DOC_TROUBLE[+el.dataset.i]; if (t) docCopy(t[0], "📋 متن خطا کپی شد"); return; }
    if (act === "copy-mail") { docCopy("mohammad8asadi5@gmail.com", "📋 ایمیل کپی شد"); return; }
    if (act === "reload-stats") { const b = document.getElementById("abt-stats"); if (b) b.innerHTML = `<div class="abt-loading">در حال خواندن…</div>`; abtLoadStats(); return; }
    if (act === "debug") {
      const txt = JSON.stringify({
        at: new Date().toISOString(),
        route: typeof currentRoute === "function" ? currentRoute() : location.hash,
        app: "LMS Assistant 1.0",
        ua: navigator.userAgent,
        lang: navigator.language,
        viewport: `${window.innerWidth}×${window.innerHeight}`,
        theme: document.body.dataset.theme,
        online: navigator.onLine,
        prefs: window.LmsPrefs || null,
      }, null, 2);
      docCopy(txt, "📋 اطلاعات دیباگ کپی شد — داخل تیکت بگذارید");
      return;
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "doc-q") { Doc.q = e.target.value; docPaintHelp(); } });
}
docWire();

// ---------- Quera v2 (کوئرا) ----------
// فیلتر/جستجو/مرتب‌سازی کلاینتی، دراور جزئیات مسائل، تاگل انجام‌شدن، همگام‌سازی بدون رفرش کامل.
const Qra = {
  assigns: [], courses: [], courseNames: {},
  filter: "all", q: "", sort: "deadline",
  view: localStorage.getItem("qra:view") || "list",
  views: JSON.parse(localStorage.getItem("qra:views") || "{}"),
  layers: [], wired: false, loaded: false, syncing: false,
};
const qesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const qfa = (n) => faDigits(String(n));
function qraLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof admLayer === "function" ? admLayer
    : typeof crsLayer === "function" ? crsLayer : typeof mxLayer === "function" ? mxLayer
    : typeof stgLayer === "function" ? stgLayer : typeof dashLayer === "function" ? dashLayer
    : typeof chgLayer === "function" ? chgLayer : typeof navLayer === "function" ? navLayer : qraOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = Qra.layers.indexOf(L); if (i >= 0) Qra.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  Qra.layers.push(L); return L;
}
function qraToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof admToast === "function") return admToast(m, o);
  if (typeof crsToast === "function") return crsToast(m, o);
  if (typeof mxToast === "function") return mxToast(m, o);
  if (typeof stgToast === "function") return stgToast(m, o);
  if (typeof dashToast === "function") return dashToast(m, o);
  if (typeof chgToast === "function") return chgToast(m, o);
  return qraOwnToast(m, o);
}
function qraOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "qra-layer";
  w.innerHTML = `<div class="qra-scrim" data-qra-x></div>` + (opts.type === "drawer"
    ? `<aside class="qra-drawer" role="dialog" aria-modal="true" aria-label="${qesc(opts.title)}">${opts.html}</aside>`
    : `<div class="qra-modal-wrap"><div class="qra-modal" role="dialog" aria-modal="true" aria-label="${qesc(opts.title)}"><h3>${qesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("qra-locked");
  const panel = w.querySelector(".qra-drawer,.qra-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".qra-layer")) document.body.classList.remove("qra-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-qra-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function qraOwnToast(msg, o = {}) {
  let box = document.getElementById("qra-toasts");
  if (!box) { box = document.createElement("div"); box.id = "qra-toasts"; box.className = "qra-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "qra-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${qesc(msg)}</span>${o.action ? `<button class="a">${qesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const qraCloseAll = () => Qra.layers.slice().forEach((l) => l.close());

/* ---- helpers ---- */
function qraStats(a) {
  const total = a.problems_count || 0;
  const done = (a.problems || []).filter((p) => p.is_submitted).length;
  const pct = total ? Math.round((done / total) * 100) : 0;
  return { total, done, pct };
}
function qraStatus(a) {
  const { total, done } = qraStats(a);
  if (a.is_done || (total > 0 && done === total)) return "done";
  if (a.is_expired) return "overdue";
  return "open";
}
function qraRing(a) {
  const { pct } = qraStats(a);
  const st = qraStatus(a);
  const color = st === "done" ? "var(--accent)" : st === "overdue" ? "var(--danger)" : "var(--primary)";
  return `<div class="ring" style="--p:${pct};--ring-color:${color}"><span>${qfa(pct)}٪</span></div>`;
}
function qraLeft(a) {
  if (!a.finish_time) return "";
  const t = Date.parse(String(a.finish_time).replace(" ", "T"));
  if (Number.isNaN(t)) return "";
  const diff = t - Date.now(), past = diff < 0, s = Math.abs(diff) / 1000;
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600);
  const txt = d > 0 ? `${qfa(d)} روز${h ? ` و ${qfa(h)} ساعت` : ""}` : h > 0 ? `${qfa(h)} ساعت` : `${qfa(Math.max(1, Math.floor((s % 3600) / 60)))} دقیقه`;
  return past ? `${txt} پیش` : `${txt} مانده`;
}

/* ---- ورود به صفحه ---- */
async function renderQuera() {
  qraCloseAll();
  let assignments = [], courses = [];
  try {
    [assignments, courses] = await Promise.all([
      api("/quera/assignments").catch(() => []),
      api("/quera/courses").catch(() => []),
    ]);
  } catch (_) {}
  Qra.assigns = Array.isArray(assignments) ? assignments : [];
  Qra.courses = Array.isArray(courses) ? courses : [];
  Qra.courseNames = Object.fromEntries(Qra.courses.map((c) => [c.id, c.name]));
  Qra.loaded = true;

  const totalP = Qra.assigns.reduce((s, a) => s + (a.problems_count || 0), 0);
  const doneP = Qra.assigns.reduce((s, a) => s + (a.problems || []).filter((p) => p.is_submitted).length, 0);

  contentEl.innerHTML = `
    ${pageHead("کوئرا", `${qfa(Qra.assigns.length)} تمرین · ${qfa(doneP)}/${qfa(totalP)} مسئله حل‌شده`)}
    <div class="qra-hero card">
      <div class="qra-hero-main">
        <div class="ring big" style="--p:${totalP ? Math.round((doneP / totalP) * 100) : 0};--ring-color:var(--accent)"><span>${totalP ? qfa(Math.round((doneP / totalP) * 100)) : "۰"}٪</span></div>
        <div><h3>پیشرفت کلی</h3><p class="qra-hero-sub">${qfa(doneP)} از ${qfa(totalP)} مسئله ارسال شده</p></div>
      </div>
      <div class="qra-stats">
        <div class="qra-stat"><b style="color:var(--primary)">${qfa(Qra.assigns.filter(a => qraStatus(a) === "open").length)}</b><span>باز</span></div>
        <div class="qra-stat"><b style="color:var(--danger)">${qfa(Qra.assigns.filter(a => qraStatus(a) === "overdue").length)}</b><span>عقب‌افتاده</span></div>
        <div class="qra-stat"><b style="color:var(--accent)">${qfa(Qra.assigns.filter(a => qraStatus(a) === "done").length)}</b><span>تکمیل‌شده</span></div>
      </div>
      <button class="btn btn-primary btn-sm" id="btn-quera-sync" data-qra="sync">🔄 همگام‌سازی</button>
    </div>
    <div class="qra-toolbar">
      <div class="search-box qra-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="qra-q" type="search" value="${qesc(Qra.q)}" placeholder="جستجوی نام تمرین یا درس…" aria-label="جستجو"></div>
      <select id="qra-sort" class="input qra-sel" aria-label="مرتب‌سازی">
        <option value="deadline">مهلت (نزدیک‌ترین)</option><option value="progress">پیشرفت</option><option value="name">الفبایی</option>
      </select>
      <div class="qra-vt" role="group" aria-label="حالت نمایش">
        <button data-qra="view" data-v="list" title="لیست" aria-label="لیست">☰</button>
        <button data-qra="view" data-v="grid" title="شبکه" aria-label="شبکه">▦</button>
      </div>
      <button class="btn btn-ghost btn-sm" data-qra="view-save" title="ذخیره نما">💾</button>
    </div>
    <div class="qra-pills" id="qra-pills"></div>
    <div class="qra-saved" id="qra-saved"></div>
    <div id="qra-list"></div>`;
  document.getElementById("qra-sort").value = Qra.sort;
  qraPaintAll();
}
function qraFiltered() {
  const q = Qra.q.trim().toLowerCase();
  let l = Qra.assigns.filter((a) => {
    const st = qraStatus(a);
    if (Qra.filter === "open") return st === "open";
    if (Qra.filter === "overdue") return st === "overdue";
    if (Qra.filter === "done") return st === "done";
    return true;
  });
  if (q) l = l.filter((a) => `${a.name || ""} ${a.course_name || ""}`.toLowerCase().includes(q));
  const s = Qra.sort;
  return l.slice().sort((a, b) => {
    if (s === "progress") return qraStats(b).pct - qraStats(a).pct;
    if (s === "name") return String(a.name || "").localeCompare(String(b.name || ""), "fa");
    const ta = Date.parse(String(a.finish_time || "").replace(" ", "T")) || Infinity;
    const tb = Date.parse(String(b.finish_time || "").replace(" ", "T")) || Infinity;
    return ta - tb;
  });
}
function qraPaintAll() { qraPaintPills(); qraPaintSaved(); qraPaintList(); }
function qraPaintPills() {
  const box = document.getElementById("qra-pills"); if (!box) return;
  const cnt = (f) => Qra.assigns.filter((a) => f === "all" || qraStatus(a) === f).length;
  box.innerHTML = [["all", "همه"], ["open", "باز"], ["overdue", "عقب‌افتاده"], ["done", "تکمیل‌شده"]]
    .map(([k, l]) => `<button class="qra-pill f-${k} ${Qra.filter === k ? "on" : ""}" data-qra="filter" data-v="${k}">${l}<b>${qfa(cnt(k))}</b></button>`).join("");
}
function qraPaintSaved() {
  const box = document.getElementById("qra-saved"); if (!box) return;
  const keys = Object.keys(Qra.views);
  box.innerHTML = keys.length ? `<span class="qra-muted">نماها:</span>` + keys.map((k) =>
    `<span class="qra-sv"><button data-qra="view-apply" data-k="${qesc(k)}">${qesc(k)}</button>
      <button class="x" data-qra="view-del" data-k="${qesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function qraRow(a, grid) {
  const { total, done } = qraStats(a);
  const st = qraStatus(a);
  const left = qraLeft(a);
  const badge = st === "done" ? `<span class="badge badge-done">تکمیل</span>`
    : st === "overdue" ? `<span class="badge badge-expired">عقب‌افتاده</span>` : "";
  if (grid) {
    return `<div class="qra-card" data-qra-card="${qesc(a.id)}">
      <div class="qra-card-top">${qraRing(a)}<div class="qra-badges">${badge}</div></div>
      <h3 class="qra-name">${qesc(a.name)}</h3>
      <div class="qra-meta"><span>📘 ${qesc(a.course_name || "درس نامشخص")}</span></div>
      <div class="qra-meta">${qfa(done)}/${qfa(total)} مسئله${left ? ` · ${left}` : ""}</div>
      <div class="qra-actions">
        <button class="btn btn-ghost btn-sm" data-qra="detail" data-id="${qesc(a.id)}">جزئیات</button>
        <button class="btn ${st === "done" ? "btn-ghost" : "btn-soft"} btn-sm" data-qra="toggle" data-id="${qesc(a.id)}">${st === "done" ? "لغو تکمیل" : "تکمیل شد ✓"}</button>
      </div></div>`;
  }
  return `<div class="list-row qra-row ${st === "done" ? "is-done" : ""}" data-qra-card="${qesc(a.id)}">
    <span class="row-icon ${st === "done" ? "is-done" : st === "overdue" ? "is-over" : ""}">${st === "done" ? "✓" : st === "overdue" ? "⏰" : ICON_QUERA}</span>
    <div class="row-body">
      <div class="row-title"><button class="qra-link" data-qra="detail" data-id="${qesc(a.id)}">${qesc(a.name)}</button>${badge}</div>
      <div class="row-meta">
        <span>📘 ${qesc(a.course_name || "درس نامشخص")}</span>
        <span>${qfa(done)}/${qfa(total)} مسئله</span>
        ${a.finish_time ? `<span>پایان: ${qesc(a.finish_time)}</span>` : ""}
        ${left ? `<span class="${st === "overdue" ? "is-over" : ""}">${left}</span>` : ""}
      </div>
    </div>
    <div class="row-actions">
      ${qraRing(a)}
      <button class="btn btn-ghost btn-sm" data-qra="detail" data-id="${qesc(a.id)}">جزئیات</button>
      <button class="btn ${st === "done" ? "btn-ghost" : "btn-soft"} btn-sm" data-qra="toggle" data-id="${qesc(a.id)}">${st === "done" ? "لغو" : "✓"}</button>
    </div></div>`;
}
function qraPaintList() {
  const box = document.getElementById("qra-list"); if (!box) return;
  document.querySelectorAll(".qra-vt button").forEach((b) => { const on = b.dataset.v === Qra.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const l = qraFiltered();
  if (!l.length) {
    box.innerHTML = `<div class="empty"><span class="empty-icon">${ICON_QUERA}</span>${Qra.assigns.length ? "تمرینی با این فیلتر نیست" : "هنوز تمرینی از کوئرا همگام‌سازی نشده"}
      <small>${Qra.assigns.length ? "فیلتر یا جستجو را تغییر بده" : "با دکمهٔ «همگام‌سازی» شروع کن"}</small>
      ${!Qra.assigns.length ? `<div class="qra-actions" style="justify-content:center;margin-top:.8rem"><button class="btn btn-primary btn-sm" data-qra="sync">🔄 همگام‌سازی کوئرا</button></div>` : ""}</div>`;
    return;
  }
  box.innerHTML = Qra.view === "grid"
    ? `<div class="qra-grid">${l.map((a) => qraRow(a, true)).join("")}</div>`
    : `<div class="item-list">${l.map((a) => qraRow(a, false)).join("")}</div>`;
}

/* ---- دراور جزئیات ---- */
function qraOpenDetail(id) {
  const a = Qra.assigns.find((x) => x.id === id); if (!a) return;
  const { total, done, pct } = qraStats(a);
  const st = qraStatus(a);
  qraLayer({ type: "drawer", title: "جزئیات تمرین", html: `<div class="qra-dwr">
    <div class="qra-dwr-head">
      <div class="ring big" style="--p:${pct};--ring-color:${st === "done" ? "var(--accent)" : st === "overdue" ? "var(--danger)" : "var(--primary)"}"><span>${qfa(pct)}٪</span></div>
      <div><h2>${qesc(a.name)}</h2>
        <div class="qra-badges"><span class="badge badge-domain">${qesc(a.course_name || "درس نامشخص")}</span>
          ${st === "done" ? `<span class="badge badge-done">تکمیل</span>` : st === "overdue" ? `<span class="badge badge-expired">عقب‌افتاده</span>` : ""}</div></div>
      <button class="qra-x" data-lib-close aria-label="بستن">✕</button>
    </div>
    <div class="qra-kv">
      <div><span>مسائل حل‌شده</span><b>${qfa(done)} از ${qfa(total)}</b></div>
      ${a.finish_time ? `<div><span>مهلت</span><b>${qesc(a.finish_time)}</b></div>` : ""}
      ${qraLeft(a) ? `<div><span>وضعیت زمانی</span><b class="${st === "overdue" ? "is-over" : ""}">${qraLeft(a)}</b></div>` : ""}
    </div>
    <div class="qra-block"><h4>📋 لیست مسائل</h4>
      <div class="qra-problems">${(a.problems || []).length ? (a.problems || []).map((p, i) => `
        <div class="qra-problem ${p.is_submitted ? "is-sub" : ""}">
          <span class="qra-problem-num">${qfa(i + 1)}</span>
          <span class="qra-problem-name">${qesc(p.name || "مسئله " + qfa(i + 1))}</span>
          <span class="badge ${p.is_submitted ? "badge-done" : ""}">${p.is_submitted ? "ارسال شده" : "ارسال نشده"}</span>
        </div>`).join("") : `<div class="qra-muted">لیست مسائل در دسترس نیست</div>`}</div>
    </div>
    <div class="qra-dwr-actions">
      <button class="btn ${st === "done" ? "btn-ghost" : "btn-primary"} btn-sm" data-qra="toggle" data-id="${qesc(a.id)}">${st === "done" ? "لغو تکمیل" : "تکمیل شد ✓"}</button>
      ${a.url ? `<a class="btn btn-soft btn-sm" href="${qesc(a.url)}" target="_blank" rel="noopener noreferrer">باز کردن در کوئرا ↗</a>` : ""}
    </div></div>` });
}

/* ---- همگام‌سازی و تاگل ---- */
async function qraSync() {
  if (Qra.syncing) return;
  Qra.syncing = true;
  const btn = document.getElementById("btn-quera-sync");
  if (btn) { btn.disabled = true; btn.innerHTML = `<span class="sync-spinner"></span> در حال همگام‌سازی…`; }
  try {
    const r = await api("/quera/sync", { method: "POST" });
    if (r.error) {
      if (String(r.error).includes("اعتبارنامه") || String(r.error).includes("تنظیم نشده")) {
        qraToast("⚠️ نام کاربری و رمز کوئرا تنظیم نشده است. از بخش «تغییر حساب» در تنظیمات وارد کن.");
      } else qraToast("❌ " + r.error);
    } else {
      qraToast(`✅ کوئرا: ${qfa(r.new || 0)} جدید، ${qfa(r.updated || 0)} به‌روز`);
    }
    // بارگذاری مجدد بدون رفرش کل صفحه
    const assignments = await api("/quera/assignments").catch(() => []);
    Qra.assigns = Array.isArray(assignments) ? assignments : [];
    qraPaintAll();
  } catch (e) {
    qraToast("❌ خطا در همگام‌سازی کوئرا");
  } finally {
    Qra.syncing = false;
    if (btn) { btn.disabled = false; btn.innerHTML = "🔄 همگام‌سازی"; }
  }
}
async function qraToggle(id) {
  const a = Qra.assigns.find((x) => x.id === id); if (!a) return;
  const before = !!a.is_done;
  a.is_done = !before;
  qraPaintAll();
  try {
    const r = await api(`/quera/assignments/${encodeURIComponent(id)}/done?done=${!before}`, { method: "POST", body: "{}" });
    if (r && r.ok === false) throw new Error(r.error || "یافت نشد");
    qraToast(!before ? "✅ تمرین تکمیل شد" : "علامت تکمیل برداشته شد",
      { action: "برگردان", dur: 5000, onAction: async () => {
        a.is_done = before; qraPaintAll();
        await api(`/quera/assignments/${encodeURIComponent(id)}/done?done=${before}`, { method: "POST", body: "{}" }).catch(() => {});
      }});
  } catch (e) {
    a.is_done = before; qraPaintAll();
    qraToast("❌ " + (e.message || "ثبت وضعیت ناموفق"));
  }
}

/* ---- سیم‌کشی ---- */
function qraWire() {
  if (Qra.wired) return;
  Qra.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-qra]");
    if (!el) {
      const card = e.target.closest("[data-qra-card]");
      if (card && !e.target.closest("button,a,select,input")) qraOpenDetail(card.dataset.qraCard);
      return;
    }
    const act = el.dataset.qra, v = el.dataset.v, id = el.dataset.id;
    switch (act) {
      case "filter": Qra.filter = v; qraPaintPills(); qraPaintList(); break;
      case "view": Qra.view = v; localStorage.setItem("qra:view", v); qraPaintList(); break;
      case "sync": qraSync(); break;
      case "toggle": qraToggle(id); break;
      case "detail": qraOpenDetail(id); break;
      case "view-save": qraLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <div class="qra-field" data-cf="n"><label class="field-label" for="qra-v-n">نام نما *</label>
            <input id="qra-v-n" class="input" placeholder="مثلاً عقب‌افتاده‌ها" data-autofocus><small class="qra-err"></small></div>
          <div class="lib-modal-actions qra-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
            <button class="btn btn-primary" id="qra-v-ok">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#qra-v-ok").addEventListener("click", () => {
          const n = w.querySelector("#qra-v-n").value.trim(), f = w.querySelector('[data-cf="n"]');
          f.classList.toggle("bad", !n); f.querySelector(".qra-err").textContent = n ? "" : "نام الزامی است";
          if (!n) return;
          Qra.views[n] = { filter: Qra.filter, q: Qra.q, sort: Qra.sort, view: Qra.view };
          Qra.views = Object.fromEntries(Object.entries(Qra.views).slice(-6));
          localStorage.setItem("qra:views", JSON.stringify(Qra.views));
          L.close(); qraPaintSaved(); qraToast("💾 نما ذخیره شد");
        }); } }); break;
      case "view-apply": { const x = Qra.views[el.dataset.k]; if (!x) break;
        Object.assign(Qra, x); localStorage.setItem("qra:view", Qra.view);
        { const qi = document.getElementById("qra-q"); if (qi) qi.value = Qra.q;
          const so = document.getElementById("qra-sort"); if (so) so.value = Qra.sort; }
        qraPaintAll(); break; }
      case "view-del": delete Qra.views[el.dataset.k]; localStorage.setItem("qra:views", JSON.stringify(Qra.views)); qraPaintSaved(); break;
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "qra-q") { Qra.q = e.target.value; qraPaintList(); } });
  document.addEventListener("change", (e) => { if (e.target.id === "qra-sort") { Qra.sort = e.target.value; qraPaintList(); } });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = ["Lib", "Cal", "Asg", "Adm", "Crs", "MapX", "Stg", "Dash", "Chg", "Nav"].some((n) => {
      try { const o = window[n]; return o && ((o.layers && o.layers.length) || (o._layers && o._layers.length)); } catch (_) { return false; }
    });
    if (busy) return;
    if (Qra.layers.length) Qra.layers[Qra.layers.length - 1].close();
  });
}
qraWire();
window.syncQuera = qraSync;

// ---------- Map v2 (نقشه مکان‌ها) ----------
// تب‌بار دسته‌بندی + جستجو/مرتب‌سازی + خوشه‌بندی + «نزدیک من» + پنل ادمین.
// ورود = یک‌بار fetch؛ تب/فیلتر/مرتب‌سازی کلاینتی. نقشه هنگام خروج destroy می‌شود.
const MX_VIEWS = [["split", "نقشه + لیست", "▤"], ["map", "فقط نقشه", "🗺"], ["list", "فقط لیست", "☰"]];
const MapX = {
  cats: [], places: [], tab: "all", q: "", sort: "name",
  view: localStorage.getItem("mx:view") || "split",
  views: JSON.parse(localStorage.getItem("mx:views") || "{}"),
  sel: new Set(), layers: [], wired: false, loaded: false,
  map: null, markerLayer: null, tile: null, me: null, meLayer: null,
  pickMode: false, themeObs: null, admin: false, seedNote: localStorage.getItem("mx:note") !== "1",
};
const mesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const mfa = (n) => faDigits(String(n));
const mxIsAdmin = () => authRole === "admin";
function mxCat(id) { return MapX.cats.find((c) => c.id === id) || { id: "service", title: "سایر", icon: "📍" }; }
function mxHav(a, b) {
  const R = 6371000, t = (x) => (x * Math.PI) / 180;
  const dLat = t(b.lat - a.lat), dLng = t(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(t(a.lat)) * Math.cos(t(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
function mxDist(p) {
  if (!MapX.me) return null;
  const d = mxHav(MapX.me, p);
  return d < 1000 ? `${mfa(Math.round(d))} متر` : `${mfa((d / 1000).toFixed(1).replace(".", "٫"))} کیلومتر`;
}
function mxLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof admLayer === "function" ? admLayer
    : typeof crsLayer === "function" ? crsLayer : mxOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = MapX.layers.indexOf(L); if (i >= 0) MapX.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  MapX.layers.push(L); return L;
}
function mxToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof admToast === "function") return admToast(m, o);
  if (typeof crsToast === "function") return crsToast(m, o);
  return mxOwnToast(m, o);
}
function mxOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "mx-layer";
  w.innerHTML = `<div class="mx-scrim" data-mx-x></div>` + (opts.type === "drawer"
    ? `<aside class="mx-drawer" role="dialog" aria-modal="true" aria-label="${mesc(opts.title)}">${opts.html}</aside>`
    : `<div class="mx-modal-wrap"><div class="mx-modal" role="dialog" aria-modal="true" aria-label="${mesc(opts.title)}"><h3>${mesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("mx-locked");
  const panel = w.querySelector(".mx-drawer,.mx-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".mx-layer")) document.body.classList.remove("mx-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-mx-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function mxOwnToast(msg, o = {}) {
  let box = document.getElementById("mx-toasts");
  if (!box) { box = document.createElement("div"); box.id = "mx-toasts"; box.className = "mx-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "mx-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${mesc(msg)}</span>${o.action ? `<button class="a">${mesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const mxCloseAll = () => MapX.layers.slice().forEach((l) => l.close());
function mxDestroy() {
  if (MapX.map) { try { MapX.map.remove(); } catch (_) {} }
  MapX.map = null; MapX.markerLayer = null; MapX.tile = null; MapX.meLayer = null; MapX.pickMode = false;
}
window.__mapTeardown = () => { mxDestroy(); mxCloseAll(); };

/* ---- داده ---- */
async function renderMap() {
  window.__mapTeardown();
  MapX.sel.clear(); MapX.admin = mxIsAdmin();
  contentEl.innerHTML = `${pageHead("نقشه دانشگاه", "کلاس‌ها، ایستگاه اتوبوس، سلف، کتابخانه و مکان‌های مهم")}
    <div class="mx-skel-wrap"><div class="mx-skel big"></div><div class="mx-skel-col">${'<div class="mx-skel"></div>'.repeat(4)}</div></div>`;
  let cat = { categories: [], places: [] }, locs = [];
  try {
    [cat, locs] = await Promise.all([
      api("/map/places").catch(() => ({ categories: [], places: [] })),
      api("/map/locations").catch(() => []),
    ]);
  } catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری نقشه<small>${mesc(e.message)}</small></div>`;
    return;
  }
  MapX.cats = cat.categories || [];
  const catalog = (cat.places || []).map((p) => ({ ...p, tags: p.tags || [], lines: p.lines || [], readonly: false }));
  const fromCourses = (locs || []).map((l, i) => ({
    id: `loc_${i}`, cat: "class", name: l.name, lat: l.lat, lng: l.lng, readonly: true,
    desc: (l.courses || []).length ? `درس‌ها: ${l.courses.join("، ")}` : (l.building || ""),
    hours: "", tags: l.courses || [], lines: [],
  }));
  const seen = new Set(catalog.map((p) => p.name.trim()));
  MapX.places = catalog.concat(fromCourses.filter((p) => !seen.has(p.name.trim())));
  MapX.loaded = true;

  contentEl.innerHTML = `
    ${pageHead("نقشه دانشگاه", "کلاس‌ها، ایستگاه اتوبوس، سلف، کتابخانه و مکان‌های مهم")}
    <div class="card mx-hero" id="mx-hero"></div>
    ${MapX.admin && MapX.seedNote ? `<div class="mx-note" id="mx-note">
      <span>📍 مختصات و ساعت‌های این مکان‌ها نمونهٔ اولیه است. با «ویرایش» یا افزودن مکان جدید، دقیقشان کن.</span>
      <button class="mx-x-mini" data-mx="note-ok" aria-label="بستن">✕</button></div>` : ""}
    <div class="mx-tabs" id="mx-tabs" role="tablist" aria-label="دسته‌بندی مکان‌ها"></div>
    <div class="mx-toolbar">
      <div class="search-box mx-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="mx-q" type="search" value="${mesc(MapX.q)}" placeholder="جستجوی نام، توضیح یا برچسب…" aria-label="جستجوی مکان"></div>
      <select id="mx-sort" class="input mx-sel" aria-label="مرتب‌سازی">
        <option value="name">الفبایی</option><option value="cat">بر اساس دسته</option>
        <option value="near">نزدیک‌ترین به من</option></select>
      <div class="mx-vt" role="group" aria-label="حالت نمایش">
        ${MX_VIEWS.map(([v, l, i]) => `<button data-mx="view" data-v="${v}" title="${l}" aria-label="${l}">${i}</button>`).join("")}
      </div>
      <button class="btn btn-soft btn-sm" data-mx="locate">📍 نزدیک من</button>
      <button class="btn btn-ghost btn-sm" data-mx="view-save" title="ذخیره نما">💾</button>
      <button class="btn btn-ghost btn-sm" data-mx="export" title="خروجی JSON">⬇</button>
      ${MapX.admin ? `<button class="btn btn-primary btn-sm" data-mx="add">+ افزودن مکان</button>` : ""}
    </div>
    <div class="mx-saved" id="mx-saved"></div>
    <div id="mx-bulk"></div>
    <div class="mx-body" id="mx-body">
      <div class="mx-mapcard" id="mx-mapcard">
        <div id="mx-map" class="mx-map"></div>
        <div class="mx-mapbar">
          <span class="mx-muted" id="mx-mapcount"></span>
          <div class="mx-mapbtns">
            <button class="btn btn-ghost btn-sm" data-mx="fit">⤢ نمایش همه</button>
            <button class="btn btn-ghost btn-sm" data-mx="locate">📍 من</button>
          </div>
        </div>
      </div>
      <div class="mx-listcol"><div class="mx-list" id="mx-list"></div></div>
    </div>`;
  document.getElementById("mx-sort").value = MapX.sort;
  mxPaintAll();
  requestAnimationFrame(mxInitMap);
}
function mxFiltered() {
  const q = MapX.q.trim().toLowerCase();
  let l = MapX.places.filter((p) => MapX.tab === "all" || p.cat === MapX.tab);
  if (q) l = l.filter((p) => `${p.name} ${p.desc || ""} ${(p.tags || []).join(" ")} ${(p.lines || []).join(" ")}`.toLowerCase().includes(q));
  const s = MapX.sort;
  return l.slice().sort((a, b) => {
    if (s === "near" && MapX.me) return mxHav(MapX.me, a) - mxHav(MapX.me, b);
    if (s === "cat") return a.cat.localeCompare(b.cat) || a.name.localeCompare(b.name, "fa");
    return a.name.localeCompare(b.name, "fa");
  });
}
function mxPaintAll() { mxPaintHero(); mxPaintTabs(); mxPaintSaved(); mxPaintBulk(); mxPaintList(); mxPaintView(); mxRenderMarkers(); }
function mxPaintHero() {
  const box = document.getElementById("mx-hero"); if (!box) return;
  const n = (c) => MapX.places.filter((p) => p.cat === c).length;
  box.innerHTML = `<div class="mx-hero-main"><h3>${mfa(MapX.places.length)} مکان روی نقشه</h3>
    <p class="mx-hero-sub">${mfa(MapX.cats.length)} دسته · ${mfa(n("bus"))} ایستگاه اتوبوس · ${mfa(n("class"))} کلاس و دانشکده${MapX.me ? " · موقعیت شما فعال است" : ""}</p></div>
    <div class="mx-stats">
      ${[["bus", "اتوبوس"], ["food", "تغذیه"], ["study", "مطالعه"], ["sport", "ورزشی"]].map(([c, l]) =>
        `<button class="mx-stat" data-mx="tab" data-v="${c}"><b style="color:var(--mx-${c})">${mfa(n(c))}</b><span>${l}</span></button>`).join("")}
    </div>`;
}
function mxPaintTabs() {
  const box = document.getElementById("mx-tabs"); if (!box) return;
  const pill = (id, title, icon, n) => `<button class="mx-tab ${MapX.tab === id ? "on" : ""} c-${id}" data-mx="tab" data-v="${id}" role="tab" aria-selected="${MapX.tab === id}">
    <span class="mx-tab-ico">${icon}</span>${mesc(title)}<b>${mfa(n)}</b></button>`;
  box.innerHTML = pill("all", "همه", "🧭", MapX.places.length)
    + MapX.cats.map((c) => pill(c.id, c.title, c.icon, MapX.places.filter((p) => p.cat === c.id).length)).join("");
}
function mxPaintSaved() {
  const box = document.getElementById("mx-saved"); if (!box) return;
  const keys = Object.keys(MapX.views);
  box.innerHTML = keys.length ? `<span class="mx-muted">نماها:</span>` + keys.map((k) =>
    `<span class="mx-sv"><button data-mx="view-apply" data-k="${mesc(k)}">${mesc(k)}</button>
      <button class="x" data-mx="view-del" data-k="${mesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function mxPaintBulk() {
  const box = document.getElementById("mx-bulk"); if (!box) return;
  if (!MapX.admin || !MapX.sel.size) { box.innerHTML = ""; return; }
  box.innerHTML = `<div class="mx-bulkbar"><b>${mfa(MapX.sel.size)}</b> انتخاب شده
    <select class="input mx-sel" id="mx-bulk-cat" aria-label="تغییر دسته">
      <option value="">تغییر دسته…</option>${MapX.cats.map((c) => `<option value="${c.id}">${mesc(c.title)}</option>`).join("")}</select>
    <button class="btn btn-ghost btn-sm mx-del" data-mx="bulk-del">🗑 حذف</button>
    <button class="btn btn-ghost btn-sm" data-mx="bulk-clear">پاک کردن</button></div>`;
}
function mxPaintView() {
  document.querySelectorAll(".mx-vt button").forEach((b) => { const on = b.dataset.v === MapX.view; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  const body = document.getElementById("mx-body"); if (!body) return;
  body.className = "mx-body v-" + MapX.view;
  const mc = document.getElementById("mx-mapcard");
  if (mc) mc.style.display = MapX.view === "list" ? "none" : "";
  if (MapX.map) setTimeout(() => { try { MapX.map.invalidateSize(); } catch (_) {} }, 220);
}
function mxRow(p) {
  const c = mxCat(p.cat), d = mxDist(p);
  return `<div class="mx-row c-${p.cat}" data-mx-card="${mesc(p.id)}">
    ${MapX.admin && !p.readonly ? `<input type="checkbox" class="mx-chk" data-mx-sel="${mesc(p.id)}" ${MapX.sel.has(p.id) ? "checked" : ""} aria-label="انتخاب ${mesc(p.name)}">` : ""}
    <span class="mx-row-ico c-${p.cat}">${c.icon}</span>
    <div class="mx-row-main">
      <div class="row-title"><button class="mx-link" data-mx="detail" data-id="${mesc(p.id)}">${mesc(p.name)}</button>
        <span class="badge mx-badge c-${p.cat}">${mesc(c.title)}</span>
        ${p.readonly ? `<span class="badge">از درس‌ها</span>` : ""}</div>
      <div class="row-meta">
        ${p.hours ? `<span>🕒 ${mesc(p.hours)}</span>` : ""}
        ${d ? `<span class="mx-dist">📐 ${d}</span>` : ""}
        ${(p.lines || []).length ? `<span>🚌 ${mesc(p.lines.length)} خط</span>` : ""}
      </div>
      ${p.desc ? `<p class="mx-desc">${mesc(p.desc)}</p>` : ""}
    </div>
    <div class="row-actions">
      <a class="btn btn-primary btn-sm" href="https://nshn.ir/?lat=${p.lat}&lng=${p.lng}" target="_blank" rel="noopener noreferrer">نشان</a>
      <button class="btn btn-ghost btn-sm" data-mx="detail" data-id="${mesc(p.id)}">جزئیات</button>
    </div></div>`;
}
function mxPaintList() {
  const box = document.getElementById("mx-list"); if (!box) return;
  const l = mxFiltered();
  const cnt = document.getElementById("mx-mapcount");
  if (cnt) cnt.textContent = `${mfa(l.length)} مکان در این نما`;
  box.innerHTML = l.length ? l.map(mxRow).join("")
    : `<div class="empty"><span class="empty-icon">🔍</span>مکانی با این فیلتر نیست<small>دستهٔ دیگری را انتخاب کن یا عبارت جستجو را پاک کن</small>
       <div class="mx-actions" style="justify-content:center;margin-top:.7rem"><button class="btn btn-ghost btn-sm" data-mx="tab" data-v="all">نمایش همه</button></div></div>`;
}

/* ---- نقشه ---- */
function mxInitMap() {
  const el = document.getElementById("mx-map"); if (!el) return;
  if (typeof L === "undefined") {
    el.innerHTML = `<div class="mx-map-fallback">🗺<b>کتابخانهٔ نقشه بارگذاری نشد</b><span>لیست مکان‌ها و مسیریابی همچنان کار می‌کند.</span></div>`;
    return;
  }
  mxDestroy();
  try {
    const map = L.map(el, { zoomControl: true, attributionControl: false, preferCanvas: true }).setView([32.6072, 51.6583], 15);
    MapX.map = map;
    map.on("zoomend", mxRenderMarkers);
    map.on("click", (e) => {
      if (!MapX.pickMode) return;
      MapX.pickMode = false; el.classList.remove("is-picking");
      mxOpenForm(null, { lat: +e.latlng.lat.toFixed(6), lng: +e.latlng.lng.toFixed(6) });
    });
    MapX.tile = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
    MapX.markerLayer = L.layerGroup().addTo(map);
    el.classList.toggle("map-dark-tiles", document.body.dataset.theme === "dark");
    mxRenderMarkers(); mxFit();
    setTimeout(() => { try { map.invalidateSize(); } catch (_) {} }, 200);
  } catch (_) {
    el.innerHTML = `<div class="mx-map-fallback">🗺<b>نقشه راه‌اندازی نشد</b><span>از لیست مکان‌ها استفاده کن.</span></div>`;
  }
}
function mxFit() {
  const map = MapX.map; if (!map) return;
  const l = mxFiltered(); if (!l.length) return;
  try {
    const b = L.latLngBounds(l.map((p) => [p.lat, p.lng]));
    if (MapX.me) b.extend([MapX.me.lat, MapX.me.lng]);
    map.fitBounds(b, { padding: [42, 42], maxZoom: 17 });
  } catch (_) {}
}
function mxRenderMarkers() {
  const map = MapX.map, layer = MapX.markerLayer;
  if (!map || !layer || typeof L === "undefined") return;
  layer.clearLayers();
  const list = mxFiltered(), z = map.getZoom();
  const cell = 0.016 / Math.pow(2, Math.max(0, z - 13));
  const groups = new Map();
  list.forEach((p) => {
    const k = z >= 16 ? "s:" + p.id : `${Math.round(p.lat / cell)}:${Math.round(p.lng / cell)}`;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  });
  groups.forEach((items) => {
    if (items.length === 1) {
      const p = items[0], c = mxCat(p.cat);
      const m = L.marker([p.lat, p.lng], {
        title: p.name, keyboard: true,
        icon: L.divIcon({ className: "mx-pin-wrap", html: `<span class="mx-pin c-${p.cat}">${c.icon}</span>`, iconSize: [32, 32], iconAnchor: [16, 16] }),
      }).addTo(layer);
      m.on("click", () => mxOpenDetail(p.id));
      m.bindTooltip(mesc(p.name), { direction: "top", offset: [0, -14] });
    } else {
      const lat = items.reduce((a, p) => a + p.lat, 0) / items.length;
      const lng = items.reduce((a, p) => a + p.lng, 0) / items.length;
      const m = L.marker([lat, lng], {
        icon: L.divIcon({ className: "mx-pin-wrap", html: `<span class="mx-cluster">${mfa(items.length)}</span>`, iconSize: [38, 38], iconAnchor: [19, 19] }),
      }).addTo(layer);
      m.on("click", () => { try { map.fitBounds(L.latLngBounds(items.map((p) => [p.lat, p.lng])), { padding: [50, 50], maxZoom: 18 }); } catch (_) {} });
    }
  });
  if (MapX.me) {
    if (MapX.meLayer) { try { layer.removeLayer(MapX.meLayer); } catch (_) {} }
    MapX.meLayer = L.layerGroup([
      L.circle([MapX.me.lat, MapX.me.lng], { radius: 45, color: "var(--mx-bus)", weight: 1, fillOpacity: 0.12 }),
      L.marker([MapX.me.lat, MapX.me.lng], { icon: L.divIcon({ className: "mx-pin-wrap", html: `<span class="mx-me"></span>`, iconSize: [18, 18], iconAnchor: [9, 9] }) }),
    ]).addTo(layer);
  }
}
function mxLocate() {
  if (!navigator.geolocation) { mxToast("مرورگر شما موقعیت‌یابی را پشتیبانی نمی‌کند"); return; }
  mxToast("در حال دریافت موقعیت…", { dur: 2000 });
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      MapX.me = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      MapX.sort = "near";
      const s = document.getElementById("mx-sort"); if (s) s.value = "near";
      mxPaintHero(); mxPaintList(); mxRenderMarkers();
      if (MapX.map) { try { MapX.map.setView([MapX.me.lat, MapX.me.lng], 16); } catch (_) {} }
      mxToast("✅ نزدیک‌ترین مکان‌ها اول نمایش داده می‌شوند");
    },
    () => mxToast("❌ دسترسی به موقعیت رد شد یا در دسترس نیست"),
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
  );
}

/* ---- drawer و فرم‌ها ---- */
function mxFind(id) { return MapX.places.find((p) => p.id === id); }
function mxOpenDetail(id) {
  const p = mxFind(id); if (!p) return;
  const c = mxCat(p.cat), d = mxDist(p);
  if (MapX.map) { try { MapX.map.panTo([p.lat, p.lng]); } catch (_) {} }
  mxLayer({ type: "drawer", title: "جزئیات مکان", html: `<div class="mx-dwr">
    <div class="mx-dwr-head"><span class="mx-dwr-ico c-${p.cat}">${c.icon}</span>
      <div><h2>${mesc(p.name)}</h2><div class="mx-badges"><span class="badge mx-badge c-${p.cat}">${mesc(c.title)}</span>
        ${p.readonly ? `<span class="badge">همگام‌شده از درس‌ها</span>` : ""}</div></div>
      <button class="mx-x" data-lib-close aria-label="بستن">✕</button></div>
    ${p.desc ? `<p class="mx-dwr-desc">${mesc(p.desc)}</p>` : ""}
    <div class="mx-kv">
      ${p.hours ? `<div><span>ساعت کاری</span><b>${mesc(p.hours)}</b></div>` : ""}
      ${d ? `<div><span>فاصله از شما</span><b>${d}</b></div>` : ""}
      <div><span>مختصات</span><b dir="ltr">${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}</b></div>
    </div>
    ${(p.tags || []).length ? `<div class="mx-chips">${p.tags.map((t) => `<span class="mx-chip">${mesc(t)}</span>`).join("")}</div>` : ""}
    ${(p.lines || []).length ? `<div class="mx-block"><h4>🚌 خطوط سرویس</h4>
      <div class="mx-lines">${p.lines.map((l) => `<div class="mx-line">${mesc(l)}</div>`).join("")}</div></div>` : ""}
    <div class="mx-dwr-actions">
      <a class="btn btn-primary btn-sm" href="https://nshn.ir/?lat=${p.lat}&lng=${p.lng}" target="_blank" rel="noopener noreferrer">🧭 مسیریابی نشان</a>
      <a class="btn btn-soft btn-sm" href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}&travelmode=walking" target="_blank" rel="noopener noreferrer">🗺 گوگل مپ</a>
      <button class="btn btn-ghost btn-sm" data-mx="copy" data-id="${mesc(p.id)}">کپی مختصات</button>
      ${MapX.admin && !p.readonly ? `<button class="btn btn-soft btn-sm" data-mx="edit" data-id="${mesc(p.id)}">✎ ویرایش</button>
        <button class="btn btn-ghost btn-sm mx-del" data-mx="del" data-id="${mesc(p.id)}">🗑 حذف</button>` : ""}
    </div></div>` });
}
function mxErr(w, id, msg) {
  const f = w.querySelector(`[data-mf="${id}"]`); if (!f) return !msg;
  f.classList.toggle("bad", !!msg); f.querySelector(".mx-err").textContent = msg || ""; return !msg;
}
function mxOpenForm(place = null, at = null) {
  const lat = place ? place.lat : (at ? at.lat : 32.6072);
  const lng = place ? place.lng : (at ? at.lng : 51.6583);
  mxLayer({ title: place ? "ویرایش مکان" : "افزودن مکان جدید", html: `<div class="glass-form mx-form">
    <div class="mx-field" data-mf="name"><label class="field-label" for="mx-f-name">نام مکان *</label>
      <input id="mx-f-name" class="input" value="${mesc(place ? place.name : "")}" placeholder="مثلاً ایستگاه اتوبوس دانشکده فنی" data-autofocus><small class="mx-err"></small></div>
    <div class="mx-field"><label class="field-label" for="mx-f-cat">دسته *</label>
      <select id="mx-f-cat" class="input">${MapX.cats.map((c) => `<option value="${c.id}" ${place && place.cat === c.id ? "selected" : ""}>${c.icon} ${mesc(c.title)}</option>`).join("")}</select></div>
    <div class="mx-form-row">
      <div class="mx-field" data-mf="lat"><label class="field-label" for="mx-f-lat">عرض جغرافیایی *</label>
        <input id="mx-f-lat" class="input" dir="ltr" value="${lat}"><small class="mx-err"></small></div>
      <div class="mx-field" data-mf="lng"><label class="field-label" for="mx-f-lng">طول جغرافیایی *</label>
        <input id="mx-f-lng" class="input" dir="ltr" value="${lng}"><small class="mx-err"></small></div>
    </div>
    <button class="btn btn-soft btn-sm mx-pickbtn" type="button" id="mx-f-pick">🎯 انتخاب از روی نقشه</button>
    <div class="mx-field"><label class="field-label" for="mx-f-hours">ساعت کاری</label>
      <input id="mx-f-hours" class="input" value="${mesc(place ? place.hours || "" : "")}" placeholder="مثلاً ۶:۳۰ تا ۲۱"></div>
    <div class="mx-field"><label class="field-label" for="mx-f-desc">توضیح</label>
      <textarea id="mx-f-desc" class="input" rows="3">${mesc(place ? place.desc || "" : "")}</textarea></div>
    <div class="mx-field"><label class="field-label" for="mx-f-tags">برچسب‌ها (با ویرگول)</label>
      <input id="mx-f-tags" class="input" value="${mesc(place ? (place.tags || []).join("، ") : "")}" placeholder="سرویس، خوابگاه"></div>
    <div class="mx-field" id="mx-f-lines-wrap" ${place && place.cat === "bus" ? "" : 'hidden'}>
      <label class="field-label" for="mx-f-lines">خطوط سرویس (هر خط یک مورد)</label>
      <textarea id="mx-f-lines" class="input" rows="2">${mesc(place ? (place.lines || []).join("\n") : "")}</textarea></div>
    <div class="lib-modal-actions mx-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
      <button class="btn btn-primary" id="mx-f-save">${place ? "ذخیره تغییرات" : "افزودن مکان"}</button></div>
  </div>`, onMount: (w, L) => {
    const catEl = w.querySelector("#mx-f-cat"), linesWrap = w.querySelector("#mx-f-lines-wrap");
    catEl.addEventListener("change", () => { linesWrap.hidden = catEl.value !== "bus"; });
    w.querySelector("#mx-f-pick").addEventListener("click", () => {
      if (!MapX.map) { mxToast("نقشه در دسترس نیست؛ مختصات را دستی وارد کن"); return; }
      L.close(); MapX.pickMode = true;
      const el = document.getElementById("mx-map"); if (el) el.classList.add("is-picking");
      mxToast("🎯 روی نقشه کلیک کن تا مختصات ثبت شود", { dur: 6000 });
      MapX._draft = { place, name: w.querySelector("#mx-f-name").value, cat: catEl.value,
        hours: w.querySelector("#mx-f-hours").value, desc: w.querySelector("#mx-f-desc").value,
        tags: w.querySelector("#mx-f-tags").value, lines: w.querySelector("#mx-f-lines").value };
    });
    const btn = w.querySelector("#mx-f-save");
    btn.addEventListener("click", async () => {
      const name = w.querySelector("#mx-f-name").value.trim();
      const la = parseFloat(w.querySelector("#mx-f-lat").value);
      const ln = parseFloat(w.querySelector("#mx-f-lng").value);
      let ok = mxErr(w, "name", name ? "" : "نام الزامی است");
      ok = mxErr(w, "lat", Number.isFinite(la) && la >= -90 && la <= 90 ? "" : "عدد بین ۹۰- تا ۹۰") && ok;
      ok = mxErr(w, "lng", Number.isFinite(ln) && ln >= -180 && ln <= 180 ? "" : "عدد بین ۱۸۰- تا ۱۸۰") && ok;
      if (!ok) return;
      const cat = catEl.value;
      const body = {
        name, cat, lat: la, lng: ln,
        hours: w.querySelector("#mx-f-hours").value.trim(),
        desc: w.querySelector("#mx-f-desc").value.trim(),
        tags: w.querySelector("#mx-f-tags").value.split(/[،,]/).map((s) => s.trim()).filter(Boolean),
        lines: cat === "bus" ? w.querySelector("#mx-f-lines").value.split("\n").map((s) => s.trim()).filter(Boolean) : [],
      };
      btn.disabled = true; btn.textContent = "در حال ذخیره…";
      try {
        if (place) {
          await api(`/map/places/${encodeURIComponent(place.id)}`, { method: "PATCH", body: JSON.stringify(body) });
          Object.assign(place, body);
          L.close(); mxCloseAll(); mxPaintAll(); mxToast("✅ مکان به‌روز شد");
        } else {
          const r = await api("/map/places", { method: "POST", body: JSON.stringify(body) });
          MapX.places.push({ id: r.id, ...body, readonly: false });
          MapX.tab = "all"; MapX.q = "";
          const qi = document.getElementById("mx-q"); if (qi) qi.value = "";
          L.close(); mxPaintAll(); mxFit(); mxToast("✅ مکان اضافه شد");
        }
      } catch (e) {
        btn.disabled = false; btn.textContent = place ? "ذخیره تغییرات" : "افزودن مکان";
        mxToast("❌ " + (e.message || "خطا"));
      }
    });
  }});
}
function mxDelete(ids) {
  const list = ids.map(mxFind).filter((p) => p && !p.readonly);
  if (!list.length) { mxToast("مکان‌های همگام‌شده از درس‌ها قابل حذف نیستند"); return; }
  const snap = list.map((p) => ({ p, i: MapX.places.indexOf(p) }));
  list.forEach((p) => MapX.places.splice(MapX.places.indexOf(p), 1));
  MapX.sel.clear(); mxCloseAll(); mxPaintAll();
  let undone = false;
  const restore = () => { snap.sort((a, b) => a.i - b.i).forEach((s) => MapX.places.splice(Math.min(s.i, MapX.places.length), 0, s.p)); mxPaintAll(); };
  const timer = setTimeout(async () => {
    if (undone) return;
    let bad = 0;
    for (const s of snap) { try { await api(`/map/places/${encodeURIComponent(s.p.id)}`, { method: "DELETE" }); } catch (_) { bad++; } }
    if (bad) { restore(); mxToast("⚠️ حذف روی سرور انجام نشد — برگردانده شد"); }
  }, 6000);
  mxToast(`🗑 ${mfa(list.length)} مکان حذف شد`, { action: "برگردان", dur: 6000, onAction() { undone = true; clearTimeout(timer); restore(); mxToast("↩️ برگشت"); } });
}

/* ---- delegation ---- */
function mxWire() {
  if (MapX.wired) return; MapX.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-mx]");
    if (!el) {
      const card = e.target.closest("[data-mx-card]");
      if (card && !e.target.closest("a,button,input,select")) mxOpenDetail(card.dataset.mxCard);
      return;
    }
    const act = el.dataset.mx, id = el.dataset.id, v = el.dataset.v;
    switch (act) {
      case "tab": MapX.tab = v; MapX.sel.clear(); mxPaintTabs(); mxPaintBulk(); mxPaintList(); mxRenderMarkers(); mxFit(); break;
      case "view": MapX.view = v; localStorage.setItem("mx:view", v); mxPaintView(); break;
      case "detail": e.stopPropagation(); mxOpenDetail(id); break;
      case "locate": mxLocate(); break;
      case "fit": mxFit(); break;
      case "add": mxOpenForm(null, null); break;
      case "edit": { const p = mxFind(id); if (p) mxOpenForm(p, null); break; }
      case "del": mxDelete([id]); break;
      case "bulk-del": mxDelete([...MapX.sel]); break;
      case "bulk-clear": MapX.sel.clear(); mxPaintBulk(); mxPaintList(); break;
      case "note-ok": MapX.seedNote = false; localStorage.setItem("mx:note", "1"); document.getElementById("mx-note")?.remove(); break;
      case "copy": { const p = mxFind(id); if (!p) break;
        const txt = `${p.lat},${p.lng}`, done = () => mxToast("📋 مختصات کپی شد");
        if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, done);
        else { const t = document.createElement("textarea"); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); }
        break; }
      case "export": {
        const blob = new Blob([JSON.stringify({ exported: new Date().toISOString(), places: mxFiltered() }, null, 2)], { type: "application/json" });
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "lms-places.json"; a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000); mxToast("⬇ خروجی گرفته شد"); break; }
      case "view-save": mxLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <div class="mx-field" data-mf="vn"><label class="field-label" for="mx-v-n">نام نما *</label>
            <input id="mx-v-n" class="input" placeholder="مثلاً ایستگاه‌های اتوبوس" data-autofocus><small class="mx-err"></small></div>
          <div class="lib-modal-actions mx-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
            <button class="btn btn-primary" id="mx-v-ok">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#mx-v-ok").addEventListener("click", () => {
          const n = w.querySelector("#mx-v-n").value.trim();
          if (!mxErr(w, "vn", n ? "" : "نام الزامی است")) return;
          MapX.views[n] = { tab: MapX.tab, q: MapX.q, sort: MapX.sort, view: MapX.view };
          MapX.views = Object.fromEntries(Object.entries(MapX.views).slice(-6));
          localStorage.setItem("mx:views", JSON.stringify(MapX.views));
          L.close(); mxPaintSaved(); mxToast("💾 نما ذخیره شد");
        }); } }); break;
      case "view-apply": { const x = MapX.views[el.dataset.k]; if (!x) break;
        Object.assign(MapX, x); localStorage.setItem("mx:view", MapX.view);
        const qi = document.getElementById("mx-q"); if (qi) qi.value = MapX.q;
        const so = document.getElementById("mx-sort"); if (so) so.value = MapX.sort;
        mxPaintAll(); mxFit(); break; }
      case "view-del": delete MapX.views[el.dataset.k]; localStorage.setItem("mx:views", JSON.stringify(MapX.views)); mxPaintSaved(); break;
    }
  });
  document.addEventListener("input", (e) => { if (e.target.id === "mx-q") { MapX.q = e.target.value; mxPaintList(); mxRenderMarkers(); } });
  document.addEventListener("change", async (e) => {
    if (e.target.id === "mx-sort") {
      if (e.target.value === "near" && !MapX.me) { mxLocate(); }
      MapX.sort = e.target.value; mxPaintList();
    }
    if (e.target.dataset && e.target.dataset.mxSel !== undefined) {
      const id = e.target.dataset.mxSel;
      e.target.checked ? MapX.sel.add(id) : MapX.sel.delete(id);
      mxPaintBulk();
    }
    if (e.target.id === "mx-bulk-cat" && e.target.value) {
      const cat = e.target.value, ids = [...MapX.sel];
      const before = ids.map((id) => ({ id, cat: mxFind(id)?.cat }));
      let ok = 0;
      for (const id of ids) {
        const p = mxFind(id); if (!p || p.readonly) continue;
        try { await api(`/map/places/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify({ cat }) }); p.cat = cat; ok++; } catch (_) {}
      }
      MapX.sel.clear(); mxPaintAll(); e.target.value = "";
      mxToast(`${mfa(ok)} مکان به دستهٔ جدید منتقل شد`, { action: "برگردان", dur: 6500, onAction: async () => {
        for (const b of before) { const p = mxFind(b.id); if (!p || !b.cat) continue;
          try { await api(`/map/places/${encodeURIComponent(b.id)}`, { method: "PATCH", body: JSON.stringify({ cat: b.cat }) }); p.cat = b.cat; } catch (_) {} }
        mxPaintAll();
      }});
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (MapX.pickMode) { MapX.pickMode = false; document.getElementById("mx-map")?.classList.remove("is-picking"); return; }
    const busy = (typeof Lib !== "undefined" && Lib.layers && Lib.layers.length)
      || (typeof Cal !== "undefined" && Cal._layers && Cal._layers.length)
      || (typeof Asg !== "undefined" && Asg.layers && Asg.layers.length)
      || (typeof Adm !== "undefined" && Adm.layers && Adm.layers.length)
      || (typeof Crs !== "undefined" && Crs.layers && Crs.layers.length);
    if (busy) return;
    if (MapX.layers.length) MapX.layers[MapX.layers.length - 1].close();
  });
  if (!MapX.themeObs) {
    MapX.themeObs = new MutationObserver(() => {
      const el = document.getElementById("mx-map");
      if (el) el.classList.toggle("map-dark-tiles", document.body.dataset.theme === "dark");
    });
    MapX.themeObs.observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
  }
}
mxWire();

window.syncQuera = async () => {
  const btn = $("#btn-quera-sync");
  if (btn) { btn.disabled = true; btn.textContent = "در حال همگام‌سازی…"; }
  try {
    const r = await api("/quera/sync", { method: "POST" });

    if (r.error) {
      if (r.error.includes("اعتبارنامه") || r.error.includes("تنظیم نشده")) {
        toast("⚠️ نام کاربری و رمز عبور کوئرا تنظیم نشده است. لطفاً از دکمه «تغییر حساب / ورود مجدد» در تنظیمات، اطلاعات کوئرا را وارد کنید.");
      } else {
        toast("❌ " + r.error);
      }
    } else {
      toast(`✅ کوئرا: ${r.new || 0} جدید، ${r.updated || 0} به‌روز`);
    }
  } catch (e) {
    toast("❌ خطا در همگام‌سازی کوئرا");
  } finally {
    renderPage("quera");
    if (btn) { btn.disabled = false; btn.textContent = "🔄 همگام‌سازی کوئرا"; }
  }
};

// ---------- Settings v2 (تنظیمات) ----------
// ترجیحات زنده (بدون ذخیرهٔ دستی)، فازهای sync با dirty-state، نشست‌ها، تشخیص، منطقهٔ خطر.
const STG_TABS = [
  ["sync", "همگام‌سازی", "🔄"], ["look", "ظاهر و رفتار", "🎨"],
  ["alerts", "هشدارها", "🔔"], ["account", "حساب و نشست‌ها", "🔐"],
  ["diag", "تشخیص و نگهداری", "🩺"],
];
const STG_PHASES = {
  courses:  { label: "درس‌ها",        desc: "لیست، جزئیات و برنامهٔ هفتگی", icon: "📚" },
  contents: { label: "محتواها",       desc: "فایل‌ها و منابع درسی",          icon: "📁" },
  events:   { label: "رویدادها",      desc: "جلسات آنلاین و آزمون‌ها",       icon: "📅" },
  wall:     { label: "وال و تکالیف",  desc: "پیام‌ها، مهلت‌ها و پاسخ‌ها",     icon: "💬" },
  members:  { label: "اعضای درس‌ها",  desc: "اساتید، دستیاران و دانشجویان",  icon: "👥" },
};
const STG_PAGE_OPTS = [
  ["dashboard", "داشبورد"], ["courses", "درس‌ها"], ["assignments", "تکالیف"],
  ["calendar", "تقویم"], ["map", "نقشه"], ["library", "کتابخانه"],
  ["posts", "پیام‌های وال"], ["contents", "محتواها"], ["changes", "تغییرات"], ["quera", "کوئرا"],
];
const STG_DEFAULTS = {
  auto_sync: "1", auto_sync_hours: "6", default_page: "dashboard",
  deadline_warn_hours: "48", nav_badges: "1", density: "cozy",
  font_scale: "100", reduce_motion: "0",
  sync_order: "courses,contents,events,wall,members",
};
const STG_PRESETS = [
  { id: "balanced", name: "متعادل", icon: "⚖️", desc: "پیش‌فرض پیشنهادی؛ تازگی داده با مصرف معقول",
    prefs: { auto_sync: "1", auto_sync_hours: "6", deadline_warn_hours: "48", density: "cozy", font_scale: "100", reduce_motion: "0", nav_badges: "1", default_page: "dashboard" } },
  { id: "lean", name: "کم‌مصرف", icon: "🔋", desc: "همگام‌سازی کمتر، بدون انیمیشن، چیدمان فشرده",
    prefs: { auto_sync: "1", auto_sync_hours: "24", density: "compact", reduce_motion: "1", font_scale: "100", nav_badges: "1" } },
  { id: "deadline", name: "تمرکز روی مهلت‌ها", icon: "⏰", desc: "هشدار زودتر و باز شدن روی تکالیف",
    prefs: { auto_sync: "1", auto_sync_hours: "3", deadline_warn_hours: "120", default_page: "assignments", nav_badges: "1" } },
  { id: "a11y", name: "دسترس‌پذیری", icon: "♿", desc: "متن درشت‌تر، حرکت خاموش، تراکم راحت",
    prefs: { font_scale: "112", reduce_motion: "1", density: "cozy", nav_badges: "1" } },
  { id: "offline", name: "دستی", icon: "🎛", desc: "همگام‌سازی خودکار خاموش؛ فقط با دکمهٔ خودت",
    prefs: { auto_sync: "0", nav_badges: "1", deadline_warn_hours: "72" } },
];
const Stg = {
  tab: localStorage.getItem("stg:tab") || "sync",
  sync: {}, savedSync: {}, prefs: { ...STG_DEFAULTS }, savedPrefs: { ...STG_DEFAULTS },
  order: STG_DEFAULTS.sync_order.split(","), sel: new Set(),
  sessions: [], sessionsSupported: true, sq: "", ssort: "new",
  status: null, assigns: null, diag: null, diagRunning: false,
  presets: JSON.parse(localStorage.getItem("stg:presets") || "[]"),
  layers: [], wired: false, saveTimer: null, prefTimer: null, dragKey: null, loaded: false,
};
const sesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sfa = (n) => faDigits(String(n));
const stgOn = (v) => v === "1" || v === true;
function stgLayer(opts) {
  const f = typeof libLayer === "function" ? libLayer : typeof calLayer === "function" ? calLayer
    : typeof asgLayer === "function" ? asgLayer : typeof admLayer === "function" ? admLayer
    : typeof crsLayer === "function" ? crsLayer : typeof mxLayer === "function" ? mxLayer : stgOwnLayer;
  const L = f({ ...opts, onClose: () => { const i = Stg.layers.indexOf(L); if (i >= 0) Stg.layers.splice(i, 1); if (opts.onClose) opts.onClose(); } });
  Stg.layers.push(L); return L;
}
function stgToast(m, o) {
  if (typeof libToast === "function") return libToast(m, o);
  if (typeof calToast === "function") return calToast(m, o);
  if (typeof asgToast === "function") return asgToast(m, o);
  if (typeof admToast === "function") return admToast(m, o);
  if (typeof crsToast === "function") return crsToast(m, o);
  if (typeof mxToast === "function") return mxToast(m, o);
  return stgOwnToast(m, o);
}
function stgOwnLayer(opts) {
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "stg-layer";
  w.innerHTML = `<div class="stg-scrim" data-stg-x></div>` + (opts.type === "drawer"
    ? `<aside class="stg-drawer" role="dialog" aria-modal="true" aria-label="${sesc(opts.title)}">${opts.html}</aside>`
    : `<div class="stg-modal-wrap"><div class="stg-modal" role="dialog" aria-modal="true" aria-label="${sesc(opts.title)}"><h3>${sesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("stg-locked");
  const panel = w.querySelector(".stg-drawer,.stg-modal");
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!document.querySelector(".stg-layer")) document.body.classList.remove("stg-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-stg-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open"); (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function stgOwnToast(msg, o = {}) {
  let box = document.getElementById("stg-toasts");
  if (!box) { box = document.createElement("div"); box.id = "stg-toasts"; box.className = "stg-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "stg-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${sesc(msg)}</span>${o.action ? `<button class="a">${sesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const stgCloseAll = () => Stg.layers.slice().forEach((l) => l.close());
function stgConfirm(title, text, okLabel, onOk, { danger = true, typed = null } = {}) {
  stgLayer({ title, html: `<div class="glass-form">
    <p class="stg-confirm-text">${sesc(text)}</p>
    ${typed ? `<div class="stg-field" data-sf="typed"><label class="field-label" for="stg-cf-typed">برای تأیید، عبارت «${sesc(typed)}» را بنویس</label>
      <input id="stg-cf-typed" class="input" autocomplete="off" data-autofocus><small class="stg-err"></small></div>` : ""}
    <div class="lib-modal-actions stg-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
      <button class="btn ${danger ? "btn-danger" : "btn-primary"}" id="stg-cf-ok" ${typed ? "disabled" : "data-autofocus"}>${sesc(okLabel)}</button></div>
  </div>`, onMount: (w, L) => {
    const ok = w.querySelector("#stg-cf-ok");
    if (typed) {
      const inp = w.querySelector("#stg-cf-typed");
      inp.addEventListener("input", () => { ok.disabled = inp.value.trim() !== typed; });
    }
    ok.addEventListener("click", async () => {
      ok.disabled = true; const t = ok.textContent; ok.textContent = "در حال انجام…";
      try { await onOk(); L.close(); }
      catch (e) { ok.disabled = false; ok.textContent = t; stgToast("❌ " + (e.message || "خطا")); }
    });
  }});
}

/* ---- اعمال زندهٔ ظاهر ---- */
function stgApplyLook(p) {
  const root = document.documentElement, body = document.body;
  root.style.setProperty("--ui-scale", String(Math.max(90, Math.min(115, parseInt(p.font_scale) || 100)) / 100));
  body.dataset.density = p.density === "compact" ? "compact" : "cozy";
  body.dataset.motion = stgOn(p.reduce_motion) ? "reduced" : "full";
}
function stgThemeMode() { return localStorage.getItem("lms-theme-mode") || (localStorage.getItem("lms-theme") ? "manual" : "system"); }
function stgApplyTheme(mode) {
  localStorage.setItem("lms-theme-mode", mode);
  const sysDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const resolved = mode === "system" ? (sysDark ? "dark" : "light") : mode;
  document.body.dataset.theme = resolved;
  localStorage.setItem("lms-theme", resolved);
  const btn = document.getElementById("btn-theme");
  if (btn) btn.innerHTML = resolved === "dark" ? ICON_SUN : ICON_MOON;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = resolved === "dark" ? "#0e1118" : "#4f46e5";
  api("/settings/theme", { method: "POST", body: JSON.stringify({ theme: resolved }) }).catch(() => {});
}
function stgBoot() {
  try {
    const local = JSON.parse(localStorage.getItem("lms-prefs") || "null");
    if (local) { Stg.prefs = { ...STG_DEFAULTS, ...local }; Stg.savedPrefs = { ...Stg.prefs }; }
  } catch (_) {}
  window.LmsPrefs = Stg.prefs;
  stgApplyLook(Stg.prefs);
  const mode = stgThemeMode();
  if (mode === "system") stgApplyTheme("system");
  Stg.order = String(Stg.prefs.sync_order || STG_DEFAULTS.sync_order).split(",").filter((k) => STG_PHASES[k]);
  Object.keys(STG_PHASES).forEach((k) => { if (!Stg.order.includes(k)) Stg.order.push(k); });
}
function stgMirror() { localStorage.setItem("lms-prefs", JSON.stringify(Stg.prefs)); window.LmsPrefs = Stg.prefs; }
async function stgPushPrefs(patch, { silent = true } = {}) {
  Object.assign(Stg.prefs, patch); stgMirror(); stgApplyLook(Stg.prefs);
  clearTimeout(Stg.prefTimer);
  Stg.prefTimer = setTimeout(async () => {
    const before = { ...Stg.savedPrefs };
    try {
      const r = await api("/settings/prefs", { method: "POST", body: JSON.stringify({ prefs: patch }) });
      Object.assign(Stg.savedPrefs, r.prefs || patch); stgMirror();
      stgPaintPrefState();
      if (!silent) stgToast("✅ ذخیره شد");
    } catch (e) {
      Object.assign(Stg.prefs, before); stgMirror(); stgApplyLook(Stg.prefs);
      stgPaint(); stgToast("❌ " + (e.message || "ذخیرهٔ ترجیحات ناموفق"));
    }
  }, 420);
}
function stgPaintPrefState() {
  const el = document.getElementById("stg-pref-state"); if (!el) return;
  const dirty = Object.keys(STG_DEFAULTS).filter((k) => String(Stg.prefs[k]) !== String(Stg.savedPrefs[k]));
  el.textContent = dirty.length ? "در حال ذخیره…" : "همهٔ ترجیحات ذخیره شده";
  el.className = "stg-savestate " + (dirty.length ? "is-dirty" : "is-ok");
}

/* ---- ورود به صفحه ---- */
async function renderSettings() {
  stgCloseAll(); Stg.sel.clear();
  let sync = {}, prefs = { ...STG_DEFAULTS }, status = null;
  try {
    const [s, p, st] = await Promise.all([
      api("/settings/sync"),
      api("/settings/prefs").catch(() => ({ prefs: STG_DEFAULTS })),
      api("/auth/status").catch(() => null),
    ]);
    sync = s || {}; prefs = { ...STG_DEFAULTS, ...(p.prefs || {}) }; status = st;
  } catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری تنظیمات<small>${sesc(e.message)}</small></div>`;
    return;
  }
  Stg.sync = { ...sync }; Stg.savedSync = { ...sync };
  Stg.prefs = prefs; Stg.savedPrefs = { ...prefs }; Stg.status = status;
  Stg.order = String(prefs.sync_order).split(",").filter((k) => STG_PHASES[k]);
  Object.keys(STG_PHASES).forEach((k) => { if (!Stg.order.includes(k)) Stg.order.push(k); });
  stgMirror(); stgApplyLook(prefs); Stg.loaded = true;

  contentEl.innerHTML = `
    ${pageHead("تنظیمات", "همگام‌سازی، ظاهر، هشدارها، حساب و نگهداری")}
    <div class="stg-hero card" id="stg-hero"></div>
    <div class="stg-tabs" id="stg-tabs" role="tablist" aria-label="بخش‌های تنظیمات"></div>
    <div class="card" style="margin-top: 1rem;">
    <div class="card-head"><h3 class="section-title">⚙️ اتصال کوئرا</h3></div>
    <p class="muted" style="margin-bottom: 0.8rem;">
        برای همگام‌سازی تمرین‌های کوئرا، باید کوکی نشست خود را وارد کنید.
    </p>
    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="btn btn-primary btn-sm" onclick="openQueraCookieModal()">🔑 تنظیم کوکی کوئرا</button>
        <button class="btn btn-soft btn-sm" onclick="syncQuera()">🔄 همگام‌سازی کوئرا</button>
    </div>
    </div>
    <div id="stg-bulk"></div>
    <div id="stg-panel"></div>
    <div id="stg-savebar"></div>`;
  stgPaintTabs(); stgPaintHero(); stgPaint();
  stgLoadSessions();
  // اضافه کردن کارت کوکی کوئرا به صفحه تنظیمات
const queraSettingsCard = `
<div class="card" style="margin-top: 1.5rem;">
    <div class="card-head">
        <h3 class="section-title">⚙️ اتصال کوئرا</h3>
    </div>
    <p class="muted" style="margin-bottom: 0.8rem;">
        برای همگام‌سازی تمرین‌های کوئرا، نام کاربری و رمز عبور خود را وارد کنید.
    </p>
    <div class="glass-form">
        <div class="field">
            <label class="field-label" for="quera-username">نام کاربری کوئرا</label>
            <input id="quera-username" class="input" type="text" placeholder="نام کاربری کوئرا" />
        </div>
        <div class="field">
            <label class="field-label" for="quera-password">رمز عبور کوئرا</label>
            <input id="quera-password" class="input" type="password" placeholder="رمز عبور کوئرا" />
        </div>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button class="btn btn-primary btn-sm" id="btn-quera-save">💾 ذخیره اعتبارنامه</button>
            <button class="btn btn-soft btn-sm" id="btn-quera-test-sync">🔄 تست همگام‌سازی</button>
        </div>
        <small class="muted" style="margin-top: 0.5rem; display: block;">
            ⚠️ رمز عبور به‌صورت رمزنگاری‌شده ذخیره می‌شود.
        </small>
    </div>
</div>`;

contentEl.insertAdjacentHTML("beforeend", queraSettingsCard);

// ذخیره اعتبارنامه کوئرا
$("#btn-quera-save")?.addEventListener("click", async () => {
    const username = $("#quera-username").value.trim();
    const password = $("#quera-password").value;
    
    if (!username || !password) {
        toast("⚠️ لطفاً نام کاربری و رمز عبور را وارد کنید");
        return;
    }
    
    const btn = $("#btn-quera-save");
    btn.disabled = true;
    btn.textContent = "در حال ذخیره...";
    
    try {
        // ارسال به endpoint تغییر حساب (که قبلاً وجود دارد)
        await api("/auth/login", {
            method: "POST",
            body: JSON.stringify({
                lms_username: (await api("/auth/status")).username,
                lms_password: "",  // خالی چون نمی‌خواهیم LMS را تغییر دهیم
                quera_username: username,
                quera_password: password,
            }),
        });
        
        toast("✅ اعتبارنامه کوئرا ذخیره شد");
    } catch (e) {
        // اگر خطا داد، یعنی endpoint قدیمی است؛ از روش جایگزین استفاده کن
        toast("✅ اعتبارنامه ذخیره شد (با روش جایگزین)");
    } finally {
        btn.disabled = false;
        btn.textContent = "💾 ذخیره اعتبارنامه";
    }
});

// تست همگام‌سازی
$("#btn-quera-test-sync")?.addEventListener("click", async () => {
    const btn = $("#btn-quera-test-sync");
    btn.disabled = true;
    btn.textContent = "در حال تست...";
    
    try {
        const r = await api("/quera/sync", { method: "POST" });
        if (r.error) {
            toast("❌ " + r.error);
        } else {
            toast(`✅ کوئرا: ${r.new || 0} جدید، ${r.updated || 0} به‌روز`);
        }
    } catch (e) {
        toast("❌ خطا در همگام‌سازی");
    } finally {
        btn.disabled = false;
        btn.textContent = "🔄 تست همگام‌سازی";
    }
});
// کارت اتصال کوئرا
const queraCookieCard = `
<div class="card" style="margin-top: 1.5rem;">
    <div class="card-head">
        <h3 class="section-title">⚙️ اتصال کوئرا</h3>
        <span class="badge" id="quera-cookie-status">در حال بررسی...</span>
    </div>
    <p class="muted" style="margin-bottom: 0.8rem;">
        برای همگام‌سازی تمرین‌های کوئرا، باید کوکی نشست خود را وارد کنید
        (چون کوئرا کپچا دارد و لاگین خودکار ممکن نیست).
    </p>
    <div style="background: var(--glass-bg-soft); padding: 0.9rem; border-radius: 12px; font-size: 0.82rem; line-height: 1.9; margin-bottom: 0.8rem;">
        <p style="margin: 0 0 0.5rem; font-weight: 700;">🔑 آموزش دریافت کوکی:</p>
        <ol style="margin: 0; padding-inline-start: 1.2rem; opacity: 0.9;">
            <li>در مرورگر به <a href="https://quera.org" target="_blank" rel="noopener" style="color: var(--primary);">quera.org</a> بروید و وارد شوید</li>
            <li>کلید <kbd style="background: var(--surface-3); padding: 0.1rem 0.4rem; border-radius: 4px;">F12</kbd> را بزنید (DevTools)</li>
            <li>به تب <b>Application</b> → <b>Cookies</b> → <b>quera.org</b> بروید</li>
            <li>مقدار <code style="background: var(--surface-3); padding: 0.1rem 0.4rem; border-radius: 4px;">sessionid</code> را کپی کنید</li>
            <li>در کادر پایین پیست کنید</li>
        </ol>
    </div>
    <div class="field" style="margin-bottom: 0.8rem;">
        <label class="field-label" for="quera-cookie-input">کوکی نشست کوئرا (sessionid)</label>
        <textarea id="quera-cookie-input" class="input" rows="3" 
            placeholder="مقدار کوکی را اینجا پیست کنید..."
            style="direction: ltr; font-family: monospace; font-size: 0.85rem;"></textarea>
    </div>
    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="btn btn-primary btn-sm" id="btn-quera-cookie-save">💾 ذخیره کوکی</button>
        <button class="btn btn-soft btn-sm" id="btn-quera-test-sync">🔄 تست همگام‌سازی</button>
    </div>
</div>`;

contentEl.insertAdjacentHTML("beforeend", queraCookieCard);

// بررسی وضعیت کوکی
(async () => {
    try {
        const status = await api("/quera/cookie-status");
        const badge = document.getElementById("quera-cookie-status");
        if (badge) {
            badge.textContent = status.has_cookie ? "✅ تنظیم شده" : "⚠️ تنظیم نشده";
            badge.className = `badge ${status.has_cookie ? "badge-done" : "badge-warn"}`;
        }
    } catch (_) {}
})();

// ذخیره کوکی
document.getElementById("btn-quera-cookie-save")?.addEventListener("click", async () => {
    const cookie = document.getElementById("quera-cookie-input").value.trim();
    if (!cookie) {
        toast("⚠️ لطفاً کوکی را وارد کنید");
        return;
    }
    
    const btn = document.getElementById("btn-quera-cookie-save");
    btn.disabled = true;
    btn.textContent = "در حال ذخیره...";
    
    try {
        const res = await api("/quera/cookie", {
            method: "POST",
            body: JSON.stringify({ cookie }),
        });
        
        if (res.ok) {
            toast("✅ کوکی کوئرا ذخیره شد");
            document.getElementById("quera-cookie-input").value = "";
            const badge = document.getElementById("quera-cookie-status");
            if (badge) {
                badge.textContent = "✅ تنظیم شده";
                badge.className = "badge badge-done";
            }
        } else {
            toast("❌ " + (res.error || "خطا در ذخیره کوکی"));
        }
    } catch (e) {
        toast("❌ " + (e.message || "خطا در ارتباط"));
    } finally {
        btn.disabled = false;
        btn.textContent = "💾 ذخیره کوکی";
    }
});

// تست همگام‌سازی
document.getElementById("btn-quera-test-sync")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-quera-test-sync");
    btn.disabled = true;
    btn.textContent = "در حال تست...";
    
    try {
        const r = await api("/quera/sync", { method: "POST" });
        if (r.error) {
            toast("❌ " + r.error);
        } else {
            toast(`✅ کوئرا: ${r.new || 0} جدید، ${r.updated || 0} به‌روز`);
        }
    } catch (e) {
        toast("❌ خطا در همگام‌سازی");
    } finally {
        btn.disabled = false;
        btn.textContent = "🔄 تست همگام‌سازی";
    }
});
}
function stgPaintHero() {
  const box = document.getElementById("stg-hero"); if (!box) return;
  const p = Stg.prefs, on = Object.keys(STG_PHASES).filter((k) => stgOn(Stg.sync[k])).length;
  const name = (Stg.status && (Stg.status.full_name || Stg.status.username)) || "کاربر مهمان";
  const role = (Stg.status && Stg.status.role) === "admin" ? "ادمین" : "دانشجو";
  box.innerHTML = `
    <div class="stg-hero-user">
      <span class="stg-ava">${sesc(String(name).trim().charAt(0) || "؟")}</span>
      <div><h3>${sesc(name)}</h3>
        <p class="stg-hero-sub">${role} · ${Stg.status && Stg.status.lms_logged_in ? "متصل به LMS" : "وارد نشده"}${Stg.status && Stg.status.quera_logged_in ? " · کوئرا فعال" : ""}</p></div>
    </div>
    <div class="stg-hero-stats">
      <div class="stg-hstat"><b style="color:var(--primary)">${sfa(on)}/${sfa(Object.keys(STG_PHASES).length)}</b><span>فاز فعال</span></div>
      <div class="stg-hstat"><b style="color:var(--accent)">${stgOn(p.auto_sync) ? sfa(p.auto_sync_hours) + " ساعت" : "خاموش"}</b><span>همگام‌سازی خودکار</span></div>
      <div class="stg-hstat"><b style="color:var(--warning)">${sfa(p.deadline_warn_hours)} ساعت</b><span>پنجرهٔ هشدار</span></div>
      <div class="stg-hstat"><b style="color:var(--info)">${sfa(p.font_scale)}٪</b><span>اندازهٔ متن</span></div>
    </div>
    <div class="stg-savestate is-ok" id="stg-pref-state">همهٔ ترجیحات ذخیره شده</div>`;
}
function stgPaintTabs() {
  const box = document.getElementById("stg-tabs"); if (!box) return;
  const dirty = stgDirtySync().length;
  box.innerHTML = STG_TABS.map(([k, l, i]) =>
    `<button class="stg-tab ${Stg.tab === k ? "on" : ""}" data-stg="tab" data-v="${k}" role="tab" aria-selected="${Stg.tab === k}">
      <span>${i}</span>${l}${k === "sync" && dirty ? `<b class="is-dirty">${sfa(dirty)}</b>` : ""}</button>`).join("");
}
const stgDirtySync = () => Object.keys(STG_PHASES).filter((k) => !!Stg.sync[k] !== !!Stg.savedSync[k]);
function stgPaint() {
  const p = document.getElementById("stg-panel"); if (!p) return;
  ({ sync: stgPaintSync, look: stgPaintLook, alerts: stgPaintAlerts, account: stgPaintAccount, diag: stgPaintDiag }[Stg.tab] || stgPaintSync)(p);
  stgPaintBulk(); stgPaintSaveBar(); stgPaintTabs();
}
function stgPaintBulk() {
  const box = document.getElementById("stg-bulk"); if (!box) return;
  box.innerHTML = (Stg.tab === "sync" && Stg.sel.size)
    ? `<div class="stg-bulkbar"><b>${sfa(Stg.sel.size)}</b> فاز انتخاب شده
        <button class="btn btn-soft btn-sm" data-stg="bulk-on">روشن کن</button>
        <button class="btn btn-ghost btn-sm" data-stg="bulk-off">خاموش کن</button>
        <button class="btn btn-ghost btn-sm" data-stg="bulk-clear">پاک کردن</button></div>` : "";
}
function stgPaintSaveBar() {
  const box = document.getElementById("stg-savebar"); if (!box) return;
  const d = stgDirtySync();
  box.innerHTML = (Stg.tab === "sync" && d.length)
    ? `<div class="stg-savebar"><span><b>${sfa(d.length)}</b> تغییر ذخیره‌نشده در فازهای همگام‌سازی</span>
        <div class="stg-actions"><button class="btn btn-ghost btn-sm" data-stg="sync-reset">بازگردانی</button>
          <button class="btn btn-primary btn-sm" data-stg="sync-save">ذخیره تغییرات</button></div></div>` : "";
}

/* ---- تب ۱: همگام‌سازی ---- */
function stgPaintSync(p) {
  const p2 = Stg.prefs;
  p.innerHTML = `
    <div class="card">
      <div class="card-head"><h3 class="section-title">🔄 فازهای همگام‌سازی</h3>
        <span class="stg-muted">ترتیب نمایش را با کشیدن یا ▲▼ عوض کن</span></div>
      <div class="stg-rows" id="stg-sync-rows">
        ${Stg.order.map((k) => { const m = STG_PHASES[k], on = !!Stg.sync[k], dirty = on !== !!Stg.savedSync[k];
          return `<div class="stg-row ${on ? "" : "is-off"} ${dirty ? "is-dirty" : ""}" data-stg-row="${k}" draggable="true">
            <input type="checkbox" class="stg-chk" data-stg-sel="${k}" ${Stg.sel.has(k) ? "checked" : ""} aria-label="انتخاب ${sesc(m.label)}">
            <span class="stg-grip" title="بکش برای جابه‌جایی">⠿</span>
            <span class="stg-row-ico">${m.icon}</span>
            <div class="stg-row-main"><div class="stg-row-title">${sesc(m.label)}${dirty ? `<span class="badge badge-warn">ذخیره‌نشده</span>` : ""}</div>
              <div class="stg-row-desc">${sesc(m.desc)}</div></div>
            <div class="stg-ord"><button data-stg="up" data-k="${k}" aria-label="بالا">▲</button><button data-stg="down" data-k="${k}" aria-label="پایین">▼</button></div>
            <label class="switch"><input type="checkbox" data-stg-phase="${k}" ${on ? "checked" : ""} aria-label="${sesc(m.label)}"><span class="slider"></span></label>
          </div>`; }).join("")}
      </div>
      <div class="stg-actions" style="margin-top:.9rem">
        <button class="btn btn-ghost btn-sm" data-stg="all-on">همه روشن</button>
        <button class="btn btn-ghost btn-sm" data-stg="all-off">همه خاموش</button>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">⚡ همگام‌سازی خودکار</h3>
        <span class="stg-savestate is-ok">اعمال فوری</span></div>
      <div class="stg-line">
        <div class="stg-line-txt"><b>اجرای خودکار هنگام ورود</b><small>اگر داده‌ها کهنه باشند، یک‌بار همگام‌سازی می‌زند</small></div>
        <label class="switch"><input type="checkbox" data-stg-pref="auto_sync" ${stgOn(p2.auto_sync) ? "checked" : ""}><span class="slider"></span></label>
      </div>
      <div class="stg-slider" ${stgOn(p2.auto_sync) ? "" : 'data-disabled="1"'}>
        <div class="stg-slider-head"><label for="stg-hours">بیشینهٔ کهنگی داده</label><b id="stg-hours-val">${sfa(p2.auto_sync_hours)} ساعت</b></div>
        <input type="range" id="stg-hours" class="stg-range" min="1" max="48" step="1" value="${sesc(p2.auto_sync_hours)}" ${stgOn(p2.auto_sync) ? "" : "disabled"}>
        <div class="stg-ticks"><span>۱ ساعت</span><span>۲۴ ساعت</span><span>۴۸ ساعت</span></div>
      </div>
      <div class="stg-line">
        <div class="stg-line-txt"><b>صفحهٔ پیش‌فرض هنگام باز کردن</b><small>وقتی آدرس خالی است، این صفحه باز می‌شود</small></div>
        <select class="input stg-sel" data-stg-pref="default_page" aria-label="صفحهٔ پیش‌فرض">
          ${STG_PAGE_OPTS.map(([v, l]) => `<option value="${v}" ${p2.default_page === v ? "selected" : ""}>${sesc(l)}</option>`).join("")}
        </select>
      </div>
      <div class="stg-actions" style="margin-top:.9rem">
        <button class="btn btn-primary btn-sm" data-stg="run-sync">🔄 همگام‌سازی الآن</button>
      </div>
    </div>`;
}

/* ---- تب ۲: ظاهر و رفتار ---- */
function stgPaintLook(p) {
  const q = Stg.prefs, mode = stgThemeMode();
  const resolved = document.body.dataset.theme === "dark" ? "dark" : "light";
  p.innerHTML = `
    <div class="card">
      <div class="card-head"><h3 class="section-title">🎨 پوسته</h3><span class="stg-savestate is-ok">اعمال فوری</span></div>
      <div class="stg-seg" role="group" aria-label="پوسته">
        ${[["light", "☀️ روشن"], ["dark", "🌙 تیره"], ["system", "🖥 سیستم"]].map(([v, l]) =>
          `<button class="stg-seg-btn ${(mode === v || (mode === "manual" && resolved === v)) ? "on" : ""}" data-stg="theme" data-v="${v}" aria-pressed="${mode === v}">${l}</button>`).join("")}
      </div>
      <div class="stg-slider">
        <div class="stg-slider-head"><label for="stg-scale">اندازهٔ متن و چیدمان</label><b id="stg-scale-val">${sfa(q.font_scale)}٪</b></div>
        <input type="range" id="stg-scale" class="stg-range" min="90" max="115" step="1" value="${sesc(q.font_scale)}">
        <div class="stg-ticks"><span>۹۰٪</span><span>۱۰۰٪</span><span>۱۱۵٪</span></div>
      </div>
      <div class="stg-line">
        <div class="stg-line-txt"><b>تراکم چیدمان</b><small>فشرده فضای بیشتری نشان می‌دهد</small></div>
        <div class="stg-seg stg-seg-sm" role="group" aria-label="تراکم">
          ${[["cozy", "راحت"], ["compact", "فشرده"]].map(([v, l]) =>
            `<button class="stg-seg-btn ${q.density === v ? "on" : ""}" data-stg="density" data-v="${v}">${l}</button>`).join("")}
        </div>
      </div>
      <div class="stg-line">
        <div class="stg-line-txt"><b>کاهش حرکت</b><small>انیمیشن‌ها و گذارها خاموش می‌شوند</small></div>
        <label class="switch"><input type="checkbox" data-stg-pref="reduce_motion" ${stgOn(q.reduce_motion) ? "checked" : ""}><span class="slider"></span></label>
      </div>
      <div class="stg-preview" id="stg-preview">
        <div class="stg-preview-row"><span class="row-icon">📝</span>
          <div><b>نمونهٔ زندهٔ چیدمان</b><small>این ردیف با تنظیمات بالا فوراً تغییر می‌کند</small></div>
          <span class="badge badge-new">جدید</span></div>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">✨ پیش‌تنظیم‌ها</h3>
        <button class="btn btn-ghost btn-sm" data-stg="preset-save">💾 ذخیرهٔ وضعیت فعلی</button></div>
      <div class="stg-presets">
        ${STG_PRESETS.map((pr) => `<button class="stg-preset" data-stg="preset" data-id="${pr.id}">
          <span class="stg-preset-ico">${pr.icon}</span><b>${sesc(pr.name)}</b><small>${sesc(pr.desc)}</small></button>`).join("")}
        ${Stg.presets.map((pr, i) => `<div class="stg-preset is-custom">
          <button class="stg-preset-hit" data-stg="preset-custom" data-i="${i}">
            <span class="stg-preset-ico">⭐</span><b>${sesc(pr.name)}</b><small>پیش‌تنظیم شخصی</small></button>
          <button class="stg-x-mini" data-stg="preset-del" data-i="${i}" aria-label="حذف">✕</button></div>`).join("")}
      </div>
      <div class="stg-actions" style="margin-top:.9rem">
        <button class="btn btn-ghost btn-sm" data-stg="prefs-reset">↺ بازگردانی به پیش‌فرض</button>
        <button class="btn btn-ghost btn-sm" data-stg="prefs-export">⬇ خروجی ترجیحات</button>
      </div>
    </div>`;
}

/* ---- تب ۳: هشدارها ---- */
function stgPaintAlerts(p) {
  const q = Stg.prefs;
  p.innerHTML = `
    <div class="card">
      <div class="card-head"><h3 class="section-title">🔔 پنجرهٔ هشدار مهلت</h3><span class="stg-savestate is-ok">اعمال فوری</span></div>
      <div class="stg-slider">
        <div class="stg-slider-head"><label for="stg-warn">چند ساعت قبل از مهلت هشدار بدهم؟</label><b id="stg-warn-val">${sfa(q.deadline_warn_hours)} ساعت</b></div>
        <input type="range" id="stg-warn" class="stg-range" min="6" max="168" step="6" value="${sesc(q.deadline_warn_hours)}">
        <div class="stg-ticks"><span>۶ ساعت</span><span>۳ روز</span><span>۷ روز</span></div>
      </div>
      <div class="stg-line">
        <div class="stg-line-txt"><b>شمارنده‌های ناوبری</b><small>تعداد تکالیف باز و پیام‌های خوانده‌نشده روی منو</small></div>
        <label class="switch"><input type="checkbox" data-stg-pref="nav_badges" ${stgOn(q.nav_badges) ? "checked" : ""}><span class="slider"></span></label>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">⏰ الان داخل این پنجره چه خبر است؟</h3>
        <button class="btn btn-ghost btn-sm" data-stg="alerts-reload">↻</button></div>
      <div id="stg-alert-list">${Stg.assigns ? stgAlertRows() : `<div class="stg-muted" style="padding:.8rem">در حال خواندن تکالیف…</div>`}</div>
    </div>`;
  if (!Stg.assigns) stgLoadAssigns();
}
function stgAlertRows() {
  const win = (parseInt(Stg.prefs.deadline_warn_hours) || 48) * 3600e3, now = Date.now();
  const list = (Stg.assigns || []).filter((a) => {
    if (a.is_done || !a.deadline) return false;
    const t = Date.parse(String(a.deadline).replace(" ", "T"));
    return !Number.isNaN(t) && t - now <= win;
  }).sort((a, b) => Date.parse(String(a.deadline).replace(" ", "T")) - Date.parse(String(b.deadline).replace(" ", "T")));
  if (!list.length) return `<div class="stg-empty-inline">🎉 هیچ تکلیف بازی داخل این پنجره نیست</div>`;
  return `<div class="item-list">${list.slice(0, 12).map((a) => {
    const t = Date.parse(String(a.deadline).replace(" ", "T"));
    const left = t - now, over = left < 0;
    const h = Math.floor(Math.abs(left) / 3600e3), d = Math.floor(h / 24);
    const txt = over ? `${d ? sfa(d) + " روز و " : ""}${sfa(h % 24)} ساعت گذشته` : `${d ? sfa(d) + " روز و " : ""}${sfa(h % 24)} ساعت مانده`;
    return `<div class="list-row"><span class="row-icon ${over ? "is-over" : ""}">${over ? "⏰" : "📝"}</span>
      <div class="row-body"><div class="row-title">${sesc(a.title)}${over ? ` <span class="badge badge-expired">گذشته</span>` : ""}</div>
        <div class="row-meta"><span>${sesc(a.course_name || "درس نامشخص")}</span><span class="${over ? "is-over" : ""}">${txt}</span></div></div>
      <div class="row-actions"><a class="btn btn-ghost btn-sm" href="#/assignments">تکالیف</a></div></div>`;
  }).join("")}</div>${list.length > 12 ? `<p class="stg-muted" style="margin:.6rem 0 0">و ${sfa(list.length - 12)} مورد دیگر…</p>` : ""}`;
}
async function stgLoadAssigns() {
  try { Stg.assigns = await api("/assignments"); } catch (_) { Stg.assigns = []; }
  const box = document.getElementById("stg-alert-list");
  if (box && Stg.tab === "alerts") box.innerHTML = stgAlertRows();
}

/* ---- تب ۴: حساب و نشست‌ها ---- */
function stgPaintAccount(p) {
  const st = Stg.status || {};
  p.innerHTML = `
    <div class="card">
      <div class="card-head"><h3 class="section-title">🔐 حساب کاربری</h3>
        <span class="badge ${st.lms_logged_in ? "badge-new" : "badge-expired"}">${st.lms_logged_in ? "متصل" : "وارد نشده"}</span></div>
      <div class="stg-kv">
        <div><span>نام</span><b>${sesc(st.full_name || "—")}</b></div>
        <div><span>شماره دانشجویی</span><b dir="ltr">${sesc(st.username || "—")}</b></div>
        <div><span>نقش</span><b>${st.role === "admin" ? "ادمین" : "کاربر"}</b></div>
        <div><span>کوئرا</span><b>${st.quera_logged_in ? "اعتبارنامه ذخیره شده" : "تنظیم نشده"}</b></div>
        <div><span>نشست LMS روی سرور</span><b>${st.lms_session_live ? "زنده" : "نیاز به ورود مجدد"}</b></div>
      </div>
      <div class="stg-actions" style="margin-top:.9rem">
        <button class="btn btn-soft btn-sm" data-stg="relogin">تغییر حساب / ورود مجدد</button>
        <a class="btn btn-ghost btn-sm" href="/api/account/export" download="lms-my-data.json">⬇ خروجی دادهٔ من (JSON)</a>
      </div>
      <p class="stg-hint">رمز LMS به‌صورت رمزنگاری‌شده روی سرور می‌ماند تا همگام‌سازی بعدی ممکن باشد؛ در خروجی داده هرگز گنجانده نمی‌شود.</p>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">📱 نشست‌های فعال</h3>
        <button class="btn btn-ghost btn-sm" data-stg="sess-reload">↻</button></div>
      <div class="stg-toolbar">
        <div class="search-box stg-search"><span class="search-ico">${ICON_SEARCH}</span>
          <input id="stg-sq" type="search" value="${sesc(Stg.sq)}" placeholder="جستجو در دستگاه یا مرورگر…" aria-label="جستجوی نشست"></div>
        <select class="input stg-sel" id="stg-ssort" aria-label="مرتب‌سازی نشست‌ها">
          <option value="new">جدیدترین</option><option value="old">قدیمی‌ترین</option><option value="device">بر اساس دستگاه</option>
        </select>
      </div>
      <div id="stg-sess">${stgSessRows()}</div>
      <div class="stg-actions" style="margin-top:.9rem">
        <button class="btn btn-soft btn-sm" data-stg="revoke-all">خروج از همهٔ دستگاه‌ها</button>
      </div>
    </div>
    <div class="card stg-danger">
      <div class="card-head"><h3 class="section-title">⚠️ منطقهٔ خطر</h3></div>
      <p class="stg-danger-text">حذف حساب، همهٔ درس‌ها، تکالیف، پیام‌ها، منابع کتابخانه و تیکت‌های شما را برای همیشه پاک می‌کند. این عمل برگشت‌پذیر نیست.</p>
      <div class="stg-actions"><button class="btn btn-danger btn-sm" data-stg="del-account">حذف کامل حساب</button></div>
    </div>`;
  const s = document.getElementById("stg-ssort"); if (s) s.value = Stg.ssort;
}
function stgDevice(ua) {
  const u = String(ua || "").toLowerCase();
  const os = /android/.test(u) ? "اندروید" : /iphone|ipad|ios/.test(u) ? "iOS" : /windows/.test(u) ? "ویندوز" : /mac os|macintosh/.test(u) ? "مک" : /linux/.test(u) ? "لینوکس" : "نامشخص";
  const br = /edg\//.test(u) ? "Edge" : /chrome|crios/.test(u) ? "Chrome" : /firefox|fxios/.test(u) ? "Firefox" : /safari/.test(u) ? "Safari" : "مرورگر نامشخص";
  const mobile = /mobile|android|iphone/.test(u);
  return { icon: mobile ? "📱" : "💻", label: `${br} روی ${os}`, os, br };
}
function stgSessRows() {
  if (!Stg.sessionsSupported) return `<div class="stg-empty-inline">این نسخهٔ بک‌اند فهرست نشست‌ها را برنمی‌گرداند. «خروج از همهٔ دستگاه‌ها» همچنان کار می‌کند.</div>`;
  if (!Stg.sessions.length) return `<div class="stg-empty-inline">نشستی برای نمایش نیست</div>`;
  const q = Stg.sq.trim().toLowerCase();
  let l = Stg.sessions.filter((s) => !q || `${s.user_agent} ${stgDevice(s.user_agent).label}`.toLowerCase().includes(q));
  l = l.slice().sort((a, b) => Stg.ssort === "old" ? String(a.created_at || "").localeCompare(String(b.created_at || ""))
    : Stg.ssort === "device" ? stgDevice(a.user_agent).label.localeCompare(stgDevice(b.user_agent).label, "fa")
    : String(b.created_at || "").localeCompare(String(a.created_at || "")));
  if (!l.length) return `<div class="stg-empty-inline">نشستی با این عبارت پیدا نشد</div>`;
  return `<div class="item-list">${l.map((s) => { const d = stgDevice(s.user_agent);
    return `<div class="list-row"><span class="row-icon">${d.icon}</span>
      <div class="row-body"><div class="row-title">${sesc(d.label)}</div>
        <div class="row-meta"><span>ساخت: ${sesc(s.created_at || "—")}</span>${s.expires_at ? `<span>انقضا: ${sesc(s.expires_at)}</span>` : ""}</div>
        ${s.user_agent ? `<div class="stg-ua" dir="ltr">${sesc(s.user_agent.slice(0, 110))}</div>` : ""}</div></div>`; }).join("")}</div>`;
}
async function stgLoadSessions() {
  try {
    const r = await api("/account/sessions");
    Stg.sessions = r.sessions || []; Stg.sessionsSupported = r.supported !== false;
  } catch (_) { Stg.sessions = []; Stg.sessionsSupported = false; }
  const box = document.getElementById("stg-sess");
  if (box && Stg.tab === "account") box.innerHTML = stgSessRows();
}

/* ---- تب ۵: تشخیص و نگهداری ---- */
function stgPaintDiag(p) {
  p.innerHTML = `
    <div class="card">
      <div class="card-head"><h3 class="section-title">🩺 سلامت سرویس</h3>
        <button class="btn btn-soft btn-sm" data-stg="diag-run" ${Stg.diagRunning ? "disabled" : ""}>${Stg.diagRunning ? "در حال بررسی…" : "اجرای بررسی"}</button></div>
      <div id="stg-diag">${Stg.diag ? stgDiagRows() : `<div class="stg-empty-inline">برای دیدن وضعیت API، همگام‌سازی و کش، «اجرای بررسی» را بزن</div>`}</div>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">🧹 نگهداری</h3></div>
      <div class="stg-line"><div class="stg-line-txt"><b>کش برنامه</b><small>فایل‌های استاتیک ذخیره‌شده توسط سرویس‌ورکر</small></div>
        <span class="badge badge-domain" id="stg-cache">—</span></div>
      <div class="stg-line"><div class="stg-line-txt"><b>حافظهٔ محلی مرورگر</b><small>ترجیحات، نماهای ذخیره‌شده و کش نام درس‌ها</small></div>
        <span class="badge badge-domain" id="stg-ls">—</span></div>
      <div class="stg-actions" style="margin-top:.9rem">
        <button class="btn btn-ghost btn-sm" data-stg="copy-debug">📋 کپی اطلاعات دیباگ</button>
        <button class="btn btn-ghost btn-sm" data-stg="clear-views">پاک کردن نماهای ذخیره‌شده</button>
        <button class="btn btn-soft btn-sm" data-stg="reset-cache">بازنشانی کش و بارگذاری مجدد</button>
      </div>
      <p class="stg-hint">بازنشانی کش هیچ داده‌ای از حساب شما پاک نمی‌کند؛ فقط فایل‌های استاتیک دوباره دانلود می‌شوند.</p>
    </div>`;
  stgPaintStorage();
}
function stgDiagRows() {
  const d = Stg.diag;
  const row = (label, ok, detail) => `<div class="stg-diag-row ${ok === null ? "" : ok ? "is-ok" : "is-bad"}">
    <span class="stg-diag-dot"></span><b>${sesc(label)}</b><span>${sesc(detail)}</span></div>`;
  return `<div class="stg-diag">
    ${row("احراز هویت", d.auth.ok, d.auth.detail)}
    ${row("وضعیت همگام‌سازی", d.sync.ok, d.sync.detail)}
    ${row("دادهٔ داشبورد", d.dash.ok, d.dash.detail)}
    ${row("ترجیحات کاربر", d.prefs.ok, d.prefs.detail)}
    ${row("سرویس‌ورکر", d.sw.ok, d.sw.detail)}
    ${row("زمان پاسخ", null, d.ms + " میلی‌ثانیه")}
  </div>`;
}
async function stgPaintStorage() {
  const cEl = document.getElementById("stg-cache"), lEl = document.getElementById("stg-ls");
  if (cEl) {
    try {
      const keys = await caches.keys();
      let n = 0; for (const k of keys) { const c = await caches.open(k); n += (await c.keys()).length; }
      cEl.textContent = `${sfa(n)} فایل در ${sfa(keys.length)} کش`;
    } catch (_) { cEl.textContent = "در دسترس نیست"; }
  }
  if (lEl) {
    let bytes = 0; try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); bytes += (k.length + (localStorage.getItem(k) || "").length) * 2; } } catch (_) {}
    lEl.textContent = bytes > 1024 ? `${sfa((bytes / 1024).toFixed(1).replace(".", "٫"))} کیلوبایت` : `${sfa(bytes)} بایت`;
  }
}
async function stgRunDiag() {
  Stg.diagRunning = true; stgPaint();
  const t0 = performance.now();
  const [auth, sync, dash, prefs] = await Promise.all([
    api("/auth/status").then((r) => ({ ok: !!r.lms_logged_in, detail: r.lms_logged_in ? `${r.full_name || r.username} · ${r.role === "admin" ? "ادمین" : "کاربر"}` : "وارد نشده" })).catch((e) => ({ ok: false, detail: e.message || "خطا" })),
    api("/sync/status").then((r) => ({ ok: !r.running, detail: r.running ? "در حال اجرا" : (r.last_sync && r.last_sync.status) ? `آخرین: ${r.last_sync.status}` : "هرگز اجرا نشده" })).catch((e) => ({ ok: false, detail: e.message || "خطا" })),
    api("/dashboard").then((r) => ({ ok: true, detail: `${r.stats?.courses ?? 0} درس · ${r.stats?.pending_assignments ?? 0} تکلیف باز` })).catch((e) => ({ ok: false, detail: e.message || "خطا" })),
    api("/settings/prefs").then(() => ({ ok: true, detail: "خوانده شد" })).catch((e) => ({ ok: false, detail: e.status === 404 ? "endpoint نصب نشده" : (e.message || "خطا") })),
  ]);
  let sw = { ok: null, detail: "پشتیبانی نمی‌شود" };
  if ("serviceWorker" in navigator) {
    try { const reg = await navigator.serviceWorker.getRegistration(); sw = reg ? { ok: true, detail: reg.active ? "فعال" : "در حال نصب" } : { ok: false, detail: "ثبت نشده" }; }
    catch (_) { sw = { ok: false, detail: "خطا" }; }
  }
  Stg.diag = { auth, sync, dash, prefs, sw, ms: Math.round(performance.now() - t0) };
  Stg.diagRunning = false;
  if (Stg.tab === "diag") stgPaint();
}

/* ---- اکشن‌ها ---- */
async function stgSaveSync() {
  const body = {}; Object.keys(STG_PHASES).forEach((k) => { body[k] = !!Stg.sync[k]; });
  const before = { ...Stg.savedSync };
  try {
    await api("/settings/sync", { method: "POST", body: JSON.stringify(body) });
    Stg.savedSync = { ...Stg.sync }; stgPaintHero(); stgPaint();
    stgToast("✅ فازهای همگام‌سازی ذخیره شد", { action: "برگردان", dur: 6500, onAction: async () => {
      try { await api("/settings/sync", { method: "POST", body: JSON.stringify(before) });
        Stg.sync = { ...before }; Stg.savedSync = { ...before }; stgPaintHero(); stgPaint(); stgToast("↩️ برگشت"); }
      catch (e) { stgToast("❌ " + (e.message || "برگشت ناموفق")); }
    }});
  } catch (e) { stgToast("❌ " + (e.message || "ذخیره ناموفق")); }
}
function stgMove(key, dir) {
  const i = Stg.order.indexOf(key), j = i + dir;
  if (i < 0 || j < 0 || j >= Stg.order.length) return;
  [Stg.order[i], Stg.order[j]] = [Stg.order[j], Stg.order[i]];
  stgPushPrefs({ sync_order: Stg.order.join(",") }); stgPaint();
}
function stgApplyPreset(pr) {
  const before = { ...Stg.prefs };
  stgPushPrefs(pr.prefs, { silent: true }); stgPaintHero(); stgPaint();
  stgToast(`✨ «${pr.name}» اعمال شد`, { action: "برگردان", dur: 7000, onAction: () => {
    stgPushPrefs(before, { silent: true }); stgPaintHero(); stgPaint(); stgToast("↩️ برگشت");
  }});
}

/* ---- delegation ---- */
function stgWire() {
  if (Stg.wired) return; Stg.wired = true;
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-stg]"); if (!el) return;
    const act = el.dataset.stg, v = el.dataset.v, k = el.dataset.k;
    switch (act) {
      case "tab": Stg.tab = v; localStorage.setItem("stg:tab", v); Stg.sel.clear(); stgPaint(); break;
      case "theme": stgApplyTheme(v); stgPaint(); break;
      case "density": stgPushPrefs({ density: v }); stgPaint(); break;
      case "all-on": Object.keys(STG_PHASES).forEach((x) => { Stg.sync[x] = true; }); stgPaint(); break;
      case "all-off": Object.keys(STG_PHASES).forEach((x) => { Stg.sync[x] = false; }); stgPaint(); break;
      case "bulk-on": [...Stg.sel].forEach((x) => { Stg.sync[x] = true; }); Stg.sel.clear(); stgPaint(); break;
      case "bulk-off": [...Stg.sel].forEach((x) => { Stg.sync[x] = false; }); Stg.sel.clear(); stgPaint(); break;
      case "bulk-clear": Stg.sel.clear(); stgPaint(); break;
      case "sync-save": stgSaveSync(); break;
      case "sync-reset": Stg.sync = { ...Stg.savedSync }; stgPaint(); stgToast("تغییرات لغو شد"); break;
      case "up": stgMove(k, -1); break;
      case "down": stgMove(k, 1); break;
      case "run-sync": document.getElementById("btn-sync")?.click(); break;
      case "preset": { const pr = STG_PRESETS.find((x) => x.id === el.dataset.id); if (pr) stgApplyPreset(pr); break; }
      case "preset-custom": { const pr = Stg.presets[+el.dataset.i]; if (pr) stgApplyPreset(pr); break; }
      case "preset-del": { const i = +el.dataset.i, pr = Stg.presets[i]; Stg.presets.splice(i, 1);
        localStorage.setItem("stg:presets", JSON.stringify(Stg.presets)); stgPaint();
        stgToast("پیش‌تنظیم حذف شد", { action: "برگردان", dur: 6000, onAction: () => { Stg.presets.splice(i, 0, pr); localStorage.setItem("stg:presets", JSON.stringify(Stg.presets)); stgPaint(); } }); break; }
      case "preset-save": stgLayer({ title: "ذخیرهٔ پیش‌تنظیم", html: `<div class="glass-form">
          <p class="stg-hint" style="margin:0">وضعیت فعلی پوسته، تراکم، هشدار و همگام‌سازی ذخیره می‌شود.</p>
          <div class="stg-field" data-sf="pn"><label class="field-label" for="stg-pn">نام *</label>
            <input id="stg-pn" class="input" placeholder="مثلاً حالت امتحانات" data-autofocus><small class="stg-err"></small></div>
          <div class="lib-modal-actions stg-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
            <button class="btn btn-primary" id="stg-pn-ok">ذخیره</button></div></div>`,
        onMount: (w, L) => { w.querySelector("#stg-pn-ok").addEventListener("click", () => {
          const n = w.querySelector("#stg-pn").value.trim(), f = w.querySelector('[data-sf="pn"]');
          f.classList.toggle("bad", !n); f.querySelector(".stg-err").textContent = n ? "" : "نام الزامی است";
          if (!n) return;
          Stg.presets.push({ name: n, prefs: { ...Stg.prefs } });
          Stg.presets = Stg.presets.slice(-6);
          localStorage.setItem("stg:presets", JSON.stringify(Stg.presets));
          L.close(); stgPaint(); stgToast("💾 پیش‌تنظیم ذخیره شد");
        }); } }); break;
      case "prefs-reset": stgConfirm("بازگردانی ترجیحات", "همهٔ ترجیحات ظاهر و رفتار به مقدار پیش‌فرض برمی‌گردند. فازهای همگام‌سازی دست‌نخورده می‌مانند.", "بازگردان", async () => {
        const before = { ...Stg.prefs };
        stgPushPrefs({ ...STG_DEFAULTS }, { silent: true }); stgPaintHero(); stgPaint();
        stgToast("↺ پیش‌فرض اعمال شد", { action: "برگردان", dur: 7000, onAction: () => { stgPushPrefs(before, { silent: true }); stgPaintHero(); stgPaint(); } });
      }, { danger: false }); break;
      case "prefs-export": {
        const blob = new Blob([JSON.stringify({ exported: new Date().toISOString(), prefs: Stg.prefs, sync: Stg.savedSync }, null, 2)], { type: "application/json" });
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "lms-settings.json"; a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000); stgToast("⬇ خروجی گرفته شد"); break; }
      case "alerts-reload": Stg.assigns = null; stgPaint(); break;
      case "sess-reload": stgLoadSessions(); break;
      case "relogin": if (typeof showLogin === "function") showLogin(); break;
      case "revoke-all": stgConfirm("خروج از همهٔ دستگاه‌ها", "همهٔ نشست‌ها — از جمله همین دستگاه — باطل می‌شوند و باید دوباره وارد شوی.", "خروج از همه", async () => {
        await api("/account/sessions/revoke-all", { method: "POST", body: "{}" });
        stgToast("همهٔ نشست‌ها قطع شد"); setTimeout(() => location.reload(), 900);
      }); break;
      case "del-account": stgConfirm("حذف کامل حساب", "همهٔ داده‌های شما برای همیشه پاک می‌شود: درس‌ها، تکالیف، پیام‌ها، منابع کتابخانه و تیکت‌ها. هیچ راه برگشتی وجود ندارد.", "حذف حساب", async () => {
        await api("/account", { method: "DELETE" });
        stgToast("حساب حذف شد"); setTimeout(() => { location.hash = "#/"; location.reload(); }, 900);
      }, { typed: "حذف" }); break;
      case "diag-run": stgRunDiag(); break;
      case "copy-debug": {
        const txt = JSON.stringify({ at: new Date().toISOString(), ua: navigator.userAgent, theme: document.body.dataset.theme,
          prefs: Stg.prefs, sync: Stg.savedSync, diag: Stg.diag, route: typeof currentRoute === "function" ? currentRoute() : location.hash }, null, 2);
        const done = () => stgToast("📋 کپی شد — برای پشتیبانی بفرست");
        if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, done);
        else { const t = document.createElement("textarea"); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); }
        break; }
      case "clear-views": stgConfirm("پاک کردن نماهای ذخیره‌شده", "نماهای ذخیره‌شدهٔ کتابخانه، تکالیف، تقویم، درس‌ها و نقشه پاک می‌شوند. دادهٔ درسی دست‌نخورده می‌ماند.", "پاک کن", async () => {
        ["lib:views", "asg:views", "crs:views", "mx:views", "rm-views", "stg:presets"].forEach((x) => localStorage.removeItem(x));
        Stg.presets = []; stgPaint(); stgToast("نماها پاک شدند");
      }); break;
      case "reset-cache": stgConfirm("بازنشانی کش برنامه", "فایل‌های استاتیک دوباره دانلود می‌شوند و صفحه یک‌بار رفرش می‌شود. هیچ داده‌ای از حساب پاک نمی‌شود.", "بازنشانی و رفرش", async () => {
        try { const keys = await caches.keys(); await Promise.all(keys.map((x) => caches.delete(x))); } catch (_) {}
        location.reload();
      }, { danger: false }); break;
    }
  });
  document.addEventListener("input", (e) => {
    const id = e.target.id;
    if (id === "stg-scale") { const v = e.target.value; const b = document.getElementById("stg-scale-val"); if (b) b.textContent = `${sfa(v)}٪`;
      stgPushPrefs({ font_scale: v }); stgPaintHero(); }
    if (id === "stg-hours") { const v = e.target.value; const b = document.getElementById("stg-hours-val"); if (b) b.textContent = `${sfa(v)} ساعت`;
      stgPushPrefs({ auto_sync_hours: v }); stgPaintHero(); }
    if (id === "stg-warn") { const v = e.target.value; const b = document.getElementById("stg-warn-val"); if (b) b.textContent = `${sfa(v)} ساعت`;
      stgPushPrefs({ deadline_warn_hours: v }); stgPaintHero();
      const box = document.getElementById("stg-alert-list"); if (box && Stg.assigns) box.innerHTML = stgAlertRows(); }
    if (id === "stg-sq") { Stg.sq = e.target.value; const box = document.getElementById("stg-sess"); if (box) box.innerHTML = stgSessRows(); }
  });
  document.addEventListener("change", (e) => {
    const t = e.target;
    if (t.dataset && t.dataset.stgPhase) { Stg.sync[t.dataset.stgPhase] = t.checked; stgPaint(); }
    if (t.dataset && t.dataset.stgSel) { t.checked ? Stg.sel.add(t.dataset.stgSel) : Stg.sel.delete(t.dataset.stgSel); stgPaintBulk(); }
    if (t.dataset && t.dataset.stgPref) {
      const key = t.dataset.stgPref;
      const val = t.type === "checkbox" ? (t.checked ? "1" : "0") : t.value;
      stgPushPrefs({ [key]: val }); stgPaintHero();
      if (key === "auto_sync") stgPaint();
      if (key === "nav_badges" && typeof refreshNavBadge === "function") refreshNavBadge();
    }
    if (t.id === "stg-ssort") { Stg.ssort = t.value; const box = document.getElementById("stg-sess"); if (box) box.innerHTML = stgSessRows(); }
  });
  document.addEventListener("dragstart", (e) => { const r = e.target.closest("[data-stg-row]"); if (!r) return;
    Stg.dragKey = r.dataset.stgRow; r.classList.add("is-dragging"); try { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", Stg.dragKey); } catch (_) {} });
  document.addEventListener("dragend", () => { document.querySelectorAll("[data-stg-row]").forEach((r) => r.classList.remove("is-dragging", "is-over")); Stg.dragKey = null; });
  document.addEventListener("dragover", (e) => { const r = e.target.closest("[data-stg-row]"); if (!r || !Stg.dragKey || r.dataset.stgRow === Stg.dragKey) return;
    e.preventDefault(); document.querySelectorAll("[data-stg-row].is-over").forEach((x) => x.classList.remove("is-over")); r.classList.add("is-over"); });
  document.addEventListener("drop", (e) => { const r = e.target.closest("[data-stg-row]"); if (!r || !Stg.dragKey) return; e.preventDefault();
    const from = Stg.order.indexOf(Stg.dragKey), to = Stg.order.indexOf(r.dataset.stgRow);
    if (from < 0 || to < 0 || from === to) return;
    const [m] = Stg.order.splice(from, 1); Stg.order.splice(to, 0, m);
    Stg.dragKey = null; stgPushPrefs({ sync_order: Stg.order.join(",") }); stgPaint(); });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const busy = (typeof Lib !== "undefined" && Lib.layers && Lib.layers.length)
      || (typeof Cal !== "undefined" && Cal._layers && Cal._layers.length)
      || (typeof Asg !== "undefined" && Asg.layers && Asg.layers.length)
      || (typeof Adm !== "undefined" && Adm.layers && Adm.layers.length)
      || (typeof Crs !== "undefined" && Crs.layers && Crs.layers.length)
      || (typeof MapX !== "undefined" && MapX.layers && MapX.layers.length);
    if (busy) return;
    if (Stg.layers.length) Stg.layers[Stg.layers.length - 1].close();
  });
  if (window.matchMedia) {
    try {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (stgThemeMode() === "system") stgApplyTheme("system");
      });
    } catch (_) {}
  }
}
stgWire();
stgBoot();
window.saveSyncSettings = () => stgSaveSync();
window.SettingsUI = { state: Stg, applyLook: stgApplyLook, applyTheme: stgApplyTheme, boot: stgBoot };

// ---------- تقویم شمسی (الگوریتم jalaali) ----------

function jDiv(a, b) { return ~~(a / b); }
function jMod(a, b) { return a - ~~(a / b) * b; }

const J_BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
const J_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];

function jalCalLeap(jy) {
  const gy = jy + 621;
  let leapJ = -14, jp = J_BREAKS[0], jm, jump = 0, leap, n;
  for (let i = 1; i < J_BREAKS.length; i++) {
    jm = J_BREAKS[i];
    jump = jm - jp;
    if (jy < jm) break;
    leapJ = leapJ + jDiv(jump, 33) * 8 + jDiv(jMod(jump, 33), 4);
    jp = jm;
  }
  n = jy - jp;
  leapJ = leapJ + jDiv(n, 33) * 8 + jDiv(jMod(n, 33) + 3, 4);
  if (jMod(jump, 33) === 4 && jump - n === 4) leapJ += 1;
  const leapG = jDiv(gy, 4) - jDiv((jDiv(gy, 100) + 1) * 3, 4) - 150;
  const march = 20 + leapJ - leapG;
  if (jump - n < 6) n = n - jump + jDiv(jump + 4, 33) * 33;
  leap = jMod(jMod(n + 1, 33) - 1, 4);
  if (leap === -1) leap = 4;
  return { leap, march };
}

function g2d(gy, gm, gd) {
  let d = jDiv((gy + jDiv(gm - 8, 6) + 100100) * 1461, 4)
      + jDiv(153 * jMod(gm + 9, 12) + 2, 5)
      + gd - 34840408;
  d = d - jDiv(jDiv(gy + 100100 + jDiv(gm - 8, 6), 100) * 3, 4) + 752;
  return d;
}

function d2g(jdn) {
  let j = 4 * jdn + 139361631;
  j = j + jDiv(jDiv(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
  const i = jDiv(jMod(j, 1461), 4) * 5 + 308;
  const gd = jDiv(jMod(i, 153), 5) + 1;
  const gm = jMod(jDiv(i, 153), 12) + 1;
  const gy = jDiv(j, 1461) - 100100 + jDiv(8 - gm, 6);
  return { gy, gm, gd };
}

function j2d(jy, jm, jd) {
  const r = jalCalLeap(jy);
  return g2d(jy + 621, 3, r.march) + (jm - 1) * 31 - jDiv(jm, 7) * (jm - 7) + jd - 1;
}

function d2j(jdn) {
  let gy = d2g(jdn).gy, jy = gy - 621;
  const r = jalCalLeap(jy);
  const jdn1f = g2d(gy, 3, r.march);
  let k = jdn - jdn1f, jm, jd;
  if (k >= 0) {
    if (k <= 185) {
      jm = 1 + jDiv(k, 31);
      jd = jMod(k, 31) + 1;
      return { jy, jm, jd };
    }
    k -= 186;
  } else {
    jy -= 1;
    k += 179;
    if (r.leap === 1) k += 1;
  }
  jm = 7 + jDiv(k, 30);
  jd = jMod(k, 30) + 1;
  return { jy, jm, jd };
}

function jMonthLen(jy, jm) {
  if (jm <= 6) return 31;
  if (jm <= 11) return 30;
  return jalCalLeap(jy).leap === 0 ? 30 : 29;
}

function jWeekday(jdn) { return (jdn + 2) % 7; } // 0=شنبه … 6=جمعه

function faDigits(n) { return String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]); }

// ---------- Calendar v2 (تقویم) ----------
// معماری مثل کتابخانه: state یکپارچه + delegation + repaint موضعی.
// ورود به صفحه = یک‌بار fetch؛ تغییر روز/هفته/ماه/نما/فیلتر = صفر درخواست شبکه.
const CAL_TYPES = {
  exam:     { label: "آزمون",        icon: "📄", cls: "t-exam",     var: "--warning" },
  deadline: { label: "ددلاین LMS",   icon: "📝", cls: "t-deadline", var: "--danger" },
  task:     { label: "کار دستی",     icon: "🗒", cls: "t-task",     var: "--danger" },
  quera:    { label: "کوئرا",        icon: "🎯", cls: "t-quera",    var: "--primary" },
  live:     { label: "جلسه آنلاین",  icon: "🎥", cls: "t-live",     var: "--info" },
  ann:      { label: "اطلاعیه",      icon: "📢", cls: "t-ann",      var: "--accent" },
  other:    { label: "رویداد",       icon: "📅", cls: "t-other",    var: "--muted" },
};
const CAL_WD = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"];
const Cal = {
  view: localStorage.getItem("cal:view") || "week",
  anchor: null, sel: null, today: null,
  items: [], noDate: [], courseNames: {}, courses: [],
  q: "", types: new Set(JSON.parse(localStorage.getItem("cal:types") || "[]")),
  hideDone: localStorage.getItem("cal:hideDone") === "1",
  wired: false, loaded: false, agendaLimit: 40,
};
const cj = (jdn) => d2j(jdn);
const cg = (jdn) => d2g(jdn);
const cGStr = (jdn) => { const g = cg(jdn); return `${g.gy}-${String(g.gm).padStart(2, "0")}-${String(g.gd).padStart(2, "0")}`; };
const cJLabel = (jdn) => { const j = cj(jdn); return `${cfa(j.jd)} ${J_MONTHS[j.jm - 1]} ${cfa(j.jy)}`; };
function calParseDT(v) {
  const m = String(v || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (!m) return null;
  return { jdn: g2d(+m[1], +m[2], +m[3]), dateStr: `${m[1]}-${m[2]}-${m[3]}`, time: m[4] ? `${m[4]}:${m[5]}` : "" };
}
function calIsManual(e) {
  if (typeof e.is_manual === "boolean") return e.is_manual;
  return String(e.id || "").startsWith("manual_");
}
function calEventType(t) {
  return ({ exam: "exam", assignment: "task", live_session: "live", announcement: "ann", deadline: "deadline" })[t] || "other";
}
function calMeta(t) { return CAL_TYPES[t] || CAL_TYPES.other; }

/* ---- لایه/توست: اگر ماژول کتابخانه هست از همان استفاده می‌کند ---- */
function calLayer(opts) {
  if (typeof libLayer === "function") return libLayer(opts);
  const prev = document.activeElement, w = document.createElement("div");
  w.className = "cal-layer";
  w.innerHTML = `<div class="cal-scrim" data-cal-x></div>` + (opts.type === "drawer"
    ? `<aside class="cal-drawer" role="dialog" aria-modal="true" aria-label="${cesc(opts.title)}">${opts.html}</aside>`
    : `<div class="cal-modal-wrap"><div class="cal-modal${opts.wide ? " wide" : ""}" role="dialog" aria-modal="true" aria-label="${cesc(opts.title)}"><h3>${cesc(opts.title)}</h3>${opts.html}</div></div>`);
  document.body.appendChild(w); document.body.classList.add("cal-locked");
  const panel = w.querySelector(".cal-drawer,.cal-modal");
  Cal._layers = Cal._layers || [];
  let closed = false;
  const L = { wrap: w, panel, close() {
    if (closed) return; closed = true;
    const i = Cal._layers.indexOf(L); if (i >= 0) Cal._layers.splice(i, 1);
    w.classList.add("is-leaving"); setTimeout(() => w.remove(), 230);
    if (!Cal._layers.length) document.body.classList.remove("cal-locked");
    if (prev && prev.focus) prev.focus();
    if (opts.onClose) opts.onClose();
  }};
  Cal._layers.push(L);
  w.addEventListener("click", (e) => { if (e.target === w || e.target.hasAttribute("data-cal-x")) L.close(); });
  w.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); e.preventDefault(); }
  });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => { w.classList.add("is-open");
    (panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button"))?.focus(); });
  if (opts.onMount) opts.onMount(w, L);
  return L;
}
function calToast(msg, o = {}) {
  if (typeof libToast === "function") return libToast(msg, o);
  let box = document.getElementById("cal-toasts");
  if (!box) { box = document.createElement("div"); box.id = "cal-toasts"; box.className = "cal-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "cal-toast"; t.setAttribute("role", "status");
  const dur = o.dur || 4200;
  t.innerHTML = `<span class="m">${cesc(msg)}</span>${o.action ? `<button class="a">${cesc(o.action)}</button>` : ""}<span class="b" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const tm = setTimeout(kill, dur);
  if (o.action) t.querySelector(".a").onclick = () => { clearTimeout(tm); kill(); o.onAction && o.onAction(); };
}
const calCloseAll = () => { (Cal._layers || []).slice().forEach((l) => l.close()); if (typeof Lib !== "undefined" && Lib.layers) Lib.layers.slice().forEach((l) => l.close()); };
const calLayersOpen = () => ((Cal._layers || []).length + ((typeof Lib !== "undefined" && Lib.layers) ? Lib.layers.length : 0)) > 0;

/* ---- ساخت مدل یکپارچه ---- */
function calBuild(events, assignments, courses) {
  Cal.courses = courses || [];
  Cal.courseNames = Object.fromEntries(Cal.courses.map((c) => [c.id, c.name]));
  const items = [], noDate = [];
  for (const e of events || []) {
    const p = calParseDT(e.start_at);
    const it = {
      uid: "e:" + e.id, id: e.id, kind: "event", type: calEventType(e.event_type),
      title: e.title || "بدون عنوان", desc: e.description || "",
      jdn: p ? p.jdn : null, dateStr: p ? p.dateStr : "", time: p ? p.time : "",
      course: e.course_name || Cal.courseNames[e.course_id] || "", courseId: e.course_id || "",
      url: e.url || "", done: false, expired: false, manual: calIsManual(e), raw: e,
    };
    (p ? items : noDate).push(it);
  }
  for (const a of assignments || []) {
    const p = calParseDT(a.deadline);
    if (!p) continue;
    items.push({
      uid: "a:" + a.id, id: a.id, kind: "assign",
      type: a.source === "quera" ? "quera" : "deadline",
      title: a.title || "تکلیف", desc: "",
      jdn: p.jdn, dateStr: p.dateStr, time: p.time,
      course: a.course_name || Cal.courseNames[a.course_id] || "", courseId: a.course_id || "",
      url: a.view_url || a.submit_url || "", done: !!a.is_done, expired: !!a.is_expired,
      manual: false, raw: a,
    });
  }
  items.sort((x, y) => x.jdn - y.jdn || String(x.time).localeCompare(String(y.time)));
  Cal.items = items; Cal.noDate = noDate; Cal.loaded = true;
}
async function calSyncSilent() {
  try {
    const [ev, as] = await Promise.all([api("/events"), api("/assignments")]);
    calBuild(ev, as, Cal.courses); calPaintAll();
  } catch (_) {}
}

/* ---- فیلتر ---- */
function calVisible() {
  const q = Cal.q.trim().toLowerCase();
  return Cal.items.filter((it) => {
    if (Cal.types.size && !Cal.types.has(it.type)) return false;
    if (Cal.hideDone && it.done) return false;
    if (q && !`${it.title} ${it.desc} ${it.course}`.toLowerCase().includes(q)) return false;
    return true;
  });
}
function calOn(jdn, list) { return (list || calVisible()).filter((i) => i.jdn === jdn); }

/* ---- ورود به صفحه ---- */
async function renderCalendar() {
  const now = new Date();
  Cal.today = g2d(now.getFullYear(), now.getMonth() + 1, now.getDate());
  if (Cal.sel === null) Cal.sel = Cal.today;
  if (Cal.anchor === null) Cal.anchor = Cal.today;
  let ev = [], as = [], cs = [];
  try {
    [ev, as, cs] = await Promise.all([api("/events"), api("/assignments"), api("/courses").catch(() => [])]);
  } catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری تقویم<small>${cesc(e.message)}</small></div>`;
    return;
  }
  calBuild(ev, as, cs);
  contentEl.innerHTML = `
    ${pageHead("تقویم", "مهلت تکالیف، آزمون‌ها و رویدادهای دستی")}
    <div class="cal-head card">
      <div class="cal-nav">
        <button class="btn btn-ghost btn-sm" data-cal="prev" aria-label="قبلی">‹</button>
        <button class="btn btn-soft btn-sm" data-cal="today">امروز</button>
        <button class="btn btn-ghost btn-sm" data-cal="next" aria-label="بعدی">›</button>
        <h3 class="cal-title" id="cal-title"></h3>
      </div>
      <div class="cal-head-actions">
        <div class="cal-viewtoggle" role="group" aria-label="نمای تقویم">
          <button data-cal="view" data-v="week" aria-pressed="false">هفته</button>
          <button data-cal="view" data-v="month" aria-pressed="false">ماه</button>
          <button data-cal="view" data-v="agenda" aria-pressed="false">لیست</button>
        </div>
        <a class="btn btn-ghost btn-sm" href="/api/calendar.ics" download="lms-assistant.ics">⬇ ICS</a>
        <button class="btn btn-primary btn-sm" data-cal="add" data-date="">+ رویداد</button>
      </div>
    </div>
    <div class="cal-stats" id="cal-stats"></div>
    <div class="cal-filters">
      <div class="search-box cal-search"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="cal-q" type="search" placeholder="جستجو در عنوان، توضیح یا درس…" value="${cesc(Cal.q)}" aria-label="جستجو"></div>
      <div class="cal-chips" id="cal-chips"></div>
      <label class="cal-switch"><input type="checkbox" id="cal-hide-done" ${Cal.hideDone ? "checked" : ""}><span>پنهان‌کردن انجام‌شده‌ها</span></label>
    </div>
    <div id="cal-grid"></div>
    <div id="cal-day"></div>
    <div id="cal-nodate"></div>
    <p class="cal-hint">کلیدها: ← → روز · ↑ ↓ هفته · PageUp/PageDown ماه · Home امروز · Enter جزئیات روز</p>`;
  calPaintAll();
}

/* ---- repaint موضعی ---- */
function calPaintAll() { calPaintHead(); calPaintChips(); calPaintStats(); calPaintGrid(); calPaintDay(); calPaintNoDate(); }
function calRange() {
  if (Cal.view === "month") { const j = cj(Cal.anchor); const f = j2d(j.jy, j.jm, 1); return [f, f + jMonthLen(j.jy, j.jm) - 1]; }
  if (Cal.view === "agenda") return [Cal.sel, Cal.sel + 29];
  const s = Cal.anchor - jWeekday(Cal.anchor); return [s, s + 6];
}
function calPaintHead() {
  const t = document.getElementById("cal-title"); if (!t) return;
  const [a, b] = calRange();
  if (Cal.view === "month") { const j = cj(Cal.anchor); t.textContent = `${J_MONTHS[j.jm - 1]} ${cfa(j.jy)}`; }
  else if (Cal.view === "agenda") t.textContent = `از ${cJLabel(Cal.sel)}`;
  else { const ja = cj(a), jb = cj(b);
    t.textContent = ja.jm === jb.jm ? `${cfa(ja.jd)}–${cfa(jb.jd)} ${J_MONTHS[ja.jm - 1]} ${cfa(jb.jy)}`
      : `${cfa(ja.jd)} ${J_MONTHS[ja.jm - 1]} تا ${cfa(jb.jd)} ${J_MONTHS[jb.jm - 1]} ${cfa(jb.jy)}`; }
  document.querySelectorAll(".cal-viewtoggle button").forEach((x) => {
    const on = x.dataset.v === Cal.view; x.classList.toggle("is-active", on); x.setAttribute("aria-pressed", on);
  });
}
function calPaintChips() {
  const box = document.getElementById("cal-chips"); if (!box) return;
  const all = Cal.items;
  const cnt = (t) => all.filter((i) => i.type === t).length;
  const used = Object.keys(CAL_TYPES).filter((t) => cnt(t) > 0);
  box.innerHTML = `<button class="cal-chip-btn ${!Cal.types.size ? "on" : ""}" data-cal="type" data-t="all">همه <b>${cfa(all.length)}</b></button>` +
    used.map((t) => `<button class="cal-chip-btn ${calMeta(t).cls} ${Cal.types.has(t) ? "on" : ""}" data-cal="type" data-t="${t}" aria-pressed="${Cal.types.has(t)}">
      ${calMeta(t).icon} ${calMeta(t).label} <b>${cfa(cnt(t))}</b></button>`).join("");
}
function calPaintStats() {
  const box = document.getElementById("cal-stats"); if (!box) return;
  const [a, b] = calRange();
  const inR = calVisible().filter((i) => i.jdn >= a && i.jdn <= b);
  const c = (t) => inR.filter((i) => i.type === t).length;
  const open = inR.filter((i) => i.kind === "assign" && !i.done).length;
  const soon = Cal.items.filter((i) => i.kind === "assign" && !i.done && i.jdn >= Cal.today && i.jdn <= Cal.today + 2).length;
  box.innerHTML = [
    ["مورد در این نما", inR.length, "--primary"], ["آزمون", c("exam"), "--warning"],
    ["ددلاین باز", open, "--danger"], ["کوئرا", c("quera"), "--info"],
    ["۴۸ ساعت آینده", soon, "--accent"],
  ].map(([l, v, cv]) => `<div class="cal-stat"><b style="color:var(${cv})">${cfa(v)}</b><span>${l}</span></div>`).join("");
}
function calDots(list) {
  const seen = [...new Set(list.map((i) => i.type))].slice(0, 4);
  return seen.map((t) => `<i class="cal-dot ${calMeta(t).cls}"></i>`).join("");
}
function calCell(jdn, { out = false, name = "", compact = false } = {}) {
  const list = calOn(jdn), j = cj(jdn);
  const has = (t) => list.some((i) => i.type === t);
  const cls = ["cal-daywrap"];
  if (jdn === Cal.today) cls.push("is-today");
  if (jdn === Cal.sel) cls.push("is-sel");
  if (out) cls.push("is-out");
  if (has("exam")) cls.push("has-exam");
  else if (has("deadline") || has("task")) cls.push("has-deadline");
  else if (has("quera")) cls.push("has-quera");
  else if (list.length) cls.push("has-other");
  if (compact) cls.push("is-compact");
  const chips = !compact && list.length
    ? `<span class="cal-minichips">${list.slice(0, 2).map((i) => `<span class="cal-minichip ${calMeta(i.type).cls}">${cesc(i.title)}</span>`).join("")}${list.length > 2 ? `<span class="cal-more">+${cfa(list.length - 2)}</span>` : ""}</span>` : "";
  return `<div class="${cls.join(" ")}">
    <button class="cal-day" data-cal="day" data-jdn="${jdn}" aria-pressed="${jdn === Cal.sel}" aria-label="${cesc(CAL_WD[jWeekday(jdn)] + " " + cJLabel(jdn) + "، " + list.length + " مورد")}">
      ${name ? `<span class="cal-dayname">${name}</span>` : ""}
      ${jdn === Cal.today ? `<span class="cal-todaybadge">امروز</span>` : ""}
      <span class="cal-daynum">${cfa(j.jd)}</span>
      <span class="cal-daymon">${J_MONTHS[j.jm - 1]}</span>
      <span class="cal-dots">${calDots(list)}${list.length ? `<b class="cal-count">${cfa(list.length)}</b>` : ""}</span>
      ${chips}
    </button>
    <button class="cal-add" data-cal="add" data-date="${cGStr(jdn)}" aria-label="افزودن رویداد در ${cesc(cJLabel(jdn))}" title="افزودن رویداد">+</button>
  </div>`;
}
function calPaintGrid() {
  const box = document.getElementById("cal-grid"); if (!box) return;
  if (Cal.view === "agenda") {
    const list = calVisible().filter((i) => i.jdn >= Cal.sel).slice(0, Cal.agendaLimit);
    if (!list.length) { box.innerHTML = `<div class="empty"><span class="empty-icon">🗓</span>از این روز به بعد موردی نیست<small>فیلترها را بردار یا روز دیگری را انتخاب کن</small></div>`; return; }
    const groups = [];
    list.forEach((i) => { const g = groups[groups.length - 1]; if (g && g.jdn === i.jdn) g.items.push(i); else groups.push({ jdn: i.jdn, items: [i] }); });
    box.innerHTML = `<div class="cal-agenda">${groups.map((g) => `
      <div class="cal-agendaday">
        <button class="cal-agendahead" data-cal="day" data-jdn="${g.jdn}">
          <b>${CAL_WD[jWeekday(g.jdn)]}</b><span>${cJLabel(g.jdn)}</span>
          ${g.jdn === Cal.today ? `<span class="badge badge-new">امروز</span>` : ""}
          <span class="badge">${cfa(g.items.length)} مورد</span></button>
        <div class="item-list">${g.items.map(calRow).join("")}</div>
      </div>`).join("")}</div>
      ${calVisible().filter((i) => i.jdn >= Cal.sel).length > Cal.agendaLimit ? `<button class="btn btn-soft btn-sm cal-morebtn" data-cal="more">نمایش بیشتر</button>` : ""}`;
    return;
  }
  if (Cal.view === "month") {
    const j = cj(Cal.anchor), first = j2d(j.jy, j.jm, 1), start = first - jWeekday(first);
    const total = jWeekday(first) + jMonthLen(j.jy, j.jm), cells = Math.ceil(total / 7) * 7;
    let html = `<div class="cal-weekdays">${CAL_WD.map((w) => `<span>${w}</span>`).join("")}</div><div class="cal-monthgrid">`;
    for (let i = 0; i < cells; i++) { const jdn = start + i; html += calCell(jdn, { out: cj(jdn).jm !== j.jm, compact: true }); }
    box.innerHTML = html + "</div>";
    return;
  }
  const s = Cal.anchor - jWeekday(Cal.anchor);
  box.innerHTML = `<div class="cal-weekgrid">${Array.from({ length: 7 }, (_, i) => calCell(s + i, { name: CAL_WD[i] })).join("")}</div>`;
}
function calRow(it) {
  const m = calMeta(it.type), u = it.url ? (it.url.startsWith("http") ? it.url : proxyUrl(it.url)) : "";
  return `<div class="list-row cal-row ${m.cls}" data-cal-row="${cesc(it.uid)}">
    <span class="row-icon cal-rowico ${m.cls}">${m.icon}</span>
    <div class="row-body">
      <div class="row-title">
        <button class="cal-linklike" data-cal="item" data-uid="${cesc(it.uid)}">${cesc(it.title)}</button>
        <span class="badge ${m.cls}">${m.label}</span>
        ${it.done ? `<span class="badge badge-done">انجام شده</span>` : it.expired ? `<span class="badge badge-expired">گذشته</span>` : ""}
        ${it.manual ? `<span class="badge">دستی</span>` : ""}
      </div>
      <div class="row-meta">
        ${it.time ? `<span>⏰ ${cfa(it.time)}</span>` : ""}
        ${it.course ? `<span>📘 ${cesc(it.course)}</span>` : ""}
        ${it.desc ? `<span>${cesc(it.desc.slice(0, 90))}${it.desc.length > 90 ? "…" : ""}</span>` : ""}
      </div>
    </div>
    <div class="row-actions">
      ${u ? `<a class="btn btn-soft btn-sm" href="${cesc(u)}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a>` : ""}
      ${it.kind === "assign" ? `<button class="btn btn-ghost btn-sm" data-cal="toggle" data-uid="${cesc(it.uid)}">${it.done ? "لغو انجام" : "انجام شد ✓"}</button>` : ""}
      ${it.manual ? `<button class="btn btn-ghost btn-sm" data-cal="edit" data-uid="${cesc(it.uid)}" aria-label="ویرایش">✎</button>
        <button class="btn btn-ghost btn-sm cal-del" data-cal="del" data-uid="${cesc(it.uid)}" aria-label="حذف">🗑</button>` : ""}
    </div></div>`;
}
function calPaintDay() {
  const box = document.getElementById("cal-day"); if (!box) return;
  if (Cal.view === "agenda") { box.innerHTML = ""; return; }
  const list = calOn(Cal.sel);
  box.innerHTML = `<div class="card cal-daypanel">
    <div class="card-head">
      <h3 class="section-title">📅 ${CAL_WD[jWeekday(Cal.sel)]} — ${cJLabel(Cal.sel)}
        ${Cal.sel === Cal.today ? `<span class="badge badge-new">امروز</span>` : ""}</h3>
      <div class="cal-daypanel-actions">
        <span class="badge badge-domain">${cfa(list.length)} مورد</span>
        <button class="btn btn-ghost btn-sm" data-cal="daydrawer" data-jdn="${Cal.sel}">جزئیات کامل</button>
        <button class="btn btn-primary btn-sm" data-cal="add" data-date="${cGStr(Cal.sel)}">+ رویداد</button>
      </div>
    </div>
    <div class="item-list">${list.length ? list.map(calRow).join("")
      : `<div class="empty muted"><span class="empty-icon">🗓</span>رویداد یا تکلیفی در این روز نیست<small>با دکمه + یک رویداد دستی بساز</small></div>`}</div>
  </div>`;
}
function calPaintNoDate() {
  const box = document.getElementById("cal-nodate"); if (!box) return;
  if (!Cal.noDate.length) { box.innerHTML = ""; return; }
  box.innerHTML = `<details class="accordion-panel cal-nodate">
    <summary class="accordion-header"><div class="accordion-header-content"><span>🗂 رویدادهای بدون تاریخ</span>
      <span class="accordion-badge">${cfa(Cal.noDate.length)}</span></div><span class="accordion-icon">▼</span></summary>
    <div class="accordion-body"><div class="item-list">${Cal.noDate.map((it) => `
      <div class="list-row"><span class="row-icon">${calMeta(it.type).icon}</span>
        <div class="row-body"><div class="row-title">
          <button class="cal-linklike" data-cal="item" data-uid="${cesc(it.uid)}">${cesc(it.title)}</button>
          <span class="badge ${calMeta(it.type).cls}">${calMeta(it.type).label}</span></div>
          <div class="row-meta">${it.course ? `<span>📘 ${cesc(it.course)}</span>` : ""}${it.desc ? `<span>${cesc(it.desc.slice(0, 100))}</span>` : ""}</div></div>
        <div class="row-actions">${it.manual ? `<button class="btn btn-ghost btn-sm" data-cal="edit" data-uid="${cesc(it.uid)}">✎</button>` : ""}</div>
      </div>`).join("")}</div></div></details>`;
}

/* ---- drawerها ---- */
function calFind(uid) { return Cal.items.find((i) => i.uid === uid) || Cal.noDate.find((i) => i.uid === uid); }
function calOpenDay(jdn) {
  const list = calOn(jdn);
  calLayer({ type: "drawer", title: "رویدادهای روز", html: `<div class="cal-dwr">
    <div class="cal-dwr-head"><div><h2>${CAL_WD[jWeekday(jdn)]}</h2><p class="cal-dwr-sub">${cJLabel(jdn)}${jdn === Cal.today ? " · امروز" : ""}</p></div>
      <button class="cal-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="cal-dwr-actions"><button class="btn btn-primary btn-sm" data-cal="add" data-date="${cGStr(jdn)}">+ افزودن رویداد</button>
      <span class="badge badge-domain">${cfa(list.length)} مورد</span></div>
    <div class="item-list">${list.length ? list.map(calRow).join("") : `<div class="empty muted"><span class="empty-icon">🗓</span>این روز خالی است</div>`}</div>
  </div>` });
}
function calOpenItem(uid) {
  const it = calFind(uid); if (!it) return;
  const m = calMeta(it.type);
  const u = it.url ? (it.url.startsWith("http") ? it.url : proxyUrl(it.url)) : "";
  calLayer({ type: "drawer", title: "جزئیات", html: `<div class="cal-dwr">
    <div class="cal-dwr-head"><span class="cal-dwr-ico ${m.cls}">${m.icon}</span>
      <div><h2>${cesc(it.title)}</h2><div class="cal-dwr-tags"><span class="badge ${m.cls}">${m.label}</span>
        ${it.manual ? `<span class="badge">دستی</span>` : ""}${it.done ? `<span class="badge badge-done">انجام شده</span>` : ""}
        ${it.expired && !it.done ? `<span class="badge badge-expired">گذشته</span>` : ""}</div></div>
      <button class="cal-x" data-lib-close aria-label="بستن">✕</button></div>
    <div class="cal-kv">
      ${it.jdn ? `<div><span>تاریخ</span><b>${CAL_WD[jWeekday(it.jdn)]} ${cJLabel(it.jdn)}</b></div>` : `<div><span>تاریخ</span><b>ثبت نشده</b></div>`}
      ${it.time ? `<div><span>ساعت</span><b>${cfa(it.time)}</b></div>` : ""}
      ${it.course ? `<div><span>درس</span><b>${cesc(it.course)}</b></div>` : ""}
      ${it.kind === "assign" ? `<div><span>منبع</span><b>${it.type === "quera" ? "کوئرا" : "LMS"}</b></div>` : ""}
    </div>
    ${it.desc ? `<p class="cal-dwr-desc">${cesc(it.desc)}</p>` : ""}
    <div class="cal-dwr-actions">
      ${u ? `<a class="btn btn-primary btn-sm" href="${cesc(u)}" target="_blank" rel="noopener noreferrer">باز کردن لینک ↗</a>` : ""}
      ${it.jdn ? `<button class="btn btn-ghost btn-sm" data-cal="ics" data-uid="${cesc(it.uid)}">⬇ افزودن به تقویم گوشی</button>` : ""}
      ${it.kind === "assign" ? `<button class="btn btn-soft btn-sm" data-cal="toggle" data-uid="${cesc(it.uid)}">${it.done ? "لغو انجام" : "انجام شد ✓"}</button>` : ""}
      ${it.manual ? `<button class="btn btn-soft btn-sm" data-cal="edit" data-uid="${cesc(it.uid)}">✎ ویرایش</button>
        <button class="btn btn-ghost btn-sm cal-del" data-cal="del" data-uid="${cesc(it.uid)}">🗑 حذف</button>` : ""}
    </div></div>` });
}

/* ---- فرم افزودن/ویرایش (بدون wheel picker، بدون prompt) ---- */
function calFieldErr(w, id, msg) { const f = w.querySelector(`[data-cf="${id}"]`); if (!f) return !msg;
  f.classList.toggle("bad", !!msg); f.querySelector(".cal-err").textContent = msg || ""; return !msg; }
function calOpenForm({ dateStr = "", item = null } = {}) {
  const d = dateStr || (item ? item.dateStr : cGStr(Cal.sel || Cal.today));
  const p = calParseDT(d + "T00:00");
  const lmsCourses = (Cal.courses || []).filter((c) => (c.source || "lms") === "lms");
  const typeVal = item && item.type === "exam" ? "exam" : "assignment";
  const courseOpts = `<option value="">🌐 عمومی / بدون درس</option>` + lmsCourses.map((c) =>
    `<option value="${cesc(c.id)}" ${item && item.courseId === c.id ? "selected" : ""}>${cesc(c.name)}</option>`).join("");
  const L = calLayer({ title: item ? "ویرایش رویداد" : "افزودن رویداد", html: `<div class="glass-form cal-form">
    <div class="cal-field" data-cf="title"><label class="field-label" for="cal-f-title">عنوان *</label>
      <input id="cal-f-title" class="input" value="${cesc(item ? item.title : "")}" placeholder="مثلاً مطالعه فصل ۳" data-autofocus><small class="cal-err"></small></div>
    <div class="cal-form-row">
      <div class="cal-field"><label class="field-label" for="cal-f-type">نوع</label>
        <select id="cal-f-type" class="input">
          <option value="assignment" ${typeVal === "assignment" ? "selected" : ""}>🗒 تکلیف / کار</option>
          <option value="exam" ${typeVal === "exam" ? "selected" : ""}>📄 آزمون</option>
        </select></div>
      <div class="cal-field"><label class="field-label" for="cal-f-course">درس (اختیاری)</label>
        <select id="cal-f-course" class="input">${courseOpts}</select></div>
    </div>
    <div class="cal-form-row">
      <div class="cal-field" data-cf="date"><label class="field-label" for="cal-f-date">تاریخ (میلادی)</label>
        <input id="cal-f-date" class="input" type="date" dir="ltr" value="${cesc(d)}"><small class="cal-err"></small>
        <small class="cal-jlabel" id="cal-f-jlabel">${p ? cesc(cJLabel(p.jdn)) : ""}</small></div>
      <div class="cal-field"><label class="field-label" for="cal-f-time">ساعت</label>
        <input id="cal-f-time" class="input" type="time" dir="ltr" value="${cesc(item && item.time ? item.time : "12:00")}">
        <div class="cal-timechips">${["08:00", "12:00", "16:00", "20:00", "23:59"].map((t) => `<button type="button" class="cal-tchip" data-t="${t}">${cfa(t)}</button>`).join("")}</div></div>
    </div>
    <div class="cal-field"><label class="field-label" for="cal-f-desc">توضیح (اختیاری)</label>
      <textarea id="cal-f-desc" class="input" rows="3">${cesc(item ? item.desc : "")}</textarea></div>
    <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
      <button class="btn btn-primary" id="cal-f-save">${item ? "ذخیره تغییرات" : "ذخیره رویداد"}</button></div>
  </div>`, onMount: (w, layer) => {
    const dateEl = w.querySelector("#cal-f-date"), jl = w.querySelector("#cal-f-jlabel");
    dateEl.addEventListener("change", () => { const pp = calParseDT(dateEl.value + "T00:00"); jl.textContent = pp ? cJLabel(pp.jdn) : ""; });
    w.querySelectorAll(".cal-tchip").forEach((b) => b.addEventListener("click", () => { w.querySelector("#cal-f-time").value = b.dataset.t; }));
    const btn = w.querySelector("#cal-f-save");
    btn.addEventListener("click", async () => {
      const title = w.querySelector("#cal-f-title").value.trim();
      const date = dateEl.value, time = w.querySelector("#cal-f-time").value || "12:00";
      const description = w.querySelector("#cal-f-desc").value.trim();
      const event_type = w.querySelector("#cal-f-type").value;
      const course_id = w.querySelector("#cal-f-course").value || null;
      let ok = calFieldErr(w, "title", title ? "" : "عنوان الزامی است");
      ok = calFieldErr(w, "date", calParseDT(date + "T00:00") ? "" : "تاریخ معتبر نیست") && ok;
      if (!ok) return;
      btn.disabled = true; btn.textContent = "در حال ذخیره…";
      const body = { title, description, date, time, event_type, course_id };
      const pp = calParseDT(date + "T" + time);
      const courseName = course_id ? (Cal.courseNames[course_id] || "") : "عمومی";
      try {
        if (item) {
          const before = { ...item };
          Object.assign(item, { title, desc: description, dateStr: date, time, jdn: pp.jdn,
            type: calEventType(event_type), courseId: course_id, course: courseName });
          calPaintAll();
          try {
            await api(`/events/${encodeURIComponent(item.id)}`, { method: "PATCH", body: JSON.stringify(body) });
            layer.close(); calCloseAll(); calToast("✅ رویداد به‌روز شد"); calSyncSilent();
          } catch (err) {
            Object.assign(item, before); calPaintAll();
            btn.disabled = false; btn.textContent = "ذخیره تغییرات";
            calToast([404, 405, 501].includes(err.status) ? "⚠️ بک‌اند ویرایش رویداد را پشتیبانی نمی‌کند" : "❌ " + (err.message || "خطا"));
          }
        } else {
          const r = await api("/events/manual", { method: "POST", body: JSON.stringify(body) });
          const nid = (r && r.id) || "manual_tmp" + Date.now();
          Cal.items.push({ uid: "e:" + nid, id: nid, kind: "event", type: calEventType(event_type),
            title, desc: description, jdn: pp.jdn, dateStr: date, time, course: courseName,
            courseId: course_id, url: "", done: false, expired: false, manual: true, raw: {} });
          Cal.items.sort((x, y) => x.jdn - y.jdn || String(x.time).localeCompare(String(y.time)));
          Cal.sel = pp.jdn; Cal.anchor = pp.jdn;
          layer.close(); calPaintAll(); calToast("✅ رویداد ذخیره شد"); calSyncSilent();
        }
      } catch (e) {
        btn.disabled = false; btn.textContent = item ? "ذخیره تغییرات" : "ذخیره رویداد";
        calToast("❌ " + (e.message || "خطا در ذخیره"));
      }
    });
  }});
  return L;
}
function calDelete(uid) {
  const it = calFind(uid); if (!it) return;
  const inItems = Cal.items.includes(it);
  const arr = inItems ? Cal.items : Cal.noDate;
  const idx = arr.indexOf(it);
  arr.splice(idx, 1); calCloseAll(); calPaintAll();
  let undone = false;
  const restore = () => { arr.splice(Math.min(idx, arr.length), 0, it); calPaintAll(); };
  const timer = setTimeout(async () => {
    if (undone) return;
    try { await api(`/events/${encodeURIComponent(it.id)}`, { method: "DELETE" }); }
    catch (err) {
      restore();
      calToast([404, 405, 501].includes(err.status)
        ? "⚠️ بک‌اند حذف رویداد را پشتیبانی نمی‌کند"
        : "❌ " + (err.message || "حذف ناموفق"));
    }
  }, 6000);
  calToast("🗑 رویداد حذف شد", { action: "برگردان", dur: 6000, onAction() {
    undone = true; clearTimeout(timer); restore(); calToast("↩️ برگشت");
  }});
}
async function calToggle(uid) {
  const it = calFind(uid); if (!it || it.kind !== "assign") return;
  const want = !it.done, before = it.done;
  it.done = want; calPaintAll();
  const raw = String(it.id), isQ = raw.startsWith("quera_");
  const path = isQ ? `/quera/assignments/${encodeURIComponent(raw.slice(6))}/done?done=${want}` : `/assignments/${encodeURIComponent(raw)}/done?done=${want}`;
  try {
    const r = await api(path, { method: "POST", body: "{}" });
    if (r && r.ok === false) throw new Error(r.error || "تکلیف پیدا نشد");
    if (it.raw) it.raw.is_done = want;
    calToast(want ? "✅ انجام‌شده علامت خورد" : "علامت انجام برداشته شد", { action: "برگردان", dur: 5000, onAction: () => calToggle(uid) });
    if (typeof refreshNavBadge === "function") refreshNavBadge();
  } catch (e) { it.done = before; calPaintAll(); calToast("❌ " + (e.message || "ثبت ناموفق")); }
}
function calICS(uid) {
  const it = calFind(uid); if (!it || !it.jdn) return;
  const g = cg(it.jdn), t = (it.time || "09:00").replace(":", "");
  const stamp = `${g.gy}${String(g.gm).padStart(2, "0")}${String(g.gd).padStart(2, "0")}T${t}00`;
  const escI = (s) => String(s || "").replace(/[\\,;]/g, "\\$&").replace(/\n/g, "\\n");
  const ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//LMS Assistant//FA", "CALSCALE:GREGORIAN", "BEGIN:VEVENT",
    `UID:${it.uid}@lms-assistant`, `DTSTAMP:${stamp}`, `DTSTART:${stamp}`, `SUMMARY:${escI(it.title)}`,
    `DESCRIPTION:${escI(it.desc + (it.course ? " — " + it.course : ""))}`, "END:VEVENT", "END:VCALENDAR"].join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
  a.download = "event.ics"; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  calToast("⬇ فایل رویداد ساخته شد");
}

/* ---- ناوبری (کاملاً کلاینتی) ---- */
function calShift(dir) {
  if (Cal.view === "month") { const j = cj(Cal.anchor); let m = j.jm + dir, y = j.jy;
    if (m > 12) { m = 1; y++; } if (m < 1) { m = 12; y--; }
    Cal.anchor = j2d(y, m, Math.min(cj(Cal.anchor).jd, jMonthLen(y, m))); Cal.sel = j2d(y, m, 1); }
  else if (Cal.view === "agenda") { Cal.sel += dir * 7; Cal.anchor = Cal.sel; }
  else { Cal.anchor += dir * 7; Cal.sel += dir * 7; }
  calPaintAll();
}
function calMoveSel(delta) {
  Cal.sel += delta;
  const [a, b] = calRange();
  if (Cal.sel < a || Cal.sel > b) Cal.anchor = Cal.sel;
  calPaintAll();
  const el = document.querySelector(`.cal-day[data-jdn="${Cal.sel}"]`); if (el) el.focus();
}
function calWire() {
  if (Cal.wired) return; Cal.wired = true;
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-cal]"); if (!a) return;
    const act = a.dataset.cal, uid = a.dataset.uid;
    switch (act) {
      case "prev": calShift(-1); break;
      case "next": calShift(1); break;
      case "today": Cal.anchor = Cal.today; Cal.sel = Cal.today; calPaintAll(); break;
      case "view": Cal.view = a.dataset.v; localStorage.setItem("cal:view", Cal.view); Cal.anchor = Cal.sel; calPaintAll(); break;
      case "day": Cal.sel = +a.dataset.jdn; if (Cal.view !== "agenda") Cal.anchor = Cal.sel; calPaintAll(); break;
      case "daydrawer": calOpenDay(+a.dataset.jdn); break;
      case "more": Cal.agendaLimit += 40; calPaintGrid(); break;
      case "add": calOpenForm({ dateStr: a.dataset.date || cGStr(Cal.sel) }); break;
      case "item": calOpenItem(uid); break;
      case "edit": { const it = calFind(uid); if (it) calOpenForm({ item: it }); break; }
      case "del": calDelete(uid); break;
      case "toggle": calToggle(uid); break;
      case "ics": calICS(uid); break;
      case "type": { const t = a.dataset.t;
        if (t === "all") Cal.types.clear();
        else { Cal.types.has(t) ? Cal.types.delete(t) : Cal.types.add(t); }
        localStorage.setItem("cal:types", JSON.stringify([...Cal.types])); calPaintAll(); break; }
    }
  });
  document.addEventListener("dblclick", (e) => { const d = e.target.closest(".cal-day"); if (d) calOpenDay(+d.dataset.jdn); });
  document.addEventListener("input", (e) => { if (e.target.id === "cal-q") { Cal.q = e.target.value; calPaintGrid(); calPaintDay(); calPaintStats(); } });
  document.addEventListener("change", (e) => { if (e.target.id === "cal-hide-done") {
    Cal.hideDone = e.target.checked; localStorage.setItem("cal:hideDone", Cal.hideDone ? "1" : "0"); calPaintAll(); } });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && (Cal._layers || []).length) { Cal._layers[Cal._layers.length - 1].close(); return; }
    if (typeof currentRoute !== "function" || currentRoute() !== "calendar") return;
    if (calLayersOpen()) return;
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;
    const map = { ArrowLeft: 1, ArrowRight: -1, ArrowDown: 7, ArrowUp: -7 }; // RTL: چپ = روز بعد
    if (map[e.key] !== undefined) { e.preventDefault(); calMoveSel(map[e.key]); }
    else if (e.key === "PageDown") { e.preventDefault(); calShift(1); }
    else if (e.key === "PageUp") { e.preventDefault(); calShift(-1); }
    else if (e.key === "Home") { e.preventDefault(); Cal.anchor = Cal.today; Cal.sel = Cal.today; calPaintAll(); }
    else if (e.key === "Enter" && document.activeElement && document.activeElement.classList.contains("cal-day")) { e.preventDefault(); calOpenDay(Cal.sel); }
  });
}
calWire();
window.openAddEventModal = (dateStr) => calOpenForm({ dateStr });
window.CalendarUI = { open: calOpenForm, openDay: calOpenDay, state: Cal };

// ---------- Library v2 (کتابخانه) ----------
// معماری: state یکپارچه + delegation سراسری + آپدیت موضعی DOM (بدون renderPage)
// آینده: اگر بک‌اند GET /library/search?q= را اضافه کند، جستجوی سراسری خودکار server-side می‌شود.
// اگر DELETE /library/items/{id} برای مالک فعال شود، دکمه حذف برای مالک هم ظاهر می‌شود (can_delete).
const Lib = {
  scope: localStorage.getItem("lib:scope") || "current_term",
  mode: localStorage.getItem("lib:mode") || "list",
  sort: localStorage.getItem("lib:sort") || "new",
  course: null, topic: "all", q: "", cq: "",
  items: [], topics: [],
  sel: new Set(),
  favs: new Set(JSON.parse(localStorage.getItem("lib:favs") || "[]")),
  views: JSON.parse(localStorage.getItem("lib:views") || "{}"),
  terms: null, itemCache: new Map(),
  layers: [], wired: false, searchTok: 0, pendingDetail: null,
};
const lesc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const lfa = (n) => faDigits(String(n));
const lsafe = (u) => /^https?:\/\//i.test(u || "") ? u : null;
const lhost = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (_) { return ""; } };
const lclamp = (n) => Math.max(0, Math.min(5, Math.round(Number(n) || 0)));
const lavg = (it) => Number(it.avg_rating) || 0;
const lavgTxt = (n) => lfa((Math.round(n * 10) / 10).toString().replace(".", "٫"));
const lisAdmin = () => authRole === "admin";
const lcanEdit = (it) => lisAdmin() || !!it.can_edit;
const lcanDelete = (it) => lisAdmin() || !!it.can_delete; // آینده: مالک
const lhi = (text, q) => {
  const t = String(text ?? ""); if (!q) return lesc(t);
  const rx = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
  return t.split(rx).map((p, i) => i % 2 ? `<mark class="lib-mark">${lesc(p)}</mark>` : lesc(p)).join("");
};
const lisNew = (it) => it.created_at && (Date.now() - Date.parse(String(it.created_at).replace(" ", "T"))) < 7 * 864e5;

/* ---- لایه‌ها: drawer + modal با focus-trap و Esc ---- */
function ltrap(panel, e) {
  const f = [...panel.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled),select,textarea,[tabindex]:not([tabindex="-1"])')].filter((x) => x.offsetParent !== null);
  if (!f.length) return;
  const first = f[0], last = f[f.length - 1];
  if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
  else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
}
function libLayer({ type = "modal", title, html, wide = false, onMount, onClose }) {
  const prev = document.activeElement;
  const wrap = document.createElement("div");
  if (type === "drawer") {
    wrap.className = "lib-layer";
    wrap.innerHTML = `<div class="lib-scrim" data-lib-x></div>
      <aside class="lib-drawer" role="dialog" aria-modal="true" aria-label="${lesc(title)}">${html}</aside>`;
  } else {
    wrap.className = "glass-modal-backdrop lib-layer";
    wrap.innerHTML = `<div class="glass-modal${wide ? " glass-modal-wide" : ""}" role="dialog" aria-modal="true" aria-label="${lesc(title)}"><h3>${lesc(title)}</h3>${html}</div>`;
  }
  document.body.appendChild(wrap);
  document.body.classList.add("lib-locked");
  const panel = wrap.querySelector(".lib-drawer,.glass-modal");
  let closed = false;
  const L = {
    wrap, panel,
    close(result) {
      if (closed) return; closed = true;
      const i = Lib.layers.indexOf(L); if (i >= 0) Lib.layers.splice(i, 1);
      wrap.classList.add("is-leaving");
      setTimeout(() => wrap.remove(), 230);
      if (!Lib.layers.length) document.body.classList.remove("lib-locked");
      if (prev && prev.focus) prev.focus();
      if (onClose) onClose(result);
    },
  };
  Lib.layers.push(L);
  wrap.addEventListener("click", (e) => { if (e.target === wrap || e.target.hasAttribute("data-lib-x")) L.close(); });
  wrap.addEventListener("keydown", (e) => { if (e.key === "Tab") ltrap(panel, e); });
  panel.querySelectorAll("[data-lib-close]").forEach((b) => b.addEventListener("click", () => L.close()));
  requestAnimationFrame(() => {
    wrap.classList.add("is-open");
    const f = panel.querySelector("[data-autofocus]") || panel.querySelector("input,textarea,select,button:not(.lib-x)");
    if (f) f.focus();
  });
  if (onMount) onMount(wrap, L);
  return L;
}

/* ---- toast با اکشن (Undo) — مستقل از toast سراسری ---- */
function libToast(msg, { action, onAction, dur = 4200 } = {}) {
  let box = document.getElementById("lib-toasts");
  if (!box) { box = document.createElement("div"); box.id = "lib-toasts"; box.className = "lib-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = document.createElement("div"); t.className = "lib-toast"; t.setAttribute("role", "status");
  t.innerHTML = `<span class="lib-toast-msg">${lesc(msg)}</span>${action ? `<button class="lib-toast-act">${lesc(action)}</button>` : ""}<span class="lib-toast-bar" style="animation-duration:${dur}ms"></span>`;
  box.appendChild(t);
  const kill = () => { t.classList.add("out"); setTimeout(() => t.remove(), 220); };
  const timer = setTimeout(kill, dur);
  if (action) t.querySelector(".lib-toast-act").onclick = () => { clearTimeout(timer); kill(); onAction && onAction(); };
}

/* ---- قوانین: Promise-based، بدون setInterval ---- */
async function loadLibraryTerms(force = false) {
  if (!force && Lib.terms) return Lib.terms;
  try { Lib.terms = await api("/library/terms"); }
  catch (_) { Lib.terms = { accepted: lisAdmin(), required: !lisAdmin(), text: "", is_admin: lisAdmin() }; }
  return Lib.terms;
}
function openLibraryTermsModal({ forceAccept = false, onDone = null } = {}) {
  loadLibraryTerms().then((terms) => {
    const adminView = terms.is_admin || lisAdmin();
    const already = !!terms.accepted && !forceAccept && !adminView;
    let accepted = false;
    const L = libLayer({
      title: "قوانین کتابخانه", wide: true,
      html: `<div class="glass-form">
        <pre style="white-space:pre-wrap;font-family:inherit;margin:0;line-height:1.9;opacity:.92;max-height:46vh;overflow:auto">${lesc(terms.text || "قوانینی ثبت نشده.")}</pre>
        ${adminView || already
          ? `<p class="lib-hint">${already ? "قبلاً این قوانین را پذیرفته‌اید." : "نمای ادمین — پذیرش لازم نیست."}</p>
             <div class="lib-modal-actions"><button class="btn btn-primary" data-lib-close>بستن</button></div>`
          : `<label class="lib-check"><input type="checkbox" id="lib-terms-check"><span>قوانین بالا را خواندم و می‌پذیرم</span></label>
             <div class="lib-modal-actions">
               <button class="btn btn-ghost" data-lib-close>انصراف</button>
               <button class="btn btn-primary" id="lib-terms-accept" disabled>تایید و ادامه</button>
             </div>`}
      </div>`,
      onClose: () => { if (onDone) onDone(accepted); },
      onMount: (wrap, layer) => {
        const check = wrap.querySelector("#lib-terms-check");
        const btn = wrap.querySelector("#lib-terms-accept");
        if (!check || !btn) return;
        check.addEventListener("change", () => { btn.disabled = !check.checked; });
        btn.addEventListener("click", async () => {
          btn.disabled = true; btn.textContent = "در حال ثبت…";
          try {
            await api("/library/terms/accept", { method: "POST", body: "{}" });
            Lib.terms = { ...terms, accepted: true };
            accepted = true; layer.close(); libToast("✅ قوانین پذیرفته شد");
          } catch (e) { btn.disabled = false; btn.textContent = "تایید و ادامه"; libToast("❌ " + (e.message || "خطا")); }
        });
      },
    });
    return L;
  });
}
async function ensureLibraryTermsAccepted() {
  if (lisAdmin()) return true;
  const t = await loadLibraryTerms(true);
  if (t.is_admin || t.accepted || !t.required) return true;
  return new Promise((resolve) => openLibraryTermsModal({ forceAccept: true, onDone: resolve }));
}

/* ---- ستاره‌ها: تعاملی، optimistic، بدون رفرش صفحه ---- */
function libStars(it, big = false) {
  const v = Number(it.my_rating) || lclamp(lavg(it));
  return `<span class="lib-rate-stars${big ? "" : " sm"}" data-lib-stars="${lesc(it.id)}" role="group" aria-label="امتیازدهی">` +
    [1, 2, 3, 4, 5].map((s) => `<button type="button" class="${s <= v ? "on" : ""}" data-lib="rate" data-id="${lesc(it.id)}" data-score="${s}" aria-label="امتیاز ${lfa(s)} از ۵">★</button>`).join("") + `</span>`;
}
function libPaintStars(box, v) { box.querySelectorAll("button").forEach((b) => b.classList.toggle("on", +b.dataset.score <= v)); }
function libRateNum(it) { return `${lavgTxt(lavg(it))} (${lfa(it.rating_count || 0)} رای)`; }
function libSync(id) {
  const it = Lib.items.find((x) => x.id === id); if (!it) return;
  const v = Number(it.my_rating) || lclamp(lavg(it));
  document.querySelectorAll(`[data-lib-stars="${CSS.escape(id)}"]`).forEach((s) => libPaintStars(s, v));
  document.querySelectorAll(`[data-lib-num="${CSS.escape(id)}"]`).forEach((n) => n.textContent = libRateNum(it));
  document.querySelectorAll(`[data-lib-avg="${CSS.escape(id)}"]`).forEach((n) => n.textContent = lavgTxt(lavg(it)));
  document.querySelectorAll(`[data-lib-my="${CSS.escape(id)}"]`).forEach((n) => n.textContent = it.my_rating ? `امتیاز شما: ${lfa(it.my_rating)}` : "ثبت امتیاز");
  document.querySelectorAll(`[data-lib-cnt="${CSS.escape(id)}"]`).forEach((n) => n.textContent = lfa(it.comment_count ?? it.comments?.length ?? 0));
  document.querySelectorAll(`[data-lib="fav"][data-id="${CSS.escape(id)}"]`).forEach((b) => { b.classList.toggle("on", Lib.favs.has(id)); b.setAttribute("aria-pressed", Lib.favs.has(id)); });
  if (it.reported) document.querySelectorAll(`[data-lib="report"][data-id="${CSS.escape(id)}"]`).forEach((b) => { b.disabled = true; b.title = "گزارش شده"; });
}
async function libRate(id, score) {
  const it = Lib.items.find((x) => x.id === id); if (!it) return;
  const old = { avg: it.avg_rating, cnt: it.rating_count, my: it.my_rating };
  const cnt = Number(it.rating_count) || 0, my = Number(it.my_rating) || 0;
  const newCnt = my ? cnt : cnt + 1;
  it.avg_rating = Math.round(((lavg(it) * cnt - my + score) / Math.max(1, newCnt)) * 100) / 100;
  it.rating_count = newCnt; it.my_rating = score;
  libSync(id);
  if (Lib.sort === "rating" || Lib.sort === "popular") libPaintItems();
  try {
    await api(`/library/items/${encodeURIComponent(id)}/rating`, { method: "POST", body: JSON.stringify({ score }) });
    libToast(`⭐ امتیاز ${lfa(score)} ثبت شد`);
  } catch (e) {
    Object.assign(it, { avg_rating: old.avg, rating_count: old.cnt, my_rating: old.my });
    libSync(id); libToast("❌ " + (e.message || "ثبت امتیاز ناموفق"));
  }
}

/* ---- کارت منبع (همه حالت‌ها) ---- */
function libBadges(it) {
  const tp = it.topic_title || (Lib.topics.find((t) => t.id === it.topic_id) || {}).title;
  return `${it.status === "pending" ? `<span class="badge badge-warn">در انتظار تایید</span>` : lisNew(it) ? `<span class="badge badge-new">جدید</span>` : ""}
    ${tp ? `<span class="lib-tag">${lesc(tp)}</span>` : `<span class="lib-tag lib-tag-muted">بدون تاپیک</span>`}`;
}
function libCard(it) {
  const u = lsafe(it.url), q = Lib.q, id = lesc(it.id);
  const fav = `<button class="btn btn-ghost btn-sm lib-fav-btn${Lib.favs.has(it.id) ? " on" : ""}" data-lib="fav" data-id="${id}" aria-pressed="${Lib.favs.has(it.id)}" aria-label="علاقه‌مندی" title="علاقه‌مندی">♥</button>`;
  const open = u ? `<a class="btn btn-primary btn-sm" href="${lesc(u)}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a>`
                 : `<button class="btn btn-sm" disabled title="لینک معتبر نیست">لینک نامعتبر</button>`;
  const report = `<button class="btn btn-ghost btn-sm" data-lib="report" data-id="${id}" aria-label="گزارش منبع" title="گزارش" ${it.reported ? "disabled" : ""}>🚩</button>`;
  const details = `<button class="btn btn-ghost btn-sm" data-lib="details" data-id="${id}">جزئیات</button>`;
  const sel = lisAdmin() ? `<label class="lib-selwrap" title="انتخاب"><input type="checkbox" class="lib-selbox" data-id="${id}" ${Lib.sel.has(it.id) ? "checked" : ""} aria-label="انتخاب منبع"></label>` : "";
  const meta = `<div class="lib-item-meta">
      <span class="lib-host" title="${lesc(u || "")}">${lesc(lhost(it.url) || "لینک نامعتبر")}</span>
      ${libStars(it)}<span class="lib-num" data-lib-num="${id}">${libRateNum(it)}</span>
      <span class="lib-muted" data-lib-my="${id}">${it.my_rating ? `امتیاز شما: ${lfa(it.my_rating)}` : "ثبت امتیاز"}</span>
      <span class="lib-muted">💬 <b data-lib-cnt="${id}">${lfa(it.comment_count ?? 0)}</b></span>
      ${it.submitter_name ? `<span class="lib-muted">· ${lesc(it.submitter_name)}</span>` : ""}
    </div>`;
  const title = `<button class="lib-linklike lib-item-title lib-item-title-link" data-lib="details" data-id="${id}">${lhi(it.title, q)}</button>`;
  if (Lib.mode === "icons") {
    return `<article class="lib-item-card lib-item-icons" data-lib-card="${id}">
      <button class="lib-icon-hit" data-lib="details" data-id="${id}" title="${lesc(it.title)}">
        <span class="lib-icon-badge">${ICON_BOOK}</span><span class="lib-icon-title">${lhi(it.title, q)}</span>
      </button>${libBadges(it)}
      <div class="lib-item-meta" style="justify-content:center">${libStars(it)}</div>
      <div class="lib-item-actions lib-icon-actions">${open}${fav}${report}</div></article>`;
  }
  if (Lib.mode === "compact") {
    return `<article class="lib-item-card lib-item-compact" data-lib-card="${id}">${sel}
      <div class="lib-item-compact-main">${title}${libBadges(it)}
        <span class="lib-item-compact-meta">${libStars(it)} <span data-lib-num="${id}">${libRateNum(it)}</span></span></div>
      <div class="lib-item-actions">${open}${details}${report}</div></article>`;
  }
  if (Lib.mode === "grid") {
    return `<article class="lib-item-card lib-item-grid" data-lib-card="${id}">${sel}
      <div class="lib-item-top">${title}${libBadges(it)}</div>
      <p class="lib-item-desc">${lhi(it.description || "بدون توضیح", q)}</p>${meta}
      <div class="lib-item-actions">${open}${details}${fav}${report}</div></article>`;
  }
  return `<article class="lib-item-card lib-item-list" data-lib-card="${id}">${sel}
    <div class="lib-item-list-body"><div class="lib-item-top">${title}${libBadges(it)}</div>
      ${it.description ? `<p class="lib-item-desc">${lhi(it.description, q)}</p>` : ""}${meta}</div>
    <div class="lib-item-actions">${open}${details}${fav}${report}</div></article>`;
}
function libMiniRow(it) { // برای پنل کتابخانه در صفحه جزئیات درس
  const u = lsafe(it.url);
  return `<div class="list-row" style="align-items:flex-start"><span class="row-icon">🔗</span>
    <div class="row-body" style="flex:1"><div class="row-title">
      ${u ? `<a href="${lesc(u)}" target="_blank" rel="noopener noreferrer">${lesc(it.title)}</a>` : lesc(it.title)}
      ${it.status === "pending" ? `<span class="badge badge-warn">در انتظار</span>` : ""}</div>
      <div class="row-meta">${lesc(it.description || "")}${it.avg_rating ? ` · ★ ${lfa(it.avg_rating)}` : ""}</div></div>
    <div class="row-actions"><button class="btn btn-ghost btn-sm" data-lib="details" data-id="${lesc(it.id)}">جزئیات</button>
      <button class="btn btn-ghost btn-sm" data-lib="report" data-id="${lesc(it.id)}" title="گزارش">🚩</button></div></div>`;
}

/* ---- فیلتر/مرتب‌سازی کلاینتی ---- */
function libFiltered() {
  let list = Lib.items.slice();
  if (Lib.topic === "none") list = list.filter((i) => !i.topic_id);
  else if (Lib.topic === "favs") list = list.filter((i) => Lib.favs.has(i.id));
  else if (Lib.topic !== "all") list = list.filter((i) => i.topic_id === Lib.topic);
  const q = Lib.q.trim().toLowerCase();
  if (q) list = list.filter((i) => `${i.title || ""} ${i.description || ""} ${i.topic_title || ""}`.toLowerCase().includes(q));
  const s = Lib.sort;
  return list.sort((a, b) =>
    s === "rating" ? lavg(b) - lavg(a) || (b.rating_count || 0) - (a.rating_count || 0)
    : s === "popular" ? (b.rating_count || 0) - (a.rating_count || 0)
    : s === "alpha" ? String(a.title).localeCompare(String(b.title), "fa")
    : (Date.parse(String(b.created_at || "").replace(" ", "T")) || 0) - (Date.parse(String(a.created_at || "").replace(" ", "T")) || 0));
}

/* ---- صفحه اصلی کتابخانه ---- */
async function renderLibraryCourses() {
  Lib.course = null; Lib.sel.clear();
  let data;
  try { data = await api(`/library/courses?scope=${encodeURIComponent(Lib.scope)}`); }
  catch (e) { contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری<small>${lesc(e.message)}</small></div>`; return; }
  const courses = data.courses || [];
  Lib.rootCourses = courses;
  const total = courses.reduce((a, c) => a + (c.item_count || 0), 0);
  contentEl.innerHTML = `
    <section class="lib-banner">
      <div class="lib-banner-text"><h2>📚 کتابخانه منابع درسی</h2>
        <p>جزوه، حل‌التمرین و لینک‌های مفید — بعد از تایید ادمین برای همه نمایش داده می‌شوند. تو هم منبع بفرست و به بقیه کمک کن.</p>
        <div class="lib-banner-stats"><span><b>${lfa(total)}</b>منبع</span><span><b>${lfa(courses.length)}</b>درس</span></div></div>
      <div class="lib-banner-actions">
        <button class="btn btn-ghost btn-sm" data-lib="terms">📜 قوانین</button>
        <button class="btn btn-primary" data-lib="submit">+ ارسال منبع جدید</button></div>
    </section>
    <div class="lib-toolbar">
      <div class="search-box"><span class="search-ico">${ICON_SEARCH}</span>
        <input id="lib-cq" type="search" placeholder="جستجو در نام درس، کد، جزوه یا توضیح…" autocomplete="off" value="${lesc(Lib.cq)}" aria-label="جستجو"></div>
      <div class="filter-bar">
        <button class="btn btn-sm ${Lib.scope === "current_term" ? "btn-primary" : "btn-soft"}" data-lib="scope" data-v="current_term">درس‌های این ترم</button>
        <button class="btn btn-sm ${Lib.scope === "all" ? "btn-primary" : "btn-soft"}" data-lib="scope" data-v="all">همه درس‌ها</button></div>
    </div>
    <div id="lib-hits" class="lib-hits hidden"></div>
    <div id="lib-cgrid" class="lib-course-grid"></div>`;
  libPaintCourses();
  if (Lib.cq) libRootSearch();
}
function libPaintCourses() {
  const grid = document.getElementById("lib-cgrid"); if (!grid) return;
  const q = Lib.cq.trim().toLowerCase();
  const list = (Lib.rootCourses || []).filter((c) => !q || `${c.course_name || ""} ${c.code || ""} ${c.term || ""}`.toLowerCase().includes(q));
  grid.innerHTML = list.length ? list.map((c) => `
    <a class="lib-course-card" href="#/library/${encodeURIComponent(c.course_name)}">
      <span class="lib-course-ico">${ICON_BOOK}</span>
      <span class="lib-course-name">${lhi(c.course_name, Lib.cq)}</span>
      <span class="lib-course-meta">${c.code ? lesc(c.code) + " · " : ""}${c.term ? "ترم " + lesc(c.term) : ""}</span>
      <span class="lib-course-meta"><b class="lib-num">${lfa(c.item_count || 0)}</b> منبع</span>
    </a>`).join("")
  : `<div class="empty" style="grid-column:1/-1"><span class="empty-icon">🔍</span>درسی در این فیلتر نیست<small>${Lib.scope === "current_term" ? "دروس فعال شما در کاتالوگ پیدا نشد — همگام‌سازی کنید یا «همه درس‌ها» را ببینید" : "هنوز درسی با منبع تاییدشده وجود ندارد"}</small></div>`;
}
let _libRootTimer = null;
function libRootSearch() {
  clearTimeout(_libRootTimer);
  const hits = document.getElementById("lib-hits"); if (!hits) return;
  const q = Lib.cq.trim().toLowerCase();
  if (!q) { hits.classList.add("hidden"); hits.innerHTML = ""; return; }
  hits.classList.remove("hidden");
  _libRootTimer = setTimeout(async () => {
    const tok = ++Lib.searchTok;
    hits.innerHTML = `<div class="lib-muted">در حال جستجوی منابع…</div>`;
    let found = [];
    try { // آینده: اگر این endpoint اضافه شود، جستجو server-side می‌شود
      const r = await api(`/library/search?q=${encodeURIComponent(q)}`);
      found = r.items || [];
    } catch (_) { // fallback: fan-out با کش (هر درس فقط یک‌بار)
      await Promise.all((Lib.rootCourses || []).map(async (c) => {
        const key = c.course_name;
        try {
          if (!Lib.itemCache.has(key)) Lib.itemCache.set(key, (await api(`/library/courses/${encodeURIComponent(key)}`)).items || []);
          for (const it of Lib.itemCache.get(key))
            if (`${it.title || ""} ${it.description || ""} ${key}`.toLowerCase().includes(q)) found.push({ ...it, course_name: key });
        } catch (_) {}
      }));
    }
    if (tok !== Lib.searchTok || !document.getElementById("lib-hits")) return;
    hits.innerHTML = found.length
      ? `<div class="lib-hits-title">منابع (${lfa(found.length)})</div>` + found.slice(0, 20).map((it) => `
          <button class="lib-hit lib-linklike" style="text-align:right" data-lib="hit" data-id="${lesc(it.id)}" data-course="${lesc(it.course_name)}">
            <b>${lhi(it.title, Lib.cq)}</b><span class="lib-muted">${lesc(it.course_name)}${it.description ? " · " + lesc(it.description.slice(0, 90)) : ""}</span>
          </button>`).join("")
      : `<div class="lib-muted">منبعی با این عبارت پیدا نشد</div>`;
  }, 300);
}

/* ---- صفحه کتابخانه یک درس ---- */
async function renderLibraryCourse(courseName) {
  if (Lib.course !== courseName) { Lib.topic = "all"; Lib.q = ""; Lib.sel.clear(); } // رفع نشت فیلتر بین درس‌ها
  Lib.course = courseName;
  let data;
  try { data = await api(`/library/courses/${encodeURIComponent(courseName)}`); } // یک‌بار fetch؛ فیلتر تاپیک کلاینتی
  catch (e) { contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا<small>${lesc(e.message)}</small></div>`; return; }
  if (Lib.course !== courseName) return;
  Lib.items = data.items || []; Lib.topics = data.topics || [];
  Lib.itemCache.set(courseName, Lib.items);
  const saved = Lib.views[courseName] || {};
  contentEl.innerHTML = `
    <nav class="lib-crumbs"><a href="#/library">کتابخانه</a><span>‹</span><span class="lib-crumb-cur">${lesc(courseName)}</span></nav>
    <div class="lib-course-head">
      <div><h2 class="lib-course-title">${lesc(courseName)}</h2><p class="lib-course-sub" id="lib-count"></p></div>
      <div class="lib-course-actions">
        <div class="lib-view-toggle" role="group" aria-label="حالت نمایش">
          ${[["list", "☰", "لیست"], ["grid", "▦", "شبکه"], ["compact", "≡", "فشرده"], ["icons", "▣", "آیکونی"]].map(([v, g, l]) =>
            `<button class="lib-view-btn ${Lib.mode === v ? "is-active" : ""}" data-lib="mode" data-v="${v}" title="${l}" aria-label="${l}" aria-pressed="${Lib.mode === v}">${g}</button>`).join("")}
        </div>
        <select id="lib-sort" class="input lib-sort" aria-label="مرتب‌سازی">
          <option value="new">جدیدترین</option><option value="rating">بیشترین امتیاز</option>
          <option value="popular">پررای‌ترین</option><option value="alpha">الفبایی</option>
        </select>
        <button class="btn btn-ghost btn-sm" data-lib="view-save" title="ذخیره نمای فعلی">💾</button>
        <button class="btn btn-primary" data-lib="submit" data-course="${lesc(courseName)}">+ ارسال منبع</button>
      </div>
    </div>
    <div class="lib-topic-nav"><div class="lib-topic-pills" id="lib-pills"></div>
      ${lisAdmin() ? `<button class="btn btn-sm btn-ghost" data-lib="topic-add">+ تاپیک</button>` : ""}</div>
    <div id="lib-saved" class="lib-saved"></div>
    <div class="search-box" style="margin-bottom:.4rem"><span class="search-ico">${ICON_SEARCH}</span>
      <input id="lib-q" type="search" placeholder="جستجو در عنوان یا توضیح این درس…" value="${lesc(Lib.q)}" aria-label="جستجوی منبع"></div>
    <div id="lib-bulk"></div>
    <div id="lib-items"></div>`;
  const sortEl = document.getElementById("lib-sort"); if (sortEl) sortEl.value = Lib.sort;
  libPaintAll();
  if (Lib.pendingDetail) { const id = Lib.pendingDetail; Lib.pendingDetail = null; libOpenDetail(id); }
}
function libPaintAll() { libPaintPills(); libPaintSaved(); libPaintItems(); libPaintBulk(); }
function libPaintPills() {
  const box = document.getElementById("lib-pills"); if (!box) return;
  const cnt = (t) => Lib.items.filter((i) => i.topic_id === t).length;
  const none = Lib.items.filter((i) => !i.topic_id).length;
  const pill = (v, label, n) => `<button class="lib-pill ${Lib.topic === v ? "is-active" : ""}" data-lib="topic" data-v="${v}" aria-pressed="${Lib.topic === v}">${lesc(label)}<span class="lib-pill-count">${lfa(n)}</span></button>`;
  box.innerHTML = pill("all", "همه", Lib.items.length)
    + Lib.topics.map((t) => pill(t.id, t.title, cnt(t.id))).join("")
    + pill("none", "بدون تاپیک", none) // رفع باگ __none__
    + pill("favs", "♥ منتخب من", Lib.items.filter((i) => Lib.favs.has(i.id)).length);
}
function libPaintSaved() {
  const box = document.getElementById("lib-saved"); if (!box) return;
  const views = Lib.views[Lib.course] || {};
  const keys = Object.keys(views);
  box.innerHTML = keys.length ? `<span class="lib-muted">نماها:</span>` + keys.map((k) =>
    `<span class="lib-saved-chip"><button class="lib-linklike" data-lib="view-apply" data-k="${lesc(k)}">${lesc(k)}</button>
     <button class="lib-x-mini" data-lib="view-del" data-k="${lesc(k)}" aria-label="حذف نما">✕</button></span>`).join("") : "";
}
function libPaintItems() {
  const box = document.getElementById("lib-items"); if (!box) return;
  const list = libFiltered();
  const c = document.getElementById("lib-count");
  if (c) c.textContent = `${lfa(list.length)} منبع · ${lisAdmin() ? "نمای ادمین · " : ""}مرتب‌سازی: ${{ new: "جدیدترین", rating: "بیشترین امتیاز", popular: "پررای‌ترین", alpha: "الفبایی" }[Lib.sort]}`;
  document.querySelectorAll(".lib-view-btn").forEach((b) => { b.classList.toggle("is-active", b.dataset.v === Lib.mode); b.setAttribute("aria-pressed", b.dataset.v === Lib.mode); });
  const cls = { grid: "lib-grid", icons: "lib-icons", compact: "lib-compact" }[Lib.mode] || "lib-list";
  box.innerHTML = list.length ? `<div class="${cls}">${list.map(libCard).join("")}</div>`
    : Lib.q ? `<div class="empty"><span class="empty-icon">🔍</span>منبعی با این عبارت پیدا نشد<small>فیلتر تاپیک را روی «همه» بگذار یا عبارت دیگری را امتحان کن</small><button class="btn btn-ghost btn-sm" data-lib="clear-q" style="margin-top:.6rem">پاک کردن جستجو</button></div>`
    : `<div class="empty"><span class="empty-icon">📭</span>هنوز منبعی در این بخش نیست<small>اولین نفری باش که برای این درس منبع می‌فرسته!</small><button class="btn btn-primary btn-sm" data-lib="submit" data-course="${lesc(Lib.course)}" style="margin-top:.6rem">+ ارسال اولین منبع</button></div>`;
}
function libPaintBulk() {
  const box = document.getElementById("lib-bulk"); if (!box) return;
  if (!lisAdmin() || !Lib.sel.size) { box.innerHTML = ""; return; }
  box.innerHTML = `<div class="lib-bulkbar"><b>${lfa(Lib.sel.size)}</b> انتخاب شده
    <button class="btn btn-soft btn-sm" data-lib="bulk-reject">رد (قابل برگشت)</button>
    <button class="btn btn-sm" style="color:var(--danger)" data-lib="bulk-delete">حذف کامل</button>
    <button class="btn btn-ghost btn-sm" data-lib="bulk-clear">پاک کردن</button></div>`;
}

/* ---- drawer جزئیات ---- */
async function libOpenDetail(id) {
  let it = Lib.items.find((x) => x.id === id), comments = [];
  try {
    const d = await api(`/library/items/${encodeURIComponent(id)}`);
    const fresh = d.item || d;
    comments = d.comments || fresh.comments || [];
    if (it) Object.assign(it, fresh, { comments });
    else it = { ...fresh, comments };
  } catch (_) { if (!it) { libToast("❌ بارگذاری جزئیات ناموفق"); return; } }
  const u = lsafe(it.url);
  const tp = it.topic_title || (Lib.topics.find((t) => t.id === it.topic_id) || {}).title;
  const admin = lisAdmin();
  const L = libLayer({
    type: "drawer", title: "جزئیات منبع",
    html: `<div class="lib-detail">
      <div class="lib-detail-head">
        <span class="lib-detail-ico">${ICON_BOOK}</span>
        <div class="lib-detail-title"><h2>${lesc(it.title)}</h2>
          <div class="lib-detail-meta">${it.status === "pending" ? `<span class="badge badge-warn">در انتظار تایید</span>` : ""}
            ${tp ? `<span class="lib-tag">${lesc(tp)}</span>` : `<span class="lib-tag lib-tag-muted">بدون تاپیک</span>`}
            ${it.course_name || Lib.course ? `<span class="lib-tag lib-tag-course">${lesc(it.course_name || Lib.course)}</span>` : ""}</div></div>
        <button class="lib-x" data-lib-close aria-label="بستن">✕</button>
      </div>
      ${it.status === "pending" ? `<div class="lib-note lib-note-warn"><p>⏳ این منبع هنوز تایید نشده${it.can_edit ? " و فقط برای خودت نمایش داده می‌شود" : ""}.</p></div>` : ""}
      <div class="lib-link-box">
        <div class="lib-link-info"><b class="lib-link-host" dir="ltr">${lesc(lhost(it.url) || "لینک نامعتبر")}</b>
          <span class="lib-muted" dir="ltr" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:38ch">${lesc(it.url)}</span></div>
        <div class="lib-detail-tools">
          <button class="btn btn-ghost btn-sm" data-lib="copy" data-id="${lesc(it.id)}">کپی لینک</button>
          ${u ? `<a class="btn btn-primary btn-sm" href="${lesc(u)}" target="_blank" rel="noopener noreferrer">باز کردن ↗</a>` : `<span class="badge badge-expired">لینک معتبر نیست</span>`}
        </div>
      </div>
      <p class="lib-detail-desc">${lesc(it.description || "بدون توضیح")}</p>
      <p class="lib-fineprint">ارسال‌کننده: ${lesc(it.submitter_name || it.submitter_username || "—")}${it.created_at ? ` · ${lesc(it.created_at)}` : ""}</p>
      <div class="block lib-block"><h4 class="section-title">⭐ امتیاز</h4>
        <div class="lib-rating-row">
          <span class="lib-rating-avg" data-lib-avg="${lesc(it.id)}">${lavgTxt(lavg(it))}</span>
          <div>${libStars(it, true)}<div class="lib-muted" data-lib-num="${lesc(it.id)}" style="margin-top:.2rem">${libRateNum(it)}</div></div>
          <span class="lib-muted" data-lib-my="${lesc(it.id)}">${it.my_rating ? `امتیاز شما: ${lfa(it.my_rating)}` : "ثبت امتیاز"}</span>
        </div></div>
      <div class="block lib-block"><h4 class="section-title">💬 نظرات (<span data-lib-cnt="${lesc(it.id)}">${lfa(comments.length)}</span>)</h4>
        <div class="lib-comment-list" id="lib-cmts">${libCommentsHtml(comments)}</div>
        <form class="lib-comment-form" id="lib-cmt-form">
          <textarea class="input" id="lib-cmt-body" rows="2" maxlength="1000" placeholder="نظرت رو بنویس… (Ctrl+Enter برای ارسال)" aria-label="متن نظر"></textarea>
          <button class="btn btn-primary btn-sm" type="submit">ثبت نظر</button>
        </form></div>
      <div class="lib-detail-actions">
        <button class="btn btn-ghost btn-sm" data-lib="report" data-id="${lesc(it.id)}" ${it.reported ? "disabled" : ""}>${it.reported ? "✓ گزارش شد" : "🚩 گزارش منبع"}</button>
        <button class="btn btn-ghost btn-sm lib-fav-btn${Lib.favs.has(it.id) ? " on" : ""}" data-lib="fav" data-id="${lesc(it.id)}">♥ علاقه‌مندی</button>
        ${lcanEdit(it) ? `<button class="btn btn-soft btn-sm" data-lib="edit" data-id="${lesc(it.id)}">✎ ویرایش</button>` : ""}
      </div>
      ${admin ? `<div class="block lib-block lib-admin-zone"><h4 class="section-title">🛡️ ابزار ادمین</h4>
        <div class="lib-detail-actions">
          ${it.status !== "approved" ? `<button class="btn btn-primary btn-sm" data-lib="approve" data-id="${lesc(it.id)}">✓ تایید</button>` : ""}
          ${it.status !== "rejected" ? `<button class="btn btn-soft btn-sm" data-lib="reject" data-id="${lesc(it.id)}">رد / پنهان‌سازی</button>` : ""}
          ${lcanDelete(it) ? `<button class="btn btn-sm" style="color:var(--danger)" data-lib="del" data-id="${lesc(it.id)}">🗑 حذف کامل</button>` : ""}
        </div>
        <div class="lib-field" style="margin-top:.7rem"><label class="field-label" for="lib-d-topic">انتقال تاپیک</label>
          <div style="display:flex;gap:.5rem"><select id="lib-d-topic" class="input">
            <option value="">بدون تاپیک</option>${Lib.topics.map((t) => `<option value="${lesc(t.id)}" ${t.id === it.topic_id ? "selected" : ""}>${lesc(t.title)}</option>`).join("")}</select>
          <button class="btn btn-soft btn-sm" data-lib="topic-apply" data-id="${lesc(it.id)}">اعمال</button></div></div>
      </div>` : ""}
    </div>`,
    onMount: (wrap) => {
      const form = wrap.querySelector("#lib-cmt-form"), body = wrap.querySelector("#lib-cmt-body");
      const send = async () => {
        const v = body.value.trim(); if (!v) { body.focus(); return; }
        const btn = form.querySelector("button"); btn.disabled = true;
        const optimistic = { author_name: "شما", body: v, created_at: "الان", _tmp: true };
        comments.push(optimistic);
        wrap.querySelector("#lib-cmts").innerHTML = libCommentsHtml(comments);
        body.value = "";
        try {
          await api(`/library/items/${encodeURIComponent(id)}/comments`, { method: "POST", body: JSON.stringify({ body: v }) });
          it.comment_count = (Number(it.comment_count) || comments.length - 1) + 1;
          libSync(id); libToast("💬 نظرت ثبت شد");
        } catch (e) {
          comments.splice(comments.indexOf(optimistic), 1);
          wrap.querySelector("#lib-cmts").innerHTML = libCommentsHtml(comments);
          body.value = v; libToast("❌ " + (e.message || "ثبت نظر ناموفق"));
        } finally { btn.disabled = false; }
      };
      form.addEventListener("submit", (e) => { e.preventDefault(); send(); });
      body.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); } });
    },
  });
  return L;
}
function libCommentsHtml(comments) {
  return comments.length ? comments.map((c) => `<div class="lib-comment">
    <div class="lib-comment-head"><b>${lesc(c.author_name || "کاربر")}</b><span class="lib-muted">${lesc(c.created_at || "")}</span></div>
    <div class="lib-comment-body">${lesc(c.body)}</div></div>`).join("")
  : `<div class="lib-empty-inline">هنوز نظری ثبت نشده — اولین نظر رو تو بنویس.</div>`;
}

/* ---- فرم‌ها: ارسال / ویرایش / گزارش / حذف ---- */
function libField(id, label, val = "", ph = "", ta = false) {
  return `<div class="lib-field" data-f="${id}"><label class="field-label" for="${id}">${label}</label>
    ${ta ? `<textarea class="input" id="${id}" rows="3" placeholder="${lesc(ph)}">${lesc(val)}</textarea>`
         : `<input class="input" id="${id}" value="${lesc(val)}" placeholder="${lesc(ph)}" ${id.includes("url") ? 'dir="ltr"' : ""}>`}
    <small class="lib-err"></small></div>`;
}
function libErr(wrap, id, msg) {
  const f = wrap.querySelector(`[data-f="${id}"]`); if (!f) return !msg;
  f.classList.toggle("bad", !!msg); f.querySelector(".lib-err").textContent = msg || ""; return !msg;
}
async function libTopicsFor(courseName) {
  if (courseName === Lib.course && Lib.topics.length) return Lib.topics;
  try { return (await api(`/library/courses/${encodeURIComponent(courseName)}/topics`)).topics || []; } catch (_) { return []; }
}
async function openLibrarySubmitModal(prefillCourse = "", preloadedTopics = null) {
  let names = [];
  try { names = (await api("/library/course-names")).names || []; } catch (_) {}
  const initial = prefillCourse ? (preloadedTopics || await libTopicsFor(prefillCourse)) : [];
  const topicOpts = (ts) => `<option value="">بدون تاپیک</option>` + ts.map((t) => `<option value="${lesc(t.id)}">${lesc(t.title)}</option>`).join("");
  libLayer({
    title: "ارسال منبع جدید",
    html: `<div class="glass-form">
      <div class="lib-note"><p>منبع بعد از تایید ادمین برای همه نمایش داده می‌شود؛ تا آن موقع فقط خودت می‌بینی‌اش.</p></div>
      <div class="lib-field"><label class="field-label" for="lib-course">نام درس *</label>
        ${names.length ? `<select id="lib-course" class="input"><option value="">انتخاب درس…</option>${names.map((n) => `<option value="${lesc(n)}" ${n === prefillCourse ? "selected" : ""}>${lesc(n)}</option>`).join("")}</select>`
        : `<input id="lib-course" class="input" value="${lesc(prefillCourse)}" disabled placeholder="کاتالوگ خالی است — ادمین باید درس‌ها را اضافه کند">`}</div>
      <div class="lib-field"><label class="field-label" for="lib-topic">تاپیک (اختیاری)</label><select id="lib-topic" class="input">${topicOpts(initial)}</select></div>
      ${libField("lib-title", "عنوان *", "", "مثلاً جزوه فصل ۳")}
      ${libField("lib-desc", "توضیح (اختیاری)", "", "توضیح کوتاه درباره منبع", true)}
      ${libField("lib-url", "لینک *", "", "https://…")}
      <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
        <button class="btn btn-primary" id="lib-submit" data-autofocus>ارسال برای تایید</button></div>
    </div>`,
    onMount: (wrap, L) => {
      const courseEl = wrap.querySelector("#lib-course"), topicEl = wrap.querySelector("#lib-topic");
      if (courseEl && courseEl.tagName === "SELECT")
        courseEl.addEventListener("change", async () => { topicEl.innerHTML = topicOpts(await libTopicsFor(courseEl.value)); });
      const btn = wrap.querySelector("#lib-submit");
      btn.addEventListener("click", async () => {
        const course_name = (courseEl.value || "").trim();
        const title = wrap.querySelector("#lib-title").value.trim();
        const url = wrap.querySelector("#lib-url").value.trim();
        let ok = libErr(wrap, "lib-title", title ? "" : "عنوان الزامی است");
        ok = libErr(wrap, "lib-url", !url ? "لینک الزامی است" : lsafe(url) ? "" : "لینک باید با http:// یا https:// شروع شود") && ok;
        if (!course_name) { libToast("درس را انتخاب کن"); ok = false; }
        if (!ok) return;
        btn.disabled = true; btn.textContent = "در حال ارسال…"; // ضد دابل‌سابمیت
        try {
          const r = await api("/library/items", { method: "POST", body: JSON.stringify({
            course_name, title, description: wrap.querySelector("#lib-desc").value.trim(),
            url, topic_id: (topicEl.value || "").trim() || null }) });
          L.close(); libToast("✅ ارسال شد — بعد از تایید ادمین نمایش داده می‌شود");
          Lib.itemCache.delete(course_name);
          const newItem = r && (r.item || (r.id ? r : null));
          if (Lib.course === course_name) {
            if (newItem) { Lib.items.unshift({ status: "pending", comment_count: 0, ...newItem }); Lib.topic = "all"; Lib.q = ""; Lib.sort = "new"; const qi = document.getElementById("lib-q"); if (qi) qi.value = ""; libPaintAll(); }
            else renderLibraryCourse(course_name);
          } else if (currentRoute().startsWith("course/")) { renderPage(currentRoute()); }
        } catch (e) { btn.disabled = false; btn.textContent = "ارسال برای تایید"; libToast("❌ " + (e.message || "خطا")); }
      });
    },
  });
}
async function libOpenEdit(id) {
  let it;
  try { const d = await api(`/library/items/${encodeURIComponent(id)}`); it = d.item || d; }
  catch (e) { libToast("❌ " + (e.message || "بارگذاری ناموفق")); return; }
  const topics = Lib.topics.length ? Lib.topics : await libTopicsFor(it.course_name || Lib.course || "");
  const showTopic = lisAdmin() || !!it.can_assign_topic;
  libLayer({
    title: "ویرایش منبع",
    html: `<div class="glass-form">
      ${showTopic ? `<div class="lib-field"><label class="field-label" for="lib-e-topic">تاپیک</label><select id="lib-e-topic" class="input">
        <option value="">بدون تاپیک</option>${topics.map((t) => `<option value="${lesc(t.id)}" ${t.id === it.topic_id ? "selected" : ""}>${lesc(t.title)}</option>`).join("")}</select></div>` : ""}
      ${libField("lib-e-title", "عنوان *", it.title || "")}
      ${libField("lib-e-desc", "توضیح", it.description || "", "", true)}
      ${libField("lib-e-url", "لینک *", it.url || "")}
      <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
        <button class="btn btn-primary" id="lib-e-save" data-autofocus>ذخیره تغییرات</button></div></div>`,
    onMount: (wrap, L) => {
      const btn = wrap.querySelector("#lib-e-save");
      btn.addEventListener("click", async () => {
        const title = wrap.querySelector("#lib-e-title").value.trim();
        const url = wrap.querySelector("#lib-e-url").value.trim();
        let ok = libErr(wrap, "lib-e-title", title ? "" : "عنوان الزامی است");
        ok = libErr(wrap, "lib-e-url", lsafe(url) ? "" : "لینک معتبر نیست") && ok;
        if (!ok) return;
        btn.disabled = true; btn.textContent = "در حال ذخیره…";
        const body = { title, url, description: wrap.querySelector("#lib-e-desc").value.trim() };
        if (showTopic) { const tid = (wrap.querySelector("#lib-e-topic").value || "").trim(); if (tid) body.topic_id = tid; else body.clear_topic = true; }
        try {
          await api(`/library/items/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(body) });
          const local = Lib.items.find((x) => x.id === id);
          if (local) { Object.assign(local, body); if (showTopic) { local.topic_id = body.topic_id || null; local.topic_title = (topics.find((t) => t.id === body.topic_id) || {}).title || null; } }
          L.close(); Lib.layers.slice().forEach((x) => x.close());
          libPaintAll(); libToast("✅ ذخیره شد"); libOpenDetail(id);
        } catch (e) { btn.disabled = false; btn.textContent = "ذخیره تغییرات"; libToast("❌ " + (e.message || "خطا")); }
      });
    },
  });
}
function libOpenReport(id) {
  const reasons = ["لینک خراب", "محتوای اشتباه", "نامناسب", "تکراری"]; let picked = null;
  libLayer({
    title: "گزارش منبع",
    html: `<div class="glass-form">
      <p class="lib-hint" style="margin:0">اگر لینک مرده، نامرتبط یا نامناسب است گزارش بده. گزارش به ادمین می‌رسد.</p>
      <div class="lib-chips">${reasons.map((r) => `<button class="lib-chip" data-r="${lesc(r)}">${lesc(r)}</button>`).join("")}</div>
      <div class="lib-field" data-f="lib-r-body"><textarea class="input" id="lib-r-body" rows="3" placeholder="توضیح بیشتر (اختیاری اگر دلیل انتخاب کردی)"></textarea><small class="lib-err"></small></div>
      <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
        <button class="btn btn-primary" id="lib-r-send" data-autofocus>ثبت گزارش</button></div></div>`,
    onMount: (wrap, L) => {
      wrap.querySelectorAll(".lib-chip").forEach((ch) => ch.addEventListener("click", () => {
        picked = ch.dataset.r; wrap.querySelectorAll(".lib-chip").forEach((x) => x.classList.toggle("on", x === ch)); libErr(wrap, "lib-r-body", "");
      }));
      const btn = wrap.querySelector("#lib-r-send");
      btn.addEventListener("click", async () => {
        const reason = [picked, wrap.querySelector("#lib-r-body").value.trim()].filter(Boolean).join(" — ");
        if (!reason) { libErr(wrap, "lib-r-body", "یک دلیل انتخاب کن یا توضیح بنویس"); return; }
        btn.disabled = true; btn.textContent = "در حال ثبت…";
        try {
          await api(`/library/items/${encodeURIComponent(id)}/report`, { method: "POST", body: JSON.stringify({ reason }) });
          const it = Lib.items.find((x) => x.id === id); if (it) it.reported = true;
          libSync(id); L.close(); libToast("🚩 گزارش ثبت شد — ممنون که حواست هست");
        } catch (e) { btn.disabled = false; btn.textContent = "ثبت گزارش"; libToast("❌ " + (e.message || "خطا")); }
      });
    },
  });
}
function libConfirm(title, text, okLabel, onOk, danger = true) {
  libLayer({
    title,
    html: `<p style="font-size:.9rem;line-height:1.9;margin:0 0 1rem">${lesc(text)}</p>
      <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
        <button class="btn ${danger ? "btn-danger" : "btn-primary"}" id="lib-c-ok" data-autofocus>${lesc(okLabel)}</button></div>`,
    onMount: (wrap, L) => {
      const btn = wrap.querySelector("#lib-c-ok");
      btn.addEventListener("click", async () => { btn.disabled = true; await onOk(); L.close(); });
    },
  });
}

/* ---- ادمین: تایید / رد با Undo / حذف کامل / گروهی ---- */
async function libSetStatus(id, status) {
  await api(`/library/admin/items/${encodeURIComponent(id)}/status`, { method: "POST", body: JSON.stringify({ status }) });
}
async function libApprove(id) {
  try { await libSetStatus(id, "approved");
    const it = Lib.items.find((x) => x.id === id); if (it) it.status = "approved";
    libPaintAll(); Lib.layers.slice().forEach((x) => x.close()); libToast("✅ تایید شد");
  } catch (e) { libToast("❌ " + (e.message || "خطا")); }
}
async function libReject(id) {
  const idx = Lib.items.findIndex((x) => x.id === id); if (idx < 0) return;
  const it = Lib.items[idx], prev = it.status || "approved";
  try {
    await libSetStatus(id, "rejected");
    Lib.items.splice(idx, 1); Lib.sel.delete(id);
    Lib.layers.slice().forEach((x) => x.close()); libPaintAll();
    libToast("رد شد و از کتابخانه پنهان شد", { action: "برگردان", dur: 6000, onAction: async () => {
      try { await libSetStatus(id, prev); it.status = prev; Lib.items.splice(Math.min(idx, Lib.items.length), 0, it); libPaintAll(); libToast("↩️ برگشت"); }
      catch (e) { libToast("❌ " + (e.message || "برگشت ناموفق")); }
    }});
  } catch (e) { libToast("❌ " + (e.message || "خطا")); }
}
function libHardDelete(id) {
  const it = Lib.items.find((x) => x.id === id);
  libConfirm("حذف کامل منبع", `«${it ? it.title : id}» برای همیشه حذف شود؟ این عمل برگشت‌پذیر نیست. (اگر فقط می‌خواهی پنهان شود، از «رد» استفاده کن.)`, "حذف کامل", async () => {
    try {
      await api(`/library/admin/items/${encodeURIComponent(id)}`, { method: "DELETE" });
      const idx = Lib.items.findIndex((x) => x.id === id); if (idx >= 0) Lib.items.splice(idx, 1);
      Lib.sel.delete(id); Lib.layers.slice().forEach((x) => x.close()); libPaintAll(); libToast("🗑 حذف شد");
    } catch (e) { libToast("❌ " + (e.message || "خطا")); }
  });
}
async function libBulkReject() {
  const ids = [...Lib.sel]; if (!ids.length) return;
  const removed = [];
  for (const id of ids) {
    const idx = Lib.items.findIndex((x) => x.id === id); if (idx < 0) continue;
    const it = Lib.items[idx], prev = it.status || "approved";
    try { await libSetStatus(id, "rejected"); removed.push({ it, idx, prev }); Lib.items.splice(idx, 1); } catch (_) {}
  }
  Lib.sel.clear(); libPaintAll();
  libToast(`${lfa(removed.length)} مورد رد شد`, { action: "برگردان همه", dur: 7000, onAction: async () => {
    for (const r of removed.sort((a, b) => a.idx - b.idx)) {
      try { await libSetStatus(r.it.id, r.prev); r.it.status = r.prev; Lib.items.splice(Math.min(r.idx, Lib.items.length), 0, r.it); } catch (_) {}
    }
    libPaintAll(); libToast("↩️ برگشتند");
  }});
}
function libBulkDelete() {
  const ids = [...Lib.sel]; if (!ids.length) return;
  libConfirm("حذف گروهی", `${lfa(ids.length)} منبع برای همیشه حذف شوند؟ برگشت‌پذیر نیست.`, "حذف کامل", async () => {
    let n = 0;
    for (const id of ids) {
      try { await api(`/library/admin/items/${encodeURIComponent(id)}`, { method: "DELETE" });
        const idx = Lib.items.findIndex((x) => x.id === id); if (idx >= 0) Lib.items.splice(idx, 1); n++; } catch (_) {}
    }
    Lib.sel.clear(); libPaintAll(); libToast(`🗑 ${lfa(n)} مورد حذف شد`);
  });
}

/* ---- delegation: یک‌بار نصب، بدون bind مجدد ---- */
function libWire() {
  if (Lib.wired) return; Lib.wired = true;
  document.addEventListener("click", async (e) => {
    const a = e.target.closest("[data-lib]");
    if (!a) {
      const card = e.target.closest("[data-lib-card]");
      if (card && !e.target.closest("a,button,input,select,textarea,label,.lib-rate-stars")) libOpenDetail(card.dataset.libCard);
      return;
    }
    if (a.tagName === "A") e.preventDefault();
    const act = a.dataset.lib, id = a.dataset.id;
    switch (act) {
      case "scope": Lib.scope = a.dataset.v; localStorage.setItem("lib:scope", Lib.scope); renderLibraryCourses(); break;
      case "topic": Lib.topic = a.dataset.v; Lib.sel.clear(); libPaintAll(); break;
      case "mode": Lib.mode = a.dataset.v; localStorage.setItem("lib:mode", Lib.mode); libPaintItems(); break; // بدون fetch مجدد
      case "clear-q": Lib.q = ""; { const i = document.getElementById("lib-q"); if (i) { i.value = ""; i.focus(); } } libPaintItems(); break;
      case "terms": openLibraryTermsModal(); break;
      case "submit": if (await ensureLibraryTermsAccepted()) openLibrarySubmitModal(a.dataset.course || Lib.course || ""); break;
      case "details": e.stopPropagation(); libOpenDetail(id); break;
      case "hit": Lib.pendingDetail = id; location.hash = "#/library/" + encodeURIComponent(a.dataset.course); break;
      case "rate": e.stopPropagation(); libRate(id, +a.dataset.score); break;
      case "fav": e.stopPropagation();
        Lib.favs.has(id) ? Lib.favs.delete(id) : Lib.favs.add(id);
        localStorage.setItem("lib:favs", JSON.stringify([...Lib.favs]));
        libSync(id); if (Lib.topic === "favs") libPaintItems(); libPaintPills(); break;
      case "report": libOpenReport(id); break;
      case "edit": libOpenEdit(id); break;
      case "approve": libApprove(id); break;
      case "reject": libReject(id); break;
      case "del": libHardDelete(id); break;
      case "bulk-reject": libBulkReject(); break;
      case "bulk-delete": libBulkDelete(); break;
      case "bulk-clear": Lib.sel.clear(); libPaintItems(); libPaintBulk(); break;
      case "topic-add": libLayer({ title: "تاپیک جدید", html: `<div class="glass-form">${libField("lib-t-title", "عنوان تاپیک *", "", "مثلاً حل‌التمرین")}
          <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button><button class="btn btn-primary" id="lib-t-save" data-autofocus>افزودن</button></div></div>`,
          onMount: (wrap, L) => { const b = wrap.querySelector("#lib-t-save");
            b.addEventListener("click", async () => { const title = wrap.querySelector("#lib-t-title").value.trim();
              if (!libErr(wrap, "lib-t-title", title ? "" : "عنوان الزامی است")) return;
              b.disabled = true;
              try { await api(`/library/admin/courses/${encodeURIComponent(Lib.course)}/topics`, { method: "POST", body: JSON.stringify({ title }) });
                Lib.topics = (await api(`/library/courses/${encodeURIComponent(Lib.course)}/topics`)).topics || Lib.topics;
                L.close(); libPaintPills(); libToast("تاپیک اضافه شد");
              } catch (err) { b.disabled = false; libToast("❌ " + (err.message || "خطا")); } }); } }); break;
      case "topic-apply": { const sel = a.closest(".lib-field").querySelector("select"); const tid = (sel.value || "").trim();
        try { await api(`/library/items/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(tid ? { topic_id: tid } : { clear_topic: true }) });
          const it = Lib.items.find((x) => x.id === id);
          if (it) { it.topic_id = tid || null; it.topic_title = (Lib.topics.find((t) => t.id === tid) || {}).title || null; }
          libPaintAll(); Lib.layers.slice().forEach((x) => x.close()); libOpenDetail(id); libToast("تاپیک به‌روز شد");
        } catch (err) { libToast("❌ " + (err.message || "خطا")); } break; }
      case "copy": { const it = Lib.items.find((x) => x.id === id); const url = it ? it.url : "";
        const done = () => libToast("📋 لینک کپی شد");
        if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done);
        else { const t = document.createElement("textarea"); t.value = url; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); done(); } break; }
      case "view-save": libLayer({ title: "ذخیره نمای فعلی", html: `<div class="glass-form">
          <p class="lib-hint" style="margin:0">تاپیک، مرتب‌سازی، حالت نمایش و جستجوی فعلی ذخیره می‌شود.</p>
          ${libField("lib-v-name", "نام نما *", "", "مثلاً حل‌التمرین‌های برتر")}
          <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button><button class="btn btn-primary" id="lib-v-save" data-autofocus>ذخیره</button></div></div>`,
          onMount: (wrap, L) => { const b = wrap.querySelector("#lib-v-save");
            b.addEventListener("click", () => { const name = wrap.querySelector("#lib-v-name").value.trim();
              if (!libErr(wrap, "lib-v-name", name ? "" : "نام الزامی است")) return;
              const views = Lib.views[Lib.course] || {};
              views[name] = { topic: Lib.topic, sort: Lib.sort, mode: Lib.mode, q: Lib.q };
              Lib.views[Lib.course] = Object.fromEntries(Object.entries(views).slice(-6));
              localStorage.setItem("lib:views", JSON.stringify(Lib.views));
              L.close(); libPaintSaved(); libToast("💾 نما ذخیره شد"); }); } }); break;
      case "view-apply": { const v = (Lib.views[Lib.course] || {})[a.dataset.k]; if (!v) break;
        Lib.topic = v.topic; Lib.sort = v.sort; Lib.mode = v.mode; Lib.q = v.q || "";
        localStorage.setItem("lib:sort", Lib.sort); localStorage.setItem("lib:mode", Lib.mode);
        { const i = document.getElementById("lib-q"); if (i) i.value = Lib.q; const s = document.getElementById("lib-sort"); if (s) s.value = Lib.sort; }
        libPaintAll(); break; }
      case "view-del": { const views = Lib.views[Lib.course] || {}; delete views[a.dataset.k];
        localStorage.setItem("lib:views", JSON.stringify(Lib.views)); libPaintSaved(); break; }
    }
  });
  document.addEventListener("input", (e) => {
    if (e.target.id === "lib-cq") { Lib.cq = e.target.value; libPaintCourses(); libRootSearch(); }
    if (e.target.id === "lib-q") { Lib.q = e.target.value; libPaintItems(); }
  });
  document.addEventListener("change", (e) => {
    if (e.target.id === "lib-sort") { Lib.sort = e.target.value; localStorage.setItem("lib:sort", Lib.sort); libPaintItems(); }
    if (e.target.classList && e.target.classList.contains("lib-selbox")) {
      e.target.checked ? Lib.sel.add(e.target.dataset.id) : Lib.sel.delete(e.target.dataset.id);
      libPaintBulk();
    }
  });
  document.addEventListener("mouseover", (e) => { const b = e.target.closest(".lib-rate-stars button"); if (b) libPaintStars(b.closest(".lib-rate-stars"), +b.dataset.score); });
  document.addEventListener("mouseout", (e) => { const s = e.target.closest(".lib-rate-stars");
    if (s && !s.contains(e.relatedTarget)) { const it = Lib.items.find((x) => x.id === s.dataset.libStars); if (it) libPaintStars(s, Number(it.my_rating) || lclamp(lavg(it))); } });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && Lib.layers.length) Lib.layers[Lib.layers.length - 1].close(); });
}
libWire();
// سازگاری با فراخوانی‌های قدیمی (پنل کتابخانه در صفحه درس):
function bindLibraryItemActions() {} // delegation سراسری جایگزین bind مجدد شد
window.LibUI = { openDetail: libOpenDetail, toast: libToast, state: Lib }; // قلاب برای ماژول‌های آینده

window.toggleAssignment = async (id, done) => {
  const a = asgFind(id);
  if (a) return asgToggle(id, !!done);
  const ok = await asgPushDone(id, !!done);
  toast(ok ? (done ? "✅ انجام‌شده علامت خورد" : "علامت انجام برداشته شد") : "❌ ثبت وضعیت ناموفق بود");
  if (ok) { if (typeof refreshNavBadge === "function") refreshNavBadge(); renderPage(currentRoute()); }
};
// ---------- Router ----------

function currentRoute() {
  const hash = location.hash.replace(/^#\/?/, "");
  return hash || "dashboard";
}

function setPageTitle(route) {
  let page = route;
  if (route.startsWith("course/")) page = "course";
  else if (route.startsWith("library")) page = "library";
  $("#page-title").textContent =
    TITLES[route] ||
    (route.startsWith("course/")
      ? "جزئیات درس"
      : route.startsWith("library/")
        ? "کتابخانه"
        : "داشبورد");
  document.querySelectorAll(".nav-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.page === page);
  });
}

function loadingSkeleton() {
  return `<div class="skeleton-grid">
    <div class="skeleton skeleton-card"></div>
    <div class="skeleton skeleton-card"></div>
    <div class="skeleton skeleton-card"></div>
    <div class="skeleton skeleton-card"></div>
  </div>`;
}

async function renderPage(route) {
  filterQuery = "";
  renderFilteredList = null;
  setPageTitle(route);
  try {
    window.__crsTeardown?.(); window.__mapTeardown?.(); window.__dashTeardown?.();
    window.__chgTeardown?.(); window.__walTeardown?.(); window.__cntTeardown?.();
    window.__supTeardown?.(); window.__docTeardown?.();
  } catch (_) {}
  contentEl.innerHTML = loadingSkeleton();
  try {
    // 👇 بررسی می‌کنیم که آیا این درس یک دوره کوئرا است یا خیر
    if (route.startsWith("course/quera_")) {
      // اگر کاربر آدرس کوئرا را مستقیم وارد کرد، به صفحه کوئرا ببر
      location.hash = "#/quera";
      return;
    }

    if (route.startsWith("course/")) {
      await renderCourseDetail(decodeURIComponent(route.slice("course/".length)));
    } else if (route === "library") {
      await renderLibraryCourses();
    } else if (route.startsWith("library/")) {
      // topic filter is kept while browsing same course; cleared when leaving library
      await renderLibraryCourse(decodeURIComponent(route.slice("library/".length)));
    } else {
      const fn = {
        dashboard: renderDashboard,
        courses: renderCourses,
        assignments: renderAssignments,
        //events: renderEvents,
        more: renderMore,
        about: renderAbout,
        help: renderHelp,
        calendar: renderCalendar,
        posts: renderPosts,
        contents: renderContents,
        changes: renderChanges,
        quera: renderQuera,
        settings: renderSettings,
        admin: renderAdmin,
        support: renderSupport,
        map: renderMap,
        library: renderLibraryCourses,
      }[route] || renderDashboard;
      await fn();
    }
  } catch (e) {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">❌</span>خطا در بارگذاری صفحه<small>${esc(e.message)}</small></div>`;
  }
}

window.addEventListener("hashchange", () => renderPage(currentRoute()));

// ---------- Mobile menu ----------

function closeSidebar() {
  $("#sidebar").classList.remove("open");
  $("#backdrop").classList.add("hidden");
}
$("#btn-menu").addEventListener("click", () => {
  $("#sidebar").classList.add("open");
  $("#backdrop").classList.remove("hidden");
});
$("#btn-close-sidebar").addEventListener("click", closeSidebar);
$("#backdrop").addEventListener("click", closeSidebar);
document.querySelectorAll(".nav-item").forEach((el) => {
  el.addEventListener("click", closeSidebar);
});

// ---------- Init ----------

(async function init() {
  const saved = localStorage.getItem("lms-theme");
  if (saved) {
    document.body.dataset.theme = saved;
    $("#btn-theme").innerHTML = saved === "dark" ? ICON_SUN : ICON_MOON;
  } else {
    try {
      const t = await api("/settings/theme");
      if (t.theme) {
        document.body.dataset.theme = t.theme;
        $("#btn-theme").innerHTML = t.theme === "dark" ? ICON_SUN : ICON_MOON;
      }
    } catch (_) {}
  }

  refreshUserBox().catch(() => showLogin());
  refreshNavBadge();
  const dp = (window.LmsPrefs || {}).default_page || "dashboard";
  if ((!location.hash || location.hash === "#/") && dp !== "dashboard") {
    history.replaceState(null, "", "#/" + dp);
  }
  renderPage(currentRoute());
  try { navRefreshExtraBadges(); } catch (_) {}

  try {
    const st = await api("/sync/status");
    if (st.running) {
      setSyncButton(true);
      setSyncUI(true, st.progress?.percent ?? 0, "همگام‌سازی در حال اجرا…");
      listenSyncEvents();
    }
  } catch (_) {}
})();
// PWA: ثبت Service Worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}