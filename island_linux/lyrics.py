"""LRCLIB, parser LRC, dan romanisasi; tidak memerlukan GTK atau display."""

from bisect import bisect_right
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import re
import time
import unicodedata

BASE_URL = "https://lrclib.net/api"
TIMESTAMP = re.compile(r"\[(\d+):([0-5]\d(?:\.\d{1,3})?)\]")
JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]")


class LyricsError(RuntimeError):
    def __init__(self, message, retry_after=60.0):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass(frozen=True)
class LyricLine:
    time: float
    text: str
    romaji: str = ""


@dataclass(frozen=True)
class LyricsResult:
    status: str
    lines: tuple[LyricLine, ...] = ()
    plain_lyrics: str = ""


def romanize_japanese(text: str, converter=None) -> str:
    """Kembalikan romaji Hepburn hanya bila teks memuat kana/kanji."""
    if not JAPANESE.search(text):
        return ""
    if converter is None:
        from pykakasi import kakasi
        converter = kakasi()
    return re.sub(r"\s+", " ", " ".join(part["hepburn"] for part in converter.convert(text))).strip()


def parse_lrc(text: str, romanizer=romanize_japanese) -> tuple[LyricLine, ...]:
    """Dukung timestamp berulang, pecahan detik, dan jeda berupa baris kosong."""
    if not isinstance(text, str):
        return ()
    offset_match = re.search(r"\[offset:([+-]?\d+)\]", text, re.IGNORECASE)
    # Offset positif pada LRC memajukan tampilan lirik.
    offset = int(offset_match.group(1)) / 1000 if offset_match else 0.0
    lines = []
    converter = None
    for raw in text.splitlines():
        matches = list(TIMESTAMP.finditer(raw))
        if not matches:
            continue
        words = raw[matches[-1].end():].strip()
        romaji = ""
        if JAPANESE.search(words):
            if romanizer is romanize_japanese:
                if converter is None:
                    from pykakasi import kakasi
                    converter = kakasi()
                romaji = romanizer(words, converter)
            else:
                romaji = romanizer(words)
        for stamp in matches:
            seconds = int(stamp.group(1)) * 60 + float(stamp.group(2)) - offset
            lines.append(LyricLine(max(0.0, seconds), words, romaji))
    return tuple(sorted(lines, key=lambda line: line.time))


def line_index_at(lines: tuple[LyricLine, ...], position: float) -> int:
    if not math.isfinite(position) or position < 0:
        return -1
    return bisect_right(lines, position, key=lambda line: line.time) - 1


def parse_record(record: dict, romanizer=romanize_japanese) -> LyricsResult:
    if not isinstance(record, dict):
        raise LyricsError("Format respons LRCLIB tidak valid")
    if record.get("instrumental") is True:
        return LyricsResult("instrumental")
    lines = parse_lrc(record.get("syncedLyrics"), romanizer)
    if lines:
        return LyricsResult("synced", lines)
    plain = record.get("plainLyrics")
    if isinstance(plain, str) and plain.strip():
        return LyricsResult("plain", plain_lyrics=plain)
    return LyricsResult("not_found")


def _normalized(text):
    return re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", str(text)).casefold()).strip()


def _duration(value):
    try:
        number = float(value)
        return number if math.isfinite(number) and number > 0 else 0.0
    except (ValueError, TypeError):
        return 0.0


def _retry_seconds(value):
    try:
        delay = float(value)
        return max(1.0, delay) if math.isfinite(delay) else 60.0
    except (TypeError, ValueError):
        try:
            return max(1.0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return 60.0


class LyricsClient:
    """Client berurutan dengan cache kecil; gunakan dari satu worker."""

    def __init__(self, session=None, user_agent="island-linux/0.1.0 (local development build)", romanizer=romanize_japanese):
        if session is None:
            import requests
            session = requests.Session()
        self.session = session
        self.user_agent = user_agent
        self.romanizer = romanizer
        self._cache = OrderedDict()
        self._next_request = 0.0

    def _request(self, endpoint, params):
        wait = self._next_request - time.monotonic()
        if wait > 0:
            # Throttle singkat boleh menunggu di worker; cooldown panjang kembali ke UI.
            if wait > 0.5:
                raise LyricsError("LRCLIB meminta jeda permintaan", retry_after=wait)
            time.sleep(wait)
        try:
            response = self.session.get(
                BASE_URL + endpoint, params=params,
                headers={"User-Agent": self.user_agent}, timeout=(3, 8),
            )
        except Exception as exc:
            raise LyricsError("Tidak dapat terhubung ke LRCLIB") from exc
        self._next_request = time.monotonic() + 0.25
        try:
            if response.status_code in (429, 503):
                # Jitter kecil menghindari percobaan ulang bersamaan antar client.
                import random
                delay = _retry_seconds(response.headers.get("Retry-After")) * random.uniform(1.05, 1.2)
                self._next_request = time.monotonic() + delay
                raise LyricsError("LRCLIB sedang membatasi permintaan", retry_after=delay)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except LyricsError:
            raise
        except Exception as exc:
            raise LyricsError("Respons LRCLIB tidak dapat dibaca") from exc
        finally:
            response.close()

    def fetch(self, artist: str, title: str, duration: float = 0.0) -> LyricsResult:
        if not artist.strip() or not title.strip() or title == "Tanpa judul":
            return LyricsResult("missing_metadata")
        duration = _duration(duration)
        key = (_normalized(artist), _normalized(title), round(duration, 1))
        cached = self._cache.get(key)
        if cached and cached[0] > time.monotonic():
            self._cache.move_to_end(key)
            return cached[1]
        params = {"artist_name": artist, "track_name": title}
        if 1 <= duration <= 3600:
            params["duration"] = duration
        record = self._request("/get", params)
        if isinstance(record, dict) and duration and abs(_duration(record.get("duration")) - duration) > 3:
            record = None
        result = parse_record(record, self.romanizer) if record is not None else LyricsResult("not_found")
        if result.status not in ("synced", "instrumental"):
            records = self._request("/search", {"artist_name": artist, "track_name": title})
            if records is not None and not isinstance(records, list):
                raise LyricsError("Format pencarian LRCLIB tidak valid")
            candidates = []
            for item in records or []:
                if not isinstance(item, dict) or _normalized(item.get("trackName", "")) != key[1]:
                    continue
                artists = [_normalized(a) for a in re.split(r"[,;]", str(item.get("artistName", "")))]
                if key[0] not in artists and _normalized(item.get("artistName", "")) != key[0]:
                    continue
                candidate_duration = _duration(item.get("duration"))
                distance = abs(candidate_duration - duration) if duration else 0.0
                if duration and (not candidate_duration or distance > 3):
                    continue
                # Seleksi dulu; romanisasi cukup untuk record yang akhirnya dipilih.
                synced = bool(parse_lrc(item.get("syncedLyrics"), romanizer=lambda _: ""))
                candidates.append((not synced, distance, item))
            if candidates:
                chosen = min(candidates, key=lambda candidate: candidate[:2])[2]
                alternative = parse_record(chosen, self.romanizer)
                if alternative.status in ("synced", "instrumental") or result.status == "not_found":
                    result = alternative
        ttl = 1800 if result.status in ("synced", "instrumental", "plain") else 300
        self._cache[key] = (time.monotonic() + ttl, result)
        self._cache.move_to_end(key)
        while len(self._cache) > 64:
            self._cache.popitem(last=False)
        return result

    def close(self):
        self.session.close()
