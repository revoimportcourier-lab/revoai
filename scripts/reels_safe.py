#!/usr/bin/env python3
"""Versión segura para Reels de un banner 9:16 generado por Higgsfield.

Aleja la imagen completa (como un zoom out) hasta que el bloque del anuncio (titular, producto,
precio y botón) quede entre el 15 % y el 64 % del alto, y extiende el fondo desde los bordes de la
propia imagen. Así nada queda tapado por la interfaz de Reels (14 % superior y 35 % inferior) y el
fondo sigue continuo aunque tenga degradado o viñeta. No genera contenido nuevo; solo reubica la imagen.

Uso: python3 scripts/reels_safe.py entrada_9x16.png salida.png
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def _blur(arr, r):
    return np.asarray(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)


def reels_safe(src, dst, y0=0.15, y1=0.64):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    a = np.asarray(im).astype(np.float32)

    # Fondo por fila tomado de los bordes laterales: tolera degradados verticales y viñetas
    e = max(4, int(W * 0.02))
    rowbg = np.median(np.concatenate([a[:, :e], a[:, -e:]], axis=1), axis=1)
    rowbg = _blur(rowbg[:, None, :].repeat(3, axis=1), 6)[:, 1]
    dev = np.abs(a - rowbg[:, None, :]).max(axis=2)
    idx = np.where(np.percentile(dev, 99, axis=1) > 40)[0]
    cols = np.where(np.percentile(dev[idx.min():idx.max() + 1], 99, axis=0) > 40)[0]
    pad = int(H * 0.03)
    top, bot = max(0, int(idx.min()) - pad), min(H, int(idx.max()) + pad)
    s = min(H * (y1 - y0) / (bot - top), 1.0)

    sw, sh = round(W * s), round(H * s)
    small = np.asarray(im.resize((sw, sh), Image.LANCZOS)).astype(np.float32)
    ox = (W - sw) // 2
    oy = int(H * y0) + (int(H * (y1 - y0)) - round((bot - top) * s)) // 2 - round(top * s)
    ct, cb = max(0, -oy), max(0, oy + sh - H)
    small = small[ct:sh - cb]
    oy = max(oy, 0)
    h = small.shape[0]

    # Fuera de la imagen reducida: sus propios bordes estirados, suavizados y con grano parecido
    canvas = np.pad(small, ((oy, H - oy - h), (ox, W - ox - sw), (0, 0)), mode="edge")
    canvas = _blur(canvas, max(8, W * 0.02))
    patch = a[: max(40, int(H * 0.06))]
    grain = float((patch.mean(axis=2) - _blur(patch, 3).mean(axis=2)).std())
    rng = np.random.default_rng(0)
    canvas += rng.normal(0, grain, (H, W))[..., None]

    # Fundido desde el borde de la imagen reducida, sin tocar el contenido
    side = (int(cols.min()) if len(cols) else W // 10) * s
    f = max(6, int(min(W * 0.06, side * 0.8)))
    yy, xx = np.mgrid[0:h, 0:sw]
    d = np.minimum.reduce([xx, sw - 1 - xx,
                           yy + (f if ct else 0), h - 1 - yy + (f if cb else 0)]).astype(np.float32)
    alpha = np.clip(d / f, 0, 1)[..., None]
    region = canvas[oy:oy + h, ox:ox + sw]
    canvas[oy:oy + h, ox:ox + sw] = small * alpha + region * (1 - alpha)
    Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).save(dst)
    return round(s, 2)


if __name__ == "__main__":
    print(reels_safe(sys.argv[1], sys.argv[2]))
