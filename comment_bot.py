"""Responde a los comentarios nuevos de los reels recientes: respuesta pública breve (+ DM opcional con el enlace).

Se ejecuta cada hora desde GitHub Actions. Solo usa la API oficial de Instagram sobre nuestros propios posts.
- Detecta la respuesta del comentario (A/B/C/D, "la b", "opción c"...; en simulacros "1a 2c 3b" o "ACB"; en
  mito o realidad "mito"/"realidad") y la compara con la correcta guardada en log.jsonl.
- Felicita a quien acierta y anima a quien falla sin desvelar la respuesta en público (está al final del vídeo).
- Como mucho un DM por persona y semana (desactivado por defecto: BOT_SEND_DMS=true para activarlo).
- Recuerda los comentarios ya atendidos en handled_comments.json.
Env: IG_TOKEN. Opcional: BOT_DRY_RUN=true (solo muestra), BOT_SEND_DMS=true.
"""
import datetime, json, os, random, re, requests
from publish_ig import GRAPH, _check, whoami

TOKEN = os.environ["IG_TOKEN"]
DRY = os.environ.get("BOT_DRY_RUN") == "true"
SEND_DMS = os.environ.get("BOT_SEND_DMS") == "true"
HANDLED = "handled_comments.json"
LINK = "https://apruebatcae.com/?utm_source=instagram&utm_medium=dm&utm_campaign=reel_comment"

PUBLIC_CORRECT = [
    "¡Correcto! 🎯 Sigue así, que esa ya no se te escapa en el examen. Más preguntas gratis en el link de la bio",
    "¡Bien! ✅ Esa es. ¿Te atreves con un simulacro completo? Link en la bio",
    "¡Exacto! 💪 Guarda el reel para repasarlo antes del examen",
    "¡Acertaste! 👏 Practica más preguntas como esta gratis en apruebatcae.com",
    "¡Esa es! 🎯 Mañana otra pregunta del temario, síguenos para no perdértela",
    "¡Muy bien! ✅ Tienes más de 1.800 preguntas para seguir practicando en el link de la bio",
]
PUBLIC_WRONG = [
    "¡Casi! 😉 Mira la explicación al final del vídeo, que esta tiene miga. Más práctica en el link de la bio",
    "¡Buen intento! La solución está al final del vídeo 👀 Guárdalo para repasarlo",
    "¡Esta tiene su trampa! 😅 Revisa la explicación del vídeo y prueba con más en apruebatcae.com",
    "¡Gracias por participar! 💪 Mira el final del vídeo y la próxima no se te escapa",
]
PUBLIC_OTHER = [
    "¡Gracias por comentar! 💚 Una pregunta del temario cada día, síguenos",
    "¡Mucho ánimo con la oposición! 💪 Practica gratis en el link de la bio",
    "¡Gracias! 💚 Guarda el reel para repasar y prueba más preguntas en apruebatcae.com",
    "¡A por la plaza! 💪 Tienes tests y simulacros gratis en el link de la bio",
]
PUBLIC_SIM = "¡{ok}/{n}! {msg} Más simulacros gratis en el link de la bio"
DM_TEXT = ("¡Gracias por participar! 💚 En Aprueba TCAE tienes más de 1.800 preguntas tipo test, simulacros y flashcards "
           "de la oposición de TCAE del SALUD para practicar gratis: " + LINK)


def letters_in(text):
    """Letras de respuesta que aparecen en el comentario, en orden. La 'a' suelta es una preposición en español, así que
    solo cuenta si es el comentario entero, va tras 'la/opción/respuesta', o va como 'a)' o '1a'."""
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
        m = re.fullmatch(r"\s*([abcd]{2,3})\s*[!.]*\s*", text.lower())     # "acb"
        if m:
            out = list(m.group(1).upper())
    return out


def judge(text, e):
    """(tipo, aciertos, total) o None si el comentario no es una respuesta."""
    fmt = e.get("formato")
    if fmt == "flashcards_express":
        m = re.search(r"\b([0-4])\s*/\s*4\b", text)
        return ("sim", int(m.group(1)), 4) if m else None
    if fmt == "mito_realidad" and e.get("veredicto"):
        t = text.lower()
        says = "MITO" if re.search(r"\bmito\b", t) and not re.search(r"\brealidad\b", t) else (
            "REALIDAD" if re.search(r"\b(realidad|real|verdad)\b", t) and not re.search(r"\bmito\b", t) else None)
        return None if says is None else ("one", int(says == e["veredicto"]), 1)
    sol = e.get("respuestas") or []
    ls = letters_in(text)
    if not sol or not ls:
        return None
    if len(sol) > 1:
        if len(ls) < len(sol):
            return None
        return ("sim", sum(a == b for a, b in zip(ls, sol)), len(sol))
    if len(set(ls)) > 1:                  # varias letras distintas: no lo damos por respuesta
        return None
    return ("one", int(ls[0] == sol[0]), 1)


def load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default


def main():
    try:
        me = whoami(TOKEN)
    except Exception as e:
        report(0, 0, [f"comprobación de token/cuenta fallida: {str(e)[:300]}"]); raise SystemExit(1)
    uid, myname = me["user_id"], me["username"]
    handled = load(HANDLED, {"comments": [], "dm": {}})
    done = set(handled["comments"])
    posts = {}
    if os.path.exists("log.jsonl"):
        for line in open("log.jsonl"):
            e = json.loads(line)
            if e.get("media_id"):
                posts[e["media_id"]] = e
    now = datetime.datetime.now(datetime.timezone.utc)
    week_ago = now - datetime.timedelta(days=7)
    media = _check(requests.get(f"{GRAPH}/{uid}/media", params={
        "fields": "id,timestamp,media_product_type,comments_count", "limit": 30, "access_token": TOKEN}))["data"]
    errors, sent_pub, sent_dm = [], 0, 0
    for m in media:
        ts = datetime.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
        if ts < week_ago or not m.get("comments_count"):
            continue
        try:
            comments = _check(requests.get(f"{GRAPH}/{m['id']}/comments", params={
                "fields": "id,text,username,timestamp", "limit": 50, "access_token": TOKEN})).get("data", [])
        except Exception as e:
            errors.append(f"leer comentarios de {m['id']}: {str(e)[:200]}"); continue
        e = posts.get(m["id"], {})
        for c in comments:
            if c["id"] in done or c.get("username") == myname:
                continue
            user = c.get("username", "")
            j = judge(c.get("text", ""), e)
            if j is None:
                pub = random.choice(PUBLIC_OTHER)
            elif j[0] == "sim":
                msg = "¡Pleno! 🎯" if j[1] == j[2] else ("¡Muy bien! 💪" if j[1] >= j[2] - 1 else "¡A seguir practicando! 💪")
                pub = PUBLIC_SIM.format(ok=j[1], n=j[2], msg=msg)
            else:
                pub = random.choice(PUBLIC_CORRECT if j[1] else PUBLIC_WRONG)
            last_dm = handled["dm"].get(user)
            can_dm = not last_dm or (now - datetime.datetime.fromisoformat(last_dm)).days >= 7
            print(f"@{user}: {c.get('text', '')[:80]!r} -> {j} dm={can_dm and SEND_DMS}")
            if not DRY:
                try:
                    _check(requests.post(f"{GRAPH}/{c['id']}/replies", data={"message": pub, "access_token": TOKEN}))
                    sent_pub += 1
                except Exception as ex:
                    print("  respuesta pública fallida:", ex); errors.append(f"respuesta: {str(ex)[:200]}")
                if can_dm and SEND_DMS:
                    try:
                        _check(requests.post(f"{GRAPH}/{uid}/messages", json={
                            "recipient": {"comment_id": c["id"]}, "message": {"text": DM_TEXT}},
                            headers={"Authorization": f"Bearer {TOKEN}"}))
                        handled["dm"][user] = now.isoformat(); sent_dm += 1
                    except Exception as ex:
                        print("  DM fallido:", ex)
            done.add(c["id"])
    handled["comments"] = sorted(done)[-5000:]
    if not DRY:
        json.dump(handled, open(HANDLED, "w"), indent=0)
    print(f"Respuestas públicas: {sent_pub}, DMs: {sent_dm}")
    report(sent_pub, sent_dm, errors)


def report(sent_pub, sent_dm, errors):
    hint = ""
    if errors:
        try:
            d = requests.get(f"{GRAPH}/debug_token", params={"input_token": TOKEN, "access_token": TOKEN}, timeout=30).json()["data"]
            need = {"instagram_manage_comments", "instagram_basic", "pages_read_engagement"}
            miss = need - set(d.get("scopes", []))
            hint = (f"Al token ({d.get('type')}) le faltan: {', '.join(sorted(miss))}. Genera de nuevo el token de página con ellos."
                    if miss else f"El token ({d.get('type')}) tiene los permisos de comentarios.")
        except Exception:
            pass
    lines = ["## Bot de comentarios", f"- Respuestas públicas: {sent_pub} · DMs: {sent_dm}"] + \
            [f"- Error: `{e}`" for e in errors[:5]] + ([f"- {hint}"] if hint else [])
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("\n".join(lines) + "\n")
    if errors and sent_pub == 0 and all("leer comentarios" in e for e in errors):
        raise SystemExit("No se pudo leer ningún comentario: mira el resumen")


if __name__ == "__main__":
    main()
