# Perpustakaan Kampus

**Tipe aplikasi:** Sirkulasi / manajemen inventaris · **Port:** http://localhost:5002

Sirkulasi buku perpustakaan: katalog, peminjaman, pengembalian dengan denda, daftar keterlambatan.

> ⚠️ Aplikasi ini **sengaja dibuat monolitik**: seluruh kode (akses data JSON, aturan bisnis, validasi, HTML, dan API) bercampur di satu file `app.py`. Tugas Anda adalah memecahnya menjadi modul **tanpa mengubah perilakunya**. Panduan lengkap: [`../README.md`](../README.md).

## Menjalankan

Aplikasi ini punya `docker-compose.yml` sendiri. Jalankan dari **folder ini**:

```bash
docker compose up --build
# buka http://localhost:5002
```

Tanpa Docker: `pip install -r requirements.txt`, lalu `python app.py` (port 5000).

## Cek Cepat Sebelum & Sesudah Dimodularisasi

Jalankan perintah berikut **sebelum** mengubah kode, catat hasilnya, lalu ulangi **sesudah** modularisasi. Hasilnya harus sama.

```bash
curl -s 'localhost:5002/api/terlambat?tanggal=2026-10-09'
```
Hasil: PJ0001 terlambat 12 hari, PJ0002 terlambat 1 hari

```bash
curl -s 'localhost:5002/api/peminjaman?status=dipinjam&tanggal=2026-10-09'
```
Hasil: satu peminjaman: PJ0004, Dr. Hasan Basri, *Software Engineering*, status `dipinjam`

```bash
curl -s -X POST localhost:5002/api/kembali -H 'Content-Type: application/json' \
  -d '{"kode":"PJ0002","tanggal":"2026-10-20"}'
```
Hasil: `terlambat_hari` 12, `denda` 12000

Data contoh ikut berubah setiap ada transaksi. Kembalikan dengan `git checkout -- data.json` sebelum mengecek ulang.

## Aturan Bisnis

Semua aturan ini saat ini tertulis **langsung di dalam fungsi route** (sebagian tertulis lebih dari sekali).

1. Pencarian buku berdasarkan **judul atau penulis** (tidak peka huruf besar/kecil)
2. Eksemplar tersedia = eksemplar − buku yang sedang dipinjam
3. Hanya anggota **aktif** yang boleh meminjam
4. Batas pinjam: **mahasiswa 3 buku**, **dosen 10 buku**
5. Lama pinjam: **mahasiswa 7 hari**, **dosen 14 hari** → jatuh tempo
6. Denda **Rp 1.000/hari** terlambat, **maksimal Rp 50.000**; dosen bebas denda
7. Kode peminjaman `PJnnnn`
8. Daftar peminjaman terlambat beserta jumlah harinya
9. Status peminjaman: **kembali** (sudah dikembalikan), **terlambat** (belum kembali dan lewat jatuh tempo), **dipinjam** (selain itu)
10. Daftar peminjaman lengkap dengan nama peminjam dan judul buku, bisa difilter per status dan per anggota
11. Riwayat anggota: jumlah pinjam, sedang dipinjam, total denda

## Daftar Route

| Method | URL | Keterangan |
|--------|-----|------------|
| GET | `/?q=` | Katalog & pencarian |
| GET, POST | `/pinjam` | Form peminjaman |
| GET, POST | `/kembali` | Form pengembalian |
| GET | `/peminjaman?status=&anggota=` | Daftar peminjaman (filter status & anggota) |
| GET | `/terlambat` | Daftar terlambat |
| GET | `/api/buku?q=` | Cari buku (JSON) |
| POST | `/api/pinjam` | `{anggota, isbn, tanggal?}` |
| POST | `/api/kembali` | `{kode, tanggal?}` |
| GET | `/api/terlambat?tanggal=` | Daftar terlambat (JSON) |
| GET | `/api/peminjaman?status=&anggota=&tanggal=` | Daftar peminjaman + nama, judul, status (JSON) |
| GET | `/api/anggota/<id>/riwayat` | Riwayat anggota |

## File

| File | Isi |
|------|-----|
| `app.py` | Seluruh aplikasi (monolitik) |
| `data.json` | Data contoh (berubah setiap ada transaksi) |
| `Dockerfile`, `requirements.txt` | Image Python 3.12 + Flask |
| `docker-compose.yml` | Menjalankan aplikasi ini di port 5002; folder di-mount ke container sehingga perubahan kode langsung terbaca |
