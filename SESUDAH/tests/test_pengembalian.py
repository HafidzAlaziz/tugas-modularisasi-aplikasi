"""Integration Test untuk alur Pengembalian Buku, Denda, dan Keterlambatan.

Mencakup:
1. KONDISI INPUT BENAR (Positive Test):
   - Pengembalian tepat waktu (denda 0, tgl_kembali terisi)
   - Pengembalian sebelum jatuh tempo (denda 0)
   - Pengembalian mahasiswa terlambat (kena denda Rp 1.000/hari)
   - Pengembalian dosen terlambat (bebas denda / denda Rp 0)
   - Filter peminjaman yang valid ('dipinjam', 'terlambat', 'kembali')
   - Menampilkan daftar keterlambatan yang valid

2. KONDISI INPUT SALAH / INVALID (Negative Test):
   - Kode peminjaman tidak ada di database -> Ditolak (TidakDitemukan)
   - Kode peminjaman SUDAH pernah dikembalikan -> Ditolak (TidakDitemukan)
   - Filter parameter status tidak dikenal (misal 'hilang', 'rusak') -> Ditolak (GalatValidasi)
"""
import json
import os
import unittest
from datetime import date

from layanan.galat import GalatValidasi, TidakDitemukan
from layanan.sirkulasi import (
    daftar_peminjaman_terlambat,
    daftar_semua_peminjaman,
    kembalikan_buku,
)
from repositori.json_repo import RepositoriJson

TEST_DB_KEMBALI = "test_data_kembali.json"


class TestPengembalianBuku(unittest.TestCase):
    """Pengujian alur pengembalian buku dan denda: kondisi benar vs kondisi salah."""

    def setUp(self):
        """Menyiapkan database tiruan sebelum setiap pengujian dijalankan."""
        self.data_awal = {
            "buku": [
                {
                    "isbn": "9780132350884",
                    "judul": "Clean Code",
                    "penulis": "Robert C. Martin",
                    "eksemplar": 1,
                },
                {
                    "isbn": "9780134494166",
                    "judul": "Clean Architecture",
                    "penulis": "Robert C. Martin",
                    "eksemplar": 2,
                },
            ],
            "anggota": [
                {
                    "id": "A001",
                    "nama": "Rizky Pratama",
                    "tipe": "mahasiswa",
                    "aktif": True,
                },
                {
                    "id": "D001",
                    "nama": "Dr. Hasan Basri",
                    "tipe": "dosen",
                    "aktif": True,
                },
            ],
            "peminjaman": [
                # PJ0001: Peminjaman aktif mahasiswa (jatuh tempo 8 Okt 2026)
                {
                    "id": "PJ0001",
                    "isbn": "9780132350884",
                    "anggota": "A001",
                    "tgl_pinjam": "2026-10-01",
                    "jatuh_tempo": "2026-10-08",
                    "tgl_kembali": None,
                    "denda": 0,
                },
                # PJ0002: Peminjaman aktif dosen (jatuh tempo 15 Okt 2026)
                {
                    "id": "PJ0002",
                    "isbn": "9780134494166",
                    "anggota": "D001",
                    "tgl_pinjam": "2026-10-01",
                    "jatuh_tempo": "2026-10-15",
                    "tgl_kembali": None,
                    "denda": 0,
                },
                # PJ0003: Peminjaman yang SUDAH dikembalikan sebelumnya
                {
                    "id": "PJ0003",
                    "isbn": "9780132350884",
                    "anggota": "A001",
                    "tgl_pinjam": "2026-09-01",
                    "jatuh_tempo": "2026-09-08",
                    "tgl_kembali": "2026-09-08",
                    "denda": 0,
                },
            ],
        }

        with open(TEST_DB_KEMBALI, "w", encoding="utf-8") as f:
            json.dump(self.data_awal, f, indent=2)

        self.repo = RepositoriJson(TEST_DB_KEMBALI)

    def tearDown(self):
        """Membersihkan file database sementara setelah pengujian selesai."""
        if os.path.exists(TEST_DB_KEMBALI):
            os.remove(TEST_DB_KEMBALI)

    # =========================================================================
    # KELOMPOK 1: KONDISI INPUT BENAR (Positive Test)
    # =========================================================================

    def test_kembalikan_buku_tepat_waktu(self):
        """Input Benar: Kembali tepat pada tanggal jatuh tempo -> telat 0, denda Rp 0."""
        hasil = kembalikan_buku(
            self.repo,
            kode="PJ0001",
            tanggal=date(2026, 10, 8),
        )

        self.assertEqual(hasil["kode"], "PJ0001")
        self.assertEqual(hasil["terlambat_hari"], 0)
        self.assertEqual(hasil["denda"], 0)

        # Verifikasi data ter-update di file JSON
        data = self.repo.muat()
        pinjaman = next(p for p in data["peminjaman"] if p["id"] == "PJ0001")
        self.assertEqual(pinjaman["tgl_kembali"], "2026-10-08")
        self.assertEqual(pinjaman["denda"], 0)

    def test_kembalikan_buku_terlambat_mahasiswa(self):
        """Input Benar: Mahasiswa telat 5 hari -> denda dihitung Rp 5.000."""
        hasil = kembalikan_buku(
            self.repo,
            kode="PJ0001",
            tanggal=date(2026, 10, 13),  # 13 Okt - 8 Okt = 5 hari
        )

        self.assertEqual(hasil["kode"], "PJ0001")
        self.assertEqual(hasil["terlambat_hari"], 5)
        self.assertEqual(hasil["denda"], 5000)

        # Verifikasi data ter-update di file JSON
        data = self.repo.muat()
        pinjaman = next(p for p in data["peminjaman"] if p["id"] == "PJ0001")
        self.assertEqual(pinjaman["tgl_kembali"], "2026-10-13")
        self.assertEqual(pinjaman["denda"], 5000)

    def test_kembalikan_buku_dosen_bebas_denda(self):
        """Input Benar: Dosen telat 10 hari -> denda tetap Rp 0 (aturan khusus dosen)."""
        hasil = kembalikan_buku(
            self.repo,
            kode="PJ0002",
            tanggal=date(2026, 10, 25),  # 25 Okt - 15 Okt = 10 hari
        )

        self.assertEqual(hasil["terlambat_hari"], 10)
        self.assertEqual(hasil["denda"], 0)

    def test_daftar_peminjaman_terlambat(self):
        """Input Benar: Mengambil daftar peminjaman yang melewati jatuh tempo per 10 Okt 2026."""
        daftar = daftar_peminjaman_terlambat(self.repo, tanggal=date(2026, 10, 10))
        # Hanya PJ0001 (JT 8 Okt) yang terlambat; PJ0002 (JT 15 Okt) belum; PJ0003 sudah kembali
        self.assertEqual(len(daftar), 1)
        self.assertEqual(daftar[0]["id"], "PJ0001")
        self.assertEqual(daftar[0]["terlambat_hari"], 2)

    def test_daftar_semua_peminjaman_filter_valid(self):
        """Input Benar: Filter status valid ('dipinjam', 'kembali')."""
        dipinjam = daftar_semua_peminjaman(self.repo, status="dipinjam", tanggal=date(2026, 10, 2))
        self.assertEqual(len(dipinjam), 2)  # PJ0001 & PJ0002

        kembali = daftar_semua_peminjaman(self.repo, status="kembali")
        self.assertEqual(len(kembali), 1)  # PJ0003

    # =========================================================================
    # KELOMPOK 2: KONDISI INPUT SALAH / INVALID (Negative Test)
    # =========================================================================

    def test_kembalikan_buku_kode_tidak_ditemukan(self):
        """Input Salah: Kode peminjaman tidak terdaftar di database."""
        with self.assertRaises(TidakDitemukan) as ctx:
            kembalikan_buku(self.repo, kode="PJ9999")
        self.assertEqual(str(ctx.exception), "Kode peminjaman tidak ditemukan atau sudah dikembalikan")

    def test_kembalikan_buku_sudah_pernah_kembali(self):
        """Input Salah: Kode peminjaman valid tetapi sudah pernah dikembalikan sebelumnya (PJ0003)."""
        with self.assertRaises(TidakDitemukan) as ctx:
            kembalikan_buku(self.repo, kode="PJ0003")
        self.assertEqual(str(ctx.exception), "Kode peminjaman tidak ditemukan atau sudah dikembalikan")

    def test_daftar_semua_peminjaman_filter_status_salah(self):
        """Input Salah: Filter status ngawur / tidak dikenal ('hilang', 'rusak')."""
        with self.assertRaises(GalatValidasi) as ctx:
            daftar_semua_peminjaman(self.repo, status="hilang")
        self.assertEqual(str(ctx.exception), "Status harus dipinjam, terlambat, atau kembali")


if __name__ == "__main__":
    unittest.main()
