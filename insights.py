"""Resultados reales de Instagram de los reels publicados -> performance.json (con ellos aprenden el piloto automático,
los agentes y el revisor). Incluye visitas al perfil y seguidores cuando Instagram los da para ese post.

Collect real Instagram results for published reels -> performance.json (used by the reviewer to learn).

Needs the Page token to include the permission instagram_manage_insights. If it doesn't, this step just says so
and everything else keeps working.
"""
import datetime, json, os, requests

HERE = os.path.dirname(os.path.abspath(__file__))
PERF = os.path.join(HERE, "performance.json")
GRAPH = f"https://graph.facebook.com/{os.environ.get('IG_API_VERSION', 'v23.0')}"
LAST_ERROR = [""]
METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions", "ig_reels_avg_watch_time"]


EXTRA = ["profile_visits", "follows"]          # no siempre disponibles para Reels: se piden aparte y se ignoran si fallan


def _extra(media_id, token):
    out = {}
    for m in EXTRA:
        try:
            r = requests.get(f"{GRAPH}/{media_id}/insights", params={"metric": m, "access_token": token}, timeout=30)
            if r.status_code == 200:
                for d in r.json().get("data", []):
                    out[d["name"]] = (d.get("values") or [{}])[0].get("value")
        except Exception:
            pass
    return out


def _metrics(media_id, token):
    m = _metrics_base(media_id, token)
    m.update(_extra(media_id, token))
    return m


def _metrics_base(media_id, token):
    r = requests.get(f"{GRAPH}/{media_id}/insights", params={"metric": ",".join(METRICS), "access_token": token}, timeout=30)
    if r.status_code == 200:
        return {d["name"]: (d.get("values") or [{}])[0].get("value") for d in r.json().get("data", [])}
    try:
        e = r.json().get("error", {})
    except Exception:
        e = {}
    LAST_ERROR[0] = f"code {e.get('code')}: {str(e.get('message') or r.text)[:160]}"
    if e.get("code") in (10, 200) or (e.get("code") == 190):      # real permission / token problem
        raise PermissionError(LAST_ERROR[0])
    out = {}                                              # e.g. (#100) a metric not available -> ask one by one
    for m in METRICS:
        r = requests.get(f"{GRAPH}/{media_id}/insights", params={"metric": m, "access_token": token}, timeout=30)
        if r.status_code == 200:
            for d in r.json().get("data", []):
                out[d["name"]] = (d.get("values") or [{}])[0].get("value")
    if not out:
        raise PermissionError(LAST_ERROR[0])
    return out


def token_scopes(token):
    """Permissions really included in the token (asks Meta's debug_token about itself)."""
    try:
        r = requests.get(f"{GRAPH}/debug_token", params={"input_token": token, "access_token": token}, timeout=30)
        d = r.json().get("data", {})
        TOKEN_INFO["granular"] = {g.get("scope"): g.get("target_ids") for g in d.get("granular_scopes", [])}
        return d.get("scopes"), d.get("type")
    except Exception:
        return None, None


TOKEN_INFO = {}


def diagnose(token):
    """Explain WHY media insights fail: which accounts the permission was granted for + an account-level test."""
    from publish_ig import whoami
    me = whoami(token); uid = me["user_id"]; out = [f"IG account id {uid} (@{me.get('username')})"]
    targets = TOKEN_INFO.get("granular", {}).get("instagram_manage_insights")
    if targets is not None:
        out.append("insights permission granted for: " + (", ".join(targets) or "no accounts")
                   + (" -> OK, includes this account" if uid in targets else " -> MISSING this Instagram account"))
    r = requests.get(f"{GRAPH}/{uid}/insights", params={"metric": "reach", "period": "day", "access_token": token}, timeout=30)
    out.append("account-level insights test: " + ("OK" if r.status_code == 200 else
               f"code {r.json().get('error', {}).get('code')}: {r.json().get('error', {}).get('message', '')[:100]}"))
    return " | ".join(out)


def account_media(token, limit=200):
    """Posts straight from the account: [{id, permalink, timestamp, media_product_type}] (ids Instagram really uses)."""
    from publish_ig import whoami
    uid = whoami(token)["user_id"]
    out, url = [], f"{GRAPH}/{uid}/media"
    params = {"fields": "id,permalink,timestamp,media_product_type", "limit": 50, "access_token": token}
    while url and len(out) < limit:
        r = requests.get(url, params=params, timeout=30); j = r.json()
        if r.status_code != 200:
            LAST_ERROR[0] = f"media list code {j.get('error', {}).get('code')}: {j.get('error', {}).get('message', '')[:120]}"
            break
        out += j.get("data", [])
        url, params = j.get("paging", {}).get("next"), None
    return out


def _norm_link(u):
    return (u or "").split("?")[0].rstrip("/").replace("/reels/", "/reel/").replace("/p/", "/reel/").lower()


def update(days=120):
    """Stats are read for the posts that really exist on the account (the source of truth), then matched to our
    log (by link, else by publication time) to know which experiment produced each one."""
    token = os.environ.get("IG_TOKEN")
    if not token:
        return "insights: nothing to do"
    logs = []
    if os.path.exists(os.path.join(HERE, "log.jsonl")):
        for line in open(os.path.join(HERE, "log.jsonl")):
            try:
                e = json.loads(line)
                if e.get("media_id") or e.get("permalink"):
                    logs.append(e)
            except Exception:
                pass
    by_link = {_norm_link(e.get("permalink")): e for e in logs if e.get("permalink")}
    by_id = {e.get("media_id"): e for e in logs if e.get("media_id")}
    perf = json.load(open(PERF)) if os.path.exists(PERF) else {}
    posts = account_media(token)
    now = datetime.datetime.now(datetime.timezone.utc)
    full = public = matched = 0
    skip = {"bad date": 0, "too new": 0, "too old": 0}; dates = []; types = {}
    for p in posts:
        types[p.get("media_product_type")] = types.get(p.get("media_product_type"), 0) + 1
        try:
            ts = datetime.datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00"))
        except Exception:
            skip["bad date"] += 1; continue
        dates.append(ts.date().isoformat())
        age = (now - ts).total_seconds() / 86400
        if age < 0.5:
            skip["too new"] += 1; continue
        if age > days:
            skip["too old"] += 1; continue
        e = by_id.get(p["id"]) or by_link.get(_norm_link(p.get("permalink")))
        if e is None:                                   # match by publication time (same day, closest log entry)
            same = [x for x in logs if x.get("date") == ts.date().isoformat()]
            e = same[0] if len(same) == 1 else None
        if e is not None:
            matched += 1
        try:
            m = _metrics(p["id"], token); full += 1
        except PermissionError:
            r = requests.get(f"{GRAPH}/{p['id']}", params={"fields": "like_count,comments_count", "access_token": token}, timeout=30)
            m = r.json() if r.status_code == 200 else {}
            m.pop("id", None); public += 1
        except Exception as err:
            print("insights error", p["id"], str(err)[:150], flush=True); continue
        base = {k: (e or {}).get(k) for k in ("slot", "formato", "estilo", "series", "imagen", "voice_speed", "music", "temas", "hook", "guion",
                                              "review_score", "arms")}
        perf[p["id"]] = {**base, "date": ts.date().isoformat(), "permalink": p.get("permalink"),
                         "type": p.get("media_product_type"), **m}
    if full:   # once real stats work, drop old likes-only rows (old ids / different scale) to avoid double counting
        perf = {k: v for k, v in perf.items() if v.get("views") is not None or v.get("reach") is not None}
    json.dump(perf, open(PERF, "w"), indent=0)
    msg = (f"insights: {full} posts with full stats, {public} likes/comments only "
           f"({len(posts)} posts found on the account, {matched} matched to our experiments)")
    if not (full or public) and posts:
        msg += (f" || posts dated {min(dates) if dates else '?'} to {max(dates) if dates else '?'}, types {types}, "
                f"skipped {skip}, our log has {len(logs)} reels from {min((e.get('date') or '?') for e in logs) if logs else '-'}"
                f" to {max((e.get('date') or '?') for e in logs) if logs else '-'}")
    if public and not full:
        scopes, ttype = token_scopes(token)
        msg += f" - token {ttype} - Instagram said: {LAST_ERROR[0]}"
        try:
            msg += " || DIAGNOSIS: " + diagnose(token)
        except Exception as err:
            msg += f" || diagnosis failed: {str(err)[:100]}"
    return msg


# ------------------------------------------------------------------ TikTok y YouTube (analítica de Zernio)
PERF_Z = os.path.join(HERE, "performance_tiktok.json")
ZAPI = "https://zernio.com/api/v1"


def _num(a, *names):
    for n in names:
        v = (a or {}).get(n)
        if isinstance(v, (int, float)):
            return v
    return None


def _chuletas():
    try:
        return json.load(open(os.path.join(HERE, "chuletas.json")))
    except Exception:
        return []


def update_zernio(max_age=21, final_age=10):
    """Resultados de TikTok y YouTube Shorts de cada reel (GET /analytics?postId= de Zernio) -> performance_tiktok.json.
    Con ellos el piloto automático aprende también de TikTok, que es donde más crece la cuenta, y sigue aprendiendo
    aunque Instagram esté caído. Cada vídeo se relee una vez al día hasta los `final_age` días. Si el plan de Zernio no
    incluye analítica (HTTP 402) lo dice y no insiste hasta la semana siguiente."""
    key = os.environ.get("ZERNIO_API_KEY")
    if not key:
        return "tiktok: sin ZERNIO_API_KEY"
    perf = json.load(open(PERF_Z)) if os.path.exists(PERF_Z) else {}
    today = datetime.date.today()
    off = perf.get("_sin_acceso") or {}
    if off.get("fecha") and (today - datetime.date.fromisoformat(off["fecha"])).days < 7:
        return f"tiktok: Zernio sin analítica ({off.get('motivo', '')[:80]}); se vuelve a probar el {off['fecha']} + 7 días"
    rows = []
    p = os.path.join(HERE, "log.jsonl")
    for line in open(p) if os.path.exists(p) else []:
        try:
            e = json.loads(line)
            age = (today - datetime.date.fromisoformat(e["date"])).days
        except Exception:
            continue
        if not 1 <= age <= max_age:
            continue
        for plat, k in (("tiktok", "tiktok_video"), ("youtube", "youtube_short")):
            pid = str((e.get("publicado") or {}).get(k) or "")
            if not pid or pid.startswith("error") or pid == "ok":
                continue
            old = perf.get(pid) or {}
            if old.get("fecha") == str(today) or (old.get("views") is not None and old.get("edad", 0) >= final_age):
                continue
            rows.append((pid, plat, e, age))
    for c in _chuletas():                                  # carruseles de TikTok (chuletas)
        try:
            age = (today - datetime.date.fromisoformat(c["fecha"])).days
        except Exception:
            continue
        pid = str((c.get("destinos") or {}).get("tiktok") or "")
        if not 1 <= age <= max_age or not pid or pid.startswith("error") or pid == "ok":
            continue
        old = perf.get(pid) or {}
        if old.get("fecha") == str(today) or (old.get("views") is not None and old.get("edad", 0) >= final_age):
            continue
        rows.append((pid, "tiktok", {"date": c["fecha"], "slot": str(c.get("slot")), "formato": "chuleta", "hook": c.get("subtema"),
                                     "tema": c.get("tema")}, age))
    rows.sort(key=lambda x: x[3])                          # los más recientes primero (son los que cambian)
    got = pending = 0
    hdr = {"Authorization": f"Bearer {key}"}
    import time
    t0 = time.time()
    for pid, plat, e, age in rows[:120]:
        if time.time() - t0 > 120:                         # tope de tiempo: nunca retrasa el reel
            break
        try:
            r = requests.get(f"{ZAPI}/analytics", params={"postId": pid}, headers=hdr, timeout=20)
        except Exception as ex:
            print("tiktok: fallo de red:", str(ex)[:120], flush=True); break
        if r.status_code == 402 or (r.status_code == 403 and "addon" in r.text.lower()):
            perf["_sin_acceso"] = {"fecha": str(today), "motivo": r.text[:200]}
            json.dump(perf, open(PERF_Z, "w"), ensure_ascii=False, indent=0)
            return ("tiktok: el plan de Zernio no incluye la analítica (complemento Analytics); sin ella el piloto automático "
                    "solo aprende de Instagram")
        if r.status_code == 429:
            break
        if r.status_code == 202:
            pending += 1; continue
        if r.status_code != 200:
            print(f"tiktok: analítica de {pid} -> {r.status_code}: {r.text[:120]}", flush=True); continue
        try:
            j = r.json()
        except Exception:
            continue
        a = j.get("analytics") or {}
        pa = next((x for x in (j.get("platformAnalytics") or []) if (x.get("platform") or "").lower() == plat), None) or {}
        if pa.get("analytics"):
            a = {**a, **{k: v for k, v in pa["analytics"].items() if v is not None}}
        views = _num(a, "views", "impressions", "reach")
        if views is None:
            pending += 1; continue
        perf[pid] = {"red": plat, "date": e.get("date"), "slot": e.get("slot"), "formato": e.get("formato"), "estilo": e.get("estilo"),
                     "hook": e.get("hook"), "guion": e.get("guion"), "arms": e.get("arms"), "duration": e.get("duration"),
                     "tema": e.get("tema") or (e.get("temas") or [None])[0],
                     "views": views, "likes": _num(a, "likes") or 0, "comments": _num(a, "comments") or 0,
                     "shares": _num(a, "shares") or 0, "saved": _num(a, "saves", "saved") or 0,
                     "url": pa.get("platformPostUrl"), "edad": age, "fecha": str(today)}
        got += 1
    perf.pop("_sin_acceso", None)
    json.dump(perf, open(PERF_Z, "w"), ensure_ascii=False, indent=0)
    tk = [v for k, v in perf.items() if isinstance(v, dict) and v.get("red") == "tiktok" and v.get("views") is not None]
    avg = round(sum(v["views"] for v in tk) / len(tk)) if tk else 0
    return (f"tiktok/youtube: {got} vídeos actualizados hoy ({pending} aún sin datos) · {len(tk)} vídeos de TikTok con métricas, "
            f"media {avg} visualizaciones")


if __name__ == "__main__":
    print(update())
    print(update_zernio())


def recent_comments(days=14, per_post=50):
    """Anonymous comment texts of recent posts (usernames are never stored). Needs instagram_manage_comments."""
    token = os.environ.get("IG_TOKEN")
    if not token:
        return []
    from publish_ig import whoami
    me = whoami(token).get("username")
    perf = json.load(open(PERF)) if os.path.exists(PERF) else {}
    now = datetime.datetime.now(datetime.timezone.utc); out = []
    for p in account_media(token, limit=60):
        try:
            ts = datetime.datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00"))
        except Exception:
            continue
        if (now - ts).days > days:
            continue
        r = requests.get(f"{GRAPH}/{p['id']}/comments", params={"fields": "text,username,like_count", "limit": per_post,
                                                                "access_token": token}, timeout=30)
        if r.status_code != 200:
            continue
        for c in r.json().get("data", []):
            if c.get("username") == me or not c.get("text"):
                continue
            out.append({"text": c["text"], "likes": c.get("like_count", 0), "story": (perf.get(p["id"]) or {}).get("hook")})
    return out
