#!/usr/bin/env python3
"""Build an offline textured FLVER preview (no game launch required).

Usage:
  python tools/preview_flver.py [flver.chrbnd.dcx] [textures.texbnd.dcx] [output_dir]
Defaults to the current Simon candidate packages under _work/mod/chr.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bnd4_build
import soulsutil

GAME = r"F:\Games\Sekiro - Shadows Die Twice"
DEFAULT_MODEL = os.path.join(ROOT, "_work", "mod", "chr", "c5400.chrbnd.dcx")
DEFAULT_TEXTURES = os.path.join(ROOT, "_work", "mod", "chr", "c5409.texbnd.dcx")
CS = os.path.join(ROOT, "_work", "tools", "cs")


def extract_named(container_path, name, output_path):
    raw = soulsutil.load(container_path)
    entries = bnd4_build.list_entries(raw)[4]
    for entry in entries:
        if bnd4_build.basename_of(entry["fullname"]).lower() == name.lower():
            data = raw[entry["offset"]:entry["offset"] + entry["size"]]
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
            return data
    raise RuntimeError("%s not found in %s" % (name, container_path))


def run(cmd):
    print("+", " ".join('"%s"' % x if " " in x else x for x in cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def main():
    model_package = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MODEL
    texture_package = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TEXTURES
    out = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(ROOT, "_work", "preview")
    if not os.path.isfile(model_package):
        model_package = os.path.join(GAME, "mods", "chr", "c5400.chrbnd.dcx")
    if not os.path.isfile(texture_package):
        texture_package = os.path.join(GAME, "mods", "chr", "c5409.texbnd.dcx")
    os.makedirs(out, exist_ok=True)
    model = os.path.join(out, "c5400.flver")
    tpf = os.path.join(out, "c5409.tpf")
    dds_dir = os.path.join(out, "dds")
    extract_named(model_package, "c5400.flver", model)
    extract_named(texture_package, "c5409.tpf", tpf)
    run([os.path.join(CS, "TpfExtract.exe"), tpf, dds_dir])

    # Mesh index -> texture in the actual c5400 FLVER/c5409 TPF material contract.
    mapping = [
        (0, "c5409_kimono_a"),
        (1, "c5409_hoture_a"),
        (2, "c5409_helfur_a"),
        (3, "c5409_body_a"),
        (4, "c5409_head_a"),
        (5, "c5409_eyeshadow_a"),
    ]
    card = os.path.join(out, "textures.tsv")
    with open(card, "w", encoding="utf-8") as f:
        for slot, tex in mapping:
            path = os.path.join(dds_dir, tex + ".dds")
            if os.path.isfile(path):
                f.write("%d|%s\n" % (slot, path))
            else:
                print("WARNING: missing texture", path)

    renderer = os.path.join(CS, "FlverRenduTex.exe")
    views = [("face", "avant"), ("profil", "droite"), ("dos", "arriere")]
    for label, view in views:
        run([renderer, model, os.path.join(out, "simon_" + label + ".png"), view,
             card, "0,1,2,3,4,5", "1.15", "1200", "1500"])
        run([renderer, model, os.path.join(out, "tete_" + label + ".png"), view,
             card, "4,5", "1.1", "1200", "1500", "4"])
    run([renderer, model, os.path.join(out, "tete_dessus.png"), "dessus",
         card, "4,5", "1.1", "1200", "1200", "4"])
    print("Preview ready:", out)
    print("Whole model: simon_face.png, simon_profil.png, simon_dos.png")
    print("Head close-ups: tete_face.png, tete_profil.png, tete_dos.png, tete_dessus.png")


if __name__ == "__main__":
    main()
