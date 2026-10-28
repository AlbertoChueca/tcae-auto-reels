"""Agente verificador: nada se publica sin pasar por aquí.

1. verify_questions(): revisa cada pregunta del banco ANTES de usarla: ¿la respuesta marcada es correcta y la única
   correcta? ¿la explicación de la app la respalda? Para legislación y plazos busca los artículos relevantes en el texto
   real de la norma (fuentes/*.txt, descargado del BOE) y exige una CITA LITERAL que luego se comprueba en código: si la
   cita no aparece de verdad en el texto, la pregunta no se publica (fuente_ok = false).
2. verify_script(): revisa lo que han escrito los agentes para el reel (explicación, trampa, truco, afirmación del mito,
   puntos clave): solo puede decir lo que respaldan la pregunta, la explicación de la app, las fichas y la fuente.
3. python verifier.py [N]  -> verifica N preguntas pendientes y escribe banco/informe_verificacion.md (dudosas y
   posibles errores del banco, útil también para corregir la propia web app).
"""
import datetime, json, os, re, sys, unicodedata

import questions as QB

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "fuentes")
REPORT = os.path.join(HERE, "banco", "informe_verificacion.md")
STOP = set("de la el los las y o a en por para con que del al se su sus es un una lo le como mas más ser son este esta "
           "estos estas cual cuál cuales indique señale opcion opción correcta incorrecta respuesta según segun ley "
           "siguiente siguientes entre sobre sin no si".split())

ROLE = """Eres el VERIFICADOR de contenidos de Aprueba TCAE, una app para opositores a Técnico en Cuidados Auxiliares de
Enfermería (TCAE) de toda España. Tu trabajo es evitar que publiquemos un error: un opositor que estudia con un
dato falso suspende por nuestra culpa. Eres estricto, preciso y nunca inventas normativa, artículos ni cifras.
Ante la duda, marcas "dudosa"."""


def fold(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(c) != "Mn")


def toks(t):
    return [w for w in re.findall(r"[a-z0-9]+", fold(t)) if w not in STOP and len(w) > 2]


# ------------------------------------------------------------------ fuentes
_CFG, _TXT = {}, {}


def cfg():
    if not _CFG:
        _CFG.update(json.load(open(os.path.join(SRC_DIR, "fuentes.json"))))
    return _CFG


def norm_text(key):
    if key not in _TXT:
        n = cfg()["normas"].get(key) or {}
        p = os.path.join(SRC_DIR, n.get("archivo", "-"))
        _TXT[key] = open(p).read() if os.path.exists(p) else ""
    return _TXT[key]


def articles(key):
    """[(etiqueta, texto)] partiendo la norma por artículos (o por párrafos si no hay artículos)."""
    txt = norm_text(key)
    if not txt:
        return []
    parts = re.split(r"\n(?=\s*(?:Art[íi]culo|Disposici[óo]n (?:adicional|transitoria|final|derogatoria))\b)", txt)
    if len(parts) < 3:
        parts = [txt[i:i + 1500] for i in range(0, len(txt), 1500)]
    out = []
    for p in parts:
        head = re.match(r"\s*((?:Art[íi]culo|Disposici[óo]n)[^.\n]{0,60})", p)
        out.append(((head.group(1).strip() if head else p[:40].strip()), p.strip()))
    return out


def sources_for(q):
    """Normas del tema + cualquier norma cuyo número (p. ej. "9/2017") aparezca en la pregunta, opciones o explicación."""
    keys = list(cfg()["temas"].get(q["topic"], []))
    txt = " ".join([q.get("pregunta", "")] + list(q.get("opciones", [])) + [q.get("explicacion", "")])
    for k, n in cfg()["normas"].items():
        nums = [c for c in n.get("clave", []) if re.match(r"\d+/\d{4}$", c)]
        if nums and any(re.search(rf"(?<!\d){re.escape(c)}(?!\d)", txt) for c in nums) and k not in keys:
            keys.append(k)
    return [k for k in keys if norm_text(k)]


def passages(q, k=3, max_chars=7000):
    """Artículos más relacionados con la pregunta en las normas de su tema."""
    want = set(toks(q["pregunta"] + " " + q["opciones"][q["correcta"]] + " " + q.get("explicacion", "")))
    nums = re.findall(r"art[íi]culos?\.?\s*(\d+)", q["pregunta"] + " " + q.get("explicacion", ""), re.I)
    scored = []
    for key in sources_for(q):
        title = cfg()["normas"][key]["titulo"]
        for lab, txt in articles(key):
            s = len(want & set(toks(txt))) / (1 + 0.002 * len(txt))
            if any(re.match(rf"Art[íi]culo\s+{n}\b", lab) for n in nums):
                s += 50
            scored.append((s, title, lab, txt))
    scored.sort(key=lambda x: -x[0])
    out, total = [], 0
    for key in sources_for(q):                      # el título oficial (número y fecha de la norma) siempre va incluido
        head = norm_text(key).split("\n", 1)[0].lstrip("# ").split(" · ")[0]
        if head:
            out.append({"norma": cfg()["normas"][key]["titulo"], "articulo": "Título oficial", "texto": head})
    for s, title, lab, txt in [x for x in scored if x[3].strip() and not x[3].lstrip().startswith("# ")][:k]:
        txt = txt[:3000]
        out.append({"norma": title, "articulo": lab, "texto": txt}); total += len(txt)
        if total > max_chars:
            break
    return out


def quote_in(cita, texts):
    """¿La cita aparece de verdad en el texto de la fuente? (sin tildes ni mayúsculas, tolerante a puntuación)."""
    c = " ".join(re.findall(r"[a-z0-9]+", fold(cita)))
    if len(c.split()) < 4:
        return False
    hay = " ".join(re.findall(r"[a-z0-9]+", fold(" ".join(texts))))
    if c in hay:
        return True
    w = c.split(); grams = [" ".join(w[i:i + 5]) for i in range(max(1, len(w) - 4))]
    return sum(g in hay for g in grams) / len(grams) >= 0.85


# ------------------------------------------------------------------ 1. preguntas
def _q_block(q, i):
    src = passages(q) if q["bloque"] in QB.STRICT or sources_for(q) else []
    fs = QB.fichas(q["topic"], 3, words=toks(q["pregunta"]))
    return src, (f"### PREGUNTA {i} (id {q['id']}) · tema: {q['tema']} · origen: "
                 f"{'EXAMEN OFICIAL ' + q['examen']['titulo'] if q.get('examen') else 'app'}\n"
                 f"{q['pregunta']}\n" + "\n".join(f"{QB.LETTERS[k]}) {o}" for k, o in enumerate(q["opciones"])) +
                 f"\nMarcada como correcta: {QB.LETTERS[q['correcta']]}\nExplicación de la app: {q.get('explicacion')}\n"
                 + ("Fichas de la app del mismo tema:\n" + "\n".join(f"- {f['q']} -> {f['a']}" for f in fs) + "\n" if fs else "")
                 + ("TEXTO REAL DE LA FUENTE (artículos más relacionados):\n" + "\n".join(
                     f"[{p['norma']} · {p['articulo']}]\n{p['texto']}" for p in src) if src
                    else "TEXTO DE LA FUENTE: no disponible.") + "\n")


def verify_questions(qs):
    """Verifica una lista de preguntas y guarda el resultado en banco/verificacion.json. Devuelve {id: resultado}."""
    import gemini
    v = QB.verif()
    blocks, srcs = [], {}
    for i, q in enumerate(qs, 1):
        s, b = _q_block(q, i); blocks.append(b); srcs[q["id"]] = s
    res = gemini.ask(f"""{ROLE}

Revisa estas {len(qs)} preguntas tipo test del banco de la app.
Para cada una decide:
- "ok": la respuesta marcada es correcta y es la ÚNICA correcta (o la mejor sin discusión) según la normativa o el
  conocimiento sanitario vigente en España, y nada del enunciado es erróneo.
- "dudosa": no puedes confirmarlo con seguridad, la pregunta es ambigua, depende de una norma que no tienes, o hay datos
  que pueden haber cambiado (cifras de población, economía, estructuras orgánicas, plazos reformados).
- "error": la respuesta marcada es incorrecta o hay más de una correcta.
Las preguntas de EXAMEN OFICIAL usan la plantilla provisional del tribunal: márcalas "ok" si es defendible; si crees que
la plantilla está mal, "dudosa" y explica por qué.
Si se da TEXTO REAL DE LA FUENTE: "referencia" = norma y artículo que lo respaldan, y "cita" = un fragmento COPIADO
LITERALMENTE de ese texto (8-35 palabras) que demuestre la respuesta. Si el texto dado no lo demuestra, cita "" y como
mucho "dudosa". Si no hay texto de fuente, "referencia" = "" y "cita" = "".
"motivo": una frase en español (por qué ok / qué falla). "correcta_sugerida": letra que crees correcta si es "error".

{chr(10).join(blocks)}
Devuelve JSON: {{"resultados": [{{"id": str, "veredicto": "ok"|"dudosa"|"error", "motivo": str, "referencia": str,
"cita": str, "correcta_sugerida": str}}]}}""", 0.1, careful=True)
    lst = res.get("resultados") or res.get("results") or (res if isinstance(res, list) else [])
    lst = [r for r in lst if isinstance(r, dict)]
    got = {str(r.get("id")).strip(): r for r in lst}
    if lst and not any(q["id"] in got for q in qs) and len(lst) == len(qs):    # el modelo cambió los ids: por orden
        got = {q["id"]: r for q, r in zip(qs, lst)}
    if not lst:
        print("verificador: respuesta sin resultados:", json.dumps(res, ensure_ascii=False)[:300], flush=True)
    out = {}
    for q in qs:
        r = got.get(q["id"])
        if not r:
            continue
        ver = r.get("veredicto") if r.get("veredicto") in ("ok", "dudosa", "error") else "dudosa"
        texts = [p["texto"] for p in srcs[q["id"]]]
        fuente_ok = bool(texts and r.get("cita") and quote_in(r["cita"], texts))
        ref = (r.get("referencia") or "").strip()
        if ref and not fuente_ok:
            ref = ""                                  # una referencia sin cita comprobada no se muestra nunca
        out[q["id"]] = {"veredicto": ver, "motivo": (r.get("motivo") or "")[:300], "fuente_ok": fuente_ok,
                        "referencia": ref[:80], "cita": (r.get("cita") or "")[:400] if fuente_ok else "",
                        "correcta_sugerida": r.get("correcta_sugerida") if ver == "error" else None,
                        "fecha": str(datetime.date.today())}
    v.update(out); QB.save_verif(v)
    n_ok = sum(1 for k in out if QB.publishable(next(q for q in qs if q["id"] == k), v))
    print(f"verificador: {len(out)} preguntas revisadas, {n_ok} publicables", flush=True)
    return out


# ------------------------------------------------------------------ 2. guion del reel
def verify_script(items, script, fmt):
    """items: preguntas preparadas del reel. Devuelve (ok, problemas). Si el verificador falla, NO se aprueba."""
    import gemini
    v = QB.verif()
    ctx = []
    if "pregunta" not in items[0]:                       # fichas de la app
        ctx.append("Fichas de la app (tema " + items[0]["tema"] + "):\n" + "\n".join(f"- {f['q']} -> {f['a']}" for f in items))
    for P in (items if "pregunta" in items[0] else []):
        r = v.get(P["id"], {})
        fs = QB.fichas(P["topic"], 3, words=toks(P["pregunta"]))
        ctx.append(f"Pregunta: {P['pregunta']}\n" + "\n".join(f"{QB.LETTERS[k]}) {o}" for k, o in enumerate(P["op"]))
                   + f"\nCorrecta: {P['letra']}\nExplicación de la app: {P.get('explicacion')}\n"
                   + ("Fichas de la app: " + " | ".join(f"{f['q']} -> {f['a']}" for f in fs) + "\n" if fs else "")
                   + (f"Fuente verificada ({r.get('referencia')}): \"{r.get('cita')}\"\n" if r.get("fuente_ok") else ""))
    try:                                             # actualidad con fuente (agente cazatendencias)
        import tendencias
        al = [l for P in items for l in tendencias.material_lines(P.get("topic"))]
        if al:
            ctx.append("Actualidad comprobada por el agente cazatendencias (vale SOLO para gancho y descripción):\n" + "\n".join(al))
    except Exception:
        pass
    try:
        import estudio
        c = estudio.app_counts(items)
        ctx.append(f"Datos reales de la app: el tema {c['tema']} tiene {c['preguntas_tema']} preguntas y {c['fichas_tema']} "
                   f"flashcards; en total {__import__('marca').PREGUNTAS_FRASE}; se practica gratis en apruebatcae.com.")
    except Exception:
        pass
    keys = ("hook_line", "screen_hook", "reveal_line", "explicacion", "trampa", "trampa_porque", "truco", "truco_line",
            "afirmacion", "veredicto", "puntos", "titulo_norma", "caption_hook", "comment_prompt", "escena", "save_line",
            "save_caption", "reto_line", "share_line", "tag_caption", "cta_line", "app_caption", "seo_line", "yt_title",
            "follow_line", "follow_caption", "cierre_line")
    texts = {k: script.get(k) for k in keys if script.get(k)}
    try:
        res = gemini.ask(f"""{ROLE}
Formato del reel: {fmt}.
MATERIAL DE REFERENCIA (lo único que vale como verdad):
{chr(10).join(ctx)}

TEXTOS QUE VAN A SALIR EN EL VÍDEO / DESCRIPCIÓN:
{json.dumps(texts, ensure_ascii=False, indent=1)}

Comprueba frase a frase: ¿todo lo que afirman estos textos está respaldado por el material de referencia? Cualquier dato
nuevo (artículo, cifra, plazo, porcentaje, órgano, fecha, estadística del tipo "el 80% falla") que no esté en el
material es un problema. La letra correcta, la trampa y el veredicto MITO/REALIDAD deben ser coherentes con la pregunta.
También es un problema prometer cosas ("esto cae seguro", "aprobarás") o tono infantil.
Devuelve JSON: {{"ok": bool, "problemas": [{{"campo": str, "frase": str, "motivo": str}}]}}""", 0.1, careful=True)
    except Exception as e:
        return False, [{"campo": "-", "frase": "-", "motivo": f"verificador no disponible: {str(e)[:150]}"}]
    probs = res.get("problemas") or []
    return bool(res.get("ok")) and not probs, probs


# ------------------------------------------------------------------ 3. informe del banco
def report():
    v = QB.verif(); qs = {q["id"]: q for q in QB.load()}
    rows = [r for r in v.items() if r[0] in qs]
    pub = sum(QB.publishable(qs[k], v) for k, _ in rows)
    bad = [(k, r) for k, r in rows if r["veredicto"] in ("error", "dudosa")]
    nofuente = [(k, r) for k, r in rows if r["veredicto"] == "ok" and qs[k]["bloque"] in QB.STRICT and not r.get("fuente_ok")]
    L = [f"# Informe del verificador ({datetime.date.today()})\n",
         f"- Preguntas en el banco: {len(qs)} · revisadas: {len(rows)} · **publicables: {pub}**",
         f"- Posibles errores: {sum(r['veredicto'] == 'error' for _, r in bad)} · dudosas: {sum(r['veredicto'] == 'dudosa' for _, r in bad)}"
         f" · correctas pero sin texto de la norma para citar: {len(nofuente)}\n",
         "Las marcadas como posible error conviene revisarlas también en la web app.\n"]
    for title, lst in (("Posibles errores", [x for x in bad if x[1]["veredicto"] == "error"]),
                       ("Dudosas", [x for x in bad if x[1]["veredicto"] == "dudosa"])):
        L.append(f"\n## {title} ({len(lst)})\n")
        for k, r in lst[:300]:
            q = qs[k]
            L.append(f"- **[{q['tema']}]** {q['pregunta']} — marcada {QB.LETTERS[q['correcta']]}) "
                     f"{q['opciones'][q['correcta']]}" + (f" · sugerida: {r.get('correcta_sugerida')}" if r.get("correcta_sugerida") else "")
                     + f"\n  - {r.get('motivo')}")
    open(REPORT, "w").write("\n".join(L) + "\n")
    return f"verificador: {pub} publicables de {len(rows)} revisadas ({len(qs)} en el banco)"


def run(n=80, fmt_kind="normal"):
    v = QB.verif()
    import random
    pend = [q for q in QB.load() if q["id"] not in v and QB.fits(q, fmt_kind)]
    random.Random(str(datetime.date.today())).shuffle(pend)          # mezcla temas y bloques en cada tanda
    pend.sort(key=QB.regional)                                        # las generales primero; Aragón al final
    week_ago = str(datetime.date.today() - datetime.timedelta(days=7))
    redo = [q for q in QB.load() if q["id"] in v and q["bloque"] in QB.STRICT and not v[q["id"]].get("fuente_ok")
            and v[q["id"]].get("veredicto") in ("ok", "dudosa") and v[q["id"]].get("fecha", "") <= week_ago
            and sources_for(q)]                                          # se reintentan con las fuentes nuevas
    pend = redo[: n // 4] + pend
    for k in range(0, min(n, len(pend)), 8):
        try:
            verify_questions(pend[k:k + 8])
        except Exception as e:
            print("lote fallido:", str(e)[:200], flush=True)
    if not os.path.exists(QB.VERIF_F):
        QB.save_verif_f({})
    try:                                                     # y una tanda de fichas para el repaso exprés
        vf = QB.verif_f()
        pend_f = [f for f in QB.fichas_candidates(str(datetime.date.today())) if f["id"] not in vf][:40]
        for k in range(0, len(pend_f), 10):
            verify_fichas(pend_f[k:k + 10])
    except Exception as e:
        print("fichas: lote fallido:", str(e)[:200], flush=True)
    msg = report(); print(msg)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(open(REPORT).read()[:60000])
    return msg


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 80)


# ------------------------------------------------------------------ 4. fichas (flashcards_express)
def verify_fichas(fs):
    """Verifica fichas de la app (pregunta -> respuesta). Legislación y plazos exigen cita literal de la fuente."""
    import gemini
    v = QB.verif_f(); blocks, srcs = [], {}
    for i, f in enumerate(fs, 1):
        q = {"topic": f["topic"], "pregunta": f["q"], "opciones": [f["a"]], "correcta": 0, "explicacion": "", "bloque": f["bloque"]}
        src = passages(q) if f["bloque"] in QB.STRICT or sources_for(q) else []
        srcs[f["id"]] = src
        blocks.append(f"### FICHA {i} (id {f['id']}) · tema {f['tema']}\nPregunta: {f['q']}\nRespuesta: {f['a']}\n"
                      + ("TEXTO REAL DE LA FUENTE:\n" + "\n".join(f"[{p['norma']} · {p['articulo']}]\n{p['texto']}" for p in src)
                         if src else "TEXTO DE LA FUENTE: no disponible.") + "\n")
    res = gemini.ask(f"""{ROLE}
Revisa estas fichas de repaso de la app. "ok" solo si la respuesta es correcta, completa para lo que se pregunta y vigente;
"dudosa" si no puedes confirmarlo o es ambigua; "error" si es incorrecta. Si hay texto de la fuente, "cita" = fragmento
COPIADO LITERALMENTE (8-35 palabras) que lo demuestre, si no "".
{chr(10).join(blocks)}
Devuelve JSON: {{"resultados": [{{"id": str, "veredicto": "ok"|"dudosa"|"error", "motivo": str, "cita": str}}]}}""", 0.1, careful=True)
    for r in res.get("resultados", []):
        f = next((x for x in fs if x["id"] == r.get("id")), None)
        if not f:
            continue
        texts = [p["texto"] for p in srcs[f["id"]]]
        ver = r.get("veredicto") if r.get("veredicto") in ("ok", "dudosa", "error") else "dudosa"
        v[f["id"]] = {"veredicto": ver, "motivo": (r.get("motivo") or "")[:300],
                      "fuente_ok": bool(texts and r.get("cita") and quote_in(r["cita"], texts)),
                      "fecha": str(datetime.date.today())}
    QB.save_verif_f(v)
    print(f"verificador: {len(fs)} fichas revisadas", flush=True)
