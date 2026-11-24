# -*- coding: utf-8 -*-
"""
Encodeur DDS BC1 (DXT1) AVEC alpha binaire, comme les textures de masques du
jeu Sekiro (le bit "transparent" du mode 3 couleurs de DXT1).

Pillow sait encoder du DXT1 mais perd l'alpha : le mode 4 couleurs est alors
toujours utilise. Ici on encode nous-memes :

  - bloc entierement opaque  -> mode 4 couleurs (c0 > c1), comme d'habitude
  - bloc avec des pixels transparents -> mode 3 couleurs : c0 et c1 sont les
    deux extremes opaques, l'index 3 vaut "transparent" (le moteur fait le
    cutout dessus).

Usage :
    from tex_dds_alpha import dds_bc1_alpha
    octets = dds_bc1_alpha(image_rgba, srgb=True)
"""
import struct

import numpy as np
from PIL import Image

DXGI_BC1_UNORM = 71
DXGI_BC1_UNORM_SRGB = 72

DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PIXELFORMAT = 0x100
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000
DDPF_FOURCC = 0x4
DDSCAPS_TEXTURE = 0x1000
DDSCAPS_COMPLEX = 0x8
DDSCAPS_MIPMAP = 0x400000


def _vers_565(rgb):
    """rgb (N,3) float 0..255 -> entiers 565."""
    r = np.clip(rgb[:, 0], 0, 255).astype(np.int32)
    g = np.clip(rgb[:, 1], 0, 255).astype(np.int32)
    b = np.clip(rgb[:, 2], 0, 255).astype(np.int32)
    r5 = (r * 31 + 127) // 255
    g6 = (g * 63 + 127) // 255
    b5 = (b * 31 + 127) // 255
    return (r5 << 11) | (g6 << 5) | b5


def _vers_888(c565):
    r = ((c565 >> 11) & 0x1F) * 255 // 31
    g = ((c565 >> 5) & 0x3F) * 255 // 63
    b = (c565 & 0x1F) * 255 // 31
    return np.stack([r, g, b], axis=-1)


def _encode_bloc(rgb, alpha):
    """rgb (4,4,3) uint8, alpha (4,4) uint8 -> 8 octets de bloc BC1."""
    opaques = alpha >= 128
    if opaques.all():
        c0v = _vers_565(rgb.reshape(-1, 3).astype(np.float64))
        # c0 = le plus clair, c1 = le plus sombre (il faut c0 > c1)
        lum = c0v.astype(np.int64) * 3
        i_max = int(np.argmax(lum))
        i_min = int(np.argmin(lum))
        c0 = int(c0v[i_max])
        c1 = int(c0v[i_min])
        if c0 == c1:
            c0 = min(0xFFFF, c0 + 1)
        if c0 < c1:
            c0, c1 = c1, c0
        p = _vers_888(np.array([[c0, c1]], dtype=np.int64))[0]
        pal = np.array([p[0], p[1],
                        (2 * p[0].astype(int) + p[1]) // 3,
                        (p[0] + 2 * p[1]) // 3], dtype=np.float64)
        dist = ((rgb.reshape(-1, 1, 3).astype(np.float64) - pal[None, :, :]) ** 2).sum(2)
        idx = dist.argmin(1).reshape(4, 4)
        return _assemble(c0, c1, idx, False)

    # mode 3 couleurs : on ne considere que les pixels opaques
    if not opaques.any():
        # bloc entierement transparent
        return _assemble(0, 0, np.full((4, 4), 3, dtype=np.int64), True)
    c0v = _vers_565(rgb[opaques].astype(np.float64))
    lum = c0v.astype(np.int64) * 3
    c0 = int(c0v[int(np.argmax(lum))])
    c1 = int(c0v[int(np.argmin(lum))])
    # BC1 ne reserve l'index 3 a la transparence que si c0 <= c1.
    # Les blocs opaques ci-dessus utilisent au contraire c0 > c1.
    if c0 == c1:
        if c1 < 0xFFFF:
            c1 += 1
        else:
            c0 -= 1
    if c0 > c1:
        c0, c1 = c1, c0
    p = _vers_888(np.array([[c0, c1]], dtype=np.int64))[0]
    pal = np.array([p[0], p[1], (p[0] + p[1]) // 2, [0, 0, 0]], dtype=np.float64)
    d = ((rgb.reshape(-1, 1, 3).astype(np.float64) - pal[None, :3, :]) ** 2).sum(2)
    idx = d.argmin(1).reshape(4, 4)
    idx[~opaques] = 3
    return _assemble(c0, c1, idx, True)


def _assemble(c0, c1, idx, trois_couleurs):
    """idx (4,4) en 0..3 -> 4 octets BC1 (2 bits par texel, ligne par ligne,
    pixel x=0 dans les bits de poids faible)."""
    out = bytearray(4)
    for y in range(4):
        octet = 0
        for x in range(4):
            octet |= (int(idx[y, x]) & 3) << (2 * x)
        out[y] = octet
    return struct.pack("<HH", c0 & 0xFFFF, c1 & 0xFFFF) + bytes(out)


def _encode_niveau(rgba):
    """rgba (h,w,4) uint8 -> octets BC1 (avec padding si necessaire)."""
    h, w = rgba.shape[:2]
    pw = max(4, (w + 3) // 4 * 4)
    ph = max(4, (h + 3) // 4 * 4)
    if (pw, ph) != (w, h):
        pad = np.zeros((ph, pw, 4), dtype=np.uint8)
        pad[:h, :w] = rgba
        rgba = pad
    bw, bh = pw // 4, ph // 4
    out = bytearray()
    for by in range(bh):
        for bx in range(bw):
            bloc = rgba[by * 4:by * 4 + 4, bx * 4:bx * 4 + 4]
            out += _encode_bloc(bloc[..., :3], bloc[..., 3])
    return bytes(out)


def dds_bc1_alpha(image, srgb=True):
    """image Pillow RGBA -> DDS BC1 complet (en-tete DX10 + mips)."""
    img = image.convert("RGBA")
    arr = np.asarray(img)
    niveaux = [arr]
    w, h = img.size
    while w > 4 or h > 4:
        w = max(1, w // 2)
        h = max(1, h // 2)
        img = img.resize((w, h), Image.LANCZOS)
        niveaux.append(np.asarray(img))

    blocs = [_encode_niveau(n) for n in niveaux]
    taille_mip0 = len(blocs[0])
    dxgi = DXGI_BC1_UNORM_SRGB if srgb else DXGI_BC1_UNORM

    entete = struct.pack(
        "<4s18I",
        b"DDS ",
        124,
        DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE,
        image.size[1], image.size[0], taille_mip0, 0, len(niveaux),
        *([0] * 11),
    )
    pixel_format = struct.pack("<I I 4s 5I", 32, DDPF_FOURCC, b"DX10", 0, 0, 0, 0, 0)
    caps = struct.pack("<I I I I I", DDSCAPS_TEXTURE | DDSCAPS_COMPLEX | DDSCAPS_MIPMAP, 0, 0, 0, 0)
    dx10 = struct.pack("<I I I I I", dxgi, 3, 0, 1, 0)
    return entete + pixel_format + caps + dx10 + b"".join(blocs)
