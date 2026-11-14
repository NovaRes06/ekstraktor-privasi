# Catatan Asal Dokumen Rujukan

Syarat lampiran B modul: setiap dokumen rujukan harus **sah dipakai** (publik),
**tidak memuat data pribadi**, **cukup berisi** (≈3 halaman), **berbeda satu sama
lain**, **bisa menjawab** pertanyaan uji, dan **asalnya tercatat**. Dokumen ini
memenuhi syarat terakhir: judul, penerbit, tahun, dan tautan/cara memperoleh.

Semua berkas diunduh dengan `python fetch_reference_docs.py` (kecuali
`ringkasan-pasal-uu-pdp.md`, yang ditulis sendiri dari teks UU). Tidak ada data
pribadi orang sungguhan di dalamnya — semuanya kebijakan yang memang dipublikasikan
perusahaan untuk dibaca publik.

| # | Berkas | Judul | Penerbit | Tahun / versi | Cara memperoleh |
|---|---|---|---|---|---|
| 1 | `kebijakan-ovo.txt` | Kebijakan Privasi OVO | PT Visionet Internasional (OVO) | halaman aktif per 2026 | https://www.ovo.id/kebijakan-privasi |
| 2 | `kebijakan-shopeepay.txt` | Privacy Policy ShopeePay | PT Airpay International Indonesia (ShopeePay) | halaman aktif per 2026 | https://shopeepay.co.id/privacy |
| 3 | `kebijakan-dana.txt` | Kebijakan Privasi DANA | PT Espay Debit Indonesia Koe (DANA) | halaman aktif per 2026 | https://www.dana.id/policy |
| 4 | `kebijakan-gopay.txt` | GoPay Privacy Notice (23 Juni 2025) | PT GoTo Gojek Tokopedia (GoPay) | 23 Juni 2025 | https://gopay.co.id/terms-and-condition/gopay-privacy-notice-23-juni-2025 |
| 5 | `kebijakan-linkaja.txt` | Kebijakan Privasi Layanan LinkAja | PT Fintek Karya Nusantara (LinkAja) | 8 Juli 2021 | https://www.linkaja.id/kebijakan-privasi |
| 6 | `kebijakan-bibit.txt` | Kebijakan Privasi Bibit | PT Bibit Tumbuh Bersama (Bibit) | efektif 3 September 2025 | https://bibit.id/privacy |
| 7 | `kebijakan-tokopedia.txt` | Kebijakan Privasi Tokopedia | PT Tokopedia | halaman aktif per 2026 | https://www.tokopedia.com/privacy |
| 8 | `ringkasan-pasal-uu-pdp.md` | Ringkasan pasal UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi | ditulis sendiri, merujuk teks UU | 2022 (UU), ringkasan 2026 | Teks UU PDP publik; diringkas manual per pasal yang relevan |

**Jumlah dokumen: 8.** Lingkup minimum menurut lampiran B adalah
`5 + (K mod 4)`, yaitu 5 sampai 8 dokumen tergantung kode peserta K. Delapan
dokumen memenuhi angka minimum untuk K berapa pun.

## Catatan kejujuran

- Dokumen #8 (`ringkasan-pasal-uu-pdp.md`) adalah **ringkasan buatan sendiri**,
  bukan salinan utuh UU. Ia lebih pendek dari 3 halaman setara (±3,5 KB). Kalau
  dosen menilai ketat syarat "cukup berisi", dokumen ini paling rawan — karena
  itu jumlah dokumen lain sengaja dibuat 7, sehingga tetap ≥7 dokumen penuh
  walaupun #8 tidak dihitung.
- Tautan bisa berubah sewaktu-waktu; yang tersimpan di repo adalah salinan teks
  pada tanggal unduh, jadi hasil evaluasi tetap bisa direproduksi.
- `fetch_reference_docs.py` mendaftarkan 7 URL; kalau satu gagal (situs lambat
  atau memblokir pengambilan otomatis), berkasnya tidak dibuat. Itu pernah
  terjadi pada `dana.id` (10 Oktober 2026) dan berhasil pada percobaan berikutnya.
