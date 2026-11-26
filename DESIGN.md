# Arah pill media

Widget pendamping desktop untuk melihat lagu tanpa membuka player. ENERGY 1, RHYTHM 1, MOTION 1: tenang, susunan tetap, tanpa animasi dekoratif.

- Bentuk pill mengikuti brief Dynamic Island, bukan bentuk tombol atau badge tambahan.
- Latar #202020 dan teks #f5f5f5 memisahkan metadata dari wallpaper yang beragam; tema gelap dipilih untuk widget kecil yang terus hadir di layar.
- Judul tebal menjadi fokus; artis #c4c4c4 berada di baris kedua agar hierarki terbaca pada ukuran kecil.
- Aksen #b8d9a0 hanya pada teks status aktual, tanpa dot atau glow.
- Sans sistem mendukung karakter Jepang dan mengikuti lingkungan GNOME tanpa font unduhan.
- Padding horizontal 20 dan vertikal 16/14 memberi ruang pada ujung lengkung; lebar 380 menampung cover dan metadata tanpa memperbesar jejak desktop berlebihan.
- Elipsis membatasi judul panjang; tooltip menyimpan teks lengkap tanpa markup dari metadata.
- Tidak ada hover-expand agar pill tidak membesar tanpa sengaja saat pointer melintas. Klik/sentuhan membuka kartu, Esc mengecilkan lebih dulu, Ctrl+Q menutup window.

Kontras terukur terhadap latar: judul 14.94:1, artis 9.34:1, status 10.45:1.

## Kartu tahap 3

- Cover 64×64 di kiri menjadi petunjuk pengenalan album; ikon audio GNOME hanya dipakai ketika cover belum/tidak tersedia.
- Ikon kontrol memakai simbol media GNOME agar bentuknya sesuai desktop dan maknanya dikenal. Tombol 40×40 memberi target klik dan fokus yang cukup.
- Sudut tombol 10 berbeda dari sudut pill 32: bentuk tombol menandai kontrol, bukan miniatur pill dekoratif.
- Progress memakai aksen status yang sama; waktu terpisah di bawah bar membuat durasi tetap terbaca tanpa mengisi bar dengan teks.
- Outline fokus 2 piksel tetap terlihat pada navigasi keyboard; label aksesibel Putar/Jeda ikut berubah sesuai aksi.
- Jalur progress #707070 memiliki kontras 3.29:1 terhadap latar; isi aksen memiliki kontras 3.18:1 terhadap jalur. Ikon terang terhadap warna tombol aktif paling terang #626262 memiliki kontras 5.59:1.

## Lirik tahap 4

- Tiga baris di bawah kontrol memberi ruang tetap untuk baris aktif, romaji, dan baris berikutnya tanpa membuat metadata bergeser saat lirik berubah.
- Baris aktif memakai warna judul; romaji dan pratinjau memakai warna sekunder agar hierarkinya terbaca tanpa tambahan aksen.
- Pergantian baris langsung mengikuti posisi playback. Tidak ada animasi gulir atau marquee yang memindahkan teks saat dibaca.
- Teks asli tetap terlihat pada lirik Jepang; romaji membantu membaca tanpa menggantikan sumber.
- Lirik panjang memakai elipsis dan tooltip penuh agar pill tetap 380 piksel. Ukuran kartu aktif terukur 380×243 pada lingkungan uji.
- Pesan mencari, gagal, tidak ditemukan, instrumental, dan tanpa timestamp memakai area yang sama agar kontrol media tetap tersedia.

## Pill kecil di dekat jam

- Posisi top-center menyelaraskan pusat pill dengan jam GNOME, mengikuti referensi pengguna. Jarak atas 40 mempertahankan akses ke panel.
- Ukuran awal 200×40 menampilkan ikon status playback dan judul singkat; kontrol serta lirik dibuka sesuai kebutuhan agar tidak menutupi pekerjaan.
- Bentuk kecil dan kartu penuh memakai warna/radius yang sama agar terbaca sebagai widget yang sama. Stack tidak homogen memungkinkan ukuran window benar-benar mengecil.
- Tombol native memenuhi aktivasi pointer/sentuhan dan Enter/Space; label aksesibel serta outline fokus tersedia. `Kecilkan` memberi jalan kembali tanpa harus menebak gesture.
- Perubahan ukuran langsung tanpa animasi mengikuti MOTION 1. Koordinat dihitung ulang sesudah alokasi GTK agar pusat tetap sejajar saat ukuran berganti.

## Jam dan media dalam panel

- Permintaan lanjutan pengguna memindahkan indikator ringkas ke panel native GNOME. Jam dan tombol lagu memiliki satu latar #202020 dengan ujung bulat, sehingga tidak ada pill yang mengambang di bawah jam.
- Jam/kalender tetap actor asli GNOME; tombol media berada di sebelahnya agar dua aksi tidak bertabrakan. Menonaktifkan extension mengembalikan actor jam ke tempat semula.
- Judul dibatasi 150 piksel dan ikon 12 piksel agar indikator tidak menghabiskan lebar panel. Teks/ikon memakai warna pill yang sudah diuji kontras.
- Kartu lengkap tetap memakai GTK dan dibuka saat diminta. Kecilkan/Esc menutup kartu pada mode panel agar tidak menyisakan indikator kedua.
