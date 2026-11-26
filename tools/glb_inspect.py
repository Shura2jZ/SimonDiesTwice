"""
Inspecte un fichier .glb (glTF 2.0 binaire) sans dependance externe.

Le .glb est un conteneur : en-tete de 12 octets, puis des "chunks"
(JSON puis BIN). On lit le JSON et on resume ce qui nous interesse pour le
portage : maillages, primitives, materiaux, squelette (skin), boites englobantes.

Usage :
    python tools/glb_inspect.py chemin/vers/modele.glb
"""

import json
import struct
import sys

COMPONENT_TYPES = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
                   5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}

MODE_NAMES = {0: "POINTS", 1: "LINES", 2: "LINE_LOOP", 3: "LINE_STRIP",
              4: "TRIANGLES", 5: "TRIANGLE_STRIP", 6: "TRIANGLE_FAN"}


def read_glb(path):
    with open(path, "rb") as fh:
        data = fh.read()
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise SystemExit(f"ce n'est pas un .glb (magic={magic!r})")
    chunks, off = {}, 12
    while off < total:
        clen, ctype = struct.unpack_from("<II", data, off)
        payload = data[off + 8: off + 8 + clen]
        chunks[ctype] = payload
        off += 8 + clen
    gltf = json.loads(chunks[0x4E4F534A].decode("utf-8"))
    return gltf, chunks.get(0x004E4942, b""), version, total


def acc_info(gltf, idx):
    a = gltf["accessors"][idx]
    return a, a.get("count", 0), a.get("type", "?")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        raise SystemExit(__doc__)
    gltf, binary, version, total = read_glb(path)

    print(f"fichier      : {path}")
    print(f"glTF version : {version}   |   taille conteneur : {total:,} octets   |   bin : {len(binary):,} octets")
    asset = gltf.get("asset", {})
    print(f"generateur   : {asset.get('generator')}   |   version glTF : {asset.get('version')}")
    print()

    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    mats = gltf.get("materials", [])
    skins = gltf.get("skins", [])
    images = gltf.get("images", [])

    print(f"nodes        : {len(nodes)}")
    print(f"meshes       : {len(meshes)}")
    print(f"materials    : {len(mats)}")
    print(f"skins        : {len(skins)}")
    print(f"images       : {len(images)}")
    print(f"animations   : {len(gltf.get('animations', []))}")
    print()

    for i, m in enumerate(meshes):
        print(f"--- mesh [{i}] '{m.get('name')}' : {len(m.get('primitives', []))} primitive(s)")
        for j, p in enumerate(m["primitives"]):
            mode = MODE_NAMES.get(p.get("mode", 4), p.get("mode"))
            attrs = p.get("attributes", {})
            parts = []
            for k, v in sorted(attrs.items()):
                a, count, typ = acc_info(gltf, v)
                parts.append(f"{k}:{typ} x{count}")
            idx = p.get("indices")
            tri = ""
            if idx is not None:
                a, count, _ = acc_info(gltf, idx)
                tri = f" | indices x{count} (={count // 3} triangles) | {COMPONENT_TYPES.get(a['componentType'], ('?',))[1] * 8} bits"
            mat = p.get("material")
            mname = mats[mat].get("name") if mat is not None and mat < len(mats) else "-"
            print(f"    [{j}] {mode}{tri} | material: {mname}")
            print(f"        attributs: {', '.join(parts)}")
        print()

    # dimension du maillage : min/max des accessors POSITION
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    verts = 0
    for m in meshes:
        for p in m.get("primitives", []):
            pos = p.get("attributes", {}).get("POSITION")
            if pos is None:
                continue
            a = gltf["accessors"][pos]
            verts += a.get("count", 0)
            for k in range(3):
                if "min" in a:
                    lo[k] = min(lo[k], a["min"][k])
                if "max" in a:
                    hi[k] = max(hi[k], a["max"][k])
    if verts:
        print(f"total sommets (POSITION) : {verts:,}")
        print("boite englobante (unites du fichier) :")
        print(f"    min = ({lo[0]:.3f}, {lo[1]:.3f}, {lo[2]:.3f})")
        print(f"    max = ({hi[0]:.3f}, {hi[1]:.3f}, {hi[2]:.3f})")
        print(f"    taille = ({hi[0]-lo[0]:.3f}, {hi[1]-lo[1]:.3f}, {hi[2]-lo[2]:.3f})")
        print()

    # materiaux
    print("materials :")
    for i, m in enumerate(mats):
        pbr = m.get("pbrMetallicRoughness", {})
        base = pbr.get("baseColorTexture")
        bn = gltf["textures"][base["index"]].get("source") if base else None
        bname = images[bn].get("name") if bn is not None and bn < len(images) else "-"
        nt = m.get("normalTexture")
        nn = gltf["textures"][nt["index"]].get("source") if nt else None
        nname = images[nn].get("name") if nn is not None and nn < len(images) else "-"
        extra = [k for k in m if k not in ("name", "pbrMetallicRoughness", "normalTexture", "emissiveTexture",
                                           "occlusionTexture", "doubleSided", "alphaMode", "extensions")]
        print(f"    [{i}] {m.get('name')}  | baseColor={bname} | normal={nname}"
              f" | alphaMode={m.get('alphaMode','OPAQUE')} | doubleSided={m.get('doubleSided', False)}"
              f" | autres cles={extra}")
    print()

    # images
    print("images :")
    for i, im in enumerate(images):
        bv = gltf.get("bufferViews", [])[im["bufferView"]] if "bufferView" in im else {}
        print(f"    [{i}] {im.get('name')} | {im.get('mimeType')} | {bv.get('byteLength', 0):,} octets")
    print()

    # squelette
    for i, s in enumerate(skins):
        joints = s.get("joints", [])
        print(f"--- skin [{i}] '{s.get('name')}' : {len(joints)} os"
              f" | skeleton racine: {nodes[s['skeleton']].get('name') if 'skeleton' in s else '-'}")
        names = [nodes[j].get("name") for j in joints]
        print(f"    premiers os : {', '.join(names[:15])}")
        print(f"    derniers os : {', '.join(names[-8:])}")
    print()

    # chaine des noeuds (racines)
    roots = gltf.get("scenes", [{}])[0].get("nodes", [])
    def walk(ni, depth=0, limit=[40]):
        if limit[0] <= 0 or depth > 4:
            return
        n = nodes[ni]
        limit[0] -= 1
        kids = n.get("children", [])
        tag = []
        if "mesh" in n:
            tag.append(f"mesh={n['mesh']}")
        if "skin" in n:
            tag.append(f"skin={n['skin']}")
        if "translation" in n:
            tag.append("T=" + ",".join(f"{v:.3f}" for v in n["translation"]))
        print("    " + "  " * depth + f"- {n.get('name')} {' '.join(tag)} ({len(kids)} enfants)")
        for c in kids:
            walk(c, depth + 1, limit)
    print("scene (premiers niveaux) :")
    for r in roots:
        walk(r)


if __name__ == "__main__":
    main()
