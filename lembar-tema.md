# LEMBAR TEMA PROYEK

Nama            : Nova Reswara
NIM             : 10241058
Program studi   : Sistem Informasi
Kode peserta K  : **5** (nomor urut pada daftar peserta kelas; tidak diturunkan dari NIM)

## Angka lingkup saya

| Unsur | Rumus | Angka minimum | Yang benar-benar disiapkan |
|---|---|---|---|
| Dokumen rujukan | `5 + (5 mod 4)` | **6** | 8 dokumen (`data/raw/`, 7 dokumen penuh + ringkasan UU PDP) |
| Kasus uji | `12 + (5 mod 6)` | **17** | 18 kasus (`set-uji/kasus.jsonl`) |
| Tool yang dipanggil agent | `2 + (5 mod 2)` | **3** | 4 tool (`cari_dokumen`, `baca_dokumen`, `ambil_field`, `simpan_laporan`) |
| Mode output tambahan | wajib bila K genap | **tidak wajib** (K = 5 ganjil) | Tetap tersedia: mode `ringkas` (4 field + paragraf ringkasan) di API dan UI |

**Cara membaca tabel ini:** dengan **K = 5**, kewajiban minimum adalah 6 dokumen,
17 kasus uji, dan 3 tool. Yang disiapkan melebihi ketiganya (8 dokumen, 18 kasus,
4 tool). Karena K ganjil, mode output ringkas **tidak wajib**; mode itu tetap
dipertahankan sebagai kelebihan, bukan kewajiban.

### Tabel bantu: angka minimum untuk K = 1..12

Tandai baris yang sesuai dengan kode peserta Anda. Jangan menebak K dari NIM.

| K | Dokumen `5+(K mod 4)` | Kasus uji `12+(K mod 6)` | Tool `2+(K mod 2)` | Mode ringkas |
|---:|---:|---:|---:|---|
| 1 | 6 | 13 | 3 | tidak wajib |
| 2 | 7 | 14 | 2 | wajib |
| 3 | 8 | 15 | 3 | tidak wajib |
| 4 | 5 | 16 | 2 | wajib |
| 5 | 6 | 17 | 3 | tidak wajib |
| 6 | 7 | 12 | 2 | wajib |
| 7 | 8 | 13 | 3 | tidak wajib |
| 8 | 5 | 14 | 2 | wajib |
| 9 | 6 | 15 | 3 | tidak wajib |
| 10 | 7 | 16 | 2 | wajib |
| 11 | 8 | 17 | 3 | tidak wajib |
| 12 | 5 | 12 | 2 | wajib |

## Tema

**Ekstraktor & penjawab kebijakan privasi dompet digital (Privia).** Tema dikunci
sejak Minggu 4 dan tidak berubah; kandidat yang tidak dipilih beserta alasannya ada
di `docs/minggu-1-pemetaan-persoalan.md`.

## Kelayakan dokumen rujukan (lampiran B §2)

| Syarat | Keadaan |
|---|---|
| Sah dipakai | Semua halaman kebijakan publik milik perusahaan; ringkasan UU PDP ditulis sendiri dari teks UU |
| Tidak memuat data pribadi | Tidak ada NIK/nomor kartu/nomor telepon orang sungguhan; guardrails menolak input semacam itu |
| Cukup berisi | 7 dokumen penuh (3,5–86 KB). Ringkasan UU PDP hanya ±3,5 KB — paling rawan; karena itu dokumen lain sengaja dibuat 7 |
| Berbeda satu sama lain | Delapan dokumen dari delapan penerbit berbeda |
| Ada jawabannya | Enam pertanyaan uji RAG terjawab dari kumpulan ini (U06, U07, B04, P03, T02, T03 — dua di antaranya memang harus ditolak) |
| Asalnya tercatat | `data/raw/SUMBER.md` |
