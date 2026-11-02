# Privia — Ekstraktor & Penjawab Kebijakan Privasi

Privia membaca kebijakan privasi dompet digital berbahasa Indonesia, mengeluarkan
sembilan aspek kepatuhan data dalam bentuk JSON tetap **beserta kutipan buktinya**,
menjawab pertanyaan berdasarkan dokumen rujukan sendiri (RAG), dan menjalankan
tugas pembandingan banyak langkah lewat agen dengan batas langkah serta persetujuan
manusia.

Proyek ini dikerjakan untuk Kapita Selekta AI Engineering (Ganjil 2026/2027),
mengikuti lima lapisan modul: LLM dasar → ekstraksi terstruktur → grounding (RAG)
→ agentic → kematangan (evaluasi, risiko, etika).

---

## 1. Persoalan dan pengguna

**Siapa yang mengalaminya.** Pengguna dompet digital yang ingin tahu bagaimana
datanya dipakai, tetapi kebijakan privasi ditulis panjang dan berbahasa hukum;
mereka menekan "setuju" tanpa membacanya (*informed consent* yang tidak benar-benar
informed). Tim kepatuhan/legal internal juga perlu memeriksa banyak kebijakan
sekaligus dan tidak sanggup membacanya manual satu per satu.

**Yang ditawarkan.** Bukan putusan "patuh/tidak patuh" — itu tetap keputusan
manusia. Privia hanya mengekstrak apa yang tertulis, menunjukkan di mana letaknya,
dan menolak menjawab kalau dokumen tidak memuatnya.

**Bukti keberhasilan.** Field hasil ekstraksi cocok dengan dokumen asli saat
diperiksa manual; field yang tidak ada dijawab "tidak disebutkan", bukan dikarang;
pertanyaan yang tidak terjawab dokumen dijawab "Tidak ada di dokumen."

## 2. Cara menjalankan

Prasyarat: Python 3.12, satu API key Gemini di `.env`.

```bash
pip install -r requirements.txt
echo "GEMINI_API_KEY=..." > .env      

python build_index.py                  # indeks 8 dokumen rujukan -> chroma_db/
uvicorn api:app --reload               
streamlit run app.py                   # antarmuka
```

Perintah lain:

```bash
python run_agent.py "Bandingkan masa retensi OVO dan ShopeePay."   # agen banyak langkah
python -m src.eval.jalankan_set_uji                                # evaluasi set uji
python uji_serangan.py                                             # 6 uji serangan
python -m pytest -q                                                # 97 uji otomatis
```

## 3. Isi repositori

| Bagian | Berkas |
|---|---|
| Produk | `app.py` (Streamlit), `api.py` (FastAPI), `run_agent.py` (agen) |
| Ekstraksi | `src/extraction/extractor.py`, `instruksi/v1.md`, `instruksi/v2.md` |
| RAG | `src/rag/{chunker,embedder,vectorstore}.py`, `build_index.py` |
| Agent | `src/agent/{agent,tools}.py`, `instruksi/agent-v1.md` |
| Guardrails | `src/guardrails/{input_filter,output_check}.py` |
| Evaluasi | `set-uji/`, `src/eval/jalankan_set_uji.py`, `logs/hasil-evaluasi-*.json` |
| Dokumen rujukan | `data/raw/` (8 dokumen) + `data/raw/SUMBER.md` (asal-usulnya) |
| Laporan | `laporan-evaluasi.md`, `kajian-risiko.md`, `guardrails.md`, `refleksi.md` |
| Rancangan | `rancangan-sistem.md`, `rancangan-rag.md`, `analisis-workflow-vs-agen.md` |
| Catatan | `docs/catatan-proses.md` (Minggu 1–16, format Lampiran C), `catatan-proses/`, `catatan-pemakaian.md`, `instruksi/CATATAN.md` |

## 4. Hasil yang bisa diperiksa sendiri

Semua angka di bawah berasal dari berkas di repo ini, bukan dari ingatan.

| Ukuran | Angka | Berkas bukti |
|---|---|---|
| Uji otomatis | 97 lulus | `python -m pytest -q` |
| Set uji (kasus flash, 17 kasus) | lulus seluruh kriteria 14/17 | `logs/hasil-evaluasi-v1.json` |
| Kriteria "format valid" | 17/17 | idem |
| Kasus yang harus ditolak | 5/5 menolak dengan benar | idem |
| Uji serangan | 4 ditolak, 0 tembus, 2 tidak teruji (kuota) | `logs/uji-serangan.json` |
| Agen berhasil menyelesaikan tugas pembandingan | 3–4 langkah, jawaban menyebut dokumen | `logs/hasil-evaluasi-lite.json`, `logs/agent_trace/` |
| Biaya per permintaan khas (ekstraksi) | $0,00358 (≈Rp 59) | `laporan-evaluasi.md` §7 |

Dua kasus memang **gagal** dan dilaporkan sebagai gagal: U03 (kutipan bukti
disusun dari beberapa butir yang tidak berurutan sehingga tidak bisa diverifikasi
apa adanya) dan U07 (bagian pengungkapan ShopeePay tidak terambil sehingga sistem
menolak padahal dokumen memuatnya). Keduanya dibahas di `laporan-evaluasi.md` §6.

## 5. Batas penggunaan

Privia **tidak boleh** dipakai untuk:

- memutuskan patuh/tidak patuh suatu kebijakan terhadap UU PDP — sistem ini sengaja
  menolak memberi putusan itu (lihat `kajian-risiko.md` §7);
- memberi nasihat hukum, atau menjadi satu-satunya dasar keputusan hukum;
- mengekstrak dokumen yang memuat data pribadi orang sungguhan (NIK, nomor kartu,
  nomor telepon) — permintaan seperti itu ditolak guardrails lapis 1;
- membaca dokumen di luar folder `data/raw/` (batas akses tool dipasang di kode).

Batas yang diketahui masih ada (mis. serangan bertahap antar-pesan belum teruji)
dicatat di `guardrails.md` §6, bukan disembunyikan.

## 6. Keterbatasan yang perlu dibaca sebelum percaya

- Set uji hanya 17–18 kasus dan disusun sendiri oleh pembuat sistem; ia mengukur
  perilaku pada kasus yang saya pikirkan, bukan seluruh variasi kebijakan di dunia.
- Penilaian otomatis hanya memeriksa hal yang bisa diperiksa mesin; kriteria
  "tidak ada pernyataan tambahan tanpa dasar" pada jawaban bebas tidak dinilai
  otomatis, dan itu dinyatakan terbuka di laporan.
- Jalur `/ask` (RAG) masih bisa menolak padahal dokumen memuat jawabannya
  (kasus U07). Ini diukur, bukan diduga.
- Model default `gemini-3.6-flash`; kuota gratisnya 20 permintaan/hari, sehingga
  sebagian pengujian selesai pada hari berbeda dan tercatat begitu.
