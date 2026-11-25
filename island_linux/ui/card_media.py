"""Kartu media GTK; menerima snapshot dan callback kontrol dari pill."""

from concurrent.futures import ThreadPoolExecutor
import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango

from island_linux import config
from .artwork import load_cover_bytes

LOG = logging.getLogger(__name__)


def _decode_cover(url):
    loader = GdkPixbuf.PixbufLoader.new()
    loader.connect("size-prepared", lambda decoder, width, height: decoder.set_size(64, 64))
    try:
        loader.write(load_cover_bytes(url))
        loader.close()
        return loader.get_pixbuf()
    except Exception:
        try:
            loader.close()
        except GLib.Error:
            pass
        raise


def _time(seconds):
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"


class CardMedia(Gtk.Box):
    def __init__(self, on_command):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._on_command = on_command
        self._state = None
        self._busy = False
        self._closed = False
        self._cover_url = None
        self._cover_future = None
        self._cover_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cover")
        self.set_margin_start(config.PADDING)
        self.set_margin_end(config.PADDING)
        self.set_margin_top(16)
        self.set_margin_bottom(14)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.append(header)
        self.cover = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        self.cover.set_pixel_size(32)
        self.cover.set_size_request(64, 64)
        self.cover.add_css_class("cover")
        self.cover.set_tooltip_text("Tidak ada cover")
        self.cover.update_property([Gtk.AccessibleProperty.LABEL], ["Cover album"])
        header.append(self.cover)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        text.set_hexpand(True)
        text.set_valign(Gtk.Align.CENTER)
        header.append(text)
        self.status_label = self._label("Mencari player…", "status")
        self.title_label = self._label("Membaca media", "track-title")
        self.artist_label = self._label("Menunggu session D-Bus", "artist")
        font = Pango.FontDescription.from_string(config.FONT)
        attributes = Pango.AttrList()
        attributes.insert(Pango.attr_font_desc_new(font))
        for label in (self.title_label, self.artist_label):
            label.set_attributes(attributes)
        for label in (self.status_label, self.title_label, self.artist_label):
            text.append(label)

        self.playback = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append(self.playback)
        self.progress = Gtk.ProgressBar()
        self.progress.update_property([Gtk.AccessibleProperty.LABEL], ["Posisi playback"])
        self.progress.set_tooltip_text("Posisi playback; seek belum tersedia")
        self.playback.append(self.progress)
        timing = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.elapsed = Gtk.Label(label="0:00", xalign=0)
        self.elapsed.set_hexpand(True)
        self.duration = Gtk.Label(label="?:??", xalign=1)
        for label in (self.elapsed, self.duration):
            label.add_css_class("timing")
            timing.append(label)
        self.playback.append(timing)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls.set_halign(Gtk.Align.CENTER)
        self.playback.append(controls)
        self.previous_button = self._button("media-skip-backward-symbolic", "Lagu sebelumnya", "previous")
        self.play_button = self._button("media-playback-pause-symbolic", "Jeda", "play_pause")
        self.next_button = self._button("media-skip-forward-symbolic", "Lagu berikutnya", "next")
        for button in (self.previous_button, self.play_button, self.next_button):
            controls.append(button)
        self.play_button.add_css_class("play-toggle")
        self.playback.set_visible(False)

    @staticmethod
    def _label(text, css_class):
        label = Gtk.Label(label=text, xalign=0)
        label.add_css_class(css_class)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        # width_chars=1 membolehkan teks panjang menyusut sesuai lebar kartu.
        label.set_width_chars(1)
        label.set_max_width_chars(26)
        return label

    def _button(self, icon, label, command):
        button = Gtk.Button.new_from_icon_name(icon)
        button.set_size_request(40, 40)
        button.set_cursor_from_name("pointer")
        button.add_css_class("media-control")
        button.set_tooltip_text(label)
        button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        button.connect("clicked", lambda *_: self._on_command(command))
        return button

    def set_text(self, status, title, artist):
        for label, value in zip((self.status_label, self.title_label, self.artist_label), (status, title, artist)):
            label.set_text(value)
            label.set_tooltip_text(value)

    def show_state(self, state, demo=False):
        self._state = state
        self.playback.set_visible(state is not None)
        if state is None:
            self.set_text("Tidak ada media aktif", "Putar musik untuk memulai", "Spotify, browser, atau VLC dengan MPRIS")
            self._set_cover("")
        else:
            status = "Sedang diputar" if state.playback_status == "Playing" else "Dijeda"
            self.set_text(("Demo · " if demo else "") + status, state.title, state.artist)
            playing = state.playback_status == "Playing"
            name = "Jeda" if playing else "Putar"
            self.play_button.set_icon_name("media-playback-pause-symbolic" if playing else "media-playback-start-symbolic")
            self.play_button.set_tooltip_text(name)
            self.play_button.update_property([Gtk.AccessibleProperty.LABEL], [name])
            self.progress.set_fraction(state.progress)
            self.elapsed.set_text(_time(state.position))
            self.duration.set_text(_time(state.duration) if state.duration else "?:??")
            self._set_cover(state.art_url)
        self.set_busy(self._busy)

    def set_busy(self, busy):
        self._busy = busy
        s = self._state
        control = s is not None and s.can_control and not busy
        self.previous_button.set_sensitive(bool(control and s.can_previous))
        self.next_button.set_sensitive(bool(control and s.can_next))
        self.play_button.set_sensitive(bool(control and (s.can_pause if s.playback_status == "Playing" else s.can_play)))

    def show_error(self, title="Tidak dapat membaca D-Bus"):
        self.show_state(None)
        self.set_text("Koneksi media terputus", title, "Mencoba lagi otomatis; periksa player/session desktop")

    def _set_cover(self, url):
        if url == self._cover_url:
            return
        self._cover_url = url
        if self._cover_future:
            self._cover_future.cancel()
        self.cover.set_from_icon_name("audio-x-generic-symbolic")
        self.cover.set_pixel_size(32)
        self.cover.set_tooltip_text("Memuat cover…" if url else "Tidak ada cover")
        if url:
            self._cover_future = self._cover_executor.submit(_decode_cover, url)
            self._cover_future.add_done_callback(lambda future: GLib.idle_add(self._cover_ready, url, future))

    def _cover_ready(self, url, future):
        # Respons lagu lama tidak boleh menimpa cover lagu baru.
        if self._closed or url != self._cover_url:
            return GLib.SOURCE_REMOVE
        try:
            pixbuf = future.result()
            self.cover.set_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
            self.cover.set_pixel_size(64)
            self.cover.set_tooltip_text("Cover album")
        except Exception as exc:
            LOG.debug("Cover tidak tersedia: %s", exc)
            self.cover.set_tooltip_text("Cover gagal dimuat; kontrol media tetap tersedia")
        return GLib.SOURCE_REMOVE

    def close(self):
        self._closed = True
        self._cover_executor.shutdown(wait=False, cancel_futures=True)
