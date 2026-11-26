#!/usr/bin/env python3
"""Jalankan pill atau inspeksi metadata melalui terminal."""

import argparse
from dataclasses import asdict
import json
import os
import sys

from island_linux.mpris_client import MprisClient, MprisError


def main() -> int:
    parser = argparse.ArgumentParser(description="island-linux: widget media MPRIS")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--inspect", action="store_true", help="Tampilkan satu snapshot MPRIS sebagai JSON")
    modes.add_argument("--demo", action="store_true", help="Tampilkan pill dengan data contoh berlabel demo")
    modes.add_argument("--selftest", action="store_true", help="Uji logic inti offline tanpa GTK, D-Bus, atau display")
    args = parser.parse_args()
    if args.selftest:
        from island_linux.selftest import run
        return run()
    if not args.inspect:
        # XWayland memberi akses ke hint posisi/above yang tidak ada di GTK4 Wayland.
        # Pilihan backend eksplisit dari pengguna tetap dihormati.
        os.environ.setdefault("GDK_BACKEND", "x11,wayland")
        try:
            from island_linux.ui.pill import run
            return run(demo=args.demo)
        except (ImportError, ValueError) as exc:
            print(f"GTK4/libadwaita tidak tersedia: {exc}. Lihat paket apt di README.", file=sys.stderr)
            return 1
    try:
        state = MprisClient().refresh()
    except MprisError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(asdict(state) if state else {"status": "Tidak ada player Playing/Paused"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
