"""TikTok y YouTube Shorts a través de Zernio (https://docs.zernio.com).

Env: ZERNIO_API_KEY. Opcional: ZERNIO_YT_ACCOUNT / ZERNIO_TT_ACCOUNT (ids de cuenta; si faltan se buscan solos).

- tiktok_video():   el reel en TikTok (público, con portada en el fotograma del gancho).
- tiktok_photos():  carrusel de fotos en TikTok (modo foto) con los fotogramas clave del reel: muy buen alcance y
                    hace de "story" automática, porque la API de TikTok no permite publicar Stories.
- tiktok_draft():   envía un vídeo (la story) al buzón de TikTok (Creator Inbox) como borrador: desde la notificación
                    de la app se publica como Story con un toque.
- youtube_short():  el reel en YouTube Shorts (no "made for kids": público adulto).
Cada función es independiente: si una falla, las demás siguen.
"""
import os, time, requests

API = "https://zernio.com/api/v1"
TAGS = ["TCAE", "oposiciones TCAE", "auxiliar de enfermería", "oposiciones", "SALUD Aragón", "test"]
_ACC = {}


def _h():
    return {"Authorization": f"Bearer {os.environ['ZERNIO_API_KEY']}"}


def _check(r, what):
    if r.status_code >= 400:
        raise RuntimeError(f"Zernio {what} error {r.status_code}: {r.text[:500]}")
    return r.json() if r.content else {}


def accounts():
    if _ACC:
        return _ACC
    ids = {"youtube": os.environ.get("ZERNIO_YT_ACCOUNT"), "tiktok": os.environ.get("ZERNIO_TT_ACCOUNT")}
    if not all(ids.values()):
        data = _check(requests.get(f"{API}/accounts", headers=_h(), timeout=60), "accounts")
        items = data.get("accounts", data if isinstance(data, list) else data.get("data", []))
        for a in items:
            p = (a.get("platform") or "").lower()
            if p in ids and not ids[p]:
                ids[p] = a.get("_id") or a.get("id")
    _ACC.update({k: v for k, v in ids.items() if v})
    print("Zernio cuentas:", {k: bool(ids.get(k)) for k in ("tiktok", "youtube")}, flush=True)
    return _ACC


def upload(path):
    """Sube un archivo a Zernio y devuelve su URL pública."""
    ct = {"mp4": "video/mp4", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}[path.rsplit(".", 1)[-1].lower()]
    for attempt in range(3):
        try:
            pre = _check(requests.post(f"{API}/media/presign", headers=_h(), json={
                "filename": os.path.basename(path), "contentType": ct, "size": os.path.getsize(path)}, timeout=60), "presign")
            with open(path, "rb") as f:
                up = requests.put(pre["uploadUrl"], data=f, headers={"Content-Type": ct}, timeout=600)
            if up.status_code >= 400:
                raise RuntimeError(f"Zernio subida {up.status_code}: {up.text[:300]}")
            return pre["publicUrl"]
        except Exception as e:
            if attempt == 2:
                raise
            print("Zernio subida, reintento:", str(e)[:150], flush=True); time.sleep(10 * (attempt + 1))


def _post(body, what):
    for attempt in range(3):
        try:
            res = _check(requests.post(f"{API}/posts", headers=_h(), json=body, timeout=120), what)
            pid = (res.get("post") or res).get("_id") if isinstance(res, dict) else None
            print(f"Zernio {what}: creado {pid}", flush=True)
            return pid or "ok"
        except RuntimeError as e:
            if " 4" in str(e)[:25] and " 429" not in str(e)[:25]:      # error de datos: no sirve reintentar
                raise
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))


def _tt_text(caption):
    """En TikTok el enlace de la bio no es clicable hasta tener seguidores suficientes: se nombra la web tal cual."""
    return (caption.replace(" (link en la bio)", "").replace("(link en la bio)", "")
            .replace("link en la bio", "apruebatcae.com"))[:2150]


def tiktok_video(video_url, caption, cover_ms=1200):
    acc = accounts().get("tiktok")
    if not acc:
        raise RuntimeError("no hay cuenta de TikTok conectada en Zernio")
    return _post({"content": _tt_text(caption), "mediaItems": [{"type": "video", "url": video_url}], "publishNow": True,
                  "platforms": [{"platform": "tiktok", "accountId": acc}],
                  "tiktokSettings": {"privacy_level": "PUBLIC_TO_EVERYONE", "allow_comment": True, "allow_duet": True,
                                     "allow_stitch": True, "content_preview_confirmed": True, "express_consent_given": True,
                                     "video_cover_timestamp_ms": int(cover_ms or 1000)}}, "tiktok vídeo")


def tiktok_photos(image_urls, title, description):
    acc = accounts().get("tiktok")
    if not acc:
        raise RuntimeError("no hay cuenta de TikTok conectada en Zernio")
    return _post({"content": title[:90], "mediaItems": [{"type": "image", "url": u} for u in image_urls[:35]], "publishNow": True,
                  "platforms": [{"platform": "tiktok", "accountId": acc}],
                  "tiktokSettings": {"media_type": "photo", "photo_cover_index": 0, "description": _tt_text(description)[:3900],
                                     "auto_add_music": True, "privacy_level": "PUBLIC_TO_EVERYONE", "allow_comment": True,
                                     "content_preview_confirmed": True, "express_consent_given": True}}, "tiktok carrusel")


def tiktok_draft(video_url, caption):
    acc = accounts().get("tiktok")
    if not acc:
        raise RuntimeError("no hay cuenta de TikTok conectada en Zernio")
    return _post({"content": _tt_text(caption)[:300], "mediaItems": [{"type": "video", "url": video_url}], "publishNow": True,
                  "platforms": [{"platform": "tiktok", "accountId": acc}],
                  "tiktokSettings": {"draft": True, "privacy_level": "PUBLIC_TO_EVERYONE", "allow_comment": True,
                                     "content_preview_confirmed": True, "express_consent_given": True}}, "tiktok borrador story")


def youtube_short(video_url, title, caption):
    acc = accounts().get("youtube")
    if not acc:
        raise RuntimeError("no hay canal de YouTube conectado en Zernio")
    desc = caption.replace("(link en la bio)", "").replace("link en la bio", "https://apruebatcae.com")
    return _post({"content": desc[:4900], "mediaItems": [{"type": "video", "url": video_url}], "publishNow": True, "tags": TAGS,
                  "platforms": [{"platform": "youtube", "accountId": acc, "platformSpecificData": {
                      "title": title[:90] + " #shorts", "visibility": "public", "madeForKids": False, "categoryId": "27"}}]},
                 "youtube short")
