"""
M1 - Inventaire des fichiers de personnages Sekiro extraits par UXM.

But : savoir immediatement quels personnages sont presents et sous quels formats,
sans rien supposer sur l'arborescence.

Usage:
    python tools/inventory_chr.py "F:\\Games\\Sekiro - Shadows Die Twice"
    python tools/inventory_chr.py <racine> --dir chr
"""
import os
import sys
import re
from collections import defaultdict

DEFAULT_DIRS = ["chr", "parts", "param", "script", "action", "event"]

INTERESTING = {
    ".chrbnd.dcx": "archive personnage (mesh+textures)",
    ".anibnd.dcx": "archive animations + squelette",
    ".behbnd.dcx": "behavior (IA / etats)",
    ".partsbnd.dcx": "archive de piece (mesh)",
    ".param.dcx": "parametres",
    ".emevd.dcx": "evenements",
    ".esd": "scripts de dialogue/etats",
    ".hkx": "Havok (squelette/anim/behavior)",
    ".flver": "modele",
    ".tpf": "textures",
}


def classify(name: str) -> str:
    low = name.lower()
    for ext, label in INTERESTING.items():
        if low.endswith(ext):
            return label
    return ""


def inventory(root: str, dirs=None) -> None:
    if not os.path.isdir(root):
        print(f"Introuvable : {root}")
        return
    dirs = dirs or DEFAULT_DIRS

    print(f"### Racine : {root}")
    entries = sorted(os.listdir(root))
    print(f"Contenu de la racine ({len(entries)} entrees) :")
    for e in entries:
        print(f"   {e}")

    for d in dirs:
        path = os.path.join(root, d)
        if not os.path.isdir(path):
            print(f"\n## [{d}] ABSENT")
            continue

        files = []
        for dirpath, _, filenames in os.walk(path):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    files.append((fn, os.path.getsize(fp), fp))
                except OSError:
                    pass

        total = sum(s for _, s, _ in files)
        print(f"\n## [{d}] {len(files)} fichiers, {total/1024/1024:.1f} Mo")

        # regroupement par identifiant de personnage (ex: c0000, c1250, ...)
        groups = defaultdict(list)
        for fn, size, fp in files:
            m = re.match(r"^(c\d{4})", fn)
            key = m.group(1) if m else "(autres)"
            groups[key].append((fn, size))

        for key in sorted(groups):
            items = groups[key]
            print(f"\n   -- {key} : {len(items)} fichiers")
            for fn, size in sorted(items)[:40]:
                label = classify(fn)
                mark = "  <== " + label if label else ""
                print(f"        {fn:<48} {size:>12,}{mark}")
            if len(items) > 40:
                print(f"        ... et {len(items)-40} autres")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    dirs = None
    if "--dir" in sys.argv:
        dirs = [sys.argv[sys.argv.index("--dir") + 1]]
    inventory(args[0], dirs)


if __name__ == "__main__":
    main()
