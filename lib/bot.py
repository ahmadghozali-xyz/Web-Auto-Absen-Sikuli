"""
lib/bot.py — SikuliBot: wrapper yang menjalankan polling loop di background thread.

Tiap user yang login dapat 1 instance SikuliBot, disimpan di registry global.
Thread polling melakukan 1 siklus (ambil jadwal + cek absen) tiap POLL_INTERVAL detik,
dan menulis hasilnya ke shared state dict yang dibaca oleh /api/status.

Bot akan terus jalan walaupun browser ditutup/HP mati — yang penting server hidup.
"""

import threading
import time
import datetime
import secrets

from . import sikuli

POLL_INTERVAL = 30          # detik antar siklus polling
LOG_BUFFER_MAX = 150        # max log yang disimpan di memori


class SikuliBot:
    """Satu instance per user. Punya thread polling sendiri."""

    def __init__(self, sid: str, nim: str, session):
        self.sid = sid                  # session id unik
        self.nim = nim                  # NIM user (untuk ditampilkan & nim_hint)
        self.session = session          # requests.Session yang sudah login
        self.thread = None
        self.stop_event = threading.Event()
        self._lock = threading.Lock()

        # Shared state (dilindungi lock)
        self._student = {"nama": "—", "nim": nim, "semester": "—"}
        self._courses = []
        self._logs = []                 # [{time, level, message}, ...]
        self._loop_count = 0
        self._last_check = None         # string "HH:MM:SS" atau None
        self._last_success = None       # timestamp absen terakhir sukses
        self._running = False
        self._started_at = None

    # ------------------------------------------------------------------ #
    # LOG BUFFER
    # ------------------------------------------------------------------ #
    def _push(self, level: str, message: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self._logs.append({"time": now, "level": level, "message": message})
            if len(self._logs) > LOG_BUFFER_MAX:
                # Buang yang paling lama, pertahankan yang terbaru
                del self._logs[: len(self._logs) - LOG_BUFFER_MAX]
            if level == "SUCCESS" and "Absen BERHASIL" in message:
                self._last_success = now

    # ------------------------------------------------------------------ #
    # SATU SIKLUS
    # ------------------------------------------------------------------ #
    def _do_check(self):
        self._loop_count += 1
        self._last_check = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            result = sikuli.run_one_cycle(self.session, nim_hint=self.nim)
            with self._lock:
                if result.get("student"):
                    self._student = result["student"]
                if result.get("courses") is not None:
                    self._courses = result["courses"]
            # Append log dari siklus ini
            open_sessions = [c["mk"] for c in result.get("courses", []) if c.get("absen_link")]
            if not open_sessions:
                self._push("INFO", "Cek siklus #" + str(self._loop_count) + " — belum ada sesi absen terbuka.")
            else:
                self._push("INFO", "Cek siklus #" + str(self._loop_count) +
                           f" — {len(open_sessions)} sesi absen terbuka.")
            for log in result.get("logs", []):
                self._push(log.get("level", "INFO"), log.get("message", ""))
        except Exception as e:
            self._push("ERROR", f"Exception saat cek: {e}")

    # ------------------------------------------------------------------ #
    # MAIN LOOP (jalan di background thread)
    # ------------------------------------------------------------------ #
    def _run_loop(self):
        self._push("INFO", "Bot auto absen aktif — polling tiap 30 detik, 24/7.")
        self._started_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._do_check()  # langsung pertama kali
        while not self.stop_event.is_set():
            # Tidur, tapi bisa di-interrupt oleh stop_event
            if self.stop_event.wait(timeout=POLL_INTERVAL):
                break
            self._do_check()
        self._push("WARN", "Bot dihentikan.")
        self._running = False

    # ------------------------------------------------------------------ #
    # CONTROL
    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        """Mulai thread polling. Return True kalau berhasil start."""
        if self._running:
            return False
        self.stop_event.clear()
        self._running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=f"sikuli-bot-{self.sid[:8]}",
        )
        self.thread.start()
        return True

    def stop(self, timeout=5) -> bool:
        """Stop thread polling. Return True kalau ada yang di-stop."""
        if not self._running:
            return False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=timeout)
        return True

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------ #
    # STATE SNAPSHOT (untuk dikirim ke frontend)
    # ------------------------------------------------------------------ #
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "sid": self.sid,
                "nim": self.nim,
                "running": self._running,
                "started_at": self._started_at,
                "student": dict(self._student),
                "courses": list(self._courses),
                "logs": list(self._logs),
                "loop_count": self._loop_count,
                "last_check": self._last_check,
                "last_success": self._last_success,
                "poll_interval": POLL_INTERVAL,
            }

    def refresh_session_from_cookies(self, cookies: dict):
        """Update cookie Sikuli di session (mis. setelah server restart)."""
        self.session.cookies.clear()
        for k, v in (cookies or {}).items():
            self.session.cookies.set(k, v)


# ====================================================================== #
# REGISTRY GLOBAL: sid -> SikuliBot
# ====================================================================== #
_REGISTRY: dict[str, SikuliBot] = {}
_REG_LOCK = threading.Lock()


def new_sid() -> str:
    """Generate session id baru (32 char hex)."""
    return secrets.token_hex(16)


def register(bot: SikuliBot):
    with _REG_LOCK:
        _REGISTRY[bot.sid] = bot


def unregister(sid: str):
    with _REG_LOCK:
        bot = _REGISTRY.pop(sid, None)
    if bot:
        bot.stop()


def get(sid: str) -> SikuliBot | None:
    with _REG_LOCK:
        return _REGISTRY.get(sid)


def get_or_recreate(sid: str, nim: str, cookies: dict) -> SikuliBot | None:
    """Ambil bot dari registry, atau buat baru dari cookies kalau server restart."""
    bot = get(sid)
    if bot:
        return bot
    if not cookies:
        return None
    session = sikuli.new_session()
    for k, v in cookies.items():
        session.cookies.set(k, v)
    bot = SikuliBot(sid, nim, session)
    register(bot)
    return bot


def shutdown_all():
    """Stop semua bot (dipanggil saat shutdown server)."""
    with _REG_LOCK:
        bots = list(_REGISTRY.values())
    for b in bots:
        b.stop()


def stats() -> dict:
    with _REG_LOCK:
        return {
            "total_bots": len(_REGISTRY),
            "running_bots": sum(1 for b in _REGISTRY.values() if b.is_running()),
            "sids": list(_REGISTRY.keys()),
        }