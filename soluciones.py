"""Respuestas y soluciones de los reels de reto (los reels no enseñan la respuesta: la gente comenta la suya).

El reel dice: "Escribe tu respuesta en comentarios y nuestra IA te contestará personalmente con la solución en menos de
24 horas". Este script lo cumple. Se ejecuta cada 2 horas (workflow "Soluciones", de 8:00 a 0:00 hora de España):
  1. A partir de 12 h después de publicar cada reel (y hasta 7 días), contesta a TODOS los comentarios, uno a uno:
     una frase personal escrita por IA que reacciona a lo que ha dicho la persona (sin datos) + la solución verificada
     ("✅ ¡Correcta! Es la B) …" / "Esta vez no: es la B) …" / "La solución es la B) …") y su porqué en una frase.
     - Instagram: con la API de Instagram.  - TikTok y YouTube: con la API de comentarios de Zernio (necesita el
       complemento Inbox de Zernio y TikTok conectado con la app "TikTok for Business"; si no, se avisa y se sigue).
     Comentario hecho entre la publicación y las 12 h -> respuesta a las 12-14 h; después -> en menos de 2 h.
  2. Instagram: comenta en el reel la solución completa (una vez, a partir de las 12 h).
  3. Una vez al día (a partir de las 12:00): una story "SOLUCIÓN DE AYER" por reel y un carrusel de TikTok "Soluciones del reto de ayer".
Recuerda lo hecho en soluciones_hechas.json: si se relanza, no repite nada.

    python soluciones.py [AAAA-MM-DD]    (con fecha: además publica las stories y el carrusel de ese día)
Env: IG_TOKEN, ZERNIO_API_KEY, GEMINI_API_KEY (frase personal; sin ella, frases fijas), GITHUB_REPOSITORY.
Opcional: DRY_RUN=true, SOLUCIONES_TIKTOK / SOLUCIONES_STORIES / SOLUCIONES_RESPUESTAS = false, RESPONDER_DESDE_H (12).
"""
import datetime, json, os, random, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DONE = os.path.join(HERE, "soluciones_hechas.json")
DRY = os.environ.get("DRY_RUN", "false").lower() == "true"
MAX_REPLIES = 80                                    # por reel y ejecución (límites de las APIs)
DELAY_H = float(os.environ.get("RESPONDER_DESDE_H", "12"))
SLOT_TIME = {"manana": (8, 0), "mediodia": (14, 30), "noche": (21, 30), "manual": (23, 0)}


def on(name):
    return os.environ.get(name, "true").lower() != "false"


def yesterday():
    try:
        from zoneinfo import ZoneInfo
        today = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
    except Exception:
        today = datetime.date.today()
    return str(today - datetime.timedelta(days=1))


def load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def entries(day):
    out = []
    for line in open(os.path.join(HERE, "log.jsonl")) if os.path.exists(os.path.join(HERE, "log.jsonl")) else []:
        try:
            e = json.loads(line)
        except Exception:
            continue
        pub = e.get("publicado") or {}
        if e.get("date") == day and e.get("solucion_texto") and any(not str(v).startswith("error") for v in pub.values()):
            out.append(e)
    order = {"manana": 0, "mediodia": 1, "noche": 2}
    return sorted(out, key=lambda e: order.get(e.get("slot"), 3))


def recent_entries(max_days=7):
    """Reels de reto publicados hace entre DELAY_H horas y max_days días (con su hora de publicación en UTC)."""
    from zoneinfo import ZoneInfo
    now = datetime.datetime.now(datetime.timezone.utc)
    out = []
    p = os.path.join(HERE, "log.jsonl")
    for line in open(p) if os.path.exists(p) else []:
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not e.get("solucion_texto") or not any(not str(v).startswith("error") for v in (e.get("publicado") or {}).values()):
            continue
        if e.get("ts"):
            ts = datetime.datetime.fromisoformat(e["ts"]).replace(tzinfo=datetime.timezone.utc)
        else:                                       # registros antiguos: hora aproximada del hueco
            h, m = SLOT_TIME.get(e.get("slot"), (23, 0))
            ts = datetime.datetime.fromisoformat(e["date"]).replace(hour=h, minute=m, tzinfo=ZoneInfo("Europe/Madrid"))
        age = (now - ts).total_seconds() / 3600
        if DELAY_H <= age <= 24 * max_days:
            out.append(e)
    return out


def key_of(e):
    return f"{e['date']}_{e.get('slot')}_{(e.get('ids') or ['x'])[0]}"


def raw_url(path):
    repo = os.environ.get("GITHUB_REPOSITORY", "AlbertoChueca/tcae-auto-reels")
    ref = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"


# ------------------------------------------------------------------ detectar la letra de cada comentario
def letters_in(text):
    """Letras de respuesta del comentario, en orden. La 'a' suelta es una preposición: solo cuenta si es el comentario
    entero, va tras 'la/opción/respuesta' o va como 'a)' o '1a'."""
    t = " " + text.lower() + " "
    out = []
    pat = re.compile(r"(?:(?P<pre>\b(?:la|opci[oó]n|respuesta|es la)\s+)|(?P<num>\b\d\s?[).:-]?\s?))?"
                     r"(?<![a-záéíóúñ])(?P<l>[abcd])(?P<post>\))?(?![\wáéíóúñ])")
    for m in pat.finditer(t):
        l = m.group("l")
        if l == "a" and not (m.group("pre") or m.group("num") or m.group("post") or re.fullmatch(r"\s*a\s*[!.?]*\s*", text.lower())):
            continue
        out.append(l.upper())
    if not out:
        m = re.fullmatch(r"\s*([abcd]{2,3})\s*[!.]*\s*", text.lower())
        if m:
            out = list(m.group(1).upper())
    return out


def judge(text, e):
    """(tipo, aciertos, total) o None si el comentario no es una respuesta."""
    if e.get("formato") == "mito_realidad" and e.get("veredicto"):
        t = text.lower()
        says = "MITO" if re.search(r"\bmito\b", t) and not re.search(r"\brealidad\b", t) else (
            "REALIDAD" if re.search(r"\b(realidad|real|verdad)\b", t) and not re.search(r"\bmito\b", t) else None)
        return None if says is None else ("one", int(says == e["veredicto"]), 1)
    sol = e.get("respuestas") or []
    ls = letters_in(text)
    if not sol or not ls:
        return None
    if len(sol) > 1:
        return ("sim", sum(a == b for a, b in zip(ls, sol)), len(sol)) if len(ls) >= len(sol) else None
    if len(set(ls)) > 1:
        return None
    return ("one", int(ls[0] == sol[0]), 1)


def _first_sentence(t, n=170):
    t = re.sub(r"\s+", " ", (t or "")).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    t = m.group(1) if m else t
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def solution_line(e):
    """La solución (verificada al crear el reel), en una línea."""
    st = e["solucion_texto"].split("\n\n")
    head = st[0].replace("✅ Solución: ", "").replace("✅ Soluciones del simulacro:\n", "").replace("\n", " · ")
    why = _first_sentence(st[1]) if len(st) > 1 else ""
    return head, why


def reply_text(j, e, reaction=""):
    head, why = solution_line(e)
    head = head.rstrip(".")
    opt = re.sub(r"^[ABCD]\)\s*", "", head).lower()[:60]
    if opt and opt in (why or "").lower():               # el porqué solo repite la opción: no aporta
        why = ""
    sol = e.get("respuestas") or []
    if e.get("formato") == "mito_realidad":
        head = f"Es {(e.get('veredicto') or '').lower()}."
    if j is None:
        core = {"mito_realidad": f"Solución: {head}", "simulacro_3": f"Soluciones: {head}"}.get(
            e.get("formato"), f"La solución es la {head}.")
    elif e.get("formato") == "mito_realidad":
        core = (f"✅ ¡Bien visto! {head}" if j[1] else f"Esta vez no 😉 {head}")
    elif j[0] == "sim":
        tag = "¡Pleno! 🎯" if j[1] == j[2] else ("¡Muy bien! 💪" if j[1] >= j[2] - 1 else "¡A seguir practicando! 💪")
        core = f"{j[1]}/{j[2]} {tag} Soluciones: {' · '.join(f'{i + 1}{l}' for i, l in enumerate(sol))}"
        why = ""
    else:
        core = (random.choice(["✅ ¡Correcta!", "🎯 ¡Esa es!", "✅ ¡Bien!"]) if j[1] else
                random.choice(["Esta vez no 😉", "¡Casi!", "Uy, esta tenía miga 😅"])) + f" Es la {head}."
    txt = " ".join(x for x in (reaction.strip(), core, why) if x)
    return txt[:900]


def reactions(comments, e):
    """Una frase personal por comentario (IA), que reacciona a lo que dice la persona SIN dar datos ni la solución.
    Si la IA no está disponible o la frase no cumple las reglas, va sin frase (la solución siempre va igual)."""
    if not comments or not os.environ.get("GEMINI_API_KEY"):
        return {}
    try:
        import gemini
        res = gemini.ask("""Eres la community manager de Aprueba TCAE (tests para las oposiciones de TCAE). Para cada comentario
escribe UNA frase corta (máx. 14 palabras), cercana y en español de España, que reaccione a lo que dice esa persona
(ánimo, gracias, empatía si duda o se queja...). PROHIBIDO: dar la solución, letras de opciones, datos sanitarios o
legales, cifras, promesas, enlaces. Sin comillas. Puedes usar 1 emoji.
Comentarios (id: texto):
""" + "\n".join(f"{c['id']}: {c['text'][:200]}" for c in comments) + """
Devuelve JSON: {"<id>": "<frase>", ...}""", 0.8)
        out = {}
        for c in comments:
            f = str(res.get(c["id"]) or "").strip()
            if 2 <= len(f.split()) <= 16 and not re.search(r"\d|\b[ABCD]\)|\bla [abcd]\b|https?:|www\.", f, re.I):
                out[c["id"]] = f
        return out
    except Exception as ex:
        print("frases personales no disponibles:", str(ex)[:150], flush=True)
        return {}


# ------------------------------------------------------------------ Instagram
def ig():
    import publish_ig as IG
    tok = os.environ["IG_TOKEN"]
    return IG, tok, IG.whoami(tok)


def ig_comment(media_id, text):
    IG, tok, _ = ig()
    return IG._check(requests.post(f"{IG.GRAPH}/{media_id}/comments", data={"message": text[:2100], "access_token": tok},
                                   timeout=60))["id"]


def ig_comments(media_id):
    IG, tok, me = ig()
    cs = IG._check(requests.get(f"{IG.GRAPH}/{media_id}/comments", params={
        "fields": "id,text,username", "limit": 100, "access_token": tok}, timeout=60)).get("data", [])
    return [{"id": c["id"], "text": c.get("text", ""), "user": c.get("username", "")} for c in cs
            if c.get("username") != me["username"]]


def ig_reply(cid, msg):
    IG, tok, _ = ig()
    IG._check(requests.post(f"{IG.GRAPH}/{cid}/replies", data={"message": msg, "access_token": tok}, timeout=60))


ZAPI = "https://zernio.com/api/v1"


def _zh():
    return {"Authorization": f"Bearer {os.environ['ZERNIO_API_KEY']}"}


def z_comments(post_id, account):
    r = requests.get(f"{ZAPI}/inbox/comments/{post_id}", headers=_zh(), params={"accountId": account, "limit": 100}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    out = []
    for c in r.json().get("comments", []):
        if (c.get("from") or {}).get("isOwner") or c.get("canReply") is False:
            continue
        out.append({"id": c["id"], "text": c.get("message", ""), "user": (c.get("from") or {}).get("username") or ""})
    return out


def z_reply(post_id, account, cid, msg):
    r = requests.post(f"{ZAPI}/inbox/comments/{post_id}", headers={**_zh(), "Idempotency-Key": f"sol-{cid}"[:250]},
                      json={"accountId": account, "message": msg, "commentId": cid}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")


def answer_all(e, platform, fetch, send, done_ids, with_at):
    """Contesta a todos los comentarios aún sin respuesta de un reel en una red. Devuelve los ids contestados."""
    cs = [c for c in fetch() if c["id"] not in done_ids and c["text"].strip()][:MAX_REPLIES]
    rx = reactions(cs, e)
    out = []
    for c in cs:
        msg = reply_text(judge(c["text"], e), e, rx.get(c["id"], ""))
        if with_at and c["user"]:
            msg = f"@{c['user']} " + msg
        print(f"  [{platform}] @{c['user']}: {c['text'][:60]!r} -> {msg[:140]}", flush=True)
        if not DRY:
            try:
                send(c["id"], msg); time.sleep(2)
            except Exception as ex:
                print(f"  [{platform}] respuesta fallida:", str(ex)[:150], flush=True); continue
        out.append(c["id"])
    return out


def ig_story_image(url):
    IG, tok, me = ig()
    cid = IG._check(requests.post(f"{IG.GRAPH}/{me['user_id']}/media", data={
        "image_url": url, "media_type": "STORIES", "access_token": tok}, timeout=120))["id"]
    IG._wait(cid, tok, "story de solución")
    return IG._check(requests.post(f"{IG.GRAPH}/{me['user_id']}/media_publish", data={
        "creation_id": cid, "access_token": tok}, timeout=120))["id"]


# ------------------------------------------------------------------ main
def respond_all(done, rows):
    has_ig, zernio = bool(os.environ.get("IG_TOKEN")), bool(os.environ.get("ZERNIO_API_KEY"))
    acc = {}
    if zernio:
        try:
            import publish_zernio as Z
            acc = Z.accounts()
        except Exception as ex:
            rows.append(f"- ❌ Zernio: cuentas no disponibles ({str(ex)[:120]})")
    for e in recent_entries():
        key = key_of(e)
        st = done.setdefault(key, {"respondidos": [], "stories": []})
        st["fecha"] = str(datetime.date.today())
        pub = e.get("publicado") or {}
        if has_ig and e.get("media_id"):
            if not st.get("comentario"):
                text = e["solucion_texto"] + "\n\n¿Acertaste? 👇 Practica más preguntas en apruebatcae.com (link en la bio)."
                try:
                    st["comentario"] = "dry" if DRY else ig_comment(e["media_id"], text)
                    rows.append(f"- ✅ {key}: solución comentada en el reel")
                except Exception as ex:
                    rows.append(f"- ❌ {key}: comentario fallido ({str(ex)[:150]})")
            if on("SOLUCIONES_RESPUESTAS"):
                try:
                    new = answer_all(e, "instagram", lambda: ig_comments(e["media_id"]), ig_reply, set(st["respondidos"]), True)
                    st["respondidos"] += new
                    if new: rows.append(f"- ✅ {key}: {len(new)} respuestas en Instagram")
                except Exception as ex:
                    rows.append(f"- ❌ {key}: respuestas en Instagram fallidas ({str(ex)[:150]})")
        for plat, pkey in (("tiktok", "tiktok_video"), ("youtube", "youtube_short")):
            pid = str(pub.get(pkey) or "")
            if not (zernio and on("SOLUCIONES_RESPUESTAS") and acc.get(plat) and pid and not pid.startswith("error")):
                continue
            if st.get(f"{plat}_off"):
                continue
            field = f"{plat}_respondidos"
            try:
                new = answer_all(e, plat, lambda: z_comments(pid, acc[plat]),
                                 lambda cid, msg: z_reply(pid, acc[plat], cid, msg), set(st.get(field, [])), False)
                st[field] = st.get(field, []) + new
                if new: rows.append(f"- ✅ {key}: {len(new)} respuestas en {plat}")
            except Exception as ex:
                msg = str(ex)
                if "PLATFORM_LIMITATION" in msg or "addon" in msg.lower() or msg.startswith("403"):
                    st[f"{plat}_off"] = msg[:160]       # sin complemento Inbox o sin TikTok for Business: no se reintenta
                rows.append(f"- ❌ {key}: respuestas en {plat} no disponibles ({msg[:150]})")


def daily_extras(day, done, rows):
    """Stories con la solución y carrusel de TikTok de los reels de un día (una vez)."""
    es = entries(day)
    has_ig = bool(os.environ.get("IG_TOKEN"))
    for e in es:
        key = key_of(e)
        st = done.setdefault(key, {"respondidos": [], "stories": []})
        if has_ig and on("SOLUCIONES_STORIES"):
            for p in e.get("soluciones") or []:
                if p in st["stories"] or not os.path.exists(os.path.join(HERE, p)):
                    continue
                try:
                    if not DRY:
                        ig_story_image(raw_url(p))
                    st["stories"].append(p)
                    rows.append(f"- ✅ {key}: story con la solución")
                except Exception as ex:
                    rows.append(f"- ❌ {key}: story fallida ({str(ex)[:150]})")
    tk = f"{day}_tiktok"
    imgs = [p for e in es for p in (e.get("soluciones") or []) if os.path.exists(os.path.join(HERE, p))]
    if imgs and on("SOLUCIONES_TIKTOK") and os.environ.get("ZERNIO_API_KEY") and not done.get(tk, {}).get("id"):
        try:
            import publish_zernio as Z
            desc = ("Soluciones del reto de ayer 🎯 ¿Cuántas acertaste? Cuéntamelo en comentarios 👇\n\n"
                    + "\n\n".join(e["solucion_texto"] for e in es)
                    + "\n\nHoy hay preguntas nuevas: síguenos. Practica gratis en apruebatcae.com\n\n#TCAE #oposicionesTCAE #auxiliardeenfermeria")
            pid = "dry" if DRY else Z.tiktok_photos([raw_url(p) for p in imgs[:35]], "Soluciones del reto de ayer", desc)
            done[tk] = {"fecha": str(datetime.date.today()), "id": pid}
            rows.append(f"- ✅ TikTok: carrusel con {len(imgs)} soluciones")
        except Exception as ex:
            rows.append(f"- ❌ TikTok: carrusel fallido ({str(ex)[:150]})")


def main(day=None):
    done = load(DONE, {})
    rows = ["## Respuestas y soluciones"]
    respond_all(done, rows)
    try:
        from zoneinfo import ZoneInfo
        hour = datetime.datetime.now(ZoneInfo("Europe/Madrid")).hour
    except Exception:
        hour = 13
    if day or hour >= 12:                          # desde las 12:00 (idempotente: cada cosa se publica una sola vez)
        daily_extras(day or yesterday(), done, rows)
    if len(rows) == 1:
        rows.append("- Nada nuevo que contestar.")
    if not DRY:
        json.dump(done, open(DONE, "w"), ensure_ascii=False, indent=0)
    print("\n".join(rows))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("\n".join(rows) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None)
