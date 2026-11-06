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
  if (!res.ok) throw new Error(`خطای سرور (${res.status})`);
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

function setTheme(theme) {
  document.body.dataset.theme = theme;
  $("#btn-theme").textContent = theme === "dark" ? "☀️" : "🌙";
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
  btn.querySelector(".btn-sync-label").textContent = running ? "در حال همگام‌سازی…" : "🔄 همگام‌سازی";
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

async function renderCourses() {
  const courses = await api("/courses");
  if (!courses.length) { contentEl.innerHTML = emptyState("درسی یافت نشد"); return; }

  // پیدا کردن جدیدترین ترم (برای فیلتر)
  const terms = courses
    .filter(c => c.source === "lms" && c.term)
    .map(c => c.term.trim());
  const currentTerm = terms.length > 0 ? [...new Set(terms)].sort().reverse()[0] : null;

  // وضعیت اولیه فیلترها
  let filters = {
    active: false,
    currentTerm: false,
    quera: false,
  };

  // ===== ساخت HTML اصلی صفحه =====
  contentEl.innerHTML = `
    ${pageHead("درس‌ها", `${courses.length} درس همگام‌سازی شده`)}
    
    <div class="filter-bar" style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1rem; align-items:center;">
      <button class="btn btn-soft btn-sm filter-btn" data-filter="active">⚡ دروس فعال</button>
      <button class="btn btn-soft btn-sm filter-btn" data-filter="quera">⚙️ کوئرا</button>
      
      <div class="search-box" style="flex:1; min-width:200px; margin-inline-start:auto;">
        <span class="search-ico">🔍</span>
        <input id="filter-input" type="search" placeholder="جستجوی نام درس، استاد یا کد…" />
      </div>
    </div>

    <div class="course-grid" id="courses-list"></div>
  `;

  // ===== توابع رندر لیست =====
  const renderList = () => {
    const list = document.getElementById("courses-list");
    if (!list) return;

    // اعمال فیلترها
    let filtered = courses.filter(c => {
      if (filters.active && c.status !== "active") return false;
      if (filters.currentTerm && currentTerm && c.term !== currentTerm) return false;
      if (filters.quera && c.source !== "quera") return false;
      return true;
    });

    // اعمال جستجو
    const q = (document.getElementById("filter-input")?.value || "").trim().toLowerCase();
    if (q) {
      filtered = filtered.filter(c =>
        `${c.name} ${c.teacher || ""} ${c.code || ""} ${c.domain}`.toLowerCase().includes(q)
      );
    }

    // تولید کارت‌ها
    list.innerHTML = filtered.length
      ? filtered.map((c) => {
          const isQuera = c.source === "quera";

          // تنظیم لینک و ویژگی‌های کلیک
          const href = isQuera ? (c.url || `https://quera.org/course/${c.group_id}`) : `#/course/${encodeURIComponent(c.id)}`;
          const target = isQuera ? 'target="_blank" rel="noopener"' : '';

          const icon = isQuera ? "⚙️" : "📘";
          const badgeDomain = isQuera
            ? '<span class="badge badge-warn">کوئرا</span>'
            : `<span class="badge badge-domain">${esc(c.domain)}</span>`;

          return `
          <a class="course-card" href="${href}" ${target}>
            <div class="course-top">
              <span class="course-icon">${icon}</span>
              ${badgeDomain}
              ${c.status === "active" ? '<span class="badge badge-new">فعال</span>' : ""}
            </div>
            <div class="course-name">${esc(c.name)}</div>
            <div class="course-meta">
              <span>👨‍🏫 ${esc(c.teacher || "—")}</span>
              ${c.code ? `<span>کد ${esc(c.code)}</span>` : ""}
              ${c.term ? `<span>ترم ${esc(c.term)}</span>` : ""}
            </div>
          </a>`;
        }).join("")
      : `<div class="empty" style="grid-column:1/-1"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  // ===== مدیریت رویدادهای فیلتر =====
  const filterBtns = document.querySelectorAll(".filter-btn");

  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const type = btn.dataset.filter;

      // تغییر وضعیت فیلتر
      if (type === "active") filters.active = !filters.active;
      if (type === "term") filters.currentTerm = !filters.currentTerm;
      if (type === "quera") filters.quera = !filters.quera;

      // تغییر ظاهر دکمه
      const isActive = filters[type];
      btn.classList.toggle("active", isActive);

      // رندر مجدد لیست
      renderList();
    });
  });

  // رویداد جستجو
  document.getElementById("filter-input")?.addEventListener("input", renderList);

  // رندر اولیه
  renderList();
}

async function renderCourseDetail(courseId) {
  const d = await api(`/courses/${encodeURIComponent(courseId)}/detail`);
  const c = d.course;

  const listOrEmpty = (items, fn, msg) =>
    items.length ? items.map(fn).join("") : `<div class="empty muted"><span class="empty-icon">📭</span>${msg}</div>`;

  // 1. ساخت HTML مکان‌ها
  let locationsHtml = "";
  if (d.locations && d.locations.length > 0) {
    locationsHtml = `<div class="location-list">` + d.locations.map((loc, index) => {
      const neshanUrl = `https://nshn.ir/?lat=${loc.lat}&lng=${loc.lng}`;
      const gmapUrl = `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}&travelmode=driving`;

      return `
        <div class="location-glass-item">
          <div class="location-glass-info">
            <div class="session-time-badge">
              <span>🗓 ${esc(loc.weekday)}</span>
              <span class="sep">·</span>
              <span style="font-weight: 700; color: var(--text);">ساعت ${esc(loc.start_time)} تا ${esc(loc.end_time)}</span>
            </div>
            <div class="faculty-title">📍 ${esc(loc.faculty)}</div>
            <div class="building-text">${esc(loc.location_text)}</div>
            <div class="location-btns">
              <a href="${neshanUrl}" target="_blank" rel="noopener" class="btn btn-primary">🧭 نشان</a>
              <a href="${gmapUrl}" target="_blank" rel="noopener" class="btn btn-soft">🗺 گوگل مپ</a>
            </div>
          </div>
          <div id="leaflet-map-${index}" class="location-map-small"></div>
        </div>
      `;
    }).join("") + `</div>`;
  } else {
      locationsHtml = `<div class="empty muted"><span class="empty-icon">📍</span>مکانی ثبت نشده است</div>`;
  }

  // 2. محتوای داخلی
  const postsHtml = listOrEmpty(d.posts, (p) => `
    <div class="list-row">
      <span class="row-icon">💬</span>
      <div class="row-body">
        <div class="row-title">${esc(p.author)}</div>
        <div class="row-meta">${esc(p.text)}</div>
      </div>
    </div>`, "پیامی نیست");

  const assignmentsHtml = listOrEmpty(d.assignments, (a) => `
    <div class="list-row">
      <span class="row-icon">📝</span>
      <div class="row-body">
        <div class="row-title">${esc(a.title)} ${a.is_done ? '<span class="badge badge-done">انجام شده</span>' : ""}</div>
        <div class="row-meta">مهلت: ${esc(a.deadline_jalali || a.deadline || "—")}</div>
      </div>
    </div>`, "تکلیفی نیست");

  const contentsHtml = listOrEmpty(d.contents, (x) => `
    <div class="list-row">
      <span class="row-icon">📄</span>
      <div class="row-body">
        <div class="row-title"><a href="${proxyUrl(x.url)}" target="_blank" rel="noopener">${esc(x.title)}</a></div>
        <div class="row-meta">${esc(x.content_type)}${x.filename ? `<span class="sep">·</span>${esc(x.filename)}` : ""}</div>
      </div>
    </div>`, "محتوایی نیست");


    // 👇 ساخت کارت برای هر فرد با آیکون شیشه‌ای دایره‌ای (مینیمال و باریک)
  const membersHtml = d.members.length
    ? d.members.map((m) => {
        let roleColor = "var(--text-muted)";
        let roleBg = "var(--glass-bg-soft)"; // استفاده از رنگ شیشه‌ای خنثی
        let roleIcon = "👤";
        let roleLabel = "دانشجو";

        if (m.member_type === "teacher") {
          roleColor = "var(--primary)";
          roleBg = "rgba(42, 166, 163, 0.15)"; // شفافیت برای استاد
          roleIcon = "👨‍🏫";
          roleLabel = "استاد";
        } else if (m.member_type === "support") {
          roleColor = "var(--warning)";
          roleBg = "rgba(255, 149, 0, 0.15)"; // شفافیت برای دستیار
          roleIcon = "🛟";
          roleLabel = "دستیار / پشتیبان";
        }

        // 👇 استایل iOS و شیشه‌ای برای دایره آیکون
        const iconStyle = `
          width: 32px; 
          height: 32px; 
          border-radius: 50%; 
          display: flex; 
          align-items: center; 
          justify-content: center; 
          font-size: 0.9rem;
          background: ${roleBg};
          border: 1px solid var(--glass-border);
          box-shadow: inset 0 1px 2px rgba(255,255,255,0.1);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          flex-shrink: 0;
        `;

        return `
          <!-- 👇 کاهش پدینگ، افزایش گردی گوشه‌ها و استفاده از استایل شیشه‌ای -->
          <div class="glass-inner-container" style="
            padding: 0.5rem 0.8rem; 
            margin-bottom: 0.5rem; 
            display: flex; 
            align-items: center; 
            gap: 0.8rem; 
            border-radius: 20px; /* گوشه‌های خیلی گرد */
            background-color: rgba(255, 255, 255, 0.03); /* شیشه‌ای */
          ">
            <div style="${iconStyle}">${roleIcon}</div>
            <div style="flex: 1;">
              <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary); margin-bottom: 0.1rem;">
                ${esc(m.name)}
              </div>
              <div style="font-size: 0.7rem; color: ${roleColor}; font-weight: 600;">
                ${roleLabel}
              </div>
            </div>
          </div>
        `;
      }).join("")
    : `<div class="empty muted"><span class="empty-icon">📭</span>عضوی نیست</div>`;

  // 3. تزریق HTML
  contentEl.innerHTML = `
    <div class="card course-hero">
      <div class="course-hero-main">
        <h3>${esc(c.name)}</h3>
        <div class="course-hero-meta">
          <span class="badge badge-domain">${esc(c.domain)}</span>
          <span>👨‍🏫 ${esc(c.teacher || "—")}</span>
          <span>کد ${esc(c.code || "—")}</span>
          <span>ترم ${esc(c.term || "—")}</span>
        </div>
      </div>
      <a href="${esc(c.url)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">باز کردن در LMS ↗</a>
    </div>

    <div class="grid-2" style="align-items: start; gap: 1.5rem;">
      
      <!-- ستون راست -->
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        
        <details class="accordion-panel" open>
          <summary class="accordion-header">
            <div class="accordion-header-content">
              <span>📝 تکالیف</span>
              ${d.assignments.filter(a => !a.is_done).length ? `<span class="accordion-badge">${d.assignments.filter(a => !a.is_done).length}</span>` : ""}
            </div>
            <span class="accordion-icon">▼</span>
          </summary>
          <div class="accordion-body">
            <div class="item-list">${assignmentsHtml}</div>
          </div>
        </details>

        <details class="accordion-panel" open>
          <summary class="accordion-header">
            <div class="accordion-header-content"><span>💬 پیام‌های وال</span></div>
            <span class="accordion-icon">▼</span>
          </summary>
          <div class="accordion-body">
            <div class="item-list">${postsHtml}</div>
          </div>
        </details>

      </div>

      <!-- ستون چپ: مکان، محتواها، اعضا -->
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        
        <!-- مکان کلاس (بسته) -->
        <details class="accordion-panel">
          <summary class="accordion-header">
            <div class="accordion-header-content"><span>📍 مکان کلاس</span></div>
            <span class="accordion-icon">▼</span>
          </summary>
          <div class="accordion-body">
            ${locationsHtml}
          </div>
        </details>

        <!-- محتواها و فایل‌ها (بسته) -->
        <details class="accordion-panel">
          <summary class="accordion-header">
            <div class="accordion-header-content"><span>📁 محتواها و فایل‌ها</span></div>
            <span class="accordion-icon">▼</span>
          </summary>
          <div class="accordion-body">
            <div class="item-list">${contentsHtml}</div>
          </div>
        </details>

        <!-- اعضا (بسته) -->
        <details class="accordion-panel">
          <summary class="accordion-header">
            <div class="accordion-header-content"><span>👥 اعضا (اساتید و دانشجویان)</span></div>
            <span class="accordion-icon">▼</span>
          </summary>
          <div class="accordion-body">
            <div class="item-list">${membersHtml}</div>
          </div>
        </details>

      </div>
    </div>
  `;

  // 4. رندر نقشه‌ها
  if (d.locations && d.locations.length > 0) {
    setTimeout(() => {
      d.locations.forEach((loc, index) => {
        const mapEl = document.getElementById(`leaflet-map-${index}`);
        if (mapEl) {
          const map = L.map(mapEl, {
            zoomControl: false, // برای نقشه کوچک، زوم‌کنترل ممکن است شلوغ کند
            attributionControl: false
          }).setView([loc.lat, loc.lng], 16);

          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
          }).addTo(map);

          // مارکر با آیکون پیش‌فرض لِفلت
          L.marker([loc.lat, loc.lng]).addTo(map);

          const detailsEl = mapEl.closest('details');
          if (detailsEl) {
              detailsEl.addEventListener('toggle', (e) => {
                  if (e.target.open) {
                      setTimeout(() => map.invalidateSize(), 200);
                  }
              });
          }
        }
      });
    }, 300);
  }
}

async function renderAssignments() {
  const items = await api("/assignments");
  if (!items.length) {
    contentEl.innerHTML = emptyState("تکلیفی یافت نشد", "بعد از همگام‌سازی اینجا ظاهر می‌شوند");
    return;
  }
  const names = await courseNameMap();
  const now = Date.now();
  const weekMs = 7 * 24 * 3600 * 1000;

  const parseDeadline = (a) => {
    if (!a.deadline) return null;
    const t = Date.parse(a.deadline);
    return Number.isNaN(t) ? null : t;
  };

  let filter = "open"; // open | overdue | week | done | all

  const counts = {
    all: items.length,
    open: items.filter((a) => !a.is_done).length,
    overdue: items.filter((a) => !a.is_done && a.is_expired).length,
    week: items.filter((a) => {
      if (a.is_done) return false;
      const d = parseDeadline(a);
      if (d == null) return false;
      return d >= now && d <= now + weekMs;
    }).length,
    done: items.filter((a) => a.is_done).length,
  };

  contentEl.innerHTML = `
    ${pageHead("تکالیف", `${items.length} تکلیف · ${counts.open} باز`)}
    <div class="filter-bar" style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem;align-items:center">
      <a class="btn btn-soft btn-sm" href="/api/calendar.ics" download="lms-assistant.ics">⬇ خروجی ICS</a>
      <button type="button" class="filter-btn active" data-af="open">باز (${counts.open})</button>
      <button type="button" class="filter-btn" data-af="overdue">عقب‌افتاده (${counts.overdue})</button>
      <button type="button" class="filter-btn" data-af="week">این هفته (${counts.week})</button>
      <button type="button" class="filter-btn" data-af="done">انجام‌شده (${counts.done})</button>
      <button type="button" class="filter-btn" data-af="all">همه (${counts.all})</button>
      <div class="search-box" style="flex:1;min-width:200px;margin-inline-start:auto">
        <span class="search-ico">🔍</span>
        <input id="filter-input" type="search" placeholder="جستجوی عنوان یا درس…" />
      </div>
    </div>
    <div class="item-list" id="list-container"></div>`;

  const matchesFilter = (a) => {
    const d = parseDeadline(a);
    switch (filter) {
      case "open":
        return !a.is_done;
      case "overdue":
        return !a.is_done && !!a.is_expired;
      case "week":
        return !a.is_done && d != null && d >= now && d <= now + weekMs;
      case "done":
        return !!a.is_done;
      default:
        return true;
    }
  };

  const sortItems = (list) =>
    list.slice().sort((a, b) => {
      // انجام‌نشده اول
      if (!!a.is_done !== !!b.is_done) return a.is_done ? 1 : -1;
      // عقب‌افتاده اول بین بازها
      if (!!a.is_expired !== !!b.is_expired) return a.is_expired ? -1 : 1;
      const da = parseDeadline(a);
      const db = parseDeadline(b);
      if (da == null && db == null) return 0;
      if (da == null) return 1;
      if (db == null) return -1;
      return da - db;
    });

  const renderList = () => {
    const el = document.getElementById("list-container");
    if (!el) return;
    let filtered = items.filter(matchesFilter);
    const q = (document.getElementById("filter-input")?.value || "").trim().toLowerCase();
    if (q) {
      filtered = filtered.filter((a) =>
        `${a.title} ${names[a.course_id] || a.course_id}`.toLowerCase().includes(q)
      );
    }
    filtered = sortItems(filtered);
    el.innerHTML = filtered.length
      ? filtered
          .map((a) => {
            const d = parseDeadline(a);
            let urgency = "";
            if (!a.is_done && a.is_expired) urgency = "عقب‌افتاده";
            else if (!a.is_done && d != null && d - now < 48 * 3600 * 1000)
              urgency = "کمتر از ۴۸ ساعت";
            return `
        <div class="list-row">
          <span class="row-icon">${a.is_done ? "✅" : a.is_expired ? "⏰" : "📝"}</span>
          <div class="row-body">
            <div class="row-title">
              ${
                a.view_url
                  ? `<a href="/api/jaam-proxy?url=${encodeURIComponent(a.view_url)}" target="_blank" rel="noopener">${esc(a.title)}</a>`
                  : esc(a.title)
              }
              ${a.is_new ? '<span class="badge badge-new">جدید</span>' : ""}
              ${a.is_expired && !a.is_done ? '<span class="badge badge-expired">گذشته</span>' : ""}
              ${urgency && !a.is_expired ? `<span class="badge badge-warn">${urgency}</span>` : ""}
              ${a.is_done ? '<span class="badge badge-done">انجام شده</span>' : ""}
            </div>
            <div class="row-meta">
              <span>مهلت: ${esc(a.deadline_jalali || a.deadline || "—")}</span>
              <span class="sep">·</span><span>${esc(names[a.course_id] || a.course_id)}</span>
            </div>
          </div>
          <div class="row-actions">
            ${
              !a.is_done && a.submit_url
                ? `<a class="btn-primary-glass" href="/api/jaam-proxy?url=${encodeURIComponent(a.submit_url)}" target="_blank" rel="noopener">ارسال ↗</a>`
                : ""
            }
            <button class="btn-ghost-glass" onclick="toggleAssignment('${esc(a.id)}', ${!a.is_done})">
              ${a.is_done ? "لغو انجام" : "انجام شد ✓"}
            </button>
          </div>
        </div>`;
          })
          .join("")
      : emptyState("موردی با این فیلتر نیست", "فیلتر دیگری را امتحان کنید");
  };

  contentEl.querySelectorAll("[data-af]").forEach((btn) => {
    btn.addEventListener("click", () => {
      filter = btn.dataset.af;
      contentEl.querySelectorAll("[data-af]").forEach((b) => b.classList.toggle("active", b === btn));
      renderList();
    });
  });
  document.getElementById("filter-input")?.addEventListener("input", renderList);
  renderList();
}


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

async function renderAdmin() {
  if (authRole !== "admin") {
    contentEl.innerHTML = `<div class="empty"><span class="empty-icon">🔒</span>دسترسی ادمین لازم است<small>اگر اخیراً ارتقا یافته‌اید، یک‌بار خارج و دوباره وارد شوید</small></div>`;
    return;
  }
  let data;
  try {
    data = await api("/admin/users");
  } catch (e) {
    contentEl.innerHTML = emptyState("خطا در دریافت لیست کاربران", String(e.message || e));
    return;
  }
  const st = data.stats || {};
  const rows = (data.users || []).map((u) => {
    const activeBadge = u.is_active
      ? '<span class="badge badge-new">فعال</span>'
      : '<span class="badge badge-expired">غیرفعال</span>';
    const roleBadge = u.role === "admin"
      ? '<span class="badge badge-warn">ادمین</span>'
      : '<span class="badge">کاربر</span>';
    const selfMark = u.is_self ? ' <small style="opacity:.7">(شما)</small>' : '';
    return `<tr data-id="${esc(u.id)}">
      <td>
        <div style="font-weight:600">${esc(u.full_name || "—")}${selfMark}</div>
        <div style="font-size:.8rem;opacity:.75;direction:ltr;text-align:right">${esc(u.lms_username)}</div>
      </td>
      <td>${roleBadge}</td>
      <td>${activeBadge}</td>
      <td style="direction:ltr;text-align:right;font-size:.85rem">${esc(u.last_login_at || "—")}</td>
      <td>${u.session_count ?? 0}</td>
      <td style="display:flex;flex-wrap:wrap;gap:.35rem">
        <button class="btn btn-soft btn-sm" data-act="role" data-id="${esc(u.id)}" data-role="${u.role === "admin" ? "user" : "admin"}" ${u.is_self && u.role === "admin" ? "disabled title=\"نقش خود را از اینجا تغییر ندهید\"" : ""}>
          ${u.role === "admin" ? "↓ کاربر" : "↑ ادمین"}
        </button>
        <button class="btn btn-soft btn-sm" data-act="active" data-id="${esc(u.id)}" data-active="${u.is_active ? "0" : "1"}" ${u.is_self ? "disabled" : ""}>
          ${u.is_active ? "غیرفعال" : "فعال‌سازی"}
        </button>
        <button class="btn btn-soft btn-sm" data-act="revoke" data-id="${esc(u.id)}">قطع نشست</button>
      </td>
    </tr>`;
  }).join("");

  contentEl.innerHTML = `
    ${pageHead("پنل ادمین", "مدیریت کاربران، نقش‌ها و نشست‌ها")}
    <div class="card" style="margin-bottom:1rem">
      <div style="display:flex;gap:1.5rem;flex-wrap:wrap">
        <div><div class="stat-value" style="font-size:1.4rem">${st.total ?? 0}</div><div class="stat-label">کل کاربران</div></div>
        <div><div class="stat-value" style="font-size:1.4rem">${st.admins ?? 0}</div><div class="stat-label">ادمین</div></div>
        <div><div class="stat-value" style="font-size:1.4rem">${st.inactive ?? 0}</div><div class="stat-label">غیرفعال</div></div>
      </div>
    </div>
    <div class="card" style="overflow:auto">
      <table class="table" style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="text-align:right;border-bottom:1px solid var(--glass-border)">
            <th style="padding:.6rem">کاربر</th>
            <th>نقش</th>
            <th>وضعیت</th>
            <th>آخرین ورود</th>
            <th>نشست</th>
            <th>عملیات</th>
          </tr>
        </thead>
        <tbody>${rows || '<tr><td colspan="6" style="padding:1rem;opacity:.7">هنوز کاربری نیست</td></tr>'}</tbody>
      </table>
    </div>
    <p style="margin-top:1rem;font-size:.85rem;opacity:.75">
      ادمین‌های اولیه را با متغیر محیطی <code>LMS_ADMIN_USERNAMES</code> (لیست شماره‌دانشجویی جدا با ویرگول) مشخص کنید.
      اگر خالی باشد، اولین کاربر لاگین‌شده به‌صورت خودکار ادمین می‌شود.
    </p>
  `;


  // --- بخش پشتیبانی ادمین ---
  let ticketsData = { tickets: [] };
  try {
    ticketsData = await api("/support/admin/tickets");
  } catch (_) {}
  const trows = (ticketsData.tickets || []).map((tk) => `
    <tr>
      <td>
        <div style="font-weight:600">${esc(tk.subject)}</div>
        <div style="font-size:.8rem;opacity:.7">${esc(tk.full_name || "")} · ${esc(tk.lms_username || "")}</div>
      </td>
      <td><span class="badge">${esc(tk.status)}</span></td>
      <td style="font-size:.85rem;direction:ltr;text-align:right">${esc(tk.updated_at || "")}</td>
      <td>
        <button class="btn btn-soft btn-sm" data-open-ticket="${esc(tk.id)}">مشاهده / پاسخ</button>
      </td>
    </tr>
  `).join("");

  contentEl.insertAdjacentHTML("beforeend", `
    <div class="card" style="margin-top:1.5rem">
      <h3 style="margin:0 0 .75rem">تیکت‌های پشتیبانی</h3>
      <div style="overflow:auto">
        <table class="table" style="width:100%;border-collapse:collapse">
          <thead><tr style="text-align:right;border-bottom:1px solid var(--glass-border)">
            <th style="padding:.5rem">موضوع</th><th>وضعیت</th><th>به‌روزرسانی</th><th></th>
          </tr></thead>
          <tbody>${trows || '<tr><td colspan="4" style="padding:1rem;opacity:.7">تیکتی نیست</td></tr>'}</tbody>
        </table>
      </div>
      <div id="admin-ticket-thread" class="hidden" style="margin-top:1rem"></div>
    </div>
  `);

  async function adminOpenTicket(id) {
    const data = await api(`/support/tickets/${encodeURIComponent(id)}`);
    const box = $("#admin-ticket-thread");
    box.classList.remove("hidden");
    const msgs = (data.messages || []).map(m => `
      <div style="padding:.6rem;margin:.4rem 0;border-radius:10px;background:${m.is_staff ? "rgba(42,166,163,.12)" : "var(--glass-bg-soft)"}">
        <div style="font-size:.75rem;opacity:.75">${esc(m.author_name)} · ${esc(m.created_at)}</div>
        <div style="white-space:pre-wrap">${esc(m.body)}</div>
      </div>`).join("");
    box.innerHTML = `
      <h4>${esc(data.ticket.subject)}</h4>
      ${msgs}
      <form id="admin-reply" style="display:flex;flex-direction:column;gap:.5rem;margin-top:.5rem">
        <textarea id="admin-reply-body" class="input" rows="3" placeholder="پاسخ پشتیبانی…" required></textarea>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap">
          <button type="submit" class="btn btn-primary">ارسال پاسخ</button>
          <button type="button" class="btn btn-soft" data-close-ticket="${esc(id)}">بستن تیکت</button>
        </div>
      </form>`;
    $("#admin-reply").addEventListener("submit", async (e) => {
      e.preventDefault();
      const body = $("#admin-reply-body").value.trim();
      await api(`/support/tickets/${encodeURIComponent(id)}/messages`, {
        method: "POST", body: JSON.stringify({ body }),
      });
      toast("پاسخ ارسال شد");
      await adminOpenTicket(id);
    });
    box.querySelector("[data-close-ticket]")?.addEventListener("click", async () => {
      await api(`/support/admin/tickets/${encodeURIComponent(id)}/status`, {
        method: "PATCH", body: JSON.stringify({ status: "closed" }),
      });
      toast("تیکت بسته شد");
      await renderAdmin();
    });
  }

  contentEl.querySelectorAll("[data-open-ticket]").forEach((btn) => {
    btn.addEventListener("click", () => adminOpenTicket(btn.dataset.openTicket));
  });


  // --- ops: maintenance / backup / audit ---
  let sys = { maintenance: false, maintenance_message: "" };
  try { sys = await api("/admin/system"); } catch (_) {}
  let audit = { items: [] };
  try { audit = await api("/admin/audit?limit=20"); } catch (_) {}

  contentEl.insertAdjacentHTML("beforeend", `
    <div class="card" style="margin-top:1.5rem">
      <h3 style="margin:0 0 .75rem">عملیات سیستم</h3>
      <div style="display:flex;flex-wrap:wrap;gap:.75rem;align-items:center;margin-bottom:1rem">
        <label style="display:flex;align-items:center;gap:.4rem">
          <input type="checkbox" id="maint-toggle" ${sys.maintenance ? "checked" : ""} />
          حالت تعمیرات (Maintenance)
        </label>
        <input id="maint-msg" class="input" style="flex:1;min-width:180px" placeholder="پیام برای کاربران" value="${esc(sys.maintenance_message || "")}" />
        <button class="btn btn-soft btn-sm" id="btn-maint-save">ذخیره</button>
        <button class="btn btn-primary btn-sm" id="btn-backup" data-admin-backup>بکاپ دیتابیس</button>
      </div>
      <div id="backup-result" style="font-size:.85rem;opacity:.85;margin-bottom:1rem"></div>
      <h4 style="margin:0 0 .5rem">آخرین اقدامات ادمین</h4>
      <div style="overflow:auto;max-height:240px">
        <table class="table" style="width:100%;border-collapse:collapse;font-size:.85rem">
          <thead><tr style="text-align:right;border-bottom:1px solid var(--glass-border)">
            <th style="padding:.35rem">زمان</th><th>عمل</th><th>بازیگر</th><th>جزئیات</th>
          </tr></thead>
          <tbody>
            ${(audit.items || []).map(it => `
              <tr>
                <td style="direction:ltr;text-align:right;padding:.35rem">${esc(it.created_at || "")}</td>
                <td>${esc(it.action)}</td>
                <td>${esc(it.actor_name || it.actor_username || "")}</td>
                <td style="opacity:.8">${esc(it.detail || it.target_user_id || "")}</td>
              </tr>`).join("") || '<tr><td colspan="4" style="padding:.5rem;opacity:.7">هنوز لاگی نیست</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
  `);

  $("#btn-maint-save")?.addEventListener("click", async () => {
    try {
      await api("/admin/system/maintenance", {
        method: "POST",
        body: JSON.stringify({
          enabled: !!$("#maint-toggle")?.checked,
          message: $("#maint-msg")?.value || "",
        }),
      });
      toast("وضعیت تعمیرات ذخیره شد");
    } catch (e) {
      toast("❌ " + (e.message || "خطا"));
    }
  });
  $("#btn-backup")?.addEventListener("click", async () => {
    try {
      const r = await api("/admin/backup", { method: "POST", body: "{}" });
      const box = $("#backup-result");
      if (box) {
        box.innerHTML = `بکاپ آماده: <code>${esc(r.filename)}</code> (${r.size_bytes} بایت)
          — <a href="${esc(r.download)}" target="_blank" rel="noopener">دانلود</a>`;
      }
      toast("✅ بکاپ ساخته شد");
    } catch (e) {
      toast("❌ " + (e.message || "خطا در بکاپ"));
    }
  });

  contentEl.querySelectorAll("[data-act]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const act = btn.dataset.act;
      btn.disabled = true;
      try {
        if (act === "role") {
          await api(`/admin/users/${encodeURIComponent(id)}/role`, {
            method: "PATCH",
            body: JSON.stringify({ role: btn.dataset.role }),
          });
          toast("نقش به‌روز شد");
        } else if (act === "active") {
          await api(`/admin/users/${encodeURIComponent(id)}/active`, {
            method: "PATCH",
            body: JSON.stringify({ active: btn.dataset.active === "1" }),
          });
          toast("وضعیت حساب به‌روز شد");
        } else if (act === "revoke") {
          await api(`/admin/users/${encodeURIComponent(id)}/revoke-sessions`, {
            method: "POST",
            body: "{}",
          });
          toast("نشست‌های کاربر قطع شد");
        }
        await renderAdmin();
      } catch (e) {
        toast("❌ " + (e.message || "خطا"));
        btn.disabled = false;
      }
    });
  });
}

async function renderMore() {
  const cards = [
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

async function renderMap() {
  const locations = await api("/map/locations");

  if (!locations.length) {
    contentEl.innerHTML = emptyState("مکانی برای نمایش وجود ندارد", "ابتدا دروس خود را همگام‌سازی کنید.");
    return;
  }

  contentEl.innerHTML = `
    ${pageHead("نقشه مکان‌های کلاس", "نمای کلی تمام ساختمان‌هایی که در آن‌ها کلاس دارید")}
    
    <div class="card" style="padding: 0; overflow: hidden; height: 600px; border-radius: var(--radius);">
      <div id="main-map" style="width: 100%; height: 100%;"></div>
    </div>
    
    <div class="grid-2" style="margin-top: 1rem;">
      ${locations.map(loc => `
        <div class="card" style="display: flex; flex-direction: column; gap: 0.5rem;">
          <div style="font-weight: 700; font-size: 1.1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            📍 ${esc(loc.name)}
          </div>
          <div class="muted">${esc(loc.building)}</div>
          <div style="margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem;">
            ${loc.courses.map(c => `<span class="badge badge-domain">${esc(c)}</span>`).join("")}
          </div>
          <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">
            <a href="https://nshn.ir/?lat=${loc.lat}&lng=${loc.lng}" target="_blank" rel="noopener" class="btn-primary-glass btn-sm">🧭 نشان</a>
            <a href="https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}" target="_blank" rel="noopener" class="btn-glass btn-sm">🗺 گوگل مپ</a>
          </div>
        </div>
      `).join("")}
    </div>
  `;

  // رندر نقشه
  setTimeout(() => {
    const mapEl = document.getElementById("main-map");
    if (mapEl) {
      const map = L.map(mapEl, {
        zoomControl: true,
        attributionControl: false
      }).setView([32.6072163, 51.6583164], 15);

      // فقط OpenStreetMap (بدون API key). تم تیره با فیلتر CSS.
      const isDark = document.body.dataset.theme === "dark";
      if (isDark) mapEl.classList.add("map-dark-tiles");
      else mapEl.classList.remove("map-dark-tiles");

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      // آیکون سفارشی برای مارکرها (به جای آیکون پیش‌فرض آبی)
      const customIcon = L.divIcon({
        className: 'custom-map-icon',
        html: `<div style="background-color:var(--primary); width:16px; height:16px; border-radius:50%; border:3px solid white; box-shadow:0 0 10px rgba(0,0,0,0.5);"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      // افزودن مارکر برای هر مکان
            // افزودن مارکر برای هر مکان
      locations.forEach(loc => {
        const marker = L.marker([loc.lat, loc.lng], { icon: customIcon }).addTo(map);

        // ساخت لیست دروس با ظاهر بهتر
        const coursesHtml = loc.courses.map(c =>
          `<div style="margin-top:6px; font-size:13px; display:flex; align-items:center; gap:6px;">
             <span style="opacity:0.7;">📚</span> <span>${esc(c)}</span>
           </div>`
        ).join("");

        marker.bindPopup(`
          <div style="direction: rtl; text-align: right; font-family: 'Vazirmatn', sans-serif;">
            <div style="font-weight: 800; font-size: 15px; margin-bottom: 4px; color: var(--primary);">
              📍 ${esc(loc.name)}
            </div>
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 8px;">
              ${esc(loc.building)}
            </div>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid var(--glass-border);">
            ${coursesHtml}
          </div>
        `);
      });
    }
  }, 200);
}

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
  const rows = [
    ["courses", "درس‌ها", "لیست و جزئیات درس‌ها"],
    ["contents", "محتواها", "فایل‌ها و منابع"],
    ["events", "رویدادها", "جلسات و آزمون‌ها"],
    ["wall", "وال (پیام‌ها و تکالیف)", "گفتگوها و مهلت‌ها"],
    ["members", "اعضای درس‌ها", "اساتید و دانشجویان"],
  ].map(([key, label, desc]) => `
    <div class="setting-row">
      <div class="setting-info"><span>${label}</span><small>${desc}</small></div>
      <label class="switch">
        <input type="checkbox" data-key="${key}" ${sync[key] ? "checked" : ""}/>
        <span class="slider"></span>
      </label>
    </div>`).join("");

  contentEl.innerHTML = `
    ${pageHead("تنظیمات", "پیکربندی همگام‌سازی و حساب کاربری")}
    <div class="card">
      <div class="card-head"><h3 class="section-title">🔄 فازهای همگام‌سازی</h3></div>
      ${rows}
      <button class="btn btn-primary" style="margin-top:1rem" onclick="saveSyncSettings()">ذخیره تنظیمات</button>
    </div>
    <div class="card">
      <div class="card-head"><h3 class="section-title">🔐 حساب کاربری</h3></div>
      <p class="muted" style="margin-bottom:.8rem">برای تغییر شماره دانشجویی یا رمز عبور، دوباره وارد شوید.</p>
      <button class="btn btn-soft" onclick="showLogin()">تغییر حساب / ورود مجدد</button>
    </div>`;
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

let calState = null;

function calEventKey(j) { return `${j.jy}-${j.jm}-${j.jd}`; }

function calRender() {
  const s = calState;
  if (!s) return;
  const title = document.getElementById("cal-title");
  if (title) title.textContent = `${J_MONTHS[s.jm - 1]} ${faDigits(s.jy)}`;

  const grid = document.getElementById("cal-grid");
  if (!grid) return;
  const firstJdn = j2d(s.jy, s.jm, 1);
  const startWd = jWeekday(firstJdn);
  const len = jMonthLen(s.jy, s.jm);
  let cells = "";
  for (let i = 0; i < startWd; i++) cells += `<div class="cal-cell cal-other"></div>`;
  for (let d = 1; d <= len; d++) {
    const key = `${s.jy}-${s.jm}-${d}`;
    const evs = s.eventsByDay.get(key) || [];
    const cls = ["cal-cell"];
    if (key === s.todayKey) cls.push("cal-today");
    if (key === s.sel) cls.push("cal-selected");
    if (evs.length) cls.push("cal-has");
    const chips = evs.slice(0, 2).map((e) => {
      const t = EVENT_TYPES[e.event_type] || EVENT_TYPES.unknown;
      return `<button class="cal-chip ${t.chipCls}" title="${esc(e.title)}" onclick="openCalEvent('${esc(e.id)}')">${esc(e.title)}</button>`;
    }).join("");
    const more = evs.length > 2 ? `<span class="cal-more">+${evs.length - 2} مورد</span>` : "";
    cells += `<div class="${cls.join(" ")}" onclick="calSelect('${key}')">
      <span class="cal-day-num">${faDigits(d)}</span>${chips}${more}
    </div>`;
  }
  grid.innerHTML = cells;
  calRenderDay();
}

function calRenderDay() {
  const s = calState;
  const card = document.getElementById("cal-day-card");
  if (!card) return;
  const [y, m, d] = s.sel.split("-").map(Number);
  const evs = s.eventsByDay.get(s.sel) || [];
  const g = d2g(j2d(y, m, d));
  const dateLabel = `${faDigits(d)} ${J_MONTHS[m - 1]} ${faDigits(y)}`;
  const gLabel = `${faDigits(g.gy)}/${faDigits(g.gm)}/${faDigits(g.gd)}`;
  const isToday = s.sel === s.todayKey;
  card.innerHTML = `
    <div class="card-head">
      <h3 class="section-title">📅 ${dateLabel} ${isToday ? '<span class="badge badge-new">امروز</span>' : ""}</h3>
      <span class="muted">${gLabel} میلادی</span>
    </div>
    <div class="item-list">
      ${evs.length ? evs.map((e) => {
        const t = EVENT_TYPES[e.event_type] || EVENT_TYPES.unknown;
        const hm = e.start_at ? String(e.start_at).slice(11, 16) : "";
        return `<div class="list-row">
          <span class="row-icon">${t.icon}</span>
          <div class="row-body">
            <div class="row-title">${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>` : esc(e.title)}
              <span class="badge ${t.cls}">${t.label}</span>
            </div>
            <div class="row-meta">
              ${hm ? `<span>⏰ ${esc(hm)}</span>` : ""}
              ${e.description ? `<span>${esc(e.description)}</span>` : ""}
            </div>
          </div>
        </div>`;
      }).join("") : `<div class="empty"><span class="empty-icon">🗓️</span>رویدادی در این روز نیست</div>`}
    </div>`;

  const nc = document.getElementById("cal-nodate-card");
  if (nc) {
    nc.innerHTML = `
      <div class="card-head"><h3 class="section-title">🗂 رویدادهای بدون تاریخ (${s.noDate.length})</h3></div>
      <div class="item-list">
        ${s.noDate.map((e) => {
          const t = EVENT_TYPES[e.event_type] || EVENT_TYPES.unknown;
          return `<div class="list-row">
            <span class="row-icon">${t.icon}</span>
            <div class="row-body">
              <div class="row-title">${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>` : esc(e.title)}
                <span class="badge ${t.cls}">${t.label}</span>
              </div>
            </div>
          </div>`;
        }).join("")}
      </div>`;
  }
}

// ---------- تقویم هفتگی افقی (Liquid Glass Desktop Style) ----------

let currentWeekOffset = 0;
let selectedDayJdn = null;


  // --- حساب من ---
  const accountCard = document.createElement("div");
  accountCard.className = "card";
  accountCard.style.marginTop = "1.5rem";
  accountCard.innerHTML = `
    <h3 style="margin:0 0 .75rem">حساب من</h3>
    <p style="opacity:.85;font-size:.9rem;margin:0 0 .75rem">خروج از همه دستگاه‌ها، دریافت کپی داده، یا حذف کامل حساب.</p>
    <div style="display:flex;flex-wrap:wrap;gap:.5rem">
      <button type="button" class="btn btn-soft btn-sm" id="btn-revoke-sessions">خروج از همه نشست‌ها</button>
      <a class="btn btn-soft btn-sm" href="/api/account/export" download="lms-my-data.json" data-account-export>⬇ خروجی داده (JSON)</a>
      <button type="button" class="btn btn-soft btn-sm" id="btn-delete-account" style="color:var(--danger)">حذف حساب</button>
    </div>
  `;
  contentEl.appendChild(accountCard);
  document.getElementById("btn-revoke-sessions")?.addEventListener("click", async () => {
    if (!confirm("از همه دستگاه‌ها خارج می‌شوید. ادامه؟")) return;
    try {
      await api("/account/sessions/revoke-all", { method: "POST", body: "{}" });
      toast("همه نشست‌ها قطع شد");
      location.reload();
    } catch (e) {
      toast("❌ " + (e.message || "خطا"));
    }
  });
  document.getElementById("btn-delete-account")?.addEventListener("click", async () => {
    if (!confirm("همه داده‌های شما برای همیشه حذف می‌شود. مطمئنید؟")) return;
    if (!confirm("این عمل برگشت‌پذیر نیست. حذف حساب؟")) return;
    try {
      await api("/account", { method: "DELETE" });
      toast("حساب حذف شد");
      location.hash = "#/";
      location.reload();
    } catch (e) {
      toast("❌ " + (e.message || "خطا"));
    }
  });


async function renderCalendar() {
  const [events, assignments] = await Promise.all([
    api("/events"),
    api("/assignments")
  ]);

  const now = new Date();
  const todayJ = d2j(g2d(now.getFullYear(), now.getMonth() + 1, now.getDate()));

  const currentWeekday = jWeekday(j2d(todayJ.jy, todayJ.jm, todayJ.jd));
  const startOfWeekJdn = j2d(todayJ.jy, todayJ.jm, todayJ.jd) - currentWeekday + (currentWeekOffset * 7);

  if (selectedDayJdn === null || currentWeekOffset === 0 && selectedDayJdn < startOfWeekJdn) {
    selectedDayJdn = j2d(todayJ.jy, todayJ.jm, todayJ.jd);
  }

  const weekDays = [];
  for (let i = 0; i < 7; i++) {
    const jdn = startOfWeekJdn + i;
    const j = d2j(jdn);
    const g = d2g(jdn);
    const gDateStr = `${g.gy}-${String(g.gm).padStart(2,'0')}-${String(g.gd).padStart(2,'0')}`;

    // 👇 ۱. فیلتر رویدادها (دستی) و تکالیف
    const dayManualEvents = events.filter(e => e.start_at && e.start_at.startsWith(gDateStr));

    // 👇 ۲. جدا کردن تکالیف LMS و کوئرا
    const dayAssignments = assignments.filter(a =>
      a.source === "lms" && a.deadline && a.deadline.startsWith(gDateStr)
    );
    const dayQueraAssignments = assignments.filter(a =>
      a.source === "quera" && a.deadline && a.deadline.startsWith(gDateStr)
    );

    // 👇 ۳. دسته‌بندی رویدادهای دستی
    const manualExams = dayManualEvents.filter(e => e.event_type === "exam");
    const manualAssignments = dayManualEvents.filter(e => e.event_type === "assignment");

    // 👇 ۴. بررسی وجود آزمون/تکلیف/کوئرا
    const hasExam = manualExams.length > 0;
    const hasAssignment = dayAssignments.length > 0 || manualAssignments.length > 0;
    const hasQuera = dayQueraAssignments.length > 0;

    weekDays.push({
      jdn, j, g, gDateStr,
      manualEvents: dayManualEvents,
      assignments: dayAssignments,
      queraAssignments: dayQueraAssignments,
      manualExams,
      manualAssignments,
      hasExam,
      hasAssignment,
      hasQuera,
      isToday: jdn === j2d(todayJ.jy, todayJ.jm, todayJ.jd),
      isSelected: jdn === selectedDayJdn
    });
  }

  const weekdaysNames = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"];
  const startJ = weekDays[0].j;
  const endJ = weekDays[6].j;
  const weekTitle = `${faDigits(startJ.jd)} ${J_MONTHS[startJ.jm - 1]} تا ${faDigits(endJ.jd)} ${J_MONTHS[endJ.jm - 1]} ${faDigits(endJ.jy)}`;

  const selectedDayData = weekDays.find(d => d.isSelected) || weekDays[0];

  // 👇 ساخت HTML
  contentEl.innerHTML = `
    ${pageHead("تقویم هفتگی", "مهلت تکالیف و رویدادها")}
    <div class="card" style="margin-bottom:1rem;display:flex;justify-content:space-between;gap:1rem;align-items:center;flex-wrap:wrap">
      <div style="opacity:.85;font-size:.9rem">خروجی ICS برای Google Calendar یا تقویم گوشی</div>
      <a class="btn btn-primary btn-sm" href="/api/calendar.ics" download="lms-assistant.ics">⬇ دانلود ICS</a>
    </div>
    <div class="filter-bar" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
      <div style="display:flex; gap:0.5rem;">
        <button class="btn-glass" onclick="changeWeek(-1)" style="padding: 0.5rem 1rem; border-radius: 999px;">‹ هفته قبل</button>
        <button class="btn-primary-glass" onclick="changeWeek(0)" style="padding: 0.5rem 1.2rem; border-radius: 999px;">امروز</button>
        <button class="btn-glass" onclick="changeWeek(1)" style="padding: 0.5rem 1rem; border-radius: 999px;">هفته بعد ›</button>
      </div>
      <h3 style="font-size: 1.1rem; font-weight: 700; display:flex; align-items:center; gap:0.5rem;">
        📅 ${weekTitle}
      </h3>
    </div>

    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.5rem; margin-bottom: 1.5rem;">
      ${weekDays.map((day, idx) => {
        let cardStyle = "padding: 1rem 0.5rem; text-align: center; cursor: pointer; transition: all 0.3s; border-radius: var(--radius-sm); backdrop-filter: blur(16px) saturate(150%); -webkit-backdrop-filter: blur(16px) saturate(150%); position: relative; overflow: hidden;";
        
        // 👇 استایل‌های گرادیانتی شیشه‌ای
        if (day.isSelected) {
          cardStyle += " border: 2px solid var(--primary); background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.05) 100%); transform: translateY(-2px); box-shadow: 0 4px 15px var(--ring), inset 0 1px 0 var(--glass-hi);";
        } else if (day.hasExam && (day.hasAssignment || day.hasQuera)) {
          cardStyle += " border: 1px solid rgba(245, 158, 11, 0.5); background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(239, 68, 68, 0.15) 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);";
        } else if (day.hasExam) {
          cardStyle += " border: 1px solid rgba(245, 158, 11, 0.5); background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);";
        } else if (day.hasAssignment) {
          cardStyle += " border: 1px solid rgba(239, 68, 68, 0.5); background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.05) 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);";
        } else if (day.hasQuera) {
          cardStyle += " border: 1px solid rgba(42, 166, 163, 0.5); background: linear-gradient(135deg, rgba(42, 166, 163, 0.2) 0%, rgba(42, 166, 163, 0.05) 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);";
        } else if (day.isToday) {
          cardStyle += " border: 1px solid var(--primary); background: rgba(59, 130, 246, 0.05);";
        } else {
          cardStyle += " border: 1px solid var(--glass-border); background: var(--glass-bg-soft);";
        }

        const examCount = day.manualExams.length;
        const deadlineCount = day.assignments.length + day.manualAssignments.length;
        const queraCount = day.queraAssignments.length;

        return `
          <div class="card" style="${cardStyle}" onclick="selectDay(${day.jdn})">
            <div class="day-add-btn" onclick="event.stopPropagation(); openAddEventModal('${day.gDateStr}')" title="افزودن رویداد">+</div>

            ${day.isToday ? '<span class="badge badge-new" style="font-size:0.6rem; padding:2px 6px; margin-bottom:4px;">امروز</span>' : '<div style="height:18px;"></div>'}
            <div style="font-weight: 800; font-size: 1rem; color: var(--text-primary); margin-top:4px;">${weekdaysNames[idx]}</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: ${day.hasExam ? 'var(--warning)' : (day.hasAssignment ? 'var(--danger)' : (day.hasQuera ? 'var(--primary)' : (day.isSelected ? 'var(--primary)' : 'var(--text)'))) }; margin: 0.2rem 0; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">${faDigits(day.j.jd)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${J_MONTHS[day.j.jm - 1]}</div>
            
            <div style="margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.2rem; align-items: center;">
              ${examCount > 0 ? `
                <div class="badge" style="font-size: 0.65rem; background: var(--warning-soft); color: var(--warning); box-shadow: 0 2px 8px var(--warning-soft); border: 1px solid var(--warning);">
                  ${faDigits(examCount)} آزمون
                </div>
              ` : ""}
              ${deadlineCount > 0 ? `
                <div class="badge badge-expired" style="font-size: 0.65rem; box-shadow: 0 2px 8px var(--danger-soft);">
                  ${faDigits(deadlineCount)} ددلاین
                </div>
              ` : ""}
              ${queraCount > 0 ? `
                <div class="badge" style="font-size: 0.65rem; background: var(--primary-soft); color: var(--primary); box-shadow: 0 2px 8px var(--primary-soft); border: 1px solid var(--primary);">
                  ${faDigits(queraCount)} کوئرا
                </div>
              ` : ""}
            </div>
          </div>
        `;
      }).join("")}
    </div>

    <!-- کارت جزئیات روز انتخاب شده -->
    <div class="card" style="padding: 1.5rem; background: var(--glass-bg); border: 1px solid var(--glass-border); box-shadow: var(--glass-shadow); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);">
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid var(--glass-border); padding-bottom: 1rem; margin-bottom: 1rem;">
        <h3 style="font-size: 1.1rem; font-weight: 800; color: var(--primary);">
          ${weekdaysNames[jWeekday(selectedDayJdn)]} — ${faDigits(selectedDayData.j.jd)} ${J_MONTHS[selectedDayData.j.jm - 1]} ${faDigits(selectedDayData.j.jy)}
        </h3>
        <span class="badge badge-domain">${faDigits(selectedDayData.manualEvents.length + selectedDayData.assignments.length + selectedDayData.queraAssignments.length)} مورد</span>
      </div>

      <div class="item-list">
        ${selectedDayData.manualEvents.length || selectedDayData.assignments.length || selectedDayData.queraAssignments.length ? [
          // 👇 رویدادهای دستی: آزمون‌ها
          ...selectedDayData.manualExams.map(e => {
            const hm = e.start_at ? String(e.start_at).slice(11, 16) : "";
            return `
              <div class="list-row" style="margin-bottom: 0.8rem; border-radius: 12px; border-color: var(--warning-soft);">
                <span class="row-icon" style="background: var(--warning-soft); color: var(--warning); font-size:1.2rem;">📄</span>
                <div class="row-body">
                  <div class="row-title">
                    ${esc(e.title)}
                    <span class="badge badge-warn">آزمون</span>
                  </div>
                  <div class="row-meta">
                    ${hm ? `<span class="badge badge-info" style="padding: 0.2rem 0.6rem;">⏰ ${hm}</span>` : ""}
                    <span class="badge badge-domain">${esc(e.course_name || "عمومی")}</span>
                    ${e.description ? `<span>${esc(e.description)}</span>` : ""}
                  </div>
                </div>
              </div>
            `;
          }),
          // 👇 رویدادهای دستی: تکالیف
          ...selectedDayData.manualAssignments.map(e => {
            const hm = e.start_at ? String(e.start_at).slice(11, 16) : "";
            return `
              <div class="list-row" style="margin-bottom: 0.8rem; border-radius: 12px; border-color: var(--danger-soft);">
                <span class="row-icon" style="background: var(--danger-soft); color: var(--danger); font-size:1.2rem;">📝</span>
                <div class="row-body">
                  <div class="row-title">
                    ${esc(e.title)}
                    <span class="badge badge-expired">تکلیف دستی</span>
                  </div>
                  <div class="row-meta">
                    ${hm ? `<span class="badge badge-info" style="padding: 0.2rem 0.6rem;">⏰ ${hm}</span>` : ""}
                    <span class="badge badge-domain">${esc(e.course_name || "عمومی")}</span>
                    ${e.description ? `<span>${esc(e.description)}</span>` : ""}
                  </div>
                </div>
              </div>
            `;
          }),
          // 👇 تکالیف LMS
          ...selectedDayData.assignments.map(a => `
            <div class="list-row" style="margin-bottom: 0.8rem; border-radius: 12px; border-color:var(--warning-soft);">
              <span class="row-icon" style="background: var(--warning-soft); color: var(--warning); font-size:1.2rem;">📝</span>
              <div class="row-body">
                <div class="row-title">
                  ${esc(a.title)}
                  <span class="badge badge-warn">مهلت تحویل</span>
                </div>
                <div class="row-meta">
                  ${a.deadline ? `<span class="badge badge-expired" style="padding: 0.2rem 0.6rem;">⏰ ${String(a.deadline).slice(11, 16)}</span>` : ""}
                  <span class="badge badge-domain">${esc(a.course_name || "درس نامشخص")}</span>
                </div>
              </div>
            </div>
          `),
          // 👇 تکالیف کوئرا
          ...selectedDayData.queraAssignments.map(qa => `
            <div class="list-row" style="margin-bottom: 0.8rem; border-radius: 12px; border-color:var(--primary-soft);">
              <span class="row-icon" style="background: var(--primary-soft); color: var(--primary); font-size:1.2rem;">🎯</span>
              <div class="row-body">
                <div class="row-title">
                  ${esc(qa.title)}
                  <span class="badge" style="background: var(--primary-soft); color: var(--primary);">کوئرا</span>
                </div>
                <div class="row-meta">
                  ${qa.deadline ? `<span class="badge badge-expired" style="padding: 0.2rem 0.6rem;">⏰ ${String(qa.deadline).slice(11, 16)}</span>` : ""}
                  <span class="badge badge-domain">${esc(qa.course_name)}</span>
                </div>
              </div>
            </div>
          `)
        ].join("") : `<div class="empty muted" style="padding: 2rem 0;">رویداد یا تکلیفی در این روز نیست.</div>`}
      </div>
    </div>
  `;
}
window.changeWeek = (offset) => {
  if (offset === 0) {
    currentWeekOffset = 0;
    const now = new Date();
    const todayJ = d2j(g2d(now.getFullYear(), now.getMonth() + 1, now.getDate()));
    selectedDayJdn = j2d(todayJ.jy, todayJ.jm, todayJ.jd);
  } else {
    currentWeekOffset += offset;
    const now = new Date();
    const todayJ = d2j(g2d(now.getFullYear(), now.getMonth() + 1, now.getDate()));
    const currentWeekday = jWeekday(j2d(todayJ.jy, todayJ.jm, todayJ.jd));
    selectedDayJdn = j2d(todayJ.jy, todayJ.jm, todayJ.jd) - currentWeekday + (currentWeekOffset * 7);
  }
  renderCalendar();
};

window.selectDay = (jdn) => {
  selectedDayJdn = jdn;
  renderCalendar();
};

window.calSelect = (key) => {
  if (!calState) return;
  calState.sel = key;
  calRender();
};

window.calShift = (delta) => {
  if (!calState) return;
  let m = calState.jm + delta, y = calState.jy;
  if (m > 12) { m = 1; y += 1; }
  if (m < 1) { m = 12; y -= 1; }
  calState.jy = y;
  calState.jm = m;
  calState.sel = `${y}-${m}-1`;
  calRender();
};

window.calToday = () => {
  if (!calState) return;
  const now = new Date();
  const j = d2j(g2d(now.getFullYear(), now.getMonth() + 1, now.getDate()));
  calState.jy = j.jy;
  calState.jm = j.jm;
  calState.sel = calEventKey(j);
  calRender();
};

window.openCalEvent = (id) => {
  if (!calState) return;
  const all = [];
  calState.eventsByDay.forEach((v) => all.push(...v));
  all.push(...calState.noDate);
  const e = all.find((x) => x.id === id);
  if (e && e.url) window.open(e.url, "_blank", "noopener");
};

// ---------- Router ----------

function currentRoute() {
  const hash = location.hash.replace(/^#\/?/, "");
  return hash || "dashboard";
}

function setPageTitle(route) {
  const page = route.startsWith("course/") ? "course" : route;
  $("#page-title").textContent =
    TITLES[route] || (route.startsWith("course/") ? "جزئیات درس" : "داشبورد");
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
    $("#btn-theme").textContent = saved === "dark" ? "☀️" : "🌙";
  } else {
    try {
      const t = await api("/settings/theme");
      if (t.theme) {
        document.body.dataset.theme = t.theme;
        $("#btn-theme").textContent = t.theme === "dark" ? "☀️" : "🌙";
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

window.openAddEventModal = async (dateStr) => {
  // ۱. دریافت لیست دروس از سرور
  let courses = [];
  try {
    courses = await api("/courses");
  } catch (e) {
    toast("خطا در دریافت لیست دروس");
  }

  // ساخت آیتم‌های منوی دروس
  const courseItems = courses.map(c =>
    `<a href="#" class="dropdown-item" onclick="setEventCourse(event, '${c.id}', '${esc(c.name)}')">${esc(c.name)}</a>`
  ).join("");

  const [gy, gm, gd] = dateStr.split('-').map(Number);
  const j = d2j(g2d(gy, gm, gd));
  const dateLabel = `${faDigits(j.jd)} ${J_MONTHS[j.jm - 1]} ${faDigits(j.jy)}`;

  const spacerTop = `<div style="height: 60px; flex-shrink: 0;"></div>`;
  const spacerBottom = `<div style="height: 60px; flex-shrink: 0;"></div>`;

  const hoursHtml = spacerTop + Array.from({length: 24}).map((_, i) => {
    const val = String(i).padStart(2, '0');
    return `<div class="wheel-item" data-val="${val}">${faDigits(i)}</div>`;
  }).join("") + spacerBottom;

  const minutesHtml = spacerTop + Array.from({length: 60}).map((_, i) => {
    const val = String(i).padStart(2, '0');
    return `<div class="wheel-item" data-val="${val}">${faDigits(i)}</div>`;
  }).join("") + spacerBottom;

  const modalHtml = `
    <div id="add-event-modal" class="modal-overlay" style="display:flex; z-index: 1000;">
      <div class="modal" style="max-width: 420px; overflow: visible;">
        <button class="modal-close" onclick="document.getElementById('add-event-modal').remove()">✕</button>
        <div class="modal-head" style="margin-bottom: 1rem;">
          <h3>افزودن رویداد جدید</h3>
          <p class="muted">تاریخ: ${dateLabel}</p>
        </div>
        
        <form id="add-event-form" onsubmit="submitManualEvent(event, '${dateStr}')">
          
          <!-- 👇 منوی انتخاب درس -->
          <div class="field" style="margin-bottom: 1rem; position: relative;">
            <label>درس مربوطه</label>
            <div class="custom-dropdown" id="dd-course-modal" style="width: 100%;">
              <button type="button" class="filter-btn glass-input" style="width: 100%; justify-content: space-between;" onclick="toggleModalDropdown('dd-course-modal')">
                <span id="selected-course-label">-- انتخاب درس --</span>
                <span>▼</span>
              </button>
              <div class="dropdown-menu" style="width: 100%; max-height: 200px; overflow-y: auto; z-index: 10000;">
                ${courseItems}
              </div>
            </div>
            <input type="hidden" id="event-course" value="" />
          </div>

          <div class="field">
            <label>عنوان</label>
            <input type="text" id="event-title" required placeholder="مثلاً: مطالعه فصل ۳" class="glass-input" />
          </div>

          <div class="field" style="margin-top: 1rem; position: relative;">
            <label>نوع</label>
            <div class="custom-dropdown" id="dd-type-modal" style="width: 100%;">
              <button type="button" class="filter-btn glass-input" style="width: 100%; justify-content: space-between;" onclick="toggleModalDropdown('dd-type-modal')">
                <span id="selected-type-label">📝 تکلیف / کار</span>
                <span>▼</span>
              </button>
              <div class="dropdown-menu" style="width: 100%; z-index: 10000;">
                <a href="#" class="dropdown-item active" onclick="setEventType(event, 'assignment', '📝 تکلیف / کار')">📝 تکلیف / کار</a>
                <a href="#" class="dropdown-item" onclick="setEventType(event, 'exam', '📄 آزمون')">📄 آزمون</a>
              </div>
            </div>
            <input type="hidden" id="event-type" value="assignment" />
          </div>

          <div class="field" style="margin-top: 1rem;">
            <label style="text-align: center; display: block; margin-bottom: 0.5rem;">ساعت دقیق</label>
            <div class="time-wheel-container" dir="ltr">
              <div class="wheel-column">
                <div class="wheel-scroll" id="hour-wheel">${hoursHtml}</div>
              </div>
              <div class="wheel-divider">:</div>
              <div class="wheel-column">
                <div class="wheel-scroll" id="minute-wheel">${minutesHtml}</div>
              </div>
              <div class="wheel-highlight"></div>
            </div>
            <input type="hidden" id="event-hour" value="12" />
            <input type="hidden" id="event-minute" value="00" />
          </div>

          <div class="field" style="margin-top: 1rem;">
            <label>توضیحات (اختیاری)</label>
            <textarea id="event-desc" rows="2" class="glass-input"></textarea>
          </div>
          
          <button type="submit" class="btn-primary-glass btn-block" style="margin-top:1.5rem; padding: 0.8rem;">ذخیره رویداد</button>
        </form>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);

  setupWheel('hour-wheel', 'event-hour', 12);
  setupWheel('minute-wheel', 'event-minute', 0);
};

window.setEventCourse = (e, id, name) => {
  e.preventDefault();
  document.getElementById('event-course').value = id;
  document.getElementById('selected-course-label').textContent = name;
  document.getElementById('dd-course-modal').classList.remove('open');

  // هایلایت کردن آیتم انتخاب شده
  const menu = document.getElementById('dd-course-modal');
  menu.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
  e.target.classList.add('active');
};

window.submitManualEvent = async (e, dateStr) => {
  e.preventDefault();

  const courseId = document.getElementById("event-course").value;
  if (!courseId) {
    toast("⚠️ لطفاً یک درس انتخاب کنید");
    return;
  }

  const title = document.getElementById("event-title").value;
  const hour = document.getElementById("event-hour").value;
  const minute = document.getElementById("event-minute").value;
  const type = document.getElementById("event-type").value;
  const desc = document.getElementById("event-desc").value;

  const time = `${hour}:${minute}`;

  const btn = e.target.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.textContent = "در حال ذخیره...";

  try {
    const res = await fetch("/api/events/manual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        description: desc,
        date: dateStr,
        time: time,
        event_type: type,
        course_id: courseId // 👈 ارسال شناسه درس
      })
    });

    if (res.ok) {
      toast("✅ رویداد با موفقیت ذخیره شد");
      document.getElementById("add-event-modal").remove();
      renderPage("calendar");
    } else {
      const err = await res.json();
      toast("❌ " + (err.detail || "خطا در ذخیره"));
      btn.disabled = false;
      btn.textContent = "ذخیره رویداد";
    }
  } catch (err) {
    toast("❌ خطا در ارتباط با سرور");
    btn.disabled = false;
    btn.textContent = "ذخیره رویداد";
  }
};

// ==========================================
// توابع کمکی منوها (کپی کنید اگر ندارید)
// ==========================================
window.toggleModalDropdown = (id) => {
  const el = document.getElementById(id);
  const isOpen = el.classList.contains('open');

  // بستن همه منوهای دیگه
  document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('open'));

  // باز/بسته کردن منوی فعلی
  if (!isOpen) {
    el.classList.add('open');
  }
};

window.setEventType = (e, val, label) => {
  e.preventDefault();
  document.getElementById('event-type').value = val;
  document.getElementById('selected-type-label').textContent = label;
  document.getElementById('dd-type-modal').classList.remove('open');

  const menu = document.getElementById('dd-type-modal');
  menu.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
  e.target.classList.add('active');
};

// ==========================================
// تابع setupWheel (برای مدیریت اسکرول و اسپیس)
// ==========================================
function setupWheel(elementId, hiddenInputId, defaultVal) {
  const el = document.getElementById(elementId);
  const input = document.getElementById(hiddenInputId);
  const items = el.querySelectorAll('.wheel-item');
  const itemHeight = 40;
  const spacerHeight = 60;

  // اسکرول به مقدار پیش‌فرض (با احتساب Spacer)
  el.scrollTop = (defaultVal * itemHeight) + spacerHeight;

  let scrollTimeout;

  el.addEventListener('scroll', () => {
    // پیدا کردن آیتمی که در وسط قرار دارد (با کسر Spacer)
    const centerIdx = Math.round((el.scrollTop - spacerHeight) / itemHeight);

    if (items[centerIdx]) {
      input.value = items[centerIdx].dataset.val;
    }

    // قفل کردن روی عدد دقیق (Magnetic Snap)
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      const snapIdx = Math.round((el.scrollTop - spacerHeight) / itemHeight);
      const targetScrollTop = (snapIdx * itemHeight) + spacerHeight;

      el.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      });

      if (items[snapIdx]) {
        input.value = items[snapIdx].dataset.val;
      }
    }, 150);
  });
}

// PWA: ثبت Service Worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}