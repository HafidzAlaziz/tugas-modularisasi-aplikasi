"""Layanan pencarian dan pengecekan katalog buku."""


def hitung_eksemplar_tersedia(buku: dict, daftar_peminjaman: list[dict]) -> int:
    """Menghitung jumlah eksemplar buku yang saat ini belum dikembalikan."""
    dipinjam = sum(
        1 for p in daftar_peminjaman
        if p["isbn"] == buku["isbn"] and p["tgl_kembali"] is None
    )
    return buku["eksemplar"] - dipinjam


def cari_katalog(
    daftar_buku: list[dict],
    daftar_peminjaman: list[dict],
    keyword: str = "",
) -> list[dict]:
    """Mencari buku di katalog berdasarkan judul atau penulis (case-insensitive)."""
    q = keyword.strip().lower()
    hasil = []
    for b in daftar_buku:
        if q == "" or q in b["judul"].lower() or q in b["penulis"].lower():
            tersedia = hitung_eksemplar_tersedia(b, daftar_peminjaman)
            hasil.append({
                "isbn": b["isbn"],
                "judul": b["judul"],
                "penulis": b["penulis"],
                "eksemplar": b["eksemplar"],
                "tersedia": tersedia,
            })
    return hasil

