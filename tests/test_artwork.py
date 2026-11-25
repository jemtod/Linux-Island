"""Cover lokal/HTTP diuji tanpa GTK, jaringan, atau display."""

from types import SimpleNamespace
from unittest.mock import MagicMock
import sys

import pytest

from island_linux.ui import artwork


def test_local_path_and_encoded_file_uri(tmp_path):
    cover = tmp_path / "album #1.jpg"
    cover.write_bytes(b"cover-lokal")
    assert artwork.load_cover_bytes(str(cover)) == b"cover-lokal"
    assert artwork.load_cover_bytes(cover.as_uri()) == b"cover-lokal"


@pytest.mark.parametrize("url", ["file://remote/album.jpg", "ftp://host/album.jpg", "relative.jpg"])
def test_unsupported_locations(url):
    with pytest.raises(ValueError):
        artwork.load_cover_bytes(url)


def test_local_cover_size_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(artwork, "MAX_COVER_BYTES", 4)
    cover = tmp_path / "large.jpg"
    cover.write_bytes(b"12345")
    with pytest.raises(ValueError, match="batas"):
        artwork.load_cover_bytes(str(cover))


def http_response(monkeypatch, chunks):
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = iter(chunks)
    get = MagicMock(return_value=response)
    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(get=get))
    return response, get


def test_http_stream_and_timeout(monkeypatch):
    response, get = http_response(monkeypatch, [b"abc", b"", b"def"])
    assert artwork.load_cover_bytes("https://example.test/cover") == b"abcdef"
    get.assert_called_once_with("https://example.test/cover", stream=True, timeout=(3, 5))
    response.raise_for_status.assert_called_once()
    response.__exit__.assert_called_once()


def test_http_limit_closes_connection(monkeypatch):
    monkeypatch.setattr(artwork, "MAX_COVER_BYTES", 4)
    response, _ = http_response(monkeypatch, [b"123", b"45"])
    with pytest.raises(ValueError, match="batas"):
        artwork.load_cover_bytes("https://example.test/large")
    response.__exit__.assert_called_once()


def test_http_error_propagates(monkeypatch):
    response, _ = http_response(monkeypatch, [])
    response.raise_for_status.side_effect = RuntimeError("HTTP 404")
    with pytest.raises(RuntimeError, match="404"):
        artwork.load_cover_bytes("https://example.test/missing")
