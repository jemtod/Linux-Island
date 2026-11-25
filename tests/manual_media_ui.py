"""Uji GTK + MPRIS terisolasi. Jalankan lewat dbus-run-session, lihat README."""

from pathlib import Path
import os
import sys
import tempfile
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GDK_BACKEND", "x11,wayland")

from pydbus import SessionBus
from island_linux.ui.pill import IslandApplication, Gtk
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
                    assert card.elapsed.get_text() == "1:05"
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
                else:
                    assert player.calls == ["PlayPause", "Next", "Previous"]
                    # Fokus keyboard mengikuti urutan previous, play, next.
                    assert card.previous_button.grab_focus()
                    assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
                    assert card.play_button.has_focus()
                    assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
                    assert card.next_button.has_focus()
                    print("PASS: D-Bus, metadata, cover, progress, PlayPause, antrean Next, Previous, fokus keyboard")
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
        publication.unpublish()
        return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
