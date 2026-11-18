"""Un hueco de publicación de Aprueba TCAE.

    python run_daily.py <mediodia|noche|manual> [--dry-run]

Tres noches por semana (variable EXPLICA_DIAS, por defecto martes, jueves y domingo) el reel de las 21:30 es un vídeo
"EXPLICADO" (explica.py: divulgación animada con ilustraciones de neón). Si ese día no sale uno verificado, se publica
el reel tipo test de siempre.

Cada ejecución:
 1. lee los resultados reales de Instagram (insights) y los agentes reescriben sus cuadernos (1 vez al día);
 2. el piloto automático elige el experimento de hoy (formato, estilo de gancho, bloque del temario, tiempo para pensar);
 3. elige pregunta(s) del banco SIN repetir y solo verificadas (verificando al momento las que hagan falta);
 4. guionista -> revisor de gancho -> verificador del guion -> render -> director de arte -> control de calidad del vídeo
    -> descripción final;
 5. publica el Reel en Instagram (+ Story recortada a 59 s) y, si hay Zernio, en TikTok y YouTube Shorts.
Si un formato no puede salir (sin preguntas verificadas, guion rechazado, Gemini caído...), prueba el siguiente formato
de la cadena, así que siempre sale algo correcto o no sale nada (nunca algo sin verificar).
"""
import datetime, json, os, random, sys, traceback

import questions as QB

slot = sys.argv[1] if len(sys.argv) > 1 else "manual"
dry = "--dry-run" in sys.argv or os.environ.get("DRY_RUN") == "true"
now = datetime.datetime.utcnow()
today = now.date()
seed = today.toordinal() * 24 + now.hour
os.makedirs("out", exist_ok=True)
HAS_AI = bool(os.environ.get("GEMINI_API_KEY"))

locs = [l for l in json.load(open("locations.json")) if l.get("id")] if os.path.exists("locations.json") else []
loc = random.Random(f"{now:%Y-%m-%d-%H}-{slot}-loc").choice(locs) if locs else None


def log(entry):
    with open("log.jsonl", "a") as f:
        f.write(json.dumps({"date": str(today), "slot": slot, **entry}, ensure_ascii=False) + "\n")


def recent_hooks(n=14):
    out = []
    try:
        for line in open("log.jsonl"):
            h = json.loads(line).get("hook")
            if h: out.append(h)
    except Exception:
        pass
    return out[-n:]


def already_published():
    """Evita publicar dos veces el mismo hueco (el workflow se despierta muchas veces al día)."""
    try:
        import hueco
        return hueco.done_today("reel", slot, str(today), hueco.window("reel", slot)[1] if slot in hueco.TARGETS["reel"] else None)
    except Exception:
        return False


def wait_until_slot():
    """El workflow arranca ~30 min antes; si el reel está listo antes de la hora, espera (máx. PUBLISH_MAX_WAIT_MIN)."""
    target = {"manana": (8, 0), "mediodia": (14, 30), "noche": (21, 30)}.get(slot)
    if not target:
        return
    try:
        from zoneinfo import ZoneInfo
        import time
        now_l = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
        goal = now_l.replace(hour=target[0], minute=target[1], second=0, microsecond=0)
        secs = (goal - now_l).total_seconds()
        if 0 < secs <= float(os.environ.get("PUBLISH_MAX_WAIT_MIN") or "0") * 60:
            print(f"esperando {secs / 60:.1f} min para publicar a las {target[0]}:{target[1]:02d}", flush=True)
            time.sleep(secs)
    except Exception:
        pass


if slot in ("manana", "mediodia", "noche") and not dry and already_published() and os.environ.get("FORCE") != "true":
    print(f"El hueco {slot} de hoy ya está publicado; no se repite")
    sys.exit(0)

status = []
if not HAS_AI:                                     # sin Gemini no hay verificador: nunca se publica nada sin verificar
    msg = ("Falta el secreto GEMINI_API_KEY (Settings → Secrets and variables → Actions → Secrets, nombre exacto "
           "GEMINI_API_KEY). Sin él no se puede verificar ninguna pregunta y no se publica nada.")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(f"## ❌ {msg}\n")
    if not (os.environ.get("QUIZ_MOCK") == "1" and QB.verif()):
        raise SystemExit(msg)
if HAS_AI:
    for name, fn in (("insights", lambda: __import__("insights").update()),
                     ("tiktok", lambda: __import__("insights").update_zernio()),
                     ("agentes", lambda: __import__("agents").daily_learning())):
        try:
            msg = fn()
        except Exception as e:
            msg = f"{name} omitido: {str(e)[:150]}"
        print(msg, flush=True); status.append(msg)

# ---- serie del día (hueco de mediodía) + experimento del piloto automático
arms, strat_msg, series_info = {}, "", None
override = os.environ.get("FORMAT_OVERRIDE", "auto")
style_override = os.environ.get("STYLE_OVERRIDE", "auto")
try:
    import strategy
    fixed = {"formato": override} if override in strategy.DEFAULT_ARMS["formato"] else {}
    if slot == "mediodia" and not fixed:
        import estudio
        series_info = estudio.series_today(today)
        fixed["formato"] = series_info["series_fmt"]          # cita fija del día: la gente sabe qué toca
    if style_override in strategy.DEFAULT_ARMS["estilo"]:
        fixed["estilo"] = style_override
    arms = strategy.choose(seed=f"{now:%Y-%m-%d-%H}-{slot}", fixed=fixed)
    if HAS_AI and slot == "mediodia":
        strat_msg = strategy.weekly_strategist()
    strategy.write_report()
    print("experimento:", {k: strategy.short(v) for k, v in arms.items()}, "|", strat_msg, flush=True)
except Exception as e:
    strat_msg = f"estrategia omitida: {str(e)[:150]}"; print(strat_msg, flush=True)
if HAS_AI:
    try:
        import estudio
        m = estudio.daily_learning(); print(m, flush=True); status.append(m)
    except Exception as e:
        status.append(f"estudio omitido: {str(e)[:120]}")
    try:                                           # agente cazatendencias: actualidad del día (una búsqueda al día)
        import tendencias
        m = tendencias.run(); print(m, flush=True); status.append(m)
    except Exception as e:
        status.append(f"cazatendencias omitido: {str(e)[:120]}")

chain = list(dict.fromkeys([arms.get("formato", "pregunta_del_dia"), "pregunta_del_dia", "examen_real", "simulacro_3"]))
out = f"out/{today}_{slot}_{now.hour:02d}.mp4"


def explica_today():
    """¿Toca vídeo explicado? A mano (formato=explicado) o las noches de EXPLICA_DIAS (0 = lunes ... 6 = domingo)."""
    if override == "explicado":
        return True
    if override != "auto" or slot != "noche":
        return False
    try:
        from zoneinfo import ZoneInfo
        wd = datetime.datetime.now(ZoneInfo("Europe/Madrid")).weekday()
    except Exception:
        wd = today.weekday()
    return str(wd) in [d.strip() for d in os.environ.get("EXPLICA_DIAS", "1,3,6").split(",")]


verify_fn = verify_f = None
if HAS_AI:
    import verifier
    verify_fn, verify_f = verifier.verify_questions, verifier.verify_fichas
STYLE_KEYS = ("follow_line", "share_line", "save_line", "reto_line", "series", "voice_speed", "music")

meta, items, S, errors, src, image = None, None, None, [], None, None
if explica_today() and (HAS_AI or os.environ.get("QUIZ_MOCK") == "1"):
    try:
        import explica
        meta, S, caption = explica.make(out, seed)
        items, src, review = [], "ia", {}
        if HAS_AI:
            import reviewer
            _, review = reviewer.review_video(out, S, caption)    # RejectReel -> reel tipo test. La descripción no se
            # toca: ya está verificada frase a frase y el revisor podría colar una promesa ("siempre cae")
        meta.update(review_score=review.get("overall"), design_score=None, guion=src, series="Explicado",
                    imagen=bool(meta.get("ilustraciones")), concepto=meta.get("subtema"), yt_title=S.get("yt_title"))
        arms = {"formato": explica.FMT, "estilo": meta["estilo"]}
    except Exception as e:
        meta = None
        errors.append(f"explicado: {str(e)[:300]}")
        print(f"[explicado] no ha podido salir, sale el reel tipo test:\n{traceback.format_exc()[-1500:]}", flush=True)
for fmt in ([] if meta else chain):
    try:
        if fmt == "flashcards_express":
            items = QB.pick_fichas(seed=f"{seed}-{fmt}", verify=verify_f)
        else:
            n = 3 if fmt == "simulacro_3" else 1
            qs = QB.pick(fmt, arms.get("bloque"), seed=f"{seed}-{fmt}", n=n, verify=verify_fn)
            items = [QB.prepare(q, seed) for q in qs]
        si = series_info if (series_info and fmt == series_info["series_fmt"]) else None
        import writer
        S, fmt, src = writer.script_for(fmt, items, arms, avoid=recent_hooks(), verify=HAS_AI, series_info=si)
        import make_quiz
        S["_fmt"] = fmt                                 # el revisor del vídeo sabe qué diseño tiene (reto o con solución)
        style = dict(make_quiz.DEFAULT_STYLE)
        style.update({k: S[k] for k in STYLE_KEYS if S.get(k)})
        image, dinfo = None, {}
        if HAS_AI and src == "ia":
            import agents, estudio
            style.update({k: v for k, v in agents.growth_lines(S, fmt).items() if not S.get(k)})
            image, dinfo = estudio.imagen_para(fmt, items, arms.get("estilo", "clasico"), S, out[:-4])
        meta = make_quiz.build(fmt, items, S, seed, out, arms, style, image=image, estilo=arms.get("estilo"))
        caption = open(out.replace(".mp4", ".txt")).read()
        review, art = {}, {}
        if HAS_AI:
            import reviewer, agents
            new_style, art = reviewer.art_direct(out, S, style, meta["timeline"], meta["duration"])
            if new_style:
                print("director de arte: vuelvo a renderizar con", {k: v for k, v in new_style.items() if style.get(k) != v}, flush=True)
                style = new_style
                meta = make_quiz.build(fmt, items, S, seed, out, arms, style, keep_voice=True, image=image,
                                       estilo=arms.get("estilo"))                  # voz en caché: no se regraba
                caption = open(out.replace(".mp4", ".txt")).read()
            caption, review = reviewer.review_video(out, S, caption)              # RejectReel -> siguiente formato
            caption = agents.growth_caption(caption, S, review)
            open(out.replace(".mp4", ".txt"), "w").write(caption)
        meta.update(review_score=review.get("overall"), design_score=art.get("overall"), guion=src,
                    series=si and si["series_name"], imagen=image is not None, concepto=dinfo.get("concepto"),
                    voice_speed=style.get("voice_speed"), music=style.get("music"), yt_title=S.get("yt_title"))
        arms["formato"] = fmt
        arms["estilo"] = meta["estilo"]
        break
    except Exception as e:
        meta = None
        errors.append(f"{fmt}: {str(e)[:300]}")
        print(f"[{fmt}] no ha podido salir, pruebo el siguiente formato:\n{traceback.format_exc()[-1500:]}", flush=True)

story_mp4 = None
if meta and slot != "manana":                      # a las 8:00 la story de Instagram es el propio reel
    try:                                           # story de 12 s para Instagram y TikTok
        import story
        story_mp4 = story.build(meta["story_base"], out.replace(".mp4", "_story.mp4"), meta["formato"])
    except Exception as e:
        print("story no generada:", str(e)[:200], flush=True)

summary = os.environ.get("GITHUB_STEP_SUMMARY")
try:
    import voice as _v
    voice_used = _v.ENGINE_USED
except Exception:
    voice_used = None
if summary:
    with open(summary, "a") as f:
        if meta:
            f.write(f"## ✅ Reel listo: {meta['formato']} · estilo {meta['estilo']}" + (f" · {meta['series']}" if meta.get("series") else "")
                    + (" · con ilustración" if meta.get("imagen") else "") + "\n\n"
                    f"- Hueco: `{slot}` · voz: `{voice_used}` · guion: `{src}` · duración {meta['duration']} s\n"
                    f"- Gancho: **{meta['hook']}**\n- Tema(s): {', '.join(meta['temas'])} · respuesta(s): {', '.join(meta['respuestas'])}\n"
                    + (f"- Revisor: {meta.get('review_score')}/10 · Director de arte: {meta.get('design_score')}/10\n")
                    + (f"- Experimento: {', '.join(f'{k}={str(v).split(chr(58))[0]}' for k, v in arms.items())}\n" if arms else ""))
        else:
            f.write("## ❌ Hoy no sale reel (nada pasó la verificación)\n\n")
        f.write("".join(f"- {m}\n" for m in status + ([strat_msg] if strat_msg else []))
                + "".join(f"- Error: `{e}`\n" for e in errors))
if meta is None:
    raise SystemExit("Ningún formato pudo generar un reel verificado")

caption = open(out.replace(".mp4", ".txt")).read()
print(caption)
if dry:
    try:                                           # muestra ligera en el repositorio (carpeta muestras/) para revisarla
        import subprocess
        import explica as _ex
        os.makedirs("muestras", exist_ok=True)
        _ex.contact_sheet(out, "muestras/ultima_prueba.jpg", 8, 5)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-vf", "scale=540:960", "-c:v", "libx264", "-preset",
                        "veryfast", "-crf", "28", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart",
                        "muestras/ultima_prueba.mp4"], check=True)
        open("muestras/ultima_prueba.txt", "w").write(f"{meta['formato']} · {meta['duration']} s · {meta['hook']}\n\n{caption}\n\n"
                                                      + json.dumps((S or {}).get("guion") or {}, ensure_ascii=False, indent=1))
    except Exception as e:
        print("muestra no guardada:", str(e)[:200], flush=True)
    print("PRUEBA: no se publica")
    sys.exit(0)

import publish_all
if loc: print("Ubicación:", loc["name"])
wait_until_slot()                                  # publica a la hora exacta del hueco (14:30 / 21:30 en España)
results = publish_all.publish(out, story_mp4, meta.get("slides") or [], caption, meta, location_id=loc and loc["id"], slot=slot)
meta.update(location=loc and loc["name"], publicado=results)
print("publicado:", json.dumps(results, ensure_ascii=False), flush=True)
if any(not str(v).startswith("error") for v in results.values()):
    QB.mark_used(items, meta["formato"])
    if meta["formato"] == "explicado":
        import explica
        explica.mark_published(meta)
if summary:
    with open(summary, "a") as f:
        f.write("\n### Publicación\n" + "".join(f"- {'✅' if not str(v).startswith('error') else '❌'} {k}: {v}\n"
                                                  for k, v in results.items()))
meta["voice"] = voice_used
meta["ts"] = datetime.datetime.utcnow().isoformat(timespec="seconds")      # hora de publicación (respuestas en 24 h)
meta["arms"] = arms
if meta.get("soluciones") and any(not str(v).startswith("error") for v in results.values()):
    import shutil                                  # la solución se publica mañana (soluciones.py): se guarda en el repo
    os.makedirs("soluciones", exist_ok=True)
    kept = []
    for i, pth in enumerate(meta["soluciones"]):
        dst = f"soluciones/{today}_{slot}_{now:%H%M}_{i + 1}.jpg"        # nombre único aunque haya 2 reels manuales
        shutil.copy(pth, dst); kept.append(dst)
    meta["soluciones"] = kept
log({k: meta.get(k) for k in ("formato", "estilo", "series", "imagen", "concepto", "voice_speed", "music", "ids", "temas", "respuestas", "veredicto", "hook", "hook_line", "duration", "guion",
                              "voice", "review_score", "design_score", "arms", "location", "permalink", "media_id",
                              "publicado", "soluciones", "solucion_texto", "ts", "topic", "subtema", "ilustraciones")})
alerta = False
try:                                               # si una red falla por un problema de cuenta, abre una incidencia
    import avisos
    alerta = avisos.revisar(results, f"reel de {slot} ({today})")
except Exception as e:
    print("avisos omitidos:", str(e)[:150], flush=True)
if all(str(v).startswith("error") for v in results.values()):
    raise SystemExit("No se pudo publicar en ninguna red")
if alerta:
    raise SystemExit("Publicado, pero una red falla por un problema de cuenta: mira la incidencia abierta en GitHub (Issues)")
