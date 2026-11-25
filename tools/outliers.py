"""
Recherche des sommets aberrants dans l'intermediaire : ceux qui sortent d'une
boite englobante raisonnable. Sert a identifier les morceaux etires (un sommet
a cheval sur deux os que la re-pose a eloignes).

Usage :
    python tools/outliers.py fichier.bin _work/isshin_nodes.tsv [marge]
"""

import struct
import sys


def main():
    chemin, chemin_tsv = sys.argv[1], sys.argv[2]
    # bornes par defaut, surchargeables
    bornes = [0.60, -0.15, 2.35, 0.60]
    if len(sys.argv) > 6:
        bornes = [float(x) for x in sys.argv[3:7]]
    bx, by_min, by_max, bz = bornes

    noms = {}
    for ligne in open(chemin_tsv, encoding="utf-8").read().splitlines()[1:]:
        c = ligne.split("\t")
        if len(c) < 29:
            continue
        noms[int(c[0])] = c[3]

    f = open(chemin, "rb")
    f.read(8)
    nb_maillages = struct.unpack("<I", f.read(4))[0]
    f.read(36)
    nb_os = struct.unpack("<I", f.read(4))[0]
    for _ in range(nb_os):
        n = struct.unpack("<I", f.read(4))[0]
        f.read(n + 4)

    compte = {}
    exemples = {}
    total = 0
    for _ in range(nb_maillages):
        n = struct.unpack("<I", f.read(4))[0]
        nom_m = f.read(n).decode("utf-8")
        f.read(12)
        ns, ni = struct.unpack("<II", f.read(8))
        for _ in range(ns):
            v = struct.unpack("<3f3f4f2f4f4i4f", f.read(96))
            x, y, z = v[0], v[1], v[2]
            dehors = (abs(x) > bx or y < by_min or y > by_max or abs(z) > bz)
            if not dehors:
                continue
            total += 1
            idx = (v[16], v[17], v[18], v[19])
            poids = (v[20], v[21], v[22], v[23])
            meilleur = max(range(4), key=lambda k: poids[k])
            cle = noms.get(idx[meilleur], "?")
            compte[cle] = compte.get(cle, 0) + 1
            if cle not in exemples:
                exemples[cle] = (nom_m, x, y, z, poids[0], poids[1], poids[2], poids[3])
        f.read(ni * 4)

    print("sommets hors de la boite : %d" % total)
    print("%-24s %8s   %s" % ("os dominant", "sommets", "exemple"))
    for cle, n in sorted(compte.items(), key=lambda kv: -kv[1]):
        nom_m, x, y, z, w0, w1, w2, w3 = exemples[cle]
        print("%-24s %8d   %-28s (%7.3f,%7.3f,%7.3f) poids %.2f %.2f %.2f %.2f"
              % (cle, n, nom_m, x, y, z, w0, w1, w2, w3))


if __name__ == "__main__":
    main()
