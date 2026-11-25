"""
Extraction de Simon (.glb) vers un format intermediaire simple, lu ensuite par
l'injecteur C# (FlverInject.exe) qui ecrit le FLVER.

Ce script fait tout le travail "intelligent" :
  - lecture de la geometrie et des poids ;
  - correspondance des os (bone_map.py) ;
  - CHANGEMENT DE POSE DE REFERENCE : le maillage de Simon est re-pose dans la
    pose de reference d'Isshin (voir ci-dessous) ;
  - rotation de 180 degres autour de Y (Simon regarde +Z, Isshin -Z) ;
  - ecriture du fichier intermediaire.

Pourquoi changer de pose de reference
-------------------------------------
La pose de reference de Simon est une pose en A (bras le long du corps), celle
d'Isshin est une pose en T (bras ecartes). Le jeu deforme le maillage en
comparant la pose animee des os a leur pose de reference. Si le maillage est
laisse dans la pose de Simon, les os d'Isshin le deforment comme s'il etait en
T : les bras partent de travers des le premier mouvement.

On re-pose donc le maillage AVANT de l'ecrire, avec un transforme rigide par os :

    p = somme_j  poids_j * ( R_j * v + t_j )

  - os en correspondance DIRECTE (squelette principal et doigts) :
        R_j = Alignement_j * R        (rotation qui amene la direction de l'os
                                       de Simon, vue apres R, sur celle de l'os
                                       d'Isshin)
        t_j = position_Isshin[os_cible] - R_j * position_Simon[j]
    Le morceau suit donc l'os d'Isshin dans la bonne direction : le bras se
    remet en T au lieu de rester pendu.

  - os en correspondance INDIRECTE (tissus, correctifs : ils remontent la chaine
    des parents), R_j = R et t_j = deplacement du parent. Le morceau suit son
    parent rigidement, sans rotation inventee. C'est le bon comportement pour un
    pan de tissu ou un os correctif.

  R est la rotation de 180 degres autour de Y. Elle est appliquee au decalage de
chaque sommet par rapport a son os, donc chaque morceau garde sa forme exacte :
c'est une re-pose, pas une deformation.

Usage :
    python tools/simon_export.py modele.glb isshin_nodes.tsv sortie.bin
        [--translation]   ne pas re-poser (translation seule, pour comparer)
        [--rigide]        tout sur l'os racine (diagnostic)
"""

import math
import os
import struct
import sys

import bone_map
import glb_model
import mat4

# --- affectation des morceaux de Simon aux materiaux d'Isshin ---------------
# (motif dans le nom du materiau, index de materiau Isshin, noeud porteur Isshin)
AFFECTATION = [
    ("head", 4, 199),      # #20#c5400_head           (peau du visage, SSS)
    ("coat", 7, 200),      # #20#c5400_kimono_nontiling (tissu opaque)
    ("top", 9, 200),       # #20#c5400_hoture          (meme shader, autre jeu de textures)
    ("bottom", 8, 200),    # #20#c5400_helmetfur       (meme shader, autre jeu de textures)
    ("cheveux", 2, 199),   # materiau 2 = c5409_eyeshadow (shader character_AMSN,
                           # g_BlendMode=2 => alpha test). Choisi car ses
                           # textures (c5409_eyeshadow_a/n) sont PROPRES a
                           # c5409 : on les remplace par l'atlas de meches de
                           # Simon sans toucher aux autres personnages.
                           # Materiau 0 (casque, BlendMode=0) : alpha ignore ->
                           # plaques noires. Materiau 26 (Fur_NTC) : correct mais
                           # sa texture FC_A_0000_common_hair_a est partagee par
                           # tous les PNJ (sourcils) -> effet de bord global.
]
AFFECTATION_DEFAUT = (3, 200)   # #20#c5400_body (SSS)

MATRICE_180_Y = (-1.0, 0.0, 0.0,
                 0.0, 1.0, 0.0,
                 0.0, 0.0, -1.0)


def rotation_180_y(v):
    """Simon regarde +Z, Isshin -Z : rotation pure de 180 degres autour de Y."""
    return (-v[0], v[1], -v[2])


# --- petites operations sur les rotations 3x3 (9 coefficients, ligne) -------

IDENTITE = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def mul3(a, b):
    return tuple(sum(a[3 * i + k] * b[3 * k + j] for k in range(3))
                 for i in range(3) for j in range(3))


def applique3(m, v):
    return (m[0] * v[0] + m[1] * v[1] + m[2] * v[2],
            m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
            m[6] * v[0] + m[7] * v[1] + m[8] * v[2])


def norme(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def normalise(v):
    n = norme(v)
    if n < 1e-12:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def produit_vectoriel(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def produit_scalaire(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def rotation_minimale(a, b):
    """Rotation (3x3) qui amene le vecteur unitaire a sur le vecteur unitaire b."""
    a, b = normalise(a), normalise(b)
    if norme(a) < 0.5 or norme(b) < 0.5:
        return IDENTITE
    d = max(-1.0, min(1.0, produit_scalaire(a, b)))
    if d > 0.999999:
        return IDENTITE
    if d < -0.999999:
        # opposition : 180 degres autour d'un axe perpendiculaire quelconque
        axe = produit_vectoriel(a, (1.0, 0.0, 0.0))
        if norme(axe) < 1e-6:
            axe = produit_vectoriel(a, (0.0, 1.0, 0.0))
        axe = normalise(axe)
        return (2 * axe[0] * axe[0] - 1, 2 * axe[0] * axe[1], 2 * axe[0] * axe[2],
                2 * axe[1] * axe[0], 2 * axe[1] * axe[1] - 1, 2 * axe[1] * axe[2],
                2 * axe[2] * axe[0], 2 * axe[2] * axe[1], 2 * axe[2] * axe[2] - 1)
    axe = normalise(produit_vectoriel(a, b))
    c, s = d, math.sqrt(max(0.0, 1.0 - d * d))
    x, y, z = axe
    C = 1.0 - c
    return (c + x * x * C, x * y * C - z * s, x * z * C + y * s,
            y * x * C + z * s, c + y * y * C, y * z * C - x * s,
            z * x * C - y * s, z * y * C + x * s, c + z * z * C)


def transpose3(m):
    return (m[0], m[3], m[6], m[1], m[4], m[7], m[2], m[5], m[8])


def charge_os_rotations(tsv):
    """Rotations GLOBALES des noeuds d'Isshin, lues dans l'export d'os.

    Le TSV stocke la matrice globale en convention LIGNE (v' = v.M, translation
    dans la derniere ligne). On renvoie la rotation 3x3 en convention COLONNE
    (v' = R.v), rangee ligne par ligne : c'est la convention de mul3/applique3,
    et donc celle des matrices de Simon (glTF).

    C'est LE repere que le moteur utilise pour la peau : bind_b, dont la
    deformation se sert sous la forme bind_b^-1.
    """
    res = {}
    for ligne in open(tsv, encoding="utf-8").read().splitlines()[1:]:
        c = ligne.split("\t")
        if len(c) < 29:
            continue
        brut = [float(x) for x in c[13:29]]
        m = [[brut[r * 4 + k] for k in range(4)] for r in range(4)]
        res[int(c[0])] = (m[0][0], m[1][0], m[2][0],
                          m[0][1], m[1][1], m[2][1],
                          m[0][2], m[1][2], m[2][2])
    return res


def charge_os(tsv, echelle=1.0):
    """Lit l'export d'os d'Isshin : nom -> index, index -> position, index -> parent.

    `echelle` : homothetie appliquee aux positions des os (le squelette de
    reference du jeu est agrandi de la meme facon, cf. FlverInject --echelle).
    """
    index, positions, parents = {}, {}, {}
    for ligne in open(tsv, encoding="utf-8").read().splitlines()[1:]:
        c = ligne.split("\t")
        if len(c) < 29:
            continue
        i = int(c[0])
        index[c[3]] = i
        parents[i] = int(c[1])
        g = [float(x) for x in c[13:29]]
        positions[i] = (g[12], g[13], g[14])
    if echelle != 1.0 and ("Master" in index or "Root" in index):
        # Le GLB de Simon a son root a l'origine (au niveau des pieds). Cote
        # Isshin, le pivot correspondant est Master, pas Root (Root est a
        # environ 1.24 m du sol). Utiliser Root decale le personnage en hauteur.
        pivot = positions[index.get("Master", index["Root"])]
        positions = {
            i: tuple(pivot[k] + (p[k] - pivot[k]) * echelle for k in range(3))
            for i, p in positions.items()
        }
    return index, positions, parents


def hierarchie_joints(g, echelle=1.0):
    """
    Pour chaque joint : son parent *en indices de joints*, et la position de sa
    pose de reference dans l'espace du modele.
    """
    joints, binds = g.skin(0)
    noeud_vers_joint = {n: i for i, n in enumerate(joints)}
    nodes = g.json["nodes"]
    parent_noeud = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent_noeud[c] = i

    parent_joint, positions = [], []
    for j, noeud in enumerate(joints):
        p = parent_noeud.get(noeud, -1)
        while p != -1 and p not in noeud_vers_joint:
            p = parent_noeud.get(p, -1)
        parent_joint.append(noeud_vers_joint.get(p, -1))
        positions.append(tuple(v * echelle for v in mat4.get_translation(binds[j])))
    noms = g.bone_names(joints)
    return noms, parent_joint, positions


def charge_os_autorises(chemin=None):
    """
    Lit la liste blanche des os d'Isshin (tools/whitelist_os.py). Sans elle, un
    os de Simon peut tomber sur un os d'arme/stockage que le jeu teleporte, et
    la geometrie part en triangles geants.
    """
    if chemin is None:
        chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "_work", "os_autorises.txt")
    if not os.path.isfile(chemin):
        return None
    autorises = set()
    for ligne in open(chemin, encoding="utf-8"):
        ligne = ligne.split("#")[0].strip()
        if not ligne:
            continue
        autorises.add(int(ligne.split("\t")[0]))
    return autorises or None


def construit_transformes(noms, parent_s, pos_s, mapping, directs, index_isshin, pos_isshin,
                          rot_isshin=None, binds_simon=None):
    """
    Construit, pour chaque os de Simon, le couple (rotation 3x3, translation) qui
    amene ses sommets dans la pose de reference d'Isshin.
    Renvoie (rotations, translations, rapport).

    Si rot_isshin (rotations globales des noeuds du FLVER) et binds_simon
    (matrices de liaison des os de Simon) sont fournis, on utilise la re-pose
    CANONIQUE, celle qui passe par les reperes locaux reels :

        rot_j = R_isshin[m] . R180 . (R_simon[j])^-1
        tr_j  = position_isshin[m] - rot_j . position_simon[j]

    C'est la seule forme compatible avec la peau du moteur, qui deforme le
    sommet par bind_b^-1 * anim_b : le sommet doit donc etre place avec
    exactement le repere local de l'os cible. L'ancienne methode (rotation
    deduite de la direction de l'os) place le morceau dans le bon axe mais avec
    un roulis quelconque : invisible a la pose de reference, mais l'ecart est
    une rotation appliquee au decalage local, et elle varie d'un os a l'autre,
    donc le maillage se dechire des que les os bougent.
    """
    n = len(noms)
    rotations, translations = [IDENTITE] * n, [(0.0, 0.0, 0.0)] * n
    rapport = []

    if rot_isshin is not None and binds_simon is not None:
        # Re-pose canonique : on aligne le repere LOCAL de l'os de Simon sur
        # celui de l'os cible d'Isshin.
        #
        # ATTENTION : ne PAS rajouter de rotation 180 autour de Y ici. Les deux
        # squelettes se font deja face en sens inverse (Simon +Z, Isshin -Z) et
        # cette difference est contenue dans les reperes d'os. L'ancienne
        # formule R_isshin . R180 . R_simon^-1 ajoutait donc un demi-tour
        # supplementaire : la tete se retrouvait en bas (le sommet du crane
        # passait de y=2.21 a y=1.80) et posee 13 cm trop bas.
        canon = {}
        for j in range(n):
            m = mapping.get(j)
            if m is None:
                continue
            rs = tuple(binds_simon[j][r][k] for r in range(3) for k in range(3))
            rot = mul3(rot_isshin[m], transpose3(rs))
            tr = tuple(pos_isshin[m][k] - applique3(rot, pos_s[j])[k] for k in range(3))
            canon[j] = (rot, tr)

        # --- UN transform par os cible d'Isshin (mesure 17/11) -------------
        # Les os correctifs/twist de Simon (upperarm_twistCor, bicep, tricep,
        # calf_twist...) ciblent les MEMES os d'Isshin que leurs os principaux,
        # mais leurs reperes locaux different (axes de vrille, rotations de
        # calibrage). En appliquant canon[j] par os, les cartes de tissu ponderees
        # sur ces os sortaient avec des transforms incompatibles entre voisins :
        # la pose de reference montrait le manteau et les jambes en cartes
        # dispersees autour du corps (rendu v6tex). Or le moteur, lui, deforme
        # TOUS ces sommets via le meme os cible m : la pose stockee doit donc etre
        # LA MEME pour tous les os de Simon pointant sur m. On choisit comme
        # transform de groupe celui de l'os principal (le moins profond dans la
        # hierarchie de Simon : l'os nu est toujours ancetre de ses correctifs).
        def profondeur(j):
            d = 0
            while parent_s[j] >= 0:
                j = parent_s[j]
                d += 1
            return d

        groupes = {}
        for j, m in mapping.items():
            groupes.setdefault(m, []).append(j)
        principal = {m: min(js, key=lambda j: (profondeur(j), j))
                     for m, js in groupes.items()}

        for j in range(n):
            m = mapping.get(j)
            if m is None:
                continue
            p = principal[m]
            rotations[j], translations[j] = canon[p]
            if j == p:
                rapport.append((j, noms[j], "repere local (principal)",
                                norme(canon[p][1]), 0.0))
            else:
                rapport.append((j, noms[j], "suit l'os principal %s" % noms[p],
                                norme(canon[p][1]), 0.0))
        return rotations, translations, rapport

    for j in range(n):
        m = mapping.get(j)
        if m is None:
            continue
        par = parent_s[j]

        if j in directs:
            # on remonte la chaine des parents jusqu'a un os dont la cible est
            # DIFFERENTE : c'est ce qui donne une direction d'os utilisable.
            # (sans cela, une phalange dont le parent vise le meme os qu'elle
            # n'a pas de direction, et l'alignement est faux.)
            ancetre = par
            while ancetre >= 0 and mapping.get(ancetre) == m:
                ancetre = parent_s[ancetre]
            if ancetre >= 0 and ancetre in mapping:
                dir_s = rotation_180_y(normalise(tuple(pos_s[j][k] - pos_s[ancetre][k] for k in range(3))))
                dir_t = normalise(tuple(pos_isshin[m][k] - pos_isshin[mapping[ancetre]][k] for k in range(3)))
                align = rotation_minimale(dir_s, dir_t)
                rot = mul3(align, MATRICE_180_Y)
                tr = tuple(pos_isshin[m][k] - applique3(rot, pos_s[j])[k] for k in range(3))
                rotations[j], translations[j] = rot, tr
                # controle : la direction de l'os doit maintenant coincider
                apres = applique3(rot, normalise(tuple(pos_s[j][k] - pos_s[ancetre][k] for k in range(3))))
                ecart = math.degrees(math.acos(max(-1.0, min(1.0, produit_scalaire(apres, dir_t)))))
                rapport.append((j, noms[j], "direct", norme(tr), ecart))
            else:
                rotations[j], translations[j] = MATRICE_180_Y, (0.0, 0.0, 0.0)
                rapport.append((j, noms[j], "direct (sans direction)", 0.0, 0.0))
        else:
            # remonter jusqu'au premier ancetre en correspondance DIRECTE :
            # c'est son deplacement qui est repris, pas celui du parent immediat
            # (sinon une chaine qui remonte plusieurs niveaux applique un
            # deplacement calcule pour un autre os).
            a = par
            while a >= 0 and a not in directs:
                a = parent_s[a]
            if a >= 0 and a in mapping:
                # Un os secondaire sans correspondance propre doit heriter de
                # toute la transformation de son ancetre mappe, rotation incluse.
                # Recalculer seulement une translation avec R180Y faisait
                # diverger les os de tissu/correctifs de leur parent lorsque
                # celui-ci avait ete aligne par direction.
                rot, tr = rotations[a], translations[a]
            else:
                rot, tr = MATRICE_180_Y, (0.0, 0.0, 0.0)
            rotations[j], translations[j] = rot, tr
            rapport.append((j, noms[j], "suit le parent", norme(tr), 0.0))
    return rotations, translations, rapport


def ecrit_entete(f, nb_maillages, nb_os):
    f.write(b"SMPORT\x00\x01")
    f.write(struct.pack("<I", nb_maillages))
    f.write(struct.pack("<9f", *MATRICE_180_Y))
    f.write(struct.pack("<I", nb_os))


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    chemin_glb, chemin_tsv, chemin_sortie = sys.argv[1], sys.argv[2], sys.argv[3]
    rigide = "--rigide" in sys.argv
    translation_seule = "--translation" in sys.argv
    par_direction = "--direction" in sys.argv   # ancienne methode (direction seule)
    peau_simple = "--peau-simple" in sys.argv
    # echelle : homothetie du personnage (Simon est a x1.5 dans Clair Obscur).
    echelle = 1.0
    for i, a in enumerate(sys.argv):
        if a == "--echelle" and i + 1 < len(sys.argv):
            echelle = float(sys.argv[i + 1])

    g = glb_model.Glb(chemin_glb)
    noms, parent_s, pos_s = hierarchie_joints(g, echelle)
    index_isshin, pos_isshin, parent_isshin = charge_os(chemin_tsv, echelle)
    # rotations globales des noeuds du FLVER : le repere local que le moteur
    # utilise pour la peau (bind_b), indispensable a une re-pose juste.
    rot_isshin = charge_os_rotations(chemin_tsv)
    joints, binds_simon = g.skin(0)

    print("os de Simon   : %d" % len(noms))
    print("os d'Isshin   : %d" % len(index_isshin))
    if rigide:
        print("mode          : RIGIDE (tout sur l'os racine)")
    elif translation_seule:
        print("mode          : translation seule (pas de re-pose)")
    else:
        print("mode          : re-pose dans la pose de reference d'Isshin")

    autorises = charge_os_autorises()
    if autorises is None:
        print("os autorises  : (liste blanche absente -> AUCUN FILTRE)")
    else:
        print("os autorises  : %d os (maillages rigides du personnage)" % len(autorises))

    mapping, liste_rapport = bone_map.mapper(noms, parent_s, pos_s,
                                             index_isshin, pos_isshin, rotation_180_y,
                                             parent_isshin=parent_isshin,
                                             os_autorises=autorises,
                                             appariement_spatial=not peau_simple)
    if peau_simple:
        print("peau           : os secondaires heritent du parent (sans proximite spatiale)")
    directs = set(i for (i, _, _, methode) in liste_rapport
                  if methode.startswith(("squelette", "doigt", "spatial")))

    with open("_work/simon_bone_map.txt", "w", encoding="utf-8") as f:
        f.write("index\tnom Simon\tcible\tmethode\n")
        for i, nom, cible, methode in sorted(liste_rapport):
            f.write("%d\t%s\t%s\t%s\n" % (i, nom, cible, methode))
    non_mappes = [r for r in liste_rapport if r[3] == "NON MAPPE"]
    methodes = {}
    for r in liste_rapport:
        cle = r[3].split(" ")[0]
        methodes[cle] = methodes.get(cle, 0) + 1
    print("correspondance : %d os mappes, %d non mappes, %d en correspondance directe"
          % (len(mapping), len(non_mappes), len(directs)))
    for m in sorted(methodes):
        print("    %-12s %d" % (m, methodes[m]))

    rotations, translations, rapport = construit_transformes(
        noms, parent_s, pos_s, mapping, directs, index_isshin, pos_isshin,
        rot_isshin=None if par_direction else rot_isshin,
        binds_simon=None if par_direction else binds_simon)

    if translation_seule:
        for j in range(len(noms)):
            m = mapping.get(j)
            if m is None:
                continue
            rotations[j] = MATRICE_180_Y
            translations[j] = tuple(pos_isshin[m][k] - rotation_180_y(pos_s[j])[k] for k in range(3))

    if not translation_seule:
        ecarts = [r[4] for r in rapport if r[2] == "direct"]
        print()
        print("=== re-pose : ecart de direction apres transformation ===")
        print("  os directs : %d, ecart max %.2f degres, ecart moyen %.2f degres"
              % (len(ecarts), max(ecarts) if ecarts else 0.0,
                 sum(ecarts) / len(ecarts) if ecarts else 0.0))
        gros = sorted([r for r in rapport if r[3] > 0.05], key=lambda r: -r[3])[:10]
        print("  deplacements les plus importants (translation du morceau) :")
        for j, nom, meth, d, ec in gros:
            print("    %-24s %-16s deplace de %.3f m" % (nom, meth, d))

    with open("_work/simon_repose.txt", "w", encoding="utf-8") as f:
        f.write("index\tnom\tmode\tdeplacement\t ecart_degres\n")
        for j, nom, meth, d, ec in rapport:
            f.write("%d\t%s\t%s\t%.4f\t%.2f\n" % (j, nom, meth, d, ec))

    # --- maillages ----------------------------------------------------------
    primitives = []
    for mesh in g.json["meshes"]:
        for prim in mesh["primitives"]:
            primitives.append(prim)

    print()
    # Mode de diagnostic : ne convertir que les cheveux, pour remplacer le slot
    # 5 d'un candidat existant sans modifier le reste du skin.
    if "--cheveux-seuls" in sys.argv:
        primitives = [prim for prim in primitives
                      if "hair" in g.json["materials"][prim["material"]]["name"].lower()
                      or "cheveu" in g.json["materials"][prim["material"]]["name"].lower()]
        if not primitives:
            raise SystemExit("aucun maillage cheveux trouve dans le GLB")

    print("=== maillages a convertir ===")
    ms = []
    total_sommets = total_triangles = 0
    for prim in primitives:
        nom_mat = g.json["materials"][prim["material"]]["name"] if "material" in prim else "(sans)"
        attributs = prim["attributes"]
        n_sommets = g.json["accessors"][attributs["POSITION"]]["count"]
        n_indices = g.json["accessors"][prim["indices"]]["count"]
        mat_isshin, noeud_isshin = AFFECTATION_DEFAUT
        for motif, mi, ni in AFFECTATION:
            if motif in nom_mat.lower():
                mat_isshin, noeud_isshin = mi, ni
                break
        ms.append((nom_mat, prim, n_sommets, n_indices, mat_isshin, noeud_isshin))
        total_sommets += n_sommets
        total_triangles += n_indices // 3
        print("  %-32s %6d sommets %6d triangles -> materiau %d, noeud %d"
              % (nom_mat, n_sommets, n_indices // 3, mat_isshin, noeud_isshin))
    print("  total : %d sommets, %d triangles" % (total_sommets, total_triangles))

    print()
    print("=== conversion ===")
    racine_isshin = index_isshin.get("Root", 1)

    # Les cheveux de Simon sont dans le GLB (6e primitive) : ils sont donc
    # re-poses comme tous les autres morceaux (os "head" de Simon).
    with open(chemin_sortie, "wb") as f:
        ecrit_entete(f, len(ms), len(mapping))
        for i, nom in enumerate(noms):
            if i not in mapping:
                continue
            b = nom.encode("utf-8")
            f.write(struct.pack("<I", len(b)))
            f.write(b)
            f.write(struct.pack("<i", mapping[i]))

        for nom_mat, prim, n_sommets, n_indices, mat_isshin, noeud_isshin in ms:
            attributs = prim["attributes"]
            positions = g.accessor(attributs["POSITION"])
            if echelle != 1.0:
                positions = [(p[0] * echelle, p[1] * echelle, p[2] * echelle) for p in positions]
            normales = g.accessor(attributs["NORMAL"]) if "NORMAL" in attributs else [(0.0, 1.0, 0.0)] * n_sommets
            tangentes = g.accessor(attributs["TANGENT"]) if "TANGENT" in attributs else [(1.0, 0.0, 0.0, 1.0)] * n_sommets
            uvs = g.accessor(attributs["TEXCOORD_0"]) if "TEXCOORD_0" in attributs else [(0.0, 0.0)] * n_sommets
            couleurs = g.accessor(attributs["COLOR_0"]) if "COLOR_0" in attributs else [(1.0, 1.0, 1.0, 1.0)] * n_sommets
            joints = g.accessor(attributs["JOINTS_0"])
            poids = g.accessor(attributs["WEIGHTS_0"])
            indices = g.accessor(prim["indices"])

            b = nom_mat.encode("utf-8")
            f.write(struct.pack("<I", len(b)))
            f.write(b)
            f.write(struct.pack("<iii", mat_isshin, noeud_isshin, -1))
            f.write(struct.pack("<II", n_sommets, n_indices))

            # positions et normales REELLEMENT ecrites, pour decider ensuite,
            # face par face, le sens d'enroulement (voir plus bas).
            pos_ecrites = []
            nrm_ecrites = []

            for v in range(n_sommets):
                uv = (uvs[v][0], uvs[v][1])
                col = couleurs[v] if len(couleurs[v]) >= 4 else (1.0, 1.0, 1.0, 1.0)

                if rigide:
                    p = rotation_180_y(positions[v])
                    n = rotation_180_y(normales[v])
                    t = rotation_180_y(tangentes[v][:3]) + (tangentes[v][3],)
                    os_finaux = [(racine_isshin, 1.0)]
                else:
                    brut = [(int(joints[v][k]), float(poids[v][k])) for k in range(4)
                            if float(poids[v][k]) > 0.0]
                    fusion = {}
                    for b_idx, w in brut:
                        cible = mapping.get(b_idx)
                        if cible is None:
                            continue
                        fusion[cible] = fusion.get(cible, 0.0) + w
                    gardes = sorted(fusion.items(), key=lambda kv: -kv[1])[:4]
                    total = sum(w for _, w in gardes) or 1.0
                    os_finaux = [(k, w / total) for k, w in gardes]

                    src = positions[v]
                    acc = [0.0, 0.0, 0.0]
                    acc_n = [0.0, 0.0, 0.0]
                    acc_t = [0.0, 0.0, 0.0]
                    for b_idx, w in brut:
                        pp = w / total
                        rot, tr = rotations[b_idx], translations[b_idx]
                        q = applique3(rot, src)
                        acc[0] += pp * (q[0] + tr[0])
                        acc[1] += pp * (q[1] + tr[1])
                        acc[2] += pp * (q[2] + tr[2])
                        qn = applique3(rot, normales[v][:3])
                        acc_n[0] += pp * qn[0]; acc_n[1] += pp * qn[1]; acc_n[2] += pp * qn[2]
                        qt = applique3(rot, tangentes[v][:3])
                        acc_t[0] += pp * qt[0]; acc_t[1] += pp * qt[1]; acc_t[2] += pp * qt[2]
                    p = (acc[0], acc[1], acc[2])
                    n = normalise(tuple(acc_n))
                    t = normalise(tuple(acc_t)) + (tangentes[v][3],)

                os_finaux = list(os_finaux) + [(0, 0.0)] * (4 - len(os_finaux))
                f.write(struct.pack("<3f", *p))
                f.write(struct.pack("<3f", *n))
                f.write(struct.pack("<4f", *t))
                f.write(struct.pack("<2f", *uv))
                f.write(struct.pack("<4f", *col))
                f.write(struct.pack("<4i", *[int(k) for k, _ in os_finaux]))
                f.write(struct.pack("<4f", *[float(w) for _, w in os_finaux]))
                pos_ecrites.append(p)
                nrm_ecrites.append(n)

            # --- sens d'enroulement des triangles -------------------------
            # Mesure (FlverWinding.exe) : dans TOUS les maillages de Sekiro, le
            # produit scalaire entre la normale geometrique d'une face (calcul
            # par le sens des indices) et la normale stockee aux sommets vaut
            # -0,98 ; le volume signe du maillage est negatif. Autrement dit la
            # vanille enroule ses triangles dans le sens INVERSE de ses normales
            # (face avant = sens horaire vu de l'exterieur, convention Direct3D
            # par defaut).
            #
            # Le GLB de Simon suit la convention UE/glTF : produit scalaire
            # +0,98, volume positif. Recopie tel quel, chaque face exterieure est
            # vue comme une face ARRIERE par Direct3D ; avec cull=True le jeu la
            # supprime : le personnage devient creux (on ne voit que l'interieur,
            # grandes surfaces sombres et bords clairs) et parait invisible.
            # Nos rendus hors-jeu ne le voyaient pas : ils utilisent
            # renderMode "Both" (les deux faces, sans test de face cachee).
            #
            # Correction : choisir l'ordre des indices pour retrouver la
            # propriete de la vanille, face par face.
            #
            # Une inversion GLOBALE (0,2,1) ne suffit pas : mesure sur le build
            # installe, 40 a 44 % des faces des maillages 3/6/7 (manteau, haut,
            # bas) gardaient un produit POSITIF, restaient donc vues comme des
            # faces arriere et etaient supprimees par cull=True. La cause est
            # dans la source : ces parties de tissu contiennent des faces
            # enroulees dans les deux sens.
            #
            # On calcule donc pour chaque triangle la normale geometrique du sens
            # des indices et la somme des normales stockees de ses trois sommets ;
            # si le produit scalaire est positif (convention glTF/UE), les deux
            # derniers indices sont permutes. Resultat attendu : 0 % de faces
            # positives, comme la vanille (verifiable par FlverWinding.exe).
            if len(indices) % 3 != 0:
                print("  ATTENTION : %d indices, pas un multiple de 3" % len(indices))
            retournees = 0
            for t in range(0, len(indices) - 2, 3):
                a = int(indices[t])
                b = int(indices[t + 1])
                c = int(indices[t + 2])
                pa, pb, pc = pos_ecrites[a], pos_ecrites[b], pos_ecrites[c]
                ux, uy, uz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
                vx, vy, vz = pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2]
                gx = uy * vz - uz * vy
                gy = uz * vx - ux * vz
                gz = ux * vy - uy * vx
                nx = nrm_ecrites[a][0] + nrm_ecrites[b][0] + nrm_ecrites[c][0]
                ny = nrm_ecrites[a][1] + nrm_ecrites[b][1] + nrm_ecrites[c][1]
                nz = nrm_ecrites[a][2] + nrm_ecrites[b][2] + nrm_ecrites[c][2]
                if gx * nx + gy * ny + gz * nz > 0.0:
                    b, c = c, b
                    retournees += 1
                f.write(struct.pack("<III", a, b, c))
            print("  %-32s ecrit (%d/%d triangles retournes)"
                  % (nom_mat, retournees, len(indices) // 3))

    import os
    print()
    print("fichier ecrit : %s (%d octets)" % (chemin_sortie, os.path.getsize(chemin_sortie)))
    print("rapport de re-pose : _work/simon_repose.txt")
    return 0


if __name__ == "__main__":
    main()
