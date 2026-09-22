"""
dev_server.py — Server preview lokal (Flask) untuk development.

Mencerminkan endpoint Vercel (api/login, api/check, api/logout) dan menyajikan
file statis dari public/. Dipakai untuk preview lokal & oleh skill publish.

Di Vercel, file ini TIDAK dipakai (yang dipakai api/*.py sebagai serverless).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from lib import sikuli, http_utils

app = Flask(__name__, static_folder=None)

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")


@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(PUBLIC, path)


# ------------------------- API (mirror Vercel api/*.py) -------------------------
@app.route("/api/login", methods=["POST", "GET"])
def api_login():
    if request.method == "GET":
        token = request.cookies.get(http_utils.COOKIE_NAME)
        session = sikuli.decrypt_session(token, http_utils.get_secret())
        return jsonify({"ok": bool(session), "status": {"logged_in": bool(session)}})

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
    token = sikuli.encrypt_session(session, http_utils.get_secret())
    import datetime
    logs = [{"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "level": "SUCCESS", "message": "Login BERHASIL! Jadwal dimuat."}] + result["logs"]
    resp = jsonify({
        "ok": True,
        "message": msg,
        "status": {"logged_in": True, "student": result["student"],
                   "courses": result["courses"], "logs": logs},
    })
    resp.set_cookie(http_utils.COOKIE_NAME, token, httponly=True, samesite="Strict",
                    max_age=86400, secure=request.is_secure)
    return resp


@app.route("/api/check", methods=["POST", "GET"])
def api_check():
    token = request.cookies.get(http_utils.COOKIE_NAME)
    session = sikuli.decrypt_session(token, http_utils.get_secret())
    if not session:
        return jsonify({"ok": False, "message": "Sesi habis, login ulang",
                        "status": {"logged_in": False}}), 401

    data = request.get_json(silent=True) or {}
    nim_hint = (data.get("nim") or "").strip()
    try:
        result = sikuli.run_one_cycle(session, nim_hint=nim_hint)
        new_token = sikuli.encrypt_session(session, http_utils.get_secret())
        import datetime
        logs = result["logs"] or [{
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO", "message": "Cek ulang: belum ada sesi absen terbuka."}]
        resp = jsonify({
            "ok": True,
            "status": {"logged_in": True, "student": result["student"],
                       "courses": result["courses"], "logs": logs},
        })
        resp.set_cookie(http_utils.COOKIE_NAME, new_token, httponly=True, samesite="Strict",
                        max_age=86400, secure=request.is_secure)
        return resp
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error siklus: {e}"}), 500


@app.route("/api/logout", methods=["POST", "GET"])
def api_logout():
    resp = jsonify({"ok": True, "message": "Sesi dihapus"})
    resp.set_cookie(http_utils.COOKIE_NAME, "", expires=0, httponly=True, samesite="Strict")
    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
