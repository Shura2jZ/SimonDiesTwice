"""
Balayage de tous les modeles de personnages du jeu (chr/*.chrbnd.dcx).

Pour chaque FLVER trouve, on releve :
  - DataOffset (+0x0C) et son alignement modulo 0x100
  - DataLength (+0x10)
  - trueFaceCount (+0x40) et totalFaceCount (+0x44)
  - le nombre de facesets (+0x50)

But : savoir si la vanille respecte une contrainte d'alignement de DataOffset
(0x100) et une limite de taille de DataLength, que notre build ne respecterait
pas.

Aucune ecriture dans les dossiers de jeu.
"""
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import soulsutil
import bnd4_build

G = r"F:\Games\Sekiro - Shadows Die Twice\chr"


def main():
    lignes = []
    erreurs = 0
    noms = sorted(n for n in os.listdir(G) if n.endswith(".chrbnd.dcx"))
    print("fichiers chrbnd : %d" % len(noms), flush=True)
    for k, nom in enumerate(noms):
        p = os.path.join(G, nom)
        try:
            data = soulsutil.load(p)
            fc, eo, es, do, ents = bnd4_build.list_entries(data)
        except Exception as ex:
            erreurs += 1
            print("  ERR %s : %s" % (nom, ex), flush=True)
            continue
        for e in ents:
            n = bnd4_build.basename_of(e["fullname"])
            if not n.lower().endswith(".flver"):
                continue
            blob = data[e["offset"]:e["offset"] + e["size"]]
            if blob[:4] == b"DCX\x00":
                try:
                    blob = soulsutil.decompress_dcx(blob)
                except Exception as ex:
                    print("  ERR DCX %s / %s : %s" % (nom, n, ex), flush=True)
                    continue
            if blob[:5] != b"FLVER":
                print("  %s / %s : pas FLVER (entete %s)" % (nom, n, blob[:8].hex()), flush=True)
                continue
            dataoff, datalen = struct.unpack_from("<2i", blob, 0x0C)
            truefc, totfc = struct.unpack_from("<2i", blob, 0x40)
            nfs = struct.unpack_from("<i", blob, 0x50)[0]
            lignes.append((nom, n, len(blob), dataoff, datalen, truefc, totfc, nfs))
        if (k + 1) % 25 == 0:
            print("  ... %d/%d" % (k + 1, len(noms)), flush=True)

    print()
    print("=== %d FLVER lus, %d erreurs ===" % (len(lignes), erreurs))
    print("%-26s %-12s %10s %10s %10s %8s" % ("chrbnd", "flver", "DataOffset", "DataLength", "trueFaces", "facesets"))
    nonalign = []
    gros = []
    LIMITE = 8 * 1024 * 1024
    for (nom, n, taille, dataoff, datalen, truefc, totfc, nfs) in lignes:
        marque = ""
        if dataoff % 0x100 != 0:
            marque += " <<NON 0x100"
            nonalign.append((nom, n, dataoff, dataoff % 0x100))
        if datalen > LIMITE:
            marque += " <<>8Mio"
            gros.append((nom, n, datalen))
        print("%-26s %-12s %10d %10d %10d %8d%s" % (nom, n, dataoff, datalen, truefc, nfs, marque))

    print()
    print("DataOffset non aligne 0x100 : %d / %d" % (len(nonalign), len(lignes)))
    for x in nonalign:
        print("   %s / %s : DataOffset=%d (mod 0x100 = 0x%X)" % x)
    print("DataLength > 8 Mio : %d / %d" % (len(gros), len(lignes)))
    for x in gros:
        print("   %s / %s : DataLength=%d (%.2f Mio)" % (x[0], x[1], x[2], x[2] / 1048576.0))
    if lignes:
        print("DataLength max : %d (%.2f Mio)" % (max(l[4] for l in lignes), max(l[4] for l in lignes) / 1048576.0))
        print("DataOffset mod 0x100 (comptes) : %s" % sorted(set(l[3] % 0x100 for l in lignes)))
        print("trueFaceCount==totalFaceCount : %d / %d" % (sum(1 for l in lignes if l[5] == l[6]), len(lignes)))


if __name__ == "__main__":
    main()
