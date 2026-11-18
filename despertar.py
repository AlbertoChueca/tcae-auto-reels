"""Despierta los workflows que tengan algo pendiente (refuerzo del reloj propio de hueco.py).

GitHub lanza tarde, o no lanza, muchos de los cron. Para no depender de que llegue justo el del workflow que toca,
CUALQUIER workflow programado que llegue (reels, chuleta, soluciones) llama a este script, que mira con hueco.py si hay
un reel o una chuleta pendientes ahora y, si su workflow no está ya en marcha, lo lanza como "programado".

    python despertar.py reel chuleta

Necesita GITHUB_TOKEN con permiso `actions: write`. Solo biblioteca estándar. Nunca falla (si algo va mal, lo dice y sigue).
"""
import json, os, sys, urllib.request

import hueco

WF = {"reel": "daily-reels.yml", "chuleta": "chuleta.yml"}


def gh(method, path, body=None):
    req = urllib.request.Request(f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt else {}


def busy(wf):
    for st in ("in_progress", "queued", "pending", "waiting", "requested"):
        if gh("GET", f"/actions/workflows/{wf}/runs?status={st}&per_page=1").get("total_count"):
            return True
    return False


def main(kinds):
    if not os.environ.get("GITHUB_TOKEN") or not os.environ.get("GITHUB_REPOSITORY"):
        print("despertar: sin GITHUB_TOKEN"); return
    for kind in kinds:
        try:
            if kind == "chuleta" and os.environ.get("CHULETA", "true").lower() == "false":
                continue
            slot, mins = hueco.due(kind)
            if slot is None:
                continue
            if busy(WF[kind]):
                print(f"despertar: {kind} '{slot}' pendiente y su workflow ya está en marcha"); continue
            gh("POST", f"/actions/workflows/{WF[kind]}/dispatches",
               {"ref": os.environ.get("GITHUB_REF_NAME") or "main", "inputs": {"programado": "true", "dry_run": "false"}})
            print(f"despertar: lanzado {kind} '{slot}' (faltan {mins:.0f} min)" if mins > 0 else f"despertar: lanzado {kind} '{slot}' (va {-mins:.0f} min tarde)")
        except Exception as e:
            print(f"despertar: {kind} no comprobado ({str(e)[:150]})")


if __name__ == "__main__":
    main(sys.argv[1:] or ["reel", "chuleta"])
