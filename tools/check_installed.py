"""
Controle du fichier de mod reellement installe : on le decompresse, on relit le
BND4, on extrait c5400.flver et on l'ecrit dans _work pour verification.

Usage :
    python tools/check_installed.py [chemin.chrbnd.dcx]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil
import bnd4_build

DEFAUT = r"F:\Games\Sekiro - Shadows Die Twice\mods\chr\c5400.chrbnd.dcx"


def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else DEFAUT
    brut = soulsutil.load(chemin)
    print("fichier       : %s" % chemin)
    print("BND4 decompresse : %d octets" % len(brut))
    fc, eo, es, do, ents = bnd4_build.list_entries(brut)
    print("entrees       : %d" % fc)
    for e in ents:
        print("  %-28s %10d octets  (offset absolu 0x%X)" % (bnd4_build.basename_of(e["fullname"]),
                                                            e["size"], e["offset"]))
    for e in ents:
        if bnd4_build.basename_of(e["fullname"]) == "c5400.flver":
            debut = e["offset"]
            donnees = brut[debut:debut + e["size"]]
            sortie = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "_work", "installe_c5400.flver")
            open(sortie, "wb").write(donnees)
            print()
            print("c5400.flver   : %d octets, magie=%r" % (len(donnees), donnees[:6]))
            print("ecrit         : %s" % sortie)
            return
    print("ERREUR : c5400.flver absent")


if __name__ == "__main__":
    main()
