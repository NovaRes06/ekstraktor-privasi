# Privia — Ekstraktor Kebijakan Privasi

Privia membaca kebijakan privasi dompet digital berbahasa Indonesia dan mengeluarkan
sembilan aspek kepatuhan data dalam bentuk JSON tetap. Tujuannya bukan memutuskan
"patuh/tidak patuh" — itu tetap keputusan manusia — melainkan menunjukkan apa yang
tertulis di dokumen dan menolak menjawab kalau dokumen tidak memuatnya.

Proyek ini dikerjakan untuk Kapita Selekta AI Engineering (Ganjil 2026/2027), mengikuti
lima lapisan modul: LLM dasar → ekstraksi terstruktur → grounding (RAG) → agentic →
kematangan (evaluasi, risiko, etika).

---

## 1. Persoalan dan pengguna

**Siapa yang mengalaminya.** Pengguna dompet digital yang ingin tahu bagaimana datanya
dipakai, tetapi kebijakan privasi ditulis panjang dan berbahasa hukum; mereka menekan
"setuju" tanpa membacanya (*informed consent* yang tidak benar-benar informed). Tim
kepatuhan/legal internal juga perlu memeriksa banyak kebijakan sekaligus.

**Yang ditawarkan.** Ekstraksi sembilan aspek kepatuhan dari teks kebijakan, dengan nilai
`"tidak disebutkan"` untuk hal yang memang tidak dibahas dokumen, sehingga "tidak ada di
dokumen" tidak tertukar dengan "sistem gagal".

**Bukti keberhasilan.** Field hasil ekstraksi cocok dengan dokumen asli saat diperiksa
manual; field yang tidak ada dijawab `"tidak disebutkan"`, bukan dikarang; pertanyaan
yang tidak terjawab dokumen dijawab "Tidak ada di dokumen."

---

## 2. Status per lapisan

| Lapisan | Isi | Status di working tree |
|---|---|---|
| 1 Fondasi | Catatan proses Minggu 1–13, perbandingan model, catatan biaya, harness BREAK Minggu 1 | **Ada** |
| 2 Kendali | Ekstraksi 9 field + kutipan bukti, prompt v1/v2 + mode ringkas, API | **Ada** — 18 key schema, retry, pemetaan galat |
| 3 Grounding | Chunker, embedding, ChromaDB, `build_index.py`, `/ask`, 8 dokumen rujukan | **Ada** — ambang kemiripan 0,65 |
| 4 Agentic | 4 tool, batas langkah, state eksternal, trace, satu titik persetujuan manusia | **Ada** |
| 5 Kematangan | Guardrails input/output, set uji 18 kasus, harness evaluasi, uji serangan, kajian risiko | **Ada** |

---

## 3. Cara menjalankan

Prasyarat: Python 3.12 dan satu API key Gemini di `.env`.

```bash
pip install -r requirements.txt
echo "GEMINI_API_KEY=..." > .env      # jangan pernah di-commit, sudah ditutup .gitignore

python build_index.py                 # indeks 8 dokumen rujukan -> chroma_db/
uvicorn api:app --reload              # API di http://127.0.0.1:8000/docs
streamlit run app.py                  # antarmuka
```

Endpoint yang tersedia: `GET /health`, `POST /extract`, `POST /fetch-url`,
`POST /extract-from-url`, `POST /ask`, `POST /agent`. URL yang mengarah ke host
internal/IP privat ditolak `403` sebelum diambil (proteksi SSRF).

Perintah lain:

```bash
python run_agent.py "Bandingkan masa retensi OVO dan ShopeePay."
python -m src.eval.jalankan_set_uji           # evaluasi set uji (memakai kuota)
python uji_serangan.py                        # 6 uji serangan (memakai kuota)
python uji_break_minggu1.py                   # 4 percobaan BREAK Minggu 1
```

### Uji otomatis dan lint

```bash
python -m pytest -q      # 97 passed
python -m ruff check     # All checks passed!
```

Keduanya dijalankan pada 14 November 2026 di working tree ini, tanpa memanggil API
(tes memakai tiruan/`monkeypatch`), jadi tidak memotong kuota.

---

## 4. Isi repositori

| Bagian | Berkas |
|---|---|
| API | `api.py` — 6 endpoint, pemetaan galat 429/422/502/403 |
| Antarmuka | `app.py` (Streamlit), `.streamlit/config.toml`, `assets/Privia.png` |
| Ekstraksi | `src/extraction/extractor.py` (18 key, mode ringkas), `instruksi/{v1,v2,agent-v1}.md`, `instruksi/CATATAN.md` |
| RAG | `src/rag/{chunker,embedder,vectorstore}.py`, `build_index.py` |
| Agent | `src/agent/{agent,tools}.py`, `run_agent.py` |
| Guardrails | `src/guardrails/{input_filter,output_check}.py` |
| Evaluasi | `set-uji/kasus.jsonl` (18 kasus), `src/eval/jalankan_set_uji.py`, `uji_serangan.py`, `logs/` |
| Dokumen rujukan | `data/raw/` — 7 kebijakan dompet digital + ringkasan UU PDP + `SUMBER.md` |
| Uji | `tests/` — 6 berkas, 97 uji lulus |
| Laporan | `laporan-evaluasi.md`, `kajian-risiko.md`, `guardrails.md`, `refleksi.md`, `lembar-tema.md` |
| Rancangan | `rancangan-sistem.md`, `rancangan-rag.md`, `analisis-workflow-vs-agen.md` |
| Catatan | `docs/catatan-proses.md` (Minggu 1–13, format Lampiran C), `catatan-pemakaian.md` |

---

## 5. Hasil yang bisa diperiksa sendiri

Semua angka di bawah berasal dari berkas di repo ini, bukan dari ingatan.

| Ukuran | Angka | Berkas bukti |
|---|---|---|
| Uji otomatis | **97 lulus**, 0 gagal | `python -m pytest -q` (14 Nov 2026) |
| Lint | **bersih** | `python -m ruff check` (14 Nov 2026) |
| Endpoint hidup | `GET /health` → 200, `/docs` → 200 | diuji live 14 Nov 2026 (port 8099) |
| Evaluasi set uji (v1) | **14 dari 17** kasus lulus semua kriteria | `logs/hasil-evaluasi-v1.json` |
| Kriteria 1–5 | 16/17, 15/17, 11/11, 17/17, 5/5 | `logs/hasil-evaluasi-v1.json` |
| Kasus gagal | 3 (U01, U03, U07) dan alasannya | `logs/failed_cases.md` |
| Uji serangan | 6 dijalankan: **4 ditolak, 0 tembus, 2 belum teruji** | `logs/uji-serangan.json` |
| BREAK Minggu 1 | 4 percobaan, 6 jawaban, prediksi ditulis lebih dulu | `logs/break-minggu1.json` |
| Biaya setara ekstraksi | $0,003581 per permintaan (aktual Rp 0, free tier) | `catatan-pemakaian.md` |
| Biaya setara agen | $0,007739 untuk 4 langkah; proyeksi 100 pengguna ≈ $7,16/bulan | `catatan-pemakaian.md` |

---

## 6. Batas penggunaan dan keterbatasan

Privia **tidak boleh** dipakai untuk:

- memutuskan patuh/tidak patuh suatu kebijakan terhadap UU PDP;
- memberi nasihat hukum, atau menjadi satu-satunya dasar keputusan hukum;
- memproses data pribadi orang sungguhan (NIK, nomor kartu, nomor telepon).

Keterbatasan yang harus dibaca sebelum percaya:

- **Dua uji serangan belum teruji** (#5 injeksi di dalam dokumen, #6 kebocoran lintas
  pengguna) karena kuota `gemini-3.6-flash` habis (HTTP 429). Statusnya `TIDAK TERUJI`,
  bukan "lulus".
- **Retrieval masih bisa meleset.** U07 adalah contoh nyata: bagian yang memuat jawaban
  tidak terambil sehingga sistem menolak padahal jawabannya ada.
- **Teks dipotong 20.000 karakter** di `/fetch-url`, sehingga dokumen panjang
  (mis. kebijakan OVO ±85 ribu karakter) hanya teranalisis sebagian.
- **Kuota gratis 20 permintaan/hari** per model; evaluasi memakai cache
  per-(kasus, model, masukan) agar tidak mengulang permintaan.
- **Evaluasi baru 17 kasus** dengan satu model utama; angka akurasi di luar itu belum
  bisa diklaim.

---

## 7. Rencana berikutnya

Urutan usahanya: (1) commit pemulihan berkas, (2) menguji ulang serangan #5 dan #6 saat
kuota tersedia, (3) memperbaiki retrieval U07, (4) memperbarui `laporan-evaluasi.md` dan
`catatan-pemakaian.md` dengan tanggal pemulihan 14 November 2026.
