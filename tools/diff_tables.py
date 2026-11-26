"""
Diff de la ZONE DES TABLES (tout ce qui precede la section de donnees, donc
avant DataOffset a 0x0C) entre le FLVER vanille du jeu et le FLVER installe.

But : reperer une table PAR MAILLAGE (ou par faceset) que notre chaine n'aurait
pas mise a jour. La vanille et notre build ont exactement les memes comptes
(33 maillages, 196 facesets, 49 tampons, 757 noeuds, 30 materiaux), donc les
tables sont au meme endroit et un diff direct est exploitable.

Usage :
    python tools/diff_tables.py [chemin.flver]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil      # noqa: E402
import bnd4_build     # noqa: E402

GAME = r"E:\Games\Sekiro - Shadows Die Twice"
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def flver_vanille():
    dcx = open(os.path.join(GAME, "chr", "c5400.chrbnd.dcx"), "rb").read()
    bnd = soulsutil.decompress_dcx(dcx)
    _, _, _, _, es = bnd4_build.list_entries(bnd)
    for e in es:
        if bnd4_build.basename_of(e["fullname"]) == "c5400.flver":
            return bnd[e["offset"]:e["offset"] + e["size"]]
    raise SystemExit("c5400.flver introuvable dans l'archive vanille")


def main():
    p_mod = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ, "_work", "installe_maintenant.flver")
    a = flver_vanille()
    b = open(p_mod, "rb").read()

    off_a = struct.unpack_from("<i", a, 0x0C)[0]
    off_b = struct.unpack_from("<i", b, 0x0C)[0]
    print("vanille : %d o, DataOffset 0x%X" % (len(a), off_a))
    print("mod     : %d o, DataOffset 0x%X" % (len(b), off_b))
    zone = min(off_a, off_b)

    # passages ou les octets different, dans la zone des tables
    plages = []
    i = 0
    while i < zone:
        if a[i] != b[i]:
            j = i
            while j < zone and a[j] != b[j]:
                j += 1
            plages.append((i, j))
            i = j
        else:
            i += 1
    print()
    print("zone des tables comparee : 0x0 .. 0x%X  (%d octets)" % (zone, zone))
    print("nb de passages differents : %d  (total %d octets)"
          % (len(plages), sum(j - i for i, j in plages)))
    print()
    for (i, j) in plages:
        n = j - i
        print("  @0x%06X .. 0x%06X  (%d octets)" % (i, j, n))
        if n <= 96:
            print("     vanille : %s" % a[i:j].hex())
            print("     mod     : %s" % b[i:j].hex())
        else:
            print("     vanille : %s ..." % a[i:i + 48].hex())
            print("     mod     : %s ..." % b[i:i + 48].hex())
    return 0


if __name__ == "__main__":
    sys.exit(main())
