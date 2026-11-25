"""Pembacaan cover terbatas ukurannya; dijalankan di worker."""

from pathlib import Path
from urllib.parse import unquote, urlsplit

MAX_COVER_BYTES = 5 * 1024 * 1024


def load_cover_bytes(url: str) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme in ("http", "https"):
        import requests

        with requests.get(url, stream=True, timeout=(3, 5)) as response:
            response.raise_for_status()
            chunks = []
            size = 0
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > MAX_COVER_BYTES:
                    raise ValueError("Cover melebihi batas 5 MiB")
                chunks.append(chunk)
            return b"".join(chunks)
    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            raise ValueError("Cover file harus berada di komputer lokal")
        path = Path(unquote(parsed.path))
    elif not parsed.scheme and Path(url).is_absolute():
        path = Path(url)
    else:
        raise ValueError("URL cover harus http, https, file, atau path absolut")
    if not path.is_file():
        raise ValueError("Cover lokal harus berupa file biasa")
    with path.open("rb") as source:
        data = source.read(MAX_COVER_BYTES + 1)
    if len(data) > MAX_COVER_BYTES:
        raise ValueError("Cover melebihi batas 5 MiB")
    return data
