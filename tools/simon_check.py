"""
Controle de l'orientation et des proportions de Simon (fichier .glb) avant
portage, en comparant aux conventions de Sekiro etablies sur Isshin :

    FLVER (Sekiro) : X = droite, Y = haut, avant = -Z
    donc un personnage a la main GAUCHE en +X, les orteils en -Z par rapport
    a la cheville, les pieds poses sur Y = 0.

Ce script mesure ces trois proprietes sur le modele source et en deduit la
transformation d'axes a appliquer. Il ne modifie rien.

Usage :
    python tools/simon_check.py modele.glb
"""

import sys

import glb_model
import mat4

# os attendus dans un squelette UE (Simon vient d'Unreal Engine 5.4)
CLES = ["pelvis", "spine_01", "neck_01", "head",
        "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
        "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
        "thigh_l", "calf_l", "foot_l", "ball_l",
        "thigh_r", "calf_r", "foot_r", "ball_r"]


def positions_os(g):
    joints, binds = g.skin(0)
    noms = g.bone_names(joints)
    pos = {}
    for nom, mat in zip(noms, binds):
        pos[nom] = mat4.get_translation(mat)
    return pos


def trouve(pos, motif):
    """Cherche un os par nom exact, sinon par suffixe (insensible a la casse)."""
    for nom, p in pos.items():
        if nom.lower() == motif:
            return nom, p
    for nom, p in pos.items():
        if nom.lower().endswith(motif):
            return nom, p
    return None, None


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    g = glb_model.Glb(sys.argv[1])
    g.report()
    print()

    pos = positions_os(g)
    print("=== os cles (position dans la pose de reference, espace du fichier) ===")
    for motif in CLES:
        nom, p = trouve(pos, motif)
        if nom is None:
            print("    %-14s absent" % motif)
        else:
            print("    %-14s %s   %s" % (motif, mat4.fmt(p), nom))
    print()

    lo, hi, nverts = g.vertex_bounds()
    print("hauteur des sommets : %.4f  (Y de %.4f a %.4f)" % (hi[1] - lo[1], lo[1], hi[1]))
    print()

    # --- controles d'orientation ---
    print("=== controles d'orientation ===")
    _, main_g = trouve(pos, "hand_l")
    _, main_d = trouve(pos, "hand_r")
    _, pied_g = trouve(pos, "foot_l")
    _, orteil_g = trouve(pos, "ball_l")
    _, bassin = trouve(pos, "pelvis")

    if main_g and main_d:
        axe = "X" if abs(main_g[0]) > abs(main_g[2]) else "Z"
        print("    main gauche %s / main droite %s" % (mat4.fmt(main_g), mat4.fmt(main_d)))
        print("    separation des mains : %.4f  (ecart selon %s)" % (abs(main_g[0] - main_d[0]), "X"))
        print("    -> la main gauche est en X %s (Sekiro attend +X pour la gauche)"
              % ("POSITIF" if main_g[0] > 0 else "NEGATIF"))
    if pied_g and orteil_g:
        dz = orteil_g[2] - pied_g[2]
        print("    cheville gauche %s   orteil gauche %s" % (mat4.fmt(pied_g), mat4.fmt(orteil_g)))
        print("    orteil - cheville en Z : %+.4f" % dz)
        print("    -> le personnage regarde vers Z %s (Sekiro attend l'avant en -Z)"
              % ("POSITIF" if dz > 0 else "NEGATIF"))
    if pied_g:
        print("    pied gauche en Y : %+.4f  (Sekiro attend les pieds vers Y = 0)" % pied_g[1])
    if bassin:
        print("    bassin en Y : %+.4f  (Isshin : 1.245)" % bassin[1])
    print()

    # --- conclusion sur les axes ---
    print("=== transformation d'axes a appliquer ===")
    neg_x = main_g is not None and main_g[0] < 0
    neg_z = pied_g is not None and orteil_g is not None and (orteil_g[2] - pied_g[2]) > 0
    print("    inverser X : %s" % ("oui" if neg_x else "non"))
    print("    inverser Z : %s" % ("oui" if neg_z else "non"))
    if neg_x and neg_z:
        print("    => rotation de 180 degres autour de Y : (x, y, z) -> (-x, y, -z)")
        print("       (rotation pure : ne change pas le sens des faces)")
    elif not neg_x and not neg_z:
        print("    => aucune transformation : (x, y, z) -> (x, y, z)")
    else:
        print("    => combinaison incoherente avec une rotation pure : a examiner")
    return 0


if __name__ == "__main__":
    main()
