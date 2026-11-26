"""
Cherche un motif d'octets dans un fichier et affiche les emplacements.

Usage :
    python tools/bin_cherche.py <fichier> <motif hexa> [contexte_octets]
Exemple :
    python tools/bin_cherche.py modele.flver "07 00 00 00 C8 00 00 00" 64
"""

import sys


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    with open(sys.argv[1], "rb") as f:
        donnees = f.read()
    motif = bytes(int(x, 16) for x in sys.argv[2].replace(",", " ").split())
    contexte = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0

    trouves = []
    debut = 0
    while True:
        i = donnees.find(motif, debut)
        if i < 0:
            break
        trouves.append(i)
        debut = i + 1

    print("fichier : %s (%d octets)" % (sys.argv[1], len(donnees)))
    print("motif   : %s" % sys.argv[2])
    print("trouve  : %d fois" % len(trouves))
    print()
    for i in trouves[:40]:
        print("  0x%06X" % i)
        if contexte:
            bloc = donnees[i:i + contexte]
            for k in range(0, len(bloc), 16):
                ligne = bloc[k:k + 16]
                print("      +%02X  %s" % (k, " ".join("%02X" % b for b in ligne)))
            print()


if __name__ == "__main__":
    main()
