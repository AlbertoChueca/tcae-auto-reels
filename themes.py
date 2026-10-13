"""Estilos visuales de los reels. Cada estilo cambia fondo, tarjetas, tipografía, forma de marcar la respuesta y colores,
pero todos respetan la zona segura y la marca (Aprueba TCAE). El piloto automático prueba cuál funciona mejor.

  clasico   tarjetas blancas sobre teal profundo (marca)
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
from fx import W, H, TEAL, TEAL_D, TEAL_M, MINT, AMBER, INK, PAPER, GREEN, RED, WHITE

STYLES = ["clasico", "cuaderno", "examen", "noche", "minimal", "ilustrado"]


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


# ------------------------------------------------------------------ temas
class Theme:
    def __init__(self, name, **kw):
        self.name = name
        # valores por defecto = clásico
        self.card_fill, self.card_outline, self.card_radius, self.shadow = PAPER, None, 46, True
        self.ink, self.dim, self.label = INK, (170, 186, 182), TEAL
        self.accent, self.accent_fg = TEAL, WHITE
        self.row_fill, self.row_active, self.row_outline, self.row_radius = (236, 244, 242), (222, 242, 237), TEAL, 28
        self.ok_mode, self.ok_col, self.ok_text = "fill", GREEN, WHITE
        self.bad_col, self.bad_fill = RED, (253, 232, 232)
        self.faded = (238, 238, 238)
        self.letter = "circle"
        self.title_bg, self.title_fg = AMBER, INK
        self.badge_bg, self.badge_fg, self.chip_bg, self.chip_fg = AMBER, INK, (255, 255, 255, 40), WHITE
        self.head_col, self.head_hot, self.head_stroke, self.head_stroke_col, self.head_shadow = WHITE, AMBER, 9, TEAL_D, True
        self.sub_band, self.sub_ink, self.sub_dim = (6, 30, 27, 120), WHITE, (150, 190, 182)
        self.ring_bg, self.ring_col, self.ring_fg = (6, 30, 27, 230), AMBER, WHITE
        self.pill_bg, self.pill_fg, self.pill_outline = TEAL_D, WHITE, MINT
        self.big_col = TEAL_M
        self.ref_bg, self.ref_fg = (226, 240, 236), TEAL_M
        self.burst = [GREEN, AMBER, MINT, WHITE]
        self.brand_bg = PAPER
        self.header = None                   # texto de cabecera de la hoja (estilo examen)
        self.music_bpm = 88
        self.__dict__.update(kw)

    def background(self, seed, image=None):
        n = self.name
        if n == "cuaderno":
            return GradientBG((252, 249, 240), (246, 241, 228), "lines", blobs=((255, 236, 150), (190, 220, 255)), blob_alpha=40, seed=seed)
        if n == "examen":
            return GradientBG((214, 220, 229), (186, 196, 210), "grid", blobs=((255, 255, 255), (200, 210, 230)), blob_alpha=50,
                              seed=seed, pat_col=(255, 255, 255, 40))
        if n == "noche":
            return GradientBG((8, 12, 34), (30, 24, 72), "stars", blobs=((120, 90, 255), (40, 200, 220), (255, 200, 120)),
                              blob_alpha=45, seed=seed)
        if n == "minimal":
            return GradientBG((246, 244, 239), (240, 237, 230), "none", blobs=((255, 200, 180),), blob_alpha=25, seed=seed)
        if n == "ilustrado" and image is not None:
            return ImageBG(image)
        return GradientBG(TEAL_D, tuple(int(a * 0.55 + b * 0.45) for a, b in zip(TEAL, TEAL_D)), "dots", seed=seed)


def get(name):
    if name == "cuaderno":
        navy, blue = (28, 38, 84), (46, 86, 196)
        return Theme("cuaderno", card_fill=(255, 255, 255), card_outline=(214, 222, 236), card_radius=18,
                     ink=navy, dim=(178, 186, 206), label=blue, accent=blue, row_fill=(244, 247, 253),
                     row_active=(232, 240, 255), row_outline=blue, row_radius=14, ok_mode="marker",
                     ok_col=(255, 226, 70), ok_text=navy, letter="circle_outline", title_bg=(255, 226, 70), title_fg=navy,
                     badge_bg=(255, 226, 70), badge_fg=navy, chip_bg=(255, 255, 255, 230), chip_fg=blue,
                     head_col=navy, head_hot=(229, 72, 77), head_stroke=8, head_stroke_col=(255, 255, 255), head_shadow=False,
                     sub_band=(255, 255, 255, 225), sub_ink=navy, sub_dim=(170, 178, 200),
                     ring_bg=(255, 255, 255, 240), ring_col=blue, ring_fg=navy,
                     pill_bg=(255, 255, 255), pill_fg=navy, pill_outline=blue, big_col=blue,
                     ref_bg=(236, 242, 255), ref_fg=blue, burst=[(255, 226, 70), blue, (229, 72, 77)], music_bpm=84)
    if name == "examen":
        ink, pen = (24, 26, 32), (31, 64, 186)
        return Theme("examen", card_fill=(255, 255, 255), card_outline=(205, 210, 220), card_radius=8,
                     ink=ink, dim=(176, 180, 190), label=(90, 96, 110), accent=ink, accent_fg=ink,
                     row_fill=(255, 255, 255), row_active=(240, 244, 255), row_outline=pen, row_radius=6,
                     ok_mode="pen", ok_col=pen, ok_text=pen, letter="box", title_bg=pen, title_fg=WHITE,
                     badge_bg=ink, badge_fg=WHITE, chip_bg=(255, 255, 255, 235), chip_fg=ink,
                     head_col=ink, head_hot=pen, head_stroke=0, head_stroke_col=WHITE, head_shadow=False,
                     sub_band=(255, 255, 255, 230), sub_ink=ink, sub_dim=(170, 174, 186),
                     ring_bg=(255, 255, 255, 245), ring_col=pen, ring_fg=ink, pill_bg=ink, pill_fg=WHITE, pill_outline=None,
                     big_col=pen, ref_bg=(238, 241, 248), ref_fg=ink, burst=[pen, (229, 72, 77), (60, 60, 70)],
                     header="OPOSICIÓN TCAE · SALUD ARAGÓN", music_bpm=80)
    if name == "noche":
        neon, glass = (122, 162, 255), (24, 30, 64)
        return Theme("noche", card_fill=glass + (238,), card_outline=(90, 110, 200), card_radius=40,
                     ink=WHITE, dim=(110, 120, 168), label=neon, accent=neon, accent_fg=(10, 14, 40),
                     row_fill=(38, 46, 92), row_active=(50, 62, 124), row_outline=neon,
                     ok_col=(64, 224, 150), ok_text=(8, 30, 20), bad_fill=(80, 30, 50), faded=(70, 76, 110),
                     title_bg=neon, title_fg=(10, 14, 40), badge_bg=neon, badge_fg=(10, 14, 40),
                     chip_bg=(255, 255, 255, 35), chip_fg=WHITE, head_hot=(255, 210, 120), head_stroke_col=(10, 14, 40),
                     sub_band=(8, 10, 30, 150), sub_dim=(120, 130, 190), ring_bg=(10, 14, 40, 230), ring_col=neon,
                     pill_bg=(10, 14, 40), pill_outline=neon, big_col=neon, ref_bg=(44, 54, 104), ref_fg=neon,
                     burst=[(64, 224, 150), neon, (255, 210, 120), WHITE], brand_bg=PAPER, music_bpm=82)
    if name == "minimal":
        blk, coral = (17, 17, 17), (255, 94, 58)
        return Theme("minimal", card_fill=(255, 255, 255), card_outline=(225, 222, 214), card_radius=30, shadow=False,
                     ink=blk, dim=(190, 186, 178), label=coral, accent=blk, row_fill=(246, 244, 239), row_active=(255, 236, 228),
                     row_outline=coral, ok_col=blk, ok_text=WHITE, letter="square", title_bg=coral, title_fg=WHITE,
                     badge_bg=blk, badge_fg=WHITE, chip_bg=(0, 0, 0, 0), chip_fg=blk,
                     head_col=blk, head_hot=coral, head_stroke=0, head_stroke_col=WHITE, head_shadow=False,
                     sub_band=(255, 255, 255, 0), sub_ink=blk, sub_dim=(190, 186, 178), ring_bg=(17, 17, 17, 255),
                     ring_col=coral, pill_bg=blk, pill_fg=WHITE, pill_outline=None, big_col=coral,
                     ref_bg=(246, 244, 239), ref_fg=blk, burst=[coral, blk, (255, 190, 170)], music_bpm=92)
    if name == "ilustrado":
        return Theme("ilustrado", card_fill=PAPER + (246,), sub_band=(0, 0, 0, 140))
    return Theme("clasico")
