/* ============================================================
   Auto Absen Sikuli — Frontend JS
   - Polling /api/status tiap 2.5 detik (ringan)
   - Start / Stop / Refresh bot
   - Theme toggle (light/dark) + localStorage
   ============================================================ */

const $ = (s) => document.querySelector(s);

const loginScreen  = $("#loginScreen");
const dashboard    = $("#dashboard");
const logoutBtn    = $("#logoutBtn");
const loginForm    = $("#loginForm");
const nimInput     = $("#nim");
const pwdInput     = $("#password");
const loginBtn     = $("#loginBtn");
const loginAlert   = $("#loginAlert");
const togglePwd    = $("#togglePwd");

const pName = $("#pName"), pNim = $("#pNim"), pSemester = $("#pSemester");
const mLoop = $("#mLoop"), mCourse = $("#mCourse"), mLast = $("#mLast");
const courseCount = $("#courseCount");
const scheduleList = $("#scheduleList");

const startBtn = $("#startBtn"), stopBtn = $("#stopBtn"), refreshBtn = $("#refreshBtn");
const heroStatusPill = $("#heroStatusPill"), heroStatusText = $("#heroStatusText");
const consoleEl = $("#console");
const autoscroll = $("#autoscroll");
const clearLog = $("#clearLog");

const themeToggle = $("#themeToggle");
const iconSun = $("#iconSun"), iconMoon = $("#iconMoon");

// ---- state ----
let pollTimer = null;
let lastLogCount = 0;
let lastState = null;

// ============================================================ //
// UTIL
// ============================================================ //
function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showAlert(type, msg) {
  loginAlert.hidden = false;
  loginAlert.className = "alert alert-" + type;
  loginAlert.textContent = msg;
}
function clearAlert() { loginAlert.hidden = true; loginAlert.textContent = ""; }
function setLoading(loading, label) {
  const lbl = loginBtn.querySelector(".btn-label");
  const sp = loginBtn.querySelector(".spinner");
  if (lbl) lbl.textContent = label;
  if (sp) sp.hidden = !loading;
  loginBtn.disabled = loading;
}

async function api(path, opts = {}) {
  try {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      ...opts,
    });
    let data = {};
    try { data = await res.json(); } catch (_) {}
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: { message: "Tidak terhubung ke server" } };
  }
}

// ============================================================ //
// THEME TOGGLE
// ============================================================ //
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const isDark = theme === "dark";
  iconSun.hidden = isDark;
  iconMoon.hidden = !isDark;
  localStorage.setItem("absen-theme", theme);
}

function initTheme() {
  const saved = localStorage.getItem("absen-theme");
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  applyTheme(saved || (prefersDark ? "dark" : "light"));
}

themeToggle.addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(cur === "dark" ? "light" : "dark");
});

initTheme();

// ============================================================ //
// LOGIN
// ============================================================ //
togglePwd.addEventListener("click", () => {
  const show = pwdInput.type === "password";
  pwdInput.type = show ? "text" : "password";
  togglePwd.innerHTML = show
    ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>'
    : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearAlert();
  setLoading(true, "Login...");
  showAlert("info", "Sedang login ke portal Sikuli...");

  const payload = {
    nim: nimInput.value.trim(),
    password: pwdInput.value.trim(),
  };

  const { ok, data } = await api("/api/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  setLoading(false, "Masuk & Mulai Absen");

  if (!ok) {
    showAlert("error", data.message || "Login gagal");
    return;
  }

  showAlert("success", "Login berhasil! Bot siap dijalankan.");
  setTimeout(clearAlert, 1500);
  enterDashboard(data.state);
});

function enterDashboard(state) {
  loginScreen.hidden = true;
  dashboard.hidden = false;
  logoutBtn.hidden = false;
  consoleEl.innerHTML = "";
  lastLogCount = 0;
  lastState = state;
  renderState(state);
}

function leaveDashboard() {
  stopPolling();
  loginScreen.hidden = false;
  dashboard.hidden = true;
  logoutBtn.hidden = true;
  lastState = null;
  nimInput.value = "";
  pwdInput.value = "";
}

// ============================================================ //
// LOGOUT
// ============================================================ //
logoutBtn.addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  leaveDashboard();
});

// ============================================================ //
// BOT CONTROL
// ============================================================ //
startBtn.addEventListener("click", async () => {
  const { ok, data } = await api("/api/start", { method: "POST" });
  if (!ok) {
    showAlert("error", data.message || "Gagal mulai bot");
    return;
  }
  renderState(data.state);
});

stopBtn.addEventListener("click", async () => {
  const { ok, data } = await api("/api/stop", { method: "POST" });
  if (ok) renderState(data.state);
});

refreshBtn.addEventListener("click", async () => {
  await api("/api/refresh", { method: "POST" });
});

clearLog.addEventListener("click", () => {
  consoleEl.innerHTML = '<div class="console-line placeholder">Log dibersihkan.</div>';
  lastLogCount = 0;
});

// ============================================================ //
// POLLING STATUS (tiap 2.5 detik)
// ============================================================ //
function startPolling() {
  if (pollTimer) return;
  pollStatus(); // immediate
  pollTimer = setInterval(pollStatus, 2500);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

async function pollStatus() {
  const { ok, data } = await api("/api/status");
  if (!ok) {
    if (data && data.logged_in === false) {
      // session expired
      leaveDashboard();
      showAlert("error", data.message || "Sesi habis, silakan login ulang.");
    }
    return;
  }
  if (data && data.state) {
    lastState = data.state;
    renderState(data.state);
  }
}

// ============================================================ //
// RENDER
// ============================================================ //
function renderState(st) {
  if (!st) return;
  // Student
  const s = st.student || {};
  pName.textContent = (s.nama && s.nama !== "N/A") ? s.nama : "Mahasiswa";
  pNim.textContent = s.nim || "—";
  pSemester.textContent = s.semester || "—";

  // Stats
  mLoop.textContent = st.loop_count || 0;
  const courses = st.courses || [];
  mCourse.textContent = courses.length;
  courseCount.textContent = courses.length + " MK";
  mLast.textContent = st.last_check ? "cek " + st.last_check : "—";

  // Schedule
  if (courses.length === 0) {
    scheduleList.innerHTML = '<div class="empty">Belum ada jadwal. Klik "Refresh" untuk memuat ulang.</div>';
  } else {
    scheduleList.innerHTML = courses.map((c, i) => `
      <div class="course ${c.absen_link ? "has-link" : ""}">
        <div class="mk-head">
          <span class="mk-name">${escapeHtml(c.mk)}</span>
          <span class="mk-idx">#${i + 1}</span>
        </div>
        ${c.ruangan ? `<div class="mk-row"><b>Ruangan</b> <span>${escapeHtml(c.ruangan)}</span></div>` : ""}
        ${c.detail  ? `<div class="mk-row"><b>Waktu</b> <span>${escapeHtml(c.detail)}</span></div>` : ""}
        ${c.dosen   ? `<div class="mk-row"><b>Dosen</b> <span>${escapeHtml(c.dosen)}</span></div>` : ""}
        ${c.absen_link
          ? '<span class="link-tag open"><svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Sesi terbuka</span>'
          : '<span class="link-tag wait">menunggu sesi</span>'}
      </div>
    `).join("");
  }

  // Hero status
  if (st.running) {
    heroStatusPill.className = "pill pill-ok";
    heroStatusPill.querySelector(".pill-dot").style.background = "#FFFBF1";
    heroStatusText.textContent = "Bot berjalan";
    startBtn.disabled = true;
    stopBtn.disabled = false;
  } else {
    heroStatusPill.className = "pill pill-warn";
    heroStatusPill.querySelector(".pill-dot").style.background = "var(--mustard)";
    heroStatusText.textContent = "Belum dimulai";
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }

  // Logs (append only new ones)
  renderLogs(st.logs || []);
}

function renderLogs(logs) {
  if (!logs || !logs.length) return;
  // Detect reset (mis. setelah logout)
  if (logs.length < lastLogCount - 5) {
    consoleEl.innerHTML = "";
    lastLogCount = 0;
  }
  // Append only new
  const newLogs = logs.slice(lastLogCount);
  if (newLogs.length === 0) return;

  const ph = consoleEl.querySelector(".placeholder");
  if (ph) ph.remove();

  const frag = document.createDocumentFragment();
  for (const log of newLogs) {
    const line = document.createElement("div");
    line.className = "console-line";
    line.innerHTML =
      `<span class="ts">[${escapeHtml(log.time)}]</span> ` +
      `<span class="lvl lvl-${escapeHtml(log.level)}">[${escapeHtml(log.level)}]</span> ` +
      escapeHtml(log.message);
    frag.appendChild(line);
  }
  consoleEl.appendChild(frag);
  lastLogCount = logs.length;

  if (autoscroll.checked) {
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }
}

// ============================================================ //
// INIT — cek apakah masih ada sesi
// ============================================================ //
(async function init() {
  const { ok, data } = await api("/api/status");
  if (ok && data && data.logged_in && data.state) {
    enterDashboard(data.state);
    startPolling();
  } else {
    // show login screen (default visible)
  }
})();