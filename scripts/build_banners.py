#!/usr/bin/env python3
"""Genera la biblioteca de banners de REVO para Meta Ads.

Lee catalogo/revo-catalogo.json (datos de revoimport.com), aplica las 5 plantillas
adaptadas de los prompts originales (+ la plantilla 6 de redimensión) y escribe:

  prompts/banners.json   filas completas (para n8n / Google Sheets)
  prompts/banners.csv    la misma tabla, para importar en Google Sheets
  prompts/BANNERS.md     versión legible, agrupada por producto

Uso:  python3 scripts/build_banners.py
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = json.loads((ROOT / "catalogo" / "revo-catalogo.json").read_text(encoding="utf-8"))
PROD = {p["id"]: p for p in CAT["productos"]}
SERV = {s["id"]: s for s in CAT["servicios"]}

GIFT_CASE = "https://revoimport.com/assets/revo/accessories/case-iphone.webp"
GIFT_MICA = "https://revoimport.com/assets/revo/accessories/mica-iphone.webp"
GIFT_CABLE = "https://revoimport.com/assets/revo/accessories/cable-usbc-usbc.webp"
CUBO_20W = "https://revoimport.com/assets/revo/accessories/cargador-20w.png"
IPHONE_LIGHTNING = "https://revoimport.com/assets/revo/iphone-13-blanco-sin-fondo.png"
IPHONE_USBC = "https://revoimport.com/assets/apple/iphone-17/sage/sage.webp"

DISCLOSURE_PRO3 = "Audífonos compatibles, no originales de Apple."

# ---------------------------------------------------------------------------
# Reglas comunes que se agregan a TODOS los prompts
# ---------------------------------------------------------------------------
RULES = (
    "Brand-safety and text rules: do not show the Apple logo, the word AirPods or any other brand logo, "
    "trademark, sticker or printed label on devices, boxes, cases, cables or screens; device backs, props and "
    "accessories stay clean and unbranded. Any visible phone screen shows only an abstract dark wallpaper with no "
    "icons, apps or text. No people, no hands, no watermarks, no QR codes and no words other than the exact quoted "
    "strings above. Spell every Spanish word exactly as written, keeping accents (á, é, í, ó, ú), ñ, ¿ and ×; "
    "currency is always written S/ followed by a space."
)

FEED_34 = (
    "Format: vertical 3:4 for Facebook and Instagram Feed. Keep the headline, every label, the price and the "
    "button inside the central 4:5 area (leave at least 4% of plain background at the very top and bottom) with "
    "at least 6% side margins, so nothing is lost when the feed crops the image to 4:5."
)

TEMPLATE_NAMES = {
    "T1": "Diagrama de partes (callouts numerados)",
    "T2": "Flat lay con 3 llamadas",
    "T3": "Ficha técnica",
    "T4": "Oferta + plantilla de reseña",
    "T5": "Knolling: problema → solución",
}


def refs_block(refs):
    lines = [f"Image {i} — {desc}" for i, (_, desc) in enumerate(refs, 1)]
    return (
        "Reference images, in order: " + "; ".join(lines) + ". Use the references only for the exact shape, "
        "proportions, color and visible details of each product and keep them identical: do not invent or remove "
        "lenses, ports, buttons, prongs, cables or accessories. Ignore and never reproduce any logo, sticker, "
        "packaging or printed text visible in the references."
    )


# ---------------------------------------------------------------------------
# Plantillas 1-5 (adaptadas de los prompts originales)
# ---------------------------------------------------------------------------
def t1(h, upper_visual, upper, lower_visual, lower, cta, price=None, nota=None):
    up_places = ", ".join(f'"{n}" {where}' for n, where, _ in upper)
    up_labels = " and ".join(f'"{n}  {label}"' for n, _, label in upper)
    lo_places = ", ".join(f'"{n}" {where}' for n, where, _ in lower)
    lo_labels = ", ".join(f'"{n}  {label}"' for n, _, label in lower)
    s = (
        "Vertical 3:4 product feature infographic ad, clean minimalist layout on a pure white background with bold "
        "black sans-serif typography (Helvetica Neue Bold / Neue Haas Grotesk style). All on-image copy is in "
        "Spanish (Peru).\n\n"
        f'Top, centered: bold black all-caps headline in one line "{h}"\n\n'
        f"Upper panel: a large rounded-corner light cool-gray card. Inside, a studio product shot of {upper_visual}, "
        "positioned on the right and slightly cropped by the right edge, soft shadow beneath. Small white circular "
        f"numbered markers with thin black outlines placed on the product: {up_places}. On the left, matching "
        f"markers with bold black text: {up_labels}\n\n"
        f"Lower panel: a second rounded light-gray card. On the left, {lower_visual}. Numbered markers on it: "
        f"{lo_places}. On the right, a vertical list with markers and bold black text: {lo_labels}\n\n"
    )
    if price:
        s += f'Above the button, centered: large bold black price text "{price}"\n'
    s += f'Bottom: a full-width black rounded-rectangle button with bold white all-caps text "{cta}"'
    if nota:
        s += f'\nUnder the button, one line of small gray text: "{nota}"'
    s += (
        "\n\nSoft diffused studio lighting, realistic materials and reflections, sharp e-commerce product "
        "photography, clean technical infographic aesthetic."
    )
    return s


def t2(scene, bg, l1, l2, captions, cta, btn_color="gray", price=None, nota=None):
    caps = "; ".join(f'"{text}" {where}' for text, where in captions) + "."
    s = (
        f"Vertical 3:4 social media ad poster, premium minimalist product photography. Top-down flat lay of {scene}, "
        f"on a smooth matte {bg} background. Soft diffused studio lighting from above, gentle vignette, subtle soft "
        "shadows under every object, high-end editorial look, sharp detail, realistic textures, the muted "
        "background contrasting with the product colors.\n\n"
        "Typography overlay in clean bold white sans-serif (Helvetica / Neue Haas style):\n"
        f'- Top, centered, large all-caps headline in two lines: "{l1}" / "{l2}"\n'
        f"- Three small lowercase callout captions with thin white 1px leader lines pointing at the product: {caps}\n"
    )
    if price:
        s += f'- Just above the button, centered: bold white price text "{price}"\n'
    s += f'- Bottom center: a white rounded-rectangle button with {btn_color} bold all-caps text "{cta}"\n'
    if nota:
        s += f'- Under the button, one line of small white text: "{nota}"\n'
    s += "\nClean layout, generous negative space, modern e-commerce ad aesthetic."
    return s


def t3(h, icons, circles, hero, cta, dims=None, price=None, nota=None):
    ic = "\n".join(f'- {icon} — two lines: "{a}" / "{b}"' for icon, a, b in icons)
    ci = "\n".join(f'- "{title}" — {desc}' for title, desc in circles)
    s = (
        "Vertical 3:4 e-commerce product spec card, clean minimalist layout on a pure white background, black "
        "typography.\n\n"
        f'Top, centered: huge bold black all-caps sans-serif headline (Helvetica Neue Bold style) "{h}"\n\n'
        "Below, a row of three feature icons, each a thin black outlined circle with a minimal line icon inside and "
        f"two-line regular-weight black text to its right:\n{ic}\n\n"
        "Next, a row of three circular close-up detail photos with thin light-gray borders, each with small bold "
        f"black text curved along the top arc of the circle:\n{ci}\n\n"
        f"Main area: a large studio hero shot of {hero}, soft natural shadow on the white background."
    )
    if dims:
        s += f" Thin black dimension lines with round dot endpoints and black text labels: {dims}."
    else:
        s += " No dimension lines."
    s += "\n\n"
    if price:
        s += f'Above the button, centered: large bold black price text "{price}"\n'
    s += (
        "Bottom: a wide outlined button with thin black border, rounded corners, white fill and bold black all-caps "
        f'text "{cta}"'
    )
    if nota:
        s += f'\nUnder the button, one line of small gray text: "{nota}"'
    s += (
        "\n\nSoft diffused studio lighting, realistic textures, sharp high-end product photography, clean technical "
        "spec-sheet aesthetic."
    )
    return s


def t4(badge, hero, title, sub, price=None, old=None, nota=None):
    s = (
        "Vertical 3:4 e-commerce promo ad, clean minimalist layout on a pure white background, modern app-style UI "
        "typography (Inter / SF Pro style).\n\n"
        f'Top left: a dark charcoal pill-shaped badge with bold white text "{badge}"\n\n'
        f"Center: a large studio hero shot of {hero}, soft natural shadow beneath, realistic materials.\n\n"
        "Below the product, centered text block:\n"
        f'- bold black sentence-case title "{title}"\n'
    )
    if price and old:
        s += (
            f'- price line: old price "{old}" in large bold gray with a strikethrough, next to the new price '
            f'"{price}" in large bold dark navy blue\n'
        )
    elif price:
        s += f'- price line: "{price}" in large bold dark navy blue\n'
    s += f'- regular black text "{sub}"\n'
    if nota:
        s += f'- one line of small gray text "{nota}"\n'
    s += (
        "\nBottom: a white rounded-rectangle card with a thin black outline, laid out as a customer review template: "
        "a row of five orange-yellow stars with small gray 5/5, an empty area for a quote, and below it a light-blue "
        "circular avatar plus an empty name line and an empty small gray line. Leave the quote, the avatar initials "
        "and the name completely blank for a real customer review to be added later.\n\n"
        "Soft diffused studio lighting, sharp high-end product photography, clean direct-response e-commerce "
        "aesthetic, generous white space."
    )
    return s


def t5(bg, center, top, left, right, bottom, l1, l2, sub, cta, under, btn_color="navy", contrast="", nota=None):
    s = (
        "Vertical 3:4 social media ad poster, premium minimalist knolling flat lay product photography, shot "
        f"directly from above. Smooth matte {bg} background with subtle texture. In the center, {center}.\n\n"
        "Everyday essentials, all generic and unbranded, arranged neatly around it in a clean grid with even "
        "spacing and right angles:\n"
        f"- Top row: {top}.\n- Left side: {left}.\n- Right side: {right}.\n- Bottom row: {bottom}.\n\n"
        "Soft diffused studio lighting, gentle soft shadows under each object, realistic textures, high-end "
        f"editorial e-commerce look{', ' + contrast if contrast else ''}.\n\n"
        "Typography overlay in clean bold white sans-serif (Helvetica / Neue Haas style):\n"
        f'- Top, centered, large all-caps headline in two lines: "{l1}" / "{l2}"\n'
        f'- Below it, a smaller sentence-case subline: "{sub}"\n'
        f'- Bottom center: a white rounded-rectangle button with {btn_color} bold all-caps text "{cta}"\n'
        f'- Under the button, small white all-caps text: "{under}"\n'
    )
    if nota:
        s += f'- Under that, one line of very small white text: "{nota}"\n'
    s += "\nGenerous negative space, balanced symmetric layout, modern minimalist ad aesthetic."
    return s


# ---------------------------------------------------------------------------
# Plantilla 6: redimensión (Feed 1:1 y Stories/Reels 9:16) a partir del master 3:4
# ---------------------------------------------------------------------------
def resize_prompt(ratio, texts):
    tl = "; ".join(f'"{t}"' for t in texts)
    base = (
        "Resize and recompose the reference ad (Image 1, the approved 3:4 master) into a new creative. Keep the same "
        "product photography, product identity, colors, background, typography style and layout logic, and keep "
        f"EXACTLY the same text strings: {tl}. Do not add, remove, translate or rephrase any text. Adjust the layout "
        "so the text and the product stay fully visible: nothing cut by the frame edges, at least 6% margins on every "
        "side, text never overlapping the product.\n\n"
    )
    if ratio == "1:1":
        base += (
            "Format: square 1:1 for Facebook and Instagram Feed. Rearrange elements instead of shrinking the text "
            "(for example product on one side and labels on the other); the headline stays on top and the button "
            "or review card stays at the bottom."
        )
    else:
        base += (
            "Format: vertical 9:16 for Instagram and Facebook Stories and Reels. Keep the top 14% and the bottom 35% "
            "of the canvas free of any text, price, label, badge, card or button; only plain background (or the "
            "extended scene surface) may continue there. Place the complete ad, headline, product, labels, price and "
            "button, inside the band between 14% and 65% of the height, scaled to fit."
        )
    return base + "\n\n" + RULES


# ---------------------------------------------------------------------------
# Datos creativos por producto
# ---------------------------------------------------------------------------
def iphone_rows(pid, color_desc, bg2, bg5, btn5, t5_head, meta):
    p = PROD[pid]
    name, up = p["nombre"], p["nombre"].upper()
    col = p["color_banner"]
    pro = p["camara"] == "triple"
    body = (
        "flat-edged smartphone with a full-width rear camera plateau holding three large lenses, a flash and a sensor"
        if pro else
        "flat-edged smartphone with a vertical two-lens camera bump in the top-left corner of the back"
    )
    vis = f"the {name} in {col} ({color_desc}), a {body}, identical to reference Image 1"
    cam_word = "Triple cámara" if pro else "Doble cámara"
    precio = p["precio"]
    precio_lc = precio[0].lower() + precio[1:]
    caps = p["capacidades"]
    caps_txt = caps[0] if len(caps) == 1 else ", ".join(caps[:-1]) + " o " + caps[-1]
    r_par = (p["refs"]["par"], f"the {name} in {col}, front and back (product identity)")
    r_cam = (p["refs"]["camara"], f"close-up of the {name} camera area")
    r_lat = (p["refs"]["lateral"], f"side profile of the {name}")
    r_case = (GIFT_CASE, "the clear transparent gift case")
    r_mica = (GIFT_MICA, "the tempered-glass gift screen protector")
    r_cable = (GIFT_CABLE, "the white USB-C gift cable")

    second = (f"Pantalla de {p['pantalla']}." if p["pantalla"] else f"{caps_txt} de almacenamiento.")
    rows = {}
    rows["T1"] = dict(
        refs=[r_par, r_cam, r_case, r_mica, r_cable],
        prompt=t1(
            h=f"TU {up}, NUEVO Y SELLADO",
            upper_visual=f"{vis}, in 3/4 rear view showing the camera, with a second unit partly visible behind it "
                         "showing the screen",
            upper=[("1", "on the camera", f"{cam_word}."), ("2", "on the screen of the second unit", second)],
            lower_visual="a top-down view of the same phone lying screen-down next to its gifts: the clear "
                         "transparent case (Image 3), the tempered-glass screen protector (Image 4) and the neatly "
                         "coiled white USB-C cable (Image 5)",
            lower=[("3", "on the phone", "Nuevo y sellado."), ("4", "on the case", "Case de regalo."),
                   ("5", "on the screen protector", "Mica de regalo."),
                   ("6", "on the cable", "Cable compatible de regalo.")],
            price=precio, cta="PIDE HOY",
            nota="+ Audífonos Pro 2 de regalo. Regalos sujetos a disponibilidad."),
    )
    rows["T2"] = dict(
        refs=[r_par, r_case, r_mica, r_cable],
        prompt=t2(
            scene=f"{vis}, lying screen-down diagonally, with its gifts arranged around it: the clear transparent case "
                  "(Image 2), the tempered-glass screen protector (Image 3) and the coiled white USB-C cable (Image 4)",
            bg=bg2, l1=f"TU {up}", l2="VIENE ACOMPAÑADO",
            captions=[("nuevo y sellado.", "upper left, with a line going down to the phone"),
                      ("case, mica y cable de regalo.", "upper right, with an L-shaped line pointing to the gifts"),
                      ("video de tu equipo antes de pagar.", "lower center, with a vertical line from the phone")],
            price=precio, cta="PIDE HOY"),
    )
    icons = []
    if p["pantalla"]:
        icons.append(("smartphone outline icon", "Pantalla de", p["pantalla"]))
    icons.append(("memory chip icon", caps[0] + (" a" if len(caps) > 1 else " de"),
                  caps[-1] if len(caps) > 1 else "almacenamiento"))
    if p["sim"].startswith("eSIM"):
        icons.append(("SIM card icon", "eSIM o", "chip físico"))
    else:
        icons.append(("shield icon", "1 año de", "garantía"))
    if len(icons) < 3:
        icons.insert(0, ("sealed box icon", "Nuevo y", "sellado"))
    rows["T3"] = dict(
        refs=[r_par, r_cam, r_lat],
        prompt=t3(
            h=f"{up}.",
            icons=icons,
            circles=[(cam_word, "close-up of the rear camera (Image 2)"),
                     (f"Color {col}", "close-up of the back surface color"),
                     ("Vista lateral", "close-up of the side profile with its buttons (Image 3)")],
            hero=f"{vis}: two units standing upright side by side, one in front view with the screen facing the camera "
                 "and one showing the back",
            dims=(f'one thin diagonal line across the front screen from corner to corner labeled "{p["pantalla"]}"'
                  if p["pantalla"] else None),
            price=precio, cta="PIDE HOY"),
    )
    rows["T4"] = dict(
        refs=[r_par],
        prompt=t4(badge="4 regalos incluidos", hero=f"{vis}, in 3/4 rear view, standing upright",
                  title=f"{name} nuevo y sellado", price=precio,
                  sub="Contraentrega en Lima · Envíos a todo el Perú"),
    )
    rows["T5"] = dict(
        refs=[r_par, r_case, r_mica, r_cable],
        prompt=t5(
            bg=bg5, center=f"{vis}, lying screen-down",
            top="the clear transparent gift case (Image 2), the tempered-glass screen protector (Image 3), the coiled "
                "white USB-C cable (Image 4)",
            left="a matte insulated steel water bottle",
            right="a black hardcover notebook with an elastic band, a leather card holder",
            bottom="a set of keys on a leather keyring, black sunglasses, a small leather wallet, a ceramic coffee cup "
                   "seen from above",
            l1=t5_head[0], l2=t5_head[1], sub=f"{name} nuevo y sellado, {precio_lc}",
            cta="PIDE HOY", under="CONTRAENTREGA EN LIMA", btn_color=btn5,
            contrast=f"the {color_desc} phone contrasting with the {bg5.split('/')[0].strip()} background"),
    )
    return rows, meta


META_IPHONE_3 = "Recibe un video de tu equipo antes de pagar. En Lima pagas al recibir; a provincia coordinamos el envío."


def build_products():
    out = {}

    out["iphone-18-pro-max"] = iphone_rows(
        "iphone-18-pro-max", "deep burgundy", "warm stone-gray", "dusty navy-blue / slate-blue", "navy",
        ("¿TOCA CAMBIAR", "DE IPHONE?"),
        dict(textos=["iPhone 18 Pro Max nuevo y sellado, 256 GB, a S/ 6,550. Te enviamos un video de tu equipo antes de pagar.",
                     "Elige Guinda, Celeste, Silver o Negro. Viene con 4 regalos y 1 año de garantía por fallas de fábrica.",
                     "En Lima pagas al recibir. A provincia también llegamos: coordinamos pago y envío por WhatsApp."],
             titulos=["iPhone 18 Pro Max a S/ 6,550", "Nuevo, sellado y con 4 regalos", "Pagas al recibir en Lima"],
             descripcion="Consulta disponibilidad"))
    out["iphone-18-pro"] = iphone_rows(
        "iphone-18-pro", "light sky blue", "soft sand-beige", "deep charcoal-gray", "charcoal",
        ("TU PRÓXIMO", "IPHONE ESTÁ AQUÍ"),
        dict(textos=["iPhone 18 Pro nuevo y sellado, 256 GB, a S/ 6,200. Te enviamos un video de tu equipo antes de pagar.",
                     "Elige Celeste, Guinda, Silver o Negro. Viene con 4 regalos y 1 año de garantía por fallas de fábrica.",
                     "En Lima pagas al recibir. A provincia también llegamos: coordinamos pago y envío por WhatsApp."],
             titulos=["iPhone 18 Pro a S/ 6,200", "Nuevo, sellado y con 4 regalos", "Pagas al recibir en Lima"],
             descripcion="Consulta disponibilidad"))
    out["iphone-17-pro-max"] = iphone_rows(
        "iphone-17-pro-max", "bright cosmic orange", "slate-gray / muted green-gray", "dusty navy-blue / slate-blue", "navy",
        ("¿BUSCAS UN", "PRO MAX?"),
        dict(textos=["iPhone 17 Pro Max nuevo y sellado desde S/ 4,600. Pantalla de 6.9 pulgadas, en 256 GB, 512 GB o 1 TB.",
                     "Silver, Naranja o Azul, con eSIM o chip físico. Incluye 4 regalos y 1 año de garantía por fallas de fábrica.",
                     META_IPHONE_3],
             titulos=["iPhone 17 Pro Max desde S/ 4,600", "Nuevo, sellado y con 4 regalos", "Video antes de pagar"],
             descripcion="Consulta disponibilidad"))
    out["iphone-17-pro"] = iphone_rows(
        "iphone-17-pro", "deep blue", "warm light-gray", "muted terracotta", "terracotta",
        ("¿LISTO PARA", "EL PRO?"),
        dict(textos=["iPhone 17 Pro nuevo y sellado desde S/ 4,190. Pantalla de 6.3 pulgadas y 256 GB.",
                     "Silver, Naranja o Azul, con eSIM o chip físico. Incluye 4 regalos y 1 año de garantía por fallas de fábrica.",
                     META_IPHONE_3],
             titulos=["iPhone 17 Pro desde S/ 4,190", "Nuevo, sellado y con 4 regalos", "Video antes de pagar"],
             descripcion="Consulta disponibilidad"))
    out["iphone-17"] = iphone_rows(
        "iphone-17", "soft lavender", "pale sage-green", "dusty slate-blue", "slate-blue",
        ("TU PRÓXIMO IPHONE.", "CON TODA CONFIANZA."),
        dict(textos=["iPhone 17 nuevo y sellado desde S/ 3,200. 256 GB y pantalla de 6.3 pulgadas.",
                     "Lila, Azul, Negro, Verde o Blanco: tú eliges. Con 4 regalos y 1 año de garantía por fallas de fábrica.",
                     META_IPHONE_3],
             titulos=["iPhone 17 desde S/ 3,200", "5 colores y 4 regalos", "Video antes de pagar"],
             descripcion="Consulta disponibilidad"))

    # ---------------- Accesorios ----------------
    META_GEN_3 = "En Lima pagas al recibir. A provincia coordinamos pago y envío por WhatsApp."
    COMPAT = "Confirma la compatibilidad con tu equipo."

    # Cable USB-C a Lightning
    p = PROD["cable-usbc-lightning"]
    cab = "the white USB-C to Lightning cable from reference Image 1"
    r1 = (p["refs"]["producto"], "the white USB-C to Lightning cable (product identity)")
    r2 = (IPHONE_LIGHTNING, "a white iPhone with a Lightning port, back view (context prop)")
    r3 = (CUBO_20W, "a compact white 20 W USB-C power adapter (context prop)")
    out[p["id"]] = ({
        "T1": dict(refs=[r1, r2], prompt=t1(
            h="CABLE USB-C A LIGHTNING",
            upper_visual=f"{cab}, loosely curved, with both connector ends in sharp close-up",
            upper=[("1", "on the USB-C plug", "Conector USB-C."), ("2", "on the Lightning plug", "Conector Lightning.")],
            lower_visual=f"a top-down view of the same cable neatly coiled next to the white iPhone from Image 2 seen from the back",
            lower=[("3", "on the coil", "1 metro de largo."), ("4", "on the Lightning plug near the phone", "Para iPhone con Lightning.")],
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T2": dict(refs=[r1, r2, r3], prompt=t2(
            scene=f"{cab} coiled in a loose loop, its USB-C end resting beside the compact white power adapter "
                  "(Image 3) and its Lightning end next to the white iPhone seen from the back (Image 2)",
            bg="muted sage-green", l1="EL CABLE QUE", l2="TE FALTABA",
            captions=[("usb-c a lightning.", "upper left, with a line going down to the cable"),
                      ("1 metro de largo.", "upper right, with an L-shaped line pointing to the coil"),
                      ("para iphone con lightning.", "lower center, with a vertical line from the Lightning plug")],
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T3": dict(refs=[r1], prompt=t3(
            h="CABLE USB-C A LIGHTNING.",
            icons=[("cable icon", "1 metro", "de largo"), ("plug icon", "USB-C a", "Lightning"),
                   ("sealed box icon", "Sellado en", "su empaque")],
            circles=[("Conector USB-C", "close-up of the USB-C plug"), ("Conector Lightning", "close-up of the Lightning plug"),
                     ("Cable de 1 m", "close-up of the white cable coil")],
            hero=f"{cab} arranged in a large loose S-curve with both ends visible",
            dims='one long thin line running along the cable labeled "1 m"',
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T4": dict(refs=[r1], prompt=t4(
            badge="Contraentrega en Lima", hero=f"{cab} coiled loosely with both plugs facing the camera",
            title="Cable USB-C a Lightning de 1 m", price=p["precio"], sub=COMPAT)),
        "T5": dict(refs=[r1, r2, r3], prompt=t5(
            bg="dusty navy-blue", center=f"{cab}, neatly coiled",
            top="the white iPhone seen from the back (Image 2), the compact white power adapter (Image 3)",
            left="a matte black water bottle", right="a spiral notebook and a pen",
            bottom="a set of keys, a small leather wallet, a pair of reading glasses",
            l1="¿TU CABLE", l2="YA FALLA?", sub="Cable USB-C a Lightning de 1 m, sellado · S/ 35",
            cta="PIDE HOY", under="ENVÍOS A TODO EL PERÚ", contrast="the white cable contrasting with the blue background")),
    }, dict(textos=["Cable USB-C a Lightning de 1 m, sellado, a S/ 35. Confirma con nosotros la compatibilidad con tu equipo.",
                    "Carga tu iPhone con conector Lightning desde un cubo USB-C. Pídelo por WhatsApp y te lo enviamos.",
                    META_GEN_3],
            titulos=["Cable USB-C a Lightning a S/ 35", "1 metro, sellado", "Pagas al recibir en Lima"],
            descripcion="Confirma tu compatibilidad"))

    # Cable USB-C a USB-C
    p = PROD["cable-usbc-usbc"]
    cab = "the white USB-C to USB-C cable from reference Image 1"
    r1 = (p["refs"]["producto"], "the white USB-C to USB-C cable (product identity)")
    r2 = (IPHONE_USBC, "a green iPhone 17 with a USB-C port (context prop)")
    out[p["id"]] = ({
        "T1": dict(refs=[r1, r2], prompt=t1(
            h="CABLE USB-C A USB-C",
            upper_visual=f"{cab}, loosely curved, with both USB-C plugs in sharp close-up",
            upper=[("1", "on one plug", "USB-C en un extremo."), ("2", "on the other plug", "USB-C en el otro.")],
            lower_visual="a top-down view of the same cable neatly coiled next to the green iPhone from Image 2 seen from the back",
            lower=[("3", "on the coil", "1 metro de largo."), ("4", "on the plug near the phone", "Para iPhone con USB-C.")],
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T2": dict(refs=[r1, r2, (CUBO_20W, "a compact white 20 W USB-C power adapter (context prop)")], prompt=t2(
            scene=f"{cab} coiled in a loose loop, one end beside the compact white power adapter (Image 3) and the "
                  "other end next to the green iPhone seen from the back (Image 2)",
            bg="warm light-gray", l1="CARGA TU IPHONE", l2="CON USB-C",
            captions=[("usb-c a usb-c.", "upper left, with a line going down to the cable"),
                      ("1 metro de largo.", "upper right, with an L-shaped line pointing to the coil"),
                      ("para iphone con usb-c.", "lower center, with a vertical line from the plug")],
            price=p["precio"], cta="PIDE HOY", btn_color="dark gray", nota=COMPAT)),
        "T3": dict(refs=[r1], prompt=t3(
            h="CABLE USB-C A USB-C.",
            icons=[("cable icon", "1 metro", "de largo"), ("plug icon", "USB-C en", "ambos extremos"),
                   ("sealed box icon", "Sellado en", "su empaque")],
            circles=[("Conector USB-C", "close-up of one USB-C plug"), ("Cable blanco", "close-up of the white cable"), ("Cable de 1 m", "close-up of the cable coil")],
            hero=f"{cab} arranged in a large loose S-curve with both ends visible",
            dims='one long thin line running along the cable labeled "1 m"',
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T4": dict(refs=[r1], prompt=t4(
            badge="Contraentrega en Lima", hero=f"{cab} coiled loosely with both plugs facing the camera",
            title="Cable USB-C a USB-C de 1 m", price=p["precio"], sub=COMPAT)),
        "T5": dict(refs=[r1, r2], prompt=t5(
            bg="muted terracotta", center=f"{cab}, neatly coiled",
            top="the green iPhone seen from the back (Image 2), a closed silver laptop",
            left="a matte white water bottle", right="a black hardcover notebook, a pen",
            bottom="a set of keys, black sunglasses, a small leather wallet",
            l1="¿TE FALTA", l2="UN CABLE?", sub="Cable USB-C a USB-C de 1 m, sellado · S/ 45",
            cta="PIDE HOY", under="ENVÍOS A TODO EL PERÚ", btn_color="terracotta",
            contrast="the white cable contrasting with the warm background")),
    }, dict(textos=["Cable USB-C a USB-C de 1 m, sellado, a S/ 45. Confirma con nosotros la compatibilidad con tu equipo.",
                    "Para iPhone con USB-C. Pídelo por WhatsApp y te lo enviamos a todo el Perú.",
                    META_GEN_3],
            titulos=["Cable USB-C a USB-C a S/ 45", "1 metro, sellado", "Pagas al recibir en Lima"],
            descripcion="Confirma tu compatibilidad"))

    # Cubo 20 W y cargador 40 W
    for pid, watts, h1, title4, extra_lbl, badge, t2h, t5h, t5sub, meta in [
        ("cargador-20w", "20 W", "CUBO USB-C DE 20 W", "Cubo USB-C de 20 W", "Carga rápida de 20 W.", "Carga rápida", ("CARGA RÁPIDA", "Y COMPACTA"),
         ("¿TU CARGADOR", "ES MUY LENTO?"), "Cubo USB-C de 20 W con carga rápida · S/ 99",
         dict(textos=["Cubo USB-C de 20 W con carga rápida a S/ 99. Compacto y listo para tu cable USB-C.",
                      "Arma tu carga completa: suma un cable USB-C a USB-C o a Lightning. Te ayudamos a elegir por WhatsApp.",
                      META_GEN_3],
              titulos=["Cubo USB-C 20 W a S/ 99", "Carga rápida, tamaño compacto", "Pagas al recibir en Lima"],
              descripcion="Confirma tu compatibilidad")),
        ("cargador-40w", "40 W", "CARGADOR USB-C DE 40 W", "Cargador USB-C de 40 W", "40 W de potencia.", "Original", ("MÁXIMA POTENCIA", "PARA TU CARGA"),
         ("MÁS POTENCIA", "PARA TU DÍA"), "Cargador USB-C de 40 W original · S/ 185",
         dict(textos=["Cargador USB-C de 40 W original a S/ 185. Máxima potencia para tu carga.",
                      "Confirma con nosotros la compatibilidad con tu equipo y pídelo por WhatsApp.",
                      META_GEN_3],
              titulos=["Cargador USB-C 40 W a S/ 185", "Original, 40 W de potencia", "Pagas al recibir en Lima"],
              descripcion="Confirma tu compatibilidad")),
    ]:
        p = PROD[pid]
        ad = f"the compact white {watts} USB-C power adapter from reference Image 1"
        r1 = (p["refs"]["producto"], f"the white {watts} USB-C power adapter (product identity)")
        r2 = (p["refs"]["cable"], "a white USB-C cable (context prop)")
        r3 = (IPHONE_USBC, "a green iPhone 17 (context prop)")
        is40 = pid == "cargador-40w"
        out[pid] = ({
            "T1": dict(refs=[r1, r2], prompt=t1(
                h=h1,
                upper_visual=f"{ad}, in 3/4 view showing its two flat plug prongs and the USB-C port",
                upper=[("1", "on the USB-C port", "Puerto USB-C."), ("2", "on the prongs", "Enchufe de dos patas.")],
                lower_visual=f"a top-down view of the same adapter with the coiled white USB-C cable (Image 2) plugged in",
                lower=[("3", "on the adapter", extra_lbl), ("4", "on the adapter body", "Original." if is40 else "Tamaño compacto.")],
                price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
            "T2": dict(refs=[r1, r2, r3], prompt=t2(
                scene=f"{ad} with the white USB-C cable (Image 2) plugged in and running to the green iPhone seen from "
                      "the back (Image 3)",
                bg="muted sage-green" if not is40 else "deep charcoal-gray", l1=t2h[0], l2=t2h[1],
                captions=[(f"{watts.lower()} de potencia.", "upper left, with a line going down to the adapter"),
                          ("puerto usb-c.", "upper right, with an L-shaped line pointing to the port"),
                          ("original." if is40 else "carga rápida.", "lower center, with a vertical line from the adapter")],
                price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
            "T3": dict(refs=[r1], prompt=t3(
                h=f"{p['nombre'].upper()}.",
                icons=[("lightning bolt icon", "Carga" if not is40 else "Máxima", "rápida" if not is40 else "potencia"),
                       (f'the text "{watts}" inside the circle', f"{watts} de", "potencia"),
                       ("USB-C port icon", "Puerto", "USB-C")],
                circles=[("Puerto USB-C", "close-up of the USB-C port"), ("Enchufe de dos patas", "close-up of the flat prongs"),
                         ("Diseño compacto" if not is40 else "Acabado blanco", "close-up of the adapter body")],
                hero=f"{ad} in 3/4 front-side view",
                price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
            "T4": dict(refs=[r1], prompt=t4(
                badge=badge, hero=f"{ad} in 3/4 view", title=title4,
                price=p["precio"], sub="Contraentrega en Lima · Envíos a todo el Perú", nota=COMPAT)),
            "T5": dict(refs=[r1, r2, r3], prompt=t5(
                bg="dusty slate-blue" if not is40 else "muted olive-green", center=f"{ad}",
                top="the green iPhone seen from the back (Image 3), the coiled white USB-C cable (Image 2)",
                left="a matte insulated steel water bottle", right="a black hardcover notebook, a leather card holder",
                bottom="a set of keys, black sunglasses, a ceramic coffee cup seen from above",
                l1=t5h[0], l2=t5h[1], sub=t5sub, cta="PIDE HOY", under="CONTRAENTREGA EN LIMA",
                btn_color="slate-blue" if not is40 else "olive-green",
                contrast="the white adapter contrasting with the colored background")),
        }, meta)

    # Case transparente
    p = PROD["case-iphone"]
    r1 = (p["refs"]["producto"], "the clear transparent phone case (product identity)")
    r2 = (p["refs"]["iphone"], "an orange iPhone 17 Pro, back view (the phone inside the case)")
    case_on = "the clear transparent case from reference Image 1 fitted on the orange iPhone 17 Pro from reference Image 2"
    out[p["id"]] = ({
        "T1": dict(refs=[r1, r2], prompt=t1(
            h="CASE TRANSPARENTE", upper_visual=f"{case_on}, 3/4 rear view",
            upper=[("1", "on the clear back", "Deja ver el color."), ("2", "on the camera opening", "Abertura para la cámara.")],
            lower_visual="the empty clear case from Image 1 lying flat, top-down, next to the phone",
            lower=[("3", "on the empty case", "Calidad premium."), ("4", "on the phone", "Para todos los modelos.")],
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T2": dict(refs=[r1, r2], prompt=t2(
            scene=f"{case_on}, lying screen-down, with a second empty clear case beside it",
            bg="soft sand-beige", l1="PROTEGE TU IPHONE", l2="SIN TAPAR SU COLOR",
            captions=[("transparente.", "upper left, with a line going down to the case"),
                      ("calidad premium.", "upper right, with an L-shaped line pointing to the empty case"),
                      ("para todos los modelos.", "lower center, with a vertical line from the phone")],
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T3": dict(refs=[r1, r2], prompt=t3(
            h="CASE TRANSPARENTE.",
            icons=[("shield icon", "Protege sin", "tapar el color"), ("smartphone outline icon", "Todos los", "modelos"),
                   ("star icon", "Calidad", "premium")],
            circles=[("Transparente", "close-up of the clear back showing the orange color through it"),
                     ("Abertura de cámara", "close-up of the camera opening"), ("Bordes", "close-up of the case edge")],
            hero=f"{case_on}, standing upright in 3/4 rear view",
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T4": dict(refs=[r1, r2], prompt=t4(
            badge="Calidad premium", hero=f"{case_on}, standing upright in 3/4 rear view",
            title="Case transparente para tu iPhone", price=p["precio"], sub=COMPAT)),
        "T5": dict(refs=[r1, r2], prompt=t5(
            bg="muted plum-gray", center=f"{case_on}, lying screen-down",
            top="a second empty clear case, a pair of white wired earphones coiled", left="a matte water bottle",
            right="a small notebook, a pen", bottom="a set of keys, sunglasses, a small wallet",
            l1="TU IPHONE,", l2="SIN TAPAR SU COLOR", sub="Case transparente calidad premium · S/ 15",
            cta="PIDE HOY", under="CONTRAENTREGA EN LIMA", btn_color="plum",
            contrast="the orange phone contrasting with the plum background")),
    }, dict(textos=["Case transparente calidad premium a S/ 15. Protege tu iPhone sin tapar su color.",
                    "Hay para todos los modelos: dinos cuál tienes y te confirmamos la compatibilidad.",
                    META_GEN_3],
            titulos=["Case transparente a S/ 15", "Protege sin tapar el color", "Para todos los modelos"],
            descripcion="Confirma tu modelo"))

    # Mica
    p = PROD["mica-iphone"]
    r1 = (p["refs"]["producto"], "the tempered-glass screen protector (product identity)")
    r2 = (p["refs"]["iphone"], "a silver iPhone 17 Pro, front view (context prop)")
    mica = "the clear rectangular tempered-glass screen protector from reference Image 1"
    out[p["id"]] = ({
        "T1": dict(refs=[r1, r2], prompt=t1(
            h="MICA DE VIDRIO TEMPLADO",
            upper_visual=f"{mica} hovering just above the screen of the silver iPhone from Image 2 (front view)",
            upper=[("1", "on the glass", "Vidrio templado."), ("2", "on the glass edge", "Calidad premium.")],
            lower_visual="a top-down view of the protector applied on the phone screen with a subtle glossy reflection",
            lower=[("3", "on the screen", "Elige la de tu modelo.")],
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T2": dict(refs=[r1, r2], prompt=t2(
            scene=f"{mica} lying next to the silver iPhone (Image 2) shown screen-up",
            bg="dusty slate-blue", l1="CUIDA TU PANTALLA", l2="POR S/ 10",
            captions=[("vidrio templado.", "upper left, with a line going down to the protector"),
                      ("calidad premium.", "upper right, with an L-shaped line pointing to the glass edge"),
                      ("elige la de tu modelo.", "lower center, with a vertical line from the phone")],
            cta="PIDE HOY", nota=COMPAT)),
        "T3": dict(refs=[r1, r2], prompt=t3(
            h="MICA DE PROTECCIÓN.",
            icons=[("layered glass icon", "Vidrio", "templado"), ("star icon", "Calidad", "premium"),
                   ("smartphone outline icon", "Según tu", "modelo")],
            circles=[("Vidrio templado", "close-up of the glass edge"), ("Brillo", "close-up of a glossy reflection on the glass"),
                     ("Pantalla", "close-up of the protected screen corner")],
            hero=f"{mica} leaning against the silver iPhone (Image 2) standing upright",
            price=p["precio"], cta="PIDE HOY", nota=COMPAT)),
        "T4": dict(refs=[r1, r2], prompt=t4(
            badge="Vidrio templado", hero=f"{mica} hovering just above the screen of the silver iPhone (Image 2)",
            title="Mica de protección para tu iPhone", price=p["precio"], sub=COMPAT)),
        "T5": dict(refs=[r1, r2], prompt=t5(
            bg="muted olive-green", center=f"the silver iPhone (Image 2) screen-up with {mica} beside it",
            top="a clear transparent phone case, a microfiber cleaning cloth", left="a matte water bottle",
            right="a black notebook, a pen", bottom="a set of keys, sunglasses, a small wallet",
            l1="¿PANTALLA", l2="SIN PROTEGER?", sub="Mica de vidrio templado · S/ 10",
            cta="PIDE HOY", under="CONTRAENTREGA EN LIMA", btn_color="olive-green")),
    }, dict(textos=["Mica de vidrio templado calidad premium a S/ 10. Cuida la pantalla de tu iPhone.",
                    "Dinos tu modelo y te confirmamos la mica compatible. Pídela por WhatsApp.",
                    META_GEN_3],
            titulos=["Mica de vidrio templado a S/ 10", "Calidad premium", "Pagas al recibir en Lima"],
            descripcion="Confirma tu modelo"))

    # ---------------- Combos ----------------
    ear = ("a pair of white in-ear wireless earbuds with short stems and a compact white glossy charging case "
           "(shape and color only from reference Image 1; that reference is a retail box: do not reproduce the box, "
           "its printing or its sticker)")
    r_ear = (PROD["combo-pro-3-a1"]["refs"]["audifonos"], "retail box showing the earbuds: use ONLY the earbud and charging-case shape and white color")
    r_cases = (PROD["combo-pro-3-a1"]["refs"]["cases"], "the six silicone case colors (black, gray, steel blue, lilac, nude pink, grayish purple): render the cases plain, without any printed text")
    r_cable = (GIFT_CABLE, "the white USB-C to USB-C cable")
    r_cubo = (CUBO_20W, "the white 20 W USB-C power adapter")
    r_light = (PROD["combo-20w"]["refs"]["cable_lightning"], "the white USB-C to Lightning cable")
    ENVIO = "Envío gratis a todo el Perú."

    p = PROD["combo-pro-3-a1"]
    out[p["id"]] = ({
        "T1": dict(refs=[r_ear, r_cases, r_cable], prompt=t1(
            h="LO QUE TRAE TU COMBO PRO 3",
            upper_visual=f"{ear}, the case open with both earbuds inside, in 3/4 view",
            upper=[("1", "on the earbuds", "Audífonos Pro 3 Calidad Premium."), ("2", "on the charging case", "Estuche de carga.")],
            lower_visual="a top-down view of the charging case fitted in a plain steel-blue protective case (colors from "
                         "Image 2) next to the coiled white USB-C cable (Image 3) and a small fan of the other case colors",
            lower=[("3", "on the steel-blue case", "Case de regalo."), ("4", "on the cable", "Cable USB-C a USB-C."),
                   ("5", "on the fan of colors", "6 colores para elegir.")],
            price=p["precio"], cta="PIDE HOY", nota=f"{ENVIO} {DISCLOSURE_PRO3}")),
        "T2": dict(refs=[r_ear, r_cases, r_cable], prompt=t2(
            scene=f"{ear}, the charging case open inside a plain lilac protective case, with the coiled white USB-C "
                  "cable (Image 3) and three more plain cases in nude pink, steel blue and black (Image 2) fanned beside it",
            bg="slate-gray / muted green-gray", l1="TU COMBO PRO 3", l2="A S/ 119",
            captions=[("audífonos + cable + case.", "upper left, with a line going down to the earbuds"),
                      ("6 colores de case.", "upper right, with an L-shaped line pointing to the fanned cases"),
                      ("envío gratis a todo el perú.", "lower center, with a vertical line from the cable")],
            cta="PIDE HOY", nota=DISCLOSURE_PRO3)),
        "T3": dict(refs=[r_ear, r_cases, r_cable], prompt=t3(
            h="COMBO PRO 3.",
            icons=[("earbuds icon", "Audífonos", "Pro 3"), ("cable icon", "Cable USB-C", "a USB-C"), ("gift icon", "Case de", "regalo")],
            circles=[("Estuche de carga", "close-up of the open charging case with the earbuds"),
                     ("Case de regalo", "close-up of the plain gray protective case"),
                     ("Cable USB-C", "close-up of the USB-C plug")],
            hero=f"{ear}, the charging case fitted in a plain gray protective case, the earbuds beside it and the coiled cable (Image 3)",
            price=p["precio"], cta="PIDE HOY", nota=f"{ENVIO} {DISCLOSURE_PRO3}")),
        "T4": dict(refs=[r_ear, r_cases, r_cable], prompt=t4(
            badge="Ahorra S/ 25",
            hero=f"{ear}, the case open with the earbuds, fitted in a plain steel-blue protective case, beside the coiled white USB-C cable",
            title="Combo Pro 3: audífonos, cable y case", price=p["precio"], old=p["precio_antes"],
            sub="Envío gratis a todo el Perú · Pagas al recibir", nota=DISCLOSURE_PRO3)),
        "T5": dict(refs=[r_ear, r_cases, r_cable], prompt=t5(
            bg="dusty navy-blue", center=f"{ear}, the charging case fitted in a plain lilac protective case",
            top="plain protective cases in black, gray and steel blue (Image 2)",
            left="the coiled white USB-C cable (Image 3)", right="plain protective cases in nude pink and grayish purple (Image 2)",
            bottom="a set of keys, black sunglasses, a small leather wallet, a phone lying screen-down without logos",
            l1="¿AUDÍFONOS NUEVOS", l2="POR S/ 119?", sub="Pro 3 Calidad Premium + cable + case de regalo",
            cta="PIDE HOY", under="ENVÍO GRATIS A TODO EL PERÚ", nota=DISCLOSURE_PRO3,
            contrast="the white earbuds and pastel cases contrasting with the blue background")),
    }, dict(textos=["Combo Pro 3 a S/ 119 (antes S/ 144): audífonos Calidad Premium + cable USB-C + case de regalo.",
                    "Envío gratis a Lima y provincia, y pagas al llegar a tu casa. Elige tu case entre 6 colores.",
                    "Audífonos Pro 3 Calidad Premium compatibles, no originales de Apple. Pídelo por WhatsApp."],
            titulos=["Combo Pro 3 a S/ 119", "Envío gratis a todo el Perú", "Case de regalo en 6 colores"],
            descripcion="Pagas al recibir"))

    p = PROD["combo-pro-3-4en1"]
    out[p["id"]] = ({
        "T1": dict(refs=[r_ear, r_cases, r_cubo, r_cable], prompt=t1(
            h="COMBO PRO 3 · 4 EN 1",
            upper_visual=f"{ear}, the case open with both earbuds inside, in 3/4 view",
            upper=[("1", "on the earbuds", "Audífonos Pro 3 Calidad Premium."), ("2", "on the charging case", "Estuche de carga.")],
            lower_visual="a top-down view of the white 20 W power adapter (Image 3), the coiled white USB-C cable (Image 4) "
                         "and a plain nude-pink protective case for the charging case (Image 2)",
            lower=[("3", "on the adapter", "Cubo original de 20 W."), ("4", "on the cable", "Cable a elección."),
                   ("5", "on the pink case", "Case de regalo.")],
            price=p["precio"], cta="PIDE HOY", nota=f"{ENVIO} {DISCLOSURE_PRO3}")),
        "T2": dict(refs=[r_ear, r_cases, r_cubo, r_cable], prompt=t2(
            scene=f"{ear}, the charging case in a plain grayish-purple protective case, next to the white 20 W power "
                  "adapter (Image 3) and the coiled white USB-C cable (Image 4)",
            bg="warm stone-gray", l1="CARGA Y ESCUCHA", l2="EN UN SOLO COMBO",
            captions=[("cubo original de 20 w.", "upper left, with a line going down to the adapter"),
                      ("cable a elección.", "upper right, with an L-shaped line pointing to the cable"),
                      ("case de regalo.", "lower center, with a vertical line from the case")],
            price=p["precio"], cta="PIDE HOY", nota=f"{ENVIO} {DISCLOSURE_PRO3}")),
        "T3": dict(refs=[r_ear, r_cases, r_cubo, r_cable], prompt=t3(
            h="COMBO 4 EN 1.",
            icons=[("earbuds icon", "Audífonos", "Pro 3"), (f'the text "20 W" inside the circle', "Cubo original", "de 20 W"),
                   ("cable icon", "Cable a", "elección")],
            circles=[("Estuche de carga", "close-up of the open charging case with the earbuds"),
                     ("Cubo de 20 W", "close-up of the white power adapter"),
                     ("Case de regalo", "close-up of the plain nude-pink protective case")],
            hero=f"all four items together: {ear}, the white 20 W adapter, the coiled white cable and a plain nude-pink case",
            price=p["precio"], cta="PIDE HOY", nota=f"{ENVIO} {DISCLOSURE_PRO3}")),
        "T4": dict(refs=[r_ear, r_cases, r_cubo, r_cable], prompt=t4(
            badge="Envío gratis",
            hero=f"{ear} in a plain black protective case, with the white 20 W adapter and the coiled white cable beside it",
            title="Combo 4 en 1: audífonos, cubo, cable y case", price=p["precio"],
            sub="Envío gratis a todo el Perú", nota=DISCLOSURE_PRO3)),
        "T5": dict(refs=[r_ear, r_cases, r_cubo, r_cable], prompt=t5(
            bg="muted terracotta", center=f"{ear}, the charging case in a plain steel-blue protective case",
            top="the white 20 W power adapter (Image 3), the coiled white USB-C cable (Image 4)",
            left="a matte water bottle", right="a black notebook, a leather card holder",
            bottom="a set of keys, black sunglasses, a phone lying screen-down without logos",
            l1="TODO PARA", l2="CARGAR Y ESCUCHAR", sub="Pro 3 + cubo original de 20 W + cable + case · S/ 219",
            cta="PIDE HOY", under="ENVÍO GRATIS A TODO EL PERÚ", btn_color="terracotta", nota=DISCLOSURE_PRO3)),
    }, dict(textos=["Combo 4 en 1 a S/ 219: Pro 3 Calidad Premium, cubo original de 20 W, cable a elección y case de regalo.",
                    "Envío gratis a Lima y provincia. Eliges cable USB-C a USB-C o a Lightning y el color de tu case.",
                    "Audífonos Pro 3 Calidad Premium compatibles, no originales de Apple. Pídelo por WhatsApp."],
            titulos=["Combo 4 en 1 a S/ 219", "Con cubo original de 20 W", "Envío gratis a todo el Perú"],
            descripcion="Case de regalo"))

    p = PROD["combo-pro-3-2x1"]
    two = ("two identical sets of white in-ear wireless earbuds with short stems, each with its compact white glossy "
           "charging case (shape and color only from reference Image 1; do not reproduce the retail box, its printing "
           "or its sticker)")
    out[p["id"]] = ({
        "T1": dict(refs=[r_ear, r_cases], prompt=t1(
            h="COMBO PRO 3 · 2×1",
            upper_visual=f"{two}, both cases open side by side, in 3/4 view",
            upper=[("1", "on the earbuds", "Dos Pro 3 Calidad Premium."), ("2", "on the charging cases", "Dos estuches de carga.")],
            lower_visual="a top-down view of the two charging cases fitted in plain protective cases, one nude pink and "
                         "one steel blue (Image 2)",
            lower=[("3", "on the pink case", "Dos cases de regalo."), ("4", "on the blue case", "Un color para cada uno.")],
            price=p["precio"], cta="PIDE HOY", nota=f"{ENVIO} {DISCLOSURE_PRO3}")),
        "T2": dict(refs=[r_ear, r_cases], prompt=t2(
            scene=f"{two}, one charging case in a plain black protective case and the other in a plain lilac one, "
                  "placed symmetrically",
            bg="soft sand-beige", l1="UNO PARA TI,", l2="OTRO PARA COMPARTIR",
            captions=[("2 pro 3 calidad premium.", "upper left, with a line going down to the earbuds"),
                      ("2 cases de regalo.", "upper right, with an L-shaped line pointing to the cases"),
                      ("envío gratis a todo el perú.", "lower center, with a vertical line between both sets")],
            price=p["precio"], cta="PIDE HOY", btn_color="dark gray", nota=DISCLOSURE_PRO3)),
        "T3": dict(refs=[r_ear, r_cases], prompt=t3(
            h="COMBO 2×1.",
            icons=[("earbuds icon", "2 audífonos", "Pro 3"), ("gift icon", "2 cases", "de regalo"), ("truck icon", "Envío", "gratis")],
            circles=[("Estuche de carga", "close-up of an open charging case with earbuds"),
                     ("Case rosa nude", "close-up of the plain nude-pink case"), ("Case azul acero", "close-up of the plain steel-blue case")],
            hero=f"{two}, standing side by side, one in a plain nude-pink case and one in a plain steel-blue case",
            price=p["precio"], cta="PIDE HOY", nota=DISCLOSURE_PRO3)),
        "T4": dict(refs=[r_ear, r_cases], prompt=t4(
            badge="Para compartir", hero=f"{two}, one in a plain gray case and one in a plain lilac case",
            title="Combo 2×1: dos Pro 3 y dos cases", price=p["precio"], sub="Envío gratis a todo el Perú",
            nota=DISCLOSURE_PRO3)),
        "T5": dict(refs=[r_ear, r_cases], prompt=t5(
            bg="deep plum-gray", center=f"{two}, side by side, one in a plain nude-pink case and one in a plain steel-blue case",
            top="plain protective cases in black, gray and lilac (Image 2)", left="two matte water bottles",
            right="two small notebooks", bottom="two sets of keys, two pairs of sunglasses",
            l1="¿PARA TI", l2="Y PARA ALGUIEN MÁS?", sub="2 Pro 3 Calidad Premium + 2 cases de regalo · S/ 199",
            cta="PIDE HOY", under="ENVÍO GRATIS A TODO EL PERÚ", btn_color="plum", nota=DISCLOSURE_PRO3)),
    }, dict(textos=["Combo 2×1 a S/ 199: dos Pro 3 Calidad Premium, cada uno con su cable y su case de regalo.",
                    "Uno para ti y otro para compartir. Elige un color de case para cada uno. Envío gratis a todo el Perú.",
                    "Audífonos Pro 3 Calidad Premium compatibles, no originales de Apple. Pídelo por WhatsApp."],
            titulos=["Combo 2×1 a S/ 199", "Dos cases de regalo", "Envío gratis a todo el Perú"],
            descripcion="Elige tus colores"))

    p = PROD["combo-20w"]
    cubo = "the compact white 20 W USB-C power adapter from reference Image 1"
    r1 = (p["refs"]["cubo"], "the white 20 W USB-C power adapter (product identity)")
    r2 = (p["refs"]["cable_usbc"], "the white USB-C to USB-C cable")
    r3 = (p["refs"]["cable_lightning"], "the white USB-C to Lightning cable")
    out[p["id"]] = ({
        "T1": dict(refs=[r1, r2, r3], prompt=t1(
            h="COMBO 20 W", upper_visual=f"{cubo}, in 3/4 view showing the USB-C port",
            upper=[("1", "on the adapter", "Cubo original de 20 W."), ("2", "on the USB-C port", "Puerto USB-C.")],
            lower_visual="a top-down view of the two cable options side by side: the USB-C to USB-C cable (Image 2) and "
                         "the USB-C to Lightning cable (Image 3), each neatly coiled",
            lower=[("3", "on the first cable", "Cable USB-C a USB-C."), ("4", "on the second cable", "O cable USB-C a Lightning.")],
            price=p["precio"], cta="PIDE HOY", nota="Envío gratis a todo el Perú. Eliges un cable.")),
        "T2": dict(refs=[r1, r2, r3], prompt=t2(
            scene=f"{cubo} with both cable options coiled beside it: the USB-C to USB-C cable (Image 2) and the USB-C to "
                  "Lightning cable (Image 3)",
            bg="muted sage-green", l1="CARGA Y CONECTA", l2="EN UN COMBO",
            captions=[("cubo original de 20 w.", "upper left, with a line going down to the adapter"),
                      ("cable a elección.", "upper right, with an L-shaped line pointing to the cables"),
                      ("envío gratis.", "lower center, with a vertical line from the adapter")],
            price=p["precio"], cta="PIDE HOY")),
        "T3": dict(refs=[r1, r2, r3], prompt=t3(
            h="COMBO 20 W.",
            icons=[(f'the text "20 W" inside the circle', "Cubo original", "de 20 W"), ("cable icon", "Cable a", "elección"),
                   ("truck icon", "Envío", "gratis")],
            circles=[("Puerto USB-C", "close-up of the adapter's USB-C port"), ("Conector USB-C", "close-up of a USB-C plug"),
                     ("Conector Lightning", "close-up of a Lightning plug")],
            hero=f"{cubo} with the two coiled cable options beside it",
            price=p["precio"], cta="PIDE HOY", nota="Eliges USB-C a USB-C o a Lightning.")),
        "T4": dict(refs=[r1, r2], prompt=t4(
            badge="Envío gratis", hero=f"{cubo} with the coiled white USB-C cable (Image 2) plugged in",
            title="Combo 20 W: cubo original y cable", price=p["precio"], sub="Eliges USB-C a USB-C o a Lightning")),
        "T5": dict(refs=[r1, r2, r3, (IPHONE_USBC, "a green iPhone 17 (context prop)")], prompt=t5(
            bg="dusty navy-blue", center=f"{cubo}",
            top="the green iPhone seen from the back (Image 4), the coiled USB-C to USB-C cable (Image 2)",
            left="the coiled USB-C to Lightning cable (Image 3)", right="a black notebook, a leather card holder",
            bottom="a set of keys, black sunglasses, a ceramic coffee cup seen from above",
            l1="CARGA Y CONECTA,", l2="SIN COMPLICARTE", sub="Cubo original de 20 W + cable a elección · S/ 110",
            cta="PIDE HOY", under="ENVÍO GRATIS A TODO EL PERÚ")),
    }, dict(textos=["Combo 20 W a S/ 110: cubo original de 20 W + cable USB-C a USB-C o a Lightning, a tu elección.",
                    "Envío gratis a Lima y provincia. Dinos qué iPhone tienes y te ayudamos a elegir el cable.",
                    "Pídelo por WhatsApp: confirmamos disponibilidad, pago y entrega contigo."],
            titulos=["Combo 20 W a S/ 110", "Cubo original + cable", "Envío gratis a todo el Perú"],
            descripcion="Elige tu cable"))

    # ---------------- Servicios ----------------
    s = SERV["renueva-iphone"]
    r_old = (s["refs"]["usado"], "a used white iPhone 13, back view (render it without any logo)")
    r_new = (s["refs"]["nuevo"], "a new silver iPhone 17 Pro, front and back")
    out[s["id"]] = ({
        "T1": dict(refs=[r_old, r_new], prompt=t1(
            h="RENUEVA TU IPHONE",
            upper_visual="the used white iPhone from reference Image 1 in 3/4 rear view",
            upper=[("1", "on the phone", "Cuéntanos qué tienes."), ("2", "on the camera", "Evaluamos tu equipo.")],
            lower_visual="the new silver iPhone 17 Pro from reference Image 2 standing upright, front and back",
            lower=[("3", "on the new phone", "Te confirmamos la valoración."), ("4", "on its camera", "Coordinamos la diferencia.")],
            cta="ESCRÍBENOS",
            nota="La valoración depende de modelo, capacidad, estado, batería, IMEI y funcionamiento.")),
        "T4": dict(refs=[r_old, r_new], prompt=t4(
            badge="Renueva tu iPhone",
            hero="the used white iPhone from reference Image 1 on the left and the new silver iPhone 17 Pro from "
                 "reference Image 2 on the right, with a thin gray arrow pointing from the old one to the new one",
            title="Tu iPhone de hoy, parte del que viene",
            sub="Evaluamos batería, pantalla, IMEI y funcionamiento")),
    }, dict(textos=["Entrega tu iPhone usado como parte de pago de uno nuevo. Lo evaluamos y te decimos cuánto podemos reconocer.",
                    "Revisamos batería, pantalla, IMEI y funcionamiento. Con la valoración confirmada, coordinamos la diferencia.",
                    "Cuéntanos modelo, capacidad y estado de tu equipo por WhatsApp para empezar."],
            titulos=["Renueva tu iPhone con REVO", "Tu iPhone usado como parte de pago", "Evaluamos tu equipo"],
            descripcion="Escríbenos"))

    s = SERV["contraentrega"]
    r_ph = (s["refs"]["iphones"], "three iPhones in silver, burgundy and orange (product identity)")
    out[s["id"]] = ({
        "T1": dict(refs=[r_ph], prompt=t1(
            h="ASÍ COMPRAS EN REVO",
            upper_visual="the three iPhones from reference Image 1 standing upright in a row, rear view",
            upper=[("1", "on the first phone", "Elige tu equipo."), ("2", "on the second phone", "Revisa tu pedido y regalos.")],
            lower_visual="a top-down view of a plain kraft-paper courier package with a blank white shipping label next "
                         "to one of the iPhones lying screen-down",
            lower=[("3", "on the phone", "Pídelo por WhatsApp."), ("4", "on the package", "Lima: pagas al recibir."),
                   ("5", "on the label", "Provincia: también llegamos.")],
            cta="ESCRÍBENOS", nota="Yape · Plin · Transferencia · Efectivo")),
        "T4": dict(refs=[r_ph], prompt=t4(
            badge="Contraentrega en Lima",
            hero="the three iPhones from reference Image 1 standing upright in a row, rear view, next to a plain "
                 "kraft-paper courier package with a blank label",
            title="Pagas al recibir en Lima",
            sub="Envíos a todo el Perú · Yape, Plin, transferencia o efectivo")),
    }, dict(textos=["En Lima pagas al recibir tu pedido en el punto coordinado. A provincia también llegamos.",
                    "Paga con Yape, Plin, transferencia o efectivo. Confirmamos disponibilidad, importe y entrega por WhatsApp.",
                    "Elige en revoimport.com, revisa tu pedido y regalos, y pídelo por WhatsApp."],
            titulos=["Pagas al recibir en Lima", "Envíos a todo el Perú", "Yape, Plin o efectivo"],
            descripcion="Pide por WhatsApp"))

    s = SERV["video-garantia"]
    r_ph = (s["refs"]["iphones"], "three iPhones in silver, burgundy and orange (product identity)")
    out[s["id"]] = ({
        "T2": dict(refs=[r_ph], prompt=t2(
            scene="the three iPhones from reference Image 1 (silver, burgundy and orange) lying screen-down side by side",
            bg="slate-gray / muted green-gray", l1="LO VES", l2="ANTES DE PAGAR",
            captions=[("video de tu equipo antes de pagar.", "upper left, with a line going down to the first phone"),
                      ("nuevo y sellado.", "upper right, with an L-shaped line pointing to the third phone"),
                      ("1 año de garantía por fallas de fábrica.", "lower center, with a vertical line from the middle phone")],
            cta="ESCRÍBENOS")),
        "T4": dict(refs=[r_ph], prompt=t4(
            badge="1 año de garantía",
            hero="the three iPhones from reference Image 1 standing upright in a row, rear view",
            title="Recibe un video de tu iPhone antes de pagar",
            sub="Garantía de 1 año por fallas de fábrica")),
    }, dict(textos=["Antes de pagar, te enviamos un video de tu iPhone para que lo conozcas y resuelvas tus dudas.",
                    "iPhones nuevos y sellados, con 1 año de garantía por fallas de fábrica. Escríbenos por WhatsApp.",
                    "En Lima pagas al recibir. A provincia coordinamos pago y envío contigo."],
            titulos=["Lo ves antes de pagar", "1 año de garantía", "Nuevos y sellados"],
            descripcion="Escríbenos"))
    return out


QUOTED = re.compile(r'"([^"]+)"')


def manifest(body):
    """Textos exactos que deben aparecer en la imagen (lo que va entre comillas)."""
    seen, out = set(), []
    for t in QUOTED.findall(body):
        if re.fullmatch(r"\d+", t) or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def fingerprint(item):
    """Huella calculada por n8n (nodo "A · Extraer catálogo") sobre config.js; los servicios son fijos."""
    return item.get("huella_web") or "servicio"


def main():
    rows = []
    for pid, (tpls, meta) in build_products().items():
        item = PROD.get(pid) or SERV[pid]
        for t in meta["textos"]:
            assert len(t) <= 125, (pid, len(t), t)
        for t in meta["titulos"]:
            assert len(t) <= 40, (pid, len(t), t)
        assert len(meta["descripcion"]) <= 30, (pid, meta["descripcion"])
        for tid, spec in tpls.items():
            body = spec["prompt"]
            texts = manifest(body)
            master = body + "\n\n" + refs_block(spec["refs"]) + "\n\n" + FEED_34 + "\n\n" + RULES
            rows.append({
                "id": f"{pid}__{tid}",
                "producto_id": pid,
                "producto": item["nombre"],
                "categoria": item.get("categoria", "servicio"),
                "plantilla": tid,
                "plantilla_nombre": TEMPLATE_NAMES[tid],
                "precio": item.get("precio", ""),
                "link": item["link"],
                "refs": " | ".join(u for u, _ in spec["refs"]),
                "textos_imagen": json.dumps(texts, ensure_ascii=False),
                "prompt_master_3x4": master,
                "prompt_1x1": resize_prompt("1:1", texts),
                "prompt_9x16": resize_prompt("9:16", texts),
                "meta_texto_1": meta["textos"][0],
                "meta_texto_2": meta["textos"][1],
                "meta_texto_3": meta["textos"][2],
                "meta_titulo_1": meta["titulos"][0],
                "meta_titulo_2": meta["titulos"][1],
                "meta_titulo_3": meta["titulos"][2],
                "meta_descripcion": meta["descripcion"],
                "meta_boton": "Enviar mensaje",
                "requiere_resena_real": "sí" if tid == "T4" else "no",
                "huella": fingerprint(item),
                "estado": "pendiente",
                "version": 1,
            })
    extra_cols = ["notas_claude", "request_master", "status_url_master", "url_master", "qa_resultado", "qa_problemas",
                  "request_1x1", "status_url_1x1", "url_1x1", "request_9x16", "status_url_9x16", "url_9x16",
                  "actualizado"]
    for r in rows:
        for c in extra_cols:
            r.setdefault(c, "")

    (ROOT / "prompts" / "banners.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(ROOT / "prompts" / "banners.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md = ["# Biblioteca de banners REVO · Meta Ads", "",
          f"{len(rows)} banners master (3:4) + sus versiones 1:1 y 9:16. Generado por `scripts/build_banners.py` "
          "desde `catalogo/revo-catalogo.json` (datos de revoimport.com).", "",
          "Cada banner tiene: imágenes de referencia (todas de revoimport.com), prompt master 3:4 (Feed), "
          "prompt de redimensión 1:1 (Feed) y 9:16 (Stories/Reels), y textos para Meta.", ""]
    current = None
    for r in rows:
        if r["producto_id"] != current:
            current = r["producto_id"]
            md += ["---", "", f"## {r['producto']}  ·  {r['precio']}".rstrip(" ·"), "", f"Link: {r['link']}", "",
                   "**Textos para Meta (súbelos como opciones múltiples del mismo anuncio)**", "",
                   f"- Texto principal 1: {r['meta_texto_1']}",
                   f"- Texto principal 2: {r['meta_texto_2']}",
                   f"- Texto principal 3: {r['meta_texto_3']}",
                   f"- Títulos: {r['meta_titulo_1']} · {r['meta_titulo_2']} · {r['meta_titulo_3']}",
                   f"- Descripción: {r['meta_descripcion']}",
                   f"- Botón: {r['meta_boton']}", ""]
        md += [f"### {r['plantilla']} · {r['plantilla_nombre']}  (`{r['id']}`)", "",
               "Referencias: " + ", ".join(f"<{u.strip()}>" for u in r["refs"].split("|")), "",
               "Textos exactos en la imagen: " + " · ".join(json.loads(r["textos_imagen"])), ""]
        if r["requiere_resena_real"] == "sí":
            md += ["> Lleva una tarjeta de reseña en blanco: complétala con una reseña real de un cliente (con su "
                   "permiso) antes de publicar. No inventes reseñas ni estrellas.", ""]
        md += ["**Prompt master 3:4 (Feed)**", "", "```text", r["prompt_master_3x4"], "```", "",
               "**Redimensión 1:1 (Feed)** — usar el master generado como Image 1", "", "```text", r["prompt_1x1"], "```", "",
               "**Redimensión 9:16 (Stories y Reels)** — usar el master generado como Image 1", "", "```text",
               r["prompt_9x16"], "```", ""]
    (ROOT / "prompts" / "BANNERS.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(rows)} banners -> prompts/banners.json, banners.csv, BANNERS.md")


if __name__ == "__main__":
    main()
