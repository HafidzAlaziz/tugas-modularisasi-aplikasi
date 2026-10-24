"""Rute API JSON.

Memanggil fungsi layanan yang SAMA persis dengan halaman Web.
Tidak ada logika bisnis atau SQL/JSON yang diulang di sini.
"""
from datetime import date
from flask import Blueprint, current_app, jsonify, request

from layanan import (
    GalatLayanan,
    cari_katalog,
    daftar_peminjaman_terlambat,
    daftar_semua_peminjaman,
    kembalikan_buku,
    pinjam_buku,
    riwayat_anggota,
)

api = Blueprint("api", __name__)


def _repo():
    return current_app.config["REPO"]


@api.errorhandler(GalatLayanan)
def tangani_galat(e: GalatLayanan):
    return jsonify({"error": e.pesan, **e.data}), e.status


@api.route("/buku")
def buku():
    q = request.args.get("q", "").strip()
    data = _repo().muat()
    return jsonify(cari_katalog(data["buku"], data["peminjaman"], q))


@api.route("/pinjam", methods=["POST"])
def pinjam():
    body = request.get_json(silent=True) or {}
    tgl = date.fromisoformat(body["tanggal"]) if body.get("tanggal") else None
    pinjaman = pinjam_buku(_repo(), body.get("anggota", ""), body.get("isbn", ""), tgl)
    return jsonify(pinjaman), 201


@api.route("/kembali", methods=["POST"])
def kembali():
    body = request.get_json(silent=True) or {}
    tgl = date.fromisoformat(body["tanggal"]) if body.get("tanggal") else None
    res = kembalikan_buku(_repo(), body.get("kode", ""), tgl)
    return jsonify({
        "kode": res["kode"],
        "terlambat_hari": res["terlambat_hari"],
        "denda": res["denda"],
    })


@api.route("/terlambat")
def terlambat():
    tgl = date.fromisoformat(request.args["tanggal"]) if request.args.get("tanggal") else None
    daftar = daftar_peminjaman_terlambat(_repo(), tgl)
    hasil = [
        {
            "id": d["id"],
            "anggota": d["anggota"],
            "isbn": d["isbn"],
            "terlambat_hari": d["terlambat_hari"],
        }
        for d in daftar
    ]
    return jsonify(hasil)


@api.route("/peminjaman")
def peminjaman():
    status = request.args.get("status")
    id_anggota = request.args.get("anggota")
    tgl = date.fromisoformat(request.args["tanggal"]) if request.args.get("tanggal") else None
    return jsonify(daftar_semua_peminjaman(_repo(), status, id_anggota, tgl))


@api.route("/anggota/<id_anggota>/riwayat")
def riwayat(id_anggota):
    return jsonify(riwayat_anggota(_repo(), id_anggota))

