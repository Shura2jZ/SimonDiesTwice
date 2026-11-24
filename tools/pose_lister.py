"""
Affiche les noeuds d'une pose JSON dont le nom contient un motif donne, avec leur
parent et leur rotation locale. Sert a reperer le noeud a animer pour un test.

Usage :
    python tools/pose_lister.py <pose.json> [motif]
"""

import json
import sys


def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else r"_work\poses\isshin_identite.json"
    motif = (sys.argv[2] if len(sys.argv) > 2 else "head").lower()

    with open(chemin, encoding="utf-8") as f:
        noeuds = json.load(f)
    print("fichier : %s" % chemin)
    print("noeuds  : %d" % len(noeuds))
    print()
    for i, e in enumerate(noeuds):
        nom = e.get("Name", "")
        if motif in nom.lower():
            r = e.get("Rotation") or {}
            print("%4d  %-34s parent %5s  rot (%.4f %.4f %.4f)  flags %s"
                  % (i, nom, e.get("ParentIndex"), r.get("X", 0.0), r.get("Y", 0.0),
                     r.get("Z", 0.0), e.get("Flags")))


if __name__ == "__main__":
    main()
