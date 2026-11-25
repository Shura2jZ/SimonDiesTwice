"""Convertit le mesh statique PSKX de l'epee de Simon en SMPORT pour c5400.

Le mesh source ne contient pas de squelette ni de poids : on l'attache au bone
R_Katana d'Isshin (index 81 dans la palette FLVER), et on garde deux matieres
(handle / blade) pour les deux sets de textures. La sortie est un candidat de
travail ; la transformation du composant Unreal est configurable et devra etre
validee visuellement en jeu.

Usage :
    python tools/simon_sword_export.py <mesh.pskx> <sortie.bin>
        [--scale 0.01] [--pitch 64.6875] [--yaw 0] [--roll 180]
        [--translation X Y Z] [--bind-tsv isshin_nodes.tsv]
"""
import math
import os
import struct
import sys

# VTXW stores the vertex index in bytes 0..3, then U and V as float32 at
# offsets 4 and 8. FACE records contain 3 uint16 indices, a uint16 material id
# and 4 padding bytes.

def lire_chunks(path):
    data = open(path, "rb").read()
    chunks = {}
    pos = 0
    while pos + 32 <= len(data):
        name = data[pos:pos + 16].split(b"\0", 1)[0].decode("ascii", "replace")
        if not name:
            break
        size, count = struct.unpack_from("<ii", data, pos + 24)
        start = pos + 32
        end = start + size * count
        if size < 0 or count < 0 or end > len(data):
            raise ValueError("chunk PSKX invalide: " + name)
        chunks[name] = (start, size, count)
        pos = end
    for required in ("PNTS0000", "VTXW0000", "FACE0000", "VTXNORMS", "MATT0000"):
        if required not in chunks:
            raise ValueError("chunk PSKX manquant: " + required)
    return data, chunks


def rot_ue(v, pitch, yaw, roll):
    """FMatrix(FRotator): vecteur local -> repere Unreal (Z vers le haut)."""
    p, y, r = (math.radians(x) for x in (pitch, yaw, roll))
    sp, cp, sy, cy, sr, cr = math.sin(p), math.cos(p), math.sin(y), math.cos(y), math.sin(r), math.cos(r)
    m = ((cp * cy, sr * sp * cy - cr * sy, -cr * sp * cy - sr * sy),
         (cp * sy, sr * sp * sy + cr * cy, -cr * sp * sy + sr * cy),
         (sp, -sr * cp, cr * cp))
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def to_sekiro(v):
    # UE/Simon Z-up, Isshin Y-up; this is the same basis change used by
    # simon_export.py and retarget.py: (x,y,z) -> (x,z,-y).
    return (v[0], v[2], -v[1])


def ecrire_entete(f, nb_mesh):
    f.write(b"SMPORT\0\1")
    f.write(struct.pack("<I", nb_mesh))
    f.write(struct.pack("<9f", 1, 0, 0, 0, 1, 0, 0, 0, 1))
    # Maillage statique : les sommets utilisent l'os R_Katana directement.
    f.write(struct.pack("<I", 1))
    nom = b"R_Katana"
    f.write(struct.pack("<I", len(nom)) + nom + struct.pack("<i", 81))


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    source, output = sys.argv[1:3]
    scale, pitch, yaw, roll = 0.01, 64.6875, 0.0, 180.0
    translation = (0.0, 0.0, 0.0)
    bind_tsv = None
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        key = args[i]
        if key in ("--scale", "--pitch", "--yaw", "--roll"):
            val = float(args[i + 1]); i += 2
            if key == "--scale": scale = val
            elif key == "--pitch": pitch = val
            elif key == "--yaw": yaw = val
            else: roll = val
        elif key == "--translation":
            translation = tuple(float(x) for x in args[i + 1:i + 4]); i += 4
        elif key == "--bind-tsv":
            bind_tsv = args[i + 1]; i += 2
        else:
            raise SystemExit("option inconnue: " + key)

    bind = None
    if bind_tsv:
        for line in open(bind_tsv, encoding="utf-8"):
            c = line.rstrip("\n").split("\t")
            if len(c) >= 29 and c[3] == "R_Katana":
                m = [float(x) for x in c[13:29]]
                bind = (m[:12], m[12:15])
                break
        if bind is None:
            raise ValueError("R_Katana absent du TSV : " + bind_tsv)

    data, chunks = lire_chunks(source)
    p0, _, nv = chunks["PNTS0000"]
    w0, _, nw = chunks["VTXW0000"]
    n0, _, nn = chunks["VTXNORMS"]
    f0, _, nf = chunks["FACE0000"]
    if nv != nw or nv != nn:
        raise ValueError("comptes PNTS/VTXW/VTXNORMS differents")

    positions, normals, uvs = [], [], []
    for v in range(nv):
        p = struct.unpack_from("<3f", data, p0 + v * 12)
        n = struct.unpack_from("<3f", data, n0 + v * 12)
        # VTXW: uint32 vertex index followed by U and V float32.
        uv = struct.unpack_from("<2f", data, w0 + v * 16 + 4)
        rp = rot_ue(p, pitch, yaw, roll)
        rn = rot_ue(n, pitch, yaw, roll)
        sp = to_sekiro(tuple(x * scale for x in rp))
        sn = to_sekiro(rn)
        # Dans le repere de R_Katana, l'axe long exporte (Z) est tourne vers +X.
        # La matrice de repos de R_Katana dirige alors la lame vers l'avant.
        sp = (sp[2], sp[1], -sp[0])
        sn = (sn[2], sn[1], -sn[0])
        length = math.sqrt(sum(x * x for x in sn)) or 1.0
        if bind is not None:
            m, t = bind
            sp = (sp[0] * m[0] + sp[1] * m[4] + sp[2] * m[8] + t[0],
                  sp[0] * m[1] + sp[1] * m[5] + sp[2] * m[9] + t[1],
                  sp[0] * m[2] + sp[1] * m[6] + sp[2] * m[10] + t[2])
            sn = (sn[0] * m[0] + sn[1] * m[4] + sn[2] * m[8],
                  sn[0] * m[1] + sn[1] * m[5] + sn[2] * m[9],
                  sn[0] * m[2] + sn[1] * m[6] + sn[2] * m[10])
            length = math.sqrt(sum(x * x for x in sn)) or 1.0
        positions.append(tuple(sp[k] + translation[k] for k in range(3)))
        normals.append(tuple(x / length for x in sn))
        uvs.append(uv)

    indices = [[], []]
    for face in range(nf):
        a, b, c, material = struct.unpack_from("<3HH", data, f0 + face * 12)
        if material > 1:
            raise ValueError("index materiau PSKX non pris en charge: %d" % material)
        indices[material].extend((a, b, c))

    noms = ("Simon Sword Handle", "Simon Sword Blade")
    materiaux = (10, 27)  # weapon00 / weapon00_02 : deux espaces texture distincts
    noeud = 207  # c5400_sword002, emplacement FLVER d'origine du mesh en main
    tangentes = []
    for nx, ny, nz in normals:
        # Choisir un axe qui ne soit pas parallele a la normale.
        axis = (0.0, 1.0, 0.0) if abs(ny) < 0.9 else (1.0, 0.0, 0.0)
        tx, ty, tz = (axis[1] * nz - axis[2] * ny,
                      axis[2] * nx - axis[0] * nz,
                      axis[0] * ny - axis[1] * nx)
        length = math.sqrt(tx * tx + ty * ty + tz * tz) or 1.0
        tangentes.append((tx / length, ty / length, tz / length, 1.0))

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "wb") as f:
        ecrire_entete(f, 2)
        for material in range(2):
            bname = noms[material].encode("utf-8")
            f.write(struct.pack("<I", len(bname)) + bname)
            f.write(struct.pack("<iiiII", materiaux[material], noeud, -1, nv, len(indices[material])))
            for v in range(nv):
                f.write(struct.pack("<3f3f4f2f4f4i4f",
                    *positions[v], *normals[v], *tangentes[v], *uvs[v],
                    1.0, 1.0, 1.0, 1.0,
                    81, 0, 0, 0, 1.0, 0.0, 0.0, 0.0))
            for index in indices[material]:
                f.write(struct.pack("<I", index))

    allp = positions
    print("PSKX : %d sommets, %d triangles handle, %d triangles blade" %
          (nv, len(indices[0]) // 3, len(indices[1]) // 3))
    print("attache : R_Katana (palette 81), node c5400_sword002 (207)")
    print("transform : scale %.4f, rot UE P/Y/R = %.4f / %.4f / %.4f" % (scale, pitch, yaw, roll))
    print("bbox FLVER : (%.4f %.4f %.4f) .. (%.4f %.4f %.4f)" %
          (min(p[0] for p in allp), min(p[1] for p in allp), min(p[2] for p in allp),
           max(p[0] for p in allp), max(p[1] for p in allp), max(p[2] for p in allp)))
    print("ecrit : %s (%d octets)" % (output, os.path.getsize(output)))


if __name__ == "__main__":
    main()
