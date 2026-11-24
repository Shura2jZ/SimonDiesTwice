"""
M1 - Etape 3 : sonder la structure reelle d'un BND4 Sekiro.

Methode : on N'INVENTE PAS la structure. On observe :
  1. un hexdump de l'en-tete
  2. toutes les chaines ASCII (noms de fichiers internes, extensions)
  3. une recherche de correspondances nom <-> taille/offset

Usage:
    python tools/bnd_probe.py <fichier.dcx|fichier.bnd>
"""
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil


def hexdump(data: bytes, start: int = 0, length: int = 0x200) -> None:
    for off in range(start, min(len(data), start + length), 16):
        chunk = data[off:off + 16]
        h = " ".join(f"{b:02X}" for b in chunk)
        a = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{off:08X}  {h:<47}  {a}")


def ascii_runs(data: bytes, minlen: int = 4, limit: int = 80):
    out = []
    cur = bytearray()
    start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not cur:
                start = i
            cur.append(b)
        else:
            if len(cur) >= minlen:
                out.append((start, bytes(cur)))
                if len(out) >= limit:
                    return out
            cur = bytearray()
    if len(cur) >= minlen:
        out.append((start, bytes(cur)))
    return out


def probe(path: str) -> None:
    raw_size = os.path.getsize(path)
    data = soulsutil.load(path)
    print(f"\n########## {path}")
    print(f"Fichier sur disque : {raw_size:,} octets")
    print(f"Apres decompression : {len(data):,} octets")
    print(f"Magic : {data[0:4]!r}")

    if data[:4] != b"BND4":
        print(">> Pas un BND4.")
        return

    print("\n--- En-tete (512 premiers octets) ---")
    hexdump(data, 0, 0x200)

    print("\n--- Chaines ASCII (offset, longueur, texte) ---")
    for off, s in ascii_runs(data, 4, 80):
        print(f"  0x{off:08X}  ({len(s):>4})  {s.decode('ascii', 'replace')}")

    print("\n--- Fin de fichier (64 derniers octets) ---")
    hexdump(data, max(0, len(data) - 64), 64)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        probe(p)


if __name__ == "__main__":
    main()
