"""
Ecriture d'un BND4 Sekiro (repack) — phase 1.

Principe de securite : on **preserve octet pour octet** tout ce qu'on ne
comprend pas (table de noms, table de hachage, champs inconnus des entrees) et
on ne retouche que ce qui doit l'etre : taille, taille non compressee et offset
de chaque fichier remplace.

Disposition etablie par mesure sur les BND4 Sekiro (c5400.chrbnd.dcx) :

    0x00  header (0x40)              magic "BND4", fileCount@0x0C, entriesOff@0x10,
                                     entrySize@0x20, dataOff@0x28, namesEnd@0x38
    0x40  table des entrees          fileCount x entrySize (0x24)
    0xD0  table des noms             chaines UTF-16LE terminees par 0
    ...   table de hachage           (copiee telle quelle, jamais regeneree)
    0x2D8 dataOff                    debut de la zone de donnees
    0x2E0 premier fichier            dataOff arrondi a 16
    ...   fichiers                   chacun aligne sur 16 octets

Entree (0x24 octets) : +0x00 flags, +0x04 id, +0x08 taille, +0x10 taille non
compressee (== taille ici), +0x18 offset, +0x1C INCONNU (copie tel quel),
+0x20 offset du nom.

Usage (module) :
    from bnd4_build import rebuild, list_entries
    nouveau = rebuild(vanilla_bytes, {"c5400.flver": nouveau_flver})
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bnd4_parse

ALIGN = 16


def align_up(value: int, align: int = ALIGN) -> int:
    return (value + align - 1) // align * align


def list_entries(data: bytes) -> tuple:
    """Retourne (fileCount, entriesOff, entrySize, dataOff, [entrees])."""
    if data[:4] != b"BND4":
        raise ValueError(f"pas un BND4 (magic={data[:4]!r})")
    fc = struct.unpack_from("<I", data, 0x0C)[0]
    eo = struct.unpack_from("<Q", data, 0x10)[0]
    es = struct.unpack_from("<Q", data, 0x20)[0]
    do = struct.unpack_from("<Q", data, 0x28)[0]

    ents = []
    for i in range(fc):
        base = eo + i * es
        name_off = struct.unpack_from("<I", data, base + 0x20)[0]
        ents.append({
            "index": i,
            "base": base,
            "flags": struct.unpack_from("<i", data, base + 0x00)[0],
            "id": struct.unpack_from("<i", data, base + 0x04)[0],
            "size": struct.unpack_from("<Q", data, base + 0x08)[0],
            "size2": struct.unpack_from("<Q", data, base + 0x10)[0],
            "offset": struct.unpack_from("<I", data, base + 0x18)[0],
            "unk1c": struct.unpack_from("<I", data, base + 0x1C)[0],
            "nameoff": name_off,
            "fullname": bnd4_parse.read_utf16(data, name_off),
        })
    return fc, eo, es, do, ents


def basename_of(fullname: str) -> str:
    return os.path.basename(fullname.replace("\\", "/"))


def rebuild(vanilla: bytes, replacements: dict, align: int = ALIGN,
            pad_total_to: int = None) -> bytes:
    """Reconstruit le BND4 en remplacant les fichiers dont le nom (base) est dans
    `replacements`. Les autres sont recopies telles quelles."""
    fc, eo, es, data_off, ents = list_entries(vanilla)

    out = bytearray(vanilla[:data_off])          # header + table + noms + hachages
    pos = align_up(data_off, align)
    out.extend(b"\0" * (pos - len(out)))

    for e in ents:
        key = basename_of(e["fullname"])
        blob = replacements.get(key)
        if blob is None:
            blob = vanilla[e["offset"]:e["offset"] + e["size"]]

        struct.pack_into("<Q", out, e["base"] + 0x08, len(blob))
        struct.pack_into("<Q", out, e["base"] + 0x10, len(blob))
        struct.pack_into("<I", out, e["base"] + 0x18, pos)

        out.extend(blob)
        pos = align_up(len(out), align)
        out.extend(b"\0" * (pos - len(out)))

    if pad_total_to:
        total = align_up(len(out), pad_total_to)
        out.extend(b"\0" * (total - len(out)))
    return bytes(out)


def describe(data: bytes) -> None:
    fc, eo, es, data_off, ents = list_entries(data)
    print(f"fileCount={fc} entriesOff=0x{eo:X} entrySize=0x{es:X} dataOff=0x{data_off:X}")
    for e in ents:
        print(f"  [{e['index']}] {basename_of(e['fullname']):<20} "
              f"off=0x{e['offset']:X} size={e['size']:,} unk1C=0x{e['unk1c']:X}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        import soulsutil
        print(f"### {p}")
        describe(soulsutil.load(p))
