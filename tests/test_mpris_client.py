"""Pengujian MPRIS tanpa session bus maupun display."""

from unittest.mock import Mock
import pytest
from island_linux.mpris_client import (
    MprisClient, MprisError, parse_metadata, PREFIX,
    PROPERTIES_INTERFACE, PLAYER_INTERFACE,
)


def properties(status="Playing", **extra):
    return {
        "PlaybackStatus": status,
        "Metadata": {"xesam:title": "Judul", "xesam:artist": ["Satu", "Dua"],
                     "mpris:artUrl": "file:///tmp/cover.jpg", "mpris:length": 200_000_000},
        "Position": 50_000_000,
        "CanControl": True, "CanPlay": True, "CanPause": True,
        "CanGoNext": True, "CanGoPrevious": True, **extra,
    }


def make_bus(players):
    bus = Mock()
    daemon = Mock()
    daemon.ListNames.return_value = ["org.example.Other", *players]
    proxies = {}
    for name, props in players.items():
        interface = Mock()
        interface.GetAll.return_value = props
        proxies[name] = {PROPERTIES_INTERFACE: interface, PLAYER_INTERFACE: Mock()}

    def get(name, path):
        if name == "org.freedesktop.DBus":
            return daemon
        if isinstance(players[name], Exception):
            raise players[name]
        return proxies[name]
    bus.get.side_effect = get
    return bus, proxies


def test_metadata_units_and_artists():
    state = parse_metadata(PREFIX + "spotify", properties())
    assert (state.title, state.artist) == ("Judul", "Satu, Dua")
    assert (state.duration, state.position, state.progress) == (200, 50, .25)
    assert state.art_url == "file:///tmp/cover.jpg"


@pytest.mark.parametrize("metadata", [{}, None, "rusak", {"xesam:artist": None}])
def test_missing_metadata(metadata):
    state = parse_metadata("player", {"Metadata": metadata})
    assert state.title == "Tanpa judul"
    assert state.artist == "Artis tidak diketahui"
    assert state.progress == 0


@pytest.mark.parametrize("value", [None, "rusak", -1, float("nan"), float("inf")])
def test_invalid_times(value):
    state = parse_metadata("player", {"Position": value, "Metadata": {"mpris:length": value}})
    assert state.position == state.duration == 0


def test_single_artist_and_progress_clamped():
    state = parse_metadata("p", {"Metadata": {"xesam:artist": "Solo", "mpris:length": 1}, "Position": 2})
    assert state.artists == ("Solo",)
    assert state.progress == 1


def test_playing_before_paused_and_stable_ties():
    a, b = PREFIX + "a", PREFIX + "b"
    bus, proxies = make_bus({a: properties("Paused"), b: properties()})
    client = MprisClient(bus)
    assert client.refresh().bus_name == b
    proxies[a][PROPERTIES_INTERFACE].GetAll.return_value = properties()
    assert client.refresh().bus_name == b
    proxies[b][PROPERTIES_INTERFACE].GetAll.return_value = properties("Stopped")
    assert client.refresh().bus_name == a


def test_paused_fallback_and_disappearing_player():
    name = PREFIX + "paused"
    bus, _ = make_bus({PREFIX + "gone": RuntimeError("disparu"), name: properties("Paused")})
    assert MprisClient(bus).refresh().bus_name == name


@pytest.mark.parametrize("players", [{}, {PREFIX + "stopped": properties("Stopped")}])
def test_empty_or_stopped(players):
    bus, _ = make_bus(players)
    client = MprisClient(bus)
    assert client.refresh() is None
    assert client.play_pause() is False


def test_bus_failure_clears_state():
    bus, _ = make_bus({PREFIX + "a": properties()})
    client = MprisClient(bus)
    client.refresh()
    bus.get.side_effect = RuntimeError("bus mati")
    with pytest.raises(MprisError, match="memindai"):
        client.refresh()
    assert client.active is None


@pytest.mark.parametrize("command,method", [("play_pause", "PlayPause"), ("next", "Next"), ("previous", "Previous")])
def test_command_targets_selected_player(command, method):
    a, b = PREFIX + "a", PREFIX + "b"
    bus, proxies = make_bus({a: properties("Paused"), b: properties()})
    client = MprisClient(bus)
    client.refresh()
    assert getattr(client, command)() is True
    getattr(proxies[b][PLAYER_INTERFACE], method).assert_called_once_with()
    getattr(proxies[a][PLAYER_INTERFACE], method).assert_not_called()


def test_unsupported_control_and_command_failure():
    name = PREFIX + "a"
    bus, proxies = make_bus({name: properties(CanGoNext=False)})
    client = MprisClient(bus)
    client.refresh()
    assert client.next() is False
    proxies[name][PLAYER_INTERFACE].PlayPause.side_effect = RuntimeError("keluar")
    with pytest.raises(MprisError, match="PlayPause"):
        client.play_pause()
    assert client.active is None
