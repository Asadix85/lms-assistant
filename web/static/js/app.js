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

async function api(path, options = {}) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
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
      refreshUserBox();
      renderPage(currentRoute());
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

$("#btn-logout").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  toast("از حساب خارج شدید");
  refreshUserBox();
});

async function refreshUserBox() {
  try {
    const st = await api("/auth/status");
    $("#user-name").textContent = st.full_name || st.username || "کاربر مهمان";
    const initial = (st.full_name || st.username || "؟").trim().charAt(0);
    $("#user-avatar").textContent = initial || "؟";
    $("#user-status").textContent = st.lms_logged_in ? "متصل به LMS" : "وارد نشده";
    if (!st.lms_logged_in) showLogin();
  } catch (_) {
    showLogin();
  }
}

// ---------- Sync + SSE ----------

const PHASE_LABELS = {
  idle: "آماده",
  login: "ورود به LMS",
  courses: "دریافت درس‌ها",
  schedules: "دریافت برنامه هفتگی",
  contents: "دریافت محتواها",
  events: "دریافت رویدادها",
  wall: "دریافت وال و تکالیف",
  members: "دریافت اعضا",
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
    finish(d.ok ? `✅ همگام‌سازی انجام شد — ${d.summary || ""}` : `❌ خطا: ${d.error}`);
  });

  eventSource.addEventListener("error", (e) => {
    let msg = "همگام‌سازی";
    try { msg = JSON.parse(e.data).data.message; } catch (_) {}
    finish("❌ خطا: " + msg);
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
  events: "رویدادها",
  calendar: "تقویم",
  posts: "پیام‌های وال",
  contents: "محتواها",
  changes: "تغییرات",
  quera: "کوئرا",
  settings: "تنظیمات",
};

async function renderDashboard() {
  const d = await api("/dashboard");
  const s = d.stats;

  const statCard = (value, label, icon, color, bg) => `
    <div class="card stat-card" style="--stat-color:${color};--stat-bg:${bg}">
      <span class="stat-icon">${icon}</span>
      <div class="stat-value">${value}</div>
      <div class="stat-label">${label}</div>
    </div>`;

  const events = d.upcoming_events.length
    ? d.upcoming_events.map((e) => {
        const m = eventMeta(e.event_type);
        return `<div class="list-row">
          <span class="row-icon">${m.icon}</span>
          <div class="row-body">
            <div class="row-title">${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>` : esc(e.title)}</div>
            <div class="row-meta">${esc(e.start_at || "بدون زمان")}<span class="sep">·</span>${m.label}</div>
          </div>
        </div>`;
      }).join("")
    : emptyState("رویدادی نیست");

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
    <div class="stats-grid">
      ${statCard(s.active_courses, "درس فعال", "📚", "var(--primary)", "var(--primary-soft)")}
      ${statCard(s.courses, "کل درس‌ها", "🎓", "var(--info)", "var(--info-soft)")}
      ${statCard(s.pending_assignments, "تکلیف باز", "✎", "var(--danger)", "var(--danger-soft)")}
      ${statCard(s.events, "رویدادها", "◷", "var(--warning)", "var(--warning-soft)")}
      ${statCard(s.posts, "پیام‌ها", "◉", "var(--accent)", "var(--accent-soft)")}
      ${statCard(s.contents, "محتواها", "▧", "var(--primary)", "var(--primary-soft)")}
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-head"><h3 class="section-title">📅 رویدادهای پیش‌رو</h3><a class="card-link" href="#/events">همه</a></div>
        <div class="item-list">${events}</div>
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

  const renderList = (items) => {
    const list = document.getElementById("courses-list");
    if (!list) return;
    list.innerHTML = items.length
      ? items.map((c) => `
        <a class="course-card" href="#/course/${encodeURIComponent(c.id)}">
          <div class="course-top">
            <span class="course-icon">📘</span>
            <span class="badge badge-domain">${esc(c.domain)}</span>
            ${c.status === "active" ? '<span class="badge badge-new">فعال</span>' : ""}
          </div>
          <div class="course-name">${esc(c.name)}</div>
          <div class="course-meta">
            <span>👨‍🏫 ${esc(c.teacher || "—")}</span>
            <span>کد ${esc(c.code || "—")}</span>
          </div>
        </a>`).join("")
      : `<div class="empty" style="grid-column:1/-1"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  contentEl.innerHTML = `
    ${pageHead("درس‌ها", `${courses.length} درس همگام‌سازی شده`)}
    ${searchBox("جستجوی نام درس، استاد یا کد…")}
    <div class="course-grid" id="courses-list"></div>`;

  const items = courses.map((c) => ({
    c,
    get searchText() { return `${c.name} ${c.teacher || ""} ${c.code || ""} ${c.domain}`.toLowerCase(); },
  }));
  attachFilter(items, {
    searchText: (it) => it.searchText,
    render: (filtered) => renderList(filtered.map((it) => it.c)),
  });
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
        <div class="row-title"><a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title)}</a></div>
        <div class="row-meta">${esc(x.content_type)}${x.filename ? `<span class="sep">·</span>${esc(x.filename)}` : ""}</div>
      </div>
    </div>`, "محتوایی نیست");

  const membersHtml = listOrEmpty(d.members.slice(0, 70), (m) => `
    <div class="list-row">
      <span class="row-icon">${m.member_type === "teacher" ? "👨‍🏫" : "👤"}</span>
      <div class="row-body">
        <div class="row-title">${esc(m.name)} ${m.member_type === "teacher" ? '<span class="badge badge-domain">استاد</span>' : ""}</div>
      </div>
    </div>`, "عضوی نیست");

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
  if (!items.length) { contentEl.innerHTML = emptyState("تکلیفی یافت نشد"); return; }
  const names = await courseNameMap();

  const renderList = (list) => {
    const el = document.getElementById("list-container");
    if (!el) return;
    el.innerHTML = list.length
      ? list.map((a) => `
        <div class="list-row">
          <span class="row-icon">${a.is_done ? "✅" : a.is_expired ? "⏰" : "📝"}</span>
          <div class="row-body">
            <div class="row-title">
              ${a.view_url ? `<a href="${esc(a.view_url)}" target="_blank" rel="noopener">${esc(a.title)}</a>` : esc(a.title)}
              ${a.is_new ? '<span class="badge badge-new">جدید</span>' : ""}
              ${a.is_expired && !a.is_done ? '<span class="badge badge-expired">گذشته</span>' : ""}
              ${a.is_done ? '<span class="badge badge-done">انجام شده</span>' : ""}
            </div>
            <div class="row-meta">
              <span>مهلت: ${esc(a.deadline_jalali || a.deadline || "—")}</span>
              <span class="sep">·</span><span>${esc(names[a.course_id] || a.course_id)}</span>
            </div>
          </div>
          <div class="row-actions">
            ${a.submit_url ? `<a class="btn btn-soft btn-sm" href="${esc(a.submit_url)}" target="_blank" rel="noopener">ارسال ↗</a>` : ""}
            <button class="btn btn-sm ${a.is_done ? "btn-ghost" : "btn-primary"}"
                    onclick="toggleAssignment('${esc(a.id)}', ${!a.is_done})">
              ${a.is_done ? "لغو" : "انجام شد ✓"}
            </button>
          </div>
        </div>`).join("")
      : `<div class="empty"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  contentEl.innerHTML = `
    ${pageHead("تکالیف", `${items.length} تکلیف ثبت شده`)}
    ${searchBox("جستجوی عنوان تکلیف یا درس…")}
    <div class="item-list" id="list-container"></div>`;

  const records = items.map((a) => ({
    a,
    get searchText() { return `${a.title} ${names[a.course_id] || a.course_id}`.toLowerCase(); },
  }));
  attachFilter(records, {
    searchText: (it) => it.searchText,
    render: (filtered) => renderList(filtered.map((it) => it.a)),
  });
}

window.toggleAssignment = async (id, done) => {
  await api(`/assignments/${encodeURIComponent(id)}/done?done=${done}`, { method: "POST" });
  toast(done ? "✅ تکلیف انجام‌شده علامت خورد" : "تکلیف بازگردانده شد");
  renderPage(currentRoute());
};

async function renderEvents() {
  const items = await api("/events");
  if (!items.length) { contentEl.innerHTML = emptyState("رویدادی یافت نشد"); return; }
  const names = await courseNameMap();

  const renderList = (list) => {
    const el = document.getElementById("list-container");
    if (!el) return;
    el.innerHTML = list.length
      ? list.map((e) => {
          const m = eventMeta(e.event_type);
          return `<div class="list-row">
            <span class="row-icon">${m.icon}</span>
            <div class="row-body">
              <div class="row-title">
                ${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>` : esc(e.title)}
                ${e.is_new ? '<span class="badge badge-new">جدید</span>' : ""}
                <span class="badge ${m.cls}">${m.label}</span>
              </div>
              <div class="row-meta">
                <span>${esc(e.start_at || "بدون زمان")}</span>
                ${e.end_at ? `<span class="sep">·</span><span>تا ${esc(e.end_at)}</span>` : ""}
                ${e.course_id ? `<span class="sep">·</span><span>${esc(names[e.course_id] || e.course_id)}</span>` : ""}
              </div>
            </div>
          </div>`;
        }).join("")
      : `<div class="empty"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  contentEl.innerHTML = `
    ${pageHead("رویدادها", "جلسات آنلاین، آزمون‌ها و ددلاین‌ها")}
    ${searchBox("جستجوی عنوان رویداد…")}
    <div class="item-list" id="list-container"></div>`;

  const records = items.map((e) => ({
    e,
    get searchText() { return `${e.title} ${names[e.course_id] || ""}`.toLowerCase(); },
  }));
  attachFilter(records, {
    searchText: (it) => it.searchText,
    render: (filtered) => renderList(filtered.map((it) => it.e)),
  });
}

async function renderPosts() {
  const items = await api("/posts");
  if (!items.length) { contentEl.innerHTML = emptyState("پیامی یافت نشد"); return; }
  const names = await courseNameMap();

  const renderList = (list) => {
    const el = document.getElementById("list-container");
    if (!el) return;
    el.innerHTML = list.length
      ? list.map((p) => `
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
          ${p.post_url ? `<div class="row-actions"><a class="btn btn-ghost btn-sm" href="${esc(p.post_url)}" target="_blank" rel="noopener">مشاهده ↗</a></div>` : ""}
        </div>`).join("")
      : `<div class="empty"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  const newCount = items.filter((p) => p.is_new).length;
  contentEl.innerHTML = `
    <div class="page-head">
      <div><h3>پیام‌های وال</h3><p>گفتگوها و اطلاعیه‌های درس‌ها</p></div>
      <button class="btn btn-soft btn-sm" onclick="markPostsRead()" ${newCount ? "" : "disabled"}>✓ همه را خواندم${newCount ? ` (${newCount})` : ""}</button>
    </div>
    ${searchBox("جستجو در پیام‌ها…")}
    <div class="item-list" id="list-container"></div>`;

  const records = items.map((p) => ({
    p,
    get searchText() { return `${p.author} ${p.text}`.toLowerCase(); },
  }));
  attachFilter(records, {
    searchText: (it) => it.searchText,
    render: (filtered) => renderList(filtered.map((it) => it.p)),
  });
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
  const names = await courseNameMap();

  const renderList = (list) => {
    const el = document.getElementById("list-container");
    if (!el) return;
    el.innerHTML = list.length
      ? list.map((c) => `
        <div class="list-row">
          <span class="row-icon">📄</span>
          <div class="row-body">
            <div class="row-title"><a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a>
              <span class="badge">${esc(c.content_type)}</span>
            </div>
            <div class="row-meta">
              <span>${esc(names[c.course_id] || c.course_id)}</span>
              ${c.filename ? `<span class="sep">·</span><span>${esc(c.filename)}</span>` : ""}
            </div>
          </div>
          <div class="row-actions"><a class="btn btn-soft btn-sm" href="${esc(c.url)}" target="_blank" rel="noopener">باز کردن ↗</a></div>
        </div>`).join("")
      : `<div class="empty"><span class="empty-icon">🔍</span>نتیجه‌ای یافت نشد</div>`;
  };

  contentEl.innerHTML = `
    ${pageHead("محتواها", "فایل‌ها و منابع درس‌ها")}
    ${searchBox("جستجوی عنوان محتوا…")}
    <div class="item-list" id="list-container"></div>`;

  const records = items.map((c) => ({
    c,
    get searchText() { return `${c.title} ${c.filename}`.toLowerCase(); },
  }));
  attachFilter(records, {
    searchText: (it) => it.searchText,
    render: (filtered) => renderList(filtered.map((it) => it.c)),
  });
}

async function renderChanges() {
  const items = await api("/changes");
  if (!items.length) { contentEl.innerHTML = emptyState("تغییری ثبت نشده"); return; }
  const typeLabel = { new: "جدید", updated: "به‌روز", removed: "حذف" };
  const typeClass = { new: "badge-new", updated: "badge-domain", removed: "badge-expired" };
  const typeIcon = { new: "➕", updated: "🔄", removed: "➖" };
  contentEl.innerHTML = `
    ${pageHead("تغییرات", "آخرین تغییرات شناسایی شده پس از همگام‌سازی")}
    <div class="item-list">
      ${items.map((ch) => `
        <div class="list-row">
          <span class="row-icon">${typeIcon[ch.type] || "🔔"}</span>
          <div class="row-body">
            <div class="row-title">
              <span class="badge ${typeClass[ch.type] || ""}">${typeLabel[ch.type] || ch.type}</span>
              ${esc(ch.entity_type)} — ${esc(ch.data?.title || ch.data?.name || ch.entity_id)}
            </div>
            <div class="row-meta">${esc(ch.detected_at || "")}</div>
          </div>
        </div>`).join("")}
    </div>`;
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

window.syncQuera = async () => {
  const btn = $("#btn-quera-sync");
  if (btn) { btn.disabled = true; btn.textContent = "در حال همگام‌سازی…"; }
  try {
    const r = await api("/quera/sync", { method: "POST" });
    if (r.error) toast("❌ " + r.error);
    else toast(`✅ کوئرا: ${r.new} جدید، ${r.updated} به‌روز`);
  } catch (e) {
    toast("❌ خطا در همگام‌سازی کوئرا");
  } finally {
    renderPage("quera");
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

async function renderCalendar() {
  const items = await api("/events");
  const now = new Date();
  const todayJ = d2j(g2d(now.getFullYear(), now.getMonth() + 1, now.getDate()));
  const eventsByDay = new Map();
  const noDate = [];
  for (const e of items) {
    const m = String(e.start_at || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) {
      const j = d2j(g2d(+m[1], +m[2], +m[3]));
      const key = calEventKey(j);
      if (!eventsByDay.has(key)) eventsByDay.set(key, []);
      eventsByDay.get(key).push(e);
    } else {
      noDate.push(e);
    }
  }
  calState = {
    jy: todayJ.jy,
    jm: todayJ.jm,
    sel: calEventKey(todayJ),
    todayKey: calEventKey(todayJ),
    eventsByDay,
    noDate,
  };

  contentEl.innerHTML = `
    ${pageHead("تقویم", "رویدادها و جلسات در تقویم شمسی")}
    <div class="card">
      <div class="cal-toolbar">
        <button class="btn btn-ghost btn-icon" onclick="calShift(-1)" title="ماه قبل">›</button>
        <button class="btn btn-ghost btn-icon" onclick="calShift(1)" title="ماه بعد">‹</button>
        <h3 id="cal-title"></h3>
        <button class="btn btn-soft btn-sm" onclick="calToday()">امروز</button>
        <div class="cal-legend">
          <span><span class="dot" style="background:var(--warning)"></span>آزمون</span>
          <span><span class="dot" style="background:var(--danger)"></span>ددلاین</span>
          <span><span class="dot" style="background:var(--info)"></span>جلسه آنلاین</span>
          <span><span class="dot" style="background:var(--accent)"></span>اطلاعیه</span>
        </div>
      </div>
      <div class="cal-weekdays">${["ش", "ی", "د", "س", "چ", "پ", "ج"].map((d) => `<span class="cal-weekday">${d}</span>`).join("")}</div>
      <div class="cal-grid" id="cal-grid"></div>
    </div>
    <div class="card" id="cal-day-card"></div>
    ${noDate.length ? `<div class="card" id="cal-nodate-card"></div>` : ""}
  `;
  calRender();
}

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
    if (route.startsWith("course/")) {
      await renderCourseDetail(decodeURIComponent(route.slice("course/".length)));
    } else {
      const fn = {
        dashboard: renderDashboard,
        courses: renderCourses,
        assignments: renderAssignments,
        events: renderEvents,
        calendar: renderCalendar,
        posts: renderPosts,
        contents: renderContents,
        changes: renderChanges,
        quera: renderQuera,
        settings: renderSettings,
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
