"""
src/agent/tools.py — tool yang dipanggil agent, beserta BATAS AKSES yang dipasang di kode.

Modul Minggu 13: batas akses yang hanya ditulis di prompt adalah celah, karena
penegakannya bergantung pada kepatuhan model. Karena itu setiap batas di bawah
diperiksa di sini, di kode, sebelum tool menyentuh apa pun:

  cari_dokumen   -> hanya membaca index vektor; tidak bisa menulis, tidak bisa jaringan
  baca_dokumen   -> hanya berkas di data/raw/ (daftar putih), maksimal 1.200 kata/panggilan
  ambil_field    -> hanya berkas di data/raw/, hanya 9 field skema, satu panggilan model
  simpan_laporan -> hanya folder logs/laporan-agent/, nama disanitasi, maksimal 20.000 karakter,
                    dan WAJIB disetujui manusia (lapis 5) — lihat agent.py

Tool yang tidak ada di TOOLS tidak bisa dipanggil sama sekali; agent tidak punya
jalan untuk menjalankan perintah shell, mengirim email, atau membaca berkas lain.
"""

from __future__ import annotations

import re
from pathlib import Path

from dotenv import load_dotenv

from src.extraction.extractor import BASE_FIELDS, extract_fields
from src.rag.vectorstore import retrieve

load_dotenv()

DATA_RAW_DIR = Path("data/raw")
LAPORAN_DIR = Path("logs/laporan-agent")

MAKS_KATA_BACA = 1_200
MAKS_PANJANG_LAPORAN = 20_000
MAKS_K_CHUNK = 10
NAMA_BERKAS_VALID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,60}\.md$")

# Berkas katalog asal dokumen bukan dokumen rujukan, jadi tidak boleh dibaca agent
# sebagai sumber jawaban.
BERKAS_DIABAIKAN = {"sumber.md"}


class ToolError(ValueError):
    """Kegagalan tool yang aman ditampilkan ke agent (bukan bug kode)."""


def dokumen_tersedia() -> list[str]:
    """Daftar putih dokumen yang boleh dibaca agent (dihitung ulang tiap panggilan)."""
    if not DATA_RAW_DIR.exists():
        return []
    return sorted(
        p.name for p in [*DATA_RAW_DIR.glob("*.txt"), *DATA_RAW_DIR.glob("*.md")]
        if p.name.lower() not in BERKAS_DIABAIKAN
    )


def _path_dokumen(nama: str) -> Path:
    """Pastikan berkas yang diminta benar-benar ada di daftar putih data/raw/."""
    if nama not in dokumen_tersedia():
        raise ToolError(
            f"Dokumen '{nama}' tidak ada di daftar putih. Yang boleh dibaca: {', '.join(dokumen_tersedia())}"
        )
    return DATA_RAW_DIR / nama


def _bersihkan_header(teks: str) -> str:
    """Buang baris 'Sumber:'/'Diunduh:' hasil unduhan supaya tidak terbaca sebagai isi kebijakan."""
    baris = teks.splitlines()
    while baris and (baris[0].startswith(("Sumber:", "Diunduh:")) or not baris[0].strip()):
        baris.pop(0)
    return "\n".join(baris).strip()


# --- tool 1 -----------------------------------------------------------------

def cari_dokumen(query: str, k: int = 5) -> dict:
    """
    Cari potongan dokumen yang relevan secara makna (RAG).

    Batas akses: hanya membaca index; k dibatasi 1..10; query maksimal 500 karakter.
    """
    if not isinstance(query, str) or not query.strip():
        raise ToolError("Argumen 'query' wajib berisi teks.")
    if len(query) > 500:
        raise ToolError("Argumen 'query' maksimal 500 karakter; ringkas dulu pertanyaannya.")
    if not isinstance(k, int) or not 1 <= k <= MAKS_K_CHUNK:
        raise ToolError(f"Argumen 'k' harus bilangan bulat 1..{MAKS_K_CHUNK}.")

    chunks = retrieve(query, k=k)
    return {
        "jumlah": len(chunks),
        "chunks": [
            {
                "dokumen": c["source_doc"],
                "bagian": c["chunk_index"],
                "jarak": round(float(c["jarak"]), 4),
                "teks": c["text"][:900],
            }
            for c in chunks
        ],
        "catatan": "jarak makin kecil = makin mirip; di atas 0,65 sudah dibuang oleh sistem",
    }


# --- tool 2 -----------------------------------------------------------------

def baca_dokumen(nama_file: str, mulai_kata: int = 0, jumlah_kata: int = MAKS_KATA_BACA) -> dict:
    """
    Baca sebagian dokumen dari data/raw/ (bukan seluruh berkas sekaligus).

    Batas akses: hanya berkas di daftar putih, maksimal 1.200 kata per panggilan.
    """
    path = _path_dokumen(nama_file)

    if not isinstance(mulai_kata, int) or mulai_kata < 0:
        raise ToolError("Argumen 'mulai_kata' harus bilangan bulat >= 0.")
    if not isinstance(jumlah_kata, int) or not 1 <= jumlah_kata <= MAKS_KATA_BACA:
        raise ToolError(f"Argumen 'jumlah_kata' harus 1..{MAKS_KATA_BACA}.")

    teks = _bersihkan_header(path.read_text(encoding="utf-8"))
    kata = teks.split()
    potong = kata[mulai_kata:mulai_kata + jumlah_kata]

    return {
        "dokumen": nama_file,
        "total_kata": len(kata),
        "mulai_kata": mulai_kata,
        "jumlah_kata": len(potong),
        "teks": " ".join(potong),
        "ada_lagi": mulai_kata + len(potong) < len(kata),
    }


# --- tool 3 -----------------------------------------------------------------

def ambil_field(nama_file: str, field: str) -> dict:
    """
    Ambil SATU field skema + buktinya dari satu dokumen (satu panggilan model).

    Batas akses: dokumen harus ada di daftar putih; field harus salah satu dari 9
    field skema. Konteks yang dikirim ke model hanya potongan dokumen yang paling
    relevan dengan field itu, bukan seluruh berkas — supaya biaya tetap kecil.
    """
    _path_dokumen(nama_file)

    if field not in BASE_FIELDS:
        raise ToolError(f"Field '{field}' tidak ada di skema. Pilihan: {', '.join(BASE_FIELDS)}")

    teks = _bersihkan_header((DATA_RAW_DIR / nama_file).read_text(encoding="utf-8"))

    # Ambil potongan dokumen INI yang paling relevan dengan field yang diminta.
    kata_kunci = field.replace("_", " ")
    konteks = [c["text"] for c in retrieve(kata_kunci, k=12) if c["source_doc"] == nama_file][:3]
    if not konteks:
        # Cadangan: kalau index belum memuat dokumen ini, pakai bagian awal dokumen.
        konteks = [" ".join(teks.split()[:3_000])]

    hasil = extract_fields("\n\n".join(konteks))
    fields = hasil["fields"]

    return {
        "dokumen": nama_file,
        "field": field,
        "nilai": fields.get(field, "tidak disebutkan"),
        "bukti": fields.get(f"bukti_{field}", "tidak disebutkan"),
        "konteks_kata": len(" ".join(konteks).split()),
        "usage": hasil.get("usage", {}),
    }


# --- tool 4 (butuh persetujuan manusia) --------------------------------------

def simpan_laporan(nama_file: str, isi: str) -> dict:
    """
    Simpan laporan ke logs/laporan-agent/.

    Batas akses: nama berkas harus cocok pola aman (huruf kecil/angka/-/_), tidak boleh
    mengandung pemisah folder, isi maksimal 20.000 karakter. Fungsi ini sendiri TIDAK
    memeriksa persetujuan — persetujuan diperiksa agent.py SEBELUM tool ini dipanggil.
    """
    if not isinstance(nama_file, str) or not NAMA_BERKAS_VALID.match(nama_file):
        raise ToolError(
            "Nama berkas harus huruf kecil/angka/'-'/'_' dan diakhiri .md "
            "(contoh: perbandingan-retensi.md). Pemisah folder tidak diizinkan."
        )
    if not isinstance(isi, str) or not isi.strip():
        raise ToolError("Argumen 'isi' wajib berisi teks laporan.")
    if len(isi) > MAKS_PANJANG_LAPORAN:
        raise ToolError(f"Isi laporan maksimal {MAKS_PANJANG_LAPORAN:,} karakter.")

    LAPORAN_DIR.mkdir(parents=True, exist_ok=True)
    tujuan = LAPORAN_DIR / nama_file
    tujuan.write_text(isi, encoding="utf-8")

    return {"tersimpan": str(tujuan), "jumlah_karakter": len(isi)}


# --- katalog tool -----------------------------------------------------------

TOOLS = {
    "cari_dokumen": {
        "fungsi": cari_dokumen,
        "deskripsi": "Cari potongan dokumen rujukan yang relevan. Argumen: query (str), k (int 1-10).",
        "butuh_persetujuan": False,
    },
    "baca_dokumen": {
        "fungsi": baca_dokumen,
        "deskripsi": (
            "Baca sebagian dokumen dari data/raw/. Argumen: nama_file (str), "
            "mulai_kata (int), jumlah_kata (int, maks 1200)."
        ),
        "butuh_persetujuan": False,
    },
    "ambil_field": {
        "fungsi": ambil_field,
        "deskripsi": (
            "Ambil satu field skema + buktinya dari satu dokumen. Argumen: nama_file (str), "
            f"field (salah satu dari: {', '.join(BASE_FIELDS)})."
        ),
        "butuh_persetujuan": False,
    },
    "simpan_laporan": {
        "fungsi": simpan_laporan,
        "deskripsi": (
            "Simpan laporan Markdown ke logs/laporan-agent/. Argumen: nama_file (str, contoh "
            "perbandingan-retensi.md), isi (str). TINDAKAN TIDAK BISA DIBATALKAN — butuh persetujuan manusia."
        ),
        "butuh_persetujuan": True,
    },
}


def jalankan_tool(nama: str, argumen: dict) -> dict:
    """Jalankan satu tool berdasarkan nama. Menolak tool yang tidak terdaftar."""
    if nama not in TOOLS:
        raise ToolError(f"Tool '{nama}' tidak terdaftar. Pilihan: {', '.join(TOOLS)}")
    if not isinstance(argumen, dict):
        raise ToolError("Argumen tool harus berupa objek JSON.")

    return TOOLS[nama]["fungsi"](**argumen)
