"""
Comparer deux BND4 Sekiro : ordre des entrees, noms, tailles, empreintes.

Une reconstruction de BND4 peut etre auto-coherente (relue correctement par notre
propre outil) tout en etant lue differemment par le jeu : ordre des entrees,
identifiants, table des noms. Ce script compare donc les deux fichiers entree par
entree, dans l'ordre, et signale toute difference d'ordre ou de contenu.

Usage :
    python tools/bnd_compare.py <reference.dcx> <candidat.dcx>
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil
import bnd4_parse


def header(data: bytes) -> dict:
    return {
        "fileCount": struct.unpack_from("<I", data, 0x0C)[0],
        "entriesOff": struct.unpack_from("<Q", data, 0x10)[0],
        "entrySize": struct.unpack_from("<Q", data, 0x20)[0],
        "dataOff": struct.unpack_from("<Q", data, 0x28)[0],
        "namesEnd": struct.unpack_from("<Q", data, 0x38)[0],
        "unk18": data[0x18:0x20],
        "unk30": struct.unpack_from("<Q", data, 0x30)[0],
        "unk00": data[0x00:0x0C],
    }


def entries(path: str):
    data = soulsutil.load(path)
    h = header(data)
    out = []
    for i in range(h["fileCount"]):
        b = h["entriesOff"] + i * h["entrySize"]
        flags = struct.unpack_from("<i", data, b + 0x00)[0]
        eid = struct.unpack_from("<i", data, b + 0x04)[0]
        size = struct.unpack_from("<Q", data, b + 0x08)[0]
        size2 = struct.unpack_from("<Q", data, b + 0x10)[0]
        off = struct.unpack_from("<I", data, b + 0x18)[0]
        unk1c = struct.unpack_from("<I", data, b + 0x1C)[0]
        no = struct.unpack_from("<I", data, b + 0x20)[0]
        name = bnd4_parse.read_utf16(data, no)
        blob = data[off:off + size]
        out.append({
            "index": i, "flags": flags, "id": eid, "size": size, "size2": size2,
            "offset": off, "unk1c": unk1c, "nameOff": no, "name": name,
            "sha": hashlib.sha256(blob).hexdigest(),
            "magic": blob[:4],
        })
    return data, h, out


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    ref_data, ref_h, ref = entries(sys.argv[1])
    cur_data, cur_h, cur = entries(sys.argv[2])

    print(f"\n########## en-tete ##########")
    for k in ref_h:
        a, b = ref_h[k], cur_h[k]
        print(f"  {k:<12} reference = {a!r:<24} candidat = {b!r:<24} {'IDENTIQUE' if a == b else '>>> DIFFERENT'}")

    print(f"\n########## entrees (ordre) ##########")
    print(f"  reference : {len(ref)} entrees      candidat : {len(cur)} entrees")
    n = max(len(ref), len(cur))
    for i in range(n):
        a = ref[i] if i < len(ref) else None
        b = cur[i] if i < len(cur) else None
        na = a["name"] if a else "(absent)"
        nb = b["name"] if b else "(absent)"
        marque = ""
        if a and b:
            if a["name"] != b["name"]:
                marque = "  <<< NOM DIFFERENT"
            elif a["sha"] != b["sha"]:
                marque = "  <<< CONTENU DIFFERENT"
        print(f"  [{i}] ref {na:<28} cand {nb:<28}{marque}")

    print(f"\n########## detail des entrees du candidat ##########")
    for e in cur:
        ident = (e["size"] == e["size2"])
        print(f"  [{e['index']}] flags=0x{e['flags']:X} id={e['id']} size={e['size']:,}"
              f" size2={e['size2']:,} identiques={ident}"
              f" offset=0x{e['offset']:X} unk1C=0x{e['unk1c']:X} nameOff=0x{e['nameOff']:X}")
        print(f"        nom={e['name']}  magic={e['magic']!r}  sha={e['sha'][:16]}")

    print(f"\n########## detail des entrees de la reference ##########")
    for e in ref:
        ident = (e["size"] == e["size2"])
        print(f"  [{e['index']}] flags=0x{e['flags']:X} id={e['id']} size={e['size']:,}"
              f" size2={e['size2']:,} identiques={ident}"
              f" offset=0x{e['offset']:X} unk1C=0x{e['unk1c']:X} nameOff=0x{e['nameOff']:X}")
        print(f"        nom={e['name']}  magic={e['magic']!r}  sha={e['sha'][:16]}")


if __name__ == "__main__":
    main()
