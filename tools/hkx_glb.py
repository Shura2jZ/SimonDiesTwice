"""
Convertit un couple (squelette.hkx, animation.hkx) en GLB.

Reproduit exactement l'invocation du code de reference (MySFformat
src/HkxAnimationClip.cs) : copie privee de l'outil et de ses modules dans un
dossier de travail jetable, configuration XML explicite, puis lancement de
`havok_toolset.exe hk_to_gltf animation.hkx`.

Le GLB produit contient A LA FOIS :
  - les noeuds du squelette (nom, hierarchie, translation/rotation/echelle de
    la pose de reference) ;
  - les pistes d'animation echantillonnees.

On peut donc, hors du jeu, comparer la pose de reference du squelette a celle
des noeuds d'un FLVER, et rejouer une vraie animation.

Usage :
    python tools/hkx_glb.py <squelette.hkx> <animation.hkx> <sortie.glb>
"""

import os
import shutil
import subprocess
import sys
import tempfile
import uuid

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_OUTIL = os.path.join(
    RACINE, "_work", "tools", "FLVER_Editor_X2.7", "Debug", "tools", "HavokToolset"
)

GABARIT_CONFIG = (
    '<hk_to_gltf extension-patterns="">'
    '<animation blend-override="AUTO" sample-rate="60" scale-type="INDEPENDENT" filename-anims="true" />'
    '<skeleton skeleton-path="{squelette}" generation="DEFAULT" visualize="false" create-root-node="false" />'
    '<scene units="METER" custom-scale="1" up-axis="Y+" forward-axis="Z+" right-handed="true" />'
    "</hk_to_gltf>"
)


def convertir(squelette: str, animation: str, sortie: str, garder: bool = False) -> str:
    """Retourne le journal de conversion. Leve une exception en cas d'echec."""
    outil = os.path.join(DOSSIER_OUTIL, "havok_toolset.exe")
    modules = os.path.join(DOSSIER_OUTIL, "modules")
    if not os.path.isfile(outil):
        raise FileNotFoundError("havok_toolset.exe introuvable : " + outil)

    travail = os.path.join(
        RACINE, "_work", "hkx_work", uuid.uuid4().hex
    )
    os.makedirs(os.path.join(travail, "modules"), exist_ok=True)

    shutil.copy2(outil, os.path.join(travail, "havok_toolset.exe"))
    for nom in os.listdir(modules):
        if nom.lower().endswith(".spk"):
            shutil.copy2(os.path.join(modules, nom), os.path.join(travail, "modules", nom))

    shutil.copy2(squelette, os.path.join(travail, "skeleton.hkx"))
    shutil.copy2(animation, os.path.join(travail, "animation.hkx"))

    # Les animations Sekiro renvoient a un "compendium" externe : un packfile
    # Havok de types pose a cote d'elles dans l'anibnd. L'outil le cherche par
    # motif dans le dossier de travail et refuse d'en trouver plusieurs : on en
    # copie donc exactement un seul.
    dossier_animation = os.path.dirname(os.path.abspath(animation))
    for nom in sorted(os.listdir(dossier_animation)):
        if nom.lower().endswith(".compendium"):
            shutil.copy2(
                os.path.join(dossier_animation, nom),
                os.path.join(travail, "animation.compendium"),
            )
            break

    chemin_squelette = os.path.join(travail, "skeleton.hkx")
    with open(os.path.join(travail, "havok_toolset.config"), "w", encoding="utf-8") as f:
        f.write(GABARIT_CONFIG.format(squelette=chemin_squelette))

    proc = subprocess.run(
        [os.path.join(travail, "havok_toolset.exe"), "hk_to_gltf", "animation.hkx"],
        cwd=travail,
        capture_output=True,
        text=True,
        timeout=180,
    )
    journal = (proc.stdout or "") + (proc.stderr or "")

    produit = os.path.join(travail, "animation.glb")
    if proc.returncode != 0 or not os.path.isfile(produit):
        if not garder:
            shutil.rmtree(travail, ignore_errors=True)
        raise RuntimeError(
            "conversion impossible (code %s)\n%s\n-- dossier : %s"
            % (proc.returncode, journal, travail)
        )

    os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True)
    shutil.copy2(produit, sortie)
    if not garder:
        shutil.rmtree(travail, ignore_errors=True)
    return journal


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    journal = convertir(sys.argv[1], sys.argv[2], sys.argv[3])
    print(journal.strip() or "(aucun journal)")
    print("OK ->", sys.argv[3], os.path.getsize(sys.argv[3]), "octets")


if __name__ == "__main__":
    main()
