"""
Cherche dans un fichier la suite d'octets correspondant a une liste de flottants
32 bits little-endian. Sert a localiser un champ dans un format binaire.

Usage :
    python tools/bin_flottants.py <fichier> <f1> <f2> ...
"""

import struct
import sys


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    with open(sys.argv[1], "rb") as f:
        donnees = f.read()
    valeurs = [float(x) for x in sys.argv[2:]]
    motif = b"".join(struct.pack("<f", v) for v in valeurs)

    print("fichier : %s (%d octets)" % (sys.argv[1], len(donnees)))
    print("motif   : %s" % ", ".join("%g" % v for v in valeurs))
    print("octets  : %s" % " ".join("%02X" % b for b in motif))
    print()

    trouves, debut = [], 0
    while True:
        i = donnees.find(motif, debut)
        if i < 0:
            break
        trouves.append(i)
        debut = i + 1
    print("trouve : %d fois" % len(trouves))
    for i in trouves[:20]:
        print("  0x%06X" % i)
        bloc = donnees[max(0, i - 32):i + 32 + len(motif)]
        base = max(0, i - 32)
        for k in range(0, len(bloc), 16):
            ligne = bloc[k:k + 16]
            marque = " <<<" if base + k <= i < base + k + 16 else ""
            print("     0x%06X  %s%s" % (base + k, " ".join("%02X" % b for b in ligne), marque))
        print()


if __name__ == "__main__":
    main()
