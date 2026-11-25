"""
M2 - Test de round-trip DCX : decompresser -> recompresser -> redecompresser.

Objectif : prouver qu'on sait ECRIRE un DCX chargeable par le jeu, sans rien
toucher au dossier du jeu (sortie dans _work/).

Usage :
    python tools/roundtrip_test.py <fichier.dcx> [<fichier2.dcx> ...]
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from soulsutil import load, parse_dcx_header
from dcx_build import build_dcx, check_prefix, DCX_PREFIX_LEN

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_work", "roundtrip")


def test(path: str) -> bool:
    raw_file = open(path, "rb").read()
    if raw_file[:4] != b"DCX\x00":
        print(f"[SKIP] {path} : pas un DCX")
        return False

    h = parse_dcx_header(raw_file)
    print(f"--- {os.path.basename(path)} : {len(raw_file):,} o, decompression...", flush=True)
    original = load(path)                      # decompression (notre code)
    print(f"    -> {len(original):,} o ; recompression...", flush=True)
    rebuilt = build_dcx(original)              # notre ecriture
    print(f"    -> {len(rebuilt):,} o ; verification...", flush=True)
    import soulsutil
    roundtrip = soulsutil.decompress_dcx(rebuilt)

    ok_prefix = check_prefix(raw_file)
    ok_data = roundtrip == original

    print(f"--- {os.path.basename(path)}")
    print(f"    taille DCX vanilla     : {len(raw_file):,} o")
    print(f"    donnees decompressees  : {len(original):,} o   (en-tete annonce {h['uncompressedSize']:,})")
    print(f"    prefixe identique      : {'OUI' if ok_prefix else 'NON'}")
    print(f"    recompresse (nous)     : {len(rebuilt):,} o  (compressSize ecrit = {len(rebuilt) - DCX_PREFIX_LEN:,})")
    print(f"    taille compressee FromSoft : {h['compressedSize']:,} o")
    print(f"    ROUND-TRIP IDENTIQUE   : {'OUI' if ok_data else 'NON'}")
    print(f"    sha256 donnees         : {hashlib.sha256(original).hexdigest()[:16]}")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, os.path.basename(path))
    with open(out, "wb") as fh:
        fh.write(rebuilt)
    print(f"    ecrit dans             : {out}")
    return ok_data and ok_prefix


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    results = [test(p) for p in sys.argv[1:]]
    print()
    print(f"RESULTAT : {sum(results)}/{len(results)} fichiers OK")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
