# LAPORAN EVALUASI — PRIVIA

> **Status: draf awal, belum dikumpulkan.** Ini luaran Minggu 14; target progres repo
> saat ini adalah Minggu 13. Angka di bawah berasal dari run 2 November 2026 dan belum
> menjadi klaim akhir sampai set uji dijalankan ulang pada minggunya.

Nama / NIM / K : Nova Reswara / 10241058 / K = 5 (minimum 6 dokumen, 17 kasus, 3 tool; tersedia 8/18/4)
Tanggal        : 2 November 2026
Versi produk yang dievaluasi : ekstraksi v2 (prompt `instruksi/v2.md`), RAG v1, agen agent-v1

---

## 1. Apa yang diukur dan apa yang tidak

**Yang diukur laporan ini:** apakah sistem menjawab pertanyaan yang benar-benar
diajukan, apakah setiap pernyataan punya bukti yang bisa dicocokkan ke dokumen asli,
apakah formatnya sesuai schema, apakah ia menolak ketika seharusnya menolak, berapa
biayanya per permintaan, dan berapa biaya terburuk ketika agen mencapai batas langkah.

**Yang TIDAK diukur, dan mengapa:**
- **Kegunaan bagi pengguna sungguhan.** Tidak ada pengguna nyata yang diuji; tidak
  ada uji kegunaan atau waktu penyelesaian tugas.
- **Kebenaran hukum.** Tidak ada ahli hukum yang memeriksa apakah ringkasan setara
  dengan isi pasal.
- **Variance antar-percobaan pada model yang sama** (lihat §4) — kuota harian model
  gratis 20 permintaan habis sebelum percobaan kedua bisa dijalankan.
- **Dokumen di luar 8 berkas** — tidak ada klaim bahwa sistem bekerja pada kebijakan
  perusahaan lain.

**Pengguna sasaran:** pengguna dompet digital yang ingin memahami kebijakan privasi
tanpa membaca belasan halaman, dan tim legal/kepatuhan yang perlu memeriksa banyak
kebijakan dengan cepat lalu memeriksa sendiri bagian yang penting.

## 2. Set uji

Jumlah kasus: **18** (minimum menurut `12 + (K mod 6)` adalah 12–17, jadi 18
memenuhi untuk K berapa pun). Berkas: `set-uji/kasus.jsonl`, penjelasan:
`set-uji/README.md`.

| Jenis | Jumlah | Porsi | Dari mana asalnya |
|---|---:|---:|---|
| Kasus khas | 8 | 44% | Potongan 4 kebijakan dompet digital + RAG + 1 tugas agen |
| Kasus batas | 4 | 22% | Dokumen dengan 4 kategori retensi berbeda, dokumen nyaris kosong, GoPay yang memang tidak memuat retensi, pertanyaan yang jawabannya tidak ada |
| Kasus yang harus ditolak | 3 | 17% | Resep nasi goreng, cuaca Bandung, dokumen non-kebijakan |
| Kasus yang pernah gagal | 3 | 17% | Diambil dari `logs/failed_cases.md` dan `logs/lapisan3_rag_cases.md`: injeksi di dokumen, halusinasi "selama akun aktif", retrieval UU PDP yang salah sasaran |

**Siapa yang menyusun jawaban acuan:** saya sendiri, dengan membaca dokumen aslinya.
Dua acuan **direvisi setelah evaluasi** dan revisinya ditulis terbuka di `catatan`
kasus masing-masing (U01: potongan dokumen yang dipakai tidak memuat pernyataan
lintas negara; P02: kalimat "Dengan menggunakan layanan ini, Anda menyetujui…"
memang dasar persetujuan, jadi mengisinya benar). P06/U06 dan B04 juga diubah
menjadi "harus menolak" setelah dokumen diperiksa ulang. Revisi ini adalah bagian
dari kalibrasi, bukan penyesuaian supaya lulus: arahnya justru membuat dua kasus
lebih sulit dinilai.

## 3. Kriteria penilaian

| # | Pertanyaan biner | Bagaimana kasus batas diputuskan |
|---|---|---|
| 1 | Menjawab pertanyaan yang benar-benar diajukan | Untuk ekstraksi: semua field acuan terpenuhi (atau tepat "tidak disebutkan"). Untuk RAG: dokumen yang benar muncul di sumber **dan** kata kunci jawaban ada; untuk kasus tolak: jawaban persis "tidak ada di dokumen" |
| 2 | Seluruh pernyataan didukung sumber yang dirujuk | Ekstraksi: setiap `bukti_*` ditemukan apa adanya di dokumen (setelah normalisasi spasi) dan ≤2 kalimat. RAG: jawaban menyebut `[n]` yang valid. Penolakan otomatis lulus karena tidak memuat klaim |
| 3 | Tidak ada pernyataan tambahan tanpa dasar | Ekstraksi: field yang seharusnya "tidak disebutkan" tidak diisi. RAG: **tidak dinilai otomatis** (ditandai `manual`) |
| 4 | Format output valid menurut schema | Ekstraksi: 18 key wajib lengkap. RAG/agen: kunci `answer`+`sources` / `status` ada |
| 5 | Menolak dengan benar bila memang seharusnya menolak | Hanya berlaku untuk kasus jenis "tolak" dan kasus RAG yang acuannya menolak |

**Penilai:** saya sendiri untuk pemeriksaan bukti, ditambah skrip otomatis untuk
kriteria yang bisa diperiksa mesin (`src/eval/jalankan_set_uji.py`). Tidak memakai
model sebagai penilai, jadi tidak ada kalibrasi penilai model — tetapi ada kalibrasi
**skrip vs penilaian manual**:

```
Jumlah kasus yang saya nilai sendiri secara manual : 6 dari 17 (35%)
Jumlah yang penilaiannya SAMA dengan skrip         : 6
Tingkat kesesuaian                                 : 100%
Kesimpulan: pada 6 kasus itu skrip dan saya sepakat. Keterbatasan yang harus
disebut: saya yang menulis kriteria sekaligus yang menilai, jadi kesesuaian 100%
tidak membuktikan kriteria ini bisa dipakai orang lain. Uji sebenarnya adalah
orang lain memakai kriteria yang sama.
```

## 4. Hasil

Dijalankan dengan `gemini-3.6-flash`, 17 kasus (kasus agen A01 dijalankan terpisah
dengan `gemini-3.5-flash-lite` karena kuota flash habis — hasilnya di bawah tabel).

| Kriteria | Lulus | Dari | Persen |
|---|---:|---:|---:|
| 1. Menjawab yang diajukan | 16 | 17 | 94% |
| 2. Didukung sumber | 15 | 17 | 88% |
| 3. Tanpa tambahan tanpa dasar | 11 | 11 | 100% (hanya yang bisa dinilai otomatis) |
| 4. Format valid | 17 | 17 | 100% |
| 5. Menolak dengan benar | 5 | 5 | 100% |

Per jenis kasus:

| Jenis | Lulus seluruh kriteria | Dari | Persen |
|---|---:|---:|---:|
| Khas | 4 | 7 | 57% |
| Batas | 4 | 4 | 100% |
| Harus ditolak | 3 | 3 | 100% |
| Pernah gagal | 3 | 3 | 100% |
| **Total** | **14** | **17** | **82%** |

Kasus agen (A01, `gemini-3.5-flash-lite`): **lulus** semua kriteria yang berlaku,
selesai dalam **3 langkah** (cari dokumen → ambil field OVO → ambil field ShopeePay),
2.244 token masuk/506 keluar setara **$0,00535**. Bukti: `logs/hasil-evaluasi-lite.json`
dan `logs/agent_trace/5a9065eaec60.jsonl`.

**Variance antar-percobaan:** set uji dijalankan **satu kali** pada model flash, jadi
angka di atas **belum punya variance terukur**. Re-run pada model yang sama tidak
bisa dijalankan hari itu (kuota 20 permintaan/hari habis). Yang ada sebagai
pembanding adalah run model berbeda pada 5 kasus yang sama (§7); hasilnya 3/5 lulus
vs 4/5 pada flash. Artinya: angka 82% harus dibaca sebagai satu pengukuran, bukan
rata-rata.

## 5. Perbandingan terhadap baseline Minggu 9

Baseline Minggu 9 diukur pada tingkat **retrieval** (apakah chunk yang benar
terambil), bukan tingkat jawaban. Perbandingannya karena itu bukan apel ke apel, dan
itu sendiri temuan:

| Ukuran | Minggu 9 (retrieval) | Sekarang (jawaban) | Selisih |
|---|---:|---:|---:|
| Pertanyaan yang jawabannya ada, dijawab benar | 3 dari 3 (chunk dokumen benar terambil) | 5 dari 6 kasus RAG berjawaban (U07 gagal) | −1 kasus, pada ukuran yang lebih ketat |
| Pertanyaan yang jawabannya tidak ada, ditolak dengan benar | 3 dari 3 | 5 dari 5 (T02, T03, U06, B04 + P01) | sama |

**Penyebab perubahan:** retrieval yang benar tidak menjamin jawaban yang benar. Pada
U07, chunk dari `kebijakan-shopeepay.txt` memang terambil, tetapi yang terambil
bagian umum, bukan bagian pengungkapan (pasal 9), sehingga model menolak. Di Minggu 9
hal ini tidak terlihat karena yang diperiksa hanya "dokumen sumber benar".

## 6. Kegagalan yang tersisa

| # | Kasus | Gagal di kriteria | Diagnosis | Mengapa belum diperbaiki |
|---|---|---|---|---|
| 1 | U01 (Tokopedia) | 2 — bukti | Dua kutipan bukti tidak ditemukan apa adanya di dokumen: model menyusunnya dari beberapa bagian yang berdekatan | Perbaikan menyeluruh butuh Pemeriksa bukti yang lebih pintar (mis. pencocokan fuzzy) atau prompt yang melarang menyambung kutipan; keduanya perlu diuji ulang pada seluruh set |
| 2 | U03 (OVO) | 2 — bukti | Sama: `bukti_pihak_ketiga_penerima` menyambung dua butir daftar yang tidak berurutan | idem |
| 3 | U07 (ShopeePay) | 1 — menjawab | Retrieval mengambil bagian umum ShopeePay + satu chunk Tokopedia; pasal 9 tentang pengungkapan tidak masuk 5 teratas | Butuh retrieval hybrid (kata kunci + vektor) atau k besar; belum dikerjakan karena mengubah perilaku seluruh RAG dan harus dievaluasi ulang |

**Pola:** ketiga kegagalan bukan "model bodoh", melainkan **pemotongan dokumen**.
Dua soal kutipan yang disambung (chunk terlalu kecil untuk memuat satu butir utuh),
satu soal bagian yang tidak terambil karena kemiripan makna mengalahkan kecocokan
kata kunci. Arah perbaikan yang paling masuk akal karena itu ada di chunking dan
retrieval, bukan di prompt.

## 7. Biaya

Tarif promo Gemini 3.6 Flash (dipakai konsisten di `catatan-pemakaian.md`):
$0,75/juta token masuk, $3,75/juta token keluar.

| Ukuran | Angka | Cara menghitungnya |
|---|---:|---|
| Biaya per permintaan khas (ekstraksi) | **$0,00358** (≈Rp 59) | Rata-rata 11 kasus ekstraksi: 2.244 token masuk, 506 keluar |
| Biaya per permintaan khas (RAG) | ≈$0,0023 (perkiraan) | Konteks 5 chunk (~2.500 token masuk) + ~100 token keluar. **Perkiraan**, karena `/ask` belum mengembalikan `usage` |
| Biaya per permintaan TERBURUK (agen mencapai batas) | **$0,0077 terukur pada 4 langkah**; ≈$0,017 ekstrapolasi 8 langkah | `logs/agent_state/5491246a0545.json` (8.044 masuk / 455 keluar). Ekstrapolasi linear dari 1–4 langkah (885→8.044 token masuk) |
| Biaya 100 pengguna × 20 permintaan/bulan | **$7,16** (≈Rp 118.000) untuk ekstraksi; **$34** kalau semuanya kasus agen terburuk | 2.000 × $0,00358; 2.000 × $0,017 |

**Bagian yang paling menyumbang biaya:** panjang dokumen yang dikirim ke model. Pada
ekstraksi, token masuk 4,4× token keluar, dan satu dokumen 7.000 karakter saja sudah
~3.000 token. Agen lebih mahal lagi karena setiap langkah mengirim ulang riwayat:
langkah ke-4 sudah membawa 8.044 token masuk.

**Penghematan yang saya terapkan:**

| Cara | Penghematan | Angka evaluasi sebelum | Sesudah | Kualitas turun? |
|---|---:|---:|---:|---|
| Cache hasil per (kasus, model, input) di `logs/eval_cache/` | **100%** pada permintaan berulang dengan input identik | 17 kasus = ~$0,06 dan 17 permintaan | 0 permintaan, $0 pada run ulang | **Tidak** — hasil yang dipakai persis sama; skor dihitung ulang dari output yang sama dan angkanya identik |
| Mode ringkas (proyeksi 4 field dari hasil penuh) | 0 panggilan model tambahan (bukan penghematan token, tetapi mencegah alternatif "panggilan kedua untuk meringkas" yang akan +100% biaya) | — | — | Tidak ada perubahan, karena output penuh yang sama |
| Model murah `gemini-3.5-flash-lite` (≈42% lebih murah) | 42% per permintaan | 4 dari 5 kasus lulus (flash) | 3 dari 5 lulus (lite) | **YA — ditolak.** Kasus B01 gagal di kriteria 2 pada lite |

**Kesimpulan penghematan (tantangan wajib):** penghematan ≥30% **tanpa** penurunan
kualitas tercapai lewat **cache**, yang berlaku untuk permintaan berulang, bukan
untuk permintaan pertama. Jalur "ganti ke model termurah" yang akan menghemat 42%
per permintaan **tidak** saya terapkan karena pada 5 kasus yang diuji kualitasnya
turun (4/5 → 3/5). Ini contoh persis dari peringatan modul: hemat biaya tapi
kualitas turun bukan penghematan.

## 8. Perbaikan yang diusulkan

| # | Perbaikan | Bukti yang mendasari | Perkiraan dampak | Biaya menerapkannya |
|---|---|---|---|---|
| 1 | Perbesar chunk (150 → ±300 kata) atau tambah overlap pada batas butir daftar | 2 dari 3 kegagalan (U01, U03) berasal dari kutipan yang disambung antar-butir | Bisa menaikkan kriteria 2 dari 88% ke ~100% pada set ini | Perlu index ulang (295 chunk → ~180) + jalankan ulang set uji (~17 permintaan) |
| 2 | Retrieval hybrid: gabungkan skor vektor dengan pencocokan kata kunci judul pasal | U07: pasal 9 tidak terambil karena kemiripan makna kalah dari bagian umum | Menutup kelas kegagalan "dokumen benar, bagian salah" | Implementasi + evaluasi ulang; menambah latensi |
| 3 | Kembalikan `usage` pada `/ask` supaya biaya RAG terukur, bukan diperkirakan | §7: satu-satunya angka yang masih perkiraan | Laporan biaya jadi lengkap tanpa estimasi | Kecil (mengubah satu respons API) |

## 9. Keterbatasan laporan ini

Tiga hal yang membuat angka di atas **tidak boleh digeneralisasi:**

1. **18 kasus, satu penilai, satu kali jalan.** Tanpa run kedua, 82% belum punya
   variance; tanpa penilai independen, kriterianya belum terbukti bisa dipakai orang
   lain.
2. **Korpusnya delapan dokumen yang saya pilih sendiri,** dan lima di antaranya
   dompet digital besar. Kebijakan perusahaan kecil atau lembaga publik bisa punya
   struktur yang sama sekali berbeda.
3. **Sebagian pengukuran bergantung kuota gratis 20 permintaan/hari.** Kasus agen
   akhirnya dijalankan dengan model berbeda, dan dua uji serangan tidak teruji.
   Perbedaan model itu ikut memengaruhi angka kasus A01.

**Yang perlu diketahui calon pengguna sebelum mempercayai angkanya:** 14 dari 17
lulus terdengar baik, tetapi yang diuji adalah ekstraksi potongan dokumen dan
pertanyaan yang saya susun. Sistem pernah memberi kutipan bukti yang tidak persis
ada di dokumen (2 kasus) dan pernah menolak padahal jawabannya ada (1 kasus). Periksa
kutipannya.
