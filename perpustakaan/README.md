# Perpustakaan Kampus (Versi Modular)

**Tipe aplikasi:** Sirkulasi / manajemen inventaris · **Port:** http://localhost:5002 (Docker) / http://localhost:5000 (Lokal)

Sirkulasi buku perpustakaan: katalog, peminjaman, pengembalian dengan denda, daftar keterlambatan.

> ✅ Aplikasi ini telah **dimodularisasi** dari versi monolitik menjadi arsitektur berlapis (*layered architecture*) yang memisahkan lapisan presentasi (rute & templates), aturan bisnis (layanan), konfigurasi (config), dan persistensi data (repositori). Laporan lengkap desain dan pemetaan fungsi: [`../LAPORAN.md`](../LAPORAN.md).

---

## Struktur Proyek

```
perpustakaan/
├── app.py                      # Application Factory: create_app() & registrasi blueprint
├── config.py                   # Konstanta aturan bisnis (kuota, durasi, denda, prefix)
├── data.json                   # Data persistensi (JSON)
├── docker-compose.yml          # Konfigurasi Docker Compose (port 5002)
├── Dockerfile                  # Image Python 3.12-slim
├── requirements.txt            # Flask==3.0.3
├── repositori/                 # Satu-satunya modul yang membaca/menulis data.json
│   ├── __init__.py
│   └── json_repo.py            # Kelas RepositoriJson
├── layanan/                    # Aturan bisnis murni (bebas Flask / request / HTML)
│   ├── __init__.py
│   ├── aturan.py               # Batas pinjam, durasi hari, denda, kode PJnnnn
│   ├── galat.py                # Exception kustom domain (GalatValidasi, TidakDitemukan)
│   ├── katalog.py              # Pencarian buku & eksemplar tersedia
│   └── sirkulasi.py            # Peminjaman, pengembalian, status, riwayat
├── rute/                       # Blueprint rute HTTP
│   ├── __init__.py
│   ├── api.py                  # Endpoint JSON (/api/...)
│   └── web.py                  # Endpoint halaman HTML
├── templates/                  # Template HTML Jinja2
│   ├── katalog.html
│   ├── kembali.html
│   ├── layout.html
│   ├── peminjaman.html
│   ├── pinjam.html
│   └── terlambat.html
└── utils/
    ├── __init__.py
    └── format.py               # Helper format rupiah (format_rupiah)
```

---

## Cara Menjalankan

### Dengan Docker
```bash
docker compose up --build
# buka http://localhost:5002
```

### Tanpa Docker (Python Lokal)
```bash
python -m venv .venv
source .venv/bin/activate    # Di Linux / Mac
# atau .venv\Scripts\activate di Windows
pip install -r requirements.txt
python app.py
# buka http://localhost:5000
```

---

## Cek Cepat Verifikasi

Perintah pengujian berikut memberikan hasil yang sama persis antara sebelum dan sesudah modularisasi:

```bash
# 1. Cek keterlambatan
curl -s 'localhost:5000/api/terlambat?tanggal=2026-10-09'
# Hasil: PJ0001 terlambat 12 hari, PJ0002 terlambat 1 hari

# 2. Cek peminjaman aktif
curl -s 'localhost:5000/api/peminjaman?status=dipinjam&tanggal=2026-10-09'
# Hasil: PJ0004, Dr. Hasan Basri, Software Engineering, status dipinjam

# 3. Cek kembali & denda
curl -s -X POST localhost:5000/api/kembali -H 'Content-Type: application/json' \
  -d '{"kode":"PJ0002","tanggal":"2026-10-20"}'
# Hasil: terlambat_hari 12, denda 12000
```

*Catatan: Kembalikan data ke awal setelah pengujian dengan `git checkout -- data.json`.*

---

## Aturan Bisnis yang Dimodularisasi

1. **Pencarian buku:** Berdasarkan judul atau penulis (*case-insensitive*) di `layanan/katalog.py`.
2. **Eksemplar tersedia:** `eksemplar - buku yang sedang dipinjam` di `layanan/katalog.py`.
3. **Validasi anggota:** Hanya anggota aktif yang boleh meminjam di `layanan/sirkulasi.py`.
4. **Batas pinjam:** Mahasiswa 3 buku, Dosen 10 buku di `config.py` dan `layanan/aturan.py`.
5. **Lama pinjam:** Mahasiswa 7 hari, Dosen 14 hari di `config.py` dan `layanan/aturan.py`.
6. **Denda keterlambatan:** Rp 1.000/hari, maksimal Rp 50.000, dosen bebas denda di `layanan/aturan.py`.
7. **Kode peminjaman:** Format otomatis `PJnnnn` di `layanan/aturan.py`.
8. **Status peminjaman:** `kembali`, `terlambat`, atau `dipinjam` di `layanan/sirkulasi.py`.
9. **Riwayat anggota:** Jumlah pinjam, sedang dipinjam, dan total denda di `layanan/sirkulasi.py`.
