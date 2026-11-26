"""
Balayage de toutes les animations de c5400.anibnd.

Pour chaque animation : conversion en GLB (via havok_toolset, comme hkx_glb.py
mais en reutilisant un dossier de travail unique), puis mesure, sur plusieurs
instants, du plus grand deplacement d'un os par rapport a sa pose de reference.

Un os qui s'eloigne de plusieurs metres de sa position de repos, alors que des
sommets du modele lui sont attaches, produit forcement des triangles geants.

On ignore les os manifestement "mous" (Wire_*, *_Target*, *Skirt*, SpineArmor*,
Eyeball*), qui sont pilotes par la simulation de tissu et dont le repos dans le
FLVER n'a pas de sens.

Usage :
    python tools/hkx_balayage.py [nombreEchantillons]
"""

import os
import shutil
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import glb_lire
import hkx_pose

ANIBND = os.path.join(RACINE, "_work", "extracted", "c5400.anibnd")
TRAVAIL = os.path.join(RACINE, "_work", "hkx_balayage")
OUTIL = os.path.join(
    RACINE, "_work", "tools", "FLVER_Editor_X2.7", "Debug", "tools", "HavokToolset"
)

GABARIT = (
    '<hk_to_gltf extension-patterns="">'
    '<animation blend-override="AUTO" sample-rate="60" scale-type="INDEPENDENT" filename-anims="true" />'
    '<skeleton skeleton-path="{squelette}" generation="DEFAULT" visualize="false" create-root-node="false" />'
    '<scene units="METER" custom-scale="1" up-axis="Y+" forward-axis="Z+" right-handed="true" />'
    "</hk_to_gltf>"
)

EXCLUS = ("Wire", "Target", "Skirt", "SpineArmor", "Eyeball")

FOCUS = os.path.join(RACINE, "_work", "os_du_modele.tsv")


def charger_focus():
    """Os reellement utilises par le modele : {nom: nombre de sommets}."""
    if not os.path.isfile(FOCUS):
        return None
    table = {}
    with open(FOCUS, "r", encoding="utf-8") as f:
        for ligne in f:
            c = ligne.rstrip("\n").split("\t")
            if len(c) >= 2:
                table[c[0]] = int(c[1])
    return table or None


def ignorer(nom):
    for motif in EXCLUS:
        if motif in nom:
            return True
    return False


def preparer():
    """Dossier de travail unique : outil, modules, squelette, un compendium."""
    if os.path.isdir(TRAVAIL):
        shutil.rmtree(TRAVAIL, ignore_errors=True)
    os.makedirs(os.path.join(TRAVAIL, "modules"))

    shutil.copy2(os.path.join(OUTIL, "havok_toolset.exe"),
                 os.path.join(TRAVAIL, "havok_toolset.exe"))
    modules = os.path.join(OUTIL, "modules")
    for nom in os.listdir(modules):
        if nom.lower().endswith(".spk"):
            shutil.copy2(os.path.join(modules, nom),
                         os.path.join(TRAVAIL, "modules", nom))

    shutil.copy2(os.path.join(ANIBND, "skeleton.hkx"),
                 os.path.join(TRAVAIL, "skeleton.hkx"))
    for nom in sorted(os.listdir(ANIBND)):
        if nom.lower().endswith(".compendium"):
            shutil.copy2(os.path.join(ANIBND, nom),
                         os.path.join(TRAVAIL, "animation.compendium"))
            break

    with open(os.path.join(TRAVAIL, "havok_toolset.config"), "w", encoding="utf-8") as f:
        f.write(GABARIT.format(squelette=os.path.join(TRAVAIL, "skeleton.hkx")))


def convertir(nom_animation):
    """Convertit une animation ; retourne le chemin du GLB, ou None."""
    glb = os.path.join(TRAVAIL, "animation.glb")
    if os.path.isfile(glb):
        os.remove(glb)
    shutil.copy2(os.path.join(ANIBND, nom_animation),
                 os.path.join(TRAVAIL, "animation.hkx"))
    proc = subprocess.run(
        [os.path.join(TRAVAIL, "havok_toolset.exe"), "hk_to_gltf", "animation.hkx"],
        cwd=TRAVAIL, capture_output=True, text=True, timeout=180,
    )
    if proc.returncode != 0 or not os.path.isfile(glb):
        return None
    return glb


def mesurer(glb, echantillons, focus):
    """
    Plus grand ecart, sur l'animation, entre la translation LOCALE d'un os et
    celle de sa pose de reference.

    Un squelette est rigide : hors os d'attachement (fourreau, lance dans le
    dos, cibles de pied, tissu), la translation locale d'un os est CONSTANTE.
    Un os dont la translation locale varie se deplace donc par rapport a son
    parent, et les sommets qui lui sont attaches partent avec lui : c'est
    exactement ce qui fabrique des triangles geants.
    """
    doc, binaire = glb_lire.lire_glb(glb)
    noeuds = doc["nodes"]
    noms = [n.get("name", "") for n in noeuds]
    ref_t = [list(n.get("translation", [0.0, 0.0, 0.0])) for n in noeuds]

    # duree : fin de la premiere piste
    duree = 3.0
    for anim in doc.get("animations", []):
        for ech in anim.get("samplers", []):
            vals = glb_lire.lire_accesseur(doc, binaire, ech["input"])
            if vals:
                duree = max(duree, vals[-1][0])
        break

    pire = (0.0, "", 0.0, 0)
    for k in range(echantillons):
        t = duree * k / float(max(1, echantillons - 1))
        loc_t, _, _ = hkx_pose.valeurs_a_instant(doc, binaire, t)
        for i, nom in enumerate(noms):
            if focus is not None:
                if nom not in focus:
                    continue
            elif ignorer(nom):
                continue
            d = ((loc_t[i][0] - ref_t[i][0]) ** 2
                 + (loc_t[i][1] - ref_t[i][1]) ** 2
                 + (loc_t[i][2] - ref_t[i][2]) ** 2) ** 0.5
            if d > pire[0]:
                pire = (d, nom, t, focus.get(nom, 0) if focus else 0)
    return pire


def main():
    echantillons = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    limite = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    preparer()

    fichiers = sorted(n for n in os.listdir(ANIBND) if n.lower().endswith(".hkx")
                      and n.lower() != "skeleton.hkx")
    if limite > 0:
        fichiers = fichiers[:limite]
    print("animations a tester :", len(fichiers))
    print("echantillons par animation :", echantillons)
    focus = charger_focus()
    if focus is None:
        print("os suivis : tous (sauf Wire/Target/Skirt/SpineArmor/Eyeball)")
    else:
        print("os suivis : les %d os reellement utilises par le modele (table %s)"
              % (len(focus), focus and os.path.basename(FOCUS)))
    print()
    print("%-22s %10s  %-26s %8s %8s" % ("animation", "depl max", "os", "instant", "sommets"))
    print("-" * 84)

    resultats = []
    echecs = 0
    for k, nom in enumerate(fichiers):
        glb = convertir(nom)
        if glb is None:
            echecs += 1
            print("%-22s   ECHEC DE CONVERSION" % nom)
            continue
        try:
            d, os_nom, t, n = mesurer(glb, echantillons, focus)
        except Exception as e:
            echecs += 1
            print("%-22s   ERREUR : %s" % (nom, e))
            continue
        resultats.append((d, nom, os_nom, t, n))
        print("%-22s %8.3f m  %-26s %8.2f s %8d" % (nom, d, os_nom, t, n))
        sys.stdout.flush()

    print()
    print("=== les 15 animations les plus violentes ===")
    resultats.sort(reverse=True)
    for d, nom, os_nom, t, n in resultats[:15]:
        print("  %-22s %8.3f m  %-26s a %.2f s  (%d sommets)" % (nom, d, os_nom, t, n))
    print()
    print("echecs :", echecs)


if __name__ == "__main__":
    main()
