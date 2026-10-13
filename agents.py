"""La sala de guionistas: 5 agentes especialistas que pulen una parte de cada reel y llevan su propio cuaderno de
lecciones, reescrito cada día a partir de los resultados reales de Instagram y de lo que dice la audiencia.

  1. gancho       - los 2 primeros segundos (texto grande, primera frase hablada, primera línea de la descripción).
  2. guion        - claridad didáctica: explicación breve, trampa, truco, mito; que se entienda a la primera.
  3. diseno       - diseño de los fotogramas: legibilidad en el móvil, zona segura, tamaño de subtítulos.
  4. crecimiento  - descripción, invitación a comentar/guardar/compartir, líneas finales -> seguidores y visitas a la web.
  5. comunidad    - lee los comentarios (sin guardar nombres) y cuenta al resto qué preguntan, qué fallan, qué piden.

Los cuadernos viven en agents/<nombre>.md (se guardan en el repo y se leen en GitHub). Son cortos y se reescriben (no se
acumulan) para que sigan centrados. Todo es opcional: si un agente falla, el reel sigue adelante.
El VERIFICADOR (verifier.py) no está en esta sala a propósito: no aprende de las métricas, solo de la fuente.
"""
import datetime, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
NB_DIR = os.path.join(HERE, "agents")
STAMP = os.path.join(NB_DIR, "last_update.txt")
FACTS = os.path.join(HERE, "assets", "app", "facts.md")

ROLES = {
    "gancho": "ESPECIALISTA EN GANCHOS. Eres responsable de los 2 primeros segundos: el texto grande en pantalla, la primera "
              "frase hablada y la primera línea de la descripción. Tu único objetivo: que quien prepara la oposición de TCAE "
              "deje de hacer scroll y se quede a responder.",
    "guion": "EDITORA DIDÁCTICA. Eres responsable de que cada explicación, trampa, truco o mito se entienda a la primera, "
             "sea breve y ayude de verdad a acertar en el examen, sin añadir datos que no estén en el material.",
    "diseno": "DIRECTORA DE ARTE. Eres responsable de la legibilidad en el móvil, la jerarquía visual, la zona segura y el "
              "acabado profesional y limpio de la marca Aprueba TCAE (teal, ámbar, tarjetas blancas).",
    "crecimiento": "RESPONSABLE DE CRECIMIENTO. Eres responsable de la descripción, la invitación a comentar, guardar y "
                   "compartir, y las líneas finales, para ganar seguidores y visitas a apruebatcae.com.",
    "comunidad": "ANALISTA DE COMUNIDAD. Lees los comentarios de la audiencia y los conviertes en ideas concretas para el "
                 "equipo (qué les gusta, qué preguntan, qué fallan, qué temas piden, si las preguntas les parecen fáciles o difíciles).",
}
NAMES = list(ROLES)


def _ask(prompt, temperature=0.6):
    import gemini
    return gemini.ask(prompt, temperature)


def notebook(name):
    try:
        return open(os.path.join(NB_DIR, f"{name}.md")).read().strip()[:1500]
    except Exception:
        return ""


def facts():
    try:
        return "\n".join(l.strip() for l in open(FACTS) if l.strip().startswith("-"))
    except Exception:
        return ""


def _brief(name):
    nb, com = notebook(name), notebook("comunidad")
    out = f"Eres la persona {ROLES[name]}"
    if nb:
        out += f"\nTU CUADERNO (lecciones de nuestros resultados reales, síguelas):\n{nb}"
    if name != "comunidad" and com:
        out += f"\nLO QUE DICE LA AUDIENCIA (analista de comunidad):\n{com}"
    return out


def _words(v, n):
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    return v if 1 <= len(v.split()) <= n else None


def _log(kind, data):
    try:
        import reviewer
        reviewer._log(kind, data)
    except Exception:
        pass


# ------------------------------------------------------------------ pasadas por reel
def growth_lines(S, fmt):
    """Crecimiento (antes del render): líneas de seguir y compartir de la tarjeta final."""
    try:
        res = _ask(f"""{_brief('crecimiento')}
Reel de hoy: formato {fmt}, gancho "{S.get('screen_hook')}".
Escribe las líneas de la tarjeta final: follow_line (máx. 6 palabras, invita a seguir la cuenta para la pregunta de mañana)
y share_line (máx. 7 palabras, invita a enviarlo a alguien que oposita). Español de España, sin emojis, sin promesas.
Devuelve JSON: {{"follow_line": str, "share_line": str}}""", 0.7)
        out = {}
        for k, n in (("follow_line", 6), ("share_line", 7)):
            if _words(res.get(k), n):
                out[k] = re.sub(r"[^\w\s¿?¡!,.:'-]", "", res[k]).strip()
        return out
    except Exception as e:
        print("agente crecimiento (líneas) omitido:", str(e)[:150], flush=True)
        return {}


def growth_caption(caption, S, review):
    """Crecimiento (después del control de calidad): descripción final. Mantiene pregunta, web y 3-5 hashtags."""
    try:
        res = _ask(f"""{_brief('crecimiento')}
Descripción actual:
{caption}

Notas del control de calidad del vídeo: {json.dumps(review, ensure_ascii=False)[:600]}
HECHOS CIERTOS de la app (no afirmes nada más sobre ella):
{facts()}
Reescribe la descripción para conseguir más guardados, comentarios, compartidos y visitas al perfil de opositores a TCAE.
Reglas: español de España; primera línea gancho (máx. 12 palabras, máx. 1 emoji); MANTÉN LITERALES la pregunta y sus
opciones (o la afirmación) tal y como están; una línea que invite a comentar la respuesta; una que invite a guardar el
post para repasar; menciona apruebatcae.com y "link en la bio"; termina con 3-5 hashtags de esta lista:
#TCAE #oposicionesTCAE #auxiliardeenfermeria #oposiciones #SALUD #Aragon. Máx. 1.500 caracteres. Sin estadísticas ni promesas.
Devuelve JSON: {{"caption": str, "why": str}}""", 0.6)
        cap = (res.get("caption") or "").strip()
        tags = re.findall(r"#\w+", cap)
        allowed = {"#TCAE", "#oposicionesTCAE", "#auxiliardeenfermeria", "#oposiciones", "#SALUD", "#Aragon"}
        core = [l for l in caption.split("\n") if re.match(r"^[ABCD]\) ", l)]          # las opciones deben seguir intactas
        if (80 <= len(cap) <= 1800 and 3 <= len(tags) <= 5 and set(tags) <= allowed and "apruebatcae" in cap.lower()
                and "bio" in cap.lower() and all(l in cap for l in core) and all(p in caption for p in re.findall(r"\d+ ?%", cap))):
            _log("agent_growth", {"why": res.get("why")})
            print("agente crecimiento: descripción reescrita", flush=True)
            return cap
        print("agente crecimiento: descripción original (la nueva no cumplía las reglas)", flush=True)
    except Exception as e:
        print("agente crecimiento omitido:", str(e)[:150], flush=True)
    return caption


# ------------------------------------------------------------------ aprendizaje diario
def daily_learning(force=False):
    """Una vez al día: cada agente reescribe su cuaderno con los resultados y los comentarios. Devuelve una línea de estado."""
    os.makedirs(NB_DIR, exist_ok=True)
    today = str(datetime.date.today())
    if not force and os.path.exists(STAMP) and open(STAMP).read().strip() == today:
        return "agentes: cuadernos ya actualizados hoy"
    try:
        perf = json.load(open(os.path.join(HERE, "performance.json")))
    except Exception:
        perf = {}
    rows = [r for r in perf.values() if r.get("hook")]
    if len(rows) < 3:
        return "agentes: esperando resultados (hacen falta 3+ reels medidos)"
    import strategy
    rows.sort(key=lambda r: -(strategy.reward(r) or 0))
    table = "\n".join(
        f"- score {strategy.reward(r) or 0:.2f} | views {r.get('views')} | guardados {r.get('saved')} | compartidos {r.get('shares')} | "
        f"comentarios {r.get('comments') or r.get('comments_count')} | visitas perfil {r.get('profile_visits')} | "
        f"visionado {r.get('ig_reels_avg_watch_time')} ms | formato {r.get('formato')} | tema {r.get('temas')} | gancho: {r.get('hook')} | "
        + ", ".join(f"{k}={strategy.short(v)}" for k, v in (r.get("arms") or {}).items())
        for r in rows[:30])
    comments = []
    try:
        import insights
        comments = insights.recent_comments()
    except Exception as e:
        print("agentes: comentarios no disponibles:", str(e)[:120], flush=True)
    com_txt = "\n".join(f"- [{c.get('story') or 'reel'}] {c['text'][:160]}" for c in comments[:150]) or "(aún no hay comentarios)"
    old = {n: notebook(n) for n in NAMES}
    try:
        res = _ask(f"""Coordinas una sala de 5 agentes especialistas para los reels de Aprueba TCAE (tests para la oposición de
TCAE del SALUD de Aragón; público adulto). Roles:
{json.dumps(ROLES, indent=1, ensure_ascii=False)}

RESULTADOS REALES EN INSTAGRAM (mejores primero; score = views + guardados, compartidos, comentarios y visitas al perfil ponderados + visionado):
{table}

COMENTARIOS RECIENTES (anónimos):
{com_txt}

CUADERNOS ACTUALES:
{json.dumps(old, ensure_ascii=False, indent=1)}

Reescribe el cuaderno de cada agente para mañana. Cada cuaderno: máx. 120 palabras, viñetas, concreto y basado en NUESTROS
datos: "Seguir haciendo", "Dejar de hacer", "Probar". Conserva solo lecciones que los datos sigan respaldando. El de
comunidad resume lo que dice la audiencia (sin nombres ni datos personales). Si hay pocos datos, dilo.
Devuelve JSON: {{"gancho": str, "guion": str, "diseno": str, "crecimiento": str, "comunidad": str}}""", 0.4)
    except Exception as e:
        return f"agentes: aprendizaje omitido ({str(e)[:120]})"
    n = 0
    for name in NAMES:
        txt = (res.get(name) or "").strip()
        if 20 <= len(txt) <= 1500:
            open(os.path.join(NB_DIR, f"{name}.md"), "w").write(f"# Cuaderno de {name} ({today})\n\n{txt}\n")
            n += 1
    open(STAMP, "w").write(today)
    return f"agentes: {n}/5 cuadernos actualizados con {len(rows)} reels y {len(comments)} comentarios"
