import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# Aturan Batas & Lama Peminjaman
BATAS_PINJAM = {"mahasiswa": 3, "dosen": 10}
LAMA_PINJAM_HARI = {"mahasiswa": 7, "dosen": 14}

# Aturan Denda
TARIF_DENDA_PER_HARI = 1000
MAKSIMAL_DENDA = 50000

# Format Kode ID
PREFIX_KODE_PINJAM = "PJ"
PANJANG_DIGIT_KODE = 4