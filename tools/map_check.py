"""
Diagnostic de la correspondance des os : combien d'os de Simon tombent sur combien
d'os d'Isshin, et sur lesquels.

Usage :
    python tools/map_check.py modele.glb _work/isshin_nodes.tsv
"""

import sys

import bone_map
import simon_export


def main():
    chemin_glb, chemin_tsv = sys.argv[1], sys.argv[2]
    g = simon_export.glb_model.Glb(chemin_glb)
    noms, parent, pos = simon_export.hierarchie_joints(g)
    index_isshin, pos_isshin, parent_isshin = simon_export.charge_os(chemin_tsv)

    mapping, rapport = bone_map.mapper(noms, parent, pos, index_isshin, pos_isshin,
                                       simon_export.rotation_180_y,
                                       parent_isshin=parent_isshin,
                                       os_autorises=simon_export.charge_os_autorises())
    inverse = {}
    for nom, i in index_isshin.items():
        inverse.setdefault(i, nom)

    cibles = {}
    for i, noeud in mapping.items():
        cibles.setdefault(noeud, []).append(noms[i])

    print("os de Simon : %d" % len(noms))
    print("os cibles distincts : %d" % len(cibles))
    print()
    print("=== repartition des cibles ===")
    for noeud, liste in sorted(cibles.items(), key=lambda kv: -len(kv[1])):
        print("  %-18s %4d os  %s" % (inverse.get(noeud, "?"), len(liste),
                                      ", ".join(liste[:4]) + (" ..." if len(liste) > 4 else "")))
    print()
    print("=== os du squelette principal ===")
    for i, nom in enumerate(noms):
        if nom in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "spine_04",
                   "spine_05", "neck_01", "neck_02", "head",
                   "clavicle_l", "upperarm_l", "lowerarm_l",
                   "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
                   "thigh_l", "calf_l", "foot_l", "ball_l",
                   "thigh_r", "calf_r", "foot_r", "ball_r"):
            print("  %-16s -> %-18s (noeud %d)" % (nom, inverse.get(mapping.get(i, -1), "?"),
                                                    mapping.get(i, -1)))


if __name__ == "__main__":
    main()
