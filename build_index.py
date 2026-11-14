"""
build_index.py — Lapisan 3: bangun ulang index RAG dari dokumen di data/raw/.

Jalankan ini SETIAP KALI kamu menambah/mengubah dokumen rujukan di folder data/raw/.
Tidak perlu dijalankan ulang untuk sekadar menjawab pertanyaan -- itu dilakukan
endpoint /ask di api.py, yang membaca index yang sudah dibangun skrip ini.

Cara pakai:
    python build_index.py
"""

from pathlib import Path

from src.rag.chunker import chunk_by_heading, chunk_text
from src.rag.vectorstore import collection_stats, index_chunks

DATA_RAW_DIR = Path("data/raw")


def main():
    if not DATA_RAW_DIR.exists():
        print(f"[GAGAL] Folder {DATA_RAW_DIR} tidak ditemukan.")
        return

    # SUMBER.md berisi katalog asal dokumen, bukan dokumen rujukan -- jangan diindeks.
    all_files = [
        p for p in [*DATA_RAW_DIR.glob("*.md"), *DATA_RAW_DIR.glob("*.txt")]
        if p.name.upper() != "SUMBER.MD"
    ]

    if not all_files:
        print(f"[PERINGATAN] Tidak ada file .md/.txt di {DATA_RAW_DIR}. "
              "Tambahkan dokumen rujukan dulu sebelum membangun index.")
        return

    total_chunks = 0

    for file_path in all_files:
        print(f"\nMemproses: {file_path.name}")
        text = file_path.read_text(encoding="utf-8")

        # Dokumen markdown terstruktur (ada heading '## ') dipecah per-bagian;
        # dokumen teks polos dipecah per-N-kata.
        if file_path.suffix == ".md" and "## " in text:
            chunks = chunk_by_heading(text, source_doc=file_path.name)
        else:
            chunks = chunk_text(text, source_doc=file_path.name)

        print(f"  -> {len(chunks)} chunk dihasilkan")

        jumlah_tersimpan = index_chunks(chunks)
        total_chunks += jumlah_tersimpan
        print(f"  -> {jumlah_tersimpan} chunk disimpan ke index")

    print(f"\n{'=' * 50}")
    print(f"SELESAI. {len(all_files)} dokumen, total chunk diproses: {total_chunks}")
    print(f"Statistik index: {collection_stats()}")
    print("=" * 50)


if __name__ == "__main__":
    main()
