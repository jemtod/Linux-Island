# island-linux

Widget floating kecil untuk GNOME/Ubuntu, terinspirasi dari [taskbar-island](https://github.com/xfwil/taskbar-island) versi Windows. Versi lite berfokus pada media MPRIS dan lirik sinkron LRCLIB.

Saat ini tahap 1 tersedia: pemindaian player, metadata, pemilihan Playing sebelum Paused, kontrol MPRIS, dan inspeksi terminal. UI dan lirik belum diimplementasikan.

## Instalasi tahap 1

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
```

Putar lagu di Spotify, browser yang mengaktifkan MPRIS, atau VLC. `--inspect` mencetak JSON berisi judul, daftar artis, URL cover, durasi dan posisi dalam detik. Jeda player lalu ulangi: status menjadi `Paused`. Tutup semua player: muncul status kosong. Perintah ini mengambil satu snapshot; jalankan ulang untuk melihat perubahan.

Pengujian logic saja tidak memerlukan GTK, pydbus, koneksi jaringan, atau display:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

## Perilaku MPRIS

Hanya service `org.mpris.MediaPlayer2.*` yang dipindai. Player Playing didahulukan, lalu Paused. Saat status seri, player sebelumnya dipertahankan agar kartu tidak berpindah-pindah. Saat pertama memilih, nama service diurutkan untuk hasil konsisten. Player Stopped tidak ditampilkan.

`play_pause()`, `next()` dan `previous()` mengembalikan `False` bila tidak ada player atau capability tidak mendukung. Kegagalan perintah/bus menghasilkan `MprisError`. Player yang hilang saat dipindai dilewati. Import pydbus ditunda hingga koneksi nyata dibuat sehingga test mock bisa berjalan headless.

Metadata tidak selalu lengkap. Durasi/posisi tidak valid dianggap nol, progres dibatasi 0 sampai 1. URL cover disimpan apa adanya; pengunduhan akan ditambahkan bersama kartu media. Dukungan browser bergantung pada integrasi MPRIS dan metadata situs.

## Tahap berikutnya

1. Pill GTK4/libadwaita dasar dengan judul dan artis.
2. Kartu media lengkap: cover, progres, dan tombol kontrol.
3. Lirik LRCLIB, sinkronisasi waktu, romanisasi Jepang; lirik tidak selalu tersedia.
4. `--selftest`, CI Python 3.11/3.12, dan dokumentasi lengkap.

Posisi absolut dan always-on-top pada GTK4/Wayland perlu diuji pada desktop nyata; belum ada klaim dukungan pada tahap ini. Roadmap setelah versi lite: kartu Claude usage, launcher tiles, auto-hide fullscreen, dan layer-shell Wayland.

## Lisensi dan kredit

MIT, lihat [LICENSE](LICENSE). taskbar-island menjadi inspirasi konsep; kode proyek ini ditulis untuk Linux dengan MPRIS.
