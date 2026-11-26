# Validasi runtime

## Pembaruan pill kecil dan posisi tengah atas

- PASS: pill demo dijalankan pada GNOME/XWayland dan hasil render diperiksa. `xwininfo` menunjukkan ukuran 200×40 di (583,40), kartu terbuka 380×288 di (493,40), lalu kembali ke 200×40 di (583,40), pada monitor 1366×768. Pusat horizontal ketiganya tetap 683.
- PASS: aktivasi `clicked` pada pill membuka kartu, tombol Kecilkan menutup kartu, Esc pada kartu mengembalikan pill kecil. Kontrol play/pause tetap bekerja setelah expand. Ini pemeriksaan sinyal GTK, bukan pengujian hardware layar sentuh.
- PASS: uji integrasi `tests/manual_media_ui.py` membuka pill melalui tombol ringkas sebelum memeriksa D-Bus, cover, progress, kontrol, fokus, lirik, romaji, dan seek. Semua pemeriksaan lulus. 67 test headless tetap lulus.
- Delivery Gate Hard PASS: tombol native memiliki label, tooltip, cursor, state hover/active dan outline fokus; tidak ada kontrol mati atau aset baru. Kontras menggunakan warna pill sebelumnya yang sudah diukur. Pilihan pengguna menjadi arahan eksplisit untuk bentuk/posisi baru.
- Delivery Gate Purpose/Liveliness PASS: ENERGY/RHYTHM/MOTION 1/1/1 dipertahankan; widget kecil menghemat ruang, expand menampilkan fungsi sesuai kebutuhan, tanpa animasi dekoratif. Alasan tercatat di DESIGN.md.
- Delivery Gate Craftsmanship PASS untuk skenario diuji: window benar-benar berubah ukuran dan tetap terpusat; metadata terus diperbarui saat ringkas. Posisi native Wayland tetap dibatasi seperti sebelumnya. Integrasi ke panel jam belum termasuk; window berada di bawah panel. Perangkat sentuh fisik belum diuji.

## Tahap 5: selftest, CI, dan dokumentasi

- PASS: `python3 -S -O island.py --selftest` menghasilkan dua PASS dengan exit code 0. Opsi `-S` menonaktifkan site-packages; `-O` memastikan pemeriksaan tidak bergantung pada assert yang bisa dihapus interpreter.
- PASS: subprocess selftest diuji dengan DISPLAY, WAYLAND_DISPLAY, dan DBUS_SESSION_BUS_ADDRESS dikeluarkan dari environment. Kegagalan pemeriksaan menghasilkan FAIL/exit code 1; kombinasi mode CLI yang bertentangan ditolak.
- PASS: 67 test pada virtualenv proyek, lalu 67 test pada virtualenv baru `/tmp/island-headless-stage5` tanpa GTK/pydbus. Virtualenv baru hanya memasang requirements-core.txt dan requirements-dev.txt; romanisasi pykakasi nyata ikut diuji. `pip check` tidak menemukan dependensi rusak.
- PASS: kompilasi Python, `git diff --check`, dan pembacaan YAML workflow; matrix berisi Python 3.11 dan 3.12.
- Batas: interpreter lokal yang tersedia adalah Python 3.14. Pengujian Python 3.11/3.12 ditetapkan dalam workflow, belum dieksekusi di lingkungan ini. GitHub Actions belum berjalan karena proyek belum dipublikasikan/push ke GitHub. Tidak ada klaim bahwa selftest memeriksa player, GTK, atau jaringan nyata.
- Dokumentasi mencakup paket apt, perbedaan Python sistem/binding GI, virtualenv GUI/headless, semua mode CLI, struktur modul, known limitations, kredit inspirasi, MIT, dan roadmap. Perubahan LICENSE yang sudah ada di workspace tidak dimasukkan dalam commit tahap ini.

### Delivery Gate tahap 5

- Hard Gate PASS: selftest dan CLI dijalankan nyata, termasuk jalur gagal dan konflik opsi; tidak ada fitur baru yang memerlukan klik UI. Copy Indonesia baru tidak memakai em dash atau klaim hasil CI yang belum terjadi (R-02/26/35/36).
- Hard Gate PASS: tidak ada aset visual, angka pemasaran, testimoni, navigasi UI, atau state GUI baru. Batas selftest dijelaskan di output dan README (R-17/18/23/24/27/28/38).
- Purpose Gate PASS: tahap ini hanya menambahkan pemeriksaan logic/CI/dokumentasi; tidak ada dekorasi atau keputusan visual baru. Bukti kontras dan UI tahap 4 tetap tercatat di bawah.
- Liveliness PASS: arah pill ENERGY/RHYTHM/MOTION 1/1/1 tidak berubah; pekerjaan tahap ini tidak mengubah tampilan.
- Craftsmanship PASS: core/test dependency dipisahkan agar runner headless tidak perlu binding GTK, CLI mode eksklusif, selftest offline tidak bergantung pada dependency pengujian pip, dan instruksi README sesuai file final (C-1/2/3/4/5).

## Tahap 4: lirik sinkron

- PASS: 63 test headless pada virtualenv Python 3.14, termasuk 35 kasus baru untuk format JSON LRCLIB, timestamp pecahan/berulang, offset, baris kosong, batas waktu pemilihan baris, fallback, cache, metadata kurang, HTTP error/timeout, Retry-After, dan pykakasi nyata.
- PASS: uji GTK + D-Bus terisolasi pada `tests/manual_media_ui.py` memakai respons HTTP mock. Baris Jepang/romaji tampil, seek 65→71→6 detik mengganti baris dengan tepat, pergantian judul meminta hasil baru, dan callback dari generasi lagu lama diabaikan. Semua kontrol tahap 3 tetap bekerja.
- PASS: client juga dipanggil ke LRCLIB nyata melalui koneksi jaringan. Hasil `synced`, 60 baris, tanpa mencetak atau menyimpan teks lagu dalam artefak proyek. Ini verifikasi layanan, bukan pengujian dengan player Spotify/browser milik pengguna.
- PASS: pill demo 380×243 dijalankan dan render diperiksa visual. Teks Jepang asli, romaji, dan pratinjau terlihat tanpa memperlebar kartu.
- PASS: status tanpa timestamp, instrumental, tidak ditemukan, metadata kurang, dan error diperiksa pada widget GTK nyata. Pemulihan setelah error mengembalikan lirik demo melalui worker.
- Batas: waktu pembaruan mengikuti polling MPRIS satu detik. Tidak ada word-level karaoke, koreksi offset per lagu, tampilan penuh lirik unsynced, atau jaminan bacaan kanji sesuai nyanyian. Ubuntu target dan Python 3.11/3.12 belum dijalankan di lingkungan ini.

### Delivery Gate tahap 4

- Hard Gate PASS: copy baru tanpa em dash; seluruh teks demo merupakan fixture berlabel, tanpa kutipan lirik lagu nyata dalam kode, screenshot produk, atau README. Tidak ada aset, statistik, atau navigasi rekaan (R-02/17/18/23/24/28/36/38).
- Hard Gate PASS: label lirik memakai elipsis dan tooltip, tiga baris memiliki ruang tetap, warna teks memakai pasangan yang sudah diukur 14.94:1 dan 9.34:1 (R-03/25/40). Cakupan desktop; pembesaran ekstrem dan screen reader belum diuji.
- Hard Gate PASS: loading/empty/error dibedakan dengan teks; kontrol tetap berfungsi melalui D-Bus uji dan urutan fokus sebelumnya terjaga (R-26/27/32/35/39).
- Hard Gate PASS: modul inti tidak mengimpor GTK, fitur ditulis langsung dalam modul, tidak ada toggle tema/animasi baru; arah dan alasan area lirik dicatat di DESIGN.md (R-33/34/37).
- Purpose Gate PASS: tidak ada teknik dekoratif baru. Penempatan, font, warna, dan pergantian baris punya alasan keterbacaan yang tertulis (R-01/04/06/07/08/09/10/12/13/14/19/22).
- Liveliness PASS: ENERGY/RHYTHM/MOTION tetap 1/1/1; lirik aktif dibedakan dari romaji/pratinjau lewat hierarki teks, tanpa menambah warna atau gerak dekoratif.
- Craftsmanship PASS untuk skenario yang diuji: request dan romanisasi berjalan di worker terpisah dari D-Bus, hasil lama ditolak dengan generation ID, retry tidak membanjiri layanan, dan status tanpa sinkronisasi tidak diberi timing rekaan (C-1/2/3/4/5 dan quality locks).

## Tahap 3: kartu media

Pemeriksaan menggunakan GTK4/libadwaita pada display GNOME melalui XWayland, Python 3.14 dan dependensi virtualenv. Player Spotify/browser milik pengguna tidak dikontrol selama pengujian. Ubuntu 24.04, Python 3.11/3.12, mixed-DPI, dan fullscreen belum diuji langsung.

- PASS: 28 unit test headless (`python3 -m pytest -q`): metadata/pemilihan/kontrol MPRIS, URI cover lokal berkarakter khusus, HTTP mock, penutupan respons saat error, dan batas ukuran unduhan.
- PASS: kompilasi Python dan `git diff --check`.
- PASS: kartu demo 380×175 dijalankan pada desktop dan hasil render diperiksa visual; tiga tombol demo mengganti lagu/status, progress dan waktu mengikuti snapshot.
- PASS: decoder cover menghasilkan gambar 64×64; hasil lama diabaikan. Skenario tanpa media, tanpa durasi, error, dan tombol tanpa capability diperiksa melalui widget GTK nyata.
- PASS: `dbus-run-session -- env ISLAND_TEST_BUS=1 .venv/bin/python tests/manual_media_ui.py` menghubungkan kartu ke client pydbus dan server MPRIS tiruan lewat session bus nyata. Ketiga method diterima; klik next saat polling masuk antrean; metadata, waktu, cover lokal, dan fokus previous/play/next diperiksa.
- PASS: properti X11 kartu masih mencakup `ABOVE` dan `SKIP_TASKBAR`.
- Batas: HTTP diuji dengan respons mock; belum ada klaim unduhan cover dari Spotify/browser nyata. Uji sinyal tombol memakai `clicked`, bukan klik mouse fisik. Navigasi fokus memakai API GTK, bukan input keyboard fisik.

### Delivery Gate tahap 3

- Hard Gate PASS (R-02/17/18/23/24/28/36/38): tidak ada em dash pada copy baru, aset produk rekaan, statistik, FAQ, atau navigasi palsu. Bitmap satu warna hanya fixture uji sementara dan dihapus setelah uji.
- Hard Gate PASS (R-03/25/32/39): metadata memakai elipsis/tooltip; tombol native GTK 40×40 memiliki label aksesibel, status enabled/disabled, cursor, hover/active, dan outline fokus. Urutan fokus diperiksa di uji integrasi. Cakupan desktop, bukan klaim dukungan mobile atau screen reader menyeluruh.
- Hard Gate PASS (R-26/27/35): ketiga tombol dieksekusi sampai ke server MPRIS uji; loading/empty/error memiliki teks. Runtime kartu dijalankan, bukan hanya dikompilasi.
- Hard Gate PASS (R-33/34/37/40): kode fitur ditulis langsung dalam modul, arah desain ada di DESIGN.md; tema tetap punya alasan, tidak ada toggle atau animasi. Cover punya alokasi 64×64; aturan dokumen/media web tidak berlaku.
- Purpose Gate PASS (R-01/04/06/07/08/09/10/12/13/14/19/22): ikon media GNOME dan ikon audio fallback relevan, tipografi/alokasi/warna dijelaskan di DESIGN.md; tidak ada gradien, glass, glow, badge, atau animasi dekoratif.
- Liveliness PASS: ENERGY/RHYTHM/MOTION tetap 1/1/1, judul dan cover menjadi titik perhatian, jarak memisahkan metadata/progress/kontrol, aksen digunakan untuk status/progress/fokus.
- Craftsmanship PASS (C-1/2/3/5 dan quality locks): kartu hanya berisi fitur tahap ini, progres informatif tidak menyamar sebagai seek, kontrol unsupported nonaktif, batas backend dijelaskan; semua pilihan visual utama punya alasan.
- Resilience PASS untuk skenario yang diuji (C-4): cover gagal/tidak tersedia mempertahankan kontrol, cover lama diabaikan, capability dan durasi kosong ditangani, pekerjaan jaringan dan D-Bus berada di worker terpisah. Target Ubuntu, pembesaran teks ekstrem, dan lingkungan multi-monitor tetap membutuhkan uji lanjutan.
- Contrast PASS: judul/artis/status mempertahankan 14.94/9.34/10.45:1 terhadap latar. Ikon pada background tombol aktif paling terang 5.59:1; jalur progress terhadap latar 3.29:1; isi progress terhadap jalur 3.18:1. Dihitung dengan contrast-check.py.

## Riwayat tahap 2

Pemeriksaan dilakukan pada sesi GNOME Wayland dengan GTK4 4.22, libadwaita 1.9, Python sistem 3.14. Target instalasi tetap Ubuntu 24.04/Python 3.11+. Kompatibilitas versi target dan metadata player nyata belum diverifikasi di lingkungan ini karena pydbus belum terpasang. Data demo dan simulasi status diberi label, bukan bukti integrasi player nyata.

## Bukti runtime

- PASS: `python3 -m pytest -q`, 20 test logic MPRIS.
- PASS: `python3 -m compileall -q island.py island_linux` dan `git diff --check`.
- PASS: pill demo dijalankan pada display desktop dengan `GDK_BACKEND=x11`; ukuran 340×85, map state `IsViewable`.
- PASS: `xprop` pada XID pill menunjukkan `_NET_WM_STATE_ABOVE` dan `_NET_WM_STATE_SKIP_TASKBAR`.
- PASS: `xwininfo` menunjukkan koordinat (1002, 40) pada monitor 1366×768: offset kanan 24, atas 40.
- PASS: hasil render GTK disimpan sementara sebagai PNG dan diperiksa secara visual; judul/artis terbaca, sudut transparan mengikuti pill.
- PASS: pemanggilan state kosong, paused, judul panjang dengan karakter markup literal dan Jepang, error, lalu recovery memperbarui label sesuai harapan.
- PASS: handler Esc dan aksi aplikasi `quit` menutup window dan membersihkan timer/executor. Ini pemeriksaan handler/aksi, bukan simulasi tombol fisik.
- PASS: backend Wayland native menampilkan window dan peringatan batas posisi/above. Worker menampilkan error nyata pydbus tidak tersedia tanpa menghentikan UI.

## Delivery Gate antislop

Status di bawah hanya untuk pill tahap 2. Aspek web/mobile yang tidak ada pada aplikasi GTK desktop ditandai tidak berlaku.

- Hard Gate PASS: teks baru tidak memakai em dash (R-02); label GTK memakai elipsis, max-width, dan tooltip teks penuh (R-03). Layout pada pembesaran teks ekstrem belum diuji.
- Hard Gate PASS: tidak ada statistik, testimoni, klaim keamanan, aset visual, FAQ, atau navigasi rekaan (R-17/18/23/24/28/36/38).
- Hard Gate PASS: kontras judul 14.94:1, artis 9.34:1, status 10.45:1, dihitung dengan contrast-check.py (R-25).
- Hard Gate PASS: tidak ada tombol media sebelum tahap 3; aksi penutupan berfungsi; loading, kosong, dan error memiliki pesan teks (R-26/27).
- Hard Gate PASS: Esc dan Ctrl+Q terhubung ke aksi penutupan; belum ada kontrol fokus lain (R-32). Tidak ada CSS/source patcher dalam proyek (R-33).
- Hard Gate PASS: tidak ada toggle tema; pill memakai tema tetap sesuai alasan DESIGN.md, tidak memiliki animasi atau kontrol kustom (R-34/39). Aturan HTML, zoom browser, dan media web tidak berlaku (R-40).
- Hard Gate PASS: aplikasi benar-benar dijalankan pada display; bukti dan batas verifikasi dicatat di atas; arahan desain ditulis sebelum finalisasi (R-35/37).
- Purpose Gate PASS: tidak ada gradien, glow, ikon dekoratif, badge, glass, shadow, ilustrasi, atau animasi. Alasan bentuk, warna, font, dan jarak ada di DESIGN.md (R-01/04/06/07/08/09/10/12/13/14/19/22).
- Liveliness PASS: ENERGY/RHYTHM/MOTION 1/1/1 dinyatakan; judul menjadi fokus, ruang memisahkan status/judul/artis, aksen hanya pada status; bentuk pill mengikuti brief.
- Craftsmanship PASS: komposisi hanya memuat metadata dan state yang dibutuhkan; setiap pilihan utama punya alasan; tidak ada section template, CTA generik, atau klaim integrasi yang belum diuji (C-1/2/3/5, R-05/11/15/16/20/21/29/30/31).
- Craftsmanship PASS untuk skenario yang diperiksa: demo, kosong, paused, error, recovery, X11 dan fallback Wayland; cakupan terbatas pada sesi tersebut (C-4). Multi-monitor, mixed-DPI, pembesaran teks, screen reader, dan Ubuntu versi target masih memerlukan uji pengguna.
