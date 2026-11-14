# Laporan Progres (Draf) — Privia

> **Catatan 14 November 2026.** Berkas ini ditulis 9 November 2026, ketika kode
> Lapisan 3–5 tidak ada di working tree. Berkas-berkas itu sudah dipulihkan dari
> riwayat git pada 14 November 2026 (105 berkas), sehingga pernyataan "belum ada
> kodenya" dan angka uji di bawah **tidak lagi menggambarkan kondisi repo**.
> Ringkasan terbaru: `README.md`.

## 0. Ringkasan satu menit 

**Sudah jadi dan bisa ditunjukkan hari ini:** API FastAPI dengan empat endpoint
(`/health`, `/extract`, `/fetch-url`, `/extract-from-url`), ekstraksi 9 field kepatuhan
lewat Gemini dengan keluaran JSON, prompt v1 dan v2 (v2 sudah ditulis, belum
disambungkan ke kode), harness BREAK Minggu 1 beserta prediksi yang ditulis sebelum
percobaan, dokumen proses Minggu 1–16, dan catatan biaya yang sudah dihitung ulang.

**Belum ada kodenya:** RAG (chunker, embedder, vectorstore, `build_index.py`, `/ask`),
antarmuka Streamlit, agen banyak langkah, guardrails, set uji dan harness evaluasi,
serta dokumen rujukan di `data/raw/`.

**Kondisi uji — angka sebenarnya, bukan klaim:** `tests/test_api.py` → **4 lulus, 26
gagal**; `tests/test_theme.py` → **3 gagal**; empat modul uji lain **gagal di tahap
import** karena modul yang diimpornya tidak ada (`src.rag`, `src.agent`,
`src.guardrails`, dan `_proyeksi_ringkas`). Total 72 fungsi uji tertulis, 4 yang lulus.

**Satu kalimat yang harus diucapkan apa adanya di presentasi:** *"Dokumen dan tes di
repo ini sudah menuliskan bentuk akhir produk; kode yang ada baru sampai Lapisan 2."*
Kalau ini tidak dikatakan lebih dulu, reviewer akan menemukannya sendiri dan seluruh
laporan kehilangan kredibilitas.

---

## 1. Apa yang sudah dibuat

### 1.1 Kode yang ada

| Berkas | Isi | Status |
|---|---|---|
| `api.py` | FastAPI: `POST /extract`, `POST /fetch-url`, `POST /extract-from-url`, `GET /health`. Ambil halaman dengan `requests`, bersihkan HTML dengan BeautifulSoup, potong 20.000 karakter. | **Berjalan** (diuji live, §2) |
| `src/extraction/extractor.py` | Kirim teks ke `gemini-3.6-flash` dengan `response_mime_type="application/json"`, parsing JSON, cek 9 field wajib, kembalikan `fields`, `missing_fields`, `usage` (token masuk/keluar). | **Berjalan** untuk satu panggilan; belum ada validasi skema v2/retry |
| `uji_break_minggu1.py` | Empat percobaan BREAK Minggu 1 (pertanyaan faktual, peristiwa bulan lalu, dokumen internal, tokoh karangan). Prediksi ditulis sebagai konstanta **sebelum** model dipanggil. | Skrip lengkap; hasil tersimpan (4 percobaan, 6 jawaban) |

### 1.2 Prompt dan instruksi

| Berkas | Isi | Sambungan ke kode |
|---|---|---|
| `prompts/system_prompt_v1.md` | Prompt aktif: 9 field, ringkasan ≤ 2 kalimat, nilai `"tidak disebutkan"`, larangan mengarang. | **Dipakai** `extractor.py` |
| `instruksi/v1.md` | Salinan prompt v1 untuk perbandingan versi. | Tidak dipakai kode |
| `instruksi/v2.md` | 9 field + 9 kutipan bukti (18 key), contoh kasus sulit termasuk dokumen yang disusupi instruksi. | **Belum tersambung** |
| `instruksi/agent-v1.md` | Instruksi untuk agen banyak langkah. | Belum ada kode agen |
| `instruksi/CATATAN.md` | Riwayat versi prompt: apa yang diubah, kenapa, efek yang terlihat. | Dokumen |

### 1.3 Tes (kontrak yang sudah ditulis, belum dipenuhi)

| Berkas | Fungsi uji | Menguji apa | Kondisi |
|---|---|---|---|
| `tests/test_api.py` | 18 (30 kasus setelah parametrik) | Pemetaan galat Gemini → HTTP bermakna, validasi URL, `/ask`, dan **penolakan host internal (anti-SSRF)** | 4 lulus, 26 gagal |
| `tests/test_guardrails.py` | 19 | Filter input (data pribadi) dan pemeriksa output | Gagal import: `src.guardrails` tidak ada |
| `tests/test_agent.py` | 15 | Agen, tool, state, persetujuan, `AgentGagal` | Gagal import: `src.agent` tidak ada |
| `tests/test_chunker.py` | 12 | Pemecahan teks per heading / per kata + overlap | Gagal import: `src.rag` tidak ada |
| `tests/test_extractor_mode.py` | 5 | Mode keluaran ringkas (`_proyeksi_ringkas`) | Gagal import: fungsi belum ada |
| `tests/test_theme.py` | 3 | Tema terang dipaksa lewat `.streamlit/config.toml` | Gagal: berkas konfigurasi tidak ada |

### 1.4 Data dan log

| Berkas | Isi | Catatan |
|---|---|---|
| `data/sample_kebijakan.txt` | Satu contoh kebijakan ringkas (BAYARKU) | **Satu-satunya** data di repo |
| `logs/success_cases.md` | Baseline ekstraksi BAYARKU: 9 field, 4 di antaranya benar dijawab `"tidak disebutkan"` | Bukti terkuat yang bisa ditunjukkan |
| `logs/break-minggu1.json` | 4 percobaan BREAK: prompt, prediksi yang ditulis lebih dulu, dan **jawaban model** (6 jawaban; percobaan 1 diulang 3×) | Belum ada kolom penilaian "prediksi tepat?" — penilaiannya masih manual |
| `logs/failed_cases.md` | Template log kasus gagal | **0 byte** — kosong |

### 1.5 Dokumen

| Berkas | Isi |
|---|---|
| `README.md` | Gambaran produk, cara menjalankan, tabel hasil, batas penggunaan |
| `docs/catatan-proses.md` | 1.470 baris: Minggu 1–16 dengan format READ/BREAK/FIX/BUILD, pemakaian biaya, daftar periksa, penggunaan AI |
| `catatan-proses/minggu-01-03.md` … `minggu-14-16.md` | Ringkasan lima blok minggu |
| `catatan-pemakaian.md` | Buku besar biaya 21 baris kegiatan Minggu 1–16, tarif, perhitungan ulang, proyeksi |
| `catatan-proses/README.md` | Indeks catatan proses |

---

## 2. Bukti yang bisa ditunjukkan hari ini (sudah diverifikasi)

Dijalankan pada 9 November 2026 di checkout ini:

| Yang diperiksa | Perintah | Hasil |
|---|---|---|
| Aplikasi bisa diimpor | `python -c "import api"` | OK — `Ekstraktor Kebijakan Privasi` |
| API hidup | `uvicorn api:app --port 8123` lalu `GET /health` | **200** `{"status":"ok"}` |
| Tool ambil halaman | `POST /fetch-url` dengan `https://example.com` | **200**, teks halaman bersih terpotong |
| Uji lapisan API | `python -m pytest tests/test_api.py -q` | **4 lulus, 26 gagal** (exit 1) |
| Uji tema | `python -m pytest tests/test_theme.py -q` | **3 gagal** (berkas `.streamlit/config.toml` tidak ada) |
| Uji seluruh repo | `python -m pytest -q` | **berhenti di koleksi**: 4 modul gagal import |
| Bukti BREAK Minggu 1 | baca `logs/break-minggu1.json` | 4 percobaan, **6 jawaban tersimpan**, semua prediksi ditulis sebelum pemanggilan |

**Yang tidak diuji hari ini:** panggilan `/extract` sungguhan ke
Gemini sengaja tidak dijalankan agar tidak menghabiskan kuota 20 permintaan/hari
sebelum presentasi. Bukti bahwa jalur ini pernah berhasil ada di
`logs/success_cases.md`, bukan dari pengujian hari ini.

---

## 3. Apa yang masih kurang

### 3.1 Ringkasan per lapisan

| Lapisan | Yang dijanjikan | Kenyataan di repo | Selisih |
|---|---|---|---|
| 1 Fondasi | Catatan proses, perbandingan model, biaya | Ada (dokumen) | Tidak ada kode yang perlu |
| 2 Kendali | Ekstraksi 18 key + validasi + retry + UI | 9 key, tanpa validasi/retry, tanpa UI | **Setengah** |
| 3 Grounding | Chunker, embedding, ChromaDB, `build_index.py`, `/ask`, 8 dokumen | Tidak ada kode, tidak ada `data/raw/` | **Belum mulai (kode)** |
| 4 Agentic | Agen, tool, state, batas langkah, persetujuan | Hanya prompt `instruksi/agent-v1.md` + tes | **Belum mulai** |
| 5 Kematangan | Guardrails, set uji, evaluasi, kajian risiko, refleksi | Tes guardrails ada; dokumen dan harness tidak | **Belum mulai** |

### 3.2 Daftar berkas yang hilang (diminta tes atau README, tetapi tidak ada)

```
src/rag/chunker.py            src/rag/embedder.py       src/rag/vectorstore.py
build_index.py                app.py                    .streamlit/config.toml
src/agent/agent.py            src/agent/tools.py        run_agent.py
src/guardrails/input_filter.py  src/guardrails/output_check.py
src/eval/jalankan_set_uji.py  set-uji/                  uji_serangan.py
data/raw/ (8 dokumen + SUMBER.md)
laporan-evaluasi.md  guardrails.md  kajian-risiko.md  refleksi.md
rancangan-sistem.md  analisis-workflow-vs-agen.md
```

### 3.3 Prioritas dan perkiraan usaha

| Prioritas | Pekerjaan | Kenapa penting sekarang | Perkiraan |
|---|---|---|---|
| **P0** | Menyamakan klaim README dengan kenyataan, **atau** menyelesaikan modul yang dijanjikan | README menyebut "97 uji otomatis", 8 dokumen, agen, guardrails, dan evaluasi — tidak satu pun ada. Ini risiko kredibilitas paling besar saat tanya jawab. | 1–2 jam (menurunkan klaim) |
| **P0** | Menyambungkan `instruksi/v2.md` + validasi 18 key + retry sekali | Fitur yang paling sering ditanyakan: kendali output. Tes `test_extractor_mode.py` sudah menuliskan kontraknya. | 3–5 jam |
| **P0** | Memperbaiki `api.py` agar sesuai `tests/test_api.py` (`_galat_model`, `/ask`, `AnyUrl`, tolak host internal) | 26 dari 30 kasus uji gagal; anti-SSRF adalah bukti keamanan yang kuat kalau ada. | 4–6 jam |
| **P1** | RAG minimal: `chunker` + `embedder` + `vectorstore` + `build_index` + `/ask` + 3 dokumen `data/raw/` | Ini inti Lapisan 3; tanpa ini presentasi hanya bercerita. | 8–12 jam |
| **P1** | `app.py` + `.streamlit/config.toml` | Demo lewat layar jauh lebih meyakinkan daripada `/docs`. | 4–6 jam |
| **P2** | Agen + guardrails + set uji + laporan evaluasi | Baru masuk akal setelah P0–P1 stabil. | 15–25 jam |

### 3.4 Ketidaksinkronan dokumen yang harus dibereskan

1. **README vs kode.** README menyebut 97 uji lulus, 8 dokumen, agen, guardrails,
   `logs/hasil-evaluasi-*.json`, `laporan-evaluasi.md` semuanya tidak ada.
2. **`docs/catatan-proses.md` vs kode.** Dokumen mencatat Minggu 9 (RAG), 10–11 (agen),
   13 (guardrails), 14 (evaluasi) sebagai dikerjakan; kodenya tidak ada di commit ini.
3. **`logs/failed_cases.md` 0 byte.** Padahal dokumen proses merujuk kasus gagal.
4. **`logs/break-minggu1.json`** sudah berisi prediksi **dan** jawaban (6 jawaban dari
   4 percobaan), tetapi belum ada penilaian "prediksi tepat atau tidak". Dokumen proses
   masih menyebut BREAK Minggu 1 belum dikerjakan — padahal sudah dijalankan 2 November
   2026. Ini contoh lain dokumen yang tertinggal dari kenyataan.

---

## 4. Cara menjalankan proyek (yang benar-benar jalan sekarang)

### 4.1 Persiapan

```bash
# dari akar proyek
python --version                 # butuh Python 3.12 (dipakai di proyek ini)
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Buat `.env` berisi satu baris (jangan pernah di-commit):

```
GEMINI_API_KEY=...
```

`.env` sudah ada di checkout ini; isinya tidak ditampilkan di laporan.

### 4.2 Menjalankan API

```bash
uvicorn api:app --reload
```

Lalu buka `http://127.0.0.1:8000/docs` — halaman uji bawaan FastAPI, tidak perlu
Postman. Perintah ini **sudah diverifikasi berjalan** (diuji di port 8123).

Contoh pemeriksaan tanpa memakai kuota model:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}

curl -X POST http://127.0.0.1:8000/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
# {"url":"...","text":"Example Domain ..."}  (200)
```

Ekstraksi (memakai 1 permintaan kuota):

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$(cat data/sample_kebijakan.txt | tr '\n' ' ')\"}"
```

### 4.3 Menjalankan uji

```bash
python -m pytest tests/test_api.py -q     # 4 lulus, 26 gagal  (jangan diklaim hijau)
python -m pytest tests/test_theme.py -q   # 3 gagal (config tema belum ada)
python -m pytest -q                       # berhenti: 4 modul gagal import
```

Kalau ditanya kenapa merah: tesnya menuliskan kontrak versi akhir, kodenya baru
Lapisan 2. Itu jawaban yang benar — bukan "di komputer saya hijau".

### 4.4 Perintah yang BELUM bisa dijalankan

| Perintah | Alasan |
|---|---|
| `streamlit run app.py` | `app.py` tidak ada |
| `python build_index.py` | tidak ada; `src/rag/` juga tidak ada |
| `python run_agent.py "..."` | tidak ada |
| `python -m src.eval.jalankan_set_uji` | tidak ada |
| `python uji_serangan.py` | tidak ada |

Jangan menampilkan perintah ini di slide sebelum berkasnya dibuat.

---

## 5. Rencana presentasi progres (8 menit)

| Waktu | Yang dilakukan | Kalimat kunci |
|---|---|---|
| 0:00–1:00 | Persoalan: pengguna dompet digital menekan "setuju" tanpa membaca; kebijakan OVO ±85 ribu karakter | "Masalahnya bukan tidak ada informasi, tapi informasi tidak bisa dipakai tanpa membacanya habis." |
| 1:00–2:30 | Arsitektur target 5 lapisan; tunjuk posisi sekarang: Lapisan 2 berjalan, 3–5 dirancang | "Saya sengaja menunjukkan peta ini supaya jelas mana yang sudah ada dan mana yang belum." |
| 2:30–4:30 | **Demo live tanpa kuota:** buka `/docs`, jalankan `/health` dan `/fetch-url` | "Dua endpoint ini tidak butuh model, jadi bisa didemokan tanpa takut kuota habis." |
| 4:30–5:30 | Demo `/extract` **satu kali** dengan `data/sample_kebijakan.txt`; kalau 429, tunjukkan keluaran yang sudah tersimpan di `logs/success_cases.md` | "Saya simpan keluarannya karena kuota gratis hanya 20 permintaan per hari." |
| 5:30–6:30 | Bukti angka: 9 field, 4 dijawab "tidak disebutkan" tanpa mengarang; biaya setara $0,003581/ekstraksi | "Yang saya banggakan bukan jawabannya, tapi yang **tidak** dijawab model." |
| 6:30–7:30 | Kegagalan yang ditemukan sendiri: BREAK Minggu 1 — percobaan 3 dan 4 model menolak mengarang, tetapi percobaan 2 memperlakukan Oktober 2026 sebagai masa depan (batas pengetahuan Januari 2025) lalu memproyeksikan; ditambah kuota 20/hari yang menggagalkan 8 dari 10 kasus uji v1/v2 | "Kegagalan ini yang mengubah keputusan saya — terutama soal waktu dan kuota." |
| 7:30–8:00 | Rencana 2 minggu ke depan + satu hal yang diminta masukan | "Saya butuh masukan: mendahulukan RAG atau memperbaiki kendali output dulu?" |

**Yang jangan diklaim di slide:** "97 uji lulus", "RAG berjalan", "agen berjalan",
"evaluasi 14/17", "8 dokumen rujukan". Semuanya belum ada di checkout ini.

---

## 6. Antisipasi pertanyaan (dan jawaban jujurnya)

**1. "Kenapa tesnya banyak yang merah?"**
Tes menuliskan kontrak versi akhir (RAG, agen, guardrails, mode ringkas); kode yang ada
baru Lapisan 2. Yang sudah lulus: 4 kasus di `test_api.py`. Rencana: menyelesaikan
`_galat_model`, `/ask`, dan validasi URL lebih dulu supaya `test_api.py` hijau penuh.

**2. "Mana bukti RAG-nya?"**
Belum ada kodenya di commit ini. Yang ada: rancangan chunking/ambang di dokumen proses
dan `tests/test_chunker.py`. Saya tidak akan mendemokan sesuatu yang tidak ada.

**3. "Apa bukti produk Anda bekerja?"**
Dua bukti: (a) `logs/success_cases.md` — 9 field terisi, 4 di antaranya benar dijawab
"tidak disebutkan", `missing_fields` kosong; (b) `logs/break-minggu1.json` — pada
percobaan 3 dan 4 model menolak mengarang (mengaku tidak punya akses / nama tidak
terscatat). Batasnya: satu dokumen ringkas dan empat percobaan, bukan evaluasi
sistematis.

**4. "Berapa biayanya?"**
$0,003581 per ekstraksi (2.244 token masuk, 506 keluar, tarif Flash), ≈ Rp 59. Aktual
Rp 0 karena free tier. Kendala sebenarnya kuota 20 permintaan/hari, bukan uang —
hitungan lengkap di `catatan-pemakaian.md`.

**5. "Apa risiko terbesar proyek ini sekarang?"**
Ketidaksinkronan dokumen dan kode. Dokumen mencatat 16 minggu seolah semua lapisan
selesai, sedangkan repo baru berisi Lapisan 2. Risikonya bukan teknis, tapi
kredibilitas — karena itu laporan ini menuliskannya di depan.

---

## 7. Daftar periksa H-1 presentasi

- [ ] Putuskan satu: perbaiki README agar sesuai kenyataan, **atau** selesaikan modul
      yang dijanjikan. Jangan biarkan keduanya bertentangan saat presentasi.
- [ ] Jalankan `python -m pytest -q` dan catat angka apa adanya di slide.
- [ ] Siapkan satu keluaran `/extract` yang sudah tersimpan (screenshot/JSON) untuk
      cadangan bila kuota habis atau internet mati.
- [ ] Cek sisa kuota sehari sebelum presentasi; jangan pakai untuk eksperimen lain.
- [ ] Siapkan `data/sample_kebijakan.txt` dalam bentuk satu baris agar mudah ditempel.
- [ ] Pastikan `.env` ada dan tidak ikut tampil di layar saat demo.
- [ ] Siapkan jawaban untuk pertanyaan no. 1 dan 5 di §6 — itu yang paling mungkin
      ditanya lebih dulu.

---

## 8. Lampiran — klaim README vs kenyataan

| Klaim di `README.md` | Ada di repo? |
|---|---|
| 97 uji otomatis lulus | **Tidak** — 4 lulus, 26 gagal, 4 modul error import |
| 8 dokumen rujukan + `data/raw/SUMBER.md` | **Tidak** — hanya `data/sample_kebijakan.txt` |
| `app.py` Streamlit | **Tidak ada** |
| `build_index.py`, `src/rag/*` | **Tidak ada** |
| `run_agent.py`, `src/agent/*` | **Tidak ada** |
| `src/guardrails/*` | **Tidak ada** |
| `set-uji/`, `src/eval/`, `uji_serangan.py` | **Tidak ada** |
| `laporan-evaluasi.md`, `guardrails.md`, `kajian-risiko.md`, `refleksi.md` | **Tidak ada** |
| `rancangan-sistem.md`, `analisis-workflow-vs-agen.md` | **Tidak ada** |
| `catatan-pemakaian.md` | **Ada** (baru dilengkapi 9 November 2026) |
| `docs/catatan-proses.md` Minggu 1–16 | **Ada** |
| `instruksi/v1.md`, `v2.md`, `agent-v1.md`, `CATATAN.md` | **Ada** |

---

## 9. Usulan langkah berikutnya (urut)

1. **Hari ini:** putuskan cakupan presentasi — Lapisan 2 + rencana, atau tunda
   presentasi sampai RAG minimal jadi. Ini keputusan, bukan pekerjaan teknis.
2. **1–2 hari:** `_galat_model` + `/ask` + `AnyUrl` + tolak host internal → kejar
   `test_api.py` hijau; sambungkan `instruksi/v2.md` + validasi 18 key + retry.
3. **3–5 hari:** RAG minimal + 3 dokumen `data/raw/` + `app.py` sederhana.
4. **Setelah presentasi:** agen, guardrails, set uji, laporan evaluasi, lalu
   menyelaraskan seluruh dokumen dengan kode yang benar-benar ada.
