"""
Bilan des facesets d'un dump FlverDump : repartition des indices par niveau de
detail (LOD) et comparaison avec les champs d'en-tete a 0x40 et 0x44.

Usage :
    python tools/facesets_bilan.py <dump.txt> [champ40] [champ44]
"""

import re
import sys


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    texte = open(sys.argv[1], encoding="utf-8-sig").read()
    ch40 = int(sys.argv[2]) if len(sys.argv) > 2 else None
    ch44 = int(sys.argv[3]) if len(sys.argv) > 3 else None

    motif = re.compile(
        r"maillage\[(\d+)\]\.faceset\[(\d+)\] drapeaux (.+?)  bande (\S+)  cull (\S+)  "
        r"unk06 (-?\d+)  indices (\d+)  somme (-?\d+)  min (-?\d+)  max (-?\d+)")

    par_maillage = {}
    total = 0
    for m in motif.finditer(texte):
        i = int(m.group(1))
        drapeaux = m.group(3).strip()
        n = int(m.group(7))
        par_maillage.setdefault(i, []).append((int(m.group(2)), drapeaux, n, int(m.group(6))))
        total += n

    print("facesets analyses : %d" % sum(len(v) for v in par_maillage.values()))
    print("indices cumules    : %d  (= %d octets)" % (total, total * 2))
    print()

    # regroupement par jeu de drapeaux
    groupes = {}
    for i, sets in par_maillage.items():
        for k, drapeaux, n, unk in sets:
            groupes[drapeaux] = groupes.get(drapeaux, 0) + n
    print("repartition par drapeaux :")
    for d in sorted(groupes, key=lambda x: -groupes[x]):
        print("   %-28s indices %9d   octets %10d" % (d, groupes[d], groupes[d] * 2))
    print()

    # par faceset : position dans le maillage
    print("par position dans le maillage (faceset 0,1,2,...) :")
    par_position = {}
    for i, sets in par_maillage.items():
        for k, drapeaux, n, unk in sets:
            par_position.setdefault(k, []).append((n, drapeaux))
    for k in sorted(par_position):
        liste = par_position[k]
        somme = sum(n for n, d in liste)
        ex = sorted(set(d for n, d in liste))
        print("   faceset[%d] : %2d occurrences, indices %9d, octets %10d, drapeaux %s"
              % (k, len(liste), somme, somme * 2, ex))
    print()

    # nombre de facesets par maillage
    rep = {}
    for i, sets in par_maillage.items():
        rep[len(sets)] = rep.get(len(sets), 0) + 1
    print("nombre de facesets par maillage : %s" % sorted(rep.items()))
    print()

    if ch40 is not None or ch44 is not None:
        print("champs d'en-tete :")
        if ch40 is not None:
            print("   0x40 = %d   ; indices cumules / 0x40 = %.4f   ; total*2/0x40 = %.4f"
                  % (ch40, total / float(ch40), total * 2 / float(ch40)))
        if ch44 is not None:
            print("   0x44 = %d   ; indices cumules / 0x44 = %.4f   ; total*2/0x44 = %.4f"
                  % (ch44, total / float(ch44), total * 2 / float(ch44)))
        print()

    print("detail (maillage, faceset, drapeaux, indices, unk06), 12 premiers :")
    n = 0
    for i in sorted(par_maillage):
        for k, drapeaux, c, unk in par_maillage[i]:
            print("   maillage %2d  faceset %d  %-28s indices %7d  unk06 %d" % (i, k, drapeaux, c, unk))
            n += 1
            if n >= 12:
                break
        if n >= 12:
            break


if __name__ == "__main__":
    main()
