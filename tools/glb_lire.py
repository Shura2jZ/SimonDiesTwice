"""
Lit un GLB produit par hkx_glb.py (squelette + animation convertis par
havok_toolset.exe) sans dependance externe.

Sous-commandes :
    python tools/glb_lire.py info  <fichier.glb>
    python tools/glb_lire.py noeuds <fichier.glb> [sortie.tsv]
    python tools/glb_lire.py anim  <fichier.glb> [sortie.tsv]

Le format TSV des noeuds : index, parent, nom, lTx, lTy, lTz, lQx, lQy, lQz, lQw, lSx, lSy, lSz
(translation, quaternion et echelle LOCAUX : c'est la pose de reference du
squelette telle que l'a ecrite le convertisseur.)
"""

import json
import struct
import sys

MAGIE_GLB = 0x46546C67
MORCEAU_JSON = 0x4E4F534A
MORCEAU_BIN = 0x004E4942

TAILLE_COMPOSANT = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
FORMAT_COMPOSANT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
LARGEUR_TYPE = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def lire_glb(chemin):
    with open(chemin, "rb") as f:
        data = f.read()
    magie, version, longueur = struct.unpack_from("<III", data, 0)
    if magie != MAGIE_GLB:
        raise ValueError("ce n'est pas un GLB (magie 0x%08X)" % magie)
    if version != 2:
        raise ValueError("version GLB inattendue : %d" % version)
    if longueur != len(data):
        raise ValueError("GLB tronque : annonce %d, fichier %d" % (longueur, len(data)))

    pos = 12
    doc = None
    binaire = b""
    while pos + 8 <= len(data):
        taille, type_morceau = struct.unpack_from("<II", data, pos)
        pos += 8
        morceau = data[pos:pos + taille]
        pos += taille
        if type_morceau == MORCEAU_JSON:
            doc = json.loads(morceau.decode("utf-8"))
        elif type_morceau == MORCEAU_BIN:
            binaire = morceau
    if doc is None:
        raise ValueError("aucun morceau JSON dans le GLB")
    return doc, binaire


def lire_accesseur(doc, binaire, index):
    """Retourne une liste de tuples de flottants."""
    acc = doc["accessors"][index]
    if "sparse" in acc:
        raise ValueError("accesseur creux non gere")
    vue = doc["bufferViews"][acc["bufferView"]]
    if vue.get("buffer", 0) != 0:
        raise ValueError("tampon autre que 0 non gere")

    type_comp = acc["componentType"]
    taille = TAILLE_COMPOSANT[type_comp]
    fmt = FORMAT_COMPOSANT[type_comp]
    largeur = LARGEUR_TYPE[acc["type"]]
    normalise = bool(acc.get("normalized", False))

    depart = vue.get("byteOffset", 0) + acc.get("byteOffset", 0)
    pas = vue.get("byteStride") or (taille * largeur)
    valeurs = []
    for i in range(acc["count"]):
        base = depart + i * pas
        ligne = []
        for k in range(largeur):
            brut = struct.unpack_from("<" + fmt, binaire, base + k * taille)[0]
            if normalise:
                if type_comp == 5120:
                    brut = max(-1.0, brut / 127.0)
                elif type_comp == 5121:
                    brut = brut / 255.0
                elif type_comp == 5122:
                    brut = max(-1.0, brut / 32767.0)
                elif type_comp == 5123:
                    brut = brut / 65535.0
            ligne.append(float(brut))
        valeurs.append(tuple(ligne))
    return valeurs


def noeuds(doc):
    """Retourne la liste (index, parent, nom, translation, rotation, echelle)."""
    brut = doc.get("nodes") or []
    parents = [-1] * len(brut)
    for i, n in enumerate(brut):
        for enfant in n.get("children", []):
            parents[enfant] = i
    res = []
    for i, n in enumerate(brut):
        t = tuple(n.get("translation", [0.0, 0.0, 0.0]))
        q = tuple(n.get("rotation", [0.0, 0.0, 0.0, 1.0]))
        s = tuple(n.get("scale", [1.0, 1.0, 1.0]))
        res.append((i, parents[i], n.get("name", ""), t, q, s))
    return res


def cmd_info(chemin):
    doc, binaire = lire_glb(chemin)
    ns = noeuds(doc)
    print("fichier : %s" % chemin)
    print("generateur : %s" % (doc.get("asset", {}).get("generator", "?")))
    print("noeuds : %d" % len(ns))
    print("animations : %d" % len(doc.get("animations", [])))
    print("maillages : %d" % len(doc.get("meshes", [])))
    print("peaux : %d" % len(doc.get("skins", [])))
    for i, anim in enumerate(doc.get("animations", [])):
        pistes = {}
        tmax = 0.0
        for ch in anim.get("channels", []):
            voie = ch["target"]["path"]
            pistes[voie] = pistes.get(voie, 0) + 1
            acc = doc["accessors"][anim["samplers"][ch["sampler"]]["input"]]
            if "max" in acc:
                tmax = max(tmax, acc["max"][0])
        print("  animation %d : %s  pistes %s  duree %.4f s"
              % (i, anim.get("name", "?"), pistes, tmax))
    print()
    print("premiers noeuds :")
    for i, parent, nom, t, q, s in ns[:25]:
        print("  [%3d] parent %3d  %-28s T(%8.4f %8.4f %8.4f)  Q(%7.4f %7.4f %7.4f %7.4f)  S(%6.3f %6.3f %6.3f)"
              % (i, parent, nom, t[0], t[1], t[2], q[0], q[1], q[2], q[3], s[0], s[1], s[2]))


def cmd_noeuds(chemin, sortie=None):
    doc, _ = lire_glb(chemin)
    lignes = ["\t".join(["index", "parent", "nom", "lTx", "lTy", "lTz",
                         "lQx", "lQy", "lQz", "lQw", "lSx", "lSy", "lSz"])]
    for i, parent, nom, t, q, s in noeuds(doc):
        lignes.append("\t".join([str(i), str(parent), nom]
                                + ["%.6f" % v for v in t] + ["%.6f" % v for v in q]
                                + ["%.6f" % v for v in s]))
    texte = "\n".join(lignes)
    if sortie:
        with open(sortie, "w", encoding="utf-8") as f:
            f.write(texte)
        print("ecrit : %s (%d noeuds)" % (sortie, len(lignes) - 1))
    else:
        print(texte)


def cmd_anim(chemin, sortie=None):
    doc, binaire = lire_glb(chemin)
    ns = noeuds(doc)
    noms = {i: nom for i, _, nom, _, _, _ in ns}
    lignes = ["\t".join(["animation", "noeud", "nom", "voie", "cles", "t_min", "t_max"])]
    for ia, anim in enumerate(doc.get("animations", [])):
        for ch in anim.get("channels", []):
            cible = ch["target"]["node"]
            voie = ch["target"]["path"]
            ech = anim["samplers"][ch["sampler"]]
            temps = lire_accesseur(doc, binaire, ech["input"])
            lignes.append("\t".join([str(ia), str(cible), noms.get(cible, ""), voie,
                                     str(len(temps)),
                                     "%.4f" % temps[0][0] if temps else "?",
                                     "%.4f" % temps[-1][0] if temps else "?"]))
    texte = "\n".join(lignes)
    if sortie:
        with open(sortie, "w", encoding="utf-8") as f:
            f.write(texte)
        print("ecrit : %s (%d pistes)" % (sortie, len(lignes) - 1))
    else:
        print(texte)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    commande, chemin = sys.argv[1], sys.argv[2]
    sortie = sys.argv[3] if len(sys.argv) > 3 else None
    if commande == "info":
        cmd_info(chemin)
    elif commande == "noeuds":
        cmd_noeuds(chemin, sortie)
    elif commande == "anim":
        cmd_anim(chemin, sortie)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
