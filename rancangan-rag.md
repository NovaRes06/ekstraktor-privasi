# Rancangan RAG 

Deliverable **BUILD Minggu 7**: rancangan alur RAG untuk kasus ini, dengan setiap
keputusan disertai alasan. Sistemnya sendiri sudah berjalan (Minggu 9 ke depan);
dokumen ini mengonsolidasi keputusan yang selama ini tersebar di kode dan catatan.

Alur yang diterapkan:

```
PENYIAPAN (sekali, atau tiap dokumen berubah)
  dokumen → chunk → embedding (gemini-embedding-001) → ChromaDB
SAAT MENJAWAB (tiap pertanyaan)
  pertanyaan → embedding → ambil k chunk terdekat
  → buang chunk dengan jarak > 0,65 → susun konteks bernomor
  → kirim ke gemini-3.6-flash dengan prompt tegas
  → jawaban + nomor konteks + daftar chunk sumber
```

## 1. Daftar dokumen rujukan

| File | Asal | Ukuran | Dapat dipakai? |
|---|---|---|---|
| kebijakan-ovo.txt | https://www.ovo.id/kebijakan-privasi | 102 chunk | Ya — dokumen publik resmi |
| kebijakan-shopeepay.txt | https://shopeepay.co.id/privacy | 49 chunk | Ya — dokumen publik resmi |
| kebijakan-gopay.txt | https://gopay.co.id/.../gopay-privacy-notice | 5 chunk | Ya — dokumen publik resmi |
| ringkasan-pasal-uu-pdp.md | UU PDP No. 27/2022 (privat) | 9 chunk | Ya — undang-undang publik |
| kebijakan-dana.txt | https://www.dana.id/policy | 46 chunk | Ya — berhasil diunduh 10 Okt 2026 setelah timeout 15s ditingkatkan ke 30s; total 211 chunk di index |

Semua asal tercatat di baris "Sumber:" awal tiap file.
Semua dokumen publik dan boleh dipakai sebagai bahan rujukan.

## 2. Enam keputusan desain dan alasannya

| # | Keputusan | Nilai yang dipilih | Alasan |
|---|---|---|---|
| 1 | Ukuran chunk | 150 kata ± teks polos; per-heading untuk .md terstruktur | Satu bagian kebijakan biasanya 1 gagasan utuh; potongan 150 kata cukup memuat klausul + sedikit konteksnya, dan tidak perlu menghitung token persisnya |
| 2 | Overlap | 30 kata | Klausul yang terpotong di batas chunk tetap utuh di salah satu sisi — diuji di `tests/test_chunker.py::test_overlap_benar_benar_terpotong` |
| 3 | Jumlah chunk diambil (N) | default k=5, dapat diubah 1–50 per request | Pertanyaan tersebar dua dokumen butuh >3 chunk; k kecil membuat konteks mubazir. Bisa diatur pemanggil (slider UI) |
| 4 | Batas minimum kemiripan | MAX_RELEVANT_DISTANCE = 0.65 (jarak cosine, makin kecil makin mirip) | Diukur langsung 10 Okt 2026: relevan 0.42–0.49, tidak relevan 0.76–0.80 (lihat `logs/lapisan3_rag_cases.md`). 0.65 berada di tengah rentang, margin ±0.16 |
| 5 | Apa yang disertakan bersama chunk | Nama file sumber + index chunk + teks | Jawaban memakai rujukan [1][2]; pengguna bisa menelusuri ke dokumen asli |
| 6 | Perilaku kalau tidak ditemukan | Menolak: jawab persis "Tidak ada di dokumen." | Keputusan etika sesuai modul: sistem yang diam-diam menjawab dari pengetahuan umum sama dengan membohongi pengguna yang mengira jawaban dari dokumen. Implementasinya dua lapis: (a) kalau 0 chunk lolos ambang, endpoint `/ask` tidak panggil model sama sekali; (b) prompt RAG memerintahkan jawab persis "Tidak ada di dokumen." |

## 3. Bentuk konteks yang dikirim ke model

Contoh nyata (perfeks: dipotong supaya muat):

```
KONTEKS:
[1] (sumber: kebijakan-ovo.txt, bagian 62)
Data kami disimpan selama Anda masih menggunakan layanan dan/atau sampai Anda
meminta penghapusan. Setelah itu data dihapus atau dianonimkan sesuai ketentuan
perundang-undangan...

[2] (sumber: ringkasan-pasal-uu-pdp.md, bagian 7)
Subjek data berhak mengakuisisi, memperbaiki, dan menghapus data pribadinya...

PERTANYAAN: Berapa lama OVO menyimpan data pribadi pengguna?
```

## 4. System prompt versi RAG

Ada di [prompts/system_prompt_rag_v1.md](prompts/system_prompt_rag_v1.md).
Aturan intinya, sesuai modul Minggu 7: kalau tidak ada di sumber, katakan tidak
ada; semua klaim disertai nomor konteks; bertentangan → sebutkan pertentangan,
jangan memilih diam-diam.

## 5. Sepuluh pertanyaan uji

Komposisi sesuai modul: 6 yang jawabannya ada, 2 yang tersebar di dua dokumen,
2 yang jawabannya tidak ada. Untuk pertanyaan tersebar dan tidak-ada, jawaban
benarnya ditulis dulu manual (dibaca dokumen, bukan dari ingatan model).

### Tipe A — jawaban ada di satu dokumen (6)

| # | Pertanyaan | Jawaban diharapkan (dicek manual) |
|---|---|---|
| A1 | Berapa lama OVO menyimpan data pribadi pengguna? | Retensi OVO: selama akun aktif / sesuai hukum (chunk `kebijakan-ovo.txt` tentang retensi) |
| A2 | Bagaimana ShopeePay membagikan data pengguna ke pihak ketiga? | ShopeePay berbagi dengan afiliasi/mitra/otoritas sesuai kebijakan bersama |
| A3 | Apa saja hak subjek data menurut UU PDP? | Hak akses, perbaikan, penghapusan, penarikan persetujuan, dll (ringkasan pasal UU PDP) |
| A4 | Data apa saja yang dikumpulkan GoPay? | Identitas, kontak, data transaksi, data perangkat (dari kebijakan gopay) |
| A5 | Bagaimana OVO melindungi data pengguna? | Enkripsi, kontrol akses, audit keamanan (kebijakan OVO bagian keamanan) |
| A6 | Apakah UU PDP mengatur transfer data ke luar negeri? | Ya, pasal tentang transfer luar negeri (butuh perlindungan setara) |

### Tipe B — jawaban tersebar di dua dokumen (2)

| # | Pertanyaan | Dokumen yang harus terambil |
|---|---|---|
| B1 | Bagaimana ketentuan hak subjek data di UU PDP dan bagaimana OVO memfasilitasinya? | `ringkasan-pasal-uu-pdp.md` + `kebijakan-ovo.txt` |
| B2 | Apakah kebijakan ShopeePay sejalan dengan ketentuan pembatasan pemrosesan pada UU PDP? | `kebijakan-shopeepay.txt` + `ringkasan-pasal-uu-pdp.md` |

### Tipe C — jawaban tidak ada di mana pun (2)

| # | Pertanyaan | Catatan |
|---|---|---|
| C1 | Berapa biaya langganan bulanan Privia Pro? | Produk pribadi mahasiswa, tidak akan ada di dokumen apa pun |
| C2 | Apa menu makanan siang yang disajikan di kantin kampus? | Konteks jauh; harus dijawab "Tidak ada di dokumen" / ditolak |

## 6. Bentuk output (field rujukan sumber wajib)

```
Jawaban: <isi jawaban, dengan rujukan [1][2] dst inline>

Konteks yang dipakai: <daftar nomor konteks yang benar-benar dipakai>
```

Ditambah dari API: `sources` (daftar chunk lengkap dengan nama file, index
chunk, dan **jarak** — makin kecil makin mirip).

--- ## 7. Perilaku penolakan (poin 6 keputusan desain) — sudah terbukti berjalan

Diverifikasi 10 Okt 2026 lewat endpoint `/ask`:
- Pertanyaan C1 akan mengembalikan jawaban berupa "Tidak ada di dokumen." beserta
  `sources: []` (tidak memanggil model, tidak konsumsi token).
- Pertanyaan A1/A2 menghasilkan jawaban berasal dari chunk `kebijakan-ovo.txt` /
  `kebijakan-shopeepay.txt` dengan jarak 0.42–0.49.

Baseline keduanya akan dijadikan bahan perbandingan Minggu 14 sesuai modul
Minggu 9.

## Tantangan wajib Minggu 7 — mengapa k=3 saja mungkin tidak cukup

Untuk pertanyaan tersebar (B1/B2), hanya mengambil 3 chunk teratas bisa gagal
karena:

1. **Distribusi jarak antar dokumen.** Chunk relevan dari dokumen kedua bisa jadi
   lebih jauh dari chunk tidak-relevan dokumen pertama — misalnya kebijakan OVO
   bagian keamanan mungkin 0.48, sedangkan UU PDP pasal hak subjek bisa 0.55.
   Jika k=3 sempit, yang ke-3 bisa saja 3 chunk dari dokumen pertama, dan
   potongan UU PDP yang dibutuhkan tidak pernah terkirim.
2. **Pengulangan topik.** Kebijakan privasi menyebut topik yang sama berulang
   (persetujuan muncul di 10+ tempat); 3 chunk teratas sering kali berisi
   dua-tiga chunk yang isinya nyaris sama, sehingga porsi konteks hampir kosong
   bagi dokumen kedua.

Dua cara mengatasinya, beserta biayanya:

| Cara | Biaya | Efek dapak |
|---|---|---|
| (a) Naikkan k (mis. 5–8) | Token masuk naik proporsional: +2–5 chunk × ±150 kata ≈ +1.000–1.800 token per query. Perkiraan biaya +$0.0008–0.0013 per question (tarif Flash $0.75/jt) | Paling murah dan sudah jadi: `k` dapat dikirim per request (slider UI) |
| (b) Filter keragaman sumber: pilih chunk teratas per dokumen (jangan semua dari satu file) | Tanpa biaya token; menambah logika k-simple di kode | Tidak selalu perlu — memaksa tiga chunk terdaftar jadi salah satu lapisan masing-masing dokumen — pertanyaan tunggal bisa kelewat kalau terlalu dipaksa |
