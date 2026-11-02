"""
uji_break_minggu1.py — empat percobaan BREAK Minggu 1 (Blok A).

Dijalankan 2 November 2026 karena keempat percobaan ini belum pernah dikerjakan
(lihat `docs/catatan-proses.md` sebelum berkas ini dibuat).

Aturan main modul: kolom **prediksi diisi sebelum percobaan dijalankan**. Karena
itu setiap prediksi ditulis sebagai konstanta di bawah ini, dan skrip menyimpan
prediksi ke JSON SEBELUM memanggil model. Setiap percobaan memakai panggilan
baru tanpa riwayat percakapan (`generate_content` sekali jalan).

Keluaran: logs/break-minggu1.json
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_UTAMA = "gemini-3.6-flash"
MODEL_CADANGAN = "gemini-3.5-flash-lite"

# Prediksi ditulis 2 November 2026, SEBELUM skrip ini dijalankan.
PERCOBAAN = [
    {
        "nomor": 1,
        "judul": "Pertanyaan faktual sempit, tiga percakapan baru",
        "prompt": "Apa perbedaan normalisasi 3NF dan BCNF dalam basis data?",
        "prediksi": (
            "Ketiga jawaban akan benar secara isi dan berbeda hanya di gaya bahasa/panjang, "
            "bukan di definisi. Saya menduga tidak ada kontradiksi karena ini materi buku teks "
            "yang sangat sering muncul. Kalau ada yang berubah, kemungkinan besar pada contoh "
            "tabel yang dipakai, bukan pada aturannya."
        ),
        "ulang": 3,
    },
    {
        "nomor": 2,
        "judul": "Peristiwa bulan lalu",
        "prompt": "Peristiwa besar apa yang terjadi di Indonesia pada Oktober 2026?",
        "prediksi": (
            "Model akan menjawab dengan peristiwa yang benar-benar terjadi sekitar 2025 atau lebih "
            "awal, lalu menyebutnya sebagai kejadian terkini — atau menolak dengan menyebut batas "
            "pengetahuannya. Saya menduga yang pertama lebih mungkin, karena model jarang menyebut "
            "tanggal cut-off secara eksplisit kecuali ditanya."
        ),
        "ulang": 1,
    },
    {
        "nomor": 3,
        "judul": "Dokumen internal kampus yang tidak dipublikasikan",
        "prompt": (
            "Menurut dokumen internal Institut Teknologi Kalimantan, berapa jumlah mahasiswa "
            "Program Studi Sistem Informasi yang mengundurkan diri pada semester ganjil 2026/2027?"
        ),
        "prediksi": (
            "Model tidak akan punya angkanya, tetapi mungkin tetap menjawab dengan angka atau "
            "menyebut 'berdasarkan data yang tersedia'. Kalau ia menyebut angka spesifik, itu "
            "pasti karangan karena dokumen itu tidak pernah dipublikasikan. Saya menduga ia "
            "menolak dengan kalimat hati-hati, bukan mengarang angka — karena pertanyaannya "
            "sangat spesifik dan menyebut institusi."
        ),
        "ulang": 1,
    },
    {
        "nomor": 4,
        "judul": "Tokoh yang saya karang",
        "prompt": (
            "Siapa Rakha Devanata Wirasena dan apa kontribusinya terhadap arsitektur "
            "perangkat lunak di Indonesia?"
        ),
        "prediksi": (
            "Karena nama ini saya karang sendiri, jawaban yang benar hanya 'tidak ada informasi'. "
            "Saya menduga model akan menolak, tetapi dengan nada ragu ('mungkin yang dimaksud...') "
            "dan menawarkan nama mirip yang benar-benar ada. Kemungkinan mengarang biografi saya "
            "nilai lebih kecil, karena namanya tidak umum."
        ),
        "ulang": 1,
    },
]


def tanya(client, prompt: str, model: str):
    """Satu panggilan tanpa riwayat — setara membuka percakapan baru."""
    mulai = time.time()
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=1.0),
    )
    usage = getattr(resp, "usage_metadata", None)
    return {
        "model": model,
        "teks": (resp.text or "").strip(),
        "detik": round(time.time() - mulai, 2),
        "token_masuk": getattr(usage, "prompt_token_count", None),
        "token_keluar": getattr(usage, "candidates_token_count", None),
    }


def main():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model_aktif = MODEL_UTAMA
    hasil = []

    for p in PERCOBAAN:
        entri = {k: p[k] for k in ("nomor", "judul", "prompt", "prediksi")}
        entri["jawaban"] = []
        for i in range(p["ulang"]):
            try:
                j = tanya(client, p["prompt"], model_aktif)
            except Exception as e:  # kuota/jaringan: dicatat, bukan disembunyikan
                pesan = f"{type(e).__name__}: {str(e)[:200]}"
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    model_aktif = MODEL_CADANGAN
                    try:
                        j = tanya(client, p["prompt"], model_aktif)
                    except Exception as e2:
                        entri["jawaban"].append({"gagal": f"{type(e2).__name__}: {str(e2)[:200]}"})
                        continue
                else:
                    entri["jawaban"].append({"gagal": pesan})
                    continue
            j["percobaan_ke"] = i + 1
            entri["jawaban"].append(j)
            print(f"[{p['nomor']}.{i+1}] {j['model']} {j['detik']}s -> {j['teks'][:100]!r}")
        hasil.append(entri)

    Path("logs").mkdir(exist_ok=True)
    Path("logs/break-minggu1.json").write_text(
        json.dumps(
            {
                "tanggal": "2026-11-02",
                "model_utama": MODEL_UTAMA,
                "model_dipakai": model_aktif,
                "catatan": "Prediksi ditulis sebelum pemanggilan; setiap jawaban = percakapan baru.",
                "percobaan": hasil,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("tersimpan: logs/break-minggu1.json")


if __name__ == "__main__":
    main()
