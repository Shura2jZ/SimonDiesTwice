"""
Lecture d'une animation USD ASCII (.usda) exportee par FModel.

Le fichier contient (entre autres) :

    uniform token[] joints = [ "root/Pelvis/...", ... ]
    uniform matrix4d[] restTransforms = [ ((...),(...),(...),(...)), ... ]
    float3[] translations.timeSamples = { <image>: [ (x,y,z), ... ], ... }
    quatf[]  rotations.timeSamples    = { <image>: [ (x,y,z,w), ... ], ... }
    half3[]  scales.timeSamples       = { <image>: [ (x,y,z), ... ], ... }

Chaque image liste une valeur par os, dans l'ordre du tableau `joints`.
Les matrices sont en lignes (translation = 4e ligne), en centimetres, Z vers le
haut (metersPerUnit = 0.01, upAxis = "Z").

    python -u tools/usda_anim.py <fichier.usda> [sortie.anim]

Format de sortie (.anim), sans dependance externe :
    ligne 1 : JSON {"os": [...], "images": [...], "nb_os": N, "nb_images": F}
    puis, en float32 little-endian :
        par image : temps, translations (3N), rotations (4N) [x,y,z,w], echelles (3N)
        enfin    : repos quaternions (4N), repos translations (3N)
"""

import array
import json
import re
import sys

RE_IMAGE = re.compile(r"^\s*(-?[0-9.]+)\s*:\s*\[(.*)\]\s*,?\s*$")
RE_TUPLE = re.compile(r"\(([^()]*)\)")


def bloc_accolades(texte, marqueur):
    i = texte.index(marqueur)
    j = texte.index("{", i)
    fin = re.compile(r"\n\s*\}").search(texte, j)
    return texte[j + 1:fin.start()]


def bloc_crochets(texte, marqueur):
    """Contenu entre crochets qui suivent `marqueur` (aucun crochet a l'interieur)."""
    i = texte.index(marqueur)
    j = texte.index("[", i)
    fin = texte.index("]", j)
    return texte[j + 1:fin]


def quaternion(m):
    """Quaternion (x, y, z, w) d'une matrice 3x3 donnee en lignes.

    L'USD ecrit les matrices en convention ligne (la translation est la 4e
    ligne) : la partie rotation est donc la transposee de la matrice usuelle.
    """
    m = [[m[j][i] for j in range(3)] for i in range(3)]
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0.0:
        s = (trace + 1.0) ** 0.5 * 2.0
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = (1.0 + m[0][0] - m[1][1] - m[2][2]) ** 0.5 * 2.0
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = (1.0 + m[1][1] - m[0][0] - m[2][2]) ** 0.5 * 2.0
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = (1.0 + m[2][2] - m[0][0] - m[1][1]) ** 0.5 * 2.0
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s
    return [x, y, z, w]


def lire_images(texte, marqueur, dimension):
    contenu = bloc_accolades(texte, marqueur)
    temps, valeurs = [], []
    for ligne in contenu.split("\n"):
        m = RE_IMAGE.match(ligne)
        if not m:
            continue
        temps.append(float(m.group(1)))
        for t in RE_TUPLE.findall(m.group(2)):
            morceaux = t.split(",")
            if len(morceaux) != dimension:
                raise SystemExit("dimension inattendue : %s" % t)
            valeurs.extend(float(v) for v in morceaux)
    return temps, valeurs


def lire_repos(texte, nb_os):
    contenu = bloc_crochets(texte, "restTransforms = [")
    tuples = RE_TUPLE.findall(contenu)
    if len(tuples) != nb_os * 4:
        raise SystemExit("restTransforms : %d tuples pour %d os" % (len(tuples), nb_os))
    quats, translations = [], []
    for i in range(nb_os):
        lignes = []
        for r in range(4):
            valeurs = [float(v) for v in tuples[i * 4 + r].split(",")]
            lignes.append(valeurs)
        quats.extend(quaternion(lignes))
        translations.extend(lignes[3][:3])
    return quats, translations


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    chemin = sys.argv[1]
    sortie = sys.argv[2] if len(sys.argv) > 2 else None

    with open(chemin, "r", encoding="utf-8", errors="replace") as fh:
        texte = fh.read()

    os_noms = [c.split("/")[-1]
               for c in re.findall(r'"([^"]*)"', bloc_crochets(texte, "joints = ["))]
    chemins = re.findall(r'"([^"]*)"', bloc_crochets(texte, "joints = ["))
    nb_os = len(os_noms)
    print("os : %d" % nb_os)

    temps_t, translations = lire_images(texte, "translations.timeSamples = {", 3)
    temps_r, rotations = lire_images(texte, "rotations.timeSamples = {", 4)
    temps_s, scales = lire_images(texte, "scales.timeSamples = {", 3)

    nb_images = len(temps_t)
    print("images : %d (de %g a %g)" % (nb_images, temps_t[0], temps_t[-1]))
    for nom, liste, dim in (("translations", translations, 3),
                            ("rotations", rotations, 4),
                            ("scales", scales, 3)):
        attendu = nb_images * nb_os * dim
        etat = "ok" if len(liste) == attendu else "INCOHERENT"
        print("  %-12s %d valeurs (attendu %d) %s" % (nom, len(liste), attendu, etat))
        if len(liste) != attendu:
            raise SystemExit("taille incoherente pour %s" % nom)

    repos_q, repos_t = lire_repos(texte, nb_os)
    print("repos : %d quaternions, %d translations" % (len(repos_q) // 4, len(repos_t) // 3))

    for i in range(3):
        t = translations[i * 3:(i + 1) * 3]
        r = rotations[i * 4:(i + 1) * 4]
        rq = repos_q[i * 4:(i + 1) * 4]
        rt = repos_t[i * 3:(i + 1) * 3]
        print("  os %2d %-18s anim t = %s q = %s | repos t = %s q = %s"
              % (i, os_noms[i], [round(v, 3) for v in t], [round(v, 3) for v in r],
                 [round(v, 3) for v in rt], [round(v, 3) for v in rq]))

    if sortie:
        with open(sortie, "wb") as fh:
            entete = {"os": os_noms, "chemins": chemins, "images": temps_t,
                      "nb_os": nb_os, "nb_images": nb_images}
            fh.write((json.dumps(entete) + "\n").encode("utf-8"))
            paquet = array.array("f")
            for k in range(nb_images):
                paquet.append(temps_t[k])
                paquet.extend(translations[k * nb_os * 3:(k + 1) * nb_os * 3])
                paquet.extend(rotations[k * nb_os * 4:(k + 1) * nb_os * 4])
                paquet.extend(scales[k * nb_os * 3:(k + 1) * nb_os * 3])
            paquet.extend(repos_q)
            paquet.extend(repos_t)
            if sys.byteorder != "little":
                paquet.byteswap()
            fh.write(paquet.tobytes())
        print("ecrit : %s" % sortie)


if __name__ == "__main__":
    main()
