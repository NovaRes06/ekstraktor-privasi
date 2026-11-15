# KAJIAN RISIKO — Privia

> **Status: draf awal, belum dikumpulkan.** Ini luaran Minggu 15; target progres repo
> saat ini adalah Minggu 13.

Nama / NIM / K : Nova Reswara / 10241058 / K = 5 (minimum 6 dokumen, 17 kasus, 3 tool; tersedia 8/18/4)
Tanggal        : 2 November 2026

---

## 1. Risiko keamanan

| Risiko | Wujudnya pada produk saya | Diuji? | Hasil uji | Mitigasi | Di lapis mana |
|---|---|---|---|---|---|
| Prompt injection lewat input pengguna | Tugas agent berisi "abaikan instruksi sebelumnya" | Ya (uji #1, #3) | Ditolak HTTP 422 sebelum model dipanggil | `input_filter.py` menolak pola kasar + membatasi panjang | 1 |
| Prompt injection lewat dokumen rujukan | Kebijakan yang diunduh memuat kalimat perintah | Tidak langsung | Kuota habis saat uji; bukti pengganti kasus P01: semua field "tidak disebutkan" | Penanda dokumen, contoh kasus sulit di prompt v2, dan **cek bukti terhadap dokumen asli** | 1, 2, 4 |
| Kebocoran data ke penyedia model | Teks kebijakan/dokumen pengguna dikirim ke Gemini | Ya (uji otomatis) | NIK 16 digit, nomor kartu, nomor telepon ditolak HTTP 422 | `deteksi_data_pribadi` + penolakan sebelum panggilan model | 1 |
| Terungkapnya system prompt | Pengguna meminta isi instruksi sistem | Ya (uji #3) | Ditolak di lapis 1; lapis 4 juga memeriksa potongan 8 kata identik | Anggap prompt bukan rahasia: isinya memang ada di repo `instruksi/` | 1, 4 |
| Penyalahgunaan di luar maksud | Dipakai memutuskan "patuh/tidak patuh" atau jadi nasihat hukum | Ya (percobaan langsung) | Model menolak memberi putusan; lapis 4 menandai pola putusan | Batas peran di prompt + pemeriksaan output + pernyataan etis §7 | 2, 4 |
| Kredensial terbuka di repositori | **Ditemukan.** `.env` berisi `GEMINI_API_KEY` pernah ter-commit pada `f14616e "add: all file"`, lalu dihapus pada `67f45aa` | Ya (pemeriksaan riwayat) | Kunci masih tersimpan di riwayat git meskipun berkasnya sudah dihapus | `.env` masuk `.gitignore`, `.env.example` disediakan | 3 (di luar model) |

### Hasil pemeriksaan riwayat repositori atas kredensial

Perintah yang dijalankan: `git log --all --oneline -- .env` dan pemeriksaan isi
commit lama tanpa mencetak nilainya (hanya nama variabel dan panjang nilai).

- `f14616e` — `.env` ikut ter-commit; isinya satu baris `GEMINI_API_KEY` (53 karakter).
- `67f45aa` — `.env` dihapus dari pelacakan dan masuk `.gitignore`.
- Berkas `.env` **masih ada di riwayat**, sehingga siapa pun yang mengkloning repo
  bisa membacanya dengan `git show f14616e:.env`.

**Tindakan yang saya ambil dan yang belum:** kunci itu **harus dicabut (revoke) di
Google AI Studio dan diganti yang baru** — menghapus berkas dari commit terakhir
tidak menghapusnya dari riwayat. Saya belum mencabutnya karena itu tindakan pada akun
pribadi di luar repositori, dan saya belum menulis ulang riwayat git karena itu
operasi yang tidak bisa dibatalkan tanpa persetujuan pemilik repo. Keduanya
dicatat sebagai tugas yang masih terbuka, bukan sebagai "sudah aman".

## 2. Batas akses tool

| Tool | Boleh | Tidak boleh | Dipasang di mana | Butuh persetujuan manusia? |
|---|---|---|---|---|
| `cari_dokumen` | baca index, k 1–10 | menulis, jaringan | kode | tidak |
| `baca_dokumen` | 8 berkas `data/raw/`, ≤1.200 kata | `.env`, `SUMBER.md`, `../` | kode (daftar putih) | tidak |
| `ambil_field` | 9 field dari dokumen daftar putih | field/dokumen lain | kode | tidak |
| `simpan_laporan` | tulis `.md` di `logs/laporan-agent/` | folder lain, >20.000 karakter | kode | **ya** |

Baris yang penegakannya hanya di instruksi: **tidak ada**. Detail dan bukti uji ada
di `guardrails.md` §2.

## 3. Bias

| Pintu | Wujud konkret pada produk saya | Bukti | Yang saya lakukan |
|---|---|---|---|
| Dari model | Istilah hukum Indonesia kadang diterjemahkan ke Inggris: potongan OVO yang terambil berbahasa Inggris ("We need to retain and process Personal Data…") padahal dokumennya bilingual | `logs/hasil-evaluasi-v1.json` kasus U06 (sumber `kebijakan-ovo.txt#19`) | Dibiarkan, tetapi jawaban wajib menyebut nama dokumen; pengguna bisa memeriksa aslinya |
| Dari dokumen rujukan | 5 dari 8 dokumen berasal dari dompet digital besar; kebijakan perusahaan kecil, koperasi, atau lembaga publik tidak terwakili, sehingga "kebiasaan industri" yang terlihat sebenarnya kebiasaan segelintir pemain besar | `data/raw/SUMBER.md` | Dinyatakan sebagai keterbatasan di `laporan-evaluasi.md` §9; sistem tidak pernah menyimpulkan "industri pada umumnya" |
| Dari rancangan saya | Schema 9 field tidak punya kategori untuk **pemasaran/profiling** dan **data anak**. Kebijakan yang memuat keduanya akan dipaksa masuk ke `tujuan_pemrosesan` atau hilang sama sekali | Skema di `src/extraction/extractor.py` | Dicatat sebagai keterbatasan yang diketahui; usulan perbaikan ada di `laporan-evaluasi.md` §8, belum dikerjakan |

### Kasus yang tidak cocok ke satu pun kategori schema

Pertanyaan "apakah kebijakan ini memuat klausul tentang **data biometrik wajah**
untuk verifikasi (selfie)?" tidak punya field sendiri. Sistem memaksanya masuk ke
`jenis_data_dikumpulkan` (sebagai "data biometrik") atau `mekanisme_keamanan`
(kalau dikaitkan dengan verifikasi). Yang dirugikan bila ini berulang: pengguna yang
ingin tahu apakah wajahnya diproses — informasi paling sensitif justru tidak punya
rumah di schema, sehingga paling mudah terlewat.

## 4. Trace data

| Pertanyaan | Jawaban |
|---|---|
| Data apa yang masuk | Teks kebijakan privasi (publik), pertanyaan pengguna, tugas agent |
| Data apa yang dikirim ke penyedia model | Teks yang sama, dipotong (≤7.000 karakter untuk uji, ≤200.000 untuk API), plus potongan dokumen hasil retrieval |
| Data apa yang disimpan, di mana, berapa lama | `chroma_db/` (embedding + teks chunk, lokal), `logs/agent_state/` dan `logs/agent_trace/` (riwayat tugas), `logs/eval_cache/` (hasil uji). Tidak ada masa retensi otomatis; semuanya berkas lokal yang bisa dihapus manual |
| Siapa pemiliknya, dan apakah ia tahu | Pemilik dokumen: perusahaan penerbit kebijakan (dokumen publik). Pemilik pertanyaan: pengguna aplikasi; diberi tahu lewat catatan di UI bahwa hasil membantu meninjau, bukan menggantikan penilaian manusia |
| Apa yang terjadi pada data bila produk berhenti dipakai | Tidak ada server pusat; menghapus folder proyek menghapus seluruh data. Tidak ada salinan di pihak ketiga selain yang tersimpan di riwayat permintaan penyedia model |
| Data apa yang seharusnya TIDAK PERNAH masuk | Kebijakan internal yang memuat data pribadi orang sungguhan (NIK, nomor kartu, nomor telepon), dokumen rahasia perusahaan, kredensial |

**Mekanisme yang MENCEGAH baris terakhir masuk** (bukan sekadar harapan):
`src/guardrails/input_filter.py` menolak input yang memuat NIK/kartu/telepon dengan
HTTP 422 sebelum teks dikirim ke model; uji otomatisnya ada di
`tests/test_guardrails.py`. Yang belum dicegah: nama orang dan alamat (tidak bisa
dikenali dengan pola) — dicatat sebagai celah di `guardrails.md` §6.

## 5. Empat pertanyaan etis

1. **Siapa yang dirugikan bila sistem ini salah?** Pengguna dompet digital yang
   mengandalkan ringkasan keliru — misalnya mengira datanya tidak dibagikan ke pihak
   ketiga padahal dibagikan — lalu mengambil keputusan berdasarkan itu. Juga tim legal
   yang memakai hasil ekstraksi tanpa memeriksa buktinya.
2. **Apakah pengguna tahu ia berhadapan dengan sistem AI, dan bahwa jawabannya bisa
   keliru?** Ya, disebut di UI ("Hasil Privia membantu meninjau isi dokumen, bukan
   menggantikan penilaian manusia") dan setiap hasil menyertakan kutipan bukti serta
   daftar dokumen sumber. Yang tidak ada: peringatan khusus per jawaban.
3. **Data siapa yang diproses, dan apakah pemiliknya tahu?** Kebijakan privasi yang
   memang dipublikasikan perusahaan untuk dibaca publik; pertanyaan pengguna aplikasi
   ini. Tidak ada data pribadi orang sungguhan yang diproses.
4. **Untuk apa sistem ini tidak boleh dipakai?** Lihat pernyataan etis §7.

## 6. Risiko yang saya TERIMA tanpa mitigasi

| # | Risiko | Mengapa saya menerimanya | Apa yang akan mengubah keputusan ini |
|---|---|---|---|
| 1 | Kutipan bukti yang digabung dari dua bagian bisa lolos pemeriksaan kalau kebetulan berurutan | Pemeriksaan literal sudah menangkap 2 dari 17 kasus; pengecekan semantik butuh model kedua dan biaya tambahan yang tidak sepadan untuk proyek kelas | Kalau produk dipakai untuk audit kepatuhan sungguhan |
| 2 | System prompt bisa dibaca siapa pun dari repo | Prompt tidak memuat rahasia; menyembunyikannya hanya menciptakan rasa aman palsu | Kalau prompt memuat aturan bisnis rahasia |
| 3 | Tidak ada autentikasi pada API | Dijalankan lokal untuk satu pengguna | Kalau dipublikasikan ke internet |
| 4 | Data tersimpan tanpa masa retensi otomatis | Semua lokal dan kecil; menghapus folder = menghapus data | Kalau memproses data pribadi |

## 7. PERNYATAAN ETIS

### Produk ini dimaksudkan untuk

Mengekstrak sembilan aspek dari kebijakan privasi berbahasa Indonesia, menampilkan
kutipan bukti untuk setiap aspek, menjawab pertanyaan tentang isi delapan dokumen
rujukan yang tercatat asalnya, dan membandingkan ketentuan antar dokumen lewat agen
yang berhenti pada batas langkah yang ditetapkan.

### Produk ini TIDAK boleh dipakai untuk

1. Menyatakan suatu kebijakan "patuh" atau "tidak patuh" terhadap UU PDP. Sistem
   menolak mengeluarkan putusan itu; pemeriksaan `periksa_putusan_kepatuhan` akan
   memblokirnya.
2. Menjadi dasar tunggal keputusan hukum, sanksi, atau penilaian terhadap perusahaan.
3. Memproses dokumen yang memuat data pribadi orang sungguhan — input seperti itu
   ditolak dengan HTTP 422.
4. Membaca berkas di luar `data/raw/` — dibatasi di kode, bukan di prompt.

### Keputusan yang tidak boleh diserahkan kepada produk ini

Menentukan apakah perusahaan melanggar hukum; menilai risiko hukum suatu kontrak;
memutuskan apakah pengguna harus menuntut atau melaporkan; menyimpulkan niat
perusahaan di luar yang tertulis.

### Apa yang produk ini sampaikan kepada penggunanya tentang dirinya

Bahwa ia sistem AI berbasis model bahasa, bahwa hasilnya bisa salah, bahwa setiap
nilai sebaiknya diperiksa terhadap kutipan bukti yang ditampilkan, dan bahwa
ketiadaan informasi ditandai "tidak disebutkan" — bukan diisi dengan dugaan.

### Kapan produk ini tidak boleh dipercaya

Privia hanya membaca apa yang tertulis di dokumen yang diberikan, dan hanya delapan
dokumen yang saya siapkan. Kalau Anda bertanya tentang aplikasi lain, tentang aturan
yang berlaku hari ini, atau tentang apa yang **tidak** ditulis perusahaan, jawabannya
tidak bisa diandalkan — termasuk ketika sistem terdengar yakin. Sistem ini juga bisa
menolak menjawab padahal jawabannya ada (tercatat pada satu dari tujuh belas kasus
uji), dan bisa mengutip kalimat yang sebenarnya disusun dari dua bagian berbeda.
Jangan pakai hasilnya sebagai nasihat hukum. Kalau jawabannya penting, buka dokumen
aslinya lewat kutipan yang ditampilkan dan periksa sendiri.
