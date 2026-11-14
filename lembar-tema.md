# LEMBAR TEMA PROYEK

Nama            : Nova Reswara
NIM             : 10241058
Program studi   : Sistem Informasi
Kode peserta K  : **belum diisi** (nomor urut pada daftar peserta kelas, diterima Minggu 1;
                  tidak diturunkan dari NIM dan tidak tercatat di berkas mana pun di repo ini)

## Angka lingkup saya

| Unsur | Rumus | Angka minimum | Yang benar-benar disiapkan |
|---|---|---|---|
| Dokumen rujukan | `5 + (K mod 4)` | 5–8 | **8 dokumen** (`data/raw/`, 7 dokumen penuh + ringkasan UU PDP) |
| Kasus uji | `12 + (K mod 6)` | 12–17 | **18 kasus** (`set-uji/kasus.jsonl`) |
| Tool yang dipanggil agent | `2 + (K mod 2)` | 2–3 | **4 tool** (`cari_dokumen`, `baca_dokumen`, `ambil_field`, `simpan_laporan`) |
| Mode output tambahan | wajib bila K genap | — | **Sudah ada**: mode `ringkas` (4 field + paragraf ringkasan), tersedia di API dan UI |

**Cara membaca tabel ini:** karena kode peserta K tidak diketahui saat proyek
dikerjakan, seluruh lingkup disiapkan pada **angka maksimum** (8 dokumen, 17+ kasus,
3+ tool, plus mode ringkas). Dengan begitu kewajiban untuk K berapa pun terpenuhi,
dan mode ringkas tetap ada walaupun K ternyata ganjil.

**Tindakan yang masih diperlukan:** isi `Kode peserta K` di atas dari daftar kelas,
lalu hitung ulang tiga angka minimum dan cocokkan dengan kolom terakhir. Tidak ada
yang perlu ditambah — hanya pencatatan.

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
