"""
Lit une zone d'un fichier et l'interprete en flottants 32 bits (4 par ligne),
avec l'offset en hexadecimal. Sert a reconnaitre une zone de sommets.

Usage :
    python tools/bin_lire.py <fichier> <offset> [octets]
"""

import struct
import sys


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    chemin = sys.argv[1]
    offset = int(sys.argv[2], 0)
    longueur = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100
    mode = sys.argv[4] if len(sys.argv) > 4 else "float"
    with open(chemin, "rb") as f:
        f.seek(offset)
        donnees = f.read(longueur)

    print("fichier : %s" % chemin)
    print("zone    : 0x%06X .. 0x%06X   (%s)" % (offset, offset + len(donnees), mode))
    print()
    for k in range(0, len(donnees) - 3, 16):
        bloc = donnees[k:k + 16]
        if mode == "int":
            vals = struct.unpack("<%di" % (len(bloc) // 4), bloc[:len(bloc) // 4 * 4])
            txt = "  ".join("%12d" % v for v in vals)
        else:
            vals = struct.unpack("<%df" % (len(bloc) // 4), bloc[:len(bloc) // 4 * 4])
            txt = "  ".join("%13.6g" % v for v in vals)
        print("  0x%06X  %s" % (offset + k, txt))


if __name__ == "__main__":
    main()
