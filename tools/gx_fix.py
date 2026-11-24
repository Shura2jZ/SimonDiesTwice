# -*- coding: utf-8 -*-
"""Corrige le defaut d'ecriture des listes GX de SoulsFormats.

Probleme mesure : dans le FLVER vanilla, la liste GX du materiau 0 (offset 0x24430)
contient 2 items (GXMD puis GX00) et dure 108 octets ; la liste du materiau 1
(offset 0x2445C) est exactement le SUFFIXE de 64 octets de la precedente.
Les listes se CHEVAUCHENT.

SoulsFormats lit correctement ces listes (indexees par offset de depart) mais les
reecrit bout a bout, sans reconstruire le chevauchement : la liste du materiau 1
est ecrite une seconde fois (+64 octets), et toutes les listes suivantes sont
decalees de +64.

Correction : recompacter la zone GX par reutilisation de suffixe, puis
- retirer les octets gagnes (la zone GX retrouve sa taille d'origine),
- decaler de -gain les offsets de chaines situes apres la zone (noms de materiaux
  et chemins .mtd, qui sont les seuls pointeurs absolus apres la zone GX),
- reecrire les gxOffset des materiaux.

Usage : gx_fix.py <entree.flver> <sortie.flver> [--rapport]
"""

import struct
import sys

MAGIE = b"FLVER"
STRIDE_MATERIAU = 0x20
CHAMP_NOM = 0x00
CHAMP_MTD = 0x04
CHAMP_GX = 0x14
STRIDE_OS = 0x80
CHAMP_NOM_OS = 0x0C
TAILLE_MESH = 0x30
TAILLE_FACESET = 0x20
TAILLE_TAMPON = 0x20
TAILLE_AGENCEMENT = 0x10
TAILLE_TEXTURE = 0x20
CHAMP_TEXTURE_1 = 0x00
CHAMP_TEXTURE_2 = 0x04
TERMINATEUR_1 = -1
TERMINATEUR_2 = 0x7FFFFFFF


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def i32(d, o):
    return struct.unpack_from("<i", d, o)[0]


def lire_entete(d):
    if d[:5] != MAGIE:
        raise ValueError("ce n'est pas un FLVER")
    return {
        "version": u32(d, 0x08),
        "data_offset": u32(d, 0x0C),
        "data_length": u32(d, 0x10),
        "nb_dummies": u32(d, 0x14),
        "nb_materiaux": u32(d, 0x18),
        "nb_os": u32(d, 0x1C),
        "nb_mesh": u32(d, 0x20),
        "nb_tampons": u32(d, 0x24),
        "nb_facesets": u32(d, 0x50),
        "nb_agencements": u32(d, 0x54),
        "nb_textures": u32(d, 0x58),
    }


def table_materiaux(d, ent):
    debut = 0x80 + ent["nb_dummies"] * 0x40
    return debut


def lire_liste(d, pos):
    """Parcourt une liste GX a partir de pos.

    Retourne (liste_des_items, taille_totale). Un item = (bloc_brut, id, unk04,
    longueur) ou bloc_brut couvre tout l'item. Le parcours s'arrete au
    terminateur (id == -1 ou 0x7FFFFFFF).
    """
    debut = pos
    items = []
    garde = 0
    while True:
        if garde > 4096:
            raise ValueError("liste GX aberrante a 0x%X" % debut)
        garde += 1
        v = i32(d, pos)
        if v in (TERMINATEUR_1, TERMINATEUR_2):
            break
        longueur = u32(d, pos + 8)
        if longueur < 12 or pos + longueur > len(d):
            raise ValueError("item GX de longueur %d invalide a 0x%X" % (longueur, pos))
        items.append((d[pos:pos + longueur], d[pos:pos + 4], u32(d, pos + 4), longueur))
        pos += longueur
    taille_terminateur = u32(d, pos + 8)
    if taille_terminateur < 12:
        raise ValueError("terminateur GX de taille %d invalide a 0x%X" % (taille_terminateur, pos))
    items.append((d[pos:pos + taille_terminateur], b"TERM", u32(d, pos + 4), taille_terminateur))
    total = (pos - debut) + taille_terminateur
    return items, total


def lire_gx(d):
    ent = lire_entete(d)
    debut_table = table_materiaux(d, ent)
    nb = ent["nb_materiaux"]
    materiaux = []
    for i in range(nb):
        o = debut_table + i * STRIDE_MATERIAU
        materiaux.append({
            "pos": o,
            "nom": u32(d, o + CHAMP_NOM),
            "mtd": u32(d, o + CHAMP_MTD),
            "gx": u32(d, o + CHAMP_GX),
        })
    return ent, materiaux


def ordre_listes(materiaux):
    """Ordre de premiere reference = ordre d'ecriture par SoulsFormats."""
    ordre = []
    vus = set()
    for m in materiaux:
        if m["gx"] and m["gx"] not in vus:
            vus.add(m["gx"])
            ordre.append(m["gx"])
    return ordre


def est_sequentielle(d, offsets, rapport):
    """SoulsFormats ecrit les listes bout a bout ; FromSoft les fait se chevaucher.

    On teste l'hypothese sequentielle : offsets[i] == offsets[0] + somme des
    longueurs precedentes. Si oui, le fichier vient de SoulsFormats et doit etre
    recompacte. Sinon (chevauchement), il est deja conforme : on ne touche a rien.
    """
    attendu = offsets[0]
    for i, off in enumerate(offsets):
        if off != attendu:
            rapport.append("  zone GX deja conforme (chevauchement) : liste %d a 0x%X, "
                           "sequentiel attendu 0x%X" % (i, off, attendu))
            return False
        _, taille = lire_liste(d, off)
        attendu += taille
    return True


def recompacte(d, offsets, rapport):
    """Retourne (zone_compacte, nouveaux_offsets_relatifs, taille_ancienne)."""
    blocs = []
    total_ancien = 0
    for off in offsets:
        items, taille = lire_liste(d, off)
        blocs.append(d[off:off + taille])
        total_ancien += taille

    # verification : la zone ecrite est bien la concatenation des listes, dans l'ordre
    if offsets[0] + total_ancien > len(d):
        raise ValueError("zone GX hors fichier")
    concat = b"".join(blocs)
    if d[offsets[0]:offsets[0] + total_ancien] != concat:
        rapport.append("  ATTENTION : la zone GX n'est pas la concatenation attendue")
        rapport.append("  zone reelle : %s" % d[offsets[0]:offsets[0] + total_ancien].hex()[:160])
        rapport.append("  concatenee  : %s" % concat.hex()[:160])
        raise ValueError("zone GX non contigue")

    buf = b""
    rel = []
    for i, bloc in enumerate(blocs):
        if bloc and buf.endswith(bloc):
            place = len(buf) - len(bloc)
            rapport.append("  liste %d : suffixe de la zone deja ecrite a +%d" % (i, place))
        else:
            trouve = buf.find(bloc)
            if trouve >= 0 and len(bloc) > 0:
                place = trouve
                rapport.append("  liste %d : deja presente dans la zone a +%d" % (i, place))
            else:
                place = len(buf)
                buf += bloc
                rapport.append("  liste %d : nouvelle, ecrite a +%d (%d octets)" % (i, place, len(bloc)))
        rel.append(place)
    return buf, rel, total_ancien


def corriger(d, verbeux=True):
    ent, materiaux = lire_gx(d)
    offsets = ordre_listes(materiaux)
    rapport = []
    if verbeux:
        rapport.append("DataOffset=%d  materiaux=%d  liste GX=%d" %
                       (ent["data_offset"], ent["nb_materiaux"], len(offsets)))
        rapport.append("  offsets d'origine : %s" % [hex(o) for o in offsets])
    if not offsets:
        rapport.append("  aucune liste GX : rien a faire")
        return bytes(d), ent, rapport, 0
    if not est_sequentielle(d, offsets, rapport):
        return bytes(d), ent, rapport, 0

    zone, rel, total_ancien = recompacte(d, offsets, rapport)
    gain = total_ancien - len(zone)
    if verbeux:
        rapport.append("  zone d'origine %d octets, zone compactee %d octets, gain %d" %
                       (total_ancien, len(zone), gain))

    # table de correspondance ancien offset -> nouvel offset absolu
    correspondance = {}
    for i, off in enumerate(offsets):
        correspondance[off] = offsets[0] + rel[i]

    out = bytearray(d)
    # 1) remplacer la zone GX par la version compactee (reduit deja de `gain`)
    fin_zone = offsets[0] + total_ancien
    if gain:
        if len(zone) != total_ancien - gain:
            raise ValueError("taille de zone inattendue")
        out[offsets[0]:fin_zone] = zone
    # 2) reecrire les gxOffset des materiaux
    for m in materiaux:
        if m["gx"]:
            nouveau = correspondance[m["gx"]]
            struct.pack_into("<I", out, m["pos"] + CHAMP_GX, nouveau)
    # 3) decaler les chaines situees apres la zone (noms de materiaux, .mtd, noms d'os,
    #    chemins et types de textures)
    if gain:
        debut_os = table_materiaux(d, ent) + ent["nb_materiaux"] * STRIDE_MATERIAU
        fin_os = debut_os + ent["nb_os"] * STRIDE_OS
        debut_textures = (fin_os
                          + ent["nb_mesh"] * TAILLE_MESH
                          + ent["nb_facesets"] * TAILLE_FACESET
                          + ent["nb_tampons"] * TAILLE_TAMPON
                          + ent["nb_agencements"] * TAILLE_AGENCEMENT)

        emplacements = []
        for m in materiaux:
            emplacements.append(m["pos"] + CHAMP_NOM)
            emplacements.append(m["pos"] + CHAMP_MTD)
        for i in range(ent["nb_os"]):
            emplacements.append(debut_os + i * STRIDE_OS + CHAMP_NOM_OS)
        for i in range(ent["nb_textures"]):
            o = debut_textures + i * TAILLE_TEXTURE
            emplacements.append(o + CHAMP_TEXTURE_1)
            emplacements.append(o + CHAMP_TEXTURE_2)

        n = 0
        for o in emplacements:
            val = struct.unpack_from("<I", out, o)[0]
            if val == 0 or val >= ent["data_offset"]:
                continue
            if val >= fin_zone:
                struct.pack_into("<I", out, o, val - gain)
                n += 1
        rapport.append("  %d pointeurs de chaines decales de -%d (sur %d champs examines)"
                       % (n, gain, len(emplacements)))
        if n == 0:
            raise ValueError("aucun pointeur de chaine trouve : structure mal identifiee")
        # 4) l'en-tete DataOffset doit suivre le decalage
        struct.pack_into("<I", out, 0x0C, ent["data_offset"] - gain)
        rapport.append("  DataOffset %d -> %d" % (ent["data_offset"], ent["data_offset"] - gain))
    return bytes(out), ent, rapport, gain


def verifie(d_avant, d_apres, verbeux=True):
    """Compare les listes GX vues par chaque materiau avant / apres."""
    e1, m1 = lire_gx(d_avant)
    e2, m2 = lire_gx(d_apres)
    if len(m1) != len(m2):
        return False, "nombre de materiaux different"
    for i, (a, b) in enumerate(zip(m1, m2)):
        if not a["gx"]:
            continue
        ia, _ = lire_liste(d_avant, a["gx"])
        ib, _ = lire_liste(d_apres, b["gx"])
        if ia != ib:
            return False, "materiau %d : items differents" % i
    return True, "ok"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    entre, sortie = sys.argv[1], sys.argv[2]
    with open(entre, "rb") as f:
        d = f.read()
    out, ent, rapport, gain = corriger(d)
    ok, msg = verifie(d, out, verbeux=False)
    print("\n".join(rapport))
    print("  verification semantique : %s" % msg)
    if not ok:
        return 2
    with open(sortie, "wb") as f:
        f.write(out)
    print("  ecrit %s (%d octets, ecart %+d)" % (sortie, len(out), len(out) - len(d)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
