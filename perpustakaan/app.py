import datetime
from flask import Flask, request, jsonify, render_template_string

from config import DATA_FILE
from repositori import RepositoriJson
from layanan import (
    GalatLayanan,
    cari_katalog,
    pinjam_buku,
    kembalikan_buku,
    daftar_peminjaman_terlambat,
    daftar_semua_peminjaman,
    riwayat_anggota,
)
from utils.format import format_rupiah

app = Flask(__name__)
repo = RepositoriJson(DATA_FILE)

NAV = '<nav><a href="/">Katalog</a> | <a href="/pinjam">Pinjam</a> | <a href="/kembali">Kembalikan</a> | <a href="/peminjaman">Daftar Peminjaman</a> | <a href="/terlambat">Terlambat</a></nav>'


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    data = repo.muat()
    hasil = cari_katalog(data["buku"], data["peminjaman"], q)
    return render_template_string("""
    <html><head><title>Perpustakaan</title><style>body{font-family:Georgia,serif;margin:30px} td,th{border-bottom:1px solid #ddd;padding:6px 12px}</style></head>
    <body>""" + NAV + """<h1>Katalog Buku</h1>
    <form><input name="q" value="{{ q }}" placeholder="judul atau penulis"><button>Cari</button></form>
    <table><tr><th>ISBN</th><th>Judul</th><th>Penulis</th><th>Tersedia</th></tr>
    {% for b in hasil %}<tr><td>{{ b.isbn }}</td><td>{{ b.judul }}</td><td>{{ b.penulis }}</td><td>{{ b.tersedia }} / {{ b.eksemplar }}</td></tr>{% endfor %}
    </table></body></html>""", hasil=hasil, q=q)


@app.route("/pinjam", methods=["GET", "POST"])
def pinjam():
    pesan = ""
    if request.method == "POST":
        id_anggota = request.form.get("anggota", "").strip()
        isbn = request.form.get("isbn", "").strip()
        try:
            p = pinjam_buku(repo, id_anggota, isbn)
            jt = datetime.date.fromisoformat(p["jatuh_tempo"])
            pesan = "Berhasil. Kode " + p["id"] + ", kembalikan paling lambat " + jt.strftime("%d-%m-%Y")
        except GalatLayanan as e:
            pesan = e.pesan
    return render_template_string("""
    <html><head><title>Pinjam</title><style>body{font-family:Georgia,serif;margin:30px}</style></head>
    <body>""" + NAV + """<h1>Peminjaman</h1><p><b>{{ pesan }}</b></p>
    <form method="post">ID anggota <input name="anggota"> ISBN <input name="isbn"> <button>Pinjam</button></form>
    </body></html>""", pesan=pesan)


@app.route("/kembali", methods=["GET", "POST"])
def kembali():
    pesan = ""
    if request.method == "POST":
        kode = request.form.get("kode", "").strip()
        try:
            res = kembalikan_buku(repo, kode)
            pesan = "Buku diterima. Denda: " + format_rupiah(res["denda"])
        except GalatLayanan as e:
            pesan = e.pesan
    return render_template_string("""
    <html><head><title>Kembali</title><style>body{font-family:Georgia,serif;margin:30px}</style></head>
    <body>""" + NAV + """<h1>Pengembalian</h1><p><b>{{ pesan }}</b></p>
    <form method="post">Kode peminjaman <input name="kode"> <button>Kembalikan</button></form>
    </body></html>""", pesan=pesan)


@app.route("/terlambat")
def terlambat():
    daftar = daftar_peminjaman_terlambat(repo)
    return render_template_string("""
    <html><head><title>Terlambat</title><style>body{font-family:Georgia,serif;margin:30px}</style></head>
    <body>""" + NAV + """<h1>Peminjaman Terlambat</h1>
    <ul>{% for d in daftar %}<li>{{ d.id }} — {{ d.nama }}: <i>{{ d.judul }}</i>, terlambat {{ d.hari }} hari</li>{% else %}<li>Tidak ada</li>{% endfor %}</ul>
    </body></html>""", daftar=daftar)


@app.route("/peminjaman")
def daftar_peminjaman():
    status = request.args.get("status", "")
    id_anggota = request.args.get("anggota", "").strip()
    daftar = daftar_semua_peminjaman(repo, status or None, id_anggota or None)
    baris = ""
    for p in daftar:
        warna = {"kembali": "#2e7d32", "terlambat": "#c62828", "dipinjam": "#1565c0"}[p["status"]]
        baris += "<tr><td>" + p["id"] + "</td><td>" + p["nama"] + " (" + p["anggota"] + ")</td><td>" + p["judul"] + "</td><td>" + p["tgl_pinjam"] + "</td>"
        baris += "<td>" + p["jatuh_tempo"] + "</td><td>" + (p["tgl_kembali"] or "-") + "</td><td>" + format_rupiah(p["denda"]) + "</td>"
        baris += "<td style='color:" + warna + "'><b>" + p["status"] + "</b></td></tr>"
    return render_template_string("""
    <html><head><title>Daftar Peminjaman</title><style>body{font-family:Georgia,serif;margin:30px} td,th{border-bottom:1px solid #ddd;padding:6px 12px}</style></head>
    <body>""" + NAV + """<h1>Daftar Peminjaman</h1>
    <form>Status <select name="status"><option value="">semua</option><option value="dipinjam">dipinjam</option><option value="terlambat">terlambat</option>
    <option value="kembali">kembali</option></select> ID anggota <input name="anggota" value="{{ anggota }}" size="6"> <button>Tampilkan</button></form>
    <table><tr><th>Kode</th><th>Peminjam</th><th>Judul</th><th>Pinjam</th><th>Jatuh tempo</th><th>Kembali</th><th>Denda</th><th>Status</th></tr>{{ baris|safe }}</table>
    </body></html>""", baris=baris, anggota=id_anggota)


# ---------------- API JSON ----------------

@app.route("/api/buku")
def api_buku():
    q = request.args.get("q", "").strip()
    data = repo.muat()
    return jsonify(cari_katalog(data["buku"], data["peminjaman"], q))


@app.route("/api/pinjam", methods=["POST"])
def api_pinjam():
    body = request.get_json(silent=True) or {}
    tgl = datetime.date.fromisoformat(body["tanggal"]) if body.get("tanggal") else None
    try:
        pinjaman = pinjam_buku(repo, body.get("anggota", ""), body.get("isbn", ""), tgl)
        return jsonify(pinjaman), 201
    except GalatLayanan as e:
        return jsonify({"error": e.pesan}), e.status


@app.route("/api/kembali", methods=["POST"])
def api_kembali():
    body = request.get_json(silent=True) or {}
    tgl = datetime.date.fromisoformat(body["tanggal"]) if body.get("tanggal") else None
    try:
        res = kembalikan_buku(repo, body.get("kode", ""), tgl)
        return jsonify({"kode": res["kode"], "terlambat_hari": res["terlambat_hari"], "denda": res["denda"]})
    except GalatLayanan as e:
        return jsonify({"error": e.pesan}), e.status


@app.route("/api/terlambat")
def api_terlambat():
    tgl = datetime.date.fromisoformat(request.args["tanggal"]) if request.args.get("tanggal") else None
    daftar = daftar_peminjaman_terlambat(repo, tgl)
    hasil = [
        {"id": d["id"], "anggota": d["anggota"], "isbn": d["isbn"], "terlambat_hari": d["terlambat_hari"]}
        for d in daftar
    ]
    return jsonify(hasil)


@app.route("/api/peminjaman")
def api_peminjaman():
    status = request.args.get("status")
    id_anggota = request.args.get("anggota")
    tgl = datetime.date.fromisoformat(request.args["tanggal"]) if request.args.get("tanggal") else None
    try:
        return jsonify(daftar_semua_peminjaman(repo, status, id_anggota, tgl))
    except GalatLayanan as e:
        return jsonify({"error": e.pesan}), e.status


@app.route("/api/anggota/<id_anggota>/riwayat")
def api_riwayat(id_anggota):
    return jsonify(riwayat_anggota(repo, id_anggota))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
