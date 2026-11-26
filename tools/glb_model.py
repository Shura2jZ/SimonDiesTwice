"""
Lecteur de fichiers .glb (glTF 2.0 binaire) en Python pur, sans dependance.

Ne lit que ce dont on a besoin pour le portage : la geometrie (avec tous ses
attributs), le squelette (os + matrices de pose de reference) et la hierarchie
des noeuds. Les textures, animations et extensions sont ignorees.

Conventions :
  - les valeurs brutes des accesseurs sont renvoyees telles quelles, en tuples ;
  - les matrices de pose de reference sont converties dans la convention du
    projet (voir tools/mat4.py) : matrice rangee, vecteur colonne ;
  - le Y est l'axe haut (convention glTF), le modele est pose sur l'origine.

Usage en ligne de commande :
    python tools/glb_model.py modele.glb
"""

import json
import struct
import sys

import mat4

COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
             5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}

TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
                   "MAT2": 4, "MAT3": 9, "MAT4": 16}


class Glb:
    """Conteneur .glb : en-tete de 12 octets, chunk JSON, chunk binaire."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            data = fh.read()
        magic, version, total = struct.unpack_from("<4sII", data, 0)
        if magic != b"glTF":
            raise ValueError("ce n'est pas un .glb (magic=%r)" % magic)
        self.version = version
        self.size = total
        self.json = None
        self.bin = b""
        off = 12
        while off < total:
            clen, ctype = struct.unpack_from("<II", data, off)
            payload = data[off + 8: off + 8 + clen]
            if ctype == 0x4E4F534A:
                self.json = json.loads(payload.decode("utf-8"))
            elif ctype == 0x004E4942:
                self.bin = payload
            off += 8 + clen
        if self.json is None:
            raise ValueError("chunk JSON absent")

    # --- acces brut -------------------------------------------------------

    def view_bytes(self, view_index):
        v = self.json["bufferViews"][view_index]
        start = v.get("byteOffset", 0)
        return self.bin[start: start + v["byteLength"]]

    def raw_accessor_bytes(self, acc_index):
        """Octets bruts d'un accesseur (sans interpretation), stride respecte."""
        acc = self.json["accessors"][acc_index]
        fmt, size = COMPONENT[acc["componentType"]]
        ncomp = TYPE_COMPONENTS[acc["type"]]
        elem = size * ncomp
        view = self.json["bufferViews"][acc["bufferView"]]
        stride = view.get("byteStride", elem)
        base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        out = bytearray()
        for i in range(acc["count"]):
            off = base + i * stride
            out += self.bin[off: off + elem]
        return bytes(out), fmt, size, ncomp, acc.get("normalized", False)

    def accessor(self, acc_index):
        """Valeurs d'un accesseur : liste de tuples (VEC*) ou de flottants (SCALAR)."""
        data, fmt, size, ncomp, normalized = self.raw_accessor_bytes(acc_index)
        div = 1.0
        if normalized:
            if fmt in ("b", "h"):
                div = float(2 ** (8 * size - 1) - 1)
            elif fmt in ("B", "H"):
                div = float(2 ** (8 * size) - 1)
        values = struct.unpack("<" + fmt * (ncomp * (len(data) // (size * ncomp))), data)
        out = []
        for i in range(0, len(values), ncomp):
            chunk = [v / div for v in values[i:i + ncomp]]
            out.append(chunk[0] if ncomp == 1 else tuple(chunk))
        return out

    def matrices(self, acc_index):
        """Accesseur de matrices 4x4 -> liste de matrices (convention projet)."""
        data, fmt, size, ncomp, _ = self.raw_accessor_bytes(acc_index)
        if ncomp != 16:
            raise ValueError("accesseur %d n'est pas MAT4" % acc_index)
        out = []
        step = 16 * size
        for i in range(0, len(data), step):
            vals = struct.unpack_from("<" + fmt * 16, data, i)
            out.append(mat4.from_gltf_columns(vals))
        return out

    # --- scene ------------------------------------------------------------

    def node_globals(self):
        """Transformation globale de chaque noeud (hierarchie + TRS ou matrice)."""
        nodes = self.json.get("nodes", [])
        out = [None] * len(nodes)

        def local(n):
            if "matrix" in n:
                return mat4.from_gltf_columns(n["matrix"])
            t = n.get("translation", (0.0, 0.0, 0.0))
            q = n.get("rotation", (0.0, 0.0, 0.0, 1.0))
            s = n.get("scale", (1.0, 1.0, 1.0))
            return mat4.trs(t, q, s)

        def walk(i, parent):
            # Vecteurs colonnes : la transformation globale est parent @ local.
            # L'ordre inverse perdait les translations des parents dans la chaine
            # et faussait les bind transforms (notamment epaules et bras).
            m = mat4.mul(parent, local(nodes[i]))
            out[i] = m
            for c in nodes[i].get("children", []):
                walk(c, m)

        for root in self.json.get("scenes", [{}])[0].get("nodes", []):
            walk(root, mat4.identity())
        return out

    def skin(self, index=0):
        """Renvoie (liste des noeuds d'os, matrices de pose de reference)."""
        skin = self.json["skins"][index]
        joints = skin["joints"]
        if "inverseBindMatrices" not in skin:
            return joints, [mat4.identity() for _ in joints]
        ibms = self.matrices(skin["inverseBindMatrices"])
        return joints, [mat4.inverse(m) for m in ibms]

    def bone_names(self, joints):
        nodes = self.json.get("nodes", [])
        return [nodes[j].get("name", "os%d" % j) for j in joints]

    def vertex_bounds(self):
        lo = [float("inf")] * 3
        hi = [float("-inf")] * 3
        n = 0
        for mesh in self.json.get("meshes", []):
            for prim in mesh.get("primitives", []):
                acc_index = prim.get("attributes", {}).get("POSITION")
                if acc_index is None:
                    continue
                acc = self.json["accessors"][acc_index]
                n += acc["count"]
                for k in range(3):
                    lo[k] = min(lo[k], acc["min"][k])
                    hi[k] = max(hi[k], acc["max"][k])
        return lo, hi, n

    def report(self):
        j = self.json
        lo, hi, nverts = self.vertex_bounds()
        print("fichier        : %s" % self.path)
        print("generateur     : %s" % j.get("asset", {}).get("generator"))
        print("noeuds         : %d   maillages : %d   materiaux : %d   peaux : %d"
              % (len(j.get("nodes", [])), len(j.get("meshes", [])),
                 len(j.get("materials", [])), len(j.get("skins", []))))
        print("sommets        : %d" % nverts)
        print("etendue        : min %s  max %s" % (mat4.fmt(lo), mat4.fmt(hi)))
        print("taille         : X %.3f  Y %.3f  Z %.3f"
              % (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
        for i, s in enumerate(j.get("skins", [])):
            joints, binds = self.skin(i)
            print("peau %d         : %d os, noeud d'origine %s"
                  % (i, len(joints), j.get("nodes", [])[joints[0]].get("name")))
        return 0


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    Glb(sys.argv[1]).report()


if __name__ == "__main__":
    main()
