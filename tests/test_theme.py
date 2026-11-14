"""
Uji penjaga tema terang (.streamlit/config.toml).

Aplikasi ini memaksa tampilan terang lewat CSS buatan sendiri di app.py. Kalau
tema Streamlit ikut sistem operasi (Windows mode gelap), Streamlit mengecat teks
putih dan label radio/slider jadi tak terbaca di atas latar putih -- terukur
rasio kontras 1.00-1.02 (syarat WCAG 4.5). Berkas konfigurasi ini yang
mengunci tema tetap terang, jadi jangan sampai hilang.
"""

import tomllib
from pathlib import Path

CONFIG = Path(".streamlit/config.toml")


def test_berkas_konfigurasi_tema_ada():
    assert CONFIG.exists(), (
        ".streamlit/config.toml hilang -- tema akan ikut OS dan teks UI bisa "
        "menjadi putih di atas latar terang (mode gelap Windows)."
    )


def test_tema_dikunci_terang():
    data = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    assert data["theme"]["base"] == "light", (
        "theme.base harus 'light'; kalau 'dark' atau dihapus, Streamlit mengikuti "
        "tema sistem operasi dan label radio/slider jadi tak terbaca."
    )


def test_warna_teks_tidak_putih():
    data = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    warna = data["theme"].get("textColor", "").lstrip("#").lower()
    assert warna, "textColor wajib didefinisikan"
    r, g, b = (int(warna[i : i + 2], 16) for i in (0, 2, 4))
    kecerahan = 0.2126 * r + 0.7152 * g + 0.0722 * b
    assert kecerahan < 140, f"textColor #{warna} terlalu terang untuk latar putih"
