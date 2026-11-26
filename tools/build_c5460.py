#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_c5460.py — construit les 3 archives du boss autonome c5460 (Simon).

Recette Land of Reeds appliquee a un ID vierge (c5460) :
  chrbnd : clone c5400 + FLVER Simon remplace + noms d'entrees renommes c5460
           (materiaux/textures c5400_* PRESERVES : cf. BndPatch --conserver)
  behbnd : clone du graphe de comportement hote (HKB) renomme c5460
           (graphime = c5400.hkx* remplace en identite c5460 + c9997 conserve)
  anibnd : clone complet du pool d'animations hote (skeleton + TAE + ~280 clips)
           renomme c5460 ; option --clip pour greffer un clip de Simon
           (slot a000_003080 = recette LoR niveau entree d'animation)

Sortie : _work/simon_boss/chr/c5460.{chrbnd,behbnd,anibnd}.dcx
Verification systematique a CHAQUE phase (relecture bnd4, noms, residus).
Rien n'est ecrit dans le jeu ; installation = etape separee explicite.

IDs attribues (registres verifies vides le 2026-11-16) :
  modele/chr  = c5460          (ni vanilla des 129 chrbnd, ni LoR des 31)
  NpcParam    = 54600000       NpcThinkParam = 54600000
  behaviorVariationId = 54600  BehaviorParam famille 5460xxxx
  AtkParam    = 54600000+      (toutes familles '546' vides)

Usage :
  python tools/build_c5460.py chrbnd
  python tools/build_c5460.py behbnd
  python tools/build_c5460.py anibnd
  python tools/build_c5460.py anibnd --clip _work/simon_skill1_package/rebuilt/a000_003080_simon.hkx
  python tools/build_c5460.py tout            # les 3 phases, sans clip
  python tools/build_c5460.py verifier        # re-verifie les 3 sorties
"""

import hashlib
import os
import struct
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import bnd4_build
import bnd4_parse
import dcx_build
import soulsutil

JEU = r"E:/Games/Sekiro - Shadows Die Twice"
ANCIEN = "c5400"
NOUVEAU = "c5460"
SRC = "chr/%s.%s.dcx" % (ANCIEN, "%s")
BNDPATCH = os.path.join(RACINE, "_work", "tools", "cs", "BndPatch.exe")
SORTIE_DIR = os.path.join(RACINE, "_work", "simon_boss", "chr")
TMP_DIR = os.path.join(RACINE, "_work", "simon_boss", "tmp")
FLVER_CIBLES = (".flver", ".clm2")  # ressources colocataires a preserver


def log(msg):
    print(msg)
    with open(os.path.join(RACINE, "_work", "simon_boss", "build_c5460.log"), "a",
              encoding="utf-8") as fh:
        fh.write(msg + "\n")


def flver_simon_actuel():
    """FLVER Simon = extraire celui du mod installe (etat canon en jeu),
    sinon fallback sur _work/mod/c5400_mod.flver."""
    mods = os.path.join(JEU, "mods", "chr", "c5400.chrbnd.dcx")
    if os.path.exists(mods):
        brut = soulsutil.load(mods)
        fc, eo, es, do, ents = bnd4_build.list_entries(brut)
        for e in ents:
            if bnd4_build.basename_of(e["fullname"]).lower() == "c5400.flver":
                tag = "mod installe %s" % mods
                return brut[e["offset"]:e["offset"] + e["size"]], tag
    chemin = os.path.join(RACINE, "_work", "mod", "c5400_mod.flver")
    return open(chemin, "rb").read(), "_work/mod/c5400_mod.flver"


def phase_texbnd():
    """LoR livre c<id>.texbnd.dcx pour chaque boss autonome : le moteur peut
    rechercher le bundle de textures par ID de modele. Clone octet-a-octet du
    bundle Simon deja installe (prouve en jeu sur c5400) comme c5460.texbnd."""
    src = os.path.join(JEU, "mods", "chr", "c5409.texbnd.dcx")
    if not os.path.exists(src):
        src = os.path.join(JEU, "chr", "c5409.texbnd.dcx")
    data = open(src, "rb").read()
    dst = os.path.join(SORTIE_DIR, "c5460.texbnd.dcx")
    os.makedirs(SORTIE_DIR, exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(data)
    log("=== phase texbnd : clone %s -> %s (%d o, md5 %s)"
        % (src, dst, len(data), hashlib.md5(data).hexdigest()[:12]))
    return dst


def phase(kind, clip=None):
    chemin_src = os.path.join(JEU, "chr", "%s.%s.dcx" % (ANCIEN, kind))
    brut = soulsutil.load(chemin_src)
    log("=== phase %s : %s (%d o bnd4)" % (kind, chemin_src, len(brut)))

    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(SORTIE_DIR, exist_ok=True)
    entree_bnd4 = os.path.join(TMP_DIR, "%s.%s.bnd4" % (ANCIEN, kind))
    sortie_bnd4 = os.path.join(TMP_DIR, "%s.%s.bnd4" % (NOUVEAU, kind))
    sortie_dcx = os.path.join(SORTIE_DIR, "%s.%s.dcx" % (NOUVEAU, kind))
    with open(entree_bnd4, "wb") as fh:
        fh.write(brut)

    cmd = [BNDPATCH, "renommer", "--in", entree_bnd4, "--out", sortie_bnd4,
           "--old", ANCIEN, "--new", NOUVEAU]

    # remplacements d'entrees selon phase
    if kind == "chrbnd":
        blob, tag = flver_simon_actuel()
        tmp = os.path.join(TMP_DIR, "simon.flver")
        with open(tmp, "wb") as fh:
            fh.write(blob)
        cmd += ["--remplacer", "%s.flver" % ANCIEN, tmp]
        log("  FLVER source   : %s (%d o, md5 %s)"
            % (tag, len(blob), hashlib.md5(blob).hexdigest()[:12]))
    if kind == "anibnd" and clip:
        cmd += ["--remplacer", "%s_003080.hkx" % ANCIEN, os.path.abspath(clip)]
        log("  clip greffe    : a000_003080.hkx <- %s" % clip)

    r = subprocess.run(cmd, capture_output=True, text=True)
    log(r.stdout.rstrip())
    if r.returncode != 0:
        log("ERREUR BndPatch(%d) : %s" % (r.returncode, r.stderr.rstrip()))
        sys.exit(1)

    # emballement DCX (pipeline eprouve make_anibnd : roundtrip verifie)
    out = open(sortie_bnd4, "rb").read()
    dcx = dcx_build.build_dcx(out)
    relu = soulsutil.decompress_dcx(dcx)
    if relu != out:
        log("ERREUR DCX : roundtrip %d != %d" % (len(relu), len(out)))
        sys.exit(1)
    with open(sortie_dcx, "wb") as fh:
        fh.write(dcx)
    log("  DCX ecrit      : %s (%d o, roundtrip OK)"
        % (sortie_dcx, len(dcx)))

    verifier(kind, sortie_dcx)
    return sortie_dcx


def verifier(kind, chemin=None):
    chemin = chemin or os.path.join(SORTIE_DIR, "%s.%s.dcx" % (NOUVEAU, kind))
    brut = soulsutil.load(chemin)
    fc, eo, es, do, ents = bnd4_build.list_entries(brut)
    ancien_noms = [bnd4_build.basename_of(e["fullname"]) for e in ents
                   if ANCIEN in bnd4_build.basename_of(e["fullname"])]
    nouveaux = [bnd4_build.basename_of(e["fullname"]) for e in ents
                if NOUVEAU in bnd4_build.basename_of(e["fullname"])]
    # residus par entree
    residus = []
    for e in ents:
        seg = brut[e["offset"]:e["offset"] + e["size"]]
        n = seg.count(ANCIEN.encode())
        if n:
            base = bnd4_build.basename_of(e["fullname"])
            attendu = base.lower().endswith(FLVER_CIBLES)
            residus.append((base, n, attendu))
    K = []
    K.append("verif %-7s : %d entrees, %d noms %s, %d residu(s) ancien"
             % (kind, fc, len(nouveaux), NOUVEAU, len(ancien_noms)))
    for base, n, attendu in residus:
        K.append("     residu %s x%d %s" % (base, n,
                 "(PROTEGE attendu : materiaux FR)" if attendu else "<<< INATTENDU"))
    for base, n, attendu in residus:
        if not attendu:
            K.append("ERREUR : residu non protege")
            log("\n".join(K))
            sys.exit(1)
    if kind == "chrbnd":
        fl = [e for e in ents if bnd4_build.basename_of(e["fullname"]) == "c5460.flver"][0]
        data = brut[fl["offset"]:fl["offset"] + fl["size"]]
        src, tag = flver_simon_actuel()
        ok = hashlib.md5(data).hexdigest() == hashlib.md5(src).hexdigest()
        K.append("     FLVER = source Simon (%s) : %s" % (tag, "OK" if ok else "DIFFERENT <<<"))
        if not ok:
            log("\n".join(K))
            sys.exit(1)
    log("\n".join(K))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    quoi = args[0]
    clip = None
    if "--clip" in args:
        clip = args[args.index("--clip") + 1]

    if quoi == "chrbnd":
        phase("chrbnd")
    elif quoi == "behbnd":
        phase("behbnd")
    elif quoi == "anibnd":
        phase("anibnd", clip)
    elif quoi == "texbnd":
        phase_texbnd()
    elif quoi == "tout":
        for k in ("chrbnd", "behbnd", "anibnd"):
            phase(k)
        phase_texbnd()
    elif quoi == "verifier":
        for k in ("chrbnd", "behbnd", "anibnd"):
            p = os.path.join(SORTIE_DIR, "%s.%s.dcx" % (NOUVEAU, k))
            if os.path.exists(p):
                verifier(k)
            else:
                log("absent : %s" % p)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
