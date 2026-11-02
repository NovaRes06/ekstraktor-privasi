# Minggu 10–13 — Blok D: Agent, Tool, Guardrails

## Dikerjakan

- **Minggu 10 — analisis workflow vs agen.** `analisis-workflow-vs-agen.md`: satu
  tugas bercabang (bandingkan retensi dua kebijakan) dirancang dalam dua bentuk,
  dibandingkan lima sisi, dipilih agen dengan kekurangan yang disebutkan. Bagian yang
  sengaja tetap workflow juga disebutkan (ekstraksi, `/ask`, guardrails, mode ringkas).
- **Minggu 10 — trace pertama (READ).** Trace agen 3 langkah:
  `cari_dokumen` → `ambil_field(OVO)` → `ambil_field(ShopeePay)` → jawaban.
  Tersimpan di `logs/agent_trace/5a9065eaec60.jsonl`.
- **Minggu 11 — agen berjalan.** `src/agent/agent.py` + 4 tool di
  `src/agent/tools.py`:
  - batas langkah 8 (maksimum keras 20);
  - state di `logs/agent_state/<task_id>.json` (di luar percakapan, bisa dilanjutkan);
  - trace JSONL satu baris per langkah;
  - tool gagal: diulang sekali (jeda 2 s), lalu dikembalikan sebagai observasi;
  - model 503: diulang sampai 3 kali (ini terjadi nyata saat pengujian).
- **Minggu 13 — guardrails berlapis.** Lapis 1 (`input_filter.py`: pola injection,
  NIK/kartu/telepon, batas panjang), lapis 3 (batas akses tool di kode), lapis 4
  (`output_check.py`: kebocoran prompt, putusan kepatuhan, nomor rujukan, bukti
  verbatim), lapis 5 (persetujuan manusia untuk `simpan_laporan`).
- **Titik HITL terbukti berjalan.** Tugas "...lalu simpan jawabannya sebagai berkas
  perbandingan-retensi.md" berhenti dengan `status: butuh_persetujuan`, menampilkan
  nama berkas + 661 karakter isi, lalu berkas baru dibuat setelah disetujui.
  Trace: `logs/agent_trace/a2b5516db110.jsonl`.
- **Minggu 13 — enam uji serangan.** Hasil: 4 ditolak, 0 tembus, 2 tidak teruji
  (kuota habis). Rincian jujur: `logs/uji-serangan.json`, ringkasan: `guardrails.md` §4.

## Tidak dikerjakan / jujur

- **Enam percobaan BREAK Minggu 10 dan Minggu 11 tidak dijalankan penuh.** Yang
  sempat dijalankan hanya batas langkah (1 langkah → `batas_langkah` dengan pesan
  jelas) dan tugas mustahil; empat percobaan lain (batas 20 dengan tugas mustahil,
  tool selalu error, tugas satu langkah, tugas ambigu) belum punya catatan prediksi
  lebih dulu.
- **Biaya terburuk pada BREAK #2** belum diukur langsung; yang ada adalah
  ekstrapolasi linear dari 1–4 langkah ($0,0009 → $0,0077), ditulis sebagai
  ekstrapolasi di laporan, bukan angka terukur.
- **Serangan #2 dan #5 tidak teruji** karena kuota model habis pada hari pengujian.
  Bukti pengganti untuk #2 diambil dari kasus set uji P01, dan itu disebut sebagai
  bukti tidak langsung.
- **Satu perbaikan agen lewat prompt** (tantangan wajib Minggu 11): agen mengabaikan
  permintaan menyimpan berkas. Setelah prompt `agent-v1.md` diberi aturan eksplisit,
  tugas yang sama berhenti di titik persetujuan. Trace sebelum/sesudah ada, tetapi
  trace "sebelum" tidak tersimpan sebagai berkas trace (hanya output di terminal).

## Yang saya pelajari

Kegagalan yang paling berbahaya di sistem agentic bukan error, melainkan hasil yang
salah tetapi masuk akal. Contoh nyata di proyek ini: agen menjawab dengan yakin bahwa
laporannya "sudah disimpan" padahal tidak ada berkas yang ditulis, karena ia tidak
memanggil tool sama sekali. Yang menangkapnya bukan model, melainkan pemeriksaan
keberadaan berkas di kode.
