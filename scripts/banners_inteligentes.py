#!/usr/bin/env python3
"""Banners inteligentes REVO: escenario de Higgsfield + foto real de revoimport.com + texto por código.

La IA solo hace el fondo (escenario vacío); el producto real de la web se pega por código y
TODO el texto (nombre, precio, sellos, "Calidad Premium", reseñas) lo escribe este script. Así no hay
errores de tildes, "s/" en minúscula, líneas perdidas ni logos colados, y cambiar un precio cuesta 0.

Uso: python3 scripts/banners_inteligentes.py <carpeta_insumos> <carpeta_salida>
  <carpeta_insumos> debe tener: escenas.json, las escenas (PNG) y las fotos recortadas que nombra DATA.
Salida: <id>__<plantilla>_<look>_{4x5,9x16,1x1}.jpg y qa.txt (errores de texto, zona segura y tamaños).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

F = Path("/usr/share/fonts/opentype/inter")
SIZES = {"4x5": (1080, 1350), "9x16": (1080, 1920), "1x1": (1080, 1080)}
# Reels/Stories: todo lo importante entre el 14 % y el 65 % del alto; márgenes laterales de 6 %.
SAFE = {"4x5": (64, 56, 1016, 1300), "1x1": (64, 48, 1016, 1036), "9x16": (64, 269, 1016, 1248)}
PREMIUM_OK = {"case-iphone", "mica-iphone", "combo-pro-3-a1", "combo-pro-3-4en1", "combo-pro-3-2x1"}
PROHIBIDAS = [r"airpods", r"\boriginal(es)?\b(?! de 20)", r"garant[ií]a apple", r"stock inmediato",
              r"entrega inmediata", r"distribuidor autorizado", r"\banc\b", r"cancelaci[oó]n de ruido"]
MIN_PT = 26


def font(name, size):
    return ImageFont.truetype(str(F / name), int(size))


# ---------------------------------------------------------------- datos (en producción: fila del Sheet)
DATA = {
    "iphone-17-pro-max": dict(
        titulo="iPhone 17 Pro Max", sub="Nuevo y sellado", precio="Desde S/ 4,600",
        sellos=["Video de tu equipo antes de pagar", "1 año de garantía REVO", "Contraentrega en Lima"],
        sellos_cortos=["Video antes de pagar", "Garantía REVO 1 año", "Contraentrega Lima"],
        nota="Garantía de REVO por fallas de fábrica.", foto="iphone17pm_sin_logo.png", alto=0.86),
    "combo-pro-3-a1": dict(
        titulo="COMBO PRO 3", sub="Audífonos Pro 3 Calidad Premium", precio="S/ 119", antes="S/ 144",
        sellos=["Envío gratis a todo el Perú", "Case de regalo en 6 colores", "Pagas al llegar a tu casa"],
        sellos_cortos=["Envío gratis", "Case de regalo", "Pagas al recibir"],
        nota=None, foto="pro3_caja.png", alto=0.62),
    "case-iphone": dict(
        titulo="Case transparente", sub="Protege sin tapar el color", precio="S/ 15",
        sellos=["Para todos los modelos", "Confirma tu modelo por WhatsApp"],
        sellos_cortos=["Todos los modelos", "Pídelo por WhatsApp"],
        nota=None, foto="case.png", alto=0.92),
}


# ---------------------------------------------------------------- escena y producto
def load_scene(ins, name, fmt, cfg):
    """Escala la escena 9:16 para cubrir el formato y la recorta dejando la tapa del pedestal abajo."""
    sc = Image.open(ins / f"{name}.png").convert("RGB")
    W, H = SIZES[fmt]
    zoom = 1.18 if fmt == "9x16" else 1.0  # en 9:16 se acerca para que el producto no quede chico
    k = max(W / sc.width, H / sc.height) * zoom
    sc = sc.resize((round(sc.width * k), round(sc.height * k)), Image.LANCZOS)
    top = cfg["top"] * sc.height                                  # centro de la tapa del pedestal
    want = {"4x5": 0.80, "1x1": 0.83, "9x16": min(cfg["top"] + 0.08, 0.62)}[fmt] * H
    x0 = (sc.width - W) // 2
    y0 = int(np.clip(top - want, 0, sc.height - H))
    return sc.crop((x0, y0, x0 + W, y0 + H)).convert("RGBA"), top - y0, cfg["w"] * sc.width


def place(canvas, obj, cx, base_y, max_h, max_w, dark):
    """Pega el recorte real con sombra de contacto y sombra suave proyectada."""
    k = min(max_h / obj.height, max_w / obj.width)
    o = obj.resize((max(1, int(obj.width * k)), max(1, int(obj.height * k))), Image.LANCZOS)
    x, y = int(cx - o.width / 2), int(base_y - o.height)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ew = o.width * 0.86
    ImageDraw.Draw(sh).ellipse([cx - ew / 2, base_y - 10, cx + ew / 2, base_y + 16], fill=(0, 0, 0, 210 if dark else 120))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    drop = Image.new("RGBA", o.size, (0, 0, 0, 255))
    drop.putalpha(o.getchannel("A").point(lambda v: int(v * (0.45 if dark else 0.22))))
    sh2 = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh2.alpha_composite(drop, (x + 14, y + 22))
    sh2 = sh2.filter(ImageFilter.GaussianBlur(24))
    canvas.alpha_composite(sh)
    canvas.alpha_composite(sh2)
    canvas.alpha_composite(o, (x, y))
    return x, y, x + o.width, y + o.height


# ---------------------------------------------------------------- texto con registro para el QA
class Pen:
    def __init__(self, im, fmt, dark):
        self.im, self.fmt, self.dark = im, fmt, dark
        self.d = ImageDraw.Draw(im)
        self.ink = (246, 246, 246) if dark else (22, 22, 26)
        self.sub = (178, 178, 184) if dark else (92, 92, 100)
        self.log = []

    def text(self, xy, s, f, fill=None, anchor="mt", strike=False):
        fill = fill or self.ink
        self.d.text(xy, s, font=f, fill=fill, anchor=anchor)
        bb = self.d.textbbox(xy, s, font=f, anchor=anchor)
        if strike:
            yb = (bb[1] + bb[3]) / 2 + 2
            self.d.line([bb[0] - 2, yb, bb[2] + 2, yb], fill=fill, width=max(3, f.size // 12))
        self.log.append((s, bb, f.size))
        return bb

    def chip(self, cx, y, s, f, anchor="mt"):
        tw = self.d.textlength(s, font=f)
        padx, h = 24, f.size + 26
        x0 = cx - tw / 2 - padx if anchor == "mt" else cx
        box = [x0, y, x0 + tw + 2 * padx, y + h]
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        fillc = (255, 255, 255, 26) if self.dark else (255, 255, 255, 215)
        line = (255, 255, 255, 60) if self.dark else (0, 0, 0, 28)
        ImageDraw.Draw(layer).rounded_rectangle(box, radius=h / 2, fill=fillc, outline=line, width=2)
        self.im.alpha_composite(layer)
        self.d = ImageDraw.Draw(self.im)
        self.text(((box[0] + box[2]) / 2, y + 13), s, f, anchor="mt")
        return box

    def premium(self, cx, y, size=26):
        """Sello "CALIDAD PREMIUM" con letras espaciadas y filetes finos."""
        f = font("Inter-SemiBold.otf", size)
        s = "C A L I D A D   P R E M I U M"
        gold = (214, 186, 120) if self.dark else (150, 116, 52)
        bb = self.text((cx, y), s, f, fill=gold)
        w = 70
        self.d.line([bb[0] - 18 - w, (bb[1] + bb[3]) / 2, bb[0] - 18, (bb[1] + bb[3]) / 2], fill=gold, width=2)
        self.d.line([bb[2] + 18, (bb[1] + bb[3]) / 2, bb[2] + 18 + w, (bb[1] + bb[3]) / 2], fill=gold, width=2)
        self.log[-1] = ("Calidad Premium", bb, size)
        return bb


def chips_rows(pen, items, f, y, W, gap=14):
    """Coloca sellos en filas centradas; devuelve la y final."""
    rows, cur, curw = [], [], 0
    for s in items:
        w = pen.d.textlength(s, font=f) + 48
        if cur and curw + gap + w > W - 128:
            rows.append(cur)
            cur, curw = [], 0
        cur.append((s, w))
        curw += (gap if cur[:-1] else 0) + w
    if cur:
        rows.append(cur)
    h = f.size + 26
    for r in rows:
        total = sum(w for _, w in r) + gap * (len(r) - 1)
        x = (W - total) / 2
        for s, w in r:
            pen.chip(x, y, s, f, anchor="lt")
            x += w + gap
        y += h + 12
    return y


# ---------------------------------------------------------------- plantillas
def vitrina(ins, cfgs, pid, look, fmt, photo):
    """Título, sello, precio y sellos arriba; el producto real sobre el pedestal abajo."""
    row = DATA[pid]
    dark = look == "onix"
    W, H = SIZES[fmt]
    im, ped, ped_w = load_scene(ins, f"escena_pedestal_{look}", fmt, cfgs[f"escena_pedestal_{look}"])
    pen = Pen(im, fmt, dark)
    x0, top, x1, bottom = SAFE[fmt]
    big = {"4x5": 80, "1x1": 68, "9x16": 82}[fmt]
    y = top + 6
    bb = pen.text((W / 2, y), row["titulo"], font("InterDisplay-ExtraBold.otf", big))
    y = bb[3] + (16 if pid in PREMIUM_OK else 24)
    if pid in PREMIUM_OK:
        bb = pen.premium(W / 2, y)
    else:
        bb = pen.text((W / 2, y), row["sub"], font("Inter-SemiBold.otf", 32), fill=pen.sub)
    y = bb[3] + (22 if fmt != "1x1" else 16)
    bb = pen.text((W / 2, y), row["precio"], font("InterDisplay-ExtraBold.otf", {"4x5": 92, "1x1": 80, "9x16": 92}[fmt]))
    if row.get("antes"):
        pen.text((bb[0] - 22, (bb[1] + bb[3]) / 2 + 6), "Antes " + row["antes"], font("Inter-Medium.otf", 30),
                 fill=pen.sub, anchor="rm", strike=True)
    y = bb[3] + 22
    sellos = row["sellos"] if fmt == "4x5" else row["sellos_cortos"]
    y = chips_rows(pen, sellos, font("Inter-SemiBold.otf", 28), y, W)
    if row.get("nota") and fmt != "1x1":
        bb = pen.text((W / 2, y + 2), row["nota"], font("Inter-Medium.otf", 26), fill=pen.sub)
        y = bb[3]
    room = ped - y - 34
    place(im, photo, W / 2, ped + 4, room * row["alto"], ped_w * 1.15, dark)
    return im, pen


def kit(ins, cfgs, fmt, fotos):
    """COMBO PRO 3 desde arriba: caja real, cable real y los 6 colores del case (círculos)."""
    W, H = SIZES[fmt]
    sc = Image.open(ins / "escena_mesa_onix.png").convert("RGB")
    sc = sc.resize((W, round(sc.height * W / sc.width)), Image.LANCZOS)
    y0 = (sc.height - H) // 2
    im = sc.crop((0, y0, W, y0 + H)).convert("RGBA")
    pen = Pen(im, fmt, True)
    x0, top, x1, bottom = SAFE[fmt]
    bb = pen.text((W / 2, top + 6), "Lo que trae tu", font("Inter-SemiBold.otf", 34 if fmt != "1x1" else 30), fill=pen.sub)
    bb = pen.text((W / 2, bb[3] + 8), "COMBO PRO 3", font("InterDisplay-ExtraBold.otf", {"4x5": 80, "1x1": 66, "9x16": 80}[fmt]))
    y = bb[3] + 30
    # zona de objetos: lo que sobra después de reservar etiquetas, colores, precio y envío (~334 px)
    zh = bottom - 334 - y - 20
    box = fotos["caja"]
    k = min(zh / box.height, (W * 0.55) / box.width)
    bw, bh = int(box.width * k), int(box.height * k)
    bx, by = int(W * 0.08), int(y + 10)
    place(im, box, bx + bw / 2, by + bh, bh, bw, True)
    cable = fotos["cable"]
    kc = min(bh * 0.92 / cable.height, W * 0.14 / cable.width)
    cw, chh = int(cable.width * kc), int(cable.height * kc)
    cx = int(W * 0.08 + bw + (W * 0.92 - (W * 0.08 + bw)) / 2)
    place(im, cable, cx, by + bh, chh, cw, True)
    f = font("Inter-SemiBold.otf", 28)
    pen.text((bx + bw / 2, by + bh + 22), "Audífonos Pro 3", f)
    pen.text((cx, by + bh + 22), "Cable USB-C", f)
    # colores del case
    cols = [((22, 22, 24), "Negro"), ((132, 128, 122), "Gris"), ((28, 46, 92), "Azul acero"),
            ((176, 160, 230), "Lila"), ((226, 178, 166), "Rosa nude"), ((84, 74, 104), "Morado grisáceo")]
    yy = by + bh + 80
    pen.text((W / 2, yy), "Case de regalo: elige tu color", font("Inter-SemiBold.otf", 30))
    yy += 54
    r = 22 if fmt != "1x1" else 18
    step = (W - 2 * 100) / 5
    for i, (c, _) in enumerate(cols):
        cxx = 100 + i * step
        pen.d.ellipse([cxx - r, yy, cxx + r, yy + 2 * r], fill=c, outline=(255, 255, 255), width=3)
    yy += 2 * r + 30
    bb = pen.text((W / 2, yy), "S/ 119", font("InterDisplay-ExtraBold.otf", 80 if fmt != "1x1" else 68))
    pen.text((bb[0] - 22, (bb[1] + bb[3]) / 2 + 6), "Antes S/ 144", font("Inter-Medium.otf", 30), fill=pen.sub,
             anchor="rm", strike=True)
    pen.text((W / 2, bb[3] + 16), "Envío gratis a todo el Perú", font("Inter-SemiBold.otf", 30), fill=pen.sub)
    return im, pen


def asi_compras(ins, cfgs, fmt, photo):
    """Así compras en REVO: 3 pasos + iPhone real sobre el pedestal marfil."""
    W, H = SIZES[fmt]
    im, ped, ped_w = load_scene(ins, "escena_pedestal_marfil", fmt, cfgs["escena_pedestal_marfil"])
    pen = Pen(im, fmt, False)
    x0, top, x1, bottom = SAFE[fmt]
    bb = pen.text((W / 2, top + 6), "Así compras en REVO", font("InterDisplay-ExtraBold.otf", {"4x5": 70, "1x1": 60, "9x16": 72}[fmt]))
    pasos = [("1", "Elige tu iPhone y escríbenos por WhatsApp"),
             ("2", "Te mandamos un video de tu equipo antes de pagar"),
             ("3", "En Lima pagas al recibir")]
    if fmt == "1x1":
        pasos = [("1", "Escríbenos por WhatsApp"), ("2", "Video de tu equipo antes de pagar"), ("3", "En Lima pagas al recibir")]
    f = font("Inter-SemiBold.otf", 30 if fmt != "1x1" else 28)
    y = bb[3] + 34
    r = 24
    for n, s in pasos:
        tw = pen.d.textlength(s, font=f)
        x = (W - (2 * r + 18 + tw)) / 2
        pen.d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=(22, 22, 26))
        pen.text((x + r, y + r), n, font("Inter-Bold.otf", 26), fill=(255, 255, 255), anchor="mm")
        pen.text((x + 2 * r + 18, y + r), s, f, anchor="lm")
        y += 2 * r + 20
    bb = pen.text((W / 2, y + 2), "1 año de garantía REVO por fallas de fábrica", font("Inter-Medium.otf", 28), fill=pen.sub)
    room = ped - bb[3] - 34
    place(im, photo, W / 2, ped + 4, room * 0.92, ped_w * 1.1, False)
    return im, pen


# ---------------------------------------------------------------- QA
def qa(pid, pen):
    errs = []
    alltext = " ".join(s for s, _, _ in pen.log).lower()
    for p in PROHIBIDAS:
        if re.search(p, alltext):
            errs.append("palabra prohibida: " + p)
    if "premium" in alltext and pid not in PREMIUM_OK:
        errs.append("'Calidad Premium' no permitido en " + pid)
    for s, bb, size in pen.log:
        for m in re.findall(r"[sS]/\s?[\d,]+", s):
            if not re.fullmatch(r"S/ \d{1,3}(,\d{3})*", m):
                errs.append("precio mal escrito: " + m)
        x0, y0, x1, y1 = SAFE[pen.fmt]
        if bb[0] < x0 - 1 or bb[2] > x1 + 1 or bb[1] < y0 - 1 or bb[3] > y1 + 1:
            errs.append(f"fuera de zona segura: {s!r} {tuple(int(v) for v in bb)}")
        if size < MIN_PT:
            errs.append(f"letra chica ({size}px): {s!r}")
    return errs


def main(ins, out):
    ins, out = Path(ins), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cfgs = json.loads((ins / "escenas.json").read_text())
    fotos = {pid: Image.open(ins / d["foto"]).convert("RGBA") for pid, d in DATA.items()}
    fotos = {pid: im.crop(im.getchannel("A").getbbox()) for pid, im in fotos.items()}
    kit_fotos = {"caja": fotos["combo-pro-3-a1"],
                 "cable": (lambda c: c.crop(c.getchannel("A").getbbox()))(Image.open(ins / "cable_usbc.png").convert("RGBA"))}
    jobs = []
    for pid, look in (("iphone-17-pro-max", "onix"), ("iphone-17-pro-max", "marfil"), ("combo-pro-3-a1", "onix"),
                      ("combo-pro-3-a1", "marfil"), ("case-iphone", "marfil")):
        for fmt in SIZES:
            jobs.append((f"{pid}__vitrina_{look}_{fmt}", pid, lambda pid=pid, look=look, fmt=fmt: vitrina(ins, cfgs, pid, look, fmt, fotos[pid])))
    for fmt in SIZES:
        jobs.append((f"combo-pro-3-a1__kit_onix_{fmt}", "combo-pro-3-a1", lambda fmt=fmt: kit(ins, cfgs, fmt, kit_fotos)))
        jobs.append((f"iphone-17-pro-max__asi-compras_marfil_{fmt}", "iphone-17-pro-max",
                     lambda fmt=fmt: asi_compras(ins, cfgs, fmt, fotos["iphone-17-pro-max"])))
    report = []
    for name, pid, fn in jobs:
        im, pen = fn()
        im.convert("RGB").save(out / f"{name}.jpg", quality=90, optimize=True)
        errs = qa(pid, pen)
        report.append(f"{name}: " + ("OK" if not errs else " | ".join(errs)))
    (out / "qa.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
