"""
src/eval/jalankan_set_uji.py — Lapisan 5: jalankan set uji dan hitung angka, bukan kesan.

Cara pakai:
    python -m src.eval.jalankan_set_uji                     # semua kasus yang bisa jalan
    python -m src.eval.jalankan_set_uji --kasus U01 U06     # sebagian kasus
    python -m src.eval.jalankan_set_uji --model gemini-3.5-flash-lite   # BREAK #2
    python -m src.eval.jalankan_set_uji --ulang             # abaikan cache

Kenapa ada cache: kuota gratis Gemini 20 permintaan/hari/model. Menjalankan ulang
kasus yang sama akan memakai kuota tanpa menambah informasi. Cache disimpan di
logs/eval_cache/ dan HANYA dipakai kalau kasus + model + versi prompt sama.

Hasil: logs/hasil-evaluasi-<tag>.json (angka mentah) dan tabel di layar.

Catatan kejujuran: skor otomatis di sini hanya bisa memeriksa hal yang bisa diperiksa
mesin (field acuan, bukti yang benar-benar ada di dokumen, format, penolakan).
Kriteria 3 untuk jawaban bebas tidak bisa dinilai otomatis dan ditandai "manual".
Kalibrasi penilaian manual ada di laporan-evaluasi.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from google.genai import errors as genai_errors

from src.agent.agent import AgentGagal, jalankan_agent
from src.extraction.extractor import BASE_FIELDS, REQUIRED_FIELDS, extract_fields
from src.guardrails.output_check import periksa_ekstraksi, periksa_jawaban

SET_UJI = Path("set-uji/kasus.jsonl")
CACHE_DIR = Path("logs/eval_cache")
HASIL_DIR = Path("logs")

KRITERIA = {
    1: "Menjawab pertanyaan yang benar-benar diajukan",
    2: "Seluruh pernyataan didukung sumber yang dirujuk",
    3: "Tidak ada pernyataan tambahan tanpa dasar",
    4: "Format output valid menurut schema",
    5: "Menolak dengan benar bila memang seharusnya menolak",
}


def muat_kasus() -> list[dict]:
    if not SET_UJI.exists():
        raise FileNotFoundError(f"Set uji tidak ditemukan: {SET_UJI}")
    return [json.loads(b) for b in SET_UJI.read_text(encoding="utf-8").splitlines() if b.strip()]


def _teks_masukan(kasus: dict) -> str:
    """Ambil teks dokumen untuk kasus ekstraksi: entah inline atau potongan berkas."""
    if kasus.get("teks"):
        return kasus["teks"]

    berkas = Path("data/raw") / kasus["berkas"]
    teks = berkas.read_text(encoding="utf-8")
    mulai = kasus.get("mulai")
    if mulai:
        posisi = teks.find(mulai)
        if posisi >= 0:
            teks = teks[posisi:]
    return teks[: kasus.get("panjang", 6000)]


# --- penilaian ---------------------------------------------------------------

def _cek_nilai(nilai: str, aturan: dict) -> bool:
    nilai_norm = str(nilai).strip().lower()
    if "harus" in aturan:
        return nilai_norm == str(aturan["harus"]).lower()
    if "bukan" in aturan:
        return nilai_norm != str(aturan["bukan"]).lower()
    if "mengandung" in aturan:
        return any(k.lower() in nilai_norm for k in aturan["mengandung"])
    raise ValueError(f"Aturan acuan tidak dikenal: {aturan}")


def nilai_ekstraksi(kasus: dict, hasil: dict, dokumen: str) -> dict[int, bool | None]:
    fields = hasil.get("fields") or {}
    acuan = kasus["acuan"]

    c1 = all(_cek_nilai(fields.get(f, ""), aturan) for f, aturan in acuan.items())
    c2 = not periksa_ekstraksi(fields, dokumen)
    # c3: field yang seharusnya kosong tidak diisi; di luar itu butuh penilaian manusia.
    c3 = all(
        str(fields.get(f, "")).strip().lower() == "tidak disebutkan"
        for f, aturan in acuan.items() if aturan.get("harus") == "tidak disebutkan"
    ) if any(a.get("harus") == "tidak disebutkan" for a in acuan.values()) else None
    c4 = all(f in fields for f in REQUIRED_FIELDS)
    semua_kosong = all(str(fields.get(f, "")).strip().lower() == "tidak disebutkan" for f in BASE_FIELDS)
    c5 = semua_kosong if kasus["jenis"] == "tolak" else None
    return {1: c1, 2: c2, 3: c3, 4: c4, 5: c5}


def nilai_rag(kasus: dict, hasil: dict) -> dict[int, bool | None]:
    jawaban = str(hasil.get("answer", ""))
    sumber = hasil.get("sources") or []
    dokumen_sumber = {s.get("source_doc") for s in sumber}
    harus_menolak = kasus["acuan"].get("harus_menolak", False)
    menolak = "tidak ada di dokumen" in jawaban.lower()

    if harus_menolak:
        c1 = menolak
        c5 = menolak
        c3 = menolak  # tidak mengarang = benar-benar menolak
    else:
        kata = kasus["acuan"].get("jawaban_mengandung") or []
        c1 = kasus["acuan"].get("dokumen") in dokumen_sumber and (
            not kata or any(k.lower() in jawaban.lower() for k in kata)
        )
        c5 = None
        c3 = None  # klaim tambahan hanya bisa dinilai manusia

    # Penolakan tidak memuat klaim, jadi tidak ada yang perlu didukung sumber.
    c2 = True if menolak else not periksa_jawaban(jawaban, jumlah_sumber=len(sumber))
    c4 = "answer" in hasil and "sources" in hasil
    return {1: c1, 2: c2, 3: c3, 4: c4, 5: c5}


def nilai_agent(kasus: dict, hasil: dict) -> dict[int, bool | None]:
    jawaban = str(hasil.get("jawaban", "")).lower()
    kata = [k.lower() for k in kasus["acuan"].get("mengandung", [])]
    c1 = bool(jawaban) and all(k in jawaban for k in kata)
    c2 = bool(jawaban) and any(doc.split(".")[0] in jawaban for doc in
                               ["kebijakan-ovo", "kebijakan-shopeepay", "kebijakan-bibit", "kebijakan-tokopedia"])
    return {1: c1, 2: c2, 3: None, 4: hasil.get("status") == "selesai", 5: None}


# --- menjalankan satu kasus --------------------------------------------------

def _kunci_cache(kasus: dict, model: str) -> Path:
    # Kunci hanya bergantung pada INPUT yang dikirim ke sistem, bukan pada jawaban acuan:
    # memperbaiki acuan tidak boleh memaksa panggilan model baru (dan membakar kuota).
    if kasus["target"] == "ekstraksi":
        masukan = _teks_masukan(kasus)
    elif kasus["target"] == "rag":
        masukan = {"pertanyaan": kasus["pertanyaan"], "k": kasus.get("k", 5)}
    else:
        masukan = {"tugas": kasus["tugas"], "max_langkah": kasus.get("max_langkah", 8)}

    bahan = json.dumps({"id": kasus["id"], "target": kasus["target"], "model": model, "input": masukan},
                       ensure_ascii=False, sort_keys=True)
    return CACHE_DIR / f"{kasus['id']}-{hashlib.sha256(bahan.encode()).hexdigest()[:12]}.json"


def _cari_cache(kasus: dict, model: str) -> Path | None:
    """Kunci persis; kalau tidak ada, cari berkas cache lama untuk kasus + model yang sama."""
    persis = _kunci_cache(kasus, model)
    if persis.exists():
        return persis
    if not CACHE_DIR.exists():
        return None
    for kandidat in CACHE_DIR.glob(f"{kasus['id']}-*.json"):
        try:
            isi = json.loads(kandidat.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isi.get("model") == model and isi.get("target") == kasus["target"]:
            return kandidat
    return None


def jalankan_kasus(kasus: dict, model: str, ulang: bool = False) -> dict:
    cache = _cari_cache(kasus, model)
    if cache and not ulang:
        simpan = json.loads(cache.read_text(encoding="utf-8"))
        simpan["dari_cache"] = True
        return simpan

    cache = _kunci_cache(kasus, model)

    mulai = datetime.now()
    target = kasus["target"]

    if target == "ekstraksi":
        dokumen = _teks_masukan(kasus)
        hasil = extract_fields(dokumen, mode="penuh")
        nilai = nilai_ekstraksi(kasus, hasil, dokumen)
        ringkas_hasil = {"fields": hasil.get("fields"), "usage": hasil.get("usage")}

    elif target == "rag":
        from api import ask_rag
        from api import AskRequest as ParamAsk

        hasil = ask_rag(ParamAsk(question=kasus["pertanyaan"], k=kasus.get("k", 5)))
        nilai = nilai_rag(kasus, hasil)
        ringkas_hasil = hasil

    elif target == "agent":
        hasil = jalankan_agent(kasus["tugas"], max_langkah=kasus.get("max_langkah", 8))
        nilai = nilai_agent(kasus, hasil)
        ringkas_hasil = {k: hasil.get(k) for k in
                         ("status", "jawaban", "jumlah_langkah", "token", "biaya_perkiraan_usd", "task_id")}

    else:
        raise ValueError(f"Target tidak dikenal: {target}")

    catatan = {
        "id": kasus["id"],
        "jenis": kasus["jenis"],
        "target": target,
        "model": model,
        "nilai": {str(k): v for k, v in nilai.items()},
        "lulus_semua": all(v for v in nilai.values() if v is not None),
        "hasil": ringkas_hasil,
        "durasi_detik": round((datetime.now() - mulai).total_seconds(), 1),
        "waktu": mulai.isoformat(timespec="seconds"),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(catatan, ensure_ascii=False, indent=2), encoding="utf-8")
    return catatan


def nilai_ulang(kasus: dict, model: str) -> dict | None:
    """
    Hitung ulang skor dari hasil yang sudah di-cache, TANPA memanggil model lagi.

    Dipakai saat aturan penilaian berubah (misalnya batas panjang kutipan diperbaiki):
    angka lama dan baru jadi bisa dibandingkan pada output yang persis sama.
    """
    cache = _cari_cache(kasus, model)
    if cache is None:
        return None

    lama = json.loads(cache.read_text(encoding="utf-8"))
    baru = dict(lama)
    target = kasus["target"]

    if target == "ekstraksi":
        nilai = nilai_ekstraksi(kasus, {"fields": lama["hasil"]["fields"]}, _teks_masukan(kasus))
    elif target == "rag":
        nilai = nilai_rag(kasus, lama["hasil"])
    else:
        nilai = nilai_agent(kasus, {"jawaban": lama["hasil"].get("jawaban", ""),
                                    "status": lama["hasil"].get("status")})

    baru["nilai"] = {str(k): v for k, v in nilai.items()}
    baru["lulus_semua"] = all(v for v in nilai.values() if v is not None)
    baru["nilai_sebelumnya"] = lama.get("nilai")
    cache.write_text(json.dumps(baru, ensure_ascii=False, indent=2), encoding="utf-8")
    baru["dari_cache"] = True
    return baru


# --- rekap -------------------------------------------------------------------

def rekap(daftar: list[dict]) -> dict:
    per_kriteria = {k: {"lulus": 0, "dinilai": 0} for k in KRITERIA}
    per_jenis: dict[str, dict] = {}

    for c in daftar:
        jenis = c["jenis"]
        per_jenis.setdefault(jenis, {"lulus": 0, "total": 0})
        per_jenis[jenis]["total"] += 1
        per_jenis[jenis]["lulus"] += 1 if c["lulus_semua"] else 0
        for k, v in c["nilai"].items():
            if v is None:
                continue
            per_kriteria[int(k)]["dinilai"] += 1
            per_kriteria[int(k)]["lulus"] += 1 if v else 0

    return {"per_kriteria": per_kriteria, "per_jenis": per_jenis,
            "total_kasus": len(daftar), "lulus_semua": sum(1 for c in daftar if c["lulus_semua"])}


def cetak(daftar: list[dict]) -> dict:
    print(f"\n{'ID':5s} {'Jenis':13s} {'Target':10s} {'1':>2s} {'2':>2s} {'3':>2s} {'4':>2s} {'5':>2s}  Lulus")
    print("-" * 62)
    for c in daftar:
        kolom = "".join(
            f"{'V' if c['nilai'][str(k)] else ('-' if c['nilai'][str(k)] is None else 'X'):>3s}"
            for k in KRITERIA
        )
        print(f"{c['id']:5s} {c['jenis']:13s} {c['target']:10s}{kolom}  {'YA' if c['lulus_semua'] else 'tidak'}")

    r = rekap(daftar)
    print("\nPer kriteria:")
    for k, v in r["per_kriteria"].items():
        persen = (100 * v["lulus"] / v["dinilai"]) if v["dinilai"] else 0
        print(f"  {k}. {KRITERIA[k]:55s} {v['lulus']:2d}/{v['dinilai']:2d}  ({persen:.0f}%)")

    print("\nPer jenis kasus:")
    for jenis, v in r["per_jenis"].items():
        print(f"  {jenis:14s} {v['lulus']}/{v['total']}")

    print(f"\nLulus seluruh kriteria: {r['lulus_semua']}/{r['total_kasus']}")
    return r


def main() -> int:
    p = argparse.ArgumentParser(description="Jalankan set uji Privia.")
    p.add_argument("--kasus", nargs="*", help="hanya kasus dengan ID ini")
    p.add_argument("--model", default=None, help="ganti model (mis. gemini-3.5-flash-lite)")
    p.add_argument("--ulang", action="store_true", help="abaikan cache")
    p.add_argument("--nilai-ulang", action="store_true",
                   help="hitung ulang skor dari cache tanpa memanggil model")
    p.add_argument("--tag", default="v1", help="nama berkas hasil")
    args = p.parse_args()

    if args.model:
        import api
        from src.agent import agent as modul_agent
        from src.extraction import extractor

        extractor.MODEL_NAME = args.model
        api.RAG_MODEL = args.model
        modul_agent.MODEL_NAME = args.model
        model = args.model
    else:
        from src.extraction.extractor import MODEL_NAME as model

    kasus = muat_kasus()
    if args.kasus:
        kasus = [k for k in kasus if k["id"] in set(args.kasus)]
        if not kasus:
            print("[GAGAL] Tidak ada kasus yang cocok dengan --kasus.")
            return 2

    hasil: list[dict] = []
    for k in kasus:
        print(f"[{k['id']}] {k['target']} ...", end=" ", flush=True)
        try:
            if args.nilai_ulang:
                h = nilai_ulang(k, model)
                if h is None:
                    print("belum ada di cache — dilewati")
                    continue
            else:
                h = jalankan_kasus(k, model, ulang=args.ulang)
        except genai_errors.ClientError as e:
            if getattr(e, "code", None) == 429:
                print("KUOTA HABIS (429) — sisa kasus dilewati. Jalankan lagi nanti; hasil yang sudah ada di-cache.")
                break
            raise
        except (AgentGagal, ValueError) as e:
            print(f"GAGAL: {e}")
            continue
        print("cache" if h.get("dari_cache") else f"{h['durasi_detik']}s", "->",
              "LULUS" if h["lulus_semua"] else "tidak")
        hasil.append(h)

    if not hasil:
        print("[GAGAL] Tidak ada hasil.")
        return 1

    ringkas = cetak(hasil)
    HASIL_DIR.mkdir(parents=True, exist_ok=True)
    tujuan = HASIL_DIR / f"hasil-evaluasi-{args.tag}.json"
    tujuan.write_text(json.dumps({"model": model, "waktu": datetime.now().isoformat(timespec="seconds"),
                                  "ringkasan": ringkas, "kasus": hasil}, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\nHasil mentah: {tujuan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
