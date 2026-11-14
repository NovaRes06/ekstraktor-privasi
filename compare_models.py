"""
compare_models.py — Minggu 3, RAKIT butir 4: bandingkan 3 model pada tugas yang sama.

Menjalankan prompt ekstraksi yang IDENTIK pada 3 model Gemini dari tingkat biaya
berbeda (murah, menengah, mahal), mencatat: token masuk/keluar, latensi, dan
perkiraan biaya per pemanggilan.

Kualitas TIDAK bisa diotomatisasi -- itu tugasmu menilai manual (skala 1-5) setelah
membaca hasil ekstraksi tiap model, karena "bagus" di sini artinya "cocok untuk
tugas ekstraksi kebijakan privasi", bukan cuma skor benchmark umum.

Cara pakai:
    python compare_models.py
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT_PATH = Path("prompts/system_prompt_v1.md")
SAMPLE_DOC_PATH = Path("data/sample_kebijakan.txt")

# Tiga model dari tingkat biaya berbeda (murah -> menengah -> mahal).
# Tarif dalam USD per JUTA token, dicek 6 September 2026 dari ai.google.dev/pricing.
# CATATAN: tarif model AI sering berubah -- kalau kamu jalankan skrip ini beberapa
# bulan dari sekarang, cek ulang tarifnya, jangan percaya angka di bawah ini mentah-mentah.
MODELS_TO_COMPARE = [
    {"name": "gemini-3.5-flash-lite", "tarif_masuk": 0.30, "tarif_keluar": 2.50},   # murah
    {"name": "gemini-3.6-flash",      "tarif_masuk": 0.75, "tarif_keluar": 3.75},   # menengah
    {"name": "gemini-3.1-pro-preview", "tarif_masuk": 2.00, "tarif_keluar": 12.00},  # mahal
]


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def call_model(model_name: str, system_prompt: str, document_text: str) -> dict:
    """Panggil satu model, ukur latensi dari sisi klien (bukan cuma dari API)."""
    start = time.perf_counter()
    response = client.models.generate_content(
        model=model_name,
        contents=f"Ekstrak informasi dari kebijakan privasi berikut:\n\n{document_text}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        ),
    )
    elapsed = time.perf_counter() - start

    raw_text = (response.text or "").strip()
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = {"_error": "gagal parsing JSON", "_raw_output": raw_text}

    usage = response.usage_metadata
    return {
        "model": model_name,
        "latensi_detik": round(elapsed, 2),
        "token_masuk": getattr(usage, "prompt_token_count", 0) or 0,
        "token_keluar": getattr(usage, "candidates_token_count", 0) or 0,
        "hasil": parsed,
    }


def hitung_biaya(token_masuk: int, token_keluar: int, tarif_masuk: float, tarif_keluar: float) -> float:
    return (token_masuk / 1_000_000 * tarif_masuk) + (token_keluar / 1_000_000 * tarif_keluar)


def main():
    system_prompt = load_system_prompt()
    document_text = SAMPLE_DOC_PATH.read_text(encoding="utf-8")

    hasil_semua = []

    for model_info in MODELS_TO_COMPARE:
        print(f"\n{'=' * 60}")
        print(f"Menjalankan: {model_info['name']}")
        print("=" * 60)

        try:
            hasil = call_model(model_info["name"], system_prompt, document_text)
        except Exception as e:
            # Kasus gagal ini SENDIRI adalah data penting -- catat, jangan cuma di-skip
            print(f"[GAGAL] {model_info['name']}: {e}")
            hasil_semua.append({
                "model": model_info["name"],
                "status": "GAGAL",
                "error": str(e),
            })
            continue

        biaya = hitung_biaya(
            hasil["token_masuk"], hasil["token_keluar"],
            model_info["tarif_masuk"], model_info["tarif_keluar"],
        )
        hasil["perkiraan_biaya_usd"] = round(biaya, 6)
        hasil["status"] = "OK"
        hasil_semua.append(hasil)

        print(f"Latensi      : {hasil['latensi_detik']} detik")
        print(f"Token masuk  : {hasil['token_masuk']}")
        print(f"Token keluar : {hasil['token_keluar']}")
        print(f"Perkiraan biaya: ${biaya:.6f}")
        print("\nHasil ekstraksi:")
        print(json.dumps(hasil["hasil"], indent=2, ensure_ascii=False))

    # Ringkasan tabel di akhir
    print(f"\n\n{'=' * 60}")
    print("RINGKASAN PERBANDINGAN")
    print("=" * 60)
    print(f"{'Model':<25}{'Status':<10}{'Latensi (s)':<15}{'Biaya (USD)':<15}")
    for h in hasil_semua:
        if h.get("status") == "OK":
            print(f"{h['model']:<25}{'OK':<10}{h['latensi_detik']:<15}{h['perkiraan_biaya_usd']:<15}")
        else:
            print(f"{h['model']:<25}{'GAGAL':<10}{'-':<15}{'-':<15}")

    print("\n[!] Kolom KUALITAS belum terisi di sini -- itu harus kamu nilai MANUAL")
    print("    dengan baca hasil ekstraksi tiap model di atas (skala 1-5), lalu")
    print("    catat di catatan-pemakaian.md, beserta ALASAN kenapa kamu beri skor itu.")

    # Simpan hasil mentah ke file, supaya bisa dibaca ulang tanpa panggil API lagi
    output_path = Path("logs/perbandingan_model.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(hasil_semua, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nHasil lengkap tersimpan di {output_path}")


if __name__ == "__main__":
    main()
