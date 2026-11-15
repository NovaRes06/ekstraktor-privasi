"""Membuat paket bukti mingguan Privia (bukti/mNN + zip 10241058-mNN.zip).

Prinsip:
- Hanya menyalin berkas yang benar-benar ada di repositori. Berkas yang tidak ada
  TIDAK dibuat, dan dicatat sebagai kekurangan di README paket.
- Bagian catatan proses tiap minggu diambil dari docs/catatan-proses.md, bukan ditulis ulang.
- Tidak ada isi yang dikarang: semua daftar di bawah menunjuk ke berkas nyata.

Pakai:
    python buat_bukti.py              # semua minggu 1-13
    python buat_bukti.py --minggu 13  # satu minggu
    python buat_bukti.py --tanpa-zip
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

AKAR = Path(__file__).resolve().parent
NIM = "10241058"
SUMBER_CATATAN = AKAR / "docs" / "catatan-proses.md"
FOLDER_BUKTI = AKAR / "bukti"

# Setiap minggu: judul, berkas sumber (relatif terhadap akar repo), dan kekurangan
# yang memang belum ada. Daftar ini sengaja konservatif.
MINGGU: dict[int, dict[str, object]] = {
    1: {
        "judul": "Orientasi: tiga persoalan, satu peta",
        "berkas": [
            "logs/break-minggu1.json",
            "uji_break_minggu1.py",
        ],
        "belum": [
            "docs/minggu-1-pemetaan-persoalan.md (dirujuk, berkas tidak ada)",
            "docs/minggu-1-Ekstraktor-Privasi.md (dirujuk, berkas tidak ada)",
            "Tantangan wajib: contoh nyata AI dipakai untuk persoalan yang salah",
        ],
    },
    2: {
        "judul": "Anatomi: token, context window, temperature, hallucination",
        "berkas": [
            "logs/perbandingan_model.json",
            "compare_models.py",
            "data/sample_kebijakan.txt",
        ],
        "belum": [
            "Laporan pengamatan minggu ini belum ada sebagai berkas terpisah",
            "Empat butir BREAK berstatus tidak tercatat (lihat catatan proses)",
        ],
    },
    3: {
        "judul": "Lingkungan kerja dan model gateway",
        "berkas": [
            "logs/perbandingan_model.json",
            "compare_models.py",
            "catatan-pemakaian.md",
            "requirements.txt",
        ],
        "belum": [],
    },
    4: {
        "judul": "Prompt terstruktur dan lembar tema",
        "berkas": [
            "instruksi/v1.md",
            "instruksi/CATATAN.md",
            "logs/uji_v1_v2.md",
            "logs/uji_v1_v2.json",
            "data/test_cases/uji_v1_v2.py",
            "lembar-tema.md",
        ],
        "belum": [
            "Uji 5 input tidak selesai penuh: 6 dari 10 percobaan kena kuota 429",
        ],
    },
    5: {
        "judul": "Structured output dan schema sebagai aturan",
        "berkas": [
            "instruksi/v2.md",
            "instruksi/CATATAN.md",
            "src/extraction/extractor.py",
        ],
        "belum": [],
    },
    6: {
        "judul": "Tool calling",
        "berkas": [
            "api.py",
            "tests/test_api.py",
        ],
        "belum": [],
    },
    7: {
        "judul": "Konsep embedding dan retrieval",
        "berkas": [
            "src/rag/chunker.py",
            "src/rag/embedder.py",
            "src/rag/vectorstore.py",
            "build_index.py",
            "data/raw/SUMBER.md",
        ],
        "belum": [],
    },
    8: {
        "judul": "UTS: presentasi rancangan sistem",
        "berkas": [
            "rancangan-sistem.md",
            "rancangan-rag.md",
            "draft_ppt_privia_slides.md",
            "draft_ppt_privia.md",
        ],
        "belum": [
            "Bukti pelaksanaan presentasi UTS tidak tercatat di repositori",
            "Peer review UTS (2 rekan) belum diisi: lihat peer-review/template-uts.md",
        ],
    },
    9: {
        "judul": "Merakit RAG utuh",
        "berkas": [
            "build_index.py",
            "src/rag/vectorstore.py",
            "set-uji/kasus.jsonl",
            "set-uji/README.md",
            "logs/lapisan3_rag_cases.md",
        ],
        "belum": [
            "Sepuluh pertanyaan uji RAG: yang ada enam",
            "U07 (pengungkapan pihak ketiga ShopeePay) masih gagal",
        ],
    },
    10: {
        "judul": "Dari workflow ke agent",
        "berkas": [
            "analisis-workflow-vs-agen.md",
            "logs/agent_trace/5a9065eaec60.jsonl",
            "logs/agent_state/5a9065eaec60.json",
        ],
        "belum": [
            "Empat percobaan BREAK tanpa catatan prediksi lebih dulu",
        ],
    },
    11: {
        "judul": "Tool, memory, dan tugas banyak langkah",
        "berkas": [
            "src/agent/agent.py",
            "src/agent/tools.py",
            "run_agent.py",
            "instruksi/agent-v1.md",
            "logs/agent_trace/a2b5516db110.jsonl",
            "logs/agent_state/a2b5516db110.json",
            "logs/laporan-agent/perbandingan-retensi.md",
        ],
        "belum": [
            "Trace \"sebelum\" perbaikan prompt tidak tersimpan sebagai berkas",
        ],
    },
    12: {
        "judul": "Studi kasus praktisi dan peer review",
        "berkas": [
            "peer-review/README.md",
            "peer-review/template-uts.md",
            "peer-review/template-minggu-12.md",
        ],
        "belum": [
            "Dua lembar peer review Minggu 12 belum diisi (template sudah tersedia)",
            "Dua lembar peer review UTS belum diisi",
            "Tantangan wajib Minggu 12 belum tercapai karena peer review belum ada",
        ],
    },
    13: {
        "judul": "Guardrails, batas akses, dan human-in-the-loop",
        "berkas": [
            "guardrails.md",
            "src/guardrails/input_filter.py",
            "src/guardrails/output_check.py",
            "tests/test_guardrails.py",
            "uji_serangan.py",
            "logs/uji-serangan.json",
            "logs/agent_trace/a2b5516db110.jsonl",
        ],
        "belum": [
            "Serangan #2 dan #5 berstatus TIDAK TERUJI (kuota 429)",
        ],
    },
}


def bagian_minggu(nomor: int) -> str:
    """Ambil bagian satu minggu dari docs/catatan-proses.md apa adanya."""
    if not SUMBER_CATATAN.exists():
        return ""
    teks = SUMBER_CATATAN.read_text(encoding="utf-8")
    penanda = f"# MINGGU {nomor} —"
    mulai = teks.find(penanda)
    if mulai == -1:
        return ""
    berikut = teks.find("# MINGGU ", mulai + len(penanda))
    potong = teks[mulai:berikut if berikut != -1 else len(teks)]
    return potong.rstrip().removesuffix("---").rstrip() + "\n"


def buat_paket(nomor: int, info: dict[str, object], dengan_zip: bool) -> tuple[Path, int, int]:
    nama = f"{NIM}-m{nomor:02d}"
    tujuan = FOLDER_BUKTI / f"m{nomor:02d}"
    if tujuan.exists():
        shutil.rmtree(tujuan)
    tujuan.mkdir(parents=True)

    tersalin: list[str] = []
    hilang: list[str] = []
    for relatif in info["berkas"]:  # type: ignore[union-attr]
        sumber = AKAR / relatif
        if not sumber.exists():
            hilang.append(relatif)
            continue
        target = tujuan / relatif
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sumber, target)
        tersalin.append(relatif)

    catatan = bagian_minggu(nomor)
    if catatan:
        (tujuan / f"catatan-proses-m{nomor:02d}.md").write_text(catatan, encoding="utf-8")
        tersalin.append(f"catatan-proses-m{nomor:02d}.md")

    baris = [
        f"# Paket Bukti Minggu {nomor} — {info['judul']}",
        "",
        "Nama : Nova Reswara",
        f"NIM : {NIM}",
        "Kode peserta K : 5",
        "",
        "## Isi paket",
        "",
        "| Berkas | Ukuran |",
        "|---|---:|",
    ]
    for relatif in tersalin:
        ukuran = (tujuan / relatif).stat().st_size
        baris.append(f"| `{relatif}` | {ukuran:,} B |".replace(",", "."))
    if hilang:
        baris += ["", "**Berkas yang tercantum di daftar tetapi tidak ditemukan saat pembuatan:**", ""]
        baris += [f"- `{h}" for h in hilang]

    kekurangan = list(info["belum"])  # type: ignore[arg-type]
    baris += ["", "## Yang belum ada pada minggu ini", ""]
    if kekurangan:
        baris += [f"- {k}" for k in kekurangan]
    else:
        baris += ["- Tidak ada kekurangan yang tercatat."]

    baris += [
        "",
        "## Catatan",
        "",
        "- Paket ini dibuat oleh `buat_bukti.py` dan hanya berisi berkas yang benar-benar",
        "  ada di repositori; tidak ada berkas atau isi yang dikarang.",
        "- Catatan proses diambil apa adanya dari `docs/catatan-proses.md` (format Lampiran C).",
        "",
    ]
    (tujuan / "README.md").write_text("\n".join(baris), encoding="utf-8")

    zip_path = FOLDER_BUKTI / f"{nama}.zip"
    if dengan_zip:
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for berkas in sorted(tujuan.rglob("*")):
                if berkas.is_file():
                    zf.write(berkas, f"{nama}/{berkas.relative_to(tujuan).as_posix()}")
    return tujuan, len(tersalin), len(kekurangan)


def tulis_indeks(hasil: dict[int, tuple[int, int]]) -> None:
    baris = [
        "# Paket Bukti Mingguan — Privia",
        "",
        "Folder ini dibuat oleh `buat_bukti.py`. Setiap minggu berisi berkas luaran yang",
        "benar-benar ada, potongan catatan proses format Lampiran C, dan satu zip",
        f"`{NIM}-m<minggu>.zip` yang siap dikumpulkan.",
        "",
        "```bash",
        "python buat_bukti.py              # semua minggu 1-13",
        "python buat_bukti.py --minggu 13  # satu minggu",
        "python buat_bukti.py --tanpa-zip  # folder saja",
        "```",
        "",
        "| Minggu | Judul | Berkas | Kekurangan tercatat |",
        "|---:|---|---:|---:|",
    ]
    for nomor in sorted(MINGGU):
        jumlah, kurang = hasil.get(nomor, (0, 0))
        baris.append(f"| {nomor} | {MINGGU[nomor]['judul']} | {jumlah} | {kurang} |")
    baris += [
        "",
        "Kekurangan **tidak diisi dengan karangan**. Daftar lengkapnya ada di README tiap",
        "paket dan di `lembar-tema.md`/`README.md` bagian keterbatasan.",
        "",
    ]
    (FOLDER_BUKTI / "README.md").write_text("\n".join(baris), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Membuat paket bukti mingguan Privia.")
    parser.add_argument("--minggu", type=int, action="append", help="minggu tertentu (boleh diulang)")
    parser.add_argument("--tanpa-zip", action="store_true", help="jangan buat zip")
    arg = parser.parse_args()

    if arg.minggu:
        salah = [m for m in arg.minggu if m not in MINGGU]
        if salah:
            print(f"Minggu tidak dikenal: {salah}")
            return 2
        dipilih = sorted(set(arg.minggu))
    else:
        dipilih = sorted(MINGGU)

    FOLDER_BUKTI.mkdir(exist_ok=True)
    hasil: dict[int, tuple[int, int]] = {}
    for nomor in dipilih:
        tujuan, jumlah, kurang = buat_paket(nomor, MINGGU[nomor], not arg.tanpa_zip)
        hasil[nomor] = (jumlah, kurang)
        print(f"m{nomor:02d}: {jumlah} berkas, {kurang} kekurangan -> {tujuan.relative_to(AKAR)}")

    if not arg.minggu:
        tulis_indeks(hasil)
        print(f"Indeks: {(FOLDER_BUKTI / 'README.md').relative_to(AKAR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
