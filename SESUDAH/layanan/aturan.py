"""Aturan bisnis perhitungan sirkulasi perpustakaan.

Fungsi murni: tanpa efek samping, tanpa Flask, tanpa akses langsung ke file.
"""
from datetime import date, timedelta

from config import (
    BATAS_PINJAM,
    LAMA_PINJAM_HARI,
    MAKSIMAL_DENDA,
    PANJANG_DIGIT_KODE,
    PREFIX_KODE_PINJAM,
    TARIF_DENDA_PER_HARI,
)


def batas_pinjam(tipe_anggota: str) -> int:
    """Mengembalikan batas maksimal eksemplar yang boleh dipinjam berdasarkan tipe anggota."""
    return BATAS_PINJAM.get(tipe_anggota, 3)


def lama_pinjam_hari(tipe_anggota: str) -> int:
    """Mengembalikan durasi peminjaman dalam hari berdasarkan tipe anggota."""
    return LAMA_PINJAM_HARI.get(tipe_anggota, 7)


def hitung_jatuh_tempo(tipe_anggota: str, tgl_pinjam: date) -> date:
    """Menghitung tanggal jatuh tempo peminjaman."""
    return tgl_pinjam + timedelta(days=lama_pinjam_hari(tipe_anggota))


def hitung_denda(tipe_anggota: str, tgl_jatuh_tempo: date, tgl_kembali: date) -> tuple[int, int]:
    """Menghitung jumlah hari keterlambatan dan denda yang harus dibayar.

    Returns:
        tuple[int, int]: (terlambat_hari, denda)
    """
    telat = (tgl_kembali - tgl_jatuh_tempo).days
    if telat <= 0 or tipe_anggota == "dosen":
        return max(telat, 0), 0
    denda = min(telat * TARIF_DENDA_PER_HARI, MAKSIMAL_DENDA)
    return telat, denda


def generate_id_pinjam(jumlah_pinjaman_sebelumnya: int) -> str:
    """Menghasilkan kode unik peminjaman berurutan, contoh: 'PJ0005'."""
    return PREFIX_KODE_PINJAM + str(jumlah_pinjaman_sebelumnya + 1).zfill(PANJANG_DIGIT_KODE)

