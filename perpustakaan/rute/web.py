"""Rute antarmuka Web HTML.

Hanya bertanggung jawab menerima request HTTP dan merender template HTML.
Logika bisnis sepenuhnya didelegasikan ke modul layanan/.
"""
from datetime import date
from flask import Blueprint, current_app, render_template, request

from layanan import (
    GalatLayanan,
    cari_katalog,
    daftar_peminjaman_terlambat,
    daftar_semua_peminjaman,
    kembalikan_buku,
    pinjam_buku,
)
from utils.format import format_rupiah

web = Blueprint("web", __name__)


def _repo():
    return current_app.config["REPO"]


@web.route("/")
def index():
    q = request.args.get("q", "").strip()
    data = _repo().muat()
    hasil = cari_katalog(data["buku"], data["peminjaman"], q)
    return render_template("katalog.html", hasil=hasil, q=q)


@web.route("/pinjam", methods=["GET", "POST"])
def pinjam():
    pesan = ""
    if request.method == "POST":
        id_anggota = request.form.get("anggota", "").strip()
        isbn = request.form.get("isbn", "").strip()
        try:
            p = pinjam_buku(_repo(), id_anggota, isbn)
            jt = date.fromisoformat(p["jatuh_tempo"])
            pesan = f"Berhasil. Kode {p['id']}, kembalikan paling lambat {jt.strftime('%d-%m-%Y')}"
        except GalatLayanan as e:
            pesan = e.pesan
    return render_template("pinjam.html", pesan=pesan)


@web.route("/kembali", methods=["GET", "POST"])
def kembali():
    pesan = ""
    if request.method == "POST":
        kode = request.form.get("kode", "").strip()
        try:
            res = kembalikan_buku(_repo(), kode)
            pesan = f"Buku diterima. Denda: {format_rupiah(res['denda'])}"
        except GalatLayanan as e:
            pesan = e.pesan
    return render_template("kembali.html", pesan=pesan)


@web.route("/terlambat")
def terlambat():
    daftar = daftar_peminjaman_terlambat(_repo())
    return render_template("terlambat.html", daftar=daftar)


@web.route("/peminjaman")
def daftar_peminjaman():
    status = request.args.get("status", "")
    id_anggota = request.args.get("anggota", "").strip()
    daftar = daftar_semua_peminjaman(_repo(), status or None, id_anggota or None)
    return render_template(
        "peminjaman.html",
        daftar=daftar,
        status=status,
        anggota=id_anggota,
    )
