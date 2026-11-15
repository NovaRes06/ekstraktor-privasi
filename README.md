# Privia — Ekstraktor Kebijakan Privasi

Privia membaca kebijakan privasi dompet digital berbahasa Indonesia dan mengeluarkan
sembilan aspek kepatuhan data dalam bentuk JSON tetap. Tujuannya bukan memutuskan
"patuh/tidak patuh" — itu tetap keputusan manusia — melainkan menunjukkan apa yang
tertulis di dokumen dan menolak menjawab kalau dokumen tidak memuatnya.

Proyek Kapita Selekta AI Engineering (Ganjil 2026/2027), kode peserta **K = 5**:
minimum 6 dokumen rujukan, 17 kasus uji, 3 tool. Yang tersedia 8 dokumen, 18 kasus,
4 tool.

**Status: progres Minggu 13.** Luaran Minggu 1–13 ada beserta buktinya. `laporan-evaluasi.md`,
`kajian-risiko.md`, dan `refleksi.md` masih **draf awal** untuk Minggu 14–16 dan belum
dikumpulkan.

## Menjalankan

Prasyarat: Python 3.12 dan satu API key Gemini di `.env` (tidak pernah di-commit).

```bash
pip install -r requirements.txt
echo "GEMINI_API_KEY=..." > .env
python build_index.py          # indeks 8 dokumen -> chroma_db/
uvicorn api:app --reload       # API di http://127.0.0.1:8000/docs
streamlit run app.py           # antarmuka
```

Endpoint: `GET /health`, `POST /extract`, `POST /fetch-url`, `POST /extract-from-url`,
`POST /ask`, `POST /agent`. URL ke host internal/IP privat ditolak `403` (proteksi SSRF).

Perintah lain: `python run_agent.py "<tugas>"`, `python -m src.eval.jalankan_set_uji`,
`python uji_serangan.py`, `python uji_break_minggu1.py`, `python buat_bukti.py`.

## Isi repositori

| Bagian | Berkas |
|---|---|
| API & antarmuka | `api.py`, `app.py`, `assets/Privia.png` |
| Ekstraksi | `src/extraction/extractor.py`, `instruksi/` (`v1.md`, `v2.md`, `rag-v1.md`, `agent-v1.md`) |
| RAG | `src/rag/`, `build_index.py`, `data/raw/` (8 dokumen + `SUMBER.md`) |
| Agent | `src/agent/`, `run_agent.py` |
| Guardrails | `src/guardrails/`, `guardrails.md` |
| Evaluasi | `set-uji/kasus.jsonl` (18 kasus), `src/eval/`, `uji_serangan.py`, `logs/` |
| Laporan & rancangan | `laporan-evaluasi.md`, `kajian-risiko.md`, `refleksi.md`, `rancangan-sistem.md`, `rancangan-rag.md`, `analisis-workflow-vs-agen.md`, `lembar-tema.md` |
| Catatan | `docs/catatan-proses.md` (Minggu 1–13, format Lampiran C), `catatan-pemakaian.md` |
| Bukti & peer review | `buat_bukti.py` + `bukti/` (13 paket zip), `peer-review/` (template) |
| Uji | `tests/` — 6 berkas, 97 uji |

## Hasil terverifikasi

| Ukuran | Angka | Bukti |
|---|---|---|
| Uji otomatis | **97 lulus**, 0 gagal | `python -m pytest -q` (14 Nov 2026) |
| Lint | **bersih** | `python -m ruff check` (14 Nov 2026) |
| Evaluasi set uji (v1) | **14 dari 17** kasus lulus semua kriteria | `logs/hasil-evaluasi-v1.json` |
| Kasus gagal | 3 (U01, U03, U07) + alasannya | `logs/failed_cases.md` |
| Uji serangan | 6 dijalankan: **4 ditolak, 0 tembus, 2 tidak teruji** | `logs/uji-serangan.json` |
| BREAK Minggu 1 | 4 percobaan, prediksi ditulis lebih dulu | `logs/break-minggu1.json` |
| Biaya | Rp 0 (free tier); setara $0,003581 per ekstraksi, $0,007739 per tugas agen 4 langkah | `catatan-pemakaian.md` |

## Batas dan keterbatasan

- Tidak boleh dipakai untuk memutuskan patuh/tidak patuh, memberi nasihat hukum, atau
  memproses data pribadi orang sungguhan.
- Serangan **#2 dan #5 belum teruji** (kuota `gemini-3.6-flash` habis, HTTP 429);
  statusnya `TIDAK TERUJI`, bukan "lulus".
- Retrieval masih bisa meleset: U07 menolak padahal jawabannya ada di dokumen.
- Teks dipotong 20.000 karakter di `/fetch-url`, sehingga dokumen panjang (OVO ±85 ribu
  karakter) hanya teranalisis sebagian.
- Kuota gratis 20 permintaan/hari per model; evaluasi memakai cache agar tidak mengulang.

## Berikutnya

1. Mengisi 4 lembar peer review (2 UTS + 2 Minggu 12) memakai template di `peer-review/`.
2. Menguji ulang serangan #2 dan #5 saat kuota tersedia.
3. Memperbaiki retrieval U07.

Rincian paket bukti dan kekurangannya: `bukti/README.md`. Rencana dan status per minggu:
`docs/catatan-proses.md`.
