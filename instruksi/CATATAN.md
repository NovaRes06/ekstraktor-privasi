# CATATAN — Riwayat Versi System Prompt

Setiap perubahan system prompt dicatat di sini: apa yang diubah, kenapa, dan
apa efek yang terlihat. Ketentuan modul Minggu 4: file ini WAJIB dan menjadi
dasar evaluasi Minggu 14 — kalau tidak dicatat, tidak bisa dijawab "versi mana
paling bagus dan kenapa".

Nama file prompt: `instruksi/v1.md`, `instruksi/v2.md` (dan nanti `v3.md`, dst.).
Prompt v1 asli disalin ke `instruksi/v1.md` agar seluruh versi berada di satu
folder yang sama; `prompts/system_prompt_v1.md` tetap ada agar tidak merusak
import yang sudah jalan (`extractor.py` membaca dari path lama).

## Tabel riwayat

| Versi | Tanggal | Yang diubah | Alasan | Efek yang terlihat |
|---|---|---|---|---|
| v1 | 2026-09-05 | versi awal: 9 field kepatuhan, tanpa field bukti | ketentuan Minggu 4 (Lapisan 2), fokus awal "format JSON stabil dulu" | sembilan field konsisten dikeluarkan; dokumen uji `sample_kebijakan.txt` menghasilkan 4 field "tidak disebutkan" tanpa dikarang |
| v1 | 2026-09-06 | (tanpa perubahan isi) diuji pada 3 model untuk perbandingan Minggu 3 | tugas wajib Minggu 3 | Flash-Lite setara Flash dalam kualitas (5/5), 4-5x lebih cepat, ~42% lebih murah — data lengkap di `catatan-pemakaian.md` |
| v2 | 2026-10-10 | menambah 9 field bukti `bukti_<nama_field>` (kutipan langsung) | ketentuan Minggu 5: field bukti "memaksa model memutuskan berdasarkan teks, bukan kesan" dan memudahkan evaluasi | belum diukur penuh — dijadwalkan uji 5 input (2 umum, 2 batas, 1 ditolak); hasil akan dicatat di baris ini |
| v2 | 2026-10-10 | menambah contoh kasus sulit (dokumen bukan kebijakan privasi yang disusupi instruksi) di samping contoh umum | contoh hanya kasus mudah membuat model mengira semua kasus mudah — persis peringatan modul | akan diukur pada uji 5 input di atas; salah satu input uji memang <dokumen> ini |
| v2 | 2026-11-02 | (tanpa perubahan isi) dipakai untuk seluruh 11 kasus ekstraksi pada set uji Lapisan 5 | evaluasi Minggu 14 | 9 dari 11 lulus; 2 gagal karena kutipan bukti disambung dari dua bagian dokumen (U01, U03) — temuan yang tidak terlihat kalau hanya bentuk JSON yang diperiksa |
| agent-v1 | 2026-11-02 | prompt baru untuk loop banyak langkah: protokol JSON `{alasan, aksi, argumen}` / `{alasan, selesai, jawaban}`, daftar 4 tool, aturan berhenti | Lapisan 4 (Minggu 10-11): ekstraksi satu langkah tidak bisa membandingkan dua dokumen | agen selesai 3-4 langkah pada 3 tugas; sempat mengabaikan permintaan menyimpan berkas, diperbaiki dengan aturan eksplisit (trace di `logs/agent_trace/`) |
| rag-v1 | 2026-10-10 | prompt RAG: jawab hanya dari konteks, sebut [1][2], tolak dengan "Tidak ada di dokumen." | Lapisan 3 (Minggu 7-9) | 5 dari 6 kasus RAG berjawaban benar; 1 menolak padahal dokumen memuat (U07) karena bagian relevan tidak terambil |

## Catatan keputusan desain yang menetap

- **Parafrase di field utama, kutipan di field bukti.** Sengaja dibedakan:
  field utama untuk dibaca manusia (ringkas), nilai bukti untuk dicek mesin
  maupun manusia (harus benar-benar ada di dokumen).
- **Nilai "tidak disebutkan" dipertahankan dari v1.** Ini partners nilai valid
  untuk kasus "tidak bisa ditentukan" yang diminta modul Minggu 5; jangan
  diganti perlahahan.
- **Format tetap ditegakkan ganda**: instruksi + `response_mime_type` di SDK.
  Modul Minggu 5: "penanganan kegagalan tiga langkah" tetap perlu karena JSON
  valid tetap bisa salah secara semantik, bukan cuma secara sintaks.

## Rencana versi berikutnya (catatan saja, belum dikerjakan)

- v3 kandidat: meminta model menolak eksplisit jika dokumen bukan kebijakan
  privasi (saat ini hanya diminta mengisi "tidak disebutkan" untuk semua field).

## Mode output ringkas (bukan versi prompt baru)

Mode `ringkas` tidak mengubah instruksi ke model. Ia memproyeksikan empat field
terpenting + buktinya dari hasil penuh yang **sama**, lalu menyusun satu paragraf.
Konsekuensinya: nol panggilan model tambahan, nol biaya tambahan, kualitas dasar
identik. Diuji di `tests/test_extractor_mode.py` (proyeksi tanpa memanggil API).
