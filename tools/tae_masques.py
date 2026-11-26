"""
Extrait les masques de dessin (ChangeDrawMask) du TAE de Sekiro.

Contexte : dans le .tae de c5400, les evenements de type 0x83 portent un masque
de 5 octets (33 bits, un par maillage du modele) juste avant l'en-tete de
l'evenement. On cherche donc la signature

    ?? ?? ?? ?? ??  00 01 00  83 00 00 00 00 00 00 00

et on affiche les 5 octets qui precedent, ainsi que leur frequence, pour savoir
quels maillages les animations masquent.

Usage :
    python tools/tae_masques.py <fichier.tae>
"""

import collections
import sys

SIGNATURE = b"\x00\x01\x00\x83\x00\x00\x00\x00\x00\x00\x00"
TAILLE_MASQUE = 5


def bits(masque):
    texte = []
    for i in range(len(masque) - 1, -1, -1):
        for b in range(7, -1, -1):
            texte.append("1" if (masque[i] >> b) & 1 else "0")
    return "".join(texte)


def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else r"_work\extracted\c5400.anibnd\c5400.tae"
    with open(chemin, "rb") as f:
        donnees = f.read()
    print("fichier : %s (%d octets)" % (chemin, len(donnees)))
    print("signature : %s" % SIGNATURE.hex(" "))
    print()

    comptes = collections.Counter()
    positions = []
    debut = 0
    while True:
        i = donnees.find(SIGNATURE, debut)
        if i < 0:
            break
        positions.append(i)
        if i >= TAILLE_MASQUE:
            comptes[donnees[i - TAILLE_MASQUE:i]] += 1
        debut = i + 1

    print("evenements trouves : %d" % len(positions))
    print("masques distincts  : %d" % len(comptes))
    print()
    print("%-8s %-14s %-12s %s" % ("masque", "hexa", "occurrences", "bits 32..0"))
    print("-" * 78)
    for masque, n in comptes.most_common():
        print("%-8s %-14s %-12d %s"
              % ("".join("%02X" % b for b in masque), masque.hex(" "), n, bits(masque)))
    print()
    print("premieres positions : %s" % ", ".join("0x%06X" % p for p in positions[:12]))


if __name__ == "__main__":
    main()
