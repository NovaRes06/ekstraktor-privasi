"""
run_agent.py — jalankan agen dari terminal (Lapisan 4).

Contoh:
    python run_agent.py "Bandingkan masa retensi data OVO dan ShopeePay."
    python run_agent.py --lanjut 3f9c1a2b4d5e --izin-simpan
    python run_agent.py --trace 3f9c1a2b4d5e

Tanpa --izin-simpan, agen akan BERHENTI sebelum menyimpan laporan (tindakan yang
tidak bisa dibatalkan) dan menampilkan persis apa yang akan ditulis.
"""

import argparse
import json
import sys

from src.agent.agent import AgentGagal, baca_trace, jalankan_agent, lanjutkan_agent
from src.guardrails.input_filter import InputDitolak


def _cetak(hasil: dict) -> None:
    print(f"\nStatus   : {hasil.get('status')}")
    print(f"Task ID  : {hasil.get('task_id')}")
    print(f"Langkah  : {hasil.get('jumlah_langkah')}/{hasil.get('batas_langkah')}")
    print(f"Token    : masuk {hasil.get('token', {}).get('masuk')}, keluar {hasil.get('token', {}).get('keluar')}")
    print(f"Biaya    : ${hasil.get('biaya_perkiraan_usd')} (perkiraan, tarif promo)")

    riwayat = hasil.get("riwayat") or []
    if riwayat:
        print("\nLangkah yang diambil:")
        for r in riwayat:
            print(f"  {r['langkah']}. {r['aksi']}({json.dumps(r['argumen'], ensure_ascii=False)[:110]})")
            if r.get("alasan"):
                print(f"     alasan: {r['alasan'][:150]}")

    if hasil.get("jawaban"):
        print(f"\nJAWABAN:\n{hasil['jawaban']}")

    for pesan in hasil.get("guardrail") or []:
        print(f"\n[GUARDRAIL] {pesan}")

    if hasil.get("pesan"):
        print(f"\n{hasil['pesan']}")

    if hasil.get("usulan"):
        u = hasil["usulan"]
        print("\n--- MENUNGGU PERSETUJUAN MANUSIA ---")
        print(f"Aksi        : {u['aksi']}")
        print(f"Alasan agen : {u['alasan_agen']}")
        print(f"Akan menulis: {u['akan_menulis_ke']} ({u['jumlah_karakter']} karakter)")
        print(f"Isi (cuplikan):\n{u['cuplikan_isi']}")
        print(f"\nLanjutkan dengan: {hasil['cara_melanjutkan']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Jalankan agen Privia dari terminal.")
    parser.add_argument("tugas", nargs="?", help="tugas dalam bahasa bebas")
    parser.add_argument("--lanjut", metavar="TASK_ID", help="lanjutkan tugas yang berhenti")
    parser.add_argument("--trace", metavar="TASK_ID", help="tampilkan trace tugas")
    parser.add_argument("--izin-simpan", action="store_true", help="setujui tindakan menulis laporan")
    parser.add_argument("--max-langkah", type=int, default=8, help="batas langkah (1-20)")
    args = parser.parse_args()

    try:
        if args.trace:
            for entri in baca_trace(args.trace):
                print(json.dumps(entri, ensure_ascii=False))
            return 0

        if args.lanjut:
            hasil = lanjutkan_agent(args.lanjut, izin_simpan=args.izin_simpan)
        elif args.tugas:
            hasil = jalankan_agent(args.tugas, izin_simpan=args.izin_simpan, max_langkah=args.max_langkah)
        else:
            parser.print_help()
            return 2
    except (AgentGagal, InputDitolak) as e:
        print(f"[GAGAL] {e}", file=sys.stderr)
        return 1

    _cetak(hasil)
    return 0 if hasil.get("status") in {"selesai", "butuh_persetujuan"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
