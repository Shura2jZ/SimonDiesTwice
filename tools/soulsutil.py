"""
Outils communs Souls (Sekiro) reutilisables.

Contient : acces Oodle + decompression DCX + chargement generique.
Aucune ecriture dans les dossiers de jeu.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oodle import Oodle

OODLE_DLL = r"F:\Games\Sekiro - Shadows Die Twice\oo2core_6_win64.dll"

_oodle = None


def get_oodle() -> Oodle:
    global _oodle
    if _oodle is None:
        _oodle = Oodle(OODLE_DLL)
    return _oodle


def parse_dcx_header(data: bytes) -> dict:
    """Retourne les champs de l'en-tete DCX (big-endian) — cf. notes/00_inventaire.md."""
    if data[:4] != b"DCX\x00":
        raise ValueError("Ce n'est pas un DCX")
    unk04, dcs_off, dcp_off, unk10, unk14 = struct.unpack_from(">5I", data, 4)
    uncomp, comp = struct.unpack_from(">2I", data, dcs_off + 4)
    return {
        "unk04": unk04,
        "dcsOffset": dcs_off,
        "dcpOffset": dcp_off,
        "headersEnd": unk10,
        "dataStart": unk14,
        "uncompressedSize": uncomp,
        "compressedSize": comp,
        "compressionType": data[dcp_off + 4:dcp_off + 8].decode("ascii", "replace"),
    }


def decompress_dcx(data: bytes) -> bytes:
    h = parse_dcx_header(data)
    ctype = h["compressionType"]
    if ctype in ("KRAK", "OODL"):
        return get_oodle().decompress(data[h["dataStart"]:], h["uncompressedSize"])
    if ctype == "DFLT":
        # deflate/zlib : c'est ce qu'utilisent les outils communautaires (FLVER Editor,
        # DSMapStudio...) et le jeu l'accepte aussi.
        import zlib
        return zlib.decompress(data[h["dataStart"]:])
    raise NotImplementedError(f"Compression non geree : {ctype!r}")


def is_dcx(data: bytes) -> bool:
    return data[:4] == b"DCX\x00"


def load(path: str) -> bytes:
    """Charge un fichier et le decompresse s'il s'agit d'un DCX."""
    with open(path, "rb") as fh:
        data = fh.read()
    if is_dcx(data):
        return decompress_dcx(data)
    return data
