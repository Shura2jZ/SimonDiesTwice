"""Extrait une plage d'images d'une animation .anim2.

    python tools/anim2_extrait.py <entree.anim2> <sortie.anim2> <debut> <fin>
"""
import array
import json
import sys


def main():
    src, dst, debut, fin = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    with open(src, "rb") as f:
        entete = json.loads(f.readline().decode("utf-8"))
        brut = array.array("f")
        brut.frombytes(f.read())
    nb = entete["nb_images"]
    p = entete["nb_pistes"]
    if not (0 <= debut <= fin < nb):
        raise ValueError("plage %d..%d hors de 0..%d" % (debut, fin, nb - 1))
    entete["nb_images"] = fin - debut + 1
    with open(dst, "wb") as f:
        f.write(json.dumps(entete).encode("utf-8") + b"\n")
        f.write(brut[debut * p * 10:(fin + 1) * p * 10].tobytes())
    print("extrait : %s images %d..%d -> %s (%d images)"
          % (src, debut, fin, dst, entete["nb_images"]))


if __name__ == "__main__":
    main()
