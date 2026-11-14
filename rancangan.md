# Rancangan Sistem — Privia

## 1. Persoalan

*Pernahkah kita menekan "Setuju" tanpa benar-benar membaca kebijakan privasi?*

**Siapa yang mengalami.** Pengguna dompet digital yang ingin memahami penggunaan data
pribadinya sebelum menyetujui, dan tim legal atau compliance yang harus meninjau banyak
dokumen dengan isi dan format yang berbeda.

**Cara sekarang.** Dibaca manual satu per satu, atau langsung menekan "setuju".

**Mengapa belum cukup.** Dokumennya panjang, istilahnya beragam, dan informasi penting
tersebar di berbagai bagian, sehingga sulit dipahami dan sulit dibandingkan secara efisien.

**Ukuran contoh.** Kebijakan privasi OVO sepanjang 85.181 karakter (±12 ribu kata);
dengan asumsi 200 kata per menit, waktu bacanya mendekati satu jam. Ini estimasi untuk
satu contoh, bukan ukuran semua kebijakan privasi.

**Kasus pemicu (skenario ilustrasi, bukan kejadian satu orang tertentu).** Seorang
pengguna mendaftar di dompet digital. Ia hanya ingin tahu data apa yang diambil, dibagikan
ke siapa, dan berapa lama disimpan. Jawabannya terkubur di dokumen sekitar 12 ribu kata,
sehingga ia langsung menekan "setuju".

**Bukti pendukung dan batasnya.** Studi pada mahasiswa Indonesia (Baso, 2025)
melaporkan 22,65% responden rutin membaca kebijakan privasi. Sampelnya hanya 31 orang
dan topiknya aplikasi IoT, jadi angka ini gambaran, bukan angka nasional. Saya belum
mewawancarai pengguna; validasi dengan 2–3 pengguna dan satu orang di bidang
kepatuhan masuk rencana.

**Bukan tujuan.** Menyimpulkan status "patuh" atau "melanggar" UU PDP, dan memberi
nasihat hukum.

| Di dalam lingkup | Sengaja di luar lingkup |
|---|---|
| Ekstraksi 9 aspek + kutipan bukti | Penilaian kepatuhan otomatis |
| Tanya jawab berbasis dokumen (RAG) | Pengetahuan umum model sebagai sumber jawaban |
| Pengambilan dokumen dari URL publik | Akses ke jaringan internal atau host privat |
| Jejak bukti: sumber, indeks chunk, jarak | Keputusan akhir yang menyangkut subjek data |

## 2. Mengapa AI generatif

**Mengapa bukan basis data atau formulir.** Keduanya baik bila informasi sudah
terstruktur. Di sini masukannya teks bebas, sehingga kolom seperti "tujuan pemrosesan"
atau "penerima data" belum ada untuk diisi, dan pengguna tidak realistis diminta mengisi
sendiri semua field untuk tiap dokumen.

**Mengapa bukan aturan atau kata kunci.** Pencarian kata kunci melewatkan makna yang
ditulis dengan ungkapan berbeda: "dibagikan ke mitra" dan "pihak ketiga penerima"
bermakna serupa tetapi tidak berbagi kata. Model bahasa dipakai untuk memetakan makna
kalimat ke field baku.

**Pembagian tugas.** Model hanya dipakai di bagian yang butuh penafsiran makna.

| Proses | Pendekatan | Alasan |
|---|---|---|
| Mengambil halaman URL | `requests` + BeautifulSoup | Teknis, tanpa penafsiran semantik |
| Memvalidasi skema | Parsing JSON + pemeriksaan field | Aturan deterministik lebih cocok untuk format |
| Mencari chunk | Embedding (`gemini-embedding-001`) + ChromaDB | Kedekatan makna; ini model embedding, bukan model bahasa generatif |
| Menyaring relevansi | Ambang jarak 0,65 | Membuang chunk sebelum konteks sampai ke model |
| Ekstraksi makna dan menjawab | Model bahasa (Gemini 3.6 Flash) | Memetakan makna dan menyusun jawaban dari konteks |
| Menghitung token dan biaya | Pencatatan penggunaan | Metrik, tidak butuh generasi bahasa |

Dari 10 langkah pada diagram bab 3, hanya 2 yang memakai model bahasa generatif
(Ekstraksi dan Jawab).

## 3. Rancangan sistem

### 3.1 Alur dalam satu gambar

```
A · EKSTRAKSI SATU DOKUMEN
 Input ──▶ Fetch & Cleaning ──▶ Ekstraksi ★ ──▶ Validasi skema ──▶ Hasil
 (teks     (requests +          (Gemini 3.6      (parse JSON,       (9 field + bukti
  /URL)     BeautifulSoup)       Flash, mode      aturan skema)      + status ADA /
                                 JSON)                               TIDAK DISEBUTKAN)

B · TANYA JAWAB BERBASIS DOKUMEN (RAG)
 Pertanyaan ──▶ Cari chunk ──▶ Saring jarak ──▶ Jawab ★ ──▶ Jawaban + sumber
                (embedding,    (buang > 0,65)   (Gemini +     ([1][2], dokumen,
                 ChromaDB,           │           konteks)      bagian, jarak)
                 k = 5)              ▼
                          "Tidak ada di dokumen."  (model tidak dipanggil)

Indeks (dibangun sekali, offline): dokumen ──▶ chunk ──▶ embedding ──▶ ChromaDB

★ = langkah yang memakai model bahasa generatif (2 dari 10 langkah)
```

### 3.2 Komponen

| Komponen | Peran |
|---|---|
| Streamlit (`app.py`) | Antarmuka: tempel teks atau URL, pilih Ekstraksi atau Tanya Jawab, tampilkan hasil |
| FastAPI (`api.py`) | Endpoint `/extract`, `/fetch-url`, `/extract-from-url`, `/ask`, `/health` |
| requests + BeautifulSoup | Mengambil dan membersihkan halaman web |
| Gemini 3.6 Flash | Ekstraksi dan penyusunan jawaban |
| gemini-embedding-001 | Embedding chunk dan pertanyaan |
| ChromaDB (lokal) | Indeks vektor di `chroma_db/` |

API dan antarmuka adalah **dua proses terpisah** yang berbicara lewat HTTP. Logika bisnis
dapat diuji langsung lewat `/docs` bawaan FastAPI tanpa antarmuka.

### 3.3 Alur A: ekstraksi

```
Teks kebijakan ─┐
                ├─▶ /extract atau /extract-from-url
URL publik ─▶ /fetch-url (cek host publik → unduh → bersihkan HTML)

 → Gemini 3.6 Flash, instruksi sistem, response_mime_type = application/json
 → validasi skema (18 key wajib)
     tidak valid → ulangi SEKALI dengan daftar pelanggaran
     masih tidak valid → gagal jelas (HTTP 422), dicatat
 → { fields, missing_fields, usage, prompt_version }
 → antarmuka: tiap field + kutipan bukti + status + token terpakai
```

### 3.4 Alur B: tanya jawab (RAG)

```
PENYIAPAN (sekali, dan ulangi tiap isi data/raw/ berubah)
  dokumen → chunk (per heading untuk .md; ±150 kata + overlap 30 untuk teks)
          → embedding gemini-embedding-001 (RETRIEVAL_DOCUMENT)
          → ChromaDB (koleksi dokumen_rujukan)

SAAT MENJAWAB
  pertanyaan → embedding (RETRIEVAL_QUERY)
            → ambil k chunk terdekat (default k = 5, rentang 1–50 per permintaan)
            → buang chunk berjarak > 0,65
            → susun konteks bernomor [1], [2], ...
            → Gemini 3.6 Flash + instruksi sistem RAG
            → jawaban + rujukan inline + daftar sumber (berkas, bagian, jarak)
```

### 3.5 Pemetaan ke lapisan proyek

| Lapisan (spesifikasi proyek) | Wujud di Privia | Status |
|---|---|---|
| 1 Fondasi | Dokumentasi Minggu 1–3, `catatan-pemakaian.md`, `compare_models.py` | Sebagian |
| 2 Kendali | Ekstraksi 9 field, skema, validasi, `fetch_url` | Berjalan |
| 3 Grounding | `build_index.py`, `retrieve`, `/ask` | Berjalan |
| 4 Agentic | `compare_version`, `save_status`, batas langkah, persetujuan manusia | Rencana (Minggu 10–13) |
| 5 Kematangan | Set uji berjawaban acuan, biaya, kajian risiko, pernyataan etis | Rencana (Minggu 14–16) |

### 3.6 Peta berkas

```
api.py                    Endpoint: /extract, /fetch-url, /extract-from-url, /ask, /health
app.py                    Antarmuka Streamlit (memanggil api.py lewat HTTP)
build_index.py            Bangun ulang indeks RAG dari data/raw/
fetch_reference_docs.py   Unduh kebijakan privasi resmi ke data/raw/
compare_models.py         Perbandingan model (ketentuan Minggu 3)

src/extraction/extractor.py   Ekstraksi + validasi skema + retry
src/rag/chunker.py            Pecah dokumen: per heading atau per N kata + overlap
src/rag/embedder.py           Embedding Gemini + penanganan batas kecepatan
src/rag/vectorstore.py        ChromaDB: simpan, cari, ambang relevansi

instruksi/v1.md, v2.md            Instruksi sistem ekstraksi
prompts/system_prompt_rag_v1.md   Instruksi sistem RAG
data/raw/                         Dokumen rujukan
logs/                             Log kasus berhasil/gagal, uji v1 vs v2, jarak retrieval
tests/                            Uji otomatis komponen murni
```

## 4. Kendali output

### 4.1 Skema

Output ekstraksi dikunci pada **9 field**, masing-masing disertai **satu kutipan bukti**
dari dokumen (total 18 key).

| No | Field | Yang dicari |
|---|---|---|
| 1 | Jenis data yang dikumpulkan | Kategori data yang diambil dari pengguna |
| 2 | Tujuan pemrosesan | Alasan data dikumpulkan atau diproses |
| 3 | Dasar pemrosesan | Dasar yang disebutkan untuk pemrosesan |
| 4 | Pihak ketiga penerima | Pihak atau mitra yang menerima atau mengakses data |
| 5 | Transfer lintas negara | Keterangan pemindahan data ke negara lain |
| 6 | Masa retensi data | Jangka waktu atau ketentuan penyimpanan |
| 7 | Hak subjek data | Hak pengguna atas data pribadinya |
| 8 | Mekanisme keamanan | Pengamanan yang disebutkan |
| 9 | Kontak penanggung jawab | Pihak yang dapat dihubungi soal privasi atau data |

**Nilai yang valid.** Setiap field berisi ringkasan atau parafrase paling banyak dua
kalimat, atau persis `"tidak disebutkan"`. Model dilarang mengarang.

**Mengapa `"tidak disebutkan"` ada.** Nilai ini membedakan "dokumen tidak membahas" dari
"sistem gagal". Tanpa jalan keluar yang sah, model terdorong mengisi dengan tebakan yang
terdengar masuk akal.

**Mengapa ada kutipan bukti.** Ringkasan bisa terdengar benar padahal tidak ada di teks.
Kutipan membuat setiap ringkasan dapat ditelusuri ke kalimat aslinya, sehingga orang yang
memeriksa tidak perlu membaca seluruh dokumen.

**Status di antarmuka.** Penanda `ADA` / `TIDAK DISEBUTKAN` adalah status hasil
ekstraksi, bukan kesimpulan hukum.

### 4.2 Riwayat versi instruksi

| Versi | Isi | Alasan perubahan |
|---|---|---|
| v1 | 9 field, ringkasan ≤ 2 kalimat, nilai `"tidak disebutkan"` | Dasar: mencegah mengarang |
| v2 | v1 + 9 kutipan bukti, satu per field | Setiap ringkasan harus dapat ditelusuri; pasangan field–bukti divalidasi |

Uji v1 versus v2 (lihat [logs/](logs/)) menunjukkan v2 menghasilkan 9 dari 9 bukti tanpa
merusak perilaku v1.

### 4.3 Penanganan output tidak valid

- Prompt meminta JSON murni, dan kode memaksa `response_mime_type = application/json`.
- Kode memvalidasi 18 key serta konsistensi pasangan field–bukti. Contoh pelanggaran:
  field terisi tetapi buktinya `"tidak disebutkan"`.
- Tidak valid → ulangi **sekali** dengan daftar pelanggaran → masih tidak valid → gagal
  jelas dengan **HTTP 422** dan dicatat. Sistem tidak menebak dan tidak melewatinya diam-diam.
- Field yang hilang dicatat pada `missing_fields` agar dapat diperiksa.

**Batas yang diketahui.** Pemeriksaan skema baru memastikan keberadaan key dan konsistensi
pasangan, belum membatasi tipe nilai secara ketat. Temperature ditinjau pada Minggu 9
(tujuannya rendah untuk ekstraksi agar konsisten; alasan dan hasilnya dicatat).

## 5. Tool, batas akses, dan persetujuan

Tiga kategori dibedakan: **tool baca** (tidak mengubah apa pun), **pemrosesan model**
(Gemini; hanya menerima teks yang sudah disaring dan tidak memegang tool lain), dan
**tindakan yang mengubah data** (satu-satunya yang wajib persetujuan manusia).

| Tool | Jenis | Fungsi | Batas akses | Persetujuan manusia | Status |
|---|---|---|---|---|---|
| `fetch_url` | Baca | Mengambil isi kebijakan dari URL pengguna | Hanya GET; batas waktu 15 detik; teks dipotong 20.000 karakter; hanya halaman publik, host internal atau IP privat ditolak (403) untuk mencegah SSRF | Tidak perlu | Dibangun |
| `retrieve` | Baca | Mencari chunk relevan di indeks lokal | Hanya ChromaDB lokal; chunk berjarak > 0,65 dibuang | Tidak perlu | Dibangun |
| `compare_version` | Baca | Membandingkan dua versi kebijakan | Hanya dua dokumen yang dipilih pengguna | Tidak perlu | Rencana |
| `save_status` | Mengubah data | Menyimpan hasil akhir pemeriksaan | Menulis hanya ke penyimpanan hasil; tidak mengubah dokumen sumber | **Wajib** sebelum disimpan | Rencana |

**Yang sengaja tidak diotomatisasi.** Menyimpulkan "patuh" atau "melanggar UU PDP".
Klaim hukum berisiko tinggi, sehingga keputusan akhir tetap di manusia.

**Kalau tool gagal.** `fetch_url` gagal → HTTP 400 dengan pesan penyebab, tidak berlanjut
ke model. `retrieve` yang tidak menemukan chunk relevan → jawaban eksplisit
"Tidak ada di dokumen." disertai catatan. Hasil kosong dibuat eksplisit karena hasil kosong
lebih berbahaya daripada error: error terlihat gagal, sedangkan kosong tampak seperti
"memang tidak ada" dan bisa lolos tanpa disadari.

**Batas yang diketahui.** Batas 20.000 karakter membuat dokumen panjang (OVO ±85 ribu
karakter) berpotensi hanya sebagian yang dianalisis. Pengguna perlu diberi tahu bila teks
terpotong.

**Jumlah tool menurut K.** Minimum `2 + (K mod 2)`. Dua tool baca sudah dibangun;
`compare_version` dibangun di Minggu 10–13 sehingga jumlahnya memenuhi untuk nilai K apa pun.

## 6. Grounding

### 6.1 Sumber rujukan

Semua dokumen bersifat publik, dan asal (URL) dicatat di baris pertama tiap berkas.

| Berkas | Jenis | Asal |
|---|---|---|
| `ringkasan-pasal-uu-pdp.md` | Ringkasan berparafrase UU No. 27 Tahun 2022, **bukan teks resmi** | Disusun sendiri dari rangkuman JDIH; teks resmi: https://peraturan.go.id/id/uu-no-27-tahun-2022 |
| `kebijakan-gopay.txt` | Privacy Notice GoPay (berlaku 26 Juni 2025); hanya ±4 KB karena sebagian halaman butuh JavaScript | https://gopay.co.id/terms-and-condition/gopay-privacy-notice-23-juni-2025 |
| `kebijakan-ovo.txt` | Kebijakan privasi OVO | https://www.ovo.id/kebijakan-privasi |
| `kebijakan-shopeepay.txt` | Kebijakan privasi ShopeePay | https://shopeepay.co.id/privacy |
| `kebijakan-dana.txt` | Kebijakan DANA; unduhan otomatis sempat gagal (timeout) | https://www.dana.id/policy |

Total sekitar 211 chunk. Minimum modul adalah `5 + (K mod 4)` dokumen, jadi 5 dokumen
hanya cukup bila `K mod 4 = 0`; penambahan dijadwalkan di Minggu 9. Dokumen dipakai
sebagai rujukan akademik dan tidak didistribusikan ulang.

### 6.2 Keputusan chunking dan retrieval

| Keputusan | Nilai | Alasan | Yang dikorbankan |
|---|---|---|---|
| Pemecahan | Per heading untuk `.md`; ±150 kata + overlap 30 untuk teks | Satu bagian kebijakan ≈ satu gagasan utuh; overlap menjaga klausul di batas chunk | Pada teks panjang, batas topik bisa terpotong |
| Ukuran chunk | ±150 kata | Titik awal yang masuk akal | Belum dibandingkan dengan 75 atau 300 kata |
| Jumlah diambil | k = 5 | Cukup untuk pasal pendukung tanpa membanjiri konteks | k = 1 berisiko melewatkan pasal pendukung; k = 10 membawa chunk tak relevan (alasan desain, belum diuji sistematis) |
| Metadata | Nama dokumen + nomor bagian | Dasar rujukan [1], [2] yang dapat ditelusuri | — |

### 6.3 Ambang relevansi dan perilaku "tidak ditemukan"

Jarak yang dilaporkan adalah nilai `distances` dari ChromaDB: makin kecil makin mirip.
Ambang **0,65** hanya berlaku untuk metrik dan model embedding yang dipakai; bila salah
satunya diganti, ambang harus diukur ulang.

Dua lapis pertahanan:

1. **Kode:** bila tidak ada chunk yang lolos ambang, model **tidak dipanggil** dan sistem
   menjawab "Tidak ada di dokumen." Hemat biaya dan tidak bergantung pada kedisiplinan model.
2. **Instruksi RAG:** model diperintahkan menjawab hanya dari konteks, menyebut nomor
   konteks, dan menjawab "Tidak ada di dokumen." bila konteks tidak memuat jawaban.

**Mengapa ini keputusan etis, bukan hanya teknis.** Jawaban yang meyakinkan tetapi tidak
didukung dokumen dapat menyesatkan pengguna, terutama untuk topik hak dan pemrosesan data
pribadi. Sistem yang diam-diam menjawab dari pengetahuan umum sama dengan membohongi
pengguna. Pendekatan ini mengurangi risiko tetapi tidak menjamin semua jawaban yang
lolos retrieval benar; isinya tetap perlu dievaluasi.

**Batas yang diketahui.** Ukuran chunk belum dibandingkan dengan alternatif, dan
pertanyaan yang jawabannya tersebar di dua dokumen belum diuji menyeluruh. Konteks yang
saling bertentangan ditangani lewat instruksi RAG (sebutkan pertentangan, jangan memilih
diam-diam), tetapi belum diuji khusus.

## 7. Bukti sejauh ini

### 7.1 Satu keberhasilan

**Pertanyaan:** "Apa saja hak subjek data menurut UU PDP?" (k = 3).
Jawaban memuat 5 hak, semuanya dirujuk ke chunk [1]; hak penghapusan juga dirujuk ke
[3]. Chunk terbaik berjarak 0,43. Chunk [2] tidak relevan dan sengaja tidak dipakai
model ("Konteks yang dipakai: [1], [3]").

### 7.2 Satu kegagalan yang saya temukan sendiri

**Pertanyaan:** "Bagaimana prosedur migrasi server untuk menyimpan data pelanggan ke cloud?"
(topik yang tidak dibahas dokumen).

- **Dugaan saya sebelum mencoba:** sistem akan mengambil chunk "Masa Retensi" karena
  kemiripan kata "menyimpan data". **Dugaan itu salah.**
- **Yang terjadi:** sistem mengambil dua chunk lain yang sama-sama tidak relevan (jarak
  0,76 dan 0,78) dan tetap mengirimnya ke model. Jawaban akhir kebetulan benar
  ("Tidak ada di dokumen."), tetapi hanya karena model patuh pada instruksi.
- **Akar masalah:** pencarian vektor selalu mengembalikan k chunk terdekat berapa pun
  jaraknya, tanpa ambang. Saat itu sistem bergantung sepenuhnya pada kedisiplinan model.
- **Perbaikan:** ambang jarak 0,65 pada `vectorstore.py`, dan `/ask` langsung menjawab
  tanpa memanggil model bila tidak ada chunk yang lolos.
- **Uji ulang:** `sources` kosong, muncul catatan bahwa model tidak dipanggil.

Kasus "seharusnya tidak ada jawaban" lain: pertanyaan "Berapa anggaran tahunan lembaga
pengawas PDP?" dijawab "Tidak ada di dokumen." (jarak terdekat 0,69).

### 7.3 Contoh jarak

| Pertanyaan | Jarak terdekat | Keputusan (ambang 0,65) |
|---|---|---|
| Hak subjek data | 0,43 | Dipakai |
| Penanggung jawab keamanan | 0,50 | Dipakai |
| Simpan data selamanya | 0,52 | Dipakai |
| Anggaran lembaga pengawas | 0,69 | Dibuang |
| Migrasi server ke cloud | 0,76 | Dibuang |

Angka ini berasal dari pengukuran awal pada indeks kecil (ringkasan UU PDP + GoPay).
Pengukuran terbaru pada indeks 5 dokumen dicatat di
[logs/lapisan3_rag_cases.md](logs/lapisan3_rag_cases.md).

### 7.4 Kegagalan lain yang sudah terjadi

| Kejadian | Penyebab | Penanganan |
|---|---|---|
| Error 404 pada model | Model lama dipensiunkan untuk akun baru | Ganti ke model yang tersedia |
| Error 400 saat membangun indeks | Batas 100 teks per panggilan embedding | Dipecah per batch |
| Error 429 saat membangun indeks | Kuota gratis embedding 100 teks per menit | Jeda otomatis dan ulang di `embedder.py` |
| Unduhan DANA timeout | Kemungkinan situs memblokir permintaan otomatis (dugaan, belum dibuktikan) | Dicatat; diunduh ulang kemudian |
| Hasil ekstraksi tampil sebagai kode HTML | Bug indentasi HTML pada antarmuka | Diperbaiki; ditemukan saat uji lewat layar |

**Batas bukti.** Satu keberhasilan, satu kegagalan, dan beberapa pengukuran jarak belum
cukup untuk menyimpulkan akurasi umum Privia. Evaluasi dengan set uji berjawaban acuan
dijadwalkan di Minggu 14–15.

## 8. Risiko dan rencana Minggu 9–16

### 8.1 Risiko

| Risiko | Bukti atau keadaan | Mitigasi | Rencana |
|---|---|---|---|
| Ketergantungan pada layanan AI | Model dapat dihentikan (404), kuota terlampaui (429; ±20 permintaan/hari/model untuk ekstraksi pada tier gratis), pengambilan dari situs tertentu bisa gagal | Penanganan error, jeda otomatis, model termurah yang memadai | Uji alternatif; jurnal biaya |
| Keamanan dan keandalan | Prompt injection dari isi dokumen belum diuji; batas 20.000 karakter membuat sebagian dokumen tidak teranalisis | Isi dokumen diperlakukan sebagai data, bukan perintah; ambang jarak | Kasus uji injeksi di Lapisan 5; peringatan bila teks terpotong |
| Salah interpretasi | Pengguna bisa menganggap hasil sebagai keputusan kepatuhan | Tidak ada kesimpulan "patuh/melanggar"; tinjauan manusia | Pernyataan etis di Lapisan 5 |
| Jawaban tidak berdasar | Model bisa mengarang | Skema + kutipan bukti + `"tidak disebutkan"` + ambang jarak | Uji pada dokumen panjang |
| Indeks tidak lengkap | Indeks yang gagal dibangun menghasilkan jawaban salah sumber | Ambang jarak | Bangun ulang indeks sebagai langkah wajib; periksa keutuhan indeks |
| Konteks bertentangan antar dokumen | Dua kebijakan bisa berbeda | Instruksi RAG: sebutkan pertentangan | Uji khusus; pertimbangkan keragaman sumber |

### 8.2 Rencana

| Waktu | Fokus | Kegiatan |
|---|---|---|
| Minggu 9 | Perbaikan dasar | Peer review; tambah dokumen hingga minimum K; uji v2 pada dokumen panjang; tetapkan temperature |
| Minggu 10–13 | Pengembangan agentic | Tool sesuai K, batas jumlah langkah, persetujuan manusia sebelum menyimpan hasil akhir |
| Minggu 14–15 | Pengujian terukur | Minimal 12 + (K mod 6) pertanyaan uji beserta jawaban acuan; laporan hasil numerik |
| Minggu 16 | Evaluasi akhir | Estimasi biaya untuk 100 pengguna, kajian risiko, pernyataan etis penggunaan |

**Angka minimum menurut K** (K = [isi]):

| Unsur | Rumus | Nilai |
|---|---|---|
| Dokumen rujukan | 5 + (K mod 4) | [hitung] |
| Kasus uji | 12 + (K mod 6) | [hitung] |
| Tool | 2 + (K mod 2) | [hitung] |
| Mode keluaran ringkas | Wajib bila K genap | Belum dibangun |

## 9. Catatan proses dan penggunaan AI

**Bagian yang dibuat dengan bantuan AI.** Kode, instruksi sistem, dan draf dokumen disusun
dengan bantuan asisten AI (Claude). Saya menjalankan, menguji, dan memeriksa setiap bagian
sendiri.

**Cara memverifikasi.** Menjalankan endpoint lewat `/docs`; mencocokkan keluaran dengan
dokumen sumber; mencatat kasus berhasil dan gagal di `logs/`; memeriksa berkas satu per
satu di komputer sendiri sebelum menyimpulkan perbaikan berhasil.

**Hal yang diberikan AI dan ternyata salah.**

- Kode awal memakai model yang ternyata sudah tidak tersedia untuk akun baru (404).
- Prediksi bahwa pertanyaan migrasi server akan mengambil chunk "Masa Retensi" (bab 7.2).
- Antarmuka sempat menampilkan HTML mentah karena indentasi (bab 7.4).

