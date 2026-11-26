"""
Controle du fichier intermediaire : ou chaque morceau du corps a-t-il ete pose ?

Pour chaque os, on regroupe les sommets dont c'est l'os dominant et on affiche
l'etendue de ce groupe. Cela permet de verifier, sans se fier a un rendu, que
chaque membre est bien alle du bon cote.

Repere FLVER : X vers la droite, Y vers le haut, -Z vers l'avant du personnage
(Isshin regarde -Z). Vue de face = camera en -Z ; dans cette vue, le +X apparait
a GAUCHE de l'ecran.

Usage :
    python tools/inter_check.py fichier.bin
"""

import struct
import sys

TYPES = ("Master", "Root", "Pelvis", "Spine", "Spine1", "Spine2", "Neck", "Head")
INTERET = ("_Hand", "_Forearm", "_UpperArm", "_Finger", "_Finger0", "_Finger4",
           "L_Toe0", "R_Toe0", "_Foot")


def lire(chemin):
    f = open(chemin, "rb")
    if not f.read(8).startswith(b"SMPORT"):
        raise SystemExit("fichier inattendu")
    nb_maillages = struct.unpack("<I", f.read(4))[0]
    axe = struct.unpack("<9f", f.read(36))
    nb_os = struct.unpack("<I", f.read(4))[0]
    os = {}
    for _ in range(nb_os):
        n = struct.unpack("<I", f.read(4))[0]
        nom = f.read(n).decode("utf-8")
        noeud = struct.unpack("<i", f.read(4))[0]
        os.setdefault(noeud, []).append(nom)

    maillages = []
    for _ in range(nb_maillages):
        n = struct.unpack("<I", f.read(4))[0]
        nom = f.read(n).decode("utf-8")
        materiau, noeud, gabarit = struct.unpack("<iii", f.read(12))
        nb_sommets, nb_indices = struct.unpack("<II", f.read(8))
        liste = []
        for _ in range(nb_sommets):
            v = struct.unpack_from("<3f3f4f2f4f4i4f", f.read(96))
            liste.append((v[0], v[1], v[2], v[16], v[17], v[18], v[19],
                          v[20], v[21], v[22], v[23]))
        f.read(nb_indices * 4)
        maillages.append((nom, materiau, noeud, liste))
    return axe, os, maillages


def charge_os_isshin(tsv):
    """Table nom -> index de noeud et index -> nom, depuis l'export d'Isshin."""
    index, inverse = {}, {}
    for ligne in open(tsv, encoding="utf-8").read().splitlines()[1:]:
        c = ligne.split("\t")
        if len(c) < 29:
            continue
        i = int(c[0])
        index[c[3]] = i
        inverse[i] = c[3]
    return index, inverse


def analyse(chemin, chemin_tsv):
    axe, os, maillages = lire(chemin)
    _, nom_isshin = charge_os_isshin(chemin_tsv)
    print("axe : [%s]" % " ".join("%.0f" % v for v in axe))
    print("maillages : %d, os cibles distincts : %d" % (len(maillages), len(os)))
    print()
    print("=== os de Simon par cible d'Isshin ===")
    for noeud, liste in sorted(os.items(), key=lambda kv: -len(kv[1])):
        print("  %-18s %4d  %s" % (nom_isshin.get(noeud, "?"), len(liste),
                                    ", ".join(sorted(liste)[:3]) + (" ..." if len(liste) > 3 else "")))
    print()

    groupes = {}
    for nom, materiau, noeud, liste in maillages:
        for v in liste:
            idx = (v[3], v[4], v[5], v[6])
            poids = (v[7], v[8], v[9], v[10])
            meilleur = 0
            for j in (1, 2, 3):
                if poids[j] > poids[meilleur]:
                    meilleur = j
            k = idx[meilleur]
            g = groupes.get(k)
            if g is None:
                g = groupes[k] = [v[0], v[1], v[2], v[0], v[1], v[2], 0]
            g[0] = min(g[0], v[0]); g[1] = min(g[1], v[1]); g[2] = min(g[2], v[2])
            g[3] = max(g[3], v[0]); g[4] = max(g[4], v[1]); g[5] = max(g[5], v[2])
            g[6] += 1

    print("%-22s %8s   %-24s %-24s" % ("os dominant", "sommets", "minimum", "maximum"))
    for k in sorted(groupes, key=lambda k: -groupes[k][6]):
        nom = nom_isshin.get(k, "?")
        g = groupes[k]
        print("%-22s %8d   (%7.3f,%7.3f,%7.3f)  (%7.3f,%7.3f,%7.3f)"
              % (nom, g[6], g[0], g[1], g[2], g[3], g[4], g[5]))

    print()
    print("=== cote des reperes (+X = gauche de l'ecran en vue de face) ===")
    for nom_b in ("L_Hand", "R_Hand", "L_Forearm", "R_Forearm", "Head",
                  "L_Foot", "R_Foot", "L_Finger0", "L_Finger4", "L_Toe0", "R_Toe0"):
        for k, g in groupes.items():
            if nom_isshin.get(k) != nom_b:
                continue
            cx = (g[0] + g[3]) / 2.0
            cy = (g[1] + g[4]) / 2.0
            cz = (g[2] + g[5]) / 2.0
            print("  %-14s %6d sommets  centre=(%6.3f, %6.3f, %6.3f)  X%s"
                  % (nom_b, g[6], cx, cy, cz, "+" if cx > 0 else "-"))
            break


if __name__ == "__main__":
    analyse(sys.argv[1] if len(sys.argv) > 1 else "_work/simon_inter.bin",
            sys.argv[2] if len(sys.argv) > 2 else "_work/isshin_nodes.tsv")
