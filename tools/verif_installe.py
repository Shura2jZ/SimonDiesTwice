"""
Affiche ce qui est REELLEMENT installe dans le jeu, sans supposer quoi que ce
soit : decompresse mods\\chr\\c5400.chrbnd.dcx, liste ses entrees, et pour le
FLVER affiche les champs d'en-tete sensibles (0x0C offset, 0x10 longueur,
0x40 faces hors motion blur, 0x44 total des faces, 0x50 facesets) + un resume
des maillages. Permet aussi de comparer a un FLVER de reference.

Usage :
    python tools/verif_installe.py [<flver_de_reference>]
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil      # noqa: E402
import bnd4_build     # noqa: E402

GAME = r"F:\Games\Sekiro - Shadows Die Twice"
CIBLE = os.path.join(GAME, "mods", "chr", "c5400.chrbnd.dcx")


def champs_flver(b):
    return {
        "0x0C DataOffset": struct.unpack_from("<i", b, 0x0C)[0],
        "0x10 DataLength": struct.unpack_from("<i", b, 0x10)[0],
        "0x14 dummies": struct.unpack_from("<i", b, 0x14)[0],
        "0x18 materiaux": struct.unpack_from("<i", b, 0x18)[0],
        "0x1C os": struct.unpack_from("<i", b, 0x1C)[0],
        "0x20 maillages": struct.unpack_from("<i", b, 0x20)[0],
        "0x24 tampons": struct.unpack_from("<i", b, 0x24)[0],
        "0x40 faces hors motion blur": struct.unpack_from("<i", b, 0x40)[0],
        "0x44 total des faces": struct.unpack_from("<i", b, 0x44)[0],
        "0x50 facesets": struct.unpack_from("<i", b, 0x50)[0],
        "0x54 agencements": struct.unpack_from("<i", b, 0x54)[0],
        "0x58 textures": struct.unpack_from("<i", b, 0x58)[0],
    }


def main():
    ref_path = sys.argv[1] if len(sys.argv) > 1 else None

    if not os.path.isfile(CIBLE):
        print("aucun mod installe : %s" % CIBLE)
        return 2

    dcx = open(CIBLE, "rb").read()
    print("fichier installe : %s" % CIBLE)
    print("  taille        : %d octets" % len(dcx))
    print("  sha256        : %s" % hashlib.sha256(dcx).hexdigest())
    print("  en-tete DCX   : %s" % soulsutil.parse_dcx_header(dcx))

    bnd = soulsutil.decompress_dcx(dcx)
    print("  BND4          : %d octets   sha %s" % (len(bnd), hashlib.sha256(bnd).hexdigest()[:16]))

    _, _, _, _, entrees = bnd4_build.list_entries(bnd)
    print("  entrees (%d) :" % len(entrees))
    flver = None
    for e in entrees:
        nom = bnd4_build.basename_of(e["fullname"])
        print("    %-28s  %9d octets  @ %d" % (nom, e["size"], e["offset"]))
        if "flver" in nom.lower():
            flver = bnd[e["offset"]:e["offset"] + e["size"]]

    if flver is None:
        print("  pas de FLVER trouve dans le BND4")
        return 1

    print()
    print("=== FLVER installe (%d octets) ===" % len(flver))
    for k, v in champs_flver(flver).items():
        print("  %-28s = %d" % (k, v))

    if ref_path and os.path.isfile(ref_path):
        ref = open(ref_path, "rb").read()
        print()
        print("=== comparaison a %s ===" % ref_path)
        rc = champs_flver(ref)
        ic = champs_flver(flver)
        for k in rc:
            meme = "IDEM " if rc[k] == ic[k] else "DIFF"
            print("  %s  %-28s vanille=%-12d installe=%d" % (meme, k, rc[k], ic[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
