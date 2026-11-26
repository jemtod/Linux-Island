"""Window pill dan koordinasi worker MPRIS dengan kartu media."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango

from island_linux import config
from island_linux.mpris_client import MediaState, MprisClient
from .card_media import CardMedia

LOG = logging.getLogger(__name__)


class PillWindow(Gtk.ApplicationWindow):
    def __init__(self, application, demo=False, panel_card=False):
        super().__init__(application=application, title="island-linux")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(config.COMPACT_WIDTH, -1)
        self.add_css_class("island")
        self.demo = demo
        self.panel_card = panel_card
        self._closed = False
        self._busy = False
        self._pending_command = None
        self._client = None
        self._state = None
        self._demo_index = 0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mpris")
        self._timer = 0
        self.expanded = False

        self.card = CardMedia(self._command)
        self.stack = Gtk.Stack()
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
        self.set_child(self.stack)
        self.compact_button = Gtk.Button()
        self.compact_button.add_css_class("compact-toggle")
        self.compact_button.set_cursor_from_name("pointer")
        self.compact_button.set_tooltip_text("Buka kartu media · Enter atau Space")
        self.compact_button.update_property([Gtk.AccessibleProperty.LABEL], ["Buka kartu media"])
        compact_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        compact_box.set_halign(Gtk.Align.CENTER)
        self.compact_icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        compact_box.append(self.compact_icon)
        self.compact_label = Gtk.Label(label="Mencari media…")
        self.compact_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.compact_label.set_width_chars(1)
        self.compact_label.set_max_width_chars(18)
        compact_box.append(self.compact_label)
        self.compact_button.set_child(compact_box)
        self.compact_button.connect("clicked", lambda *_: self.set_expanded(True))
        self.stack.add_named(self.compact_button, "compact")
        expanded_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.collapse_button = Gtk.Button(label="Kecilkan")
        self.collapse_button.add_css_class("collapse-toggle")
        self.collapse_button.set_cursor_from_name("pointer")
        self.collapse_button.set_halign(Gtk.Align.END)
        self.collapse_button.set_margin_end(20)
        self.collapse_button.set_margin_top(10)
        self.collapse_button.connect("clicked", lambda *_: self.set_expanded(False))
        expanded_box.append(self.collapse_button)
        expanded_box.append(self.card)
        self.stack.add_named(expanded_box, "expanded")
        self.stack.set_visible_child_name("compact")
        css = Gtk.CssProvider()
        css.load_from_data(f"""
            window.island {{ background: {config.BACKGROUND}; color: {config.FOREGROUND};
                border-radius: {config.RADIUS}px; box-shadow: none; }}
            .island .track-title {{ font-weight: 700; }}
            .island .artist {{ color: {config.SECONDARY}; }}
            .island .status {{ color: {config.ACCENT}; font-size: 9pt; }}
            .island .timing {{ color: {config.SECONDARY}; font-size: 9pt; }}
            .island .lyric-current {{ color: {config.FOREGROUND}; font-size: 11pt; }}
            .island .lyric-secondary {{ color: {config.SECONDARY}; font-size: 9pt; }}
            .island .cover {{ color: {config.SECONDARY}; border-radius: 10px; }}
            .island progressbar trough {{ background: #707070; min-height: 4px; }}
            .island progressbar progress {{ background: {config.ACCENT}; min-height: 4px; }}
            .island button.media-control {{ background: #383838; color: {config.FOREGROUND};
                border: none; border-radius: 10px; box-shadow: none; }}
            .island button.play-toggle {{ background: #484848; }}
            .island button.media-control:hover {{ background: #555555; }}
            .island button.media-control:active {{ background: #626262; }}
            .island button.media-control:disabled {{ opacity: 0.4; }}
            .island button.media-control:focus-visible {{ outline: 2px solid {config.ACCENT}; outline-offset: 2px; }}
            .island button.compact-toggle {{ background: transparent; color: {config.FOREGROUND};
                border: none; box-shadow: none; border-radius: 22px; padding: 10px 16px; min-height: 20px; }}
            .island button.compact-toggle image {{ color: {config.ACCENT}; }}
            .island button.collapse-toggle {{ background: #383838; color: {config.SECONDARY};
                border: none; box-shadow: none; border-radius: 8px; padding: 6px 10px; }}
            .island button.compact-toggle:hover, .island button.collapse-toggle:hover {{ background: #484848; }}
            .island button.compact-toggle:active, .island button.collapse-toggle:active {{ background: #555555; }}
            .island button.compact-toggle:focus-visible, .island button.collapse-toggle:focus-visible {{
                outline: 2px solid {config.ACCENT}; outline-offset: -3px; }}
        """.encode())
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._key_pressed)
        self.add_controller(keys)
        self.connect("map", self._mapped)
        self.connect("close-request", self._close)

        if demo:
            self.show_state(MediaState("demo", "Playing", "Contoh lagu 1", ("Contoh artis",),
                                       duration=210, position=42, can_control=True, can_play=True,
                                       can_pause=True, can_next=True, can_previous=True))
        else:
            self._poll()
        self._timer = GLib.timeout_add_seconds(config.POLL_INTERVAL_SECONDS, self._poll)
        if panel_card:
            self.set_expanded(True)

    def _key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            if self.expanded:
                self.set_expanded(False)
            else:
                self.close()
            return True
        return False

    def set_expanded(self, expanded):
        if not expanded and self.panel_card:
            self.close()
            return
        self.expanded = expanded
        self.stack.set_visible_child_name("expanded" if expanded else "compact")
        self.set_default_size(config.WIDTH if expanded else config.COMPACT_WIDTH, -1)
        (self.collapse_button if expanded else self.compact_button).grab_focus()
        if self.get_mapped():
            GLib.timeout_add(100, self._place)

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
            center = geometry.x + (geometry.width - self.get_width()) // 2
            top = geometry.y + config.OFFSET_Y
            bottom = geometry.y + geometry.height - self.get_height() - config.OFFSET_Y
            x = (center if config.POSITION.endswith("center") else left if config.POSITION.endswith("left") else right) * scale
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
        if self.demo:
            if self._state.playback_status == "Playing":
                self.show_state(replace(self._state, position=min(self._state.duration, self._state.position + config.POLL_INTERVAL_SECONDS)))
            return GLib.SOURCE_CONTINUE
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
            self._state = None
            self.card.show_error()
            self.compact_label.set_text("Media terputus")
            self.compact_button.set_tooltip_text("Koneksi media terputus · Klik untuk detail")
            GLib.timeout_add(100, self._place)
        if self._pending_command is not None:
            command, expected_player = self._pending_command
            self._pending_command = None
            self._start_command(command, expected_player)
        else:
            self.card.set_busy(False)
        return GLib.SOURCE_REMOVE

    def show_state(self, state):
        visibility_changed = (self._state is None) != (state is None)
        self._state = state
        self.card.show_state(state, demo=self.demo)
        self.compact_label.set_text(state.title if state else "Tidak ada media")
        self.compact_icon.set_from_icon_name("media-playback-start-symbolic" if state and state.playback_status == "Playing" else "media-playback-pause-symbolic" if state else "audio-x-generic-symbolic")
        self.compact_button.set_tooltip_text(f"{state.title} · {state.artist}\nKlik untuk membuka kartu media" if state else "Putar musik, lalu klik untuk membuka kartu media")
        if visibility_changed and self.get_mapped():
            GLib.timeout_add(100, self._place)

    def _command(self, command):
        if self._closed or self._state is None:
            return
        if self.demo:
            if command == "play_pause":
                status = "Paused" if self._state.playback_status == "Playing" else "Playing"
                self.show_state(replace(self._state, playback_status=status))
            else:
                self._demo_index = (self._demo_index + (1 if command == "next" else -1)) % 3
                self.show_state(replace(self._state, title=f"Contoh lagu {self._demo_index + 1}", position=0))
            return
        if self._busy:
            # Klik ketika polling berjalan ditunda, bukan dibuang.
            if self._pending_command is None:
                self._pending_command = (command, self._state.bus_name)
                self.card.set_busy(True)
            return
        self._start_command(command, self._state.bus_name)

    def _start_command(self, command, expected_player):
        self._busy = True
        self.card.set_busy(True)
        future = self._executor.submit(self._send_command, command, expected_player)
        future.add_done_callback(lambda result: GLib.idle_add(self._receive, result))

    def _send_command(self, command, expected_player):
        # Jangan kirim klik dari kartu lama ke player baru hasil polling.
        if self._client is None or self._client.active is None or self._client.active.bus_name != expected_player:
            raise RuntimeError("Player berubah sebelum perintah dikirim")
        if not getattr(self._client, command)():
            raise RuntimeError("Player tidak mendukung perintah ini")
        return self._client.refresh()

    def _close(self, window):
        self._closed = True
        if self._timer:
            GLib.source_remove(self._timer)
        self.card.close()
        self._executor.shutdown(wait=False, cancel_futures=True)
        return False


class IslandApplication(Adw.Application):
    def __init__(self, demo=False, panel_card=False):
        super().__init__(application_id="io.github.island_linux", flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.demo = demo
        self.panel_card = panel_card
        self.window = None
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.window.close() if self.window else self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def do_activate(self):
        if self.window is None:
            self.window = PillWindow(self, demo=self.demo, panel_card=self.panel_card)
        self.window.present()


def run(demo=False, panel_card=False):
    Gtk.init()
    if Gdk.Display.get_default() is None:
        print("Display GTK tidak tersedia. Jalankan dari sesi desktop Ubuntu.")
        return 1
    return IslandApplication(demo=demo, panel_card=panel_card).run([])
