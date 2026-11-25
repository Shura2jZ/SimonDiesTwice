"""
M1 - Etape 2 (corrige) : lire un conteneur DCX de Sekiro et le decompresser.

Fait empiriquement etabli sur fc_m_0000.partsbnd.dcx :
  - les entiers de l'en-tete DCX sont BIG-ENDIAN
  - layout observe :
      0x00  "DCX\\0"
      0x04  u32 (0x00011000)
      0x08  u32 dcsOffset  (= 0x18)
      0x0C  u32 dcpOffset  (= 0x24)
      0x10  u32 (fin des en-tetes, = 0x44)
      0x14  u32 (debut des donnees compressees, = 0x4C)
      0x18  "DCS\\0" + u32 uncompressedSize + u32 compressedSize
      0x24  "DCP\\0" + char[4] compressionType ("KRAK" = Oodle/Kraken)
      data  a partir de l'offset indique en 0x14

Usage:
    python tools/dcx_inspect.py <fichier> [--dump]
"""
import sys
import os
import glob
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oodle import Oodle

OODLE_DLL = r"F:\Games\Sekiro - Shadows Die Twice\oo2core_6_win64.dll"


def hexdump(data: bytes, label: str = "") -> None:
    if label:
        print(f"--- {label} ---")
    for off in range(0, len(data), 16):
        chunk = data[off:off + 16]
        h = " ".join(f"{b:02X}" for b in chunk)
        a = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{off:08X}  {h:<47}  {a}")


def inspect(path: str, dump: bool, oodle: Oodle) -> None:
    size = os.path.getsize(path)
    print(f"\n########## {path}")
    print(f"Taille totale : {size:,} octets")

    with open(path, "rb") as fh:
        head = fh.read(0x30)
    hexdump(head, "En-tete (48 premiers octets)")

    if head[0:4] != b"DCX\x00":
        print(">> Pas un DCX. Magic :", head[0:4])
        return

    unk04, dcs_off, dcp_off, unk10, unk14 = struct.unpack_from(">5I", head, 4)

    with open(path, "rb") as fh:
        fh.seek(dcs_off)
        dcs = fh.read(0x0C)
        uncomp_size, comp_size = struct.unpack_from(">2I", dcs, 4)
        fh.seek(dcp_off)
        dcp = fh.read(0x20)
        comp_type = dcp[4:8].decode("ascii", "replace")

    print("\n[ETABLI] En-tete DCX (big-endian) :")
    print(f"  unk04            = 0x{unk04:08X}")
    print(f"  dcsOffset        = 0x{dcs_off:X}")
    print(f"  dcpOffset        = 0x{dcp_off:X}")
    print(f"  fin des en-tetes = 0x{unk10:X}")
    print(f"  debut des donnees= 0x{unk14:X}")
    print(f"  DCS.signature    = {dcs[0:4]!r}")
    print(f"  uncompressedSize = {uncomp_size:,}")
    print(f"  compressedSize   = {comp_size:,}")
    print(f"  DCP.signature    = {dcp[0:4]!r}")
    print(f"  compressionType  = {comp_type!r}")

    with open(path, "rb") as fh:
        fh.seek(unk14)
        comp = fh.read(size - unk14)

    print(f"\n[TEST] Decompression Oodle : {len(comp):,} octets compresses -> attendu {uncomp_size:,}")
    if comp_type != "KRAK" and comp_type != "OODL":
        print("  >> Type de compression non gere par ce script.")
        return
    try:
        out = oodle.decompress(comp, uncomp_size)
    except Exception as e:
        print(f"  ECHEC : {e}")
        return
    print(f"  OK -> {len(out):,} octets")
    print(f"  magic du contenu decompresse : {out[0:8]!r}")
    hexdump(out[:0x40], "Debut du contenu decompresse")
    if dump:
        # On n'ecrit JAMAIS dans le dossier du jeu : sortie dans le projet.
        outdir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "_work", "extracted",
        )
        os.makedirs(outdir, exist_ok=True)
        outp = os.path.join(outdir, os.path.basename(path) + ".decompressed")
        with open(outp, "wb") as f:
            f.write(out)
        print(f"  -> ecrit dans {outp}")


def main() -> None:
    args = sys.argv[1:]
    dump = "--dump" in args
    targets = [a for a in args if not a.startswith("--")]
    if not targets:
        print(__doc__)
        sys.exit(1)
    oodle = Oodle(OODLE_DLL)
    for t in targets:
        for m in (glob.glob(t) or [t]):
            if os.path.isfile(m):
                inspect(m, dump, oodle)
            else:
                print(f"Introuvable : {m}")


if __name__ == "__main__":
    main()
