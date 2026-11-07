"""Integration Test untuk alur Pengembalian Buku dan Denda.

Menguji interaksi antara modul:
- layanan/sirkulasi.py (kembalikan_buku, daftar_peminjaman_terlambat)
- layanan/aturan.py (hitung_denda, tarif denda, bebas denda dosen)
- repositori/json_repo.py (pembacaan & update data transaksi di file JSON sementara)
"""
import json
import os
import unittest
from datetime import date

from layanan.galat import TidakDitemukan
from layanan.sirkulasi import daftar_peminjaman_terlambat, kembalikan_buku
from repositori.json_repo import RepositoriJson

TEST_DB_KEMBALI = "test_data_kembali.json"


class TestPengembalianBuku(unittest.TestCase):
    """Pengujian integrasi khusus alur operasional pengembalian buku dan kalkulasi denda."""

    def setUp(self):
        """Menyiapkan database tiruan sebelum setiap test berjalan."""
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
                # Peminjaman aktif mahasiswa (jatuh tempo 8 Okt 2026)
                {
                    "id": "PJ0001",
                    "isbn": "9780132350884",
                    "anggota": "A001",
                    "tgl_pinjam": "2026-10-01",
                    "jatuh_tempo": "2026-10-08",
                    "tgl_kembali": None,
                    "denda": 0,
                },
                # Peminjaman aktif dosen (jatuh tempo 15 Okt 2026)
                {
                    "id": "PJ0002",
                    "isbn": "9780134494166",
                    "anggota": "D001",
                    "tgl_pinjam": "2026-10-01",
                    "jatuh_tempo": "2026-10-15",
                    "tgl_kembali": None,
                    "denda": 0,
                },
                # Peminjaman yang SUDAH dikembalikan sebelumnya
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
        """Menghapus file database sementara setelah test selesai."""
        if os.path.exists(TEST_DB_KEMBALI):
            os.remove(TEST_DB_KEMBALI)

    def test_kembalikan_buku_tepat_waktu(self):
        # Kembali tepat tanggal 8 Okt 2026 -> terlambat 0, denda 0
        hasil = kembalikan_buku(
            self.repo,
            kode="PJ0001",
            tanggal=date(2026, 10, 8),
        )

        self.assertEqual(hasil["kode"], "PJ0001")
        self.assertEqual(hasil["terlambat_hari"], 0)
        self.assertEqual(hasil["denda"], 0)

        # Cek update di file database
        data = self.repo.muat()
        pinjaman = next(p for p in data["peminjaman"] if p["id"] == "PJ0001")
        self.assertEqual(pinjaman["tgl_kembali"], "2026-10-08")
        self.assertEqual(pinjaman["denda"], 0)

    def test_kembalikan_buku_terlambat_mahasiswa(self):
        # Kembali pada 13 Okt 2026 (telat 5 hari -> Rp 5.000)
        hasil = kembalikan_buku(
            self.repo,
            kode="PJ0001",
            tanggal=date(2026, 10, 13),
        )

        self.assertEqual(hasil["kode"], "PJ0001")
        self.assertEqual(hasil["terlambat_hari"], 5)
        self.assertEqual(hasil["denda"], 5000)

        # Cek update di file database
        data = self.repo.muat()
        pinjaman = next(p for p in data["peminjaman"] if p["id"] == "PJ0001")
        self.assertEqual(pinjaman["tgl_kembali"], "2026-10-13")
        self.assertEqual(pinjaman["denda"], 5000)

    def test_kembalikan_buku_dosen_bebas_denda(self):
        # Dosen telat 10 hari (25 Okt) -> denda tetap 0
        hasil = kembalikan_buku(
            self.repo,
            kode="PJ0002",
            tanggal=date(2026, 10, 25),
        )

        self.assertEqual(hasil["terlambat_hari"], 10)
        self.assertEqual(hasil["denda"], 0)

    def test_kembalikan_buku_kode_tidak_ditemukan(self):
        # Kode tidak terdaftar
        with self.assertRaises(TidakDitemukan):
            kembalikan_buku(self.repo, kode="PJ9999")

    def test_kembalikan_buku_sudah_pernah_kembali(self):
        # PJ0003 sudah punya tgl_kembali -> tidak boleh dikembalikan ulang
        with self.assertRaises(TidakDitemukan):
            kembalikan_buku(self.repo, kode="PJ0003")

    def test_daftar_peminjaman_terlambat(self):
        # Pada 10 Okt 2026:
        # PJ0001 (JT 8 Okt) sudah telat 2 hari
        # PJ0002 (JT 15 Okt) belum telat
        # PJ0003 sudah dikembalikan (tidak boleh muncul)
        daftar = daftar_peminjaman_terlambat(self.repo, tanggal=date(2026, 10, 10))
        self.assertEqual(len(daftar), 1)
        self.assertEqual(daftar[0]["id"], "PJ0001")
        self.assertEqual(daftar[0]["terlambat_hari"], 2)


if __name__ == "__main__":
    unittest.main()
