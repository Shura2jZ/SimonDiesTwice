"""
Lecture de la table d'exports d'une DLL Windows (PE32/PE32+).

Sert ici a verifier quelles fonctions Oodle sont REELLEMENT exportees par
oo2core_6_win64.dll, avant d'ecrire du code qui les appelle.

Usage:
    python tools/pe_exports.py <chemin.dll> [filtre]
"""
import struct
import sys


def rva_to_offset(sections, rva: int):
    for va, vsize, praw, rsize in sections:
        if va <= rva < va + max(vsize, rsize):
            return praw + (rva - va)
    return None


def read_cstr(data: bytes, off: int) -> str:
    end = data.index(b"\x00", off)
    return data[off:end].decode("ascii", "replace")


def exports(path: str):
    d = open(path, "rb").read()
    if d[:2] != b"MZ":
        raise ValueError("pas un PE")
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    if d[pe:pe + 4] != b"PE\x00\x00":
        raise ValueError("signature PE absente")

    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    optsize = struct.unpack_from("<H", d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", d, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)

    sects = []
    soff = opt + optsize
    for i in range(nsec):
        s = soff + i * 40
        vsize, va, rsize, praw = struct.unpack_from("<4I", d, s + 8)
        sects.append((va, vsize, praw, rsize))

    exp_rva, exp_size = struct.unpack_from("<2I", d, dd)
    if exp_rva == 0:
        return []
    eoff = rva_to_offset(sects, exp_rva)
    nnames, _, rva_funcs, rva_names, rva_ords = struct.unpack_from("<5I", d, eoff + 0x14)

    foff = rva_to_offset(sects, rva_funcs)
    noff = rva_to_offset(sects, rva_names)
    ooff = rva_to_offset(sects, rva_ords)
    if None in (foff, noff, ooff):
        return []

    out = []
    for i in range(nnames):
        name_rva = struct.unpack_from("<I", d, noff + 4 * i)[0]
        ordi = struct.unpack_from("<H", d, ooff + 2 * i)[0]
        n_off = rva_to_offset(sects, name_rva)
        if n_off is None:
            continue
        out.append((read_cstr(d, n_off), struct.unpack_from("<I", d, foff + 4 * ordi)[0]))
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    filt = sys.argv[2] if len(sys.argv) > 2 else ""
    exps = exports(path)
    sel = [e for e in exps if filt.lower() in e[0].lower()]
    print(f"{path} : {len(exps)} exports, {len(sel)} correspondant a {filt!r}")
    for name, rva in sorted(sel):
        print(f"   {name}")


if __name__ == "__main__":
    main()
