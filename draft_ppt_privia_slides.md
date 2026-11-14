# Slide Package — Privia (8 halaman)

> Cara pakai: tiap slide di bawah punya dua blok — (A) isi poin presentasi, dan (B) ruang
> visual/catatan pembicara. Blok B sengaja tidak diisi retouche karena butuh aset nyata
> (screenshot, diagram, kutipan asli); petunjuk isotopnya sudah tertulis.

---

## Slide 1 — Persoalan

### A. Isi presentasi

**Siapa yang mengalaminya**
- Pengguna aplikasi dompet digital / fintech (GoPay, OVO, DANA, ShopeePay) yang ingin
  tahu apa yang terjadi dengan datanya, tapi kebijakan privasi biasanya panjang dan
  berbahasa hukum.
- Pihak yang meninjau kebijakan dalam waktu singkat dan butuh pemetaan terstruktur,
  bukan sekadar membaca tembus-tembus.

**Bagaimana diselesaikan sekarang**
- Membaca dokumen satu per satu, menandai bagian penting sendiri, lalu menyusun catatan
  manual.
- Kalau cuma butuh jawaban cepat seperti "berapa lama data disimpan", tetap harus
  memindai keseluruhan teks.

**Mengapa belum cukup**
- Bisa dilakukan, tapi tidak terstruktur: sulit dibandingkan antar dokumen, dan mudah
  kelewatan bagian yang memang tidak disebutkan secara eksplit.
- Tanpa kutipan dasar, temuan "tidak disebutkan" mudah dipertanyakan: memang tidak ada,
  atau hanya luput dari mata?

### B. Ruang visual / catatan pembicara

- Gunakan screenshot kebijakan panjang, atau kutipan pendek dari data/raw yang
  menunjukkan betapa padatnya dokumen.
- Saran kontras: sangat panjang vs ringkasan 9 aspek yang diharapkan.

---

## Slide 2 — Mengapa AI generatif, dan bukan pendekatan biasa

### A. Isi presentasi

**Tugas inti**
- Membaca teks bebas, memahami maksud, lalu memetakannya ke sembilan kategori tetap.

**Mengapa bukan basis data biasa**
- Basis data hanya bekerja untuk informasi yang sudah terstruktur di dokumen.
- Kebanyakan dokumen tidak begitu; kalau informasi tidak tertulis, basis data tidak
  bisa memberi jawaban yang bermakna "tidak disebutkan".

**Mengapa bukan formulir statis**
- Dokumen menulis hal yang sama dengan cara berbeda; formulir kaku tidak fleksibel
  untuk menangkap variasi redaksi dan bahasa hukum.

**Mengapa bukan aturan biasa**
- Regex / kata kunci mudah rusak saat redaksi berubah; tidak ada cara alami untuk
  mengatakan "tidak yakin, jadi jawab tidak disebutkan".

**Mengapa AI generatif**
- AI dipakai sebagai pembaca yang bisa memparafrase dan mengejar maksud, bukan
  pengganti penilaian kepatuhan.
- Output dikunci ke skema tetap lengkap dengan kutipan sumber.
- Jika informasi tidak ada, respons yang diinginkan adalah "tidak disebutkan",
  bukan tebakan.

### B. Ruang visual / catatan pembicara

- Buat perbandingan singkat dalam 4 kolom: basis data, formulir, aturan, AI generatif.
- Tekankan kalau AI di sini dipakai terbatas, bukan bebas.

---

## Slide 3 — Rancangan sistem: alur dari input sampai output

### A. Isi presentasi

**Sisi A — Ekstraksi langsung**
1. Input: teks kebijakan / URL publik.
2. Jika URL: download halaman, bersihkan HTML (buang script/style).
3. Endpoint: /extract atau /extract-from-url.
4. Hasil: 9 field, atau 9 field + 9 kutipan bukti (versi v2).
5. Output: JSON terstruktur yang ditampilkan di Privia (Streamlit).

**Sisi B — Tanya-jawab berbasis dokumen (RAG)**
1. Dokumen di data/raw/ diproses bila berubah:
   - Markdown terstruktur → dipecah per heading.
   - Teks polos → dipecah per ~150 kata dengan overlap 30 kata.
2. Setiap chunk di-embedding dengan gemini-embedding-001, lalu disimpan di ChromaDB
   (chroma_db/).
3. Saat pengguna bertanya:
   - Pertanyaan di-embedding.
   - Mengambil k chunk terdekat (default k=5, rentang 1–50).
   - Membuang chunk dengan jarak > 0.65.
   - Menyusun konteks bernomor [1], [2], ...
   - Mengirim ke gemini-3.6-flash dengan system prompt RAG.
   - Output: jawaban + rujukan inline + daftar chunk sumber + jarak.

**Catatan arsitektur**
- API dipisah dari antarmuka: FastAPI (api.py) dan Streamlit (app.py).
- Ada endpoint /health untuk pengecekan sederhana.
- Tool /fetch-url dibatasi hanya halaman publik.

### B. Ruang visual / catatan pembicara

- Diagram horizontal satu baris: teks/URL → ekstrak / fetch → JSON → tampilan.
- Diagram RAG: dokumen → chunk → embedding → ChromaDB → pertanyaan → filter → konteks
  → jawaban + sumber.
- Jika ingin satu gambar penuh, gabungkan dua sisi dengan tebal/pewarna berbeda.

---

## Slide 4 — Kendali output

### A. Isi presentasi

**Schema**
- Ekstraksi harus menghasilkan:
  - v1: 9 field.
  - v2: 9 field + 9 kutipan bukti.
- Skema ditulis di instruksi/v1.md dan instruksi/v2.md.
- Dari sisi kode, output diarahkan ke JSON melalui response_mime_type, dan
  respons yang gagal di-parse ditolak dengan HTTP 422.

**Nilai valid**
- Jika informasi ada di dokumen: parafrase maksimal 2 kalimat, Bahasa Indonesia,
  bukan salin kalimat berantai panjang.
- v2: setiap field disertai kutipan langsung sebagai bukti.
- Jika informasi tidak ada: isi persis "tidak disebutkan".
- Untuk v2, bukti juga diisi "tidak disebutkan".

**Penanganan output tidak valid**
- Jika JSON gagal di-parse, sistem lempar HTTP 422 dengan detail galat.
- Strategi utama adalah pencegahan: prompt tegas + response_mime_type + penekanan
  "jangan mengarang".
- Validasi logika isi (benar-benar sesuai teks) masih mengandalkan pemeriksaan manusia
  dan uji kasus tambahan, bukan hanya validasi struktur.

### B. Ruang visual / catatan pembicara

- Tampilkan mini skema: 9 field saja, atau 18 field versi v2.
- Contoh kutipan pendek dari dokumen nyata yang menunjukkan pasangan field–bukti.

---

## Slide 5 — Tool

### A. Isi presentasi

**Tool utama**
- Gemini API: ekstraksi kebijakan dan embedding RAG; model utama: gemini-3.6-flash.
- ChromaDB lokal (chroma_db/): menyimpan chunk dan embedding.
- FastAPI (api.py): bungkus endpoint ekstraksi dan RAG.
- Streamlit (app.py): antarmuka pengguna.
- BeautifulSoup + requests: mengambil dan membersihkan halaman publik.

**Batas akses**
- /fetch-url dan /extract-from-url hanya boleh mengambil halaman publik.
- Host internal, IP privat/loopback, dan nama yang resolve ke alamat tidak publik
  ditolak dengan HTTP 403 sebelum permintaan keluar (anti-SSRF).
- Teks dari URL dibatasi panjang sebagai jaga-jaga.

**Yang perlu persetujuan manusia**
- Keputusan akhir kepatuhan tidak dibuat otomatis; sistem hanya ekstrak dan beri
  bukti.
- Persetujuan juga relevan untuk:
  - menambah dokumen rujukan,
  - mengubah index,
  - mengubah batas ambang jarak.

### B. Ruang visual / catatan pembicara

- Tabel sederhana: tool, peran, dan batasan.
- Jika perlu kesan keselamatan, sorot batas akses tool sebagai poin penting.

---

## Slide 6 — Grounding

### A. Isi presentasi

**Dokumen rujukan**
- Kebijakan publik yang diunduh dan disimpan di data/raw/:
  - OVO
  - ShopeePay
  - GoPay
  - DANA
- Ringkasan pasal UU PDP No. 27/2022 sebagai konteks hukum.

**Chunking**
- Markdown terstruktur → dipecah per heading.
- Teks polos → dipecah per ~150 kata dengan overlap 30 kata.
- Alasan: satu bagian kebijakan biasanya satu topik utuh, dan overlap mencegah
  informasi terpotong di batas chunk.

**Retrieval**
- Embedding: gemini-embedding-001.
- Saat pertanyaan masuk, ambil k chunk terdekat (default 5; bisa diatur per request
  antara 1–50).
- Chunk yang terlalu jauh dibuang sebelum dikirim ke model, dengan ambang
  MAX_RELEVANT_DISTANCE = 0.65.

**Kalau jawaban tidak ditemukan**
- Jika tidak ada chunk yang lolos ambang, endpoint /ask tidak memanggil model dan
  langsung menjawab "Tidak ada di dokumen."
- System prompt RAG juga memerintahkan hal yang sama: jika tidak ada di konteks,
  jawab "Tidak ada di dokumen.", jangan tebak.
- Jika model tidak mengembalikan teks (mis. karena penyaringan konten), sistem
  tetap menyampaikan keadaan tersebut secara transparan.

### B. Ruang visual / catatan pembicara

- Tampilkan dua lapis pertahanan: filter jarak di retrieval, dan instruksi "jangan
  mengarang" di prompt.
- Bisa ditambah contoh jarak: relevan vs tidak relevan.

---

## Slide 7 — Bukti sejauh ini

### A. Isi presentasi

**Satu keberhasilan yang ditemukan sendiri**
- Uji v1 vs v2 menunjukkan v2 menghasilkan 9/9 field bukti pada kasus umum_1,
  sementara v1 tidak memiliki field bukti sama sekali.
- Artinya v2 memenuhi mandat "setiap field disertai kutipan sumber" yang belum ada
  di v1, dengan biaya tambahan yang wajar.

**Satu kegagalan / batas yang ditemukan sendiri**
- Uji mencakup dokumen kosong dan dokumen yang bukan kebijakan, yang masuk ke
  kategori "seharusnya ditolak/tidak relevan".
- Di sisi ekstraksi, ditemukan batas praktis: kuota harian Gemini free tier terbatas.
  Setelah ~20 request/hari/proyek habis, sisa kasus tidak bisa diukur saat itu.
- Ini bukan bug sistem utama, tapi batas operasional yang perlu direncanakan.

### B. Ruang visual / catatan pembicara

- Rekap singkat: 1 berhasil, 1 batas/gagal, bukan klaim sempurna.
- Jika presentasi formal, sertakan sumber: logs/uji_v1_v2.md dan logs/uji_v1_v2.json.

---

## Slide 8 — Risiko dan rencana Minggu 9–16

### A. Isi presentasi

**Apa yang paling mungkin salah**
- Model mengarang jawaban yang terdengar masuk akal padahal tidak ada di dokumen.
  Mitigasi: skema tetap, kutipan bukti, instruksi "tidak yakin = tidak disebutkan",
  dan filter jarak di RAG.
- Jawaban RAG yang salah sumber jika index tidak lengkap. Mitigasi: rebuild index
  setelah dokumen baru dengan python build_index.py.
- Biaya dan kuota API terbatas; beberapa model besar tidak tersedia di free tier.
  Mitigasi: gunakan model termurah yang masih memadai, dan catat pemakaian tiap
  minggu.
- Dokumen terlalu panjang atau terlalu banyak dapat membuat proses chunking dan
  embedding lebih berat; k default mungkin perlu penyesuaian.

**Rencana Minggu 9–16**
- Uji ekstraksi lebih banyak pada dokumen asli yang lebih panjang dan lebih kompleks.
- Uji ulang perbandingan model di dokumen lebih berat sebelum memutuskan model default.
- Pertahankan dan pertajam RAG: periksa k, kualitas chunking, dan perilaku saat
  konteks saling bertentangan.
- Bangun lapisan penilaian/manajemen lebih lanjut: hasil ekstraksi menjadi bahan,
  bukan pengganti keputusan manusia.
- Siapkan jejak audit dan catatan biaya yang dapat dirujuk nanti.

### B. Ruang visual / catatan pembicara

- Timeline kasar atau tabel: risiko — mitigasi — status.
- Tekankan bahwa rencana ini realistis, bukan janji perfect.

---

# Catatan akhir

- File draf awal: [draft_ppt_privia.md](draft_ppt_privia.md).
- File slide siap pakai: [draft_ppt_privia_slides.md](draft_ppt_privia_slides.md).
- Isi blok B sengaja tidak diisi aset nyata karena butuh foto, diagram, atau kutipan
  asli dari dokumen; petunjuk isotopnya sudah tertulis di tiap blok.
