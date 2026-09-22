/* ============================================================
   Auto Absensi Sikuli UMRI — frontend (Vercel/serverless)
   Polling 30 detik dipindah ke sisi browser: setInterval ->
   POST /api/check. Cookie sesi HttpOnly otomatis dikirim browser.
   ============================================================ */

const $ = (s) => document.querySelector(s);

// ---- Elements ----
const loginScreen = $("#loginScreen");
const dashboard = $("#dashboard");
const logoutBtn = $("#logoutBtn");
const connPill = $("#connPill");

const loginForm = $("#loginForm");
const nimInput = $("#nim");
const pwdInput = $("#password");
const intervalInput = $("#interval");
const timeoutInput = $("#timeout");
const loginBtn = $("#loginBtn");
const loginAlert = $("#loginAlert");
const togglePwd = $("#togglePwd");

const pName = $("#pName"), pNim = $("#pNim"), pSemester = $("#pSemester");
const mInterval = $("#mInterval"), mLoop = $("#mLoop"), mLast = $("#mLast"), mCourse = $("#mCourse");
const courseCount = $("#courseCount");
const scheduleList = $("#scheduleList");

const startBtn = $("#startBtn"), stopBtn = $("#stopBtn"), refreshBtn = $("#refreshBtn");
const heroDot = $("#heroDot"), heroStatusText = $("#heroStatusText");
const consoleEl = $("#console");
const autoscroll = $("#autoscroll");
const clearLog = $("#clearLog");

let pollTimer = null;
let loopCount = 0;
let storedNim = "";

// ----------------------------------------------------------- //
// UTIL
// ----------------------------------------------------------- //
function setPill(state, text) {
  connPill.className = "pill " + state;
  // pertahankan ikon
  const svg = connPill.querySelector("svg");
  connPill.textContent = " " + text;
  if (svg) connPill.insertBefore(svg, connPill.firstChild);
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
function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  let data = {};
  try { data = await res.json(); } catch (_) {}
  return { ok: res.ok, data };
}

// ----------------------------------------------------------- //
// LOGIN
// ----------------------------------------------------------- //
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
  setLoading(true, "Memproses...");
  setPill("pill-warn", "Login...");

  storedNim = nimInput.value.trim();
  const payload = {
    nim: storedNim,
    password: pwdInput.value.trim(),
    timeout: timeoutInput.value || 10,
  };

  const { ok, data } = await api("/api/login", {
    method: "POST", body: JSON.stringify(payload),
  });

  setLoading(false, "Masuk & Ambil Jadwal");
  if (!ok) {
    setPill("pill-err", "Gagal");
    showAlert("error", data.message || "Login gagal");
    return;
  }
  setPill("pill-ok", "Tersambung");
  showAlert("success", data.message || "Login berhasil!");
  setTimeout(clearAlert, 1800);
  enterDashboard(data.status, payload.timeout, intervalInput.value || 30);
});

function enterDashboard(status, timeout, interval) {
  loginScreen.hidden = true;
  dashboard.hidden = false;
  logoutBtn.hidden = false;
  consoleEl.innerHTML = "";
  mInterval.textContent = interval + "s";
  renderStatus(status);
  renderLogs({ logs: status.logs || [] });
}

function leaveDashboard() {
  stopBot();
  loginScreen.hidden = false;
  dashboard.hidden = true;
  logoutBtn.hidden = true;
  setPill("pill-neutral", "Silakan login");
  pwdInput.value = "";
  loopCount = 0;
  loginForm.scrollIntoView({ behavior: "smooth" });
}

// ----------------------------------------------------------- //
// LOGOUT
// ----------------------------------------------------------- //
logoutBtn.addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  leaveDashboard();
});

// ----------------------------------------------------------- //
// BOT CONTROL (client-side polling)
// ----------------------------------------------------------- //
startBtn.addEventListener("click", startBot);
stopBtn.addEventListener("click", stopBot);
refreshBtn.addEventListener("click", manualCheck);
clearLog.addEventListener("click", () => {
  consoleEl.innerHTML = '<div class="console-line placeholder">Log dibersihkan.</div>';
});

function startBot() {
  const interval = (parseInt(intervalInput.value, 10) || 30) * 1000;
  startBtn.disabled = true;
  stopBtn.disabled = false;
  heroDot.className = "status-dot running";
  heroStatusText.textContent = "Bot berjalan — mengecek tiap " + (interval/1000) + "s";
  setPill("pill-ok", "Bot berjalan");
  pushLog("INFO", "Bot Absen Aktif! Menunggu sesi absen terbuka...");
  // langsung sekali, lalu interval
  manualCheck();
  pollTimer = setInterval(manualCheck, interval);
}

function stopBot() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  startBtn.disabled = false;
  stopBtn.disabled = true;
  heroDot.className = "status-dot stopped";
  heroStatusText.textContent = "Bot dihentikan";
  setPill("pill-neutral", "Berhenti");
  pushLog("WARN", "Bot dihentikan oleh pengguna.");
}

async function manualCheck() {
  const { ok, data } = await api("/api/check", {
    method: "POST", body: JSON.stringify({ nim: storedNim }),
  });
  if (!ok) {
    if (data && data.status && data.status.logged_in === false) {
      setPill("pill-err", "Sesi habis");
      pushLog("ERROR", data.message || "Sesi habis, login ulang.");
      leaveDashboard();
    } else {
      pushLog("ERROR", data.message || "Gagal saat cek.");
    }
    return;
  }
  loopCount += 1;
  renderStatus(data.status);
  renderLogs(data.status);
}

// ----------------------------------------------------------- //
// RENDER
// ----------------------------------------------------------- //
function renderStatus(st) {
  const s = st.student || {};
  pName.textContent = s.nama && s.nama !== "N/A" ? s.nama : "Mahasiswa";
  pNim.textContent = s.nim || "—";
  pSemester.textContent = s.semester || "—";

  const courses = st.courses || [];
  mCourse.textContent = courses.length;
  courseCount.textContent = courses.length + " MK";
  if (courses.length === 0) {
    scheduleList.innerHTML = '<div class="empty">Belum ada jadwal terdeteksi. Klik "Refresh".</div>';
  } else {
    scheduleList.innerHTML = courses.map((c, i) => `
      <div class="course ${c.absen_link ? "has-link" : ""}">
        <div class="mk-head">
          <span class="mk-name">${escapeHtml(c.mk)}</span>
          <span class="mk-idx">#${i + 1}</span>
        </div>
        ${c.ruangan ? row("Ruangan", c.ruangan) : ""}
        ${c.detail ? row("Waktu", c.detail) : ""}
        ${c.dosen ? row("Dosen", c.dosen) : ""}
        ${c.absen_link
          ? '<span class="link-tag open"><svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Sesi absen terbuka</span>'
          : '<span class="link-tag wait">menunggu sesi</span>'}
      </div>`).join("");
  }

  mLoop.textContent = loopCount;
  const now = new Date().toLocaleTimeString("id-ID");
  mLast.textContent = "cek terakhir " + now;
}

function row(label, val) {
  return `<div class="mk-row"><b>${label}</b> <span>${escapeHtml(val)}</span></div>`;
}

function renderLogs(st) {
  const logs = (st && st.logs) || [];
  if (logs.length) {
    const ph = consoleEl.querySelector(".placeholder");
    if (ph) ph.remove();
    const frag = document.createDocumentFragment();
    for (const log of logs) {
      const line = document.createElement("div");
      line.className = "console-line";
      line.innerHTML =
        `<span class="ts">[${log.time}]</span> ` +
        `<span class="lvl lvl-${log.level}">[${log.level}]</span> ` +
        escapeHtml(log.message);
      frag.appendChild(line);
    }
    consoleEl.appendChild(frag);
    if (autoscroll.checked) consoleEl.scrollTop = consoleEl.scrollHeight;
  }
}

function pushLog(level, message) {
  renderLogs({ logs: [{ time: new Date().toLocaleString("id-ID"), level, message }] });
}

// ----------------------------------------------------------- //
// INIT
// ----------------------------------------------------------- //
(async function init() {
  setPill("pill-neutral", "Memeriksa sesi...");
  const { ok, data } = await api("/api/login"); // GET -> cek cookie
  if (ok && data.status && data.status.logged_in) {
    // punya sesi lama -> ambil jadwal sekali
    const r = await api("/api/check", { method: "POST", body: JSON.stringify({ nim: "" }) });
    enterDashboard(r.data ? r.data.status : {}, timeoutInput.value, intervalInput.value);
    loopCount = 0;
    mLoop.textContent = 0;
  } else {
    setPill("pill-neutral", "Silakan login");
  }
})();
