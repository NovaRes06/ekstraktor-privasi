# Catatan Kasus Lapisan 3 (RAG)

Berkas ini adalah rujukan yang disebut di komentar `api.py` (Kasus 3) dan
`src/rag/vectorstore.py` (dasar pemilihan ambang `MAX_RELEVANT_DISTANCE`).
Sebelumnya berkas ini tidak ada, jadi rujukan itu menggantung.

Semua angka di bawah **diukur langsung pada 10 Oktober 2026** terhadap index hasil
`python build_index.py`, memakai embedding `gemini-embedding-001` dan jarak
cosine ChromaDB. **Makin kecil jarak = makin mirip.**

## Isi index saat pengukuran

| Dokumen | Jumlah chunk |
| --- | --- |
| `kebijakan-ovo.txt` | 102 |
| `kebijakan-shopeepay.txt` | 49 |
| `ringkasan-pasal-uu-pdp.md` | 9 |
| `kebijakan-gopay.txt` | 5 |
| **Total** | **165** |

## Ambang `MAX_RELEVANT_DISTANCE = 0.65`

Ambang ini dipilih dari pengukuran, bukan tebakan. Rentang teramati:

| Kelompok | Jarak chunk terdekat | Keputusan |
| --- | --- | --- |
| Query relevan | 0.4205 – 0.4879 | seluruhnya **LOLOS** |
| Query tidak relevan | 0.7641 – 0.8019 | seluruhnya **DIBUANG** |

Jarak 0.65 berada di tengah-tengah, jadi ada margin ±0.16 ke arah mana pun.
Catatan di `vectorstore.py` ("relevan selalu di bawah 0,56, tidak relevan selalu
di atas 0,69") tetap akurat — pengukuran ulang ini bahkan lebih rapat dari itu.

---

## Kasus 1 — query relevan, dokumennya benar-benar jadi sumber

| Query | 3 chunk teratas | Jarak |
| --- | --- | --- |
| Berapa lama OVO menyimpan data pribadi pengguna? | `kebijakan-ovo.txt` | 0.4205, 0.4393, 0.4449 |
| Bagaimana ShopeePay membagikan data pengguna ke pihak ketiga? | `kebijakan-shopeepay.txt` | 0.4661, 0.4831, 0.4879 |
| Apa saja hak subjek data menurut UU PDP? | `ringkasan-pasal-uu-pdp.md` | 0.4258 |

## Kasus 2 — query tidak relevan, jaraknya jauh dan dibuang

| Query | Chunk terdekat | Jarak | Keputusan |
| --- | --- | --- | --- |
| Resep nasi goreng sederhana | `kebijakan-ovo.txt` | 0.7641 | DIBUANG |
| Cuaca di kota Bandung besok | `kebijakan-ovo.txt` | 0.7890 | DIBUANG |
| Cara melatih anjing agar tidak menggonggong | `kebijakan-ovo.txt` | 0.8019 | DIBUANG |

Yang penting di sini: chunk terdekat datang dari dokumen kebijakan privasi yang
isinya sama sekali tidak menjawab. Tanpa ambang, chunk ini tetap dikirim ke model
sebagai "konteks" dan model bisa mengarang jawaban dari konteks yang salah.

## Kasus 3 — tidak ada chunk yang relevan, model TIDAK dipanggil

Ini kasus yang dirujuk komentar `api.py`. Semua chunk melewati ambang, sehingga
`retrieve()` mengembalikan daftar kosong dan endpoint `/ask` menjawab
"Tidak ada di dokumen." **tanpa memanggil Gemini sama sekali** — hemat biaya dan
tidak bergantung pada kedisiplinan model untuk mengaku tidak tahu.

| Query | Chunk lolos ambang | Akibat |
| --- | --- | --- |
| Resep nasi goreng sederhana | 0 | model tidak dipanggil |
| Cuaca di kota Bandung besok | 0 | model tidak dipanggil |

Diverifikasi: `retrieve(query, k=10)` mengembalikan `[]` untuk kedua query di atas.

---

## Perbaikan index 10 Oktober 2026 (penting)

Sebelum `build_index.py` dijalankan ulang, index hanya berisi **14 chunk dari 2
dokumen** — `kebijakan-ovo.txt` dan `kebijakan-shopeepay.txt` sudah ada di
`data/raw/` tetapi tidak pernah ter-index. Akibatnya pertanyaan tentang OVO dan
ShopeePay mengembalikan chunk yang **lolos ambang tapi salah sasaran**:

| Query | Sebelum (14 chunk) | Sesudah (165 chunk) |
| --- | --- | --- |
| Berapa lama OVO menyimpan data pribadi? | `ringkasan-pasal-uu-pdp.md` 0.5661, `kebijakan-gopay.txt` 0.6407 | `kebijakan-ovo.txt` 0.4205 |
| Bagaimana ShopeePay membagikan data ke pihak ketiga? | `ringkasan-pasal-uu-pdp.md` 0.6116 | `kebijakan-shopeepay.txt` 0.4661 |

Pelajarannya: ambang jarak adalah pertahanan tambahan, bukan pengganti. Kalau
dokumennya tidak ada di index, chunk yang tidak relevan bisa saja berada di bawah
ambang. **Jalankan ulang `python build_index.py` setiap kali menambah dokumen di
`data/raw/`.**

## Catatan: `kebijakan-dana.txt` belum tersedia

`fetch_reference_docs.py` mendaftarkan 4 sumber, tapi hanya 3 yang berhasil
diunduh. `https://www.dana.id/policy` gagal 3 kali pada 10 Oktober 2026 (read
timeout 15s dan 30s ×2), kemungkinan karena situsnya lambat atau memblokir
pengambilan otomatis. Berkasnya sengaja tidak dibuat. Kalau nanti berhasil,
tambahkan ke `data/raw/` lalu jalankan ulang `build_index.py`.
