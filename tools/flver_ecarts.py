"""
Compare deux FLVER et decrit l'ecart comme une INSERTION d'octets.

But : SoulsFormats reecrit la vanille avec 64 octets en plus (l'en-tete
"grandit" : DataOffset 190208 -> 190272). On veut savoir EXACTEMENT ou et quoi.

Methode : on trouve le premier octet qui differe, puis on cherche la longueur k
telle que B = A[0:start] + X + A[start:]  (X = les k octets inseres). On affiche
X, son contexte, et une lecture "lisible" (chaines UTF-16 / ASCII / entiers).

Usage : python tools/flver_ecarts.py <A.flver> <B.flver>
"""
import struct
import sys


def zones_differentes(a, b, debut, fin):
    zones = []
    i = debut
    while i < fin:
        if a[i] != b[i]:
            j = i
            while j < fin and a[j] != b[j]:
                j += 1
            zones.append((i, j - i))
            i = j
        else:
            i += 1
    return zones


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    a = open(sys.argv[1], "rb").read()
    b = open(sys.argv[2], "rb").read()
    print("A = %s  (%d octets)" % (sys.argv[1], len(a)))
    print("B = %s  (%d octets)" % (sys.argv[2], len(b)))
    print("difference de taille : %d octets" % (len(b) - len(a)))

    # 1) differences alignees au debut (champs d'en-tete)
    print()
    print("=== zones differentes dans les 0x3000 premiers octets (A vs B, meme offset) ===")
    for (o, l) in zones_differentes(a, b, 0, min(0x3000, len(a), len(b))):
        va = a[o:o + min(l, 8)]
        vb = b[o:o + min(l, 8)]
        ia = struct.unpack("<i", a[o:o + 4])[0] if l >= 4 else None
        ib = struct.unpack("<i", b[o:o + 4])[0] if l >= 4 else None
        print("  +0x%04X  %2d octets   A=%-12s B=%-12s%s"
              % (o, l, va.hex(" "), vb.hex(" "),
                 ("   (entier A=%d B=%d)" % (ia, ib)) if l == 4 else ""))

    # 2) point d'insertion : on balaie depuis la FIN, car tout ce qui suit
    # l'insertion est identique a un decalage de k pres.
    print()
    k = len(b) - len(a)
    s = 0
    for i in range(len(a) - 1, -1, -1):
        if a[i] != b[i + k]:
            s = i + 1
            break
    print("=== les octets >= 0x%X de A se retrouvent a l'identique decales de %d dans B ==="
          % (s, k))
    print("    (donc la zone modifiee est avant 0x%X)" % s)

    if s < 0x3000:
        print()
        print("=== dernieres zones differentes avant l'insertion (A vs B, meme offset) ===")
        for (o, l) in zones_differentes(a, b, max(0, s - 0x400), min(s, len(b))) [-12:]:
            va = a[o:o + min(l, 12)]
            vb = b[o:o + min(l, 12)]
            ia = struct.unpack("<i", a[o:o + 4])[0] if l == 4 else None
            ib = struct.unpack("<i", b[o:o + 4])[0] if l == 4 else None
            print("  +0x%04X  %2d octets   A=%-14s B=%-14s%s"
                  % (o, l, va.hex(" "), vb.hex(" "),
                     ("   (entier A=%d B=%d)" % (ia, ib)) if l == 4 else ""))

    print()
    print("=== ce que B contient la ou A a le debut de la zone (insertion supposee) ===")
    deb = max(0, s - 64)
    x = b[deb:deb + k + 64]
    for o in range(0, len(x), 16):
        bloc = x[o:o + 16]
        texte = "".join(chr(c) if 32 <= c < 127 else "." for c in bloc)
        print("  0x%06X  %-47s  %s" % (deb + o, bloc.hex(" "), texte))

    print()
    print("=== le meme endroit dans A ===")
    y = a[deb:deb + k + 64]
    for o in range(0, len(y), 16):
        bloc = y[o:o + 16]
        texte = "".join(chr(c) if 32 <= c < 127 else "." for c in bloc)
        print("  0x%06X  %-47s  %s" % (deb + o, bloc.hex(" "), texte))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
