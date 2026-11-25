"""
Ecriture d'un conteneur DCX Sekiro (Oodle / KRAK).

FAITS (mesures + SoulsAssetPipeline) :

1. En-tete DCX = prefixe FIXE de 0x4C octets ; seules les deux tailles de la
   section DCS varient.

     offset  contenu
     0x00    "DCX\0"
     0x04    u32 = 0x00011000
     0x08    u32 dcsOffset   = 0x18
     0x0C    u32 dcpOffset   = 0x24
     0x10    u32 headersEnd  = 0x44
     0x14    u32 dataStart   = 0x4C
     0x18    "DCS\0" + u32 uncompressedSize + u32 compressedSize
     0x24    "DCP\0" "KRAK" + u32 0x20 + u8 niveau + (3 octets nuls)
             + 3 x u32 nuls + u32 0x00010100
     0x30    ^ l'octet de niveau est ICI (FromSoft ecrit 6)
     0x44    "DCA\0" + u32 = 0x00000008   (constant)
     0x4C    flux Oodle (Kraken, AVEC table de sauts)

2. Le flux Oodle DOIT etre decoupe en tranches (seekChunkReset) : le jeu lit
   par tranches et plante sinon (SoulsAssetPipeline : "Required for the game
   to not crash"). Voir tools/oodle.py.

3. Le FICHIER doit etre rembourre de zeros jusqu'a un multiple de 16. Mesure
   sur 6 DCX vanilla : la taille du fichier est TOUJOURS multiple de 16, avec
   1 a 7 octets de zeros apres le flux (non comptes dans compressedSize).
   SoulsAssetPipeline fait de meme (bw.Pad(0x10)).

Usage (module) :
    from dcx_build import build_dcx, DCX_PREFIX_LEN
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from soulsutil import get_oodle, parse_dcx_header

DCX_PREFIX_LEN = 0x4C
DCX_PREFIX_ALIGNEMENT = 0x10
OFFSET_NIVEAU = 0x30

DCX_PREFIX = bytes.fromhex(
    "44435800"      # "DCX\0"
    "00011000"      # unk04  (constant)
    "00000018"      # dcsOffset
    "00000024"      # dcpOffset
    "00000044"      # headersEnd
    "0000004c"      # dataStart
    "44435300"      # "DCS\0"
    "00000000"      # <- uncompressedSize (patche)
    "00000000"      # <- compressedSize   (patche)
    "44435000"      # "DCP\0"
    "4b52414b"      # "KRAK"
    "00000020"      # constant
    "06000000"      # niveau de compression declare (patche par build_dcx)
    "00000000"      # constant
    "00000000"      # constant
    "00000000"      # constant
    "00010100"      # constant
    "44434100"      # "DCA\0"
    "00000008"      # constant
)
assert len(DCX_PREFIX) == DCX_PREFIX_LEN, len(DCX_PREFIX)


def build_dcx(raw: bytes, level: int = 6, rembourrer: bool = True) -> bytes:
    """Construit un DCX (KRAK) contenant `raw`.

    level : 6 par defaut, car c'est la valeur que FromSoft inscrit dans ses
    propres fichiers (bloc DCP, offset 0x30), et le niveau passe a Oodle est
    rendu coherent avec elle.
    """
    oodle = get_oodle()
    comp = oodle.compress(raw, level=level)
    hdr = bytearray(DCX_PREFIX)
    struct.pack_into(">I", hdr, 0x1C, len(raw))    # uncompressedSize
    struct.pack_into(">I", hdr, 0x20, len(comp))   # compressedSize
    hdr[OFFSET_NIVEAU] = level & 0xFF              # niveau declare

    fichier = bytes(hdr) + comp
    if rembourrer:
        reste = (-len(fichier)) % DCX_PREFIX_ALIGNEMENT
        fichier += b"\0" * reste
    return fichier


def check_prefix(original_dcx: bytes) -> bool:
    """Verifie que notre prefixe constant == celui d'un DCX vanilla (hors tailles)."""
    orig = bytearray(original_dcx[:DCX_PREFIX_LEN])
    mine = bytearray(DCX_PREFIX)
    for off in (0x1C, 0x20):
        orig[off:off + 4] = b"\0\0\0\0"
        mine[off:off + 4] = b"\0\0\0\0"
    return bytes(orig) == bytes(mine)
