# Minggu 7–9 — Blok C: Grounding, Ambang, Baseline

## Dikerjakan

- **Dokumen rujukan.** Mulai 5 berkas (4 dompet digital + ringkasan UU PDP); pada
  2 November 2026 ditambah LinkAja, Bibit, Tokopedia menjadi **8 dokumen** — memenuhi
  `5 + (K mod 4)` untuk K berapa pun. Asal-usul tiap dokumen dicatat di
  `data/raw/SUMBER.md` (judul, penerbit, tahun, tautan).
- **Index.** `python build_index.py` membangun 295 chunk dari 8 dokumen. Sebelumnya
  index hanya berisi 14 chunk dari 2 dokumen, padahal 4 dokumen sudah ada di
  `data/raw/` — akibatnya pertanyaan OVO/ShopeePay mengambil chunk dari dokumen yang
  salah (0,5661 dan 0,6116, masih di bawah ambang 0,65 tetapi tidak menjawab).
- **Ambang relevansi 0,65** dipilih dari pengukuran, bukan tebakan:

  | Kelompok | Jarak teramati | Keputusan |
  |---|---|---|
  | Query relevan | 0,4205–0,4879 | lolos |
  | Query tidak relevan | 0,7641–0,8019 | dibuang |

- **Perilaku "tidak ditemukan".** Kalau semua chunk di atas ambang, `retrieve()`
  mengembalikan `[]` dan `/ask` menjawab "Tidak ada di dokumen." **tanpa memanggil
  model** — hemat biaya sekaligus tidak bergantung pada kedisiplinan model.
- **Baseline Minggu 9 (dua angka).** 3 dari 3 pertanyaan berjawaban mengambil dokumen
  yang benar; 3 dari 3 pertanyaan tak berjawaban ditolak. Semua di tingkat retrieval.

## Tidak dikerjakan / jujur

- `kebijakan-dana.txt` sempat gagal diunduh 3 kali (read timeout 15 s dan 30 s ×2)
  pada 10 Oktober 2026; baru berhasil pada percobaan berikutnya. Catatan lama di
  `logs/lapisan3_rag_cases.md` masih menyebut "belum tersedia" — sudah tidak akurat,
  berkasnya sekarang ada dan ikut terindeks.
- Baseline Minggu 9 diukur pada tingkat retrieval, bukan tingkat jawaban. Saat
  evaluasi Minggu 14 ukurannya berubah, sehingga perbandingannya tidak apel ke apel
  (ditulis terbuka di `laporan-evaluasi.md` §5).

## Yang saya pelajari

Ambang jarak adalah pertahanan tambahan, bukan pengganti. Kalau dokumennya tidak ada
di index, chunk yang tidak relevan bisa tetap lolos ambang. Pelajaran ini yang
memunculkan aturan: **jalankan ulang `build_index.py` setiap kali menambah dokumen**.
