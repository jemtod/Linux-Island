# island-linux

Widget floating kecil untuk GNOME/Ubuntu, terinspirasi dari [taskbar-island](https://github.com/xfwil/taskbar-island) versi Windows. Versi lite berfokus pada media MPRIS dan lirik sinkron LRCLIB.

Saat ini tahap 3 tersedia: client MPRIS dan pill GTK4/libadwaita dengan cover, judul, artis, status playback, progress, waktu, dan tombol previous/play-pause/next. Lirik menyusul pada tahap berikutnya.

## Instalasi

Target proyek: Ubuntu 24.04 LTS, Python 3.11+. Jalankan dari sesi desktop pengguna, bukan lewat sudo, agar memakai session D-Bus yang sama dengan player.

```bash
sudo apt update
sudo apt install python3-venv python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
cd island-linux
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python island.py --inspect
python island.py
```

Putar lagu di Spotify, browser yang mengaktifkan MPRIS, atau VLC. `--inspect` mencetak JSON berisi judul, daftar artis, URL cover, durasi dan posisi dalam detik. Jeda player lalu ulangi: status menjadi `Paused`. Tutup semua player: muncul status kosong. Perintah ini mengambil satu snapshot; jalankan ulang untuk melihat perubahan.

Pengujian logic saja tidak memerlukan GTK, pydbus, koneksi jaringan, atau display:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

## Menguji kartu media tahap 3

Untuk memeriksa UI tanpa player atau D-Bus:

```bash
python island.py --demo
```

Pill berlabel `Demo` menampilkan lagu contoh, progress yang berjalan, dan tiga kontrol yang berfungsi pada data simulasi. Play/pause menghentikan/melanjutkan waktu demo; next/previous berpindah di antara tiga judul contoh. Tidak ada cover contoh; ikon audio GNOME menjadi fallback. Tutup dengan Esc atau Ctrl+Q saat pill memiliki fokus, lalu jalankan `python island.py` untuk metadata nyata. Pill memindai setiap satu detik di worker agar akses D-Bus tidak memblokir UI. Saat semua player ditutup, pill mengecil dengan ajakan memutar musik. Gangguan bus ditampilkan sebagai pesan dan dicoba lagi otomatis.

Saat lagu diputar, periksa cover, judul/artis, dan posisi terhadap player asli. Klik play/pause: status dan posisi mengikuti. Klik next/previous: player asli harus menerima perintah. Tombol yang tidak didukung capability player dinonaktifkan. Tab memindahkan fokus antar tombol; Enter/Space mengaktifkannya. Coba judul panjang: teks dipotong dengan elipsis dan teks lengkap tersedia saat di-hover. Buka window lain: pill seharusnya tetap di atas.

Cover mendukung HTTP/HTTPS, URI `file://`, dan path absolut. Pemuatan/decode dilakukan di worker terpisah, dengan batas 5 MiB dan timeout jaringan. Cover kosong, rusak, atau gagal diunduh memakai ikon audio; kontrol tetap berjalan. Respons cover lagu lama diabaikan bila lagu sudah berganti. URL gagal dicoba lagi setelah URL berubah atau aplikasi dijalankan ulang. Cover tidak disimpan ke disk.

Progress bar bersifat informatif, belum mendukung seek. Bila durasi tidak tersedia, waktu total ditampilkan `?:??` dan progress tetap nol. Posisi mengikuti snapshot MPRIS tiap detik, bukan perkiraan waktu lokal. Player kadang membatasi next/previous atau memperbarui status setelah jeda singkat.

Uji integrasi opsional memakai player tiruan di session D-Bus terisolasi. Jalankan dari terminal desktop dengan virtualenv aktif:

```bash
dbus-run-session -- env ISLAND_TEST_BUS=1 python tests/manual_media_ui.py
```

Window uji muncul sebentar, memuat cover fixture lokal, menjalankan ketiga kontrol, memeriksa antrean klik saat polling dan urutan fokus keyboard, lalu menutup. Hasil yang diharapkan: baris `PASS: D-Bus, metadata, cover, progress, PlayPause, antrean Next, Previous, fokus keyboard`. Skrip ini tidak termasuk koleksi pytest headless dan tidak mengontrol player di session desktop utama. Beberapa sistem menampilkan log portal GNOME selama session uji dibuat/dihentikan.

Secara default entry point mencoba backend X11, termasuk XWayland di GNOME Wayland, lalu fallback Wayland. Hint EWMH `ABOVE` dan posisi sudut dikirim melalui libX11; tidak memerlukan wmctrl atau layer-shell. Compositor tetap menentukan hasil akhirnya. Jika ingin memilih backend secara eksplisit:

```bash
GDK_BACKEND=x11 python island.py
GDK_BACKEND=wayland python island.py
```

Pada Wayland native, GTK4 tidak menyediakan posisi absolut/always-on-top: window biasa tetap muncul dan terminal memberi peringatan. Jangan gunakan backend native jika membutuhkan kedua fitur itu sekarang. Pada mesin tanpa XWayland, gunakan fallback native atau aktifkan XWayland pada sistem.

Ubah `POSITION` (`top-right`, `top-left`, `bottom-right`, `bottom-left`), `OFFSET_X`, `OFFSET_Y`, ukuran, font, dan warna di `island_linux/config.py`, lalu jalankan ulang. Posisi awal mengacu ke monitor utama X11. Offset belum memperhitungkan panel/dock; naikkan offset bila bertumpuk. Mixed-DPI/multi-monitor dan fullscreen perlu diuji lagi; always-on-top tidak berarti overlay di atas fullscreen, layar kunci, atau GNOME Overview.

Layout dan alasan warna dicatat di [DESIGN.md](DESIGN.md). Pengujian GTK memerlukan display; unit test tetap dapat dijalankan headless.

## Perilaku MPRIS

Hanya service `org.mpris.MediaPlayer2.*` yang dipindai. Player Playing didahulukan, lalu Paused. Saat status seri, player sebelumnya dipertahankan agar kartu tidak berpindah-pindah. Saat pertama memilih, nama service diurutkan untuk hasil konsisten. Player Stopped tidak ditampilkan.

`play_pause()`, `next()` dan `previous()` mengembalikan `False` bila tidak ada player atau capability tidak mendukung. Kegagalan perintah/bus menghasilkan `MprisError`. Player yang hilang saat dipindai dilewati. Import pydbus ditunda hingga koneksi nyata dibuat sehingga test mock bisa berjalan headless.

Metadata tidak selalu lengkap. Durasi/posisi tidak valid dianggap nol, progres dibatasi 0 sampai 1. URL cover disimpan apa adanya; pengunduhan akan ditambahkan bersama kartu media. Dukungan browser bergantung pada integrasi MPRIS dan metadata situs.

## Tahap berikutnya

1. Lirik LRCLIB, sinkronisasi waktu, romanisasi Jepang; lirik tidak selalu tersedia.
2. `--selftest`, CI Python 3.11/3.12, dan dokumentasi lengkap.

Roadmap setelah versi lite: kartu Claude usage, launcher tiles, auto-hide fullscreen, dan layer-shell Wayland.

## Lisensi dan kredit

MIT, lihat [LICENSE](LICENSE). taskbar-island menjadi inspirasi konsep; kode proyek ini ditulis untuk Linux dengan MPRIS.
