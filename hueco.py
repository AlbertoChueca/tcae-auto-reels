"""¿Qué toca publicar AHORA? (reloj propio, porque el programador de GitHub llega tarde).

GitHub lanza los workflows programados cuando puede: en este repositorio llegaban entre 4 y 9 horas tarde (el reel de
las 21:30 salía a las 2 de la madrugada) y bastantes ni llegaban. Por eso los workflows ya no se fían de la hora del
cron: se despiertan muchas veces al día y este script decide, mirando la hora real de España, si hay algo pendiente.

    python hueco.py reel      -> mediodia (14:30) | noche (21:30) | skip
    python hueco.py chuleta   -> 8 | 18 | skip

Un hueco "toca" si estamos entre ANTES minutos antes de su hora y DESPUES minutos después y hoy aún no se ha publicado.
Si el workflow llega antes de la hora, genera el contenido y ESPERA a la hora exacta para publicar (los minutos de
espera son gratis en un repositorio público); si llega después, publica en cuanto está listo. Pasada la ventana, ese
hueco se salta (mejor no publicar que publicar a las 3 de la madrugada).
Escribe slot=... en GITHUB_OUTPUT. Solo usa la biblioteca estándar (corre antes de instalar nada).
"""
import datetime, json, os, sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = {"reel": {"mediodia": (14, 30), "noche": (21, 30)}, "chuleta": {"8": (8, 0), "18": (18, 0)}}
ANTES = {"reel": int(os.environ.get("HUECO_ANTES_MIN", "180")), "chuleta": int(os.environ.get("HUECO_ANTES_MIN", "180"))}
DESPUES = {"reel": int(os.environ.get("HUECO_DESPUES_MIN", "120")), "chuleta": int(os.environ.get("HUECO_DESPUES_MIN", "150"))}


def done_today(kind, slot, day, after=None):
    """¿Ya se publicó hoy ese hueco? day = fecha UTC (la que guardan los registros). after (UTC, sin zona): los reels
    publicados antes de esa hora no cuentan (son el hueco de AYER, que GitHub lanzó de madrugada con retraso)."""
    try:
        if kind == "reel":
            for line in open(os.path.join(HERE, "log.jsonl")):
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("date") == day and e.get("slot") == slot and any(
                        not str(v).startswith("error") for v in (e.get("publicado") or {}).values()):
                    if after is not None and e.get("ts") and datetime.datetime.fromisoformat(e["ts"]) < after:
                        continue
                    return True
        else:
            for e in json.load(open(os.path.join(HERE, "chuletas.json"))):
                if e.get("fecha") == day and str(e.get("slot")) == slot and e.get("publicado"):
                    return True
    except Exception:
        pass
    return False


def window(kind, slot, now=None):
    """(hora del hueco hoy en España, inicio de su ventana en UTC sin zona)."""
    now = now or datetime.datetime.now(ZoneInfo("Europe/Madrid"))
    h, m = TARGETS[kind][slot]
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    start = (target - datetime.timedelta(minutes=ANTES[kind] + 30)).astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return target, start


def due(kind, now=None):
    """(slot, minutos hasta su hora; negativo si ya pasó) del hueco pendiente, o (None, None)."""
    now = now or datetime.datetime.now(ZoneInfo("Europe/Madrid"))
    day = now.astimezone(datetime.timezone.utc).date().isoformat()
    best = (None, None)
    for slot in TARGETS[kind]:
        target, start = window(kind, slot, now)
        mins = (target - now).total_seconds() / 60
        if -DESPUES[kind] <= mins <= ANTES[kind] and not done_today(kind, slot, day, start):
            if best[0] is None or abs(mins) < abs(best[1]):
                best = (slot, mins)
    return best


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "reel"
    slot, mins = due(kind)
    now = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
    if slot is None:
        print(f"{now:%H:%M} (España): no hay {kind} pendiente ahora")
    else:
        print(f"{now:%H:%M} (España): toca {kind} '{slot}' " + (f"(faltan {mins:.0f} min: se prepara y espera a su hora)" if mins > 0
                                                               else f"(va {-mins:.0f} min tarde: se publica en cuanto esté)"))
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write(f"slot={slot or 'skip'}\n")
    else:
        print(slot or "skip")
