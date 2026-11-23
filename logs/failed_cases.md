# Kasus yang gagal — evaluasi `gemini-3.6-flash`, 2 November 2026

Sumber: `logs/hasil-evaluasi-v1.json` (17 kasus dievaluasi, 14 lulus semua kriteria).
Berkas ini mencatat kasus yang **tidak** lulus saat itu, apa adanya. Status terbaru:
U07 sudah lulus setelah perbaikan peringkat retrieval (23 November 2026); U01 dan U03
masih gagal. Perbaikannya ada di `docs/catatan-proses.md` dan `laporan-evaluasi.md`.

Kriteria penilaian (lihat `set-uji/README.md`): 1 = field acuan benar, 2 = kutipan bukti
verbatim, 3 = tidak mengarang, 4 = format/skema 18 key, 5 = perilaku tolak.

| ID | Jenis | Target | Kriteria gagal | Apa yang terjadi |
|---|---|---|---|---|
| U01 | umum | ekstraksi | 2 (kutipan bukti) | Jawaban acuan sempat keliru: potongan 7.000 karakter mulai dari bagian "Penyimpanan Data" tidak memuat pernyataan "di luar wilayah Indonesia" (letaknya ±28 ribu karakter sebelumnya). Acuan sudah direvisi; kasus tetap dicatat gagal pada kriteria bukti. |
| U03 | umum | ekstraksi | 2 (kutipan bukti) | Bagian sumber data OVO. Nilai field benar, tetapi kutipan yang dikembalikan bukan kalimat verbatim dari potongan yang diuji. |
| U07 | umum | rag | 1 (field/sumber acuan) — **DIPERBAIKI 23 Nov 2026** | Retrieval meleset: 5 chunk teratas didominasi bagian umum ShopeePay dan satu chunk Tokopedia, bagian pengungkapan (pasal 9) tidak terambil. Sistem akhirnya menolak padahal dokumen memuat jawabannya. Kegagalan ini dipertahankan sebagai catatan, bukan dihapus. |

## Catatan

- U07 semula **sengaja dipertahankan** (jenis `umum`, bukan `pernah_gagal`) supaya laporan
  tidak hanya memuat kasus yang lolos. Setelah diukur, penyebabnya bukan isi yang hilang
  melainkan peringkat: chunk pasal 9 berjarak 0,5031 sedangkan enam chunk umum ShopeePay
  0,4661–0,4992. Perbaikan: peringkat dikoreksi dengan nama dokumen yang disebut pertanyaan
  dan frasa persis (`retrieve()` di `src/rag/vectorstore.py`). Hasil: 15 dari 17 lulus,
  bukti `logs/hasil-evaluasi-v1-fix-u07.json`, uji `tests/test_vectorstore_ranking.py`.
- Kasus A01 (target `agent`) tidak termasuk 17 kasus di atas karena evaluasi agen
  dijalankan terpisah dan hasilnya di `logs/laporan-agent/`.
- Dua uji serangan (#5 injeksi di dalam dokumen, #6 kebocoran lintas pengguna) berstatus
  `TIDAK TERUJI` karena kuota `gemini-3.6-flash` habis (HTTP 429) saat dijalankan —
  lihat `logs/uji-serangan.json`.
