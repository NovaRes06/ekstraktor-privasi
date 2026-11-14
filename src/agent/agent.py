"""
src/agent/agent.py — Lapisan 4: agent multi-langkah dengan batas langkah, state, dan trace.

Rancangan yang dipilih (bandingkan dengan `analisis-workflow-vs-agen.md`):

  siklus ReAct  : REASON (model memilih langkah) -> ACT (tool dijalankan) -> OBSERVE (hasil
                  masuk riwayat) -> ulangi sampai selesai / batas langkah / gagal berulang.
  batas langkah : MAX_LANGKAH = 8. Bukan pilihan, tapi syarat (modul Minggu 10).
  state         : logs/agent_state/<task_id>.json — di LUAR percakapan, bisa dibaca dan
                  dilanjutkan. Kalau state hanya ada di riwayat percakapan, tugas yang
                  terputus tidak bisa dilanjutkan dan biaya konteks naik terus.
  trace         : logs/agent_trace/<task_id>.jsonl — satu baris per langkah, bisa dibaca
                  ulang untuk mencari sumber masalah (modul Minggu 11).
  human-in-loop : tool `simpan_laporan` (menulis berkas, tidak bisa dibatalkan) TIDAK
                  dijalankan tanpa persetujuan eksplisit. Sistem berhenti, menampilkan
                  apa persisnya yang akan disimpan, lalu menunggu.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from src.agent.tools import TOOLS, ToolError, jalankan_tool
from src.guardrails.input_filter import saring_input
from src.guardrails.output_check import periksa_jawaban

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"
PROMPT_PATH = Path("instruksi/agent-v1.md")

MAX_LANGKAH = 8
MAX_PERCOBAAN_TOOL = 2
MAX_PERCOBAAN_PARSE = 2
MAX_PERCOBAAN_MODEL = 3  # 503 "high demand" memang sementara; dicoba ulang dengan jeda
PANJANG_HASIL_DI_TRACE = 1_200

STATE_DIR = Path("logs/agent_state")
TRACE_DIR = Path("logs/agent_trace")

# Tarif promo Gemini 3.6 Flash (dipakai juga di catatan-pemakaian.md).
TARIF_MASUK_PER_JUTA = 0.75
TARIF_KELUAR_PER_JUTA = 3.75


class AgentGagal(RuntimeError):
    """Kegagalan agent yang pesannya layak ditampilkan ke pengguna."""


def _waktu() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ringkas(hasil: dict) -> str:
    teks = json.dumps(hasil, ensure_ascii=False)
    return teks[:PANJANG_HASIL_DI_TRACE] + ("..." if len(teks) > PANJANG_HASIL_DI_TRACE else "")


def _perkiraan_biaya(masuk: int, keluar: int) -> float:
    return masuk / 1_000_000 * TARIF_MASUK_PER_JUTA + keluar / 1_000_000 * TARIF_KELUAR_PER_JUTA


# --- penyimpanan state & trace ----------------------------------------------

def _simpan_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"{state['task_id']}.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def muat_state(task_id: str) -> dict:
    path = STATE_DIR / f"{task_id}.json"
    if not path.exists():
        raise AgentGagal(f"State tugas '{task_id}' tidak ditemukan di {STATE_DIR}.")
    return json.loads(path.read_text(encoding="utf-8"))


def _catat_trace(task_id: str, entri: dict) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    with (TRACE_DIR / f"{task_id}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entri, ensure_ascii=False) + "\n")


# --- meminta satu langkah dari model ----------------------------------------

def _riwayat_teks(state: dict) -> str:
    if not state["riwayat"]:
        return "(belum ada langkah)"

    baris = []
    for r in state["riwayat"]:
        baris.append(
            f"Langkah {r['langkah']}: alasan=\"{r['alasan']}\" aksi={r['aksi']} "
            f"argumen={json.dumps(r['argumen'], ensure_ascii=False)}\n  hasil: {r['hasil']}"
        )
    return "\n".join(baris)


def _minta_langkah(state: dict) -> tuple[dict, dict]:
    """Minta model memilih langkah berikutnya. Mengembalikan (keputusan, usage)."""
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    isi = (
        f"TUGAS: {state['tugas']}\n\n"
        f"LANGKAH YANG SUDAH DIAMBIL:\n{_riwayat_teks(state)}\n\n"
        f"Ini langkah ke-{state['langkah'] + 1} dari batas {state['max_langkah']}. "
        "Keluarkan HANYA satu objek JSON sesuai protokol."
    )

    galat_terakhir = ""
    for percobaan in range(1, MAX_PERCOBAAN_PARSE + 1):
        tambahan = f"\n\nCATATAN: jawabanmu sebelumnya tidak valid: {galat_terakhir}. Keluarkan JSON saja." \
            if galat_terakhir else ""
        respons = None
        for percobaan_model in range(1, MAX_PERCOBAAN_MODEL + 1):
            try:
                respons = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=isi + tambahan,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0,  # agent dijaga sedapat mungkin bisa ditebak (lihat trace)
                    ),
                )
                break
            except genai_errors.ServerError:
                # 503/500 dari sisi Google: bukan salah prompt, jadi layak diulang.
                if percobaan_model == MAX_PERCOBAAN_MODEL:
                    raise
                time.sleep(5 * percobaan_model)
        mentah = (respons.text or "").strip()

        try:
            keputusan = json.loads(mentah)
        except json.JSONDecodeError as e:
            galat_terakhir = f"bukan JSON valid ({e})"
            if percobaan == MAX_PERCOBAAN_PARSE:
                raise AgentGagal(
                    f"Agen tidak mengeluarkan JSON valid setelah {percobaan} percobaan. "
                    f"Keluaran mentah: {mentah[:300]}"
                ) from e
            continue

        if not isinstance(keputusan, dict) or ("selesai" not in keputusan and "aksi" not in keputusan):
            galat_terakhir = "objek harus punya 'aksi' atau 'selesai'"
            if percobaan == MAX_PERCOBAAN_PARSE:
                raise AgentGagal(f"Agen mengeluarkan JSON yang tidak sesuai protokol: {str(keputusan)[:300]}")
            continue

        usage = getattr(respons, "usage_metadata", None)
        return keputusan, {
            "masuk": getattr(usage, "prompt_token_count", 0) or 0,
            "keluar": getattr(usage, "candidates_token_count", 0) or 0,
        }

    raise AgentGagal("Agen tidak menghasilkan keputusan.")


# --- inti loop --------------------------------------------------------------

def _catat_token(state: dict, usage: dict) -> None:
    state["token"]["masuk"] += int(usage.get("masuk") or 0)
    state["token"]["keluar"] += int(usage.get("keluar") or 0)
    state["biaya_perkiraan_usd"] = round(
        _perkiraan_biaya(state["token"]["masuk"], state["token"]["keluar"]), 6
    )


def _jalankan_tool_dengan_ulang(nama: str, argumen: dict) -> tuple[dict | None, str | None, int]:
    """
    Jalankan tool, ulangi maksimal MAX_PERCOBAAN_TOOL kali untuk kegagalan sementara.

    Perilaku saat gagal (modul Minggu 11): dicoba ulang sekali, lalu kegagalan
    dikembalikan ke agent sebagai observasi — bukan crash, dan bukan diulang tanpa henti.
    """
    galat = ""
    for percobaan in range(1, MAX_PERCOBAAN_TOOL + 1):
        try:
            return jalankan_tool(nama, argumen), None, percobaan
        except ToolError as e:
            return None, str(e), percobaan  # kesalahan argumen: mengulang tidak menolong
        except Exception as e:  # kegagalan jaringan/API: layak dicoba ulang
            galat = f"{type(e).__name__}: {e}"
            if percobaan < MAX_PERCOBAAN_TOOL:
                time.sleep(2 * percobaan)
    return None, f"tool gagal setelah {MAX_PERCOBAAN_TOOL} percobaan ({galat})", MAX_PERCOBAAN_TOOL


def _lanjut(state: dict, izin_simpan: bool) -> dict:
    """Loop ReAct. State dimutasi dan disimpan setiap langkah."""
    while state["langkah"] < state["max_langkah"]:
        # 1) Ada aksi tertunda yang menunggu persetujuan manusia?
        if state["pending"]:
            if not izin_simpan:
                return _hasil_persetujuan(state)
            return _setujui_dan_lanjutkan(state)

        # 2) REASON
        keputusan, usage = _minta_langkah(state)
        _catat_token(state, usage)

        # 3) Selesai?
        if keputusan.get("selesai"):
            jawaban = str(keputusan.get("jawaban", "")).strip()
            masalah = periksa_jawaban(jawaban)
            state["status"] = "selesai" if not masalah else "diblokir_guardrail"
            state["jawaban"] = jawaban
            state["guardrail"] = masalah
            _simpan_state(state)
            _catat_trace(state["task_id"], {
                "waktu": _waktu(), "langkah": state["langkah"] + 1, "alasan": keputusan.get("alasan", ""),
                "aksi": "selesai", "argumen": {}, "hasil": jawaban[:PANJANG_HASIL_DI_TRACE],
                "guardrail": masalah,
            })
            return _ringkas_hasil(state)

        # 4) ACT
        aksi = keputusan.get("aksi")
        argumen = keputusan.get("argumen") or {}

        langkah_ke = state["langkah"] + 1
        state["langkah"] = langkah_ke

        if aksi not in TOOLS:
            observasi = {"galat": f"tool '{aksi}' tidak terdaftar. Pilihan: {', '.join(TOOLS)}"}
            durasi, percobaan = 0.0, 1
        elif TOOLS[aksi]["butuh_persetujuan"] and not izin_simpan:
            # Lapis 5: berhenti sebelum tindakan yang tidak bisa dibatalkan.
            state["pending"] = {"aksi": aksi, "argumen": argumen, "alasan": keputusan.get("alasan", "")}
            _simpan_state(state)
            _catat_trace(state["task_id"], {
                "waktu": _waktu(), "langkah": langkah_ke, "alasan": keputusan.get("alasan", ""),
                "aksi": aksi, "argumen": argumen, "hasil": "MENUNGGU PERSETUJUAN MANUSIA",
            })
            return _hasil_persetujuan(state)
        else:
            mulai = time.monotonic()
            hasil, galat, percobaan = _jalankan_tool_dengan_ulang(aksi, argumen if isinstance(argumen, dict) else {})
            durasi = round(time.monotonic() - mulai, 2)
            observasi = hasil if hasil is not None else {"galat": galat}
            if isinstance(observasi, dict) and "usage" in observasi:
                _catat_token(state, observasi["usage"])

        # 5) OBSERVE
        state["riwayat"].append({
            "langkah": langkah_ke,
            "alasan": keputusan.get("alasan", ""),
            "aksi": aksi,
            "argumen": argumen,
            "hasil": _ringkas(observasi),
            "percobaan": percobaan,
        })
        _simpan_state(state)
        _catat_trace(state["task_id"], {
            "waktu": _waktu(), "langkah": langkah_ke, "alasan": keputusan.get("alasan", ""),
            "aksi": aksi, "argumen": argumen, "durasi_detik": durasi, "percobaan": percobaan,
            "hasil": _ringkas(observasi),
        })

    # Batas langkah tercapai (modul Minggu 10-11): dihentikan, dan pengguna melihatnya.
    state["status"] = "batas_langkah"
    _simpan_state(state)
    _catat_trace(state["task_id"], {
        "waktu": _waktu(), "langkah": state["langkah"], "aksi": "batas_langkah",
        "alasan": f"batas {state['max_langkah']} langkah tercapai", "argumen": {}, "hasil": "",
    })
    return _ringkas_hasil(state)


def _setujui_dan_lanjutkan(state: dict) -> dict:
    pending = state["pending"]
    mulai = time.monotonic()
    try:
        hasil = jalankan_tool(pending["aksi"], pending["argumen"])
        observasi = hasil
    except Exception as e:  # kegagalan tool dilaporkan, bukan crash
        observasi = {"galat": f"{type(e).__name__}: {e}"}

    state["langkah"] += 1
    state["riwayat"].append({
        "langkah": state["langkah"],
        "alasan": pending.get("alasan", ""),
        "aksi": pending["aksi"],
        "argumen": pending["argumen"],
        "hasil": _ringkas(observasi),
        "percobaan": 1,
        "disetujui_manusia": True,
    })
    state["pending"] = None
    state["persetujuan"] = [*state.get("persetujuan", []), {"aksi": pending["aksi"], "disetujui": True}]
    _simpan_state(state)
    _catat_trace(state["task_id"], {
        "waktu": _waktu(), "langkah": state["langkah"], "aksi": pending["aksi"],
        "argumen": pending["argumen"], "durasi_detik": round(time.monotonic() - mulai, 2),
        "hasil": _ringkas(observasi), "disetujui_manusia": True,
    })
    return _lanjut(state, izin_simpan=True)


def _hasil_persetujuan(state: dict) -> dict:
    pending = state["pending"]
    argumen = pending["argumen"] if isinstance(pending["argumen"], dict) else {}
    isi = str(argumen.get("isi", ""))

    return {
        "status": "butuh_persetujuan",
        "task_id": state["task_id"],
        "pesan": (
            "Agen berhenti sebelum tindakan yang tidak bisa dibatalkan. "
            "Periksa apa yang akan terjadi, lalu setujui atau tolak."
        ),
        "usulan": {
            "aksi": pending["aksi"],
            "alasan_agen": pending.get("alasan", ""),
            "akan_menulis_ke": f"logs/laporan-agent/{argumen.get('nama_file', '?')}",
            "jumlah_karakter": len(isi),
            "cuplikan_isi": isi[:600],
        },
        "cara_melanjutkan": (
            f"python run_agent.py --lanjut {state['task_id']} --izin-simpan   "
            f"(atau POST /agent dengan {{\"task_id\": \"{state['task_id']}\", \"izin_simpan\": true}})"
        ),
        "waktu_berhenti": _waktu(),
        "biaya_perkiraan_usd": state["biaya_perkiraan_usd"],
    }


def _ringkas_hasil(state: dict) -> dict:
    return {
        "status": state["status"],
        "task_id": state["task_id"],
        "jawaban": state.get("jawaban", "") if state["status"] == "selesai" else "",
        "guardrail": state.get("guardrail", []),
        "jumlah_langkah": state["langkah"],
        "batas_langkah": state["max_langkah"],
        "riwayat": [
            {"langkah": r["langkah"], "alasan": r["alasan"], "aksi": r["aksi"], "argumen": r["argumen"],
             "percobaan": r["percobaan"]}
            for r in state["riwayat"]
        ],
        "token": state["token"],
        "biaya_perkiraan_usd": state["biaya_perkiraan_usd"],
        "trace": str(TRACE_DIR / f"{state['task_id']}.jsonl"),
        "state": str(STATE_DIR / f"{state['task_id']}.json"),
        "pesan": (
            f"Batas {state['max_langkah']} langkah tercapai sebelum tugas selesai. "
            "Riwayat langkah di atas menunjukkan apa yang sudah dicoba; tugas bisa dilanjutkan "
            "dengan memuat state yang sama, atau dipersempit."
            if state["status"] == "batas_langkah" else
            "Jawaban diblokir guardrails lapis 4; lihat daftar 'guardrail'."
            if state["status"] == "diblokir_guardrail" else ""
        ),
    }


# --- API publik -------------------------------------------------------------

def jalankan_agent(
    tugas: str,
    *,
    task_id: str | None = None,
    izin_simpan: bool = False,
    max_langkah: int = MAX_LANGKAH,
) -> dict:
    """
    Jalankan tugas baru. `izin_simpan=False` berarti tindakan berdampak akan berhenti
    dan menunggu persetujuan (bukan dijalankan diam-diam).
    """
    if not isinstance(max_langkah, int) or not 1 <= max_langkah <= 20:
        raise AgentGagal("max_langkah harus bilangan bulat 1..20 (batas keras, modul Minggu 10).")

    saring_input(tugas, untuk="tugas", tolak_injeksi=True, tolak_data_pribadi=True)

    state = {
        "task_id": task_id or uuid.uuid4().hex[:12],
        "tugas": tugas,
        "dibuat": _waktu(),
        "langkah": 0,
        "max_langkah": max_langkah,
        "riwayat": [],
        "pending": None,
        "persetujuan": [],
        "status": "berjalan",
        "jawaban": "",
        "guardrail": [],
        "token": {"masuk": 0, "keluar": 0},
        "biaya_perkiraan_usd": 0.0,
        "model": MODEL_NAME,
        "prompt": str(PROMPT_PATH),
    }
    _simpan_state(state)
    return _lanjut(state, izin_simpan)


def lanjutkan_agent(task_id: str, *, izin_simpan: bool = False) -> dict:
    """Lanjutkan tugas yang berhenti menunggu persetujuan (atau yang kena batas langkah)."""
    state = muat_state(task_id)

    if state["status"] == "batas_langkah":
        # Melanjutkan tugas yang kena batas berarti menambah anggaran langkah — keputusan
        # manusia, bukan keputusan agent. Batas keras tetap 20.
        state["max_langkah"] = min(state["max_langkah"] + MAX_LANGKAH, 20)
        state["status"] = "berjalan"
        _simpan_state(state)

    if state.get("pending") and not izin_simpan:
        return _hasil_persetujuan(state)

    return _lanjut(state, izin_simpan)


def baca_trace(task_id: str) -> list[dict]:
    """Baca ulang trace tugas untuk mencari sumber masalah (modul Minggu 11)."""
    path = TRACE_DIR / f"{task_id}.jsonl"
    if not path.exists():
        raise AgentGagal(f"Trace '{task_id}' tidak ditemukan.")
    return [json.loads(baris) for baris in path.read_text(encoding="utf-8").splitlines() if baris.strip()]
