# island-linux

Widget floating kecil untuk GNOME/Ubuntu, terinspirasi dari [taskbar-island](https://github.com/xfwil/taskbar-island) versi Windows. Versi lite berfokus pada media MPRIS dan lirik sinkron LRCLIB.

Versi lite menyediakan cover, metadata, progress, kontrol media, serta lirik sinkron LRCLIB dan romanisasi Jepang. Logic MPRIS dan lirik terpisah dari GTK agar bisa diuji headless. Kartu Claude usage dan launcher belum termasuk versi ini.

Pill mulai kecil (200×40) di tengah atas, tepat di bawah panel jam GNOME. Klik/sentuh pill untuk membuka kartu lengkap. Tombol `Kecilkan` atau Esc mengembalikannya ke bentuk kecil; Esc saat sudah kecil menutup aplikasi. Ctrl+Q selalu menutup saat window fokus. Aktivasi melalui Enter/Space juga didukung. Bentuk membesar langsung tanpa animasi; tidak membuka otomatis saat hover.

## Instalasi

Target proyek: Ubuntu 24.04 LTS dengan GNOME, Python 3.11+ (Python bawaan Ubuntu 24.04 adalah 3.12), GTK4 dan libadwaita. Gunakan Python sistem Ubuntu untuk GUI agar binding `python3-gi` cocok dengan interpreter. Virtualenv menggunakan `--system-site-packages` untuk mengakses binding tersebut. Jalankan aplikasi dari sesi desktop pengguna, bukan lewat sudo, agar memakai session D-Bus yang sama dengan player.

```bash
sudo apt update
sudo apt install python3-venv python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gdkpixbuf-2.0 libx11-6 xwayland dbus
cd island-linux
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python island.py --selftest
python island.py --inspect
python island.py
```

Putar lagu di Spotify, browser yang mengaktifkan MPRIS, atau VLC. `--inspect` mencetak JSON berisi judul, daftar artis, URL cover, durasi dan posisi dalam detik. Jeda player lalu ulangi: status menjadi `Paused`. Tutup semua player: muncul status kosong. Perintah ini mengambil satu snapshot; jalankan ulang untuk melihat perubahan.

Instalasi membutuhkan internet; pengujian logic berikut berjalan tanpa GTK, pydbus, koneksi jaringan, atau display. Gunakan virtualenv terpisah jika ingin menguji lingkungan minimal:

```bash
python3 -m venv .venv-headless
source .venv-headless/bin/activate
python -m pip install -r requirements-core.txt -r requirements-dev.txt
python -m pytest -q
deactivate
```

Folder `.venv-headless` tidak diperlukan untuk menjalankan GUI. Aktifkan kembali `.venv` sebelum menjalankan pill.

## Selftest dan CI

Selftest hanya memerlukan Python standar, bahkan tanpa dependensi pip:

```bash
python3 island.py --selftest
```

Hasil yang diharapkan: dua baris `PASS`, satu untuk MPRIS dan satu untuk lirik, dengan exit code 0. Bila pemeriksaan gagal, muncul `FAIL` dan exit code 1. Pemeriksaan meliputi metadata dan satuan waktu, prioritas player, tiga kontrol mock, fallback LRCLIB, cache, pemilihan baris, dan alur romanisasi mock. Selftest tidak menguji koneksi bus nyata, layanan LRCLIB, GTK, atau kamus pykakasi; gunakan pytest dan uji integrasi desktop untuk cakupan itu.

Mode `--selftest`, `--inspect`, dan `--demo` saling eksklusif. Tanpa opsi, aplikasi membuka GUI. `--inspect` membutuhkan pydbus dan session bus nyata, tetapi tidak membuka window.

[Workflow CI](.github/workflows/ci.yml) menjalankan pytest dan selftest pada Python 3.11 serta 3.12 di runner Ubuntu 24.04. Runner hanya memasang dependensi logic/test. Pengujian yang memerlukan GTK/display berada di `tests/manual_media_ui.py`, di luar pola koleksi `test_*.py`, sehingga tidak dijalankan pada CI headless. Workflow baru berjalan setelah repository di-push ke GitHub; hasil lokal bukan bukti bahwa GitHub Actions sudah berjalan.

## Struktur proyek

```text
island.py                  # CLI, inspeksi, selftest, atau GUI
island_linux/
  config.py                # Posisi, tema, font, identitas LRCLIB
  mpris_client.py          # Seleksi player, metadata, kontrol
  lyrics.py                # LRCLIB, parser LRC, romanisasi, cache
  selftest.py              # Pemeriksaan logic offline
  ui/
    pill.py                # Window dan worker D-Bus
    card_media.py          # Kartu media dan worker lirik/cover
    artwork.py             # Pembacaan cover lokal/HTTP
    x11.py                 # Hint posisi dan above pada X11
tests/                     # Unit test headless dan uji desktop opsional
.github/workflows/ci.yml    # Matrix Python 3.11/3.12
```

## Menguji kartu media

Untuk memeriksa UI tanpa player atau D-Bus:

```bash
python island.py --demo
```

Klik pill kecil untuk melihat kartu berlabel `Demo` dengan lagu contoh, progress yang berjalan, dan tiga kontrol yang berfungsi pada data simulasi. Play/pause menghentikan/melanjutkan waktu demo; next/previous berpindah di antara tiga judul contoh. Tidak ada cover contoh; ikon audio GNOME menjadi fallback. Tutup dengan Ctrl+Q saat pill memiliki fokus, lalu jalankan `python island.py` untuk metadata nyata. Pill memindai setiap satu detik di worker agar akses D-Bus tidak memblokir UI. Saat semua player ditutup, pill kecil menampilkan `Tidak ada media`; kartu yang sedang terbuka menampilkan ajakan memutar musik. Gangguan bus ditampilkan sebagai pesan dan dicoba lagi otomatis.

Saat lagu diputar, periksa cover, judul/artis, dan posisi terhadap player asli. Klik play/pause: status dan posisi mengikuti. Klik next/previous: player asli harus menerima perintah. Tombol yang tidak didukung capability player dinonaktifkan. Tab memindahkan fokus antar tombol; Enter/Space mengaktifkannya. Coba judul panjang: teks dipotong dengan elipsis dan teks lengkap tersedia saat di-hover. Buka window lain: pill seharusnya tetap di atas.

Cover mendukung HTTP/HTTPS, URI `file://`, dan path absolut. Pemuatan/decode dilakukan di worker terpisah, dengan batas 5 MiB dan timeout jaringan. Cover kosong, rusak, atau gagal diunduh memakai ikon audio; kontrol tetap berjalan. Respons cover lagu lama diabaikan bila lagu sudah berganti. URL gagal dicoba lagi setelah URL berubah atau aplikasi dijalankan ulang. Cover tidak disimpan ke disk.

Progress bar bersifat informatif, belum mendukung seek. Bila durasi tidak tersedia, waktu total ditampilkan `?:??` dan progress tetap nol. Posisi mengikuti snapshot MPRIS tiap detik, bukan perkiraan waktu lokal. Player kadang membatasi next/previous atau memperbarui status setelah jeda singkat.

Uji integrasi opsional memakai player tiruan di session D-Bus terisolasi. Jalankan dari terminal desktop dengan virtualenv aktif:

```bash
dbus-run-session -- env ISLAND_TEST_BUS=1 python tests/manual_media_ui.py
```

Window uji muncul sebentar, memuat cover fixture lokal, menjalankan ketiga kontrol, memeriksa antrean klik saat polling, urutan fokus keyboard, sinkronisasi lirik, dan romaji, lalu menutup. Hasil yang diharapkan: baris `PASS: D-Bus, cover, progress, kontrol, fokus, lirik, romaji, seek maju/mundur, respons lagu lama`. HTTP LRCLIB dimock memakai `responses`; tidak ada akses internet dari skrip uji ini. Skrip tidak termasuk koleksi pytest headless dan tidak mengontrol player di session desktop utama. Beberapa sistem menampilkan log portal GNOME selama session uji dibuat/dihentikan.

## Menguji lirik

Perbarui dependensi pada virtualenv aktif, lalu jalankan demo tanpa internet:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python island.py --demo
```

Bagian bawah kartu menampilkan baris aktif, romaji bila ada teks Jepang, serta pratinjau baris berikutnya. Demo memakai teks contoh buatan proyek. Setelah beberapa detik, teks Jepang dan romaji muncul. Tombol jeda menghentikan posisi lirik; next/previous memulai waktu contoh dari nol. Baris berganti langsung tanpa animasi agar mudah dibaca. Teks panjang dipotong dengan elipsis; arahkan pointer untuk membaca tooltip lengkap.

Untuk lagu nyata, jalankan `python island.py`, lalu putar lagu di player MPRIS. Saat terhubung internet dan LRCLIB memiliki lirik sinkron yang cocok, baris mengikuti posisi player setiap satu detik. Seek di aplikasi player asli untuk memeriksa lompatan maju/mundur. Jeda tidak menggeser lirik bila posisi MPRIS tetap. Pindah lagu saat lirik masih dimuat: respons lagu sebelumnya harus diabaikan.

Client mencoba `/api/get` dengan artis pertama, judul, dan durasi jika valid, lalu `/api/search` bila lirik sinkron belum ditemukan. Kandidat pencarian harus cocok pada judul/artis yang dinormalisasi, dengan selisih durasi paling besar tiga detik jika durasi diketahui. Pencocokan ini bisa melewatkan metadata dengan tambahan judul live/remix atau nama artis yang berbeda. Tanpa durasi, versi rekaman lebih sulit dibedakan.

Cache hanya di memori, maksimal 64 lagu: hasil tersedia disimpan 30 menit, hasil tidak ditemukan 5 menit. Polling playback tidak mengulang permintaan lirik setiap detik. Kegagalan jaringan dicoba lagi setelah sekitar satu menit selama lagu tetap aktif; respons pembatasan layanan mengikuti `Retry-After` dengan tambahan jeda kecil. Lirik yang tidak ditemukan dicari kembali saat lagu berganti kembali, sesuai umur cache, atau setelah aplikasi dijalankan ulang.

Status `Lirik tersedia tanpa timestamp` berarti LRCLIB punya teks tanpa waktu; teks tersebut tidak dipaksakan menjadi lirik sinkron. Lagu instrumental dan metadata yang kurang juga diberi pesan tersendiri. Timestamp kosong pada LRC ditampilkan sebagai `Jeda lirik`, bukan mempertahankan baris sebelumnya. Parser mendukung timestamp berulang dan offset LRC; offset positif memajukan waktu tampil.

Romanisasi memakai pykakasi dalam worker dan mempertahankan teks asli. Deteksi didasarkan pada kana/kanji, sehingga teks Han non-Jepang juga bisa dianggap Jepang. Bacaan kanji dan pemisahan kata tidak selalu sesuai konteks atau pengucapan penyanyi.

Header identitas client dapat diubah melalui `LRCLIB_USER_AGENT` di config.py. Nilai bawaan menandai build lokal; tambahkan URL proyek publik atau kontak yang benar bila mendistribusikannya. Referensi implementasi: [API LRCLIB](https://lrclib.net/docs.md) dan [API pykakasi](https://pykakasi.readthedocs.io/en/latest/api.html).

## Posisi dan backend desktop

Secara default entry point mencoba backend X11, termasuk XWayland di GNOME Wayland, lalu fallback Wayland. Hint EWMH `ABOVE` dan posisi sudut dikirim melalui libX11; tidak memerlukan wmctrl atau layer-shell. Compositor tetap menentukan hasil akhirnya. Jika ingin memilih backend secara eksplisit:

```bash
GDK_BACKEND=x11 python island.py
GDK_BACKEND=wayland python island.py
```

Pada Wayland native, GTK4 tidak menyediakan posisi absolut/always-on-top: window biasa tetap muncul dan terminal memberi peringatan. Jangan gunakan backend native jika membutuhkan kedua fitur itu sekarang. Pada mesin tanpa XWayland, gunakan fallback native atau aktifkan XWayland pada sistem.

Ubah `POSITION` (`top-center` sebagai default, `top-right`, `top-left`, `bottom-center`, `bottom-right`, `bottom-left`), `OFFSET_X`, `OFFSET_Y`, `COMPACT_WIDTH`, `WIDTH`, font, dan warna di `island_linux/config.py`, lalu jalankan ulang. Posisi awal mengacu ke monitor utama X11. Pada posisi center, `OFFSET_X` diabaikan agar pill tetap tepat di tengah meskipun ukurannya berubah. `OFFSET_Y=40` memberi jarak dari tepi atas untuk panel GNOME standar; sesuaikan jika tinggi panel berbeda. Widget ini tidak menggantikan atau menempel di dalam panel jam GNOME; integrasi panel membutuhkan extension GNOME tersendiri. Mixed-DPI/multi-monitor dan fullscreen perlu diuji lagi; always-on-top tidak berarti overlay di atas fullscreen, layar kunci, atau GNOME Overview.

Layout dan alasan warna dicatat di [DESIGN.md](DESIGN.md). Pengujian GTK memerlukan display; unit test tetap dapat dijalankan headless.

## Perilaku MPRIS

Hanya service `org.mpris.MediaPlayer2.*` yang dipindai. Player Playing didahulukan, lalu Paused. Saat status seri, player sebelumnya dipertahankan agar kartu tidak berpindah-pindah. Saat pertama memilih, nama service diurutkan untuk hasil konsisten. Player Stopped tidak ditampilkan.

`play_pause()`, `next()` dan `previous()` mengembalikan `False` bila tidak ada player atau capability tidak mendukung. Kegagalan perintah/bus menghasilkan `MprisError`. Player yang hilang saat dipindai dilewati. Import pydbus ditunda hingga koneksi nyata dibuat sehingga test mock bisa berjalan headless.

Metadata tidak selalu lengkap. Durasi/posisi tidak valid dianggap nol, progres dibatasi 0 sampai 1. URL cover diteruskan ke worker pemuatan kartu media. Dukungan browser bergantung pada integrasi MPRIS dan metadata situs.

## Batas versi lite dan troubleshooting

- Jika `import gi` gagal, pastikan memakai Python sistem dan virtualenv dibuat dengan `--system-site-packages`. Interpreter unduhan atau versi Python lain belum tentu dapat memuat binding apt.
- Jika player tidak terdeteksi, jalankan `python island.py --inspect` dari terminal sesi desktop yang sama. Periksa bahwa player/browser mengekspos service MPRIS; hanya status Playing/Paused yang dipilih.
- Durasi, posisi, cover, dan capability mengikuti data player. Metadata yang kurang atau posisi yang jarang diperbarui bisa membuat tampilan tidak lengkap/terlambat.
- LRCLIB tidak selalu memiliki lagu atau versi rekaman yang cocok. Romanisasi otomatis memiliki batas bacaan kanji; deteksi karakter Han juga dapat menangkap bahasa selain Jepang.
- Wayland native belum mendukung posisi sudut/above. Backend XWayland memakai hint compositor; fullscreen, GNOME Overview, mixed-DPI, dan multi-monitor belum dijamin.
- Progress belum dapat dipakai seek. Belum ada hover-expand, autostart, atau installer desktop. Pill dibuka melalui klik/sentuhan atau keyboard, lalu dikecilkan melalui tombol atau Esc. Ctrl+Q saat window fokus menutup aplikasi.
- Worker memakai timeout jaringan, tetapi penutupan proses dapat menunggu request aktif selesai. Cache lirik hanya bertahan selama proses berjalan.

## Roadmap

Kartu Claude usage, launcher tiles, auto-hide fullscreen, dan dukungan layer-shell Wayland menyusul setelah versi lite. Bukti pengujian dan batas lingkungan dicatat di [VALIDATION.md](VALIDATION.md).

## Lisensi dan kredit

MIT, lihat [LICENSE](LICENSE). taskbar-island menjadi inspirasi konsep; kode proyek ini ditulis untuk Linux dengan MPRIS.
