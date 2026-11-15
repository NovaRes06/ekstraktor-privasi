# Paket Bukti Mingguan — Privia

Folder ini dibuat oleh `buat_bukti.py`. Setiap minggu berisi berkas luaran yang
benar-benar ada, potongan catatan proses format Lampiran C, dan satu zip
`10241058-m<minggu>.zip` yang siap dikumpulkan.

```bash
python buat_bukti.py              # semua minggu 1-13
python buat_bukti.py --minggu 13  # satu minggu
python buat_bukti.py --tanpa-zip  # folder saja
```

| Minggu | Judul | Berkas | Kekurangan tercatat |
|---:|---|---:|---:|
| 1 | Orientasi: tiga persoalan, satu peta | 3 | 3 |
| 2 | Anatomi: token, context window, temperature, hallucination | 4 | 2 |
| 3 | Lingkungan kerja dan model gateway | 5 | 0 |
| 4 | Prompt terstruktur dan lembar tema | 7 | 1 |
| 5 | Structured output dan schema sebagai aturan | 4 | 0 |
| 6 | Tool calling | 3 | 0 |
| 7 | Konsep embedding dan retrieval | 6 | 0 |
| 8 | UTS: presentasi rancangan sistem | 5 | 2 |
| 9 | Merakit RAG utuh | 6 | 2 |
| 10 | Dari workflow ke agent | 4 | 1 |
| 11 | Tool, memory, dan tugas banyak langkah | 8 | 1 |
| 12 | Studi kasus praktisi dan peer review | 4 | 3 |
| 13 | Guardrails, batas akses, dan human-in-the-loop | 8 | 1 |

Kekurangan **tidak diisi dengan karangan**. Daftar lengkapnya ada di README tiap
paket dan di `lembar-tema.md`/`README.md` bagian keterbatasan.
