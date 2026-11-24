"""
Lecture des animations ActorX (.psa) exportees par FModel.

Un .psa est une suite de blocs nommes :

    char  nom[20]
    int32 taille
    ...donnees...

Blocs utiles :
    ANIMHEAD   version
    BONENAMES  squelette (noms, parents)
    ANIMINFO   liste des sequences (nom, nombre d'images, decalage)
    ANIMKEYS   les images : position (3 float), orientation (4 float), temps

Sous-commandes :
    python tools/psa_lire.py blocs <fichier.psa>
        Liste les blocs avec leur taille. Sert a verifier nos hypotheses.

    python tools/psa_lire.py os <fichier.psa> [n]
        Squelette : nombre d'os, premiers noms, parents.

    python tools/psa_lire.py sequences <fichier.psa>
        Sequences contenues et leur duree.

    python tools/psa_lire.py cles <fichier.psa> <os> [images]
        Valeurs brutes d'un os, pour caler les conventions (unites, ordre du
        quaternion, repere).

Aucune ecriture.
"""

import math
import struct
import sys


def blocs(chemin):
    """Retourne [(nom, taille, offset_donnees)] en parcourant tous les blocs."""
    with open(chemin, "rb") as fh:
        donnees = fh.read()
    res = []
    pos = 0
    while pos + 24 <= len(donnees):
        nom = donnees[pos:pos + 20].split(b"\x00")[0].decode("ascii", "replace")
        (taille,) = struct.unpack_from("<I", donnees, pos + 20)
        if not nom or pos + 24 + taille > len(donnees):
            break
        res.append((nom, taille, pos + 24))
        pos += 24 + taille
    return donnees, res


def lire_os(donnees, offset, taille):
    """BONENAMES : nombre, puis par os nom[64], flags, parent, nbEnfants, enfants[],
    longueur, taille(3 float), quaternion(4 float)."""
    (nombre,) = struct.unpack_from("<i", donnees, offset)
    pos = offset + 4
    os_liste = []
    for _ in range(nombre):
        nom = donnees[pos:pos + 64].split(b"\x00")[0].decode("ascii", "replace")
        pos += 64
        flags, parent, nb_enfants = struct.unpack_from("<iii", donnees, pos)
        pos += 12
        enfants = list(struct.unpack_from("<%di" % nb_enfants, donnees, pos)) if nb_enfants else []
        pos += 4 * nb_enfants
        (longueur,) = struct.unpack_from("<f", donnees, pos)
        pos += 4
        # Champs optionnels selon la version du format.
        reste = offset + taille - pos
        taille_os = quat_os = None
        if reste >= 28:
            taille_os = struct.unpack_from("<fff", donnees, pos)
            pos += 12
            quat_os = struct.unpack_from("<ffff", donnees, pos)
            pos += 16
        os_liste.append({
            "nom": nom, "flags": flags, "parent": parent,
            "enfants": enfants, "longueur": longueur,
            "taille": taille_os, "rotation": quat_os,
        })
    return os_liste, pos - offset, taille


def lire_infos(donnees, offset, taille):
    """ANIMINFO : nombre, puis par sequence nom[64], groupe, nbOs, puis par os
    (nbImages, debut)."""
    (nombre,) = struct.unpack_from("<i", donnees, offset)
    pos = offset + 4
    sequences = []
    for _ in range(nombre):
        nom = donnees[pos:pos + 64].split(b"\x00")[0].decode("ascii", "replace")
        pos += 64
        groupe, nb_os = struct.unpack_from("<ii", donnees, pos)
        pos += 8
        pistes = []
        for _ in range(nb_os):
            nb_images, debut = struct.unpack_from("<ii", donnees, pos)
            pos += 8
            pistes.append((nb_images, debut))
        sequences.append({"nom": nom, "groupe": groupe, "pistes": pistes})
    return sequences, pos - offset, taille


def bloc(donnees, liste, nom):
    for n, taille, offset in liste:
        if n == nom:
            return taille, offset
    return None


def hexa(donnees, offset, longueur):
    fin = min(len(donnees), offset + longueur)
    for pos in range(offset, fin, 16):
        morceau = donnees[pos:pos + 16]
        texte = "".join(chr(b) if 32 <= b < 127 else "." for b in morceau)
        print("  %08X  %-47s  %s" % (pos, " ".join("%02X" % b for b in morceau), texte))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    commande, chemin = sys.argv[1], sys.argv[2]

    if commande in ("hexa", "trouver", "chercher"):
        with open(chemin, "rb") as fh:
            donnees = fh.read()
        if commande == "hexa":
            hexa(donnees, int(sys.argv[3], 0), int(sys.argv[4], 0))
            return
        if commande == "chercher":
            for mot in sys.argv[3:]:
                motif = mot.encode("ascii")
                positions = []
                pos = 0
                while True:
                    i = donnees.find(motif, pos)
                    if i < 0:
                        break
                    positions.append(i)
                    pos = i + 1
                print("  %-12s %d occurrence(s) : %s"
                      % (mot, len(positions), " ".join("0x%X" % p for p in positions[:12])))
            return
        for motif in (b"ANIMHEAD", b"BONENAMES", b"ANIMINFO", b"ANIMKEYS",
                      b"SCALEKEYS", b"KEYFRAMER", b"ANIMCURVE"):
            pos = 0
            while True:
                i = donnees.find(motif, pos)
                if i < 0:
                    break
                avant = donnees[max(0, i - 12):i]
                print("  %-10s a 0x%08X  octets precedents %s"
                      % (motif.decode(), i, avant.hex(" ")))
                pos = i + 1
        print("taille du fichier : %d" % len(donnees))
        return

    donnees, liste = blocs(chemin)

    if commande == "blocs":
        print("fichier : %s  (%d octets)" % (chemin, len(donnees)))
        for nom, taille, offset in liste:
            print("  %-12s %12d octets  a 0x%X" % (nom, taille, offset))
        return

    if commande == "os":
        b = bloc(donnees, liste, "BONENAMES")
        if not b:
            print("pas de bloc BONENAMES")
            return
        os_liste, consomme, taille = lire_os(donnees, b[1], b[0])
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        print("bloc BONENAMES : %d octets, %d os, %d octets consommes par notre lecture"
              % (taille, len(os_liste), consomme))
        for i, o in enumerate(os_liste[:n]):
            par = os_liste[o["parent"]]["nom"] if 0 <= o["parent"] < len(os_liste) else "-"
            print("  [%3d] %-40s parent %-3d %-30s longueur %.4f"
                  % (i, o["nom"], o["parent"], par, o["longueur"]))
        if len(os_liste) > n:
            print("  ... (%d os au total)" % len(os_liste))
        return

    if commande == "sequences":
        b = bloc(donnees, liste, "ANIMINFO")
        if not b:
            print("pas de bloc ANIMINFO")
            return
        sequences, consomme, taille = lire_infos(donnees, b[1], b[0])
        print("bloc ANIMINFO : %d octets, %d sequence(s)" % (taille, len(sequences)))
        for s in sequences:
            images = max([p[0] for p in s["pistes"]]) if s["pistes"] else 0
            actives = len([p for p in s["pistes"] if p[0] > 0])
            print("  %-30s os %3d  images %4d  os animes %3d"
                  % (s["nom"], len(s["pistes"]), images, actives))
        return

    if commande == "cles":
        _, liste = blocs(chemin)
        b_info = bloc(donnees, liste, "ANIMINFO")
        sequences, _, _ = lire_infos(donnees, b_info[1], b_info[0])
        s = sequences[0]
        nom_os = sys.argv[3]
        b_os = bloc(donnees, liste, "BONENAMES")
        os_liste, _, _ = lire_os(donnees, b_os[1], b_os[0])
        index = next(i for i, o in enumerate(os_liste) if o["nom"] == nom_os)
        nb_images, debut = s["pistes"][index]

        b_cles = bloc(donnees, liste, "ANIMKEYS")
        (total,) = struct.unpack_from("<i", donnees, b_cles[1])
        taille_cle = (b_cles[0] - 4) / total
        print("ANIMKEYS : %d cles, %d octets par cle (%.2f flottants)"
              % (total, taille_cle, taille_cle / 4.0))
        print("sequence %s, os %s : %d images a partir de %d" % (s["nom"], nom_os, nb_images, debut))
        combien = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        nf = int(taille_cle // 4)
        for k in range(min(combien, nb_images)):
            vals = struct.unpack_from("<%df" % nf, donnees, b_cles[1] + 4 + (debut + k) * int(taille_cle))
            print("  image %3d : %s" % (k, " ".join("%9.4f" % v for v in vals)))
        # Duree totale a partir des temps.
        base = b_cles[1] + 4
        temps = []
        for k in range(0, min(total, 200000)):
            vals = struct.unpack_from("<%df" % nf, donnees, base + k * int(taille_cle))
            temps.append(vals[-1])
        if temps:
            print("temps : min %.4f  max %.4f" % (min(temps), max(temps)))
        return

    print(__doc__)


if __name__ == "__main__":
    main()
