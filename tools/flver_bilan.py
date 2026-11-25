"""
Bilan arithmetique d'un dump FlverDump : confronte les champs d'en-tete aux
donnees reelles des maillages.

  - somme des indices de tous les facesets ;
  - taille des agencements de sommets ;
  - octets de sommets attendus ;
  - comparaison avec DataOffset / DataLength et avec le champ d'en-tete a 0x40.

Usage :
    python tools/flver_bilan.py <dump.txt> [nom]
"""

import re
import sys


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    nom = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
    texte = open(sys.argv[1], encoding="utf-8-sig").read()

    def champ(prefixe, cle):
        m = re.search(re.escape(prefixe + cle) + r"\s*=\s*([-\d.eE+]+)", texte)
        return m.group(1) if m else "?"

    # agencements
    tailles = {}
    for m in re.finditer(r"agencement\[(\d+)\] taille = (\d+)\s+membres = (\d+)", texte):
        tailles[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))

    # maillages : nombre de sommets et agencements utilises
    maillages = []
    for m in re.finditer(r"maillage\[(\d+)\] materiau (\d+)\s+noeud (\d+).*?sommets (\d+)", texte):
        maillages.append({"i": int(m.group(1)), "mat": int(m.group(2)),
                          "noeud": int(m.group(3)), "sommets": int(m.group(4))})

    tampons = {}
    for m in re.finditer(r"maillage\[(\d+)\]\.tampon\[(\d+)\] tampon (\d+)\s+agencement (\d+)\s+aretesCompressees (\w+)", texte):
        tampons.setdefault(int(m.group(1)), []).append((int(m.group(2)), int(m.group(3)), int(m.group(4))))

    facesets = {}
    total_indices = 0
    for m in re.finditer(r"maillage\[(\d+)\]\.faceset\[(\d+)\] drapeaux (\S+)\s+bande (\S+)\s+cull (\S+)\s+unk06 (-?\d+)\s+indices (\d+)", texte):
        i, k = int(m.group(1)), int(m.group(2))
        n = int(m.group(7))
        facesets.setdefault(i, []).append((k, m.group(3), n))
        total_indices += n

    print("=== %s ===" % nom)
    print("champs d'en-tete :")
    for k in ("DataOffset", "DataLength", "dummies", "materiaux", "noeuds", "maillages", "tamponsSommets",
              "agencements", "osBase"):
        print("   compte.%-16s = %s" % (k, champ("compte.", k)))
    print("   en-tete.bboxMin          = %s" % champ("en-tete.", "bboxMin"))
    print("   en-tete.bboxMax          = %s" % champ("en-tete.", "bboxMax"))
    print()
    print("agencements de sommets : %s"
          % ", ".join("%d:%d o/%d membres" % (i, t, n) for i, (t, n) in sorted(tailles.items())))
    print()
    print("maillages : %d   sommets : %d   facesets : %d   indices cumules : %d"
          % (len(maillages), sum(m["sommets"] for m in maillages),
             sum(len(v) for v in facesets.values()), total_indices))
    print("octets d'indices cumules (x2) : %d" % (total_indices * 2))

    octets_sommets = 0
    detail = []
    for m in maillages:
        for tampon in tampons.get(m["i"], []):
            taille = tailles.get(tampon[2], (0, 0))[0]
            octets_sommets += m["sommets"] * taille
        detail.append((m["i"], m["mat"], m["sommets"], len(tampons.get(m["i"], [])),
                       [t[2] for t in tampons.get(m["i"], [])]))
    print("octets de sommets attendus  : %d" % octets_sommets)
    print("somme indices + sommets     : %d" % (total_indices * 2 + octets_sommets))
    print()
    print("nb de copies d'indices que represente DataLength : "
          "%.3f" % ((int(champ("compte.", "DataLength")) - octets_sommets) / float(total_indices * 2))
          if champ("compte.", "DataLength").isdigit() and total_indices * 2 else "?")
    print()
    print("detail par maillage : (i, materiau, sommets, nb tampons, agencements)")
    for d in detail[:40]:
        print("   %s" % (d,))

    # nombre de facesets par maillage
    rep = {}
    for i, v in facesets.items():
        rep[len(v)] = rep.get(len(v), 0) + 1
    print()
    print("nombre de facesets par maillage : %s" % sorted(rep.items()))


if __name__ == "__main__":
    main()
