"""
Balayage rapide d'un FLVER : liste les chaines de caracteres du fichier et isole
celles qui ressemblent a des noms d'os / de materiaux.

Ce n'est PAS un parseur FLVER (les offsets ne sont pas interpretes) : c'est un
outil d'exploration, pour savoir a quoi ressemblent les noms avant d'ecrire un
parseur. Les chaines sont listees dans l'ordre du fichier, ce qui correspond
en general a l'ordre d'ecriture des structures.

Usage :
    python tools/flver_scan.py chemin/vers/modele.flver [motif]
"""

import re
import sys

BONE_LIKE = re.compile(
    r"^(Root|Pelvis|Spine\d?|Neck\d?|Head|Clavicle_[LR]|L_[A-Za-z0-9_]+|R_[A-Za-z0-9_]+"
    r"|Slave|Dummy|Node|Master|Sword|Weapon|Face|Eye|Jaw|Tongue|Cloth[A-Za-z0-9_]*)$"
)
MTD_LIKE = re.compile(r"\.mtd$", re.IGNORECASE)


def scan(path, extra=None):
    with open(path, "rb") as fh:
        data = fh.read()

    print(f"fichier : {path}")
    print(f"taille  : {len(data):,} octets")
    magic = data[:6]
    print(f"magic   : {magic!r}")
    print()

    strings = [(m.start(), m.group().decode("ascii"))
               for m in re.finditer(rb"[\x20-\x7e]{3,}", data)]

    bones = [(o, s) for o, s in strings if BONE_LIKE.match(s)]
    mtds = [(o, s) for o, s in strings if MTD_LIKE.search(s)]

    print(f"chaines au total  : {len(strings):,}")
    print(f"noms d'os probables : {len(bones)}")
    print(f"fichiers .mtd       : {len(mtds)}")
    print()

    if mtds:
        print("--- materiaux (.mtd) ---")
        for o, s in mtds:
            print(f"    0x{o:07X}  {s}")
        print()

    print("--- noms d'os probables, dans l'ordre du fichier ---")
    for i, (o, s) in enumerate(bones):
        print(f"    {i:4d}  0x{o:07X}  {s}")
    print()

    if extra:
        pat = re.compile(extra)
        print(f"--- autres chaines correspondant a {extra!r} ---")
        for o, s in strings:
            if pat.search(s):
                print(f"    0x{o:07X}  {s}")
        print()

    # les noms d'os doivent occuper une zone contigue : on montre l'etendue
    if bones:
        first = bones[0][0]
        last = max(o for o, _ in bones)
        print(f"zone des noms d'os : 0x{first:07X} .. 0x{last:07X} "
              f"({last - first:,} octets)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    scan(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
