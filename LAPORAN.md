# Laporan Tugas: Modularisasi Aplikasi Monolitik — Perpustakaan Kampus

**Mata Kuliah:** Konstruksi & Rekayasa Perangkat Lunak  
**Topik Aplikasi:** Perpustakaan Kampus (Sirkulasi & Inventaris Buku)  
**Port Aplikasi:** `5002` (Docker) / `5000` (Lokal Python)  
**Penyusun:** Hafidz Alaziz  
**Repositori GitHub:** [https://github.com/HafidzAlaziz/tugas-modularisasi-aplikasi](https://github.com/HafidzAlaziz/tugas-modularisasi-aplikasi)

---

## 1. Ringkasan Eksekutif

Aplikasi awal `perpustakaan/app.py` merupakan sistem monolitik (~300 baris kode) di mana akses berkas JSON, aturan bisnis sirkulasi, validasi data, routing HTTP, template HTML inline, dan API JSON bercampur dalam satu berkas.

Tugas ini berhasil memecah aplikasi tersebut menjadi modul-modul terpisah dengan arsitektur berlapis (*layered architecture*) yang memenuhi kriteria:
1. **Logika bisnis murni terisolasi** di modul `layanan/` (terdiri dari 13 fungsi layanan independen tanpa dependensi Flask).
2. **Akses persistensi terisolasi** di modul `repositori/` (*single source of truth* untuk I/O `data.json`).
3. **Penyajian terpisah** pada modul `rute/` (Blueprint `web.py` dan `api.py`) serta template Jinja2 di `templates/`.
4. **Konfigurasi dan konstanta aturan** diekstraksi ke `config.py` sehingga tidak ada lagi *magic numbers*.
5. **Perilaku aplikasi 100% konsisten**, diverifikasi melalui uji *Cek Cepat*.

---

## 2. Struktur Modul & Berkas

```
perpustakaan/
├── app.py                      # Application Factory: create_app() & registrasi blueprint
├── config.py                   # Konstanta aturan bisnis (kuota, durasi, denda, prefix)
├── data.json                   # Berkas data persistensi
├── docker-compose.yml          # Konfigurasi container Docker
├── Dockerfile                  # Spesifikasi image Python 3.12-slim
├── requirements.txt            # Dependensi (Flask==3.0.3)
├── repositori/                 # Lapisan Persistensi Data
│   ├── __init__.py
│   └── json_repo.py            # Kelas RepositoriJson (satu-satunya I/O berkas JSON)
├── layanan/                    # Lapisan Logika Bisnis (Domain) - Bebas Flask
│   ├── __init__.py
│   ├── aturan.py               # Aturan kuota pinjam, durasi hari, denda, ID generator
│   ├── galat.py                # Exception domain kustom (GalatValidasi, TidakDitemukan)
│   ├── katalog.py              # Logika pencarian buku & kalkulasi eksemplar tersedia
│   └── sirkulasi.py            # Logika peminjaman, pengembalian, status, filter, riwayat
├── rute/                       # Lapisan Presentasi HTTP
│   ├── __init__.py
│   ├── api.py                  # Blueprint REST API JSON (/api/...)
│   └── web.py                  # Blueprint Web HTML (/)
├── templates/                  # Lapisan Template Presentasi Jinja2
│   ├── katalog.html            # Halaman katalog & pencarian buku
│   ├── kembali.html            # Halaman form pengembalian buku
│   ├── layout.html             # Template dasar (header, nav, style)
│   ├── peminjaman.html         # Halaman tabel daftar peminjaman
│   ├── pinjam.html             # Halaman form peminjaman buku
│   └── terlambat.html          # Halaman daftar keterlambatan
└── utils/                      # Helper & Utilitas Umum
    ├── __init__.py
    └── format.py               # Pemformatan mata uang rupiah (format_rupiah)
```

---

## 3. Diagram Modul & Ketergantungan

```mermaid
flowchart TD
    subgraph Presentasi["Lapisan Presentasi (HTTP & UI)"]
        W["rute/web.py<br/>(Blueprint Web)"]
        A["rute/api.py<br/>(Blueprint API)"]
        T["templates/*.html<br/>(Jinja2 Templates)"]
    end

    subgraph Bisnis["Lapisan Layanan Bisnis (Pure Python)"]
        LK["layanan/katalog.py"]
        LS["layanan/sirkulasi.py"]
        LA["layanan/aturan.py"]
        LG["layanan/galat.py"]
    end

    subgraph AksesData["Lapisan Akses Data"]
        R["repositori/json_repo.py<br/>(RepositoriJson)"]
        J[("data.json")]
    end

    subgraph Konfigurasi["Konfigurasi & Helper"]
        C["config.py"]
        U["utils/format.py"]
    end

    W --> LK
    W --> LS
    W --> T
    W --> U
    A --> LK
    A --> LS
    A --> LG
    LS --> LA
    LS --> LK
    LS --> LG
    LS --> R
    LK --> C
    LA --> C
    R --> J
```

> **Arah Ketergantungan:** Seluruh dependensi mengalir satu arah ke bawah (*unidirectional*). Lapisan layanan (`layanan/`) tidak pernah mengimpor atau mengetahui keberadaan lapisan presentasi (`rute/` atau Flask).

---

## 4. Peta Perubahan Kode

Tabel pemetaan refaktorisasi dari blok monolitik lama ke fungsi dan modul baru:

| No | Blok di `app.py` Lama | Fungsi Baru | Modul Baru | Alasan Refaktorisasi |
|---|---|---|---|---|
| 1 | Hitung eksemplar tersedia (baris 20–24 & 190) | `hitung_eksemplar_tersedia()` | `layanan/katalog.py` | Menghilangkan duplikasi perhitungan buku aktif yang dipinjam. |
| 2 | Pencarian katalog (baris 18–19 & 189) | `cari_katalog()` | `layanan/katalog.py` | Menyatukan logika pencarian buku case-insensitive antara Web dan API. |
| 3 | Evaluasi batas kuota pinjam (baris 56–59 & 209–214) | `batas_pinjam()` | `layanan/aturan.py` | Menghilangkan *magic numbers* (3 mhs / 10 dosen) & duplikasi validasi. |
| 4 | Durasi peminjaman (baris 64 & 219–221) | `lama_pinjam_hari()` | `layanan/aturan.py` | Menghilangkan *magic numbers* (7 hari mhs / 14 hari dosen). |
| 5 | Hitung jatuh tempo (baris 65 & 231) | `hitung_jatuh_tempo()` | `layanan/aturan.py` | Memisahkan perhitungan tanggal jatuh tempo dari penanganan HTTP. |
| 6 | Kalkulasi hari telat & denda (baris 100–103 & 241–243) | `hitung_denda()` | `layanan/aturan.py` | Menyatukan aturan denda Rp 1.000/hari, max Rp 50.000, dosen bebas denda. |
| 7 | Pembuatan kode unik pinjam (baris 66 & 222) | `generate_id_pinjam()` | `layanan/aturan.py` | Menjamin format serial `PJnnnn` konsisten di satu tempat. |
| 8 | Evaluasi status pinjaman (baris 149–154 & 275–280) | `tentukan_status_pinjaman()` | `layanan/sirkulasi.py` | Menghilangkan duplikasi penentuan status kembali/terlambat/dipinjam. |
| 9 | Alur transaksi peminjaman (baris 47–71 & 197–227) | `pinjam_buku()` | `layanan/sirkulasi.py` | Memastikan validasi ketersediaan dan anggota identik di Web dan API. |
| 10 | Alur transaksi pengembalian (baris 82–108 & 230–248) | `kembalikan_buku()` | `layanan/sirkulasi.py` | Memusatkan pemrosesan tanggal kembali, denda, dan update data. |
| 11 | Filter daftar peminjaman (baris 148–170 & 273–285) | `daftar_semua_peminjaman()` | `layanan/sirkulasi.py` | Menyatukan penggabungan relasi (join) judul buku dan nama anggota. |
| 12 | Riwayat anggota (baris 290–296) | `riwayat_anggota()` | `layanan/sirkulasi.py` | Mengisolasi komputasi agregasi peminjaman dan denda per anggota. |
| 13 | Akses I/O berkas JSON (11 kali `open(DATA_FILE)`) | `muat()`, `simpan()` | `repositori/json_repo.py` | Menerapkan *Information Hiding* terkait media penyimpanan berkas. |
| 14 | Format mata uang (baris 108 & 169) | `format_rupiah()` | `utils/format.py` | Menghilangkan duplikasi regex/string replace format Rp. |

---

## 5. Analisis Desain Perangkat Lunak

### A. Cohesion dan Coupling
- **Peningkatan Cohesion (High Cohesion):**  
  Sebelumnya, `app.py` memiliki *low cohesion* karena menangani formatting HTML, parsing request HTTP, query data, validasi, dan aturan denda sekaligus. Setelah modularisasi, setiap modul hanya memiliki satu fokus tanggung jawab (contoh: `layanan/aturan.py` murni menghitung nilai angka dan tanggal).
- **Penurunan Coupling (Low Coupling):**  
  Lapisan logika bisnis `layanan/` tidak memiliki ketergantungan pada pustaka web (`Flask`). Apabila framework presentasi diganti (misalnya ke FastAPI atau CLI), seluruh modul `layanan/` dan `repositori/` dapat digunakan ulang tanpa perubahan satu baris kode pun.

### B. Penerapan Prinsip SOLID
1. **Single Responsibility Principle (SRP):**  
   Setiap fungsi dan modul hanya memiliki satu alasan untuk berubah. Contoh:
   - Jika tarif denda perpustakaan berubah, hanya berkas `config.py` yang diperbarui.
   - Jika tampilan antarmuka web diperbarui, hanya berkas di `templates/` yang diubah.
2. **Open/Closed Principle (OCP):**  
   Penambahan jenis anggota baru (misalnya "karyawan") cukup menambahkan pemetaan di `config.py` tanpa merombak logika di `sirkulasi.py`.
3. **Dependency Inversion Principle (DIP):**  
   Fungsi di `layanan/` dan blueprint di `rute/` menerima objek repositori yang diinjeksi melalui `current_app.config["REPO"]` atau parameter fungsi, bukan mengikat langsung ke berkas `data.json`.

### C. Information Hiding
- Modul `rute/` dan `layanan/` tidak mengetahui apakah data disimpan di dalam file JSON, SQLite, atau remote database. Hanya kelas `RepositoriJson` yang mengetahui struktur pembacaan berkas fisik.

---

## 6. Temuan Code Smell & Inkonsistensi

1. **Magic Numbers Tersebar:** Angka `1000`, `50000`, `3`, `10`, `7`, `14` tertulis berulang kali di berbagai fungsi route.  
   *Solusi:* Dipusatkan ke konstanta bernama di `config.py`.
2. **Duplikasi Format Rupiah:** Sintaks `"{:,}".format(denda).replace(",", ".")` diulang di route web pengembalian dan daftar pinjam.  
   *Solusi:* Dibuatkan helper `format_rupiah()` di `utils/format.py` dan didaftarkan sebagai Jinja filter.
3. **Penyatuan Validasi Status:** Pada route API awal terdapat validasi status yang eksplisit, namun di route web filter status dilakukan manual.  
   *Solusi:* Disatukan melalui `daftar_semua_peminjaman()` di modul layanan.

---

## 7. Bukti Verifikasi (Cek Cepat Sebelum vs Sesudah)

Pengujian dilakukan menggunakan perintah uji *Cek Cepat* dari spesifikasi tugas. Hasil sebelum dan sesudah modularisasi terbukti **identik**:

### Uji 1: Daftar Terlambat per 2026-10-09
```bash
curl -s 'localhost:5000/api/terlambat?tanggal=2026-10-09'
```
**Hasil:**
```json
[
  {
    "anggota": "A001",
    "id": "PJ0001",
    "isbn": "9780201633610",
    "terlambat_hari": 12
  },
  {
    "anggota": "A001",
    "id": "PJ0002",
    "isbn": "9780132350884",
    "terlambat_hari": 1
  }
]
```

### Uji 2: Peminjaman Aktif per 2026-10-09
```bash
curl -s 'localhost:5000/api/peminjaman?status=dipinjam&tanggal=2026-10-09'
```
**Hasil:**
```json
[
  {
    "anggota": "A003",
    "denda": 0,
    "id": "PJ0004",
    "isbn": "9781292096131",
    "jatuh_tempo": "2026-10-09",
    "judul": "Software Engineering",
    "nama": "Dr. Hasan Basri",
    "status": "dipinjam",
    "tgl_kembali": null,
    "tgl_pinjam": "2026-09-25"
  }
]
```

### Uji 3: Pengembalian dengan Denda Keterlambatan
```bash
curl -s -X POST localhost:5000/api/kembali -H 'Content-Type: application/json' \
  -d '{"kode":"PJ0002","tanggal":"2026-10-20"}'
```
**Hasil:**
```json
{
  "denda": 12000,
  "kode": "PJ0002",
  "terlambat_hari": 12
}
```

---

## 8. Kesimpulan

Refaktorisasi aplikasi Perpustakaan Kampus telah berhasil mengubah kode monolitik menjadi aplikasi yang modular, bersih (*clean code*), mudah dipelihara (*maintainable*), dan siap diuji dengan unit test pada tahapan berikutnya, dengan tetap menjaga integritas fungsional 100%.
