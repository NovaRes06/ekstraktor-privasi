"""
src/rag/vectorstore.py — simpan dan cari chunk berdasarkan kemiripan makna (vektor).

ChromaDB dipakai sebagai "basis data vektor" lokal -- datanya tersimpan di folder
chroma_db/ (dibuat otomatis), tidak perlu server terpisah, cocok untuk proyek kelas.
"""

from pathlib import Path

import chromadb

from src.rag.chunker import Chunk
from src.rag.embedder import embed_query, embed_texts

DB_PATH = Path("chroma_db")
COLLECTION_NAME = "dokumen_rujukan"

# Ambang batas jarak: chunk dengan jarak di atas ini dianggap TIDAK relevan dan
# dibuang sebelum dikirim ke model. Nilai 0,65 ditentukan dari observasi kasus uji
# (lihat logs/lapisan3_rag_cases.md): chunk yang benar-benar relevan selalu di
# bawah 0,56; chunk yang terbukti tidak relevan selalu di atas 0,69. Ini bukan
# angka ajaib universal -- sesuaikan lagi kalau corpus dokumen bertambah banyak
# dan pola jaraknya berubah.
MAX_RELEVANT_DISTANCE = 0.65


def get_collection():
    client = chromadb.PersistentClient(path=str(DB_PATH))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def index_chunks(chunks: list[Chunk]) -> int:
    """
    Simpan daftar chunk ke ChromaDB, lengkap dengan embedding dan metadata asalnya.
    Mengembalikan jumlah chunk yang berhasil disimpan.
    """
    if not chunks:
        return 0

    collection = get_collection()

    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    ids = [f"{c.source_doc}::chunk{c.chunk_index}" for c in chunks]
    metadatas = [{"source_doc": c.source_doc, "chunk_index": c.chunk_index} for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return len(chunks)


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Cari k chunk yang paling relevan secara makna dengan query.
    Mengembalikan list dict: {text, source_doc, chunk_index, jarak}.

    'jarak' (distance) makin KECIL berarti makin MIRIP -- ini sering jadi sumber
    kebingungan, karena intuisinya biasanya 'semakin besar skor = semakin cocok'.
    """
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count()),
    )

    retrieved = []
    for i in range(len(results["ids"][0])):
        jarak = results["distances"][0][i]

        # Buang chunk yang terlalu jauh -- ini jaring pengaman TAMBAHAN, bukan
        # pengganti instruksi 'jangan mengarang' di system prompt. Dua lapis
        # pertahanan lebih aman daripada mengandalkan satu saja (lihat Kasus 3
        # di logs/lapisan3_rag_cases.md, tempat kelemahan ini ditemukan).
        if jarak > MAX_RELEVANT_DISTANCE:
            continue

        retrieved.append({
            "text": results["documents"][0][i],
            "source_doc": results["metadatas"][0][i]["source_doc"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "jarak": jarak,
        })

    return retrieved


def collection_stats() -> dict:
    """Info ringkas isi index, berguna untuk debugging."""
    collection = get_collection()
    return {"jumlah_chunk_tersimpan": collection.count()}
