"""Vídeos "EXPLICADOS": un tema del temario contado en 40-50 s con ilustraciones de neón, rótulos grandes y datos.

Qué es: el formato de divulgación animada que mejor funciona ahora mismo en redes (una situación en segunda persona ->
qué pasa por dentro y por qué -> el dato clave -> qué hace la TCAE -> idea para llevarse -> "pásaselo a..."), con los
colores de Aprueba TCAE sobre fondo oscuro: teal neón, menta y dorado.

Cómo se hace cada vídeo:
  1. Tema: el que lleva más tiempo sin explicarse (los de actualidad del cazatendencias primero). Solo temario sanitario.
  2. Guion (IA): 5-7 escenas. Cada una lleva la voz, 1-3 rótulos (palabras literales de la voz), un dibujo y, si toca,
     un dato en pantalla (cifra con contador, lista de pasos o "NO esto / SÍ esto").
  3. Verificación: el verificador (modelo "pro") contrasta frase a frase la voz, los rótulos, los datos y la
     descripción con el material de la app de ese tema. Si algo no está respaldado se reescribe una vez; si sigue sin
     pasar, se prueba otro tema; si ninguno pasa, esa noche sale el reel tipo test de siempre.
  4. Ilustraciones (IA de imagen): una por escena, todas con el mismo estilo (la primera sirve de referencia), sin
     texto ni personas reconocibles. Cada una pasa una revisión (sin letras, sin nada desagradable, sin contradecir la
     voz) y un etalonaje a los colores de la marca. Si una no sale, la escena usa un fondo de neón dibujado en código.
  5. Render: movimiento de cámara en cada ilustración, rótulos que entran cuando la voz dice la palabra, subtítulos
     tipo karaoke arriba, datos animados y cierre "pásaselo" (móvil enviando el vídeo) + la web.

    python explica.py [tema]      DRY_RUN=true: solo genera · QUIZ_MOCK=1 VOICE_ENGINE=mock: sin IA (prueba de diseño)
"""
import datetime, json, math, os, random, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import fx
import marca
import questions as QB
from fx import W, H, FPS, SR, clamp, eo, eob, eio

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "explicados.json")
MOCK = os.environ.get("QUIZ_MOCK") == "1"
FMT = "explicado"
FP, F9, F8 = fx.FPOP, fx.F900, fx.F800

# la marca en versión "neón sobre oscuro": mismo teal, menta y dorado de apruebatcae.com
BG0 = (5, 22, 26); BG1 = (9, 46, 48); NEON = (47, 224, 200); MINT = (196, 246, 238); AMBER = (242, 207, 72)
CORAL = (255, 104, 124); WHITE = (255, 255, 255); INK = (8, 34, 36)
TONE = {"neutro": WHITE, "bien": NEON, "alerta": CORAL, "dato": AMBER}
SUB_Y, ROT_Y = 330, 520                                   # subtítulos arriba y rótulo debajo (como el formato original)
CTA1 = "Pásaselo a esa compañera que se lo está preparando contigo."
CTA2 = "Y practica este tema gratis en apruebatcae.com."


# ------------------------------------------------------------------ 1. tema y material
def log():
    try:
        return json.load(open(LOG))
    except Exception:
        return []


def topics():
    import chuleta
    return [t for t in chuleta.topics() if QB.tema_de(t)[1] == "clinico"]


def pick_topics(seed, n=3):
    """Temas candidatos: los de actualidad primero y, después, los que llevan más tiempo sin vídeo."""
    L = log(); last = {}
    for i, e in enumerate(L):
        last[e.get("topic")] = i
    ts = topics(); random.Random(seed).shuffle(ts)
    try:
        import tendencias
        hot = set(tendencias.topics_hot())
    except Exception:
        hot = set()
    ts.sort(key=lambda t: (t not in hot or last.get(t, -1) >= len(L) - 8, last.get(t, -1)))
    return ts[:n]


# ------------------------------------------------------------------ 2. guion (IA) y verificación
ROLE = """Eres la guionista de los vídeos EXPLICADOS de Aprueba TCAE (apruebatcae.com), una web app de tests para las
oposiciones de TCAE (Técnico en Cuidados Auxiliares de Enfermería) de toda España. Haces vídeos verticales de 40-50
segundos de divulgación animada: cuentas UNA idea del temario como una pequeña historia, con una situación real de
planta o de examen, el porqué de lo que pasa y qué hace la TCAE. Hablas de tú, en español de España, con frases cortas
y habladas (como se lo contarías a una compañera en el descanso), sin tecnicismos gratuitos, sin infantilizar, sin
promesas ("esto cae seguro") y sin estadísticas o cifras que no estén en el material."""

SCHEMA = """{
 "subtema": str (la idea concreta del vídeo, 2-7 palabras),
 "titulo": str (4-9 palabras, título del vídeo, con gancho y sin clickbait falso),
 "escenas": [ (de 5 a 7 escenas, en este orden narrativo)
   {"voz": str (8-22 palabras; lo que dice la voz en esa escena),
    "rotulos": [str] (1-3 rótulos que van saliendo en grande; cada uno son 1-3 palabras LITERALES y seguidas de "voz", en MAYÚSCULAS),
    "tono": "neutro" | "bien" | "alerta" | "dato",
    "dibujo": str (EN INGLÉS, 12-30 palabras: qué se ve en la ilustración de esa escena),
    "dibujo_b": str o "" (EN INGLÉS, opcional y como mucho en 2 escenas: la MISMA escena un instante después, cuando algo cambia),
    "dato": null | {"tipo": "cifra", "valor": str (p. ej. "2", "30º", "37,5"), "unidad": str (1-2 palabras), "etiqueta": str (2-5 palabras)}
                 | {"tipo": "lista", "items": [str] (2-4 pasos o elementos, 1-4 palabras cada uno)}
                 | {"tipo": "versus", "no": str (1-4 palabras), "si": str (1-4 palabras)} } ],
 "caption_gancho": str (máx. 14 palabras, 1 emoji: la duda o situación que abre la descripción),
 "caption_cuerpo": str (35-70 palabras: lo que explica el vídeo, para quien lee sin sonido; solo datos del material),
 "pregunta_comentarios": str (máx. 18 palabras: una pregunta fácil de contestar que invite a comentar su experiencia o su duda)
}"""

GUIDE = """ESTRUCTURA (es lo que hace que estos vídeos se vean hasta el final):
- Escena 1 = GANCHO: una situación concreta en SEGUNDA PERSONA y en presente, como si le estuviera pasando ahora
  ("Entras en la habitación y tu paciente...", "Estás en el examen y dudas entre..."). Máx. 14 palabras. Sin saludar,
  sin presentarte y sin "hoy vamos a ver".
- Escenas 2-3 = QUÉ PASA Y POR QUÉ: el mecanismo, contado paso a paso y de forma visual.
- Una escena con EL DATO CLAVE del material (una cifra, un tiempo, un orden): ponlo en "dato" SOLO si está en el material.
- Una escena con QUÉ HACE LA TCAE (pasos o elementos concretos: "dato" tipo lista).
- Última escena = IDEA PARA LLEVARSE, corta y redonda ("no es X: es Y"), con "dato" tipo versus: "no" = la idea
  equivocada o lo que NO hay que hacer y "si" = la correcta, cada una entendible por sí sola en 1-4 palabras y sin
  dos puntos (p. ej. no: "MÁS CREMAS", si: "MENOS PRESIÓN").
Lo ideal son 6 escenas y entre 85 y 125 palabras de voz en total. Cada frase añade algo; nada de relleno ("en este
vídeo te explico", "recuerda para tu examen").
RÓTULOS: son el resumen visual. Palabras literales de la voz de esa escena, las que llevan la idea (un verbo, un
término, una cifra). El primer rótulo de la escena 1 tiene que enganchar por sí solo.
DIBUJOS: cada dibujo ENSEÑA lo que dice la voz en esa escena, no decora: el órgano o la zona del cuerpo en esquema
con lo que le pasa resaltado (un vaso que se estrecha, una zona de piel aplastada contra el colchón, el aire entrando
en los pulmones), el objeto que se usa o la situación en la habitación. Nada de libretas, escritorios u objetos de
oficina. Las personas, siempre figuras simples sin cara. No pidas dibujar una técnica o una postura exacta (puede
quedar mal): mejor el objeto, el órgano o la situación. Nunca texto, letras, números, sangre, heridas, agujas en la
piel ni desnudos.
DIBUJO_B: úsalo en 1 o 2 escenas en las que algo CAMBIA mientras habla la voz (el vaso abierto -> el vaso obstruido;
la piel normal -> la piel enrojecida): "dibujo" es el antes y "dibujo_b" el después, con el mismo encuadre."""


def _playbook():
    """Lo que la revisión semanal ha aprendido de los explicados que mejor funcionan (solo estilo, no datos)."""
    try:
        import strategy
        pb = strategy.playbook_of("explicados")
        return ("LO QUE MEJOR FUNCIONA EN NUESTROS VÍDEOS EXPLICADOS (para elegir idea y gancho; no añade datos al material):\n" + pb[:900]) if pb else ""
    except Exception:
        return ""


def write(tema, mat, notes=None, avoid=()):
    import gemini
    try:
        import tendencias
        hot = "\n".join(tendencias.material_lines(next((t for t in topics() if QB.tema_de(t)[0] == tema), "")))
    except Exception:
        hot = ""
    prompt = f"""{ROLE}

TEMA: {tema}
MATERIAL DE LA APP (lo ÚNICO que puedes afirmar; no añadas datos, cifras ni ejemplos que no estén aquí):
{mat}
{("ACTUALIDAD (opcional, solo si encaja de verdad con la idea):" + chr(10) + hot) if hot else ""}
{("IDEAS YA HECHAS de este tema (elige otra distinta): " + "; ".join(avoid)) if avoid else ""}
{("CORRIGE estos problemas del intento anterior: " + json.dumps(notes, ensure_ascii=False)[:1200]) if notes else ""}
{_playbook()}

Elige dentro del tema UNA idea que tenga un PORQUÉ (un mecanismo, una causa, un orden con sentido) y que confunda en
los test, y escribe el vídeo.
{GUIDE}

Devuelve SOLO JSON con esta forma:
{SCHEMA}"""
    return gemini.ask(prompt, 0.8)


def _wc(s):
    return len(str(s or "").split())


def _one(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _norm(w):
    import unicodedata
    w = unicodedata.normalize("NFD", str(w).lower())
    return re.sub(r"[^a-z0-9ñ]", "", "".join(c for c in w if unicodedata.category(c) != "Mn" or c == "̃"))


def _find(words, phrase, start=0):
    """Índice de la primera palabra de `phrase` dentro de `words` (comparación sin tildes ni signos) o None."""
    ws = [_norm(w) for w in words]; ph = [p for p in (_norm(x) for x in str(phrase).split()) if p]
    if not ph:
        return None
    for i in range(start, len(ws) - len(ph) + 1):
        if ws[i:i + len(ph)] == ph:
            return i
    return None


def clean(c):
    """Valida forma y medidas: lo que no cabe en pantalla o no se puede sincronizar con la voz se descarta."""
    scenes = []
    for s in (c.get("escenas") or [])[:7]:
        voz = _one(s.get("voz"))
        if not 5 <= _wc(voz) <= 26:
            raise ValueError(f"escena con voz fuera de medida ({_wc(voz)} palabras)")
        if voz[-1] not in ".?!…":
            voz += "."
        rots = []
        for r in (s.get("rotulos") or [])[:3]:
            r = _one(r).upper().strip(".,;:")
            if 1 <= _wc(r) <= 3 and len(r) <= 24 and _find(voz.split(), r) is not None and r not in rots:
                rots.append(r)
        if not rots:
            raise ValueError("escena sin rótulos literales de la voz")
        rots.sort(key=lambda r: _find(voz.split(), r))
        d = s.get("dato") if isinstance(s.get("dato"), dict) else None
        dato = None
        if d and d.get("tipo") == "cifra" and 1 <= len(_one(d.get("valor"))) <= 6 and re.search(r"\d", str(d.get("valor"))):
            dato = {"tipo": "cifra", "valor": _one(d["valor"]), "unidad": _one(d.get("unidad")).upper()[:18],
                    "etiqueta": _one(d.get("etiqueta"))[:40]}
        elif d and d.get("tipo") == "lista":
            items = [_one(x) for x in (d.get("items") or []) if 1 <= _wc(x) <= 5 and len(_one(x)) <= 30][:4]
            if len(items) >= 2:
                dato = {"tipo": "lista", "items": items}
        elif d and d.get("tipo") == "versus" and 1 <= _wc(d.get("no")) <= 5 and 1 <= _wc(d.get("si")) <= 5:
            dato = {"tipo": "versus", "no": _one(d["no"]).upper()[:28], "si": _one(d["si"]).upper()[:28]}
        scenes.append({"voz": voz, "rotulos": rots, "tono": s.get("tono") if s.get("tono") in TONE else "neutro",
                       "dibujo": _one(s.get("dibujo"))[:320], "dibujo_b": _one(s.get("dibujo_b"))[:320], "dato": dato})
    if not 5 <= len(scenes) <= 7:
        raise ValueError("hacen falta de 5 a 7 escenas")
    total = sum(_wc(s["voz"]) for s in scenes)
    if not 70 <= total <= 135:
        raise ValueError(f"la voz tiene {total} palabras (debe tener entre 85 y 125)")
    if _wc(scenes[0]["voz"]) > 16:
        raise ValueError("el gancho (escena 1) pasa de 14 palabras")
    extra = [i for i, s in enumerate(scenes) if s["dibujo_b"]]
    for i in extra[2:]:
        scenes[i]["dibujo_b"] = ""
    out = {"subtema": _one(c.get("subtema"))[:60], "titulo": _one(c.get("titulo")).rstrip("."), "escenas": scenes,
           "caption_gancho": _one(c.get("caption_gancho")), "caption_cuerpo": _one(c.get("caption_cuerpo")),
           "pregunta_comentarios": _one(c.get("pregunta_comentarios"))}
    if not (3 <= _wc(out["titulo"]) <= 11 and 3 <= _wc(out["caption_gancho"]) <= 18 and 20 <= _wc(out["caption_cuerpo"]) <= 90
            and 3 <= _wc(out["pregunta_comentarios"]) <= 22 and out["subtema"]):
        raise ValueError("título o descripción fuera de medida")
    import writer
    vals = [out["titulo"], out["caption_gancho"], out["caption_cuerpo"], out["pregunta_comentarios"]] + \
        [x for s in scenes for x in [s["voz"]] + s["rotulos"]]
    if any(writer.has_meta(v) for v in vals):
        raise ValueError("lleva indicaciones de diseño o de tono")
    return out


def verify(c, tema, mat):
    import gemini, verifier
    texts = {"titulo": c["titulo"],
             "escenas": [{"voz": s["voz"], "rotulos": s["rotulos"], "dato_en_pantalla": s["dato"]} for s in c["escenas"]],
             "descripcion": [c["caption_gancho"], c["caption_cuerpo"], c["pregunta_comentarios"]]}
    try:
        res = gemini.ask(f"""{verifier.ROLE}
Revisas el guion de un VÍDEO EXPLICADO (divulgación animada de 45 s) del tema "{tema}".
MATERIAL DE REFERENCIA (lo único que vale como verdad):
{mat}

GUION:
{json.dumps(texts, ensure_ascii=False, indent=1)}

A) CONTENIDO (estricto). Comprueba frase a frase: ¿todo lo que se afirma (voz, rótulos, datos en pantalla y
descripción) está respaldado por el material? Es un problema cualquier dato, cifra, causa, mecanismo, orden, ejemplo o
generalización ("siempre", "nunca", "todos") que no esté en el material; asociar una definición al término equivocado;
simplificar hasta decir algo falso; un "dato en pantalla" que no coincide con la voz.
B) GANCHO Y FORMA (flexible). La situación en segunda persona del gancho, las transiciones y la pregunta para
comentarios son recursos narrativos: NO son un problema salvo que afirmen un hecho sanitario falso, prometan algo
("cae seguro", "aprobarás") o inventen estadísticas.
Devuelve JSON: {{"ok": bool, "problemas": [{{"frase": str, "motivo": str}}]}}""", 0.1, careful=True)
    except Exception as e:
        return False, [{"frase": "-", "motivo": f"verificador no disponible: {str(e)[:150]}"}]
    probs = res.get("problemas") or []
    return bool(res.get("ok")) and not probs, probs


def content_for(topic):
    import chuleta
    tema, mat = chuleta.material(topic)
    if MOCK:
        return tema, mock_content(tema)
    avoid = [e.get("subtema") for e in log() if e.get("topic") == topic and e.get("subtema")]
    notes = None
    for attempt in range(2):
        try:
            c = clean(write(tema, mat, notes, avoid))
        except Exception as e:
            print(f"explicado: guion no válido ({str(e)[:160]})", flush=True); notes = [str(e)[:160]]; continue
        ok, probs = verify(c, tema, mat)
        if ok:
            print(f"explicado: guion verificado ({c['subtema']})", flush=True)
            return tema, c
        notes = probs
        print("explicado: el verificador pide cambios:", json.dumps(probs, ensure_ascii=False)[:500], flush=True)
    raise RuntimeError(f"no hay guion verificado para {tema}")


def mock_content(tema):
    """Guion de ejemplo para probar el diseño sin IA (no se publica nunca)."""
    return clean({"subtema": "Por qué se cambia de postura", "titulo": "Por qué girar al paciente cada dos horas",
                  "escenas": [
                      {"voz": "Entras en la habitación y tu paciente lleva toda la mañana en la misma postura.",
                       "rotulos": ["TODA LA MAÑANA", "MISMA POSTURA"], "tono": "neutro", "dibujo": "hospital room", "dato": None},
                      {"voz": "El peso del cuerpo aplasta la piel contra el colchón y la sangre deja de llegar.",
                       "rotulos": ["APLASTA LA PIEL", "DEJA DE LLEGAR"], "tono": "alerta", "dibujo": "skin", "dibujo_b": "skin 2",
                       "dato": None},
                      {"voz": "Sin oxígeno, el tejido empieza a dañarse antes de que se vea nada por fuera.",
                       "rotulos": ["SIN OXÍGENO"], "tono": "alerta", "dibujo": "tissue", "dato": None},
                      {"voz": "Por eso los cambios posturales se hacen cada dos horas, también de noche.",
                       "rotulos": ["CADA DOS HORAS"], "tono": "dato", "dibujo": "clock",
                       "dato": {"tipo": "cifra", "valor": "2", "unidad": "horas", "etiqueta": "cambio postural"}},
                      {"voz": "Tú vigilas las zonas de apoyo: sacro, talones y codos, y mantienes la piel limpia y seca.",
                       "rotulos": ["ZONAS DE APOYO"], "tono": "bien", "dibujo": "bed",
                       "dato": {"tipo": "lista", "items": ["Sacro", "Talones", "Codos", "Piel limpia y seca"]}},
                      {"voz": "La úlcera no se cura mejor con cremas: se evita quitando la presión a tiempo.",
                       "rotulos": ["QUITANDO LA PRESIÓN"], "tono": "bien", "dibujo": "bed 2",
                       "dato": {"tipo": "versus", "no": "MÁS CREMAS", "si": "MENOS PRESIÓN"}}],
                  "caption_gancho": "¿Por qué hay que girar al paciente aunque esté dormido? 🛏️",
                  "caption_cuerpo": "Cuando alguien pasa horas en la misma postura, su propio peso aplasta la piel contra el "
                                    "colchón y la sangre no llega. El tejido se daña por dentro antes de verse por fuera. "
                                    "Por eso los cambios posturales se programan y se vigilan las zonas de apoyo.",
                  "pregunta_comentarios": "¿Qué zona de apoyo se te olvida siempre en los test?"})


# ------------------------------------------------------------------ 3. ilustraciones
STYLE = ("Flat vector illustration in a dark neon line-art style, like a modern animated science explainer. "
         "Very dark teal-black background (#05161A to #092E30). The subject is drawn with clean glowing outlines in bright "
         "teal (#2FE0C8) and soft mint (#C4F6EE), with flat fills in dark teal shades, and ONE warm amber-gold (#F2CF48) "
         "accent on the most important element. Simple geometric shapes, thick consistent line weight, subtle glow, no "
         "gradients on the background, no photo-realism, no 3D. Any people are simple stylised figures with NO facial "
         "features. Composition for a vertical 9:16 video: subject in the middle and lower-middle of the frame, the top "
         "third is empty dark background. Absolutely no text, no letters, no numbers, no labels, no logos, no watermark, "
         "no UI. No blood, no wounds, no needles piercing skin, no nudity. Draw only what the scene describes: no extra "
         "people, no decorative icons.")


def grade(img):
    """Etalonaje a la marca: mezcla la ilustración con su versión en degradado teal (oscuro -> teal -> menta), así
    cualquier color que se haya escapado vuelve a la paleta y el dorado se conserva como acento."""
    im = img.convert("RGB")
    lum = np.asarray(im.convert("L"), np.float32) / 255.0
    stops = np.array([BG0, (10, 70, 70), (26, 158, 143), NEON, MINT], np.float32)
    x = np.clip(lum, 0, 1) * (len(stops) - 1); i = np.clip(x.astype(int), 0, len(stops) - 2); f = (x - i)[..., None]
    mapped = stops[i] * (1 - f) + stops[i + 1] * f
    a = np.asarray(im, np.float32)
    warm = ((a[..., 0] > a[..., 2] + 40) & (a[..., 1] > a[..., 2] + 20))[..., None]       # dorados: se respetan más
    k = np.where(warm, 0.15, 0.5)
    out = a * (1 - k) + mapped * k
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def image_ok(img, sc):
    """Revisión de cada ilustración: sin texto, oscura, nada desagradable y sin contradecir lo que dice la voz."""
    if float(np.asarray(img.convert("L").resize((64, 64))).mean()) > 120:
        return False, "fondo claro"
    import base64, io, gemini
    b = io.BytesIO(); t = img.convert("RGB"); t.thumbnail((640, 640)); t.save(b, "JPEG", quality=85)
    try:
        r = gemini.ask([{"text": "Ilustración para una escena de un vídeo educativo de oposiciones de TCAE. La voz dice: "
                                 f"«{sc['voz']}». Se pidió dibujar: {sc['dibujo']}.\n"
                                 "Responde: ¿tiene texto, letras o números legibles? ¿Hay sangre, heridas, agujas en la piel, "
                                 "desnudos o algo desagradable? ¿Alguna persona tiene rasgos faciales detallados o parece "
                                 "alguien real? ¿Muestra algo que CONTRADIGA la frase de la voz o un error sanitario "
                                 "evidente (por ejemplo, una técnica mal hecha)? ok = true solo si la respuesta a todo es NO "
                                 'y la imagen tiene que ver con la escena. Devuelve JSON: {"ok": bool, "motivo": str}'},
                        {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b.getvalue()).decode()}}], 0.1)
        return bool(r.get("ok")), str(r.get("motivo") or "")[:160]
    except Exception as e:
        return False, f"revisión no disponible: {str(e)[:100]}"


def illustration(sc, what, ref=None):
    """Una ilustración revisada (2 intentos) o None."""
    import gemini
    for k in range(2):
        try:
            prompt = STYLE + "\nScene to draw: " + what
            if ref is not None:
                prompt += ("\nThe attached image is ONLY a style reference: match exactly its drawing style, line weight and "
                           "colour palette, but draw this new scene (do not copy its content).")
            img = gemini.image(prompt, aspect="9:16", refs=[ref] if ref is not None else ())
            ok, why = image_ok(img, sc)
            if ok:
                return img
            print(f"explicado: ilustración rechazada ({why})", flush=True)
        except Exception as e:
            print("explicado: ilustración fallida:", str(e)[:160], flush=True)
    return None


def illustrations(c):
    """[(A, B)] por escena (PIL o None). La primera válida sirve de referencia de estilo a las demás."""
    n = len(c["escenas"]); out = [[None, None] for _ in range(n)]
    if MOCK or not os.environ.get("GEMINI_API_KEY") or os.environ.get("EXPLICA_IMAGENES", "true").lower() == "false":
        return out
    ref = None
    for i, sc in enumerate(c["escenas"]):
        if sc["dibujo"]:
            out[i][0] = illustration(sc, sc["dibujo"], ref)
            if out[i][0] is not None:
                ref = out[i][0]; break
    if ref is None:
        return out
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(i, 0, sc["dibujo"]) for i, sc in enumerate(c["escenas"]) if out[i][0] is None and sc["dibujo"]]
    with ThreadPoolExecutor(3) as ex:
        for (i, j, _), img in zip(jobs, ex.map(lambda jb: illustration(c["escenas"][jb[0]], jb[2], ref), jobs)):
            out[i][j] = img
    jobs = [(i, sc["dibujo_b"]) for i, sc in enumerate(c["escenas"]) if sc["dibujo_b"] and out[i][0] is not None]
    with ThreadPoolExecutor(2) as ex:                    # el "instante después" parte de su propia escena
        for (i, _), img in zip(jobs, ex.map(lambda jb: illustration(
                c["escenas"][jb[0]], jb[1] + " Keep the same framing, objects and position as the reference image; only "
                "change what the description says changes.", out[jb[0]][0]), jobs)):
            out[i][1] = img
    print(f"explicado: {sum(1 for a, _ in out if a is not None)}/{n} ilustraciones"
          f" (+{sum(1 for _, b in out if b is not None)} de cambio)", flush=True)
    return out


# ------------------------------------------------------------------ 4. piezas de dibujo
def F(path, size):
    return fx.font(path, int(size))


_CACHE = {}


def cached(key, fn):
    if key not in _CACHE:
        if len(_CACHE) > 400:
            _CACHE.clear()
        _CACHE[key] = fn()
    return _CACHE[key]


def glow(im, color, blur=18, strength=0.85):
    """Añade un halo de luz del color dado alrededor de lo dibujado."""
    pad = blur * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    halo = Image.new("RGBA", im.size, tuple(color) + (0,))
    halo.putalpha(im.getchannel("A").point(lambda a: int(a * strength)))
    out.alpha_composite(halo, (pad, pad)); out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def neon_text(text, size, color, maxw=960, max_lines=2, path=None, stroke=7):
    """Rótulo grande en mayúsculas con contorno oscuro y halo."""
    path = path or FP
    def make():
        s = size
        while s > 54:
            f = F(path, s); pos, n = fx.wrap(text.split(), f, maxw)
            if n <= max_lines and all(f.getlength(w) <= maxw for w in text.split()):
                break
            s -= 4
        f = F(path, s); pos, n = fx.wrap(text.split(), f, maxw); lh = int(s * 1.08)
        widths = {}
        for w, x, ln in pos:
            widths[ln] = x + f.getlength(w)
        tw = int(max(widths.values())) + 2 * stroke + 8
        im = Image.new("RGBA", (tw, lh * n + int(s * 0.3) + 2 * stroke), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for w, x, ln in pos:
            off = (tw - 2 * stroke - 8 - widths[ln]) / 2
            d.text((stroke + 4 + x + off, stroke + ln * lh), w, font=f, fill=color, stroke_width=stroke, stroke_fill=BG0)
        return glow(im, color, 20, 0.7)
    return cached(("neon", text, size, color, maxw, max_lines, path), make)


class NeonBG:
    """Fondo de neón dibujado en código (cierre del vídeo y respaldo si falta una ilustración): degradado oscuro,
    suelo en perspectiva, anillos que giran y un foco de luz del color de la escena."""

    def __init__(self, seed=0, color=NEON):
        rng = random.Random(seed)
        y = np.linspace(0, 1, H)[:, None, None]
        base = np.array(BG0, np.float32) * (1 - y) + np.array(BG1, np.float32) * y
        im = Image.fromarray(np.broadcast_to(base, (H, W, 3)).astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(im, "RGBA")
        hz = 1180                                             # suelo en perspectiva
        for k in range(1, 15):
            yy = hz + (H - hz) * (k / 14) ** 2.2
            d.line([(0, yy), (W, yy)], fill=NEON + (int(18 + 30 * k / 14),), width=2)
        for k in range(-9, 10):
            d.line([(W / 2 + k * 30, hz), (W / 2 + k * 330, H)], fill=NEON + (28,), width=2)
        orb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(orb).ellipse([W / 2 - 430, 900 - 430, W / 2 + 430, 900 + 430], fill=tuple(color) + (70,))
        im.alpha_composite(orb.filter(ImageFilter.GaussianBlur(150)))
        self.base = im; self.color = color
        self.rings = [(rng.uniform(210, 250) + 95 * k, rng.uniform(0, 360), rng.choice([-1, 1]) * rng.uniform(8, 20),
                       rng.uniform(40, 110)) for k in range(3)]

    def frame(self, lt, dur=6.0, switch=None, punch=0.0, dimk=0.0):
        im = self.base.copy(); d = ImageDraw.Draw(im, "RGBA")
        cx, cy = W / 2, 900
        for r, a0, sp, span in self.rings:
            r = r * (1 + 0.03 * punch); a = a0 + sp * lt
            for off in (0, 180):
                d.arc([cx - r, cy - r, cx + r, cy + r], a + off, a + off + span, fill=tuple(self.color) + (150,), width=5)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=MINT + (26,), width=2)
        return im


class SceneBG:
    """Ilustración a pantalla completa con movimiento de cámara (zoom lento + un pequeño golpe cuando entra un rótulo),
    fundido A -> B si hay ilustración B y atenuado progresivo cuando entra un dato en pantalla."""
    S = 1.2

    def __init__(self, a, b=None, k=0, dim=False):
        self.a = self._prep(a); self.b = self._prep(b) if b is not None else None
        self.a_dim = self._dim(self.a) if dim else None
        self.b_dim = self._dim(self.b) if (dim and self.b is not None) else None
        self.dir = 1 if k % 2 == 0 else -1
        self.pan = [(0, -1), (1, 0), (0, 1), (-1, 0)][k % 4]

    def _prep(self, img):
        im = grade(img)
        r = max(W * self.S / im.width, H * self.S / im.height)
        return im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)

    @staticmethod
    def _dim(im):
        return Image.blend(im.filter(ImageFilter.GaussianBlur(4)), Image.new("RGB", im.size, BG0), 0.55)

    def _view(self, src, lt, dur, punch):
        p = eio(lt / max(dur, 0.1))
        z = (1.04 + 0.11 * p) if self.dir > 0 else (1.15 - 0.11 * p)
        z *= 1 + 0.025 * punch
        vw, vh = src.width / self.S / z * 1.0, src.height / self.S / z
        mx, my = (src.width - vw) / 2, (src.height - vh) / 2
        x0 = mx + self.pan[0] * mx * 0.5 * (p - 0.5); y0 = my + self.pan[1] * my * 0.35 * (p - 0.5)
        return src.crop((int(x0), int(y0), int(x0 + vw), int(y0 + vh))).resize((W, H), Image.BILINEAR)

    def _mix(self, sharp, soft, lt, dur, punch, dimk):
        if soft is None or dimk <= 0:
            return self._view(sharp, lt, dur, punch)
        if dimk >= 1:
            return self._view(soft, lt, dur, punch)
        return Image.blend(self._view(sharp, lt, dur, punch), self._view(soft, lt, dur, punch), dimk)

    def frame(self, lt, dur=6.0, switch=None, punch=0.0, dimk=0.0):
        fr = self._mix(self.a, self.a_dim, lt, dur, punch, dimk)
        if self.b is not None and switch is not None and lt > switch:
            fr = Image.blend(fr, self._mix(self.b, self.b_dim, lt, dur, punch, dimk), eio((lt - switch) / 0.45))
        return fr.convert("RGBA")


def sweep():
    """Barrido de luz diagonal (da vida a la ilustración al empezar cada escena)."""
    def make():
        w = 520
        x = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
        a = (np.clip(1 - np.abs(x), 0, 1) ** 2.2 * 46).astype(np.uint8)
        arr = np.zeros((H + 600, w, 4), np.uint8); arr[..., :3] = MINT; arr[..., 3] = np.broadcast_to(a, (H + 600, w))
        return Image.fromarray(arr, "RGBA").rotate(16, Image.BILINEAR, expand=True)
    return cached("sweep", make)


def vignette():
    """Oscurece arriba (subtítulos y rótulo) y abajo (interfaz de la red) para que el texto siempre se lea."""
    def make():
        y = np.arange(H, dtype=np.float32)[:, None]
        a = 215 * np.clip(1 - y / 760, 0, 1) ** 1.25 + 170 * np.clip((y - 1380) / 540, 0, 1) ** 1.2
        arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = BG0; arr[..., 3] = np.clip(np.broadcast_to(a, (H, W)), 0, 255)
        return Image.fromarray(arr, "RGBA")
    return cached("vig", make)


def particles(fr, tt, seed=7):
    d = ImageDraw.Draw(fr, "RGBA"); rng = random.Random(seed)
    for k in range(22):
        x0, y0, sp, r, ph = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(14, 46), rng.uniform(2, 5), rng.uniform(0, 6.28)
        y = (y0 - sp * tt) % H; x = x0 + 16 * math.sin(tt * 0.7 + ph)
        a = int(70 + 60 * math.sin(tt * 1.3 + ph))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(MINT if k % 3 else AMBER) + (max(20, a),))


def sub_image(words, lit, keys):
    """Subtítulo karaoke de un tramo: dichas en blanco, la que suena ahora resaltada, las siguientes atenuadas."""
    def make():
        f = F(FP, 54); sp = f.getlength(" ")
        widths = [f.getlength(w) for w in words]; tw = sum(widths) + sp * (len(words) - 1)
        im = Image.new("RGBA", (int(tw) + 60, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 30
        for i, w in enumerate(words):
            now = i == lit - 1
            if now and _norm(w) in keys:
                d.rounded_rectangle([x - 12, 10, x + widths[i] + 12, 90], 14, fill=NEON)
                d.text((x, 16), w, font=f, fill=INK)
            else:
                col = WHITE if i < lit else (255, 255, 255, 92)
                d.text((x, 16), w, font=f, fill=col, stroke_width=3, stroke_fill=BG0 + (150 if i < lit else 60,))
            x += widths[i] + sp
        return im
    return cached(("sub", tuple(words), lit, tuple(sorted(keys)) if lit else ()), make)


def chunks(words, times):
    """Parte una frase en tramos cortos de subtítulo: [(i0, i1)] (corta en signos de puntuación o cada ~22 letras)."""
    out, i0, n = [], 0, 0
    for i, w in enumerate(words):
        n += len(w) + 1
        last = i == len(words) - 1
        if last or (w[-1] in ",.;:?!…" and i - i0 >= 1) or n >= 22 or i - i0 >= 3:
            if not last and len(words) - i - 1 == 1 and n < 26:      # no dejar una palabra suelta al final
                continue
            out.append((i0, i + 1)); i0, n = i + 1, 0
    return out


def chip(n, text):
    def make():
        f = F(F9, 50); tw = f.getlength(text)
        im = Image.new("RGBA", (int(tw) + 150, 96), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, im.width - 1, 95], 48, fill=(6, 34, 36, 235), outline=NEON, width=4)
        d.ellipse([12, 12, 84, 84], fill=NEON)
        fn = F(FP, 44); s = str(n); d.text((48 - fn.getlength(s) / 2, 17), s, font=fn, fill=INK)
        d.text((104, 16), text, font=f, fill=WHITE)
        return glow(im, NEON, 14, 0.35)
    return cached(("chip", n, text), make)


def versus_card(text, good, strike=0.0):
    def make():
        col = NEON if good else CORAL
        f = F(FP, 62)
        s = 62
        while f.getlength(text) > 700 and s > 40:
            s -= 3; f = F(FP, s)
        tw = f.getlength(text)
        im = Image.new("RGBA", (int(tw) + 190, 130), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, im.width - 1, 129], 34, fill=(NEON + (255,)) if good else (30, 16, 24, 235),
                            outline=col, width=5)
        icon = (fx.check_icon(78, NEON, INK) if good else fx.cross_icon(78, WHITE, CORAL))
        im.alpha_composite(icon, (24, 26))
        d.text((124, 65 - s * 0.72), text, font=f, fill=INK if good else (255, 214, 220))
        if not good and strike > 0:
            d.line([(118, 68), (118 + (tw + 14) * strike, 68)], fill=CORAL, width=8)
        return glow(im, col, 18, 0.6 if good else 0.3)
    return cached(("vs", text, good, round(strike, 2)), make)


def big_number(txt, unit, label):
    def make():
        f = F(FP, 330 if len(txt) <= 2 else (250 if len(txt) <= 4 else 190))
        tw = f.getlength(txt); bb = f.getbbox(txt)
        fu = F(FP, 78); fl = F(F8, 46)
        w = int(max(tw, fu.getlength(unit), fl.getlength(label))) + 80
        num_h = bb[3] + 20
        im = Image.new("RGBA", (w, num_h + 190), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text(((w - tw) / 2, 0), txt, font=f, fill=AMBER, stroke_width=8, stroke_fill=BG0)
        if unit:
            d.text(((w - fu.getlength(unit)) / 2, num_h), unit, font=fu, fill=MINT, stroke_width=5, stroke_fill=BG0)
        if label:
            d.text(((w - fl.getlength(label)) / 2, num_h + 104), label, font=fl, fill=WHITE, stroke_width=4, stroke_fill=BG0)
        return glow(im, AMBER, 26, 0.45)
    return cached(("num", txt, unit, label), make)


def phone(thumb, lt):
    """Móvil enviando el vídeo a una compañera (cierre "pásaselo")."""
    pw, ph = 470, 900
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], 62, fill=255)
    scr = cached("phone_scr", lambda: Image.blend(thumb.resize((pw, ph), Image.LANCZOS).convert("RGB"),
                                                  Image.new("RGB", (pw, ph), BG0), 0.25).convert("RGBA")).copy()
    d = ImageDraw.Draw(scr, "RGBA")
    p = eo((lt - 0.45) / 0.4)                               # hoja de compartir que sube
    if p > 0:
        sh = 340; y0 = ph - sh * p
        d.rounded_rectangle([14, y0, pw - 14, ph + 60], 40, fill=(255, 255, 255, 250))
        d.text((44, y0 + 26), "Enviar a", font=F(F9, 34), fill=(31, 41, 55))
        people = [("C", "Compi", fx.TEAL), ("G", "Grupo opo", (232, 201, 61)), ("A", "Academia", (140, 120, 220))]
        for k, (ini, name, col) in enumerate(people):
            cx = 96 + k * 140; cy = y0 + 150
            if k == 0 and lt > 1.25:                        # toque en la primera
                pr = clamp((lt - 1.25) / 0.45)
                d.ellipse([cx - 52 - 26 * pr, cy - 52 - 26 * pr, cx + 52 + 26 * pr, cy + 52 + 26 * pr],
                          outline=fx.TEAL + (int(255 * (1 - pr)),), width=6)
                d.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], outline=fx.TEAL, width=6)
            d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], fill=col)
            fi = F(FP, 46); d.text((cx - fi.getlength(ini) / 2, cy - 34), ini, font=fi, fill=WHITE)
            fn = F(F8, 25); d.text((cx - fn.getlength(name) / 2, cy + 56), name, font=fn, fill=(31, 41, 55))
    im.paste(scr, (0, 0), mask)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, pw - 1, ph - 1], 62, outline=MINT, width=7)
    ImageDraw.Draw(im).rounded_rectangle([pw / 2 - 60, 18, pw / 2 + 60, 40], 11, fill=BG0)
    return im


def brand_block():
    def make():
        im = Image.new("RGBA", (980, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        logo = Image.new("RGBA", (132, 132), (0, 0, 0, 0))
        ImageDraw.Draw(logo).rounded_rectangle([0, 0, 131, 131], 36, fill=fx.TEAL)
        logo.alpha_composite(fx.check_icon(92, WHITE, fx.TEAL), (20, 20))
        f = F(F9, 96); tw = f.getlength("Aprueba TCAE"); x0 = (980 - (132 + 28 + tw)) / 2
        im.alpha_composite(logo, (int(x0), 10))
        d.text((x0 + 160, 18), "Aprueba", font=f, fill=WHITE)
        d.text((x0 + 160 + f.getlength("Aprueba "), 18), "TCAE", font=f, fill=NEON)
        sub = fx.text_block("Tests, simulacros y flashcards para las oposiciones de TCAE", F8, 40, 820, MINT, align="center")
        im.alpha_composite(sub, ((980 - sub.width) // 2, 190))
        p1 = fx.pill("PRACTICA ESTE TEMA GRATIS", 46, AMBER, INK, padx=40, pady=16)
        im.alpha_composite(p1, ((980 - p1.width) // 2, 350))
        p2 = glow(fx.pill(marca.WEB, 76, NEON, INK, padx=52, pady=20, path=FP), NEON, 22, 0.55)
        im.alpha_composite(p2, ((980 - p2.width) // 2, 440 - 66))
        t = fx.text_block(f"Link en el perfil · {marca.HANDLE}", F9, 40, 900, WHITE, align="center")
        im.alpha_composite(t, ((980 - t.width) // 2, 650))
        return im
    return cached("brand", make)


# ------------------------------------------------------------------ 5. render
def record(lines):
    """Graba la voz (mismo control que los reels: cada frase dicha una vez, en español y sin indicaciones)."""
    import voice
    voice.reset()
    for attempt in range(3):
        try:
            clips = []
            groups = [lines[i:i + 3] for i in range(0, len(lines) - 2, 3)]
            done = sum(len(g) for g in groups)
            groups += [lines[done:-2]] if lines[done:-2] else []
            groups.append(lines[-2:])
            for grp in groups:
                clips += voice.say_many([t for _, t, _ in grp], speed=1.06, styles=[s for _, _, s in grp], one_take=len(grp) > 1)
            break
        except voice.VoiceError as e:
            print(f"voz cambiada a mitad de vídeo ({e}); repito con {voice.next_engine()}", flush=True)
            voice.reset(voice.next_engine())
    else:
        raise RuntimeError("no se pudo grabar una voz coherente")
    A = {k: c for (k, _, _), c in zip(lines, clips)}
    if voice.LOCK != "mock":
        for k, t, s_ in lines:
            why = voice.problem(A[k], t); tries = 0
            while why and tries < 4:
                tries += 1
                print(f"voz: '{k}' {why}; la grabo otra vez sola (intento {tries})", flush=True)
                try:
                    A[k] = voice.say_many([t], speed=1.06, styles=[s_], one_take=False, force=True)[0]
                except voice.VoiceError:
                    raise
                except Exception as e:
                    print("voz: nueva toma fallida:", str(e)[:150], flush=True); continue
                why = voice.problem(A[k], t)
            if why:
                raise RuntimeError(f"la voz no graba bien '{t[:40]}' ({why})")
    return A


def build(c, images, out, seed=0, tema=""):
    """Renderiza el vídeo. images: [(A, B)] por escena (PIL o None). Devuelve los datos del reel (como make_quiz)."""
    import soundfile as sf
    import voice
    E = c["escenas"]; n_sc = len(E)
    styles = ["intrigued, direct, like starting a story"] + ["clear and warm, explaining to a friend"] * (n_sc - 2) + \
             ["confident, landing the key idea"]
    lines = [(f"s{i}", s["voz"], styles[i]) for i, s in enumerate(E)] + \
            [("cta1", CTA1, "friendly, a smile in the voice"), ("cta2", CTA2, "upbeat and clear")]
    A = record(lines)
    TXT = {k: t for k, t, _ in lines}
    D = {k: len(a) / SR for k, a in A.items()}

    # ---- línea de tiempo
    SEG, VO, t = [], {}, 0.0
    for i, s in enumerate(E):
        lead = 0.12 if i == 0 else 0.3
        dur = max(2.6, D[f"s{i}"] + lead + (0.75 if s["dato"] else 0.4))
        SEG.append({"kind": "scene", "i": i, "a": t, "b": t + dur}); VO[f"s{i}"] = t + lead; t += dur
    d1 = max(2.6, D["cta1"] + 0.55); SEG.append({"kind": "share", "a": t, "b": t + d1}); VO["cta1"] = t + 0.25; t += d1
    d2 = max(3.2, D["cta2"] + 1.3); SEG.append({"kind": "brand", "a": t, "b": t + d2}); VO["cta2"] = t + 0.3; t += d2
    total = t
    WT = {k: [VO[k] + ts for ts, _ in voice.align(A[k], TXT[k])] for k in VO}
    WORDS = {k: TXT[k].split() for k in VO}
    CH = {k: chunks(WORDS[k], WT[k]) for k in VO}

    # ---- cuándo entra cada rótulo y cada dato (cuando la voz dice su palabra)
    for sg in SEG[:n_sc]:
        i = sg["i"]; s = E[i]; k = f"s{i}"; a, b = sg["a"], sg["b"]; ws = WORDS[k]
        rt = []
        for j, r in enumerate(s["rotulos"]):
            idx = _find(ws, r)
            tr = WT[k][idx] - 0.08 if idx is not None else a + (j + 0.4) / len(s["rotulos"]) * (b - a)
            if i == 0 and j == 0:
                tr = min(tr, a + 0.15)                       # el gancho, en pantalla desde el primer instante
            rt.append(max(tr, (rt[-1] + 0.5) if rt else a + 0.1))
        sg["rt"] = rt
        d = s["dato"]; v0 = VO[k]; vd = D[k]
        if d and d["tipo"] == "lista":
            ts_ = []
            for j, it in enumerate(d["items"]):
                idx = _find(ws, it) if _wc(it) <= 3 else _find(ws, it.split()[0])
                tj = WT[k][idx] - 0.05 if idx is not None else v0 + vd * (0.25 + 0.6 * j / len(d["items"]))
                ts_.append(max(tj, (ts_[-1] + 0.3) if ts_ else a + 0.5))
            sg["dt"] = ts_
        elif d and d["tipo"] == "versus":
            i_no = _find(ws, d["no"]); i_si = _find(ws, d["si"])
            t_no = WT[k][i_no] if i_no is not None else v0 + vd * 0.3
            t_si = WT[k][i_si] if i_si is not None else v0 + vd * 0.68
            sg["dt"] = [min(t_no, t_si - 0.7) if t_si - 0.7 > a else a + 0.4, max(t_si, a + 1.2)]
        elif d:
            idx = next((x for x, w in enumerate(ws) if re.search(r"\d", w) or _norm(w) in
                        ("un", "una", "dos", "tres", "cuatro", "cinco", "seis", "ocho", "diez", "doce", "quince", "treinta")), None)
            sg["dt"] = [WT[k][idx] - 0.1 if idx is not None else rt[-1] + 0.2]
    keys = {f"s{i}": {_norm(w) for r in s["rotulos"] for w in r.split()} for i, s in enumerate(E)}
    keys["cta1"] = {"pasaselo"}; keys["cta2"] = {"gratis", _norm(marca.WEB)}

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
        if sg["a"] > 0:
            put(sfx, fx.whoosh(), sg["a"] - 0.16, 1.2)
        if sg["kind"] == "scene":
            put(sfx, fx.soft_hit(), sg["rt"][0], 0.42)
            d = E[sg["i"]]["dato"]
            if d and d["tipo"] == "cifra":
                put(sfx, fx.riser(0.6), sg["dt"][0], 0.5); put(sfx, fx.soft_hit(), sg["dt"][0] + 0.6, 0.5)
            elif d:
                for tj in sg["dt"]:
                    put(sfx, fx.tick(True), tj, 0.9)
                if d["tipo"] == "versus":
                    put(sfx, fx.chime_ok(), sg["dt"][1], 0.55)
        if sg["kind"] == "share":
            put(sfx, fx.tick(True), sg["a"] + 1.25, 1.0); put(sfx, fx.chime_ok(), sg["a"] + 1.6, 0.6)
    music = fx.study_beat(total, 98)[:n]
    venv = np.convolve((np.abs(vo) > 0.01).astype(np.float32), np.ones(3000) / 3000, "same")
    mix = vo * 1.15 + sfx + music * (0.5 - 0.32 * np.clip(venv * 3, 0, 1))
    mix = fx.dehiss(np.tanh(mix * 1.05) * 0.92)
    wav = out.replace(".mp4", ".wav"); sf.write(wav, mix, SR)

    # ---- fondos y piezas fijas
    BGS = []
    for i, s in enumerate(E):
        a_img, b_img = images[i] if i < len(images) else (None, None)
        if a_img is not None:
            BGS.append(SceneBG(a_img, b_img, i, dim=bool(s["dato"])))
        else:
            BGS.append(NeonBG(seed + i, TONE[s["tono"]] if s["tono"] != "neutro" else NEON))
    end_bg = NeonBG(seed + 99, NEON)
    thumb = next((grade(a) for a, _ in images if a is not None), None)
    if thumb is None:
        thumb = BGS[0].frame(1.0).convert("RGB")
    vig = vignette()
    handle = fx.pill(marca.HANDLE, 28, (0, 0, 0, 90), (255, 255, 255, 190), padx=20, pady=8, path=F8)
    sent = fx.pill("Enviado     ", 40, NEON, INK, padx=30, pady=12)
    sent.alpha_composite(fx.check_icon(46, NEON, INK), (sent.width - 76, (sent.height - 46) // 2))
    sent = glow(sent, NEON, 14, 0.5)
    share_rot = neon_text("PÁSASELO", 124, AMBER)

    def subtitle(fr, tt):
        k = next((k for k in VO if VO[k] - 0.05 <= tt < VO[k] + D[k] + 0.35), None)
        if k is None:
            return
        lit = sum(1 for x in WT[k] if x <= tt)
        i0, i1 = next(((a, b) for a, b in CH[k] if lit <= b), CH[k][-1])
        if lit < i0:
            lit = i0
        im = sub_image(WORDS[k][i0:i1], lit - i0, keys.get(k, set()))
        fx.paste_center(fr, im, W / 2, SUB_Y)

    def frame_at(tt):
        sg = next((s for s in SEG if s["a"] <= tt < s["b"]), SEG[-1])
        lt = tt - sg["a"]; dur = sg["b"] - sg["a"]
        if sg["kind"] == "scene":
            i = sg["i"]; s = E[i]; rt = sg["rt"]
            j = max([x for x, tr in enumerate(rt) if tr <= tt], default=-1)
            punch = max(0.0, 1 - (tt - rt[j]) / 0.35) if j >= 0 else 0.0
            sw = (rt[1] - sg["a"] if len(rt) > 1 else dur * 0.5)
            d = s["dato"]
            dimk = eio((tt - (sg["dt"][0] - 0.3)) / 0.45) if d else 0.0      # la ilustración se atenúa al entrar el dato
            fr = BGS[i].frame(lt, dur, sw, punch, dimk)
            if i > 0 and lt < 0.28:                          # fundido rápido desde la escena anterior
                pv = SEG[i - 1]
                prev = BGS[i - 1].frame(pv["b"] - pv["a"] + lt, pv["b"] - pv["a"], None, 0.0, 1.0 if E[i - 1]["dato"] else 0.0)
                fr = Image.blend(prev, fr, eio(lt / 0.28))
            if 0.15 < lt < 1.25 and isinstance(BGS[i], SceneBG):
                sw_im = sweep(); px = -sw_im.width + (W + sw_im.width) * eio((lt - 0.15) / 1.1)
                fr.alpha_composite(sw_im, (int(px), -300))
            fr.alpha_composite(vig)
            particles(fr, tt, seed)
            col = TONE[s["tono"]]
            big = isinstance(BGS[i], NeonBG) and not d       # sin ilustración: el rótulo ocupa el centro
            if j >= 0:
                im = neon_text(s["rotulos"][j], 150 if big else 116, col if j == len(rt) - 1 or s["tono"] != "neutro" else WHITE)
                p = (tt - rt[j]) / 0.28
                fx.paste_center(fr, im, W / 2, 900 if big else ROT_Y + im.height / 2 - 96, 0.7 + 0.3 * eob(p), min(1, p * 2.2))
            if d and d["tipo"] == "cifra":
                p = (tt - sg["dt"][0]) / 0.6
                if p > 0:
                    m = re.fullmatch(r"(\D*)(\d{1,4})(\D*)", d["valor"])
                    txt = (m.group(1) + str(int(round(int(m.group(2)) * eo(p)))) + m.group(3)) if m else d["valor"]
                    im = big_number(txt, d["unidad"], d["etiqueta"])
                    fx.paste_center(fr, im, W / 2, 1060, 0.8 + 0.2 * eob(p * 1.4) + 0.04 * max(0, 1 - abs(p - 1) * 3), min(1, p * 3))
            elif d and d["tipo"] == "lista":
                n_it = len(d["items"]); y0 = 1060 - (n_it - 1) * 62
                left = (W - max(chip(q + 1, it).width for q, it in enumerate(d["items"]))) / 2
                for q, it in enumerate(d["items"]):
                    p = (tt - sg["dt"][q]) / 0.3
                    if p > 0:
                        im = chip(q + 1, it)
                        fx.paste_center(fr, im, left + im.width / 2 - (1 - eob(p)) * 160, y0 + q * 124, 1, min(1, p * 2))
            elif d and d["tipo"] == "versus":
                p_no = (tt - sg["dt"][0]) / 0.3; p_si = (tt - sg["dt"][1]) / 0.32
                if p_no > 0:
                    im = versus_card(d["no"], False, clamp((tt - sg["dt"][0] - 0.45) / 0.3) if p_si <= 0 else 1.0)
                    fx.paste_center(fr, im, W / 2, 960, 0.85 + 0.15 * eob(p_no), min(1, p_no * 2) * (0.6 if p_si > 0.5 else 1))
                if p_si > 0:
                    im = versus_card(d["si"], True)
                    fx.paste_center(fr, im, W / 2, 1150, 0.7 + 0.3 * eob(p_si) + 0.03 * math.sin(tt * 5), min(1, p_si * 2))
        elif sg["kind"] == "share":
            fr = end_bg.frame(tt, punch=max(0, 1 - lt / 0.3)); fr.alpha_composite(vig); particles(fr, tt, seed)
            fx.paste_center(fr, share_rot, W / 2, ROT_Y - 6, 0.7 + 0.3 * eob(lt / 0.28), min(1, lt * 6))
            ph = phone(thumb, lt)
            fx.paste_center(fr, ph, W / 2, 1100 + (1 - eo(lt / 0.4)) * 220, 1, min(1, lt * 4), 3 * (1 - eo(lt / 0.5)))
            if lt > 1.6:
                fx.paste_center(fr, sent, W / 2, 1020, eob((lt - 1.6) / 0.3))
        else:
            fr = end_bg.frame(tt); fr.alpha_composite(vig); particles(fr, tt, seed)
            fx.paste_center(fr, brand_block(), W / 2, 960, 0.9 + 0.1 * eob(lt / 0.4), min(1, lt * 4))
        if sg["kind"] == "scene":
            fx.paste_center(fr, handle, W / 2, 1462, alpha=0.9)
        subtitle(fr, tt)
        return fr

    if os.environ.get("EXPLICA_STILLS"):                    # prueba de diseño: solo unos fotogramas clave
        os.remove(wav)
        ts_ = [0.9] + [sg["b"] - 0.25 for sg in SEG]
        paths = []
        for q, tt in enumerate(ts_):
            p = out.replace(".mp4", f"_still{q:02d}.jpg"); frame_at(tt).convert("RGB").save(p, quality=88); paths.append(p)
        return {"stills": paths, "duration": round(total, 1)}

    thumb_t = min(SEG[0]["b"] - 0.2, SEG[0]["rt"][0] + 0.9)
    caps = {int(thumb_t * FPS): out.replace(".mp4", "_slide01_hook.png")}
    for q, sg in enumerate(SEG[1:], 2):
        caps[int((sg["b"] - 0.25) * FPS)] = out.replace(".mp4", f"_slide{q:02d}_{sg['kind']}.png")
    slides = []
    tmp = out.replace(".mp4", "_tmp.mp4")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", wav, "-shortest"] + fx.enc_args(tmp), stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        fr = frame_at(fi / FPS)
        if fi in caps:
            fr.convert("RGB").save(caps[fi]); slides.append(caps[fi])
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait(); os.remove(wav)
    if proc.returncode:
        raise RuntimeError("ffmpeg falló al codificar el vídeo explicado")
    os.replace(tmp, out)
    print(f"explicado: {total:.1f} s · {n_sc} escenas · {sum(1 for b in BGS if isinstance(b, SceneBG))} con ilustración", flush=True)
    return {"formato": FMT, "estilo": "neon", "ids": [], "temas": [tema], "respuestas": [], "veredicto": None,
            "hook": c["titulo"], "hook_line": E[0]["voz"], "duration": round(total, 1),
            "timeline": [(s_["kind"], round(s_["a"], 2)) for s_ in SEG], "thumb_ms": int(thumb_t * 1000),
            "slides": slides, "story_base": slides[0] if slides else None, "soluciones": [], "solucion_texto": None,
            "subtema": c["subtema"], "ilustraciones": sum(1 for b in BGS if isinstance(b, SceneBG))}


def caption(c, seed=0):
    rng = random.Random(seed)
    tags = ["#TCAE", "#oposicionesTCAE"] + rng.sample(["#auxiliardeenfermeria", "#oposiciones", "#TCAEoposiciones", "#tecnicoencuidados"], 3)
    return (f"{c['caption_gancho']}\n\n{c['caption_cuerpo']}\n\n💬 {c['pregunta_comentarios']}\n"
            "📌 Guárdalo para repasar y pásaselo a tu compi de opo.\n\n"
            "Practica este tema gratis con tests, simulacros y flashcards de las oposiciones de TCAE en apruebatcae.com "
            "(link en la bio).\n\n" + " ".join(tags))


def contact_sheet(mp4, out_jpg, cols=6, rows=5):
    """Hoja de contactos del vídeo (para revisarlo de un vistazo sin descargarlo)."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout.strip() or 40)
    n = cols * rows
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf",
                    f"fps={n / dur:.4f},scale=270:480,tile={cols}x{rows}", "-frames:v", "1", "-q:v", "4", out_jpg], check=True)
    return out_jpg


def make(out, seed=0, topic=None):
    """Tema -> guion verificado -> ilustraciones -> vídeo. Devuelve (meta, S, caption) o lanza un error si no sale."""
    errs = []
    for tp in ([topic] if topic else pick_topics(seed)):
        try:
            tema, c = content_for(tp)
            imgs = illustrations(c)
            if not MOCK and os.environ.get("GEMINI_API_KEY") and sum(1 for a, _ in imgs if a is not None) < len(c["escenas"]) - 2:
                raise RuntimeError("faltan demasiadas ilustraciones")
            meta = build(c, imgs, out, seed, tema)
            cap = caption(c, seed)
            open(out.replace(".mp4", ".txt"), "w").write(cap)
            meta["topic"] = tp
            S = {"screen_hook": c["titulo"], "hook_line": c["escenas"][0]["voz"], "comment_prompt": c["pregunta_comentarios"],
                 "yt_title": c["titulo"], "_fmt": FMT, "guion": c}
            return meta, S, cap
        except Exception as e:
            errs.append(f"{tp}: {str(e)[:200]}"); print(f"explicado: {tp} no ha podido salir ({str(e)[:300]})", flush=True)
    raise RuntimeError("ningún tema dio un vídeo explicado verificado: " + " | ".join(errs))


def mark_published(meta):
    L = log()
    L.append({"date": str(datetime.date.today()), "topic": meta.get("topic"), "subtema": meta.get("subtema"),
              "titulo": meta.get("hook"), "ilustraciones": meta.get("ilustraciones")})
    json.dump(L, open(LOG, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    o = f"out/explicado_{datetime.date.today()}.mp4"
    m, S_, cap_ = make(o, seed=datetime.date.today().toordinal(), topic=sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({k: v for k, v in m.items() if k != "slides"}, ensure_ascii=False)); print(cap_)
