"""
Pose des os d'un GLB produit par hkx_glb.py.

Calcule les matrices monde des noeuds, soit a la pose de reference (les TRS
des noeuds du GLB, qui viennent du squelette HKX), soit a un instant donne
d'une animation.

Sous-commandes :
    python tools/hkx_pose.py comparer <glb> <isshin_nodes.tsv>
        Compare, os par os, la position monde de la pose de reference du HKX
        avec celle des noeuds du FLVER (colonne g13,g14,g15 du TSV).

    python tools/hkx_pose.py positions <glb> <temps_s> <isshin_nodes.tsv>
        Meme comparaison, mais avec l'animation echantillonnee a l'instant
        demande (0 = debut).

    python tools/hkx_pose.py oracle <glb_animation> <tsv_flver> <temps_s> <sortie.tsv>
        Ecrit, pour chaque os, sa matrice monde d'animation exprimee dans le
        repere du FLVER. C'est l'entree de FlverDeforme.exe.

Conventions
-----------
Les matrices internes de ce module sont en convention COLONNE (comme glTF :
le point est un vecteur colonne, la translation est dans la 4e colonne).

Le FLVER et le System.Numerics de .NET utilisent la convention LIGNE (le point
est un vecteur ligne, la translation est dans la 4e ligne) : on transpose donc
a l'ecriture du TSV.

Reperes : HavokToolset applique un changement de base (rotation de 180 degres
autour de X, plus la translation d'offset de la racine) au noeud racine de sa
sortie "squelette". Ses PISTES d'animation, elles, sont deja dans les reperes
locaux du FLVER : verifie os par os, 187 os sur 198 ont un local identique et
la racine animee a t=0 vaut +88,9 degres autour de Y contre +90 degres pour le
noeud Master du FLVER. Les 11 os d'ecart sont les os de tissu (jupes, armures),
un oeil et les cibles de pied, dont le repos dans le FLVER n'est pas significatif
(ils sont pilotes par CLM2 et par la cinématique inverse).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb_lire


def identite():
    return [[1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def multiplier(a, b):
    """Produit matriciel en convention colonne : (a*b) applique b puis a."""
    r = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            s = 0.0
            for k in range(4):
                s += a[i][k] * b[k][j]
            r[i][j] = s
    return r


def transposer(m):
    return [[m[j][i] for j in range(4)] for i in range(4)]


def inverser(m):
    """Inversion 4x4 par Gauss-Jordan (matrices rigides ou legerement mises a l'echelle)."""
    a = [list(m[i]) + [1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("matrice singuliere")
        a[col], a[pivot] = a[pivot], a[col]
        p = a[col][col]
        a[col] = [v / p for v in a[col]]
        for r in range(4):
            if r == col:
                continue
            f = a[r][col]
            if f != 0.0:
                a[r] = [a[r][k] - f * a[col][k] for k in range(8)]
    return [row[4:] for row in a]


def quaternion_vers_matrice(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n == 0.0:
        return identite()
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0.0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0.0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def locale(t, q, s):
    """M = T * R * S (convention colonne : l'echelle, puis la rotation, puis la translation)."""
    m = quaternion_vers_matrice(q)
    for i in range(3):
        for j in range(3):
            m[i][j] *= s[j]
        m[i][3] = t[i]
    return m


def hierarchie(doc):
    brut = doc.get("nodes") or []
    parents = [-1] * len(brut)
    for i, n in enumerate(brut):
        for enfant in n.get("children", []):
            parents[enfant] = i
    return parents


def valeurs_a_instant(doc, binaire, secondes):
    """Retourne les TRS locaux apres application des pistes d'animation."""
    brut = doc.get("nodes") or []
    t = [list(n.get("translation", [0.0, 0.0, 0.0])) for n in brut]
    q = [list(n.get("rotation", [0.0, 0.0, 0.0, 1.0])) for n in brut]
    s = [list(n.get("scale", [1.0, 1.0, 1.0])) for n in brut]

    for anim in doc.get("animations", []):
        for ch in anim.get("channels", []):
            cible = ch["target"]["node"]
            voie = ch["target"]["path"]
            ech = anim["samplers"][ch["sampler"]]
            temps = [v[0] for v in glb_lire.lire_accesseur(doc, binaire, ech["input"])]
            vals = glb_lire.lire_accesseur(doc, binaire, ech["output"])
            if not temps:
                continue
            if secondes <= temps[0]:
                i, alpha = 0, 0.0
            elif secondes >= temps[-1]:
                i, alpha = (len(temps) - 2 if len(temps) > 1 else 0), 1.0
            else:
                i = 0
                while i + 1 < len(temps) and temps[i + 1] < secondes:
                    i += 1
                alpha = (secondes - temps[i]) / (temps[i + 1] - temps[i])
            a = vals[i]
            b = vals[i + 1] if i + 1 < len(vals) else vals[i]
            if voie == "rotation":
                melange = [a[k] * (1 - alpha) + b[k] * alpha for k in range(4)]
                n = math.sqrt(sum(v * v for v in melange)) or 1.0
                q[cible] = [v / n for v in melange]
            elif voie == "translation":
                t[cible] = [a[k] * (1 - alpha) + b[k] * alpha for k in range(3)]
            elif voie == "scale":
                s[cible] = [a[k] * (1 - alpha) + b[k] * alpha for k in range(3)]
    return t, q, s


def matrices_monde(doc, binaire=None, secondes=None):
    """Matrices monde (convention colonne) de tous les noeuds du GLB."""
    parents = hierarchie(doc)
    if secondes is None:
        t = [list(n.get("translation", [0.0, 0.0, 0.0])) for n in doc["nodes"]]
        q = [list(n.get("rotation", [0.0, 0.0, 0.0, 1.0])) for n in doc["nodes"]]
        s = [list(n.get("scale", [1.0, 1.0, 1.0])) for n in doc["nodes"]]
    else:
        t, q, s = valeurs_a_instant(doc, binaire, secondes)

    n = len(parents)
    locales = [locale(t[i], q[i], s[i]) for i in range(n)]
    monde = [None] * n
    etat = [0] * n

    def resoudre(i):
        if etat[i] == 2:
            return
        if etat[i] == 1:
            raise ValueError("cycle dans le squelette")
        etat[i] = 1
        p = parents[i]
        if p >= 0:
            resoudre(p)
            monde[i] = multiplier(monde[p], locales[i])
        else:
            monde[i] = locales[i]
        etat[i] = 2

    for i in range(n):
        resoudre(i)
    return monde, parents


def lire_tsv(chemin):
    """Retourne {nom: (index, parent, position_monde, matrice_colonne)}.

    Le TSV contient la matrice globale en convention ligne, ligne par ligne :
    la translation est donc aux colonnes g13,g14,g15.
    """
    res = {}
    with open(chemin, "r", encoding="utf-8") as f:
        entete = f.readline()
        colonnes = entete.rstrip("\n").split("\t")
        for ligne in f:
            c = ligne.rstrip("\n").split("\t")
            if len(c) < len(colonnes):
                continue
            nom = c[3]
            brut = [float(c[13 + k]) for k in range(16)]
            ligne_maj = [[brut[i * 4 + j] for j in range(4)] for i in range(4)]
            res[nom] = (
                int(c[0]), int(c[1]),
                (ligne_maj[3][0], ligne_maj[3][1], ligne_maj[3][2]),
                transposer(ligne_maj),
            )
    return res


def noms(doc):
    return [n.get("name", "") for n in doc["nodes"]]


def comparer(glb, tsv, secondes=None):
    doc, binaire = glb_lire.lire_glb(glb)
    monde, parents = matrices_monde(doc, binaire, secondes)
    os_flver = lire_tsv(tsv)
    noms_glb = noms(doc)

    print("noeuds GLB : %d   os FLVER : %d   noms communs : %d"
          % (len(noms_glb), len(os_flver), len([n for n in noms_glb if n in os_flver])))
    if secondes is not None:
        print("animation echantillonnee a t = %.4f s" % secondes)
    print()

    ecarts = []
    for i, nom in enumerate(noms_glb):
        if nom not in os_flver:
            continue
        m = monde[i]
        p_glb = (m[0][3], m[1][3], m[2][3])
        p_flver = os_flver[nom][2]
        ecarts.append((math.dist(p_glb, p_flver), nom, p_glb, p_flver, i))

    ecarts.sort(reverse=True)
    print("=== les 15 plus gros ecarts de position monde ===")
    for d, nom, pg, pf, i in ecarts[:15]:
        print("  %-24s glb[%3d] (%8.4f %8.4f %8.4f)  flver (%8.4f %8.4f %8.4f)  ecart %8.5f"
              % (nom, i, pg[0], pg[1], pg[2], pf[0], pf[1], pf[2], d))

    if ecarts:
        moy = sum(e[0] for e in ecarts) / len(ecarts)
        med = sorted(e[0] for e in ecarts)[len(ecarts) // 2]
        print()
        print("ecart moyen %.6f   median %.6f   max %.6f" % (moy, med, ecarts[0][0]))
        print("os a plus de 1 cm d'ecart : %d" % len([e for e in ecarts if e[0] > 0.01]))

    print()
    print("=== quelques os de reference ===")
    for nom in ("Master", "Root", "Pelvis", "Spine2", "Spine", "Neck", "Head",
                "L_UpperArm", "R_UpperArm", "L_Hand", "R_Hand", "L_Foot", "R_Foot"):
        if nom in os_flver and nom in noms_glb:
            i = noms_glb.index(nom)
            m = monde[i]
            pg = (m[0][3], m[1][3], m[2][3])
            pf = os_flver[nom][2]
            print("  %-14s glb (%7.4f %7.4f %7.4f)   flver (%7.4f %7.4f %7.4f)"
                  % (nom, pg[0], pg[1], pg[2], pf[0], pf[1], pf[2]))


def oracle(glb_animation, tsv_flver, secondes, sortie):
    """Ecrit la pose d'animation dans le repere exact du FLVER.

    Les pistes d'animation du GLB sont deja exprimees dans les reperes locaux
    du FLVER : la conversion de HavokToolset n'applique son changement de base
    qu'au noeud racine de sa sortie "squelette seul", pas aux pistes. On le
    controle en comparant la racine animee a la racine du FLVER.
    """
    doc_an, bin_an = glb_lire.lire_glb(glb_animation)
    monde_an, parents_an = matrices_monde(doc_an, bin_an, secondes)
    noms_an = noms(doc_an)
    os_flver = lire_tsv(tsv_flver)

    if "Master" in os_flver and "Master" in noms_an:
        a = monde_an[noms_an.index("Master")]
        b = os_flver["Master"][3]
        ecart = max(abs(a[r][c] - b[r][c]) for r in range(4) for c in range(4))
        print("controle racine : ecart max %.6f  (petit = meme repere)" % ecart)
        if ecart > 0.5:
            print("  ATTENTION : ecart important, la pose n'est pas dans le repere du FLVER")

    lignes = []
    for i, nom in enumerate(noms_an):
        if nom not in os_flver:
            continue
        a = monde_an[i]
        v = [a[j][k] for k in range(4) for j in range(4)]
        lignes.append(nom + "\t" + "\t".join("%.9g" % x for x in v))

    manquants = [n for n in os_flver if n not in noms_an]
    with open(sortie, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    print("ecrit %s : %d os poses ; %d os du FLVER sans equivalent GLB"
          % (sortie, len(lignes), len(manquants)))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    commande = sys.argv[1]
    if commande == "comparer":
        comparer(sys.argv[2], sys.argv[3])
    elif commande == "positions":
        comparer(sys.argv[2], sys.argv[4], float(sys.argv[3]))
    elif commande == "oracle":
        if len(sys.argv) < 6:
            print(__doc__)
            sys.exit(1)
        oracle(sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
