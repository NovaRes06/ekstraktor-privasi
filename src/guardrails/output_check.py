"""
src/guardrails/output_check.py — Lapis 4 guardrails: periksa output sebelum ditampilkan.

Kenapa lapis ini ada: instruksi di prompt (lapis 2) bisa dilemahkan oleh teks lain di
konteks yang sama. Pemeriksaan di sini berjalan SETELAH model selesai, di kode, jadi
tidak bergantung pada kepatuhan model.

Yang diperiksa:
  1. output tidak kosong;
  2. tidak membocorkan system prompt (potongan 8 kata yang identik dengan prompt);
  3. tidak memberi putusan kepatuhan ("kebijakan ini patuh") — produk ini sengaja
     tidak menyimpulkan patuh/tidak patuh terhadap UU PDP;
  4. jawaban yang memakai sumber wajib menyebut nomor rujukannya ([1], [2], ...);
  5. bukti pada hasil ekstraksi benar-benar ada di dokumen (atau persis
     "tidak disebutkan").

Batas yang diketahui: pemeriksaan 2 dan 5 bersifat literal, jadi parafrase halus
bisa lolos. Ini dicatat di guardrails.md, bukan disembunyikan.
"""

from __future__ import annotations

import re

MAKS_POTONGAN_PROMPT = 8  # jumlah kata per potongan yang dianggap "kebocoran"

# Putusan kepatuhan yang tidak boleh dikeluarkan sistem (produk = ekstraktor, bukan penilai).
POLA_PUTUSAN = [
    r"kebijakan\s+ini\s+(sudah\s+)?(patuh|tidak\s+patuh|melanggar|memenuhi)",
    r"(patuh|tidak\s+patuh)\s+terhadap\s+uu\s+pdp",
    r"kesimpulan(nya)?\s*:\s*(patuh|tidak\s+patuh)",
    r"this\s+policy\s+(is|is\s+not)\s+compliant",
]

_MAKS_KALIMAT_KUTIPAN = 2  # prompt v2 meminta bukti maksimal 2 kalimat


def _normalisasi(teks: str) -> str:
    return re.sub(r"\s+", " ", teks.lower()).strip()


def _potongan(kata: list[str], n: int) -> set[str]:
    return {" ".join(kata[i:i + n]) for i in range(len(kata) - n + 1)}


def periksa_kebocoran_prompt(jawaban: str, system_prompt: str) -> list[str]:
    """Deteksi potongan panjang system prompt yang muncul apa adanya di output."""
    if not system_prompt or not jawaban:
        return []

    kata_prompt = _normalisasi(system_prompt).split()
    kata_jawaban = _normalisasi(jawaban).split()
    if len(kata_prompt) < MAKS_POTONGAN_PROMPT or len(kata_jawaban) < MAKS_POTONGAN_PROMPT:
        return []

    bersama = _potongan(kata_prompt, MAKS_POTONGAN_PROMPT) & _potongan(kata_jawaban, MAKS_POTONGAN_PROMPT)
    if bersama:
        contoh = sorted(bersama)[0]
        return [f"output memuat {len(bersama)} potongan {MAKS_POTONGAN_PROMPT} kata yang identik dengan "
                f"system prompt (contoh: \"{contoh[:80]}...\")"]
    return []


def periksa_putusan_kepatuhan(jawaban: str) -> list[str]:
    """Produk tidak boleh menyimpulkan patuh/tidak patuh — itu keputusan manusia."""
    for pola in POLA_PUTUSAN:
        cocok = re.search(pola, jawaban, re.IGNORECASE)
        if cocok:
            return [f"output memberi putusan kepatuhan (\"{cocok.group(0)}\"), padahal sistem hanya "
                    "mengekstrak dan merujuk pasal"]
    return []


def periksa_rujukan(jawaban: str, jumlah_sumber: int) -> list[str]:
    """Bila jawaban memakai sumber, ia wajib menyebut nomor rujukan yang benar."""
    if jumlah_sumber == 0 or not jawaban.strip():
        return []

    nomor = {int(n) for n in re.findall(r"\[(\d{1,2})\]", jawaban)}
    if not nomor:
        return ["jawaban tidak menyebut satu pun nomor rujukan ([1], [2], ...) padahal sumber dikirim"]

    di_luar = sorted(n for n in nomor if n < 1 or n > jumlah_sumber)
    if di_luar:
        return [f"jawaban merujuk sumber [{di_luar[0]}] padahal hanya {jumlah_sumber} sumber yang dikirim"]
    return []


def periksa_jawaban(jawaban: str, *, jumlah_sumber: int = 0, system_prompt: str = "") -> list[str]:
    """Kumpulkan semua masalah pada jawaban bebas. Kosong = lolos."""
    masalah: list[str] = []

    if not jawaban or not jawaban.strip():
        return ["output kosong — tidak ada yang boleh ditampilkan"]

    if system_prompt:
        masalah.extend(periksa_kebocoran_prompt(jawaban, system_prompt))
    masalah.extend(periksa_putusan_kepatuhan(jawaban))
    masalah.extend(periksa_rujukan(jawaban, jumlah_sumber))
    return masalah


def periksa_ekstraksi(fields: dict, dokumen: str) -> list[str]:
    """
    Lapis 4 untuk hasil ekstraksi: bukti harus benar-benar ada di dokumen.

    Ini pemeriksaan TAMBAHAN di atas validasi skema di extractor.py. Skema hanya
    memastikan bentuknya benar; pemeriksaan ini memastikan isinya bisa ditelusuri.
    """
    masalah: list[str] = []
    dokumen_normal = _normalisasi(dokumen)

    def _jumlah_kalimat(teks: str) -> int:
        # Hitung tanda akhir kalimat yang diikuti spasi/akhir teks. Singkatan seperti
        # "PT." ikut terhitung -- itu diterima, karena aturan ini sengaja longgar
        # (tujuannya menangkap kutipan panjang, bukan menghukum singkatan).
        return len(re.findall(r"[.!?](?:\s|$)", teks)) or 1

    for kunci, nilai in fields.items():
        if not kunci.startswith("bukti_"):
            continue
        bukti = str(nilai).strip()
        if not bukti or bukti.lower() == "tidak disebutkan":
            continue
        if _jumlah_kalimat(bukti) > _MAKS_KALIMAT_KUTIPAN:
            masalah.append(f"{kunci}: kutipan bukti lebih dari {_MAKS_KALIMAT_KUTIPAN} kalimat "
                           f"({len(bukti)} karakter) — bukan kutipan ringkas yang diminta prompt")
        if _normalisasi(bukti) not in dokumen_normal:
            masalah.append(f"{kunci}: kutipan tidak ditemukan apa adanya di dokumen — bukti tidak bisa diverifikasi")
    return masalah
