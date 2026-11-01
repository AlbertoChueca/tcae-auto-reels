"""Diagnóstico del guion: ejecuta la cadena guionista -> revisor -> estudio -> verificador paso a paso para varios
formatos y escribe TODO (guiones, cambios y motivos de rechazo) en diagnostico.md. No publica nada.

    python diagnostico.py [formato ...]
"""
import json, os, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "diagnostico.md")
rows = ["# Diagnóstico del guion\n"]


def log(x=""):
    rows.append(str(x)); print(str(x)[:300], flush=True)


def main(fmts):
    import questions as QB, writer, verifier, reviewer, estudio
    for fmt in fmts:
        log(f"\n## {fmt}")
        try:
            if fmt == "flashcards_express":
                items = QB.pick_fichas(seed="diag", verify=None)
            else:
                qs = QB.pick(fmt, None, seed="diag-" + fmt, n=3 if fmt == "simulacro_3" else 1, verify=None)
                items = [QB.prepare(q, 1) for q in qs]
            log("Pregunta(s): " + " | ".join((P.get("pregunta") or P.get("q"))[:90] for P in items))
        except Exception as e:
            log(f"sin preguntas: {e}"); continue
        notes = None
        for attempt in range(2):
            log(f"\n### intento {attempt + 1}")
            try:
                s = writer.write(fmt, items, {"hook_style": "reto"}, (), notes)
                log("guionista OK:\n```json\n" + json.dumps(s, ensure_ascii=False, indent=1)[:2500] + "\n```")
            except Exception as e:
                log(f"guionista FALLÓ: {type(e).__name__}: {str(e)[:400]}"); notes = [str(e)[:150]]; continue
            try:
                s2 = reviewer.improve_script(s, fmt, items, {})
                log("revisor: cambios " + json.dumps({k: v for k, v in s2.items() if s.get(k) != v}, ensure_ascii=False)[:800])
                s = s2
            except Exception as e:
                log(f"revisor FALLÓ: {str(e)[:300]}")
            try:
                s2 = estudio.text_pass(fmt, items, s, None)
                log("estudio: añade " + json.dumps({k: v for k, v in s2.items() if s.get(k) != v}, ensure_ascii=False)[:1200])
                s = s2
            except Exception as e:
                log(f"estudio FALLÓ: {str(e)[:300]}")
            try:
                s = writer.strip_meta(fmt, items, s)
            except ValueError as e:
                log(f"strip_meta RECHAZA: {e}"); notes = [str(e)]; continue
            try:
                ok, probs = verifier.verify_script(items, s, fmt)
                log(f"verificador: ok={ok}\n```json\n{json.dumps(probs, ensure_ascii=False, indent=1)[:2500]}\n```")
                if ok:
                    break
                notes = probs
            except Exception as e:
                log(f"verificador FALLÓ: {traceback.format_exc()[-600:]}")
    open(OUT, "w").write("\n".join(rows) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("\n".join(rows)[:60000] + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["pregunta_del_dia", "error_tipico", "mito_realidad", "caso_practico"])
