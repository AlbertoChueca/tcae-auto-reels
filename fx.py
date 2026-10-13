"""Piezas comunes de render (vídeo + audio) para los reels de Aprueba TCAE.

Todo se dibuja a 1080x1920 y se codifica a 720x1280 (~2,5 Mbps, AAC 48 kHz, sin edit lists, moov al principio):
vídeos ligeros (~10 MB) que la API de Instagram acepta a la primera.
Sonido 100 % tonal (sin ruido blanco) + filtro final `dehiss` como red de seguridad.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, SR = 1080, 1920, 25, 24000
OUT_W, OUT_H = 720, 1280
SAFE_TOP, SAFE_BOTTOM = 250, 1500      # la interfaz de Instagram/TikTok tapa arriba, abajo y la columna derecha
F900 = os.path.join(HERE, "fonts", "Nunito-900.ttf")
F800 = os.path.join(HERE, "fonts", "Nunito-800.ttf")
FPOP = os.path.join(HERE, "fonts", "Poppins-Bold.ttf")

# ---- marca (teal de apruebatcae.com: #1a9e8f)
TEAL = (26, 158, 143); TEAL_D = (11, 59, 54); TEAL_M = (16, 104, 94); MINT = (170, 236, 222)
AMBER = (255, 200, 87); INK = (18, 49, 45); PAPER = (251, 250, 247); MUTED = (150, 168, 164)
GREEN = (43, 182, 115); RED = (229, 72, 77); WHITE = (255, 255, 255)

_FONTS = {}


def font(path, size):
    k = (path, size)
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(path, size)
    return _FONTS[k]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eob(t, s=1.7):
    t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def eo(t): t = clamp(t); return 1 - (1 - t) ** 3
def eio(t): t = clamp(t); return 3 * t * t - 2 * t * t * t


# ------------------------------------------------------------------ texto
def wrap(words, fnt, maxw, space=None):
    """[(word, x, line)] + n_lines: reparto en líneas sin cortar palabras."""
    space = space or fnt.getlength(" ")
    out, x, line = [], 0.0, 0
    for w in words:
        wl = fnt.getlength(w)
        if x and x + wl > maxw:
            line += 1; x = 0.0
        out.append((w, x, line)); x += wl + space
    return out, line + 1


def fit_font(text, path, size, maxw, max_lines, min_size=34):
    """Tamaño de letra más grande con el que `text` cabe en max_lines líneas."""
    words = text.split()
    while size > min_size:
        _, n = wrap(words, font(path, size), maxw)
        if n <= max_lines:
            break
        size -= 2
    return size


def text_block(text, path, size, maxw, color=INK, lit=None, dim=None, align="left", line_gap=1.22):
    """Bloque de texto. lit = nº de palabras ya dichas (karaoke): esas van en `color`, el resto en `dim`."""
    words = text.split(); f = font(path, size)
    pos, n = wrap(words, f, maxw)
    lh = int(size * line_gap)
    widths = {}
    for w, x, ln in pos:
        widths[ln] = x + f.getlength(w)
    im = Image.new("RGBA", (int(maxw) + 8, lh * n + int(size * 0.35)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, (w, x, ln) in enumerate(pos):
        off = 0 if align == "left" else (maxw - widths[ln]) / 2
        c = color if (lit is None or k < lit) else (dim or MUTED)
        d.text((x + off, ln * lh), w, font=f, fill=c)
    return im


def word_img(word, size, color=WHITE, stroke=9, path=None, stroke_col=TEAL_D, shadow=True):
    """Palabra grande con contorno (ganchos y titulares)."""
    fo = font(path or F900, size)
    w = int(fo.getlength(word)) + 2 * stroke + 20
    im = Image.new("RGBA", (w, int(size * 1.4) + 2 * stroke), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shadow:
        d.text((stroke + 10 + 5, stroke + 7), word, font=fo, fill=(0, 0, 0, 120))
    d.text((stroke + 10, stroke), word, font=fo, fill=color, stroke_width=stroke, stroke_fill=stroke_col)
    return im


def headline(text, size=104, maxw=940, max_lines=3, color=WHITE, hot=AMBER, hot_words=(), stroke=9, stroke_col=TEAL_D,
             shadow=True):
    """Titular centrado de varias líneas con contorno; palabras de hot_words en color `hot`."""
    size = fit_font(text.upper(), F900, size, maxw - 40, max_lines, 54)
    ims = [word_img(w.upper(), size, hot if w.strip(".,!?¿¡:").lower() in hot_words else color, stroke, None, stroke_col, shadow)
           for w in text.split()]
    lines, cur, cw = [], [], 0
    for im in ims:
        if cur and cw + im.width > maxw:
            lines.append(cur); cur, cw = [], 0
        cur.append(im); cw += im.width - 6
    lines.append(cur)
    lh = max(i.height for i in ims) - int(size * 0.22)
    out = Image.new("RGBA", (maxw + 40, lh * len(lines) + int(size * 0.3)), (0, 0, 0, 0))
    for li, line in enumerate(lines):
        tw = sum(i.width - 6 for i in line); x = (out.width - tw) / 2
        for im in line:
            out.alpha_composite(im, (int(x), li * lh)); x += im.width - 6
    return out


def pill(txt, size, bg, fg=WHITE, padx=34, pady=14, path=None, outline=None):
    f = font(path or F900, size)
    tw = f.getlength(txt); bb = f.getbbox("ÁgÑ")
    h = bb[3] - bb[1] + 2 * pady
    im = Image.new("RGBA", (int(tw + 2 * padx), int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], im.height // 2, fill=bg,
                        outline=outline, width=4 if outline else 0)
    d.text((padx, pady - bb[1]), txt, font=f, fill=fg)
    return im


def shadowed(im, blur=22, off=(0, 18), alpha=90):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (4, 20, 18, 0)); sh.putalpha(im.getchannel("A").point(lambda a: a * alpha // 255))
    out.alpha_composite(sh, (pad + off[0], pad + off[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def paste_center(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if im is None or scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha)))
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


_BANDS = {}


def band_img(h, w=W - 80, a=120):
    k = (h, w, a)
    if k not in _BANDS:
        band = Image.new("RGBA", (w + 60, h), (0, 0, 0, 0))
        ImageDraw.Draw(band).rounded_rectangle([30, 18, w + 30, h - 18], 38, fill=(6, 30, 27, a))
        _BANDS[k] = band.filter(ImageFilter.GaussianBlur(10))
    return _BANDS[k]


def check_icon(size, color=WHITE, bg=GREEN):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, size - 1, size - 1], fill=bg)
    s = size
    d.line([(s * .27, s * .52), (s * .44, s * .68), (s * .74, s * .34)], fill=color, width=max(4, s // 9), joint="curve")
    return im


def cross_icon(size, color=WHITE, bg=RED):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, size - 1, size - 1], fill=bg); s = size; w = max(4, s // 9)
    d.line([(s * .32, s * .32), (s * .68, s * .68)], fill=color, width=w)
    d.line([(s * .68, s * .32), (s * .32, s * .68)], fill=color, width=w)
    return im


# ------------------------------------------------------------------ fondo
class Background:
    """Degradado teal profundo + luces suaves que se mueven despacio + rejilla de puntos tipo cuaderno.
    Las luces se componen a 1/4 de resolución (son difusas) y se escalan: rápido aunque se dibuje cada fotograma."""
    S = 4

    def __init__(self, seed=0, mood=TEAL):
        rng = np.random.RandomState(seed)
        w, h = W // self.S, H // self.S
        y = np.linspace(0, 1, h)[:, None, None]
        top, bot = np.array(TEAL_D, np.float32), np.array(mood, np.float32) * 0.55 + np.array(TEAL_D) * 0.45
        base = np.broadcast_to(top * (1 - y) + bot * y, (h, w, 3)).copy()
        self.base = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
        self.dots = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(self.dots)
        for yy in range(30, H, 54):
            for xx in range(27, W, 54):
                d.ellipse([xx - 2, yy - 2, xx + 2, yy + 2], fill=(255, 255, 255, 18))
        self.blobs = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(65, 115), rng.uniform(0, 6.28),
                       [MINT, TEAL, AMBER][k % 3], 40 if k % 3 == 2 else 62) for k in range(5)]
        self._cache = {}

    def _blob(self, r, col, a):
        k = (int(r), col, a)
        if k not in self._cache:
            im = Image.new("RGBA", (int(r * 2.6), int(r * 2.6)), (0, 0, 0, 0))
            ImageDraw.Draw(im).ellipse([r * .3, r * .3, r * 2.3, r * 2.3], fill=col + (a,))
            self._cache[k] = im.filter(ImageFilter.GaussianBlur(r * 0.32))
        return self._cache[k]

    def frame(self, t):
        im = self.base.copy()
        for x, y, r, ph, col, a in self.blobs:
            b = self._blob(r, col, a)
            cx = x + 18 * math.sin(t * 0.21 + ph); cy = y + 22 * math.cos(t * 0.17 + ph)
            im.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))
        im = im.resize((W, H), Image.BILINEAR)
        im.alpha_composite(self.dots)
        return im


# ------------------------------------------------------------------ audio (todo tonal)
def tone(freq, dur, decay=18, vol=0.35):
    t = np.arange(int(SR * dur)) / SR
    return (np.sin(2 * np.pi * freq * t) * np.exp(-decay * t) * vol).astype(np.float32)


def tick(high=False): return tone(1500 if high else 1150, 0.05, 70, 0.22 if high else 0.15)


def whoosh(dur=0.45):
    n = int(SR * dur); t = np.arange(n) / SR; ph = t / dur
    f = 260 + 520 * ph ** 1.4
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.35 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return (s * np.sin(np.pi * ph) ** 2 * 0.06).astype(np.float32)


def chime_ok():
    """Acierto: arpegio mayor brillante."""
    out = np.zeros(int(SR * 1.3), np.float32)
    for k, f in enumerate((659.3, 830.6, 987.8, 1318.5)):
        s = tone(f, 1.0, 4.5, 0.16); s[:int(SR * 0.6)] += tone(f * 2, 0.6, 9, 0.04)
        i = int(SR * 0.07 * k); out[i:i + len(s)] += s[: len(out) - i]
    return out


def soft_hit():
    t = np.arange(int(SR * 0.8)) / SR
    f = 55 + 60 * np.exp(-t * 18)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * np.clip(t / 0.004, 0, 1) * 0.5).astype(np.float32)


def stamp():
    """Golpe seco para el sello MITO / REALIDAD."""
    s = soft_hit() * 1.2; s[:int(SR * 0.25)] += tone(220, 0.25, 14, 0.25)
    return s


def riser(d):
    t = np.arange(int(SR * d)) / SR
    f = 220 + 900 * (t / d) ** 2
    return ((np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.1) * (t / d) ** 2).astype(np.float32)


def study_beat(total, bpm=88):
    """Base musical suave tipo 'lo-fi de estudio': bombo redondo, tic tonal y acordes de pad (sin ruido)."""
    n = int(SR * (total + 1)); out = np.zeros(n, np.float32)
    step = 60 / bpm / 2
    t = np.arange(int(SR * 0.3)) / SR
    kick = (np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-t * 28)) / SR) * np.exp(-t * 10) * 0.55).astype(np.float32)
    hat = tone(3200, 0.04, 120, 0.035)
    chords = [(220.0, 261.6, 329.6), (196.0, 246.9, 293.7), (174.6, 220.0, 261.6), (196.0, 246.9, 329.6)]
    i, tt = 0, 0.0
    while tt < total:
        k = int(tt * SR)
        if i % 4 == 0:
            out[k:k + len(kick)] += kick[: n - k]
        elif i % 2 == 1:
            out[k:k + len(hat)] += hat[: n - k]
        if i % 16 == 0:                                        # un acorde cada compás
            dur = step * 16; tc = np.arange(int(SR * dur)) / SR
            env = np.clip(tc / 0.6, 0, 1) * np.clip((dur - tc) / 0.8, 0, 1)
            pad = sum(np.sin(2 * np.pi * f * tc) + 0.3 * np.sin(2 * np.pi * f * 2.001 * tc) for f in chords[(i // 16) % 4])
            pad = (pad * env * 0.025).astype(np.float32)
            out[k:k + len(pad)] += pad[: n - k]
        tt += step; i += 1
    return out


def dehiss(a, sr=SR):
    """Red de seguridad sobre toda la banda sonora: cualquier tramo >= 80 ms que suene a ruido blanco se silencia."""
    a = np.asarray(a, np.float32); fr = int(sr * 0.02); n = len(a) // fr
    if n < 5:
        return a
    F = a[: n * fr].reshape(n, fr)
    X = np.abs(np.fft.rfft(F * np.hanning(fr), axis=1)) + 1e-9
    flat = np.exp(np.mean(np.log(X[:, 3:]), axis=1)) / np.mean(X[:, 3:], axis=1)
    rms = np.sqrt(np.mean(F ** 2, axis=1)); top = np.percentile(rms, 95) + 1e-9
    bad = (flat > 0.78) & (rms > 0.004 * top)
    g = np.ones(n, np.float32); i = 0
    while i < n:
        if bad[i]:
            j = i
            while j < n and bad[j]: j += 1
            if j - i >= 4: g[i:j] = 0.05
            i = j
        else:
            i += 1
    if g.min() == 1:
        return a
    gs = np.concatenate([np.repeat(g, fr), np.ones(len(a) - n * fr, np.float32)])
    gs = np.convolve(gs, np.ones(int(sr * 0.012)) / int(sr * 0.012), "same")
    print(f"audio: eliminados {int(np.sum(g < 1)) * 20} ms de siseo", flush=True)
    return (a * gs).astype(np.float32)


def enc_args(out, scale=True):
    return ((["-vf", f"scale={OUT_W}:{OUT_H}:flags=bicubic"] if scale else []) +
            ["-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high", "-crf", "23", "-maxrate", "2500k",
             "-bufsize", "5000k", "-g", str(FPS * 2), "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", "-use_editlist", "0", out])
