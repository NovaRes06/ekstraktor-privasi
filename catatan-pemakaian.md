# Catatan Pemakaian Model

File ini diisi **setiap minggu**, bukan cuma di akhir. Ini bahan mentah untuk laporan
biaya di Lapisan 5 (Minggu 14-16) — supaya saat itu tiba, saya tidak perlu mengarang
angka dari ingatan, tapi tinggal rekap dari sini.

Format tiap baris: tanggal, kegiatan, model, perkiraan token, perkiraan biaya.

---

| Tanggal | Kegiatan | Model | Token Masuk | Token Keluar | Perkiraan Biaya |
|---|---|---|---|---|---|
| 2026-09-05 | Uji coba pertama: ekstraksi 9 field dari kebijakan privasi BAYARKU (versi ringkas) via endpoint `/extract` | gemini-3.6-flash | 500 | 220 | Lihat catatan di bawah |

---

## Catatan perhitungan biaya

**Tarif Gemini 3.6 Flash (dicek 6 September 2026):**
- Harga promo (berlaku sampai 31 Desember 2026): **$0,75 / juta token masukan**, **$3,75 / juta token keluaran**
- Harga normal (mulai 1 Januari 2027): $1,50 / juta token masukan, $7,50 / juta token keluaran — **naik 2x lipat**, penting dicatat untuk proyeksi biaya jangka panjang di Lapisan 5
- Free tier (tanpa kartu kredit, via AI Studio) masih mencakup model ini per September 2026

Perhitungan untuk baris pertama di atas (pakai tarif promo, sebagai skenario "kalau berbayar"):
```
Biaya = (token_masuk ÷ 1.000.000 × tarif_masuk) + (token_keluar ÷ 1.000.000 × tarif_keluar)
      = (500 ÷ 1.000.000 × $0,75) + (220 ÷ 1.000.000 × $3,75)
      = $0,000375 + $0,000825
      = $0,0012  (≈ Rp 20, dengan kurs kasar Rp 16.500/USD)
```

Catatan: karena dipakai lewat free tier, biaya aktual yang kamu bayar adalah **$0** untuk
pemanggilan ini. Tapi tetap penting menghitung "kalau berbayar"-nya — ini melatih kebiasaan
yang dibutuhkan di Lapisan 5, dan berguna kalau nanti proyekmu perlu naik ke tier berbayar
karena kena limit harian free tier.

## Baris berikutnya akan ditambahkan setelah:
- [ ] Perbandingan 3 model dijalankan (Minggu 3, wajib)
- [ ] Setiap kali mencoba dokumen baru selama pengembangan Lapisan 2-3
