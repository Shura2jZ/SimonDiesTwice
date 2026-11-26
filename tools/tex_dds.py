"""
Fabrique un DDS BC1 (DXT1) avec chaine de mips complete, a partir d'une image
Pillow. Deux variantes : sRGB (albedo) et lineaire (normales, masques).

Pillow sait encoder le DXT1 mais ecrit un DDS sans extension DX10 ; on lui
emprunte uniquement le flux de blocs et on ecrit nous-memes l'en-tete DDS
complet (DX10 + format DXGI explicite), pour que le jeu cree la texture dans le
bon espace colorimetrique.

Usage (module) :
    from tex_dds import dds_bc1
    octets = dds_bc1(image_rgb, srgb=True)
"""
import io
import struct

from PIL import Image

DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000
DDPF_FOURCC = 0x4
DDSCAPS_TEXTURE = 0x1000
DDSCAPS_COMPLEX = 0x8
DDSCAPS_MIPMAP = 0x400000

DXGI_BC1_UNORM = 71
DXGI_BC1_UNORM_SRGB = 72

DDS_MAGIC = b"DDS "
DDS_HEADER_SIZE = 124
DX10_HEADER_SIZE = 20


def _blocs(image: Image.Image) -> bytes:
    """Encode une image (deja au bon format) en blocs BC1 via Pillow."""
    w, h = image.size
    # Pillow exige des dimensions multiples de 4 pour le DXT1 : on complete.
    pw, ph = max(4, (w + 3) // 4 * 4), max(4, (h + 3) // 4 * 4)
    if (pw, ph) != (w, h):
        fond = Image.new("RGB", (pw, ph), (0, 0, 0))
        fond.paste(image.convert("RGB"), (0, 0))
        image = fond
    tampon = io.BytesIO()
    image.convert("RGB").save(tampon, format="DDS", pixel_format="DXT1")
    donnees = tampon.getvalue()
    # Pillow ecrit un en-tete DDS de 128 octets sans DX10.
    return donnees[128:]


def dds_bc1(image: Image.Image, srgb: bool) -> bytes:
    """Construit un DDS BC1 complet (en-tete DX10 + mips)."""
    image = image.convert("RGB")
    niveaux = [image]
    largeur, hauteur = image.size
    while largeur > 4 or hauteur > 4:
        largeur = max(1, largeur // 2)
        hauteur = max(1, hauteur // 2)
        niveaux.append(image.resize((largeur, hauteur), Image.LANCZOS))

    blocs = [_blocs(niveau) for niveau in niveaux]
    taille_mip0 = len(blocs[0])

    dxgi = DXGI_BC1_UNORM_SRGB if srgb else DXGI_BC1_UNORM

    entete = struct.pack(
        "<4s18I",
        DDS_MAGIC,
        DDS_HEADER_SIZE,
        DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
        | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE,
        image.size[1], image.size[0], taille_mip0, 0, len(niveaux),
        *([0] * 11),
    )
    pixel_format = struct.pack("<I I 4s 5I", 32, DDPF_FOURCC, b"DX10", 0, 0, 0, 0, 0)
    caps = struct.pack(
        "<I I I I I",
        DDSCAPS_TEXTURE | DDSCAPS_COMPLEX | DDSCAPS_MIPMAP,
        0, 0, 0, 0,
    )
    dx10 = struct.pack("<I I I I I", dxgi, 3, 0, 1, 0)
    return entete + pixel_format + caps + dx10 + b"".join(blocs)


def lire_entete_dds(donnees: bytes) -> dict:
    """Relit ce que le jeu lira : dimensions, mips, format DXGI."""
    if donnees[:4] != DDS_MAGIC:
        raise ValueError("pas un DDS")
    hauteur, largeur = struct.unpack_from("<II", donnees, 12)
    mips = struct.unpack_from("<I", donnees, 28)[0]
    fourcc = donnees[84:88]
    dxgi = struct.unpack_from("<I", donnees, 128)[0] if fourcc == b"DX10" else None
    return {"largeur": largeur, "hauteur": hauteur, "mips": mips, "dxgi": dxgi}
