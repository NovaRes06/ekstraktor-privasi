"""
api.py — Lapisan 2 lanjutan: bungkus logika ekstraksi jadi API.

Cara jalankan:
    uvicorn api:app --reload

Lalu buka http://localhost:8000/docs untuk coba langsung lewat browser
(FastAPI otomatis bikin halaman uji coba, gak perlu Postman).
"""

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.extraction.extractor import extract_fields

app = FastAPI(title="Ekstraktor Kebijakan Privasi")


class ExtractTextRequest(BaseModel):
    text: str


class ExtractUrlRequest(BaseModel):
    url: str


@app.post("/extract")
def extract_from_text(payload: ExtractTextRequest):
    """Ekstrak 9 field dari teks kebijakan privasi yang dikirim langsung."""
    try:
        result = extract_fields(payload.text)
    except ValueError as e:
        # Ini kasus gagal parsing JSON — catat manual ke logs/failed_cases.md
        raise HTTPException(status_code=422, detail=str(e))
    return result


@app.post("/fetch-url")
def fetch_document_from_url(payload: ExtractUrlRequest):
    """
    Tool eksternal pertama: ambil teks kebijakan privasi langsung dari URL.
    Membersihkan HTML jadi teks polos sebelum dikembalikan.
    """
    try:
        response = requests.get(payload.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil URL: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Buang script/style supaya teksnya bersih
    for tag in soup(["script", "style"]):
        tag.decompose()

    clean_text = soup.get_text(separator="\n", strip=True)

    return {"url": payload.url, "text": clean_text[:20000]}  # batasi panjang untuk jaga-jaga


@app.post("/extract-from-url")
def extract_from_url(payload: ExtractUrlRequest):
    """
    Endpoint gabungan: ambil dokumen dari URL, langsung ekstrak.
    Ini yang paling praktis dipanggil dari frontend nanti.
    """
    fetched = fetch_document_from_url(payload)
    try:
        result = extract_fields(fetched["text"])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    result["source_url"] = payload.url
    return result


@app.get("/health")
def health_check():
    """Cek sederhana apakah API hidup."""
    return {"status": "ok"}
