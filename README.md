<div align="center">

# Auto Absen Sikuli — Web Edition

**Versi web dari bot absen otomatis untuk portal mahasiswa UMRI.**<br>
Dari yang dulu jalan di Terminal → sekarang cukup buka di browser, klik tombol, biarkan bot bekerja.

[![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Dev-Flask-000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](#-lisensi)

</div>

---

## Apa ini?

**Auto Absen Sikuli** adalah program yang membantu kamu **mengisi daftar hadir (presensi) online** di portal mahasiswa [sikuli.umri.ac.id](https://sikuli.umri.ac.id) secara **otomatis**.

Versi aslinya (dari [repo ini](https://github.com/ahmadghozali-xyz/auto-absen-sikuli)) berjalan di **Terminal / Command Prompt** — harus install Python, ketik perintah, dan kalau ditutup bot-nya berhenti. Ribet buat yang belum biasa.

**Web Edition** ini mengubahnya jadi **aplikasi web**:

| Dulu (CLI) | Sekarang (Web) |
|---|---|
| Buka Terminal, ketik `python absen.py` | Buka browser → klik **Mulai Bot** |
| Log muncul sebagai teks hitam-putih | Log berwarna + auto-scroll di layar |
| Tutup Terminal → bot mati | Bisa ditab browser, polling jalan di latar |
| Susah buat non-IT | Tinggal isi NIM + password, klik tombol |

> [!IMPORTANT]
> Program ini ** membantu**, bukan menggantikan kehadiran fisik. Tetap hadir di kelas ya. Bot hanya mengisi form presensi online saat sesi absen dibuka dosen.

---

## Fitur

- **Login aman** — kredensial hanya dipakai sesaat untuk login, **tidak disimpan** di server.
- **Ambil jadwal otomatis** — setelah login, jadwal mata kuliah hari ini langsung muncul.
- **Bot polling** — mengecek sesi presensi yang terbuka setiap 30 detik, lalu mengisi form kehadiran.
- **Live log console** — lihat proses absen real-time, berwarna hijau (sukses) / merah (gagal) / kuning (menunggu).
- **Tema gelap modern (OLED)** — desain dark mode elegan, ramah mata, hemat baterai.
- **Responsif** — jalan di HP, tablet, dan laptop.
- **Siap deploy ke Vercel** — gratis, dapat URL publik dalam menit.

---

## Cara Kerja (singkat & simpel)

> Analogi: seperti kamu minta teman **menunggu di depan kelas** dan **langsung tanda tangan absen** begitu dosen buka sesi — tanpa kamu harus bolak-balik cek sendiri.

```
Kamu buka web → isi NIM + password → klik "Masuk"
        │
        ▼
   Bot login ke sikuli.umri.ac.id  (pakai kredensial kamu)
        │
        ▼
   Bot ambil jadwal hari ini  → tampil di layar
        │
        ▼
   Kamu klik "Mulai Bot"
        │
        ▼
   ┌─────────────►  Cek sesi presensi yang terbuka (tiap 30 detik)
   │              │
   │              ▼
   │         Ada yang terbuka? ── TIDAK ──► tunggu, cek lagi 30 detik
   │              │
   │             YA
   │              ▼
   │         Isi form kehadiran → log "Absen BERHASIL"
   │              │
   └──────────────┘
```

**Bagian teknis (boleh dilewati):** tiap siklus polling, browser memanggil satu fungsi di server (login pakai sesi yang sudah terenkripsi di cookie → ambil jadwal → cari link absen → submit form). Tidak ada proses yang nyangkut di server 24 jam, karena Vercel bersifat *serverless* (fungsi jalan hanya saat dipanggil).

---

## Tampilan

UI pakai design system dari [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (dark mode OLED + font Fira Code/Sans).

```
┌─────────────────────────────────────────────┐
│  🟢 Auto Absen Sikuli — Web Edition         │   ← header + status
├─────────────────────────────────────────────┤
│  [ NIM ________ ] [ Password ________ ]    │   ← login
│              [ Masuk & Ambil Jadwal ]       │
├─────────────────────────────────────────────┤
│  Profil: Nama · NIM · Semester              │   ← dashboard
│  Jadwal: [Matkul A]  [Matkul B]  [Matkul C] │   ← kartu jadwal
├─────────────────────────────────────────────┤
│  [▶ Mulai Bot]  [⏹ Stop]  [↻ Refresh]       │   ← kontrol
├─────────────────────────────────────────────┤
│  > [12:01:05] [SUCCESS] Absen BERHASIL...   │   ← live log console
│  > [12:01:35] [INFO] Menunggu sesi...       │
└─────────────────────────────────────────────┘
```

---

## Teknologi yang Dipakai

| Bagian | Teknologi | Kenapa |
|---|---|---|
| Frontend (tampilan) | HTML, CSS, JavaScript murni | Tanpa framework → ringan & cepat |
| Backend (API + serve statis) | Python 3.12 + Flask | Pola "Zero-config Flask" yang Vercel dukung penuh |
| HTTP client & parsing | `requests` + `BeautifulSoup` | Sama seperti versi CLI asli |
| Keamanan sesi | `cryptography` (Fernet encryption) | Cookie sesi dienkripsi, tidak bisa dibaca orang lain |
| Hosting | Vercel (serverless Python runtime) | Gratis, otomatis, dapat HTTPS |

---

## Struktur Proyek

```
auto-absen-sikuli-web/
├── app.py                  # Flask app (entrypoint Vercel: variabel `app`)
│                           #   Route API: /api/login, /api/check, /api/logout
│                           #   Serve statis: public/index.html, /style.css, /script.js
├── lib/                    # Logika inti bot (dipakai app.py)
│   └── sikuli.py           #   login, ambil jadwal, absen (adaptasi absen.py)
├── public/                 # File statis (dilihat browser)
│   ├── index.html          #   struktur halaman
│   ├── style.css           #   tampilan (dark OLED)
│   └── script.js           #   logika polling & tampilan
├── pyproject.toml          # Pin entrypoint Vercel: tool.vercel.entrypoint = "app:app"
├── requirements.txt        # Dependency Python (flask, requests, beautifulsoup4, cryptography)
├── vercel.json             # Konfigurasi deploy Vercel (maxDuration, cleanUrls)
├── .python-version         # Pin versi Python 3.12 (default Vercel)
└── README.md               # File ini
```

---

## Cara Pakai

Ada **dua jalur**. Untuk mahasiswa non-IT, **jalur A (online)** paling gampang.

### Jalur A — Pakai yang sudah online (paling gampang)

Kalau kamu cuma mau **pakai**, nggak mau repot install:

1. Klik link deploy (akan diisi setelah kamu upload ke Vercel).
2. Isi **NIM** + **password Sikuli** kamu.
3. Klik **Masuk & Ambil Jadwal**.
4. Klik **▶ Mulai Bot**. Biarkan tab terbuka.

Selesai. Bot akan absen otomatis tiap 30 detik selama sesi presensi terbuka.

### Jalur B — Install sendiri di laptop

Butuh sedikit keberanian, tapi tidak serumit kelihatannya.

**Yang harus diinstall dulu:**
- [Python 3.10+](https://python.org/downloads) — cek: buka Terminal/CMD, ketik `python --version`
- [Git](https://git-scm.com/downloads) — untuk download source code

**Langkah-langkah:**

```bash
# 1. Download kodenya
git clone https://github.com/USERNAME-KAMU/Web-Auto-Absen-Sikuli.git
cd Web-Auto-Absen-Sikuli

# 2. Install dependency Python (Flask, requests, dll)
pip install -r requirements.txt

# 3. Jalankan server lokal (Flask dev server)
python app.py

# 4. Buka browser ke:
#    http://localhost:5000
```

> [!NOTE]
> `USERNAME-KAMU` ganti dengan username GitHub kamu sendiri (sesuai repo yang dibuat).

---

## Deploy ke Vercel (dapat URL publik gratis)

Ini langkah untuk **publish ke internet** biar bisa diakses dari HP mana saja.

### Prasyarat
1. Bikin akun gratis di [vercel.com](https://vercel.com) (bisa login pakai GitHub).
2. Repo ini sudah ada di GitHub kamu (lihat bagian "Cara Upload" di bawah).

### Langkah

1. Login ke [vercel.com](https://vercel.com) → klik **Add New → Project**.
2. Pilih repo `Web-Auto-Absen-Sikuli` dari daftar.
3. Di bagian **Environment Variables**, tambah satu variabel:

   | Name | Value |
   |---|---|
   | `SESSION_SECRET` | kode rahasia acak (lihat cara buat di bawah) |

   Buat kode rahasia: buka Terminal, jalankan `openssl rand -hex 32`, copy hasilnya, paste ke Value.

4. Klik **Deploy**. Tunggu ±1 menit.
5. Selesai! Dapat URL seperti `https://web-auto-absen-sikuli.vercel.app`.

> [!TIP]
> `SESSION_SECRET` dipakai untuk **mengenkripsi cookie sesi kamu**. Tanpa ini, app tetap jalan pakai key default, tapi **sangat disarankan set** supaya aman.

> [!NOTE]
> **Kenapa Flask, bukan file-based `/api/*.py`?** Versi awal project ini pakai folder `/api/` dengan handler `BaseHTTPRequestHandler` (pola lama Vercel). Tapi sejak 2024, Vercel default-nya pakai **Python framework preset** (Flask/FastAPI via `app.py` + `pyproject.toml`). Pola `/api/` sekarang hanya untuk proyek lama. Oleh karena itu project ini disederhanakan jadi **satu Flask app** di `app.py` — lebih bersih, lebih cepat, dan langsung kedeteksi Vercel tanpa konfigurasi tambahan.

---

## Environment Variables

Hanya satu:

| Nama | Wajib? | Kegunaan |
|---|---|---|
| `SESSION_SECRET` | Wajib untuk produksi | Kunci rahasia buat enkripsi cookie sesi (Fernet). Pakai string acak 32+ karakter. |

---

## API Endpoints

Untuk yang ingin tahu / ingin kembangkan:

| Method | Path | Fungsi |
|---|---|---|
| `POST` | `/api/login` | Login ke Sikuli, simpan sesi di cookie terenkripsi |
| `GET` | `/api/login` | Cek apakah masih ada sesi valid |
| `POST` | `/api/check` | Jalankan 1 siklus: ambil jadwal → cek & isi absen |
| `POST` | `/api/logout` | Hapus sesi |

Contoh response `/api/login` sukses:
```json
{
  "ok": true,
  "message": "Login Berhasil",
  "status": {
    "logged_in": true,
    "student": {"nama": "...", "nim": "...", "semester": "..."},
    "courses": [{"mk": "...", "ruangan": "...", "absen_link": "..."}],
    "logs": [{"time": "...", "level": "SUCCESS", "message": "..."}]
  }
}
```

---

## FAQ

<details>
<summary><b>Kredensial saya disimpan tidak?</b></summary>

**Tidak.** Password hanya dipakai sesaat untuk login ke `sikuli.umri.ac.id`, lalu hilang dari memori. Yang disimpan di cookie browser hanya **sesi login** (PHPSESSID) dalam bentuk **terenkripsi**. Server tidak punya database, tidak menyimpan NIM/password siapa pun.
</details>

<details>
<summary><b>Kenapa harus klik "Mulai Bot", nggak otomatis jalan terus?</b></summary>

Karena deploy di Vercel (serverless), bot tidak bisa jalan 24 jam di server. Polling tiap 30 detik **dijalankan dari browser kamu** (tab harus tetap terbuka). Selama tab terbuka, bot terus cek sesi presensi.
</details>

<details>
<summary><b>Kenapa login saya bilang "NIM atau Password salah"?</b></summary>

Pastikan:
1. NIM & password benar (coba login manual di sikuli.umri.ac.id dulu).
2. Internet stabil.
3. Portal tidak sedang maintenance.
</details>

<details>
<summary><b>Aman nggak pakai ini?</b></summary>

Kode ini **open-source** — siapa pun bisa baca dan audit. Tidak ada kode tersembunyi yang ngirim data kamu ke pihak ketiga. Tapi tetap: **pakai dengan risiko sendiri**, dan utamakan hadir fisik di kelas.
</details>

<details>
<summary><b>Bisa untuk kampus lain?</b></summary>

Saat ini khusus portal `sikuli.umri.ac.id`. Kalau portal kampusmu mirip (berbasis PHP + form login biasa), kemungkinan bisa diadaptasi dengan ubah `BASE_URL` di `lib/sikuli.py`.
</details>

---

## Keamanan & Privasi

- **Tidak ada database** — server tidak menyimpan data mahasiswa apapun.
- **Cookie terenkripsi** — sesi login disimpan di cookie browser dalam bentuk terenkripsi (Fernet/AES). Token yang ditamper akan ditolak otomatis.
- **HTTPS** — Vercel memberi SSL gratis, koneksi terenkripsi end-to-end.
- **Tidak ada tracking** — tidak ada Google Analytics, tidak ada iklan, tidak ada script pihak ketiga.

---

## Disclaimer

> [!WARNING]
> Program ini dibuat untuk **tujuan edukasi & otomasi kehadiran online**. Gunakan dengan bijak. Tetap **hadir fisik** di kelas — bot hanya membantu mengisi form presensi online, bukan menggantikan kehadiranmu. Penyalahgunaan (misal untuk bolos) bukan tanggung jawab pembuat.

---

## Kontribusi

Mau bantu? Bisa:
- Laporkan bug via [Issues](../../issues)
- Ajukan perbaikan via [Pull Request](../../pulls)
- Bantu adaptasi untuk kampus lain

---

## Kredit

- Logika bot asli: [ahmadghozali-xyz/auto-absen-sikuli](https://github.com/ahmadghozali-xyz/auto-absen-sikuli)
- Design system: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
- Web adaptation & deploy: dibungkus jadi aplikasi web siap-deploy.

---

## Lisensi

MIT License — bebas pakai, ubah, sebarkan. Lihat file `LICENSE` (kalau ada) atau [MIT summary](https://choosealicense.com/licenses/mit/).

---

<div align="center">

**Dibuat untuk mahasiswa UMRI.** 🎓<br>
Pakai bijak, tetap kuliah, tetap semangat.

</div>
