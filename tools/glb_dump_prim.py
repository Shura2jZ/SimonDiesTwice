"""
Exporte les positions d'une primitive .glb vers un TSV (index x y z).

Sert a comparer le modele source (GLB exporte par FModel) et notre build FLVER
sommet par sommet : si l'ordre des sommets est conserve, on retrouve la
transformation exacte entre les deux.

Usage :
    python tools/glb_dump_prim.py modele.glb <fragment de materiau> sortie.tsv
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
    bin_ = None
    while pos + 8 <= len(donnees):
        longueur, genre = struct.unpack_from("<II", donnees, pos)
        bloc = donnees[pos + 8:pos + 8 + longueur]
        if genre == 0x4E4F534A:
            js = json.loads(bloc.decode("utf-8"))
        elif genre == 0x004E4942:
            bin_ = bloc
        pos += 8 + longueur
    return js, bin_


TAILLES = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
           5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NCOMPOSANTES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def lire_accesseur(js, bin_, index):
    a = js["accessors"][index]
    bv = js["bufferViews"][a["bufferView"]]
    fmt, taille = TAILLES[a["componentType"]]
    n = NCOMPOSANTES[a["type"]]
    depart = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    pas = bv.get("byteStride", taille * n)
    valeurs = []
    for i in range(a["count"]):
        o = depart + i * pas
        valeurs.append(struct.unpack_from("<" + fmt * n, bin_, o))
    return valeurs


def main():
    chemin, fragment, sortie = sys.argv[1], sys.argv[2], sys.argv[3]
    js, bin_ = lire_glb(chemin)
    mats = js.get("materials", [])

    primitive = None
    for noeud in js["nodes"]:
        if "mesh" not in noeud:
            continue
        for prim in js["meshes"][noeud["mesh"]].get("primitives", []):
            im = prim.get("material")
            nom = mats[im]["name"] if im is not None else ""
            if fragment.lower() in nom.lower():
                primitive = prim
                break
        if primitive:
            break
    if not primitive:
        raise SystemExit("primitive introuvable pour : " + fragment)

    positions = lire_accesseur(js, bin_, primitive["attributes"]["POSITION"])
    with open(sortie, "w", encoding="utf-8") as fh:
        fh.write("# index\tx\ty\tz\n")
        for i, p in enumerate(positions):
            fh.write("%d\t%.6f\t%.6f\t%.6f\n" % (i, p[0], p[1], p[2]))
    print("ecrit : %s  (%d sommets)" % (sortie, len(positions)))


main()
