"""Fige une image d'une animation .anim2 sur toute sa duree (test de pose).

    python tools/anim2_fige.py <anim2 entree> <anim2 sortie> <image>
"""
import array
import json
import sys


def main():
    src, dst, image = sys.argv[1], sys.argv[2], int(sys.argv[3])
    with open(src, "rb") as f:
        entete = json.loads(f.readline().decode("utf-8"))
        brut = array.array("f")
        brut.frombytes(f.read())
    nb = entete["nb_images"]
    p = entete["nb_pistes"]
    if not 0 <= image < nb:
        raise ValueError("image %d hors de 0..%d" % (image, nb - 1))
    base = image * p * 10
    une = brut[base:base + p * 10]
    with open(dst, "wb") as f:
        f.write(json.dumps(entete).encode("utf-8") + b"\n")
        tampon = array.array("f")
        for _ in range(nb):
            tampon.extend(une)
        tampon.tofile(f)
    print("fige : %s image %d sur %d images -> %s" % (src, image, nb, dst))


if __name__ == "__main__":
    main()
