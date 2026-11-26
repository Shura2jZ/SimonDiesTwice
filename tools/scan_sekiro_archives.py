"""
M1 - Etape 1 : identification empirique des archives Sekiro.
Ne suppose AUCUN format : on lit les octets reels et on cherche des magics connus.

Usage:
    python tools/scan_sekiro_archives.py "F:\\Games\\Sekiro - Shadows Die Twice"
"""
import sys
import os
import glob

MAGICS = {
    b"BHD5": "Archive index DS3/ER (BHD5)",
    b"BHD4": "Archive index (BHD4)",
    b"BHD3": "Archive index (BHD3)",
    b"BND4": "Conteneur BND4",
    b"BND3": "Conteneur BND3",
    b"DFLT": "Compression DCX (deflate)",
    b"DCX\0": "Conteneur DCX",
    b"KRAK": "Compression DCX (Kraken)",
    b"FLVER": "Modele FLVER",
    b"HKX": "Havok HKX",
}

HEADER = 64


def probe(path: str) -> None:
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        head = fh.read(HEADER)
    hexhead = " ".join(f"{b:02X}" for b in head[:32])
    print(f"\n=== {os.path.basename(path)}  ({size:,} octets) ===")
    print(f"  hex   : {hexhead}")
    print(f"  ascii : {''.join(chr(b) if 32 <= b < 127 else '.' for b in head[:32])}")

    found = [label for magic, label in MAGICS.items() if head.startswith(magic)]
    if found:
        print(f"  MAGIC detecte en tete : {', '.join(found)}")
    else:
        # le magic n'est peut-etre pas en tete -> on cherche dans tout le fichier
        with open(path, "rb") as fh:
            blob = fh.read()
        hits = []
        for magic, label in MAGICS.items():
            off = blob.find(magic)
            if off != -1:
                hits.append(f"{label} @ offset {off}")
        if hits:
            print(f"  magic trouve hors tete : {'; '.join(hits)}")
        else:
            print("  AUCUN magic connu -> probablement chiffre, ou format inconnu")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    root = sys.argv[1]

    bhd = sorted(glob.glob(os.path.join(root, "Data*.bhd")))
    bdt = sorted(glob.glob(os.path.join(root, "Data*.bdt")))
    print(f"Fichiers .bhd trouves : {len(bhd)}")
    print(f"Fichiers .bdt trouves : {len(bdt)}")

    print("\n########## INDEXES (.bhd) ##########")
    for p in bhd:
        probe(p)

    print("\n########## DATA (.bdt) - 1er fichier seulement ##########")
    if bdt:
        probe(bdt[0])


if __name__ == "__main__":
    main()
