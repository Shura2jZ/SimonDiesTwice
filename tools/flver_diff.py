"""
Compare deux dumps produits par FlverDump.exe, section par section.

Affiche uniquement ce qui differe : en-tete, comptes, agencements de sommets,
materiaux, listes de commandes, dummies, os, squelettes. La section des
maillages est traitee a part (le nombre de maillages differe forcement).

Usage :
    python tools/flver_diff.py <dumpA.txt> <dumpB.txt>
"""

import sys


def lire(chemin):
    sections = {}
    courante = None
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.rstrip("\n")
            if ligne.startswith("## "):
                courante = ligne[3:].strip()
                sections[courante] = []
            elif courante is not None:
                sections[courante].append(ligne)
    return sections


def diff_lignes(nom, a, b, limite=25):
    print("--- %s : %d lignes contre %d" % (nom, len(a), len(b)))
    n = 0
    for i in range(max(len(a), len(b))):
        la = a[i] if i < len(a) else "(absent)"
        lb = b[i] if i < len(b) else "(absent)"
        if la != lb:
            n += 1
            if n <= limite:
                print("    [%d] A: %s" % (i, la))
                print("        B: %s" % lb)
    if n == 0:
        print("    identique")
    elif n > limite:
        print("    ... %d differences au total" % n)


def diff_entete(a, b):
    print("--- en-tete et comptes")
    da, db = {}, {}
    for section in ("en-tete", "compte"):
        for l in a.get(section, []):
            if " = " in l:
                k, v = l.split(" = ", 1)
                da[k] = v
        for l in b.get(section, []):
            if " = " in l:
                k, v = l.split(" = ", 1)
                db[k] = v
    for k in sorted(set(da) | set(db)):
        va, vb = da.get(k, "(absent)"), db.get(k, "(absent)")
        if va != vb:
            print("    %-28s A: %-24s B: %s" % (k, va, vb))
    if all(da.get(k) == db.get(k) for k in set(da) | set(db)):
        print("    identique")


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    a = lire(sys.argv[1])
    b = lire(sys.argv[2])
    print("A = %s" % sys.argv[1])
    print("B = %s" % sys.argv[2])
    print()

    ordre = ["en-tete", "compte", "agencements de sommets", "materiaux",
             "listes de commandes graphiques", "dummies", "os (noms, parents, drapeaux)",
             "squelettes"]
    diff_entete(a, b)
    for nom in ordre[2:]:
        diff_lignes(nom, a.get(nom, []), b.get(nom, []))

    print()
    print("--- maillages")
    ma = [l for l in a.get("maillages", []) if l.startswith("maillage[") and ".faceset" not in l and ".tampon" not in l]
    mb = [l for l in b.get("maillages", []) if l.startswith("maillage[") and ".faceset" not in l and ".tampon" not in l]
    print("    A : %d maillages" % len(ma))
    for l in ma:
        print("      " + l)
    print("    B : %d maillages" % len(mb))
    for l in mb:
        print("      " + l)


if __name__ == "__main__":
    main()
