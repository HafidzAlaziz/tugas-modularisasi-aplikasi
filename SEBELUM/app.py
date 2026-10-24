# Perpustakaan Kampus (sirkulasi buku) — aplikasi MONOLITIK: semua kode ada di satu file ini.
# Tugas mahasiswa: pecah menjadi modul tanpa mengubah perilakunya (lihat README.md).
from flask import Flask, request, jsonify, render_template_string
import json, os, datetime

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

NAV = '<nav><a href="/">Katalog</a> | <a href="/pinjam">Pinjam</a> | <a href="/kembali">Kembalikan</a> | <a href="/peminjaman">Daftar Peminjaman</a> | <a href="/terlambat">Terlambat</a></nav>'


@app.route("/")
def index():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    q = request.args.get("q", "").strip().lower()
    hasil = []
    for b in data["buku"]:
        if q == "" or q in b["judul"].lower() or q in b["penulis"].lower():
            dipinjam = 0
            for p in data["peminjaman"]:
                if p["isbn"] == b["isbn"] and p["tgl_kembali"] is None:
                    dipinjam += 1
            hasil.append({"isbn": b["isbn"], "judul": b["judul"], "penulis": b["penulis"], "tersedia": b["eksemplar"] - dipinjam, "eksemplar": b["eksemplar"]})
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
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        id_anggota = request.form.get("anggota", "").strip()
        isbn = request.form.get("isbn", "").strip()
        anggota = None
        for a in data["anggota"]:
            if a["id"] == id_anggota:
                anggota = a
        buku = None
        for b in data["buku"]:
            if b["isbn"] == isbn:
                buku = b
        if anggota is None or not anggota["aktif"]:
            pesan = "Anggota tidak ditemukan atau tidak aktif"
        elif buku is None:
            pesan = "Buku tidak ditemukan"
        else:
            aktif = [p for p in data["peminjaman"] if p["anggota"] == id_anggota and p["tgl_kembali"] is None]
            batas = 10 if anggota["tipe"] == "dosen" else 3
            dipinjam = len([p for p in data["peminjaman"] if p["isbn"] == isbn and p["tgl_kembali"] is None])
            if len(aktif) >= batas:
                pesan = "Batas pinjam tercapai (" + str(batas) + " buku)"
            elif buku["eksemplar"] - dipinjam <= 0:
                pesan = "Semua eksemplar sedang dipinjam"
            else:
                hari_ini = datetime.date.today()
                lama = 14 if anggota["tipe"] == "dosen" else 7
                jatuh_tempo = hari_ini + datetime.timedelta(days=lama)
                id_baru = "PJ" + str(len(data["peminjaman"]) + 1).zfill(4)
                data["peminjaman"].append({"id": id_baru, "isbn": isbn, "anggota": id_anggota, "tgl_pinjam": hari_ini.isoformat(),
                                           "jatuh_tempo": jatuh_tempo.isoformat(), "tgl_kembali": None, "denda": 0})
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                pesan = "Berhasil. Kode " + id_baru + ", kembalikan paling lambat " + jatuh_tempo.strftime("%d-%m-%Y")
    return render_template_string("""
    <html><head><title>Pinjam</title><style>body{font-family:Georgia,serif;margin:30px}</style></head>
    <body>""" + NAV + """<h1>Peminjaman</h1><p><b>{{ pesan }}</b></p>
    <form method="post">ID anggota <input name="anggota"> ISBN <input name="isbn"> <button>Pinjam</button></form>
    </body></html>""", pesan=pesan)


@app.route("/kembali", methods=["GET", "POST"])
def kembali():
    pesan = ""
    if request.method == "POST":
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        kode = request.form.get("kode", "").strip()
        pinjaman = None
        for p in data["peminjaman"]:
            if p["id"] == kode and p["tgl_kembali"] is None:
                pinjaman = p
        if pinjaman is None:
            pesan = "Kode peminjaman tidak ditemukan atau sudah dikembalikan"
        else:
            hari_ini = datetime.date.today()
            telat = (hari_ini - datetime.date.fromisoformat(pinjaman["jatuh_tempo"])).days
            tipe = ""
            for a in data["anggota"]:
                if a["id"] == pinjaman["anggota"]:
                    tipe = a["tipe"]
            denda = 0
            if telat > 0 and tipe != "dosen":
                denda = telat * 1000
                if denda > 50000:
                    denda = 50000
            pinjaman["tgl_kembali"] = hari_ini.isoformat()
            pinjaman["denda"] = denda
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            pesan = "Buku diterima. Denda: Rp " + "{:,}".format(denda).replace(",", ".")
    return render_template_string("""
    <html><head><title>Kembali</title><style>body{font-family:Georgia,serif;margin:30px}</style></head>
    <body>""" + NAV + """<h1>Pengembalian</h1><p><b>{{ pesan }}</b></p>
    <form method="post">Kode peminjaman <input name="kode"> <button>Kembalikan</button></form>
    </body></html>""", pesan=pesan)


@app.route("/terlambat")
def terlambat():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    hari_ini = datetime.date.today()
    daftar = []
    for p in data["peminjaman"]:
        if p["tgl_kembali"] is None and datetime.date.fromisoformat(p["jatuh_tempo"]) < hari_ini:
            nama = ""
            for a in data["anggota"]:
                if a["id"] == p["anggota"]:
                    nama = a["nama"]
            judul = ""
            for b in data["buku"]:
                if b["isbn"] == p["isbn"]:
                    judul = b["judul"]
            daftar.append({"id": p["id"], "nama": nama, "judul": judul, "hari": (hari_ini - datetime.date.fromisoformat(p["jatuh_tempo"])).days})
    return render_template_string("""
    <html><head><title>Terlambat</title><style>body{font-family:Georgia,serif;margin:30px}</style></head>
    <body>""" + NAV + """<h1>Peminjaman Terlambat</h1>
    <ul>{% for d in daftar %}<li>{{ d.id }} — {{ d.nama }}: <i>{{ d.judul }}</i>, terlambat {{ d.hari }} hari</li>{% else %}<li>Tidak ada</li>{% endfor %}</ul>
    </body></html>""", daftar=daftar)


@app.route("/peminjaman")
def daftar_peminjaman():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    status = request.args.get("status", "")
    id_anggota = request.args.get("anggota", "").strip()
    hari_ini = datetime.date.today()
    baris = ""
    for p in data["peminjaman"]:
        if p["tgl_kembali"] is not None:
            st = "kembali"
        elif datetime.date.fromisoformat(p["jatuh_tempo"]) < hari_ini:
            st = "terlambat"
        else:
            st = "dipinjam"
        if status != "" and st != status:
            continue
        if id_anggota != "" and p["anggota"] != id_anggota:
            continue
        nama = ""
        for a in data["anggota"]:
            if a["id"] == p["anggota"]:
                nama = a["nama"]
        judul = ""
        for b in data["buku"]:
            if b["isbn"] == p["isbn"]:
                judul = b["judul"]
        warna = {"kembali": "#2e7d32", "terlambat": "#c62828", "dipinjam": "#1565c0"}[st]
        baris += "<tr><td>" + p["id"] + "</td><td>" + nama + " (" + p["anggota"] + ")</td><td>" + judul + "</td><td>" + p["tgl_pinjam"] + "</td>"
        baris += "<td>" + p["jatuh_tempo"] + "</td><td>" + (p["tgl_kembali"] or "-") + "</td><td>Rp " + "{:,}".format(p["denda"]).replace(",", ".") + "</td>"
        baris += "<td style='color:" + warna + "'><b>" + st + "</b></td></tr>"
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
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    q = request.args.get("q", "").strip().lower()
    hasil = []
    for b in data["buku"]:
        if q == "" or q in b["judul"].lower() or q in b["penulis"].lower():
            dipinjam = len([p for p in data["peminjaman"] if p["isbn"] == b["isbn"] and p["tgl_kembali"] is None])
            hasil.append(dict(b, tersedia=b["eksemplar"] - dipinjam))
    return jsonify(hasil)


@app.route("/api/pinjam", methods=["POST"])
def api_pinjam():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    body = request.get_json(silent=True) or {}
    id_anggota = body.get("anggota", "")
    isbn = body.get("isbn", "")
    anggota = next((a for a in data["anggota"] if a["id"] == id_anggota), None)
    buku = next((b for b in data["buku"] if b["isbn"] == isbn), None)
    if anggota is None or not anggota["aktif"]:
        return jsonify({"error": "Anggota tidak ditemukan atau tidak aktif"}), 400
    if buku is None:
        return jsonify({"error": "Buku tidak ditemukan"}), 404
    aktif = [p for p in data["peminjaman"] if p["anggota"] == id_anggota and p["tgl_kembali"] is None]
    if anggota["tipe"] == "dosen":
        batas = 10
    else:
        batas = 3
    if len(aktif) >= batas:
        return jsonify({"error": "Batas pinjam tercapai (" + str(batas) + " buku)"}), 400
    dipinjam = len([p for p in data["peminjaman"] if p["isbn"] == isbn and p["tgl_kembali"] is None])
    if buku["eksemplar"] - dipinjam <= 0:
        return jsonify({"error": "Semua eksemplar sedang dipinjam"}), 400
    tgl = datetime.date.fromisoformat(body["tanggal"]) if body.get("tanggal") else datetime.date.today()
    lama = 7
    if anggota["tipe"] == "dosen":
        lama = 14
    pinjaman = {"id": "PJ" + str(len(data["peminjaman"]) + 1).zfill(4), "isbn": isbn, "anggota": id_anggota, "tgl_pinjam": tgl.isoformat(),
                "jatuh_tempo": (tgl + datetime.timedelta(days=lama)).isoformat(), "tgl_kembali": None, "denda": 0}
    data["peminjaman"].append(pinjaman)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return jsonify(pinjaman), 201


@app.route("/api/kembali", methods=["POST"])
def api_kembali():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    body = request.get_json(silent=True) or {}
    pinjaman = next((p for p in data["peminjaman"] if p["id"] == body.get("kode") and p["tgl_kembali"] is None), None)
    if pinjaman is None:
        return jsonify({"error": "Kode peminjaman tidak ditemukan atau sudah dikembalikan"}), 404
    tgl = datetime.date.fromisoformat(body["tanggal"]) if body.get("tanggal") else datetime.date.today()
    telat = (tgl - datetime.date.fromisoformat(pinjaman["jatuh_tempo"])).days
    anggota = next(a for a in data["anggota"] if a["id"] == pinjaman["anggota"])
    denda = 0
    if telat > 0 and anggota["tipe"] != "dosen":
        denda = min(telat * 1000, 50000)
    pinjaman["tgl_kembali"] = tgl.isoformat()
    pinjaman["denda"] = denda
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return jsonify({"kode": pinjaman["id"], "terlambat_hari": max(telat, 0), "denda": denda})


@app.route("/api/terlambat")
def api_terlambat():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    tgl = datetime.date.fromisoformat(request.args["tanggal"]) if request.args.get("tanggal") else datetime.date.today()
    hasil = []
    for p in data["peminjaman"]:
        jt = datetime.date.fromisoformat(p["jatuh_tempo"])
        if p["tgl_kembali"] is None and jt < tgl:
            hasil.append({"id": p["id"], "anggota": p["anggota"], "isbn": p["isbn"], "terlambat_hari": (tgl - jt).days})
    return jsonify(hasil)


@app.route("/api/peminjaman")
def api_peminjaman():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    status = request.args.get("status")
    id_anggota = request.args.get("anggota")
    tgl = datetime.date.fromisoformat(request.args["tanggal"]) if request.args.get("tanggal") else datetime.date.today()
    if status not in (None, "dipinjam", "terlambat", "kembali"):
        return jsonify({"error": "Status harus dipinjam, terlambat, atau kembali"}), 400
    hasil = []
    for p in data["peminjaman"]:
        if p["tgl_kembali"] is not None:
            st = "kembali"
        elif datetime.date.fromisoformat(p["jatuh_tempo"]) < tgl:
            st = "terlambat"
        else:
            st = "dipinjam"
        if (status is None or st == status) and (id_anggota is None or p["anggota"] == id_anggota):
            anggota = next((a for a in data["anggota"] if a["id"] == p["anggota"]), None)
            buku = next((b for b in data["buku"] if b["isbn"] == p["isbn"]), None)
            hasil.append(dict(p, nama=anggota["nama"] if anggota else "", judul=buku["judul"] if buku else "", status=st))
    return jsonify(hasil)


@app.route("/api/anggota/<id_anggota>/riwayat")
def api_riwayat(id_anggota):
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    riwayat = [p for p in data["peminjaman"] if p["anggota"] == id_anggota]
    total_denda = 0
    for p in riwayat:
        total_denda += p["denda"]
    return jsonify({"anggota": id_anggota, "jumlah_pinjam": len(riwayat), "sedang_dipinjam": len([p for p in riwayat if p["tgl_kembali"] is None]), "total_denda": total_denda})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
