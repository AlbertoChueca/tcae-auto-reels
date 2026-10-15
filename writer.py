"""Guionista: escribe los textos del reel (gancho, revelado, explicación, trampa, truco, mito, puntos clave, CTA) a
partir SOLO de la pregunta del banco, su explicación, las fichas de la app y la fuente verificada.

Los textos del enunciado y las opciones NUNCA los reescribe la IA: salen tal cual del banco.
Sin GEMINI_API_KEY (o si falla) se usa template(): textos fijos + la explicación de la propia app, sin nada inventado.
"""
import json, os, re

import questions as QB

FORMATS = {
    "pregunta_del_dia": "Pregunta del día",
    "error_tipico": "Error típico en el examen",
    "truco_memorizar": "Truco para memorizar",
    "mito_realidad": "Mito o realidad",
    "simulacro_3": "Simulacro rápido",
    "legislacion_30s": "Legislación en 30 segundos",
    "examen_real": "Cayó en el examen",
    "caso_practico": "Caso práctico de turno",
    "flashcards_express": "Repaso exprés con 4 fichas",
}
AUDIENCE = """PÚBLICO: personas adultas que preparan las oposiciones de TCAE (Técnico en Cuidados Auxiliares de Enfermería)
en cualquier comunidad de España (SAS, SERMAS, SALUD, SCS, Osakidetza...); muchas trabajan y estudian a la vez. Habla
para TODA España: no menciones ninguna comunidad concreta salvo que la pregunta sea de su temario específico. Registro:
cercano, motivador, profesional; nada infantil, nada de "chicos", sin exageraciones ni promesas ("esto cae seguro", "aprobarás"), sin
estadísticas inventadas ("el 90% falla"). Español de España (vosotros/tú, "oposición", "temario", "plaza")."""

SCHEMAS = {
    "pregunta_del_dia": '"explicacion": str (18-38 palabras: por qué es la correcta)',
    "examen_real": '"explicacion": str (12-34 palabras: por qué es la correcta; si no hay fuente verificada, di solo que es la respuesta de la plantilla provisional del tribunal y el motivo que dé el material)',
    "error_tipico": '"trampa": "A"|"B"|"C"|"D" (la opción INCORRECTA más tentadora), "trampa_porque": str (16-34 palabras: por qué engaña esa opción y por qué la buena es la otra)',
    "truco_memorizar": '"truco": str (3-12 palabras, regla mnemotécnica o asociación fácil, solo con datos del material), "truco_line": str (10-26 palabras, la voz explica el truco)',
    "caso_practico": '"escena": str (14-34 palabras, segunda persona y presente: situación de turno de una TCAE que lleva a la pregunta; SOLO ambientación, sin datos clínicos, cifras ni normas, sin revelar la respuesta), "escena_visual": str (máx. 40 palabras, la imagen de esa escena, sin texto), "explicacion": str (18-38 palabras: por qué es la correcta)',
    "flashcards_express": '"cierre_line": str (6-16 palabras, pregunta cuántas fichas sabía e invita a comentarlo y guardar el reel)',
    "mito_realidad": '"afirmacion": str (8-24 palabras, una frase afirmativa sacada de la pregunta: o la respuesta correcta reformulada (REALIDAD) o una opción incorrecta reformulada (MITO)), "veredicto": "MITO"|"REALIDAD", "explicacion": str (14-34 palabras)',
    "legislacion_30s": '"titulo_norma": str (2-8 palabras), "puntos": [str, str, str] (3 ideas clave de 5-14 palabras cada una, SOLO con datos de la cita de la fuente, la explicación o las fichas)',
    "simulacro_3": '"cierre_line": str (6-16 palabras, invita a comentar cuántas ha acertado, p. ej. 3/3)',
}


def _brief(name):
    try:
        import agents
        return agents._brief(name)
    except Exception:
        return ""


def _material(items):
    if "pregunta" not in items[0]:                     # fichas de la app (flashcards_express)
        return f"FICHAS DE LA APP · tema: {items[0]['tema']}\n" + "\n".join(f"- {f['q']} -> {f['a']}" for f in items)
    v = QB.verif(); out = []
    for i, P in enumerate(items, 1):
        r = v.get(P["id"], {})
        fs = QB.fichas(P["topic"], 3, words=re.findall(r"\w+", P["pregunta"].lower()))
        out.append(f"PREGUNTA {i} · tema: {P['tema']}" + (f" · EXAMEN OFICIAL {P['examen']['titulo']}" if P.get("examen") else "")
                   + f"\n{P['pregunta']}\n" + "\n".join(f"{QB.LETTERS[k]}) {o}" for k, o in enumerate(P["op"]))
                   + f"\nCORRECTA: {P['letra']}\nExplicación de la app: {P.get('explicacion')}\n"
                   + ("Fichas de la app: " + " | ".join(f"{f['q']} -> {f['a']}" for f in fs) + "\n" if fs else "")
                   + (f"Fuente verificada ({r['referencia']}): \"{r['cita']}\"\n" if r.get("fuente_ok") else ""))
    return "\n".join(out)


def write(fmt, items, arms=None, avoid=(), notes=None):
    """Guion JSON del reel (Gemini). notes = problemas que encontró el verificador en un intento anterior."""
    import gemini
    arms = arms or {}
    pb = ""
    try:
        import strategy
        pb = strategy.playbook_text()
    except Exception:
        pass
    prompt = f"""Eres el GUIONISTA de los reels de Aprueba TCAE (Instagram, TikTok, YouTube Shorts), una web app gratuita de
tests para las oposiciones de TCAE de toda España (apruebatcae.com).
{AUDIENCE}

{_brief('guion')}
{_brief('gancho')}
{("LO QUE FUNCIONA CON NUESTRA AUDIENCIA (datos reales):" + chr(10) + pb) if pb else ""}

FORMATO DE HOY: {FORMATS[fmt]}. Estilo de gancho a probar (experimento): {arms.get('hook_style', 'el que mejor encaje')}.
MATERIAL (lo ÚNICO que puedes usar como dato; no añadas artículos, cifras, plazos ni nada que no esté aquí):
{_material(items)}

Escribe en español de España, frases cortas para decir en voz alta (máx. 14 palabras por frase), números en cifra.
Cada campo es EXACTAMENTE lo que se dice o se lee en pantalla: nunca escribas indicaciones de tono, de voz o de actuación
(nada de "tono amable", "como si fueras una compañera", "(sonriendo)", "Narradora:"), ni menciones a quién habla.
Campos:
- "screen_hook": texto GRANDE de los 2 primeros segundos (2-6 palabras, sin emojis): curiosidad o reto que frene el scroll.
- "hook_line": lo primero que dice la voz (5-14 palabras); no repitas literal el screen_hook.
- "reveal_line": la voz da la solución (3-12 palabras), p. ej. "La correcta es la {items[0].get('letra', 'B')}." (solo la letra: NO vuelvas a leer el texto de la opción) (en simulacro y fichas: una frase corta de transición).
- {SCHEMAS[fmt]}
- "cta_line": cierre hablado (8-20 palabras) que invite a practicar gratis en apruebatcae.com (puedes decir "link en la bio").
- "caption_hook": primera línea de la descripción (máx. 12 palabras, como mucho 1 emoji).
- "comment_prompt": invitación a comentar la respuesta (máx. 12 palabras), p. ej. "Comenta A, B, C o D antes de ver la solución".
No repitas ganchos recientes: {'; '.join(list(avoid)[-12:]) or 'ninguno'}.
{("CORRIGE ESTOS PROBLEMAS QUE ENCONTRÓ EL VERIFICADOR:" + chr(10) + json.dumps(notes, ensure_ascii=False)) if notes else ""}
Devuelve solo JSON con esos campos."""
    s = gemini.ask(prompt, 0.9)
    return clean(fmt, items, s)


# Indicaciones de actuación/registro que una IA puede colar en un texto que luego se LEE EN VOZ ALTA o sale en pantalla
# ("tono amable, como si fueras una compañera", "(con voz cálida)", "Narradora:"...). Nunca deben publicarse.
_ADJ = (r"(?:amable|cercan[oa]|c[aá]lid[oa]|alegre|did[aá]ctic[oa]|motivador[a]?|suave|segur[oa]|natural|neutr[oa]|"
        r"en[eé]rgic[oa]|c[oó]mplice|tranquil[oa]|firme|positiv[oa]|intrigante|rotund[oa]|claro|clara|amistos[oa]|"
        r"profesional|dulce|animad[oa]|emp[aá]tic[oa]|conversacional|informal|serio|seria)")
META = re.compile(r"\b(?:en )?(?:un )?tono " + _ADJ + r"|\btono de voz\b|como si fuer[ao]s?\b|como si (?:hablaras|estuvieras)\b|"
                  r"\bcomo una compañera (?:que|de)\b|\b(?:con )?(?:una )?voz " + _ADJ + r"|\bvoz en off\b|"
                  r"\bnarrador(?:a)?\b|\blocutor(?:a)?\b|\bentonaci[oó]n\b|\bacento (?:peninsular|espa[nñ]ol|de espa[nñ]a|neutro)\b|"
                  r"\bparagraph\b|\btranscript\b|\bdirector'?s notes\b|\bnotas de (?:direcci[oó]n|actuaci[oó]n)\b|"
                  r"\bdelivery\b|\b(?:warm|friendly|calm|energetic|clear) (?:tone|voice)\b|\bread (?:only|aloud)\b|"
                  r"\((?:[^)]*\b(?:voz|tono|sonr[ií]e|pausa|r[ií]e|susurr|enf[aá]tic)[^)]*)\)|\[[^\]]*\]|"
                  r"^\s*(?:narradora?|voz|locutora?|presentadora?)\s*:", re.I)
SPOKEN_KEYS = ("hook_line", "reveal_line", "cta_line", "explicacion", "trampa_porque", "truco_line", "afirmacion",
               "cierre_line", "escena", "puntos")


def has_meta(v):
    """True si el texto lleva indicaciones de tono/voz/escena en vez de solo lo que hay que decir o mostrar."""
    if isinstance(v, (list, tuple)):
        return any(has_meta(x) for x in v)
    return isinstance(v, str) and bool(META.search(v))


def strip_meta(fmt, items, s):
    """Última barrera: cualquier campo con indicaciones de actuación vuelve a la plantilla (o se elimina si es opcional)."""
    base = template(fmt, items)
    for k in list(s):
        if k in ("caption", "yt_title") or not has_meta(s[k]):
            continue
        if k in SPOKEN_KEYS and k not in base:
            raise ValueError(f"'{k}' lleva indicaciones de voz/tono")
        print(f"guion: quito indicaciones de voz/tono de '{k}': {str(s[k])[:80]!r}", flush=True)
        if k in base and not has_meta(base[k]):
            s[k] = base[k]
        else:
            s.pop(k)
    return s


def _w(v, lo, hi):
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    return v if lo <= len(v.split()) <= hi else None


def clean(fmt, items, s):
    """Valida longitudes y campos; lo que no cumple se sustituye por la plantilla segura."""
    base = template(fmt, items)
    out = dict(base)
    for k, lo, hi in (("screen_hook", 2, 6), ("hook_line", 4, 16), ("reveal_line", 2, 12), ("cta_line", 6, 22),
                      ("caption_hook", 3, 14), ("comment_prompt", 3, 14), ("explicacion", 10, 40),
                      ("trampa_porque", 12, 36), ("truco", 2, 12), ("truco_line", 8, 28), ("afirmacion", 6, 26),
                      ("titulo_norma", 1, 8), ("cierre_line", 5, 18)):
        val = _w(s.get(k), lo, hi)
        if val:
            out[k] = val
    out["screen_hook"] = re.sub(r"[^\w\s¿?¡!,.:'-]", "", out["screen_hook"]).strip()
    letra = items[0].get("letra")
    m = re.search(r"\b(?:la|opci[oó]n|respuesta)\s+([ABCD])\b", out["reveal_line"])
    if letra and fmt not in ("simulacro_3", "flashcards_express", "mito_realidad") and (not m or m.group(1) != letra):
        out["reveal_line"] = base["reveal_line"]              # la voz nunca puede decir una letra que no es la correcta
    if fmt not in ("simulacro_3", "flashcards_express", "mito_realidad") and items[0].get("op"):
        ok_txt = re.findall(r"\w+", items[0]["op"][items[0]["ok"]].lower())
        rv = " ".join(re.findall(r"\w+", out["reveal_line"].lower()))
        if any(" ".join(ok_txt[i:i + 3]) in rv for i in range(max(1, len(ok_txt) - 2))) and len(ok_txt) >= 2:
            out["reveal_line"] = base["reveal_line"]          # no vuelve a leer la opción: ya se ve en verde en pantalla
    if "apruebatcae" not in out["cta_line"].lower().replace(" ", ""):
        out["cta_line"] = base["cta_line"]
    if fmt == "error_tipico":
        t = str(s.get("trampa") or "").strip().upper()[:1]
        if t in QB.LETTERS and t != items[0]["letra"] and out.get("trampa_porque"):
            out["trampa"] = t
        else:
            raise ValueError("trampa no válida")
    if fmt == "mito_realidad":
        ver = str(s.get("veredicto") or "").strip().upper()
        if ver not in ("MITO", "REALIDAD") or not _w(s.get("afirmacion"), 6, 26):
            raise ValueError("mito/realidad no válido")
        out["veredicto"] = ver
    if fmt == "caso_practico":
        if not (_w(s.get("escena"), 12, 36) and not re.search(r"\d", s.get("escena", ""))):
            raise ValueError("escena no válida")
        out["escena"] = re.sub(r"\s+", " ", s["escena"]).strip()
        if _w(s.get("escena_visual"), 5, 45):
            out["escena_visual"] = s["escena_visual"].strip()
    if fmt == "truco_memorizar" and not (_w(s.get("truco"), 2, 12) and _w(s.get("truco_line"), 8, 28)):
        raise ValueError("truco no válido")
    if fmt == "legislacion_30s":
        pts = [p for p in (s.get("puntos") or []) if _w(p, 4, 16)]
        if len(pts) != 3:
            raise ValueError("puntos no válidos")
        out["puntos"] = [re.sub(r"\s+", " ", p).strip() for p in pts]
    src = " ".join(P.get("pregunta", P.get("q", "")) + " " + " ".join(P.get("op", [P.get("a", "")])) + " " + P.get("explicacion", "")
                   for P in items)
    for pct in re.findall(r"\d+(?:[.,]\d+)? ?%", " ".join(str(v) for v in out.values())):
        if pct.replace(" ", "") not in src.replace(" ", ""):
            raise ValueError(f"porcentaje {pct} que no está en el material (posible estadística inventada)")
    return out


def _short_expl(text, max_words=40):
    """Explicación de la app recortada por frases completas (nunca a mitad de frase)."""
    sent = re.split(r"(?<=[.;])\s+", text.strip())
    out = []
    for s_ in sent:
        if out and len(" ".join(out + [s_]).split()) > max_words:
            break
        out.append(s_)
    res = " ".join(out)
    return res if len(res.split()) <= max_words + 12 else None


def template(fmt, items):
    """Textos seguros sin IA: frases fijas + explicación literal de la app."""
    P = items[0]
    ex = _short_expl(P.get("explicacion", "")) or ""
    letra = P.get("letra", "")
    if P.get("origen") == "examen":
        ex = "Es la respuesta de la plantilla provisional del tribunal."
    hooks = {"pregunta_del_dia": ("¿Te la sabes?", "Pregunta del día del temario de TCAE. A ver si la aciertas."),
             "examen_real": ("Cayó en el examen", "Esta pregunta cayó en un examen oficial de TCAE."),
             "simulacro_3": ("¿Aciertas las 3?", "Simulacro rápido: tres preguntas tipo test. ¿Cuántas aciertas?"),
             "error_tipico": ("Ojo con la trampa", "Esta pregunta tiene trampa. Léela con calma."),
             "truco_memorizar": ("Truco para no olvidarla", "Te dejo una pregunta y un truco para recordarla."),
             "mito_realidad": ("¿Mito o realidad?", "Mito o realidad. Piénsalo antes de que lo diga."),
             "legislacion_30s": ("Legislación en 30 segundos", "Legislación en treinta segundos. Lo que tienes que saber."),
             "caso_practico": ("Caso práctico de planta", "Caso práctico. Imagina que estás de turno."),
             "flashcards_express": ("4 fichas de repaso", f"Repaso exprés de {P.get('tema', 'temario')}. ¿Cuántas sabes?")}
    sh, hl = hooks[fmt]
    return {"screen_hook": sh, "hook_line": hl, "reveal_line": f"La correcta es la {letra}.",
            "explicacion": ex, "cta_line": f"Practica gratis con {__import__('marca').PREGUNTAS_FRASE} en apruebatcae.com. Tienes el link en la bio.",
            "caption_hook": {"examen_real": "Esta cayó en el examen oficial de TCAE 📝"}.get(fmt, "¿Sabrías responderla en el examen? 📝"),
            "comment_prompt": ("Comenta cuántas sabías, del 0 al 4" if fmt == "flashcards_express"
                               else "Comenta A, B, C o D antes de ver la solución"),
            "cierre_line": ("¿Cuántas sabías? Coméntalo y guarda el reel para repasar." if fmt == "flashcards_express"
                            else "¿Cuántas has acertado? Comenta tu resultado, del cero al tres.")}


def script_for(fmt, items, arms=None, avoid=(), verify=True, series_info=None):
    """Guion verificado. Hasta 2 intentos con IA; si no pasa el verificador -> plantilla segura (formato del día)."""
    notes = None
    if os.environ.get("GEMINI_API_KEY") and os.environ.get("QUIZ_MOCK") != "1":
        for attempt in range(2):
            try:
                s = write(fmt, items, arms, avoid, notes)
            except Exception as e:
                print(f"guionista: intento {attempt + 1} fallido: {str(e)[:150]}", flush=True); continue
            try:                                          # revisor: pule gancho/descripción (no toca datos)
                import reviewer
                s = reviewer.improve_script(s, fmt, items, arms)
            except Exception as e:
                print("revisor omitido:", str(e)[:120], flush=True)
            try:                                          # estudio creativo: memoria, viralidad, embudo, SEO, series...
                import estudio
                s = estudio.text_pass(fmt, items, s, series_info)
            except Exception as e:
                print("estudio creativo omitido:", str(e)[:120], flush=True)
            try:
                s = strip_meta(fmt, items, s)
            except ValueError as e:
                notes = [str(e) + ": escribe solo lo que se dice, sin indicaciones de tono ni de voz"]
                print("guionista:", e, flush=True); continue
            if not verify:
                return s, fmt, "ia"
            import verifier
            ok, probs = verifier.verify_script(items, s, fmt)
            if ok:
                print("guionista: guion verificado", flush=True)
                return s, fmt, "ia"
            notes = probs
            print(f"verificador: guion rechazado: {json.dumps(probs, ensure_ascii=False)[:300]}", flush=True)
    if fmt in ("error_tipico", "truco_memorizar", "mito_realidad", "legislacion_30s", "caso_practico"):
        raise RuntimeError(f"el formato {fmt} necesita un guion verificado")
    s = strip_meta(fmt, items, template(fmt, items))
    if series_info:
        s["series"] = series_info["series"]; s["follow_line"] = f"Mañana: {series_info['manana']}. ¡Síguenos!"
    if not s["explicacion"] and fmt not in ("simulacro_3", "flashcards_express"):
        raise RuntimeError("la explicación de la app es demasiado larga para el reel")
    return s, fmt, "plantilla"
