# Analisis Workflow vs Agen — Privia

Tugas Minggu 10: temukan satu tugas di bidang produk yang **tidak selesai** dengan satu
langkah, rancang dalam dua bentuk, bandingkan lima sisi, lalu pilih satu dengan
alasannya.

---

## 1. Tugas yang butuh banyak langkah

**Tugas:** "Bandingkan masa retensi data antara kebijakan OVO dan ShopeePay. Sebutkan
dokumen mana yang menyebutkan berapa lama data disimpan, dan mana yang tidak."

Kenapa tidak selesai dalam satu langkah: untuk menjawabnya sistem harus (a) mencari
bagian yang membahas retensi di **dua dokumen berbeda**, (b) mengekstrak field
`masa_retensi_data` dari masing-masing, lalu (c) membandingkan hasilnya. Langkah (b)
baru bisa dilakukan setelah tahu dokumen mana yang perlu dibuka, dan langkah (c)
bergantung pada hasil (b). Urutannya tidak bisa ditetapkan di awal karena kalau
pencarian pertama sudah menemukan jawaban yang jelas (misalnya OVO menyebut "10
tahun"), pencarian tambahan tidak perlu.

## 2. Rancangan A — workflow tetap

```
[1] cari_dokumen("masa retensi data OVO")        ─┐
[2] cari_dokumen("masa retensi data ShopeePay")  ─┤ selalu dua kali
[3] ambil_field(ovo, masa_retensi_data)          ─┤ selalu dua kali
[4] ambil_field(shopeepay, masa_retensi_data)    ─┘
[5] panggil model: "bandingkan dua hasil ini"    -> jawaban
```

Lima panggilan tetap, urutan pasti, tidak ada keputusan di tengah jalan.

## 3. Rancangan B — agen (yang dipakai)

```
REASON  -> model memilih langkah berikutnya
ACT     -> cari_dokumen / baca_dokumen / ambil_field / simpan_laporan
OBSERVE -> hasil masuk riwayat (dan ke state di logs/agent_state/)
ulangi sampai: selesai · batas 8 langkah · gagal berulang
```

Trace nyata (`logs/agent_trace/5491246a0545.jsonl`), tugas ShopeePay + dasar hukum:

```
1 cari_dokumen({"query": "retensi data penyimpanan penghapusan", "k": 3})  -> 3 chunk
2 ambil_field({"nama_file": "kebijakan-ovo.txt", "field": "masa_retensi_data"})
3 ambil_field({"nama_file": "kebijakan-shopeepay.txt", "field": "masa_retensi_data"})
4 selesai -> jawaban menyebut kedua dokumen
```

## 4. Perbandingan lima sisi

| Sisi | A: workflow tetap | B: agen |
|---|---|---|
| Bisa ditebak | **Ya.** Selalu 5 panggilan, urutan sama. Bisa digambarkan sebelum dijalankan | **Tidak.** Trace di atas 3 langkah; tugas lain bisa 4–6. Tiga kali jalan bisa berbeda urutan |
| Biaya | Tetap: 2 retrieval + 2 ekstraksi + 1 sintesis. Diukur ≈ $0,005–0,007 per tugas | Bervariasi. Terukur $0,0009 (1 langkah) sampai $0,0077 (4 langkah); terburuk pada batas 8 langkah ≈ $0,017 |
| Kemudahan pengujian | **Mudah.** Tiap langkah bisa diuji terpisah; kegagalan jelas di langkah mana | Sulit. Ruang kemungkinan langkah besar; pengujian hanya bisa pada trace yang benar-benar terjadi |
| Penanganan kegagalan | Kaku: kalau OVO tidak ada di index, langkah 3 tetap jalan dan hasilnya kosong | Fleksibel: bisa mencoba kata kunci lain atau dokumen lain setelah hasil pertama |
| Kualitas hasil | Cukup untuk tugas yang polanya pasti; boros kalau salah satu dokumen ternyata tidak relevan | **Lebih baik pada tugas yang bercabang.** Pada kasus ShopeePay, agen menemukan bagian pengungkapan yang tidak terambil oleh jalur RAG satu langkah (U07 gagal, agen berhasil) |

## 5. Pilihan dan kekurangan yang diterima

**Dipilih: B (agen), khusus untuk tugas pembandingan lintas dokumen.** Alasan: tugas
ini memang bercabang — langkah kedua bergantung pada temuan pertama — sehingga
workflow lima langkah tetap akan membuang panggilan ketika satu dokumen ternyata
tidak relevan, dan tidak punya cara mencoba pendekatan lain ketika pencarian pertama
meleset.

**Kekurangan yang saya terima:** hasilnya tidak bisa ditebak persis, biaya terburuk
8× biaya terendah, dan pengujiannya hanya bisa memeriksa trace yang benar-benar
terjadi. Untuk menahan kerugiannya: batas 8 langkah (maksimum keras 20), state
tersimpan di luar percakapan, dan setiap langkah tercatat di trace.

## 6. Bagian yang SENGAJA tetap workflow

| Bagian | Mengapa bukan agen |
|---|---|
| Ekstraksi 9 field | Urutannya pasti: kirim dokumen → periksa schema → ulang sekali kalau melanggar. Tidak ada keputusan yang bergantung pada temuan di tengah jalan |
| Tanya jawab RAG (`/ask`) | Satu retrieval + satu jawaban. Menjadikannya agen berarti menambah 3–4 panggilan untuk pertanyaan yang selesai dalam satu |
| Pemeriksaan bukti & guardrails | Harus deterministik. Guardrail yang "diputuskan model" bukan guardrail |
| Mode ringkas | Proyeksi deterministik dari hasil penuh; panggilan model kedua hanya menambah biaya tanpa informasi baru |

Menjadikan keempat bagian itu agentic akan menaikkan biaya dan ketidakpastian tanpa
menambah kemampuan — persis kerugian yang disebut modul, tanpa manfaatnya.

## 7. Tantangan wajib — biaya untuk 100 permintaan

Memakai angka nyata dari `catatan-pemakaian.md` dan `logs/agent_state/`:

| | Workflow (5 panggilan tetap) | Agen (rata-rata 3,4 langkah dari 9 run tercatat) |
|---|---:|---:|
| Token masuk per tugas | ≈ 2.244 (2 retrieval ≈ 0 + 2 ekstraksi ≈ 2.244 + sintesis kecil) | 901–8.044, median ≈ 5.255 |
| Biaya per tugas | ≈ $0,0050 | ≈ $0,0054 (median) |
| 100 permintaan | ≈ $0,50 | ≈ $0,54, terburuk $1,71 |
| Selisih | — | **≈1,1× rata-rata, sampai 3,4× pada kasus terburuk** |

Apa yang didapat dari selisih itu: kemampuan mencoba pendekatan lain ketika
pencarian pertama meleset — terbukti pada kasus ShopeePay, di mana jalur RAG satu
langkah menolak (U07) sementara agen menemukan jawabannya dalam 4 langkah. Kalau
tugasnya selalu berbentuk sama, selisih ini murni kerugian.
