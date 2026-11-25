"""
Compare deux fichiers binaires et affiche la premiere zone qui differe, avec
plusieurs interpretations (entier signe, hexa, flottant).

Usage :
    python tools/bin_diff.py <fichierA> <fichierB> [longueur]
"""

import struct
import sys


def lire(chemin):
    with open(chemin, "rb") as f:
        return f.read()


def mots(donnees, debut, longueur):
    lignes = []
    for off in range(debut, min(debut + longueur, len(donnees)) - 3, 4):
        brut = donnees[off:off + 4]
        i = struct.unpack("<i", brut)[0]
        u = struct.unpack("<I", brut)[0]
        fl = struct.unpack("<f", brut)[0]
        fl_txt = ("%12.6g" % fl) if abs(fl) < 1e12 and (fl == 0.0 or 1e-6 < abs(fl) < 1e9) else "     (bizarre)"
        lignes.append("  0x%06X  %04X %04X  int %12d  uint %10u  float %s"
                      % (off, u >> 16, u & 0xFFFF, i, u, fl_txt))
    return lignes


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    a = lire(sys.argv[1])
    b = lire(sys.argv[2])
    longueur = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x60
    force = int(sys.argv[4], 0) if len(sys.argv) > 4 else None

    print("A = %s  (%d octets)" % (sys.argv[1], len(a)))
    print("B = %s  (%d octets)" % (sys.argv[2], len(b)))

    if a == b:
        print("fichiers identiques")
        return

    # premiere difference
    n = min(len(a), len(b))
    premier = next((i for i in range(n) if a[i] != b[i]), n)
    if force is not None:
        premier = force
    print("zone examinee a partir de : 0x%06X" % premier)
    print()

    # zones qui different, regroupees
    i = premier
    zones = []
    while i < n:
        if a[i] != b[i]:
            debut = i
            while i < n and a[i] != b[i]:
                i += 1
            zones.append((debut, i))
        i += 1
    print("nombre de zones differentes : %d" % len(zones))
    print("premieres zones :")
    for d, f in zones[:12]:
        print("   0x%06X .. 0x%06X   (%d octets)" % (d, f, f - d))
    print()

    debut = max(0, premier - 16)
    print("=== A autour de la premiere difference ===")
    for l in mots(a, debut, longueur):
        print(l)
    print()
    print("=== B autour de la premiere difference ===")
    for l in mots(b, debut, longueur):
        print(l)


if __name__ == "__main__":
    main()
