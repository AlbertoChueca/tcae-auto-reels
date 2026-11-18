"""Revisión semanal del piloto automático: mide si la cuenta crece y pule sola el contenido de la semana siguiente.

Se ejecuta una vez por semana, el lunes (workflow "Revisión semanal"; si GitHub no entrega su cron, lo lanza
despertar.py desde cualquier aviso de reels o chuletas; también a mano). Hace cuatro cosas:

 1. MIDE. Junta los resultados de Instagram, TikTok y YouTube (reels, vídeos explicados y chuletas) y los seguidores,
    y compara la semana que acaba con la anterior: publicaciones, visualizaciones, interacciones, comentarios,
    guardados y seguidores por red. Lo guarda en crecimiento.json (una foto por semana, para comparar igual con igual).
 2. DECIDE (cambios automáticos, acotados y reversibles):
      - pausa una semana los 1-2 formatos y estilos de reel que rinden claramente peor que la media de su red (con
        datos suficientes). Un formato o estilo nunca está pausado más de 2 semanas seguidas: a la tercera vuelve a
        probarse. Si el formato pausado era la serie fija de un día, ese día elige formato el piloto automático;
      - añade hasta 2 estilos de gancho nuevos y retira el que pierde con claridad.
 3. APRENDE. Un agente estratega (IA) lee todas las tablas y escribe los playbooks que usan guionistas y revisores:
    playbook.md (reels), playbook_chuletas.md y playbook_explicados.md.
 4. INFORMA. Escribe informe_semanal.md y abre una incidencia en GitHub "Informe semanal" asignada al dueño (llega por
    correo) con las cifras, lo que ha cambiado y las sugerencias que necesitan su decisión (el piloto no toca solo ni la
    proporción de retos, ni el nº de explicados, ni los horarios).

    python semanal.py [--forzar]
"""
import datetime, json, math, os, statistics, sys

import strategy

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "crecimiento.json")
REPORT = os.path.join(HERE, "informe_semanal.md")
PB_CHULETAS = os.path.join(HERE, "playbook_chuletas.md")
PB_EXPLICADOS = os.path.join(HERE, "playbook_explicados.md")
REDES = ("instagram", "tiktok", "youtube")
NOMBRE = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube"}
MIN_N, UMBRAL = 6, -0.45                        # para pausar: al menos 6 vídeos medidos y media 0,45 desviaciones bajo lo normal


def _load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def week_key(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


# ------------------------------------------------------------------ 1. datos
def posts():
    """Todas las publicaciones medidas, en un solo formato: reels y explicados (con sus palancas) y chuletas."""
    out = []
    chul = _load(os.path.join(HERE, "chuletas.json"), [])
    by_ig = {str((c.get("destinos") or {}).get("instagram") or "").split("?")[0].rstrip("/"): c for c in chul}
    logs = {}
    try:
        for line in open(os.path.join(HERE, "log.jsonl")):
            e = json.loads(line)
            for k in ("media_id",):
                if e.get(k):
                    logs[e[k]] = e
            for k in ("tiktok_video", "youtube_short"):
                v = str((e.get("publicado") or {}).get(k) or "")
                if v and not v.startswith("error"):
                    logs[v] = e
    except Exception:
        pass

    def reto(e):
        return bool(e.get("reto")) if "reto" in e else bool(e.get("soluciones"))
    for pid, r in _load(os.path.join(HERE, "performance.json"), {}).items():
        if not isinstance(r, dict) or r.get("views") is None and r.get("reach") is None:
            continue
        base = {"red": "instagram", "date": r.get("date"), "views": r.get("views") or r.get("reach") or 0, "likes": r.get("likes") or 0,
                "comments": r.get("comments") or 0, "shares": r.get("shares") or 0, "saved": r.get("saved") or 0,
                "watch": (r.get("ig_reels_avg_watch_time") or 0) / 1000 or None, "profile_visits": r.get("profile_visits") or 0,
                "follows": r.get("follows") or 0, "url": r.get("permalink")}
        if r.get("type") == "REELS":
            e = logs.get(pid) or {}
            out.append({**base, "tipo": "explicado" if r.get("formato") == "explicado" else "reel", "formato": r.get("formato"),
                        "estilo": r.get("estilo"), "hook": r.get("hook"), "arms": r.get("arms"), "slot": r.get("slot"),
                        "reto": reto(e) if e else None, "tema": (r.get("temas") or [None])[0]})
        else:
            c = by_ig.get(str(r.get("permalink") or "").split("?")[0].rstrip("/"))
            if c:
                out.append({**base, "tipo": "chuleta", "formato": "chuleta", "tema": c.get("tema"), "hook": c.get("subtema"),
                            "slot": str(c.get("slot"))})
    for pid, r in _load(os.path.join(HERE, "performance_tiktok.json"), {}).items():
        if not isinstance(r, dict) or not r.get("views"):
            continue
        e = logs.get(pid) or {}
        tipo = "chuleta" if r.get("formato") == "chuleta" else ("explicado" if r.get("formato") == "explicado" else "reel")
        out.append({"red": r.get("red") or "tiktok", "date": r.get("date"), "views": r.get("views") or 0, "likes": r.get("likes") or 0,
                    "comments": r.get("comments") or 0, "shares": r.get("shares") or 0, "saved": r.get("saved") or 0, "watch": None,
                    "tipo": tipo, "formato": r.get("formato"), "estilo": r.get("estilo"), "hook": r.get("hook"), "arms": r.get("arms"),
                    "slot": r.get("slot"), "reto": reto(e) if e else None, "tema": r.get("tema") or (e.get("temas") or [None])[0],
                    "url": r.get("url")})
    return [p for p in out if p.get("date")]


def followers():
    """Seguidores actuales por red (lo que cada API deje leer)."""
    import requests
    out, diag = {}, []
    tok = os.environ.get("IG_TOKEN")
    if tok:
        try:
            from publish_ig import whoami, GRAPH
            uid = whoami(tok)["user_id"]
            j = requests.get(f"{GRAPH}/{uid}", params={"fields": "followers_count,media_count", "access_token": tok}, timeout=30).json()
            if j.get("followers_count") is not None:
                out["instagram"] = int(j["followers_count"])
            else:
                diag.append(f"instagram: {str(j)[:120]}")
        except Exception as e:
            diag.append(f"instagram: {str(e)[:120]}")
    if os.environ.get("ZERNIO_API_KEY"):
        try:
            import publish_zernio as Z
            data = requests.get(f"{Z.API}/accounts", headers=Z._h(), timeout=40).json()
            items = data.get("accounts", data if isinstance(data, list) else data.get("data", []))
            for a in items:
                p = (a.get("platform") or "").lower()
                n = next((a.get(k) for k in ("followerCount", "followersCount", "followers", "follower_count") if isinstance(a.get(k), (int, float))), None)
                if n is None and isinstance(a.get("metadata"), dict):
                    n = next((a["metadata"].get(k) for k in ("followerCount", "followersCount", "followers", "follower_count", "subscriberCount")
                              if isinstance(a["metadata"].get(k), (int, float))), None)
                if p in ("tiktok", "youtube") and n is not None:
                    out[p] = int(n)
                elif p in ("tiktok", "youtube"):
                    diag.append(f"{p}: sin seguidores en /accounts (campos {sorted(a)[:18]})")
            if "tiktok" not in out and Z.accounts().get("tiktok"):
                r = requests.get(f"{Z.API}/analytics/tiktok/account-insights", headers=Z._h(), timeout=40,
                                 params={"accountId": Z.accounts()["tiktok"], "metrics": "follower_count", "metricType": "total_value"})
                if r.status_code == 200:
                    v = ((r.json().get("metrics") or {}).get("follower_count") or {}).get("total")
                    if isinstance(v, (int, float)):
                        out["tiktok"] = int(v)
                else:
                    diag.append(f"tiktok insights: HTTP {r.status_code} {r.text[:100]}")
        except Exception as e:
            diag.append(f"zernio: {str(e)[:120]}")
    return out, diag


def kpis(P, start, end):
    """Cifras por red de las publicaciones con fecha en [start, end)."""
    out = {}
    for red in REDES:
        rows = [p for p in P if p["red"] == red and str(start) <= p["date"] < str(end)]
        if not rows:
            continue
        v = [p["views"] for p in rows]
        out[red] = {"publicaciones": len(rows), "views": int(sum(v)), "mediana_views": int(statistics.median(v)),
                    "interacciones": int(sum(p["likes"] + p["comments"] + p["shares"] + p["saved"] for p in rows)),
                    "comentarios": int(sum(p["comments"] for p in rows)), "guardados": int(sum(p["saved"] for p in rows)),
                    "compartidos": int(sum(p["shares"] for p in rows))}
    return out


def table(P, key, red, tipo="reel", min_n=2):
    """[(opción, n, mediana de views, comentarios, guardados, compartidos)] de una palanca en una red."""
    g = {}
    for p in P:
        if p["red"] == red and p["tipo"] == tipo:
            k = key(p)
            if k is not None:
                g.setdefault(k, []).append(p)
    rows = [(k, len(v), statistics.median(x["views"] for x in v), statistics.mean(x["comments"] for x in v),
             statistics.mean(x["saved"] for x in v), statistics.mean(x["shares"] for x in v)) for k, v in g.items() if len(v) >= min_n]
    return sorted(rows, key=lambda r: -r[2])


def _arm(p, lever):
    a = (p.get("arms") or {}).get(lever)
    return strategy.short(a) if a else None


# ------------------------------------------------------------------ 2. decisiones automáticas
def pauses(prev_weeks):
    """Formatos y estilos a pausar esta semana: {palanca: [opción]} + explicación. Solo se pausa lo que rinde mal con
    datos suficientes Y en todas las redes donde tiene datos (lo que va bien en TikTok no se pausa por ir mal en Instagram)."""
    res = strategy._results()
    out, why = {}, []
    for lever in ("formato", "estilo"):
        opts = strategy.arms().get(lever, [])
        by = {}
        for arms_, z, r in res:
            a = arms_.get(lever)
            if a in opts:
                by.setdefault(a, []).append((r.get("red") or "instagram", z))
        bad = []
        for a, zs in by.items():
            m = sum(z for _, z in zs) / len(zs)
            per = {}
            for red, z in zs:
                per.setdefault(red, []).append(z)
            everywhere = all(sum(v) / len(v) < 0 for v in per.values() if len(v) >= 3)
            if len(zs) >= MIN_N and m <= UMBRAL and everywhere:
                bad.append((m, a, len(zs)))
        keep = []
        for m, a, k in sorted(bad):
            streak = sum(1 for w in prev_weeks[-2:] if a in ((w.get("pausados") or {}).get(lever) or []))
            if streak >= 2:
                why.append(f"{lever} `{a}` vuelve a prueba esta semana (llevaba 2 semanas en pausa)")
                continue
            if len(keep) < 2 and len(opts) - len(keep) > 4:
                keep.append(a); why.append(f"{lever} `{a}` en pausa esta semana: {k} vídeos, {m:+.2f} respecto a un vídeo normal de su red")
        out[lever] = keep
    return out, why


def config_text():
    cada = os.environ.get("RETO_CADA") or "5"
    dias = {"0": "lunes", "1": "martes", "2": "miércoles", "3": "jueves", "4": "viernes", "5": "sábado", "6": "domingo"}
    ex = ", ".join(dias.get(d.strip(), d) for d in (os.environ.get("EXPLICA_DIAS") or "1,3,6").split(",") if d.strip())
    return (f"- Publicaciones al día (hora de España): chuleta a las 8:00, reel a las 14:30, chuleta a las 18:00 y reel a las 21:30 "
            f"(14 chuletas y 14 reels por semana), en Instagram y TikTok; los reels también en YouTube.\n"
            f"- Reels tipo test: 1 de cada {cada} es un reto sin solución (la IA contesta en 24 h) y el resto enseña la solución "
            f"(desde el 18/11/2026; antes eran casi todos reto, así que los datos de 'con solución' son todavía pocos).\n"
            f"- Vídeos explicados (divulgación animada): {ex} a las 21:30, desde el 19/11/2026.\n"
            f"- Hasta el 18/11/2026 GitHub publicaba con 4-9 horas de retraso: los datos por hueco ('mediodia', 'noche', "
            f"'manana') NO corresponden a esas horas reales y no sirven para proponer horarios.")


def strategist(P, K, K_prev, old_pb, pausas_txt):
    """Agente estratega: playbooks + ganchos nuevos + resumen y sugerencias para el dueño."""
    import gemini, reviewer

    def tb(rows):
        return "\n".join(f"  - {k}: {n} vídeos · mediana {med:.0f} views · {c:.1f} coment. · {s:.1f} guard. · {sh:.1f} compart."
                         for k, n, med, c, s, sh in rows) or "  (sin datos suficientes)"
    blocks = []
    for red in ("tiktok", "instagram"):
        R = [p for p in P if p["red"] == red]
        if not R:
            continue
        top = sorted([p for p in R if p["tipo"] != "chuleta"], key=lambda p: -p["views"])
        blocks.append(f"""### {red.upper()} · reels
Por formato:\n{tb(table(P, lambda p: p.get('formato'), red))}
Por estilo visual:\n{tb(table(P, lambda p: p.get('estilo'), red))}
Por estilo de gancho:\n{tb(table(P, lambda p: _arm(p, 'hook_style'), red))}
Por bloque del temario:\n{tb(table(P, lambda p: _arm(p, 'bloque'), red))}
Por tiempo para pensar:\n{tb(table(P, lambda p: _arm(p, 'think_time'), red))}
Reto (sin solución) frente a solución en el vídeo:\n{tb(table(P, lambda p: None if p.get('reto') is None else ('reto' if p['reto'] else 'con solución'), red))}
Por hueco:\n{tb(table(P, lambda p: p.get('slot'), red))}
Mejores: """ + "; ".join(f"«{p.get('hook')}» ({p.get('formato')}, {p['views']} views, {p['comments']} com., {p['saved']} guard.)" for p in top[:6])
                      + "\nPeores: " + "; ".join(f"«{p.get('hook')}» ({p.get('formato')}, {p['views']} views)" for p in top[-4:])
                      + f"\n### {red.upper()} · vídeos explicados\n{tb(table(P, lambda p: p.get('tema'), red, 'explicado', 1))}"
                      + f"\n### {red.upper()} · chuletas (carruseles)\n" + "\n".join(
                          f"  - {p.get('tema')} · «{p.get('hook')}»: {p['views']} views, {p['saved']} guard., {p['shares']} compart."
                          for p in sorted([p for p in R if p["tipo"] == "chuleta"], key=lambda p: -(p["saved"] * 5 + p["views"] / 50))[:10]))
    comments = []
    try:
        import insights
        comments = insights.recent_comments(days=8)
    except Exception:
        pass
    A = strategy.arms()
    out = gemini.ask(f"""{reviewer.PRODUCER}
Ahora eres la ESTRATEGA del canal y haces la REVISIÓN SEMANAL. El objetivo es crecer semana a semana en TikTok e
Instagram (visualizaciones, comentarios, guardados, compartidos y seguidores) y llevar gente a apruebatcae.com.

CIFRAS DE LA SEMANA (y de la anterior):
{json.dumps({"esta_semana": K, "anterior": K_prev}, ensure_ascii=False, indent=1)}

RESULTADOS POR RED (todas las publicaciones medidas):
{chr(10).join(blocks)}

COMENTARIOS RECIENTES (anónimos): {json.dumps([c['text'][:120] for c in comments[:60]], ensure_ascii=False)}

CONFIGURACIÓN ACTUAL (lo que ya se hace; no lo propongas como novedad):
{config_text()}

CAMBIOS QUE YA HA DECIDIDO EL PILOTO AUTOMÁTICO ESTA SEMANA: {pausas_txt or 'ninguno'}
ESTILOS DE GANCHO ACTUALES: {json.dumps([strategy.short(x) for x in A['hook_style']], ensure_ascii=False)}
PLAYBOOK ANTERIOR:
{old_pb[:1500]}

Escribe, solo a partir de ESTOS datos (si una conclusión tiene pocos vídeos detrás, dilo; no inventes cifras):
- "playbook": lecciones para los REELS tipo test (máx. 220 palabras, viñetas): qué formatos, ganchos, bloques, tiempo para
  pensar y cierres funcionan en CADA red y qué evitar. Concreto y accionable para el guionista.
- "chuletas": lecciones para los carruseles (máx. 90 palabras): qué temas y titulares se guardan y comparten más.
- "explicados": lecciones para los vídeos explicados (máx. 90 palabras) o "" si aún no hay datos.
- "new_options": como mucho 2 estilos de gancho NUEVOS, "nombre: descripción de una línea", inspirados en lo que
  funciona y distintos de los actuales. Nunca estadísticas inventadas ni promesas de aprobar.
- "resumen": para el dueño de la cuenta (máx. 80 palabras, sin jerga): qué ha funcionado esta semana y qué no. De lo que
  viene, menciona SOLO lo que de verdad cambia (los cambios del piloto de arriba y que los guionistas siguen el playbook
  nuevo); no prometas cambios de horario, de volumen ni de proporciones, porque eso no lo decide el piloto.
- "sugerencias": de 0 a 3 propuestas que necesitan su decisión y que CAMBIEN la configuración actual (proporción de
  retos, nº de vídeos explicados o de chuletas, horarios), cada una con el dato concreto que la respalda y diciendo de
  qué valor a qué valor. Si los datos no justifican cambiar nada, devuelve una lista vacía.
Devuelve JSON: {{"playbook": str, "chuletas": str, "explicados": str, "new_options": [{{"lever": "hook_style", "option": str}}],
"resumen": str, "sugerencias": [str]}}""", 0.5)
    return out if isinstance(out, dict) else {}


def apply_hooks(out):
    """Añade los ganchos nuevos y retira, como mucho, uno que pierda con claridad (igual que antes, pero cada semana)."""
    A = strategy.arms(); changes = []
    for o in (out.get("new_options") or [])[:2]:
        opt = (o.get("option") or "").strip() if isinstance(o, dict) else ""
        if (o.get("lever") if isinstance(o, dict) else None) == "hook_style" and ":" in opt and 3 <= len(opt.split()) <= 30 \
                and strategy.short(opt) not in [strategy.short(x) for x in A["hook_style"]] and len(A["hook_style"]) < 10:
            A["hook_style"].append(opt); changes.append(f"gancho nuevo a prueba: `{strategy.short(opt)}`")
    st, mu, sd, _ = strategy.stats()
    ranked = [(a, n, m) for a, (n, m) in st.get("hook_style", {}).items() if m is not None]
    if len(A["hook_style"]) > 4 and len(ranked) >= 4:
        best = max(m for _, _, m in ranked); median = sorted(m for _, _, m in ranked)[len(ranked) // 2]
        losers = [(m, a) for a, n, m in ranked if n >= 8 and m < median and m < best - 2.5 * sd / math.sqrt(n) and a in A["hook_style"]]
        if losers:
            a = min(losers)[1]; A["hook_style"].remove(a); changes.append(f"gancho retirado: `{strategy.short(a)}`")
    return A, changes


# ------------------------------------------------------------------ 3. informe
def _delta(a, b):
    if b in (None, 0) or a is None:
        return ""
    d = (a - b) / b * 100
    return f" ({d:+.0f} %)"


def report(key, K, K_prev, fol, fol_prev, changes, res, P, monday):
    L = [f"# Informe semanal · {key}", "",
         f"_Semana del {monday - datetime.timedelta(days=7):%d/%m} al {monday - datetime.timedelta(days=1):%d/%m}. Entre paréntesis, "
         "el cambio frente a la semana anterior. Las cifras son las acumuladas hasta hoy: los últimos días aún suben._", ""]
    if res.get("resumen"):
        L += ["## En pocas palabras", "", str(res["resumen"]).strip(), ""]
    L += ["## Cifras", "", "| Red | Publicaciones | Visualizaciones | Mediana por publicación | Comentarios | Guardados | Compartidos | Seguidores |",
          "|---|---|---|---|---|---|---|---|"]
    for red in REDES:
        k, pv = K.get(red), K_prev.get(red) or {}
        if not k:
            continue
        f, fp = fol.get(red), (fol_prev or {}).get(red)
        seg = "-" if f is None else (f"{f:,}".replace(",", ".") + (f" ({f - fp:+d})" if isinstance(fp, int) else ""))
        L.append(f"| {NOMBRE[red]} | {k['publicaciones']} | {k['views']:,}".replace(",", ".") + f"{_delta(k['views'], pv.get('views'))} | "
                 f"{k['mediana_views']}{_delta(k['mediana_views'], pv.get('mediana_views'))} | {k['comentarios']}{_delta(k['comentarios'], pv.get('comentarios'))} | "
                 f"{k['guardados']}{_delta(k['guardados'], pv.get('guardados'))} | {k['compartidos']}{_delta(k['compartidos'], pv.get('compartidos'))} | {seg} |")
    week = [p for p in P if str(monday - datetime.timedelta(days=7)) <= p["date"] < str(monday)]
    if week:
        L += ["", "## Lo mejor de la semana", ""]
        for p in sorted(week, key=lambda p: -p["views"])[:5]:
            L.append(f"- {NOMBRE[p['red']]} · {p.get('formato')} · «{p.get('hook')}»: {p['views']} visualizaciones, {p['comments']} comentarios, "
                     f"{p['saved']} guardados" + (f" · [ver]({p['url']})" if p.get("url") else ""))
    L += ["", "## Qué cambia solo esta semana", ""] + ([f"- {c}" for c in changes] or ["- Nada: no hay ninguna opción que rinda claramente peor con datos suficientes."])
    L += ["- El piloto automático sigue eligiendo en cada reel el formato, estilo, gancho, bloque y tiempo para pensar que mejor "
          "funcionan (y explora un 15 % para no estancarse), y los guionistas trabajan con el playbook nuevo."]
    if res.get("sugerencias"):
        L += ["", "## Sugerencias que necesitan tu decisión", ""] + [f"- {str(s).strip()}" for s in res["sugerencias"][:3]]
    for title, txt in (("Playbook de reels", res.get("playbook")), ("Playbook de chuletas", res.get("chuletas")),
                       ("Playbook de explicados", res.get("explicados"))):
        if txt:
            L += ["", f"## {title}", "", str(txt).strip()]
    return "\n".join(L) + "\n"


def issue(key, body):
    """Incidencia 'Informe semanal' asignada al dueño (llega por correo); cierra la de la semana anterior."""
    if os.environ.get("INFORME_ISSUE", "true").lower() == "false":
        return
    try:
        import avisos
        title = f"📈 Informe semanal · {key}"
        opened = avisos._gh("GET", "/issues", params={"state": "open", "per_page": 100}) or []
        same = next((i for i in opened if i.get("title") == title), None)
        if same:                                             # revisión repetida: se actualiza el informe de esa semana
            avisos._gh("PATCH", f"/issues/{same['number']}", json={"body": body[:60000]})
            return
        for i in opened:
            if str(i.get("title", "")).startswith("📈 Informe semanal") and "pull_request" not in i:
                avisos._gh("PATCH", f"/issues/{i['number']}", json={"state": "closed", "state_reason": "completed"})
        owner = os.environ.get("GITHUB_REPOSITORY_OWNER")
        made = avisos._gh("POST", "/issues", json={"title": title, "body": body[:60000], "labels": ["informe-semanal"],
                                                   "assignees": [owner] if owner else []})
        if made is None:
            avisos._gh("POST", "/issues", json={"title": title, "body": body[:60000]})
    except Exception as e:
        print("semanal: incidencia no creada:", str(e)[:150], flush=True)


# ------------------------------------------------------------------ main
def run(force=False):
    today = datetime.date.today()
    key = week_key(today)
    S = _load(STATE, {"semanas": {}})
    S.setdefault("semanas", {})
    if key in S["semanas"] and not force:
        return f"revisión semanal: {key} ya hecha"
    monday = today - datetime.timedelta(days=today.weekday())
    P = posts()
    if len([p for p in P if p["tipo"] != "chuleta"]) < 6:
        return "revisión semanal: esperando más resultados"
    K = kpis(P, monday - datetime.timedelta(days=7), monday)
    prev_key = week_key(monday - datetime.timedelta(days=7))
    prev = S["semanas"].get(prev_key) or {}
    K_prev = prev.get("kpis") or kpis(P, monday - datetime.timedelta(days=14), monday - datetime.timedelta(days=7))
    fol, diag = followers()
    order = sorted(k for k in S["semanas"] if k < key)
    pau, why = pauses([S["semanas"][k] for k in order])
    res = {}
    if os.environ.get("GEMINI_API_KEY"):
        try:
            res = strategist(P, K, K_prev, strategy.playbook_text(), "; ".join(why))
        except Exception as e:
            print("semanal: estratega no disponible:", str(e)[:200], flush=True)
    if not res and os.environ.get("GEMINI_API_KEY") and today.weekday() < 2 and not force:
        return "revisión semanal: el estratega no ha respondido; se reintenta en el siguiente aviso"
    A, hook_changes = apply_hooks(res)
    A["pausados"] = {"semana": key, **pau}
    json.dump(A, open(strategy.ARMS_FILE, "w"), indent=1, ensure_ascii=False)
    for path, title, txt, lo in ((strategy.PLAYBOOK, "Playbook", res.get("playbook"), 60), (PB_CHULETAS, "Playbook de chuletas", res.get("chuletas"), 25),
                                 (PB_EXPLICADOS, "Playbook de explicados", res.get("explicados"), 25)):
        txt = str(txt or "").strip()
        if lo <= len(txt) <= 2500:
            open(path, "w").write(f"# {title} (actualizado {today})\n\n{txt}\n")
    changes = why + hook_changes
    body = report(key, K, K_prev, fol, prev.get("seguidores"), changes, res, P, monday)
    open(REPORT, "w").write(body)
    S["semanas"][key] = {"fecha": str(today), "kpis": K, "seguidores": fol, "pausados": pau, "cambios": changes, "diag": diag[:6]}
    json.dump(S, open(STATE, "w"), ensure_ascii=False, indent=1)
    try:
        strategy.write_report()
    except Exception:
        pass
    issue(key, body)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(body)
    return f"revisión semanal {key}: {len(P)} publicaciones medidas · cambios: {'; '.join(changes) or 'ninguno'}"


if __name__ == "__main__":
    print(run("--forzar" in sys.argv))
