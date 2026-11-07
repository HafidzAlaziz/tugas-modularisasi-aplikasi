# #!/usr/bin/env bash
# # Skrip untuk menjalankan SEBELUM dan SESUDAH secara bersamaan di port berbeda

# # Bersihkan proses background saat script dihentikan (Ctrl+C)
# trap 'echo -e "\nMenghentikan kedua server..."; kill $(jobs -p) 2>/dev/null' EXIT

# ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# echo "=================================================="
# echo "Menjalankan kedua versi aplikasi Perpustakaan..."
# echo "=================================================="

# # 1. Menjalankan SEBELUM di Port 5001
# cd "$ROOT_DIR/SEBELUM"
# "$ROOT_DIR/SESUDAH/.venv/bin/flask" --app app run --port 5001 > /dev/null 2>&1 &
# PID_SEBELUM=$!
# echo "✓ SEBELUM (Monolitik) : http://localhost:5001 (PID: $PID_SEBELUM)"

# 2. Menjalankan SESUDAH di Port 5002
cd "/home/Hafidz/Documents/Tugas/tugas-modularisasi-aplikasi/SESUDAH"
"/home/Hafidz/Documents/Tugas/tugas-modularisasi-aplikasi/SESUDAH/.venv/bin/flask" --app app run --port 5002 > /dev/null 2>&1 &
PID_SESUDAH=$!
echo "✓ SESUDAH (Modular)   : http://localhost:5002 (PID: $PID_SESUDAH)"

echo "--------------------------------------------------"
echo "Kedua server aktif. Tekan CTRL + C untuk berhenti."
echo "=================================================="

# Tunggu proses
wait

