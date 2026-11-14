# Catatan Pemakaian Model
## 1. Aturan pencatatan

1. **Token** diambil dari `usage_metadata` respons (`prompt_token_count` /
   `candidates_token_count`) bila tersedia. Angka bertanda **±** adalah perkiraan
   (dihitung dari jumlah karakter/teks saat metadata tidak tersimpan) dan **tidak
   boleh dipakai sebagai angka pasti** di laporan akhir.
2. **Biaya** adalah **biaya setara bila memakai API berbayar**. Pemakaian sebenarnya
   lewat free tier, sehingga **rupiah yang benar-benar keluar Rp 0**. Kolom biaya tetap
   diisi supaya kebiasaan menghitung terbentuk dan proyeksi bisa dibuat.
3. **Satu baris = satu kegiatan**, bukan satu panggilan. Kegiatan yang terdiri dari
   beberapa panggilan (mis. uji 5 kasus) dicatat totalnya, dan jumlah panggilannya
   disebut di kolom kegiatan.
4. **Kegagalan tetap dicatat** (mis. 429 kuota habis): panggilan yang gagal tidak
   menghasilkan token keluaran, tetapi tetap menunjukkan biaya kuota yang terpakai.

---

## 2. Tarif yang dipakai

| Model | Tarif masukan | Tarif keluaran | Dasar |
|---|---|---|---|
| `gemini-3.6-flash` | $0,75 / juta token | $3,75 / juta token | Harga promo (berlaku s.d. 31 Des 2026), dicek 6 Sep 2026 |
| `gemini-3.6-flash` (mulai 1 Jan 2027) | $1,50 / juta token | $7,50 / juta token | Harga normal — **2× lipat**, penting untuk proyeksi jangka panjang |
| `gemini-3.5-flash-lite` | $0,30 / juta token | $2,50 / juta token | Tarif efektif yang **membuat angka terukur cocok**: 661 × $0,30 + 252 × $2,50 = $0,000828. Bukan kutipan halaman harga — perlu dicek ulang bila dipakai untuk keputusan uang |
| `gemini-embedding-001` | gratis di free tier | — | 295 chunk (±120.000 token) tidak menambah biaya; tarif berbayarnya belum pernah dipakai di proyek ini sehingga tidak dihitung |

**Dua konvensi yang dipakai di berkas ini — jangan dicampur:**

1. **Buku besar (§3) memakai tarif `gemini-3.6-flash` untuk semua model**, termasuk
   baris yang modelnya Flash-Lite. Tujuannya agar angka antar minggu bisa dibandingkan
   (aturan ini tertulis di `docs/catatan-proses.md`). Konsekuensinya: hitungan agen di
   §3 **lebih mahal dari yang sebenarnya** bila memakai Flash-Lite — mis. trace 3 langkah
   $0,005351 di §3 menjadi $0,002517 dengan tarif Flash-Lite.
2. **Tabel perbandingan model (§4.1) memakai tarif model masing-masing**, karena justru
   perbedaan tarif itulah yang sedang diukur.

Angka yang bertanda **±** dibulatkan ke dua angka penting saat dicatat, jadi menghitung
ulang bisa berbeda di digit terakhir (mis. ±8.900 masuk / ±2.000 keluar menghasilkan
$0,014175 dan dicatat ±$0,0142). Itu pembulatan, bukan kesalahan hitung.

Rumus yang dipakai di seluruh berkas:

```
Biaya = (token_masuk ÷ 1.000.000 × tarif_masuk) + (token_keluar ÷ 1.000.000 × tarif_keluar)
```

Kurs kasar yang dipakai untuk kolom rupiah: **Rp 16.500 / USD**.

---

## 3. Buku besar pemakaian (Minggu 1–16)

| Minggu | Tanggal | Kegiatan | Model | Token masuk | Token keluar | Biaya setara |
|---|---|---|---|---|---|---|
| 1 | 2026-09-05 | Ekstraksi pertama: kebijakan privasi BAYARKU (versi ringkas) via `/extract` | gemini-3.6-flash | 500 | 220 | $0,0012 |
| 1 | 2026-09-05 | BREAK #1–#4: 6 panggilan percobaan awal | gemini-3.5-flash-lite | 137 | 3.469 | $0,013111 |
| 2 | 2026-09-12 | Perbandingan 3 model pada input identik (Pro gagal, tidak menghasilkan token) | Flash-Lite + Flash | 1.322 | 501 | $0,002259 |
| 3 | 2026-09-19 | Baseline ekstraksi pertama + uji koneksi | gemini-3.6-flash | ±2.000 | ±500 | ±$0,0034 |
| 4 | 2026-10-10 | Uji prompt v1 vs v2: 4 panggilan sukses, sisanya 429 | gemini-3.6-flash | ±8.900 | ±2.000 | ±$0,0142 |
| 5 | 2026-10-17 | Uji schema & validasi (retry, kasus pelanggaran) | gemini-3.6-flash | ±4.500 | ±1.000 | ±$0,0071 |
| 6 | 2026-10-24 | Uji `fetch_url` + ekstraksi dari URL | gemini-3.6-flash | ±3.000 | ±700 | ±$0,0049 |
| 7 | 2026-10-31 | Embedding uji coba (di luar tarif Flash) | gemini-embedding-001 | ±20.000 | — | gratis di free tier |
| 8 | 2026-11-02 | UTS: tidak ada panggilan model (dokumen saja) | — | 0 | 0 | $0 |
| 9 | 2026-10-10 → 11-02 | Enam kasus RAG (`/ask`) | gemini-3.6-flash | ±15.000 | ±600 | ±$0,0134 |
| 9 | 2026-10-10 → 11-02 | Embedding 295 chunk untuk indeks | gemini-embedding-001 | ±120.000 | — | gratis di free tier |
| 10 | 2026-11-02 | Trace agen 3 langkah | gemini-3.5-flash-lite | 5.255 | 376 | $0,005351 |
| 10 | 2026-11-02 | Trace batas 1 langkah (berhenti sesuai batas) | gemini-3.5-flash-lite | 885 | 84 | $0,000979 |
| 11 | 2026-11-02 | Trace agen 4 langkah (ShopeePay) | gemini-3.5-flash-lite | 8.044 | 455 | $0,007739 |
| 11 | 2026-11-02 | Trace 4 langkah + persetujuan manusia | gemini-3.5-flash-lite | 5.753 | 530 | $0,006302 |
| 12 | 2026-11-02 | Peer review & studi kasus: tidak ada panggilan model | — | 0 | 0 | $0 |
| 13 | 2026-11-02 | Enam uji serangan (4 berhasil, 2 kena 429) | gemini-3.6-flash | ±4.000 | ±400 | ±$0,0045 |
| 14 | 2026-11-02 | 11 kasus ekstraksi (rata-rata per permintaan) | gemini-3.6-flash | 2.244 /permintaan | 506 /permintaan | $0,003581 /permintaan |
| 14 | 2026-11-02 | Kasus agen A01 | gemini-3.5-flash-lite | 5.255 | 376 | $0,005351 |
| 15 | 2026-11-02 | Analisis dokumen & riwayat git: tidak ada panggilan model | — | 0 | 0 | $0 |
| 16 | 2026-11-02 | UAS: pemeriksaan dokumen & uji otomatis, tanpa panggilan model | — | 0 | 0 | $0 |

**Tiga catatan saat menghitung ulang tabel ini:**

1. **Baris Minggu 2 adalah satu-satunya yang memakai tarif masing-masing model**
   (Flash-Lite 661/252 = $0,000828 + Flash 661/249 = $0,001429 = $0,002257), karena
   isinya justru perbandingan model. Bila seluruh baris itu dihitung dengan tarif Flash
   saja, hasilnya **$0,002870** — bukan $0,002259. Itu sebabnya baris ini diberi tanda
   berbeda dari yang lain, bukan karena salah hitung.
2. **Baris Minggu 1, 10, 11, dan 14 (agen) memakai tarif Flash** meski modelnya
   Flash-Lite, sesuai konvensi §2. Dengan tarif Flash-Lite, angkanya menjadi kira-kira
   setengah: baris BREAK Minggu 1 $0,008714, agen 3 langkah $0,002517.
3. **Latensi Flash-Lite tercatat 2,17 s di catatan Minggu 2 dan 1,95 s di**
   `catatan-proses/minggu-01-03.md`. Itu dua pengukuran pada run berbeda, bukan
   kontradiksi angka token/biaya; token dan biayanya sama.

---

## 4. Rincian yang bisa dihitung ulang

### 4.1 Perbandingan tiga model (Minggu 3, wajib)

Input identik: `data/sample_kebijakan.txt`, prompt dan system instruction sama.

| Model | Status | Latensi | Token masuk | Token keluar | Biaya | Kualitas |
|---|---|---|---|---|---|---|
| `gemini-3.5-flash-lite` | OK | 1,95 s | 661 | 252 | $0,000828 | 5/5 |
| `gemini-3.6-flash` | OK | 8,23 s | 661 | 249 | $0,001429 | 5/5 |
| `gemini-3.1-pro-preview` | **GAGAL** | — | — | — | tidak dapat dihitung | tidak dapat dinilai |

Hitung ulang baris Flash:

```
(661 ÷ 1.000.000 × $0,75) + (249 ÷ 1.000.000 × $3,75)
= $0,00049575 + $0,00093375
= $0,0014295  →  $0,001429
```

Hitung ulang baris Flash-Lite:

```
(661 ÷ 1.000.000 × $0,30) + (252 ÷ 1.000.000 × $2,50)
= $0,00019830 + $0,00063000
= $0,0008283  →  $0,000828
```

**Kenapa Pro gagal dan kenapa itu bukan bug:** `429 RESOURCE_EXHAUSTED` dengan
`limit: 0` — jatah gratis model Pro memang nol, bukan kuota yang habis. Billing
sengaja tidak diaktifkan hanya untuk satu baris perbandingan; kegagalannya sendiri
sudah menjadi data.

### 4.2 Perhitungan langkah-demi-langkah (rujukan Minggu 2)

Perhitungan yang dirujuk `docs/catatan-proses.md` Minggu 2 (biaya satu percakapan):

```
masukan : 661 token × $0,75/juta  = $0,00049575
keluaran: 250 token × $3,75/juta  = $0,00093750
jumlah                            = $0,00143325  →  $0,001433
```

### 4.3 Biaya satuan per jenis permintaan (data nyata, Minggu 14)

| Jenis | Token masuk | Token keluar | Biaya (tarif Flash) | Rupiah (≈) |
|---|---|---|---|---|
| Ekstraksi 1 dokumen (rata-rata 11 kasus) | 2.244 | 506 | $0,003581 | Rp 59 |
| Tugas agen 3 langkah | 5.255 | 376 | $0,005351 | Rp 88 |
| Tugas agen 4 langkah | 8.044 | 455 | $0,007739 | Rp 128 |
| Tugas agen 4 langkah + persetujuan | 5.753 | 530 | $0,006302 | Rp 104 |

Catatan: ketiga baris agen memakai `gemini-3.5-flash-lite` tetapi dihitung dengan tarif
Flash (konvensi §2 nomor 1). Dengan tarif Flash-Lite sesungguhnya: 3 langkah $0,002517,
4 langkah $0,003551, 4 langkah + persetujuan $0,003051 — **setengah dari angka tabel**.
Angka tabel sengaja dipertahankan agar sebanding dengan baris ekstraksi.

**Rasio agen terhadap ekstraksi:** $0,007739 ÷ $0,003581 ≈ **2,2×** — tugas yang
sama, biaya dua kali lipat, karena tiap langkah agen mengirim ulang konteks.

### 4.4 Biaya per pertanyaan RAG (turunan, bukan terukur per kasus)

Enam kasus RAG memakai ±15.000 token masuk dan ±600 token keluar total → rata-rata
±2.500 masuk / ±100 keluar per pertanyaan ≈ **$0,00225** per pertanyaan. Angka ini
**turunan dari total**, bukan hasil pengukuran per kasus; jangan dikutip sebagai
"terukur".

---

## 5. Rekap

| Ukuran | Nilai | Catatan |
|---|---|---|
| Total token masuk (teks) | ±89.200 | dijumlahkan dari tabel §3; angka ± tetap perkiraan |
| Total token keluar (teks) | ±16.800 | idem |
| Total token embedding | ±140.000 | 20.000 (Minggu 7) + 120.000 (295 chunk) |
| Total biaya setara | **±$0,129** (≈ Rp 2.135) | kumulatif Minggu 1–16, tarif Flash (§2) |
| Biaya yang benar-benar dibayar | **Rp 0** | seluruhnya free tier |

Angka kumulatif ini konsisten dengan penjumlahan per minggu di
`docs/catatan-proses.md` ditambah baris BAYARKU yang tidak masuk rekap mingguan di sana:
0,0131 + 0,0023 + 0,0034 + 0,0142 + 0,0071 + 0,0049 + 0 + 0,0134 + 0,0063 + 0,014 +
0,0045 + 0,045 + 0,0012 = **$0,1294** (dibulatkan ±$0,129).

Perhitungan ulang seluruh tabel memberi $0,1298 bila semua token dihitung dengan tarif
Flash — selisih $0,0004 murni berasal dari angka ± yang dibulatkan. **Tidak ada baris
yang tidak bisa dihitung ulang.**

---

## 6. Proyeksi biaya

| Skenario | Perhitungan | Hasil |
|---|---|---|
| 1.000 ekstraksi dokumen | 1.000 × $0,003581 | **$3,58** (≈ Rp 59.100) |
| 1.000 ekstraksi, tarif normal 2027 | 1.000 × $0,007162 | **$7,16** (≈ Rp 118.100) |
| 100 tugas agen 4 langkah | 100 × $0,007739 | **$0,77** (tarif Flash; dengan Flash-Lite $0,36) |
| 100 pengguna × 20 permintaan/bulan | 2.000 × $0,003581 | **$7,16/bulan** |

**Batas free tier adalah kendala sebenarnya, bukan uang.** Kuota gratis
`gemini-3.6-flash` adalah **20 permintaan/hari/proyek** (±600/bulan). Skenario 100
pengguna × 20 permintaan = 2.000 permintaan/bulan, yaitu **±3,3× di atas kuota** —
artinya skenario itu mustahil di free tier meski biaya setaranya hanya $7,16. Ini
sudah terbukti menghambat pengujian (Minggu 4: 6 dari 10 kasus tidak terukur;
Minggu 14: run kedua untuk mengukur variance tidak bisa dijalankan).

---

## 7. Mengapa `gemini-3.6-flash`, bukan Flash-Lite yang 42% lebih murah

Keputusan ini **berubah** sepanjang semester, dan perubahannya perlu dicatat:

- **Minggu 3:** pada satu dokumen ringkas, kualitas Flash-Lite dan Flash tidak bisa
  dibedakan (5/5 vs 5/5), sementara Flash-Lite 4–5× lebih cepat dan ~42% lebih murah.
  Kesimpulan sementara saat itu: kandidat kuat untuk jadi default.
- **Minggu 14:** pada 5 kasus yang sama dari set uji, Flash lulus 4/5 sedangkan
  Flash-Lite 3/5 — selisih 20 poin persen, dan kegagalannya tepat pada kasus
  penolakan dan bukti verbatim, yaitu kasus yang justru menjadi alasan produk ini ada.

**Keputusan akhir:** tetap `gemini-3.6-flash`. Penghematan 42% ditolak karena
kegagalannya terkonsentrasi di kasus tepi, dan kasus tepi itulah inti mutu produk.
Pelajaran yang saya catat untuk diri sendiri: **membandingkan harga, bukan
kegagalan, adalah cara berpikir yang keliru** — model murah gagal paling sering di
tempat yang paling mahal akibatnya.

---

## 8. Yang belum tercatat

- **Variance antar-run tidak terukur.** Rencana menjalankan set uji dua kali gagal
  karena 429; jadi tidak ada angka variasi jawaban. Pengulangan dengan cache
  (output identik, 100% hemat) bukan pengganti pengukuran variance.
- **Biaya terburuk agen (8 langkah) hanya diekstrapolasi,** belum diukur. Angka yang
  dipakai di laporan adalah hasil ekstrapolasi dari trace 4 langkah, bukan pengukuran.
- **Dua dari enam uji serangan tidak teruji** karena kuota; biaya keduanya tidak
  masuk hitungan.
- **Token embedding hanya perkiraan (±).** Tidak ada `usage_metadata` yang disimpan
  untuk 295 chunk; angkanya dihitung dari jumlah teks, dan kebetulan gratis sehingga
  tidak memengaruhi total biaya.
- **Tidak ada pencocokan dengan dashboard penagihan.** Semua angka adalah biaya
  setara hasil hitung sendiri; karena free tier, tidak ada tagihan untuk dicocokkan.
- **Sebagian token BREAK Minggu 1 tidak terpisah per percobaan** — yang tercatat
  hanya total 6 panggilan.

---

## 9. Cara menambah baris baru

Tambahkan satu baris di akhir tabel §3, lalu:

1. isi token dari `usage_metadata` bila ada; kalau tidak ada, beri tanda **±** dan
   sebut cara menaksirnya;
2. hitung biaya dengan rumus §2 dan **tulis langkahnya** di §4 bila angka itu akan
   dikutip di laporan;
3. perbarui total di §5 dan, kalau angkanya berubah, proyeksi di §6.

| Minggu | Tanggal | Kegiatan | Model | Token masuk | Token keluar | Biaya setara |
|---|---|---|---|---|---|---|
| _contoh_ | 2026-11-09 | Uji dokumen panjang (1 panggilan) | gemini-3.6-flash | _metadata_ | _metadata_ | _hitung_ |

---

## 10. Riwayat berkas

| Tanggal | Perubahan |
|---|---|
| 2026-09-05 | Dibuat; baris pertama: ekstraksi BAYARKU (500 masuk / 220 keluar). |
| 2026-11-09 | Dilengkapi menjadi buku besar Minggu 1–16: 21 baris kegiatan, dua konvensi tarif, perhitungan ulang tiap baris, rekap, proyeksi 100 pengguna, koreksi keputusan model, dan daftar hal yang belum tercatat. |
