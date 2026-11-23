"""
Uji koreksi peringkat retrieval (src/rag/vectorstore.py).

Latar: kasus U07 gagal bukan karena jawabannya tidak ada di index, melainkan
karena chunk pasal 9 (jarak 0,5031) kalah dari enam chunk umum ShopeePay
(0,4661-0,4992). Selisih sekecil itu tidak cukup untuk dipercaya, jadi peringkat
dibantu dua sinyal kata: nama dokumen yang disebut pertanyaan dan frasa persis.

Uji di sini hanya menguji fungsi penilai (tanpa memanggil API embedding).
"""

from src.rag.vectorstore import (
    DOCUMENT_BONUS,
    PHRASE_BONUS,
    _document_name,
    _query_phrases,
    _query_terms,
    _ranking_bonus,
)

QUERY = "Bagaimana ShopeePay membagikan data pengguna ke pihak ketiga?"


def test_nama_dokumen_dinormalkan():
    assert _document_name("kebijakan-shopeepay.txt") == "shopeepay"
    assert _document_name("ringkasan-pasal-uu-pdp.md") == "uu pdp"


def test_kata_umum_tidak_dihitung_sebagai_istilah():
    istilah = _query_terms(QUERY)
    assert "bagaimana" not in istilah
    assert "pihak" in istilah and "ketiga" in istilah


def test_frasa_mengambil_pasangan_kata_berurutan():
    assert "pihak ketiga" in _query_phrases(QUERY)
    # "ke" kata umum, jadi pasangan yang melewatinya tidak dianggap frasa
    assert "pengguna ke" not in _query_phrases(QUERY)


def test_chunk_pasal_9_diutamakan_daripada_chunk_umum():
    """Inti perbaikan U07: chunk yang memuat frasa + nama dokumen menang."""
    chunk_umum = "ShopeePay sangat menjaga kerahasiaan data pribadi pengguna."
    chunk_pasal_9 = (
        "9. APAKAH PERSEROAN MENGUNGKAPKAN INFORMASI KEPADA PIHAK LUAR? "
        "9.1 Kami akan mengungkapkan data pribadi Anda kepada penyedia layanan "
        "pihak ketiga, agen dan/atau afiliasi atau perusahaan terkait kami."
    )

    bonus_umum = _ranking_bonus(QUERY, chunk_umum, "kebijakan-shopeepay.txt")
    bonus_pasal = _ranking_bonus(QUERY, chunk_pasal_9, "kebijakan-shopeepay.txt")

    assert bonus_pasal > bonus_umum
    # jarak 0,5031 vs 0,4661: koreksi harus lebih besar dari selisih itu
    assert bonus_pasal - bonus_umum > 0.5031 - 0.4661


def test_dokumen_lain_tidak_mendapat_bonus_nama():
    teks = "Kami mengungkapkan data pribadi Anda kepada pihak ketiga."
    bonus_lain = _ranking_bonus(QUERY, teks, "kebijakan-tokopedia.txt")
    bonus_benar = _ranking_bonus(QUERY, teks, "kebijakan-shopeepay.txt")
    assert bonus_lain == PHRASE_BONUS
    assert bonus_benar == DOCUMENT_BONUS + PHRASE_BONUS


def test_tanpa_kecocokan_tidak_ada_bonus():
    assert _ranking_bonus(QUERY, "Resep nasi goreng sederhana.", "kebijakan-ovo.txt") == 0.0
