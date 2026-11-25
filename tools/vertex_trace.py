"""
Trace fine : on prend des sommets du modele de Simon choisis par une region de
l'espace SOURCE, et on affiche ou ils arrivent dans l'espace cible, avec les os
qui les commandent.

Sert a comprendre un membre qui se retrouve au mauvais endroit.

Usage :
    python tools/vertex_trace.py modele.glb _work/isshin_nodes.tsv xmin xmax [ymin ymax]
"""

import sys

import bone_map
import simon_export


def main():
    chemin_glb, chemin_tsv = sys.argv[1], sys.argv[2]
    xmin = float(sys.argv[3]) if len(sys.argv) > 3 else -9
    xmax = float(sys.argv[4]) if len(sys.argv) > 4 else 9
    ymin = float(sys.argv[5]) if len(sys.argv) > 5 else -9
    ymax = float(sys.argv[6]) if len(sys.argv) > 6 else 9

    g = simon_export.glb_model.Glb(chemin_glb)
    noms, parent, pos = simon_export.hierarchie_joints(g)
    index_isshin, pos_isshin, parent_isshin = simon_export.charge_os(chemin_tsv)
    mapping, liste = bone_map.mapper(noms, parent, pos, index_isshin, pos_isshin,
                                     simon_export.rotation_180_y,
                                     parent_isshin=parent_isshin,
                                     os_autorises=simon_export.charge_os_autorises())
    directs = set(i for (i, _, _, meth) in liste
                  if meth.startswith(("squelette", "doigt", "spatial")))
    rotations, translations, _ = simon_export.construit_transformes(
        noms, parent, pos, mapping, directs, index_isshin, pos_isshin)

    compte = {}
    lo = [9e9] * 3
    hi = [-9e9] * 3
    total = 0
    for mesh in g.json["meshes"]:
        for prim in mesh["primitives"]:
            at = prim["attributes"]
            if "POSITION" not in at or "JOINTS_0" not in at:
                continue
            positions = g.accessor(at["POSITION"])
            joints = g.accessor(at["JOINTS_0"])
            poids = g.accessor(at["WEIGHTS_0"])
            for v in range(len(positions)):
                p = positions[v]
                if not (xmin <= p[0] <= xmax and ymin <= p[1] <= ymax):
                    continue
                total += 1
                gardes = sorted(((int(joints[v][k]), float(poids[v][k])) for k in range(4)),
                                key=lambda kv: -kv[1])[:2]
                nom_dom = noms[gardes[0][0]]
                compte[nom_dom] = compte.get(nom_dom, 0) + 1
                acc = [0.0, 0.0, 0.0]
                tot = sum(w for _, w in gardes) or 1.0
                for b, w in gardes:
                    rot, tr = rotations[b], translations[b]
                    q = simon_export.applique3(rot, p)
                    for k in range(3):
                        acc[k] += (w / tot) * (q[k] + tr[k])
                for k in range(3):
                    lo[k] = min(lo[k], acc[k])
                    hi[k] = max(hi[k], acc[k])

    print("sommets dans la region source x[%g;%g] y[%g;%g] : %d" % (xmin, xmax, ymin, ymax, total))
    for nom, n in sorted(compte.items(), key=lambda kv: -kv[1])[:12]:
        print("   os dominant %-24s %6d" % (nom, n))
    if total:
        print("apres transformation : min (%7.3f,%7.3f,%7.3f)  max (%7.3f,%7.3f,%7.3f)"
              % (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


if __name__ == "__main__":
    main()
