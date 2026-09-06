"""
src/extraction/extractor.py — logika inti ekstraksi, versi Gemini API.

Menggunakan Google GenAI SDK resmi (bukan library lama 'google-generativeai').
Model 'gemini-2.5-flash' dipilih karena termasuk yang tersedia di free tier
(Flash & Flash-Lite masih gratis; model Pro tidak lagi gratis sejak April 2026).
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

SYSTEM_PROMPT_PATH = Path("prompts/system_prompt_v1.md")

REQUIRED_FIELDS = [
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


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def extract_fields(document_text: str) -> dict:
    """
    Kirim teks dokumen ke Gemini, minta ekstraksi 9 field.
    Mengembalikan dict berisi field hasil + metadata pemakaian token.
    """
    system_prompt = load_system_prompt()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=f"Ekstrak informasi dari kebijakan privasi berikut:\n\n{document_text}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",  # minta Gemini keluarkan JSON murni
        ),
    )

    raw_text = (response.text or "").strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        # Kasus gagal parsing = kandidat kuat untuk dicatat di logs/failed_cases.md
        raise ValueError(f"Gagal parsing JSON dari model. Keluaran mentah: {raw_text}") from e

    missing = [f for f in REQUIRED_FIELDS if f not in parsed]

    usage = response.usage_metadata
    return {
        "fields": parsed,
        "missing_fields": missing,
        "usage": {
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
        },
    }
