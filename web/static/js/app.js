/* ===== LMS Assistant Web — Frontend (SPA با Hash Routing) ===== */

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
  toastTimer = setTimeout(() => t.classList.add("hidden"), 3500);
}

function emptyState(text) {
  return `<div class="empty">📭 ${esc(text)}<br/><small>ابتدا همگام‌سازی را اجرا کنید</small></div>`;
}

// ---------- Theme ----------

function setTheme(theme) {
  document.body.dataset.theme = theme;
  $("#btn-theme").textContent = theme === "dark" ? "☀️" : "🌙";
  localStorage.setItem("lms-theme", theme);
  api("/settings/theme", { method: "POST", body: JSON.stringify({ theme }) }).catch(() => {});
}

$("#btn-theme").addEventListener("click", () => {
  setTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
});

// ---------- Login Modal ----------

const loginModal = $("#login-modal");

function showLogin() { loginModal.classList.remove("hidden"); }
function hideLogin() { loginModal.classList.add("hidden"); $("#login-error").classList.add("hidden"); }

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
  const st = await api("/auth/status");
  $("#user-name").textContent = st.full_name || st.username || "کاربر مهمان";
  if (!st.lms_logged_in) showLogin();
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
  $("#sync-bar").style.width = percent + "%";
  if (label) $("#sync-label").textContent = label;
}

$("#btn-sync").addEventListener("click", async () => {
  const btn = $("#btn-sync");
  btn.disabled = true;
  try {
    const r = await api("/sync/start", { method: "POST" });
    if (!r.ok && r.error) { toast("⏳ " + r.error); btn.disabled = false; return; }
    setSyncUI(true, 0, "شروع همگام‌سازی…");
    listenSyncEvents();
  } catch (e) {
    toast("❌ خطا در شروع همگام‌سازی");
    btn.disabled = false;
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
    $("#btn-sync").disabled = false;
    if (eventSource) { eventSource.close(); eventSource = null; }
    renderPage(currentRoute()); // رفرش صفحه فعلی با داده تازه
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
    // اتصال SSE قطع شد؛ وضعیت را از polling می‌گیریم
    setTimeout(async () => {
      const st = await api("/sync/status");
      if (!st.running) {
        $("#btn-sync").disabled = false;
        setSyncUI(false);
      }
    }, 2000);
  };
}

// ---------- Pages (render functions) ----------

const TITLES = {
  dashboard: "داشبورد",
  courses: "درس‌ها",
  assignments: "تکالیف",
  events: "رویدادها",
  posts: "پیام‌های وال",
  contents: "محتواها",
  changes: "تغییرات",
  quera: "کوئرا",
  settings: "تنظیمات",
};

async function renderDashboard() {
  const d = await api("/dashboard");
  const s = d.stats;

  const statCard = (v, l) =>
    `<div class="card stat-card"><div class="stat-value">${v}</div><div class="stat-label">${l}</div></div>`;

  const events = d.upcoming_events.length
    ? d.upcoming_events.map((e) => `
        <div class="item"><div class="body">
          <div class="title">${esc(e.title)}</div>
          <div class="meta">${esc(e.start_at || "بدون زمان")} · ${esc(e.event_type)}</div>
        </div></div>`).join("")
    : emptyState("رویدادی نیست");

  const assignments = d.upcoming_assignments.length
    ? d.upcoming_assignments.map((a) => `
        <div class="item"><div class="body">
          <div class="title">${esc(a.title)} ${a.is_expired ? '<span class="badge badge-expired">گذشته</span>' : ""}</div>
          <div class="meta">مهلت: ${esc(a.deadline_jalali || a.deadline || "-")}</div>
        </div></div>`).join("")
    : emptyState("تکلیفی نیست");

  const posts = d.recent_posts.length
    ? d.recent_posts.map((p) => `
        <div class="item"><div class="body">
          <div class="title">${esc(p.author)}</div>
          <div class="meta">${esc(p.text.slice(0, 120))}</div>
        </div></div>`).join("")
    : emptyState("پیامی نیست");

  contentEl.innerHTML = `
    <div class="stats-grid">
      ${statCard(s.active_courses, "درس فعال")}
      ${statCard(s.courses, "کل درس‌ها")}
      ${statCard(s.pending_assignments, "تکلیف انجام‌نشده")}
      ${statCard(s.events, "رویدادها")}
      ${statCard(s.posts, "پیام‌ها")}
      ${statCard(s.contents, "محتواها")}
    </div>
    <div class="grid-2">
      <div class="card"><h3 class="section-title">📅 رویدادهای پیش‌رو</h3><div class="item-list">${events}</div></div>
      <div class="card"><h3 class="section-title">📝 تکالیف نزدیک</h3><div class="item-list">${assignments}</div></div>
    </div>
    <div class="card"><h3 class="section-title">💬 آخرین پیام‌ها</h3><div class="item-list">${posts}</div></div>
  `;
}

async function renderCourses() {
  const courses = await api("/courses");
  if (!courses.length) { contentEl.innerHTML = emptyState("درسی یافت نشد"); return; }
  contentEl.innerHTML = `
    <div class="item-list">
      ${courses.map((c) => `
        <div class="item">
          <div class="body">
            <div class="title">
              <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.name)}</a>
              <span class="badge badge-domain">${esc(c.domain)}</span>
              ${c.status === "active" ? '<span class="badge badge-new">فعال</span>' : ""}
            </div>
            <div class="meta">
              استاد: ${esc(c.teacher || "—")} · کد: ${esc(c.code || "—")} · گروه: ${esc(c.group_id)}
            </div>
          </div>
          <button class="btn btn-ghost btn-sm" onclick="location.hash='#/course/${esc(c.id)}'">جزئیات</button>
        </div>`).join("")}
    </div>`;
}

async function renderCourseDetail(courseId) {
  const d = await api(`/courses/${encodeURIComponent(courseId)}/detail`);
  const c = d.course;

  const listOrEmpty = (items, fn, msg) =>
    items.length ? items.map(fn).join("") : `<div class="empty muted">${msg}</div>`;

  contentEl.innerHTML = `
    <div class="card">
      <h3>${esc(c.name)} <span class="badge badge-domain">${esc(c.domain)}</span></h3>
      <p class="muted">استاد: ${esc(c.teacher || "—")} · کد: ${esc(c.code || "—")} · ترم: ${esc(c.term || "—")}</p>
      <a href="${esc(c.url)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm" style="margin-top:.6rem;display:inline-block">باز کردن در LMS ↗</a>
    </div>
    <div class="grid-2">
      <div class="card"><h3 class="section-title">📁 محتواها (${d.contents.length})</h3>
        <div class="item-list">${listOrEmpty(d.contents, (x) => `
          <div class="item"><div class="body">
            <div class="title"><a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title)}</a></div>
            <div class="meta">${esc(x.content_type)}</div>
          </div></div>`, "محتوایی نیست")}</div>
      </div>
      <div class="card"><h3 class="section-title">📝 تکالیف (${d.assignments.length})</h3>
        <div class="item-list">${listOrEmpty(d.assignments, (a) => `
          <div class="item"><div class="body">
            <div class="title">${esc(a.title)} ${a.is_done ? '<span class="badge badge-done">انجام شده</span>' : ""}</div>
            <div class="meta">مهلت: ${esc(a.deadline_jalali || a.deadline || "—")}</div>
          </div></div>`, "تکلیفی نیست")}</div>
      </div>
      <div class="card"><h3 class="section-title">💬 پیام‌های وال (${d.posts.length})</h3>
        <div class="item-list">${listOrEmpty(d.posts, (p) => `
          <div class="item"><div class="body">
            <div class="title">${esc(p.author)}</div>
            <div class="meta">${esc(p.text)}</div>
          </div></div>`, "پیامی نیست")}</div>
      </div>
      <div class="card"><h3 class="section-title">👥 اعضا (${d.members.length})</h3>
        <div class="item-list">${listOrEmpty(d.members.slice(0, 40), (m) => `
          <div class="item"><div class="body">
            <div class="title">${esc(m.name)} ${m.member_type === "teacher" ? '<span class="badge badge-domain">استاد</span>' : ""}</div>
          </div></div>`, "عضوی نیست")}</div>
      </div>
    </div>`;
}

async function renderAssignments() {
  const items = await api("/assignments");
  if (!items.length) { contentEl.innerHTML = emptyState("تکلیفی یافت نشد"); return; }
  contentEl.innerHTML = `<div class="item-list">
    ${items.map((a) => `
      <div class="item">
        <div class="body">
          <div class="title">
            ${a.view_url ? `<a href="${esc(a.view_url)}" target="_blank" rel="noopener">${esc(a.title)}</a>` : esc(a.title)}
            ${a.is_new ? '<span class="badge badge-new">جدید</span>' : ""}
            ${a.is_expired && !a.is_done ? '<span class="badge badge-expired">گذشته</span>' : ""}
            ${a.is_done ? '<span class="badge badge-done">انجام شده</span>' : ""}
          </div>
          <div class="meta">مهلت: ${esc(a.deadline_jalali || a.deadline || "—")} · درس: ${esc(a.course_id)}</div>
        </div>
        <button class="btn btn-sm ${a.is_done ? "btn-ghost" : "btn-primary"}"
                onclick="toggleAssignment('${esc(a.id)}', ${!a.is_done})">
          ${a.is_done ? "لغو" : "انجام شد ✓"}
        </button>
      </div>`).join("")}
  </div>`;
}

window.toggleAssignment = async (id, done) => {
  await api(`/assignments/${encodeURIComponent(id)}/done?done=${done}`, { method: "POST" });
  toast(done ? "✅ تکلیف انجام‌شده علامت خورد" : "تکلیف بازگردانده شد");
  renderPage(currentRoute());
};

async function renderEvents() {
  const items = await api("/events");
  if (!items.length) { contentEl.innerHTML = emptyState("رویدادی یافت نشد"); return; }
  contentEl.innerHTML = `<div class="item-list">
    ${items.map((e) => `
      <div class="item"><div class="body">
        <div class="title">
          ${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>` : esc(e.title)}
          ${e.is_new ? '<span class="badge badge-new">جدید</span>' : ""}
          <span class="badge">${esc(e.event_type)}</span>
        </div>
        <div class="meta">${esc(e.start_at || "بدون زمان")} ${e.end_at ? "تا " + esc(e.end_at) : ""}</div>
      </div></div>`).join("")}
  </div>`;
}

async function renderPosts() {
  const items = await api("/posts");
  if (!items.length) { contentEl.innerHTML = emptyState("پیامی یافت نشد"); return; }
  contentEl.innerHTML = `<div class="item-list">
    ${items.map((p) => `
      <div class="item"><div class="body">
        <div class="title">${esc(p.author)} ${p.is_new ? '<span class="badge badge-new">جدید</span>' : ""}</div>
        <div class="meta">${esc(p.text)}</div>
        <div class="muted" style="margin-top:.3rem">${esc(p.posted_at_jalali || p.posted_at || "")} · درس: ${esc(p.course_id)}</div>
      </div></div>`).join("")}
  </div>`;
}

async function renderContents() {
  const items = await api("/contents");
  if (!items.length) { contentEl.innerHTML = emptyState("محتوایی یافت نشد"); return; }
  contentEl.innerHTML = `<div class="item-list">
    ${items.map((c) => `
      <div class="item"><div class="body">
        <div class="title"><a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a>
          <span class="badge">${esc(c.content_type)}</span>
        </div>
        <div class="meta">درس: ${esc(c.course_id)}</div>
      </div></div>`).join("")}
  </div>`;
}

async function renderChanges() {
  const items = await api("/changes");
  if (!items.length) { contentEl.innerHTML = emptyState("تغییری ثبت نشده"); return; }
  const typeLabel = { new: "جدید", updated: "به‌روز", removed: "حذف" };
  const typeClass = { new: "badge-new", updated: "badge-domain", removed: "badge-expired" };
  contentEl.innerHTML = `<div class="item-list">
    ${items.map((ch) => `
      <div class="item"><div class="body">
        <div class="title">
          <span class="badge ${typeClass[ch.type] || ""}">${typeLabel[ch.type] || ch.type}</span>
          ${esc(ch.entity_type)} — ${esc(ch.data?.title || ch.data?.name || ch.entity_id)}
        </div>
        <div class="meta">${esc(ch.detected_at || "")}</div>
      </div></div>`).join("")}
  </div>`;
}

async function renderQuera() {
  const [assignments, courses] = await Promise.all([api("/quera/assignments"), api("/quera/courses")]);
  const courseNames = Object.fromEntries(courses.map((c) => [c.id, c.name]));

  contentEl.innerHTML = `
    <div class="card" style="display:flex;justify-content:space-between;align-items:center">
      <span>${assignments.length} تمرین همگام‌سازی‌شده</span>
      <button class="btn btn-primary btn-sm" id="btn-quera-sync" onclick="syncQuera()">🔄 همگام‌سازی کوئرا</button>
    </div>
    <div class="item-list">
      ${assignments.length ? assignments.map((a) => {
        const submitted = a.problems.filter((p) => p.is_submitted).length;
        return `
        <div class="item"><div class="body">
          <div class="title">${esc(a.name)}
            ${a.is_done ? '<span class="badge badge-done">بسته</span>' : ""}
            ${a.is_manual ? '<span class="badge">دستی</span>' : ""}
          </div>
          <div class="meta">
            دوره: ${esc(a.course_name)} · پایان: ${esc(a.finish_time || "—")} ·
            حل‌شده: ${submitted}/${a.problems_count}
          </div>
        </div></div>`;
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
    ["courses", "درس‌ها"],
    ["contents", "محتواها"],
    ["events", "رویدادها"],
    ["wall", "وال (پیام‌ها و تکالیف)"],
    ["members", "اعضای درس‌ها"],
  ].map(([key, label]) => `
    <div class="setting-row">
      <span>${label}</span>
      <label class="switch">
        <input type="checkbox" data-key="${key}" ${sync[key] ? "checked" : ""}/>
        <span class="slider"></span>
      </label>
    </div>`).join("");

  contentEl.innerHTML = `
    <div class="card">
      <h3 class="section-title">🔄 فازهای همگام‌سازی</h3>
      ${rows}
      <button class="btn btn-primary" style="margin-top:1rem" onclick="saveSyncSettings()">ذخیره تنظیمات</button>
    </div>
    <div class="card">
      <h3 class="section-title">🔐 حساب کاربری</h3>
      <p class="muted" style="margin-bottom:.7rem">برای تغییر شماره دانشجویی یا رمز عبور، دوباره وارد شوید.</p>
      <button class="btn btn-ghost" onclick="showLogin()">تغییر حساب / ورود مجدد</button>
    </div>`;
}

window.saveSyncSettings = async () => {
  const body = {};
  document.querySelectorAll("[data-key]").forEach((el) => { body[el.dataset.key] = el.checked; });
  await api("/settings/sync", { method: "POST", body: JSON.stringify(body) });
  toast("✅ تنظیمات ذخیره شد");
};

window.showLogin = showLogin;

// ---------- Router ----------

function currentRoute() {
  const hash = location.hash.replace(/^#\/?/, "");
  return hash || "dashboard";
}

async function renderPage(route) {
  const page = route.startsWith("course/") ? "course" : route;
  document.querySelectorAll(".nav-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.page === page);
  });
  $("#page-title").textContent =
    TITLES[route] || (route.startsWith("course/") ? "جزئیات درس" : "داشبورد");

  contentEl.innerHTML = '<div class="loading">⏳ در حال بارگذاری…</div>';
  try {
    if (route.startsWith("course/")) {
      await renderCourseDetail(decodeURIComponent(route.slice("course/".length)));
    } else {
      const fn = {
        dashboard: renderDashboard,
        courses: renderCourses,
        assignments: renderAssignments,
        events: renderEvents,
        posts: renderPosts,
        contents: renderContents,
        changes: renderChanges,
        quera: renderQuera,
        settings: renderSettings,
      }[route] || renderDashboard;
      await fn();
    }
  } catch (e) {
    contentEl.innerHTML = `<div class="empty">❌ خطا در بارگذاری صفحه<br/><small>${esc(e.message)}</small></div>`;
  }
}

window.addEventListener("hashchange", () => renderPage(currentRoute()));

// ---------- Mobile menu ----------

$("#btn-menu").addEventListener("click", () => {
  $("#sidebar").classList.toggle("open");
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
  renderPage(currentRoute());

  // اگر sync در حال اجراست، نوار پیشرفت را وصل کن
  try {
    const st = await api("/sync/status");
    if (st.running) {
      $("#btn-sync").disabled = true;
      setSyncUI(true, st.progress?.percent ?? 0, "همگام‌سازی در حال اجرا…");
      listenSyncEvents();
    }
  } catch (_) {}
})();
