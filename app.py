"""Privia — Antarmuka Streamlit untuk Privacy Policy Assistant.

PENTING: app.py memanggil api.py melalui HTTP. Jalankan API di terminal
terpisah sebelum menjalankan antarmuka Streamlit.

Terminal 1: python -m uvicorn api:app --reload
Terminal 2: python -m streamlit run app.py
"""

from pathlib import Path
import html as html_lib

import requests
import streamlit as st


# ============================================================
# KONFIGURASI
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000"
APP_NAME = "Privia"
APP_SUBTITLE = "Your Privacy Policy Assistant"
LOGO_PATH = Path("assets/Privia.png")

st.set_page_config(
    page_title=f"{APP_NAME} | {APP_SUBTITLE}",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS — VISUAL SYSTEM
# ============================================================

def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

        :root {
            --blue-50: #F1FAFF;
            --blue-100: #DDF3FF;
            --blue-200: #C2E8FA;
            --blue-400: #83CBEF;
            --blue-600: #429CCB;
            --blue-700: #2D789F;
            --pink-100: #FDEAF2;
            --pink-300: #F3B1CE;
            --pink-500: #DB7BA7;
            --ink: #213547;
            --muted: #74899A;
            --line: #DFEAF1;
            --canvas: #F7FAFD;
            --white: #FFFFFF;
            --green-100: #E5F7EE;
            --green-700: #247C57;
            --amber-100: #FFF3DC;
            --amber-700: #A96C0A;
            --red-100: #FFE8EA;
            --red-700: #B84D5C;
        }

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
            color: var(--ink);
        }
        h1, h2, h3, h4, .app-title, .hero-title, .section-heading {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 88% 0%, rgba(221,243,255,.7), transparent 28rem),
                radial-gradient(circle at 65% 38%, rgba(253,234,242,.34), transparent 27rem),
                var(--canvas);
        }
        [data-testid="stHeader"] { background: transparent; }
        .block-container {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* SIDEBAR */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #DDF3FF 0%, #EAF7FD 66%, #F8F1F8 100%);
            border-right: 1px solid #D6EAF5;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.25rem;
        }
        [data-testid="stSidebar"] * { color: var(--ink); }
        [data-testid="stSidebar"] hr {
            border: none;
            border-top: 1px solid rgba(69, 139, 177, .19);
            margin: 1rem 0;
        }
        .brand-row {
            display: flex;
            align-items: center;
            gap: 11px;
            margin: .1rem 0 .15rem 0;
        }
        .brand-mark {
            width: 42px;
            height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 42px;
            border-radius: 14px;
            background: linear-gradient(140deg, #66BDE8 0%, #E7A3C3 100%);
            color: white !important;
            font-size: 21px;
            font-weight: 800;
            box-shadow: 0 6px 16px rgba(73, 155, 199, .18);
        }
        .app-title {
            font-size: 1.38rem;
            font-weight: 800;
            letter-spacing: -.045em;
            line-height: 1.1;
            color: #2E7198 !important;
            margin: 0;
        }
        .app-subtitle {
            margin-top: .28rem;
            font-size: .68rem;
            line-height: 1.35;
            color: #668295 !important;
        }
        .sidebar-caption {
            font-size: .76rem;
            color: #58778B !important;
            line-height: 1.55;
            padding: .85rem .05rem .3rem;
        }
        .nav-eyebrow {
            margin: .2rem 0 .45rem;
            color: #7591A2 !important;
            font-size: .66rem;
            font-weight: 800;
            letter-spacing: .12em;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: .85rem;
            padding: .38rem .68rem;
            border: 1px solid rgba(36,124,87,.12);
            border-radius: 999px;
            background: var(--green-100);
            color: var(--green-700) !important;
            font-size: .7rem;
            font-weight: 700;
        }
        .status-pill.offline {
            border-color: rgba(184,77,92,.12);
            background: var(--red-100);
            color: var(--red-700) !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] { margin: 0 0 .28rem 0; }
        [data-testid="stSidebar"] [data-testid="stButton"] > button {
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            width: 100%;
            min-height: 45px;
            box-sizing: border-box;
            border: 1px solid transparent;
            border-radius: 11px;
            padding: .65rem .8rem;
            background: rgba(255,255,255,.36);
            color: #3B596C !important;
            font-family: 'DM Sans', sans-serif;
            font-size: .84rem;
            font-weight: 600;
            text-align: left !important;
            box-shadow: none;
            transition: background .16s ease, border-color .16s ease;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] > button > div {
            width: 100%;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            text-align: left !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] > button p {
            width: 100%;
            margin: 0;
            text-align: left !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
            background: rgba(255,255,255,.85);
            border-color: rgba(73,155,199,.2);
        }
        [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(100deg, #BEE8FC 0%, #F5D5E5 100%) !important;
            border-color: rgba(76,151,193,.16) !important;
            color: #244D65 !important;
            box-shadow: 0 4px 12px rgba(80,143,176,.09);
        }
        .sidebar-footer {
            margin-top: 1.25rem;
            padding: .85rem .8rem;
            border: 1px solid rgba(86,149,180,.16);
            border-radius: 12px;
            background: rgba(255,255,255,.38);
            color: #678195 !important;
            font-size: .69rem;
            line-height: 1.5;
        }

        /* HERO / PAGE HEADER */
        .hero-panel {
            position: relative;
            overflow: hidden;
            margin: .15rem 0 1.25rem;
            padding: 1.65rem 1.8rem 1.55rem;
            border: 1px solid rgba(210,229,240,.95);
            border-radius: 22px;
            background: linear-gradient(
                115deg,
                rgba(255,255,255,.97) 0%,
                rgba(242,250,255,.96) 58%,
                rgba(255,244,249,.93) 100%
            );
            box-shadow: 0 12px 34px rgba(57,110,145,.07);
        }
        .hero-panel:after {
            content: '';
            position: absolute;
            right: -48px;
            top: -76px;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            border: 30px solid rgba(139,207,238,.13);
            pointer-events: none;
        }
        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            margin-bottom: .7rem;
            color: #478CB4;
            font-size: .68rem;
            font-weight: 800;
            letter-spacing: .13em;
            text-transform: uppercase;
        }
        .hero-dot {
            width: 7px;
            height: 7px;
            display: inline-block;
            border-radius: 50%;
            background: linear-gradient(135deg, #55B7E3, #D978A5);
        }
        .hero-title {
            position: relative;
            z-index: 1;
            margin: 0 0 .55rem;
            font-size: clamp(1.8rem, 3vw, 2.45rem);
            font-weight: 800;
            letter-spacing: -.055em;
            line-height: 1.14;
            color: #243F53;
        }
        .hero-title .accent {
            background: linear-gradient(90deg, #398EBE, #C96798);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-description {
            position: relative;
            z-index: 1;
            max-width: 780px;
            color: #718697;
            font-size: .93rem;
            line-height: 1.7;
        }
        .hero-description strong { color: #3B5D73; }
        .hero-chip-row { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 1rem; }
        .hero-chip {
            display: inline-flex;
            align-items: center;
            padding: .32rem .62rem;
            border: 1px solid #DFEBF2;
            border-radius: 999px;
            background: rgba(255,255,255,.78);
            color: #658094;
            font-size: .68rem;
            font-weight: 700;
        }

        /* SECTION AND WORKFLOW */
        .section-heading {
            margin: .25rem 0 .25rem;
            color: #2D485B;
            font-size: 1.08rem;
            font-weight: 800;
            letter-spacing: -.025em;
        }
        .section-subtitle {
            margin: 0 0 .85rem;
            color: var(--muted);
            font-size: .82rem;
            line-height: 1.55;
        }
        .step-card {
            display: flex;
            gap: 11px;
            align-items: flex-start;
            min-height: 88px;
            padding: .9rem .85rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: rgba(255,255,255,.82);
        }
        .step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 29px;
            height: 29px;
            flex: 0 0 29px;
            border-radius: 10px;
            background: linear-gradient(135deg, #D8F1FE, #F9E1ED);
            color: #3D7797;
            font-size: .74rem;
            font-weight: 800;
        }
        .step-title { margin: .05rem 0 .2rem; color: #344F62; font-size: .78rem; font-weight: 800; }
        .step-desc { color: #8092A0; font-size: .7rem; line-height: 1.45; }

        /* FORM CARDS */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--line) !important;
            border-radius: 17px !important;
            background: rgba(255,255,255,.92) !important;
            box-shadow: 0 7px 24px rgba(69,120,149,.045);
        }
        .panel-heading {
            margin: 0 0 .15rem;
            color: #2D485B;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1rem;
            font-weight: 800;
        }
        .panel-copy { color: var(--muted); font-size: .79rem; line-height: 1.5; margin-bottom: .6rem; }
        .section-label {
            margin: .1rem 0 .45rem;
            color: #6E91A6;
            font-size: .67rem;
            font-weight: 800;
            letter-spacing: .12em;
        }
        .stTextArea textarea, .stTextInput input {
            border: 1px solid #D9E7EF !important;
            border-radius: 12px !important;
            background: #FCFEFF !important;
            color: var(--ink) !important;
            font-family: 'DM Sans', sans-serif !important;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #83CBEF !important;
            box-shadow: 0 0 0 3px rgba(131,203,239,.18) !important;
        }
        div[role="radiogroup"] { gap: .55rem; }
        div[role="radiogroup"] label {
            border: 1px solid #DFEAF1;
            border-radius: 10px;
            padding: .43rem .68rem;
            background: #FBFDFF;
        }
        [data-testid="stSlider"] [data-baseweb="slider"] > div > div { background: #D8EAF4 !important; }
        [data-testid="stSlider"] [data-baseweb="slider"] > div > div > div {
            background: linear-gradient(90deg, #63B7E3, #E28FB4) !important;
        }
        [data-testid="stSlider"] [role="slider"] {
            background: #D978A5 !important;
            border: 3px solid white !important;
            box-shadow: 0 0 0 2px #D978A5 !important;
        }

        /* BUTTONS */
        .stButton button {
            border-radius: 11px;
            font-family: 'DM Sans', sans-serif;
            font-weight: 700;
            transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
        }
        .stButton button[kind="primary"] {
            border: none !important;
            background: linear-gradient(100deg, #55B1DF 0%, #D978A5 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 6px 16px rgba(104,158,191,.19);
        }
        .stButton button[kind="primary"]:hover {
            filter: saturate(1.04) brightness(.98);
            box-shadow: 0 8px 20px rgba(104,158,191,.24);
            transform: translateY(-1px);
        }
        .stButton button[kind="secondary"] {
            border: 1px solid #DCE8EF;
            background: #FFFFFF;
            color: #446176;
        }

        /* EXTRACTION RESULTS */
        .result-topline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: .5rem;
            margin: 1.1rem 0 .55rem;
        }
        .result-title {
            margin: 0;
            color: #2D485B;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.08rem;
            font-weight: 800;
        }
        .result-hint { color: #8092A0; font-size: .73rem; }
        .result-card {
            margin-top: .65rem;
            padding: .55rem 1.15rem;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: white;
            box-shadow: 0 7px 24px rgba(69,120,149,.045);
        }
        .field-row {
            display: grid;
            grid-template-columns: minmax(200px, .85fr) minmax(0, 1.65fr);
            align-items: start;
            gap: 1.1rem;
            padding: .88rem .15rem;
            border-bottom: 1px solid #EDF2F6;
        }
        .field-row:last-child { border-bottom: none; }
        .field-label {
            color: #344F62;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: .79rem;
            font-weight: 700;
            line-height: 1.5;
        }
        .field-value { color: #526A7C; font-size: .81rem; line-height: 1.65; overflow-wrap: anywhere; }
        .field-value.empty { color: #93A2AD; font-style: italic; }
        .field-bukti {
            display: block;
            margin: .38rem 0 0;
            padding: .5rem .65rem;
            border-left: 3px solid #B7DCEB;
            border-radius: 0 8px 8px 0;
            background: #F6FAFD;
            color: #5F7F91;
            font-size: .74rem;
            line-height: 1.6;
            overflow-wrap: anywhere;
        }
        .field-bukti strong { color: #40718B; font-weight: 700; }
        .field-badge {
            display: inline-flex;
            margin: .32rem 0 0;
            padding: .15rem .48rem;
            border-radius: 999px;
            font-family: 'DM Sans', sans-serif;
            font-size: .59rem;
            font-weight: 800;
            letter-spacing: .055em;
        }
        .field-badge.ada { background: #E5F6FD; color: #3688B3; }
        .field-badge.kosong { background: var(--amber-100); color: var(--amber-700); }
        [data-testid="stMetric"] {
            padding: .85rem 1rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: linear-gradient(145deg, #FFFFFF 0%, #F8FCFF 100%);
            box-shadow: 0 5px 15px rgba(69,120,149,.035);
        }
        [data-testid="stMetricLabel"] { color: #738A9A !important; font-size: .72rem !important; }
        [data-testid="stMetricValue"] { color: #2C526B !important; font-family: 'Plus Jakarta Sans', sans-serif; }

        /* ANSWER AND SOURCES */
        .answer-card {
            padding: 1.2rem 1.35rem;
            border: 1px solid #DCEAF1;
            border-left: 4px solid #D978A5;
            border-radius: 15px;
            background: linear-gradient(125deg, #F2FAFE 0%, #FFF6FA 100%);
            color: #304E61;
            font-size: .9rem;
            line-height: 1.8;
            box-shadow: 0 7px 23px rgba(69,120,149,.045);
            overflow-wrap: anywhere;
        }
        .source-card {
            margin: .5rem 0;
            padding: .85rem 1rem;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: #FFFFFF;
        }
        .source-meta { margin-bottom: .35rem; color: #4785A7; font-size: .7rem; font-weight: 800; line-height: 1.5; }
        .source-text {
            color: #607587;
            font-size: .79rem;
            line-height: 1.65;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }
        .empty-state {
            padding: 1.3rem 1rem;
            border: 1px dashed #CFE0EA;
            border-radius: 14px;
            background: rgba(255,255,255,.65);
            color: #7B91A1;
            font-size: .82rem;
            line-height: 1.6;
            text-align: center;
        }
        .footer-note { color: #91A0AC; font-size: .68rem; line-height: 1.55; margin-top: 1.2rem; }
        .stAlert { border-radius: 12px; }

        @media (max-width: 900px) {
            .block-container { padding-top: 1rem; }
            .hero-panel { padding: 1.25rem; }
            .field-row { grid-template-columns: 1fr; gap: .35rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def esc(value) -> str:
    """Escape isi din API sebelum dimasukkan ke HTML."""
    return html_lib.escape(str(value)).replace("\n", "<br>")


def cek_api_hidup() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2.5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def pesan_error_api(exc: requests.RequestException) -> str:
    """Ambil detail error dari respons API bila tersedia."""
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            detail = response.json()
            if isinstance(detail, dict):
                detail = detail.get("detail", detail.get("message", detail))
            return f"HTTP {response.status_code}: {detail}"
        except (ValueError, requests.RequestException):
            return f"HTTP {response.status_code}: {response.text or str(exc)}"
    return str(exc)


LABEL_FIELD = {
    "jenis_data_dikumpulkan": "Jenis Data yang Dikumpulkan",
    "tujuan_pemrosesan": "Tujuan Pemrosesan",
    "dasar_pemrosesan": "Dasar Pemrosesan",
    "pihak_ketiga_penerima": "Pihak Ketiga Penerima Data",
    "transfer_lintas_negara": "Transfer Lintas Negara",
    "masa_retensi_data": "Masa Retensi Data",
    "hak_subjek_data": "Hak Subjek Data",
    "mekanisme_keamanan": "Mekanisme Keamanan",
    "kontak_penanggung_jawab": "Kontak Penanggung Jawab",
}


def render_hasil_ekstraksi(data: dict) -> None:
    fields = data.get("fields") or {}
    missing_fields = data.get("missing_fields") or []
    usage = data.get("usage") or {}
    mode = data.get("mode", "penuh")
    # Mode ringkas hanya membawa 4 field; jangan tampilkan 5 sisanya sebagai
    # "tidak disebutkan" karena itu akan terbaca seolah dokumennya tidak memuatnya.
    kunci = [k for k in LABEL_FIELD if k in fields] if mode == "ringkas" else list(LABEL_FIELD)
    rows_html = []
    jumlah_ada = 0

    for key in kunci:
        label = LABEL_FIELD[key]
        raw_value = fields.get(key, "Tidak disebutkan")
        value = str(raw_value).strip()
        kosong = value.lower() in {
            "tidak disebutkan", "(tidak ada di hasil)", "", "none", "null"
        }
        if not kosong:
            jumlah_ada += 1
        badge = (
            '<span class="field-badge kosong">TIDAK DISEBUTKAN</span>'
            if kosong else
            '<span class="field-badge ada">TERIDENTIFIKASI</span>'
        )
        value_class = "field-value empty" if kosong else "field-value"
        # v2: pasangan bukti (kutipan langsung dari dokumen) ditampilkan di bawah
        # ringkasan supaya setiap field bisa dicek balik ke dokumen aslinya.
        bukti_raw = str(fields.get(f"bukti_{key}", "") or "").strip()
        bukti_kosong = bukti_raw.lower() in {"", "tidak disebutkan"}
        bukti_html = (
            f'<div class="field-bukti"><strong>Bukti:</strong> {esc(bukti_raw)}</div>'
            if bukti_raw and not bukti_kosong
            else ''
        )
        rows_html.append(
            '<div class="field-row">'
            f'<div class="field-label">{esc(label)}<br>{badge}</div>'
            f'<div class="{value_class}">{esc(value)}{bukti_html}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="result-topline">'
        '<div class="result-title">Hasil ekstraksi</div>'
        f'<div class="result-hint">{len(kunci)} aspek kebijakan privasi</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(3)
    metric_cols[0].metric("Aspek teridentifikasi", f"{jumlah_ada} / {len(kunci)}")
    metric_cols[1].metric("Token masuk", usage.get("input_tokens", "—"))
    metric_cols[2].metric("Token keluar", usage.get("output_tokens", "—"))

    if data.get("ringkasan"):
        st.markdown(
            '<div class="result-card" style="margin-bottom:14px">'
            f'<div class="field-label">Ringkasan</div><div class="field-value">{esc(data["ringkasan"])}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="result-card">' + "".join(rows_html) + '</div>',
        unsafe_allow_html=True,
    )

    if missing_fields:
        st.warning("Field yang tidak tersedia pada skema respons: " + ", ".join(map(str, missing_fields)))

    # Lapis 4 guardrails: masalah pada bukti ditampilkan terang-terangan, bukan disembunyikan.
    masalah = data.get("guardrail") or []
    if masalah:
        st.warning("Guardrails menemukan masalah pada hasil ini:\n- " + "\n- ".join(map(str, masalah)))


def render_hero(kicker: str, title: str, description: str, chips: list[str]) -> None:
    chips_html = "".join(f'<span class="hero-chip">{esc(chip)}</span>' for chip in chips)
    st.markdown(
        '<div class="hero-panel">'
        f'<div class="hero-kicker"><span class="hero-dot"></span>{esc(kicker)}</div>'
        f'<div class="hero-title">{title}</div>'
        f'<div class="hero-description">{description}</div>'
        f'<div class="hero-chip-row">{chips_html}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def pindah_halaman(nama_halaman: str) -> None:
    st.session_state.page = nama_halaman


# ============================================================
# INITIAL STATE & CSS
# ============================================================
inject_css()

if "page" not in st.session_state:
    st.session_state.page = "ekstraksi"
if "hasil_ekstraksi" not in st.session_state:
    st.session_state.hasil_ekstraksi = None
if "hasil_tanya" not in st.session_state:
    st.session_state.hasil_tanya = None
if "pertanyaan_terakhir" not in st.session_state:
    st.session_state.pertanyaan_terakhir = ""

api_hidup = cek_api_hidup()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        '<div class="brand-row">'
        '<div class="brand-mark">P</div>'
        '<div><div class="app-title">Privia</div>'
        '<div class="app-subtitle">Your Privacy Policy Assistant</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if api_hidup:
        st.markdown('<div class="status-pill">● API Tersambung</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill offline">● API Tidak Tersambung</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="sidebar-caption">Pahami kebijakan privasi yang panjang dengan cara yang lebih terstruktur.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="nav-eyebrow">RUANG KERJA</div>', unsafe_allow_html=True)

    if st.button(
        "✦  Ekstraksi Kebijakan",
        use_container_width=True,
        key="nav_ekstraksi",
        type="primary" if st.session_state.page == "ekstraksi" else "secondary",
    ):
        pindah_halaman("ekstraksi")
        st.rerun()

    if st.button(
        "◌  Tanya Jawab",
        use_container_width=True,
        key="nav_tanya",
        type="primary" if st.session_state.page == "tanya" else "secondary",
    ):
        pindah_halaman("tanya")
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-footer"><strong>Catatan penggunaan</strong><br>'
        'Hasil Privia membantu meninjau isi dokumen, bukan menggantikan penilaian manusia atau nasihat hukum.</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE: EKSTRAKSI KEBIJAKAN
# ============================================================
if st.session_state.page == "ekstraksi":
    render_hero(
        "PRIVACY POLICY WORKSPACE",
        'Ubah dokumen panjang menjadi <span class="accent">informasi yang jelas.</span>',
        'Ekstrak informasi penting dari kebijakan privasi ke dalam sembilan aspek terstruktur. '
        'Bagian yang tidak dinyatakan dalam dokumen akan ditandai, bukan ditebak.',
        ["9 aspek kebijakan", "Input teks atau URL", "Hasil terstruktur"],
    )

    st.markdown('<div class="section-heading">Mulai dari dokumen</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Pilih sumber kebijakan yang ingin kamu tinjau.</div>',
        unsafe_allow_html=True,
    )

    step_cols = st.columns(3, gap="medium")
    steps = [
        ("01", "Masukkan dokumen", "Tempel teks kebijakan atau gunakan tautan halaman publik."),
        ("02", "Ekstraksi informasi", "AI memetakan isi dokumen ke sembilan aspek tetap."),
        ("03", "Tinjau hasil", "Periksa ringkasan dan tandai bagian yang belum disebutkan."),
    ]
    for col, (number, title, desc) in zip(step_cols, steps, strict=True):
        with col:
            st.markdown(
                f'<div class="step-card"><div class="step-number">{number}</div>'
                f'<div><div class="step-title">{esc(title)}</div><div class="step-desc">{esc(desc)}</div></div></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Sumber kebijakan</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-copy">Pilih cara memasukkan dokumen ke dalam Privia.</div>',
            unsafe_allow_html=True,
        )
        sumber = st.radio(
            "Sumber dokumen",
            ["Tempel teks langsung", "Dari URL"],
            horizontal=True,
            label_visibility="collapsed",
            key="sumber_ekstraksi",
        )

        # Mode output (lingkup lampiran B: K genap wajib punya mode ringkas).
        mode_ekstraksi = "ringkas" if st.toggle(
            "Mode ringkas (4 aspek utama + satu paragraf)",
            value=False,
            key="mode_ringkas",
            help="Mode penuh menampilkan 9 aspek + bukti. Mode ringkas memproyeksikan 4 aspek "
                 "terpenting dari hasil yang sama, tanpa panggilan model tambahan.",
        ) else "penuh"

        if sumber == "Tempel teks langsung":
            teks_input = st.text_area(
                "Isi kebijakan privasi",
                height=230,
                placeholder="Tempel isi kebijakan privasi di sini...",
                label_visibility="collapsed",
                key="teks_input",
            )
            tombol = st.button("✦  Ekstrak kebijakan", type="primary", use_container_width=True, key="btn_extract_text")
            if tombol:
                if not teks_input.strip():
                    st.warning("Teks masih kosong. Tempel isi kebijakan privasi terlebih dahulu.")
                else:
                    with st.spinner("Mengekstrak informasi dari dokumen..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/extract",
                                json={"text": teks_input, "mode": mode_ekstraksi},
                                timeout=45,
                            )
                            response.raise_for_status()
                            st.session_state.hasil_ekstraksi = response.json()
                        except requests.RequestException as exc:
                            st.error("Ekstraksi belum berhasil. Periksa status API dan detail berikut.")
                            st.code(pesan_error_api(exc))
        else:
            url_input = st.text_input(
                "URL kebijakan privasi",
                placeholder="https://contoh-aplikasi.com/privacy-policy",
                label_visibility="collapsed",
                key="url_input",
            )
            st.caption("Gunakan URL halaman kebijakan privasi yang dapat diakses secara publik.")
            tombol = st.button("↗  Ambil & ekstrak", type="primary", use_container_width=True, key="btn_extract_url")
            if tombol:
                if not url_input.strip():
                    st.warning("URL masih kosong. Masukkan URL kebijakan privasi terlebih dahulu.")
                else:
                    with st.spinner("Mengambil halaman dan mengekstrak informasi..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/extract-from-url",
                                json={"url": url_input, "mode": mode_ekstraksi},
                                timeout=45,
                            )
                            response.raise_for_status()
                            st.session_state.hasil_ekstraksi = response.json()
                        except requests.RequestException as exc:
                            st.error("Dokumen belum berhasil diambil. Periksa URL dan detail berikut.")
                            st.code(pesan_error_api(exc))

    if st.session_state.hasil_ekstraksi:
        render_hasil_ekstraksi(st.session_state.hasil_ekstraksi)

    st.markdown(
        '<div class="footer-note">Privia membantu mengorganisasi informasi yang tertulis dalam dokumen. '
        'Hasil ekstraksi perlu diperiksa kembali terhadap sumber aslinya.</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE: TANYA JAWAB BERBASIS DOKUMEN
# ============================================================
else:
    render_hero(
        "DOCUMENT-GROUNDED Q&A",
        'Tanyakan kebijakannya. <span class="accent">Lihat dasar jawabannya.</span>',
        'Ajukan pertanyaan berdasarkan dokumen yang sudah di-index. Privia menampilkan potongan sumber '
        'yang dipakai sehingga jawaban dapat ditinjau kembali.',
        ["Berbasis dokumen", "Sumber ditampilkan", "Jawaban dapat ditinjau"],
    )

    st.markdown('<div class="section-heading">Apa yang ingin kamu ketahui?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Tulis pertanyaan dengan bahasa sehari-hari. '
        'Sistem akan mencari potongan dokumen yang paling relevan.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown('<div class="panel-heading">Pertanyaan kamu</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-copy">Contoh: Apa saja hak subjek data menurut UU PDP?</div>',
            unsafe_allow_html=True,
        )
        pertanyaan = st.text_input(
            "Pertanyaan",
            placeholder="Ketik pertanyaan tentang kebijakan privasi...",
            label_visibility="collapsed",
            key="input_pertanyaan",
        )
        slider_col, button_col = st.columns([2, 1])
        with slider_col:
            jumlah_chunk = st.slider(
                "Jumlah potongan sumber (k)",
                min_value=1,
                max_value=10,
                value=5,
                help="Jumlah maksimum potongan dokumen yang akan dicari sebelum disaring dengan ambang relevansi.",
                key="jumlah_chunk",
            )
        with button_col:
            tombol_tanya = st.button("✦  Tanya Privia", type="primary", use_container_width=True, key="btn_ask")

        if tombol_tanya:
            if not pertanyaan.strip():
                st.warning("Pertanyaan masih kosong. Tulis pertanyaan terlebih dahulu.")
            else:
                with st.spinner("Menelusuri sumber dan menyusun jawaban..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/ask",
                            json={"question": pertanyaan, "k": jumlah_chunk},
                            timeout=60,
                        )
                        response.raise_for_status()
                        st.session_state.hasil_tanya = response.json()
                        st.session_state.pertanyaan_terakhir = pertanyaan
                    except requests.RequestException as exc:
                        st.error("Pertanyaan belum berhasil diproses oleh API. Detail error:")
                        st.code(pesan_error_api(exc))

    if st.session_state.hasil_tanya:
        data = st.session_state.hasil_tanya
        st.markdown(
            '<div class="result-topline">'
            '<div class="result-title">Jawaban Privia</div>'
            '<div class="result-hint">Pertanyaan: ' + esc(st.session_state.pertanyaan_terakhir) + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="answer-card">' + esc(data.get("answer", "Tidak ada jawaban dari API.")) + '</div>',
            unsafe_allow_html=True,
        )

        if data.get("catatan"):
            st.info(str(data["catatan"]))

        sources = data.get("sources") or []
        st.markdown(
            '<div class="result-topline">'
            '<div class="result-title">Sumber yang digunakan</div>'
            '<div class="result-hint">' + str(len(sources)) + ' potongan sumber</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if sources:
            for i, src in enumerate(sources, start=1):
                try:
                    jarak = float(src.get("jarak", 0))
                    jarak_text = f"{jarak:.4f}"
                except (TypeError, ValueError):
                    jarak_text = str(src.get("jarak", "—"))
                st.markdown(
                    '<div class="source-card">'
                    f'<div class="source-meta">SUMBER [{i}] &nbsp;·&nbsp; '
                    f'{esc(src.get("source_doc", "Dokumen tidak diketahui"))} '
                    f'&nbsp;·&nbsp; bagian {esc(src.get("chunk_index", "—"))} '
                    f'&nbsp;·&nbsp; jarak {esc(jarak_text)}</div>'
                    f'<div class="source-text">{esc(src.get("text", ""))}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="empty-state">Tidak ada potongan sumber yang dipakai untuk jawaban ini. '
                'Periksa kembali indeks dokumen atau ajukan pertanyaan yang lebih spesifik.</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="footer-note">Jawaban dibuat berdasarkan dokumen yang tersedia dalam indeks. '
        'Jika sumber tidak mendukung jawaban, verifikasi melalui dokumen asli '
        'dan jangan menganggapnya sebagai nasihat hukum.</div>',
        unsafe_allow_html=True,
    )
