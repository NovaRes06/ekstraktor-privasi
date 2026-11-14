"""
Uji lapisan API (api.py).

Fokus utama: memastikan galat dari Google GenAI TIDAK pernah bocor jadi
HTTP 500 'Internal Server Error' tanpa JSON `detail`. Sebelum perbaikan,
`ServerError` (mis. 503 saat Gemini lagi ramai) membuat /extract dan
/extract-from-url membalas 500 sehingga app.py tidak bisa menampilkan
sebab kegagalannya.
"""

import pytest
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

import api


@pytest.fixture()
def client():
    with TestClient(api.app) as c:
        yield c


def _server_error(code: int = 503) -> genai_errors.ServerError:
    return genai_errors.ServerError(
        code,
        {"error": {"code": code, "status": "UNAVAILABLE", "message": "high demand"}},
    )


def _client_error(code: int) -> genai_errors.ClientError:
    return genai_errors.ClientError(
        code,
        {"error": {"code": code, "status": "RESOURCE_EXHAUSTED", "message": "quota habis"}},
    )


# --- pemetaan galat ----------------------------------------------------------

@pytest.mark.parametrize(
    "exc,kode_yang_diharapkan",
    [
        (_client_error(429), 429),
        (_client_error(400), 422),
        (_client_error(401), 502),
        (_client_error(403), 502),
        (_client_error(404), 502),
        (_server_error(503), 502),
        (_server_error(500), 502),
    ],
)
def test_galat_genai_dipetakan_ke_http_bermakna(exc, kode_yang_diharapkan):
    http = api._galat_model(exc, "uji")
    assert http.status_code == kode_yang_diharapkan


def test_pemetaan_429_menyertakan_retry_after():
    http = api._galat_model(_client_error(429), "uji")
    assert http.headers.get("Retry-After") == "20"


def test_detail_selalu_ada_supaya_bisa_ditampilkan():
    """app.py membaca `detail`; tanpa itu pengguna cuma melihat 'Internal Server Error'."""
    for exc in (_client_error(429), _server_error(503)):
        http = api._galat_model(exc, "uji")
        assert isinstance(http.detail, str)
        assert "uji" in http.detail  # konteks sebab kegagalan ikut terbawa


def test_galat_pemrograman_tidak_ditelan():
    """ galat bukan milik Gemini harus tetap naik, jadi bug tidak ketutup jadi 502."""
    with pytest.raises(KeyError):
        api._galat_model(KeyError("kunci hilang"), "uji")


# --- perilaku endpoint -------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_extract_tanpa_body_ditolak_422(client):
    assert client.post("/extract", json={}).status_code == 422


def test_extract_from_url_dengan_url_tidak_valid_ditolak_422(client):
    """AnyUrl menolak di tahap validasi, bukan baru gagal saat requests.get."""
    r = client.post("/extract-from-url", json={"url": "bukan-url"})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_fetch_url_tanpa_skema_ditolak_422(client):
    assert client.post("/fetch-url", json={"url": "bukan-url-sama-sekali"}).status_code == 422


def test_ask_dengan_k_nol_ditolak_422(client):
    """k = 0 membuat ChromaDB menolak query (n_results = 0)."""
    assert client.post("/ask", json={"question": "halo", "k": 0}).status_code == 422


def test_ask_dengan_pertanyaan_kosong_ditolak_422(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_dengan_k_negatif_ditolak_422(client):
    assert client.post("/ask", json={"question": "halo", "k": -3}).status_code == 422


def test_extract_sa_gemini_503_tidak_menjadi_500(client, monkeypatch):
    """Inti perbaikan: 503 dari Gemini -> 502 ber-`detail`, bukan 500 polos."""
    monkeypatch.setattr(api, "extract_fields", lambda text, mode="penuh": (_ for _ in ()).throw(_server_error(503)))
    r = client.post("/extract", json={"text": "isi kebijakan"})
    assert r.status_code == 502, "ServerError GenAI harusnya jadi 502, bukan 500"
    body = r.json()
    assert "detail" in body
    assert "503" in str(body["detail"])


def test_extract_url_gemini_429_jadi_429(client, monkeypatch):
    monkeypatch.setattr(api, "fetch_document_from_url", lambda p: {"text": "isi"})
    monkeypatch.setattr(api, "extract_fields", lambda text, mode="penuh": (_ for _ in ()).throw(_client_error(429)))
    r = client.post("/extract-from-url", json={"url": "https://contoh.id/privasi"})
    assert r.status_code == 429
    assert r.headers.get("Retry-After") == "20"


def test_ask_galat_embedding_tidak_menjadi_500(client, monkeypatch):
    monkeypatch.setattr(api, "retrieve", lambda *a, **k: (_ for _ in ()).throw(_server_error(503)))
    r = client.post("/ask", json={"question": "Apa hak subjek data?"})
    assert r.status_code == 502
    assert "detail" in r.json()


def test_extract_url_galat_jaringan_ditolak_400(client, monkeypatch):
    import requests as req

    def _lempar(url, **kwargs):
        raise req.ConnectionError("gagal resolv host")

    monkeypatch.setattr(req, "get", _lempar)
    r = client.post("/fetch-url", json={"url": "https://tidak-ada.example/policy"})
    assert r.status_code == 400
    assert "detail" in r.json()


# --- batas akses tool /fetch-url (ketentuan Minggu 6) -----------------------
# Tool hanya boleh mengambil halaman PUBLIK. Ini menghalangi SSRF: tanpa
# proteksi, URL internal bisa dipakai memindai jaringan dari dalam server.

@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/health",          # host localhost persis
        "http://127.0.0.1:8000/health",          # loopback sebagai IP
        "http://10.1.2.3/config",                # IP privat persis
        "http://192.168.1.10/router",            # IP privat kelas C
        "http://172.16.0.5/internal",            # ip privat kelas B
        "http://printer.kantor.local/status",    # host .local
        "http://intranet.internal/dashboard",    # host .internal
    ],
)
def test_fetch_url_menolak_host_internal_403(client, url, monkeypatch):
    """Semuanya harus 403 SEBELUM requests.get dipanggil sama sekali."""
    import requests as req

    def _tidak_boleh_dipanggil(*a, **k):
        raise AssertionError("requests.get dipanggil untuk host internal -- proteksi bocor")

    monkeypatch.setattr(req, "get", _tidak_boleh_dipanggil)
    r = client.post("/fetch-url", json={"url": url})
    assert r.status_code == 403
    assert "publik" in r.json()["detail"].lower()


def test_fetch_url_host_resolve_ke_ip_privat_ditolak(client, monkeypatch):
    """Penyamaran via DNS: host nama biasa yang resolve ke 10.x."""
    import socket

    def _palugikan(host, *a, **k):
        # bentuk hasil mirip socket.getaddrinfo asli
        return [(2, 1, 6, "", ("10.9.8.7", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", _palugikan)
    r = client.post("/fetch-url", json={"url": "https://kebijakan-contoh.com/privasi"})
    assert r.status_code == 403
    assert "10.9.8.7" in r.json()["detail"]


def test_fetch_url_host_publik_tetap_diteruskan(client, monkeypatch):
    """Proteksi tidak boleh terlalu keras: host publik harus tetap bisa diambil."""
    import socket
    import requests as req

    monkeypatch.setattr(
        socket, "getaddrinfo",
        lambda host, *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )

    class _JawabanPalsu:
        text = "<html><body><p>Kami mengumpulkan nama dan email.</p></body></html>"
        def raise_for_status(self):
            pass

    monkeypatch.setattr(req, "get", lambda url, **k: _JawabanPalsu())
    r = client.post("/fetch-url", json={"url": "https://kebijakan-contoh.com/privasi"})
    assert r.status_code == 200
    assert "Kami mengumpulkan nama dan email" in r.json()["text"]
