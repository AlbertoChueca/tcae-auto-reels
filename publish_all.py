"""Publica a la vez en todas las redes (cada destino es independiente: un fallo nunca bloquea a los demás).

  Instagram   Reel (+ ubicación y portada) y Story propia de 12 s que anuncia el reel
  TikTok      el mismo vídeo publicado a la vez + carrusel de fotos (opcional) + la story al buzón como borrador (opcional)
  YouTube     Short

Interruptores (Settings > Secrets and variables > Actions > Variables): IG_STORY, TIKTOK, TIKTOK_CARRUSEL,
TIKTOK_STORY_BORRADOR, YOUTUBE: "true", "false" o el hueco en el que actúan ("mediodia" / "noche").
Por defecto todo activo salvo el carrusel de TikTok con los fotogramas del reel (duplicaba el vídeo; el carrusel de
TikTok es ahora la chuleta diaria de las 18:00). Hueco "manana" (8:00): reel en TikTok y YouTube y, en Instagram, el
reel completo como story (sin post en el feed para no quitar alcance a los otros).
TikTok y YouTube necesitan ZERNIO_API_KEY.
"""
import os, threading
from concurrent.futures import ThreadPoolExecutor


SLOT = [""]


def on(name, default="true"):
    """"true"/"false", o el nombre de un hueco ("mediodia"/"noche") para activarlo solo en ese hueco."""
    v = os.environ.get(name, default).lower()
    return v == "true" or (v == SLOT[0] and v != "")


def carousel_text(meta, caption):
    first = caption.split("\n", 1)[0]
    return first, caption


def publish(reel, story, slides, caption, meta, location_id=None, slot=""):
    """Devuelve {destino: resultado}. resultado = id/permalink o 'error: ...'."""
    SLOT[0] = slot
    res = {}
    zernio = bool(os.environ.get("ZERNIO_API_KEY"))
    jobs = {}

    def ig_reel():
        from publish_ig import publish_reel
        m = publish_reel(reel, caption, location_id=location_id, thumb_ms=meta.get("thumb_ms"))
        meta.update(permalink=m.get("permalink"), media_id=m.get("id"))
        return m.get("permalink") or m.get("id")

    def ig_story():
        from publish_ig import publish_story
        return publish_story(story or reel).get("id")

    morning = slot == "manana"                # 8:00: el reel va a TikTok y YouTube; en Instagram solo como story
    if not morning:
        jobs["instagram_reel"] = ig_reel
    if (on("IG_STORY") or morning) and os.environ.get("IG_TOKEN"):
        jobs["instagram_story"] = ig_story
    if zernio:
        import publish_zernio as Z
        urls, lock = {}, threading.Lock()

        def url(path):                       # cada archivo se sube una sola vez (aunque lo pidan dos destinos a la vez)
            with lock:
                if path not in urls:
                    urls[path] = Z.upload(path)
                return urls[path]
        from publish_ig import ig_safe
        light = ig_safe(reel)
        if on("TIKTOK"):
            jobs["tiktok_video"] = lambda: Z.tiktok_video(url(light), caption, meta.get("thumb_ms"))
        if on("YOUTUBE"):
            jobs["youtube_short"] = lambda: Z.youtube_short(url(light), meta.get("yt_title") or f"{meta.get('hook')} | Test TCAE", caption)
        if on("TIKTOK_CARRUSEL", "false") and slides and not morning:
            title, desc = carousel_text(meta, caption)
            jobs["tiktok_carrusel"] = lambda: Z.tiktok_photos([url(p) for p in slides], title, desc)
        if on("TIKTOK_STORY_BORRADOR") and story and not morning:
            jobs["tiktok_story_borrador"] = lambda: Z.tiktok_draft(url(story), caption.split("\n", 1)[0])
    with ThreadPoolExecutor(len(jobs)) as ex:
        futs = {k: ex.submit(f) for k, f in jobs.items()}
        for k, f in futs.items():
            try:
                res[k] = str(f.result(timeout=1500))
            except Exception as e:
                res[k] = f"error: {str(e)[:200]}"
                print(f"publicación {k} fallida:", str(e)[:300], flush=True)
    return res
