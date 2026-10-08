#!/usr/bin/env python3
"""Versión segura para Reels de un banner 9:16 generado por Higgsfield.

Reduce el bloque del anuncio (titular, producto, precio y botón) para que quede entre el 15 % y el
64 % del alto, y rellena el resto con el mismo fondo, así nada queda tapado por la interfaz de Reels
(14 % superior y 35 % inferior). No genera contenido nuevo; solo reubica la imagen.

Uso: python3 scripts/reels_safe.py entrada_9x16.png salida.png
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def reels_safe(src, dst, y0=0.15, y1=0.64):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    a = np.asarray(im).astype(np.float32)
    bg = np.median(a[: int(H * 0.10)].reshape(-1, 3), axis=0)
    dev = np.abs(a - bg).max(axis=2)
    idx = np.where(np.percentile(dev, 99, axis=1) > 40)[0]
    pad = int(H * 0.04)
    top, bot = max(0, int(idx.min()) - pad), min(H, int(idx.max()) + pad)
    pad_top, pad_bot = int(idx.min()) - top, bot - int(idx.max())
    block = im.crop((0, top, W, bot))
    s = min((H * (y1 - y0)) / block.height, 1.0)
    nb = block.resize((int(W * s), int(block.height * s)), Image.LANCZOS)

    # Fondo: franja superior vacía repetida en espejo, con el color ajustado al del bloque
    strip = im.crop((0, 0, W, max(40, top)))
    canvas = Image.new("RGB", (W, H))
    y, flip = 0, False
    while y < H:
        t = strip.transpose(Image.FLIP_TOP_BOTTOM) if flip else strip
        canvas.paste(t, (0, y))
        y += t.height
        flip = not flip
    nba = np.asarray(nb).astype(np.float32)
    ring = np.concatenate([nba[:12].reshape(-1, 3), nba[-12:].reshape(-1, 3),
                           nba[:, :12].reshape(-1, 3), nba[:, -12:].reshape(-1, 3)])
    ca = np.asarray(canvas).astype(np.float32)
    ca = np.clip(ca + (np.median(ring, axis=0) - np.median(ca.reshape(-1, 3), axis=0)), 0, 255)
    canvas = Image.fromarray(ca.astype(np.uint8))

    # El borde suavizado nunca toca el contenido: cabe dentro del margen vacío del bloque
    side = int(np.argmax(np.percentile(dev[int(idx.min()):int(idx.max())], 99, axis=0) > 40))
    f = max(6, int(min(pad_top, pad_bot, side) * s / 2.5))
    mask = Image.new("L", nb.size, 0)
    mask.paste(Image.new("L", (nb.width - 2 * f, nb.height - 2 * f), 255), (f, f))
    mask = mask.filter(ImageFilter.GaussianBlur(f / 2))
    x = (W - nb.width) // 2
    yb = int(H * y0) + (int(H * (y1 - y0)) - nb.height) // 2
    canvas.paste(nb, (x, yb), mask)
    canvas.save(dst)
    return round(s, 2)


if __name__ == "__main__":
    print(reels_safe(sys.argv[1], sys.argv[2]))
