"""
M1 - Sonde des fichiers MSB (map) de Sekiro.

Objectif : sans parser le format MSB, extraire du decompresse les noms de modeles
de personnages places dans chaque map (chaines du type "c5400_0000").

Verifie aussi le magic du MSB decompresse (validation du pipeline DCX sur un
nouveau format).

Usage :
    python tools/msb_scan.py "F:\\Games\\Sekiro - Shadows Die Twice\\map\\mapstudio"
    python tools/msb_scan.py <dossier> --grep c5400

Aucune ecriture dans les dossiers de jeu.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from soulsutil import load, is_dcx, parse_dcx_header

CHR_TOKEN = re.compile(rb"c\d{4}(?:_[0-9a-fA-F]{2,4})?")


def scan_msb(path: str, grep=None) -> None:
    raw = open(path, "rb").read()
    dcx = is_dcx(raw)
    data = load(path)
    magic = data[:4]

    tokens = sorted({m.group().decode() for m in CHR_TOKEN.finditer(data)})
    roots = sorted({t.split("_")[0] for t in tokens})

    print("=" * 70)
    print(f"{os.path.basename(path)}  ({len(raw):,} o brut, {len(data):,} o decompresse)")
    print(f"   DCX={dcx}  magic={magic!r}")
    if dcx:
        h = parse_dcx_header(raw)
        print(f"   compression={h['compressionType']}  taille annoncee={h['uncompressedSize']:,}")
    print(f"   {len(roots)} modeles personnage distincts : {' '.join(roots)}")

    if grep:
        needle = grep.encode()
        hits = [t for t in tokens if needle in t.encode()]
        print(f"   grep {grep!r} -> {hits}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    grep = None
    if "--grep" in sys.argv:
        grep = sys.argv[sys.argv.index("--grep") + 1]

    if not args:
        print(__doc__)
        sys.exit(1)

    target = args[0]
    if os.path.isdir(target):
        files = sorted(
            os.path.join(target, f) for f in os.listdir(target) if f.endswith(".msb.dcx")
        )
    else:
        files = [target]

    for fp in files:
        scan_msb(fp, grep)


if __name__ == "__main__":
    main()
