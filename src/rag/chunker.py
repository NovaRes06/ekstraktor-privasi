"""
src/rag/chunker.py — pecah dokumen panjang jadi potongan (chunk) yang lebih kecil.

Kenapa dipecah: model butuh konteks yang RELEVAN, bukan seluruh dokumen sekaligus.
Memasukkan dokumen 50 halaman ke tiap pemanggilan itu mahal dan rawan 'kehilangan
di tengah' (lihat Konsep Minggu 2). Jadi kita pecah dulu, baru ambil yang relevan
saja saat menjawab pertanyaan (lihat retriever.py).
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source_doc: str   # nama file asal, supaya bisa ditelusuri balik
    chunk_index: int  # urutan chunk dalam dokumen itu


def chunk_text(text: str, source_doc: str, chunk_size_words: int = 150, overlap_words: int = 30) -> list[Chunk]:
    """
    Pecah teks jadi potongan ~150 kata, dengan overlap 30 kata antar potongan.

    Overlap penting: kalau informasi penting kebetulan terpotong persis di batas
    chunk, overlap memastikan ia tetap utuh di salah satu potongan.

    Syarat: 0 <= overlap_words < chunk_size_words. Kalau overlap sama besar atau
    lebih besar dari ukuran chunk, 'start = end - overlap_words' tidak pernah maju
    dan while-loop di bawah tak pernah berhenti (loop tak terbatas yang membekukan
    build_index.py). Ditolak di sini dengan pesan jelas, bukan ditelan diam-diam.
    """
    if chunk_size_words <= 0:
        raise ValueError(f"chunk_size_words harus lebih besar dari 0, bukan {chunk_size_words}")
    if not 0 <= overlap_words < chunk_size_words:
        raise ValueError(
            f"overlap_words harus >= 0 dan lebih kecil dari chunk_size_words "
            f"(overlap_words={overlap_words}, chunk_size_words={chunk_size_words}); "
            "kalau tidak, langkah mundurnya sama besar dengan langkah majunya "
            "sehingga chunk_text tidak pernah selesai."
        )

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    index = 0

    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)

        chunks.append(Chunk(text=chunk_text_str, source_doc=source_doc, chunk_index=index))

        if end >= len(words):
            break

        start = end - overlap_words  # mundur sedikit untuk overlap
        index += 1

    return chunks


def chunk_by_heading(text: str, source_doc: str) -> list[Chunk]:
    """
    Alternatif: pecah berdasarkan heading markdown ('## ...').
    Cocok untuk dokumen yang sudah terstruktur rapi (seperti ringkasan UU PDP kita),
    karena satu heading biasanya = satu topik utuh, lebih baik daripada potong
    per-N-kata yang bisa memotong di tengah topik.
    """
    sections = []
    current_heading = "Pendahuluan"
    current_lines: list[str] = []

    for line in text.split("\n"):
        if line.strip().startswith("## "):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line.strip("# ").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    chunks = []
    for i, (heading, body) in enumerate(sections):
        if not body:
            continue
        chunks.append(Chunk(text=f"{heading}\n{body}", source_doc=source_doc, chunk_index=i))

    return chunks
