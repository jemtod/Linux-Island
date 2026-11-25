#!/usr/bin/env python3
"""Entry point sementara: inspeksi metadata melalui terminal."""

import argparse
from dataclasses import asdict
import json
import sys

from island_linux.mpris_client import MprisClient, MprisError


def main() -> int:
    parser = argparse.ArgumentParser(description="island-linux: widget media MPRIS")
    parser.add_argument("--inspect", action="store_true", help="Tampilkan satu snapshot MPRIS sebagai JSON")
    args = parser.parse_args()
    if not args.inspect:
        parser.print_help()
        print("UI belum tersedia pada tahap 1. Gunakan --inspect.")
        return 0
    try:
        state = MprisClient().refresh()
    except MprisError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(asdict(state) if state else {"status": "Tidak ada player Playing/Paused"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
