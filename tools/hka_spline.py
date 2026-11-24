"""Decodeur/encodeur des pistes spline Havok 2016 (hkaSplineCompressedAnimation).

Porte de HavokLib (PredatorCZ) source/hka_spline_decompressor.cpp + .hpp.
"""
import math
import struct

QT_8BIT, QT_16BIT, QT_32BIT, QT_40BIT, QT_48BIT, QT_24BIT, QT_16BITQUAT, QT_UNCOMPRESSED = range(8)

STT_DYNAMIC, STT_STATIC, STT_IDENTITY = range(3)

QT_TAILLE_QUAT = {
    QT_32BIT: 4,
    QT_40BIT: 5,
    QT_48BIT: 6,
    QT_24BIT: 3,
    QT_16BITQUAT: 4,
    QT_UNCOMPRESSED: 16,
}


class Masque(object):
    __slots__ = ("brut", "pos", "rot", "echelle")

    def __init__(self, brut, pos, rot, echelle):
        self.brut = brut
        self.pos = pos
        self.rot = rot
        self.echelle = echelle

    def type_pos(self, i):
        bit_statique = 1 << i
        bit_spline = 16 << i
        if self.pos & bit_statique:
            return STT_STATIC
        if self.pos & bit_spline:
            return STT_DYNAMIC
        return STT_IDENTITY

    def type_rot(self):
        if self.rot & 0xF0:
            return STT_DYNAMIC
        if self.rot & 0x0F:
            return STT_STATIC
        return STT_IDENTITY

    def type_echelle(self, i):
        bit_statique = 1 << i
        bit_spline = 16 << i
        if self.echelle & bit_statique:
            return STT_STATIC
        if self.echelle & bit_spline:
            return STT_DYNAMIC
        return STT_IDENTITY

    @property
    def quant_pos(self):
        return self.brut & 3

    @property
    def quant_rot(self):
        return ((self.brut >> 2) & 0xF) + 2

    @property
    def quant_echelle(self):
        return (self.brut >> 6) & 3


def lire_masques(donnees, offset, nb_pistes, nb_flottants=0):
    masques = []
    for i in range(nb_pistes):
        base = offset + 4 * i
        masques.append(Masque(donnees[base], donnees[base + 1],
                              donnees[base + 2], donnees[base + 3]))
    return masques


def aligner(pos, align):
    reste = pos % align
    return pos if reste == 0 else pos + align - reste


def lire_quat32(donnees, pos):
    val = struct.unpack_from("<I", donnees, pos)[0]
    frac = 1.0 / 1023.0
    r = ((val >> 18) & 1023) * frac
    r = 1.0 - r * r
    phi_theta = val & 0x3FFFF
    phi = math.floor(math.sqrt(phi_theta))
    theta = 0.0
    if phi > 0:
        theta = (math.pi / 4.0) * (phi_theta - phi * phi) / phi
        phi = (math.pi / 2.0 / 511.0) * phi
    magnitude = math.sqrt(max(0.0, 1.0 - r * r))
    sp, cp = math.sin(phi), math.cos(phi)
    st, ct = math.sin(theta), math.cos(theta)
    q = [sp * ct * magnitude, sp * st * magnitude, cp * magnitude, r]
    for bit in range(4):
        if val & (0x10000000 << bit):
            q[bit] = -q[bit]
    return tuple(q), pos + 4


def lire_quat48(donnees, pos):
    x, y, z = struct.unpack_from("<hhh", donnees, pos)
    result_shift = ((y >> 14) & 2) | ((x >> 15) & 1)
    r_sign = (z >> 15) != 0
    masque = (1 << 15) - 1
    fractal = 0.000043161

    def comp(v):
        v = (v & masque) - (masque >> 1)
        return v * fractal

    v = [comp(x), comp(y), comp(z), 0.0]
    # QComputeElement() : reconstruit la 4e composante par normalisation
    carre = v[0] * v[0] + v[1] * v[1] + v[2] * v[2]
    v[3] = math.sqrt(max(0.0, 1.0 - carre))
    if r_sign:
        v[3] = -v[3]
    # _mm_shuffle selon resultShift : remet la composante "w" a sa place
    if result_shift == 0:
        q = (v[3], v[0], v[1], v[2])
    elif result_shift == 1:
        q = (v[0], v[3], v[1], v[2])
    elif result_shift == 2:
        q = (v[0], v[1], v[3], v[2])
    else:
        q = (v[0], v[1], v[2], v[3])
    return q, pos + 6


def lire_quat(donnees, pos, qtype):
    if qtype == QT_32BIT:
        return lire_quat32(donnees, pos)
    if qtype == QT_48BIT:
        return lire_quat48(donnees, pos)
    if qtype == QT_UNCOMPRESSED:
        return tuple(struct.unpack_from("<4f", donnees, pos)), pos + 16
    if qtype == QT_40BIT:
        return lire_quat40(donnees, pos)
    raise ValueError("quantization quaternion non geree : %d" % qtype)


def lire_quat40(donnees, pos):
    brut = int.from_bytes(donnees[pos:pos + 5], "little")
    c0 = brut & 0xFFFFFFFF
    c1 = (brut >> 24) & 0xFFFFFFFF

    def mul32(a, b):
        return (a * b) & 0xFFFFFFFF

    l0 = mul32(c0, 1 << 20) >> 20
    l1 = mul32(c0, 1 << 8) >> 20
    l2 = mul32(c1, 1 << 20) >> 20
    m = 2047
    fractal = 0.000345436
    v = [float(x - m) * fractal for x in (l0, l1, l2)]
    v.append(0.0)
    carre = v[0] * v[0] + v[1] * v[1] + v[2] * v[2]
    v[3] = math.sqrt(max(0.0, 1.0 - carre))
    if (brut >> 38) & 1:
        v[3] = -v[3]
    shift = (brut >> 36) & 3
    if shift == 0:
        q = (v[3], v[0], v[1], v[2])
    elif shift == 1:
        q = (v[0], v[3], v[1], v[2])
    elif shift == 2:
        q = (v[0], v[1], v[3], v[2])
    else:
        q = (v[0], v[1], v[2], v[3])
    return q, pos + 5

# ---------------------------------------------------------------------------
# Lecture d'un bloc complet
# ---------------------------------------------------------------------------

class PisteVectorielle(object):
    """Piste position ou echelle : composantes statiques ou spline."""
    __slots__ = ("statique", "spline", "degre", "noeuds", "points", "minmax")

    def __init__(self):
        self.statique = [None, None, None]
        self.spline = [False, False, False]
        self.degre = 0
        self.noeuds = []
        self.points = [[], [], []]
        self.minmax = [(0.0, 0.0)] * 3

    def est_statique(self):
        return not any(self.spline)

    def valeur(self, image):
        if not any(self.spline):
            defaut = 0.0
            return tuple(self.statique[i] if self.statique[i] is not None else defaut
                         for i in range(3))
        res = []
        for i in range(3):
            if self.spline[i]:
                res.append(_nurbs(self.degre, image, self.noeuds, self.points[i]))
            else:
                res.append(self.statique[i] if self.statique[i] is not None else 0.0)
        return tuple(res)


class PisteQuat(object):
    __slots__ = ("statique", "dynamique", "degre", "noeuds", "points")

    def __init__(self):
        self.statique = (0.0, 0.0, 0.0, 1.0)
        self.dynamique = False
        self.degre = 0
        self.noeuds = []
        self.points = []

    def valeur(self, image):
        if not self.dynamique:
            return self.statique
        return _nurbs_quat(self.degre, image, self.noeuds, self.points)


def _trouver_span(degre, valeur, nb_points, noeuds):
    if valeur >= noeuds[nb_points]:
        return nb_points - 1
    bas = degre
    haut = nb_points
    milieu = (bas + haut) // 2
    while valeur < noeuds[milieu] or valeur >= noeuds[milieu + 1]:
        if valeur < noeuds[milieu]:
            haut = milieu
        else:
            bas = milieu
        milieu = (bas + haut) // 2
    return milieu


def _nurbs(degre, image, noeuds, points):
    span = _trouver_span(degre, image, len(points), noeuds)
    n = [1.0] + [0.0] * degre
    for i in range(1, degre + 1):
        for j in range(i - 1, -1, -1):
            denom = noeuds[span + i - j] - noeuds[span - j]
            a = (image - noeuds[span - j]) / denom if denom else 0.0
            tmp = n[j] * a
            n[j + 1] += n[j] - tmp
            n[j] = tmp
    total = 0.0
    for i in range(degre + 1):
        total += points[span - i] * n[i]
    return total


def _nurbs_quat(degre, image, noeuds, points):
    # Les quaternions sont evalues composante par composante puis normalises.
    span = _trouver_span(degre, image, len(points), noeuds)
    n = [1.0] + [0.0] * degre
    for i in range(1, degre + 1):
        for j in range(i - 1, -1, -1):
            denom = noeuds[span + i - j] - noeuds[span - j]
            a = (image - noeuds[span - j]) / denom if denom else 0.0
            tmp = n[j] * a
            n[j + 1] += n[j] - tmp
            n[j] = tmp
    q = [0.0, 0.0, 0.0, 0.0]
    for i in range(degre + 1):
        p = points[span - i]
        for k in range(4):
            q[k] += p[k] * n[i]
    norme = math.sqrt(sum(v * v for v in q))
    if norme > 1e-8:
        q = [v / norme for v in q]
    return tuple(q)


def decoder_bloc(donnees, offset, nb_pistes, nb_flottants=0, journal=None):
    pos = offset
    masques = lire_masques(donnees, pos, nb_pistes)
    if journal is not None:
        journal.append(("masques", pos))
    pos += 4 * nb_pistes + nb_flottants
    pos = aligner(pos, 4)

    pistes = []
    for m in masques:
        if journal is not None:
            journal.append(("piste", pos))
        piste = {"pos": PisteVectorielle(), "rot": PisteQuat(),
                 "echelle": PisteVectorielle()}
        piste["echelle"].statique = [1.0, 1.0, 1.0]

        # position
        p = piste["pos"]
        p.spline = [m.type_pos(i) == STT_DYNAMIC for i in range(3)]
        if any(p.spline):
            nb_items = struct.unpack_from("<H", donnees, pos)[0]
            pos += 2
            p.degre = donnees[pos]
            pos += 1
            taille_noeuds = nb_items + p.degre + 2
            p.noeuds = list(donnees[pos:pos + taille_noeuds])
            pos += taille_noeuds
            pos = aligner(pos, 4)
            for i in range(3):
                if p.spline[i]:
                    p.minmax[i] = struct.unpack_from("<2f", donnees, pos)
                    pos += 8
                elif m.type_pos(i) == STT_STATIC:
                    p.statique[i] = struct.unpack_from("<f", donnees, pos)[0]
                    pos += 4
            for t in range(nb_items + 1):
                for i in range(3):
                    if not p.spline[i]:
                        continue
                    if m.quant_pos == QT_8BIT:
                        d = donnees[pos] / 255.0
                        pos += 1
                    else:
                        d = struct.unpack_from("<H", donnees, pos)[0] / 65535.0
                        pos += 2
                    mini, maxi = p.minmax[i]
                    p.points[i].append(mini + (maxi - mini) * d)
            pos = aligner(pos, 4)
        else:
            for i in range(3):
                if m.type_pos(i) == STT_STATIC:
                    p.statique[i] = struct.unpack_from("<f", donnees, pos)[0]
                    pos += 4

        # rotation
        r = piste["rot"]
        type_rot = m.type_rot()
        if type_rot == STT_DYNAMIC:
            r.dynamique = True
            nb_items = struct.unpack_from("<H", donnees, pos)[0]
            pos += 2
            r.degre = donnees[pos]
            pos += 1
            taille_noeuds = nb_items + r.degre + 2
            r.noeuds = list(donnees[pos:pos + taille_noeuds])
            pos += taille_noeuds
            if m.quant_rot in (QT_48BIT, QT_16BITQUAT):
                pos = aligner(pos, 2)
            elif m.quant_rot in (QT_32BIT, QT_UNCOMPRESSED):
                pos = aligner(pos, 4)
            for t in range(nb_items + 1):
                q, pos = lire_quat(donnees, pos, m.quant_rot)
                r.points.append(q)
        elif type_rot == STT_STATIC:
            r.statique, pos = lire_quat(donnees, pos, m.quant_rot)
        pos = aligner(pos, 4)

        # echelle
        e = piste["echelle"]
        e.spline = [m.type_echelle(i) == STT_DYNAMIC for i in range(3)]
        if any(e.spline):
            nb_items = struct.unpack_from("<H", donnees, pos)[0]
            pos += 2
            e.degre = donnees[pos]
            pos += 1
            taille_noeuds = nb_items + e.degre + 2
            e.noeuds = list(donnees[pos:pos + taille_noeuds])
            pos += taille_noeuds
            pos = aligner(pos, 4)
            for i in range(3):
                if e.spline[i]:
                    e.minmax[i] = struct.unpack_from("<2f", donnees, pos)
                    pos += 8
                elif m.type_echelle(i) == STT_STATIC:
                    e.statique[i] = struct.unpack_from("<f", donnees, pos)[0]
                    pos += 4
            for t in range(nb_items + 1):
                for i in range(3):
                    if not e.spline[i]:
                        continue
                    if m.quant_echelle == QT_8BIT:
                        d = donnees[pos] / 255.0
                        pos += 1
                    else:
                        d = struct.unpack_from("<H", donnees, pos)[0] / 65535.0
                        pos += 2
                    mini, maxi = e.minmax[i]
                    e.points[i].append(mini + (maxi - mini) * d)
            pos = aligner(pos, 4)
        else:
            for i in range(3):
                if m.type_echelle(i) == STT_STATIC:
                    e.statique[i] = struct.unpack_from("<f", donnees, pos)[0]
                    pos += 4
        pistes.append(piste)

    return pistes, masques, pos

# ---------------------------------------------------------------------------
# Ecriture : un bloc a partir des valeurs par image (pos, quat, scale)
# ---------------------------------------------------------------------------

FRACTAL_48 = 0.000043161


def encoder_quat48(q):
    """q = (x, y, z, w) normalise -> 6 octets au format Havok 48 bits."""
    v = list(q)
    norme = math.sqrt(sum(c * c for c in v))
    if norme > 1e-8:
        v = [c / norme for c in v]
    k = max(range(4), key=lambda i: abs(v[i]))
    autres = [v[i] for i in range(4) if i != k]
    vals = []
    for c in autres:
        iv = int(round(c / FRACTAL_48))
        iv = max(-16383, min(16384, iv))
        vals.append((iv + 16383) & 0x7FFF)
    mot_x = vals[0] | ((k & 1) << 15)
    mot_y = vals[1] | (((k >> 1) & 1) << 15)
    mot_z = vals[2] | ((1 if v[k] < 0.0 else 0) << 15)
    return struct.pack("<3H", mot_x, mot_y, mot_z)


def _encoder_vectorielle(valeurs, defaut):
    """valeurs : liste de tuples (x, y, z) ; defaut pour les composantes fixes
    quand la composante ne varie pas (0 pour position, 1 pour echelle)."""
    complets = list(zip(*valeurs))
    composantes = []
    for i in range(3):
        mini = min(complets[i])
        maxi = max(complets[i])
        if maxi - mini < 1e-7:
            composantes.append(("static", (mini + maxi) * 0.5))
        else:
            composantes.append(("spline", (mini, maxi)))
    return composantes


def encoder_bloc(images, nb_pistes, nb_flottants=0, journal=None, details=None):
    """images : liste (par image) de listes (par piste) de (pos, quat, echelle)."""
    nb_images = len(images)
    degre = 1

    masques = bytearray()
    corps = bytearray()
    for piste in range(nb_pistes):
        if journal is not None:
            journal.append(("piste", len(corps)))
        pos_valeurs = [images[f][piste][0] for f in range(nb_images)]
        rot_valeurs = [images[f][piste][1] for f in range(nb_images)]
        ech_valeurs = [images[f][piste][2] for f in range(nb_images)]

        pos_info = _encoder_vectorielle(pos_valeurs, 0.0)
        ech_info = _encoder_vectorielle(ech_valeurs, 1.0)

        # rotation : statique si toutes les cles sont quasi identiques
        ref = rot_valeurs[0]
        statique = all(abs(abs(sum(a * b for a, b in zip(ref, q))) - 1.0) < 1e-6
                       for q in rot_valeurs)

        quant = 1 | (2 << 2)  # positions 16 bits, rotations 48 bits
        bits_pos = 0
        for i in range(3):
            if pos_info[i][0] == "static":
                bits_pos |= 1 << i
            else:
                bits_pos |= 16 << i
        bits_ech = 0
        for i in range(3):
            if ech_info[i][0] == "static":
                bits_ech |= 1 << i
            else:
                bits_ech |= 16 << i
        bits_rot = 0x0F if statique else 0xF0

        if details is not None:
            details.append((piste, pos_info, statique, ech_info))

        masques += bytes([quant, bits_pos, bits_rot, bits_ech])

        # --- position
        if any(info[0] == "spline" for info in pos_info):
            corps += struct.pack("<H", nb_images - 1)
            corps += bytes([degre])
            nb = nb_images + degre + 1
            noeuds = [0, 0] + list(range(1, nb_images - 1)) + [nb_images - 1, nb_images - 1]
            corps += bytes(noeuds)
            corps += b"\0" * (aligner(len(corps), 4) - len(corps))
            for i in range(3):
                if pos_info[i][0] == "spline":
                    corps += struct.pack("<2f", *pos_info[i][1])
                else:
                    corps += struct.pack("<f", pos_info[i][1])
            for f in range(nb_images):
                for i in range(3):
                    if pos_info[i][0] == "spline":
                        mini, maxi = pos_info[i][1]
                        d = 0.0 if maxi <= mini else (pos_valeurs[f][i] - mini) / (maxi - mini)
                        corps += struct.pack("<H", max(0, min(65535, int(round(d * 65535.0)))))
            corps += b"\0" * (aligner(len(corps), 4) - len(corps))
        else:
            for i in range(3):
                if pos_info[i][0] == "static":
                    corps += struct.pack("<f", pos_info[i][1])

        # --- rotation
        if statique:
            corps += encoder_quat48(ref)
        else:
            corps += struct.pack("<H", nb_images - 1)
            corps += bytes([degre])
            noeuds = [0, 0] + list(range(1, nb_images - 1)) + [nb_images - 1, nb_images - 1]
            corps += bytes(noeuds)
            corps += b"\0" * (aligner(len(corps), 2) - len(corps))
            for q in rot_valeurs:
                corps += encoder_quat48(q)
        corps += b"\0" * (aligner(len(corps), 4) - len(corps))

        # --- echelle
        if any(info[0] == "spline" for info in ech_info):
            corps += struct.pack("<H", nb_images - 1)
            corps += bytes([degre])
            noeuds = [0, 0] + list(range(1, nb_images - 1)) + [nb_images - 1, nb_images - 1]
            corps += bytes(noeuds)
            corps += b"\0" * (aligner(len(corps), 4) - len(corps))
            for i in range(3):
                if ech_info[i][0] == "spline":
                    corps += struct.pack("<2f", *ech_info[i][1])
                else:
                    corps += struct.pack("<f", ech_info[i][1])
            for f in range(nb_images):
                for i in range(3):
                    if ech_info[i][0] == "spline":
                        mini, maxi = ech_info[i][1]
                        d = 0.0 if maxi <= mini else (ech_valeurs[f][i] - mini) / (maxi - mini)
                        # l'echelle est quantifiee sur 8 bits (bits 6-7 du masque = 0)
                        corps += bytes([max(0, min(255, int(round(d * 255.0))))])
            corps += b"\0" * (aligner(len(corps), 4) - len(corps))
        else:
            for i in range(3):
                if ech_info[i][0] == "static":
                    corps += struct.pack("<f", ech_info[i][1])

    entete = bytearray(masques)
    if nb_flottants:
        entete += b"\0" * nb_flottants
    entete += b"\0" * (aligner(len(entete), 4) - len(entete))
    return bytes(entete) + bytes(corps)
