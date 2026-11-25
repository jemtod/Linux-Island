"""Pill tahap 2: metadata ringkas dan polling tanpa memblokir UI."""

from concurrent.futures import ThreadPoolExecutor
import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango

from island_linux import config
from island_linux.mpris_client import MediaState, MprisClient

LOG = logging.getLogger(__name__)


class PillWindow(Gtk.ApplicationWindow):
    def __init__(self, application, demo=False):
        super().__init__(application=application, title="island-linux")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(config.WIDTH, -1)
        self.add_css_class("island")
        self.demo = demo
        self._closed = False
        self._busy = False
        self._client = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mpris")
        self._timer = 0

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        box.set_margin_start(config.PADDING)
        box.set_margin_end(config.PADDING)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        self.set_child(box)
        self.status_label = self._label("Mencari player…", "status")
        self.title_label = self._label("Membaca media", "track-title")
        self.artist_label = self._label("Menunggu session D-Bus", "artist")
        for label in (self.status_label, self.title_label, self.artist_label):
            box.append(label)

        font = Pango.FontDescription.from_string(config.FONT)
        attributes = Pango.AttrList()
        attributes.insert(Pango.attr_font_desc_new(font))
        box.set_tooltip_text("Esc atau Ctrl+Q untuk menutup island-linux")
        for label in (self.title_label, self.artist_label):
            label.set_attributes(attributes)
        css = Gtk.CssProvider()
        css.load_from_data(f"""
            window.island {{ background: {config.BACKGROUND}; color: {config.FOREGROUND};
                border-radius: {config.RADIUS}px; box-shadow: none; }}
            .island .track-title {{ font-weight: 700; }}
            .island .artist {{ color: {config.SECONDARY}; }}
            .island .status {{ color: {config.ACCENT}; font-size: 9pt; }}
        """.encode())
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._key_pressed)
        self.add_controller(keys)
        self.connect("map", self._mapped)
        self.connect("close-request", self._close)

        if demo:
            self.show_state(MediaState("demo", "Playing", "Contoh judul lagu", ("Contoh artis",)))
        else:
            self._poll()
            self._timer = GLib.timeout_add_seconds(config.POLL_INTERVAL_SECONDS, self._poll)

    @staticmethod
    def _label(text, css_class):
        label = Gtk.Label(label=text, xalign=0)
        label.add_css_class(css_class)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(34)
        return label

    def _key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _mapped(self, widget):
        # Saat map pertama, ukuran widget belum selalu selesai dialokasikan.
        GLib.timeout_add(100, self._place)

    def _place(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        # Wayland native tidak menyediakan posisi absolut maupun keep-above.
        surface = self.get_surface()
        try:
            gi.require_version("GdkX11", "4.0")
            from gi.repository import GdkX11
            if not isinstance(surface, GdkX11.X11Surface):
                LOG.warning("Wayland native: posisi dan always-on-top tidak tersedia; gunakan GDK_BACKEND=x11.")
                return
            from .x11 import place_above
            display = self.get_display()
            monitor = display.get_primary_monitor() or display.get_monitor_at_surface(surface)
            geometry = monitor.get_geometry()
            scale = monitor.get_scale_factor()
            left = geometry.x + config.OFFSET_X
            right = geometry.x + geometry.width - self.get_width() - config.OFFSET_X
            top = geometry.y + config.OFFSET_Y
            bottom = geometry.y + geometry.height - self.get_height() - config.OFFSET_Y
            x = (left if config.POSITION.endswith("left") else right) * scale
            y = (bottom if config.POSITION.startswith("bottom") else top) * scale
            place_above(surface.get_xid(), max(0, x), max(0, y))
        except Exception as exc:
            LOG.warning("Tidak dapat mengatur pill di X11: %s", exc)
        return GLib.SOURCE_REMOVE

    def _read(self):
        if self._client is None:
            self._client = MprisClient()
        return self._client.refresh()

    def _poll(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        if not self._busy:
            self._busy = True
            future = self._executor.submit(self._read)
            future.add_done_callback(lambda result: GLib.idle_add(self._receive, result))
        return GLib.SOURCE_CONTINUE

    def _receive(self, future):
        self._busy = False
        if self._closed:
            return GLib.SOURCE_REMOVE
        try:
            self.show_state(future.result())
        except Exception as exc:
            LOG.warning("Pembacaan media gagal: %s", exc)
            self._set_text("Koneksi media terputus", "Tidak dapat membaca D-Bus", "Periksa session desktop; mencoba lagi otomatis")
        return GLib.SOURCE_REMOVE

    def _set_text(self, status, title, artist):
        for label, text in zip((self.status_label, self.title_label, self.artist_label), (status, title, artist)):
            label.set_text(text)
            label.set_tooltip_text(text)

    def show_state(self, state):
        if state is None:
            self._set_text("Tidak ada media aktif", "Putar musik untuk memulai", "Spotify, browser, atau VLC dengan MPRIS")
        else:
            status = "Sedang diputar" if state.playback_status == "Playing" else "Dijeda"
            if self.demo:
                status = "Demo · " + status
            self._set_text(status, state.title, state.artist)

    def _close(self, window):
        self._closed = True
        if self._timer:
            GLib.source_remove(self._timer)
        self._executor.shutdown(wait=False, cancel_futures=True)
        return False


class IslandApplication(Adw.Application):
    def __init__(self, demo=False):
        super().__init__(application_id="io.github.island_linux", flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.demo = demo
        self.window = None
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.window.close() if self.window else self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def do_activate(self):
        if self.window is None:
            self.window = PillWindow(self, demo=self.demo)
        self.window.present()


def run(demo=False):
    Gtk.init()
    if Gdk.Display.get_default() is None:
        print("Display GTK tidak tersedia. Jalankan dari sesi desktop Ubuntu.")
        return 1
    return IslandApplication(demo=demo).run([])
