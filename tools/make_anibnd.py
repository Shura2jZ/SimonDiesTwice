"""
Fabrique `c5400.anibnd.dcx` (squelette + ~280 animations) pour la surcharge `mods\\`.

Chaine : DCX -> BND4 -> remplacements -> BND4 -> DCX (Oodle/KRAK maison).

Sans `--remplacer`, le BND4 produit doit etre **octet pour octet** celui du jeu :
seul le conteneur DCX change. C'est le temoin de la chaine d'ecriture, et le
socle du portage du moveset.

Usage :
    python tools/make_anibnd.py
    python tools/make_anibnd.py --install
    python tools/make_anibnd.py --remplacer a000_003000.hkx _work\\a000_003000_mod.hkx [--install]

Sorties uniquement dans `_work/` (et `mods/` avec `--install`, avec sauvegarde).
"""
import os
import shutil
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import bnd4_build      # noqa: E402
import dcx_build       # noqa: E402
import soulsutil       # noqa: E402

GAME = r"F:\Games\Sekiro - Shadows Die Twice"
VANILLE = os.path.join(GAME, "chr", "c5400.anibnd.dcx")
CIBLE_MODS = os.path.join(GAME, "mods", "chr", "c5400.anibnd.dcx")
SORTIE = os.path.join(RACINE, "_work", "mod", "chr", "c5400.anibnd.dcx")
SAUVEGARDE = os.path.join(RACINE, "_work", "mod_backup")


def main() -> None:
    args = sys.argv[1:]
    install = "--install" in args

    remplacements = {}
    if "--remplacer" in args:
        i = args.index("--remplacer")
        nom, chemin = args[i + 1], args[i + 2]
        blob = open(chemin, "rb").read()
        remplacements[nom] = blob
        print("Remplacement  : %s = %s (%d octets)" % (nom, chemin, len(blob)))
    if "--tous" in args:
        i = args.index("--tous")
        blob = open(args[i + 1], "rb").read()
        remplacements["*"] = blob
        print("Remplacement total : %s (%d octets)" % (args[i + 1], len(blob)))
    if "--liste" in args:
        i = args.index("--liste")
        blob = open(args[i + 2], "rb").read()
        for nom in args[i + 1].split(","):
            nom = nom.strip()
            if nom:
                remplacements[nom] = blob
        print("Remplacement liste : %d fichiers = %s" % (len(remplacements), args[i + 2]))

    vanilla = soulsutil.load(VANILLE)
    print("anibnd vanilla: %s" % VANILLE)
    print("  BND4 decompresse : %d octets" % len(vanilla))

    fc, eo, es, data_off, ents = bnd4_build.list_entries(vanilla)
    print("  entrees : %d   dataOffset = 0x%X   taille entree = 0x%X" % (fc, data_off, es))

    if "*" in remplacements:
        blob = remplacements.pop("*")
        n = 0
        for e in ents:
            base = bnd4_build.basename_of(e["fullname"])
            if base.endswith(".hkx") and base.lower() != "skeleton.hkx":
                remplacements[base] = blob
                n += 1
        print("Remplacement total : %d animations .hkx (squelette conserve)" % n)

    if remplacements:
        connus = {bnd4_build.basename_of(e["fullname"]) for e in ents}
        for nom in remplacements:
            if nom not in connus:
                print("ERREUR : %r n'est pas une entree de l'anibnd" % nom)
                sys.exit(3)
            for e in ents:
                if bnd4_build.basename_of(e["fullname"]) == nom:
                    if len(remplacements) <= 12:
                        print("  %-24s vanilla %8d o  ->  %8d o  (%+d)"
                              % (nom, e["size"], len(remplacements[nom]),
                                 len(remplacements[nom]) - e["size"]))

    nouveau_bnd = bnd4_build.rebuild(vanilla, remplacements)

    # `rebuild` aligne chaque fichier, y compris le dernier : le vanilla, lui,
    # s'arrete net. On retire ce remplissage final pour rester au plus pres.
    en_trop = len(nouveau_bnd) - len(vanilla)
    if en_trop > 0 and nouveau_bnd[-en_trop:] == b"\0" * en_trop:
        nouveau_bnd = nouveau_bnd[:len(vanilla)]
        print("Alignement    : %d octets de remplissage final retires" % en_trop)

    print("BND4 reconstruit : %d octets" % len(nouveau_bnd))

    if not remplacements:
        # Temoin : le BND4 doit etre identique au vanilla.
        if nouveau_bnd == vanilla:
            print("VERIF BND4    : reconstruit == vanilla (0 octet de diff)  OK")
        else:
            n = sum(1 for a, b in zip(nouveau_bnd, vanilla) if a != b)
            print("VERIF BND4    : ATTENTION %d octets differents sur %d/%d"
                  % (n, len(nouveau_bnd), len(vanilla)))

    # En-tete DCX : constante attendue par le jeu (hors les deux tailles).
    with open(VANILLE, "rb") as fh:
        entete_vanille = fh.read(dcx_build.DCX_PREFIX_LEN)
    if dcx_build.check_prefix(entete_vanille):
        print("VERIF entete  : prefixe DCX maison == prefixe vanilla  OK")
    else:
        print("VERIF entete  : ATTENTION prefixe different du vanilla")
        for off in range(dcx_build.DCX_PREFIX_LEN):
            if entete_vanille[off] != dcx_build.DCX_PREFIX[off]:
                print("    offset 0x%02X : vanilla %02X  /  maison %02X"
                      % (off, entete_vanille[off], dcx_build.DCX_PREFIX[off]))

    nouveau_dcx = dcx_build.build_dcx(nouveau_bnd)
    print("DCX maison    : %d octets (vanilla %d, %+d)"
          % (len(nouveau_dcx), os.path.getsize(VANILLE),
             len(nouveau_dcx) - os.path.getsize(VANILLE)))

    # Controle : notre DCX se relit-il a l'identique ?
    relu = soulsutil.decompress_dcx(nouveau_dcx)
    print("VERIF DCX     : relecture %s" % ("identique OK" if relu == nouveau_bnd
                                            else "DIFFERENTE (%d/%d)" % (len(relu), len(nouveau_bnd))))

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with open(SORTIE, "wb") as fh:
        fh.write(nouveau_dcx)
    print("Ecrit         : %s" % SORTIE)

    if install:
        os.makedirs(SAUVEGARDE, exist_ok=True)
        if os.path.exists(CIBLE_MODS):
            shutil.copy2(CIBLE_MODS, os.path.join(SAUVEGARDE, "c5400.anibnd.avant_maj.dcx"))
            print("Sauvegarde    : _work\\mod_backup\\c5400.anibnd.avant_maj.dcx")
        os.makedirs(os.path.dirname(CIBLE_MODS), exist_ok=True)
        shutil.copy2(SORTIE, CIBLE_MODS)
        print("Installe      : %s" % CIBLE_MODS)
    else:
        print("(non installe ; relancer avec --install)")


if __name__ == "__main__":
    main()
