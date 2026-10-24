"""Repositori data perpustakaan berbasis file JSON.

Modul ini adalah SATU-SATUNYA modul yang mengetahui format dan cara penyimpanan data.json.
"""
import json


class RepositoriJson:
    """Membaca dan menyimpan seluruh data perpustakaan dari/ke satu file JSON."""

    def __init__(self, path: str):
        self.path = path

    def muat(self) -> dict:
        """Memuat seluruh data dari file JSON."""
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def simpan(self, data: dict) -> None:
        """Menyimpan seluruh data ke file JSON."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
