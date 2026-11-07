"""Unit Test untuk modul layanan/katalog.py.

Menguji logika pencarian katalog dan perhitungan ketersediaan eksemplar buku:
- Menghitung sisa eksemplar buku yang belum dikembalikan
- Pencarian buku case-insensitive berdasarkan judul
- Pencarian buku case-insensitive berdasarkan nama penulis
- Pencarian dengan kata kunci kosong (mengembalikan semua buku)
- Pencarian dengan kata kunci yang tidak cocok
"""
import unittest

from layanan.katalog import cari_katalog, hitung_eksemplar_tersedia


class TestKatalogBuku(unittest.TestCase):
    """Pengujian unit untuk pencarian katalog dan ketersediaan buku."""

    def setUp(self):
        self.daftar_buku = [
            {
                "isbn": "9780132350884",
                "judul": "Clean Code",
                "penulis": "Robert C. Martin",
                "eksemplar": 3,
            },
            {
                "isbn": "9780134494166",
                "judul": "Clean Architecture",
                "penulis": "Robert C. Martin",
                "eksemplar": 2,
            },
            {
                "isbn": "9789792248616",
                "judul": "Laskar Pelangi",
                "penulis": "Andrea Hirata",
                "eksemplar": 5,
            },
        ]

        self.daftar_peminjaman = [
            # 1 eksemplar Clean Code sedang dipinjam (belum kembali)
            {
                "id": "PJ0001",
                "isbn": "9780132350884",
                "tgl_kembali": None,
            },
            # 1 eksemplar Clean Code sudah dikembalikan (tidak mengurangi stok)
            {
                "id": "PJ0002",
                "isbn": "9780132350884",
                "tgl_kembali": "2026-10-05",
            },
            # 2 eksemplar Clean Architecture sedang dipinjam (stok habis)
            {
                "id": "PJ0003",
                "isbn": "9780134494166",
                "tgl_kembali": None,
            },
            {
                "id": "PJ0004",
                "isbn": "9780134494166",
                "tgl_kembali": None,
            },
        ]

    def test_hitung_eksemplar_tersedia_sebagian(self):
        # Clean Code: total 3, dipinjam aktif 1 -> sisa 2
        buku_clean_code = self.daftar_buku[0]
        sisa = hitung_eksemplar_tersedia(buku_clean_code, self.daftar_peminjaman)
        self.assertEqual(sisa, 2)

    def test_hitung_eksemplar_tersedia_habis(self):
        # Clean Architecture: total 2, dipinjam aktif 2 -> sisa 0
        buku_clean_arch = self.daftar_buku[1]
        sisa = hitung_eksemplar_tersedia(buku_clean_arch, self.daftar_peminjaman)
        self.assertEqual(sisa, 0)

    def test_hitung_eksemplar_tersedia_utuh(self):
        # Laskar Pelangi: total 5, tidak ada yang dipinjam -> sisa 5
        buku_laskar = self.daftar_buku[2]
        sisa = hitung_eksemplar_tersedia(buku_laskar, self.daftar_peminjaman)
        self.assertEqual(sisa, 5)

    def test_cari_katalog_semua(self):
        # Keyword kosong -> kembalikan semua buku (3 buku)
        hasil = cari_katalog(self.daftar_buku, self.daftar_peminjaman, keyword="")
        self.assertEqual(len(hasil), 3)

    def test_cari_katalog_berdasarkan_judul(self):
        # Case-insensitive: 'clean' harus mencocokkan 'Clean Code' & 'Clean Architecture'
        hasil = cari_katalog(self.daftar_buku, self.daftar_peminjaman, keyword="clean")
        self.assertEqual(len(hasil), 2)
        judul_list = [b["judul"] for b in hasil]
        self.assertIn("Clean Code", judul_list)
        self.assertIn("Clean Architecture", judul_list)

    def test_cari_katalog_berdasarkan_penulis(self):
        # Cari berdasarkan nama penulis: 'hirata'
        hasil = cari_katalog(self.daftar_buku, self.daftar_peminjaman, keyword="hirata")
        self.assertEqual(len(hasil), 1)
        self.assertEqual(hasil[0]["judul"], "Laskar Pelangi")

    def test_cari_katalog_tidak_ditemukan(self):
        # Keyword acak yang tidak ada
        hasil = cari_katalog(self.daftar_buku, self.daftar_peminjaman, keyword="xyz123")
        self.assertEqual(len(hasil), 0)


if __name__ == "__main__":
    unittest.main()
