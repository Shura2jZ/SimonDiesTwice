"""
Apercu de la structure d'un fichier USD ASCII (.usda) exporte par FModel.

Les lignes sont enormes (les tableaux d'images tiennent sur une ligne), donc on
n'affiche que des extraits.

    python -u tools/usda_apercu.py <fichier.usda> [debut] [longueur]
"""

import sys


def main():
    chemin = sys.argv[1]
    debut = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    longueur = int(sys.argv[3]) if len(sys.argv) > 3 else 600

    with open(chemin, "r", encoding="utf-8", errors="replace") as fh:
        lignes = fh.readlines()

    print("lignes : %d" % len(lignes))
    for numero, ligne in enumerate(lignes, 1):
        ligne = ligne.rstrip("\n")
        if len(ligne) > 160:
            print("%5d  [%8d car.]  %s ..." % (numero, len(ligne), ligne[:longueur]))
        else:
            print("%5d  [%8d car.]  %s" % (numero, len(ligne), ligne))


if __name__ == "__main__":
    main()
