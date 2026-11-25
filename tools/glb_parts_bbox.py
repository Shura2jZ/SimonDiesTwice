"""
Boites englobantes par primitive d'un .glb (glTF 2.0 binaire), sans dependance.

But : comparer l'orientation de la tete de Simon dans le fichier source et dans
notre build. On lit les min/max des accesseurs POSITION (obligatoires en glTF)
et on applique la transformation du noeud porteur s'il y en a une.

Usage :
    python tools/glb_parts_bbox.py chemin/vers/modele.glb
"""

import json
import struct
import sys


def lire_glb(chemin):
    with open(chemin, "rb") as fh:
        donnees = fh.read()
    if donnees[:4] != b"glTF":
        raise SystemExit("ce n'est pas un .glb")
    pos = 12
    js = None
    while pos + 8 <= len(donnees):
        longueur, genre = struct.unpack_from("<II", donnees, pos)
        bloc = donnees[pos + 8:pos + 8 + longueur]
        if genre == 0x4E4F534A:      # JSON
            js = json.loads(bloc.decode("utf-8"))
        pos += 8 + longueur
    return js


def mat_identite():
    # glTF : colonnes d'abord
    return [1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0]


def mat_mul(a, b):
    r = [0.0] * 16
    for c in range(4):
        for l in range(4):
            r[c * 4 + l] = sum(a[k * 4 + l] * b[c * 4 + k] for k in range(4))
    return r


def trs_vers_matrice(noeud):
    if "matrix" in noeud:
        return list(noeud["matrix"])
    t = noeud.get("translation", [0.0, 0.0, 0.0])
    q = noeud.get("rotation", [0.0, 0.0, 0.0, 1.0])
    s = noeud.get("scale", [1.0, 1.0, 1.0])
    x, y, z, w = q
    m = [
        1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 0.0,
        2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 0.0,
        2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y), 0.0,
        t[0], t[1], t[2], 1.0,
    ]
    for c in range(3):
        for l in range(3):
            m[c * 4 + l] *= s[c]
    return m


def transformer_point(m, p):
    x, y, z = p
    return (m[0] * x + m[4] * y + m[8] * z + m[12],
            m[1] * x + m[5] * y + m[9] * z + m[13],
            m[2] * x + m[6] * y + m[10] * z + m[14])


def main():
    chemin = sys.argv[1]
    js = lire_glb(chemin)
    acc = js.get("accessors", [])
    mats = js.get("materials", [])
    noeuds = js.get("nodes", [])

    # Une entree par noeud porteur de maillage, avec sa transformation absolue.
    def parcourir(noeud, parent):
        m = mat_mul(parent, trs_vers_matrice(noeud))
        if "mesh" in noeud:
            yield noeud, m
        for e in noeud.get("children", []):
            yield from parcourir(noeuds[e], m)

    racines = set(range(len(noeuds)))
    for n in noeuds:
        for e in n.get("children", []):
            racines.discard(e)

    trouves = []
    for r in sorted(racines):
        for noeud, m in parcourir(noeuds[r], mat_identite()):
            trouve = js["meshes"][noeud["mesh"]]
            for i, prim in enumerate(trouve.get("primitives", [])):
                ia = prim["attributes"].get("POSITION")
                if ia is None:
                    continue
                a = acc[ia]
                if "min" not in a or "max" not in a:
                    continue
                coin = [transformer_point(m, (a["min"][0], a["min"][1], a["min"][2])),
                        transformer_point(m, (a["max"][0], a["min"][1], a["min"][2])),
                        transformer_point(m, (a["min"][0], a["max"][1], a["min"][2])),
                        transformer_point(m, (a["max"][0], a["max"][1], a["min"][2])),
                        transformer_point(m, (a["min"][0], a["min"][1], a["max"][2])),
                        transformer_point(m, (a["max"][0], a["min"][1], a["max"][2])),
                        transformer_point(m, (a["min"][0], a["max"][1], a["max"][2])),
                        transformer_point(m, (a["max"][0], a["max"][1], a["max"][2]))]
                bmin = tuple(min(c[k] for c in coin) for k in range(3))
                bmax = tuple(max(c[k] for c in coin) for k in range(3))
                im = prim.get("material")
                nom = mats[im]["name"] if im is not None and im < len(mats) else "?"
                trouves.append((nom, i, a["count"], bmin, bmax))

    print("fichier : " + chemin)
    print("primitives : " + str(len(trouves)))
    for nom, i, n, bmin, bmax in trouves:
        ctr = tuple((bmin[k] + bmax[k]) / 2 for k in range(3))
        ext = tuple(bmax[k] - bmin[k] for k in range(3))
        print("")
        print("  %-30s prim %d  sommets %d" % (nom, i, n))
        print("    min  : %8.4f %8.4f %8.4f" % bmin)
        print("    max  : %8.4f %8.4f %8.4f" % bmax)
        print("    centre %8.4f %8.4f %8.4f   etendue %6.4f %6.4f %6.4f" % (ctr + ext))

    # Comparaison tete / yeux, si les deux sont la.
    tete = next((t for t in trouves if t[0].lower().endswith("_head")), None)
    yeux = next((t for t in trouves if "blackpart" in t[0].lower()), None)
    if tete and yeux:
        ct = tuple((tete[3][k] + tete[4][k]) / 2 for k in range(3))
        cy = tuple((yeux[3][k] + yeux[4][k]) / 2 for k in range(3))
        haut = tete[4][1] - tete[3][1]
        print("")
        print("  ecart yeux - centre tete : %8.4f %8.4f %8.4f" % tuple(cy[k] - ct[k] for k in range(3)))
        print("  hauteur de la tete       : %8.4f" % haut)
        print("  position verticale relative des yeux : %+.1f %% de la hauteur"
              % (100.0 * (cy[1] - tete[3][1]) / haut))


main()
