"""
Comparaison des poses de reference, os par os : position chez Simon, os cible
chez Isshin, position de la cible, distance entre les deux.

Sert a comprendre les deplacements calcules par simon_export.py.

Usage :
    python tools/pose_check.py modele.glb _work/isshin_nodes.tsv [motif]
"""

import sys

import bone_map
import simon_export


def main():
    chemin_glb, chemin_tsv = sys.argv[1], sys.argv[2]
    motif = sys.argv[3].lower() if len(sys.argv) > 3 else ""
    g = simon_export.glb_model.Glb(chemin_glb)
    noms, parent, pos = simon_export.hierarchie_joints(g)
    index_isshin, pos_isshin, parent_isshin = simon_export.charge_os(chemin_tsv)
    inverse = {}
    for nom, i in index_isshin.items():
        inverse.setdefault(i, nom)

    mapping, rapport = bone_map.mapper(noms, parent, pos, index_isshin, pos_isshin,
                                       simon_export.rotation_180_y,
                                       parent_isshin=parent_isshin,
                                       os_autorises=simon_export.charge_os_autorises())
    directs = set(i for (i, _, _, meth) in rapport
                  if meth.startswith("squelette") or meth.startswith("doigt"))

    print("%-24s %-28s %-24s %-28s %8s" % ("os Simon", "position Simon", "os cible",
                                           "position Isshin", "distance"))
    for i, nom in enumerate(noms):
        if motif and motif not in nom.lower():
            continue
        if i not in directs:
            continue
        m = mapping[i]
        ps, pt = pos[i], pos_isshin[m]
        d = sum((ps[k] - pt[k]) ** 2 for k in range(3)) ** 0.5
        print("%-24s (%7.3f,%7.3f,%7.3f) %-24s (%7.3f,%7.3f,%7.3f) %8.3f"
              % (nom, ps[0], ps[1], ps[2], inverse.get(m, "?"), pt[0], pt[1], pt[2], d))

    print()
    print("--- parent de chaque os direct (pour comprendre les directions) ---")
    for i, nom in enumerate(noms):
        if i not in directs or (motif and motif not in nom.lower()):
            continue
        p = parent[i]
        pm = mapping.get(p)
        print("  %-24s parent=%-22s -> cible parent=%-18s" %
              (nom, noms[p] if p >= 0 else "(racine)", inverse.get(pm, "?") if pm is not None else "?"))


if __name__ == "__main__":
    main()
