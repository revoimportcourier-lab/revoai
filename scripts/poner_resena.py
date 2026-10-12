#!/usr/bin/env python3
"""Escribe una reseña real de un cliente en la tarjeta en blanco de un banner T4 (Feed o Stories).

La tarjeta se ubica por sus 5 estrellas naranjas. Se conservan el marco, las estrellas y "5/5"; se borra
el avatar y las líneas grises y se escribe:
    “Texto de la reseña, tal cual lo escribió el cliente.”
    (inicial)  Nombre · Ciudad
Si la calificación es menor a 5, las últimas estrellas pasan a gris y "5/5" cambia a "n/5".
Con --estrellas 0 (el cliente no dio nota) se quitan las estrellas y el puntaje.

Uso (una imagen):
    python3 scripts/poner_resena.py entrada.png salida.png --texto "..." --nombre "Carla M." \
        --ciudad "Arequipa" [--estrellas 5]
Uso (lote): python3 scripts/poner_resena.py --csv resenas/resenas.csv --carpeta <carpeta con los PNG>
    El CSV usa las columnas de resenas/resenas.csv; solo procesa filas con permiso = sí. Escribe
    master_resena.png, v916_resena.png y reels_916_resena.png en <carpeta>/<producto_id>__T4/.

No inventa nada: el texto va tal cual. Solo se permite recortar con "…" (lo hace la persona, no el script).
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = Path("/usr/share/fonts/opentype/inter")
F_TEXT = FONTS / "Inter-Medium.otf"
F_NAME = FONTS / "Inter-SemiBold.otf"
F_META = FONTS / "Inter-Regular.otf"


def _runs(mask):
    """Tramos consecutivos de True: [(inicio, fin_inclusivo)]."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def find_card(a):
    """Devuelve dict con stars (x0,y0,x1,y1), score (x0,y0,x1,y1) y zone (x0,y0,x1,y1) a reescribir."""
    H, W, _ = a.shape
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    orange = (r > 215) & (g > 120) & (g < 205) & (b < 110)
    rows = _runs(orange.sum(axis=1) > 6)
    best = None
    for y0, y1 in rows:
        if not (0.009 * H < y1 - y0 < 0.05 * H):
            continue
        cols = _runs(orange[y0:y1 + 1].any(axis=0))
        stars = [c for c in cols if c[1] - c[0] > (y1 - y0) * 0.5]
        if len(stars) >= 5:
            # 5 estrellas seguidas con espaciado parecido
            for i in range(len(stars) - 4):
                grp = stars[i:i + 5]
                gaps = [grp[k + 1][0] - grp[k][1] for k in range(4)]
                if max(gaps) - min(gaps) <= max(4, 0.6 * (y1 - y0)) and max(gaps) < 1.2 * (y1 - y0):
                    best = (grp[0][0], y0, grp[4][1], y1, [(s[0], s[1]) for s in grp])
    if best is None:
        raise ValueError("no encontré las 5 estrellas de la tarjeta de reseña")
    sx0, sy0, sx1, sy1, star_cols = best
    sh = sy1 - sy0
    L = a.mean(axis=2)
    bg = float(np.median(L[sy1 + sh: sy1 + 2 * sh, sx0: sx0 + 6 * sh]))
    dark = L < bg - 70

    # "5/5" a la derecha de las estrellas
    seg = dark[sy0 - 2: sy1 + 3, sx1 + 2: min(W, sx1 + 6 * sh)] | (L[sy0 - 2: sy1 + 3, sx1 + 2: min(W, sx1 + 6 * sh)] < bg - 25)
    sc = np.where(seg.any(axis=0))[0]
    score = None
    if len(sc):
        runs = _runs(seg.any(axis=0))
        first = [runs[0]]
        for rr in runs[1:]:
            if rr[0] - first[-1][1] > sh * 0.8:
                break
            first.append(rr)
        sr = np.where(seg[:, first[0][0]: first[-1][1] + 1].any(axis=1))[0]
        score = (sx1 + 2 + first[0][0], sy0 - 2 + sr.min(), sx1 + 2 + first[-1][1], sy0 - 2 + sr.max())

    # marco: borde inferior (línea oscura larga bajo las estrellas)
    y_b = None
    for y in range(sy1 + sh, min(H, sy1 + 14 * sh)):
        if dark[y, sx0: sx0 + 8 * sh].mean() > 0.85:
            y_b = y
            break
    # bordes laterales (si no hay, se usan márgenes desde las estrellas)
    mid = (sy1 + (y_b or sy1 + 4 * sh)) // 2
    x_l = None
    for x in range(sx0 - 1, max(0, sx0 - 6 * sh), -1):
        if dark[sy1: mid, x].mean() > 0.85:
            x_l = x
            break
    x_r = None
    for x in range(sx1 + 6 * sh, W):
        if dark[sy1: mid, x].mean() > 0.85:
            x_r = x
            break
    if y_b is None:
        raise ValueError("no encontré el borde inferior de la tarjeta")
    if x_l is None:
        x_l = max(0, sx0 - sh)
    if x_r is None:
        x_r = W - x_l
    pad = max(4, sh // 3)
    zone = (x_l + pad, sy1 + max(3, sh // 4), x_r - pad, y_b - pad)
    return {"stars": (sx0, sy0, sx1, sy1), "star_cols": star_cols, "score": score, "zone": zone,
            "bg": bg, "star_h": sh, "frame": (x_l, y_b, x_r)}


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def place(src, dst, texto, nombre, ciudad, estrellas=0):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    c = find_card(a)
    x0, y0, x1, y1 = c["zone"]
    sh = c["star_h"]
    estrellas = int(estrellas)
    if estrellas == 0:  # el cliente no dio nota: sin estrellas ni puntaje, el texto sube
        y0 = c["stars"][1] - max(3, sh // 4)
        if c["score"]:
            x1 = max(x1, c["score"][2] + 4)
    out = a.copy()
    # fondo de la tarjeta: color de cada fila tomado del borde derecho de la zona (sin texto)
    ref = np.median(a[y0:y1, x1 - max(6, sh // 2): x1], axis=1)
    out[y0:y1, x0:x1] = ref[:, None, :]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    # estrellas y puntaje
    if 0 < estrellas < 5:
        arr = np.asarray(img).astype(np.float32)
        sx0, sy0, sx1, sy1 = c["stars"]
        for cx0, cx1 in c["star_cols"][estrellas:]:
            blk = arr[sy0: sy1 + 1, cx0: cx1 + 1]
            orange = (blk[..., 0] > 200) & (blk[..., 2] < 140)
            blk[orange] = [205, 208, 214]
        img = Image.fromarray(arr.astype(np.uint8))
        d = ImageDraw.Draw(img)
    if c["score"] and 0 < estrellas < 5:
        qx0, qy0, qx1, qy1 = c["score"]
        sc_col = tuple(int(v) for v in np.asarray(im)[qy0: qy1 + 1, qx0: qx1 + 1].reshape(-1, 3).min(axis=0))
        d.rectangle((qx0 - 2, qy0 - 2, qx1 + 2, qy1 + 2), fill=tuple(int(v) for v in ref[0]))
        fs = ImageFont.truetype(str(F_META), max(10, int((qy1 - qy0) * 1.35)))
        d.text((qx0, qy0 - int((qy1 - qy0) * 0.25)), f"{estrellas}/5", font=fs, fill=sc_col)

    # texto: el tamaño más grande que entre en 3 líneas dejando espacio para el nombre
    W_ = x1 - x0 - sh // 2
    H_ = y1 - y0
    quoted = f"“{texto.strip()}”"
    for size in range(int(sh * 1.05), 9, -1):
        ft = ImageFont.truetype(str(F_TEXT), size)
        lines = wrap(d, quoted, ft, W_)
        lh = int(size * 1.28)
        fn = ImageFont.truetype(str(F_NAME), max(9, int(size * 0.9)))
        name_h = int(size * 1.6)
        if len(lines) <= 3 and lh * len(lines) + name_h + size * 0.3 <= H_:
            break
    else:
        raise ValueError("la reseña es muy larga para esta tarjeta; recórtala con …")
    text_col = (31, 41, 55)
    y = y0 + max(0, (H_ - (lh * len(lines) + name_h + int(size * 0.3))) // 2)
    for line in lines:
        d.text((x0 + sh // 4, y), line, font=ft, fill=text_col)
        y += lh
    y += int(size * 0.3)
    # autor: círculo con inicial + nombre · ciudad
    r = int(name_h * 0.42)
    cx, cy = x0 + sh // 4 + r, y + name_h // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(191, 219, 254))
    fi = ImageFont.truetype(str(F_NAME), int(r * 1.15))
    ini = nombre.strip()[:1].upper()
    d.text((cx, cy), ini, font=fi, fill=(30, 64, 175), anchor="mm")
    fm = ImageFont.truetype(str(F_META), max(9, int(size * 0.9)))
    nx = cx + r + int(size * 0.5)
    d.text((nx, cy), nombre.strip(), font=fn, fill=text_col, anchor="lm")
    if ciudad.strip():
        nx += d.textlength(nombre.strip(), font=fn)
        d.text((nx, cy), f" · {ciudad.strip()}", font=fm, fill=(107, 114, 128), anchor="lm")
    img.save(dst)
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", nargs="?")
    ap.add_argument("salida", nargs="?")
    ap.add_argument("--texto")
    ap.add_argument("--nombre")
    ap.add_argument("--ciudad", default="")
    ap.add_argument("--estrellas", type=int, default=0, help="1 a 5, o 0 si el cliente no dio nota")
    ap.add_argument("--csv")
    ap.add_argument("--carpeta")
    a = ap.parse_args()
    if a.csv:
        base = Path(a.carpeta)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from reels_safe import reels_safe
        for row in csv.DictReader(open(a.csv, encoding="utf-8-sig")):
            if row.get("permiso", "").strip().lower() not in ("sí", "si"):
                continue
            bid = f"{row['producto_id'].strip()}__T4"
            stars = row.get("estrellas", "").strip()
            for name in ("master.png", "v916.png"):
                src = base / bid / name
                if not src.exists():
                    continue
                dst = base / bid / name.replace(".png", "_resena.png")
                try:
                    place(src, dst, row["texto"], row["nombre"], row.get("ciudad", ""), int(stars) if stars else 0)
                except ValueError as e:
                    print("saltado", src, e)
                    continue
                print("ok", dst)
                if name == "v916.png":
                    reels_safe(dst, base / bid / "reels_916_resena.png")
        return
    if not (a.entrada and a.salida and a.texto and a.nombre):
        sys.exit("faltan argumentos: entrada salida --texto --nombre")
    place(a.entrada, a.salida, a.texto, a.nombre, a.ciudad, a.estrellas)


if __name__ == "__main__":
    main()
