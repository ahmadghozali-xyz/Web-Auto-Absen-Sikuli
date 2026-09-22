"""api/login.py — Vercel serverless: login ke Sikuli & set cookie sesi terenkripsi."""

import os
import sys

# Pastikan root proyek ada di sys.path agar `lib` bisa di-import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from lib import sikuli, http_utils


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = http_utils.read_json_body(self)
        nim = (data.get("nim") or "").strip()
        password = (data.get("password") or "").strip()
        timeout = int(data.get("timeout", 10) or 10)

        if not nim or not password:
            http_utils.send_json(self, 400, {"ok": False, "message": "NIM dan Password wajib diisi"})
            return

        session, ok, msg = sikuli.login(nim, password, timeout=timeout)
        if not ok:
            http_utils.send_json(self, 401, {"ok": False, "message": msg, "status": {"logged_in": False}})
            return

        # Ambil profil + jadwal sekali untuk dashboard
        result = sikuli.run_one_cycle(session, nim_hint=nim)
        token = sikuli.encrypt_session(session, http_utils.get_secret())

        http_utils.send_json(
            self, 200,
            {
                "ok": True,
                "message": msg,
                "status": {
                    "logged_in": True,
                    "student": result["student"],
                    "courses": result["courses"],
                    "logs": [{"time": _now(), "level": "SUCCESS", "message": "Login BERHASIL! Jadwal dimuat."}
                             ] + result["logs"],
                },
            },
            set_cookie=http_utils.make_cookie(token),
        )

    def do_GET(self):
        # Cek apakah masih punya sesi valid (cookie)
        cookies = http_utils.parse_cookies(self)
        token = cookies.get(http_utils.COOKIE_NAME)
        session = sikuli.decrypt_session(token, http_utils.get_secret())
        if not session:
            http_utils.send_json(self, 200, {"ok": False, "status": {"logged_in": False}})
            return
        http_utils.send_json(self, 200, {"ok": True, "status": {"logged_in": True}})


def _now():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
