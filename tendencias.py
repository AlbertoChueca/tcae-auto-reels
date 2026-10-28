"""Agente 9 · CAZATENDENCIAS: busca cada mañana actualidad buena y real para el contenido de Aprueba TCAE.

Una vez al día (lo llama el primer reel del día) busca en Google, con la búsqueda integrada de Gemini, lo que hoy
interesa a quien prepara las oposiciones de TCAE en España:
  - convocatorias, plazos y exámenes de TCAE (BOE y boletines autonómicos),
  - campañas sanitarias en marcha (vacunación, gripe, calor...), días mundiales de esta semana,
  - noticias sanitarias que afectan al trabajo de una TCAE.
Cada hallazgo lleva su fuente (URL) y se relaciona con temas del temario de la app.

Qué cambia con él:
  1. Los reels y la chuleta eligen antes preguntas de los temas de actualidad (sin dejar de verificarlas).
  2. El guionista puede usar UN dato de actualidad en el gancho o la descripción si encaja con la pregunta; ese dato
     entra como material del verificador con su fuente (si no, se rechaza como cualquier dato inventado).
  3. Escribe su cuaderno (agents/cazatendencias.md), que leen los agentes de gancho y crecimiento.

Guarda tendencias.json. Si la búsqueda falla, el día sigue igual que siempre.
    python tendencias.py [--forzar]
"""
import datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tendencias.json")
NB = os.path.join(HERE, "agents", "cazatendencias.md")
MAX_AGE_DAYS = 2


def load():
    try:
        return json.load(open(OUT))
    except Exception:
        return {}


def current():
    """Hallazgos de hoy o de ayer (si no hay, lista vacía)."""
    d = load()
    try:
        age = (datetime.date.today() - datetime.date.fromisoformat(d.get("fecha", "2000-01-01"))).days
    except Exception:
        return []
    return d.get("items", []) if age < MAX_AGE_DAYS else []


def topics_hot():
    """Temas del banco que están de actualidad (para elegir antes sus preguntas)."""
    out = []
    for it in current():
        out += [t for t in it.get("temas", []) if t not in out]
    return out


def for_topic(topic):
    """Hallazgos relacionados con un tema concreto (para el guionista y el verificador)."""
    return [it for it in current() if topic in (it.get("temas") or [])]


def material_lines(topic):
    return [f"- ACTUALIDAD ({it['fecha']}, fuente {it['url']}): {it['dato']}" for it in for_topic(topic)]


def _topic_catalog():
    import questions as QB
    seen = {}
    for q in QB.load():
        if q["topic"] not in seen and not QB.regional(q):
            seen[q["topic"]] = q["tema"]
    return seen


def _search(prompt):
    """Gemini con búsqueda de Google. Devuelve (texto, nº de fuentes consultadas)."""
    import gemini
    body = {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.3}}
    last = None
    names = list(gemini.TEXT_MODELS) + sorted([m for m in gemini.available() if "flash" in m and gemini._text_only(m)],
                                              key=gemini._rank)
    for model in dict.fromkeys(names):
        try:
            j = gemini.post(model, body)
            cand = j["candidates"][0]
            txt = "".join(p.get("text", "") for p in cand["content"]["parts"])
            gm = cand.get("groundingMetadata") or cand.get("grounding_metadata") or {}
            n = len(gm.get("groundingChunks") or gm.get("grounding_chunks") or [])
            q = len(gm.get("webSearchQueries") or gm.get("web_search_queries") or [])
            print(f"cazatendencias: modelo {model} · {q} búsquedas · {n} fuentes · claves {sorted(gm)}", flush=True)
            return txt, n or q                    # búsqueda real hecha (fuentes o, al menos, consultas a Google)
        except Exception as e:
            last = e
    raise last or RuntimeError("sin modelo con búsqueda")


def run(force=False):
    today = datetime.date.today()
    d = load()
    if not force and d.get("fecha") == str(today):
        return f"cazatendencias: ya buscó hoy ({len(d.get('items', []))} hallazgos)"
    if not os.environ.get("GEMINI_API_KEY"):
        return "cazatendencias: sin GEMINI_API_KEY"
    cat = _topic_catalog()
    try:
        txt, n_src = _search(f"""Hoy es {today:%d/%m/%Y}. Eres la CAZATENDENCIAS de Aprueba TCAE, una cuenta de Instagram y TikTok
para opositores de TCAE (Técnico en Cuidados Auxiliares de Enfermería) de toda España.
Busca en internet y elige de 3 a 6 hallazgos ACTUALES (de los últimos 14 días o de los próximos 14) que hoy interesen a
una opositora de TCAE:
- convocatorias, plazos de solicitud o fechas de examen de TCAE (BOE, boletines autonómicos, servicios de salud);
- campañas sanitarias en marcha en España (vacunación de gripe, COVID, VRS, olas de calor o frío...);
- días mundiales o nacionales de salud de esta semana;
- noticias sanitarias que cambian el día a día de una TCAE.
Para cada hallazgo, relaciónalo con 1-3 temas del temario de esta lista (usa SOLO estos ids):
{json.dumps(cat, ensure_ascii=False)}
Reglas: solo hechos que hayas comprobado en una fuente fiable (organismo oficial, boletín, medio serio); el "dato" es una
frase corta y literal de lo que dice la fuente, sin exagerar ni añadir cifras; nada de bulos ni rumores.
Responde SOLO con JSON, sin texto alrededor:
{{"items": [{{"titulo": str, "dato": str (máx. 30 palabras), "url": str, "fecha": "AAAA-MM-DD", "temas": [str],
"gancho": str (máx. 10 palabras, idea para el gancho de un reel), "por_que": str (máx. 20 palabras)}}],
"cuaderno": str (máx. 120 palabras: qué está de actualidad esta semana y cómo aprovecharlo en reels, en viñetas)}}""")
    except Exception as e:
        return f"cazatendencias: búsqueda no disponible ({str(e)[:150]})"
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        res = json.loads(m.group(0)) if m else {}
    except Exception:
        res = {}
    items = []
    for it in res.get("items") or []:
        try:
            f = datetime.date.fromisoformat(str(it.get("fecha"))[:10])
        except Exception:
            continue
        temas = [t for t in (it.get("temas") or []) if t in cat][:3]
        url = str(it.get("url") or "")
        dato = re.sub(r"\s+", " ", str(it.get("dato") or "")).strip()
        if (abs((f - today).days) <= 21 and temas and url.startswith("http") and 5 <= len(dato.split()) <= 40
                and n_src > 0):                             # sin búsqueda real (0 fuentes) no se acepta nada
            items.append({"titulo": str(it.get("titulo", ""))[:120], "dato": dato, "url": url, "fecha": str(f),
                          "temas": temas, "gancho": str(it.get("gancho", ""))[:80], "por_que": str(it.get("por_que", ""))[:160]})
    json.dump({"fecha": str(today), "fuentes_consultadas": n_src, "items": items}, open(OUT, "w"), ensure_ascii=False, indent=1)
    nb = str(res.get("cuaderno") or "").strip()
    os.makedirs(os.path.dirname(NB), exist_ok=True)
    lines = [f"# Cuaderno de cazatendencias ({today})", "", nb[:1500] if nb else "(sin resumen)", "", "## Hallazgos"]
    lines += [f"- **{it['titulo']}** ({it['fecha']}) · temas: {', '.join(it['temas'])} · {it['dato']} · [fuente]({it['url']})"
              for it in items] or ["- Ninguno fiable hoy."]
    open(NB, "w").write("\n".join(lines) + "\n")
    return f"cazatendencias: {len(items)} hallazgos de actualidad ({n_src} fuentes consultadas)"


if __name__ == "__main__":
    print(run("--forzar" in sys.argv))
