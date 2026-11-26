"""
Pose le champ d'en-tete FLVER 0x40 ("nombre de faces hors maillages de motion
blur et faces degenerees") a une valeur donnee, sans rien d'autre modifier.

Pourquoi : SoulsFormats ecrit 0x40 == 0x44 (total des faces) pour les facesets
en liste de triangles, alors que la vanille y met la somme des faces des
facesets qui NE portent PAS le drapeau MotionBlur (0x80000000).
Mesure sur la vanille de c5400 : 0x40 = 262 326 = faces hors MotionBlur,
0x44 = 562 486 = total (outil FlverFacesets).

Usage :
    python tools/flver_040.py <fichier.flver> <valeur> [<sortie.flver>]

Si <sortie.flver> est omis, la modification est faite sur place (copie de
securite .avant_040 ecrite a cote).
"""
import os
import shutil
import struct
import sys

OFFSET_040 = 0x40


def lire_champ(chemin):
    with open(chemin, "rb") as f:
        f.seek(OFFSET_040)
        return struct.unpack("<i", f.read(4))[0]


def ecrire_champ(chemin, valeur):
    with open(chemin, "r+b") as f:
        f.seek(OFFSET_040)
        f.write(struct.pack("<i", valeur))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    entree = sys.argv[1]
    valeur = int(sys.argv[2], 0)
    sortie = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.isfile(entree):
        print("introuvable : %s" % entree)
        return 2

    avant = lire_champ(entree)
    print("fichier        : %s" % entree)
    print("0x40 avant     : %d" % avant)

    if sortie:
        shutil.copyfile(entree, sortie)
        cible = sortie
        print("copie          : %s" % sortie)
    else:
        cible = entree
        sauvegarde = entree + ".avant_040"
        if not os.path.exists(sauvegarde):
            shutil.copyfile(entree, sauvegarde)
            print("sauvegarde     : %s" % sauvegarde)

    ecrire_champ(cible, valeur)
    apres = lire_champ(cible)
    print("0x40 apres     : %d" % apres)
    print("identique a la valeur demandee : %s" % (apres == valeur))
    print("taille         : %d octets (inchangee : %s)"
          % (os.path.getsize(cible), os.path.getsize(cible) == os.path.getsize(entree)))
    return 0 if apres == valeur else 1


if __name__ == "__main__":
    sys.exit(main())
