# Rancangan Sistem — Privia (versi akhir)

Dokumen ini adalah rancangan akhir setelah Lapisan 4 dan 5 selesai. Rancangan awal
per-lapisan tetap tersimpan di `rancangan.md` (Lapisan 2–3) dan `rancangan-rag.md`
(keputusan retrieval); yang di sini adalah gabungannya plus alasan setiap keputusan.

---

## 1. Alur dalam satu gambar

```
                 ┌──────────────────────────────────────────────┐
   input teks ──►│ Lapis 1 guardrails: saring input              │
   atau URL      │  - pola injection (dokumen: ditandai)        │
                 │  - data pribadi (ditolak, tidak dikirim)     │
                 └───────────────┬──────────────────────────────┘
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │ Alur A — Ekstraksi (workflow, satu langkah)            │
        │  prompt v2 → JSON 9 field + 9 bukti → cek schema       │
        │  gagal → ulang sekali dengan daftar pelanggaran        │
        │  masih gagal → ValueError jelas (bukan ditebak)        │
        └───────────────┬────────────────────────────────────────┘
                        │  mode penuh / mode ringkas (proyeksi 4 field)
                        ▼
                 ┌──────────────────────────────┐
                 │ Lapis 4 guardrails: bukti     │
                 │ dicek ada di dokumen asli     │
                 └──────────────────────────────┘

        ┌────────────────────────────────────────────────────────┐
        │ Alur B — Tanya jawab (workflow RAG, satu langkah)      │
        │  embed pertanyaan → ChromaDB top-k → buang jarak >0.65 │
        │  kosong? → "Tidak ada di dokumen." TANPA panggil model │
        │  ada? → model + konteks bernomor [1][2]                │
        └───────────────┬────────────────────────────────────────┘
                        ▼
                 ┌──────────────────────────────┐
                 │ Lapis 4: cek kebocoran prompt,│
                 │ putusan kepatuhan, rujukan    │
                 └──────────────────────────────┘

        ┌────────────────────────────────────────────────────────┐
        │ Alur C — Agen (agentic, banyak langkah)                │
        │  REASON → ACT (tool) → OBSERVE → ulangi                │
        │  batas 8 langkah · state di logs/agent_state/          │
        │  trace di logs/agent_trace/ · tool gagal: ulang 1x     │
        │  simpan_laporan → BERHENTI minta persetujuan manusia   │
        └────────────────────────────────────────────────────────┘
```

## 2. Keputusan rancangan dan alasannya

| # | Keputusan | Alasan | Alternatif yang ditolak |
|---|---|---|---|
| 1 | Schema tetap 9 field + 9 bukti | Tanpa bukti, hasil tidak bisa diverifikasi dan model bebas "merasa" | Skema bebas/teks naratif: tidak bisa diuji, tidak bisa dipakai mesin |
| 2 | Bukti = kutipan langsung, nilai = parafrase | Dua pembaca berbeda: manusia butuh ringkas, pemeriksa butuh yang bisa dicocokkan persis ke dokumen | Semua parafrase: tidak bisa dibuktikan; semua kutipan: tidak terbaca |
| 3 | `response_mime_type=application/json` + validasi skema + ulang sekali | JSON valid belum berarti benar; menegakkan di dua tempat menutup dua jenis kegagalan berbeda | Hanya instruksi prompt: format bocor sesekali |
| 4 | Ambang jarak 0,65 sebelum model dipanggil | Menghemat biaya DAN tidak bergantung pada kedisiplinan model mengaku tidak tahu; diukur dari 0,42–0,49 (relevan) vs 0,76–0,80 (tidak) | Mengandalkan prompt "jangan mengarang": terbukti bisa gagal |
| 5 | Ekstraksi & RAG tetap **workflow**, bukan agent | Urutan langkahnya pasti; menjadikannya agent hanya menambah biaya, variansi, dan kesulitan uji tanpa manfaat | Agent untuk semua alur |
| 6 | Agent hanya untuk tugas pembandingan lintas dokumen | Langkah kedua bergantung hasil pertama (dokumen mana yang menyebut apa), sehingga urutan tidak bisa ditentukan di awal | Chain tetap 8 panggilan: mahal untuk tugas yang selesai dalam 3 |
| 7 | Batas 8 langkah + maksimum keras 20 | Biaya terburuk harus bisa dihitung; agent yang berputar tanpa batas tidak bisa dipertanggungjawabkan | Tanpa batas, atau batas 20 sejak awal |
| 8 | State di luar percakapan (`logs/agent_state/*.json`) | Bisa diperiksa, dilanjutkan setelah terputus, dan konteks tidak membengkak | State di riwayat chat: tidak bisa dicek/dilanjutkan |
| 9 | Persetujuan manusia untuk `simpan_laporan` | Menulis berkas tidak bisa dibatalkan; modul mewajibkan titik HITL pada tindakan berdampak | Menjalankan otomatis dengan kalimat "jangan" di prompt |
| 10 | Batas akses tool dipasang di kode (daftar putih `data/raw/`) | Lapis 3 tidak bergantung pada kepatuhan model; prompt adalah lapis terlemah | Hanya instruksi prompt |
| 11 | Mode ringkas = proyeksi hasil penuh, bukan panggilan kedua | Nol biaya tambahan, kualitas dasar identik, dan bisa dibuktikan dengan angka yang sama | Panggilan model kedua untuk meringkas |
| 12 | Cache hasil evaluasi per (kasus, model, input) | Kuota gratis 20 permintaan/hari; tanpa cache, pengujian ulang menghabiskan kuota tanpa informasi baru | Menjalankan ulang semua tiap kali |
| 13 | Penilaian otomatis + kalibrasi manual ≥1/3 | Angka otomatis saja tidak cukup; kalibrasi wajib dilaporkan | Hanya "LLM as judge" tanpa kalibrasi |

## 3. Komponen

| Komponen | Berkas | Tanggung jawab |
|---|---|---|
| Ekstraksi | `src/extraction/extractor.py` | Panggil Gemini, tegakkan skema 18 key, mode penuh/ringkas |
| RAG | `src/rag/*.py` | Chunking 150 kata/overlap 30, embedding, ChromaDB, ambang 0,65 |
| Agent | `src/agent/agent.py` | Loop ReAct, batas langkah, state, trace, HITL |
| Tool | `src/agent/tools.py` | 4 tool + batas akses yang ditegakkan di kode |
| Guardrails | `src/guardrails/*.py` | Lapis 1 (input) dan lapis 4 (output) |
| API | `api.py` | `/extract`, `/extract-from-url`, `/ask`, `/agent`, `/health` |
| UI | `app.py` | Streamlit: ekstraksi (mode penuh/ringkas), tanya jawab |
| Evaluasi | `src/eval/jalankan_set_uji.py` | Jalankan `set-uji/kasus.jsonl`, hitung kriteria, cache |

## 4. Kendali output

Schema 18 key (9 field + 9 bukti) ditegakkan tiga lapis: instruksi prompt,
`response_mime_type`, dan validasi `_field_tidak_valid` di kode. Kegagalan
ditangani tiga langkah (cek → ulang sekali dengan daftar pelanggaran → gagal jelas
dengan `ValueError`), bukan ditebak atau dilewati diam-diam.

Riwayat versi prompt ada di `instruksi/CATATAN.md`: v1 (9 field), v2 (menambah 9
field bukti + contoh kasus sulit), agent-v1 (protokol JSON untuk loop banyak
langkah). Mode ringkas bukan versi prompt baru karena ia tidak mengubah instruksi
ke model.

## 5. Tool, batas akses, dan persetujuan

| Tool | Boleh | Tidak boleh | Ditegakkan di |
|---|---|---|---|
| `cari_dokumen` | baca index vektor, k 1–10 | menulis, jaringan | kode |
| `baca_dokumen` | 8 berkas di `data/raw/`, maks 1.200 kata | berkas lain, `.env`, `SUMBER.md`, path traversal | kode (daftar putih) |
| `ambil_field` | 9 field skema dari dokumen daftar putih | field lain, dokumen lain | kode |
| `simpan_laporan` | tulis `.md` di `logs/laporan-agent/` | folder lain, nama aneh, >20.000 karakter | kode + **persetujuan manusia** |

Tidak ada tool shell, email, atau HTTP bebas di agen. Rincian dan hasil uji ada di
`guardrails.md`.

## 6. Grounding

Delapan dokumen rujukan (4 dompet digital, 1 platform investasi, 1 marketplace,
1 e-wallet tambahan, 1 ringkasan UU PDP), asal-usulnya di `data/raw/SUMBER.md`.
Chunking 150 kata dengan overlap 30; dokumen markdown terstruktur dipecah per
heading. Ambang relevansi 0,65 dipilih dari pengukuran, bukan tebakan
(`logs/lapisan3_rag_cases.md`).

## 7. Bukti sejauh ini

| Bukti | Angka | Berkas |
|---|---|---|
| Uji otomatis | 97 lulus | `pytest -q` |
| Set uji (17 kasus, model flash) | 14 lulus seluruh kriteria | `logs/hasil-evaluasi-v1.json` |
| Kasus agent | selesai dalam 3–4 langkah, menyebut sumber | `logs/agent_trace/` |
| Serangan | 4 ditolak, 0 tembus, 2 tidak teruji | `logs/uji-serangan.json` |
| Bukti verbatim | 15/17 kasus buktinya bisa dicocokkan ke dokumen | `laporan-evaluasi.md` §4 |

## 8. Yang sengaja TIDAK dibangun

- **Multi-agent** (beberapa agent berperan berbeda). Modul menyebutnya jarang
  terbukti lebih baik untuk proyek satu semester; satu agent dengan 4 tool cukup
  untuk tugas yang ada, dan biaya serta sumber masalahnya jauh lebih mudah dilacak.
- **Memory jangka panjang antar-sesi.** Tidak ada kebutuhan menyimpan preferensi
  pengguna, dan menyimpan isi kebijakan yang dibaca pengguna justru menambah risiko
  data. State tugas disimpan per tugas lalu berhenti di situ.
- **Penilaian kepatuhan otomatis.** Sengaja ditolak; itu keputusan manusia dan
  menjadi batas etis produk (`kajian-risiko.md` §7).
- **Antarmuka agen di Streamlit.** Agen dijalankan lewat CLI dan `/agent`; menambah
  halaman UI tidak menambah bukti apa pun yang dinilai, sedangkan waktu lebih baik
  dipakai untuk evaluasi dan laporan.
