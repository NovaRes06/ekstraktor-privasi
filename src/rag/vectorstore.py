"""
src/rag/vectorstore.py — simpan dan cari chunk berdasarkan kemiripan makna (vektor).

ChromaDB dipakai sebagai "basis data vektor" lokal -- datanya tersimpan di folder
chroma_db/ (dibuat otomatis), tidak perlu server terpisah, cocok untuk proyek kelas.
"""

import re
from itertools import pairwise
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

# --- fusi peringkat: jarak makna + kecocokan kata ----------------------------
#
# Jarak embedding saja tidak cukup memilih chunk yang tepat. Pada kasus U07
# ("Bagaimana ShopeePay membagikan data pengguna ke pihak ketiga?") chunk yang
# benar-benar memuat pasal 9 hanya berjarak 0,5031, sedangkan enam chunk umum
# ShopeePay berjarak 0,4661-0,4992 -- selisihnya 0,004-0,037, terlalu tipis
# untuk dipercaya sebagai sinyal. Akibatnya sistem menolak padahal dokumennya
# memuat jawaban.
#
# Karena itu peringkat akhir memakai dua koreksi yang bisa dijelaskan:
#   1. Bila pertanyaan menyebut nama dokumen yang ada di korpus (mis. "ShopeePay"
#      pada pertanyaan di atas), chunk dari dokumen itu didahulukan.
#   2. Bila chunk memuat frasa persis dari pertanyaan ("pihak ketiga"),
#      peringkatnya naik. Frasa lebih kuat daripada kata tunggal karena
#      "pihak" dan "ketiga" terpisah muncul di banyak dokumen.
#
# Ambang MAX_RELEVANT_DISTANCE tetap diukur pada jarak embedding asli, jadi
# koreksi ini hanya MENYUSUN ULANG chunk yang sudah lolos ambang -- tidak pernah
# meloloskan chunk yang jauh. Bobot dipilih dari pengukuran lima kasus RAG
# (U07, P03, B04, T02, T03); lihat logs/lapisan3_rag_cases.md.
DOCUMENT_BONUS = 0.20
PHRASE_BONUS = 0.05
CANDIDATE_MINIMUM = 20
CANDIDATE_PER_K = 3

# Kata yang terlalu umum untuk dijadikan penanda dokumen atau frasa kunci.
KATA_UMUM = frozenset({
    "bagaimana", "apa", "apakah", "kapan", "siapa", "mengapa", "berapa",
    "ke", "di", "dan", "atau", "yang", "untuk", "dari", "dengan", "pada",
    "itu", "ini", "adalah", "akan", "dapat", "bisa", "saja", "saya", "anda",
    "kami", "kita", "menurut", "adakah", "dalam", "oleh", "sebagai",
})

_TOKEN = re.compile(r"[a-z0-9]+")


def _document_name(source_doc: str) -> str:
    """'kebijakan-shopeepay.txt' -> 'shopeepay'; 'ringkasan-pasal-uu-pdp.md' -> 'ringkasan pasal uu pdp'."""
    nama = re.sub(r"^(kebijakan-|ringkasan-pasal-)", "", source_doc)
    nama = re.sub(r"\.(txt|md)$", "", nama)
    return nama.replace("-", " ").lower()


def _query_terms(query: str) -> list[str]:
    return [w for w in _TOKEN.findall(query.lower()) if w not in KATA_UMUM and len(w) > 2]


def _query_phrases(query: str) -> list[str]:
    """Frasa dua kata berurutan dari pertanyaan, tanpa kata umum di dalamnya."""
    kata = _TOKEN.findall(query.lower())
    return [
        f"{a} {b}"
        for a, b in pairwise(kata)
        if a not in KATA_UMUM and b not in KATA_UMUM
    ]


def _ranking_bonus(query: str, teks_chunk: str, source_doc: str) -> float:
    """Pengurangan jarak (makin besar = makin diutamakan) dari sinyal kata."""
    bonus = 0.0

    nama_dokumen = _document_name(source_doc)
    if any(istilah in nama_dokumen for istilah in _query_terms(query)):
        bonus += DOCUMENT_BONUS

    teks = teks_chunk.lower()
    frasa_cocok = sum(1 for frasa in _query_phrases(query) if frasa in teks)
    bonus += PHRASE_BONUS * min(frasa_cocok, 2)  # dua frasa sudah cukup meyakinkan

    return bonus


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
    Cari k chunk yang paling relevan dengan query.
    Mengembalikan list dict: {text, source_doc, chunk_index, jarak}.

    'jarak' (distance) makin KECIL berarti makin MIRIP -- ini sering jadi sumber
    kebingungan, karena intuisinya biasanya 'semakin besar skor = semakin cocok'.

    Peringkat akhir bukan jarak mentah, melainkan jarak dikurangi koreksi dari
    penyebutan nama dokumen dan frasa persis pertanyaan (lihat _ranking_bonus).
    Kandidat diambil lebih banyak daripada k supaya koreksi itu punya pilihan;
    ambang jarak tetap berlaku pada jarak embedding asli.
    """
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)

    jumlah_kandidat = min(
        max(k * CANDIDATE_PER_K, CANDIDATE_MINIMUM), collection.count()
    )
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=jumlah_kandidat,
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

        teks = results["documents"][0][i]
        source_doc = results["metadatas"][0][i]["source_doc"]
        retrieved.append({
            "text": teks,
            "source_doc": source_doc,
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "jarak": jarak,
            "_skor": jarak - _ranking_bonus(query, teks, source_doc),
        })

    retrieved.sort(key=lambda c: (c["_skor"], c["jarak"]))
    for chunk in retrieved:
        chunk.pop("_skor")

    return retrieved[:k]


def collection_stats() -> dict:
    """Info ringkas isi index, berguna untuk debugging."""
    collection = get_collection()
    return {"jumlah_chunk_tersimpan": collection.count()}
