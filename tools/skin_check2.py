"""
Diagnostic du skinning : pour chaque sommet, on mesure la distance entre sa
position (re-posee) et les os qui le ponderent. C'est cette distance qui est
utilisee au moment de l'animation : si l'os est loin du sommet, le sommet
"part en vrille" des que l'os tourne (les grandes aiguilles blanches en jeu).

Repond aussi : poids total nul, indices d'os hors des os deformants.

Usage :
    python tools/skin_check2.py fichier.bin _work/isshin_nodes.tsv [seuil]
"""

import math
import struct
import sys


def main():
    chemin, chemin_tsv = sys.argv[1], sys.argv[2]
    seuil = float(sys.argv[3]) if len(sys.argv) > 3 else 0.10
    limite_deform = 184

    noms, pos = {}, {}
    for ligne in open(chemin_tsv, encoding="utf-8").read().splitlines()[1:]:
        c = ligne.split("\t")
        if len(c) < 29:
            continue
        i = int(c[0])
        noms[i] = c[3]
        g = [float(x) for x in c[13:29]]
        pos[i] = (g[12], g[13], g[14])

    f = open(chemin, "rb")
    f.read(8)
    nb_maillages = struct.unpack("<I", f.read(4))[0]
    f.read(36)
    nb_os = struct.unpack("<I", f.read(4))[0]
    for _ in range(nb_os):
        n = struct.unpack("<I", f.read(4))[0]
        f.read(n + 4)

    total = 0
    sans_poids = 0
    hors_limite = 0
    anormal = 0
    exemples_anormaux = []
    repartition = {}
    pires = []
    for _ in range(nb_maillages):
        n = struct.unpack("<I", f.read(4))[0]
        nom_m = f.read(n).decode("utf-8")
        f.read(12)
        ns, ni = struct.unpack("<II", f.read(8))
        for iv in range(ns):
            brut_v = f.read(96)
            if len(brut_v) != 96:
                print("[DIAG] maillage %s : lecture courte (%d octets) au sommet %d, "
                      "position fichier %d, ns declare %d"
                      % (nom_m, len(brut_v), iv, f.tell(), ns))
                return
            v = struct.unpack("<3f3f4f2f4f4i4f", brut_v)
            p = (v[0], v[1], v[2])
            idx = (v[16], v[17], v[18], v[19])
            poids = (v[20], v[21], v[22], v[23])
            total += 1
            mauvais = (any(x != x for x in p) or any(x != x for x in poids))
            if mauvais:
                anormal += 1
                if len(exemples_anormaux) < 8:
                    exemples_anormaux.append((nom_m, p, idx, poids))
                continue
            somme = sum(poids)
            if somme < 1e-6:
                sans_poids += 1
                continue
            for k in range(4):
                if poids[k] <= 0.0:
                    continue
                if idx[k] >= limite_deform:
                    hors_limite += 1
            # distance au barycentre des os ponderes
            if somme > 0:
                cx = sum(poids[k] * pos.get(idx[k], (0, 0, 0))[0] for k in range(4)) / somme
                cy = sum(poids[k] * pos.get(idx[k], (0, 0, 0))[1] for k in range(4)) / somme
                cz = sum(poids[k] * pos.get(idx[k], (0, 0, 0))[2] for k in range(4)) / somme
            else:
                cx = cy = cz = 0.0
            d = math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2 + (p[2] - cz) ** 2)
            tranche = min(int(d / 0.05), 12)
            repartition[tranche] = repartition.get(tranche, 0) + 1
            if d > seuil:
                pires.append((d, nom_m, idx, poids, p))
        f.read(ni * 4)

    print("sommets              : %d" % total)
    print("sans poids (somme=0) : %d" % sans_poids)
    print("positions/poids NaN  : %d" % anormal)
    for nom_m, p, idx, poids in exemples_anormaux:
        print("    %-26s pos=(%g,%g,%g) os=%s poids=%s" % (nom_m, p[0], p[1], p[2],
                                                             str(idx), str(poids)))
    print("references a un os non deformant (>= %d) : %d" % (limite_deform, hors_limite))
    print()
    print("distance sommet -> barycentre de ses os :")
    for t in sorted(repartition):
        etiq = "%.2f-%.2f m" % (t * 0.05, (t + 1) * 0.05) if t < 12 else "> 0,60 m"
        print("   %-12s %8d" % (etiq, repartition[t]))

    pires.sort(reverse=True)
    print()
    print("sommets a plus de %.2f m de leurs os : %d" % (seuil, len(pires)))
    compte = {}
    for d, nom_m, idx, poids, p in pires:
        for k in range(4):
            if poids[k] > 0.05:
                cle = noms.get(idx[k], "?")
                compte[cle] = compte.get(cle, 0) + 1
    print("  os concernes (nb de sommets) :")
    for cle, n in sorted(compte.items(), key=lambda kv: -kv[1])[:25]:
        print("     %-24s %7d" % (cle, n))
    print()
    print("  20 pires cas :")
    for d, nom_m, idx, poids, p in pires[:20]:
        liste = ", ".join("%s(%.2f)" % (noms.get(idx[k], "?"), poids[k])
                          for k in range(4) if poids[k] > 0.0)
        print("     %6.3f m  %-26s (%6.3f,%6.3f,%6.3f)  %s"
              % (d, nom_m, p[0], p[1], p[2], liste))


if __name__ == "__main__":
    main()
