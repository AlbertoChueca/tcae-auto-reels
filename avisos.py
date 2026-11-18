"""Avisos: si una red deja de publicar, que te enteres el mismo día (y no cinco días después).

Cada vez que se publica algo (reel, chuleta, respuestas) se llama a `revisar(resultados, origen)`:
- Si Instagram, TikTok o YouTube fallan por un problema de CUENTA (token caducado o invalidado, cuenta desconectada),
  se abre una incidencia (issue) en el repositorio de GitHub, asignada al dueño: GitHub le manda un correo y una
  notificación al móvil. La incidencia explica paso a paso cómo arreglarlo. Mientras siga fallando se añade, como
  mucho, un comentario al día; cuando vuelve a funcionar, la incidencia se cierra sola.
- Además `revisar` devuelve True para que el workflow termine en rojo (después de guardar todo): en la pestaña Actions
  se ve a simple vista que algo va mal aunque las otras redes hayan publicado.
Los fallos puntuales (un vídeo que Instagram rechaza, un corte de red) no abren incidencia.

Necesita GITHUB_TOKEN con permiso `issues: write` (lo dan los workflows). Sin él, solo escribe el aviso en el resumen.
"""
import datetime, json, os
import requests

API = "https://api.github.com"
LABEL = "aviso-publicacion"

IG_STEPS = """**Instagram ha dejado de aceptar el token (`IG_TOKEN`)**. Suele pasar al cambiar la contraseña de Facebook o cuando
Facebook cierra las sesiones por seguridad. Hasta que lo renueves no se publica nada en Instagram (reels, stories,
chuletas) ni se contestan allí los comentarios. TikTok y YouTube siguen publicando.

**Cómo arreglarlo (5 minutos):**
1. Entra en <https://developers.facebook.com/tools/explorer/>, elige tu app y pulsa **Generate Access Token** (token de
   usuario) con estos permisos: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`,
   `instagram_manage_comments`, `pages_show_list`, `pages_read_engagement`.
2. Copia ese token, ábrelo en <https://developers.facebook.com/tools/debug/accesstoken/> y pulsa **Extend Access Token**
   (token de larga duración).
3. De vuelta en el Explorer, pega el token de larga duración y consulta `me/accounts`: copia el `access_token` de la
   **página** vinculada a @apruebatcae (empieza por `EAA`). Ese token de página no caduca.
4. En GitHub: **Settings → Secrets and variables → Actions → Secrets → `IG_TOKEN` → Update** y pega el token de página.
5. **Actions → Comprobar conexiones → Run workflow**: Instagram debe salir en verde. Esta incidencia se cierra sola en
   la siguiente publicación correcta."""

ZERNIO_STEPS = """**Zernio no puede publicar en {red}** (cuenta desconectada, clave no válida o plan sin esa función).

**Cómo arreglarlo:** entra en <https://zernio.com>, revisa en *Accounts* que la cuenta de {red} sigue conectada
(reconéctala si pide permisos) y que la clave de API del secreto `ZERNIO_API_KEY` sigue activa. Después lanza
**Actions → Comprobar conexiones**. Esta incidencia se cierra sola en la siguiente publicación correcta."""

PROBLEMS = {
    "instagram": ("⚠️ Instagram no está publicando: hay que renovar IG_TOKEN", IG_STEPS),
    "tiktok": ("⚠️ TikTok no está publicando: revisa la cuenta en Zernio", ZERNIO_STEPS.format(red="TikTok")),
    "youtube": ("⚠️ YouTube no está publicando: revisa el canal en Zernio", ZERNIO_STEPS.format(red="YouTube")),
}


def _net(key):
    k = key.lower()
    return "instagram" if k.startswith(("instagram", "ig")) else "tiktok" if "tiktok" in k else "youtube" if "youtube" in k else None


def account_error(msg):
    """¿El error es de la cuenta (hay que hacer algo a mano) y no un fallo puntual?"""
    m = str(msg).lower()
    return any(x in m for x in ("access token", "oauthexception", '"code":190', "session has been invalidated", "token no válido",
                                "error 401", " 401:", "unauthorized", "no hay cuenta", "no hay canal", "reconnect", "token expired",
                                "invalid api key"))


def _gh(method, path, **kw):
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not tok or not repo:
        return None
    r = requests.request(method, f"{API}/repos/{repo}{path}", timeout=30, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}, **kw)
    if r.status_code >= 400:
        print(f"avisos: GitHub {method} {path} -> {r.status_code}: {r.text[:200]}", flush=True)
        return None
    return r.json() if r.content else {}


def _open_issues():
    return [i for i in (_gh("GET", "/issues", params={"state": "open", "per_page": 100}) or [])
            if "pull_request" not in i]                    # se reconocen por el título (la etiqueta es solo para filtrar)


def revisar(results, origen=""):
    """results: {destino: resultado o 'error: ...'}. Abre/actualiza/cierra incidencias. Devuelve True si hay un
    problema de cuenta sin resolver (para que el workflow acabe en rojo)."""
    bad, good = {}, set()
    for k, v in (results or {}).items():
        net = _net(k)
        if not net:
            continue
        if isinstance(v, str) and v.startswith("error"):
            if account_error(v):
                bad.setdefault(net, v)
        elif v:
            good.add(net)
    good -= set(bad)
    if not bad and not good:
        return False
    today = str(datetime.date.today())
    try:
        issues = _open_issues()
    except Exception as e:
        print("avisos: no se pudo consultar GitHub:", str(e)[:150], flush=True); issues = []
    by_net = {net: next((i for i in issues if i["title"] == PROBLEMS[net][0]), None) for net in PROBLEMS}
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER")
    for net, err in bad.items():
        title, steps = PROBLEMS[net]
        body = (f"{steps}\n\n---\nDetectado el {today} al publicar: {origen}.\n\nError que devuelve la red:\n```\n{str(err)[:400]}\n```\n"
                "_Aviso automático del sistema de publicación de Aprueba TCAE._")
        try:
            if by_net.get(net) is None:
                made = _gh("POST", "/issues", json={"title": title, "body": body, "labels": [LABEL],
                                                    "assignees": [owner] if owner else []})
                if made is None:                             # p. ej. no se puede asignar: se intenta sin asignar
                    made = _gh("POST", "/issues", json={"title": title, "body": body, "labels": [LABEL]})
                print(f"avisos: incidencia abierta para {net}" if made else f"avisos: {title}", flush=True)
            else:
                num = by_net[net]["number"]
                last = str(by_net[net].get("updated_at", ""))[:10]
                if last < today:                             # como mucho un recordatorio al día
                    _gh("POST", f"/issues/{num}/comments", json={"body": f"Sigue fallando hoy ({today}, {origen}). "
                                                                           "Los pasos para arreglarlo están arriba."})
        except Exception as e:
            print("avisos: no se pudo abrir la incidencia:", str(e)[:150], flush=True)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(f"\n## {title}\n{steps}\n")
    for net in good:
        if by_net.get(net) is not None:
            num = by_net[net]["number"]
            try:
                _gh("POST", f"/issues/{num}/comments", json={"body": f"✅ Vuelve a publicar con normalidad ({today}, {origen})."})
                _gh("PATCH", f"/issues/{num}", json={"state": "closed", "state_reason": "completed"})
                print(f"avisos: incidencia de {net} cerrada (ya funciona)", flush=True)
            except Exception as e:
                print("avisos: no se pudo cerrar la incidencia:", str(e)[:150], flush=True)
    return bool(bad)


if __name__ == "__main__":
    import sys
    print(revisar(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}, "prueba"))
