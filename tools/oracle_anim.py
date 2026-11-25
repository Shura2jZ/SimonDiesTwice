"""
Oracle d'animation hors-jeu.

1) convertit une animation HKX de c5400 en GLB (havok_toolset, comme hkx_glb) ;
2) echantillonne quelques instants et ecrit, pour chacun, un TSV de matrices
   monde d'os exprimees dans le repere du FLVER (hkx_pose.py oracle) ;
3) lance FlverDeforme.exe sur la vanille ET sur notre build avec EXACTEMENT la
   meme pose, pour comparer ce que le moteur ferait des deux.

FlverDeforme applique p = somme(poids * pose * bind^-1 * v) et imprime un
rapport : deplacement max par maillage, somme des poids, os les plus violents.

Aucune ecriture dans les dossiers de jeu.

Usage :
    python tools/oracle_anim.py [animation.hkx] [t1,t2,...]
"""
import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import hkx_balayage          # noqa: E402
import hkx_pose              # noqa: E402

VANILLE = os.path.join(RACINE, "_work", "extracted", "c5400.chrbnd", "c5400.flver")
NOTRE = os.environ.get("ORACLE_MODELE", os.path.join(RACINE, "_work", "simon_wl.flver"))
TSV = os.path.join(RACINE, "_work", "isshin_nodes.tsv")
DEFORME = os.path.join(RACINE, "_work", "tools", "cs", "FlverDeforme.exe")
SORTIE = os.path.join(RACINE, "_work", "oracle")


def main():
    animation = sys.argv[1] if len(sys.argv) > 1 else "a000_003011.hkx"
    instants = [float(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["0.30", "0.80", "1.50"])]

    os.makedirs(SORTIE, exist_ok=True)

    print("=== preparation du dossier havok ===", flush=True)
    hkx_balayage.preparer()
    glb = hkx_balayage.convertir(animation)
    if glb is None:
        raise SystemExit("conversion HKX -> GLB echouee pour %s" % animation)
    print("GLB : %s (%d octets)" % (glb, os.path.getsize(glb)), flush=True)

    poses = []
    for t in instants:
        sortie = os.path.join(SORTIE, "pose_%05.2f.tsv" % t)
        print()
        print("=== instant %.2f s ===" % t, flush=True)
        hkx_pose.oracle(glb, TSV, t, sortie)
        poses.append((t, sortie))

    for nom, modele in (("vanille", VANILLE), ("notre", NOTRE)):
        for t, pose in poses:
            sortie = os.path.join(SORTIE, "deforme_%s_%05.2f.flver" % (nom, t))
            print()
            print("#" * 78)
            print("### %s   t = %.2f s   ->  %s" % (nom.upper(), t, os.path.basename(sortie)))
            print("#" * 78, flush=True)
            p = subprocess.run([DEFORME, modele, pose, sortie],
                               capture_output=True, text=True, timeout=900)
            if p.returncode != 0:
                print("ECHEC :", p.returncode, p.stdout[-2000:], p.stderr[-2000:])
                continue
            print(p.stdout)
    print()
    print("modeles deformes ecrits dans", SORTIE)


if __name__ == "__main__":
    main()
