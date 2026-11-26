"""
M1 - Etape 4 : parseur BND4 Sekiro (base sur des observations, pas sur des suppositions).

Champs du header CONFIRMES par recoupement sur fc_m_0000.partsbnd.dcx :
  fileCount  = u32 LE @ 0x0C   (= 5)
  entriesOff = u64 LE @ 0x10   (= 0x40)
  entrySize  = u64 LE @ 0x20   (= 0x24)
  dataOff    = u64 LE @ 0x28   (= 0x410)
  namesEnd   = u64 LE @ 0x38   (= 0x3C8)
  (0x10 + fileCount*entrySize doit etre egal a la fin de la table, et
   dataOff doit tomber juste apres la zone des noms)

Champs d'une entree (0x24 octets) :
  +0x00 i32 flags
  +0x04 i32 id (-1 = absent)
  +0x08 i64 size
  +0x10 i64 size (bis : egal a size -> donnee NON compressee)
  +0x18 i32 offset (absolu dans le BND4)
  +0x1C i32 ? (inconnu)
  +0x20 i32 nameOffset (absolu dans le BND4)

ATTENTION : la signification exacte de +0x1C et de certains champs du header
reste a confirmer. Le script VALIDE la coherence (offsets + sizes).

Usage:
    python tools/bnd4_parse.py <fichier>
"""
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soulsutil


def read_utf16(data: bytes, off: int, maxbytes: int = 1024) -> str:
    end = off
    while end + 1 < len(data) and end - off < maxbytes:
        if data[end] == 0 and data[end + 1] == 0:
            break
        end += 2
    return data[off:end].decode("utf-16-le", "replace")


def read_ascii_z(data: bytes, off: int, maxbytes: int = 256) -> str:
    end = data.find(b"\x00", off, off + maxbytes)
    if end == -1:
        end = min(len(data), off + maxbytes)
    return data[off:end].decode("ascii", "replace")


def identify(data: bytes, off: int) -> str:
    """Deviner le type du blob a un offset donne (par son magic)."""
    if off < 0 or off + 12 > len(data):
        return "hors limites"
    head = data[off:off + 16]
    if head[:4] == b"DDS ":
        return "DDS (texture)"
    if head[:4] == b"FLVER":
        return "FLVER (modele)"
    if head[:4] == b"TPF\x00":
        return "TPF (bundle de textures)"
    if head[:4] == b"DCX\x00":
        return "DCX (a decompresser)"
    if head[:4] == b"BND4":
        return "BND4 (sous-archive)"
    return f"inconnu ({head[:4]!r})"


def parse(path: str) -> None:
    data = soulsutil.load(path)
    print(f"\n########## {path}  ({len(data):,} octets decompresses)")
    if data[:4] != b"BND4":
        print(">> pas un BND4")
        return

    file_count = struct.unpack_from("<I", data, 0x0C)[0]
    entries_off = struct.unpack_from("<Q", data, 0x10)[0]
    entry_size = struct.unpack_from("<Q", data, 0x20)[0]
    data_off = struct.unpack_from("<Q", data, 0x28)[0]
    names_end = struct.unpack_from("<Q", data, 0x38)[0]
    unk_18 = data[0x18:0x20]
    unk_30 = struct.unpack_from("<Q", data, 0x30)[0]

    print(f"fileCount   = {file_count}")
    print(f"entriesOff  = 0x{entries_off:X}")
    print(f"entrySize   = 0x{entry_size:X}")
    print(f"dataOff     = 0x{data_off:X}")
    print(f"namesEnd    = 0x{names_end:X}")
    print(f"0x18 (8o)   = {unk_18!r}")
    print(f"0x30 (u64)  = 0x{unk_30:X} ({unk_30})")

    table_end = entries_off + file_count * entry_size
    print(f"\n[verif] fin de table = 0x{table_end:X} (attendu 0xF4)")

    print("\n--- Entrees ---")
    total = 0
    for i in range(file_count):
        base = entries_off + i * entry_size
        flags = struct.unpack_from("<i", data, base + 0x00)[0]
        eid = struct.unpack_from("<i", data, base + 0x04)[0]
        size = struct.unpack_from("<Q", data, base + 0x08)[0]
        size2 = struct.unpack_from("<Q", data, base + 0x10)[0]
        offset = struct.unpack_from("<I", data, base + 0x18)[0]
        unk1c = struct.unpack_from("<I", data, base + 0x1C)[0]
        name_off = struct.unpack_from("<I", data, base + 0x20)[0]

        name = read_utf16(data, name_off)
        kind = identify(data, offset)
        total += size

        print(f"\n  [{i}] flags=0x{flags:X} id={eid}")
        print(f"      size={size:,}  size2={size2:,}  (identiques: {size == size2})")
        print(f"      offset=0x{offset:X} ({offset:,})  unk1C=0x{unk1c:X}  nameOff=0x{name_off:X}")
        print(f"      nom   = {name}")
        print(f"      type  = {kind}")

    print(f"\n[verif] somme des sizes = {total:,}")
    print(f"[verif] dataOff + somme   = {data_off + total:,}  (taille fichier = {len(data):,})")

    # magics attendus aux offsets
    print("\n--- Magics aux offsets des entrees ---")
    for i in range(file_count):
        base = entries_off + i * entry_size
        offset = struct.unpack_from("<I", data, base + 0x18)[0]
        print(f"  [{i}] @0x{offset:X} : {data[offset:offset+8]!r}  -> {identify(data, offset)}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        parse(p)


if __name__ == "__main__":
    main()
