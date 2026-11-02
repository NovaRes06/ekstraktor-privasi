# Minggu 1–3 — Blok A: Persoalan, Peta, Model

## Dikerjakan

- **Minggu 1 READ.** Tiga persoalan dipetakan: ekstraktor kebijakan privasi fintech,
  ekstraktor dokumen tender (LPSE), triase tiket IT (ITIL). Tabel lengkap di
  `docs/minggu-1-Ekstraktor-Privasi.md`; peta tiga kandidat di
  `docs/minggu-1-pemetaan-persoalan.md`.
- **Minggu 1 BUILD.** Kandidat 1 dipilih dengan alasan tertulis: sumber dokumen
  paling mudah diakses, ada rujukan objektif (UU PDP) untuk menilai benar-salah, dan
  sudah berjalan paling jauh secara teknis.
- **Minggu 2.** Konsep "konteks itu terbatas" diterapkan: dokumen dipecah per 150
  kata dengan overlap 30 (`src/rag/chunker.py`), bukan dikirim utuh.
- **Minggu 3 — perbandingan tiga model (wajib).** Ekstraksi 9 field dari
  `data/sample_kebijakan.txt` dengan prompt identik:

  | Model | Status | Latensi | Token (masuk/keluar) | Biaya | Kualitas |
  |---|---|---|---|---|---|
  | gemini-3.5-flash-lite | OK | 1,95 s | 661 / 252 | $0,000828 | 5/5 |
  | gemini-3.6-flash | OK | 8,23 s | 661 / 249 | $0,001429 | 5/5 |
  | gemini-3.1-pro-preview | GAGAL | — | — | — | tidak dapat dinilai |

- **Tantangan wajib Minggu 3.** Flash-Lite ~42% lebih murah dan 4–5× lebih cepat
  dengan kualitas yang tidak bisa dibedakan pada satu dokumen ringkas; proyeksi 1.000
  pemanggilan menghemat $0,601.

## Tidak dikerjakan / jujur

- **Minggu 1 BREAK (4 percobaan) belum dikerjakan.** Entri kosongnya masih ada di
  `docs/catatan-proses.md`. Ini kesenjangan yang tidak ditutup sampai akhir semester.
- **Tantangan wajib Minggu 1** ("temukan contoh AI dipakai untuk persoalan yang
  salah") belum dikerjakan — butuh observasi lapangan, bukan sesuatu yang bisa
  dikarang.
- `gemini-3.1-pro-preview` gagal dengan `429 RESOURCE_EXHAUSTED, limit: 0`, artinya
  jatah gratis model Pro memang nol. Kegagalan ini **tidak** diperbaiki dengan
  mengaktifkan billing; kegagalannya sendiri dicatat sebagai data.

## Yang saya pelajari

Model termurah tidak selalu lebih buruk — tetapi satu dokumen ringkas bukan bukti.
Peringatan itu terbukti di Minggu 14: ketika model murah diuji pada 5 kasus yang
lebih beragam, kualitasnya benar-benar turun (4/5 → 3/5).
