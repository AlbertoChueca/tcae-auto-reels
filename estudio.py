"""Estudio creativo: 10 agentes especialistas que hacen cada reel más premium, más compartible y más útil para que
quien prepara la oposición de TCAE siga la cuenta y use la app. Se suman a la sala de guionistas (agents.py) y al
verificador (verifier.py); TODO lo que estos agentes escriben y sale en pantalla o en la descripción pasa después por el
verificador, así que pueden ser creativos sin poder colar un dato falso.

  1. directora_creativa  concepto visual del reel y la idea de la ilustración (coherente con el estilo del día)
  2. ilustradora         genera la imagen ORIGINAL (Gemini) para el gancho, el caso práctico y el estilo "ilustrado"
  3. revisora_visual     revisa la imagen: sin texto, sin errores de higiene/EPI, sin anatomía rota, nada sensible
  4. narradora_casos     convierte la pregunta en una escena de turno (caso práctico) sin añadir datos
  5. memoria             invita a GUARDAR el reel con una técnica de repaso (repetición espaciada, autoevaluación)
  6. viralidad           retos para comentar y etiquetar a la compañera de estudio; línea para compartir
  7. series              series fijas por día de la semana con número de capítulo y avance de mañana -> seguir
  8. embudo_app          lleva a la app con datos REALES de la app (nº de preguntas/fichas de ese tema)
  9. seo                 palabras que busca un opositor (TikTok/YouTube/Instagram), título de YouTube
 10. ritmo               ritmo y música: velocidad de voz y energía según lo que retiene a la audiencia

Cada agente tiene su cuaderno en agents/estudio_<nombre>.md, reescrito cada día con los resultados reales.
Todo es opcional: si un agente falla, el reel sigue con lo que ya tenía.
"""
import datetime, json, os, re

import marca as M

HERE = os.path.dirname(os.path.abspath(__file__))
NB_DIR = os.path.join(HERE, "agents")
STAMP = os.path.join(NB_DIR, "estudio_last_update.txt")
IMG_LOG = os.path.join(HERE, "image_log.jsonl")

ROLES = {
    "directora_creativa": "DIRECTORA CREATIVA. Decides el concepto visual de cada reel y la idea de la ilustración, para que "
                          "el canal se vea premium, reconocible y variado, sin repetir ideas recientes.",
    "ilustradora": "ILUSTRADORA. Conviertes la idea en una imagen original vertical de calidad editorial, coherente con la marca.",
    "revisora_visual": "REVISORA VISUAL. Revisas cada imagen como lo haría una supervisora de enfermería y una directora de arte: "
                       "sin texto, sin errores de higiene o EPI, sin anatomía deforme, nada sensible.",
    "narradora_casos": "NARRADORA DE CASOS. Conviertes una pregunta del temario en una escena breve y realista de un turno de TCAE "
                       "(planta, urgencias, centro de salud, residencia) que haga sentir que el examen va de su trabajo real.",
    "memoria": "EXPERTA EN MEMORIA Y TÉCNICAS DE ESTUDIO. Haces que la gente GUARDE el reel para repasarlo, con técnicas reales "
               "(repetición espaciada, autoevaluación, recuperación activa).",
    "viralidad": "ESPECIALISTA EN COMPARTIR. Creas retos y frases que hacen que la gente comente, etiquete a su compañera de "
                 "oposición y envíe el reel por privado.",
    "series": "RESPONSABLE DE SERIES. Construyes citas fijas (una serie por día de la semana, con número de capítulo) para que "
              "seguir la cuenta tenga sentido.",
    "embudo_app": "RESPONSABLE DE CONVERSIÓN A LA APP. Conectas cada reel con lo que la persona puede practicar en apruebatcae.com, "
                  "solo con datos reales de la app.",
    "seo": "ESPECIALISTA EN BÚSQUEDA (SEO social). Eliges las palabras exactas que busca un opositor de TCAE en TikTok, YouTube "
           "e Instagram y las colocas de forma natural.",
    "ritmo": "EDITORA DE RITMO Y RETENCIÓN. Decides la velocidad de la voz y la energía de la música para que no se vayan antes "
             "de la solución.",
}
NAMES = list(ROLES)

# Serie fija de cada día (0 = lunes). El hueco de mediodía sigue la serie; el de la noche lo elige el piloto automático.
SERIES = {0: ("Lunes de legislación", "legislacion_30s"), 1: ("Martes de trampas", "error_tipico"),
          2: ("Miércoles de simulacro", "simulacro_3"), 3: ("Jueves de casos prácticos", "caso_practico"),
          4: ("Viernes de mitos", "mito_realidad"), 5: ("Sábado de reto", "pregunta_del_dia"),
          6: ("Domingo de examen real", "examen_real")}

AUDIENCE = ("Público: adultos que preparan las oposiciones de TCAE en cualquier comunidad de España, muchas trabajando a "
            "turnos. Cuenta generalista: no menciones una comunidad concreta salvo que la pregunta sea de su temario. "
            "Español de España, tono cercano y profesional, nada infantil, sin promesas ni estadísticas inventadas.")


def _ask(prompt, temperature=0.7, careful=False, parts=None):
    import gemini
    return gemini.ask(parts or prompt, temperature, careful=careful)


def notebook(name):
    try:
        return open(os.path.join(NB_DIR, f"estudio_{name}.md")).read().strip()[:1200]
    except Exception:
        return ""


def brief(name):
    nb = notebook(name)
    com = ""
    try:
        import agents
        com = agents.notebook("comunidad")
    except Exception:
        pass
    return (f"Eres la {ROLES[name]}\n{AUDIENCE}" + (f"\nTU CUADERNO (lecciones de nuestros datos reales):\n{nb}" if nb else "")
            + (f"\nLO QUE DICE LA AUDIENCIA:\n{com}" if com else ""))


def _w(v, lo, hi):
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    return v if lo <= len(v.split()) <= hi else None


def _clean(v):
    return re.sub(r"[^\w\s¿?¡!,.:'()/-]", "", v or "").strip()


def _log(kind, data):
    try:
        import reviewer
        reviewer._log("estudio_" + kind, data)
    except Exception:
        pass


def _desc(items):
    P = items[0]
    if "q" in P and "pregunta" not in P:
        return f"Fichas de {P['tema']}: " + " | ".join(f"{f['q']} -> {f['a']}" for f in items)
    return f"Tema: {P['tema']}. Pregunta: {P['pregunta']} Respuesta correcta: {P['op'][P['ok']]}"


# ------------------------------------------------------------------ 7. series (sin IA: siempre cierto)
def series_today(today=None, slot="mediodia"):
    today = today or datetime.date.today()
    name, fmt = SERIES[today.weekday()]
    n = 1
    try:
        for line in open(os.path.join(HERE, "log.jsonl")):
            if json.loads(line).get("series") == name:
                n += 1
    except Exception:
        pass
    nxt = SERIES[(today.weekday() + 1) % 7][0]
    return {"series": f"{name} · Nº {n}", "series_name": name, "series_fmt": fmt, "manana": nxt}


def series_lines(info, S):
    """Línea de seguir con el avance REAL de mañana (la serie de mañana es fija)."""
    out = {"follow_line": f"Mañana: {info['manana']}. ¡Síguenos!"}
    try:
        res = _ask(f"""{brief('series')}
Hoy es "{info['series']}". Mañana toca "{info['manana']}".
Escribe follow_line (máx. 8 palabras) para la tarjeta final que invite a seguir la cuenta para no perderse lo de mañana;
debe nombrar "{info['manana']}" tal cual. Y follow_caption (máx. 18 palabras) para la descripción.
Devuelve JSON: {{"follow_line": str, "follow_caption": str}}""")
        fl = _w(res.get("follow_line"), 3, 9)
        if fl and info["manana"].lower() in fl.lower():
            out["follow_line"] = _clean(fl)
        fc = _w(res.get("follow_caption"), 4, 20)
        if fc and info["manana"].lower() in fc.lower():
            out["follow_caption"] = fc
    except Exception as e:
        print("estudio series omitido:", str(e)[:120], flush=True)
    return out


# ------------------------------------------------------------------ 1. directora creativa
def directora(fmt, items, estilo, S):
    recent = []
    try:
        for line in open(IMG_LOG):
            recent.append(json.loads(line).get("idea"))
    except Exception:
        pass
    try:
        res = _ask(f"""{brief('directora_creativa')}
Reel de hoy: formato {fmt}, estilo visual "{estilo}". {_desc(items)}
Gancho: "{S.get('screen_hook')}". {('Escena: ' + S['escena']) if S.get('escena') else ''}
Propón:
- concepto: el concepto visual del reel en una frase (máx. 14 palabras).
- imagen_idea: UNA ilustración vertical que acompañe (máx. 45 palabras): escena de trabajo de una TCAE o de estudio de la
  oposición relacionada con el tema (sin texto en la imagen, sin pacientes identificables, sin sangre ni desnudos). Que no
  se parezca a estas recientes: {'; '.join([r for r in recent if r][-10:]) or 'ninguna'}.
- usar_imagen_gancho: true si la imagen hará el gancho más potente que el fondo de marca.
Devuelve JSON: {{"concepto": str, "imagen_idea": str, "usar_imagen_gancho": bool}}""", 0.9)
        idea = _w(res.get("imagen_idea"), 6, 60)
        return {"concepto": _w(res.get("concepto"), 3, 16) or "", "imagen_idea": idea,
                "usar_imagen": bool(res.get("usar_imagen_gancho")) or estilo == "ilustrado" or fmt == "caso_practico"}
    except Exception as e:
        print("estudio directora omitida:", str(e)[:120], flush=True)
        return {"imagen_idea": None, "usar_imagen": False}


# ------------------------------------------------------------------ 2 + 3. ilustradora y revisora visual
ART = {"ilustrado": "ilustración digital pictórica de calidad editorial, estilo novela gráfica suave, luz cálida cinematográfica",
       "noche": "ilustración digital de noche, luz de flexo cálida y azules profundos, atmósfera tranquila",
       "cuaderno": "ilustración plana moderna con textura de papel, colores suaves",
       "examen": "ilustración plana sobria y luminosa, tonos azules y grises",
       "minimal": "ilustración minimalista con pocos elementos y mucho espacio vacío, colores cálidos suaves",
       "clasico": "ilustración plana moderna y limpia con tonos verde azulado (teal) y ámbar"}
RULES = ("Imagen vertical 9:16. NADA de texto, letras, números, carteles legibles, logotipos ni marcas. Personas adultas "
         "genéricas (no famosas), con uniforme sanitario de TCAE (pijama sanitario) cuando aparezcan en el trabajo; higiene "
         "correcta: pelo recogido, sin anillos ni pulseras, guantes cuando toque. Sin sangre, heridas, agujas en primer plano, "
         "desnudos ni pacientes identificables. Manos y caras bien dibujadas. El motivo principal en el centro de la imagen y "
         "la parte inferior más oscura y despejada (ahí irá texto).")


def ilustradora(idea, estilo, seed=0):
    import gemini
    prompt = f"{ART.get(estilo, ART['clasico'])}. Escena: {idea}. {RULES}"
    return gemini.image(prompt), prompt


def revisora(img, idea):
    """Devuelve (ok, motivo, mejor_idea)."""
    import base64, io
    b = io.BytesIO(); im = img.copy(); im.thumbnail((640, 640)); im.convert("RGB").save(b, "JPEG", quality=82)
    try:
        res = _ask(None, 0.2, parts=[{"text": f"""{brief('revisora_visual')}
Idea pedida: {idea}
Revisa la imagen: ¿hay texto, letras, números o logos? ¿errores de higiene o EPI (anillos, pelo suelto, sin guantes con
fluidos), material clínico absurdo o peligroso? ¿anatomía deforme (manos, caras)? ¿algo sensible (sangre, desnudos, paciente
identificable, menores)? ¿se ve profesional y encaja con la idea? ¿el centro y la parte de abajo dejan sitio para texto?
"ok" = true solo si no hay ningún problema que una opositora o una supervisora notaría.
Devuelve JSON: {{"ok": bool, "problemas": [str], "mejor_idea": str}}"""},
                                         {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b.getvalue()).decode()}}])
        return bool(res.get("ok")), "; ".join(res.get("problemas") or [])[:300], _w(res.get("mejor_idea"), 6, 60)
    except Exception as e:
        return False, f"revisora no disponible: {str(e)[:100]}", None


def imagen_para(fmt, items, estilo, S, out_base):
    """Directora -> ilustradora -> revisora (1 redibujo). Devuelve (imagen o None, info)."""
    d = directora(fmt, items, estilo, S)
    idea = d.get("imagen_idea") or S.get("escena_visual")
    if S.get("escena_visual") and fmt == "caso_practico":
        idea = S["escena_visual"]
    if not idea or not d.get("usar_imagen"):
        return None, d
    for attempt in range(2):
        try:
            img, prompt = ilustradora(idea, estilo)
        except Exception as e:
            print("estudio ilustradora: sin imagen:", str(e)[:150], flush=True)
            return None, d
        ok, why, better = revisora(img, idea)
        print(f"estudio revisora visual: {'ok' if ok else 'rechazada'} {why[:120]}", flush=True)
        try:
            with open(IMG_LOG, "a") as f:
                f.write(json.dumps({"date": str(datetime.date.today()), "idea": idea, "ok": ok, "problemas": why},
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass
        if ok:
            img.save(out_base + "_ilustracion.jpg", quality=90)
            d["imagen_idea"] = idea
            return img, d
        idea = better or idea
    return None, d


# ------------------------------------------------------------------ 4. narradora de casos
def narradora(items, S):
    """Pule la escena del caso práctico y da la idea visual. Sin datos clínicos ni legales nuevos."""
    try:
        res = _ask(f"""{brief('narradora_casos')}
{_desc(items)}
Escena actual: "{S.get('escena')}"
Reescribe la escena (14-34 palabras, segunda persona, presente: "Estás de turno de mañana en..."): situación concreta y
creíble que lleve a la pregunta. Prohibido añadir datos clínicos, cifras, plazos o normas: solo ambientación (lugar, turno,
quién pregunta, qué estás haciendo). No reveles la respuesta.
Y escena_visual: descripción de la imagen de esa escena (máx. 40 palabras, sin texto).
Devuelve JSON: {{"escena": str, "escena_visual": str}}""", 0.8)
        out = {}
        if _w(res.get("escena"), 12, 36) and not re.search(r"\d", res["escena"]):
            out["escena"] = res["escena"].strip()
        if _w(res.get("escena_visual"), 6, 45):
            out["escena_visual"] = res["escena_visual"].strip()
        return out
    except Exception as e:
        print("estudio narradora omitida:", str(e)[:120], flush=True)
        return {}


# ------------------------------------------------------------------ 5. memoria
def memoria(fmt, items, S):
    try:
        res = _ask(f"""{brief('memoria')}
Formato {fmt}. {_desc(items)}
Escribe:
- save_line: texto corto en pantalla (máx. 6 palabras) que invite a GUARDAR el reel para repasar (p. ej. "Guárdalo y repásalo mañana").
- save_caption: una línea para la descripción (máx. 22 palabras) con una técnica de estudio real (repetición espaciada,
  autoevaluación, explicarlo en voz alta...) aplicada a este reel. Sin datos del temario, sin promesas.
Devuelve JSON: {{"save_line": str, "save_caption": str}}""", 0.8)
        out = {}
        if _w(res.get("save_line"), 2, 6): out["save_line"] = _clean(res["save_line"])
        if _w(res.get("save_caption"), 6, 24) and not re.search(r"\d+ ?%", res["save_caption"]): out["save_caption"] = res["save_caption"].strip()
        return out
    except Exception as e:
        print("estudio memoria omitida:", str(e)[:120], flush=True)
        return {}


# ------------------------------------------------------------------ 6. viralidad
def viralidad(fmt, items, S):
    try:
        res = _ask(f"""{brief('viralidad')}
Formato {fmt}. {_desc(items)} Gancho: "{S.get('screen_hook')}".
Escribe:
- reto_line: reto en pantalla durante la cuenta atrás (máx. 6 palabras), p. ej. "¿Tu compi de estudio la acierta?".
- share_line: línea de la tarjeta final (máx. 7 palabras) para enviar el reel a quien oposita contigo.
- tag_caption: línea de la descripción (máx. 18 palabras) para etiquetar a la compañera de oposición con un mini reto.
Sin datos del temario, sin desvelar la respuesta, sin promesas, nada que ridiculice a nadie.
Devuelve JSON: {{"reto_line": str, "share_line": str, "tag_caption": str}}""", 0.9)
        out = {}
        if _w(res.get("reto_line"), 2, 6): out["reto_line"] = _clean(res["reto_line"])
        if _w(res.get("share_line"), 2, 7): out["share_line"] = _clean(res["share_line"])
        if _w(res.get("tag_caption"), 4, 20): out["tag_caption"] = res["tag_caption"].strip()
        return out
    except Exception as e:
        print("estudio viralidad omitida:", str(e)[:120], flush=True)
        return {}


# ------------------------------------------------------------------ 8. embudo a la app (datos reales)
def app_counts(items):
    import questions as QB
    topic = items[0]["topic"]
    nq = sum(1 for q in QB.load() if q["topic"] == topic)
    try:
        nf = sum(1 for f in json.load(open(QB.FICHAS)) if f["topic"] == topic)
    except Exception:
        nf = 0
    return {"tema": items[0]["tema"], "preguntas_tema": nq, "fichas_tema": nf}


def embudo(fmt, items, S):
    c = app_counts(items)
    try:
        res = _ask(f"""{brief('embudo_app')}
DATOS REALES de la app (usa solo estos números): tema "{c['tema']}": {c['preguntas_tema']} preguntas tipo test y
{c['fichas_tema']} flashcards. En total {M.PREGUNTAS_FRASE}, simulacros y estadísticas. Se practica gratis en apruebatcae.com.
Escribe:
- cta_line: cierre hablado (10-22 palabras) que invite a practicar ESTE tema en la app; nombra "apruebatcae.com".
- app_caption: línea de la descripción (máx. 22 palabras) con el número real de preguntas o fichas de este tema.
Devuelve JSON: {{"cta_line": str, "app_caption": str}}""", 0.7)
        out = {}
        allowed = {str(c["preguntas_tema"]), str(c["fichas_tema"]), M.PREGUNTAS, M.PREGUNTAS.replace(".", "")}
        for k, lo, hi in (("cta_line", 8, 24), ("app_caption", 5, 24)):
            v = _w(res.get(k), lo, hi)
            nums = re.findall(r"\d[\d.]*", v or "")
            if v and all(n in allowed for n in nums) and "apruebatcae" in (v.lower().replace(" ", "") if k == "cta_line" else "apruebatcae"):
                out[k] = v
        return out
    except Exception as e:
        print("estudio embudo omitido:", str(e)[:120], flush=True)
        return {}


# ------------------------------------------------------------------ 9. SEO
def seo(fmt, items, S):
    try:
        res = _ask(f"""{brief('seo')}
Formato {fmt}. {_desc(items)} Gancho: "{S.get('screen_hook')}".
Escribe:
- yt_title: título de YouTube Shorts (máx. 80 caracteres) con lo que buscaría un opositor (p. ej. "test TCAE oposiciones",
  el tema), atractivo y sin clickbait engañoso, sin revelar la respuesta.
- seo_line: una frase natural para la descripción (máx. 20 palabras) con 2-3 búsquedas típicas (oposiciones TCAE 2026,
  test auxiliar de enfermería, el tema...), sin mencionar ninguna comunidad autónoma.
Devuelve JSON: {{"yt_title": str, "seo_line": str}}""", 0.6)
        out = {}
        t = (res.get("yt_title") or "").strip()
        if 10 <= len(t) <= 90 and "#" not in t: out["yt_title"] = t
        if _w(res.get("seo_line"), 5, 22): out["seo_line"] = res["seo_line"].strip()
        return out
    except Exception as e:
        print("estudio seo omitido:", str(e)[:120], flush=True)
        return {}


# ------------------------------------------------------------------ 10. ritmo
def ritmo(fmt, S):
    perf = []
    try:
        for r in json.load(open(os.path.join(HERE, "performance.json"))).values():
            if r.get("ig_reels_avg_watch_time"):
                perf.append(f"{r.get('formato')}/{r.get('estilo')}: visionado medio {r['ig_reels_avg_watch_time']} ms, "
                            f"velocidad voz {r.get('voice_speed')}, música {r.get('music')}")
    except Exception:
        pass
    try:
        res = _ask(f"""{brief('ritmo')}
Formato {fmt}. Datos de retención reales: {'; '.join(perf[-20:]) or 'aún no hay'}.
Elige voice_speed (entre 1.00 y 1.12; 1.06 es normal) y music ("calma", "normal" o "energica") para que el público se quede
hasta la solución sin agobiarse. Devuelve JSON: {{"voice_speed": number, "music": str, "why": str}}""", 0.4)
        out = {}
        try:
            out["voice_speed"] = round(min(1.12, max(1.0, float(res.get("voice_speed")))), 2)
        except Exception:
            pass
        if res.get("music") in ("calma", "normal", "energica"):
            out["music"] = res["music"]
        return out
    except Exception as e:
        print("estudio ritmo omitido:", str(e)[:120], flush=True)
        return {}


# ------------------------------------------------------------------ pasada de textos (antes del verificador)
TEXT_KEYS = ("escena", "save_line", "save_caption", "reto_line", "share_line", "tag_caption", "cta_line", "app_caption",
             "seo_line", "yt_title", "follow_line", "follow_caption")


def text_pass(fmt, items, S, series_info=None):
    """Agentes 4-9 en paralelo. Devuelve S ampliado (todo esto lo revisa después el verificador)."""
    from concurrent.futures import ThreadPoolExecutor
    jobs = {"memoria": lambda: memoria(fmt, items, S), "viralidad": lambda: viralidad(fmt, items, S),
            "seo": lambda: seo(fmt, items, S), "ritmo": lambda: ritmo(fmt, S)}
    if fmt != "flashcards_express":
        jobs["embudo"] = lambda: embudo(fmt, items, S)
    if fmt == "caso_practico":
        jobs["narradora"] = lambda: narradora(items, S)
    if series_info:
        jobs["series"] = lambda: series_lines(series_info, S)
    out = dict(S)
    with ThreadPoolExecutor(6) as ex:
        futs = {k: ex.submit(f) for k, f in jobs.items()}
        for k, f in futs.items():
            try:
                res = f.result(timeout=240) or {}
                out.update(res)
                _log(k, {"campos": list(res)})
            except Exception as e:
                print(f"estudio {k} omitido:", str(e)[:120], flush=True)
    if series_info:
        out["series"] = series_info["series"]
        out.setdefault("follow_line", f"Mañana: {series_info['manana']}. ¡Síguenos!")
    return out


# ------------------------------------------------------------------ aprendizaje diario
def daily_learning(force=False):
    os.makedirs(NB_DIR, exist_ok=True)
    today = str(datetime.date.today())
    if not force and os.path.exists(STAMP) and open(STAMP).read().strip() == today:
        return "estudio: cuadernos ya actualizados hoy"
    try:
        perf = json.load(open(os.path.join(HERE, "performance.json")))
    except Exception:
        perf = {}
    rows = [r for r in perf.values() if r.get("hook")]
    if len(rows) < 3:
        return "estudio: esperando resultados (hacen falta 3+ reels medidos)"
    import strategy
    rows.sort(key=lambda r: -(strategy.reward(r) or 0))
    table = "\n".join(
        f"- score {strategy.reward(r) or 0:.2f} | views {r.get('views')} | guardados {r.get('saved')} | compartidos {r.get('shares')} | "
        f"comentarios {r.get('comments')} | visitas perfil {r.get('profile_visits')} | seguidores {r.get('follows')} | "
        f"visionado {r.get('ig_reels_avg_watch_time')} ms | {r.get('formato')} | estilo {r.get('estilo')} | serie {r.get('series')} | "
        f"imagen {'sí' if r.get('imagen') else 'no'} | gancho: {r.get('hook')}" for r in rows[:30])
    imgs = []
    try:
        imgs = [json.loads(l) for l in open(IMG_LOG)][-15:]
    except Exception:
        pass
    old = {n: notebook(n) for n in NAMES}
    try:
        res = _ask(f"""Coordinas el estudio creativo (10 agentes) de los reels de Aprueba TCAE. Roles:
{json.dumps(ROLES, indent=1, ensure_ascii=False)}

RESULTADOS REALES (mejores primero):
{table}

ÚLTIMAS IMÁGENES (idea, aprobada o no, problemas): {json.dumps(imgs, ensure_ascii=False)[:2500]}

CUADERNOS ACTUALES: {json.dumps(old, ensure_ascii=False)[:6000]}

Reescribe el cuaderno de cada agente (máx. 90 palabras, viñetas: Seguir haciendo / Dejar de hacer / Probar), concreto y
basado en estos datos. Si los datos no bastan, dilo. Devuelve JSON con una clave por agente: {json.dumps(NAMES)}""", 0.4)
    except Exception as e:
        return f"estudio: aprendizaje omitido ({str(e)[:120]})"
    n = 0
    for name in NAMES:
        txt = (res.get(name) or "").strip()
        if 20 <= len(txt) <= 1200:
            open(os.path.join(NB_DIR, f"estudio_{name}.md"), "w").write(f"# Cuaderno de {name} ({today})\n\n{txt}\n")
            n += 1
    open(STAMP, "w").write(today)
    return f"estudio: {n}/10 cuadernos actualizados"
