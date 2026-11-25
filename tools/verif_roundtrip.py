"""
Verifie si notre chaine d'ecriture (SoulsFormats reecrit le FLVER, puis gx_fix,
puis le patch 0x40) reproduit la vanille A L'OCTET PRES.

C'est le test que demande l'utilisateur : "es-tu sur d'ecrire au bon endroit ?".
Si la chaine rend la vanille identique, elle est innocente et le probleme vient
de nos donnees. Sinon, chaque plage differente est un defaut de la chaine, et
c'est LUI qui casse le jeu (dans tous nos builds, quel que soit le contenu).

Ne fait aucune ecriture dans les dossiers de jeu.
"""

import os
import shutil
import struct
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))
import gx_fix          # noqa: E402

VANILLE = os.path.join(RACINE, "_work", "extracted", "c5400.chrbnd", "c5400.flver")
ROUNDTRIP = os.path.join(RACINE, "_work", "vanille_rt2.flver")
OUTIL = os.path.join(RACINE, "_work", "tools", "cs", "FlverRoundtrip.exe")


def plages(a, b):
    res, debut = [], None
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            if debut is None:
                debut = i
        else:
            if debut is not None:
                res.append((debut, i))
                debut = None
    if debut is not None:
        res.append((debut, min(len(a), len(b))))
    return res


def main():
    van = open(VANILLE, "rb").read()
    print("vanille          : %d octets" % len(van))

    r = subprocess.run([OUTIL, VANILLE, ROUNDTRIP], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("FlverRoundtrip a echoue : " + r.stdout + r.stderr)
    rt = open(ROUNDTRIP, "rb").read()
    print("roundtrip brut   : %d octets  (delta %+d)" % (len(rt), len(rt) - len(van)))

    # 1) gx_fix, exactement comme make_mod.py
    corrige, _, rapport, gain = gx_fix.corriger(rt)
    for ligne in rapport:
        print("   gx_fix : " + ligne.strip())
    print("apres gx_fix     : %d octets  (delta %+d)" % (len(corrige), len(corrige) - len(van)))

    # 2) patch 0x40 avec la valeur de la vanille (SoulsFormats y met true==total)
    valeur = struct.unpack_from("<i", van, 0x40)[0]
    octets = bytearray(corrige)
    avant = struct.unpack_from("<i", octets, 0x40)[0]
    struct.pack_into("<i", octets, 0x40, valeur)
    corrige = bytes(octets)
    print("patch 0x40       : %d -> %d" % (avant, valeur))

    print()
    print("=== comparaison avec la vanille ===")
    if len(corrige) != len(van):
        print("  TAILLES DIFFERENTES : %d vs %d" % (len(corrige), len(van)))
    pl = plages(van, corrige)
    if not pl:
        print("  >>> IDENTIQUE A L'OCTET PRES : la chaine d'ecriture est innocente.")
        return
    total = sum(f - d for d, f in pl)
    print("  >>> %d plages different, %d octets au total" % (len(pl), total))
    for d, f in pl[:25]:
        print("      0x%08X .. 0x%08X  (%d octets)" % (d, f, f - d))
        print("         vanille : %s" % van[d:min(f, d + 24)].hex(" "))
        print("         ecrit   : %s" % corrige[d:min(f, d + 24)].hex(" "))
    if len(pl) > 25:
        print("      ... (%d plages de plus)" % (len(pl) - 25))

    # 3) ou tombent ces plages ? (zone des tables / zone de donnees)
    do = struct.unpack_from("<i", van, 0x0C)[0]
    print()
    print("  DataOffset vanille : 0x%X" % do)
    tables = [p for p in pl if p[0] < do]
    donnees = [p for p in pl if p[0] >= do]
    print("  plages dans les TABLES  (avant 0x%X) : %d" % (do, len(tables)))
    print("  plages dans les DONNEES (apres)      : %d" % len(donnees))
    if tables:
        print("  premiere plage de table : 0x%X..0x%X" % tables[0])


if __name__ == "__main__":
    main()
