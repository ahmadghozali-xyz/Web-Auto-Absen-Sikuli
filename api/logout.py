"""api/logout.py — Vercel serverless: hapus cookie sesi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from lib import http_utils


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        http_utils.send_json(
            self, 200,
            {"ok": True, "message": "Sesi dihapus"},
            set_cookie=http_utils.clear_cookie(),
        )

    def do_GET(self):
        self.do_POST()
