# Draft PPT — Privia: Ekstraktor & Penjawab Kebijakan Privasi

> Templat 8 halaman. Isi akhir di sebelah kanan masih kosong sampai data lapangan
> masuk; bagian "yang akan diisi" sudah dicatat biar nggak lupa saat presentasi.

---

## Slide 1 — Persoalan

**Siapa yang mengalaminya:**
- Pengguna aplikasi dompet digital / fintech (GoPay, OVO, DANA, ShopeePay) yang
  ingin tahu apa yang terjadi dengan datanya, tapi kebijakan privasi biasanya panjang,
  berbahasa hukum, dan sulit discan dalam waktu singkat.
- Pihak yang meninjau kepatuhan internal (kurang formal di projek ini) yang butuh
  pemetaan cepat 9 aspek UU PDP dari teks kebijakan.

**Bagaimana diselesaikan sekarang:**
- Membaca manual dokumen per halaman, menandai sendiri bagian yang relevan, lalu
  menyusun catatan sendiri. Kalau cuma mau tahu "berapa lama data disimpan", tetap
  harus memindai keseluruhan teks.

**Mengapa belum cukup:**
- manusia analysa satu dokumen dalam hitungan menit, tapi prosesnya tidak terstruktur:
  sulit dibandingkan antar dokumen, dan mudah kelewatan bagian yang tidak disebutkan
  secara eksplisit.
- Tanpa dasar kutipan, temuan "tidak disebutkan" gampang dipertanyakan: apakah
  memang tidak ada, atau hanya luput dari mata?

> [Bagian kanan: contoh 1 screenshot kebijakan panjang / atau kutipan pendek.]

---

## Slide 2 — Mengapa AI generatif

**Tugas inti:** baca teks bebas, pahami maksud, lalu petakan ke 9 kategori tetap.

**Mengapa bukan basis data biasa:**
- Ada 9 field yang harus diisi; kalau pakai basis data / formulir, yang bisa
  didapat hanya data yang sudah terstruktur di dokumen — padahal kebanyakan dokumen
  tidak begitu. Kalau informasi tidak tertulis, basis data tidak bisa memberi
  jawaban "tidak disebutkan" secara bermakna.

**Mengapa bukan formulir statis:**
- Setiap dokumen menulis hal sama dengan cara berbeda (bahasa hukum, susunan beda,
  ada yang hanya berkisar sebagian aspek). Formulir kaku tidak fleksibel cukup
  untuk menangkap arti di balik variasi itu.

**Mengapa bukan aturan biasa:**
- Aturan ekstraksi berbasis regex / kata kunci mudah break saat ada variasi redaksi;
  dokumen asli tidak konsisten; aturan juga tidak punya cara "tidak yakin = tidak
  disebutkan" yang terdengar masuk akal tapi salah.

**Posisi AI generatif di sini:**
- AI dipakai sebagai pembaca yang bisa memparafrase dan mengejar arti, bukan
  pengganti penilaian kepatuhan. Outputnya selalu dikunci ke skema tetap lengkap
  dengan kutipan sumber.
- Kalau informasi tidak ada, respons yang diinginkan adalah "tidak disebutkan"
  — bukan tebakan. Itu perbedaan utama dengan penggunaan AI yang bebas.

> [Bagian kanan: perbandingan singkat 4 pendekatan terhadap persoalan yang sama.]

---

## Slide 3 — Rancangan sistem (satu alur)

Alur utama dalam projek ini ada dua sisi:

**Sisi A — Ekstraksi langsung**
```
Teks kebijakan / URL publik
  → (kalau URL) fetch + bersihkan HTML
  → endpoint /extract atau /extract-from-url
  → Ekstraksi 9 field + 9 kutipan bukti
  → JSON terstruktur (skema wajib, dipaksa dari sisi kode)
  → ditampilkan di Privia (app.py / Streamlit)
```

**Sisi B — Tanya-jawab berbasis dokumen (RAG)**
```
Dokumen di data/raw/
  → chunk (per heading / per ~150 kata + overlap 30)
  → embedding (gemini-embedding-001)
  → ChromaDB (chroma_db/)
      dipakai tiap ada dokumen baru atau berubah

Saat jawab:
Pertanyaan → embedding pertanyaan
  → ambil k chunk terdekat (default k=5, rentang 1–50)
  → buang chunk dengan jarak > 0.65
  → susun konteks bernomor [1], [2], ...
  → kirim ke gemini-3.6-flash dengan system prompt RAG
  → jawaban + rujukan inline + daftar chunk sumber + jarak
```

**Catatan arsitektur singkat:**
- API dipisah dari antarmuka: `api.py` (FastAPI) vs `app.py` (Streamlit).
- Punya endpoint /health buat cek status.
- Batas akses: tool /fetch-url hanya izinkan halaman publik.

> [Bagian kanan: satu diagram alur kolom dari kiri ke kanan.]

---

## Slide 4 — Kendali output

**Schema**
- Ekstraksi wajib menghasilkan 9 field (versi v1) atau 18 field (v2: 9 field +
  9 kutipan bukti), sesuai skema di instruksi/v1.md dan instruksi/v2.md.
- Dari sisi kode, `response_mime_type="application/json"` digunakan supaya Gemini
  mengekspos respons dalam bentuk JSON; validasi skema tetap perlu dicek
  (hasil parsing JSON dari API yang kembali).

**Nilai valid yang diakui**
- Jika informasi ada di dokumen: parafrase maksimal 2 kalimat, Bahasa Indonesia,
  bukan salin kalimat asli panjang. Untuk v2, setiap field disertai kutipan
  langsung sebagai bukti.
- Jika informasi tidak ada: isi persis `"tidak disebutkan"` dan (untuk v2)
  `bukti_<field>` juga `"tidak disebutkan"`.
- Tidak boleh membuat informasi yang tidak ada di teks.

**Penanganan output tidak valid**
- Kalau respons dari model gagal di-parse sebagai JSON, sistem lempar
  HTTP 422 dengan detail error (lihat api.py, except ValueError).
- Strategi utama bukan cuma "kirim lagi", tapi mencegah dari awal:
  prompt tegas, response_mime_type, dan (hasil uji) penekanan pada
  "jangan mengarang".
- Edge yang belum tertutup: validasi isi logika (mis. field benar-benar
  sesuai teks) masih mengandalkan pemeriksaan manusia / uji kasus tambahan,
  bukan sekadar validasi struktur JSON.

> [Bagian kanan: skema JSON mini (9 field / atau 18 field) atau kutipan dari v2.]

---

## Slide 5 — Tool

**Tool utama dalam projek**
- Gemini API (ekstraksi kebijakan + embedding RAG). Model utama: gemini-3.6-flash.
- ChromaDB lokal (folder chroma_db/) untuk menyimpan chunk + embedding.
- FastAPI (api.py) dan Streamlit (app.py) sebagai bungkus antarmuka.
- BeautifulSoup + requests untuk mengambil dan membersihkan halaman publik.

**Batas akses tool**
- Endpoint `/fetch-url` dan `/extract-from-url` hanya boleh mengambil halaman publik.
  Host internal, IP privat/loopback, dan nama yang resolve ke alamat tidak publik
  ditolak dengan HTTP 403 sebelum permintaan keluar (SSRF).
- Default batas panjang teks yang diambil dari URL dibatasi (simoler ~20.000 karakter
  dalam implementasi saat ini) sebagai jaga-jaga.

**Yang perlu persetujuan manusia**
- Keputusan akhir kepatuhan / status "patuh-tidak" tidak dibuat otomatis sama sekali:
  sistem ini ekstrak terstruktur dan menyediakan bukti, tapi penilaian substansi
  tetap human-in-the-loop (direka ulang di rancangan sebagai layer yang sengaja
  tidak agentic).
- Persetujuan layak juga untuk: menambah dokumen rujukan, mengubah index, atau
  mengubah batas ambang jarak.

> [Bagian kanan: tabel tool vs peran / atau batasan akses.]

---

## Slide 6 — Grounding

**Dokumen rujukan**
- Kebijakan publik: OVO, ShopeePay, GoPay, DANA (masing-masing diunduh dan disimpan
  di data/raw/). Ringkasan pasal UU PDP No. 27/2022 juga dimasukkan sebagai konteks
  hukum.

**Chunking**
- Dokumen markdown terstruktur (ada `## `) dipecah per heading.
- Dokumen teks polos dipecah per ~150 kata dengan overlap 30 kata.
- Alasan: satu topik kebijakan biasanya utuh di satu bagian; overlap mencegah
  informasi penting terpotong di batas chunk.

**Retrieval**
- Embedding dibuat dengan gemini-embedding-001.
- Saat pertanyaan masuk, sistem mengambil k chunk terdekat (default 5, bisa diatur
  per request 1–50).
- Chunk yang terlalu jauh dibuang sebelum dikirim ke model:
  ambang `MAX_RELEVANT_DISTANCE = 0.65`.

**Apa yang terjadi kalau jawaban tidak ditemukan**
- Jika tidak ada chunk yang lolos ambang, endpoint /ask tidak memanggil model dan
  langsung menjawab "Tidak ada di dokumen." (hemat biaya + jujur).
- System prompt RAG juga menegaskan hal yang sama: jika tidak ada di konteks,
  jawab persis "Tidak ada di dokumen.", jangan tebak atau jawab dari pengetahuan umum.
- Jika model menolak merespons (mis. respons kosong karena penyaringan konten),
  sistem tetap menyampaikan keadaan itu dengan transparan, bukan mengarang jawaban.

> [Bagian kanan: visualisasi 2 lapis pertahanan: filter jarak + instruksi "jangan
> mengarang".]

---

## Slide 7 — Bukti sejauh ini

**Satu keberhasilan yang ditemukan sendiri**
- Pada uji v1 vs v2, system prompt v2 berhasil menghasilkan 9/9 field bukti
  pada kasus umum_1, sementara v1 tidak memiliki field bukti sama sekali.
- Artinya v2 memenuhi mandat "setiap field disertai kutipan sumber" yang memang
  belum ada di v1. Biayanya wajar: tambahan ~2,15 detik karena output lebih panjang.
  Sumber: logs/uji_v1_v2.md dan logs/uji_v1_v2.json.

**Satu kegagalan / batas yang ditemukan sendiri**
- Uji terhadap dokumen kosong (batas_1_kosong_isi) dan dokumen yang bukan kebijakan
  (seharusnya_ditolak: "resep nasi goreng") masuk ke kategori "seharusnya ditolak /
  tidak relevan" — dan RAG punya pertahanan relevan untuk itu.
- Namun, persis di bagian ekstraksi, ditemukan realitas praktis: kuota harian
  Gemini free tier terbatas dan menahan penyelesaian uji.
  Setelah ~20 request/hari/proyek habis, sisa kasus tidak bisa diukur saat itu.
  Jadi ini bukan bug sistem, tapi batas operasional yang perlu direncanakan
  (log, jadwal ulang, atau stepping ke tier berbayar kalau perlu skalakan).
  Sumber: logs/uji_v1_v2.md.

> [Bagian kanan: rekap singkat 1 berhasil / 1 gagal, bukan klaim "semua bagus".]

---

## Slide 8 — Risiko dan rencana Minggu 9–16

**Apa yang paling mungkin salah**
- Hallusinasi / bermakna "tidak disebutkan" tapi diganti teks yang terdengar masuk akal.
  Mitigasi utama sudah ada: skema tetap, kutipan bukti, instruksi "tidak yakin = tidak
  disebutkan", dan filter jarak di RAG. Tapi tetap perlu uji lebih banyak dokumen asli.
- Jawaban RAG yang salah sumber jika index tidak lengkap. Mitigasi: selalu rebuild index
  setelah dokumen baru (`python build_index.py`). Catatan lapangan: index awal cuma
  berisi sedikit chunk, dan itu sempat bikin hasil "lolos ambang tapi salah sasaran".
- Biaya / kuota API. Beberapa model kelas besar tidak tersedia di free tier, dan
  kuota harian terbatas. Mitigasi: gunakan model termurah yang masih memadai untuk
  tugas ini (studi perbandingan Flash vs Flash-Lite menunjukkan hasil tak-terbedakan
  untuk dokumen ringkas), dan catat pemakaian per minggu (catatan di catatan-pemakaian.md).
- Dokumen terlalu panjang / banyak → chunk dan embedding bisa makin berat, dan k
  default perlu penyesuaian.

**Rencana Minggu 9–16**
- Perluasan uji ekstraksi ke dokumen asli yang lebih panjang dan lebih kompleks,
  bukan hanya versi ringkas.
- Uji ulang perbandingan model di dokumen yang lebih berat sebelum memutuskan model
  default.
- Pertahankan & polish hasil RAG: cekribulan k (jumlah chunk), kualitas chunking,
  dan perilaku saat konteks saling bertentangan.
- Bangun lapisan 4–5 (penilaian/manajemen) sesuai rencana proyek: hasil ekstraksi
  jadi bahan, bukan pengganti keputusan manusia. Siapkan jejak audit / laporan biaya
  yang bisa dirujuk nanti.

> [Bagian kanan: timeline kasar atau tabel risiko vs mitigasi.]
