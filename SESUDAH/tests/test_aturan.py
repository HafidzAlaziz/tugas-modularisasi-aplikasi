"""Unit Test untuk modul layanan/aturan.py dan utils/format.py.

Menguji fungsi murni (pure functions) secara terisolasi tanpa akses database atau Flask:
- Batas pinjam per tipe anggota
- Lama pinjam per tipe anggota
- Perhitungan tanggal jatuh tempo
- Perhitungan denda (termasuk batas denda maksimal & pembebasan dosen)
- Pembuatan kode unik peminjaman (PJnnnn)
- Format rupiah
"""
import unittest
from datetime import date

from layanan.aturan import (
    batas_pinjam,
    generate_id_pinjam,
    hitung_denda,
    hitung_jatuh_tempo,
    lama_pinjam_hari,
)
from utils.format import format_rupiah


class TestAturanSirkulasi(unittest.TestCase):
    """Pengujian unit untuk fungsi kalkulasi aturan bisnis perpustakaan."""

    # --- batas_pinjam ---

    def test_batas_pinjam_mahasiswa(self):
        self.assertEqual(batas_pinjam("mahasiswa"), 3)

    def test_batas_pinjam_dosen(self):
        self.assertEqual(batas_pinjam("dosen"), 10)

    def test_batas_pinjam_tipe_tidak_dikenal(self):
        # Tipe tidak dikenal harus kembali ke default 3
        self.assertEqual(batas_pinjam("umum"), 3)

    # --- lama_pinjam_hari ---

    def test_lama_pinjam_mahasiswa(self):
        self.assertEqual(lama_pinjam_hari("mahasiswa"), 7)

    def test_lama_pinjam_dosen(self):
        self.assertEqual(lama_pinjam_hari("dosen"), 14)

    def test_lama_pinjam_tipe_tidak_dikenal(self):
        # Tipe tidak dikenal harus kembali ke default 7 hari
        self.assertEqual(lama_pinjam_hari("umum"), 7)

    # --- hitung_jatuh_tempo ---

    def test_jatuh_tempo_mahasiswa(self):
        # 1 Okt + 7 hari = 8 Okt
        self.assertEqual(
            hitung_jatuh_tempo("mahasiswa", date(2026, 10, 1)),
            date(2026, 10, 8),
        )

    def test_jatuh_tempo_dosen(self):
        # 1 Okt + 14 hari = 15 Okt
        self.assertEqual(
            hitung_jatuh_tempo("dosen", date(2026, 10, 1)),
            date(2026, 10, 15),
        )

    # --- hitung_denda ---

    def test_denda_tepat_waktu(self):
        # Kembali tepat pada jatuh tempo -> telat 0, denda 0
        telat, denda = hitung_denda("mahasiswa", date(2026, 10, 8), date(2026, 10, 8))
        self.assertEqual(telat, 0)
        self.assertEqual(denda, 0)

    def test_denda_sebelum_jatuh_tempo(self):
        # Kembali lebih awal dari jatuh tempo -> telat 0, denda 0
        telat, denda = hitung_denda("mahasiswa", date(2026, 10, 8), date(2026, 10, 5))
        self.assertEqual(telat, 0)
        self.assertEqual(denda, 0)

    def test_denda_terlambat_mahasiswa(self):
        # Mahasiswa telat 5 hari -> Rp 1.000 x 5 = Rp 5.000
        telat, denda = hitung_denda("mahasiswa", date(2026, 10, 8), date(2026, 10, 13))
        self.assertEqual(telat, 5)
        self.assertEqual(denda, 5000)

    def test_denda_maksimal(self):
        # Telat 60 hari -> 60 x 1.000 = 60.000, terkena plafon MAKSIMAL_DENDA 50.000
        telat, denda = hitung_denda("mahasiswa", date(2026, 10, 1), date(2026, 11, 30))
        self.assertEqual(telat, 60)
        self.assertEqual(denda, 50000)

    def test_denda_dosen_bebas_denda(self):
        # Dosen telat 10 hari -> tetap denda Rp 0
        telat, denda = hitung_denda("dosen", date(2026, 10, 8), date(2026, 10, 18))
        self.assertEqual(telat, 10)
        self.assertEqual(denda, 0)

    # --- generate_id_pinjam ---

    def test_generate_id_pertama(self):
        self.assertEqual(generate_id_pinjam(0), "PJ0001")

    def test_generate_id_kelima(self):
        self.assertEqual(generate_id_pinjam(4), "PJ0005")

    def test_generate_id_keseratus(self):
        self.assertEqual(generate_id_pinjam(99), "PJ0100")

    # --- format_rupiah ---

    def test_format_rupiah_nol(self):
        self.assertEqual(format_rupiah(0), "Rp 0")

    def test_format_rupiah_seribu(self):
        self.assertEqual(format_rupiah(1000), "Rp 1.000")

    def test_format_rupiah_limapuluh_ribu(self):
        self.assertEqual(format_rupiah(50000), "Rp 50.000")


if __name__ == "__main__":
    unittest.main()
