"""
Verifie si notre chaine conteneur (DCX + BND4) est bien fidele a la vanille.

Mesures :
  1) en-tete DCX : vanille vs le notre, champ par champ ;
  2) BND4 : rebuild SANS aucun remplacement -> est-il byte-identique a la vanille ?
     (si oui, notre writer BND4 est innocent ; sinon, c'est un suspect direct)
  3) notre fichier installe se relit-il bien (notre DCX -> notre BND4) ?

N'ecrit rien : lecture seule + affichage.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil          # noqa: E402
import bnd4_build         # noqa: E402
import dcx_build          # noqa: E402

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"E:\Games\Sekiro - Shadows Die Twice"

VANILLE_DCX = os.path.join(GAME, "chr", "c5400.chrbnd.dcx")
NOTRE_DCX = os.path.join(PROJ, "_work", "mod", "chr", "c5400.chrbnd.dcx")


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


van_dcx = open(VANILLE_DCX, "rb").read()
not_dcx = open(NOTRE_DCX, "rb").read()

print("=== 1) en-tete DCX ===")
for nom, d in (("vanille", van_dcx), ("notre", not_dcx)):
    print("  %-8s %s" % (nom, soulsutil.parse_dcx_header(d)))
print("  préfixe constant identique : %s" % dcx_build.check_prefix(van_dcx))
print("  vanille 0x00..0x4C : %s" % van_dcx[:0x4C].hex(" "))
print("  notre   0x00..0x4C : %s" % not_dcx[:0x4C].hex(" "))

van_raw = soulsutil.decompress_dcx(van_dcx)
not_raw = soulsutil.decompress_dcx(not_dcx)

print()
print("=== 2) BND4 décompressé ===")
print("  vanille : %d octets   sha %s" % (len(van_raw), sha(van_raw)))
print("  notre   : %d octets   sha %s" % (len(not_raw), sha(not_raw)))

print()
print("=== 3) rebuild du BND4 sans aucun remplacement ===")
reb = bnd4_build.rebuild(van_raw, {})
print("  rebuild : %d octets   sha %s" % (len(reb), sha(reb)))
print("  byte-identique à la vanille : %s" % (reb == van_raw))
if reb != van_raw:
    n = min(len(reb), len(van_raw))
    zones = []
    i = 0
    while i < n:
        if reb[i] != van_raw[i]:
            j = i
            while j < n and reb[j] != van_raw[j]:
                j += 1
            zones.append((i, j - i))
            i = j
        else:
            i += 1
    print("  zones différentes : %d" % len(zones))
    for (o, l) in zones[:40]:
        print("    0x%06X  %3d octets   vanille=%s   rebuild=%s" % (
            o, l,
            van_raw[o:o + min(l, 8)].hex(" "),
            reb[o:o + min(l, 8)].hex(" ")))

print()
print("=== 4) relecture de notre fichier ===")
print("  notre BND4 relu == rebuild ? %s" % (not_raw == reb))
print("  notre BND4 relu == vanille ? %s" % (not_raw == van_raw))

print()
print("=== 5) compression : recompresser la vanille change-t-il le contenu ? ===")
recomp = dcx_build.build_dcx(van_raw)
back = soulsutil.decompress_dcx(recomp)
print("  taille DCX vanille : %d   notre recompression : %d" % (len(van_dcx), len(recomp)))
print("  contenu identique après recompression : %s" % (back == van_raw))
