# Log Kasus Berhasil (Baseline) — Lapisan 2

File ini menyimpan hasil ekstraksi yang **sudah benar**, untuk jadi pembanding kalau nanti
ada perubahan pada system prompt, model, atau kode — supaya kamu bisa cek apakah perubahan
itu memperbaiki atau malah merusak hasil yang sudah bagus.

Format tiap entri: tanggal, dokumen input, model yang dipakai, hasil, dan catatan kenapa
ini dianggap baseline yang baik.

---

## 2026-09-05 — Baseline pertama: kebijakan privasi BAYARKU (versi ringkas)

**Model:** gemini-3.6-flash

**Input:**
```
KEBIJAKAN PRIVASI - APLIKASI DOMPET DIGITAL BAYARKU. Kami mengumpulkan nama lengkap, 
nomor telepon, alamat email, nomor KTP, riwayat transaksi, dan lokasi perangkat Anda. 
Data digunakan untuk memproses transaksi dan verifikasi identitas sesuai ketentuan Bank 
Indonesia. Kami dapat membagikan data kepada bank mitra dan otoritas berwenang. Kami 
menerapkan enkripsi standar industri. Hubungi privacy@bayarku.example.com untuk 
pertanyaan privasi.
```

**Output:**
```json
{
  "jenis_data_dikumpulkan": "Aplikasi mengumpulkan data pribadi berupa nama lengkap, nomor telepon, email, dan KTP, serta data operasional seperti riwayat transaksi dan lokasi perangkat.",
  "tujuan_pemrosesan": "Pemrosesan data bertujuan untuk memproses transaksi pengguna dan melakukan verifikasi identitas sesuai dengan ketentuan Bank Indonesia.",
  "dasar_pemrosesan": "tidak disebutkan",
  "pihak_ketiga_penerima": "Data pengguna dapat dibagikan kepada bank mitra dan otoritas yang berwenang.",
  "transfer_lintas_negara": "tidak disebutkan",
  "masa_retensi_data": "tidak disebutkan",
  "hak_subjek_data": "tidak disebutkan",
  "mekanisme_keamanan": "Perusahaan menerapkan sistem enkripsi data sesuai dengan standar industri.",
  "kontak_penanggung_jawab": "Pertanyaan mengenai privasi dapat disampaikan melalui email ke privacy@bayarku.example.com."
}
```

**Token usage:** input 500, output 220

**Kenapa ini baseline yang baik:**
- 4 dari 9 field (`dasar_pemrosesan`, `transfer_lintas_negara`, `masa_retensi_data`, `hak_subjek_data`)
  benar-benar tidak disebutkan di teks asli, dan model dengan tepat menjawab **"tidak disebutkan"**
  alih-alih mengarang jawaban yang terdengar masuk akal. Ini bukti awal bahwa system prompt v1
  berhasil mencegah halusinasi pada kasus paling dasar.
- 5 field lainnya diparafrase dengan benar (bukan disalin persis kata demi kata dari input),
  sesuai instruksi di system prompt.
- Semua 9 field wajib muncul di output (`missing_fields` kosong) — validasi skema lolos.

**Yang belum diuji dari kasus ini (perlu kasus tambahan nanti):**
- Dokumen yang jauh lebih panjang (kebijakan privasi asli biasanya 2000+ kata)
- Dokumen berbahasa campuran Indonesia-Inggris
- Dokumen yang justru MENYEBUTKAN semua 9 field secara lengkap (untuk cek apakah model bisa
  mengekstrak dengan akurat, bukan cuma jago bilang "tidak disebutkan")
- Dokumen yang sengaja ambigu/menyesatkan (untuk cari kasus gagal wajib Lapisan 2)

---

<!-- Tambahkan entri baru di bawah ini setiap kali menemukan hasil yang bagus dan layak
     dijadikan pembanding -->
