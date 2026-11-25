"""Uji GTK + MPRIS terisolasi. Jalankan lewat dbus-run-session, lihat README."""

from pathlib import Path
import os
import sys
import tempfile
import traceback
import json
from concurrent.futures import Future
from urllib.parse import parse_qs, urlsplit

import responses

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GDK_BACKEND", "x11,wayland")

from pydbus import SessionBus
from island_linux.ui.pill import IslandApplication, Gtk
from island_linux.lyrics import BASE_URL, LyricsResult, parse_lrc
from gi.repository import GdkPixbuf, GLib


class TestPlayer:
    dbus = '''<node><interface name="org.mpris.MediaPlayer2.Player">
    <method name="PlayPause"/><method name="Next"/><method name="Previous"/>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Position" type="x" access="read"/>
    <property name="CanControl" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    </interface></node>'''

    PlaybackStatus = "Playing"
    Position = 65_000_000
    CanControl = CanPlay = CanPause = CanGoNext = CanGoPrevious = True

    def __init__(self, cover_uri):
        self.calls = []
        self.Metadata = {
            "xesam:title": GLib.Variant("s", "Uji MPRIS lokal"),
            "xesam:artist": GLib.Variant("as", ["Player uji terisolasi"]),
            "mpris:length": GLib.Variant("x", 210_000_000),
            "mpris:artUrl": GLib.Variant("s", cover_uri),
        }

    def PlayPause(self):
        self.calls.append("PlayPause")
        self.PlaybackStatus = "Paused" if self.PlaybackStatus == "Playing" else "Playing"

    def Next(self):
        self.calls.append("Next")

    def Previous(self):
        self.calls.append("Previous")


def main():
    # Bus harus terisolasi agar uji tidak membaca/mengontrol player pengguna.
    if not os.environ.get("ISLAND_TEST_BUS"):
        print("Gunakan: dbus-run-session -- env ISLAND_TEST_BUS=1 python tests/manual_media_ui.py")
        return 1
    with tempfile.TemporaryDirectory(prefix="island-ui-test-") as directory:
        cover = Path(directory) / "fixture.png"
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 64, 64)
        pixbuf.fill(0xB8D9A0FF)
        pixbuf.savev(str(cover), "png", [], [])
        player = TestPlayer(cover.as_uri())
        bus = SessionBus()
        publication = bus.publish("org.mpris.MediaPlayer2.island_test", ("/org/mpris/MediaPlayer2", player))
        app = IslandApplication()
        # Respons LRCLIB tiruan mencegah akses internet dari uji integrasi.
        http = responses.RequestsMock()

        def lyrics_response(request):
            title = parse_qs(urlsplit(request.url).query)["track_name"][0]
            text = "[00:00]Baris lagu baru" if title == "Lagu Baru" else (
                "[00:05]Baris pertama\n[01:05]こんにちは 世界\n[01:10]Baris berikutnya\n[01:20]")
            return 200, {"Content-Type": "application/json"}, json.dumps({
                "trackName": title, "artistName": "Player uji terisolasi", "duration": 210,
                "instrumental": False, "syncedLyrics": text, "plainLyrics": None,
            })

        http.add_callback(responses.GET, BASE_URL + "/get", callback=lyrics_response)
        http.start()
        errors = []
        stage = 0
        attempts = 0

        def check():
            nonlocal stage, attempts
            attempts += 1
            try:
                assert attempts < 100, "Uji melampaui batas waktu"
                window = app.window
                card = window.card
                if window._state is None or window._busy:
                    return GLib.SOURCE_CONTINUE
                if stage == 0:
                    assert window._state.title == "Uji MPRIS lokal"
                    if card.cover.get_paintable() is None:
                        return GLib.SOURCE_CONTINUE
                    if card._lyrics_result is None:
                        return GLib.SOURCE_CONTINUE
                    assert card.elapsed.get_text() == "1:05"
                    assert card.lyric_label.get_text() == "こんにちは 世界"
                    assert "sekai" in card.romaji_label.get_text()
                    card.play_button.emit("clicked")
                    stage = 1
                elif stage == 1:
                    assert player.calls == ["PlayPause"]
                    assert window._state.playback_status == "Paused"
                    # Klik saat polling berlangsung harus masuk antrean.
                    window._poll()
                    card.next_button.emit("clicked")
                    stage = 2
                elif stage == 2:
                    assert player.calls == ["PlayPause", "Next"]
                    card.previous_button.emit("clicked")
                    stage = 3
                elif stage == 3:
                    assert player.calls == ["PlayPause", "Next", "Previous"]
                    # Fokus keyboard mengikuti urutan previous, play, next.
                    assert card.previous_button.grab_focus()
                    assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
                    assert window.get_focus() == card.play_button
                    assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
                    assert window.get_focus() == card.next_button
                    player.Position = 71_000_000
                    stage = 4
                elif stage == 4:
                    if window._state.position != 71:
                        return GLib.SOURCE_CONTINUE
                    assert card.lyric_label.get_text() == "Baris berikutnya"
                    player.Position = 6_000_000
                    stage = 5
                elif stage == 5:
                    if window._state.position != 6:
                        return GLib.SOURCE_CONTINUE
                    assert card.lyric_label.get_text() == "Baris pertama"
                    player.Metadata = {**player.Metadata, "xesam:title": GLib.Variant("s", "Lagu Baru")}
                    stage = 6
                else:
                    if window._state.title != "Lagu Baru" or card._lyrics_result is None:
                        return GLib.SOURCE_CONTINUE
                    assert card.lyric_label.get_text() == "Baris lagu baru"
                    stale = Future()
                    stale.set_result(LyricsResult("synced", parse_lrc("[00:00]Lagu lama")))
                    card._lyrics_ready(card._lyrics_generation - 1, stale)
                    assert card.lyric_label.get_text() == "Baris lagu baru"
                    print("PASS: D-Bus, cover, progress, kontrol, fokus, lirik, romaji, seek maju/mundur, respons lagu lama")
                    window.close()
                    return GLib.SOURCE_REMOVE
            except Exception:
                traceback.print_exc()
                errors.append(True)
                app.window.close()
                return GLib.SOURCE_REMOVE
            return GLib.SOURCE_CONTINUE

        GLib.timeout_add(200, check)
        app.run([])
        http.stop()
        http.reset()
        publication.unpublish()
        return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
