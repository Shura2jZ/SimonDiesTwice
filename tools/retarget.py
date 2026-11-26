"""Retarget de l'animation Simon (USD/.anim) sur le squelette d'Isshin (c5400).

    python tools/retarget.py <Simon_Skill_1.anim> <SK_Simon.glb> <skeleton.xml>
                             <sortie.anim2> [images] [fps]

Methode (celle validee dans la preview Blender) :
  - positions monde des articulations Simon par la chaine des translations ;
  - orientation de chaque os = balayage (rotation minimale) de la direction de
    repos (bind GLB) vers la direction animee ;
  - le bassin garde en plus le delta de rotation complet (orientation du corps).

Les rotations sont exprimees dans le repere du squelette d'Isshin (Y haut,
X = gauche, -Z = avant) via la matrice de passage deduite des deux squelettes.

Sortie : en-tete JSON + float32
    {"nb_images": N, "nb_pistes": P, "fps": F, "noms": [...]}
    par image : pour chaque piste : pos(3), quat(4), scale(3)
"""

import array
import json
import math
import os
import struct
import sys
import xml.etree.ElementTree as ET

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import glb_lire

# ---------------------------------------------------------------------------
# quaternions (x, y, z, w)
# ---------------------------------------------------------------------------


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qnorm(q):
    n = math.sqrt(sum(c * c for c in q))
    if n < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)


def q_axe_angle(axe, angle):
    n = math.sqrt(axe[0] * axe[0] + axe[1] * axe[1] + axe[2] * axe[2])
    if n < 1e-9:
        return (0.0, 0.0, 0.0, 1.0)
    s = math.sin(angle * 0.5) / n
    return (axe[0] * s, axe[1] * s, axe[2] * s, math.cos(angle * 0.5))


def qrot(q, v):
    x, y, z, w = q
    tx = 2.0 * (y * v[2] - z * v[1])
    ty = 2.0 * (z * v[0] - x * v[2])
    tz = 2.0 * (x * v[1] - y * v[0])
    return (
        v[0] + w * tx + (y * tz - z * ty),
        v[1] + w * ty + (z * tx - x * tz),
        v[2] + w * tz + (x * ty - y * tx),
    )


def swing(a, b):
    """Rotation minimale qui amene la direction a sur la direction b."""
    na = math.sqrt(sum(c * c for c in a))
    nb = math.sqrt(sum(c * c for c in b))
    if na < 1e-9 or nb < 1e-9:
        return (0.0, 0.0, 0.0, 1.0)
    ax, ay, az = (c / na for c in a)
    bx, by, bz = (c / nb for c in b)
    d = ax * bx + ay * by + az * bz
    if d > 0.999999:
        return (0.0, 0.0, 0.0, 1.0)
    if d < -0.999999:
        # directions opposees : axe perpendiculaire quelconque
        if abs(ax) < 0.9:
            axe = (0.0, -az, ay)
        else:
            axe = (az, 0.0, -ax)
        n = math.sqrt(sum(c * c for c in axe))
        return (axe[0] / n, axe[1] / n, axe[2] / n, 0.0)
    cx = ay * bz - az * by
    cy = az * bx - ax * bz
    cz = ax * by - ay * bx
    return qnorm((cx, cy, cz, 1.0 + d))


def qslerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0.0:
        b = (-b[0], -b[1], -b[2], -b[3])
        d = -d
    if d > 0.9995:
        return qnorm(tuple(a[i] + (b[i] - a[i]) * t for i in range(4)))
    theta = math.acos(max(-1.0, min(1.0, d)))
    s = math.sin(theta)
    wa = math.sin((1.0 - t) * theta) / s
    wb = math.sin(t * theta) / s
    return qnorm(tuple(a[i] * wa + b[i] * wb for i in range(4)))


def matrice_depuis_base(gauche, haut, avant):
    """Matrice 3x3 colonnes = images de X, Y, Z de la base source."""
    return [
        [gauche[0], haut[0], avant[0]],
        [gauche[1], haut[1], avant[1]],
        [gauche[2], haut[2], avant[2]],
    ]


def mat_vec(m, v):
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3))


def mat_t(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rot_vers_quat(m):
    """Matrice 3x3 (rotation) -> quaternion (x, y, z, w)."""
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s
    return qnorm((x, y, z, w))


def quat_vers_mat(q):
    x, y, z, w = q
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


# ---------------------------------------------------------------------------
# lectures
# ---------------------------------------------------------------------------


def lire_anim(chemin):
    with open(chemin, "rb") as fh:
        entete = json.loads(fh.readline().decode("utf-8"))
        brut = array.array("f")
        brut.frombytes(fh.read())
    return entete, brut


def lire_squelette(chemin):
    root = ET.parse(chemin).getroot()
    obj = [o for o in root.findall("object") if o.get("type") == "hkaSkeleton"][0]
    noms, parents, repos = [], [], []
    for e in obj:
        nom = e.get("name")
        if e.tag == "array" and nom == "bones":
            for st in e.findall("struct"):
                noms.append(st.findtext("string[@name='name']"))
        elif e.tag == "array" and nom == "parentIndices":
            parents = [int(x) for x in (e.text or "").split()]
        elif e.tag == "array" and nom == "referencePose":
            for v in e.findall("vec12"):
                vals = [struct.unpack("f", struct.pack("I", int(x[1:], 16)))[0]
                        for x in (v.text or "").split()]
                repos.append({"t": tuple(vals[0:3]),
                              "q": qnorm(tuple(vals[4:8])),
                              "s": tuple(vals[8:11])})
    return noms, parents, repos


def globaux(noms, parents, repos):
    """Transformations globales (position, quaternion) depuis les locales."""
    monde = [None] * len(noms)
    for i in range(len(noms)):
        p = parents[i]
        t, q = repos[i]["t"], repos[i]["q"]
        if p < 0:
            monde[i] = (t, q)
        else:
            tp, qp = monde[p]
            dt = qrot(qp, t)
            monde[i] = ((tp[0] + dt[0], tp[1] + dt[1], tp[2] + dt[2]), qmul(qp, q))
    return monde


def lire_repos_psa(chemin):
    """Repli : pose de repos du PSA (nom, parent, quaternion, translation).

    Meme convention que l'animation : Z haut, metres, quaternions (x, y, z, w).
    """
    with open(chemin, "r", encoding="utf-8-sig") as f:
        d = json.load(f)
    noms = [str(n).lower() for n in d["noms"]]
    parents = d["parents"]
    rq = d["repos_q"]
    rt = d["repos_t"]
    noeuds = [{"name": n, "children": []} for n in noms]
    parent = {}
    for i, p in enumerate(parents):
        if 0 <= p < len(noms):
            parent[i] = p
            noeuds[p]["children"].append(i)
    monde = [None] * len(noms)
    for i in range(len(noms)):
        t = (rt[i][0] * 0.01, rt[i][1] * 0.01, rt[i][2] * 0.01)
        q = qnorm(tuple(rq[i]))
        p = parent.get(i, -1)
        if p < 0:
            monde[i] = (t, q)
        else:
            tp, qp = monde[p]
            dt = qrot(qp, t)
            monde[i] = ((tp[0] + dt[0], tp[1] + dt[1], tp[2] + dt[2]),
                        qmul(qp, q))
    return {"nodes": noeuds}, parent, monde


def lire_glb_repos(chemin):
    """Squelette de repos du GLB, converti Y-haut -> Z-haut."""
    doc, _ = glb_lire.lire_glb(chemin)
    noeuds = doc.get("nodes", [])
    parent = {}
    for i, n in enumerate(noeuds):
        for c in n.get("children", []):
            parent[c] = i
    qx90 = (0.7071067811865476, 0.0, 0.0, 0.7071067811865476)
    qx90i = qconj(qx90)
    monde = [None] * len(noeuds)
    for i, n in enumerate(noeuds):
        t = n.get("translation", [0.0, 0.0, 0.0])
        # gltf (x, y, z) -> Blender/USD Z-haut (x, -z, y)
        tl = (t[0], -t[2], t[1])
        q = qnorm(tuple(n.get("rotation", [0.0, 0.0, 0.0, 1.0])))
        q = qmul(qmul(qx90, q), qx90i)
        p = parent.get(i, -1)
        if p < 0:
            monde[i] = (tl, q)
        else:
            tp, qp = monde[p]
            dt = qrot(qp, tl)
            monde[i] = ((tp[0] + dt[0], tp[1] + dt[1], tp[2] + dt[2]), qmul(qp, q))
    return doc, parent, monde


# ---------------------------------------------------------------------------
# correspondance Isshin -> Simon
# ---------------------------------------------------------------------------

CORRESPONDANCE = {
    "Master": "root",
    "Root": "pelvis",
    "Pelvis": "pelvis",
    "Spine": "spine_01",
    "Spine1": "spine_03",
    "Spine2": "spine_05",
    "Collar": "spine_05",
    "Neck": "neck_01",
    "Head": "head",
    "L_Clavicle": "clavicle_l",
    "L_Shoulder": "upperarm_l",
    "L_UpperArm": "upperarm_l",
    "L_Elbow": "lowerarm_l",
    "L_Forearm": "lowerarm_l",
    "L_ForeArmTwist": "lowerarm_l",
    "L_Hand": "hand_l",
    "L_Hip": "thigh_l",
    "L_Thigh": "thigh_l",
    "L_ThighTwist": "thigh_l",
    "L_ThighTwist1": "thigh_l",
    "L_Knee": "calf_l",
    "L_Calf": "calf_l",
    "L_CalfTwist": "calf_l",
    "L_CalfTwist1": "calf_l",
    "L_Foot": "foot_l",
    "L_FootTwist": "foot_l",
    "L_Toe0": "ball_l",
    "R_Clavicle": "clavicle_r",
    "R_Shoulder": "upperarm_r",
    "R_UpperArm": "upperarm_r",
    "R_Elbow": "lowerarm_r",
    "R_Forearm": "lowerarm_r",
    "R_ForeArmTwist": "lowerarm_r",
    "R_Hand": "hand_r",
    "R_Hip": "thigh_r",
    "R_Thigh": "thigh_r",
    "R_ThighTwist": "thigh_r",
    "R_ThighTwist1": "thigh_r",
    "R_Knee": "calf_r",
    "R_Calf": "calf_r",
    "R_CalfTwist": "calf_r",
    "R_CalfTwist1": "calf_r",
    "R_Foot": "foot_r",
    "R_FootTwist": "foot_r",
    "R_Toe0": "ball_r",
}


def main():
    anim_path, glb_path, skel_path, sortie = sys.argv[1:5]
    nb_sortie = int(sys.argv[5]) if len(sys.argv) > 5 else 439
    fps = float(sys.argv[6]) if len(sys.argv) > 6 else 60.0
    fps_src = float(sys.argv[7]) if len(sys.argv) > 7 else 30.0
    mode_racine = os.environ.get("RACINE", "vertical")
    facteur_vrille = float(os.environ.get("VRILLE", "1.0"))
    facteur_pelvis = os.environ.get("PELVIS_DELTA", "1") not in ("0", "non", "")
    print("vrille : %.2f   bassin en delta complet : %s" % (facteur_vrille, facteur_pelvis))

    # --- animation Simon
    entete, brut = lire_anim(anim_path)
    chemins = entete["chemins"]
    nb_os = entete["nb_os"]
    nb_images = entete["nb_images"]
    images_times = entete.get("images", list(range(nb_images)))
    duree = (nb_images - 1) / fps_src
    print("anim : %d os, %d images, %.3f s (%.3f i/s)" %
          (nb_os, nb_images, duree, fps_src))
    idx = {c: i for i, c in enumerate(chemins)}
    chemin_court = {}
    for c in chemins:
        chemin_court.setdefault(c.rsplit("/", 1)[-1].lower(), c)
    parent = {}
    for c in chemins:
        p = c.rsplit("/", 1)[0] if "/" in c else ""
        parent[c] = p if p in idx else None
    profondeur = {}
    for c in chemins:
        d, p = 0, parent[c]
        while p is not None:
            d += 1
            p = parent[p]
        profondeur[c] = d
    ordre = sorted(chemins, key=lambda c: profondeur[c])
    taille_ligne = 1 + 10 * nb_os
    decalage_tr = 1
    decalage_rot = 1 + 3 * nb_os

    print("anim : %d os, %d images, %.3f s (%.3f i/s)" %
          (nb_os, nb_images, duree, fps_src))

    # --- squelette Simon (bind) et Isshin (repos)
    if not os.path.exists(glb_path):
        repli = os.path.join(RACINE, "_work", "usda", "Simon_Skill_1_psa_repos.json")
        print("GLB absent (%s), repli sur %s" % (glb_path, repli))
        doc, parent_glb, monde_glb = lire_repos_psa(repli)
    else:
        doc, parent_glb, monde_glb = lire_glb_repos(glb_path)
    par_nom_glb = {}
    for i, n in enumerate(doc.get("nodes", [])):
        par_nom_glb[n.get("name", "")] = i

    noms_iss, parents_iss, repos_iss = lire_squelette(skel_path)
    monde_iss = globaux(noms_iss, parents_iss, repos_iss)
    idx_iss = {n: i for i, n in enumerate(noms_iss)}
    print("isshin : %d os" % len(noms_iss))

    # --- base commune
    def base_de(monde, idx, nom_pelvis, nom_haut, nom_gauche):
        p = monde[idx[nom_pelvis]][0]
        h = monde[idx[nom_haut]][0]
        g = monde[idx[nom_gauche]][0]
        haut = tuple(h[i] - p[i] for i in range(3))
        gauche = tuple(g[i] - p[i] for i in range(3))
        n = math.sqrt(sum(c * c for c in haut))
        haut = tuple(c / n for c in haut)
        avant = (haut[1] * gauche[2] - haut[2] * gauche[1],
                 haut[2] * gauche[0] - haut[0] * gauche[2],
                 haut[0] * gauche[1] - haut[1] * gauche[0])
        n = math.sqrt(sum(c * c for c in avant))
        avant = tuple(c / n for c in avant)
        # on rederive la gauche pour avoir une base orthonormee
        gauche = (avant[1] * haut[2] - avant[2] * haut[1],
                  avant[2] * haut[0] - avant[0] * haut[2],
                  avant[0] * haut[1] - avant[1] * haut[0])
        n = math.sqrt(sum(c * c for c in gauche))
        gauche = tuple(c / n for c in gauche)
        return gauche, haut, avant

    b_sim = base_de(monde_glb, par_nom_glb, "pelvis", "neck_01", "thigh_l")
    b_iss = base_de(monde_iss, idx_iss, "Pelvis", "Neck", "L_Thigh")
    print("base Simon (gauche, haut, avant) :", [tuple(round(c, 3) for c in v) for v in b_sim])
    print("base Isshin                      :", [tuple(round(c, 3) for c in v) for v in b_iss])
    # Les deux squelettes sont deja alignes : X = gauche, haut = +Z (Simon) / +Y
    # (Isshin), avant = haut x gauche.  On utilise donc la correspondance exacte
    # (x, y, z) Simon -> (x, z, -y) Isshin plutot que les bases mesurees (qui
    # portent l'inclinaison de la pose de repos).
    m = [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]
    print("matrice de passage Simon -> Isshin :", m)

    # --- jointures utiles : les os Simon mappes + leurs ancetres
    utiles = set()
    for nom_iss, nom_sim in CORRESPONDANCE.items():
        if nom_iss not in idx_iss:
            continue
        c = chemin_court.get(nom_sim)
        if c is None:
            continue
        while c is not None:
            utiles.add(c)
            c = parent[c]
    ordre_utile = [c for c in ordre if c in utiles]
    print("jointures utiles :", len(ordre_utile))

    # --- directions de repos (Simon) par os
    enfants_glb = {}
    for i, p in parent_glb.items():
        enfants_glb.setdefault(p, []).append(i)
    nom_par_noeud = {i: n.get("name", "") for i, n in enumerate(doc.get("nodes", []))}

    # chemin d'animation pour chaque os Simon (par nom court)
    chemin_par_os = {}
    for nom, i in par_nom_glb.items():
        ch = chemin_court.get(nom.lower())
        if ch is not None:
            chemin_par_os[nom] = ch

    def direction_repos(noeud):
        meilleur = None
        longueur = 0.0
        for c in enfants_glb.get(noeud, []):
            if nom_par_noeud[c] not in chemin_par_os:
                continue
            a = monde_glb[noeud][0]
            b = monde_glb[c][0]
            d = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
            n = math.sqrt(sum(x * x for x in d))
            if n > longueur:
                longueur = n
                meilleur = c
        if meilleur is None:
            return None, None
        a = monde_glb[noeud][0]
        b = monde_glb[meilleur][0]
        return (b[0] - a[0], b[1] - a[1], b[2] - a[2]), meilleur

    directions = {}
    enfants_suivis = {}
    for nom in par_nom_glb:
        d, e = direction_repos(par_nom_glb[nom])
        directions[nom] = d
        enfants_suivis[nom] = e

    # --- enfants suivis cote Isshin : l'enfant mappe le plus long, de role
    # different (on exclut les os qui renvoient au meme os Simon)
    iss_enfants = {}
    for i, p in enumerate(parents_iss):
        if p >= 0:
            iss_enfants.setdefault(p, []).append(i)
    iss_enf_suivi = {}
    for i, nom in enumerate(noms_iss):
        sim = CORRESPONDANCE.get(nom)
        if sim is None or sim not in chemin_par_os:
            continue
        a = monde_iss[i][0]
        meilleur, longueur = None, 0.02
        for c in iss_enfants.get(i, []):
            sim_c = CORRESPONDANCE.get(noms_iss[c])
            if sim_c is None or sim_c == sim or sim_c not in chemin_par_os:
                continue
            d = math.dist(a, monde_iss[c][0])
            if d > longueur:
                longueur, meilleur = d, c
        if meilleur is not None:
            iss_enf_suivi[i] = meilleur
    print("os Isshin orientes :", len(iss_enf_suivi), "/", len(noms_iss))
    i_pelvis = noms_iss.index("Pelvis") if "Pelvis" in noms_iss else -1

    # --- boucle images
    ref0_q = {}
    ref0_d = {}
    positions = [None] * nb_sortie
    for k in range(nb_sortie):
        t = k / fps
        image_src = min(nb_images - 1, int(round(t * fps_src)))
        base = image_src * taille_ligne
        ligne_tr = base + decalage_tr
        ligne_rot = base + decalage_rot

        monde = {}
        pos = {}
        for ch in ordre_utile:
            i = idx[ch]
            # rotations du .anim en (w, x, y, z)
            q = qnorm((brut[ligne_rot + 4 * i + 1], brut[ligne_rot + 4 * i + 2],
                       brut[ligne_rot + 4 * i + 3], brut[ligne_rot + 4 * i]))
            tr = (brut[ligne_tr + 3 * i] * 0.01,
                  brut[ligne_tr + 3 * i + 1] * 0.01,
                  brut[ligne_tr + 3 * i + 2] * 0.01)
            p = parent[ch]
            if p is None:
                monde[ch] = (tr, q)
            else:
                pq = monde[p][1]
                dt = qrot(pq, tr)
                pp = monde[p][0]
                monde[ch] = ((pp[0] + dt[0], pp[1] + dt[1], pp[2] + dt[2]), qmul(pq, q))

        # rotations cibles par os Isshin : on oriente l'os d'Isshin (sa direction
        # de repos) vers la direction animee de Simon, ramenee dans son repere.
        cibles = {}
        vrilles = []
        for i, nom_iss in enumerate(noms_iss):
            nom_sim = CORRESPONDANCE.get(nom_iss)
            if nom_sim is None:
                continue
            ch = chemin_par_os.get(nom_sim)
            if ch is None or ch not in monde:
                continue
            enfant = iss_enf_suivi.get(i)
            if enfant is None:
                continue
            nom_sim_c = CORRESPONDANCE[noms_iss[enfant]]
            ch2 = chemin_par_os.get(nom_sim_c)
            if ch2 is None or ch2 not in monde:
                continue
            pa = monde[ch][0]
            b = monde[ch2][0]
            d_sim = (b[0] - pa[0], b[1] - pa[1], b[2] - pa[2])
            if math.sqrt(sum(x * x for x in d_sim)) <= 1e-5:
                continue
            d_ref = mat_vec(m, d_sim)
            a2 = monde_iss[i][0]
            b2 = monde_iss[enfant][0]
            d_rest = (b2[0] - a2[0], b2[1] - a2[1], b2[2] - a2[2])
            cibles[nom_iss] = qmul(swing(d_rest, d_ref), monde_iss[i][1])
            # vrille : rotation de l'os autour de son propre axe, mesuree par
            # rapport a l'image 0 (la pose de repos du PSA ne coincide pas avec
            # celle de l'animation, donc un delta absolu serait faux).
            if facteur_vrille != 0.0 and nom_iss in ref0_q:
                delta_sim = qmul(monde[ch][1], qconj(ref0_q[nom_iss]))
                axe = ref0_d[nom_iss]
                sin_t = (delta_sim[0] * axe[0] + delta_sim[1] * axe[1]
                         + delta_sim[2] * axe[2])
                angle = 2.0 * math.atan2(sin_t, delta_sim[3])
                angle = max(-0.9, min(0.9, angle)) * facteur_vrille
                vrilles.append(abs(angle))
                cibles[nom_iss] = qmul(q_axe_angle(d_ref, angle), cibles[nom_iss])
            elif k == 0:
                n = math.sqrt(sum(c * c for c in d_sim))
                ref0_q[nom_iss] = monde[ch][1]
                ref0_d[nom_iss] = (d_sim[0] / n, d_sim[1] / n, d_sim[2] / n)

        # le bassin garde le lacet de Simon : son axe rachidien est presque
        # vertical, donc l'orientation seule ne le capte pas.  La rotation est
        # relative a l'image 0, pour ne pas dependre de la pose de repos.
        if facteur_pelvis and "Pelvis" in cibles:
            chp = chemin_par_os.get("pelvis")
            if chp is not None and chp in monde and "pelvis" in ref0_q:
                delta_p = qmul(monde[chp][1], qconj(ref0_q["pelvis"]))
                qm = rot_vers_quat(m)
                delta_p = qmul(qmul(qm, delta_p), qconj(qm))
                cibles["Pelvis"] = qmul(delta_p, cibles["Pelvis"])
            elif k == 0 and chp is not None and chp in monde:
                ref0_q["pelvis"] = monde[chp][1]
        if k == 0 and vrilles:
            print("vrille |deg| moyenne %.1f, max %.1f"
                  % (math.degrees(sum(vrilles) / len(vrilles)),
                     math.degrees(max(vrilles))))

        # la racine du squelette suit le bassin
        if "Root" in cibles and "Pelvis" in cibles:
            cibles["Root"] = cibles["Pelvis"]

        # translations locales (repos), sauf la racine qui porte le deplacement
        delta = (0.0, 0.0, 0.0)
        ch_pelvis = chemin_par_os.get("pelvis")
        if ch_pelvis is not None and ch_pelvis in monde:
            p0 = None
            if not hasattr(main, "_pelvis0"):
                main._pelvis0 = monde[ch_pelvis][0]
            p0 = main._pelvis0
            d = tuple(monde[ch_pelvis][0][i] - p0[i] for i in range(3))
            d_iss = mat_vec(m, d)
            if mode_racine == "vertical":
                d_iss = (0.0, d_iss[1], 0.0)
            elif mode_racine == "aucune":
                d_iss = (0.0, 0.0, 0.0)
            delta = d_iss

        pistes = []
        monde_p = [None] * len(noms_iss)
        for i, nom in enumerate(noms_iss):
            p = parents_iss[i]
            repos_t = repos_iss[i]["t"]
            repos_q = repos_iss[i]["q"]
            if nom in cibles:
                w = cibles[nom]
            elif p >= 0 and monde_p[p] is not None:
                w = qmul(monde_p[p], repos_q)
            else:
                w = repos_q
            if p >= 0 and monde_p[p] is not None:
                rot = qmul(qconj(monde_p[p]), w)
            else:
                rot = w
            monde_p[i] = w
            tr = repos_t
            if nom == "Root":
                # deplacement monde -> repere du parent (Master), rotation animee
                rp = cibles.get("Master", monde_iss[parents_iss[i]][1] if p >= 0 else (0.0, 0.0, 0.0, 1.0))
                dl = qrot(qconj(rp), delta)
                tr = (repos_t[0] + dl[0], repos_t[1] + dl[1], repos_t[2] + dl[2])
            pistes.append((tr, rot, (1.0, 1.0, 1.0)))
        positions[k] = pistes

    # --- ecriture
    with open(sortie, "wb") as f:
        f.write(json.dumps({"nb_images": nb_sortie, "nb_pistes": len(noms_iss),
                            "fps": fps, "noms": noms_iss}).encode("utf-8") + b"\n")
        tampon = array.array("f")
        for image in positions:
            for tr, q, s in image:
                tampon.extend((tr[0], tr[1], tr[2], q[0], q[1], q[2], q[3],
                               s[0], s[1], s[2]))
        tampon.tofile(f)
    print("ecrit :", sortie, os.path.getsize(sortie), "octets")


if __name__ == "__main__":
    main()
