"""Ecrit une animation produite par tools/retarget.py dans un HKX Sekiro.

    python tools/anim_hkx.py <anim2> <xml_modele> <xml_sortie> <hkx_sortie> [fps]

Le XML modele fournit l'objet hkaSplineCompressedAnimation (199 pistes, binding
identique au squelette c5400) ; on remplace ses donnees et ses entetes de temps.
"""
import array
import json
import os
import struct
import sys
import xml.etree.ElementTree as ET

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import hka_spline as HS
import hkx_xml

IMAGES_PAR_BLOC = 255


def lire_anim2(chemin):
    with open(chemin, "rb") as f:
        entete = json.loads(f.readline().decode("utf-8"))
        brut = array.array("f")
        brut.frombytes(f.read())
    nb = entete["nb_images"]
    p = entete["nb_pistes"]
    if len(brut) != nb * p * 10:
        raise ValueError("taille inattendue : %d floats pour %d x %d x 10" % (len(brut), nb, p))
    images = []
    for f in range(nb):
        base = f * p * 10
        piste = []
        for i in range(p):
            o = base + 10 * i
            piste.append(((brut[o], brut[o + 1], brut[o + 2]),
                          (brut[o + 3], brut[o + 4], brut[o + 5], brut[o + 6]),
                          (brut[o + 7], brut[o + 8], brut[o + 9])))
        images.append(piste)
    return entete, images


def reel_hex(v):
    return "x%08x" % struct.unpack("<I", struct.pack("<f", v))[0]


def main():
    anim2, xml_src, xml_dst, hkx_dst = sys.argv[1:5]
    fps = float(sys.argv[5]) if len(sys.argv) > 5 else 60.0

    entete, images = lire_anim2(anim2)
    nb_images = entete["nb_images"]
    nb_pistes = entete["nb_pistes"]

    tree = ET.parse(xml_src)
    root = tree.getroot()
    obj = [o for o in root.findall("object") if o.get("type") == "hkaSplineCompressedAnimation"][0]
    pistes_xml = int(obj.find("int[@name='numberOfTransformTracks']").text)
    if pistes_xml != nb_pistes:
        raise ValueError("le modele a %d pistes, l'animation %d" % (pistes_xml, nb_pistes))

    # --- decoupage en blocs
    offsets = []
    float_offsets = []
    donnees = bytearray()
    debut = 0
    while debut < nb_images:
        fin = min(debut + IMAGES_PAR_BLOC + 1, nb_images)
        offsets.append(len(donnees))
        bloc = HS.encoder_bloc(images[debut:fin], nb_pistes)
        donnees += bloc
        # Avec zero piste flottante, Havok veut neanmoins l'offset local du
        # curseur float a la fin des transform tracks de chaque bloc. Il faut
        # garder la longueur non alignee moins le trailer de 4 octets : le
        # padding 16-byte appartient au bloc suivant, pas a la zone spline utile.
        float_offsets.append(max(0, len(bloc) - 4))
        while len(donnees) % 16:
            donnees.append(0)
        if fin >= nb_images:
            break
        debut = fin - 1
    print("blocs : %s ; donnees %d octets" % (offsets, len(donnees)))

    # --- entetes
    duree = (nb_images - 1) / fps
    bloc_duree = IMAGES_PAR_BLOC / fps
    for e in obj:
        nom = e.get("name")
        if nom == "numFrames":
            e.text = str(nb_images)
        elif nom == "numBlocks":
            e.text = str(len(offsets))
        elif nom == "maskAndQuantizationSize":
            e.text = str(4 * nb_pistes)
        elif nom == "blockDuration":
            e.text = reel_hex(bloc_duree)
        elif nom == "blockInverseDuration":
            e.text = reel_hex(1.0 / bloc_duree)
        elif nom == "frameDuration":
            e.text = reel_hex(1.0 / fps)
        elif nom == "blockOffsets":
            e.set("size", str(len(offsets)))
            e.text = " ".join(str(x) for x in offsets)
        elif nom == "floatBlockOffsets":
            # Le template Sekiro a zero piste flottante, mais les offsets de
            # debut de la zone float doivent quand meme designer le curseur local
            # apres les transform tracks (longueurs non alignees calculees ci-dessus).
            e.set("size", str(len(float_offsets)))
            e.text = " ".join(str(x) for x in float_offsets)
        elif nom == "data":
            e.set("size", str(len(donnees)))
            e.text = " ".join(str(x) for x in donnees)
        elif nom == "duration":
            e.text = reel_hex(duree)
    print("duree %.4f s, %d images, %d blocs" % (duree, nb_images, len(offsets)))

    tree.write(xml_dst, encoding="unicode")

    # --- cadre de reference (root motion d'origine) : on le met a zero
    tree = ET.parse(xml_dst)
    root = tree.getroot()
    for o in root.findall("object"):
        if o.get("type") == "hkaDefaultAnimatedReferenceFrame":
            for e in o:
                if e.get("name") == "duration":
                    e.text = reel_hex(0.0)
                elif e.get("name") == "referenceFrameSamples":
                    e.set("size", "1")
                    e.text = "x00000000 x00000000 x00000000 x00000000"
    tree.write(xml_dst, encoding="unicode")

    hkx_xml.from_xml(xml_dst, hkx_dst)
    print("hkx ecrit :", hkx_dst, os.path.getsize(hkx_dst), "octets")


if __name__ == "__main__":
    main()
