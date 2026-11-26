"""Pemeriksaan offline yang dapat dijalankan hanya dengan Python standar."""

from unittest.mock import Mock

from .lyrics import LyricsClient, line_index_at, romanize_japanese
from .mpris_client import MprisClient, PLAYER_INTERFACE, PROPERTIES_INTERFACE


def _check(condition, message):
    # Tidak memakai assert agar tetap berjalan ketika Python memakai -O.
    if not condition:
        raise RuntimeError(message)


def check_mpris():
    paused = "org.mpris.MediaPlayer2.paused"
    playing = "org.mpris.MediaPlayer2.playing"
    daemon = Mock()
    daemon.ListNames.return_value = [paused, playing]
    proxies = {}
    for name, status in ((paused, "Paused"), (playing, "Playing")):
        properties = Mock()
        properties.GetAll.return_value = {
            "PlaybackStatus": status,
            "Metadata": {"xesam:title": "Lagu selftest", "xesam:artist": ["Artis selftest"],
                         "mpris:length": 120_000_000},
            "Position": 30_000_000, "CanControl": True, "CanPause": True,
            "CanPlay": True, "CanGoNext": True, "CanGoPrevious": True,
        }
        proxies[name] = {PROPERTIES_INTERFACE: properties, PLAYER_INTERFACE: Mock()}
    bus = Mock()
    bus.get.side_effect = lambda name, path: daemon if name == "org.freedesktop.DBus" else proxies[name]
    client = MprisClient(bus)
    state = client.refresh()
    _check(state is not None and state.bus_name == playing, "Prioritas Playing gagal")
    _check(state.artist == "Artis selftest" and state.duration == 120 and state.progress == 0.25, "Metadata/satuan waktu gagal")
    for command, method in (("play_pause", "PlayPause"), ("next", "Next"), ("previous", "Previous")):
        _check(getattr(client, command)(), f"Kontrol {method} ditolak")
        getattr(proxies[playing][PLAYER_INTERFACE], method).assert_called_once_with()
    daemon.ListNames.return_value = [paused]
    _check(client.refresh().bus_name == paused, "Fallback Paused gagal")
    daemon.ListNames.return_value = []
    _check(client.refresh() is None, "Status kosong gagal")


def check_lyrics():
    # Mock session menyimulasikan 404 /get dan JSON asli berbentuk array /search.
    missing = Mock(status_code=404)
    search = Mock(status_code=200)
    search.json.return_value = [{
        "id": 1, "trackName": "Lagu selftest", "artistName": "Artis selftest",
        "albumName": "", "duration": 120, "instrumental": False,
        "plainLyrics": "Baris pertama\nBaris kedua",
        "syncedLyrics": "[00:05.00]Baris pertama\n[00:10.50]Baris kedua\n[00:15.00]",
    }]
    session = Mock()
    session.get.side_effect = [missing, search]
    client = LyricsClient(session=session)
    try:
        result = client.fetch("Artis selftest", "Lagu selftest", 120)
        _check(result.status == "synced", "Fallback LRCLIB gagal")
        for position, expected in ((0, -1), (5, 0), (10.5, 1), (15, 2), (6, 0)):
            _check(line_index_at(result.lines, position) == expected, "Pemilihan baris/seek gagal")
        _check(result.lines[2].text == "", "Jeda lirik gagal")
        client.fetch("Artis selftest", "Lagu selftest", 120)
        _check(session.get.call_count == 2, "Cache lirik gagal")
        converter = Mock()
        converter.convert.return_value = [{"hepburn": "sekai"}]
        _check(romanize_japanese("世界", converter) == "sekai", "Alur romanisasi gagal")
    finally:
        client.close()


def run():
    failures = 0
    for name, check in (("MPRIS (metadata, seleksi, kontrol mock)", check_mpris),
                        ("Lirik (LRCLIB mock, waktu, cache, romanisasi mock)", check_lyrics)):
        try:
            check()
            print(f"PASS: {name}")
        except Exception as exc:
            failures += 1
            print(f"FAIL: {name}: {exc}")
    print("Selftest selesai. Player, jaringan, GTK, dan pykakasi nyata tidak diuji.")
    return int(bool(failures))
