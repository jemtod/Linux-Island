"""Buat ZIP extension lokal tanpa menulis ke direktori konfigurasi pengguna."""

import argparse
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    parser = argparse.ArgumentParser(description="Paketkan extension jam + media GNOME")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    python = args.python.absolute()
    if not python.is_file():
        parser.error("Interpreter Python tidak ditemukan")
    source = root / "gnome-extension" / "island-linux@local"
    destination = root / "dist" / "island-linux@local.shell-extension.zip"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for name in ("metadata.json", "extension.js", "stylesheet.css"):
            archive.write(source / name, name)
        archive.writestr("launcher.json", json.dumps({"argv": [str(python), str(root / "island.py")]}))
    print(destination)
    print("Paket ini menyimpan path lokal. Pasang ulang jika folder proyek/virtualenv dipindahkan.")


if __name__ == "__main__":
    main()
