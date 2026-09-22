"""lib/http_utils.py — helper kecil untuk BaseHTTPRequestHandler di Vercel."""

import json
import os

COOKIE_NAME = "sikuli_sess"


def get_secret():
    """Ambil secret untuk enkripsi cookie. Wajib diset di env Vercel."""
    s = os.environ.get("SESSION_SECRET") or os.environ.get("SESSION_KEY")
    if not s:
        # Fallback dev lokal (JANGAN pakai di produksi)
        s = "dev-only-insecure-secret-please-set-SESSION_SECRET"
    return s


def read_json_body(handler):
    """Baca & parse JSON body dari request."""
    length = int(handler.headers.get("Content-Length", 0) or 0)
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw or b"{}")
    except Exception:
        return {}


def parse_cookies(handler):
    """Parse header Cookie jadi dict."""
    raw = handler.headers.get("Cookie", "")
    out = {}
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            out[k] = v
    return out


def send_json(handler, status, data, set_cookie=None):
    """Kirim respons JSON, opsional set cookie."""
    body = json.dumps(data).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    if set_cookie is not None:
        handler.send_header("Set-Cookie", set_cookie)
    handler.end_headers()
    handler.wfile.write(body)


def make_cookie(value, max_age=86400):
    """Buat string Set-Cookie yang aman."""
    return (
        f"{COOKIE_NAME}={value}; Path=/; HttpOnly; Secure; SameSite=Strict; "
        f"Max-Age={max_age}"
    )


def clear_cookie():
    """Buat string Set-Cookie untuk menghapus cookie."""
    return f"{COOKIE_NAME}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0"
