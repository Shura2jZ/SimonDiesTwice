"""
Correspondance des os entre le squelette de Simon (Unreal Engine 5.4, fichier
.glb) et celui d'Isshin (FromSoft, FLVER).

Trois etages :
  1. une table explicite pour le squelette principal (bassin, colonne, membres) ;
  2. les doigts, apparies par geometrie (direction du doigt depuis la main) ;
  3. tout le reste (tissus, cheveux, correctifs) remonte la chaine des parents
     jusqu'au premier os deja mappe.

Toutes les cles sont des INDICES DE JOINTS (indices utilises par les poids des
sommets), pas des indices de noeuds ni des noms.

Convention gauche/droite -- decision documentee :
  Isshin regarde vers -Z et ses os nommes L_ sont en +X, c'est-a-dire a la
  DROITE anatomique du personnage (nomenclature "cote spectateur", classique en
  animation). Simon, dans le .glb, regarde vers +Z et ses os _l sont en +X,
  c'est-a-dire a sa gauche anatomique (nomenclature anatomique, usage Unreal).
  On fait donc tourner le modele de 180 degres autour de Y -- rotation pure,
  aucune symetrie, aucune face a retourner -- et on echange L et R dans la
  correspondance. Les deux choix vont ensemble : prendre l'un sans l'autre
  donnerait un personnage en miroir.
"""

# --- 1. squelette principal -------------------------------------------------
# nom Unreal (sans suffixe de cote) -> nom FromSoft (sans prefixe de cote)
COEUR = {
    "root": "Master",
    "pelvis": "Pelvis",
    "spine_01": "Spine",
    "spine_03": "Spine1",
    "spine_05": "Spine2",
    "neck_01": "Neck",
    "head": "Head",
}

DERIVE = {
    "clavicle": "Clavicle",
    "upperarm": "UpperArm",
    "lowerarm": "Forearm",
    "hand": "Hand",
    "thigh": "Thigh",
    "calf": "Calf",
    "foot": "Foot",
    "ball": "Toe0",
}

# nom Unreal -> nom de chaine FromSoft (ordre verifie par geometrie)
DOIGTS = {"thumb": "Finger4", "index": "Finger0", "middle": "Finger1",
          "ring": "Finger2", "pinky": "Finger3"}

SEGMENTS = ("01", "02", "03", "04")


def _suffixe(nom):
    """('l'|'r'|None, nom sans suffixe de cote)."""
    n = nom.lower()
    if n.endswith("_l"):
        return "l", n[:-2]
    if n.endswith("_r"):
        return "r", n[:-2]
    return None, n


def _retourner(cote):
    return {"l": "r", "r": "l"}.get(cote)


def _norme(v):
    return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5


def _distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _direction(depuis, vers):
    d = (vers[0] - depuis[0], vers[1] - depuis[1], vers[2] - depuis[2])
    n = _norme(d)
    return (d[0] / n, d[1] / n, d[2] / n) if n > 1e-9 else (0.0, 0.0, 0.0)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _apparier_doigts(noms, mapping, pos_simon, index_isshin, pos_isshin, transformation):
    """
    Apparie les doigts par geometrie.

    La direction seule ne suffit pas (les cinq doigts pointent presque dans le
    meme sens depuis la main). On compare donc la POSITION des bases de doigts
    dans le repere de la main, apres mise a l'echelle : le bouquet de doigts
    d'Isshin sert de gabarit, et chaque doigt de Simon est associe au plus
    proche encore libre. C'est ce qui distingue pouce / index / majeur / annulaire
    / auriculaire de facon fiable.
    """
    rapport = []
    for cote in ("r", "l"):
        nom_main = "hand_%s" % cote
        if nom_main not in noms:
            continue
        i_main = noms.index(nom_main)
        if i_main not in mapping:
            continue
        pos_main_s = pos_simon[i_main]
        pos_main_i = pos_isshin[mapping[i_main]]
        cote_isshin = _retourner(cote).upper()

        candidats = []
        for cand in DOIGTS.values():
            nom_i = "%s_%s" % (cote_isshin, cand)
            if nom_i in index_isshin:
                candidats.append((nom_i, _sub(pos_isshin[index_isshin[nom_i]], pos_main_i)))
        if not candidats:
            continue

        doigts = []
        for doigt in DOIGTS:
            nom_b = "%s_01_%s" % (doigt, cote)
            if nom_b in noms:
                doigts.append((doigt, nom_b, noms.index(nom_b),
                               transformation(_sub(pos_simon[noms.index(nom_b)], pos_main_s))))
        if not doigts:
            continue

        # les deux mains n'ont pas la meme taille : on met a l'echelle
        m_s = sum(_norme(v) for _, _, _, v in doigts) / len(doigts)
        m_i = sum(_norme(v) for _, v in candidats) / len(candidats)
        ech = m_s / max(1e-9, m_i)

        pris = set()
        for doigt, nom_b, i, v in doigts:
            vv = (v[0] * ech, v[1] * ech, v[2] * ech)
            meilleur, meilleure_dist = None, 1e30
            for nom_i, w in candidats:
                if nom_i in pris:
                    continue
                d = _distance(vv, w)
                if d < meilleure_dist:
                    meilleur, meilleure_dist = nom_i, d
            if meilleur is None:
                continue
            pris.add(meilleur)
            mapping[i] = index_isshin[meilleur]
            rapport.append((i, nom_b, meilleur, "doigt (ecart %.3f)" % meilleure_dist))
            # chaine : 01 -> base, 02 -> base+"1", 03 -> base+"1"
            # (les chaines FromSoft ont deux articulations, les chaines Unreal trois)
            for k in (1, 2, 3):
                nom_s = "%s_%02d_%s" % (doigt, k + 1, cote)
                if nom_s not in noms:
                    continue
                cible = meilleur if k == 0 else meilleur + "1"
                if cible in index_isshin:
                    mapping[noms.index(nom_s)] = index_isshin[cible]
                    rapport.append((noms.index(nom_s), nom_s, cible, "doigt (suite)"))
    return rapport


def _sous_arbre(racine, parent_isshin, limite):
    """Ensemble des noeuds du sous-arbre de racine (racine comprise), bornes aux
    os deformants (< limite)."""
    enfants = {}
    for n, p in parent_isshin.items():
        enfants.setdefault(p, []).append(n)
    vus, pile = set(), [racine]
    while pile:
        n = pile.pop()
        if n in vus or n >= limite:
            continue
        vus.add(n)
        for c in enfants.get(n, ()):
            pile.append(c)
    return vus


def _apparier_spatialement(noms, parent, mapping, pos_simon, pos_isshin,
                           transformation, parent_isshin, limite_deform, portee=0.5,
                           os_autorises=None):
    """
    Pour les os restants (tissus, correctifs), on cherche l'os d'Isshin le plus
    proche SPATIALEMENT, mais uniquement dans le sous-arbre de l'os cible du
    parent. Cela evite les appariements absurdes (un pan de tissu qui irait
    s'accrocher a un os du pied) tout en trouvant les correspondances reelles :
    par exemple les os correctifs du bras de Simon, qui longent l'avant-bras,
    tombent ainsi sur l'avant-bras d'Isshin et non sur l'epaule.

    os_autorises : ensemble d'indices de noeuds d'Isshin sur lesquels on a le
    DROIT d'accrocher de la geometrie de corps (mesure : les os utilises par les
    maillages rigides du personnage vanille). Sans ce filtre, un pan de hanche
    tombe sur le fourreau (Katana_Saya_Storage), un os de STOCKAGE que le systeme
    d'equipement teleporte : la geometrie part alors en triangles geants.

    Renvoie la liste des lignes de rapport pour les os apparies ainsi.
    """
    rapport = []
    n = len(noms)
    cache = {}
    for j in range(n):
        if j in mapping:
            continue
        # remonter la chaine des parents de Simon jusqu'au premier os mappe
        a, sauts = j, 0
        while a != -1 and a not in mapping and sauts < 60:
            a = parent[a] if 0 <= a < n else -1
            sauts += 1
        if a == -1 or a not in mapping:
            continue
        cible_parent = mapping[a]
        sous = cache.get(cible_parent)
        if sous is None:
            sous = cache[cible_parent] = _sous_arbre(cible_parent, parent_isshin,
                                                     limite_deform)
        if not sous:
            continue
        p = transformation(pos_simon[j])
        meilleur, meilleure_dist = None, 1e30
        for cand in sous:
            if os_autorises is not None and cand not in os_autorises:
                continue
            pc = pos_isshin.get(cand)
            if pc is None:
                continue
            d = _distance(p, pc)
            if d < meilleure_dist:
                meilleur, meilleure_dist = cand, d
        if meilleur is not None and meilleure_dist <= portee:
            mapping[j] = meilleur
            rapport.append((j, noms[j], "noeud %d (%.3f m)" % (meilleur, meilleure_dist),
                            "spatial"))
    return rapport


def mapper(noms, parent, pos_simon, index_isshin, pos_isshin, transformation=None,
           parent_isshin=None, limite_deform=184, os_autorises=None,
           appariement_spatial=True):
    """
    Construit la correspondance.

    noms           : noms des os de Simon, ordre des joints
    parent         : parent de chaque os, en indices de joints (-1 pour la racine)
    pos_simon      : position de chaque os de Simon (pose de reference, espace .glb)
    index_isshin   : nom d'os FromSoft -> index global de noeud
    pos_isshin     : index global de noeud -> position dans la pose de reference
    transformation : fonction appliquee aux vecteurs .glb -> FLVER (rotation 180 Y)
    os_autorises   : indices d'os d'Isshin acceptables pour de la geometrie de corps
                     (voir _apparier_spatialement) ; None = aucun filtre

    Renvoie (mapping, rapport) : mapping est un dict index Simon -> index Isshin.
    """
    if transformation is None:
        transformation = lambda v: v
    mapping = {}
    rapport = []
    n = len(noms)

    # --- etage 1 : squelette principal ------------------------------------
    for i, nom in enumerate(noms):
        cote, base = _suffixe(nom)
        cible = None
        if base in COEUR:
            cible = COEUR[base]
        elif cote is not None and base in DERIVE:
            cible = "%s_%s" % (_retourner(cote).upper(), DERIVE[base])
        if cible is None:
            continue
        if cible in index_isshin:
            mapping[i] = index_isshin[cible]
            rapport.append((i, nom, cible, "squelette"))
        else:
            rapport.append((i, nom, cible + " (absent)", "A REVOIR"))

    # --- etage 2 : doigts --------------------------------------------------
    rapport.extend(_apparier_doigts(noms, mapping, pos_simon, index_isshin,
                                    pos_isshin, transformation))

    # --- etage 2 bis : les metacarpes suivent leur doigt -------------------
    for i, nom in enumerate(noms):
        if i in mapping or "metacarpal" not in nom.lower():
            continue
        doigt = nom.split("_")[0].lower()
        if doigt not in DOIGTS:
            continue
        for j, autre in enumerate(noms):
            if j in mapping and autre.lower().startswith(doigt + "_01_"):
                mapping[i] = mapping[j]
                rapport.append((i, nom, noms[j], "metacarpe"))
                break

    # --- etage 2 ter : appariement spatial contraint -----------------------
    # Pour une peau provenant d'un autre jeu, l'appariement par proximite peut
    # accrocher les os de manteau/correctifs aux jambes ou aux bras. Le mode
    # simple desactive cette etape : ces os heritent alors de leur parent mappe.
    if parent_isshin and appariement_spatial:
        rapport.extend(_apparier_spatialement(noms, parent, mapping, pos_simon, pos_isshin,
                                              transformation, parent_isshin, limite_deform,
                                              os_autorises=os_autorises))

    # --- etage 3 : remontee de la chaine des parents -----------------------
    for i in range(n):
        if i in mapping:
            continue
        j, sauts = i, 0
        while j != -1 and j not in mapping and sauts < 40:
            j = parent[j] if 0 <= j < n else -1
            sauts += 1
        if j != -1 and j in mapping:
            mapping[i] = mapping[j]
            rapport.append((i, noms[i], noms[j], "parent (%d)" % sauts))
        else:
            rapport.append((i, noms[i], "?", "NON MAPPE"))

    # --- controle : aucune cible interdite ---------------------------------
    if os_autorises is not None:
        interdits = sorted(set(m for m in mapping.values()
                               if m not in os_autorises and m not in (0, 1)))
        if interdits:
            for m in interdits:
                noms_concernes = [noms[i] for i in sorted(mapping)
                                  if mapping[i] == m]
                rapport.append((-1, ", ".join(noms_concernes[:4]), "noeud %d" % m,
                                "CIBLE INTERDITE (os d'arme/stockage/fil)"))
    return mapping, rapport
