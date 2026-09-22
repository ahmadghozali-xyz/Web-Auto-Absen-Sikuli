<div align="center">

# Auto Absen Sikuli — Web Edition

**Versi web dari bot absen otomatis untuk portal mahasiswa UMRI.**<br>
Login sekali, bot kerja 24/7 — sampai wisuda.

[![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask-000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](#-lisensi)

</div>

---

## 🌟 Apa ini?

**Auto Absen Sikuli** adalah program yang membantu kamu **mengisi daftar hadir (presensi) online** di portal mahasiswa [sikuli.umri.ac.id](https://sikuli.umri.ac.id) secara **otomatis**.

Versi aslinya (dari [repo ini](https://github.com/ahmadghozali-xyz/auto-absen-sikuli)) berjalan di **Terminal / Command Prompt** — harus install Python, ketik perintah, dan kalau ditutup bot-nya berhenti.

**Web Edition** ini mengubahnya jadi **aplikasi web** dengan bot yang **jalan terus di server** — jadi walaupun kamu **tutup browser, matikan HP, atau keluar rumah**, bot-nya tetap bekerja selama server-nya hidup.

| Dulu (CLI) | Sekarang (Web Edition) |
|---|---|
| Buka Terminal, ketik `python absen.py` | Buka browser → klik **Mulai Bot** |
| Tutup Terminal → bot mati | Bot **tetap jalan di server** 24/7 |
| HP harus terhubung internet & browser terbuka | **Tutup HP, browser, internet** — bot jalan terus |
| Log hitam putih | Log berwarna + auto-scroll, tema terang/gelap |
| Susah buat non-IT | Tinggal login di browser, klik tombol |

> [!IMPORTANT]
> Program ini **membantu**, bukan menggantikan kehadiran fisik. Tetap hadir di kelas ya. Bot hanya mengisi form presensi online saat sesi absen dibuka dosen.

---

## ✨ Fitur

- 🤖 **Bot 24/7** — jalan di server, polling tiap 30 detik, **aktif sampai wisuda**.
- 🔐 **Login aman** — kredensial hanya dipakai sesaat untuk login, **tidak disimpan** permanen.
- 📅 **Jadwal otomatis** — setelah login, jadwal mata kuliah hari ini langsung muncul.
- 📜 **Live log console** — lihat proses absen real-time, berwarna per level.
- 🎨 **Tema retro terang/gelap** — default terang (cream hangat), toggle ke gelap kapan saja.
- 📱 **Responsif** — jalan di HP, tablet, laptop.
- 🚀 **Deploy gratis** — Railway / Render / Fly.io, dapat URL publik dalam menit.

---

## 🤔 Cara Kerja (singkat & simpel)

> Analogi: seperti kamu minta **asisten pribadi** yang **duduk di depan portal Sikuli** 24 jam. Begitu dosen buka sesi presensi, dia langsung **tanda tangan absen** untuk kamu — tanpa kamu harus buka HP, buka browser, atau bahkan harus bangun dari tidur.

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
   │         Ada yang terbuka? ── TIDAK ──► tunggu 30 detik, cek lagi
   │              │
   │             YA
   │              ▼
   │         Isi form kehadiran → log "Absen BERHASIL"
   │              │
   └──────────────┘
   ↑                                                            │
   └──────── bot tetap jalan walau kamu tutup browser ──────────┘
```

**Kenapa bisa tetap jalan?** Bot polling jalan di **server** sebagai *background thread*, bukan di browser kamu. Tutup browser, matikan HP, ganti jaringan — server tetap ngecek Sikuli. Kamu bisa buka HP besoknya, lihat log: *"Absen BERHASIL untuk Matkul X jam 09:30"*.

---

## 🖼 Tampilan

UI pakai gaya **retro modern** — kartu dengan border tebal dan shadow "stempel", font serif elegan untuk judul, warna hangat (terracotta, teal, mustard). Default tema **terang** (cream), bisa di-toggle ke **gelap** lewat ikon bulan/matahari di pojok kanan atas.

```
┌──────────────────────────────────────────────────────┐
│  ✓ Auto Absen    [Sikuli UMRI]               ☀  ⏏   │   ← topbar
├──────────────────────────────────────────────────────┤
│  [● Bot Auto Absen]  [● 24/7 Aktif]                 │
│                                                      │
│  Login Sekali,                                       │
│   Otomatis Absen                                     │   ← hero
│                                                      │
│  Bot auto absen yang mengecek portal Sikuli setiap   │
│  30 detik dan langsung mengisi kehadiran begitu      │
│  dosen membuka sesi. Aktif 24/7 sampai wisuda —      │
│  tidak akan ketinggalan 1 absen pun.                 │
│                                                      │
│  [ NIM _______________ ]                             │
│  [ Password ___________ ]  [👁]                      │   ← form
│             [ Masuk & Mulai Absen ]                   │
└──────────────────────────────────────────────────────┘
```

---

## 🛠 Teknologi

| Bagian | Teknologi | Kenapa |
|---|---|---|
| Frontend | HTML + CSS + JavaScript murni | Tanpa framework → ringan & cepat |
| Backend | Python 3.11 + Flask + Gunicorn | Standar, mudah deploy |
| Bot engine | `threading` + `requests` + `BeautifulSoup` | Background thread polling 30 detik |
| HTTP client | `requests` | Sama seperti versi CLI asli |
| Keamanan sesi | `cryptography` (Fernet encryption) | Cookie sesi dienkripsi, tidak bisa dibaca orang lain |
| Hosting | Railway / Render / Fly.io (persistent) | **Wajib** — serverless (Vercel) tidak bisa untuk bot 24/7 |

---

## 📂 Struktur File

```
Web-Auto-Absen-Sikuli/
├── app.py              # Flask app: API + serve public/
│                       #   Endpoint: /api/{login,start,stop,status,refresh,logout}
├── lib/
│   ├── sikuli.py       #   Fungsi stateless: login, ambil jadwal, absen
│   └── bot.py          #   SikuliBot class: thread + registry bot per user
├── public/             # Frontend statis
│   ├── index.html      #   Struktur UI retro
│   ├── style.css       #   Tema terang/gelap, palet retro hangat
│   └── script.js       #   Polling /api/status, toggle tema, kontrol bot
├── Procfile            # web: gunicorn app:app (Railway/Render/Heroku)
├── requirements.txt    # Dependency Python
├── runtime.txt         # Pin Python 3.11
└── README.md           # File ini
```

---

## 🚀 Cara Pakai

### Jalur A — Pakai yang sudah online (paling gampang)

1. Buka link deploy (lihat README kamu atau minta linknya).
2. Isi **NIM** + **password Sikuli** kamu.
3. Klik **Masuk & Mulai Absen**.
4. Klik **▶ Mulai Bot** di dashboard.

Selesai. **Tutup browser, matikan HP, tidur malam** — bot tetap kerja di server.

### Jalur B — Install sendiri di laptop

**Prasyarat:**
- [Python 3.10+](https://python.org/downloads)
- [Git](https://git-scm.com/downloads)

```bash
# 1. Download
git clone https://github.com/ahmadghozali-xyz/Web-Auto-Absen-Sikuli.git
cd Web-Auto-Absen-Sikuli

# 2. Install dependency
pip install -r requirements.txt

# 3. Jalankan
python app.py

# 4. Buka http://localhost:5000
```

---

## ☁️ Deploy ke Cloud (dapat URL publik)

Bot **harus** di-host di server yang **persistent** (bukan serverless). Rekomendasi gratis:

### 🟣 Railway (paling gampang, recommended)

1. Login ke [railway.app](https://railway.app) dengan akun GitHub.
2. **New Project → Deploy from GitHub repo** → pilih `Web-Auto-Absen-Sikuli`.
3. Tunggu Railway deteksi otomatis (Python + Procfile).
4. Klik **Variables** → tambah satu variabel:

   | Name | Value |
   |---|---|
   | `SESSION_SECRET` | buka Terminal lokal, jalankan `openssl rand -hex 32`, paste hasilnya |

5. Klik **Deploy** → tunggu ±1-2 menit.
6. Klik **Settings → Generate Domain** untuk dapat URL publik.
7. Buka URL → login → **Mulai Bot**.

> 💡 Railway free tier: **$5 credit/bulan** (~500 jam runtime). Cukup untuk 1 service kecil 24/7.

### 🟢 Render (alternatif, free tier permanen)

1. Login ke [render.com](https://render.com) dengan GitHub.
2. **New → Web Service** → pilih repo `Web-Auto-Absen-Sikuli`.
3. Isi:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
4. **Environment** → tambah `SESSION_SECRET` (sama seperti di atas).
5. Pilih **Free** instance → klik **Create Web Service**.
6. Tunggu deploy selesai.

> ⚠️ Render free tier: **mati setelah 15 menit tidak ada traffic**. Untuk 24/7 pakai **Starter** ($7/bulan) atau Railway free.

### 🟣 Fly.io (advanced, generous free tier)

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
fly launch --no-deploy
fly secrets set SESSION_SECRET=$(openssl rand -hex 32)
fly deploy
```

---

## 🔐 Environment Variables

| Nama | Wajib? | Kegunaan |
|---|---|---|
| `SESSION_SECRET` | **Wajib untuk produksi** | Kunci enkripsi cookie (Fernet). Buat dengan `openssl rand -hex 32`. |
| `PORT` | Otomatis di-set host | Port untuk bind gunicorn (default 5000). |

---

## 📡 API Endpoints

| Method | Path | Fungsi |
|---|---|---|
| `POST` | `/api/login` | Login ke Sikuli, simpan sesi di cookie terenkripsi |
| `GET`  | `/api/status` | Snapshot state bot: student, courses, logs, running |
| `POST` | `/api/start` | Mulai bot thread (polling 24/7) |
| `POST` | `/api/stop` | Stop bot thread |
| `POST` | `/api/refresh` | Satu siklus cek manual (tanpa start) |
| `POST` | `/api/logout` | Stop bot, hapus cookie |

Response `/api/status`:
```json
{
  "ok": true,
  "logged_in": true,
  "state": {
    "running": true,
    "student": {"nama": "...", "nim": "...", "semester": "..."},
    "courses": [{"mk": "...", "ruangan": "...", "absen_link": "..."}],
    "logs": [{"time": "10:23:01", "level": "SUCCESS", "message": "Absen BERHASIL..."}],
    "loop_count": 42,
    "last_check": "10:23:01",
    "poll_interval": 30
  }
}
```

---

## ❓ FAQ

<details>
<summary><b>Kredensial saya disimpan tidak?</b></summary>

**Tidak.** Password hanya dipakai sesaat untuk login ke `sikuli.umri.ac.id`, lalu hilang dari memori. Yang disimpan di cookie browser hanya **sesi login** (PHPSESSID) dalam bentuk **terenkripsi**. Server tidak punya database, tidak menyimpan NIM/password siapa pun.
</details>

<details>
<summary><b>Kalau saya tutup browser / matikan HP, bot tetap jalan?</b></summary>

**Ya!** Bot polling berjalan di **server** sebagai background thread. Tutup browser, matikan HP, ganti jaringan — server tetap ngecek Sikuli tiap 30 detik. Kalau ragu, buka HP besoknya dan lihat log konsol — di situ ada bukti bot sudah jalan beberapa kali.
</details>

<details>
<summary><b>Kalau server-nya mati / restart?</b></summary>

Bot akan berhenti. Tapi:
1. Sesi login kamu (cookie) **tetap valid** sampai 8 jam.
2. Buka lagi web-nya, klik **Mulai Bot** lagi — server akan login ulang otomatis pakai cookie.
3. Pilih host yang reliable (Railway/Render paid tier, VPS sendiri) untuk uptime tinggi.
</details>

<details>
<summary><b>Kenapa tidak pakai Vercel lagi?</b></summary>

Vercel itu **serverless** — fungsi cuma jalan saat dipanggil, lalu mati. Tidak ada proses 24 jam. Untuk bot polling 30 detik, kita butuh server yang **persistent** — itulah Railway, Render, atau Fly.io. Versi sebelumnya (Vercel) ada di branch/history repo kalau mau bandingkan.
</details>

<details>
<summary><b>Kenapa login saya bilang "NIM atau Password salah"?</b></summary>

Pastikan:
1. NIM & password benar (coba login manual di sikuli.umri.ac.id dulu).
2. Internet stabil di server (cek log Railway/Render).
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

<details>
<summary><b>Berapa biaya hosting?</b></summary>

**Gratis** untuk penggunaan pribadi (Railway free $5/bulan cukup, atau Render free dengan catatan idle 15 menit). Kalau mau 100% uptime tanpa jeda, Render Starter $7/bulan atau Railway Hobby $5/bulan.
</details>

---

## 🛡 Keamanan & Privasi

- **Tidak ada database** — server tidak menyimpan data mahasiswa apapun.
- **Cookie terenkripsi** — sesi login disimpan di cookie browser dalam bentuk terenkripsi (Fernet/AES). Token yang ditamper akan ditolak otomatis.
- **HTTPS** — Railway/Render memberi SSL gratis.
- **Tidak ada tracking** — tidak ada Google Analytics, tidak ada iklan, tidak ada script pihak ketiga.

---

## ⚠️ Disclaimer

> [!WARNING]
> Program ini dibuat untuk **tujuan edukasi & otomasi kehadiran online**. Gunakan dengan bijak. Tetap **hadir fisik** di kelas — bot hanya membantu mengisi form presensi online, bukan menggantikan kehadiranmu. Penyalahgunaan (misal untuk bolos) bukan tanggung jawab pembuat.

---

## 🤝 Kontribusi

Mau bantu? Bisa:
- Laporkan bug via [Issues](../../issues)
- Ajukan perbaikan via [Pull Request](../../pulls)
- Bantu adaptasi untuk kampus lain

---

## 🙏 Kredit

- Logika bot asli: [ahmadghozali-xyz/auto-absen-sikuli](https://github.com/ahmadghozali-xyz/auto-absen-sikuli)
- Design system retro: terinspirasi dari pola desain vintage/modern (Playfair Display + Nunito + Caveat, palet hangat earth-tone)
- Web adaptation & deploy: dibungkus jadi aplikasi web persistent siap-deploy.

---

## 📜 Lisensi

MIT License — bebas pakai, ubah, sebarkan.

---

<div align="center">

**Program aman dan sudah teruji sampai wisuda, dwyor** 🎓<br>
Pakai bijak, tetap kuliah, tetap semangat.

</div>