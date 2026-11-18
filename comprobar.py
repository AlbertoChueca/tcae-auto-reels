"""Chequeo de salud (workflow "Comprobar conexiones", cada lunes y a mano): ¿está todo listo para publicar?

Revisa tokens y cuentas (Instagram, Zernio/TikTok/YouTube, Gemini), el banco (preguntas y fichas publicables, días de
reserva), las fuentes legales y cómo fueron las publicaciones de la última semana. Escribe estado.md y, si algo crítico
falla, termina con error para que GitHub te avise por correo.
"""
import datetime, json, os, sys

import questions as QB

rows, critical = [], []
redes = {}                                         # estado de cada red para avisos.py (incidencia en GitHub si falla)


def ok(name, good, detail, crit=False):
    rows.append(f"| {'✅' if good else ('❌' if crit else '⚠️')} {name} | {detail} |")
    if not good and crit:
        critical.append(name)


# ---- Instagram
tok = os.environ.get("IG_TOKEN")
if tok:
    try:
        from publish_ig import whoami
        import insights
        me = whoami(tok)
        scopes, ttype = insights.token_scopes(tok)
        need = {"instagram_basic", "instagram_content_publish", "instagram_manage_insights", "instagram_manage_comments"}
        miss = need - set(scopes or [])
        ok("Instagram", not miss, f"@{me['username']} · token {ttype}" + (f" · faltan permisos: {', '.join(sorted(miss))}" if miss else ""), True)
        redes["instagram"] = "ok"
    except Exception as e:
        ok("Instagram", False, f"token no válido: {str(e)[:150]}", True)
        redes["instagram"] = f"error: token no válido: {str(e)[:300]}"
else:
    ok("Instagram", False, "falta el secreto IG_TOKEN", True)

# ---- Zernio (TikTok + YouTube)
if os.environ.get("ZERNIO_API_KEY"):
    try:
        import publish_zernio as Z
        acc = Z.accounts()
        ok("TikTok (Zernio)", "tiktok" in acc, "conectada" if "tiktok" in acc else "conecta la cuenta de TikTok en Zernio")
        ok("YouTube (Zernio)", "youtube" in acc, "conectado" if "youtube" in acc else "conecta el canal de YouTube en Zernio")
        redes["tiktok"] = "ok" if "tiktok" in acc else "error: no hay cuenta de TikTok conectada en Zernio"
        redes["youtube"] = "ok" if "youtube" in acc else "error: no hay canal de YouTube conectado en Zernio"
        try:                                       # ¿el plan de Zernio da métricas? (con ellas el piloto aprende de TikTok)
            import requests
            pid = None
            for line in open("log.jsonl"):
                v = str((json.loads(line).get("publicado") or {}).get("tiktok_video") or "")
                if v and not v.startswith("error"):
                    pid = v
            r = requests.get(f"{Z.API}/analytics", params={"postId": pid}, headers=Z._h(), timeout=40)
            det = f"HTTP {r.status_code}"
            if r.status_code == 200:
                j = r.json(); a = j.get("analytics") or {}
                det += " · último vídeo de TikTok: " + ", ".join(f"{k} {a.get(k)}" for k in ("views", "likes", "comments", "shares", "saves") if k in a)
                det += f" · campos: {sorted(j)[:14]}"
            else:
                det += f" · {r.text[:160]}"
            ok("Métricas de TikTok (Zernio)", r.status_code in (200, 202), det)
        except Exception as e:
            ok("Métricas de TikTok (Zernio)", False, str(e)[:150])
    except Exception as e:
        ok("Zernio", False, f"error: {str(e)[:150]}")
else:
    ok("Zernio", False, "sin ZERNIO_API_KEY: no se publica en TikTok ni YouTube")

# ---- Gemini
if os.environ.get("GEMINI_API_KEY"):
    try:
        import gemini
        av = gemini.available()
        tts = [m for m in av if "tts" in m]; img = [m for m in av if "image" in m]
        gemini.ask('Devuelve JSON {"ok": true}', 0)
        ok("Gemini texto", True, f"{len(av)} modelos disponibles")
        ok("Gemini voz", bool(tts), ", ".join(tts[:3]) or "sin modelos TTS: se usará la voz de respaldo")
        ok("Gemini imagen", bool(img), ", ".join(img[:3]) or "sin modelos de imagen: reels sin ilustración")
    except Exception as e:
        ok("Gemini", False, f"error: {str(e)[:150]}", True)
else:
    ok("Gemini", False, "falta GEMINI_API_KEY (sin ella no se verifica nada y no se publica)", True)

# ---- banco
qs = QB.load(); v = QB.verif(); done = {x["id"] for x in QB.used()}
pub = [q for q in qs if QB.publishable(q, v)]
fresh = [q for q in pub if q["id"] not in done]
by = {}
for q in fresh:
    by[q["bloque"]] = by.get(q["bloque"], 0) + 1
ok("Banco verificado", len(fresh) >= 30, f"{len(fresh)} preguntas publicables sin usar ({', '.join(f'{k} {n}' for k, n in sorted(by.items()))}) "
   f"de {len(qs)} · ~{len(fresh) // 2} días de reserva", len(fresh) < 4)
vf = QB.verif_f()
ok("Fichas verificadas", sum(1 for r in vf.values() if r.get("veredicto") == "ok") >= 8,
   f"{sum(1 for r in vf.values() if r.get('veredicto') == 'ok')} fichas aprobadas")
import marca
anunciadas = marca.preguntas_num()
ok("Cifra anunciada", anunciadas <= len(qs) * 1.05 or anunciadas == 0,
   f"los reels dicen '{marca.PREGUNTAS_FRASE}' y el banco importado tiene {len(qs)}"
   + ("" if anunciadas <= len(qs) * 1.05 else " · sube a webapp/ el index.html actual de la app o ajusta la variable APP_PREGUNTAS"))
leg = by.get("legislacion", 0)
ok("Legislación", leg > 0, f"{leg} preguntas de legislación con cita verificada" + ("" if leg else " · lanza 'Descargar fuentes' y 'Verificar banco'"))
try:
    cfg = json.load(open("fuentes/fuentes.json"))["normas"]
    have = [k for k, n in cfg.items() if os.path.exists(os.path.join("fuentes", n["archivo"]))]
    falt = [n["titulo"] for k, n in cfg.items() if k not in have]
    ok("Fuentes legales", not falt, f"{len(have)}/{len(cfg)} normas" + (f" · faltan: {'; '.join(falt[:4])}" if falt else ""))
except Exception as e:
    ok("Fuentes legales", False, str(e)[:100])

# ---- última semana
week = str(datetime.date.today() - datetime.timedelta(days=7))
stats = {}
try:
    for line in open("log.jsonl"):
        e = json.loads(line)
        if e.get("date", "") >= week:
            for k, r in (e.get("publicado") or {}).items():
                stats.setdefault(k, [0, 0])[0 if not str(r).startswith("error") else 1] += 1
except Exception:
    pass
ok("Publicaciones (7 días)", bool(stats) and all(b == 0 for _, b in stats.values()),
   " · ".join(f"{k}: {a} ok / {b} fallos" for k, (a, b) in stats.items()) or "aún no hay publicaciones")

txt = f"# Estado ({datetime.date.today()})\n\n| comprobación | detalle |\n|---|---|\n" + "\n".join(rows) + "\n"
open("estado.md", "w").write(txt); print(txt)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(txt)
try:
    import avisos
    avisos.revisar(redes, "comprobación de conexiones")
except Exception as e:
    print("avisos omitidos:", str(e)[:150])
if critical:
    sys.exit("Problemas críticos: " + ", ".join(critical))
