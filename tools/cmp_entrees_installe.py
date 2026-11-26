"""
Compare, entree par entree, l'archive chrbnd INSTALLEE dans le jeu avec l'archive
vanille du meme nom. Les tailles et les octets sont compares : un HKX ou un CLM2
mal replace par la reconstruction du BND4 ne serait pas vu par make_mod.py, qui
ne verifie que l'entree FLVER.

Usage :
    python tools/cmp_entrees_installe.py [<id personnage>]   (defaut : c5400)
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil      # noqa: E402
import bnd4_build     # noqa: E402

GAME = r"E:\Games\Sekiro - Shadows Die Twice"


def entrees(path):
    raw = open(path, "rb").read()
    bnd = soulsutil.decompress_dcx(raw)
    _, _, _, _, es = bnd4_build.list_entries(bnd)
    d = []
    for e in es:
        nom = bnd4_build.basename_of(e["fullname"])
        d.append((nom, e["size"], e["offset"], bnd[e["offset"]:e["offset"] + e["size"]]))
    return raw, bnd, d


def main():
    ident = sys.argv[1] if len(sys.argv) > 1 else "c5400"
    van_path = os.path.join(GAME, "chr", ident + ".chrbnd.dcx")
    mod_path = os.path.join(GAME, "mods", "chr", ident + ".chrbnd.dcx")

    for p in (van_path, mod_path):
        if not os.path.isfile(p):
            print("absent : %s" % p)
            return 2

    rv, bv, ev = entrees(van_path)
    rm, bm, em = entrees(mod_path)

    print("vanille : %s" % van_path)
    print("  fichier %d o | BND4 %d o | %d entrees" % (len(rv), len(bv), len(ev)))
    for nom, taille, off, _ in ev:
        print("    %-24s %9d o  @ %d" % (nom, taille, off))
    print("mod     : %s" % mod_path)
    print("  fichier %d o | BND4 %d o | %d entrees" % (len(rm), len(bm), len(em)))
    for nom, taille, off, _ in em:
        print("    %-24s %9d o  @ %d" % (nom, taille, off))

    print()
    print("=== comparaison entree par entree ===")
    dv = {n: (t, o, b) for n, t, o, b in ev}
    dm = {n: (t, o, b) for n, t, o, b in em}
    for nom in sorted(set(dv) | set(dm)):
        a = dv.get(nom)
        c = dm.get(nom)
        if a is None:
            print("  %-24s ABSENT de la vanille (mod %d o)" % (nom, c[0]))
        elif c is None:
            print("  %-24s ABSENT du mod (vanille %d o)" % (nom, a[0]))
        elif a[2] == c[2]:
            print("  %-24s IDENTIQUE                 %9d o  sha %s" % (nom, c[0], hashlib.sha256(c[2]).hexdigest()[:16]))
        else:
            print("  %-24s *** DIFFERENT ***        vanille %9d o  mod %9d o" % (nom, a[0], c[0]))
            print("      sha vanille %s" % hashlib.sha256(a[2]).hexdigest()[:16])
            print("      sha mod     %s" % hashlib.sha256(c[2]).hexdigest()[:16])
            n = min(len(a[2]), len(c[2]))
            premiers = [i for i in range(n) if a[2][i] != c[2][i]]
            if premiers:
                print("      premier ecart a l'octet %d (sur %d compares)" % (premiers[0], n))
                i = premiers[0]
                lo = max(0, i - 8)
                print("      vanille : %s" % a[2][lo:i + 8].hex())
                print("      mod     : %s" % c[2][lo:i + 8].hex())
                print("      nb d'octets differents : %d" % len(premiers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
