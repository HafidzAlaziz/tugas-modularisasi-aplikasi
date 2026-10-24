"""Layanan operasional sirkulasi peminjaman dan pengembalian perpustakaan."""
from datetime import date

from .aturan import (
    batas_pinjam,
    generate_id_pinjam,
    hitung_denda,
    hitung_jatuh_tempo,
)
from .galat import GalatValidasi, TidakDitemukan
from .katalog import hitung_eksemplar_tersedia


def tentukan_status_pinjaman(
    jatuh_tempo: date,
    tgl_kembali: str | None,
    tgl_acuan: date,
) -> str:
    """Menentukan status suatu transaksi peminjaman ('kembali', 'terlambat', 'dipinjam')."""
    if tgl_kembali is not None:
        return "kembali"
    if jatuh_tempo < tgl_acuan:
        return "terlambat"
    return "dipinjam"


def pinjam_buku(
    repo,
    id_anggota: str,
    isbn: str,
    tanggal: date | None = None,
) -> dict:
    """Memvalidasi dan mencatat transaksi peminjaman baru."""
    data = repo.muat()
    anggota = next((a for a in data["anggota"] if a["id"] == id_anggota), None)
    buku = next((b for b in data["buku"] if b["isbn"] == isbn), None)

    if anggota is None or not anggota.get("aktif", False):
        raise GalatValidasi("Anggota tidak ditemukan atau tidak aktif")
    if buku is None:
        raise TidakDitemukan("Buku tidak ditemukan")

    pinjaman_aktif = [
        p for p in data["peminjaman"]
        if p["anggota"] == id_anggota and p["tgl_kembali"] is None
    ]
    batas = batas_pinjam(anggota["tipe"])
    if len(pinjaman_aktif) >= batas:
        raise GalatValidasi(f"Batas pinjam tercapai ({batas} buku)")

    tersedia = hitung_eksemplar_tersedia(buku, data["peminjaman"])
    if tersedia <= 0:
        raise GalatValidasi("Semua eksemplar sedang dipinjam")

    tgl_pinjam = tanggal or date.today()
    jatuh_tempo = hitung_jatuh_tempo(anggota["tipe"], tgl_pinjam)
    id_baru = generate_id_pinjam(len(data["peminjaman"]))

    pinjaman = {
        "id": id_baru,
        "isbn": isbn,
        "anggota": id_anggota,
        "tgl_pinjam": tgl_pinjam.isoformat(),
        "jatuh_tempo": jatuh_tempo.isoformat(),
        "tgl_kembali": None,
        "denda": 0,
    }
    data["peminjaman"].append(pinjaman)
    repo.simpan(data)
    return pinjaman


def kembalikan_buku(
    repo,
    kode: str,
    tanggal: date | None = None,
) -> dict:
    """Memvalidasi dan memproses pengembalian buku beserta kalkulasi dendanya."""
    data = repo.muat()
    pinjaman = next(
        (p for p in data["peminjaman"] if p["id"] == kode and p["tgl_kembali"] is None),
        None,
    )
    if pinjaman is None:
        raise TidakDitemukan("Kode peminjaman tidak ditemukan atau sudah dikembalikan")

    tgl_kembali = tanggal or date.today()
    anggota = next(a for a in data["anggota"] if a["id"] == pinjaman["anggota"])
    jatuh_tempo = date.fromisoformat(pinjaman["jatuh_tempo"])

    telat, denda = hitung_denda(anggota["tipe"], jatuh_tempo, tgl_kembali)
    pinjaman["tgl_kembali"] = tgl_kembali.isoformat()
    pinjaman["denda"] = denda
    repo.simpan(data)

    return {
        "kode": pinjaman["id"],
        "terlambat_hari": max(telat, 0),
        "denda": denda,
        "pinjaman": pinjaman,
    }


def daftar_peminjaman_terlambat(
    repo,
    tanggal: date | None = None,
) -> list[dict]:
    """Mendapatkan daftar semua peminjaman yang telah melewati tanggal jatuh tempo."""
    data = repo.muat()
    tgl_acuan = tanggal or date.today()
    hasil = []
    for p in data["peminjaman"]:
        jt = date.fromisoformat(p["jatuh_tempo"])
        if p["tgl_kembali"] is None and jt < tgl_acuan:
            anggota = next((a for a in data["anggota"] if a["id"] == p["anggota"]), None)
            buku = next((b for b in data["buku"] if b["isbn"] == p["isbn"]), None)
            hari = (tgl_acuan - jt).days
            hasil.append({
                "id": p["id"],
                "anggota": p["anggota"],
                "nama": anggota["nama"] if anggota else "",
                "isbn": p["isbn"],
                "judul": buku["judul"] if buku else "",
                "terlambat_hari": hari,
                "hari": hari,
            })
    return hasil


def daftar_semua_peminjaman(
    repo,
    status: str | None = None,
    id_anggota: str | None = None,
    tanggal: date | None = None,
) -> list[dict]:
    """Mendapatkan daftar peminjaman dengan filter status dan/atau id anggota."""
    data = repo.muat()
    tgl_acuan = tanggal or date.today()

    if status and status not in ("dipinjam", "terlambat", "kembali"):
        raise GalatValidasi("Status harus dipinjam, terlambat, atau kembali")

    hasil = []
    for p in data["peminjaman"]:
        jt = date.fromisoformat(p["jatuh_tempo"])
        st = tentukan_status_pinjaman(jt, p["tgl_kembali"], tgl_acuan)

        if status and st != status:
            continue
        if id_anggota and p["anggota"] != id_anggota:
            continue

        anggota = next((a for a in data["anggota"] if a["id"] == p["anggota"]), None)
        buku = next((b for b in data["buku"] if b["isbn"] == p["isbn"]), None)

        item = dict(p)
        item["nama"] = anggota["nama"] if anggota else ""
        item["judul"] = buku["judul"] if buku else ""
        item["status"] = st
        hasil.append(item)

    return hasil


def riwayat_anggota(repo, id_anggota: str) -> dict:
    """Menghitung ringkasan riwayat peminjaman untuk anggota tertentu."""
    data = repo.muat()
    riwayat = [p for p in data["peminjaman"] if p["anggota"] == id_anggota]
    total_denda = sum(p["denda"] for p in riwayat)
    sedang_dipinjam = sum(1 for p in riwayat if p["tgl_kembali"] is None)

    return {
        "anggota": id_anggota,
        "jumlah_pinjam": len(riwayat),
        "sedang_dipinjam": sedang_dipinjam,
        "total_denda": total_denda,
    }
