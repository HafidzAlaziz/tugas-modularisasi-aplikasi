"""Exception domain perpustakaan.

Rute API memetakannya ke status HTTP; rute web menampilkan pesan galat.
"""


class GalatLayanan(Exception):
    status = 400

    def __init__(self, pesan: str, status: int = 400, **data):
        super().__init__(pesan)
        self.pesan = pesan
        self.status = status
        self.data = data


class GalatValidasi(GalatLayanan):
    status = 400


class TidakDitemukan(GalatLayanan):
    status = 404

