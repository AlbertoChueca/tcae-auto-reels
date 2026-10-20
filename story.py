"""Story de 12 s para Instagram y TikTok que anuncia el reel del día (sin desvelar la respuesta).

Parte del fotograma de la pregunta del propio reel (mismo estilo, misma tarjeta) y le añade: pegatina "NUEVO REEL",
cuenta atrás animada, reto ("¿A, B, C o D?") y "La solución, en el reel de hoy · @apruebatcae". Música suave y tics.
Las Stories se ven a menudo sin sonido, así que todo se entiende solo con la imagen.

    python story.py slide_pregunta.png out_story.mp4 [formato]
"""
import math, os, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

import fx
from fx import W, H, FPS, SR, F900, AMBER, INK, WHITE, RED, eob, eo

DUR = 12.0
HANDLE = os.environ.get("IG_HANDLE", "@apruebatcae")
ASK = {"mito_realidad": "¿MITO O REALIDAD?", "flashcards_express": "¿TE LA SABES?", "simulacro_3": "¿ACIERTAS LAS 3?",
       "legislacion_30s": "¿TE LO SABES?", "caso_practico": "¿QUÉ HARÍAS TÚ?"}


def _ring(remain, frac, size=170):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([6, 6, size - 6, size - 6], fill=(10, 14, 20, 225))
    d.arc([14, 14, size - 14, size - 14], -90, -90 + 360 * frac, fill=RED if remain <= 3 else AMBER, width=16)
    f = fx.font(F900, 78); t = str(remain)
    d.text((size / 2 - f.getlength(t) / 2, size / 2 - 52), t, font=f, fill=WHITE)
    return im


def build(base_png, out, fmt="pregunta_del_dia"):
    base = Image.open(base_png).convert("RGBA").resize((W, H))
    # como un reel compartido en story: vista previa con esquinas redondeadas sobre el fondo desenfocado
    pw, ph = int(W * 0.6), int(H * 0.6)
    small = base.resize((pw, ph), Image.LANCZOS)
    mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], 44, fill=255)
    small.putalpha(mask)
    small = fx.shadowed(small, 26, (0, 20), 120)
    from PIL import ImageFilter
    bgc = base.resize((W // 10, H // 10)).filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BILINEAR)
    bgc = Image.blend(bgc, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.25)
    sticker = fx.pill("NUEVO REEL · " + HANDLE, 40, AMBER, INK, padx=30, pady=12)
    ask = fx.headline(ASK.get(fmt, "¿A, B, C O D?"), 84, 980, 1, hot_words=())
    sol = fx.pill("RESPONDE EN EL REEL DE HOY", 40, WHITE, INK, padx=30, pady=14)
    import marca
    web = fx.pill(marca.WEB, 32, (0, 0, 0, 120), WHITE, padx=22, pady=8, path=fx.F800)
    ask_y = 300 + ph + 30 + ask.height / 2 - 20             # medido: el titular nunca pisa la pegatina de abajo
    sol_y = min(1800, ask_y + ask.height / 2 + sol.height / 2 + 10)
    n = int(DUR * FPS)
    # audio: base suave + tic cada segundo durante la cuenta atrás
    total = DUR
    a = fx.study_beat(total, 90)[: int(SR * total)] * 0.5
    for s_ in range(10):
        t = fx.tick(s_ >= 7); i = int((1.0 + s_) * SR); a[i:i + len(t)] += t[: len(a) - i]
    wav = out.replace(".mp4", ".wav"); sf.write(wav, fx.dehiss(np.tanh(a * 1.1) * 0.9), SR)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", wav, "-shortest"] + fx.enc_args(out), stdin=subprocess.PIPE)
    for fi in range(n):
        t = fi / FPS
        fr = bgc.copy()
        z = 1.0 + 0.03 * eo(t / DUR)
        im = small if z == 1 else small.resize((int(small.width * z), int(small.height * z)), Image.BILINEAR)
        fx.paste_center(fr, im, W / 2, 300 + ph / 2)
        fx.paste_center(fr, sticker, W / 2, 245, eob(t / 0.35), 1, -3)
        if 1.0 <= t < 11.0:
            lt = t - 1.0; remain = 10 - int(lt)
            fx.paste_center(fr, _ring(remain, 1 - lt / 10), W / 2 + pw / 2 - 10, 360, 1 + 0.1 * max(0, 1 - (lt % 1) * 5))
        fx.paste_center(fr, ask, W / 2, ask_y, eob((t - 0.4) / 0.35) * (1 + 0.03 * math.sin(t * 5)))
        fx.paste_center(fr, sol, W / 2, sol_y, eob((t - 0.9) / 0.35))
        fx.paste_center(fr, web, W / 2, min(1760, sol_y + 78), min(1, t / 0.5))
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait(); os.remove(wav)
    if proc.returncode:
        raise RuntimeError("ffmpeg falló al codificar la story")
    return out


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "pregunta_del_dia"))
