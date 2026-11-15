# Refleksi

> **Status: draf awal, belum dikumpulkan.** Ini luaran Minggu 16; target progres repo
> saat ini adalah Minggu 13.

Nova Reswara · 10241058 · Privia · 2 November 2026

## 1. Keputusan rancangan yang paling saya sesali

Menunda pemeriksaan bukti (lapis 4) sampai Minggu 14. Field `bukti_*` sudah ada
sejak prompt v2 di Minggu 5, tetapi selama sembilan minggu saya hanya memeriksa
**bentuknya** (18 key lengkap), bukan **isinya**. Akibatnya v2 dipakai dengan
keyakinan bahwa setiap nilai punya dasar, padahal model kadang menyusun kutipan dari
dua butir berbeda — dan tidak ada yang menangkapnya sampai pemeriksaan verbatim
dibuat. Kalau saya mengulang, pemeriksaan "kutipan ini benar-benar ada di dokumen"
akan saya tulis pada hari yang sama dengan field buktinya, bukan sembilan minggu
kemudian. Biayanya kecil (satu fungsi), nilainya besar, dan menumpuknya di akhir
membuat dua dari tujuh belas kasus uji gagal pada hal yang seharusnya sudah ketahuan
sejak Minggu 5.

## 2. Kesalahan yang tidak tertangkap siapa pun kecuali saya

Selama berhari-hari index RAG hanya berisi 14 chunk dari 2 dokumen, padahal empat
dokumen sudah ada di `data/raw/`. Sistem tetap menjawab dengan lancar, jarak chunk
tetap di bawah ambang, dan semuanya tampak benar — hanya saja pertanyaan tentang OVO
dijawab dengan potongan dari ringkasan UU PDP. Tidak ada error, tidak ada peringatan.
Yang membuat saya tahu adalah pemeriksaan manual jarak chunk saat menulis catatan
Lapisan 3, bukan sistemnya. Kesalahan ini mengubah cara saya menilai "berhasil":
jarak di bawah ambang tidak berarti dokumennya benar, dan keheningan sistem bukan
bukti bahwa ia bekerja. Sekarang `build_index.py` mencetak jumlah dokumen, dan
catatan itu saya tulis di `logs/lapisan3_rag_cases.md` supaya tidak terulang.

Kesalahan kedua yang hanya saya yang tahu: agen pernah menjawab "laporan sudah
disimpan" tanpa menulis berkas apa pun, karena ia tidak memanggil tool. Kalau tidak
ada pemeriksaan keberadaan berkas, saya akan percaya pada kalimatnya.

## 3. Bagaimana AI membantu, dan di titik mana ia menyesatkan

AI membantu paling banyak pada hal yang membosankan dan berulang: menulis kerangka
kode uji, merapikan tabel laporan, dan — yang paling berguna — memaksa saya
merumuskan ulang kriteria sampai bisa dinilai mesin. Setiap kali saya meminta
"nilai kualitas jawaban ini", jawabannya selalu terdengar masuk akal dan tidak bisa
dipakai; begitu saya memecahnya menjadi lima pertanyaan ya/tidak, barulah angkanya
punya arti.

AI menyesatkan saya pada dua hal. Pertama, ia sangat meyakinkan saat menghasilkan
"kutipan" yang sebenarnya disusun dari dua bagian dokumen — terlihat seperti bukti,
padahal bukan. Kedua, saat saya meminta bantuan menyusun acuan uji, dua jawaban
acuannya salah dan baru ketahuan setelah dibandingkan dengan dokumen aslinya (U01
dan P02); kalau saya percaya begitu saja, laporan evaluasi saya akan berisi dua
kegagalan sistem yang sebenarnya kegagalan acuan saya sendiri. Pelajarannya:
pekerjaan yang menentukan benar-salah tidak boleh diserahkan ke alat yang sedang
dinilai.

## 4. Kalau produk ini dipakai orang sungguhan mulai besok

Yang paling membuat saya khawatir bukan jawaban yang salah terang-terangan, tetapi
**kutipan yang tampak benar**. Pengguna yang melihat kutipan akan merasa sudah
memeriksa; padahal kutipan itu bisa saja hasil sambungan dua bagian, dan sistem tidak
memberi tahu bahwa ia menyambung. Kekhawatiran kedua: delapan dokumen yang saya pakai
semuanya dari perusahaan besar, sehingga pola yang terlihat akan terasa seperti
"begitulah kebijakan privasi di Indonesia" — padahal itu hanya kebiasaan delapan
perusahaan. Kekhawatiran ketiga: kunci API yang masih tersimpan di riwayat git. Itu
bukan risiko teoretis; siapa pun yang mengkloning repo bisa membacanya, dan
memperbaikinya harus saya lakukan **sebelum** produk dipakai orang lain.
