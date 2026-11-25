"""
Liste les os d'un squelette .glb, avec leur position dans la pose de reference
et leur parent. Sert aussi a produire la table de correspondance des os.

Usage :
    python tools/simon_bones.py modele.glb [--parents]
"""

import sys

import glb_model
import mat4


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    g = glb_model.Glb(sys.argv[1])
    joints, binds = g.skin(0)
    noms = g.bone_names(joints)

    # parent de chaque os, d'apres la hierarchie des noeuds
    nodes = g.json["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i

    print("os : %d" % len(noms))
    for i, (node_index, nom, mat) in enumerate(zip(joints, noms, binds)):
        pos = mat4.get_translation(mat)
        p = parent.get(node_index)
        pnom = nodes[p].get("name") if p is not None else "-"
        print("%3d  %-28s parent=%-24s %s" % (i, nom, pnom, mat4.fmt(pos)))
    return 0


if __name__ == "__main__":
    main()
