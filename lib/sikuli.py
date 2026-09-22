"""
lib/sikuli.py — Logika inti bot absen Sikuli UMRI.

Adaptasi dari absen.py (ahmadghozali-xyz/auto-absen-sikuli).
Berisi fungsi-fungsi stateless untuk dipakai oleh:
  - lib/bot.py  (thread yang menjalankan polling loop)
  - app.py      (Flask routes)
"""

import re
import datetime
import json
import base64
import hashlib

import requests
from bs4 import BeautifulSoup

try:
    from cryptography.fernet import Fernet, InvalidToken
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False

BASE_URL = "https://sikuli.umri.ac.id"
LOGIN_URL = f"{BASE_URL}/auth/aksi/"
SCHEDULE_URL = f"{BASE_URL}/mahasiswa/jadwal"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# --------------------------------------------------------------------------- #
# SESSION BUILD / SERIALIZE
# --------------------------------------------------------------------------- #
def new_session(timeout=10):
    """Buat requests.Session baru dengan header default."""
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    return s


def _fernet(secret):
    """Buat Fernet dari secret string (panjang bebas -> di-hash jadi 32 byte)."""
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


# --------------------------------------------------------------------------- #
# COOKIE ENCRYPTION (multi-field: sid, nim, cookies)
# --------------------------------------------------------------------------- #
def encrypt_payload(sid: str, nim: str, session: requests.Session, secret: str) -> str:
    """Serialisasi {sid, nim, cookies} jadi token terenkripsi untuk cookie HttpOnly."""
    payload = {
        "s": sid,
        "n": nim,
        "c": dict(session.cookies),
    }
    if not _HAS_CRYPTO:
        # Fallback dev (TIDAK aman)
        raw = json.dumps(payload).encode()
        return base64.urlsafe_b64encode(raw).decode()
    f = _fernet(secret)
    return f.encrypt(json.dumps(payload).encode()).decode()


def decrypt_payload(token: str, secret: str) -> dict | None:
    """Balik token cookie jadi {sid, nim, cookies} atau None kalau invalid/expired."""
    if not token:
        return None
    try:
        if not _HAS_CRYPTO:
            raw = base64.urlsafe_b64decode(token.encode())
            data = json.loads(raw)
        else:
            f = _fernet(secret)
            data = json.loads(f.decrypt(token.encode()).decode())
        # Sanitasi: minimal punya field 's' dan 'c'
        if not isinstance(data, dict) or "s" not in data or "c" not in data:
            return None
        return data
    except (InvalidToken, ValueError, Exception):
        return None


def session_from_payload(payload: dict, timeout=10) -> requests.Session:
    """Rekonstruksi requests.Session dari payload hasil decrypt_payload."""
    s = new_session(timeout=timeout)
    for k, v in (payload.get("c") or {}).items():
        s.cookies.set(k, v)
    return s


def refresh_cookie_token(token: str, secret: str) -> str | None:
    """Dekrip lalu re-enkrip (untuk perpanjang masa aktif cookie)."""
    data = decrypt_payload(token, secret)
    if not data:
        return None
    # Rebuild session supaya cookies fresh
    sess = session_from_payload(data)
    return encrypt_payload(data["s"], data.get("n", ""), sess, secret)


# --------------------------------------------------------------------------- #
# LOGIN
# --------------------------------------------------------------------------- #
def login(nim, password, timeout=10):
    """Login ke Sikuli. Mengembalikan (session, ok, message)."""
    s = new_session()
    payload = {"nim": nim.strip(), "password": password.strip(), "remember": "1"}
    try:
        resp = s.post(LOGIN_URL, data=payload, allow_redirects=True, timeout=timeout)
        resp.raise_for_status()
        if ("login" in resp.url.lower() or "auth" in resp.url.lower()) and "aksi" not in resp.url.lower():
            if "salah" in resp.text.lower() or "gagal" in resp.text.lower():
                return s, False, "NIM atau Password salah"
            return s, False, "Login gagal, periksa kembali kredensial Anda"
        return s, True, "Login Berhasil"
    except Exception as e:
        return s, False, f"Login gagal: {e}"


# --------------------------------------------------------------------------- #
# PROFIL & JADWAL
# --------------------------------------------------------------------------- #
def get_student_info(session, nim_hint=""):
    """Ambil profil + HTML jadwal. Mengembalikan dict."""
    try:
        resp = session.get(SCHEDULE_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        nama = "N/A"
        nim = nim_hint or "N/A"
        semester = "N/A"

        profile_box = soup.find(
            class_=re.compile(r"(user|profile|mahasiswa|biodata)", re.I)
        )
        if profile_box:
            text = profile_box.get_text()
            m_nim = re.search(r"\b\d{7,10}\b", text)
            if m_nim:
                nim = m_nim.group(0)

        for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "div", "span"]):
            t = el.get_text(strip=True)
            if "Semester" in t and len(t) < 30 and semester == "N/A":
                semester = t
            elif "NIM" in t and len(t) < 40 and nim == "N/A":
                nim = t.replace("NIM", "").strip(" :")

        return {"nama": nama, "nim": nim, "semester": semester, "html": resp.text}
    except Exception as e:
        return {"nama": "Error", "nim": "Error", "semester": str(e), "html": ""}


def parse_schedule(html_content):
    """Parsing kartu/row mata kuliah dari HTML jadwal."""
    soup = BeautifulSoup(html_content or "", "html.parser")
    courses = []

    cards = soup.find_all(
        class_=re.compile(r"(card|box|item|jadwal-item|row)", re.I)
    )
    if not cards:
        cards = soup.find_all("tr")

    for c in cards:
        text = c.get_text(" ", strip=True)
        if "Ruangan" in text or "Detail" in text or "Dosen" in text:
            mk_name = ""
            ruangan = ""
            detail = ""
            dosen = ""

            header = c.find(["h3", "h4", "h5", "h6", "strong", "b", "a"])
            if header:
                mk_name = header.get_text(strip=True)

            m_ruang = re.search(r"Ruangan\s*:\s*\[?([^\]\n]+)\]?", text, re.I)
            if m_ruang:
                ruangan = m_ruang.group(1).strip()

            m_detail = re.search(r"Detail\s*:\s*\[?([^\]\n]+)\]?", text, re.I)
            if m_detail:
                detail = m_detail.group(1).strip()

            m_dosen = re.search(r"Dosen\s*(?:Pengampu)?\s*:\s*([^\n]+)", text, re.I)
            if m_dosen:
                dosen = m_dosen.group(1).strip()

            absen_link = None
            for a in c.find_all("a", href=True):
                if any(
                    k in a.get_text().lower() or k in a["href"].lower()
                    for k in ["absen", "presensi", "hadir", "masuk"]
                ):
                    absen_link = a["href"]
                    if not absen_link.startswith("http"):
                        absen_link = BASE_URL + absen_link
                    break

            if mk_name or ruangan or detail:
                courses.append(
                    {
                        "mk": mk_name or "Mata Kuliah",
                        "ruangan": ruangan,
                        "detail": detail,
                        "dosen": dosen,
                        "absen_link": absen_link,
                    }
                )
    return courses


def check_and_do_attendance(session, courses):
    """Buka link absen yang terbuka & submit form kehadiran.
    Mengembalikan list log dicts untuk siklus ini."""
    logs = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for c in courses:
        if c["absen_link"]:
            try:
                resp = session.get(c["absen_link"], timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    form = soup.find("form")
                    if form:
                        action = form.get("action", c["absen_link"])
                        if not action.startswith("http"):
                            action = BASE_URL + action
                        data = {}
                        for inp in form.find_all("input"):
                            if inp.get("name"):
                                data[inp["name"]] = inp.get("value", "hadir")
                        post_resp = session.post(action, data=data, timeout=10)
                        if post_resp.status_code == 200:
                            logs.append(
                                {"time": now, "level": "SUCCESS",
                                 "message": f"Absen BERHASIL untuk {c['mk']} - {c['detail']}"}
                            )
                    else:
                        logs.append(
                            {"time": now, "level": "SUCCESS",
                             "message": f"Akses Presensi Berhasil: {c['mk']}"}
                        )
            except Exception as e:
                logs.append(
                    {"time": now, "level": "WARN",
                     "message": f"Gagal absen {c['mk']}: {e}"}
                )
    return logs


def run_one_cycle(session, nim_hint=""):
    """Satu siklus penuh: ambil jadwal -> cek & absen.
    Mengembalian dict {student, courses, logs}."""
    info = get_student_info(session, nim_hint=nim_hint)
    courses = parse_schedule(info.get("html", ""))
    logs = check_and_do_attendance(session, courses)
    return {
        "student": {"nama": info["nama"], "nim": info["nim"], "semester": info["semester"]},
        "courses": courses,
        "logs": logs,
    }