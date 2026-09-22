"""
app.py — Flask app untuk Auto Absen Sikuli (persistent host).

Versi ini menjalankan bot polling di background THREAD (per-user),
jadi bot tetap jalan walaupun browser ditutup, HP mati, atau tidak ada
yang login. Tanggung jawab server: jaga thread tetap hidup 24/7.

Endpoint:
  GET  /             → public/index.html (UI retro)
  GET  /api/status   → snapshot state (student/courses/logs/bot)
  POST /api/login    → login Sikuli, set cookie {sid,nim,cookies}
  POST /api/start    → mulai bot thread
  POST /api/stop     → stop bot thread
  POST /api/refresh  → satu siklus cek manual (tanpa start)
  POST /api/logout   → stop bot, hapus cookie

Deploy:
  - Railway / Render / Fly.io: Procfile (web: gunicorn app:app)
  - Lokal dev: python app.py
"""

import os
import sys
import datetime
import logging

# Pastikan root proyek ada di sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, make_response

from lib import sikuli, bot as bot_registry

app = Flask(__name__, static_folder="public", static_url_path="")

COOKIE_NAME = "sikuli_sess"
COOKIE_MAX_AGE = 60 * 60 * 8   # 8 jam

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("auto-absen")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _secret():
    """Kunci enkripsi cookie. Pakai SESSION_SECRET env var di produksi."""
    s = os.environ.get("SESSION_SECRET")
    if s:
        return s
    # Fallback dev lokal saja — JANGAN dipakai di produksi
    return "dev-insecure-secret-do-not-use-in-prod-change-me"


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _cookie_secure():
    """Cookie aman (HTTPS) di produksi, longgar di local debug."""
    return not app.debug


def _set_session_cookie(resp, token):
    resp.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=_cookie_secure(),
        samesite="Lax",
        path="/",
    )


def _delete_session_cookie(resp):
    resp.delete_cookie(COOKIE_NAME, path="/")


def _read_payload(req):
    """Baca & decrypt cookie. Return dict payload atau None."""
    token = req.cookies.get(COOKIE_NAME)
    return sikuli.decrypt_payload(token, _secret())


def _bot_snapshot_or_error():
    """Ambil bot berdasarkan cookie, return (bot, error_response_or_None)."""
    payload = _read_payload(request)
    if not payload:
        return None, (jsonify({
            "ok": False,
            "logged_in": False,
            "message": "Sesi habis, silakan login ulang",
        }), 401)
    sid = payload["s"]
    nim = payload.get("n", "")
    cookies = payload.get("c", {})

    # Re-create bot kalau server restart
    b = bot_registry.get_or_recreate(sid, nim, cookies)
    if not b:
        return None, (jsonify({
            "ok": False,
            "logged_in": False,
            "message": "Sesi rusak, silakan login ulang",
        }), 401)
    return b, None


# --------------------------------------------------------------------------- #
# API: /api/login (POST)
# --------------------------------------------------------------------------- #
@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    nim = (data.get("nim") or "").strip()
    password = (data.get("password") or "").strip()
    timeout = int(data.get("timeout", 10) or 10)

    if not nim or not password:
        return jsonify({"ok": False, "message": "NIM dan Password wajib diisi"}), 400

    session, ok, msg = sikuli.login(nim, password, timeout=timeout)
    if not ok:
        return jsonify({"ok": False, "message": msg}), 401

    # Satu siklus awal untuk populate jadwal
    result = sikuli.run_one_cycle(session, nim_hint=nim)

    # Bikin bot instance (belum jalan, tunggu tombol "Mulai")
    sid = bot_registry.new_sid()
    b = bot_registry.SikuliBot(sid, nim, session)
    b._student = result["student"]
    b._courses = result["courses"]
    bot_registry.register(b)
    log.info("User login: nim=%s sid=%s", nim, sid[:8])

    token = sikuli.encrypt_payload(sid, nim, session, _secret())
    resp = make_response(jsonify({
        "ok": True,
        "message": msg,
        "state": b.snapshot(),
    }), 200)
    _set_session_cookie(resp, token)
    return resp


# --------------------------------------------------------------------------- #
# API: /api/status (GET)
# --------------------------------------------------------------------------- #
@app.get("/api/status")
def api_status():
    """Snapshot state bot (student/courses/logs/running). Dipanggil tiap 2-3 detik dari frontend."""
    b, err = _bot_snapshot_or_error()
    if err:
        return err
    return jsonify({
        "ok": True,
        "logged_in": True,
        "state": b.snapshot(),
    }), 200


# --------------------------------------------------------------------------- #
# API: /api/start (POST) — mulai bot thread
# --------------------------------------------------------------------------- #
@app.post("/api/start")
def api_start():
    b, err = _bot_snapshot_or_error()
    if err:
        return err
    if b.is_running():
        return jsonify({"ok": True, "message": "Bot sudah berjalan", "state": b.snapshot()}), 200
    started = b.start()
    log.info("Bot start: sid=%s ok=%s", b.sid[:8], started)
    return jsonify({
        "ok": True,
        "message": "Bot dimulai — polling 30 detik, 24/7",
        "state": b.snapshot(),
    }), 200


# --------------------------------------------------------------------------- #
# API: /api/stop (POST)
# --------------------------------------------------------------------------- #
@app.post("/api/stop")
def api_stop():
    b, err = _bot_snapshot_or_error()
    if err:
        return err
    b.stop()
    log.info("Bot stop: sid=%s", b.sid[:8])
    return jsonify({
        "ok": True,
        "message": "Bot dihentikan",
        "state": b.snapshot(),
    }), 200


# --------------------------------------------------------------------------- #
# API: /api/refresh (POST) — satu siklus manual, tanpa start thread
# --------------------------------------------------------------------------- #
@app.post("/api/refresh")
def api_refresh():
    b, err = _bot_snapshot_or_error()
    if err:
        return err
    # Pakai thread terpisah agar tidak block request kalau Sikuli lambat
    import threading
    def _run():
        b._do_check()
    threading.Thread(target=_run, daemon=True, name=f"refresh-{b.sid[:8]}").start()
    return jsonify({
        "ok": True,
        "message": "Refresh dijadwalkan",
        "state": b.snapshot(),
    }), 200


# --------------------------------------------------------------------------- #
# API: /api/logout (POST)
# --------------------------------------------------------------------------- #
@app.post("/api/logout")
def api_logout():
    payload = _read_payload(request)
    if payload:
        bot_registry.unregister(payload["s"])
        log.info("Logout: sid=%s", payload["s"][:8])
    resp = make_response(jsonify({"ok": True, "message": "Logout berhasil"}), 200)
    _delete_session_cookie(resp)
    return resp


# --------------------------------------------------------------------------- #
# Static frontend
# --------------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found(_e):
    if not request.path.startswith("/api/"):
        return app.send_static_file("index.html")
    return jsonify({"ok": False, "message": "Not Found"}), 404


# --------------------------------------------------------------------------- #
# Graceful shutdown
# --------------------------------------------------------------------------- #
import atexit
atexit.register(bot_registry.shutdown_all)


# --------------------------------------------------------------------------- #
# Local dev
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)