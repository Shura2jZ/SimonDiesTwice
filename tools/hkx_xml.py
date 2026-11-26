"""Conversion HKX (tagfile Havok 2016) <-> XML, via TagTools (Skyth) porte en Python 3.

Usage :
    python tools/hkx_xml.py to-xml   <fichier.hkx> <sortie.xml> [--backport]
    python tools/hkx_xml.py from-xml <entree.xml>  <sortie.hkx>

--backport ecrit les types au format Havok 2012 (ce que fait TagTools pour
recompiler avec AssetCc2). Sans --backport, les types 2016 du fichier sont
conserves tels quels, ce qui permet un aller-retour fidele.
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

import tagtools3 as T


def charger_types():
    chemin = os.path.join(RACINE, "tools", "TypeDatabase.xml")
    return T.TagTypeHelper.loadTypes(chemin)


def trouver_compendium(hkx):
    dossier = os.path.dirname(os.path.abspath(hkx))
    for nom in sorted(os.listdir(dossier)):
        if nom.lower().endswith(".compendium"):
            return os.path.join(dossier, nom)
    return None


def to_xml(hkx, xml, backport=False):
    compendium = trouver_compendium(hkx)
    obj = T.TagReader.fromFile(hkx, compendium)
    bp = T.TagTypeBackporter.backportTypes2012 if backport else None
    T.TagXmlSerializer.toFile(xml, obj, bp)
    print("xml ecrit : {} ({} octets)".format(xml, os.path.getsize(xml)))


def from_xml(xml, hkx, compendium=None):
    if compendium is None:
        compendium = trouver_compendium(hkx)
    if compendium and os.path.isfile(compendium):
        with T.TagReader(open(compendium, "rb")) as r:
            types = list(r.types)
            cid = r.ids[0]
        obj = T.TagXmlParser.fromFile(xml, types)
        with T.TagWriter(open(hkx, "wb")) as w:
            w.writeRootSection(obj, types, cid)
        print("hkx ecrit (compendium {} ) : {} ({} octets)".format(
            cid.hex(), hkx, os.path.getsize(hkx)))
        return
    types = charger_types()
    obj = T.TagXmlParser.fromFile(xml, types)
    T.TagWriter.toFile(hkx, obj)
    print("hkx ecrit (types embarques) : {} ({} octets)".format(hkx, os.path.getsize(hkx)))


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    mode, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "to-xml":
        to_xml(src, dst, "--backport" in sys.argv[4:])
    elif mode == "from-xml":
        from_xml(src, dst)
    else:
        print("mode inconnu : " + mode)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
