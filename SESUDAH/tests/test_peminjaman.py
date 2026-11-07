"""Integration Test untuk alur Peminjaman Buku.

Menguji interaksi antara modul:
- layanan/sirkulasi.py (fungsi pinjam_buku)
- layanan/aturan.py (batas pinjam, lama hari, kode PJ)
- layanan/katalog.py (stok eksemplar tersedia)
- repositori/json_repo.py (pembacaan & penulisan transaksi ke file JSON sementara)
"""
import json
import os
import unittest
from datetime import date

from layanan.galat import GalatValidasi, TidakDitemukan
from layanan.sirkulasi import pinjam_buku
from repositori.json_repo import RepositoriJson

TEST_DB_PINJAM = "test_data_pinjam.json"


class TestPeminjamanBuku(unittest.TestCase):
    """Pengujian integrasi khusus alur operasional peminjaman buku."""

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
                    "eksemplar": 3,
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
                    "id": "A002",
                    "nama": "Siti Rahma",
                    "tipe": "mahasiswa",
                    "aktif": False,  # Nonaktif
                },
                {
                    "id": "D001",
                    "nama": "Dr. Hasan Basri",
                    "tipe": "dosen",
                    "aktif": True,
                },
            ],
            "peminjaman": [],
        }

        with open(TEST_DB_PINJAM, "w", encoding="utf-8") as f:
            json.dump(self.data_awal, f, indent=2)

        self.repo = RepositoriJson(TEST_DB_PINJAM)

    def tearDown(self):
        """Menghapus file database sementara setelah test selesai."""
        if os.path.exists(TEST_DB_PINJAM):
            os.remove(TEST_DB_PINJAM)

    def test_pinjam_buku_sukses_mahasiswa(self):
        # Mahasiswa aktif meminjam buku -> jatuh tempo +7 hari
        tgl_pinjam = date(2026, 10, 1)
        pinjaman = pinjam_buku(
            self.repo,
            id_anggota="A001",
            isbn="9780132350884",
            tanggal=tgl_pinjam,
        )

        self.assertEqual(pinjaman["id"], "PJ0001")
        self.assertEqual(pinjaman["anggota"], "A001")
        self.assertEqual(pinjaman["isbn"], "9780132350884")
        self.assertEqual(pinjaman["jatuh_tempo"], "2026-10-08")  # +7 hari
        self.assertIsNone(pinjaman["tgl_kembali"])

        # Verifikasi data tersimpan di database JSON
        data = self.repo.muat()
        self.assertEqual(len(data["peminjaman"]), 1)
        self.assertEqual(data["peminjaman"][0]["id"], "PJ0001")

    def test_pinjam_buku_sukses_dosen_14_hari(self):
        # Dosen aktif meminjam buku -> jatuh tempo +14 hari
        tgl_pinjam = date(2026, 10, 1)
        pinjaman = pinjam_buku(
            self.repo,
            id_anggota="D001",
            isbn="9780134494166",
            tanggal=tgl_pinjam,
        )

        self.assertEqual(pinjaman["id"], "PJ0001")
        self.assertEqual(pinjaman["jatuh_tempo"], "2026-10-15")  # +14 hari

    def test_pinjam_buku_anggota_tidak_aktif(self):
        # Anggota nonaktif (A002) harus ditolak
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="A002", isbn="9780132350884")
        self.assertIn("tidak aktif", str(ctx.exception))

    def test_pinjam_buku_anggota_tidak_ditemukan(self):
        # ID anggota fiktif harus ditolak
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="A999", isbn="9780132350884")
        self.assertIn("Anggota tidak ditemukan", str(ctx.exception))

    def test_pinjam_buku_tidak_ditemukan(self):
        # ISBN fiktif harus melempar TidakDitemukan
        with self.assertRaises(TidakDitemukan) as ctx:
            pinjam_buku(self.repo, id_anggota="A001", isbn="9999999999999")
        self.assertIn("Buku tidak ditemukan", str(ctx.exception))

    def test_pinjam_buku_eksemplar_habis(self):
        # Clean Code hanya ada 1 eksemplar, dipinjam A001
        pinjam_buku(self.repo, id_anggota="A001", isbn="9780132350884")

        # Anggota lain mencoba pinjam buku yang sama saat stok 0
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="D001", isbn="9780132350884")
        self.assertIn("Semua eksemplar sedang dipinjam", str(ctx.exception))

    def test_pinjam_buku_melebihi_batas_kuota_mahasiswa(self):
        # Batas kuota mahasiswa = 3. Buat 3 peminjaman aktif sebelumnya
        data = self.repo.muat()
        for i in range(1, 4):
            data["peminjaman"].append({
                "id": f"PJ000{i}",
                "isbn": "9780134494166",
                "anggota": "A001",
                "tgl_pinjam": "2026-10-01",
                "jatuh_tempo": "2026-10-08",
                "tgl_kembali": None,
                "denda": 0,
            })
        self.repo.simpan(data)

        # Pinjaman ke-4 harus ditolak karena kuota 3 buku tercapai
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="A001", isbn="9780134494166")
        self.assertIn("Batas pinjam tercapai (3 buku)", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
