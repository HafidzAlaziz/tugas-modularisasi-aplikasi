"""Integration Test untuk alur Peminjaman Buku.

Mencakup:
1. KONDISI INPUT BENAR (Happy Path):
   - Mahasiswa aktif pinjam buku tersedia (jatuh tempo +7 hari)
   - Dosen aktif pinjam buku tersedia (jatuh tempo +14 hari)
   - Transaksi tersimpan rapi di file database JSON

2. KONDISI INPUT SALAH / INVALID (Negative Path):
   - Anggota nonaktif (aktif: False) -> Ditolak (GalatValidasi)
   - ID Anggota tidak terdaftar -> Ditolak (GalatValidasi)
   - ISBN Buku fiktif / tidak ada di katalog -> Ditolak (TidakDitemukan)
   - Stok eksemplar habis (sedang dipinjam semua) -> Ditolak (GalatValidasi)
   - Peminjaman melebihi batas kuota (mahasiswa maks 3) -> Ditolak (GalatValidasi)
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
    """Pengujian alur peminjaman buku: kondisi benar vs kondisi salah."""

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
                    "aktif": False,  # NONAKTIF
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
        """Membersihkan file database sementara setelah pengujian selesai."""
        if os.path.exists(TEST_DB_PINJAM):
            os.remove(TEST_DB_PINJAM)

    # =========================================================================
    # KELOMPOK 1: KONDISI INPUT BENAR (Positive Test)
    # =========================================================================

    def test_pinjam_buku_sukses_mahasiswa(self):
        """Input Benar: Mahasiswa aktif meminjam buku yang tersedia (jatuh tempo 7 hari)."""
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
        self.assertEqual(pinjaman["jatuh_tempo"], "2026-10-08")  # 1 Okt + 7 hari
        self.assertIsNone(pinjaman["tgl_kembali"])

        # Verifikasi data benar-benar tersimpan di database JSON
        data = self.repo.muat()
        self.assertEqual(len(data["peminjaman"]), 1)
        self.assertEqual(data["peminjaman"][0]["id"], "PJ0001")

    def test_pinjam_buku_sukses_dosen_14_hari(self):
        """Input Benar: Dosen aktif meminjam buku yang tersedia (jatuh tempo 14 hari)."""
        tgl_pinjam = date(2026, 10, 1)
        pinjaman = pinjam_buku(
            self.repo,
            id_anggota="D001",
            isbn="9780134494166",
            tanggal=tgl_pinjam,
        )

        self.assertEqual(pinjaman["id"], "PJ0001")
        self.assertEqual(pinjaman["jatuh_tempo"], "2026-10-15")  # 1 Okt + 14 hari

    # =========================================================================
    # KELOMPOK 2: KONDISI INPUT SALAH / INVALID (Negative Test)
    # =========================================================================

    def test_pinjam_buku_anggota_tidak_aktif(self):
        """Input Salah: Anggota ada di database tetapi status 'aktif: False'."""
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="A002", isbn="9780132350884")
        self.assertEqual(str(ctx.exception), "Anggota tidak ditemukan atau tidak aktif")

    def test_pinjam_buku_anggota_tidak_ditemukan(self):
        """Input Salah: ID anggota fiktif / tidak ada di database."""
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="A999", isbn="9780132350884")
        self.assertEqual(str(ctx.exception), "Anggota tidak ditemukan atau tidak aktif")

    def test_pinjam_buku_tidak_ditemukan(self):
        """Input Salah: ISBN buku fiktif / tidak ada di katalog."""
        with self.assertRaises(TidakDitemukan) as ctx:
            pinjam_buku(self.repo, id_anggota="A001", isbn="9999999999999")
        self.assertEqual(str(ctx.exception), "Buku tidak ditemukan")

    def test_pinjam_buku_eksemplar_habis(self):
        """Input Salah: Meminjam buku saat seluruh stok fisik sedang dipinjam orang lain."""
        # Clean Code hanya ada 1 eksemplar, dipinjam A001
        pinjam_buku(self.repo, id_anggota="A001", isbn="9780132350884")

        # Dosen D001 mencoba pinjam buku yang sama saat stok sisa 0
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="D001", isbn="9780132350884")
        self.assertEqual(str(ctx.exception), "Semua eksemplar sedang dipinjam")

    def test_pinjam_buku_melebihi_batas_kuota_mahasiswa(self):
        """Input Salah: Anggota meminjam melebihi batas kuota (mahasiswa batasnya 3 buku)."""
        # Siapkan 3 peminjaman aktif sebelumnya untuk A001
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

        # Pinjaman ke-4 harus ditolak
        with self.assertRaises(GalatValidasi) as ctx:
            pinjam_buku(self.repo, id_anggota="A001", isbn="9780134494166")
        self.assertEqual(str(ctx.exception), "Batas pinjam tercapai (3 buku)")


if __name__ == "__main__":
    unittest.main()
