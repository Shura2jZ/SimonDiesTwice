"""
Balayage des modeles de personnages : quels sont les plus gros en faces ?

But : tester des limites possibles du moteur.
Notre build a totalFaceCount = 1 043 144 (3 129 432 indices).
La vanille c5400 : 562 486 (1 687 458 indices).

Si aucun modele livre par le jeu ne depasse une valeur (2^21 indices,
2^22 indices, un nombre de faces...), c'est un candidat serieux.

Aucune ecriture dans les dossiers de jeu.
"""
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import soulsutil
import bnd4_build

G = r"E:\Games\Sekiro - Shadows Die Twice\chr"


def main():
    lignes = []
    noms = sorted(n for n in os.listdir(G) if n.endswith(".chrbnd.dcx"))
    print("fichiers chrbnd : %d" % len(noms), flush=True)
    for k, nom in enumerate(noms):
        try:
            data = soulsutil.load(os.path.join(G, nom))
            entries = bnd4_build.list_entries(data)[4]
        except Exception as ex:
            print("  ERR %s : %s" % (nom, ex), flush=True)
            continue
        for e in entries:
            n = bnd4_build.basename_of(e["fullname"])
            if not n.lower().endswith(".flver"):
                continue
            blob = data[e["offset"]:e["offset"] + e["size"]]
            if blob[:4] == b"DCX\x00":
                try:
                    blob = soulsutil.decompress_dcx(blob)
                except Exception:
                    continue
            if blob[:5] != b"FLVER":
                continue
            dataoff, datalen = struct.unpack_from("<2i", blob, 0x0C)
            truefc, totfc = struct.unpack_from("<2i", blob, 0x40)
            nvtx, nbuf = struct.unpack_from("<2i", blob, 0x20)[0], struct.unpack_from("<i", blob, 0x24)[0]
            lignes.append((nom, n, datalen, truefc, totfc, nbuf))
        if (k + 1) % 25 == 0:
            print("  ... %d/%d" % (k + 1, len(noms)), flush=True)

    print()
    print("%d FLVER lus" % len(lignes))
    print()
    print("=== 15 plus gros par nombre total de faces ===")
    print("%-26s %10s %10s %14s %14s" % ("chrbnd", "DataLength", "facesets", "trueFaces", "totalFaces"))
    for l in sorted(lignes, key=lambda x: -x[4])[:15]:
        print("%-26s %10d %10d %14d %14d" % (l[0], l[2], l[5], l[3], l[4]))

    print()
    maxf = max(l[4] for l in lignes)
    maxi = maxf * 3
    print("totalFaceCount max : %d  (soit %d indices)" % (maxf, maxi))
    for lim, lbl in [(2 ** 20, "2^20 indices"), (2 ** 21, "2^21 indices"), (2 ** 22, "2^22 indices"),
                     (66560, "65 536 faces"), (1000000, "1 000 000 faces"), (500000, "500 000 faces")]:
        if lbl.endswith("indices"):
            n = sum(1 for l in lignes if l[4] * 3 > lim)
        else:
            n = sum(1 for l in lignes if l[4] > lim)
        print("  modeles depassant %-18s : %d" % (lbl, n))

    print()
    print("=== les 10 plus gros en DataLength, avec leurs faces ===")
    for l in sorted(lignes, key=lambda x: -x[2])[:10]:
        print("  %-26s DataLength=%9d  totalFaces=%9d  indices=%9d" % (l[0], l[2], l[4], l[4] * 3))

    print()
    print("reference : notre build c5400 -> totalFaces=1043144  indices=3129432")
    print("reference : vanille      c5400 -> totalFaces=562486   indices=1687458")


if __name__ == "__main__":
    main()
