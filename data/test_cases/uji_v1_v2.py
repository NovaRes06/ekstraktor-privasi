"""
uji_v1_v2.py — jalankan prompt v1 dan v2 pada 5 input yang sama (komposisi
modul Minggu 4): 2 umum, 2 kasus batas, 1 yang seharusnya ditolak.

Cara pakai:
    python data/test_cases/uji_v1_v2.py

Output: logs/uji_v1_v2.json (bukti sebelum/sesudah untuk CATATAN.md) plus
ringkasan tabel ke terminal.
"""
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

load_dotenv()

BASE_FIELDS = [
    "jenis_data_dikumpulkan", "tujuan_pemrosesan", "dasar_pemrosesan",
    "pihak_ketiga_penerima", "transfer_lintas_negara", "masa_retensi_data",
    "hak_subjek_data", "mekanisme_keamanan", "kontak_penanggung_jawab",
]

INPUT_UJI = {
    "umum_1": (
        "Kami mengumpulkan nama, email, dan nomor telepon untuk memproses "
        "pesanan dan mengirim promosi. Data dibagikan ke mitra logistik."
    ),
    "umum_2": (
        "Aplikasi menyimpan riwayat transaksi dan lokasi perangkat. "
        "Kontak privasi: privacy@contoh.id. "
        "Enkripsi standar industri dipakai saat transmisi."
    ),
    "batas_1_kosong_isi": "Halaman ini disengaja kosong.",
    "batas_2_dua_kategori": (
        "Data keuangan disimpan 5 tahun sesuai ketentuan perpajakan. "
        "Data lokasi dihapus setelah 30 hari."
    ),
    "seharusnya_ditolak": (
        "Resep nasi goreng: tumis bumbu, masukkan nasi, aduk rata, "
        "sajikan hangat."
    ),
}

MODELS = {"v1": "instruksi/v1.md", "v2": "instruksi/v2.md"}
MODEL_NAME = "gemini-3.6-flash"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def jalankan(nama_versi: str, path_prompt: str, teks: str) -> dict:
    prompt = Path(path_prompt).read_text(encoding="utf-8")
    mulai = time.perf_counter()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=f"Ekstrak informasi dari kebijakan privasi berikut:\n\n{teks}",
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            response_mime_type="application/json",
        ),
    )
    detik = round(time.perf_counter() - mulai, 2)
    raw = (response.text or "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "GAGAL_PARSE", "raw": raw[:300], "detik": detik}

    missing = [f for f in BASE_FIELDS if f not in parsed]
    bukti_ada = [f"bukti_{f}" for f in BASE_FIELDS if f"bukti_{f}" in parsed]
    return {
        "status": "OK",
        "detik": detik,
        "missing_fields": missing,
        "jumlah_bukti": len(bukti_ada),
        "fields": parsed,
    }


def main() -> None:
    hasil = {}
    for kasus, teks in INPUT_UJI.items():
        for versi, path in MODELS.items():
            key = f"{kasus}__{versi}"
            print(f"[{key}] ...", flush=True)
            try:
                hasil[key] = jalankan(versi, path, teks)
            except Exception as e:  # galat apa pun dicatat apa adanya sebagai data
                hasil[key] = {"status": "ERROR", "error": str(e)[:300]}

    out = Path("logs/uji_v1_v2.json")
    out.write_text(json.dumps(hasil, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 76}")
    print(f"{'Kasus':<22}{'Versi':<7}{'Status':<13}{'Detik':<8}{'Bukti':<7}{'Missing':<20}")
    print("-" * 76)
    for kasus in INPUT_UJI:
        for versi in MODELS:
            r = hasil[f"{kasus}__{versi}"]
            print(
                f"{kasus:<22}{versi:<7}{r.get('status', '?'):<13}"
                f"{r.get('detik', '-'):<8}"
                f"{r.get('jumlah_bukti', '-'):<7}"
                f"{str(len(r.get('missing_fields', []))) if r.get('status') == 'OK' else '-':<20}"
            )
    print(f"\nBukti lengkap tersimpan: {out}")


if __name__ == "__main__":
    main()
