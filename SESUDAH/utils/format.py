def format_rupiah(nilai: int) -> str:
    """Memformat integer menjadi format mata uang Rupiah, contoh: 12000 -> 'Rp 12.000'"""
    return "Rp " + "{:,}".format(nilai).replace(",", ".")