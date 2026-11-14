"""
fetch_reference_docs.py — unduh kebijakan privasi fintech asli ke data/raw/.

Jalankan SEKALI untuk menambah dokumen rujukan, lalu jalankan ulang build_index.py
supaya dokumen baru ikut ter-index.

Cara pakai:
    python fetch_reference_docs.py

Sumber yang diunduh di sini semuanya URL RESMI dari masing-masing perusahaan
(bukan artikel pihak ketiga), dicek 7 Oktober 2026. Kalau salah satu gagal
(halaman pindah/berubah), itu wajar -- perusahaan sering mengubah struktur
website mereka. Cek manual URL terbaru kalau perlu.
"""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_RAW_DIR = Path("data/raw")

# (nama file, URL resmi)
# Daftar ini dipakai juga sebagai catatan asal dokumen (syarat "asalnya tercatat",
# lampiran B): judul, penerbit, dan tautannya ada di data/raw/SUMBER.md.
SUMBER_DOKUMEN = [
    ("kebijakan-shopeepay.txt", "https://shopeepay.co.id/privacy"),
    ("kebijakan-ovo.txt", "https://www.ovo.id/kebijakan-privasi"),
    ("kebijakan-dana.txt", "https://www.dana.id/policy"),
    ("kebijakan-gopay.txt", "https://gopay.co.id/terms-and-condition/gopay-privacy-notice-23-juni-2025"),
    # Ditambahkan 2 November 2026 untuk memenuhi lingkup minimum dokumen rujukan
    # (5 + (K mod 4), maksimum 8). Ketiganya halaman resmi perusahaan, publik.
    ("kebijakan-linkaja.txt", "https://www.linkaja.id/kebijakan-privasi"),
    ("kebijakan-bibit.txt", "https://bibit.id/privacy"),
    ("kebijakan-tokopedia.txt", "https://www.tokopedia.com/privacy"),
]


def fetch_and_clean(url: str) -> str:
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


def main():
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    berhasil = 0
    for nama_file, url in SUMBER_DOKUMEN:
        print(f"\nMengunduh: {url}")
        try:
            teks = fetch_and_clean(url)
        except requests.RequestException as e:
            print(f"  [GAGAL] {e}")
            print("  -> Catat ini di logs/failed_cases.md kalau mau, atau cek URL terbaru manual.")
            continue

        if len(teks) < 200:
            print(f"  [PERINGATAN] Teks yang didapat sangat pendek ({len(teks)} karakter) "
                  f"-- kemungkinan halaman butuh JavaScript untuk render, atau strukturnya berubah.")

        output_path = DATA_RAW_DIR / nama_file
        output_path.write_text(
            f"Sumber: {url}\nDiunduh: (isi tanggal unduh kamu di sini)\n\n{teks}",
            encoding="utf-8",
        )
        print(f"  -> Disimpan ke {output_path} ({len(teks)} karakter)")
        berhasil += 1

    print(f"\n{'=' * 50}")
    print(f"SELESAI. {berhasil}/{len(SUMBER_DOKUMEN)} dokumen berhasil diunduh.")
    print("Langkah berikutnya: jalankan 'python build_index.py' untuk mengindeks dokumen baru.")
    print("=" * 50)


if __name__ == "__main__":
    main()
