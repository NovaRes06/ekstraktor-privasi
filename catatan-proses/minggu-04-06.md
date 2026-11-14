# Minggu 4–6 — Blok B: Structured Output, Prompt, Tool Pertama

## Dikerjakan

- **Minggu 4 BUILD.** Prompt v1 (`instruksi/v1.md`): 9 field kepatuhan, JSON murni,
  ditegakkan dua tempat (instruksi + `response_mime_type="application/json"`).
- **Minggu 4 uji v1 vs v2 (5 input, diukur 10 Oktober 2026).**
  `umum_1`: v1 OK 5,52 s; v2 OK 7,67 s dengan **9/9 field bukti terisi**.
  `umum_2`: v1 OK 4,04 s; v2 kena 503.
  Enam kasus sisanya kena `429 RESOURCE_EXHAUSTED` karena kuota harian 20
  permintaan/model. Data mentah: `logs/uji_v1_v2.json`, laporan: `logs/uji_v1_v2.md`.
- **Minggu 5.** Prompt v2 menambah 9 field `bukti_<field>` (kutipan langsung) dan
  contoh kasus sulit (dokumen bukan kebijakan yang disisupi instruksi). Riwayat
  lengkap: `instruksi/CATATAN.md`.
- **Penanganan kegagalan tiga langkah** di `src/extraction/extractor.py`: cek schema →
  ulang sekali dengan daftar pelanggaran → `ValueError` jelas. Tidak ada tebakan.
- **Minggu 5 — mode output ringkas** (wajib bila K genap): proyeksi 4 field dari hasil
  penuh yang sama, tanpa panggilan model tambahan; tersedia di API (`mode`) dan UI
  (toggle).
- **Minggu 6 — tool eksternal pertama:** `/fetch-url` mengambil halaman publik dan
  membersihkan HTML; `/extract-from-url` menggabungkan ambil + ekstrak. Batas akses
  dipasang di kode: host internal, IP privat, dan nama yang resolve ke IP privat
  ditolak 403 **sebelum** `requests.get` dipanggil (uji SSRF ada di
  `tests/test_api.py`).

## Tidak dikerjakan / jujur

- Uji 5 input Minggu 4 tidak pernah selesai penuh: 6 dari 10 percobaan kena kuota,
  dan baris tabelnya tidak pernah diisi ulang. Angka "4 request sukses" masih perlu
  dihitung ulang — sampai akhir semester tidak dihitung ulang.
- Contoh kasus sulit di v2 baru diuji sebagai kasus set uji (P01) pada Minggu 14,
  bukan saat prompt itu dibuat.

## Yang saya pelajari

Kualitas prompt tidak bisa dinilai dari satu-dua kasus; yang bisa dinilai hanyalah
"pada kasus yang terukur, tidak memburuk". Field bukti ternyata menambah satu masalah
baru: model bisa menyusun kutipan yang **terdengar** seperti kutipan tetapi disambung
dari dua tempat — ditemukan pada Minggu 14 lewat pemeriksaan verbatim.
