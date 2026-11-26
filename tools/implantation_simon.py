#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_gameparam.py + install_simon_boss.py — chaîne params & installation test.

Sous-commandes :
  extraire   : copie les .param du bundle mod courant (overlay) vers
               _work/simon_boss/param/ (jeu de travail jamais modifié ailleurs)
  appliquer  : invoque ParamEdit.exe pour créer les lignes c5460 :
                 NpcParam      54600000  (clone 54000000, behaviorVariationId=54600, hp pilotable)
                 NpcThinkParam 54600000  (clone 54000000, battleGoalID=546000 = 54600*10)
               + lignes BehaviorParam familles 254600000+k / AtkParam (option --complet)
  packer     : recompile le bundle gameparam.parambnd.dcx depuis le jeu de travail
               (bnd4_build.rebuild + dcx_build, roundtrip verifié) →
               _work/simon_boss/param/gameparam.parambnd.dcx
  verifier   : relit le bundle produit (nb entrees, lignes 54600000 présentes)
  installer  : copie dans l'overlay mods/ AVEC SAUVEGARDE dans
               _work/mod_backup/c5460_<horodatage>/ + manifeste
               (4 archives chr c5460, bundle gameparam, MSB retarget)
  reverter   : restaure la dernière sauvegarde créée par installer

Toujours : le jeu (base) n'est jamais écrit — overlay mods/ uniquement, réversible.
"""

import datetime
import hashlib
import os
import shutil
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import bnd4_build
import dcx_build
import soulsutil

JEU = r"F:/Games/Sekiro - Shadows Die Twice"
WORK = os.path.join(RACINE, "_work", "simon_boss")
PARAM_DIR = os.path.join(WORK, "param")
CHR_SRC = os.path.join(WORK, "chr")
BUNDLE_SRC = os.path.join(JEU, "mods", "param", "gameparam", "gameparam.parambnd.dcx")
DEFS_DIR = os.path.join(RACINE, "_work", "lor", "defs")
PARAMEDIT = os.path.join(RACINE, "_work", "tools", "cs", "ParamEdit.exe")
BACKUP_ROOT = os.path.join(RACINE, "_work", "mod_backup")

# MSB de spawn : château d'Ashina (bâtiment principal, records debout à y≈54
# = preuve de sol stable ; idole d'arrivée : Ashina Castle: Dojo).
# m20 (Temple) = abandonné nettoyé à l'installation (fichier retiré de mods/).
MSB_MAP = "m11_01_00_00"            # carte du spawn cible
MSB_ANCIEN = "m20_00_00_00"         # install précédente à nettoyer
EXEMPLAIRE = "c5430_0000"           # record debout même carte (struct NPC)
POS = "-111.8,54.0,237.4"           # entre c5430_0000 (3.0 m) et c5060_0001 (3.8 m)
# EntityID DUTIFER, jamais -1 : 284/285 ennemis vanilla en portent ; -1 (bogue
# d'ecriture anterieur) = record jamais instancie en jeu -> invisible.
# Valeur libre dans la carte (max observe 1120623, outil MsbForensics --max-entity).
ENTITE = 1120624
# Test B : sonde meme structure, modele vanilla visible de la salle (c1001)
PROBE_NOM    = "PROBE_VANILLA"
PROBE_MODELE = "c1001"
PROBE_NPC    = 10010000
PROBE_THINK  = 10010000
PROBE_ENTITE = 1120625
# Toit de Genichiro (preuve : tuiles m015321/22/32 y=61.6, bandes u=x+z
# 109..139 x v=x-z -342..-360 -> plateau ~21x13 m centre (-113.4, 61.6, 237.6))
TOIT_POS   = "-113.4,61.6,237.6"
TOIT_ENTITE = 1120626

REGI = [
    # Espace A (apparition) : clones IDENTIQUES du hôte — le pipeline
    # comportement (variationId 53200 -> familles 253200…, battleGoalID 532000)
    # reste entièrement vanilla : aucune dépendance à créer. Les familles 54600
    # viendront à la phase attaques (voir notes/15).
    ("NpcParam.param", "NpcParam.xml", "54600000", "54000000", ""),
    ("NpcThinkParam.param", "NpcThinkParam.xml", "54600000", "54000000", ""),
]


def log(msg):
    print(msg)
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "build_gameparam.log"), "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def extraire():
    brut = soulsutil.load(BUNDLE_SRC)
    fc, eo, es, do, ents = bnd4_build.list_entries(brut)
    os.makedirs(PARAM_DIR, exist_ok=True)
    n = 0
    for e in ents:
        base = bnd4_build.basename_of(e["fullname"])
        blob = brut[e["offset"]:e["offset"] + e["size"]]
        if base.lower().endswith(".param"):
            with open(os.path.join(PARAM_DIR, base), "wb") as fh:
                fh.write(blob)
            n += 1
    log("=== extraire : %d .param (%d entrees) de %s\n    → %s" % (n, fc, BUNDLE_SRC, PARAM_DIR))


def appliquer(complet=False):
    if not os.path.exists(PARAMEDIT):
        log("ERREUR : ParamEdit.exe absent — sous-agent en cours ?")
        sys.exit(1)
    for param, defxml, nid, src, sets in REGI:
        chemin = os.path.join(PARAM_DIR, param)
        defch = os.path.join(DEFS_DIR, defxml)
        cmd = [PARAMEDIT, "add", chemin, defch, nid, ""]
        if src:
            cmd += ["--copy", src]
        if sets:
            cmd += ["--set"] + [x for x in sets.split(",") if x]
        r = subprocess.run(cmd, capture_output=True, text=True)
        log("param %s : %s" % (param, (r.stdout + r.stderr).strip()))
        if r.returncode != 0:
            log("ERREUR ParamEdit sur %s" % param)
            sys.exit(1)
    if complet:
        log("(mode complet : familles Behavior/Atk — voir phase attaques)")


def packer():
    brut = soulsutil.load(BUNDLE_SRC)
    fc, eo, es, do, ents = bnd4_build.list_entries(brut)
    rempl = {}
    for e in ents:
        base = bnd4_build.basename_of(e["fullname"])
        p = os.path.join(PARAM_DIR, base)
        if base.lower().endswith(".param") and os.path.exists(p):
            rempl[base] = open(p, "rb").read()
    out = bnd4_build.rebuild(brut, rempl)
    dcx = dcx_build.build_dcx(out)
    relu = soulsutil.decompress_dcx(dcx)
    if relu != out:
        log("ERREUR : roundtrip dcx KO")
        sys.exit(1)
    dest = os.path.join(PARAM_DIR, "gameparam.parambnd.dcx")
    with open(dest, "wb") as fh:
        fh.write(dcx)
    log("=== packer : %d entrees remplacees, bundle %d o (bnd %d o) → %s"
        % (len(rempl), len(dcx), len(out), dest))


def verifier():
    dest = os.path.join(PARAM_DIR, "gameparam.parambnd.dcx")
    brut = soulsutil.load(dest)
    fc, eo, es, do, ents = bnd4_build.list_entries(brut)
    ok = 0
    for nom, ref in (("NpcParam.param", b"\x40\x1e\x83\xd4"),  # 54600000 LE
                     ):
        e = [x for x in ents if bnd4_build.basename_of(x["fullname"]) == nom]
        if not e:
            log("ERREUR : %s absent du bundle" % nom)
            sys.exit(1)
        blob = brut[e[0]["offset"]:e[0]["offset"] + e[0]["size"]]
        tmp = os.path.join(PARAM_DIR, "_verif_%s" % nom)
        with open(tmp, "wb") as fh:
            fh.write(blob)
    # lecture directe via param_lire
    sys.path.insert(0, r"C:/Users/marou/.deepai-code/scratch/2026-11-16-je-veux-que-tu-reprenne-59b1186e/isshin")
    import param_lire as PL
    for nom, defxml in (("NpcParam.param", "NpcParam.xml"), ("NpcThinkParam.param", "NpcThinkParam.xml")):
        e = [x for x in ents if bnd4_build.basename_of(x["fullname"]) == nom]
        blob = brut[e[0]["offset"]:e[0]["offset"] + e[0]["size"]]
        tmp = os.path.join(PARAM_DIR, "_verif_%s" % nom)
        with open(tmp, "wb") as fh:
            fh.write(blob)
        P = PL.Param(tmp, os.path.join(DEFS_DIR, defxml))
        lid = [i for i in P.lignes if str(i) == "54600000"]
        log("verif %s : %s — nb lignes=%d, ligne 54600000 %s"
            % (nom, "OK" if lid else "ABSENTE <<<", len(P.lignes),
               "trouvee " + (str(P.ligne(lid[0]).get("behaviorVariationId") or
                              P.ligne(lid[0]).get("battleGoalID")) if lid else "")))
        ok += bool(lid)
    log("=== verifier : %d/2 lignes c5460 presentes" % ok)
    if ok != 2:
        sys.exit(1)


def _cibles():
    d = {}
    for f in ("chrbnd", "behbnd", "anibnd", "texbnd"):
        p = os.path.join(CHR_SRC, "c5460.%s.dcx" % f)
        if os.path.exists(p):
            d[os.path.join("chr", "c5460.%s.dcx" % f)] = p
    p = os.path.join(PARAM_DIR, "gameparam.parambnd.dcx")
    if os.path.exists(p):
        d[os.path.join("param", "gameparam", "gameparam.parambnd.dcx")] = p
    return d


def installer():
    """Spawn c5460 = NOUVEAU record SIMON_SPAWN (add, exemplaire c5430_0000,
    entity neutre -1) dans m11_01_00_00 — aucun record vanilla touché —
    installation overlay avec sauvegarde systématique (.avant / nouveaux.txt)."""
    # copie de travail vanilla (lecture seule) du jeu
    vanilla = os.path.join(JEU, "map", "mapstudio", "%s.msb.dcx" % MSB_MAP)
    MSB_WORK = os.path.join(WORK, "msb", "%s.msb.dcx" % MSB_MAP)
    MSB_WIP = os.path.join(WORK, "msb", "spawn_c5460.dcx")
    os.makedirs(os.path.dirname(MSB_WORK), exist_ok=True)
    if not os.path.exists(MSB_WORK):
        shutil.copy2(vanilla, MSB_WORK)
    # chaîne : SIMON_SPAWN (dojo) -> PROBE_VANILLA (mêmes coord.) -> SIMON_ROOF (toit)
    # Pas de Simon dans le dojo/interieur : uniquement (1) la sonde vanilla de
    # diagnostic aux COORDONNEES exactes de l'ancien Simon (meme test controle)
    # et (2) SIMON_ROOF, emplacement final sur le toit de Genichiro.
    etapes = [
        (PROBE_NOM, PROBE_MODELE, str(PROBE_NPC), str(PROBE_THINK), POS, PROBE_ENTITE, EXEMPLAIRE, MSB_WIP + ".e1"),
        ("SIMON_ROOF", "c5460", "54600000", "54600000", TOIT_POS, TOIT_ENTITE, EXEMPLAIRE, MSB_WIP),
    ]
    entree = MSB_WORK
    for nom, modele, npc, think, pos, ent, scale, sortie in etapes:
        r = subprocess.run([
            os.path.join(RACINE, "_work", "tools", "cs", "MsbPatch.exe"),
            "add", "--record", nom, "--model", modele,
            "--npc", npc, "--think", think,
            "--pos", pos, "--at-scale", scale, "--entity-id", str(ent),
            "--in", entree, "--out", sortie], capture_output=True, text=True)
        log("MsbPatch add %s : %s" % (nom, (r.stdout + r.stderr).strip().splitlines()[-3:]))
        if r.returncode != 0 or not os.path.exists(sortie):
            log("ERREUR MsbPatch: " + r.stderr)
            sys.exit(1)
        entree = sortie
    cibles = _cibles()
    cibles[os.path.join("map", "mapstudio", "%s.msb.dcx" % MSB_MAP)] = MSB_WIP

    horo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sauvegarde = os.path.join(BACKUP_ROOT, "c5460_" + horo)
    manifeste = []
    nouveaux = []            # cibles neuves (à supprimer à la réversion)
    os.makedirs(sauvegarde, exist_ok=True)
    # nettoyage : l'install spawn-précédent (m20) porte un nom hors cibles -> purgé
    purge = os.path.join(JEU, "mods", "map", "mapstudio", "%s.msb.dcx" % MSB_ANCIEN)
    if os.path.exists(purge):
        os.remove(purge)
        nouveaux.append(os.path.join("map", "mapstudio", "%s.msb.dcx" % MSB_ANCIEN) + "\n")
        manifeste.append(("purge", MSB_ANCIEN, "install precedente"))
    for rel, src in sorted(cibles.items()):
        dst = os.path.join(JEU, "mods", rel)
        # inchange = on ne touche ni le fichier ni son backup ("seulement
        # les necessaires")
        if os.path.exists(dst):
            m_dst = hashlib.md5(open(dst, "rb").read()).hexdigest()
            m_src = hashlib.md5(open(src, "rb").read()).hexdigest()
            if m_dst == m_src:
                manifeste.append(("inchange", rel, m_dst[:12]))
                continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            b = os.path.join(sauvegarde, rel + ".avant")
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(dst, b)
            manifeste.append(("sauvegarde", rel, hashlib.md5(open(b, "rb").read()).hexdigest()[:12]))
        else:
            nouveaux.append(rel + "\n")
        shutil.copy2(src, dst)
        manifeste.append(("installe", rel, hashlib.md5(open(dst, "rb").read()).hexdigest()[:12]))
    with open(os.path.join(sauvegarde, "nouveaux.txt"), "w", encoding="utf-8") as fh:
        fh.writelines(nouveaux)
    with open(os.path.join(sauvegarde, "manifeste.txt"), "w", encoding="utf-8") as fh:
        for a, b, c in manifeste:
            fh.write("%-11s %s %s\n" % (a, b, c))
    log("=== installer : %d fichier(s) copiés dans mods/ ; sauvegarde %s" % (len(cibles), sauvegarde))
    for a, b, c in manifeste:
        log("   %-11s %s %s" % (a, b, c))


def reverter():
    subs = [os.path.join(BACKUP_ROOT, d) for d in os.listdir(BACKUP_ROOT)
            if d.startswith("c5460_")]
    if not subs:
        log("rien à réverter (aucune sauvegarde c5460)")
        sys.exit(1)
    d = sorted(subs)[-1]
    n = 0
    # 1) supprime les fichiers cree par l'installation (nouveaux.txt)
    neuf = os.path.join(d, "nouveaux.txt")
    if os.path.exists(neuf):
        for rel in open(neuf, encoding="utf-8").read().splitlines():
            p = os.path.join(JEU, "mods", rel)
            if os.path.exists(p):
                os.remove(p)
                n += 1
    # 2) restaure les sauvegardes .avant
    for racine, _, fichiers in os.walk(d):
        for f in fichiers:
            if not f.endswith(".avant"):
                continue
            rel = os.path.relpath(os.path.join(racine, f), d)[:-len(".avant")]
            src = os.path.join(racine, f)
            dst = os.path.join(JEU, "mods", rel)
            shutil.copy2(src, dst)
            n += 1
    log("=== reverter : %d fichier(s) restaurés depuis %s" % (n, d))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    q = args[0]
    if q == "extraire":
        extraire()
    elif q == "appliquer":
        appliquer("--complet" in args)
    elif q == "packer":
        packer()
    elif q == "verifier":
        verifier()
    elif q == "chaîne" or q == "chaine":
        extraire(); appliquer("--complet" in args); packer(); verifier()
    elif q == "installer":
        installer()
    elif q == "reverter":
        reverter()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
