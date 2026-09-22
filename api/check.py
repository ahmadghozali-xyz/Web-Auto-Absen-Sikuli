"""api/check.py — Vercel serverless: SATU siklus cek & absen (dipanggil browser tiap N detik)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from lib import sikuli, http_utils


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        cookies = http_utils.parse_cookies(self)
        token = cookies.get(http_utils.COOKIE_NAME)
        session = sikuli.decrypt_session(token, http_utils.get_secret())

        if not session:
            http_utils.send_json(self, 401, {
                "ok": False,
                "message": "Sesi habis, silakan login ulang",
                "status": {"logged_in": False},
            })
            return

        body = http_utils.read_json_body(self) or {}
        nim_hint = (body.get("nim") or "").strip()

        try:
            result = sikuli.run_one_cycle(session, nim_hint=nim_hint)
            # Perbarui cookie (mungkin server Sikuli merotasi session ID)
            new_token = sikuli.encrypt_session(session, http_utils.get_secret())
            http_utils.send_json(
                self, 200,
                {
                    "ok": True,
                    "status": {
                        "logged_in": True,
                        "student": result["student"],
                        "courses": result["courses"],
                        "logs": result["logs"] or [_idle()],
                    },
                },
                set_cookie=http_utils.make_cookie(new_token),
            )
        except Exception as e:
            http_utils.send_json(self, 500, {"ok": False, "message": f"Error siklus: {e}"})

    # GET = alias POST untuk kemudahan polling sederhana
    def do_GET(self):
        self.do_POST()


def _idle():
    import datetime
    return {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "message": "Cek ulang: belum ada sesi absen terbuka.",
    }
