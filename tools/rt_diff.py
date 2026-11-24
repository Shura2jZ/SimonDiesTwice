"""
Compare la vanille et son roundtrip SoulsFormats, en alignant sur DataOffset.

But : savoir si l'ecriture SoulsFormats preserve les OCTETS de la zone de
donnees (sommets + indices). Si oui, la corruption eventuelle est ailleurs
(tables, en-tete, listes GX, chaines). Si non, on voit exactement quelles
plages sont alterees.

Aucune ecriture dans les dossiers de jeu.
"""
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)


def entete(blob):
    assert blob[:5] == b"FLVER", "pas un FLVER"
    d = {}
    d["DataOffset"], d["DataLength"] = struct.unpack_from("<2i", blob, 0x0C)
    d["dummies"], d["materiaux"], d["os"], d["maillages"], d["tampons"] = struct.unpack_from("<5i", blob, 0x14)
    d["trueFaces"], d["totalFaces"] = struct.unpack_from("<2i", blob, 0x40)
    d["tailleIndice"] = blob[0x48]
    d["unicode"] = blob[0x49]
    d["unk4A"], = struct.unpack_from("<b", blob, 0x4A)
    d["unk4C"], = struct.unpack_from("<i", blob, 0x4C)
    d["facesets"], d["agencements"], d["textures"] = struct.unpack_from("<3i", blob, 0x50)
    d["unk5C"], d["unk5D"] = blob[0x5C], blob[0x5D]
    d["unk68"], = struct.unpack_from("<i", blob, 0x68)
    d["version"], = struct.unpack_from("<i", blob, 0x08)
    return d


def plages(a, b):
    """Plages d'octets qui different, compressees en intervalles."""
    res = []
    debut = None
    for i in range(len(a)):
        if a[i] != b[i]:
            if debut is None:
                debut = i
        else:
            if debut is not None:
                res.append((debut, i))
                debut = None
    if debut is not None:
        res.append((debut, len(a)))
    return res


def main():
    van = sys.argv[1] if len(sys.argv) > 1 else r"_work\extracted\c5400.chrbnd\c5400.flver"
    rt = sys.argv[2] if len(sys.argv) > 2 else r"_work\vanille_rt.flver"
    A = open(van, "rb").read()
    B = open(rt, "rb").read()
    ea, eb = entete(A), entete(B)

    print("=== en-tetes ===")
    for k in ea:
        va, vb = ea[k], eb[k]
        flag = "  <-- DIFFERENT" if va != vb else ""
        print("  %-14s vanille=%-12s roundtrip=%-12s%s" % (k, va, vb, flag))
    print()
    print("taille fichier : vanille=%d  roundtrip=%d  (delta %+d)" % (len(A), len(B), len(B) - len(A)))
    print()

    print("=== zone de donnees (alignee sur DataOffset) ===")
    la, lb = ea["DataLength"], eb["DataLength"]
    da = A[ea["DataOffset"]:ea["DataOffset"] + la]
    db = B[eb["DataOffset"]:eb["DataOffset"] + lb]
    print("  longueur : vanille=%d  roundtrip=%d" % (len(da), len(db)))
    if len(da) != len(db):
        print("  LONGUEURS DIFFERENTES -> comparaison tronquee")
    n = min(len(da), len(db))
    if da[:n] == db[:n]:
        print("  >>> OCTETS IDENTIQUES sur %d octets" % n)
    else:
        pl = plages(da[:n], db[:n])
        total = sum(f - d for d, f in pl)
        print("  >>> %d plages different, %d octets au total" % (len(pl), total))
        for d, f in pl[:20]:
            print("      data+0x%08X .. +0x%08X  (%d octets)" % (d, f, f - d))
            print("         vanille  : %s" % da[d:min(f, d + 32)].hex(" "))
            print("         roundtrip: %s" % db[d:min(f, d + 32)].hex(" "))
        if len(pl) > 20:
            print("      ... (%d plages de plus)" % (len(pl) - 20))
    print()

    print("=== zone des tables (0x80 .. DataOffset) ===")
    ta = A[:ea["DataOffset"]]
    tb = B[:eb["DataOffset"]]
    na, nb = len(ta), len(tb)
    print("  longueur : vanille=%d  roundtrip=%d" % (na, nb))
    n = min(na, nb)
    pl = plages(ta[:n], tb[:n])
    print("  comparaison a decalage nul : %d plages different" % len(pl))
    for d, f in pl[:12]:
        print("      0x%06X .. 0x%06X  (%d octets)" % (d, f, f - d))
    print()
    print("  (rappel : un decalage global fait apparaitre un grand nombre de plages ;")
    print("   ce qui compte est de reperer des plages ISOLEES anormales)")


if __name__ == "__main__":
    main()
