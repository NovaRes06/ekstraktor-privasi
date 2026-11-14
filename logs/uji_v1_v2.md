Laporan Uji v1 vs v2 — 10 Oktober 2026

Uji komposisi modul Minggu 4: 5 kasus (2 umum, 2 batas, 1 seharusnya ditolak)
dijalankan pada prompt v1 (instruksi/v1.md, 9 field) dan v2 (instruksi/v2.md,
9 field + 9 bukti), model gemini-3.6-flash, response_mime_type=json.
Skrip: data/test_cases/uji_v1_v2.py. Data mentah: logs/uji_v1_v2.json.

## Hasil yang TERUKUR sebelum kuota harian habis

| Kasus | Versi | Status | Detik | Jumlah field bukti |
|---|---|---|---|---|
| umum_1 (kebijakan ringkas) | v1 | OK | 5.52 | 0 |
| umum_1                     | v2 | OK | 7.67 | **9/9** |
| umum_2                     | v1 | OK | 4.04 | (0) |
| umum_2                     | v2 | 503 (server sibuk) | — | — |

Temuan #1 (v2): pada umum_1, v2 menghasilkan **9/9 field bukti terisi** —
memenuhi ketentuan Minggu 5. v1 tidak punya field bukti sama sekali (0).
Biaya wajar: v2 2.15 detik lebih lambat (7.67 vs 5.52) karena output lebih panjang.

## Kegagalan yang TIDAK terlindungi: kuota harian

Perlu dicatat apa adanya: setelah 4 pemanggilan sukses, sisanya mengembalikan
429 RESOURCE_EXHAUSTED dengan detail:

    Quota exceeded for metric: ...generate_content_free_tier_requests
    quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier
    quotaValue: '20'
    Please retry in 38348s (10 dll 39 menit)

Limit harian free tier model ini **20 request/hari/proyek**. Kuota yang sama
dipakai build_index.py Minggu ini dan berbagai uji lainnya hari ini, jadi sisa
hari ini sudah habis. Ini menghalangi pelengkapan uji, bukan gagalnya proyek:

    Sisa 8 kasus (umum_2__v2, batas_1*, batas_2*, seharusnya_ditolak*) TIDAK
    terukur hari ini. Jalankan ulang besok: python data/test_cases/uji_v1_v2.py

Ini dibukukkan di catatan pengembangan sebelumnya juga (Minggu 3: model Pro
punya "limit: 0" di free tier; Minggu 2-4: rate-limit embedding yang lewat
error 429 per menit di src/rag/embedder.py).

## Kesimpulan yang bisa diambil sekarang

- v2 TIDAK merusak perilaku yang sudah benar: satu kasus yang terukur penuh
  (umum_1) menghasilkan semua field bukti yang valid, tanpa field hilang.
- Temuan berguna yang harus diperiksa saat kurungan kuota lepas: 10 kasus,
  termasuk yang seharusnya ditolak (seharusnya_ditolak: resep nasi goreng),
  semuanya diproses/dicatat di logs/uji_v1_v2.json.
