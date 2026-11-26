"""
Interrogation d'un export d'os produit par FlverBones.exe (_work/isshin_nodes.tsv).

Le fichier est un tableau TSV : index, parent, flags, nom, translations/rotations/
echelles locales, puis les 16 coefficients de la matrice globale (M11..M44).

Usage :
    python tools/inspect_nodes.py fichier.tsv [motif]        # filtre sur le nom
    python tools/inspect_nodes.py fichier.tsv --list         # liste tous les noms
"""

import re
import sys


def charge(chemin):
    lignes = open(chemin, encoding="utf-8").read().splitlines()
    entete = lignes[0].split("\t")
    os = []
    for l in lignes[1:]:
        c = l.split("\t")
        if len(c) < 20:
            continue
        g = [float(x) for x in c[13:29]]
        os.append({"index": int(c[0]), "parent": int(c[1]), "flags": c[2], "nom": c[3],
                   "local_t": (float(c[4]), float(c[5]), float(c[6])),
                   "local_r": (float(c[7]), float(c[8]), float(c[9])),
                   "global": (g[12], g[13], g[14]),
                   "mat": g})
    return os


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    os = charge(sys.argv[1])
    print("%d os charges" % len(os))
    if len(sys.argv) > 2 and sys.argv[2] == "--list":
        for o in os:
            print("%4d  parent=%4d  %s" % (o["index"], o["parent"], o["nom"]))
        return 0
    motif = sys.argv[2] if len(sys.argv) > 2 else ".*"
    pat = re.compile(motif, re.I)
    n = 0
    for o in os:
        if not pat.search(o["nom"]):
            continue
        n += 1
        p = o["global"]
        print("%4d  %-26s parent=%-4d  X=%9.5f  Y=%9.5f  Z=%9.5f"
              % (o["index"], o["nom"], o["parent"], p[0], p[1], p[2]))
    print("%d os correspondants" % n)
    return 0


if __name__ == "__main__":
    main()
