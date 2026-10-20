"""Soluciones del día anterior (los reels ya no enseñan la respuesta: así la gente comenta su letra).

Cada día (workflow "Soluciones", 13:00 hora de España) toma los reels publicados AYER y:
  1. Instagram: comenta en cada reel la solución con su explicación (texto verificado guardado al crear el reel).
  2. Instagram: responde a cada persona que dejó su letra ("✅ ¡Correcta!" / "Era la B, ¡la próxima es tuya!").
     Los comentarios que no son una respuesta no se contestan (nada de spam).
  3. Instagram: una story por solución (la imagen "SOLUCIÓN DE AYER" del propio reel).
  4. TikTok: un carrusel de fotos "Soluciones del reto de ayer" con todas las soluciones (la API de TikTok no permite
     comentar, así que la solución llega como publicación propia, una al día).
Recuerda lo hecho en soluciones_hechas.json: si se relanza, no repite nada.

    python soluciones.py [AAAA-MM-DD]       (por defecto: ayer, hora de España)
Env: IG_TOKEN, ZERNIO_API_KEY, GITHUB_REPOSITORY (las imágenes se sirven desde el repositorio público).
Opcional: DRY_RUN=true (solo muestra), SOLUCIONES_TIKTOK=false, SOLUCIONES_STORIES=false, SOLUCIONES_RESPUESTAS=false.
"""
import datetime, json, os, random, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DONE = os.path.join(HERE, "soluciones_hechas.json")
DRY = os.environ.get("DRY_RUN", "false").lower() == "true"
MAX_REPLIES = 60


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


def reply_text(j, e):
    sol = e.get("respuestas") or []
    if e.get("formato") == "mito_realidad":
        v = (e.get("veredicto") or "").lower()
        return random.choice([f"✅ ¡Bien visto! Es {v}.", f"🎯 ¡Correcto! Es {v}."]) if j[1] else \
            random.choice([f"Esta vez no 😉 Es {v}. ¡La próxima es tuya! 💪", f"¡Casi! Es {v}. Te dejo la explicación en el comentario 👆"])
    if j[0] == "sim":
        msg = "¡Pleno! 🎯" if j[1] == j[2] else ("¡Muy bien! 💪" if j[1] >= j[2] - 1 else "¡A seguir practicando! 💪")
        return f"{j[1]}/{j[2]} {msg} Soluciones: {' · '.join(f'{i + 1}{l}' for i, l in enumerate(sol))}"
    L = sol[0] if sol else "?"
    return random.choice([f"✅ ¡Correcta! Era la {L}. 🎯", f"🎯 ¡Esa es! La {L}. Sigue así 💪", f"✅ ¡Bien! La {L}. Esa ya no se te escapa"]) if j[1] else \
        random.choice([f"Esta vez no 😉 Era la {L}. ¡La próxima es tuya! 💪", f"¡Casi! Era la {L}. Mira la explicación en el comentario 👆",
                       f"Era la {L} 😅 Esta tenía miga. ¡A por la siguiente!"])


# ------------------------------------------------------------------ Instagram
def ig():
    import publish_ig as IG
    tok = os.environ["IG_TOKEN"]
    return IG, tok, IG.whoami(tok)


def ig_comment(media_id, text):
    IG, tok, _ = ig()
    return IG._check(requests.post(f"{IG.GRAPH}/{media_id}/comments", data={"message": text[:2100], "access_token": tok},
                                   timeout=60))["id"]


def ig_replies(media_id, e, done_ids):
    IG, tok, me = ig()
    myname = me["username"]
    cs = IG._check(requests.get(f"{IG.GRAPH}/{media_id}/comments", params={
        "fields": "id,text,username", "limit": 100, "access_token": tok}, timeout=60)).get("data", [])
    out = []
    for c in cs:
        if c["id"] in done_ids or c.get("username") == myname or len(out) >= MAX_REPLIES:
            continue
        j = judge(c.get("text", ""), e)
        if j is None:
            continue
        msg = reply_text(j, e)
        print(f"  @{c.get('username')}: {c.get('text', '')[:60]!r} -> {msg}", flush=True)
        if not DRY:
            try:
                IG._check(requests.post(f"{IG.GRAPH}/{c['id']}/replies", data={"message": msg, "access_token": tok}, timeout=60))
                time.sleep(2)
            except Exception as ex:
                print("  respuesta fallida:", str(ex)[:150], flush=True); continue
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
def main(day=None):
    day = day or yesterday()
    es = entries(day)
    done = load(DONE, {})
    rows = [f"## Soluciones de los reels del {day}"]
    if not es:
        print(f"No hay reels con solución pendiente del {day}")
        rows.append("- No hay reels con solución pendiente.")
    has_ig = bool(os.environ.get("IG_TOKEN"))
    for e in es:
        key = f"{day}_{e.get('slot')}"
        st = done.setdefault(key, {"fecha": str(datetime.date.today()), "respondidos": [], "stories": []})
        st["fecha"] = str(datetime.date.today())
        print(f"• {key}: {e.get('formato')} · respuesta {e.get('respuestas') or e.get('veredicto')}", flush=True)
        text = e["solucion_texto"] + "\n\n¿Acertaste? 👇 Practica más preguntas en apruebatcae.com (link en la bio)."
        if has_ig and e.get("media_id"):
            if not st.get("comentario"):
                try:
                    st["comentario"] = "dry" if DRY else ig_comment(e["media_id"], text)
                    rows.append(f"- ✅ {key}: solución comentada en el reel")
                except Exception as ex:
                    rows.append(f"- ❌ {key}: comentario fallido ({str(ex)[:150]})")
            if on("SOLUCIONES_RESPUESTAS"):
                try:
                    new = ig_replies(e["media_id"], e, set(st["respondidos"]))
                    st["respondidos"] += new
                    rows.append(f"- ✅ {key}: {len(new)} respuestas a quien dejó su letra")
                except Exception as ex:
                    rows.append(f"- ❌ {key}: respuestas fallidas ({str(ex)[:150]})")
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
    if not DRY:
        json.dump(done, open(DONE, "w"), ensure_ascii=False, indent=0)
    print("\n".join(rows))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("\n".join(rows) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None)
