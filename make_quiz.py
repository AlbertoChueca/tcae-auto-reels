"""Reel tipo test de Aprueba TCAE (sin mascota: diseño de tarjeta + voz en off), en 6 estilos visuales (themes.py).

Estructura: gancho -> pregunta (la voz la lee, las palabras se iluminan al decirlas) -> cuenta atrás para pensar ->
respuesta correcta resaltada (con destello) -> explicación breve con su referencia -> cierre con la web app.
Formatos: pregunta_del_dia, examen_real, error_tipico, truco_memorizar, mito_realidad, simulacro_3, legislacion_30s,
caso_practico (escena ilustrada + pregunta) y flashcards_express (4 fichas de la app que se giran).

    QUIZ_MOCK=1 VOICE_ENGINE=mock python make_quiz.py <formato> out.mp4 [estilo]      (prueba sin red)
"""
import json, math, os, random, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

import fx
import themes
from fx import W, H, FPS, SR, F800, F900, TEAL, AMBER, INK, PAPER, GREEN, RED, WHITE, eob, eo, clamp
import questions as QB

HERE = os.path.dirname(os.path.abspath(__file__))
CARD_W, PAD = 950, 46
CARD_TOP = 410            # tope superior mínimo de las tarjetas
CARD_CENTER = 900         # las tarjetas se centran aquí si caben (zona segura 250-1500)
CARD_MAX_BOTTOM = 1385   # deja sitio debajo para 'Comenta…' / retos dentro de la zona segura
HDR = 74                  # alto de la cabecera de la hoja (estilo examen)
THINK = {"corto": 5, "normal": 7, "largo": 9}
BADGE = {"pregunta_del_dia": "PREGUNTA DEL DÍA", "examen_real": "CAYÓ EN EL EXAMEN", "error_tipico": "ERROR TÍPICO",
         "truco_memorizar": "TRUCO PARA MEMORIZAR", "mito_realidad": "MITO O REALIDAD", "simulacro_3": "SIMULACRO RÁPIDO",
         "legislacion_30s": "LEGISLACIÓN EN 30 SEGUNDOS", "caso_practico": "CASO PRÁCTICO",
         "flashcards_express": "REPASO EXPRÉS"}
DEFAULT_STYLE = {"caption_scale": 1.0, "screen_hook": "", "follow_line": "Síguenos: una pregunta cada día",
                 "share_line": "Envíaselo a quien oposita contigo", "save_line": "", "reto_line": "", "series": ""}
TAGS_FIXED = ["#TCAE", "#oposicionesTCAE"]
TAGS_ROT = ["#auxiliardeenfermeria", "#oposiciones", "#SALUD", "#Aragon"]
T = themes.get("clasico")


def ctop(h):
    """Posición superior de una tarjeta de alto h: centrada en la zona útil, sin pasar de los límites."""
    return int(max(CARD_TOP - 20, min(CARD_CENTER - h / 2, CARD_MAX_BOTTOM - h)))


def _mix(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a[:3], b[:3]))


# ------------------------------------------------------------------ tarjetas
def _card_base(h, header=None):
    im = Image.new("RGBA", (CARD_W, int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, CARD_W - 1, int(h) - 1], T.card_radius, fill=T.card_fill,
                        outline=T.card_outline, width=3 if T.card_outline else 0)
    if header:
        f = fx.font(F900, 26)
        d.text((PAD, 26), header, font=f, fill=T.ink)
        d.text((CARD_W - PAD - f.getlength("HOJA DE RESPUESTAS"), 26), "HOJA DE RESPUESTAS", font=fx.font(F800, 22), fill=T.label)
        d.line([(PAD, HDR - 8), (CARD_W - PAD, HDR - 8)], fill=T.ink, width=3)
    return im


def _letter(row, k, cy, color=None):
    """Distintivo de la letra (A-D) según el estilo."""
    rd = ImageDraw.Draw(row); L = QB.LETTERS[k]; f = fx.font(F900, 36)
    if T.letter == "box":                                  # casilla de hoja de respuestas
        rd.rectangle([20, cy - 26, 72, cy + 26], outline=T.ink, width=4)
        rd.text((46 - f.getlength(L.lower()) / 2, cy - 25), L.lower(), font=f, fill=color or T.ink)
    elif T.letter == "circle_outline":
        rd.ellipse([16, cy - 31, 78, cy + 31], outline=color or T.accent, width=4)
        rd.text((47 - f.getlength(L) / 2, cy - 25), L, font=f, fill=color or T.accent)
    elif T.letter == "square":
        rd.rounded_rectangle([16, cy - 31, 78, cy + 31], 12, fill=color or T.accent)
        rd.text((47 - f.getlength(L) / 2, cy - 25), L, font=f, fill=T.accent_fg)
    else:
        rd.ellipse([16, cy - 31, 78, cy + 31], fill=color or T.accent)
        rd.text((47 - f.getlength(L) / 2, cy - 25), L, font=f, fill=T.accent_fg)


class QuestionCard:
    """Tarjeta con enunciado + 4 opciones. Mide su propio tamaño para caber siempre en la zona segura."""

    def __init__(self, P, label, counter=None):
        self.P, self.label, self.counter = P, label, counter
        self.hdr = HDR if T.header else 0
        inner = CARD_W - 2 * PAD
        for qs, os_ in ((62, 48), (58, 46), (54, 43), (50, 40), (47, 38), (44, 35), (41, 33), (38, 30)):
            self.qs, self.os = qs, os_
            self.q_img = fx.text_block(P["pregunta"], F900, qs, inner)
            self.rows = [self._row_layout(k) for k in range(4)]
            self.h = self.hdr + PAD + 52 + self.q_img.height + 26 + sum(self.rows) + 16 * 3 + PAD
            if CARD_TOP + self.h <= CARD_MAX_BOTTOM:
                break
        self.ok_center = (CARD_W / 2, self.h / 2)
        self._cache = {}

    def _row_layout(self, k):
        im = fx.text_block(self.P["op"][k], F800, self.os, CARD_W - 2 * PAD - 70 - 44)
        return max(86, im.height + 30)

    def render(self, lit=None, active=None, reveal=0.0, trampa=None, show_trampa=0.0):
        key = (lit, active, round(reveal, 1), trampa, round(show_trampa, 1))
        if key in self._cache:
            return self._cache[key]
        P = self.P
        im = _card_base(self.h, T.header); d = ImageDraw.Draw(im)
        y = self.hdr + PAD - 6
        room = CARD_W - 2 * PAD - (110 if self.counter else 0)
        lab = self.label
        while fx.font(F800, 30).getlength(lab) > room and " " in lab:
            lab = lab.rsplit(" ", 1)[0].rstrip(" ,·-") + "…"
        d.text((PAD, y), lab, font=fx.font(F800, 30), fill=T.label)
        if self.counter:
            c = fx.pill(self.counter, 30, T.accent if T.letter != "box" else T.ink, WHITE, padx=22, pady=8)
            im.alpha_composite(c, (CARD_W - PAD - c.width, y - 6))
        y += 52
        q = fx.text_block(P["pregunta"], F900, self.qs, CARD_W - 2 * PAD, T.ink, lit=lit, dim=T.dim)
        im.alpha_composite(q, (PAD, y)); y += q.height + 26
        a = eo(reveal)
        for k in range(4):
            rh = self.rows[k]
            ok, is_tr = k == P["ok"], (k == trampa and show_trampa > 0)
            fill, txt, outline, lcol = T.row_fill, T.ink, None, None
            if active == k and reveal == 0:
                fill, outline = T.row_active, T.row_outline
            if reveal > 0:
                if ok and T.ok_mode == "fill":
                    fill = _mix(T.row_fill, T.ok_col, a); txt = T.ok_text if a > .5 else T.ink
                elif ok and T.ok_mode == "pen":
                    fill = _mix(T.row_fill, (232, 238, 255), a); txt = T.ok_text if a > .5 else T.ink
                elif ok:
                    txt = T.ok_text
                elif is_tr:
                    fill, outline = T.bad_fill, T.bad_col
                else:
                    txt = _mix(T.ink, T.faded, a * .75); lcol = _mix(T.accent, T.faded, a * .8)
            row = Image.new("RGBA", (CARD_W - 2 * PAD, rh), (0, 0, 0, 0)); rd = ImageDraw.Draw(row)
            rd.rounded_rectangle([0, 0, row.width - 1, rh - 1], T.row_radius, fill=fill, outline=outline, width=5 if outline else 0)
            cy = rh // 2
            t = fx.text_block(P["op"][k], F800, self.os, row.width - 70 - 44, txt)
            if ok and reveal > 0 and T.ok_mode == "marker":        # subrayador amarillo que se desliza
                hl = Image.new("RGBA", (int((t.width + 20) * a) + 2, t.height - 6), T.ok_col + (190,))
                row.alpha_composite(hl, (90, (rh - t.height) // 2 + 8))
            if reveal > 0.5 and ok and T.ok_mode == "pen":           # aspa de bolígrafo azul en la casilla
                _letter(row, k, cy, T.ok_col)
                p = clamp((reveal - .5) * 2)
                rd.line([(24, cy - 22), (24 + 44 * p, cy - 22 + 44 * p)], fill=T.ok_col, width=7)
                if p > .5:
                    rd.line([(68, cy - 22), (68 - 44 * (p - .5) * 2, cy - 22 + 44 * (p - .5) * 2)], fill=T.ok_col, width=7)
            elif reveal > 0.5 and ok:
                icon = fx.check_icon(62, T.ok_col, T.ok_text) if T.ok_mode == "fill" else fx.check_icon(62, WHITE, T.accent)
                row.alpha_composite(icon, (16, cy - 31))
            elif reveal > 0.5 and is_tr:
                row.alpha_composite(fx.cross_icon(62, WHITE, T.bad_col), (16, cy - 31))
            else:
                _letter(row, k, cy, lcol)
            row.alpha_composite(t, (100, (rh - t.height) // 2 + 4))
            if is_tr:
                tag = fx.pill("TRAMPA", 26, T.bad_col, WHITE, padx=16, pady=6)
                row.alpha_composite(tag, (row.width - tag.width - 14, 8))
            im.alpha_composite(row, (PAD, y))
            if ok:
                self.ok_center = (PAD + 60, y + rh / 2)
            y += rh + 16
        self._cache[key] = im
        return im


class TextCard:
    """Tarjeta de explicación / truco / afirmación / puntos clave / ficha, con karaoke del texto hablado."""

    def __init__(self, title, body, ref=None, top_line=None, big=None, bullets=None, title_color=None, body_size=54,
                 title_fg=None):
        self.title, self.body, self.ref, self.top, self.big, self.bullets = title, body, ref, top_line, big, bullets
        self.title_color, self.title_fg = title_color or T.title_bg, title_fg or (T.title_fg if not title_color else WHITE)
        inner = CARD_W - 2 * PAD
        for bs in (body_size, body_size - 4, body_size - 8, body_size - 12, body_size - 16):
            self.bs = bs
            self.h = self._measure(inner)
            if CARD_TOP + self.h <= CARD_MAX_BOTTOM:
                break
        self._cache = {}

    def _measure(self, inner):
        h = PAD
        if self.top:
            h += fx.text_block(self.top, F800, 36, inner - 90).height + 40
        if self.title:
            h += 64
        if self.big:
            h += fx.text_block(self.big, F900, 64, inner).height + 24
        if self.body:
            h += fx.text_block(self.body, F800, self.bs, inner).height + 10
        for b in self.bullets or []:
            h += fx.text_block(b, F800, self.bs, inner - 84).height + 26
        if self.ref:
            h += 80
        return h + PAD

    def render(self, lit=None, n_bullets=None, bullet_lit=None):
        key = (lit, n_bullets, bullet_lit)
        if key in self._cache:
            return self._cache[key]
        inner = CARD_W - 2 * PAD
        im = _card_base(self.h); d = ImageDraw.Draw(im)
        y = PAD
        if self.top:                                      # respuesta correcta recordada arriba
            t = fx.text_block(self.top, F800, 36, inner - 90, T.ok_text if T.ok_mode == "fill" else T.ink)
            band = Image.new("RGBA", (inner, t.height + 24), (0, 0, 0, 0))
            bcol = T.ok_col if T.ok_mode == "fill" else (_mix(T.ok_col, (255, 255, 255), .55))
            ImageDraw.Draw(band).rounded_rectangle([0, 0, inner - 1, band.height - 1], min(24, T.row_radius), fill=bcol)
            band.alpha_composite(fx.check_icon(50, bcol, T.ok_text if T.ok_mode == "fill" else T.ink), (14, (band.height - 50) // 2))
            band.alpha_composite(t, (80, 14)); im.alpha_composite(band, (PAD, y)); y += band.height + 22
        if self.title:
            p = fx.pill(self.title, 30, self.title_color, self.title_fg, padx=22, pady=9)
            im.alpha_composite(p, (PAD, y)); y += 64
        if self.big:
            b = fx.text_block(self.big, F900, 64, inner, T.big_col)
            im.alpha_composite(b, (PAD, y)); y += b.height + 24
        if self.body:
            b = fx.text_block(self.body, F800, self.bs, inner, T.ink, lit=lit, dim=T.dim)
            im.alpha_composite(b, (PAD, y)); y += b.height + 10
        for k, bl in enumerate(self.bullets or []):
            if n_bullets is not None and k >= n_bullets:
                break
            d.ellipse([PAD, y + 2, PAD + 58, y + 60], fill=T.accent if T.letter != "box" else T.ink)
            f = fx.font(F900, 34); d.text((PAD + 29 - f.getlength(str(k + 1)) / 2, y + 6), str(k + 1), font=f,
                                          fill=T.accent_fg if T.letter != "box" else WHITE)
            b = fx.text_block(bl, F800, self.bs, inner - 84, T.ink,
                              lit=(bullet_lit if k == (n_bullets or 0) - 1 else None), dim=T.dim)
            im.alpha_composite(b, (PAD + 84, y + 4)); y += b.height + 26
        if self.ref:
            r = fx.pill(self.ref, 28, T.ref_bg, T.ref_fg, padx=20, pady=10, path=F800)
            im.alpha_composite(r, (PAD, int(self.h - PAD - r.height)))
        self._cache[key] = im
        return im


def brand_card(style):
    """Tarjeta final: marca + web + qué hay en la app (solo hechos ciertos)."""
    h = 820
    im = Image.new("RGBA", (CARD_W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, CARD_W - 1, h - 1], 46, fill=PAPER)
    logo = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rounded_rectangle([0, 0, 119, 119], 32, fill=TEAL)
    logo.alpha_composite(fx.check_icon(84, WHITE, TEAL).resize((84, 84)), (18, 18))
    f = fx.font(F900, 84); tw = f.getlength("Aprueba TCAE")
    x0 = (CARD_W - (120 + 26 + tw)) / 2
    im.alpha_composite(logo, (int(x0), 70))
    d.text((x0 + 146, 78), "Aprueba", font=f, fill=INK)
    d.text((x0 + 146 + f.getlength("Aprueba "), 78), "TCAE", font=f, fill=TEAL)
    sub = fx.text_block("Tests, simulacros y flashcards para la oposición de TCAE del SALUD", F800, 38, 780,
                        (90, 112, 108), align="center")
    im.alpha_composite(sub, ((CARD_W - sub.width) // 2, 230))
    p1 = fx.pill("PRACTICA GRATIS", 40, AMBER, INK, padx=36, pady=14)
    im.alpha_composite(p1, ((CARD_W - p1.width) // 2, 380))
    p2 = fx.pill("apruebatcae.com", 64, TEAL, WHITE, padx=46, pady=18)
    im.alpha_composite(p2, ((CARD_W - p2.width) // 2, 485))
    p3 = fx.text_block("Link en la bio", F900, 40, 600, INK, align="center")
    im.alpha_composite(p3, ((CARD_W - p3.width) // 2, 640))
    if style.get("follow_line"):
        p4 = fx.text_block(style["follow_line"], F800, 32, 820, (90, 112, 108), align="center")
        im.alpha_composite(p4, ((CARD_W - p4.width) // 2, 712))
    return im


def badge(fmt, extra=None, series=None):
    b = fx.pill(series.upper() if series else BADGE[fmt], 34, T.badge_bg, T.badge_fg, padx=28, pady=12)
    if not extra:
        return b
    e = fx.pill(extra, 30, T.chip_bg, T.chip_fg, padx=22, pady=11, path=F800)
    if b.width + 16 + e.width > W - 120:
        return b
    im = Image.new("RGBA", (b.width + 16 + e.width, max(b.height, e.height)), (0, 0, 0, 0))
    im.alpha_composite(b, (0, (im.height - b.height) // 2)); im.alpha_composite(e, (b.width + 16, (im.height - e.height) // 2))
    return im


def ring(remain, frac, size=170):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([6, 6, size - 6, size - 6], fill=T.ring_bg)
    col = RED if remain <= 3 else T.ring_col
    d.arc([14, 14, size - 14, size - 14], -90, -90 + 360 * frac, fill=col, width=16)
    f = fx.font(F900, 78); t = str(remain)
    d.text((size / 2 - f.getlength(t) / 2, size / 2 - 52), t, font=f, fill=T.ring_fg if T.name != "minimal" else WHITE)
    return im


def burst(fr, cx, cy, lt, seed=3):
    """Destello de partículas al revelar la respuesta correcta (0,8 s)."""
    if lt > 0.8:
        return
    rng = random.Random(seed); d = ImageDraw.Draw(fr)
    for k in range(30):
        ang = rng.uniform(0, 2 * math.pi); sp = rng.uniform(260, 820); col = T.burst[k % len(T.burst)]
        r0 = sp * eo(lt / 0.8); x = cx + math.cos(ang) * r0; y = cy + math.sin(ang) * r0 * 0.7 + 260 * lt * lt
        s = max(2, 10 * (1 - lt / 0.8))
        d.ellipse([x - s, y - s, x + s, y + s], fill=tuple(col[:3]) + (int(255 * (1 - lt / 0.8)),))


# ------------------------------------------------------------------ guion -> líneas de voz
def lines_for(fmt, items, S):
    P = items[0]
    L = [("hook", S["hook_line"], "enérgica y cercana, reto amistoso")]
    if fmt == "flashcards_express":
        for i, F in enumerate(items):
            L.append((f"fq{i}", F["q"], "clara, pregunta de repaso"))
            L.append((f"fa{i}", F["a"], "segura y didáctica"))
        L.append(("fin", S["cierre_line"], "cálida, invitando a comentar"))
    elif fmt == "simulacro_3":
        for i, Q in enumerate(items):
            L.append((f"q{i}", Q["pregunta"], "clara, ritmo ágil de examen"))
            L.append((f"r{i}", f"La {Q['letra']}.", "segura, breve"))
        L.append(("fin", S["cierre_line"], "cálida, invitando a comentar"))
    elif fmt == "mito_realidad":
        L.append(("st", S["afirmacion"], "intrigante, dejando la duda"))
        L.append(("rev", "¡Mito!" if S["veredicto"] == "MITO" else "¡Realidad!", "rotunda, con chispa"))
        L.append(("ex", S["explicacion"], "didáctica y cercana, como una compañera que lo explica bien"))
    else:
        if fmt == "legislacion_30s":
            for k, p in enumerate(S["puntos"]):
                L.append((f"p{k}", p, "didáctica, clara, buen ritmo"))
        if fmt == "caso_practico":
            L.append(("esc", S["escena"], "narrativa, ambiente de planta de hospital, intriga suave"))
        L.append(("q", P["pregunta"], "clara, ritmo de examen, sin prisa"))
        if fmt != "legislacion_30s":
            for k, o in enumerate(P["op"]):
                L.append((f"o{k}", f"{QB.LETTERS[k]}. {o}", "neutra, enumerando opciones"))
        L.append(("rev", S["reveal_line"], "segura, con una sonrisa"))
        if fmt == "error_tipico":
            L.append(("ex", S["trampa_porque"], "didáctica, avisando de la trampa"))
        elif fmt == "truco_memorizar":
            L.append(("ex", S["truco_line"], "cómplice, compartiendo un truco"))
        elif fmt != "legislacion_30s":
            L.append(("ex", S["explicacion"], "didáctica y cercana, como una compañera que lo explica bien"))
    L.append(("cta", S["cta_line"], "cálida y motivadora"))
    return L


def ref_label(P):
    r = QB.verif().get(P["id"], {})
    if r.get("fuente_ok") and r.get("referencia"):
        return "Fuente: " + r["referencia"]
    if P.get("examen"):
        return f"Examen oficial · {P['examen']['titulo']}"
    return "Tema: " + P["tema"]


def caption_text(fmt, items, S, rng, st=None):
    P = items[0]; st = st or {}
    if fmt == "flashcards_express":
        body = "Repaso exprés de " + P["tema"] + ":\n\n" + "\n\n".join(f"{i + 1}. {F['q']}\n→ {F['a']}" for i, F in enumerate(items))
    elif fmt == "simulacro_3":
        body = "\n\n".join(f"{i + 1}. {Q['pregunta']}\n" + "\n".join(f"{QB.LETTERS[k]}) {o}" for k, o in enumerate(Q["op"]))
                           for i, Q in enumerate(items))
    elif fmt == "mito_realidad":
        body = f"¿Mito o realidad? «{S['afirmacion']}»"
    else:
        body = (S["escena"] + "\n\n" if fmt == "caso_practico" else "") + P["pregunta"] + "\n" + \
               "\n".join(f"{QB.LETTERS[k]}) {o}" for k, o in enumerate(P["op"]))
    tags = TAGS_FIXED + rng.sample(TAGS_ROT, 3)
    sol = "" if fmt == "flashcards_express" else " La solución, al final del vídeo."
    extra = "".join(f"{x}\n" for x in (S.get("save_caption"), S.get("tag_caption"), S.get("app_caption"),
                                        S.get("follow_caption"), S.get("seo_line")) if x)
    return (f"{S['caption_hook']}\n\n{body}\n\n{S['comment_prompt'].rstrip('.!')}.{sol}\n\n" + (extra + "\n" if extra else "")
            + "Practica gratis con más de 1.800 preguntas tipo test, simulacros y flashcards de la oposición de TCAE "
            "del SALUD en apruebatcae.com (link en la bio).\n\n" + " ".join(tags))


# ------------------------------------------------------------------ build
def build(fmt, items, S, seed, out, arms=None, style=None, max_len=58.0, keep_voice=False, image=None, estilo=None):
    """image: ilustración original (PIL) para el estilo 'ilustrado', el gancho y la escena del caso práctico."""
    global T
    import voice
    arms = arms or {}
    estilo = estilo or arms.get("estilo") or "clasico"
    if estilo == "ilustrado" and image is None:
        estilo = "noche"                                 # sin imagen: el estilo más parecido
    T = themes.get(estilo)
    st = {**DEFAULT_STYLE, **(style or {})}
    if st.get("screen_hook"):
        S = {**S, "screen_hook": st["screen_hook"]}
    rng = random.Random(f"{seed}-{fmt}")
    P = items[0]
    count = 5 if fmt == "simulacro_3" else THINK.get(arms.get("think_time"), 7)
    L = lines_for(fmt, items, S)
    speed = float(st.get("voice_speed") or 1.06)

    if not keep_voice:
        voice.reset()                    # reel nuevo: elige la mejor voz y úsala en todas las frases
    for attempt in range(3):
        try:
            clips = voice.say_many([t for _, t, _ in L], speed=speed, styles=[s for _, _, s in L])
            break
        except voice.VoiceError as e:
            print(f"voz cambiada a mitad de reel ({e}); repito con {voice.next_engine()}", flush=True)
            voice.reset(voice.next_engine())
    else:
        raise RuntimeError("no se pudo grabar una voz coherente")
    A = {k: c for (k, _, _), c in zip(L, clips)}; TXT = {k: t for k, t, _ in L}
    D = {k: len(a) / SR for k, a in A.items()}

    # ---- línea de tiempo (si sale demasiado larga, se acorta el tiempo para pensar)
    def plan(count):
        SEG, VO = [], {}
        t = 0.0

        def seg(kind, dur, **kw):
            nonlocal t
            SEG.append({"kind": kind, "a": t, "b": t + dur, **kw}); t += dur

        def say(k, at):
            VO[k] = at

        seg("hook", max(2.6, D["hook"] + 0.6)); say("hook", 0.25)
        if fmt == "flashcards_express":
            pause = max(1.2, min(2.5, count / 3))
            for i in range(len(items)):
                a = t; seg("fq", D[f"fq{i}"] + 0.6 + pause, q=i); say(f"fq{i}", a + 0.35)
                a = t; seg("fa", D[f"fa{i}"] + 0.9, q=i); say(f"fa{i}", a + 0.4)
            a = t; seg("score", D["fin"] + 1.2); say("fin", a + 0.3)
        elif fmt == "simulacro_3":
            for i, Q in enumerate(items):
                a = t; seg("question", D[f"q{i}"] + 0.9, q=i); say(f"q{i}", a + 0.45)
                seg("count", count, q=i, n=count)
                a = t; seg("reveal", max(1.6, D[f"r{i}"] + 0.6), q=i); say(f"r{i}", a + 0.15)
            a = t; seg("score", D["fin"] + 1.2); say("fin", a + 0.3)
        elif fmt == "mito_realidad":
            a = t; seg("statement", D["st"] + 1.0); say("st", a + 0.45)
            seg("count", count, q=0, n=count)
            a = t; seg("stamp", max(1.6, D["rev"] + 0.7)); say("rev", a + 0.1)
            a = t; seg("explain", D["ex"] + 1.2); say("ex", a + 0.5)
        else:
            if fmt == "legislacion_30s":
                a = t; tt = a + 0.5; starts = []
                for k in range(3):
                    starts.append(tt); say(f"p{k}", tt); tt += D[f"p{k}"] + 0.35
                seg("points", tt - a + 0.5, starts=starts)
            if fmt == "caso_practico":
                a = t; seg("scene", D["esc"] + 1.0); say("esc", a + 0.4)
            a = t; tt = a + 0.45; say("q", tt); tt += D["q"] + 0.3; ostarts = []
            if "o0" in A:
                for k in range(4):
                    ostarts.append(tt); say(f"o{k}", tt); tt += D[f"o{k}"] + 0.2
            seg("question", tt - a + 0.3, q=0, ostarts=ostarts)
            seg("count", count, q=0, n=count)
            a = t; seg("reveal", max(2.0, D["rev"] + 0.9), q=0,
                       trampa=S.get("trampa") if fmt == "error_tipico" else None); say("rev", a + 0.15)
            if "ex" in A:
                a = t; seg("explain", D["ex"] + 1.2); say("ex", a + 0.5)
        a = t; seg("cta", max(4.8, D["cta"] + 1.8)); say("cta", a + 0.4)
        return SEG, VO, t

    SEG, VO, total = plan(count)
    n_counts = max(1, sum(1 for s_ in SEG if s_["kind"] == "count"))
    if total > max_len and count > 4:
        count = max(4, count - math.ceil((total - max_len) / n_counts))
        SEG, VO, total = plan(count)
    print(f"reel: {fmt} · estilo {T.name} · {total:.1f} s · {count} s para pensar", flush=True)

    # ---- audio
    n = int(SR * (total + 0.5)); vo = np.zeros(n, np.float32); sfx = np.zeros(n, np.float32)

    def put(buf, a, at, g=1.0):
        i = int(at * SR)
        if i >= n: return
        if i < 0: a = a[-i:]; i = 0
        j = min(n, i + len(a)); buf[i:j] += a[: j - i] * g
    for k, at in VO.items():
        put(vo, A[k], at)
    for sg in SEG:
        if sg["kind"] in ("question", "statement", "points", "explain", "cta", "score", "scene", "fq"):
            put(sfx, fx.whoosh(), sg["a"] - 0.15, 1.1)
        if sg["kind"] == "count":
            for s_ in range(sg["n"]):
                put(sfx, fx.tick(s_ >= sg["n"] - 3), sg["a"] + s_, 1.0)
            put(sfx, fx.riser(min(3.0, sg["n"])), sg["b"] - min(3.0, sg["n"]), 0.8)
        if sg["kind"] in ("reveal", "fa"):
            put(sfx, fx.chime_ok(), sg["a"] + 0.05, 1.0 if sg["kind"] == "reveal" else 0.6)
        if sg["kind"] == "stamp":
            put(sfx, fx.stamp(), sg["a"] + 0.05, 0.9)
    bpm = {"calma": T.music_bpm - 8, "energica": T.music_bpm + 14}.get(st.get("music"), T.music_bpm)
    music = fx.study_beat(total, bpm)[:n]
    venv = np.convolve((np.abs(vo) > 0.01).astype(np.float32), np.ones(3000) / 3000, "same")
    for sg in SEG:
        if sg["kind"] == "count":                         # más tensión y menos música mientras piensas
            music[int(sg["a"] * SR):int(sg["b"] * SR)] *= 0.55
    mix = vo * 1.15 + sfx + music * (0.55 - 0.35 * np.clip(venv * 3, 0, 1))
    mix = fx.dehiss(np.tanh(mix * 1.05) * 0.92)
    wav = out.replace(".mp4", ".wav"); sf.write(wav, mix, SR)

    # ---- karaoke: momento en que se dice cada palabra
    WT = {k: [VO[k] + ts for ts, _ in voice.align(A[k], TXT[k])] for k in VO}

    def lit(k, tt):
        return sum(1 for x in WT[k] if x <= tt) if k in WT else None

    # ---- elementos visuales
    bg = T.background(rng.randint(0, 999), image)
    hook_bg = themes.ImageBG(image, dark=0.25, blur=0) if image is not None else None
    extra = (P["examen"]["titulo"] if fmt == "examen_real" and P.get("examen") else
             (P["tema"] if len(P["tema"]) <= 26 and fmt not in ("simulacro_3",) else None))
    bdg = badge(fmt, extra, st.get("series"))
    on_img = hook_bg is not None
    hook_img = fx.headline(S["screen_hook"], 112, 920, 3,
                           color=WHITE if on_img else T.head_col, hot=AMBER if on_img else T.head_hot,
                           hot_words=("trampa", "examen", "mito", "realidad", "truco", "3", "30", "cayó", "error", "caso"),
                           stroke=9 if on_img else T.head_stroke, stroke_col=(10, 10, 14) if on_img else T.head_stroke_col,
                           shadow=True if on_img else T.head_shadow)
    cards = []
    if fmt != "flashcards_express":
        cards = [QuestionCard(Q, ("EXAMEN OFICIAL · " + Q["examen"]["titulo"]) if Q.get("examen") else Q["tema"].upper(),
                              f"{i + 1}/3" if fmt == "simulacro_3" else None) for i, Q in enumerate(items)]
    expl = stmt = pts = scene_card = None
    fronts, backs = [], []
    if fmt == "flashcards_express":
        for i, F in enumerate(items):
            fronts.append(TextCard(f"FICHA {i + 1}/{len(items)}", F["q"], "Tema: " + F["tema"], body_size=64))
            backs.append(TextCard("RESPUESTA", F["a"], "Tema: " + F["tema"], body_size=56, title_color=T.ok_col,
                                  title_fg=T.ok_text if T.ok_mode == "fill" else T.ink))
    else:
        corr = f"{P['letra']}) {P['op'][P['ok']]}"
        if fmt == "error_tipico":
            expl = TextCard("OJO CON LA TRAMPA", S["trampa_porque"], ref_label(P), top_line=corr, title_color=T.bad_col)
        elif fmt == "truco_memorizar":
            expl = TextCard("TRUCO PARA RECORDARLO", S["truco_line"], ref_label(P), top_line=corr, big=S["truco"], body_size=42)
        elif fmt == "mito_realidad":
            expl = TextCard("¿POR QUÉ?", S["explicacion"], ref_label(P))
        elif "ex" in A:
            expl = TextCard("¿POR QUÉ?", S["explicacion"], ref_label(P), top_line=corr, body_size=54)
        if fmt == "mito_realidad":
            stmt = TextCard("¿MITO O REALIDAD?", S["afirmacion"], None, body_size=72)
        if fmt == "legislacion_30s":
            pts = TextCard(None, None, ref_label(P), big=S.get("titulo_norma"), bullets=S["puntos"])
        if fmt == "caso_practico" and hook_bg is None:
            scene_card = TextCard("CASO PRÁCTICO", S["escena"], None, body_size=60)
    brand = fx.shadowed(brand_card(st))
    stamp_img = fx.pill(S.get("veredicto", "MITO"), 120, RED if S.get("veredicto") == "MITO" else GREEN, WHITE,
                        padx=60, pady=26, outline=WHITE) if fmt == "mito_realidad" else None
    n_items = len(items)
    score_img = fx.headline("¿Cuántas sabías?" if fmt == "flashcards_express" else "¿Cuántas has acertado?", 104, 900, 3,
                            color=T.head_col, hot=T.head_hot, hot_words=("acertado?", "sabías?"), stroke=T.head_stroke,
                            stroke_col=T.head_stroke_col, shadow=T.head_shadow)
    score_row = None
    if fmt in ("simulacro_3", "flashcards_express"):
        labs = [f"{k}/{n_items}" for k in range(n_items + 1)]
        ps = [fx.pill(x, 46, T.badge_bg if x == labs[-1] else (255, 255, 255), T.badge_fg if x == labs[-1] else INK,
                      padx=24, pady=12) for x in labs]
        score_row = Image.new("RGBA", (sum(p.width for p in ps) + 18 * (len(ps) - 1), ps[0].height), (0, 0, 0, 0)); x = 0
        for p in ps:
            score_row.alpha_composite(p, (x, 0)); x += p.width + 18
    comment_lab = fx.pill("COMENTA: A, B, C O D", 40, T.pill_bg, T.pill_fg, padx=30, pady=12, outline=T.pill_outline)
    reto_lab = fx.pill(st["reto_line"].upper(), 38, T.pill_bg, T.pill_fg, padx=30, pady=12, outline=T.pill_outline) \
        if st.get("reto_line") else None
    save_lab = fx.pill(st["save_line"].upper(), 34, T.title_bg, T.title_fg, padx=26, pady=12) if st.get("save_line") else None

    def sub_img(k, tt, size=50, dark=False):
        """Subtítulo de la línea k (karaoke) en una banda."""
        n_ = lit(k, tt)
        if not n_:
            return None
        ink, dim, band_c = (WHITE, (170, 180, 190), (0, 0, 0, 150)) if dark else (T.sub_ink, T.sub_dim, T.sub_band)
        txt = fx.text_block(TXT[k], F900, int(size * st["caption_scale"]), 900, ink, lit=n_, dim=dim, align="center")
        b = Image.new("RGBA", (W - 20, txt.height + 64), (0, 0, 0, 0))
        if band_c[3]:
            ImageDraw.Draw(b).rounded_rectangle([30, 18, b.width - 30, b.height - 18], 38, fill=band_c)
        b.alpha_composite(txt, ((b.width - txt.width) // 2, 34))
        return b

    def card_at(img, tt, a, enter=0.35):
        p = eo((tt - a) / enter)
        return img, ctop(img.height) + img.height / 2 + (1 - p) * 140, p

    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", wav, "-shortest"] + fx.enc_args(out), stdin=subprocess.PIPE)
    sh_cache = {}

    def shadow(img):
        if not T.shadow:
            return img
        k = id(img)
        if k not in sh_cache:
            if len(sh_cache) > 40: sh_cache.clear()
            sh_cache[k] = (fx.shadowed(img), img)
        return sh_cache[k][0]

    def flip(img_a, img_b, p):
        """Giro de ficha: anverso -> reverso (escala horizontal)."""
        src = img_a if p < 0.5 else img_b
        k = abs(math.cos(p * math.pi))
        return src.resize((max(2, int(src.width * k)), src.height), Image.BILINEAR)

    # ---- fotogramas fijos (carrusel de TikTok y base de las stories): uno por bloque, en su mejor momento
    caps, slides = {}, []
    for sg in SEG:
        k, a, b = sg["kind"], sg["a"], sg["b"]
        if k == "count":
            continue
        t_ = {"hook": a + 0.8 * (b - a), "reveal": a + min(1.2, b - a - 0.1), "stamp": a + min(1.0, b - a - 0.1),
              "cta": a + min(3.0, b - a - 0.2)}.get(k, b - 0.15)
        caps[int(t_ * FPS)] = (k, out.replace(".mp4", f"_slide{len(caps) + 1:02d}_{k}.png"))
    story_base = None
    for fi in range(int(total * FPS)):
        tt = fi / FPS
        sg = next((s for s in SEG if s["a"] <= tt < s["b"]), SEG[-1])
        lt = tt - sg["a"]; kind = sg["kind"]
        if kind in ("hook", "scene") and hook_bg is not None:
            fr = hook_bg.frame(tt)
            grad = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(grad)
            for yy in range(0, H, 8):
                a_ = int(200 * max(0, (yy - H * 0.35) / (H * 0.65)) ** 1.3 + 90 * max(0, 1 - yy / 420))
                gd.rectangle([0, yy, W, yy + 8], fill=(0, 0, 0, min(220, a_)))
            fr.alpha_composite(grad)
        else:
            fr = bg.frame(tt)
        if kind != "cta":
            fx.paste_center(fr, bdg, 60 + bdg.width / 2, 312, alpha=eo(tt / 0.4))
        if kind == "hook":
            y_h = 860 if hook_bg is not None else 800
            fx.paste_center(fr, hook_img, W / 2, y_h, eob(lt / 0.35), min(1, lt / 0.15))
            s_ = sub_img("hook", tt, dark=hook_bg is not None)
            if s_ is not None: fx.paste_center(fr, s_, W / 2, 1300)
        elif kind == "scene":
            if scene_card is not None:
                img = scene_card.render(lit=lit("esc", tt)); im_, y, p = card_at(img, tt, sg["a"])
                fx.paste_center(fr, shadow(im_), W / 2, y, alpha=p)
            else:
                fx.paste_center(fr, fx.pill("CASO PRÁCTICO", 40, AMBER, INK, padx=30, pady=12), W / 2, 1060, eob(lt / 0.3))
                s_ = sub_img("esc", tt, 52, dark=True)
                if s_ is not None: fx.paste_center(fr, s_, W / 2, 1260)
        elif kind in ("fq", "fa"):
            i = sg["q"]
            if kind == "fq":
                img = fronts[i].render(lit=lit(f"fq{i}", tt)); im_, y, p = card_at(img, tt, sg["a"])
                fx.paste_center(fr, shadow(im_), W / 2, y, alpha=p)
            else:
                p = clamp(lt / 0.45)
                img = flip(fronts[i].render(), backs[i].render(lit=lit(f"fa{i}", tt)), p) if p < 1 else backs[i].render(lit=lit(f"fa{i}", tt))
                h_ = max(fronts[i].h, backs[i].h) if p < 1 else img.height
                fx.paste_center(fr, shadow(img) if p >= 1 else img, W / 2, ctop(h_) + h_ / 2 if p < 1 else ctop(img.height) + img.height / 2)
        elif kind in ("question", "count", "reveal") and stmt is None:
            qi = sg.get("q", 0); C = cards[qi]
            if kind == "question":
                act = None
                for k, s0 in enumerate(sg.get("ostarts") or []):
                    if s0 <= tt < s0 + D[f"o{k}"] + 0.15: act = k          # solo mientras se lee esa opción
                img = C.render(lit=lit(f"q{qi}" if fmt == "simulacro_3" else "q", tt), active=act)
                im_, y, p = card_at(img, tt, sg["a"])
                fx.paste_center(fr, shadow(im_), W / 2, y, alpha=p)
            elif kind == "count":
                img = C.render()
                fx.paste_center(fr, shadow(img), W / 2, ctop(img.height) + img.height / 2)
                remain = sg["n"] - int(lt); ph = lt % 1
                fx.paste_center(fr, ring(remain, 1 - lt / sg["n"]), W - 150, 300, 1 + 0.12 * max(0, 1 - ph * 5))
                cy = ctop(img.height) + img.height + 58
                lab = reto_lab if (reto_lab is not None and int(lt / 2.5) % 2 == 1) else comment_lab
                if cy + 30 < fx.SAFE_BOTTOM + 20:
                    fx.paste_center(fr, lab, W / 2, cy, eob((lt % 2.5) / 0.3))
            else:
                prog = clamp(lt / 0.45)
                tr = QB.LETTERS.index(sg["trampa"]) if sg.get("trampa") else None
                img = C.render(reveal=prog, trampa=tr, show_trampa=clamp((lt - 0.6) / 0.3) if tr is not None else 0)
                top_ = ctop(img.height)
                fx.paste_center(fr, shadow(img), W / 2, top_ + img.height / 2, 1 + 0.02 * math.sin(min(1, lt / 0.3) * math.pi))
                burst(fr, W / 2 - CARD_W / 2 + C.ok_center[0], top_ + C.ok_center[1], lt, seed=qi)
        elif kind == "statement" or (kind in ("count", "stamp") and stmt is not None):
            if kind == "statement":
                img = stmt.render(lit=lit("st", tt)); im_, y, p = card_at(img, tt, sg["a"])
                fx.paste_center(fr, shadow(im_), W / 2, y, alpha=p)
            else:
                img = stmt.render(); fx.paste_center(fr, shadow(img), W / 2, ctop(img.height) + img.height / 2)
                if kind == "count":
                    remain = sg["n"] - int(lt); ph = lt % 1
                    fx.paste_center(fr, ring(remain, 1 - lt / sg["n"]), W - 150, 300, 1 + 0.12 * max(0, 1 - ph * 5))
                    lab = fx.pill("COMENTA: ¿MITO O REALIDAD?", 38, T.pill_bg, T.pill_fg, padx=30, pady=12, outline=T.pill_outline)
                    if ctop(img.height) + img.height + 110 < fx.SAFE_BOTTOM:
                        fx.paste_center(fr, lab, W / 2, ctop(img.height) + img.height + 70)
                else:
                    fx.paste_center(fr, stamp_img, W / 2, ctop(img.height) + img.height / 2, 1.6 - 0.6 * eob(lt / 0.3), min(1, lt / 0.1), -8)
                    burst(fr, W / 2, ctop(img.height) + img.height / 2, lt)
        elif kind == "explain":
            img = expl.render(lit=lit("ex", tt)); im_, y, p = card_at(img, tt, sg["a"])
            fx.paste_center(fr, shadow(im_), W / 2, y, alpha=p)
            if save_lab is not None and lt > 1.0 and y + img.height / 2 + 80 < fx.SAFE_BOTTOM:
                fx.paste_center(fr, save_lab, W / 2, y + img.height / 2 + 70, eob((lt - 1.0) / 0.35))
        elif kind == "points":
            nb = sum(1 for s0 in sg["starts"] if tt >= s0 - 0.1)
            bl = lit(f"p{max(0, nb - 1)}", tt) if nb else None
            img = pts.render(n_bullets=max(0, nb), bullet_lit=bl); im_, y, p = card_at(img, tt, sg["a"])
            fx.paste_center(fr, shadow(im_), W / 2, y, alpha=p)
        elif kind == "score":
            fx.paste_center(fr, score_img, W / 2, 720, eob(lt / 0.35))
            fx.paste_center(fr, score_row, W / 2, 1000, eob((lt - 0.3) / 0.35))
            s_ = sub_img("fin", tt)
            if s_ is not None: fx.paste_center(fr, s_, W / 2, 1260)
        elif kind == "cta":
            fx.paste_center(fr, brand, W / 2, 330 + brand.height / 2 - 66, eob(lt / 0.4), min(1, lt / 0.2))
            if st.get("share_line") and lt > 1.2:
                fx.paste_center(fr, fx.pill(st["share_line"].upper(), 34, AMBER, INK, padx=26, pady=12), W / 2, 1225,
                                eob((lt - 1.2) / 0.35))
            s_ = sub_img("cta", tt, 44)
            if s_ is not None: fx.paste_center(fr, s_, W / 2, 1395)
        if fi in caps and len(slides) < 12:
            name, path = caps[fi]
            fr.convert("RGB").save(path); slides.append(path)
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait(); os.remove(wav)
    for want in ("question", "statement", "fq", "points", "scene"):      # base de la story: la pregunta sin resolver
        story_base = next((p for p in slides if f"_{want}.png" in p), None)
        if story_base:
            break
    if proc.returncode:
        raise RuntimeError("ffmpeg falló al codificar el reel")

    cap = caption_text(fmt, items, S, rng, st)
    open(out.replace(".mp4", ".txt"), "w").write(cap)
    return {"formato": fmt, "estilo": T.name, "ids": [Q["id"] for Q in items], "temas": [Q["tema"] for Q in items],
            "respuestas": [Q["letra"] for Q in items] if fmt != "flashcards_express" else [],
            "veredicto": S.get("veredicto"), "hook": S["screen_hook"], "hook_line": S["hook_line"],
            "duration": round(total, 1), "timeline": [(s_["kind"], round(s_["a"], 2)) for s_ in SEG],
            "thumb_ms": int(1200), "slides": slides, "story_base": story_base or (slides[0] if slides else None)}


def mock_script(fmt, items):
    import writer
    S = writer.template(fmt, items)
    P = items[0]
    S.update({"trampa": next(L for L in "ABCD" if L != P.get("letra", "A")),
              "trampa_porque": "Parece correcta porque suena a norma general, pero la buena es la otra opción.",
              "truco": "Prueba de truco corto", "truco_line": "Esto es una línea de prueba para el truco del vídeo.",
              "afirmacion": "Esta es una afirmación de prueba para el formato mito o realidad.", "veredicto": "MITO",
              "titulo_norma": P["tema"][:30], "explicacion": S.get("explicacion") or "Explicación de prueba.",
              "escena": "Turno de noche en la planta. Tu compañera te pregunta algo antes de entrar en la habitación.",
              "puntos": ["Primer punto clave de prueba del vídeo", "Segundo punto clave algo más largo de prueba",
                         "Tercer punto clave de prueba"]})
    return S


if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "pregunta_del_dia"
    out = sys.argv[2] if len(sys.argv) > 2 else f"out/test_{fmt}.mp4"
    estilo = sys.argv[3] if len(sys.argv) > 3 else "clasico"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if fmt == "flashcards_express":
        items = QB.fichas_candidates(seed=7)[:4]
    else:
        n = 3 if fmt == "simulacro_3" else 1
        items = [QB.prepare(q, 7) for q in QB.candidates(fmt, None, seed=7)[:n]]
    img = None
    if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
        img = Image.open(sys.argv[4])
    S = mock_script(fmt, items)
    print(json.dumps(build(fmt, items, S, 7, out, {"estilo": estilo}, image=img), ensure_ascii=False, indent=1))
