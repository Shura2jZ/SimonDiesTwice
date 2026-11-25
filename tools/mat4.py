"""
Algebre 4x4 elementaire, sans dependance externe.

Convention unique et volontairement explicite, utilisee partout dans le projet :
  - une matrice est une liste de 4 listes de 4 flottants, rangee par rangee
    (m[0] = premiere rangee) ;
  - les vecteurs sont des colonnes : v' = M . v ;
  - mul(a, b) applique d'abord b, puis a (produit matriciel classique).

glTF stocke ses matrices par colonnes (spec glTF 2.0) : from_gltf_columns()
fait la conversion pour eviter toute confusion.
"""

import math


def identity():
    return [[1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def mul(a, b):
    """Produit matriciel : le resultat applique b puis a."""
    out = [[0.0] * 4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            s = 0.0
            for k in range(4):
                s += a[r][k] * b[k][c]
            out[r][c] = s
    return out


def mul_all(*mats):
    out = identity()
    for m in mats:
        out = mul(out, m)
    return out


def from_gltf_columns(seq):
    """Convertit 16 flottants stockes par colonnes (glTF) en matrice rangee."""
    return [[float(seq[c * 4 + r]) for c in range(4)] for r in range(4)]


def translation(x, y, z):
    m = identity()
    m[0][3], m[1][3], m[2][3] = float(x), float(y), float(z)
    return m


def scaling(x, y, z):
    m = identity()
    m[0][0], m[1][1], m[2][2] = float(x), float(y), float(z)
    return m


def diagonal(x, y, z):
    """Matrice diagonale (rotation de 180 degres si deux signes sont negatifs)."""
    return scaling(x, y, z)


def quat_to_matrix(x, y, z, w):
    """Quaternion (x, y, z, w) -> matrice de rotation."""
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n == 0.0:
        return identity()
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0.0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0.0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def trs(t, q, s):
    """Compose translation, rotation (quaternion) et echelle : M = T . R . S."""
    tq = quat_to_matrix(q[0], q[1], q[2], q[3])
    for r in range(3):
        for c in range(3):
            tq[r][c] *= s[c]
    tq[0][3], tq[1][3], tq[2][3] = float(t[0]), float(t[1]), float(t[2])
    return tq


def apply_point(m, v):
    """Transforme un point (translation incluse)."""
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    return (m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
            m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
            m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3])


def apply_dir(m, v):
    """Transforme une direction (sans translation) - pour normales et tangentes."""
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    return (m[0][0] * x + m[0][1] * y + m[0][2] * z,
            m[1][0] * x + m[1][1] * y + m[1][2] * z,
            m[2][0] * x + m[2][1] * y + m[2][2] * z)


def get_translation(m):
    return (m[0][3], m[1][3], m[2][3])


def inverse(m):
    """Inverse d'une matrice 4x4 par pivot de Gauss-Jordan (robuste, sans hypothese)."""
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(4)] for i, row in enumerate(m)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("matrice singuliere (colonne %d)" % col)
        a[col], a[pivot] = a[pivot], a[col]
        p = a[col][col]
        a[col] = [v / p for v in a[col]]
        for r in range(4):
            if r == col or a[r][col] == 0.0:
                continue
            f = a[r][col]
            a[r] = [a[r][k] - f * a[col][k] for k in range(8)]
    return [row[4:] for row in a]


def normalize(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0.0:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def fmt(v, nd=4):
    if isinstance(v, (list, tuple)):
        return "(" + ", ".join(fmt(x, nd) for x in v) + ")"
    return ("%." + str(nd) + "f") % v


def fmt_matrix(m, nd=3):
    return "\n".join("    [" + ", ".join(("%." + str(nd) + "f") % v for v in row) + "]" for row in m)
