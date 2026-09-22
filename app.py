"""app.py — Flask app: serves static frontend + API for Sikuli bot.

Entry point untuk Vercel (Python framework preset, variable: `app`).
Juga bisa dijalankan lokal: `python app.py` → http://localhost:5000
"""

import os
import sys
import datetime

# Pastikan root proyek ada di sys.path agar `lib` bisa di-import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, make_response
from lib import sikuli

# static_folder="public"  → serve folder public/
# static_url_path=""      → serve di root (jadi /style.css, /script.js)
# "/"                     → otomatis serve public/index.html
app = Flask(__name__, static_folder="public", static_url_path="")

COOKIE_NAME = "sikuli_sess"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _secret():
    """Kunci enkripsi cookie. Pakai SESSION_SECRET env var di Vercel."""
    s = os.environ.get("SESSION_SECRET")
    if s:
        return s
    # Fallback lokal saja — JANGAN dipakai di produksi
    return "dev-insecure-secret-do-not-use-in-prod-change-me"


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _cookie_secure():
    """Cookie aman (HTTPS) di produksi, longgar di local debug."""
    # app.debug=True saat `python app.py` (lokal). Di Vercel: debug=False → secure=True.
    return not app.debug


def _set_session_cookie(resp, token):
    resp.set_cookie(
        COOKIE_NAME,
        token,
        max_age=60 * 60 * 8,        # 8 jam
        httponly=True,              # JS frontend tidak bisa baca
        secure=_cookie_secure(),    # HTTPS-only di produksi
        samesite="Lax",
        path="/",
    )


# --------------------------------------------------------------------------- #
# API: /api/login  (POST = login, GET = cek sesi)
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
        return jsonify({"ok": False, "message": msg, "status": {"logged_in": False}}), 401

    result = sikuli.run_one_cycle(session, nim_hint=nim)
    token = sikuli.encrypt_session(session, _secret())

    resp = make_response(
        jsonify(
            {
                "ok": True,
                "message": msg,
                "status": {
                    "logged_in": True,
                    "student": result["student"],
                    "courses": result["courses"],
                    "logs": [
                        {"time": _now(), "level": "SUCCESS", "message": "Login BERHASIL! Jadwal dimuat."}
                    ]
                    + result["logs"],
                },
            }
        ),
        200,
    )
    _set_session_cookie(resp, token)
    return resp


@app.get("/api/login")
def api_login_check():
    token = request.cookies.get(COOKIE_NAME)
    session = sikuli.decrypt_session(token, _secret())
    if not session:
        return jsonify({"ok": False, "status": {"logged_in": False}}), 200
    return jsonify({"ok": True, "status": {"logged_in": True}}), 200


# --------------------------------------------------------------------------- #
# API: /api/check  (POST = 1 siklus: ambil jadwal → cek & isi absen)
# --------------------------------------------------------------------------- #
@app.post("/api/check")
def api_check():
    token = request.cookies.get(COOKIE_NAME)
    session = sikuli.decrypt_session(token, _secret())
    if not session:
        return (
            jsonify(
                {"ok": False, "message": "Sesi habis, silakan login ulang",
                 "status": {"logged_in": False}}
            ),
            401,
        )

    data = request.get_json(silent=True) or {}
    nim = (data.get("nim") or "").strip()

    result = sikuli.run_one_cycle(session, nim_hint=nim)
    new_token = sikuli.encrypt_session(session, _secret())  # refresh cookie

    resp = make_response(
        jsonify(
            {
                "ok": True,
                "status": {
                    "logged_in": True,
                    "student": result["student"],
                    "courses": result["courses"],
                    "logs": [
                        {"time": _now(), "level": "INFO", "message": "Cek siklus selesai."}
                    ]
                    + result["logs"],
                },
            }
        ),
        200,
    )
    _set_session_cookie(resp, new_token)
    return resp


# --------------------------------------------------------------------------- #
# API: /api/logout
# --------------------------------------------------------------------------- #
@app.post("/api/logout")
def api_logout():
    resp = make_response(jsonify({"ok": True, "message": "Logout berhasil"}), 200)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


# --------------------------------------------------------------------------- #
# Static frontend (Flask auto-serve public/ karena static_folder="public")
# --------------------------------------------------------------------------- #
# "/"               → public/index.html
# "/style.css"      → public/style.css
# "/script.js"      → public/script.js
# (Flask handles via static_url_path="")

@app.errorhandler(404)
def not_found(_e):
    # Untuk path non-API yang tidak ada → fallback ke index.html (SPA-friendly)
    if not request.path.startswith("/api/"):
        return app.send_static_file("index.html")
    return jsonify({"ok": False, "message": "Not Found"}), 404


# --------------------------------------------------------------------------- #
# Local dev
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)