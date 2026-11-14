"""
Uji mode output ringkas (ketentuan lingkup: K genap wajib punya mode ringkas).

Mode ringkas TIDAK memanggil model. Ia memproyeksikan empat field dari hasil penuh
yang sama, jadi yang perlu diuji adalah proyeksinya — bukan kualitas model.
"""

import pytest

from src.extraction.extractor import REQUIRED_FIELDS, _proyeksi_ringkas, extract_fields

FIELDS_PENUH = {
    "jenis_data_dikumpulkan": "Nama, email, dan riwayat transaksi.",
    "tujuan_pemrosesan": "Verifikasi akun dan pencegahan penipuan.",
    "pihak_ketiga_penerima": "Penyedia layanan pembayaran.",
    "masa_retensi_data": "tidak disebutkan",
    "dasar_pemrosesan": "tidak disebutkan",
    "transfer_lintas_negara": "tidak disebutkan",
    "hak_subjek_data": "tidak disebutkan",
    "mekanisme_keamanan": "Enkripsi AES-256.",
    "kontak_penanggung_jawab": "privasi@contoh.id",
}
for _f in list(FIELDS_PENUH):
    FIELDS_PENUH[f"bukti_{_f}"] = FIELDS_PENUH[_f]


def test_proyeksi_hanya_membawa_empat_field():
    hasil = _proyeksi_ringkas(FIELDS_PENUH)
    field_terpilih = [k for k in hasil["fields"] if not k.startswith("bukti_")]
    assert len(field_terpilih) == 4
    assert "mekanisme_keamanan" not in hasil["fields"], "field di luar empat field utama tidak boleh ikut"


def test_proyeksi_menyertakan_bukti_pasangannya():
    hasil = _proyeksi_ringkas(FIELDS_PENUH)
    for k in [k for k in hasil["fields"] if not k.startswith("bukti_")]:
        assert f"bukti_{k}" in hasil["fields"]


def test_ringkasan_satu_paragraf_dan_jujur_soal_kekosongan():
    hasil = _proyeksi_ringkas(FIELDS_PENUH)
    assert len(hasil["ringkasan"].splitlines()) == 1
    assert "tidak disebutkan" in hasil["ringkasan"], "field kosong harus tetap terbaca sebagai tidak disebutkan"


def test_mode_tidak_dikenal_ditolak():
    with pytest.raises(ValueError, match="mode harus"):
        extract_fields("teks apa pun", mode="ringkas-sekali")


def test_skema_penuh_tetap_18_key():
    """Mode ringkas tidak boleh mengubah daftar field wajib untuk mode penuh."""
    assert len(REQUIRED_FIELDS) == 18
