"""
Cherche la plus grosse entree FLVER parmi les archives chrbnd vanille du jeu.
But : savoir si un personnage d'origine depasse la taille de notre FLVER modde
(12 129 840 octets). Si oui, l'hypothese "limite de taille du moteur" tombe.

Sortie : tableau (nom, taille du .dcx compresse, taille du BND4, taille du FLVER,
nombre de maillages lu dans l'en-tete FLVER a 0x20).
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil      # noqa: E402
import bnd4_build     # noqa: E402

GAME = r"E:\Games\Sekiro - Shadows Die Twice"
CHR = os.path.join(GAME, "chr")


def flver_info(b):
    if b[:5] != b"FLVER":
        return None
    return {
        "version": struct.unpack_from("<i", b, 4)[0],
        "DataOffset": struct.unpack_from("<i", b, 0x0C)[0],
        "DataLength": struct.unpack_from("<i", b, 0x10)[0],
        "noeuds": struct.unpack_from("<i", b, 0x1C)[0],
        "maillages": struct.unpack_from("<i", b, 0x20)[0],
        "facesets": struct.unpack_from("<i", b, 0x50)[0],
    }


def main():
    combien = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    fichiers = sorted(
        (os.path.join(CHR, f) for f in os.listdir(CHR) if f.endswith(".chrbnd.dcx")),
        key=lambda p: os.path.getsize(p), reverse=True)[:combien]

    lignes = []
    for p in fichiers:
        try:
            dcx = open(p, "rb").read()
            bnd = soulsutil.decompress_dcx(dcx)
            _, _, _, _, es = bnd4_build.list_entries(bnd)
        except Exception as exc:                    # noqa: BLE001
            lignes.append((os.path.basename(p), len(dcx), -1, -1, "erreur : %s" % exc))
            continue
        meilleur = None
        for e in es:
            nom = bnd4_build.basename_of(e["fullname"])
            if "flver" not in nom.lower():
                continue
            brut = bnd[e["offset"]:e["offset"] + e["size"]]
            info = flver_info(brut)
            if info is None:
                continue
            cand = (e["size"], nom, info)
            if meilleur is None or cand[0] > meilleur[0]:
                meilleur = cand
        if meilleur is None:
            lignes.append((os.path.basename(p), len(dcx), len(bnd), -1, "aucun FLVER"))
        else:
            lignes.append((os.path.basename(p), len(dcx), len(bnd), meilleur[0],
                           "%s | %d maillages, %d facesets, DataLength %d"
                           % (meilleur[1], meilleur[2]["maillages"],
                              meilleur[2]["facesets"], meilleur[2]["DataLength"])))

    print("%-20s %11s %11s %11s  %s" % ("archive", "dcx", "BND4", "FLVER", "detail"))
    for nom, a, b, c, d in lignes:
        print("%-20s %11d %11d %11d  %s" % (nom, a, b, c, d))

    tailles = [c for _, _, _, c, _ in lignes if c and c > 0]
    if tailles:
        print()
        print("FLVER max vanille : %d octets" % max(tailles))
        print("notre FLVER modde : %d octets" % 12129840)
    return 0


if __name__ == "__main__":
    sys.exit(main())
