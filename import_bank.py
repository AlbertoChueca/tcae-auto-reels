"""Importa el banco de preguntas de la web app Aprueba TCAE (su index.html) a banco/preguntas.json y banco/fichas.json.

    python import_bank.py ruta/a/index.html

Lee SOLO las constantes de datos de la app (TOPICS, TEST_QUESTIONS, FLASHCARDS, REAL_EXAMS y las listas de módulos)
con Node.js, sin ejecutar el resto del código. Cada pregunta recibe un id estable (hash del tema + enunciado), así que
volver a importar tras actualizar la app conserva qué preguntas ya se verificaron o publicaron.
Las preguntas con `exam:"..."` son de exámenes oficiales y se marcan como tal (origen "examen").
"""
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_Q = os.path.join(HERE, "banco", "preguntas.json")
OUT_F = os.path.join(HERE, "banco", "fichas.json")


def _id(*parts):
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:10]


def load_raw(html):
    raw = os.path.join(HERE, "banco", "_raw.json")
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    subprocess.run(["node", os.path.join(HERE, "tools_extract.js"), html, raw], check=True)
    d = json.load(open(raw)); os.remove(raw)
    if not d.get("TEST_QUESTIONS"):
        raise SystemExit("No encuentro TEST_QUESTIONS en el HTML: ¿es el index.html de la web app?")
    return d


def bloque_de(topic, d):
    for name, key in (("legislacion", "LEGISLACION_TOPIC_KEYS"), ("geografia", "GEOGRAFIA_TOPIC_KEYS"),
                      ("fechas", "FECHAS_TOPIC_KEYS"), ("prefijos", "PREFIJOS_TOPIC_KEYS")):
        if topic in (d.get(key) or []):
            return name
    return "clinico"


def main(html):
    d = load_raw(html)
    topics = d.get("TOPICS") or {}
    exams = {e["id"]: e for e in (d.get("REAL_EXAMS") or [])}
    qs, seen = [], set()
    for q in d["TEST_QUESTIONS"]:
        opts = [str(o).strip() for o in q.get("options") or []]
        if len(opts) != 4 or not isinstance(q.get("correct"), int) or not 0 <= q["correct"] < 4:
            continue
        qid = _id(q.get("topic", ""), q["q"].strip())
        if qid in seen:
            continue
        seen.add(qid)
        ex = exams.get(q.get("exam")) if q.get("exam") else None
        qs.append({"id": qid, "topic": q.get("topic"), "tema": topics.get(q.get("topic"), q.get("topic")),
                   "bloque": bloque_de(q.get("topic"), d), "pregunta": q["q"].strip(), "opciones": opts,
                   "correcta": q["correct"], "explicacion": (q.get("explain") or "").strip(),
                   "origen": "examen" if ex else "webapp",
                   "examen": ({"id": ex["id"], "titulo": ex.get("title"), "subtitulo": ex.get("subtitle")} if ex else None)})
    fichas = [{"topic": f.get("topic"), "q": f["q"].strip(), "a": f["a"].strip()} for f in (d.get("FLASHCARDS") or [])
              if f.get("q") and f.get("a")]
    old = {}
    if os.path.exists(OUT_Q):
        old = {q["id"]: q for q in json.load(open(OUT_Q))}
    json.dump(qs, open(OUT_Q, "w"), ensure_ascii=False, indent=0)
    json.dump(fichas, open(OUT_F, "w"), ensure_ascii=False, indent=0)
    new = [q for q in qs if q["id"] not in old]
    gone = [k for k in old if k not in {q["id"] for q in qs}]
    print(f"{len(qs)} preguntas ({sum(q['origen'] == 'examen' for q in qs)} de examen oficial), {len(fichas)} fichas, "
          f"{len(topics)} temas. Nuevas: {len(new)}, eliminadas: {len(gone)}.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
