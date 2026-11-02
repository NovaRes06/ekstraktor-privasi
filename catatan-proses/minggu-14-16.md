# Minggu 14–16 — Blok E: Evaluasi, Risiko, Portofolio

## Dikerjakan

- **Set uji 18 kasus** (`set-uji/kasus.jsonl`) dengan komposisi 44% khas, 22% batas,
  17% tolak, 17% pernah gagal; lima kriteria ya/tidak; penjelasan di `set-uji/README.md`.
- **Harness evaluasi** (`src/eval/jalankan_set_uji.py`) dengan cache per
  (kasus, model, input) karena kuota gratis 20 permintaan/hari/model, dan mode
  `--nilai-ulang` untuk menghitung ulang skor tanpa memanggil model.
- **Hasil (2 November 2026):** 14 dari 17 kasus lulus seluruh kriteria pada
  `gemini-3.6-flash`; per kriteria 94% / 88% / 100% / 100% / 100%. Kasus agen lulus
  dalam 3 langkah pada `gemini-3.5-flash-lite` (kuota flash habis).
  Berkas: `logs/hasil-evaluasi-v1.json`, `logs/hasil-evaluasi-lite.json`.
- **Kalibrasi.** Enam kasus (35%) dinilai manual; kesesuaian dengan skrip 6/6.
  Keterbatasannya (penilai = perancang kriteria) ditulis di laporan §3.
- **Perbandingan model murah (BREAK #2).** 5 kasus yang sama: flash 4/5 lulus,
  Flash-Lite 3/5. Penghematan 42% **tidak** diterapkan karena kualitas turun.
- **Penghematan yang diterapkan:** cache hasil → 100% penghematan pada permintaan
  berulang dengan output identik.
- **Kajian risiko** (`kajian-risiko.md`): 6 risiko keamanan, 3 pintu bias dengan
  contoh konkret, trace data 6 baris + mekanisme pencegah, 4 pertanyaan etis,
  4 risiko yang diterima, pernyataan etis, dan paragraf "kapan produk tidak boleh
  dipercaya".
- **Pemeriksaan riwayat kredensial (Minggu 15 #6).** Ditemukan: `.env` berisi
  `GEMINI_API_KEY` pernah ter-commit di `f14616e` dan dihapus di `67f45aa`; nilainya
  masih ada di riwayat. Tindakan: `guardrails.md`, `kajian-risiko.md` §1, dan
  rekomendasi mencabut kunci + menulis ulang riwayat — **belum dijalankan**.
- **Refleksi** (`refleksi.md`), satu halaman.

## Tidak dikerjakan / jujur

- **Variance (BREAK #1 Minggu 14) belum terukur.** Set uji dijalankan satu kali pada
  model yang sama; run kedua tidak bisa dijalankan karena kuota harian habis sebelum
  sempat diulang. Angka 82% karena itu satu pengukuran, bukan rata-rata.
- **Penilai model tidak dipakai**, jadi kalibrasi penilai model (BREAK #4, #6) tidak
  ada. Kalibrasi yang ada adalah skrip vs penilaian manual saya.
- **Temperature 1 (BREAK #5)** tidak diuji; model ekstraksi memakai setelan bawaan
  dan agen memakai temperature 0.
- **Dua uji serangan tidak teruji** (kuota), dan **enam percobaan BREAK Minggu 10–11**
  tidak lengkap. Keduanya disebut di catatan ini dan di `guardrails.md` §6 alih-alih
  diklaim selesai.
- **Kunci API belum dicabut dan riwayat git belum dibersihkan** — butuh tindakan di
  akun Google dan keputusan pemilik repo (operasi riwayat tidak bisa dibatalkan).

## Yang saya pelajari

Angka yang jujur lebih berguna daripada angka yang bagus. Dua kegagalan (U01, U03)
justru membuka temuan yang lebih penting daripada skornya: model bisa menyusun
"kutipan" dari dua tempat berbeda, dan hanya pemeriksaan verbatim yang menangkapnya.
Tanpa set uji dan pemeriksaan bukti, kelemahan itu tidak akan pernah terlihat.
