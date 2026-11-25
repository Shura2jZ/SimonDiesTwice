"""
Fabrique une pose de test a partir d'une pose existante : on ne modifie QUE la
rotation locale d'un seul noeud (repere par son nom). Sert a verifier que les
indices d'os des sommets pointent bien sur le bon noeud.

Usage :
    python tools/pose_un_os.py <pose_entree.json> <pose_sortie.json> <nom_noeud> <rx> <ry> <rz>
"""

import json
import sys


def main():
    if len(sys.argv) < 7:
        raise SystemExit(__doc__)
    entree, sortie, nom = sys.argv[1], sys.argv[2], sys.argv[3]
    rx, ry, rz = (float(x) for x in sys.argv[4:7])

    with open(entree, encoding="utf-8") as f:
        noeuds = json.load(f)

    cibles = [i for i, n in enumerate(noeuds) if n.get("Name") == nom]
    if not cibles:
        raise SystemExit("noeud introuvable : %s" % nom)
    i = cibles[0]
    avant = noeuds[i]["Rotation"]
    noeuds[i]["Rotation"] = {"X": rx, "Y": ry, "Z": rz}
    print("noeud %d (%s) : rotation %s -> (%.4f, %.4f, %.4f)"
          % (i, nom, avant, rx, ry, rz))
    print("enfants directs : %s"
          % [k for k, n in enumerate(noeuds) if n.get("ParentIndex") == i])

    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(noeuds, f, separators=(",", ":"))
    print("ecrit : %s" % sortie)


if __name__ == "__main__":
    main()
