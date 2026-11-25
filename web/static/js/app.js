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

function setTheme(theme) {
  document.body.dataset.theme = theme;
  const btn = $("#btn-theme");
  if (btn) btn.innerHTML = theme === "dark" ? ICON_SUN : ICON_MOON;
  document.querySelector('meta[name="theme-color"]').content =
    theme === "dark" ? "#0e1118" : "#4f46e5";
  localStorage.setItem("lms-theme", theme);
  api("/settings/theme", { method: "POST", body: JSON.stringify({ theme }) }).catch(() => {});
}

$("#btn-theme").addEventListener("click", () => {
  setTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
});

// ---------- Login Modal ----------

const loginModal = $("#login-modal");

function showLogin() { loginModal.classList.remove("hidden"); }
function hideLogin() {
  loginModal.classList.add("hidden");
  $("#login-error").classList.add("hidden");
}

// password eye toggles
document.addEventListener("click", (e) => {
  const eye = e.target.closest("[data-toggle]");
  if (eye) {
    const input = document.getElementById(eye.dataset.toggle);
    if (!input) return;
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    eye.textContent = show ? "🙈" : "👁";
  }
  const closer = e.target.closest("[data-close]");
  if (closer) {
    const modal = document.getElementById(closer.dataset.close);
    if (modal) modal.classList.add("hidden");
  }
});

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#btn-login-submit");
  btn.disabled = true;
  btn.textContent = "در حال ورود…";
  try {
    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        lms_username: $("#lms-username").value,
        lms_password: $("#lms-password").value,
        quera_username: $("#quera-username").value,
        quera_password: $("#quera-password").value,
      }),
    });
    if (result.ok) {
      hideLogin();
      toast(`✅ خوش آمدید${result.full_name ? "، " + result.full_name : ""}`);
      await refreshUserBox();
      await renderPage(currentRoute());
      maybeAutoSync();
    } else {
      const err = $("#login-error");
      err.textContent = "❌ " + (result.error || "ورود ناموفق بود");
      err.classList.remove("hidden");
    }
  } catch (ex) {
    const err = $("#login-error");
    err.textContent = "❌ خطای ارتباط با سرور";
    err.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "ورود";
  }
});


// Admin local login toggle
$("#btn-toggle-admin-login")?.addEventListener("click", () => {
  $("#login-form").classList.add("hidden");
  $("#admin-login-form").classList.remove("hidden");
  $("#login-title").textContent = "ورود ادمین";
});
$("#btn-toggle-lms-login")?.addEventListener("click", () => {
  $("#admin-login-form").classList.add("hidden");
  $("#login-form").classList.remove("hidden");
  $("#login-title").textContent = "ورود به حساب کاربری";
});
$("#admin-login-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#btn-admin-login-submit");
  btn.disabled = true;
  btn.textContent = "در حال ورود…";
  try {
    const result = await api("/auth/local-login", {
      method: "POST",
      body: JSON.stringify({
        username: $("#admin-username").value.trim(),
        password: $("#admin-password").value,
      }),
    });
    if (result.ok) {
      hideLogin();
      toast(`✅ خوش آمدید${result.full_name ? "، " + result.full_name : ""}`);
      await refreshUserBox();
      location.hash = "#/admin";
      renderPage("admin");
    } else {
      const err = $("#admin-login-error");
      err.textContent = "❌ " + (result.error || "ورود ناموفق");
      err.classList.remove("hidden");
    }
  } catch (ex) {
    const err = $("#admin-login-error");
    err.textContent = "❌ خطای ارتباط با سرور";
    err.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "ورود ادمین";
  }
});

$("#btn-logout").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  toast("از حساب خارج شدید");
  refreshUserBox();
});

let authRole = "user";

async function refreshUserBox() {
  try {
    const st = await api("/auth/status");
    authRole = st.role || "user";
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
  try {
    const st = await api("/sync/status");
    if (st.running) return;
    const ls = st.last_sync;
    let need = !ls || ls.status === "never";
    if (!need && ls.at) {
      const ts = Date.parse(String(ls.at).replace(" ", "T") + "Z");
      if (!Number.isNaN(ts)) {
        need = Date.now() - ts > 6 * 3600 * 1000;
      }
    }
    if (!need) return;
    _autoSyncTried = true;
    toast("🔄 همگام‌سازی خودکار شروع شد…");
    const r = await api("/sync/start", { method: "POST" });
    if (!r.ok && r.error) {
      toast("⏳ " + r.error);
      return;
    }
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
      const st = await api("/sync/status");
      if (!st.running) {
        setSyncButton(false);
        setSyncUI(false);
      }
    }, 2000);
  };
}

async function refreshNavBadge() {
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
async function renderDashboard() {
  const d = await api("/dashboard");
  const s = d.stats;
  const alerts = d.alerts || [];
  const alertsHtml = alerts.length
    ? `<div class="card" style="margin-bottom:1rem;border:1px solid var(--danger-soft, #fca5a5)">
        <h3 style="margin:0 0 .5rem">⏰ هشدار مهلت‌ها</h3>
        <div style="display:flex;flex-direction:column;gap:.4rem">
          ${alerts.map(a => `
            <div style="display:flex;justify-content:space-between;gap:.75rem;align-items:flex-start;padding:.45rem .2rem;border-bottom:1px solid var(--glass-border)">
              <div>
                <div style="font-weight:600">${esc(a.title)}</div>
                <div style="font-size:.8rem;opacity:.8">${esc(a.message)}${a.deadline_jalali ? " · " + esc(a.deadline_jalali) : ""}</div>
              </div>
              <span class="badge ${a.level === "danger" ? "badge-expired" : "badge-warn"}">${a.kind === "overdue" ? "گذشته" : "نزدیک"}</span>
            </div>
          `).join("")}
        </div>
      </div>`
    : "";



  const ls = d.last_sync;
  const lastSyncHtml = ls
    ? `<div class="card" style="margin-bottom:1rem">
        <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap">
          <div>
            <div style="font-weight:700">${esc(ls.title)}</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.25rem">${esc(ls.detail || "")}</div>
            ${ls.at ? `<div style="font-size:.75rem;opacity:.65;margin-top:.35rem;direction:ltr;text-align:right">${esc(ls.at)}</div>` : ""}
          </div>
          <span class="badge ${ls.status === "success" ? "badge-new" : ls.status === "error" ? "badge-expired" : ""}">${
            ls.status === "success" ? "موفق" : ls.status === "error" ? "ناموفق" : "—"
          }</span>
        </div>
        ${ls.status === "error" ? `<button class="btn btn-soft btn-sm" id="btn-retry-sync" style="margin-top:.75rem">تلاش دوباره همگام‌سازی</button>` : ""}
      </div>`
    : "";

const statCard = (value, label, icon, color, bg) => `
    <div class="card stat-card" style="--stat-color:${color};--stat-bg:${bg}">
      <span class="stat-icon">${icon}</span>
      <div class="stat-value">${value}</div>
      <div class="stat-label">${label}</div>
    </div>`;

  // 👇 ساخت لیست جلسات امروز
  const todayEvents = d.today_events && d.today_events.length
    ? d.today_events.map((e) => {
        const m = eventMeta(e.event_type);
        // استفاده از پروکسی برای لینک کلاس
        const link = e.url ? `/api/jaam-proxy?url=${encodeURIComponent(e.url)}` : null;

        return `
          <div class="list-row">
            <span class="row-icon">${m.icon}</span>
            <div class="row-body">
              <div class="row-title">
                ${link ? `<a href="${link}" target="_blank" rel="noopener" style="color:var(--primary); font-weight:700;">${esc(e.title)}</a>` : esc(e.title)}
                <span class="badge ${m.cls}">${m.label}</span>
              </div>
              <div class="row-meta">
                <span>⏰ ${esc(e.start_at)}</span>
              </div>
            </div>
            ${link ? `<div class="row-actions"><a class="btn-primary-glass btn-sm" href="${link}" target="_blank" rel="noopener">ورود به جلسه ↗</a></div>` : ""}
          </div>`;
      }).join("")
    : emptyState("امروز جلسه یا رویدادی ندارید", "فردا دوباره سر بزنید");

  const assignments = d.upcoming_assignments.length
    ? d.upcoming_assignments.map((a) => `
        <div class="list-row">
          <span class="row-icon">📝</span>
          <div class="row-body">
            <div class="row-title">${esc(a.title)} ${a.is_expired ? '<span class="badge badge-expired">گذشته</span>' : ""}</div>
            <div class="row-meta">مهلت: ${esc(a.deadline_jalali || a.deadline || "-")}</div>
          </div>
        </div>`).join("")
    : emptyState("تکلیفی نیست");

  const posts = d.recent_posts.length
    ? d.recent_posts.map((p) => `
        <div class="list-row">
          <span class="row-icon">💬</span>
          <div class="row-body">
            <div class="row-title">${esc(p.author)}</div>
            <div class="row-meta">${esc(p.text.slice(0, 130))}${p.text.length > 130 ? "…" : ""}</div>
          </div>
        </div>`).join("")
    : emptyState("پیامی نیست");

  contentEl.innerHTML = `
    ${pageHead("داشبورد", "نمای کلی وضعیت دروس و مهلت‌ها")}
    ${alertsHtml}
    ${lastSyncHtml}
    <div class="stats-grid">
      ${statCard(s.active_courses, "درس فعال", "📚", "var(--primary)", "var(--primary-soft)")}
      ${statCard(s.courses, "کل درس‌ها", "🎓", "var(--info)", "var(--info-soft)")}
      ${statCard(s.pending_assignments, "تکلیف باز", "✎", "var(--danger)", "var(--danger-soft)")}
      ${statCard(s.contents, "محتواها", "▧", "var(--primary)", "var(--primary-soft)")}
    </div>
    <div class="grid-2">
      <!-- 👇 تغییر عنوان و محتوا به جلسات امروز -->
      <div class="card">
        <div class="card-head">
          <h3 class="section-title">🎥 جلسات آنلاین امروز</h3>
          <a class="card-link" href="#/calendar">تقویم</a>
        </div>
        <div class="item-list">${todayEvents}</div>
      </div>
      
      <div class="card">
        <div class="card-head"><h3 class="section-title">📝 تکالیف نزدیک</h3><a class="card-link" href="#/assignments">همه</a></div>
        <div class="item-list">${assignments}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">💬 آخرین پیام‌ها</h3><a class="card-link" href="#/posts">همه</a></div>
      <div class="item-list">${posts}</div>
    </div>`;
}

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

async function renderPosts() {
  const items = await api("/posts");
  if (!items.length) {
    contentEl.innerHTML = emptyState("پیامی یافت نشد", "بعد از همگام‌سازی پیام‌های وال اینجا می‌آیند");
    return;
  }
  const names = await courseNameMap();
  let filter = "unread"; // unread | all

  const unreadCount = items.filter((p) => p.is_new).length;

  contentEl.innerHTML = `
    ${pageHead("پیام‌های وال", `${items.length} پیام · ${unreadCount} خوانده‌نشده`)}
    <div class="filter-bar" style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem;align-items:center">
      <button type="button" class="filter-btn active" data-pf="unread">خوانده‌نشده (${unreadCount})</button>
      <button type="button" class="filter-btn" data-pf="all">همه (${items.length})</button>
      <button class="btn btn-soft btn-sm" onclick="markPostsRead()" ${unreadCount ? "" : "disabled"}>✓ همه را خواندم</button>
      <div class="search-box" style="flex:1;min-width:180px;margin-inline-start:auto">
        <span class="search-ico">🔍</span>
        <input id="posts-filter-input" type="search" placeholder="جستجو در متن یا نویسنده…" />
      </div>
    </div>
    <div class="item-list" id="list-container"></div>`;

  const renderList = () => {
    const el = document.getElementById("list-container");
    if (!el) return;
    let list = items.filter((p) => (filter === "unread" ? p.is_new : true));
    const q = (document.getElementById("posts-filter-input")?.value || "").trim().toLowerCase();
    if (q) {
      list = list.filter((p) =>
        `${p.author || ""} ${p.text || ""} ${names[p.course_id] || ""}`.toLowerCase().includes(q)
      );
    }
    el.innerHTML = list.length
      ? list
          .map(
            (p) => `
        <div class="list-row">
          <span class="row-icon">💬</span>
          <div class="row-body">
            <div class="row-title">${esc(p.author)} ${p.is_new ? '<span class="badge badge-new">جدید</span>' : ""}</div>
            <div class="row-meta">${esc(p.text)}</div>
            <div class="row-meta muted" style="margin-top:.35rem">
              <span>${esc(p.posted_at_jalali || p.posted_at || "")}</span>
              <span class="sep">·</span><span>${esc(names[p.course_id] || p.course_id)}</span>
            </div>
          </div>
        </div>`
          )
          .join("")
      : emptyState("موردی با این فیلتر نیست", "فیلتر «همه» را امتحان کنید");
  };

  contentEl.querySelectorAll("[data-pf]").forEach((btn) => {
    btn.addEventListener("click", () => {
      filter = btn.dataset.pf;
      contentEl.querySelectorAll("[data-pf]").forEach((b) => b.classList.toggle("active", b === btn));
      renderList();
    });
  });
  document.getElementById("posts-filter-input")?.addEventListener("input", renderList);
  renderList();
}

window.markPostsRead = async () => {
  await api("/posts/read", { method: "POST" });
  toast("✅ همه پیام‌ها خوانده شدند");
  refreshNavBadge();
  renderPage("posts");
};

async function renderContents() {
  const items = await api("/contents");
  if (!items.length) { contentEl.innerHTML = emptyState("محتوایی یافت نشد"); return; }

  // تابع محاسبه زمان (با پشتیبانی از تاریخ دقیق)
  const formatTime = (isoString) => {
    if (!isoString) return "نامشخص";
    const date = new Date(isoString);
    const diff = Math.floor((new Date() - date) / 1000);
    if (diff < 60) return "همین الان";
    if (diff < 3600) return `${Math.floor(diff / 60)} دقیقه پیش`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ساعت پیش`;
    return `${Math.floor(diff / 86400)} روز پیش`;
  };

  const renderList = (list) => {
    const el = document.getElementById("list-container");
    if (!el) return;

    el.innerHTML = list.length
      ? list.map((c) => `
        <div class="list-row" style="padding: 1rem;">
          <span class="row-icon" style="background: var(--primary-soft); color: var(--primary); font-size:1.2rem;">📄</span>
          <div class="row-body">
            <div class="row-title" style="font-size: 1.05rem; margin-bottom: 0.3rem;">
              <a href="/api/jaam-proxy?url=${encodeURIComponent(c.url)}" target="_blank" rel="noopener" style="color:var(--text); font-weight: 800;">${esc(c.title)}</a>
              <span class="badge badge-domain" style="margin-inline-start:0.5rem;">${esc(c.content_type)}</span>
            </div>
            
            <div class="row-meta" style="display:flex; flex-wrap:wrap; gap:0.8rem; align-items:center;">
              <a href="#/course/${encodeURIComponent(c.course_id)}" class="chip" style="text-decoration:none; cursor:pointer; background:var(--glass-bg-soft); border:1px solid var(--glass-border);">
                📘 ${esc(c.course_name)}
              </a>
              <span class="badge" style="color:var(--text-muted); background:transparent; border:1px solid var(--glass-border);">
                👨‍🏫 ${esc(c.teacher)}
              </span>
              <span class="badge" style="color:var(--text-muted); background:transparent; border:1px solid var(--glass-border);">
                ⏱ ${formatTime(c.last_seen_at)}
              </span>
            </div>
          </div>
          
          <div class="row-actions">
            <!-- 👇 استفاده از دکمه شیشه‌ای جدید -->
            <a class="btn-glass-action" href="/api/jaam-proxy?url=${encodeURIComponent(c.url)}" target="_blank" rel="noopener">باز کردن ↗</a>
          </div>
        </div>`).join("")
      : `<div class="empty"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  contentEl.innerHTML = `
    ${pageHead("محتواها", "فایل‌ها و منابع درس‌ها")}
    ${searchBox("جستجوی عنوان محتوا…")}
    <div class="item-list" id="list-container"></div>`;

  const records = items.map((c) => ({
    c,
    get searchText() { return `${c.title} ${c.filename} ${c.course_name} ${c.teacher}`.toLowerCase(); },
  }));

  attachFilter(records, {
    searchText: (it) => it.searchText,
    render: (filtered) => renderList(filtered.map((it) => it.c)),
  });
}

async function renderChanges() {
  const items = await api("/changes");
  if (!items.length) { contentEl.innerHTML = emptyState("تغییری ثبت نشده"); return; }

  let filters = { type: "all", time: "all" };

  const ENTITY_META = {
    content: { icon: "📁", label: "فایل/محتوا", color: "var(--primary)", bg: "var(--primary-soft)" },
    assignment: { icon: "📝", label: "تکلیف", color: "var(--warning)", bg: "var(--warning-soft)" },
    event: { icon: "📅", label: "رویداد", color: "var(--info)", bg: "var(--info-soft)" },
    post: { icon: "💬", label: "پیام وال", color: "var(--accent)", bg: "var(--accent-soft)" },
  };

  const CHANGE_META = {
    new: { label: "ایجاد / افزودن", color: "var(--accent)", bg: "var(--accent-soft)", icon: "➕" },
    updated: { label: "به‌روزرسانی", color: "var(--info)", bg: "var(--info-soft)", icon: "🔄" },
    removed: { label: "حذف / انقضا", color: "var(--danger)", bg: "var(--danger-soft)", icon: "➖" },
  };

  const timeAgo = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    const diff = Math.floor((new Date() - date) / 1000);
    if (diff < 60) return "همین الان";
    if (diff < 3600) return `${Math.floor(diff / 60)} دقیقه پیش`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ساعت پیش`;
    return `${Math.floor(diff / 86400)} روز پیش`;
  };

  contentEl.innerHTML = `
    ${pageHead("آخرین تغییرات", "تایم‌لاین فعالیت‌ها و به‌روزرسانی‌های سامانه")}
    
    <div class="filter-bar" style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1.5rem; align-items:center;">
      <div class="custom-dropdown" id="dd-type">
        <button class="filter-btn" onclick="toggleDropdown('dd-type')">همه انواع</button>
        <div class="dropdown-menu">
          <a href="#" class="dropdown-item active" data-val="all">همه انواع</a>
          <a href="#" class="dropdown-item" data-val="content">فایل‌ها</a>
          <a href="#" class="dropdown-item" data-val="assignment">تکالیف</a>
          <a href="#" class="dropdown-item" data-val="event">رویدادها</a>
          <a href="#" class="dropdown-item" data-val="post">پیام‌ها</a>
        </div>
      </div>
      <div class="custom-dropdown" id="dd-time">
        <button class="filter-btn" onclick="toggleDropdown('dd-time')">همه زمان‌ها</button>
        <div class="dropdown-menu">
          <a href="#" class="dropdown-item active" data-val="all">همه زمان‌ها</a>
          <a href="#" class="dropdown-item" data-val="week">هفته اخیر</a>
        </div>
      </div>
    </div>

    <div class="timeline-list" id="changes-list"></div>
  `;

  const renderList = () => {
    const listEl = document.getElementById("changes-list");
    if (!listEl) return;

    let filtered = items.filter(ch => {
      if (filters.type !== "all" && ch.entity_type !== filters.type) return false;
      if (filters.time === "week") {
        const chDate = new Date(ch.detected_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        if (chDate < weekAgo) return false;
      }
      return true;
    });

    listEl.innerHTML = filtered.length ? filtered.map((ch) => {
      const entity = ENTITY_META[ch.entity_type] || { icon: "🔔", label: ch.entity_type, color: "var(--text-muted)", bg: "var(--surface-2)" };
      const change = CHANGE_META[ch.type] || { label: ch.type, color: "var(--text)", bg: "var(--surface-2)", icon: "•" };

      const courseLink = ch.course_id
        ? `<a href="#/course/${encodeURIComponent(ch.course_id)}" style="color:var(--primary); text-decoration:none; font-weight:600;">${esc(ch.course_name)}</a>`
        : "سیستم";

      return `
        <div class="timeline-item">
          <div class="timeline-icon" style="color: ${entity.color}; background: ${entity.bg};">
            ${entity.icon}
          </div>
          <div class="timeline-line"></div>
          <div class="timeline-content card">
            <div class="timeline-header">
              <span class="timeline-title">${esc(ch.title)}</span>
              <span class="badge" style="color: ${change.color}; background: ${change.bg};">
                ${change.icon} ${change.label}
              </span>
            </div>
            
            <div class="timeline-meta" style="margin-top: 0.6rem; display:flex; flex-wrap:wrap; gap:0.5rem; align-items:center;">
              <span class="badge badge-domain">${courseLink}</span>
              <span class="sep">·</span>
              <span>👨‍🏫 ${esc(ch.teacher_name)}</span>
              <span class="sep">·</span>
              <span>${entity.label}</span>
              <span class="sep">·</span>
              <span>${timeAgo(ch.detected_at)}</span>
            </div>
          </div>
        </div>
      `;
    }).join("") : `<div class="empty" style="margin-top:2rem"><span class="empty-icon">🔍</span>تغییری با این فیلترها یافت نشد</div>`;
  };

  // مدیریت منوها...
  window.toggleDropdown = (id) => {
    document.querySelectorAll('.custom-dropdown').forEach(el => { if (el.id !== id) el.classList.remove('open'); });
    document.getElementById(id).classList.toggle('open');
  };

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.custom-dropdown')) {
      document.querySelectorAll('.custom-dropdown').forEach(el => el.classList.remove('open'));
    }
  });

  document.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const parent = e.target.closest('.custom-dropdown');
      const type = parent.id === 'dd-type' ? 'type' : 'time';
      filters[type] = e.target.dataset.val;
      parent.querySelector('button').textContent = e.target.textContent + " ▼";
      parent.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
      e.target.classList.add('active');
      parent.classList.remove('open');
      renderList();
    });
  });

  renderList();
}



async function renderSupport() {
  let list;
  try {
    list = await api("/support/tickets");
  } catch (e) {
    contentEl.innerHTML = emptyState("برای پشتیبانی وارد شوید", "ابتدا لاگین کنید");
    showLogin();
    return;
  }
  const tickets = list.tickets || [];

  contentEl.innerHTML = `
    ${pageHead("پشتیبانی", "گزارش باگ و پیگیری پاسخ تیم")}
    <div class="card" style="margin-bottom:1rem">
      <h4 style="margin:0 0 .75rem">تیکت جدید</h4>
      <form id="support-form" style="display:flex;flex-direction:column;gap:.6rem">
        <input id="sup-subject" class="input" placeholder="موضوع (مثلاً خطا در sync)" required maxlength="200" />
        <textarea id="sup-body" class="input" rows="4" placeholder="توضیح مشکل…" required maxlength="5000"></textarea>
        <button type="submit" class="btn btn-primary" style="align-self:flex-start">ارسال گزارش</button>
      </form>
    </div>
    <div class="card">
      <h4 style="margin:0 0 .75rem">تیکت‌های من</h4>
      <div id="sup-list">
        ${tickets.length ? tickets.map(t => `
          <button class="row" data-ticket="${esc(t.id)}" style="width:100%;text-align:right;cursor:pointer;border:none;background:transparent;padding:.75rem 0;border-bottom:1px solid var(--glass-border)">
            <div style="font-weight:600">${esc(t.subject)} <span class="badge">${esc(t.status)}</span></div>
            <div style="font-size:.8rem;opacity:.7">${esc(t.updated_at || "")} · ${t.message_count || 0} پیام</div>
          </button>
        `).join("") : '<div style="opacity:.7;padding:.5rem 0">هنوز تیکتی ثبت نکرده‌اید</div>'}
      </div>
      <div id="sup-thread" class="hidden" style="margin-top:1rem"></div>
    </div>
  `;

  $("#support-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const subject = $("#sup-subject").value.trim();
    const body = $("#sup-body").value.trim();
    try {
      await api("/support/tickets", { method: "POST", body: JSON.stringify({ subject, body }) });
      toast("✅ گزارش ثبت شد");
      await renderSupport();
    } catch (ex) {
      toast("❌ " + (ex.message || "خطا"));
    }
  });

  async function openThread(id) {
    const data = await api(`/support/tickets/${encodeURIComponent(id)}`);
    const box = $("#sup-thread");
    box.classList.remove("hidden");
    const msgs = (data.messages || []).map(m => `
      <div style="padding:.6rem;margin:.4rem 0;border-radius:10px;background:${m.is_staff ? "rgba(42,166,163,.12)" : "var(--glass-bg-soft)"}">
        <div style="font-size:.75rem;opacity:.75">${esc(m.author_name)} · ${esc(m.created_at)}</div>
        <div style="white-space:pre-wrap">${esc(m.body)}</div>
      </div>
    `).join("");
    box.innerHTML = `
      <h4 style="margin:0 0 .5rem">${esc(data.ticket.subject)} <span class="badge">${esc(data.ticket.status)}</span></h4>
      ${msgs}
      ${data.ticket.status !== "closed" ? `
        <form id="sup-reply" style="display:flex;gap:.5rem;margin-top:.75rem">
          <input id="sup-reply-body" class="input" style="flex:1" placeholder="پاسخ شما…" required />
          <button class="btn btn-primary" type="submit">ارسال</button>
        </form>` : '<p style="opacity:.7">این تیکت بسته شده است</p>'}
    `;
    const form = $("#sup-reply");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const body = $("#sup-reply-body").value.trim();
        await api(`/support/tickets/${encodeURIComponent(id)}/messages`, {
          method: "POST", body: JSON.stringify({ body }),
        });
        toast("ارسال شد");
        await openThread(id);
      });
    }
  }

  contentEl.querySelectorAll("[data-ticket]").forEach((btn) => {
    btn.addEventListener("click", () => openThread(btn.dataset.ticket));
  });
}

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
  let l = Adm.tickets.filter((t) => Adm.tf === "all" ? true : Adm.tf === "closed" ? t.status === "closed" : t.status !== "closed");
  if (q) l = l.filter((t) => `${t.subject || ""} ${t.full_name || ""} ${t.lms_username || ""}`.toLowerCase().includes(q));
  return l.slice().sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
}
function admPaintTickets(p) {
  const list = admTicketsList();
  const pills = [["open", "باز"], ["closed", "بسته"], ["all", "همه"]];
  p.innerHTML = `
    <div class="adm-toolbar">${admSearch("tickets", "جستجوی موضوع یا نام کاربر…")}
      <button class="btn btn-ghost btn-sm" data-adm="refresh" data-v="tickets">↻</button></div>
    <div class="adm-pills">${pills.map(([k, l]) => {
      const n = k === "all" ? Adm.tickets.length : k === "closed" ? Adm.tickets.filter((t) => t.status === "closed").length : Adm.tickets.filter((t) => t.status !== "closed").length;
      return `<button class="adm-pill ${Adm.tf === k ? "on" : ""}" data-adm="tf" data-v="${k}">${l}<b>${xfa(n)}</b></button>`;
    }).join("")}</div>
    <div class="adm-list">${list.map((t) => `<div class="adm-row">
      <input type="checkbox" class="adm-chk" data-adm-sel="${xesc(t.id)}" ${Adm.sel.has(t.id) ? "checked" : ""} aria-label="انتخاب تیکت">
      <span class="row-icon">🎧</span>
      <div class="adm-row-main"><div class="row-title"><button class="adm-link" data-adm="ticket" data-id="${xesc(t.id)}">${xesc(t.subject)}</button>
        <span class="badge ${t.status === "closed" ? "badge-done" : "badge-new"}">${xesc(t.status)}</span></div>
        <div class="row-meta"><span>${xesc(t.full_name || "")}</span><span dir="ltr">${xesc(t.lms_username || "")}</span><span>${xago(t.updated_at)}</span></div></div>
      <div class="row-actions"><button class="btn btn-soft btn-sm" data-adm="ticket" data-id="${xesc(t.id)}">مشاهده / پاسخ</button></div></div>`).join("")
      || admEmpty("📭", "تیکتی در این فیلتر نیست")}</div>`;
}
async function admOpenTicket(id) {
  let data;
  try { data = await api(`/support/tickets/${encodeURIComponent(id)}`); }
  catch (e) { admToast("❌ " + (e.message || "بارگذاری تیکت ناموفق")); return; }
  const tk = data.ticket || {}; const msgs = data.messages || [];
  const L = admLayer({ type: "drawer", title: "تیکت پشتیبانی", html: `<div class="adm-dwr">
    <div class="adm-dwr-head"><span class="row-icon">🎧</span>
      <div><h2>${xesc(tk.subject || "")}</h2><div class="adm-badges">
        <span class="badge ${tk.status === "closed" ? "badge-done" : "badge-new"}" id="adm-tk-status">${xesc(tk.status || "")}</span>
        <span class="badge">${xesc(tk.full_name || tk.lms_username || "")}</span></div></div>
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
    { href: "#/library", icon: "📚", title: "کتابخانه", desc: "جزوه، آزمایش و لینک‌های مفید با تایید ادمین", isExternal: false },
    { href: "#/quera", icon: "⚙️", title: "کوئرا", desc: "مدیریت تمرین‌ها و کلاس‌های کوئرا", isExternal: false },
    { href: "#/settings", icon: "🔧", title: "تنظیمات", desc: "پیکربندی همگام‌سازی و حساب", isExternal: false },
    { href: "#/support", icon: "💬", title: "پشتیبانی", desc: "گزارش باگ و پیگیری پاسخ", isExternal: false },
    { href: "#/admin", icon: "🛡️", title: "پنل ادمین", desc: "مدیریت کاربران و نقش‌ها", isExternal: false, adminOnly: true },
    { href: "https://lms4.ui.ac.ir/pages/nodemain", icon: "🏠", title: "پنل اصلی LMS", desc: "ورود به صفحه اصلی سامانه", isExternal: true },
    { href: "https://lms4.ui.ac.ir/pages/messages", icon: "📥", title: "صندوق پیام‌ها", desc: "مشاهده پیام‌های خصوصی", isExternal: true },
    { href: "https://lms4.ui.ac.ir/pages/nodemain", icon: "🆘", title: "راهنما و پشتیبانی", desc: "دریافت راهنمایی از سامانه", isExternal: true },
    // 👇 کارت جدید درباره ما
    { href: "/api/calendar.ics", icon: "📅", title: "خروجی تقویم ICS", desc: "دانلود برای Google Calendar و گوشی", isExternal: true },
    { href: "#/help", icon: "📘", title: "راهنما و حریم خصوصی", desc: "این سایت چه می‌کند و چه چیزی ذخیره می‌شود", isExternal: false },
    { href: "#/about", icon: "💡", title: "درباره ما", desc: "درباره پروژه، سازنده و راه‌های ارتباطی", isExternal: false }
  ];

  contentEl.innerHTML = `
    ${pageHead("سایر امکانات", "دسترسی به ابزارهای جانبی و پنل اصلی سامانه")}
    
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.5rem; padding-top: 1rem;">
      ${cards.filter(c => !c.adminOnly || authRole === "admin").map(c => `
        <a href="${c.href}" 
           class="ios-card" 
           ${c.isExternal ? 'target="_blank" rel="noopener"' : ''}
           style="text-decoration: none; display: flex;">
          <div class="ios-card-icon">${c.icon}</div>
          <div class="ios-card-title">${c.title}</div>
          <div class="ios-card-desc">${c.desc}</div>
        </a>
      `).join("")}
    </div>
  `;
}


async function renderHelp() {
  contentEl.innerHTML = `
    ${pageHead("راهنما و حریم خصوصی", "شفافیت دربارهٔ کارکرد سایت")}
    <div style="display:flex;flex-direction:column;gap:1rem;max-width:820px">
      <div class="card">
        <h3 style="margin:0 0 .5rem">این سایت چیست؟</h3>
        <p style="margin:0;opacity:.9;line-height:1.7">
          یک دستیار شخصی برای دانشجویان است تا دروس، تکالیف، پیام‌ها و رویدادهای
          <strong>LMS دانشگاه اصفهان</strong> (و در صورت تمایل کوئرا) را یکجا ببینید.
          هدف این است که بعد از یک‌بار ورود، داده‌های خودتان آماده باشد و هر بار همه چیز را از صفر وارد نکنید.
        </p>
      </div>

      <div class="card">
        <h3 style="margin:0 0 .5rem">چه چیزهایی ذخیره می‌شود؟</h3>
        <ul style="margin:.25rem 0 0;padding-inline-start:1.2rem;line-height:1.8;opacity:.9">
          <li>فهرست دروس، تکالیف، پیام‌های وال، محتواها و رویدادهایی که از LMS همگام می‌شوند</li>
          <li>نشست ورود شما به <em>همین سایت</em> (کوکی HttpOnly)</li>
          <li>رمز LMS به‌صورت <strong>رمزنگاری‌شده</strong> (قابل بازیابی فقط روی سرور با کلید محرمانه) تا همگام‌سازی بعدی ممکن باشد</li>
          <li>در صورت امکان، کوکی نشست LMS به‌صورت رمزنگاری‌شده برای کاهش نیاز به زدن مکرر رمز</li>
          <li>تیکت‌های پشتیبانی که خودتان می‌فرستید</li>
        </ul>
      </div>

      <div class="card">
        <h3 style="margin:0 0 .5rem">چه چیزهایی ذخیره <u>نمی‌شود</u>؟</h3>
        <ul style="margin:.25rem 0 0;padding-inline-start:1.2rem;line-height:1.8;opacity:.9">
          <li>رمز شما به‌صورت متن ساده در دیتابیس یا لاگ API برنمی‌گردد</li>
          <li>کاربران دیگر به دروس، تکالیف یا پیام‌های شما دسترسی ندارند</li>
          <li>ادمین پنل، محتوای درسی شما را برای «فضولی» نمی‌بیند؛ تمرکزش روی حساب‌ها و پشتیبانی است</li>
        </ul>
      </div>

      <div class="card">
        <h3 style="margin:0 0 .5rem">چطور شروع کنم؟</h3>
        <ol style="margin:.25rem 0 0;padding-inline-start:1.2rem;line-height:1.8;opacity:.9">
          <li>با شماره دانشجویی و رمز <strong>LMS</strong> وارد شوید</li>
          <li>دکمهٔ <strong>همگام‌سازی</strong> را بزنید و صبر کنید تا تمام شود</li>
          <li>داشبورد، تکالیف و تقویم را بررسی کنید</li>
          <li>اگر خطا دیدید، وضعیت آخرین همگام‌سازی روی داشبورد را بخوانید یا از <a href="#/support">پشتیبانی</a> تیکت بزنید</li>
        </ol>
      </div>

      <div class="card">
        <h3 style="margin:0 0 .5rem">نکته‌های مهم امنیتی</h3>
        <ul style="margin:.25rem 0 0;padding-inline-start:1.2rem;line-height:1.8;opacity:.9">
          <li>این سرویس جایگزین رسمی LMS نیست؛ اگر در دسترس نبود، مستقیم به LMS بروید</li>
          <li>روی سیستم مشترک، بعد از کار <strong>خروج</strong> کنید</li>
          <li>اگر شک دارید نشست‌تان لو رفته، دوباره وارد شوید (نشست قبلی باطل می‌شود) یا به پشتیبانی بگویید</li>
        </ul>
      </div>

      <div style="display:flex;gap:.75rem;flex-wrap:wrap">
        <a class="btn btn-primary" href="#/support">گزارش مشکل</a>
        <a class="btn btn-soft" href="#/about">درباره پروژه</a>
      </div>
    </div>
  `;
}

async function renderAbout() {
  contentEl.innerHTML = `
    ${pageHead("درباره ما", "آشنایی با پروژه، سازنده و اهداف آن")}
    
    <div style="display: flex; flex-direction: column; gap: 1.5rem; max-width: 900px; margin: 0 auto; padding-bottom: 3rem;">
      
          <!-- 👇 هدر (Hero) جدید: کارت معرفی سازنده با قابلیت توسعه -->
            <!-- 👇 بخش معرفی سازنده (شیشه در شیشه) -->
      <div style="position: relative; width: 100%; margin-bottom: 1.5rem;">
        
        <!-- کارت شیشه‌ای اصلی (کانتینر) -->
        <div class="card" style="padding: 1.5rem; background: linear-gradient(135deg, rgba(42, 166, 163, 0.1) 0%, var(--glass-bg) 100%); border-radius: 24px; position: relative; overflow: hidden; border: 1px solid var(--glass-border);">
          
          <!-- افکت گرادیانت پس‌زمینه -->
          <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(42,166,163,0.15) 0%, transparent 60%); pointer-events: none;"></div>

          <!-- 👇 چیدمان افقی -->
          <div style="display: flex; flex-direction: row; gap: 1.5rem; align-items: stretch; flex-wrap: wrap; position: relative; z-index: 1;">
            
            <!-- شیشه اول: سمت راست (عکس و نام) -->
            <div class="glass-inner-container" style="flex: 0 0 240px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem 1.5rem; background: var(--glass-bg-strong); border: 1px solid var(--glass-border-hover); border-radius: 20px; box-shadow: inset 0 2px 5px rgba(255,255,255,0.1);">
              
              <!-- عکس پروفایل -->
              <div style="width: 120px; height: 120px; margin-bottom: 1.2rem; border-radius: 50%; padding: 4px; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); box-shadow: 0 8px 20px var(--ring);">
                <div style="width: 100%; height: 100%; border-radius: 50%; overflow: hidden; background: var(--bg);">
                  <img src="/static/img/my-avatar.jpg" alt="محمد اسدی" style="width: 100%; height: 100%; object-fit: cover; display: block;" />
                </div>
              </div>

              <h2 style="font-size: 1.4rem; font-weight: 800; color: var(--text-primary); margin-bottom: 0.2rem; text-align: center;">محمد اسدی</h2>
              <p style="font-size: 0.9rem; color: var(--primary); font-weight: 600; margin-bottom: 0.8rem; text-align: center;">توسعه‌دهنده</p>
              <div class="badge badge-domain" style="font-size: 0.75rem; padding: 0.3rem 0.8rem;">مهندسی کامپیوتر • ورودی ۱۴۰۴</div>
            </div>

            <!-- شیشه دوم: سمت چپ (بیوگرافی و ارتباطات) -->
            <div class="glass-inner-container" style="flex: 1; min-width: 280px; padding: 2rem; display: flex; flex-direction: column; justify-content: center; background: var(--glass-bg-strong); border: 1px solid var(--glass-border-hover); border-radius: 20px; box-shadow: inset 0 2px 5px rgba(255,255,255,0.1);">
              
              <h3 style="font-size: 1.2rem; font-weight: 800; margin-bottom: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📝 درباره من
              </h3>
              
              <!-- متن بیوگرافی -->
              <p style="line-height: 1.8; color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 1.5rem;">
                دانشجوی مهندسی کامپیوتر دانشگاه اصفهان. علاقه‌مند به توسعه وب، هوش مصنوعی و ساخت ابزارهایی که زندگی روزمره را ساده‌تر می‌کنند. عاشق یادگیری تکنولوژی‌های جدید و پروژه‌های متن‌باز.
              </p>

              <!-- آیکون‌های ارتباطی -->
              <div style="display: flex; gap: 0.8rem; flex-wrap: wrap; margin-top: auto;">
                
                <!-- گیت‌هاب -->
                <a href="https://github.com/Asadix85" target="_blank" rel="noopener" title="گیت‌هاب" 
                   style="width: 45px; height: 45px; border-radius: 50%; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--glass-border); display: flex; align-items: center; justify-content: center; text-decoration: none; transition: all 0.2s;"
                   onmouseover="this.style.background='#333'; this.style.transform='translateY(-3px)';" 
                   onmouseout="this.style.background='rgba(255, 255, 255, 0.05)'; this.style.transform='translateY(0)';">
                  <!-- کلاس icon-github اضافه شد -->
                  <svg class="icon-github" width="20" height="20" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                </a>

                <!-- تلگرام -->
                <a href="https://t.me/ASAADIX" target="_blank" rel="noopener" title="تلگرام" 
                   style="width: 45px; height: 45px; border-radius: 50%; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--glass-border); display: flex; align-items: center; justify-content: center; text-decoration: none; transition: all 0.2s;"
                   onmouseover="this.style.background='#229ED9'; this.style.transform='translateY(-3px)';" 
                   onmouseout="this.style.background='rgba(255, 255, 255, 0.05)'; this.style.transform='translateY(0)';">
                  <!-- کلاس icon-telegram اضافه شد -->
                  <svg class="icon-telegram" width="20" height="20" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.26-1.91.178-.184 3.247-2.977 3.307-3.23.005-.02.01-.04-.006-.06-.015-.017-.037-.023-.058-.023-.05 0-.084.027-.113.043-.038.023-3.523 2.237-3.558 2.258-.085.05-.174.086-.27.107-.11.024-.224.04-.337.04-.12 0-.24-.016-.348-.046l-1.148-.36c-.23-.073-.455-.148-.458-.38-.002-.12.034-.243.108-.368.192-.325 1.666-.94 2.513-1.278 1.033-.412 2.078-.825 3.096-1.23 1.07-.424 1.6-.65 1.753-.677z"/></svg>
                </a>

                <!-- ایمیل -->
                <a href="mailto:mohammad8asadi5@gmail.com" title="ایمیل" 
                   style="width: 45px; height: 45px; border-radius: 50%; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--glass-border); display: flex; align-items: center; justify-content: center; text-decoration: none; transition: all 0.2s;"
                   onmouseover="this.style.background='#EA4335'; this.style.transform='translateY(-3px)';" 
                   onmouseout="this.style.background='rgba(255, 255, 255, 0.05)'; this.style.transform='translateY(0)';">
                  <!-- کلاس icon-email اضافه شد -->
                  <svg class="icon-email" width="20" height="20" viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                </a>

              </div>
            </div>

          </div>
        </div>

      </div>

      <!-- 👇 توضیحات پروژه -->
      <div class="card" style="padding: 2rem;">
        <h3 style="font-size: 1.3rem; font-weight: 800; margin-bottom: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
          📖 درباره‌ی این پروژه
        </h3>
        <div style="line-height: 1.8; color: var(--text-secondary); font-size: 0.95rem;">
          <p style="margin-bottom: 1rem;">
            <b>LMS Assistant</b> یک دستیار متن‌باز است که برای آسان‌تر کردن تجربه‌ی دانشجویان دانشگاه اصفهان طراحی شده است. این ابزار به شما کمک می‌کند تا تمام اطلاعات درسی خود را در یک محیط یکپارچه و مدرن مدیریت کنید.
          </p>
          <p style="margin-bottom: 1rem;">
            با یک کلیک ساده، برنامه به صورت خودکار دروس، فایل‌های آموزشی، تکالیف، پیام‌های استادان و رویدادهای تقویم را از سامانه LMS استخراج می‌کند. همچنین تغییرات جدید را تشخیص داده و به شما اطلاع می‌دهد تا هیچ مهلتی را از دست ندهید.
          </p>
          <p>
            علاوه بر این، تمرین‌های سایت <b>کوئرا</b> (مخصوص دروس برنامه‌نویسی) نیز در کنار تکالیف LMS نمایش داده می‌شوند. هدف ما ساختن یک محیط ساده، سریع و کاربردی است که تمرکز شما را بر یادگیری افزایش دهد.
          </p>
        </div>
      </div>

      <!-- 👇 ویژگی‌های فنی -->
      <div class="card" style="padding: 2rem;">
        <h3 style="font-size: 1.3rem; font-weight: 800; margin-bottom: 1.5rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
          ⚙️ ویژگی‌های فنی
        </h3>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem;">
          
          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">🐍</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">Python + FastAPI</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">بک‌اند پرسرعت با پایتون و فریم‌ورک FastAPI</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">🍪</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">Multi-Domain SSO</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">پشتیبانی از lms3, lms4, lms5 با احراز هویت خودکار</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">💾</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">SQLite Storage</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">ذخیره‌سازی محلی روی سیستم شما، بدون نیاز به سرور خارجی</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">🔄</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">Change Detection</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">تشخیص خودکار موارد جدید بین همگام‌سازی‌ها</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">📅</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">تقویم ددلاین‌ها</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">نمای هفتگی از مهلت تکالیف و رویدادهای مهم</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">🎨</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">Liquid Glass UI</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">رابط کاربری مدرن با افکت‌های شیشه‌ای و تم روشن/تیره</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">🎯</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">Quera Integration</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">همگام‌سازی تمرین‌های سایت کوئرا در کنار LMS</div>
            </div>
          </div>

          <div class="glass-inner-container" style="padding: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 2rem;">📊</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary);">آمار و نمودار</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">نمایش آمار کلی با نمودارهای تعاملی</div>
            </div>
          </div>

        </div>
      </div>

      <!-- 👇 فوتر -->
      <div style="text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 1rem;">
        <p>LMS Assistant v0.1.0 • ساخته شده با ❤️ برای دانشگاه اصفهان</p>
        <p>© ۱۴۰۵ — محمد اسدی</p>
      </div>

    </div>
  `;
}

async function renderQuera() {
  const [assignments, courses] = await Promise.all([api("/quera/assignments"), api("/quera/courses")]);
  const courseNames = Object.fromEntries(courses.map((c) => [c.id, c.name]));

  const ring = (a) => {
    const pct = a.problems_count ? Math.round((a.problems.filter((p) => p.is_submitted).length / a.problems_count) * 100) : 0;
    return `<div class="ring" style="--p:${pct}"><span>${pct}٪</span></div>`;
  };

  contentEl.innerHTML = `
    ${pageHead("کوئرا", "تمرین‌ها و دوره‌های کوئرا")}
    <div class="card quera-toolbar">
      <div class="quera-count">${assignments.length} تمرین همگام‌سازی شده</div>
      <button class="btn btn-primary btn-sm" id="btn-quera-sync" onclick="syncQuera()">🔄 همگام‌سازی کوئرا</button>
    </div>
    <div class="item-list">
      ${assignments.length ? assignments.map((a) => {
        const submitted = a.problems.filter((p) => p.is_submitted).length;
        return `
        <div class="list-row">
          <span class="row-icon">⚙️</span>
          <div class="row-body">
            <div class="row-title">${esc(a.name)}
              ${a.is_done ? '<span class="badge badge-done">بسته</span>' : ""}
              ${a.is_manual ? '<span class="badge">دستی</span>' : ""}
            </div>
            <div class="row-meta">
              <span>دوره: ${esc(a.course_name || courseNames[a.id] || "—")}</span>
              <span class="sep">·</span><span>پایان: ${esc(a.finish_time || "—")}</span>
              <span class="sep">·</span><span>حل‌شده: ${submitted}/${a.problems_count}</span>
            </div>
          </div>
          <div class="row-actions">${ring(a)}</div>
        </div>`;
      }).join("") : emptyState("تمرینی از کوئرا دریافت نشده")}
    </div>`;
}

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

async function renderSettings() {
  const sync = await api("/settings/sync");
  const rows = [["courses","درس‌ها","لیست و جزئیات درس‌ها"],["contents","محتواها","فایل‌ها و منابع"],
    ["events","رویدادها","جلسات و آزمون‌ها"],["wall","وال (پیام‌ها و تکالیف)","گفتگوها و مهلت‌ها"],
    ["members","اعضای درس‌ها","اساتید و دانشجویان"]].map(([key,label,desc]) =>
    `<div class="setting-row"><div class="setting-info"><span>${label}</span><small>${desc}</small></div>
     <label class="switch"><input type="checkbox" data-key="${key}" ${sync[key] ? "checked" : ""}/><span class="slider"></span></label></div>`).join("");
  contentEl.innerHTML = `${pageHead("تنظیمات","پیکربندی همگام‌سازی و حساب کاربری")}
    <div class="card"><div class="card-head"><h3 class="section-title">🔄 فازهای همگام‌سازی</h3></div>${rows}
      <button class="btn btn-primary" style="margin-top:1rem" id="btn-save-sync">ذخیره تنظیمات</button></div>
    <div class="card"><div class="card-head"><h3 class="section-title">🔐 حساب کاربری</h3></div>
      <p class="muted" style="margin-bottom:.8rem">برای تغییر شماره دانشجویی یا رمز عبور، دوباره وارد شوید.</p>
      <button class="btn btn-soft" id="btn-relogin">تغییر حساب / ورود مجدد</button></div>
    <div class="card"><div class="card-head"><h3 class="section-title">🧾 داده‌ها و نشست‌ها</h3></div>
      <p class="muted" style="margin-bottom:.8rem">خروج از همه دستگاه‌ها، دریافت کپی داده، یا حذف کامل حساب.</p>
      <div style="display:flex;flex-wrap:wrap;gap:.5rem">
        <button class="btn btn-soft btn-sm" id="btn-revoke-sessions">خروج از همه نشست‌ها</button>
        <a class="btn btn-soft btn-sm" href="/api/account/export" download="lms-my-data.json">⬇ خروجی داده (JSON)</a>
        <button class="btn btn-soft btn-sm" id="btn-delete-account" style="color:var(--danger)">حذف حساب</button>
      </div></div>`;
  const save = document.getElementById("btn-save-sync");
  save.addEventListener("click", async () => {
    save.disabled = true; save.textContent = "در حال ذخیره…";
    const body = {}; document.querySelectorAll("[data-key]").forEach((el) => { body[el.dataset.key] = el.checked; });
    try { await api("/settings/sync", { method: "POST", body: JSON.stringify(body) }); toast("✅ تنظیمات ذخیره شد"); }
    catch (e) { toast("❌ " + (e.message || "خطا")); }
    finally { save.disabled = false; save.textContent = "ذخیره تنظیمات"; }
  });
  document.getElementById("btn-relogin").addEventListener("click", () => showLogin());
  const confirmBox = (title, text, okLabel, run) => calLayer({ title, html:
    `<p style="font-size:.9rem;line-height:1.9;margin:0 0 1rem">${cesc(text)}</p>
     <div class="lib-modal-actions"><button class="btn btn-ghost" data-lib-close>انصراف</button>
     <button class="btn btn-danger" id="cal-cf-ok" data-autofocus>${cesc(okLabel)}</button></div>`,
    onMount: (w, L) => { const b = w.querySelector("#cal-cf-ok");
      b.addEventListener("click", async () => { b.disabled = true; await run(); L.close(); }); } });
  document.getElementById("btn-revoke-sessions").addEventListener("click", () =>
    confirmBox("خروج از همه نشست‌ها", "از همه دستگاه‌ها خارج می‌شوید و باید دوباره وارد شوید.", "خروج از همه", async () => {
      try { await api("/account/sessions/revoke-all", { method: "POST", body: "{}" }); toast("همه نشست‌ها قطع شد"); location.reload(); }
      catch (e) { toast("❌ " + (e.message || "خطا")); } }));
  document.getElementById("btn-delete-account").addEventListener("click", () =>
    confirmBox("حذف کامل حساب", "همه داده‌های شما برای همیشه حذف می‌شود. این عمل برگشت‌پذیر نیست.", "حذف حساب", async () => {
      try { await api("/account", { method: "DELETE" }); toast("حساب حذف شد"); location.hash = "#/"; location.reload(); }
      catch (e) { toast("❌ " + (e.message || "خطا")); } }));
}

window.saveSyncSettings = async () => {
  const body = {};
  document.querySelectorAll("[data-key]").forEach((el) => { body[el.dataset.key] = el.checked; });
  await api("/settings/sync", { method: "POST", body: JSON.stringify(body) });
  toast("✅ تنظیمات ذخیره شد");
};

window.showLogin = showLogin;

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
  try { window.__crsTeardown?.(); window.__mapTeardown?.(); } catch (_) {}
  try { window.__crsTeardown?.(); } catch (_) {}
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
  renderPage(currentRoute());

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