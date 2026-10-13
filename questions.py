"""Banco de preguntas: elegir la(s) pregunta(s) de cada reel sin repetir, solo entre las verificadas.

Reglas:
- Solo preguntas propias de la web app (banco/preguntas.json, importadas con import_bank.py) o de exámenes oficiales.
- Una pregunta solo sale si el verificador la ha dado por buena (banco/verificacion.json). Las de legislación y plazos
  necesitan además una cita literal encontrada en el texto de la norma (fuentes/), así nunca se publica normativa inventada.
- Nunca se repite una pregunta hasta agotar las elegibles; se evita repetir tema en los últimos reels.
- Las opciones de las preguntas de la app se barajan (salvo "todas/ninguna/A y B...") para que la respuesta no sea casi
  siempre la A; las de examen oficial se muestran en su orden original.
"""
import datetime, json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, "banco", "preguntas.json")
FICHAS = os.path.join(HERE, "banco", "fichas.json")
VERIF = os.path.join(HERE, "banco", "verificacion.json")
USED = os.path.join(HERE, "used.json")
STRICT = {"legislacion", "fechas"}          # bloques que exigen cita literal de la fuente
LETTERS = "ABCD"
LIMITS = {"normal": (170, 80), "corta": (115, 58)}
NO_SHUFFLE = re.compile(r"\b(todas|ninguna|ambas|anteriores|las dos|son correctas|son ciertas|a y b|b y c|a y c|a, b|"
                        r"opciones? [abcd]\b|respuestas? [abcd]\b)", re.I)


def load():
    return json.load(open(BANK))


_F = {}


def fichas(topic, n=4, seed=0, words=()):
    """Fichas de la app del mismo tema (contexto real para el guionista y el verificador)."""
    if not _F:
        for f in (json.load(open(FICHAS)) if os.path.exists(FICHAS) else []):
            _F.setdefault(f["topic"], []).append(f)
    fs = _F.get(topic, [])
    if words:
        ws = {w for w in words if len(w) > 4}
        fs = sorted(fs, key=lambda f: -len(ws & set(re.findall(r"\w+", (f["q"] + " " + f["a"]).lower()))))
        return fs[:n]
    return random.Random(seed).sample(fs, min(n, len(fs)))


def verif():
    try:
        return json.load(open(VERIF))
    except Exception:
        return {}


def save_verif(v):
    os.makedirs(os.path.dirname(VERIF), exist_ok=True)
    json.dump(v, open(VERIF, "w"), ensure_ascii=False, indent=0)


def used():
    try:
        return json.load(open(USED))
    except Exception:
        return []


def mark_used(qs, fmt):
    u = used()
    for q in qs:
        u.append({"id": q["id"], "topic": q.get("topic"), "fecha": str(datetime.date.today()), "formato": fmt})
    json.dump(u, open(USED, "w"), indent=0)


def fits(q, kind="normal"):
    ql, ol = LIMITS[kind]
    return len(q["pregunta"]) <= ql and all(len(o) <= ol for o in q["opciones"])


def publishable(q, v):
    r = v.get(q["id"])
    if not r or r.get("veredicto") != "ok":
        return False
    return r.get("fuente_ok") or q["bloque"] not in STRICT


def candidates(fmt, bloque=None, seed=0):
    """Preguntas que encajan con el formato (longitud, bloque, origen), sin usar todavía y mezcladas con la semilla."""
    qs = load()
    kind = "corta" if fmt == "simulacro_3" else "normal"
    qs = [q for q in qs if fits(q, kind)]
    if fmt == "examen_real":
        qs = [q for q in qs if q["origen"] == "examen"]
    elif fmt == "legislacion_30s":
        qs = [q for q in qs if q["bloque"] == "legislacion"]
    elif bloque and bloque != "mixto":
        sub = [q for q in qs if q["bloque"] == bloque or (bloque == "aragon" and q["bloque"] in ("geografia", "fechas"))]
        qs = sub or qs
    if fmt in ("error_tipico", "truco_memorizar", "mito_realidad"):       # necesitan una explicación con contenido
        qs = [q for q in qs if q["origen"] == "webapp" and len(q["explicacion"].split()) >= 8] or qs
    u = used()
    done = {x["id"] for x in u}
    fresh = [q for q in qs if q["id"] not in done]
    if not fresh:                                    # banco agotado para este formato: vuelve a empezar
        fresh = qs
    recent_topics = {x.get("topic") for x in u[-6:]}
    rng = random.Random(seed)
    rng.shuffle(fresh)
    fresh.sort(key=lambda q: q["topic"] in recent_topics)       # temas recientes al final
    return fresh


def pick(fmt, bloque=None, seed=0, n=1, verify=None, max_checks=40):
    """Devuelve n preguntas publicables. Las aún no verificadas se verifican aquí (en lotes) con `verify(lista)`."""
    v = verif()
    cands = candidates(fmt, bloque, seed)
    out, topics = [], set()
    ok_now = [q for q in cands if publishable(q, v)]
    for q in ok_now:
        if q["topic"] not in topics:
            out.append(q); topics.add(q["topic"])
        if len(out) == n:
            return out
    if verify:
        pending = [q for q in cands if q["id"] not in v][:max_checks]
        for k in range(0, len(pending), 8):
            verify(pending[k:k + 8]); v = verif()
            for q in pending[k:k + 8]:
                if publishable(q, v) and q["topic"] not in topics:
                    out.append(q); topics.add(q["topic"])
                if len(out) == n:
                    return out
    if bloque and bloque != "mixto":                     # el bloque del experimento no tiene preguntas listas: cualquier bloque
        return pick(fmt, None, seed, n, verify, max_checks)
    raise LookupError(f"no hay suficientes preguntas verificadas para '{fmt}' ({len(out)}/{n}); "
                      f"ejecuta el workflow 'Verificar banco' o añade textos en fuentes/")


def prepare(q, seed=0):
    """Pregunta lista para el vídeo: opciones (quizá barajadas) con letra, letra correcta y textos."""
    idx = list(range(4))
    if q["origen"] != "examen" and not any(NO_SHUFFLE.search(o) for o in q["opciones"]):
        random.Random(f"{q['id']}-{seed}").shuffle(idx)
    opts = [q["opciones"][i] for i in idx]
    c = idx.index(q["correcta"])
    return {**q, "op": opts, "ok": c, "letra": LETTERS[c], "orden": idx}


# ------------------------------------------------------------------ fichas (formato flashcards_express)
VERIF_F = os.path.join(HERE, "banco", "verificacion_fichas.json")
_TEMAS = {}


def tema_de(topic):
    if not _TEMAS:
        for q in load():
            _TEMAS.setdefault(q["topic"], (q["tema"], q["bloque"]))
    return _TEMAS.get(topic, (topic, "clinico"))


def ficha_id(f):
    import hashlib
    return hashlib.sha1(f"{f['topic']}|{f['q']}".encode()).hexdigest()[:10]


def verif_f():
    try:
        return json.load(open(VERIF_F))
    except Exception:
        return {}


def save_verif_f(v):
    json.dump(v, open(VERIF_F, "w"), ensure_ascii=False, indent=0)


def fichas_candidates(seed=0):
    """Fichas cortas de la app agrupadas por tema; devuelve las del tema elegido (sin usar, tema no reciente)."""
    fichas(None, 0)                                   # carga _F
    u = used(); done = {x["id"] for x in u}; recent = {x.get("topic") for x in u[-8:]}
    groups = []
    for topic, fs in _F.items():
        ok = [f for f in fs if 12 <= len(f["q"]) <= 90 and 3 <= len(f["a"]) <= 140 and topic != "vocabulario"
              and (f["q"].rstrip().endswith("?") or len(f["q"].split()) >= 5)]
        ok = [f for f in ok if ficha_id(f) not in done] or ok
        if len(ok) >= 4:
            groups.append((topic in recent, topic, ok))
    rng = random.Random(seed); rng.shuffle(groups); groups.sort(key=lambda g: g[0])
    out = []
    for _, topic, fs in groups:
        tema, bloque = tema_de(topic)
        rng.shuffle(fs)
        out.extend({"id": ficha_id(f), "topic": topic, "tema": tema, "bloque": bloque, "q": f["q"], "a": f["a"]} for f in fs)
    return out


def pick_fichas(seed=0, n=4, verify=None, max_topics=4):
    v = verif_f()
    cands = fichas_candidates(seed)
    by_topic = {}
    for f in cands:
        by_topic.setdefault(f["topic"], []).append(f)
    for topic in list(by_topic)[:max_topics]:
        fs = by_topic[topic]
        good = [f for f in fs if _ficha_ok(f, v)]
        if len(good) < n and verify:
            pend = [f for f in fs if f["id"] not in v][:12]
            if pend:
                verify(pend); v = verif_f()
                good = [f for f in fs if _ficha_ok(f, v)]
        if len(good) >= n:
            return good[:n]
    raise LookupError("no hay 4 fichas verificadas del mismo tema; ejecuta 'Verificar banco'")


def _ficha_ok(f, v):
    r = v.get(f["id"])
    return bool(r and r.get("veredicto") == "ok" and (r.get("fuente_ok") or f["bloque"] not in STRICT))
