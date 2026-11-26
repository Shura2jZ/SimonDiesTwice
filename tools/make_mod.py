"""
Phase 1 : fabriquer `c5400.chrbnd.dcx` modde (mesh remplace) et l'installer.

Chaine, toutes briques validees par round-trip :
    FLVER modde -> BND4 reconstruit (byte-identique si rien ne change)
                -> DCX (Oodle Kraken) -> fichier de mod

SECURITE : par defaut on ecrit dans `_work/mod/` (jamais dans le dossier du
jeu). L'installation dans `<jeu>\\mods\\chr\\` demande le drapeau explicite
`--install`.

Usage :
    python tools/make_mod.py <flver_modde.flver> [--install]
    python tools/make_mod.py <flver_modde.flver> --vanilla <autre.chrbnd.dcx>
    python tools/make_mod.py <flver_modde.flver> --sans-clm2

Le fichier de tissu `c5400_c.clm2` est reecrit en automatique : il contient une
liste dont CHAQUE element correspond a un maillage du FLVER, dans le meme ordre.
Les donnees d'origine ne concernent que les 4 maillages de tissu simule
(indices 21 a 24) ; comme nous n'avons plus que 5 maillages, le jeu lit hors de
la liste et le tissu explose en jeu. On ecrit donc un CLM2 ayant exactement
autant d'elements que notre FLVER, tous vides : plus aucun tissu simule.
`--sans-clm2` garde le fichier d'origine (diagnostic).
"""

import os
import shutil
import struct
import subprocess
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil
import bnd4_build
import dcx_build
import gx_fix

GAME_ROOT = r"F:\Games\Sekiro - Shadows Die Twice"
VANILLA_CHRBND = os.path.join(GAME_ROOT, "chr", "c5400.chrbnd.dcx")
INNER_NAME = "c5400.flver"
INNER_CLM2 = "c5400_c.clm2"

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT, "_work", "mod", "chr")
OUT_NAME = "c5400.chrbnd.dcx"
CLM2_TOOL = os.path.join(PROJECT, "_work", "tools", "cs", "Clm2Tool.exe")
OUTIL_040 = os.path.join(PROJECT, "_work", "tools", "cs", "FlverEntete040.exe")
TMP_SOULS = os.path.join(PROJECT, "_work", "tmp")


def corriger_entete_040(donnees: bytes) -> bytes:
    """Recalcule les deux compteurs de faces de l'en-tete FLVER (voir FlverEntete040.cs).

    Mesure (regle exacte sur la vanille de c5400) :
      0x40 = triangles des facesets SANS le drapeau MotionBlur (0x80000000)
      0x44 = triangles de tous les facesets
    SoulsFormats ecrit le total dans LES DEUX champs. L'injecteur corrige 0x40,
    mais tout passage ulterieur par SoulsFormats (FlverComplete, FlverOsForce,
    ...) le reecrase : cette etape doit donc etre la derniere avant l'empaquetage.
    """
    if not os.path.exists(OUTIL_040):
        raise SystemExit(f"ERREUR : outil absent : {OUTIL_040}")
    os.makedirs(TMP_SOULS, exist_ok=True)
    entree = os.path.join(TMP_SOULS, "entete040_entree.flver")
    sortie = os.path.join(TMP_SOULS, "entete040_sortie.flver")
    with open(entree, "wb") as h:
        h.write(donnees)
    resultat = subprocess.run([OUTIL_040, entree, sortie],
                              capture_output=True, text=True)
    for ligne in (resultat.stdout or "").splitlines():
        print("entete 0x40/0x44: " + ligne.strip())
    if resultat.returncode != 0:
        print(resultat.stderr or "")
        raise SystemExit("ERREUR : correction de l'en-tete 0x40/0x44 impossible")
    with open(sortie, "rb") as h:
        return h.read()


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    install = "--install" in sys.argv
    vanilla_path = VANILLA_CHRBND
    if "--vanilla" in sys.argv:
        vanilla_path = sys.argv[sys.argv.index("--vanilla") + 1]

    if not args:
        print(__doc__)
        sys.exit(1)

    flver_path = args[0]
    modded = open(flver_path, "rb").read()
    if modded[:5] != b"FLVER":
        print(f"ERREUR : {flver_path} ne commence pas par 'FLVER' (magic={modded[:5]!r})")
        sys.exit(2)
    print(f"FLVER modde   : {flver_path}  ({len(modded):,} octets)")

    # --- correction du defaut d'ecriture des listes GX (voir tools/gx_fix.py)
    # SoulsFormats reeecrit bout a bout les listes GX qui se chevauchent dans les
    # fichiers FromSoft, ce qui duplique un bloc de 64 octets et decale tout le
    # reste. Mesure : sans cette correction, la version vanilla de la geometrie
    # suffit deja a faire exploser le rendu en jeu.
    avant_gx = modded
    modded, _, rapport_gx, gain_gx = gx_fix.corriger(modded)
    for ligne in rapport_gx:
        print("GX            : " + ligne.strip())
    ok_gx, msg_gx = gx_fix.verifie(avant_gx, modded)
    if not ok_gx:
        print(f"ERREUR : correction GX incoherente ({msg_gx})")
        sys.exit(5)
    if len(modded) != len(avant_gx):
        print(f"GX            : {len(avant_gx):,} -> {len(modded):,} octets ({-gain_gx:+d})")
    else:
        print("GX            : rien a corriger (liste GX deja conforme)")
    print(f"FLVER corrige : {len(modded):,} octets")

    # --- correction des deux compteurs de faces de l'en-tete (0x40 et 0x44)
    # A faire EN DERNIER : c'est la seule etape qui restaure 0x40 apres les
    # passages par SoulsFormats. Voir corriger_entete_040 ci-dessus.
    modded = corriger_entete_040(modded)

    vanilla = soulsutil.load(vanilla_path)
    old_size = next(e["size"] for e in bnd4_build.list_entries(vanilla)[4]
                    if bnd4_build.basename_of(e["fullname"]) == INNER_NAME)
    print(f"chrbnd vanilla: {vanilla_path}  ({len(vanilla):,} octets decompresses)")
    print(f"  {INNER_NAME} vanilla : {old_size:,} octets  ->  modde : {len(modded):,} "
          f"({len(modded) - old_size:+,})")

    # --- fichier de tissu : meme nombre d'elements que notre FLVER, tous vides
    remplacements = {INNER_NAME: modded}
    if "--sans-clm2" in sys.argv:
        print(f"  {INNER_CLM2}         : conserve tel quel (--sans-clm2)")
    else:
        nb_maillages = struct.unpack_from("<I", modded, 0x20)[0]
        _, _, _, data_off, entrees = bnd4_build.list_entries(vanilla)
        entree = next(e for e in entrees
                      if bnd4_build.basename_of(e["fullname"]) == INNER_CLM2)
        brut = vanilla[entree["offset"]:entree["offset"] + entree["size"]]
        source = os.path.join(PROJECT, "_work", "clm2_source.clm2")
        cible = os.path.join(PROJECT, "_work", "clm2_mod.clm2")
        with open(source, "wb") as fh:
            fh.write(brut)
        if not os.path.exists(CLM2_TOOL):
            print(f"ERREUR : {CLM2_TOOL} absent (compiler avec tools\\cs_build.ps1 Clm2Tool)")
            sys.exit(4)
        res = subprocess.run([CLM2_TOOL, "reduire", source, cible, str(nb_maillages)],
                             capture_output=True, text=True)
        if res.returncode != 0:
            print("ERREUR : Clm2Tool a echoue")
            print(res.stdout, res.stderr)
            sys.exit(4)
        clm2 = open(cible, "rb").read()
        remplacements[INNER_CLM2] = clm2
        print(f"  {INNER_CLM2}         : {len(brut)} octets vanilla  ->  {len(clm2)} "
              f"({nb_maillages} elements, tous vides)")

    new_bnd = bnd4_build.rebuild(vanilla, remplacements)
    print(f"BND4 reconstruit : {len(new_bnd):,} octets")

    dcx = dcx_build.build_dcx(new_bnd)
    print(f"DCX final        : {len(dcx):,} octets")

    # --- verification complete : on relit ce qu'on vient d'ecrire ---
    back = soulsutil.decompress_dcx(dcx)
    ok_data = back == new_bnd
    entries = bnd4_build.list_entries(back)[4]
    e0 = next(e for e in entries if bnd4_build.basename_of(e["fullname"]) == INNER_NAME)
    extracted = back[e0["offset"]:e0["offset"] + e0["size"]]
    ok_flver = extracted == modded
    ligne_clm2 = "non remplace"
    if INNER_CLM2 in remplacements:
        e1 = next(e for e in entries if bnd4_build.basename_of(e["fullname"]) == INNER_CLM2)
        tire = back[e1["offset"]:e1["offset"] + e1["size"]]
        ok_clm2 = tire == remplacements[INNER_CLM2]
        ligne_clm2 = f"c5400_c.clm2 relu identique={ok_clm2}"
        if not ok_clm2:
            print("ERREUR : le CLM2 relu differe.")
            sys.exit(3)
    print(f"verification     : BND4 relu identique={ok_data} | {INNER_NAME} relu identique={ok_flver}"
          f" | {ligne_clm2}")
    if not (ok_data and ok_flver):
        print("ERREUR : la relecture ne redonne pas les memes donnees.")
        sys.exit(3)

    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, OUT_NAME)
    with open(dest, "wb") as fh:
        fh.write(dcx)
    print(f"ecrit            : {dest}")

    if install:
        target_dir = os.path.join(GAME_ROOT, "mods", "chr")
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, OUT_NAME)
        shutil.copy2(dest, target)
        print(f"INSTALLE         : {target}")
    else:
        print("(non installe : ajoute --install pour copier dans <jeu>\\mods\\chr\\)")


if __name__ == "__main__":
    main()
