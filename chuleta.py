"""Chuletas visuales: carrusel de 5-8 imágenes estilo "apuntes kawaii" (Instagram + TikTok modo foto).

Qué es: un tema concreto del temario (tipos de lesiones de la piel, prefijos de frecuencia, posiciones...) explicado en
diapositivas de colores de la marca, con titulares "burbuja", tarjetas con los términos clave resaltados, pegatinas
kawaii ORIGINALES dibujadas por IA (objetos y órganos simpáticos, nunca personas), un "¿te atreves?" con una pregunta
verificada del banco y la solución + llamada a la acción en la última imagen. Es el formato que más se GUARDA y se
COMPARTE en las cuentas de oposiciones sanitarias.

Rigor (igual que en los reels):
- Todo el contenido sale SOLO del material de la app de ese tema (fichas + preguntas con su explicación).
- El verificador (modelo "pro") contrasta frase a frase cada texto de las diapositivas y de la descripción con ese
  material; si algo no está respaldado se reescribe una vez y, si sigue sin pasar, se prueba otro tema.
- La pregunta del "¿te atreves?" es una pregunta del banco ya verificada.
- Solo temas sanitarios (bloques clínico y prefijos), no legislación (exige cita literal de la norma).

    python chuleta.py            -> genera y publica (DRY_RUN=true: solo genera; QUIZ_MOCK=1: sin IA, para probar el diseño)
"""
import datetime, json, math, os, random, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import fx
import marca
import questions as QB

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "chuletas.json")
W, H = 1080, 1350                                        # 4:5, el formato vertical de carrusel de Instagram
FONTS = os.path.join(HERE, "fonts")
F_BUB = os.path.join(FONTS, "Fredoka-700.ttf")           # titulares "burbuja"
F_HEAD = os.path.join(FONTS, "Fredoka-600.ttf")
F_BODY = os.path.join(FONTS, "Nunito-700.ttf")
F_BOLD = os.path.join(FONTS, "Nunito-900.ttf")

# paleta de la marca en versión "apuntes": fondo menta, teal, dorado, tinta oscura y pasteles derivados
INK = (24, 52, 58); TEAL = fx.TEAL; TEAL_D = fx.TEAL_D; AMBER = fx.AMBER; WHITE = (255, 255, 255)
BG = (226, 246, 242); DOT = (26, 158, 143, 30)
CARD_FILLS = [(255, 255, 255), (255, 247, 214), (214, 242, 236), (255, 236, 224)]
TITLE_FILLS = [TEAL, AMBER, (140, 214, 203), (255, 190, 160)]
TOPIC_BLOQUES = ("clinico", "prefijos")
MOCK = os.environ.get("QUIZ_MOCK") == "1"


def F(path, size):
    return fx.font(path, int(size))


# ------------------------------------------------------------------ 1. tema y material
def log():
    try:
        return json.load(open(LOG))
    except Exception:
        return []


def topics():
    """Temas con material suficiente para una chuleta (generales primero: Aragón nunca entra aquí)."""
    QB.fichas("x", 1)                                     # carga las fichas
    out = []
    for t, fs in QB._F.items():
        tema, bloque = QB.tema_de(t)
        if bloque in TOPIC_BLOQUES and t not in QB.REGIONAL_TOPICS and len(fs) >= 8:
            out.append(t)
    return out


def pick_topic(seed, skip=()):
    """El tema que lleva más tiempo sin chuleta (los nunca usados primero), al azar entre empates."""
    last = {}
    for i, e in enumerate(log()):
        last[e.get("topic")] = i
    ts = [t for t in topics() if t not in skip]
    rng = random.Random(seed); rng.shuffle(ts)
    ts.sort(key=lambda t: last.get(t, -1))
    return ts[0] if ts else None


def material(topic):
    """Fichas y preguntas (con su explicación) del tema: lo único que la chuleta puede afirmar."""
    tema, _ = QB.tema_de(topic)
    QB.fichas("x", 1)                                     # carga las fichas
    fs = QB._F.get(topic, [])[:80]
    v = QB.verif()
    qs = [q for q in QB.load() if q["topic"] == topic and q["origen"] == "webapp"]
    qs.sort(key=lambda q: not QB.publishable(q, v))
    lines = [f"- {f['q']} -> {f['a']}" for f in fs]
    lines += [f"- Pregunta: {q['pregunta']} Respuesta correcta: {q['opciones'][q['correcta']]}. {q['explicacion']}"
              for q in qs[:25]]
    return tema, "\n".join(lines)


def used_subtemas(topic):
    return [e.get("subtema") for e in log() if e.get("topic") == topic and e.get("subtema")]


def quiz_question(topic, seed):
    """Una pregunta YA VERIFICADA del mismo tema para la diapositiva "¿Te atreves?" (o None)."""
    v = QB.verif()
    used = {x["id"] for x in QB.used()} | {e.get("quiz_id") for e in log()}
    qs = [q for q in QB.load() if q["topic"] == topic and QB.publishable(q, v) and QB.fits(q)]
    if MOCK and not qs:
        qs = [q for q in QB.load() if q["topic"] == topic and QB.fits(q)]
    qs.sort(key=lambda q: q["id"] in used)
    return QB.prepare(qs[0], seed) if qs else None


# ------------------------------------------------------------------ 2. guion (IA) y verificación
ROLE = """Eres la creadora de las CHULETAS VISUALES de Aprueba TCAE (apruebatcae.com), una web app de tests para las
oposiciones de TCAE (Técnico en Cuidados Auxiliares de Enfermería) de toda España. Haces carruseles de Instagram tipo
"apuntes bonitos": claros, ordenados, fáciles de memorizar y que dan ganas de GUARDAR y ENVIAR a la compi de oposición.
Escribes en español de España, cercano y profesional, nada infantil, sin promesas ("esto cae seguro") ni estadísticas."""

SCHEMA = """{
 "subtema": str (el subtema concreto, 2-7 palabras),
 "titulo_lineas": [str, ...] (2-4 líneas MUY cortas del titular de portada, máx. 12 caracteres cada una, p. ej. ["TIPOS", "DE", "LESIONES"] o ["NO TE", "LÍES CON", "LAS UPP"]),
 "subtitulo": str (8-18 palabras: qué vas a aprender / por qué te sirve en el test),
 "pegatina_portada": str (en inglés: un objeto u órgano simpático relacionado con el tema, sin personas, p. ej. "a smiling heart with a stethoscope"),
 "diapositivas": [ (3-5 diapositivas)
   {"titulo": str (1-4 palabras),
    "items": [ {"termino": str (1-5 palabras), "texto": str (6-24 palabras; marca 1-2 palabras clave con **asteriscos**)} ] (2-4 items),
    "truco": str o "" (opcional, 6-16 palabras: regla para memorizar o diferencia clave, SOLO con datos del material),
    "pegatina": str (en inglés: objeto u órgano simpático para esa diapositiva, sin personas)} ],
 "caption_gancho": str (máx. 14 palabras, 1-2 emojis, primera línea de la descripción: una duda típica del opositor),
 "caption_intro": str (25-60 palabras: por qué este tema confunde en los test y qué resuelve la chuleta),
 "caption_puntos": [str] (3-5 líneas cortas "TÉRMINO → idea clave", cada una empieza con un emoji de color 💚💛🩵🧡),
 "reto": str (máx. 25 palabras: reto para comentar, p. ej. "sin mirar, ¿sabrías decir qué es una pápula?")
}"""


def write(topic, tema, mat, notes=None, avoid=()):
    import gemini
    prompt = f"""{ROLE}

TEMA: {tema}
MATERIAL DE LA APP (lo ÚNICO que puedes afirmar; no añadas ningún dato, cifra, clasificación ni ejemplo que no esté aquí):
{mat}

Elige UN subtema concreto de este material que funcione muy bien como chuleta visual (una clasificación, tipos, diferencias
entre términos que se confunden, siglas, fases, prefijos...). {("Evita estos subtemas ya publicados: " + "; ".join(avoid)) if avoid else ""}
Haz una chuleta de 3-5 diapositivas: cada diapositiva agrupa 2-4 términos con su explicación muy breve y clara.
Reglas: cada frase debe poder comprobarse en el material; nada de "siempre/nunca" si el material no lo dice; sin
mencionar comunidades autónomas; sin emojis dentro de las diapositivas (solo en la descripción); los términos tal y como
aparecen en el material. Escribe SOLO lo que se lee, sin indicaciones de diseño.
{("CORRIGE estos problemas que encontró el verificador en tu versión anterior: " + json.dumps(notes, ensure_ascii=False)) if notes else ""}
Devuelve JSON exactamente con esta forma:
{SCHEMA}"""
    return gemini.ask(prompt, 0.7)


def _wc(s):
    return len(str(s or "").split())


def clean(c):
    """Valida forma y longitudes (lo que no cabe en una diapositiva bonita se rechaza)."""
    lines = [str(x).strip().upper() for x in (c.get("titulo_lineas") or []) if str(x).strip()]
    if not 1 <= len(lines) <= 4 or any(len(x) > 14 for x in lines):
        raise ValueError("titular de portada no válido")
    slides = []
    for s in (c.get("diapositivas") or [])[:5]:
        items = [{"termino": str(i.get("termino", "")).strip(), "texto": re.sub(r"\s+", " ", str(i.get("texto", ""))).strip()}
                 for i in (s.get("items") or [])[:4]]
        items = [i for i in items if 1 <= _wc(i["termino"]) <= 6 and 4 <= _wc(i["texto"]) <= 28]
        if len(items) >= 2 and 1 <= _wc(s.get("titulo")) <= 5:
            truco = re.sub(r"\s+", " ", str(s.get("truco") or "")).strip()
            slides.append({"titulo": str(s["titulo"]).strip(), "items": items,
                           "truco": truco if 4 <= _wc(truco) <= 20 else "", "pegatina": str(s.get("pegatina") or "")[:120]})
    if len(slides) < 3:
        raise ValueError("menos de 3 diapositivas válidas")
    pts = [str(p).strip() for p in (c.get("caption_puntos") or []) if 2 <= _wc(p) <= 16][:5]
    out = {"subtema": str(c.get("subtema") or "").strip()[:60], "titulo_lineas": lines,
           "subtitulo": re.sub(r"\s+", " ", str(c.get("subtitulo") or "")).strip(),
           "pegatina_portada": str(c.get("pegatina_portada") or "")[:120], "diapositivas": slides,
           "caption_gancho": str(c.get("caption_gancho") or "").strip(), "caption_intro": str(c.get("caption_intro") or "").strip(),
           "caption_puntos": pts, "reto": str(c.get("reto") or "").strip()}
    if not 5 <= _wc(out["subtitulo"]) <= 22 or not 3 <= _wc(out["caption_gancho"]) <= 18 or not _wc(out["reto"]) <= 30:
        raise ValueError("subtítulo, gancho o reto fuera de medida")
    import writer
    vals = out["titulo_lineas"] + [out["subtitulo"], out["caption_gancho"], out["caption_intro"], out["reto"]] + \
        out["caption_puntos"] + [x for s in slides for x in [s["titulo"], s["truco"]] + [i["termino"] for i in s["items"]]
                                 + [i["texto"] for i in s["items"]]]
    if any(writer.has_meta(v) for v in vals):
        raise ValueError("lleva indicaciones de diseño o de tono")
    return out


def verify(c, tema, mat):
    import gemini, verifier
    texts = {"titular": " ".join(c["titulo_lineas"]), "subtitulo": c["subtitulo"],
             "diapositivas": [{"titulo": s["titulo"], "items": s["items"], "truco": s["truco"]} for s in c["diapositivas"]],
             "caption": [c["caption_gancho"], c["caption_intro"]] + c["caption_puntos"] + [c["reto"]]}
    try:
        res = gemini.ask(f"""{verifier.ROLE}
Revisas una CHULETA VISUAL (carrusel de Instagram) del tema "{tema}".
MATERIAL DE REFERENCIA (lo único que vale como verdad):
{mat}

TEXTOS DE LA CHULETA:
{json.dumps(texts, ensure_ascii=False, indent=1)}

Comprueba frase a frase: ¿todo lo que afirman está respaldado por el material? Es un problema cualquier dato, cifra,
ejemplo, clasificación o generalización ("siempre", "nunca", "todos") que no esté en el material, asociar una definición
al término equivocado, o mezclar conceptos. También prometer cosas o el tono infantil.
Devuelve JSON: {{"ok": bool, "problemas": [{{"frase": str, "motivo": str}}]}}""", 0.1, careful=True)
    except Exception as e:
        return False, [{"frase": "-", "motivo": f"verificador no disponible: {str(e)[:150]}"}]
    probs = res.get("problemas") or []
    return bool(res.get("ok")) and not probs, probs


def content_for(topic, seed):
    tema, mat = material(topic)
    if MOCK:
        return tema, mock_content(topic, tema)
    notes = None
    for attempt in range(2):
        try:
            c = clean(write(topic, tema, mat, notes, used_subtemas(topic)))
        except Exception as e:
            print(f"chuleta: guion no válido ({str(e)[:150]})", flush=True); notes = [str(e)[:150]]; continue
        ok, probs = verify(c, tema, mat)
        if ok:
            print(f"chuleta: verificada ({c['subtema']})", flush=True)
            return tema, c
        notes = probs
        print("chuleta: el verificador pide cambios:", json.dumps(probs, ensure_ascii=False)[:400], flush=True)
    raise RuntimeError(f"no hay chuleta verificada para {tema}")


def mock_content(topic, tema):
    fs = QB._F.get(topic, [])[:9]
    sl = []
    for k in range(3):
        its = [{"termino": f["q"].split("?")[0].replace("¿", "")[:30].split(" y ")[0], "texto": " ".join(f["a"].split()[:20])}
               for f in fs[k * 3:k * 3 + 3]]
        its[0]["texto"] = "**" + its[0]["texto"].split()[0] + "** " + " ".join(its[0]["texto"].split()[1:])
        sl.append({"titulo": ["Lo básico", "No los confundas", "Repaso final"][k], "items": its,
                   "truco": "Fíjate en la raíz de la palabra para deducir el significado." if k == 1 else "", "pegatina": ""})
    return {"subtema": tema, "titulo_lineas": ["CHULETA", "DE", tema.split()[-1].upper()[:12]],
            "subtitulo": "Lo que más se confunde en los test, explicado en 1 minuto para que no falles.",
            "pegatina_portada": "", "diapositivas": sl, "caption_gancho": "🧠 ¿Te lías con este tema?",
            "caption_intro": "Texto de prueba.", "caption_puntos": ["💚 Uno → idea", "💛 Dos → idea"], "reto": "¿Lo sabías?"}


# ------------------------------------------------------------------ 3. pegatinas kawaii (IA) con borde blanco
STICKER = ("Cute kawaii sticker illustration of {thing}. Thick dark teal-gray outline, flat soft pastel colours (mint green, "
           "teal, warm butter yellow, soft peach), simple rounded shapes, tiny happy face with blush cheeks if it suits the "
           "object. One single object, centered, isolated on a pure plain white background, nothing else. No text, no letters, "
           "no numbers, no logos, no people, no humans, no hands, no blood, no needles piercing skin.")


def cut_out(img):
    """Quita el fondo blanco (relleno desde los bordes, así el blanco DENTRO del dibujo se conserva) y añade el
    borde blanco grueso y la sombra de pegatina."""
    im = img.convert("RGB"); w, h = im.size
    key = (255, 0, 255)
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if min(im.getpixel((x, y))) > 225:
            ImageDraw.floodfill(im, (x, y), key, thresh=40)
    import numpy as np
    a = np.array(im)
    mask = ~((a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255))
    alpha = Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.MinFilter(3))
    rgba = img.convert("RGBA"); rgba.putalpha(alpha)
    bb = alpha.getbbox()
    if not bb or (bb[2] - bb[0]) * (bb[3] - bb[1]) < 0.05 * w * h:
        raise ValueError("pegatina vacía")
    rgba = rgba.crop(bb); al = rgba.getchannel("A")
    pad = 40
    out = Image.new("RGBA", (rgba.width + 2 * pad, rgba.height + 2 * pad), (0, 0, 0, 0))
    big = Image.new("L", out.size, 0); big.paste(al, (pad, pad))
    border = big.filter(ImageFilter.MaxFilter(23)).filter(ImageFilter.GaussianBlur(1.2))
    shadow = Image.new("RGBA", out.size, (10, 60, 55, 0)); shadow.putalpha(border.point(lambda v: v * 70 // 255))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); sh.alpha_composite(shadow, (6, 12)); sh = sh.filter(ImageFilter.GaussianBlur(6))
    white = Image.new("RGBA", out.size, (255, 255, 255, 0)); white.putalpha(border)
    out.alpha_composite(sh); out.alpha_composite(white); out.alpha_composite(rgba, (pad, pad))
    return out


def sticker_ok(img, thing):
    """Revisión rápida: sin texto, sin personas, sin nada raro."""
    import base64, io, gemini
    b = io.BytesIO(); t = img.convert("RGB"); t.thumbnail((512, 512)); t.save(b, "JPEG", quality=85)
    try:
        r = gemini.ask([{"text": f"Imagen pedida: kawaii sticker of {thing}. ¿Tiene texto, letras o números? ¿Aparece alguna "
                                 "persona o parte del cuerpo humano realista? ¿Hay algo desagradable, sangre o un error "
                                 "sanitario evidente? ¿Es UN objeto simpático sobre fondo blanco liso? "
                                 'Devuelve JSON: {"ok": bool, "motivo": str}'},
                        {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b.getvalue()).decode()}}], 0.1)
        return bool(r.get("ok")), r.get("motivo")
    except Exception as e:
        return False, str(e)[:100]


def sticker(thing, seed=0):
    """Pegatina original por IA (2 intentos); si no sale bien, una pegatina dibujada en código."""
    if thing and not MOCK and os.environ.get("GEMINI_API_KEY"):
        import gemini
        for k in range(2):
            try:
                img = gemini.image(STICKER.format(thing=thing), aspect="1:1")
                ok, why = sticker_ok(img, thing)
                if ok:
                    return cut_out(img)
                print(f"pegatina rechazada ({why})", flush=True)
            except Exception as e:
                print("pegatina: fallo:", str(e)[:150], flush=True)
    return drawn_sticker(seed)


def drawn_sticker(seed=0):
    """Pegatina de respaldo hecha en código: corazón, estrella o gota con carita."""
    kind = ["heart", "star", "drop"][seed % 3]
    S = 520; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(255, 170, 160), AMBER, (140, 214, 203)][seed % 3]
    if kind == "heart":
        pts = [(S / 2 + 200 * (16 * math.sin(t) ** 3) / 17, S / 2 - 10 - 200 * (13 * math.cos(t) - 5 * math.cos(2 * t)
               - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17) for t in [i * 2 * math.pi / 120 for i in range(120)]]
    elif kind == "star":
        pts = [(S / 2 + (210 if i % 2 == 0 else 105) * math.cos(-math.pi / 2 + i * math.pi / 5),
                S / 2 + 15 + (210 if i % 2 == 0 else 105) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    else:
        pts = [(S / 2 + 170 * math.cos(t) * (1 if math.sin(t) > 0 else 1 - 0.0 * math.sin(t)),
                S / 2 + 60 + (170 * math.sin(t) if math.sin(t) > 0 else 240 * math.sin(t) * (1 - abs(math.cos(t)) ** 0.6)))
               for t in [i * 2 * math.pi / 120 for i in range(120)]]
    d.polygon(pts, fill=col, outline=INK, width=12)
    cx, cy = S / 2, S / 2 + 20
    for ex in (-55, 55):
        d.ellipse([cx + ex - 13, cy - 30, cx + ex + 13, cy], fill=INK)
    d.arc([cx - 30, cy - 10, cx + 30, cy + 30], 20, 160, fill=INK, width=9)
    for ex in (-95, 95):
        d.ellipse([cx + ex - 24, cy + 2, cx + ex + 24, cy + 26], fill=(255, 130, 130, 140))
    bg = Image.new("RGB", (S, S), WHITE); bg.paste(im, (0, 0), im)
    return cut_out(bg)


# ------------------------------------------------------------------ 4. dibujo de las diapositivas
def background(seed):
    im = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(im, "RGBA")
    for y in range(30, H, 44):
        for x in range(30 + (22 if (y // 44) % 2 else 0), W, 44):
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=DOT)
    rng = random.Random(seed)
    for _ in range(3):                                         # manchas suaves de color
        bx, by, r = rng.randint(-100, W), rng.randint(-100, H), rng.randint(180, 320)
        blob = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(blob).ellipse([bx - r, by - r, bx + r, by + r], fill=rng.choice([(255, 247, 214, 150), (200, 238, 230, 160)]))
        im.alpha_composite(blob.filter(ImageFilter.GaussianBlur(60)))
    return im


def sparkle(d, cx, cy, r, col=AMBER):
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.32
        a = -math.pi / 2 + i * math.pi / 4
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col, outline=INK, width=max(3, int(r / 9)))


def bubble_line(text, size, fill, maxw):
    """Una línea de titular burbuja: relleno de color, contorno oscuro, borde blanco grueso y sombra."""
    while size > 40 and F(F_BUB, size).getlength(text) + size * 0.4 > maxw:
        size -= 4
    f = F(F_BUB, size)
    ow, iw = max(8, int(size * 0.13)), max(4, int(size * 0.055))
    bb = f.getbbox(text, stroke_width=ow)
    w_, h_ = bb[2] - bb[0] + 2 * ow + 20, bb[3] - bb[1] + 2 * ow + 30
    im = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    o = (ow + 10 - bb[0], ow + 8 - bb[1])
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((o[0] + 4, o[1] + size * 0.06), text, font=f, fill=(15, 122, 109, 120), stroke_width=ow,
                            stroke_fill=(15, 122, 109, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2)))
    d = ImageDraw.Draw(im)
    d.text(o, text, font=f, fill=WHITE, stroke_width=ow, stroke_fill=WHITE)
    d.text(o, text, font=f, fill=fill, stroke_width=iw, stroke_fill=INK)
    return im


def bubble_title(lines, size, maxw, fills=None, gap=-0.12):
    fills = fills or TITLE_FILLS
    ims = [bubble_line(l, size, fills[i % len(fills)], maxw) for i, l in enumerate(lines)]
    h = sum(i.height for i in ims) + int(gap * size) * (len(ims) - 1)
    out = Image.new("RGBA", (max(i.width for i in ims), max(1, h)), (0, 0, 0, 0)); y = 0
    for i in ims:
        out.alpha_composite(i, ((out.width - i.width) // 2, y)); y += i.height + int(gap * size)
    return out


def _rich_tokens(text):
    """'texto con **clave**' -> [(palabra, negrita)]"""
    out, bold = [], False
    for part in re.split(r"(\*\*)", text):
        if part == "**":
            bold = not bold; continue
        for w in part.split():
            if out and re.fullmatch(r"[.,;:!?)»…]+", w):          # la puntuación se pega a la palabra anterior
                out[-1] = (out[-1][0] + w, out[-1][1])
            else:
                out.append((w, bold))
    return out


def rich(text, size, maxw, color=INK, hi=TEAL_D, path=F_BODY, bold_path=F_BOLD, align="left", gap=1.28, draw_on=None, xy=(0, 0)):
    """Texto con palabras clave en negrita de color y subrayado de rotulador. Devuelve la altura (y dibuja si draw_on)."""
    toks = _rich_tokens(text)
    fn, fb = F(path, size), F(bold_path, size)
    sp = fn.getlength(" ")
    lines, cur, x = [], [], 0.0
    for w, b in toks:
        wl = (fb if b else fn).getlength(w)
        if cur and x + wl > maxw:
            lines.append((cur, x - sp)); cur, x = [], 0.0
        cur.append((w, b, x)); x += wl + sp
    if cur:
        lines.append((cur, x - sp))
    lh = int(size * gap)
    if draw_on is not None:
        d = ImageDraw.Draw(draw_on, "RGBA")
        for li, (ws, lw) in enumerate(lines):
            ox = xy[0] + ((maxw - lw) / 2 if align == "center" else 0)
            y = xy[1] + li * lh
            for w, b, x in ws:
                if b:
                    wl = fb.getlength(w)
                    d.rounded_rectangle([ox + x - 4, y + size * 0.55, ox + x + wl + 4, y + size * 1.08], 8,
                                        fill=(232, 201, 61, 150))
                d.text((ox + x, y), w, font=fb if b else fn, fill=hi if b else color)
    return lh * len(lines)


def header(im, n, total):
    d = ImageDraw.Draw(im)
    p = fx.pill(marca.WEB, 30, WHITE, TEAL_D, padx=22, pady=9, path=fx.F800, outline=None)
    im.alpha_composite(p, (40, 36))
    if total:
        q = fx.pill(f"{n}/{total}", 30, INK, WHITE, padx=22, pady=9, path=fx.F800)
        im.alpha_composite(q, (W - 40 - q.width, 36))


def footer_handle(im):
    f = F(F_HEAD, 30); t = marca.HANDLE if hasattr(marca, "HANDLE") else "@apruebatcae"
    ImageDraw.Draw(im).text((W / 2 - f.getlength(t) / 2, H - 58), t, font=f, fill=TEAL_D)


def place_sticker(im, st, cx, cy, size, rot=0):
    if st is None:
        return
    s = st.copy(); s.thumbnail((size, size), Image.LANCZOS)
    if rot:
        s = s.rotate(rot, Image.BICUBIC, expand=True)
    im.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))


def slide_cover(c, st, total, seed):
    im = background(seed); d = ImageDraw.Draw(im)
    header(im, 1, 0)
    tag = fx.pill("CHULETA TCAE", 40, AMBER, INK, padx=30, pady=12, path=F_HEAD)
    im.alpha_composite(tag, ((W - tag.width) // 2, 130))
    n = len(c["titulo_lineas"])
    title = bubble_title(c["titulo_lineas"], {1: 250, 2: 220, 3: 190, 4: 160}[n], 980)
    y = 215
    im.alpha_composite(title, ((W - title.width) // 2, y)); y += title.height + 10
    hsub = rich(c["subtitulo"], 50, 900, path=F_BOLD, align="center")
    rich(c["subtitulo"], 50, 900, path=F_BOLD, align="center", draw_on=im, xy=((W - 900) / 2, y)); y += hsub
    room = H - 70 - y
    for (x_, y_, r) in [(110, 250, 34), (970, 300, 40), (90, 560, 22), (990, 640, 26)]:
        sparkle(d, x_, y_, r)
    place_sticker(im, st, W - 260, y + room / 2 + 10, min(470, max(240, room)), rot=-6)
    sw = fx.pill("DESLIZA  >>", 40, TEAL, WHITE, padx=34, pady=14, path=F_HEAD)
    im.alpha_composite(sw, (70, int(min(H - 160, y + room / 2))))
    footer_handle(im)
    return im


def slide_content(s, st, n, total, seed):
    im = background(f"{seed}-{n}"); header(im, n, total)
    words = s["titulo"].upper().split()
    lines = [" ".join(words)] if len(" ".join(words)) <= 13 else [" ".join(words[:len(words) // 2 + len(words) % 2]),
                                                                      " ".join(words[len(words) // 2 + len(words) % 2:])]
    for scale in (1.35, 1.25, 1.15, 1.07, 1.0, 0.92, 0.85, 0.78, 0.72, 0.66):
        tsize, term, body = 130 * min(1.1, scale), 54 * scale, 42 * scale
        title = bubble_title(lines, tsize, 900, fills=[TITLE_FILLS[n % len(TITLE_FILLS)], TITLE_FILLS[(n + 1) % len(TITLE_FILLS)]])
        y0 = 110 + title.height + 6
        cards = []
        for it in s["items"]:
            ht = rich(it["termino"], term, 800, path=F_HEAD, bold_path=F_HEAD, gap=1.12)
            hb = rich(it["texto"], body, 850)
            cards.append(int(ht + hb + 60))
        tr_h = (rich(s["truco"], body * 0.95, 760, path=F_BOLD) + int(term) + 70) if s["truco"] else 0
        total_h = y0 + sum(cards) + 26 * len(cards) + tr_h + 50
        if total_h + (200 if (st is not None and scale > 1.0) else 0) <= H - 40:
            break
    im.alpha_composite(title, ((W - title.width) // 2, 100))
    d = ImageDraw.Draw(im, "RGBA"); y = y0
    for k, (it, ch) in enumerate(zip(s["items"], cards)):
        fill = CARD_FILLS[k % len(CARD_FILLS)]
        d.rounded_rectangle([60 + 6, y + 8, W - 60 + 6, y + ch + 8], 34, fill=(15, 122, 109, 60))
        d.rounded_rectangle([60, y, W - 60, y + ch], 34, fill=fill, outline=INK, width=5)
        d.ellipse([92, y + 22 + term * 0.38, 116, y + 46 + term * 0.38], fill=TITLE_FILLS[k % len(TITLE_FILLS)], outline=INK, width=4)
        ht = rich(it["termino"], term, 800, color=TEAL_D, path=F_HEAD, bold_path=F_HEAD, gap=1.12, draw_on=im, xy=(134, y + 22))
        rich(it["texto"], body, 850, draw_on=im, xy=(134, y + 34 + ht))
        y += ch + 26
    if s["truco"]:
        note = Image.new("RGBA", (860, tr_h), (0, 0, 0, 0)); nd = ImageDraw.Draw(note)
        nd.rounded_rectangle([0, 0, 859, tr_h - 1], 26, fill=(255, 236, 160), outline=INK, width=5)
        nd.text((36, 22), "TRUCO", font=F(F_BUB, term), fill=INK)
        rich(s["truco"], body * 0.95, 760, path=F_BOLD, draw_on=note, xy=(36, 30 + term * 1.1))
        note = note.rotate(-1.5, Image.BICUBIC, expand=True)
        im.alpha_composite(note, ((W - note.width) // 2, int(y)))
        y += note.height
    free = H - 50 - y
    if free > 200:
        place_sticker(im, st, W - 190, y + free / 2, min(300, free), rot=8)
    else:                                                  # sin hueco: pegatina pequeña sobre la esquina de la última tarjeta
        place_sticker(im, st, W - 110, min(H - 110, y - 40), 170, rot=10)
    sparkle(ImageDraw.Draw(im), 70, 150, 26)
    return im


def slide_quiz(P, n, total, seed):
    im = background(f"{seed}-quiz"); header(im, n, total)
    for sc in (1.0, 0.92, 0.85, 0.78, 0.7, 0.62):
        title = bubble_title(["¿TE", "ATREVES?"], 150 * sc, 900, fills=[AMBER, TEAL])
        qs, os_ = 48 * sc, 42 * sc
        qh = rich(P["pregunta"], qs, 860, path=F_BOLD)
        ohs = [max(96 * sc, rich(o, os_, 780) + 44 * sc) for o in P["op"]]
        need = 110 + title.height + 10 + qh + 100 + sum(ohs) + 18 * 4 + 110
        if need <= H - 40:
            break
    im.alpha_composite(title, ((W - title.width) // 2, 100))
    d = ImageDraw.Draw(im, "RGBA"); y = 110 + title.height + 10
    d.rounded_rectangle([60, y, W - 60, y + qh + 70], 34, fill=WHITE, outline=INK, width=5)
    rich(P["pregunta"], qs, 860, path=F_BOLD, draw_on=im, xy=(110, y + 35)); y += qh + 100
    for k, (o, h_) in enumerate(zip(P["op"], ohs)):
        oh = rich(o, os_, 780)
        d.rounded_rectangle([60, y, W - 60, y + h_], 30, fill=CARD_FILLS[(k + 1) % 4], outline=INK, width=4)
        r = 34 * min(1, sc + 0.1)
        d.ellipse([118 - r, y + h_ / 2 - r, 118 + r, y + h_ / 2 + r], fill=TEAL, outline=INK, width=4)
        f = F(F_BUB, 44 * min(1, sc + 0.1)); L = QB.LETTERS[k]
        bb = f.getbbox(L)
        d.text((118 - (bb[0] + bb[2]) / 2, y + h_ / 2 - (bb[1] + bb[3]) / 2), L, font=f, fill=WHITE)
        rich(o, os_, 780, draw_on=im, xy=(180, y + (h_ - oh) / 2 + 2)); y += h_ + 18
    p = fx.pill("LA SOLUCIÓN, EN LA ÚLTIMA IMAGEN  >>", 36, INK, WHITE, padx=30, pady=14, path=F_HEAD)
    im.alpha_composite(p, ((W - p.width) // 2, int(min(H - p.height - 30, y + 14))))
    return im


def slide_cta(P, n, total, seed, st):
    im = background(f"{seed}-cta"); header(im, n, total)
    d = ImageDraw.Draw(im, "RGBA"); y = 120
    if P:
        title = bubble_title(["SOLUCIÓN"], 140, 900, fills=[TEAL])
        im.alpha_composite(title, ((W - title.width) // 2, y)); y += title.height + 10
        txt = f"**{P['letra']}.** {P['op'][P['ok']]}"
        ex = P.get("explicacion") or ""
        ex = ex if len(ex.split()) <= 38 else ""
        h1 = rich(txt, 50, 860, path=F_BOLD); h2 = rich(ex, 38, 860) if ex else 0
        d.rounded_rectangle([60, y, W - 60, y + h1 + h2 + 80], 34, fill=(214, 242, 236), outline=INK, width=5)
        rich(txt, 50, 860, path=F_BOLD, draw_on=im, xy=(110, y + 34))
        if ex:
            rich(ex, 38, 860, draw_on=im, xy=(110, y + 44 + h1))
        y += h1 + h2 + 120
    else:
        title = bubble_title(["¿TE", "SIRVE?"], 170, 900, fills=[AMBER, TEAL])
        im.alpha_composite(title, ((W - title.width) // 2, y)); y += title.height + 40
    rows = [("GUÁRDALA", "para tus repasos antes del examen"), ("ENVÍASELA", "a tu compi de oposición"),
            ("PRACTICA GRATIS", f"con {marca.PREGUNTAS_FRASE} tipo test")]
    for k, (a, b) in enumerate(rows):
        d.rounded_rectangle([60, y, W - 60, y + 112], 30, fill=CARD_FILLS[k % 4], outline=INK, width=4)
        d.ellipse([86, y + 26, 146, y + 86], fill=TITLE_FILLS[k], outline=INK, width=4)
        f = F(F_BUB, 40); d.text((116 - f.getlength(str(k + 1)) / 2, y + 28), str(k + 1), font=f, fill=INK)
        d.text((176, y + 14), a, font=F(F_HEAD, 44), fill=TEAL_D)
        d.text((176, y + 64), b, font=F(F_BODY, 34), fill=INK)
        y += 130
    web = bubble_line(marca.WEB, 96, AMBER, 980)
    im.alpha_composite(web, ((W - web.width) // 2, int(min(H - web.height - 70, y + 10))))
    if H - 70 - (y + web.height) > 220:
        place_sticker(im, st, W / 2, (y + web.height + H - 70) / 2 + 20, 230)
    footer_handle(im)
    return im


def render(c, P, stickers, out_dir, seed):
    os.makedirs(out_dir, exist_ok=True)
    total = 1 + len(c["diapositivas"]) + (1 if P else 0) + 1
    slides = [slide_cover(c, stickers[0], total, seed)]
    for i, s in enumerate(c["diapositivas"]):
        slides.append(slide_content(s, stickers[1 + i] if 1 + i < len(stickers) else None, i + 2, total, seed))
    if P:
        slides.append(slide_quiz(P, len(slides) + 1, total, seed))
    slides.append(slide_cta(P, len(slides) + 1, total, seed, stickers[0]))
    paths = []
    for i, s in enumerate(slides):
        p = os.path.join(out_dir, f"chuleta_{i + 1:02d}.jpg")
        s.convert("RGB").save(p, "JPEG", quality=92, optimize=True)        # Instagram solo acepta JPEG por URL
        paths.append(p)
    return paths


# ------------------------------------------------------------------ 5. descripción
TAGS = ["#TCAE", "#oposicionesTCAE", "#auxiliardeenfermeria", "#apuntesTCAE", "#oposiciones"]


def caption(c, P):
    pts = "\n".join(c["caption_puntos"])
    quiz = f"\n\n🎯 Y en la penúltima imagen, una pregunta tipo test del tema: ¿la aciertas? Dime tu letra en comentarios." if P else ""
    return (f"{c['caption_gancho']}\n\n{c['caption_intro']}\n\n{pts}{quiz}\n\n"
            f"💬 {c['reto']}\n\n"
            f"📌 GUÁRDALA para tus repasos.\n📤 ENVÍASELA a tu compi de oposición.\n\n"
            f"Practica gratis con {marca.PREGUNTAS_FRASE} tipo test, simulacros y flashcards en apruebatcae.com (link en la bio).\n\n"
            + " ".join(TAGS))


# ------------------------------------------------------------------ 6. publicar
def public_urls(paths):
    """URLs públicas de las imágenes (Instagram las descarga desde ahí): Zernio o, si no, el propio repositorio público."""
    if os.environ.get("ZERNIO_API_KEY"):
        import publish_zernio as Z
        return [Z.upload(p) for p in paths]
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("sin ZERNIO_API_KEY ni repositorio público para alojar las imágenes")
    import subprocess, sincronizar, time
    sincronizar.main(f"Chuleta {datetime.date.today()} (imágenes)", paths)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    time.sleep(5)
    return [f"https://raw.githubusercontent.com/{repo}/{sha}/{os.path.relpath(p, HERE)}" for p in paths]


def ig_carousel(urls, cap):
    import requests, publish_ig as IG
    token = os.environ["IG_TOKEN"]; uid = IG.whoami(token)["user_id"]
    kids = []
    for i, u in enumerate(urls[:10]):
        cid = IG._check(requests.post(f"{IG.GRAPH}/{uid}/media", data={"image_url": u, "is_carousel_item": "true",
                                                                       "access_token": token}, timeout=120))["id"]
        kids.append(cid)
    for i, cid in enumerate(kids):
        IG._wait(cid, token, f"imagen {i + 1}")
    cid = IG._check(requests.post(f"{IG.GRAPH}/{uid}/media", data={"media_type": "CAROUSEL", "children": ",".join(kids),
                                                                   "caption": cap, "access_token": token}, timeout=120))["id"]
    IG._wait(cid, token, "carrusel")
    p = IG._check(requests.post(f"{IG.GRAPH}/{uid}/media_publish", data={"creation_id": cid, "access_token": token}, timeout=120))
    m = IG._check(requests.get(f"{IG.GRAPH}/{p['id']}", params={"fields": "id,permalink", "access_token": token}))
    print("Instagram carrusel:", m.get("permalink"), flush=True)
    return m


def publish(paths, cap, c):
    res = {}
    try:
        urls = public_urls(paths)
    except Exception as e:
        return {"error": f"no se pudieron alojar las imágenes: {str(e)[:200]}"}
    if os.environ.get("IG_TOKEN"):
        try:
            m = ig_carousel(urls, cap); res["instagram"] = m.get("permalink") or m.get("id")
        except Exception as e:
            res["instagram"] = f"error: {str(e)[:300]}"
    if os.environ.get("ZERNIO_API_KEY") and os.environ.get("TIKTOK", "true").lower() != "false":
        try:
            import publish_zernio as Z
            title = " ".join(c["titulo_lineas"]).capitalize()
            res["tiktok"] = Z.tiktok_photos(urls, title, cap)
        except Exception as e:
            res["tiktok"] = f"error: {str(e)[:300]}"
    return res


# ------------------------------------------------------------------ main
def main():
    today = str(datetime.date.today())
    dry = os.environ.get("DRY_RUN", "false").lower() == "true"
    if not dry and os.environ.get("FORCE") != "true" and any(e.get("fecha") == today and e.get("publicado") for e in log()):
        print("ya se publicó la chuleta de hoy"); return
    if not MOCK and not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("Falta GEMINI_API_KEY: sin verificador no se publica ninguna chuleta.")
    seed = today
    out_dir = os.path.join(HERE, "out", f"chuleta_{today}")
    tried, tema, c, topic = [], None, None, os.environ.get("CHULETA_TEMA") or None
    for attempt in range(3):
        topic = topic if (attempt == 0 and topic) else pick_topic(f"{seed}-{attempt}", tried)
        if not topic:
            break
        tried.append(topic)
        try:
            tema, c = content_for(topic, seed)
            break
        except Exception as e:
            print(f"chuleta: tema {topic} descartado: {str(e)[:200]}", flush=True); c = None
    if not c:
        raise SystemExit("hoy no hay chuleta verificada (mejor no publicar que publicar un error)")
    P = quiz_question(topic, seed)
    things = [c["pegatina_portada"]] + [s["pegatina"] for s in c["diapositivas"][:3]]
    stickers = [sticker(t, i) for i, t in enumerate(things)]
    paths = render(c, P, stickers, out_dir, seed)
    cap = caption(c, P)
    open(os.path.join(out_dir, "descripcion.txt"), "w").write(cap)
    print(f"chuleta: {tema} · {c['subtema']} · {len(paths)} imágenes", flush=True)
    res = {} if dry else publish(paths, cap, c)
    print("publicación:", json.dumps(res, ensure_ascii=False), flush=True)
    ok = any(isinstance(v, str) and not v.startswith("error") for v in res.values())
    entry = {"fecha": today, "topic": topic, "tema": tema, "subtema": c["subtema"], "quiz_id": P and P["id"],
             "imagenes": len(paths), "publicado": ok, "destinos": res, "dry_run": dry}
    if not dry:                                            # las pruebas no cuentan como tema usado
        L = log(); L.append(entry); json.dump(L, open(LOG, "w"), ensure_ascii=False, indent=0)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(
            f"## Chuleta {today}\n- Tema: {tema} · {c['subtema']}\n- Imágenes: {len(paths)}\n- Publicación: {json.dumps(res, ensure_ascii=False)}\n")
    if not dry and not ok:
        raise SystemExit("la chuleta no se pudo publicar en ningún sitio")


if __name__ == "__main__":
    main()
