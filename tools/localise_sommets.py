"""
Localise dans le FLVER la position du premier sommet du premier maillage.

La position re-posee du premier sommet se trouve telle quelle dans
_work/simon_inter.bin (format SMPORT) : on la relit puis on cherche ses octets
dans le FLVER. Cela donne le vrai debut des donnees de sommets, a comparer avec
DataOffset + (taille annoncee des indices).

Usage :
    python tools/localise_sommets.py <simon_inter.bin> <modele.flver>
"""

import struct
import sys

TAILLE_SOMMET = 96


def premier_sommet(chemin_bin):
    with open(chemin_bin, "rb") as f:
        donnees = f.read()
    if donnees[:8] != b"SMPORT\x00\x01":
        raise SystemExit("ce n'est pas un fichier SMPORT")
    pos = 8
    nb_maillages, = struct.unpack_from("<I", donnees, pos)
    pos += 4
    pos += 36                       # MATRICE_180_Y
    nb_os, = struct.unpack_from("<I", donnees, pos)
    pos += 4
    for _ in range(nb_os):          # table des os
        n, = struct.unpack_from("<I", donnees, pos)
        pos += 4 + n + 4
    n, = struct.unpack_from("<I", donnees, pos)
    nom = donnees[pos + 4:pos + 4 + n].decode("utf-8")
    pos += 4 + n
    pos += 12                       # mat, noeud, -1
    n_sommets, n_indices = struct.unpack_from("<II", donnees, pos)
    pos += 8
    x, y, z = struct.unpack_from("<3f", donnees, pos)
    return nom, nb_maillages, n_sommets, n_indices, (x, y, z)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    nom, nb, ns, ni, p = premier_sommet(sys.argv[1])
    print("SMPORT : %d maillages, premier = %s (%d sommets, %d indices)" % (nb, nom, ns, ni))
    print("premier sommet, position : %r" % (p,))
    motif = struct.pack("<3f", *p)
    print("octets : %s" % " ".join("%02X" % b for b in motif))
    print()

    with open(sys.argv[2], "rb") as f:
        flver = f.read()
    trouves, debut = [], 0
    while True:
        i = flver.find(motif, debut)
        if i < 0:
            break
        trouves.append(i)
        debut = i + 1
    print("FLVER : %d octets ; position trouvee %d fois" % (len(flver), len(trouves)))
    donnees_off, donnees_len = struct.unpack_from("<II", flver, 0x0C)
    print("DataOffset = %d (0x%X)   DataLength = %d" % (donnees_off, donnees_off, donnees_len))
    print("fin de la zone de donnees : %d" % (donnees_off + donnees_len))
    for i in trouves[:12]:
        print("   trouve a 0x%06X   ecart a DataOffset = %d" % (i, i - donnees_off))


if __name__ == "__main__":
    main()
