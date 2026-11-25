# Validasi tahap 2

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
