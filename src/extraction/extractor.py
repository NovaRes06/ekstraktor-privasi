"""
src/extraction/extractor.py — logika inti ekstraksi, versi Gemini API.

Menggunakan Google GenAI SDK resmi (bukan library lama 'google-generativeai').
Model 'gemini-3.6-flash' dipilih karena termasuk yang tersedia di free tier
(Flash & Flash-Lite masih gratis; model Pro butuh billing aktif).
Catatan: Google cukup sering memensiunkan versi model lama untuk akun baru.
Kalau suatu saat muncul error 404 'model no longer available', cek pesan
errornya — biasanya Google langsung kasih tahu nama model pengganti yang
harus dipakai, tinggal ganti nilai MODEL_NAME di bawah ini.

Perubahan v2 (10 Oktober 2026), ikut ketentuan modul Minggu 4-5:
  - system prompt naik ke instruksi/v2.md: 9 field kepatuhan + 9 field bukti
    (kutipan langsung dari dokumen per field).
  - Penanganan kegagalan TIGA LANGKAH sesuai modul Minggu 5:
      1. cek output terhadap schema,
      2. bila tidak valid -> ulangi SEKALI dengan pesan error disertakan,
      3. bila masih tidak valid -> catat, kembalikan kegagalan yang JELAS.
    Jangan menebak dan jangan diam-diam melewatinya.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"

# v2 memakai prompt baru di folder instruksi/; v1 lama tetap tersimpan agar bisa
# dibandingkan (uji v1 vs v2, ketentuan Minggu 4).
SYSTEM_PROMPT_PATH = Path("instruksi/v2.md")

BASE_FIELDS = [
    "jenis_data_dikumpulkan",
    "tujuan_pemrosesan",
    "dasar_pemrosesan",
    "pihak_ketiga_penerima",
    "transfer_lintas_negara",
    "masa_retensi_data",
    "hak_subjek_data",
    "mekanisme_keamanan",
    "kontak_penanggung_jawab",
]

# Semua field wajib: 9 field utama + 9 pasangan bukti.
REQUIRED_FIELDS = BASE_FIELDS + [f"bukti_{f}" for f in BASE_FIELDS]

MAX_ATTEMPTS = 2  # 1 percobaan ulang setelah kegagalan validasi (modul Minggu 5)

# Mode output (ketentuan lingkup lampiran B: K genap wajib punya satu mode ringkas
# selain mode penuh). Mode ringkas adalah PROYEKSI dari hasil penuh yang sama --
# tidak menambah panggilan model, jadi tidak menambah biaya dan kualitas dasarnya
# identik. Yang berubah hanya berapa banyak yang ditampilkan.
MODE_VALID = {"penuh", "ringkas"}
FIELD_RINGKAS = [
    "jenis_data_dikumpulkan",
    "tujuan_pemrosesan",
    "pihak_ketiga_penerima",
    "masa_retensi_data",
]


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _field_tidak_valid(fields: dict) -> list[str]:
    """
    Kembalikan daftar pelanggaran schema terhadap hasil ekstraksi.
    Aturan:
      - semua REQUIRED_FIELDS harus ada;
      - field utama harus string (nilai "tidak disebutkan" sah);
      - bukti harus string; harus benar-benar disebutkan atau di isi persis
        "tidak disebutkan" (tidak boleh string kosong).
    """
    pelanggaran: list[str] = []

    for f in REQUIRED_FIELDS:
        if f not in fields:
            pelanggaran.append(f"key hilang: {f}")
        elif not isinstance(fields[f], str):
            pelanggaran.append(f"key bukan string: {f}")

    for f in BASE_FIELDS:
        if f in fields:
            nilai = str(fields.get(f, "")).strip()
            bukti = str(fields.get(f"bukti_{f}", "")).strip()
            ada = nilai.lower() != "tidak disebutkan"
            if ada and not bukti:
                pelanggaran.append(f"bukti kosong padahal field '{f}' diisi")
            if ada and bukti.lower() == "tidak disebutkan":
                pelanggaran.append(f"field '{f}' diisi tapi buktinya bilang tidak disebutkan")
            if not ada and bukti and bukti.lower() != "tidak disebutkan":
                pelanggaran.append(f"field '{f}' tidak disebutkan tapi buktinya diisi")

    return pelanggaran


def _proyeksi_ringkas(fields: dict) -> dict:
    """Ambil empat field terpenting + buktinya, lalu susun satu paragraf ringkas."""
    terpilih = {k: fields[k] for k in FIELD_RINGKAS if k in fields}
    for k in FIELD_RINGKAS:
        bukti = f"bukti_{k}"
        if bukti in fields:
            terpilih[bukti] = fields[bukti]

    def _isi(kunci: str) -> str:
        nilai = str(fields.get(kunci, "tidak disebutkan")).strip()
        return "tidak disebutkan" if nilai.lower() == "tidak disebutkan" else nilai

    ringkasan = (
        f"Data yang dikumpulkan: {_isi('jenis_data_dikumpulkan')} "
        f"Tujuannya: {_isi('tujuan_pemrosesan')} "
        f"Dibagikan ke: {_isi('pihak_ketiga_penerima')} "
        f"Masa simpan: {_isi('masa_retensi_data')}"
    )

    return {"fields": terpilih, "ringkasan": ringkasan}


def extract_fields(document_text: str, mode: str = "penuh") -> dict:
    """
    Kirim teks dokumen ke Gemini, minta ekstraksi 9 field + 9 bukti.
    Mengembalikan dict berisi field hasil + metadata pemakaian token.

    `mode`:
      - "penuh"   -> 9 field + 9 bukti (perilaku v2 sejak awal);
      - "ringkas" -> 4 field terpenting + bukti + satu paragraf ringkasan.
        Proyeksi dari hasil penuh yang SAMA, jadi tidak ada panggilan model tambahan.

    Penanganan kegagalan tiga langkah:
      1) cek hasil terhadap schema (_field_tidak_valid),
      2) bila tidak valid -> ulangi SEKALI dengan daftar pelanggarannya
         disertakan supaya model tahu apa yang salah,
      3) bila masih tidak valid -> raise ValueError dengan pesan JELAS.
    """
    if mode not in MODE_VALID:
        raise ValueError(f"mode harus salah satu dari {sorted(MODE_VALID)}, bukan '{mode}'")

    system_prompt = load_system_prompt()

    pesan = f"Ekstrak informasi dari kebijakan privasi berikut:\n\n{document_text}"
    tambahan = ""  # pesan error dari percobaan sebelumnya, kalau ada

    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=(pesan + tambahan),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",  # minta Gemini keluarkan JSON murni
            ),
        )

        raw_text = (response.text or "").strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as e:
            if attempt == MAX_ATTEMPTS:
                # Langkah 3: gagal JELAS, bukan ditelan diam-diam.
                raise ValueError(
                    f"Gagal parsing JSON dari model setelah {attempt} percobaan. "
                    f"Keluaran mentah: {raw_text[:500]}"
                ) from e
            tambahan = (
                "\n\nCATATAN: jawabanmu sebelumnya bukan JSON yang valid "
                f"(parse error: {e}). Keluarkan HANYA objek JSON, tanpa teks lain."
            )
            continue  # langkah 2: ulangi sekali dengan pesan error disertakan

        pelanggaran = _field_tidak_valid(parsed)

        if not pelanggaran:
            missing = [f for f in REQUIRED_FIELDS if f not in parsed]
            if missing:
                # Pertahanan dalam penilaian _field_tidak_valid seharusnya
                # membuat daftar ini kosong; tetap dikembalikan sebagai jaga-jaga.
                return {
                    "fields": parsed,
                    "missing_fields": missing,
                    "usage": _usage(response),
                }
            usage = _usage(response)
            hasil = {
                "mode": "penuh",
                "fields": parsed,
                "missing_fields": [],
                "usage": usage,
                "prompt_version": "v2",
            }
            if mode == "ringkas":
                hasil.update(_proyeksi_ringkas(parsed))
                hasil["mode"] = "ringkas"
                hasil["catatan"] = (
                    "Mode ringkas = proyeksi empat field dari hasil penuh yang sama; "
                    "tidak ada panggilan model tambahan."
                )
            return hasil

        if attempt == MAX_ATTEMPTS:
            raise ValueError(
                "Output model melanggar schema setelah "
                f"{attempt} percobaan. Pelanggaran: {pelanggaran}. "
                f"Keluaran mentah: {raw_text[:500]}"
            )

        tambahan = (
            "\n\nCATATAN: jawabanmu sebelumnya melanggar skema berikut:\n- "
            + "\n- ".join(pelanggaran)
            + "\nPerbaiki dan keluarkan kembali HANYA objek JSON yang lengkap."
        )

    # Tidak pernah sampai sini, tapi Python butuh return eksplisit.
    raise RuntimeError("extract_fields keluar dari loop tanpa hasil")


def _usage(response) -> dict:
    usage = response.usage_metadata
    return {
        "input_tokens": getattr(usage, "prompt_token_count", None),
        "output_tokens": getattr(usage, "candidates_token_count", None),
    }
