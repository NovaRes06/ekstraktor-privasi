"""
src/rag/embedder.py — ubah teks jadi vektor angka (embedding) memakai Gemini.

Embedding adalah representasi angka dari MAKNA teks, bukan dari kata-katanya
persis. Dua kalimat dengan kata berbeda tapi makna mirip akan punya embedding
yang 'berdekatan' secara matematis -- itu dasar cara kerja pencarian semantik.

Model: gemini-embedding-001 (GA, bukan preview).

Batas free tier yang sudah terbukti kena di proyek ini:
  - maksimal 100 teks per SATU panggilan  (error 400)
  - maksimal 100 teks per MENIT           (error 429)
Karena itu modul ini (1) memecah teks jadi batch kecil, (2) menunggu sendiri
kalau kuota semenit hampir habis, dan (3) mengulang otomatis kalau tetap kena 429.
"""

import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "gemini-embedding-001"

MAX_BATCH_SIZE = 45           # teks per panggilan (dua batch = 90, muat dalam satu menit)
RATE_LIMIT_PER_MINUTE = 90    # batas sebenarnya 100; disisakan margin
MAX_RETRY = 6

# Catatan (waktu, jumlah teks) dari panggilan sukses dalam satu menit terakhir
_sent_log: list[tuple[float, int]] = []


def _tunggu_kuota(jumlah: int) -> None:
    """Tidur secukupnya sampai mengirim `jumlah` teks tidak melewati batas per menit."""
    while True:
        sekarang = time.monotonic()
        _sent_log[:] = [(t, n) for t, n in _sent_log if sekarang - t < 60]
        terpakai = sum(n for _, n in _sent_log)

        if terpakai + jumlah <= RATE_LIMIT_PER_MINUTE or not _sent_log:
            return

        tunggu = 60 - (sekarang - _sent_log[0][0]) + 1
        print(f"  [menunggu kuota gratis Gemini, sekitar {tunggu:.0f} detik...]")
        time.sleep(max(tunggu, 1))


def _embed_batch(batch: list[str], task_type: str) -> list[list[float]]:
    for percobaan in range(1, MAX_RETRY + 1):
        _tunggu_kuota(len(batch))
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
        except errors.ClientError as e:
            kena_429 = getattr(e, "code", None) == 429 or "429" in str(e)[:20]
            if not kena_429 or percobaan == MAX_RETRY:
                raise
            # Google menyebut jeda yang disarankan di pesan error: "retry in 17.6s"
            cocok = re.search(r"retry in ([\d.]+)s", str(e))
            jeda = float(cocok.group(1)) + 3 if cocok else 20
            print(f"  [kena batas kecepatan, mengulang dalam {jeda:.0f} detik "
                  f"(percobaan {percobaan}/{MAX_RETRY})]")
            time.sleep(jeda)
            continue

        _sent_log.append((time.monotonic(), len(batch)))
        return [list(e.values) for e in result.embeddings]

    raise RuntimeError("embed_content gagal setelah semua percobaan ulang")


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Buat embedding untuk sekumpulan teks (dipakai saat indexing dokumen).

    task_type="RETRIEVAL_DOCUMENT" untuk dokumen yang akan disimpan,
    task_type="RETRIEVAL_QUERY" untuk pertanyaan yang akan dicari -- keduanya
    dioptimalkan beda oleh model, jangan ditukar.
    """
    if not texts:
        return []

    hasil: list[list[float]] = []
    for i in range(0, len(texts), MAX_BATCH_SIZE):
        hasil.extend(_embed_batch(texts[i:i + MAX_BATCH_SIZE], task_type))
    return hasil


def embed_query(query: str) -> list[float]:
    """Buat embedding untuk SATU pertanyaan (dipakai saat pencarian/retrieval)."""
    return _embed_batch([query], "RETRIEVAL_QUERY")[0]
