"""
api.py — Lapisan 2 lanjutan: bungkus logika ekstraksi jadi API.

Cara jalankan:
    uvicorn api:app --reload

Lalu buka http://localhost:8000/docs untuk coba langsung lewat browser
(FastAPI otomatis bikin halaman uji coba, gak perlu Postman).
"""

import ipaddress
import os
import socket
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import errors as genai_errors
from pydantic import AnyUrl, BaseModel, Field

from src.extraction.extractor import extract_fields
from src.guardrails.input_filter import InputDitolak, saring_input
from src.guardrails.output_check import periksa_ekstraksi, periksa_jawaban
from src.rag.vectorstore import retrieve

load_dotenv()
rag_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
RAG_MODEL = "gemini-3.6-flash"
RAG_SYSTEM_PROMPT_PATH = Path("prompts/system_prompt_rag_v1.md")

app = FastAPI(title="Ekstraktor Kebijakan Privasi")


class ExtractTextRequest(BaseModel):
    text: str
    # Mode output (ketentuan lingkup: K genap wajib punya mode ringkas).
    # "ringkas" = proyeksi 4 field dari hasil penuh yang sama, bukan panggilan model baru.
    mode: Literal["penuh", "ringkas"] = "penuh"


class ExtractUrlRequest(BaseModel):
    # AnyUrl menolak 'bukan-url' di TAHAP VALIDASI (HTTP 422), bukan baru gagal
    # di tengah jalan saat requests.get dipanggil (yang dulu balas 400).
    url: AnyUrl
    mode: Literal["penuh", "ringkas"] = "penuh"


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    # k >= 1 wajib: n_results = 0 bikin ChromaDB menolak query.
    k: int = Field(default=5, ge=1, le=50)  # jumlah chunk yang diambil, bisa diubah per-request


class AgentRequest(BaseModel):
    """Tugas untuk agen banyak langkah (Lapisan 4)."""

    tugas: str = Field(default="", min_length=0)
    task_id: str | None = None  # diisi untuk melanjutkan tugas yang berhenti
    izin_simpan: bool = False  # persetujuan manusia untuk tool simpan_laporan
    max_langkah: int = Field(default=8, ge=1, le=20)


def _galat_model(exc: Exception, konteks: str) -> HTTPException:
    """
    Terjemahkan error Google GenAI jadi HTTP yang punya arti.

    Tanpa ini, ServerError (mis. 503 saat Gemini lagi ramai) lolos mentah dan
    FastAPI membalas 500 'Internal Server Error' tanpa JSON `detail`, sehingga
    app.py tidak bisa menampilkan sebabnya ke pengguna. Hanya dipakai untuk
    galat API-nya sendiri -- galat pemrograman tetap dibiarkan jadi 500 supaya
    tidak ketutup rapat.
    """
    code = getattr(exc, "code", None)

    if isinstance(exc, genai_errors.ClientError) and code == 429:
        return HTTPException(
            status_code=429,
            detail=f"{konteks}: kelebihan kuota Gemini (HTTP 429). Coba lagi beberapa saat lagi. | {exc}",
            headers={"Retry-After": "20"},
        )
    if isinstance(exc, genai_errors.ClientError) and code == 404:
        return HTTPException(
            status_code=502,
            detail=f"{konteks}: model tidak tersedia untuk akun ini (HTTP 404). "
                   f"Ganti nama model di berkas sumber. | {exc}",
        )
    if isinstance(exc, genai_errors.ClientError) and code in (401, 403):
        return HTTPException(
            status_code=502,
            detail=f"{konteks}: GEMINI_API_KEY ditolak (HTTP {code}). Periksa berkas .env. | {exc}",
        )
    if isinstance(exc, genai_errors.ClientError):
        return HTTPException(
            status_code=422,
            detail=f"{konteks}: permintaan ditolak Gemini (HTTP {code}). | {exc}",
        )
    if isinstance(exc, genai_errors.ServerError):
        return HTTPException(
            status_code=502,
            detail=f"{konteks}: Gemini sedang bermasalah di sisi mereka (HTTP {code}). "
                   f"Ini biasanya sementara -- coba lagi. | {exc}",
        )
    if isinstance(exc, genai_errors.APIError):
        return HTTPException(
            status_code=502,
            detail=f"{konteks}: galat API Gemini (HTTP {code}). | {exc}",
        )
    if isinstance(exc, (requests.RequestException, TimeoutError, OSError)):
        return HTTPException(
            status_code=502,
            detail=f"{konteks}: gagal menghubungi Gemini. Periksa koneksi. | {type(exc).__name__}: {exc}",
        )
    # Sengaja TIDAK ditangkap di sini: kalau sampai ke ini berarti bug di kode kita,
    # dan menguburnya jadi 502 justru menyembunyikan masalah.
    raise exc


@app.post("/extract")
def extract_from_text(payload: ExtractTextRequest):
    """Ekstrak 9 field dari teks kebijakan privasi yang dikirim langsung."""
    try:
        # Lapis 1: input disaring sebelum dikirim ke penyedia model. Data pribadi
        # orang sungguhan DITOLAK di sini, bukan sekadar diharapkan tidak ikut.
        saring_input(payload.text, untuk="dokumen", tolak_data_pribadi=True)
        result = extract_fields(payload.text, mode=payload.mode)
    except InputDitolak as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except genai_errors.APIError as e:
        raise _galat_model(e, "Ekstraksi gagal") from e
    except ValueError as e:
        # Ini kasus gagal parsing JSON — catat manual ke logs/failed_cases.md
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Lapis 4: bukti pada hasil dicek terhadap dokumen asli (bukan hanya bentuk schema).
    result["guardrail"] = periksa_ekstraksi(result.get("fields", {}), payload.text)
    return result


@app.post("/fetch-url")
def fetch_document_from_url(payload: ExtractUrlRequest):
    """
    Tool eksternal pertama: ambil teks kebijakan privasi langsung dari URL.
    Membersihkan HTML jadi teks polos sebelum dikembalikan.

    Batas aksen (lihat komentar di atas): hanya halaman PUBLIK. Permintaan ke
    host internal atau IP privat ditolak dengan HTTP 403, sebelum Requests.get
    dipanggil sama sekali.
    """
    _tolak_host_internal(str(payload.url))

    try:
        response = requests.get(str(payload.url), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil URL: {e}") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Buang script/style supaya teksnya bersih
    for tag in soup(["script", "style"]):
        tag.decompose()

    clean_text = soup.get_text(separator="\n", strip=True)

    return {"url": str(payload.url), "text": clean_text[:20000]}  # batasi panjang untuk jaga-jaga


@app.post("/extract-from-url")
def extract_from_url(payload: ExtractUrlRequest):
    """
    Endpoint gabungan: ambil dokumen dari URL, langsung ekstrak.
    Ini yang paling praktis dipanggil dari frontend nanti.
    """
    fetched = fetch_document_from_url(payload)
    try:
        saring_input(fetched["text"], untuk="dokumen", tolak_data_pribadi=True)
        result = extract_fields(fetched["text"], mode=payload.mode)
    except InputDitolak as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except genai_errors.APIError as e:
        raise _galat_model(e, "Ekstraksi dari URL gagal") from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    result["source_url"] = str(payload.url)
    return result


@app.post("/ask")
def ask_rag(payload: AskRequest):
    """
    Lapisan 3: jawab pertanyaan berdasarkan dokumen yang sudah di-index
    (lihat build_index.py). Jawaban WAJIB menyertakan chunk sumber yang dipakai.

    Index harus sudah dibangun dulu dengan: python build_index.py
    """
    from src.rag.vectorstore import collection_stats

    # Lapis 1: pertanyaan disaring dulu (injection ditolak, data pribadi ditolak).
    try:
        saring_input(payload.question, untuk="pertanyaan", tolak_injeksi=True, tolak_data_pribadi=True)
    except InputDitolak as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if collection_stats()["jumlah_chunk_tersimpan"] == 0:
        return {
            "answer": "Index belum berisi dokumen apa pun. Jalankan 'python build_index.py' dulu.",
            "sources": [],
        }

    try:
        retrieved_chunks = retrieve(payload.question, k=payload.k)
    except genai_errors.APIError as e:
        raise _galat_model(e, "Pencarian sumber gagal") from e

    if not retrieved_chunks:
        # Semua chunk yang ditemukan terlalu jauh (di atas MAX_RELEVANT_DISTANCE) --
        # langsung jawab tanpa panggil model, hemat biaya DAN tidak bergantung pada
        # kedisiplinan model (lihat logs/lapisan3_rag_cases.md, Kasus 3).
        return {
            "answer": "Tidak ada di dokumen.",
            "sources": [],
            "catatan": (
                "Tidak ada chunk yang cukup relevan ditemukan "
                "(di atas ambang batas jarak) -- model tidak dipanggil."
            ),
        }

    # Susun konteks bernomor, supaya model bisa merujuk balik [1], [2], dst.
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[{i}] (sumber: {chunk['source_doc']}, bagian {chunk['chunk_index']})\n{chunk['text']}"
        )
    context_text = "\n\n".join(context_blocks)

    system_prompt = RAG_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    try:
        response = rag_client.models.generate_content(
            model=RAG_MODEL,
            contents=f"KONTEKS:\n{context_text}\n\nPERTANYAAN: {payload.question}",
            config={"system_instruction": system_prompt},
        )
    except genai_errors.APIError as e:
        raise _galat_model(e, "Penyusunan jawaban gagal") from e

    answer = (response.text or "").strip()
    if not answer:
        # response.text bisa None kalau penyaringan konten menghalangi hasil.
        # Dikirim balik apa adanya, app.py akan menampilkan literal "None".
        return {
            "answer": "Model tidak mengembalikan jawaban (kemungkinan besar diblokir penyaringan konten).",
            "sources": retrieved_chunks,
            "catatan": "Respons model kosong -- tidak ada teks yang boleh ditampilkan.",
        }

    # Lapis 4: cek kebocoran prompt, putusan kepatuhan, dan rujukan sebelum ditampilkan.
    masalah = periksa_jawaban(answer, jumlah_sumber=len(retrieved_chunks), system_prompt=system_prompt)
    if any("system prompt" in m for m in masalah):
        return {
            "answer": "Jawaban diblokir guardrails: output memuat isi instruksi sistem.",
            "sources": [],
            "guardrail": masalah,
        }

    return {
        "answer": answer,
        "sources": retrieved_chunks,
        "guardrail": masalah,
    }


@app.get("/health")
def health_check():
    """Cek sederhana apakah API hidup."""
    return {"status": "ok"}


@app.post("/agent")
def jalankan_agen(payload: AgentRequest):
    """
    Lapisan 4: jalankan (atau lanjutkan) agen banyak langkah.

    Tanpa `izin_simpan`, agen berhenti SEBELUM menulis berkas dan membalas
    status "butuh_persetujuan" berisi apa persisnya yang akan disimpan.
    """
    from src.agent.agent import AgentGagal, jalankan_agent, lanjutkan_agent

    try:
        if payload.task_id:
            return lanjutkan_agent(payload.task_id, izin_simpan=payload.izin_simpan)
        if not payload.tugas.strip():
            raise HTTPException(status_code=422, detail="Isi 'tugas' atau 'task_id'.")
        return jalankan_agent(
            payload.tugas, izin_simpan=payload.izin_simpan, max_langkah=payload.max_langkah
        )
    except InputDitolak as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except AgentGagal as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except genai_errors.APIError as e:
        raise _galat_model(e, "Agen gagal berjalan") from e


# BATAS AKSES TOOL /fetch-url (ketentuan modul Minggu 6)
#
# Tool ini BOLEH: mengunduh halaman PUBLIK dari internet (http/https) untuk
# diekstrak kebijakan privasinya.
# Tool ini TIDAK BOLEH: menyentuh sisi internal:
#   - host localhost/*.local/*.internal/*.lan/*.home
#   - alamat IP loopback/private/link-local (127.x, 10.x, 192.168.x, 169.254.x, ...)
#   - host nama yang resolve ke alamat tidak-publik (penyamaran via DNS)
#
# Alasannya nyata, bukan formalitas: endpoint ini menerima URL apa pun dari
# pengguna. Tanpa proteksi, "http://localhost:8000/health" bisa jadi pintu
# memindai jaringan dari dalam server (SSRF) -- dan karena nama host diperiksa
# sampai ke alamat IP hasil resolve-nya, "resep-privasi.internal" yang
# resolve ke 10.x juga tertangkap (cek nama host saja tidak cukup).

def _tolak_host_internal(url: str) -> None:
    """
    Tolak URL yang mengarah ke host internal/IP privat dengan HTTP 403.
    Bagian dari batas akses tool /fetch-url -- bukan pengaman 'nice to have':
    endpoint ini menerima URL dari pengguna, jadi tanpa proteksi ini ia bisa
    jadi alat untuk memindai jaringan dari dalam server (SSRF).
    """
    host = urlparse(url).hostname or ""
    if not host:
        raise HTTPException(status_code=400, detail="URL tidak punya nama host.")

    host_bertanda = {
        "localhost", "host.docker.internal", "metadata.google.internal",
    }
    # *.local (mDNS) dkk -- semuanya tidak mengarah ke internet publik.
    akhiran_internal = (".local", ".internal", ".lan", ".home")
    if host.lower() in host_bertanda or host.lower().endswith(akhiran_internal):
        raise HTTPException(
            status_code=403,
            detail=f"Host '{host}' adalah host internal -- tool ini hanya boleh mengambil halaman publik.",
        )

    # Bila host berupa IP langsung (mis. http://10.0.0.5/), tolok bila privat.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    else:
        if not ip.is_global:
            raise HTTPException(
                status_code=403,
                detail=f"Alamat IP {host} tidak publik -- tool ini hanya boleh mengambil halaman publik.",
            )

    # Host "nama" (mis. intranet.internal): resolve dulu -- bila hasilnya IP
    # privat/loopback, tolak. Ini menghalangi penyamaran via DNS.
    try:
        info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return  # host tidak dikenal -- biarkan requests.get yang gagal normal
    for _keluarga, _tipe, _proto, _canon, sa in info:
        ip_resolv = ipaddress.ip_address(sa[0])
        if not ip_resolv.is_global:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Host '{host}' resolve ke alamat tidak publik ({ip_resolv}) "
                    "-- tool ini hanya boleh mengambil halaman publik."
                ),
            )
