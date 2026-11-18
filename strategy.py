"""Piloto automático (adaptado de StreakChess). Palancas: formato, estilo de gancho, bloque del temario, tiempo para pensar.

Autopilot optimiser: every reel is a small experiment, and the account learns what works by trial and error.

Each reel picks one option ("arm") for each lever below. After a reel has been live for 3+ days its real Instagram
results (performance.json, from insights.py) become its reward. Next choices use Thompson sampling: options that
perform better are chosen more and more often, weak ones fade out, and ~15% of reels keep exploring so the system
never gets stuck. Once a week a strategist agent (Gemini) reads all the results, writes playbook.md (plain-English
lessons used by the script writer and the reviewer) and may propose a couple of new options to test.

Files: strategy_arms.json (current options), strategy_report.md (what's winning, readable on GitHub), playbook.md.
"""
import datetime, json, math, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS_FILE = os.path.join(HERE, "strategy_arms.json")
REPORT = os.path.join(HERE, "strategy_report.md")
PLAYBOOK = os.path.join(HERE, "playbook.md")
PERF = os.path.join(HERE, "performance.json")
PERF_Z = os.path.join(HERE, "performance_tiktok.json")
EXPLORE = float(os.environ.get("EXPLORE_RATE", "0.15"))
MIN_AGE_DAYS = 3
MAX_AGE_DAYS = int(os.environ.get("PILOTO_DIAS", "60"))        # el piloto aprende de los últimos 60 días (la cuenta cambia)
# Redes de las que aprende el piloto. YouTube Shorts queda fuera: con 10-40 visualizaciones por vídeo es ruido y
# distorsionaba las decisiones (p. ej. hundía formatos que en TikTok van bien). Sigue saliendo en los informes.
LEARN_FROM = [x.strip() for x in os.environ.get("PILOTO_REDES", "instagram,tiktok").split(",") if x.strip()]

DEFAULT_ARMS = {
    "formato": ["pregunta_del_dia", "examen_real", "error_tipico", "truco_memorizar", "mito_realidad", "simulacro_3",
                "legislacion_30s", "caso_practico", "flashcards_express"],
    "estilo": ["marca", "clasico", "cuaderno", "examen", "noche", "minimal", "ilustrado"],
    "hook_style": [
        "reto: retar directamente ('¿la acertarías en el examen?')",
        "trampa: avisar de que la pregunta tiene trampa o confunde",
        "empatía: hablar a quien estudia después del turno o con poco tiempo",
        "curiosidad: abrir con un dato o duda que pique la curiosidad (solo del material)",
        "examen: recordar que es el tipo de pregunta que cae en el examen oficial",
        "repaso exprés: 'repaso de 30 segundos' para estudiar en cualquier hueco",
    ],
    "bloque": ["clinico", "legislacion", "mixto"],
    "think_time": ["corto", "normal", "largo"],
}
THINK_SECONDS = {"corto": 5, "normal": 7, "largo": 9}


def _file():
    try:
        return json.load(open(ARMS_FILE))
    except Exception:
        return {}


def arms():
    """Opciones de cada palanca (solo listas: el archivo guarda además las pausas de la semana)."""
    a = {k: v for k, v in _file().items() if isinstance(v, list)}
    for k, v in DEFAULT_ARMS.items():
        a.setdefault(k, list(v))
    a["bloque"] = [b for b in a["bloque"] if b != "aragon"] or list(DEFAULT_ARMS["bloque"])   # cuenta generalista
    return a


def paused(lever=None):
    """Formatos y estilos que la revisión semanal (semanal.py) ha dejado en pausa ESTA semana: {palanca: [opción]}."""
    p = _file().get("pausados") or {}
    y, w, _ = datetime.date.today().isocalendar()
    if p.get("semana") != f"{y}-W{w:02d}":
        p = {}
    out = {k: [x for x in (p.get(k) or []) if isinstance(x, str)] for k in ("formato", "estilo")}
    return out if lever is None else out.get(lever, [])


def playbook_of(name):
    """Playbook de 'chuletas' o 'explicados' (lo escribe la revisión semanal)."""
    try:
        return open(os.path.join(HERE, f"playbook_{name}.md")).read().strip()
    except Exception:
        return ""



def reward(r):
    """Más es mejor. Visualizaciones + guardados (clave en contenido de estudio) + compartidos + comentarios +
    visitas al perfil (el paso previo a ir a la web) + tiempo de visionado."""
    views = r.get("views") or r.get("reach")
    eng = ((r.get("likes") or 0) + 3 * (r.get("comments") or 0) + 4 * (r.get("shares") or 0) + 5 * (r.get("saved") or 0)
           + 4 * (r.get("profile_visits") or 0) + 6 * (r.get("follows") or 0))
    if views:
        watch = (r.get("ig_reels_avg_watch_time") or 0) / 1000.0
        return math.log1p(views) + 0.7 * math.log1p(eng) + 0.06 * min(watch, 40)
    if r.get("like_count") is not None or r.get("likes") is not None:      # no insights permission: public counts
        return math.log1p((r.get("like_count") or r.get("likes") or 0) + 3 * (r.get("comments_count") or r.get("comments") or 0))
    return None


def reward_z(r):
    """TikTok / YouTube (analítica de Zernio): visualizaciones + interacciones."""
    views = r.get("views")
    if not views:
        return None
    eng = (r.get("likes") or 0) + 3 * (r.get("comments") or 0) + 4 * (r.get("shares") or 0) + 5 * (r.get("saved") or 0)
    return math.log1p(views) + 0.7 * math.log1p(eng)


def _results():
    """[(arms, puntuación, fila)] de Instagram, TikTok y YouTube. Cada red tiene su escala (en TikTok un vídeo normal
    tiene muchas más visualizaciones), así que la puntuación de cada vídeo se mide contra la media de SU red: 0 = un
    vídeo normal en esa red, +1 = una desviación típica mejor. Así las tres redes suman en el mismo aprendizaje."""
    today = datetime.date.today(); groups = {}
    for path, fn, red in ((PERF, reward, "instagram"), (PERF_Z, reward_z, None)):
        try:
            perf = json.load(open(path))
        except Exception:
            continue
        for r in perf.values():
            try:
                if not isinstance(r, dict) or not MIN_AGE_DAYS <= (today - datetime.date.fromisoformat(r["date"])).days <= MAX_AGE_DAYS:
                    continue
            except Exception:
                continue
            if (red or r.get("red") or "tiktok") not in LEARN_FROM:
                continue
            rw = fn(r)
            if rw is not None and r.get("arms"):
                groups.setdefault(red or r.get("red") or "tiktok", []).append((r["arms"], rw, {**r, "red": red or r.get("red")}))
    out = []
    for red, rows in groups.items():
        vals = [rw for _, rw, _ in rows]
        mu = sum(vals) / len(vals)
        sd = max((sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5, 0.25) if len(vals) >= 4 else 1.0
        out += [(a, (rw - mu) / sd, r) for a, rw, r in rows]
    return out


def stats():
    """{lever: {arm: (n, mean)}} plus the global mean/sd of rewards."""
    res = _results(); A = arms()
    vals = [rw for _, rw, _ in res]
    mu = sum(vals) / len(vals) if vals else 0.0
    sd = (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5 if len(vals) > 1 else 1.0
    st = {lev: {a: [0, 0.0] for a in opts} for lev, opts in A.items()}
    for chosen, rw, _ in res:
        for lev, a in chosen.items():
            if lev in st and a in st[lev]:
                st[lev][a][0] += 1; st[lev][a][1] += rw
    out = {lev: {a: (n, (s / n if n else None)) for a, (n, s) in d.items()} for lev, d in st.items()}
    return out, mu, max(sd, 0.3), len(res)


def _recent_arms(n=2):
    out = []
    try:
        for line in open(os.path.join(HERE, "log.jsonl")):
            a = json.loads(line).get("arms")
            if a: out.append(a)
    except Exception:
        pass
    return out[-n:]


def choose(seed=None, fixed=None):
    """Pick one option per lever (Thompson sampling with a prior centred on the account average).
    Variedad: formato y estilo de gancho nunca repiten la opción de los 2 últimos reels."""
    rng = random.Random(seed)
    st, mu, sd, n_total = stats()
    recent = _recent_arms(2)
    pick = {}
    for lev, d in st.items():
        if fixed and lev in fixed:
            pick[lev] = fixed[lev]; continue
        off = set(paused(lev)) if lev in ("formato", "estilo") else set()
        if off and len(d) - len(off & set(d)) >= 3:        # en pausa esta semana (revisión semanal)
            d = {a: v for a, v in d.items() if a not in off}
        if lev in ("hook_style", "formato", "estilo"):
            banned = {r.get(lev) for r in recent}
            if len(d) - len(banned & set(d)) >= 2:
                d = {a: v for a, v in d.items() if a not in banned}
        if rng.random() < EXPLORE or n_total < 6:
            pick[lev] = rng.choice(list(d)); continue
        best, best_v = None, -1e9
        for a, (n, mean) in d.items():
            m = mean if mean is not None else mu
            v = rng.gauss((m * n + mu * 1) / (n + 1), sd / math.sqrt(n + 1))
            if v > best_v:
                best, best_v = a, v
        pick[lev] = best
    return pick


def short(a):
    return a.split(":")[0]


def write_report():
    st, mu, sd, n = stats()
    lines = [f"# Piloto automático Aprueba TCAE - qué está funcionando\n", f"_Updated {datetime.date.today()} · {n} reels with results "
             f"(3+ days old) · average score {mu:.2f}_\n"]
    if n < 6:
        lines.append("\nStill collecting data: options are being tested evenly for now.\n")
    for lev, d in st.items():
        lines.append(f"\n## {lev}\n\n| option | reels | avg score |\n|---|---|---|")
        for a, (k, m) in sorted(d.items(), key=lambda x: -(x[1][1] if x[1][1] is not None else -1e9)):
            lines.append(f"| {short(a)} | {k} | {'-' if m is None else f'{m:.2f}'} |")
    by = {}
    for _, _, r in _results():                             # qué formato funciona en cada red (visualizaciones medias)
        by.setdefault(r.get("red") or "instagram", {}).setdefault(r.get("formato") or "?", []).append(r.get("views") or r.get("reach") or 0)
    for red, d in by.items():
        lines.append(f"\n## {red}: visualizaciones medias por formato\n\n| formato | vídeos | media |\n|---|---|---|")
        for f, v in sorted(d.items(), key=lambda x: -sum(x[1]) / len(x[1])):
            lines.append(f"| {f} | {len(v)} | {sum(v) / len(v):.0f} |")
    if os.path.exists(PLAYBOOK):
        lines.append("\n---\n" + open(PLAYBOOK).read())
    open(REPORT, "w").write("\n".join(lines) + "\n")
    return "\n".join(lines)


def playbook_text():
    try:
        return open(PLAYBOOK).read().strip()
    except Exception:
        return ""


def weekly_strategist(force=False):
    """La revisión semanal vive ahora en semanal.py (mide el crecimiento, pausa lo que no funciona, escribe los playbooks
    y manda el informe). Se llama desde run_daily.py con el primer reel de cada semana."""
    import semanal
    return semanal.run(force)
