# Set Uji — Privia

Berkas ini menjelaskan isi `set-uji/`: 18 kasus, jawaban acuan, dan kriteria
penilaian yang bisa dipakai orang lain tanpa bertanya kepada saya.

- `kasus.jsonl` — satu kasus per baris (format JSON Lines), dibaca oleh
  `src/eval/jalankan_set_uji.py`.
- `README.md` — dokumen ini: komposisi, cara menjalankan, cara membaca hasil.

## 1. Komposisi (18 kasus)

Minimum modul: `12 + (K mod 6)` = 12–17 kasus. Delapan belas memenuhi untuk K berapa pun.

| Jenis | ID | Jumlah | Porsi | Isi |
|---|---|---:|---:|---|
| Umum | U01–U07, A01 | 8 | 44% | Ekstraksi 4 kebijakan nyata, 3 pertanyaan RAG, 1 tugas agen |
| Batas | B01–B04 | 4 | 22% | 4 kategori retensi berbeda; dokumen nyaris kosong; GoPay tanpa retensi; pertanyaan yang jawabannya tidak ada |
| Tolak | T01–T03 | 3 | 17% | Resep nasi goreng (ekstraksi + RAG), cuaca Bandung |
| Pernah gagal | P01–P03 | 3 | 17% | Injeksi di dokumen; halusinasi "selama akun aktif"; retrieval UU PDP salah sasaran |

## 2. Bentuk satu kasus

```json
{"id": "U05", "jenis": "umum", "target": "ekstraksi",
 "teks": "…isi dokumen…",
 "acuan": {"jenis_data_dikumpulkan": {"bukan": "tidak disebutkan"},
           "transfer_lintas_negara": {"harus": "tidak disebutkan"}},
 "catatan": "mengapa kasus ini ada"}
```

Kolom `target` menentukan jalur yang diuji:

| Target | Masukan | Yang dinilai |
|---|---|---|
| `ekstraksi` | `teks`, atau `berkas` + `mulai` + `panjang` (potongan dari `data/raw/`) | 18 key schema + nilai field acuan + bukti verbatim |
| `rag` | `pertanyaan`, `k` | dokumen sumber + kata kunci jawaban + `guardrail` |
| `agent` | `tugas`, `max_langkah` | status selesai + jawaban menyebut dokumen |

Aturan acuan yang dikenal skrip:

- `{"harus": "tidak disebutkan"}` — nilai field harus persis itu;
- `{"bukan": "tidak disebutkan"}` — field harus terisi;
- `{"mengandung": ["kata", "lain"]}` — nilai harus memuat salah satu;
- `{"harus_menolak": true}` — jawaban RAG harus "Tidak ada di dokumen.";
- `{"dokumen": "nama.txt", "jawaban_mengandung": [...]}` — sumber harus muncul dan jawaban memuat kata kunci.

## 3. Cara menjalankan

```bash
python -m src.eval.jalankan_set_uji                          # semua kasus (cache dipakai)
python -m src.eval.jalankan_set_uji --kasus U05 B01 T01      # sebagian
python -m src.eval.jalankan_set_uji --ulang                  # paksa panggil model lagi
python -m src.eval.jalankan_set_uji --nilai-ulang            # nilai ulang dari cache, tanpa API
python -m src.eval.jalankan_set_uji --model gemini-3.5-flash-lite --tag lite
```

Hasil mentah ditulis ke `logs/hasil-evaluasi-<tag>.json`. Kolom tabel:
`V` = lulus, `X` = gagal, `-` = tidak berlaku untuk kasus itu.

## 4. Lima kriteria ya/tidak

1. Menjawab pertanyaan yang benar-benar diajukan
2. Seluruh pernyataan didukung sumber yang dirujuk
3. Tidak ada pernyataan tambahan tanpa dasar
4. Format output valid menurut schema
5. Menolak dengan benar bila memang seharusnya menolak

Kriteria 3 pada jawaban bebas **tidak** dinilai otomatis; di tabel ia muncul `-`.
Kriteria 5 hanya berlaku untuk kasus yang memang harus ditolak.

## 5. Cara membaca hasil dengan jujur

- `V` pada kriteria 2 berarti bukti **ditemukan apa adanya** di dokumen, bukan
  "kelihatannya masuk akal". Dua kasus gagal justru karena ini.
- Kasus yang ditandai `-` tidak boleh dihitung sebagai lulus maupun gagal; persen
  dihitung hanya dari yang dinilai.
- Satu kali jalan bukan bukti kestabilan. Variance belum terukur (lihat
  `laporan-evaluasi.md` §4).
- Kasus agen A01 dijalankan dengan model berbeda dari 17 kasus lain karena kuota
  harian; itu dicatat di laporan.
