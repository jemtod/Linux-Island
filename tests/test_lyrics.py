"""Lirik buatan sendiri dalam bentuk JSON LRCLIB; tanpa jaringan/display."""

from unittest.mock import Mock

import pytest
import requests
import responses
from responses import matchers

from island_linux.lyrics import (
    BASE_URL, LyricLine, LyricsClient, LyricsError, line_index_at,
    parse_lrc, parse_record, romanize_japanese,
)


def record(**extra):
    return {
        "id": 123, "name": "Lagu Uji", "trackName": "Lagu Uji",
        "artistName": "Artis Uji", "albumName": "Album Uji", "duration": 120,
        "instrumental": False, "plainLyrics": "Baris pertama\nBaris kedua",
        "syncedLyrics": "[00:05.00]Baris pertama\n[00:10.25]Baris kedua\n[00:15.00]",
        **extra,
    }


def test_lrc_timestamp_formats_sorting_and_repeated_lines():
    lines = parse_lrc("[ar:Artis]\n[00:03.125]Tiga\n[00:01][00:02.50]Ulang\nrusak\n[00:60]Bukan timestamp")
    assert [(line.time, line.text) for line in lines] == [(1, "Ulang"), (2.5, "Ulang"), (3.125, "Tiga")]


def test_offset_and_empty_timed_line():
    lines = parse_lrc("[offset:+500]\n[00:00.20]Awal\n[00:02.00]\n")
    assert lines == (LyricLine(0, "Awal"), LyricLine(1.5, ""))


@pytest.mark.parametrize("position,index", [(0, -1), (4.99, -1), (5, 0), (10.249, 0), (10.25, 1), (15, 2), (100, 2), (-1, -1), (float("nan"), -1)])
def test_line_selection_boundaries_seek_and_silence(position, index):
    lines = parse_record(record()).lines
    assert line_index_at(lines, position) == index


def test_duplicate_timestamps_and_empty_lyrics():
    lines = parse_lrc("[00:01]Pertama\n[00:01]Kedua")
    assert line_index_at(lines, 1) == 1
    assert line_index_at((), 1) == -1
    assert parse_lrc(None) == ()


@pytest.mark.parametrize("payload,status", [
    ({"instrumental": True}, "instrumental"),
    ({"syncedLyrics": None, "plainLyrics": "Tanpa waktu"}, "plain"),
    ({"syncedLyrics": "rusak", "plainLyrics": None}, "not_found"),
    ({"syncedLyrics": "[00:01]Uji"}, "synced"),
])
def test_record_statuses(payload, status):
    assert parse_record(payload).status == status


def test_romaji_preserves_original_and_timing():
    romanizer = Mock(return_value="konnichiwa")
    lines = parse_lrc("[00:01]こんにちは\n[00:02]Teks Latin", romanizer)
    assert lines[0] == LyricLine(1, "こんにちは", "konnichiwa")
    assert lines[1] == LyricLine(2, "Teks Latin", "")
    romanizer.assert_called_once_with("こんにちは")


def test_pykakasi_api_and_non_japanese_fast_path():
    converter = Mock()
    converter.convert.return_value = [{"hepburn": "sekai"}]
    assert romanize_japanese("世界", converter) == "sekai"
    assert romanize_japanese("Hello", converter) == ""
    converter.convert.assert_called_once_with("世界")


def test_real_pykakasi_conversion():
    pytest.importorskip("pykakasi")
    result = romanize_japanese("こんにちは 世界")
    assert "sekai" in result
    assert not any("\u3040" <= char <= "\u9fff" for char in result)


@responses.activate
def test_exact_get_parameters_json_and_cache():
    responses.get(BASE_URL + "/get", json=record(), match=[matchers.query_param_matcher({
        "artist_name": "Artis Uji", "track_name": "Lagu Uji", "duration": "120.0",
    })])
    client = LyricsClient()
    result = client.fetch("Artis Uji", "Lagu Uji", 120)
    assert result.status == "synced"
    assert result.lines[1].time == 10.25
    assert client.fetch("Artis Uji", "Lagu Uji", 120) is result
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["User-Agent"].startswith("island-linux/")
    client.close()


@responses.activate
def test_fallback_search_rejects_wrong_artist_version_and_duration():
    responses.get(BASE_URL + "/get", status=404, json={"name": "TrackNotFound", "statusCode": 404})
    responses.get(BASE_URL + "/search", json=[
        record(trackName="Lagu Uji Live"), record(artistName="Artis Lain"),
        record(duration=200), record(syncedLyrics=None),
        record(duration=121, syncedLyrics="[00:01]Pilihan tepat"),
    ], match=[matchers.query_param_matcher({"artist_name": "Artis Uji", "track_name": "Lagu Uji"})])
    result = LyricsClient().fetch("Artis Uji", "Lagu Uji", 120)
    assert result.lines[0].text == "Pilihan tepat"


@responses.activate
def test_unsynced_get_tries_search_before_returning_plain():
    responses.get(BASE_URL + "/get", json=record(syncedLyrics=None))
    responses.get(BASE_URL + "/search", json=[])
    result = LyricsClient().fetch("Artis Uji", "Lagu Uji", 120)
    assert result.status == "plain"
    assert result.plain_lyrics == "Baris pertama\nBaris kedua"


@responses.activate
def test_missing_duration_omits_query_parameter():
    responses.get(BASE_URL + "/get", json=record(), match=[matchers.query_param_matcher({
        "artist_name": "Artis Uji", "track_name": "Lagu Uji",
    })])
    assert LyricsClient().fetch("Artis Uji", "Lagu Uji").status == "synced"


@responses.activate
def test_no_result_is_cached():
    responses.get(BASE_URL + "/get", status=404)
    responses.get(BASE_URL + "/search", json=[])
    client = LyricsClient()
    assert client.fetch("Artis Uji", "Lagu Uji", 120).status == "not_found"
    client.fetch("Artis Uji", "Lagu Uji", 120)
    assert len(responses.calls) == 2


@responses.activate
def test_instrumental_skips_search():
    responses.get(BASE_URL + "/get", json=record(instrumental=True, syncedLyrics=None))
    assert LyricsClient().fetch("Artis Uji", "Lagu Uji", 120).status == "instrumental"
    assert len(responses.calls) == 1


@pytest.mark.parametrize("artist,title", [("", "Judul"), ("Artis", ""), ("Artis", "Tanpa judul")])
def test_missing_metadata_does_not_request(artist, title):
    session = Mock()
    assert LyricsClient(session).fetch(artist, title).status == "missing_metadata"
    session.get.assert_not_called()


@responses.activate
@pytest.mark.parametrize("status", [429, 503])
def test_retry_after_blocks_new_requests_including_different_track(status):
    responses.get(BASE_URL + "/get", status=status, headers={"Retry-After": "120"}, body="busy")
    client = LyricsClient()
    with pytest.raises(LyricsError) as error:
        client.fetch("Artis Uji", "Lagu Uji", 120)
    assert error.value.retry_after >= 120
    with pytest.raises(LyricsError):
        client.fetch("Artis Uji", "Lagu Lain", 120)
    assert len(responses.calls) == 1


@responses.activate
@pytest.mark.parametrize("body", ["not JSON", "[]", "null"])
def test_invalid_json_and_record_shapes(body):
    responses.get(BASE_URL + "/get", body=body)
    responses.get(BASE_URL + "/search", json={"invalid": "shape"})
    with pytest.raises(LyricsError):
        LyricsClient().fetch("Artis Uji", "Lagu Uji", 120)


@responses.activate
def test_network_timeout_is_recoverable():
    responses.get(BASE_URL + "/get", body=requests.Timeout("offline"))
    responses.get(BASE_URL + "/get", json=record())
    client = LyricsClient()
    with pytest.raises(LyricsError):
        client.fetch("Artis Uji", "Lagu Uji", 120)
    assert client.fetch("Artis Uji", "Lagu Uji", 120).status == "synced"


@responses.activate
def test_wrong_get_duration_falls_back_to_search():
    responses.get(BASE_URL + "/get", json=record(duration=300))
    responses.get(BASE_URL + "/search", json=[record()])
    assert LyricsClient().fetch("Artis Uji", "Lagu Uji", 120).status == "synced"
    assert len(responses.calls) == 2
