"""
Uji logika pemecahan dokumen (src/rag/chunker.py).

Ini modul paling berbahaya di proyek: dulu `chunk_text` bisa berputar selamanya
kalau overlap >= ukuran chunk, dan karena dipanggil dari build_index.py itu
artinya skrip indexing membekukan tanpa pesan apa pun. Setiap uji di sini
dijalankan lewat _dengan_batas_waktu supaya kegagalan berupa "menggantung"
terbaca sebagai GAGAL, bukan sebagai pytest yang hang.
"""

import threading

import pytest

from src.rag.chunker import Chunk, chunk_by_heading, chunk_text

BATAS_WAKTU = 5.0


def _dengan_batas_waktu(fn, timeout: float = BATAS_WAKTU):
    """Jalankan fn di thread latar; gagal kalau belum selesai dalam `timeout` detik."""
    kotak: dict = {}

    def target() -> None:
        try:
            kotak["nilai"] = fn()
        except BaseException as exc:
            # Galat apapun di thread latar disalurkan ulang ke thread utama,
            # supaya kegagalan tampil sebagai uji gagal, bukan menggantung.
            kotak["galat"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise AssertionError(
            f"chunk_text tidak berhenti dalam {timeout} detik -- infinite loop."
        )
    if "galat" in kotak:
        raise kotak["galat"]
    return kotak.get("nilai")


def test_teks_kosong_menghasilkan_chunk_kosong():
    assert chunk_text("", "kosong.txt") == []


def test_teks_pendek_menghasilkan_satu_chunk():
    hasil = chunk_text("hanya beberapa kata saja", "pendek.txt")
    assert len(hasil) == 1
    assert hasil[0].chunk_index == 0
    assert hasil[0].source_doc == "pendek.txt"


def test_index_chunk_unik_dan_berurutan():
    hasil = _dengan_batas_waktu(lambda: chunk_text("kata " * 400, "uji.txt"))
    indeks = [c.chunk_index for c in hasil]
    assert indeks == sorted(indeks)
    assert len(set(indeks)) == len(indeks), "chunk_index duplikat -- id di ChromaDB akan bentrok"


def test_overlap_benar_benar_terpotong():
    """Dua chunk berurutan harus berbagi `overlap_words` kata terakhir/awal."""
    kata = [f"k{i}" for i in range(400)]
    hasil = _dengan_batas_waktu(
        lambda: chunk_text(" ".join(kata), "uji.txt", chunk_size_words=50, overlap_words=10)
    )
    pertama, kedua = hasil[0], hasil[1]
    ekor = pertama.text.split()[-10:]
    kepala = kedua.text.split()[:10]
    assert ekor == kepala, "overlap tidak diterapkan -- informasi di batas chunk bisa hilang"


def test_seluruh_kata_tersimpan():
    kata = " ".join(f"kat{n}" for n in range(200))
    hasil = _dengan_batas_waktu(lambda: chunk_text(kata, "uji.txt"))
    tersimpan = {w for c in hasil for w in c.text.split()}
    assert tersimpan == set(kata.split()), "ada kata yang hilang saat pemecahan"


# --- pertahanan terhadap infinite loop -------------------------------------

@pytest.mark.parametrize(
    "chunk_size,overlap",
    [
        (10, 10),   # sama besar -> start tidak pernah maju
        (10, 11),   # overlap lebih besar -> start mundur
        (5, 5),     # sama besar, ukuran kecil
        (10, 20),   # jauh lebih besar
    ],
)
def test_overlap_terlalu_besar_ditolak_bukan_menggantung(chunk_size, overlap):
    with pytest.raises(ValueError, match="overlap_words"):
        _dengan_batas_waktu(
            lambda: chunk_text(
                "kata " * 50,
                "uji.txt",
                chunk_size_words=chunk_size,
                overlap_words=overlap,
            )
        )


@pytest.mark.parametrize("chunk_size", [0, -1, -150])
def test_ukuran_chunk_non_positif_ditolak(chunk_size):
    with pytest.raises(ValueError, match="chunk_size_words"):
        _dengan_batas_waktu(
            lambda: chunk_text("kata " * 20, "uji.txt", chunk_size_words=chunk_size)
        )


@pytest.mark.parametrize("overlap", [-1, -30])
def test_overlap_negatif_ditolak(overlap):
    with pytest.raises(ValueError, match="overlap_words"):
        _dengan_batas_waktu(
            lambda: chunk_text(
                "kata " * 20, "uji.txt", chunk_size_words=50, overlap_words=overlap
            )
        )


def test_overlap_satu_kurang_dari_ukuran_chunk_masih_diperbolehkan():
    """Batas atas yang sah: maju perlahan tapi tetap berhenti."""
    hasil = _dengan_batas_waktu(
        lambda: chunk_text("kata " * 60, "uji.txt", chunk_size_words=10, overlap_words=9)
    )
    assert len(hasil) > 1


def test_overlap_nol_diperbolehkan():
    hasil = _dengan_batas_waktu(
        lambda: chunk_text("kata " * 60, "uji.txt", chunk_size_words=20, overlap_words=0)
    )
    assert len(hasil) == 3  # 60 / 20 tanpa tumpang tindih


# --- pemecahan per-heading ---------------------------------------------------

def test_chunk_by_heading():
    md = "# Judul\n\n## Bagian A\nisi A\n\n## Bagian B\nisi B\n"
    hasil = chunk_by_heading(md, "z.md")
    judul = [c.text.split("\n", 1)[0] for c in hasil]
    assert "Bagian A" in judul and "Bagian B" in judul
    assert all(isinstance(c, Chunk) for c in hasil)


def test_chunk_by_heading_melewati_badan_kosong():
    md = "awal\n\n## Kosong\n\n## Berisi\nisi\n"
    hasil = chunk_by_heading(md, "z.md")
    assert all(c.text.split("\n", 1)[1].strip() for c in hasil)
