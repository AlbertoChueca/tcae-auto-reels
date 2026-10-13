"""Estilos visuales de los reels. Cada estilo cambia fondo, tarjetas, tipografía, forma de marcar la respuesta y colores,
pero todos respetan la zona segura y la marca (Aprueba TCAE). El piloto automático prueba cuál funciona mejor.

  marca     como la web app: fondo claro, tarjetas blancas, teal #1a9e8f y dorado (por defecto)
  clasico   tarjetas blancas sobre teal oscuro de la marca
  cuaderno  hoja de libreta con renglones, subrayador amarillo y post-it
  examen    hoja de examen oficial sobre la mesa: casillas que se marcan con bolígrafo azul
  noche     "estudiando de noche": azul marino, estrellas y acentos neón (ideal a las 21:30)
  minimal   editorial: fondo claro, tipografía negra grande y un único acento coral
  ilustrado imagen original generada por la ilustradora (IA) de fondo, con tarjetas encima
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

import fx
from fx import W, H, TEAL, TEAL_D, TEAL_M, MINT, AMBER, INK, PAPER, GREEN, RED, WHITE, BG, BORDER, MUTED, TEAL_DEEP

STYLES = ["marca", "clasico", "cuaderno", "examen", "noche", "minimal", "ilustrado"]


# ------------------------------------------------------------------ fondos
class GradientBG:
    """Degradado vertical + luces difusas que se mueven + patrón (puntos, renglones, estrellas, cuadrícula)."""
    S = 4

    def __init__(self, top, bottom, pattern="dots", blobs=(MINT, TEAL, AMBER), blob_alpha=60, seed=0, pat_col=(255, 255, 255, 18)):
        rng = np.random.RandomState(seed)
        w, h = W // self.S, H // self.S
        y = np.linspace(0, 1, h)[:, None, None]
        base = np.broadcast_to(np.array(top, np.float32) * (1 - y) + np.array(bottom, np.float32) * y, (h, w, 3)).copy()
        self.base = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
        self.pat = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(self.pat)
        self.stars = []
        if pattern == "dots":
            for yy in range(30, H, 54):
                for xx in range(27, W, 54):
                    d.ellipse([xx - 2, yy - 2, xx + 2, yy + 2], fill=pat_col)
        elif pattern == "lines":                                   # libreta: renglones + margen rojo
            for yy in range(150, H, 62):
                d.line([(0, yy), (W, yy)], fill=(120, 160, 220, 90), width=3)
            d.line([(118, 0), (118, H)], fill=(230, 90, 90, 120), width=4)
            for yy in (300, 900, 1500):
                d.ellipse([28, yy - 22, 72, yy + 22], fill=(0, 0, 0, 0), outline=(150, 150, 150, 120), width=4)
        elif pattern == "grid":
            for yy in range(0, H, 46):
                d.line([(0, yy), (W, yy)], fill=pat_col, width=1)
            for xx in range(0, W, 46):
                d.line([(xx, 0), (xx, H)], fill=pat_col, width=1)
        elif pattern == "stars":
            self.stars = [(rng.uniform(0, W), rng.uniform(0, H * 0.75), rng.uniform(1.5, 3.5), rng.uniform(0, 6.28))
                          for _ in range(90)]
        self.blobs = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(65, 115), rng.uniform(0, 6.28),
                       blobs[k % len(blobs)], blob_alpha) for k in range(5)] if blobs else []
        self._cache = {}

    def _blob(self, r, col, a):
        k = (int(r), col, a)
        if k not in self._cache:
            im = Image.new("RGBA", (int(r * 2.6), int(r * 2.6)), (0, 0, 0, 0))
            ImageDraw.Draw(im).ellipse([r * .3, r * .3, r * 2.3, r * 2.3], fill=tuple(col[:3]) + (a,))
            self._cache[k] = im.filter(ImageFilter.GaussianBlur(r * 0.32))
        return self._cache[k]

    def frame(self, t):
        im = self.base.copy()
        for x, y, r, ph, col, a in self.blobs:
            b = self._blob(r, col, a)
            cx = x + 18 * math.sin(t * 0.21 + ph); cy = y + 22 * math.cos(t * 0.17 + ph)
            im.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))
        im = im.resize((W, H), Image.BILINEAR)
        im.alpha_composite(self.pat)
        if self.stars:
            d = ImageDraw.Draw(im)
            for x, y, r, ph in self.stars:
                a = int(120 + 120 * math.sin(t * 1.7 + ph))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, max(30, a)))
        return im


class ImageBG:
    """Imagen original de fondo: movimiento lento tipo Ken Burns, oscurecida para que las tarjetas se lean."""

    def __init__(self, img, dark=0.55, blur=6):
        im = img.convert("RGB")
        r = max(W * 1.12 / im.width, H * 1.12 / im.height)
        im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
        self.sharp = im
        soft = im.filter(ImageFilter.GaussianBlur(blur)) if blur else im
        self.soft = Image.blend(soft, Image.new("RGB", soft.size, (6, 22, 20)), dark)
        self.mode = "soft"

    def frame(self, t, sharp=False):
        src = self.sharp if sharp else self.soft
        z = 1.0 + 0.05 * (0.5 - 0.5 * math.cos(min(t, 60) / 60 * math.pi))
        vw, vh = src.width / 1.12 / z * 1.0, src.height / 1.12 / z
        x0 = (src.width - vw) / 2 + 20 * math.sin(t * 0.05); y0 = (src.height - vh) / 2
        return src.crop((int(x0), int(y0), int(x0 + vw), int(y0 + vh))).resize((W, H), Image.BILINEAR).convert("RGBA")


# ------------------------------------------------------------------ temas (todos con los colores de apruebatcae.com)
class Theme:
    def __init__(self, name, **kw):
        self.name = name
        # valores por defecto = clásico (teal oscuro de la marca + tarjetas blancas)
        self.card_fill, self.card_outline, self.card_radius, self.shadow = PAPER, None, 40, True
        self.ink, self.dim, self.label = INK, (176, 186, 198), TEAL
        self.accent, self.accent_fg = TEAL, WHITE
        self.row_fill, self.row_active, self.row_outline, self.row_radius = BG, MINT, TEAL, 24
        self.ok_mode, self.ok_col, self.ok_text = "fill", GREEN, WHITE
        self.bad_col, self.bad_fill = RED, (253, 236, 236)
        self.faded = (226, 231, 236)
        self.letter = "circle"
        self.title_bg, self.title_fg = AMBER, INK
        self.badge_bg, self.badge_fg, self.chip_bg, self.chip_fg = AMBER, INK, (255, 255, 255, 46), WHITE
        self.head_col, self.head_hot, self.head_stroke, self.head_stroke_col, self.head_shadow = WHITE, AMBER, 9, TEAL_DEEP, True
        self.sub_band, self.sub_ink, self.sub_dim = (8, 60, 54, 150), WHITE, (160, 205, 198)
        self.ring_bg, self.ring_col, self.ring_fg = (8, 60, 54, 235), AMBER, WHITE
        self.pill_bg, self.pill_fg, self.pill_outline = TEAL_DEEP, WHITE, MINT
        self.big_col = TEAL_D
        self.ref_bg, self.ref_fg = MINT, TEAL_D
        self.burst = [GREEN, AMBER, MINT, WHITE]
        self.web_bg, self.web_fg = (255, 255, 255, 60), WHITE      # marca de agua con la web (arriba)
        self.header = None                   # texto de cabecera de la hoja (estilo examen)
        self.music_bpm = 88
        self.__dict__.update(kw)

    def background(self, seed, image=None):
        n = self.name
        if n == "marca":
            return GradientBG(BG, MINT, "dots", blobs=(TEAL, AMBER, (180, 230, 222)), blob_alpha=30, seed=seed,
                              pat_col=(26, 158, 143, 26))
        if n == "cuaderno":
            return GradientBG((252, 250, 243), (246, 243, 232), "lines", blobs=((232, 201, 61), (180, 230, 222)), blob_alpha=38, seed=seed)
        if n == "examen":
            return GradientBG((222, 230, 232), (196, 210, 212), "grid", blobs=((255, 255, 255), MINT), blob_alpha=50,
                              seed=seed, pat_col=(255, 255, 255, 40))
        if n == "noche":
            return GradientBG((3, 26, 24), (10, 66, 60), "stars", blobs=((26, 158, 143), (95, 211, 196), (232, 201, 61)),
                              blob_alpha=42, seed=seed)
        if n == "minimal":
            return GradientBG((250, 251, 251), (243, 246, 246), "none", blobs=(MINT,), blob_alpha=40, seed=seed)
        if n == "ilustrado" and image is not None:
            return ImageBG(image)
        return GradientBG(TEAL_DEEP, TEAL_D, "dots", blobs=(MINT, TEAL, AMBER), seed=seed)


def get(name):
    light = dict(head_col=INK, head_hot=TEAL, head_stroke=6, head_stroke_col=WHITE, head_shadow=False,
                 sub_band=(255, 255, 255, 235), sub_ink=INK, sub_dim=(170, 180, 190),
                 ring_bg=(255, 255, 255, 245), ring_col=TEAL, ring_fg=INK, pill_bg=TEAL, pill_fg=WHITE, pill_outline=None,
                 chip_bg=(255, 255, 255, 255), chip_fg=TEAL_D, web_bg=(255, 255, 255, 220), web_fg=TEAL_D)
    if name == "marca":
        return Theme("marca", card_outline=BORDER, card_radius=32, badge_bg=TEAL, badge_fg=WHITE,
                     burst=[GREEN, TEAL, AMBER], **light)
    if name == "cuaderno":
        return Theme("cuaderno", card_outline=BORDER, card_radius=16, label=TEAL_D, row_fill=(248, 250, 250),
                     row_radius=12, ok_mode="marker", ok_col=AMBER, ok_text=INK, letter="circle_outline",
                     badge_bg=AMBER, badge_fg=INK, burst=[AMBER, TEAL, RED], music_bpm=84, **light)
    if name == "examen":
        return Theme("examen", card_outline=(205, 212, 220), card_radius=8, label=MUTED, accent=INK, accent_fg=INK,
                     row_fill=PAPER, row_active=MINT, row_outline=TEAL_D, row_radius=6, ok_mode="pen", ok_col=TEAL_D,
                     ok_text=TEAL_D, letter="box", title_bg=TEAL_D, title_fg=WHITE, badge_bg=INK, badge_fg=WHITE,
                     big_col=TEAL_D, ref_bg=BG, ref_fg=INK, burst=[TEAL_D, RED, INK],
                     header="OPOSICIÓN TCAE · SALUD ARAGÓN", music_bpm=80,
                     **{**light, "ring_col": TEAL_D, "pill_bg": INK})
    if name == "noche":
        neon = (95, 211, 196)
        return Theme("noche", card_fill=(10, 44, 41, 240), card_outline=(40, 120, 110), ink=WHITE, dim=(110, 150, 145),
                     label=neon, accent=neon, accent_fg=TEAL_DEEP, row_fill=(18, 62, 58), row_active=(26, 84, 78),
                     row_outline=neon, ok_col=(70, 210, 140), ok_text=(6, 32, 20), bad_fill=(80, 30, 34), faded=(60, 92, 88),
                     badge_bg=neon, badge_fg=TEAL_DEEP, sub_band=(2, 20, 18, 160), ring_bg=(2, 24, 22, 235), ring_col=AMBER,
                     pill_bg=(2, 24, 22), pill_outline=neon, big_col=neon, ref_bg=(22, 70, 64), ref_fg=neon,
                     burst=[(70, 210, 140), neon, AMBER, WHITE], music_bpm=82)
    if name == "minimal":
        return Theme("minimal", card_outline=BORDER, card_radius=28, shadow=False, label=TEAL, accent=INK,
                     row_fill=(246, 248, 248), ok_col=TEAL, letter="square", title_bg=TEAL, title_fg=WHITE,
                     badge_bg=INK, badge_fg=WHITE, burst=[TEAL, INK, AMBER], music_bpm=92,
                     **{**light, "head_stroke": 0, "sub_band": (255, 255, 255, 0), "pill_bg": INK})
    if name == "ilustrado":
        return Theme("ilustrado", card_fill=PAPER + (246,), sub_band=(0, 0, 0, 140))
    return Theme("clasico")
