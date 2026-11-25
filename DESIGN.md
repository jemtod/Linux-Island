# Arah pill media

Widget pendamping desktop untuk melihat lagu tanpa membuka player. ENERGY 1, RHYTHM 1, MOTION 1: tenang, susunan tetap, tanpa animasi dekoratif.

- Bentuk pill mengikuti brief Dynamic Island, bukan bentuk tombol atau badge tambahan.
- Latar #202020 dan teks #f5f5f5 memisahkan metadata dari wallpaper yang beragam; tema gelap dipilih untuk widget kecil yang terus hadir di layar.
- Judul tebal menjadi fokus; artis #c4c4c4 berada di baris kedua agar hierarki terbaca pada ukuran kecil.
- Aksen #b8d9a0 hanya pada teks status aktual, tanpa dot atau glow.
- Sans sistem mendukung karakter Jepang dan mengikuti lingkungan GNOME tanpa font unduhan.
- Padding horizontal 20 dan vertikal 16/14 memberi ruang pada ujung lengkung; lebar 380 menampung cover dan metadata tanpa memperbesar jejak desktop berlebihan.
- Elipsis membatasi judul panjang; tooltip menyimpan teks lengkap tanpa markup dari metadata.
- Tidak ada hover-expand pada tahap awal agar isi stabil. Esc dan Ctrl+Q menutup window; Alt+drag (atau Super+drag sesuai pengaturan GNOME) dapat dipakai memindahkan window.

Kontras terukur terhadap latar: judul 14.94:1, artis 9.34:1, status 10.45:1.

## Kartu tahap 3

- Cover 64×64 di kiri menjadi petunjuk pengenalan album; ikon audio GNOME hanya dipakai ketika cover belum/tidak tersedia.
- Ikon kontrol memakai simbol media GNOME agar bentuknya sesuai desktop dan maknanya dikenal. Tombol 40×40 memberi target klik dan fokus yang cukup.
- Sudut tombol 10 berbeda dari sudut pill 32: bentuk tombol menandai kontrol, bukan miniatur pill dekoratif.
- Progress memakai aksen status yang sama; waktu terpisah di bawah bar membuat durasi tetap terbaca tanpa mengisi bar dengan teks.
- Outline fokus 2 piksel tetap terlihat pada navigasi keyboard; label aksesibel Putar/Jeda ikut berubah sesuai aksi.
- Jalur progress #707070 memiliki kontras 3.29:1 terhadap latar; isi aksen memiliki kontras 3.18:1 terhadap jalur. Ikon terang terhadap warna tombol aktif paling terang #626262 memiliki kontras 5.59:1.
