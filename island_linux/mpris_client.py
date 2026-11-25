"""Akses MPRIS tanpa ketergantungan pada widget atau display GTK."""

from collections.abc import Mapping
from dataclasses import dataclass
import logging
import math
from typing import Any

PREFIX = "org.mpris.MediaPlayer2."
OBJECT_PATH = "/org/mpris/MediaPlayer2"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
LOG = logging.getLogger(__name__)


class MprisError(RuntimeError):
    """Session bus atau perintah player tidak tersedia."""


def _seconds(value: Any) -> float:
    try:
        result = float(value) / 1_000_000
        return max(0.0, result) if math.isfinite(result) else 0.0
    except (TypeError, ValueError, OverflowError):
        return 0.0


@dataclass(frozen=True)
class MediaState:
    bus_name: str
    playback_status: str
    title: str = "Tanpa judul"
    artists: tuple[str, ...] = ()
    art_url: str = ""
    track_id: str = ""
    duration: float = 0.0
    position: float = 0.0
    can_control: bool = False
    can_play: bool = False
    can_pause: bool = False
    can_next: bool = False
    can_previous: bool = False

    @property
    def artist(self) -> str:
        return ", ".join(self.artists) or "Artis tidak diketahui"

    @property
    def progress(self) -> float:
        return min(1.0, self.position / self.duration) if self.duration else 0.0


def parse_metadata(bus_name: str, properties: Mapping) -> MediaState:
    """Normalisasi hasil GetAll, termasuk metadata yang tidak lengkap."""
    metadata = properties.get("Metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}
    artists = metadata.get("xesam:artist", [])
    if isinstance(artists, str):
        artists = [artists]
    if not isinstance(artists, (list, tuple)):
        artists = []

    def text(key: str, default: str = "") -> str:
        value = metadata.get(key)
        return value if isinstance(value, str) and value.strip() else default

    return MediaState(
        bus_name=bus_name,
        playback_status=str(properties.get("PlaybackStatus", "Stopped")),
        title=text("xesam:title", "Tanpa judul"),
        artists=tuple(a for a in artists if isinstance(a, str) and a.strip()),
        art_url=text("mpris:artUrl"),
        track_id=text("mpris:trackid"),
        duration=_seconds(metadata.get("mpris:length", 0)),
        position=_seconds(properties.get("Position", 0)),
        can_control=bool(properties.get("CanControl", False)),
        can_play=bool(properties.get("CanPlay", False)),
        can_pause=bool(properties.get("CanPause", False)),
        can_next=bool(properties.get("CanGoNext", False)),
        can_previous=bool(properties.get("CanGoPrevious", False)),
    )


class MprisClient:
    def __init__(self, bus=None):
        # Import ditunda agar pengujian mock tidak perlu PyGObject/pydbus.
        if bus is None:
            try:
                from pydbus import SessionBus
                bus = SessionBus()
            except Exception as exc:
                raise MprisError(f"Tidak dapat membuka session D-Bus: {exc}") from exc
        self.bus = bus
        self.active: MediaState | None = None

    def refresh(self) -> MediaState | None:
        """Playing didahulukan, lalu Paused; pertahankan player saat seri."""
        try:
            names = self.bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus").ListNames()
        except Exception as exc:
            self.active = None
            raise MprisError(f"Tidak dapat memindai session D-Bus: {exc}") from exc
        states = []
        for name in sorted(n for n in names if n.startswith(PREFIX)):
            try:
                proxy = self.bus.get(name, OBJECT_PATH)
                properties = proxy[PROPERTIES_INTERFACE].GetAll(PLAYER_INTERFACE)
                state = parse_metadata(name, properties)
                if state.playback_status in ("Playing", "Paused"):
                    states.append(state)
            except Exception as exc:
                # Player bisa keluar antara ListNames dan GetAll.
                LOG.debug("Melewati player %s: %s", name, exc)
        previous = self.active.bus_name if self.active else None
        self.active = min(
            states,
            key=lambda s: (s.playback_status != "Playing", s.bus_name != previous, s.bus_name),
            default=None,
        )
        return self.active

    def _command(self, method: str) -> bool:
        state = self.active
        if state is None or not state.can_control:
            return False
        allowed = {
            "PlayPause": state.can_pause if state.playback_status == "Playing" else state.can_play,
            "Next": state.can_next,
            "Previous": state.can_previous,
        }
        if not allowed[method]:
            return False
        try:
            proxy = self.bus.get(state.bus_name, OBJECT_PATH)
            getattr(proxy[PLAYER_INTERFACE], method)()
        except Exception as exc:
            self.active = None
            raise MprisError(f"Perintah {method} gagal: {exc}") from exc
        return True

    def play_pause(self) -> bool:
        return self._command("PlayPause")

    def next(self) -> bool:
        return self._command("Next")

    def previous(self) -> bool:
        return self._command("Previous")
