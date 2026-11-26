"""
Compare, entree par entree, le BND4 installe et le BND4 vanille.

But : voir exactement quelles entrees different (FLVER oui, mais aussi TPF,
HKX, CLM2, anibnd...). Une entree abimee autre que le FLVER serait une piste
directe (textures dans la figure, geometrie absente...).

Aucune ecriture dans les dossiers de jeu.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil
import bnd4_build

VAN = r"E:\Games\Sekiro - Shadows Die Twice\chr\c5400.chrbnd.dcx"
NOT = r"E:\Games\Sekiro - Shadows Die Twice\mods\chr\c5400.chrbnd.dcx"


def entrees(dcx):
    brut = soulsutil.load(dcx)
    fc, eo, es, do, ents = bnd4_build.list_entries(brut)
    out = []
    for e in ents:
        blob = brut[e["offset"]:e["offset"] + e["size"]]
        out.append((bnd4_build.basename_of(e["fullname"]), blob))
    return brut, out


def main():
    for p in (VAN, NOT):
        print("%s : %s" % (p, "present" if os.path.exists(p) else "ABSENT"))
        if os.path.exists(p):
            print("   md5 %s  taille %d" % (hashlib.md5(open(p, "rb").read()).hexdigest(),
                                            os.path.getsize(p)))
    print()
    if not os.path.exists(NOT):
        return
    rv, ev = entrees(VAN)
    rn, en = entrees(NOT)
    print("BND4 vanille  : %d octets, %d entrees" % (len(rv), len(ev)))
    print("BND4 installe : %d octets, %d entrees" % (len(rn), len(en)))
    print()

    dv = dict(ev)
    dn = dict(en)
    noms = sorted(set(dv) | set(dn))
    print("%-28s %10s %10s  %s" % ("entree", "vanille", "installe", "etat"))
    for n in noms:
        a = dv.get(n)
        b = dn.get(n)
        if a is None:
            print("%-28s %10s %10d  ABSENTE DE LA VANILLE" % (n, "-", len(b)))
            continue
        if b is None:
            print("%-28s %10d %10s  ABSENTE DE L'INSTALLE" % (n, len(a), "-"))
            continue
        if a == b:
            etat = "identique"
        else:
            diff = sum(1 for i in range(min(len(a), len(b))) if a[i] != b[i])
            etat = "DIFFERENT (%d octets diff, delta taille %+d)" % (diff, len(b) - len(a))
        print("%-28s %10d %10d  %s" % (n, len(a), len(b), etat))


if __name__ == "__main__":
    main()
