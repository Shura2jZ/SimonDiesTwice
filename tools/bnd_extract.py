"""
M1 - Etape 5 : extraire les fichiers internes d'un BND4 Sekiro + identifier leur format.

Sortie : _work/extracted/<nom>/...   (jamais dans le dossier du jeu)

Usage:
    python tools/bnd_extract.py <fichier.bnd|.dcx> [--recursive]
"""
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil
import bnd4_parse

OUT_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_work", "extracted"
)


def hexdump(data: bytes, length: int = 0x40) -> None:
    for off in range(0, min(len(data), length), 16):
        chunk = data[off:off + 16]
        h = " ".join(f"{b:02X}" for b in chunk)
        a = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"    {off:08X}  {h:<47}  {a}")


def extract(path: str, recursive: bool = False, depth: int = 0) -> None:
    data = soulsutil.load(path)
    label = os.path.splitext(os.path.basename(path))[0]
    outdir = os.path.join(OUT_ROOT, label)
    os.makedirs(outdir, exist_ok=True)

    if data[:4] != b"BND4":
        print(f"  (pas un BND4 : {data[:4]!r})")
        return

    file_count = struct.unpack_from("<I", data, 0x0C)[0]
    entries_off = struct.unpack_from("<Q", data, 0x10)[0]
    entry_size = struct.unpack_from("<Q", data, 0x20)[0]

    print(f"\n### Extraction de {os.path.basename(path)} -> {outdir}")
    for i in range(file_count):
        base = entries_off + i * entry_size
        size = struct.unpack_from("<Q", data, base + 0x08)[0]
        offset = struct.unpack_from("<I", data, base + 0x18)[0]
        name_off = struct.unpack_from("<I", data, base + 0x20)[0]
        name = bnd4_parse.read_utf16(data, name_off)
        fname = os.path.basename(name.replace("\\", "/"))
        blob = data[offset:offset + size]

        dest = os.path.join(outdir, fname)
        with open(dest, "wb") as fh:
            fh.write(blob)

        print(f"\n  [{i}] {fname}  ({size:,} octets) -> {dest}")
        print(f"      magic : {blob[:8]!r}")
        hexdump(blob[:0x40])

        if recursive and blob[:4] == b"BND4" and depth < 3:
            extract(dest, recursive=True, depth=depth + 1)


def main() -> None:
    args = sys.argv[1:]
    rec = "--recursive" in args
    for p in [a for a in args if not a.startswith("--")]:
        extract(p, rec)


if __name__ == "__main__":
    main()
