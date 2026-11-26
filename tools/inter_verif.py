"""
Integrite de l'intermediaire SMPORT : on verifie que chaque maillage tient
exactement dans le fichier, sans trou ni depassement.

Usage :
    python tools/inter_verif.py fichier.bin
"""

import os
import struct
import sys


def main():
    chemin = sys.argv[1]
    taille = os.path.getsize(chemin)
    brut = open(chemin, "rb").read()
    print("fichier   : %s" % chemin)
    print("taille    : %d octets" % taille)
    print("magie     : %r" % brut[:8])

    pos = 0
    pos += 8
    nb_maillages = struct.unpack_from("<I", brut, pos)[0]; pos += 4
    pos += 36
    nb_os = struct.unpack_from("<I", brut, pos)[0]; pos += 4
    print("maillages : %d   os : %d" % (nb_maillages, nb_os))
    for _ in range(nb_os):
        n = struct.unpack_from("<I", brut, pos)[0]; pos += 4
        pos += n + 4
    print("table des os finit a 0x%X" % pos)

    for m in range(nb_maillages):
        n = struct.unpack_from("<I", brut, pos)[0]; pos += 4
        nom = brut[pos:pos + n].decode("utf-8", "replace"); pos += n
        mat, noeud, gab = struct.unpack_from("<iii", brut, pos); pos += 12
        ns, ni = struct.unpack_from("<II", brut, pos); pos += 8
        attendu = ns * 96 + ni * 4
        reste = taille - pos
        print("  [%d] %-28s mat=%d noeud=%d gab=%d  sommets=%-6d indices=%-6d "
              "octets=%d  reste_apres=%d %s"
              % (m, nom, mat, noeud, gab, ns, ni, attendu, reste - attendu,
                 "OK" if reste >= attendu else "DEPASSE"))
        pos += attendu


if __name__ == "__main__":
    main()
