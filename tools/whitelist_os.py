"""
Construit la liste blanche des os d'Isshin sur lesquels on a le DROIT d'accrocher
de la geometrie de corps, a partir du modele vanille.

Principe (mesure, pas supposition) : les maillages RIGIDES du personnage
(casque, cils, ombre des yeux, corps, tete, fourrure) montrent quels os sont
pilotés par l'animation du corps. Les maillages de TISSU (hakama, barbe,
Adjust_cloth) utilisent en plus des os de tissu, pilotés par la simulation CLM2.
Les maillages d'ARME utilisent des os de stockage/arme, teleportes par le
systeme d'equipement. On interdit les deux dernieres classes.

Entree : _work/os_vanille.txt (sortie de FlverOs.exe sur la vanille)
Sortie : _work/os_autorises.txt (indices d'os autorises, un par ligne)
"""
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTREE = os.path.join(RACINE, "_work", "os_vanille.txt")
SORTIE = os.path.join(RACINE, "_work", "os_autorises.txt")

# maillages rigides du personnage (materiaux 0 a 4, 8) :
# casque, cils, ombre des yeux, corps, tete, fourrure.
RIGIDES = {0, 1, 2, 3, 4, 8}
# maillages de tissu du personnage (materiaux 5, 6, 7) et correctifs (21-26)
TISSUS = {5, 6, 7, 21, 22, 23, 24, 25, 26}

LIGNE_MAILLAGE = re.compile(r"^\[\s*(\d+)\]\s+noeud=\s*(\d+)\s+\(([^)]*)\)")
LIGNE_OS = re.compile(r"^\s+(\d+)\s+(\S+)\s+(\d+)\s+sommets")


def main():
    maillage = None
    os_par_maillage = {}
    for ligne in open(ENTREE, encoding="utf-8", errors="replace"):
        m = LIGNE_MAILLAGE.match(ligne)
        if m:
            maillage = int(m.group(1))
            os_par_maillage[maillage] = {}
            continue
        if maillage is None:
            continue
        m = LIGNE_OS.match(ligne)
        if m:
            os_par_maillage[maillage][int(m.group(1))] = m.group(2)
            continue
        if ligne.startswith("==="):
            maillage = None

    if not os_par_maillage:
        raise SystemExit("aucun maillage lu dans " + ENTREE)

    rigide = {}
    tissu = {}
    for mi, table in os_par_maillage.items():
        if mi in RIGIDES:
            for i, nom in table.items():
                rigide[i] = nom
        if mi in TISSUS:
            for i, nom in table.items():
                tissu[i] = nom

    specifiques_tissu = {i: n for i, n in tissu.items() if i not in rigide}

    print("maillages lus : %d" % len(os_par_maillage))
    print("os utilises par les maillages RIGIDES : %d" % len(rigide))
    print("os utilises par les maillages de TISSU : %d" % len(tissu))
    print("os specifiques au TISSU (interdits) : %d" % len(specifiques_tissu))
    print()
    print("=== os specifiques au tissu ===")
    for i in sorted(specifiques_tissu):
        print("  %4d %s" % (i, specifiques_tissu[i]))
    print()
    print("=== tous les os utilises par les maillages rigides (liste blanche) ===")
    for i in sorted(rigide):
        print("  %4d %s" % (i, rigide[i]))

    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write("# os d'Isshin autorises pour de la geometrie de corps (issus des\n")
        f.write("# maillages rigides du personnage) ; genere par tools/whitelist_os.py\n")
        for i in sorted(rigide):
            f.write("%d\t%s\n" % (i, rigide[i]))
    print()
    print("ecrit : " + SORTIE)


if __name__ == "__main__":
    main()
