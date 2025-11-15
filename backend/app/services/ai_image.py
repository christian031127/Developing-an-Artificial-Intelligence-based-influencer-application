# backend/app/services/ai_image.py
import io, uuid, os
from pathlib import Path
import httpx
from fastapi import HTTPException
from PIL import Image
from ..core.settings import settings

MEDIA_DIR = Path("/app/uploads/images").resolve()
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

HF_ENDPOINT = lambda model: f"https://api-inference.huggingface.co/models/{model}"

_FORBID = {"poster","banner","flyer","layout","title","caption","typography","text","logo","watermark","frame"}

def _strip_forbidden(s: str) -> str:
    """Egyszerű szűrő: kiszedi a poszteres/ráírt szövegre utaló szavakat a promptból."""
    t = s or ""
    low = t.lower()
    for w in _FORBID:
        low = low.replace(w, "")
    return " ".join(low.split())

def build_prompt(*, persona_name: str | None, topic: str, trend_tags: list[str] | None) -> tuple[str, str]:
    """KOMPATIBILITÁSI BUILDER – (positive, negative) promptot ad vissza."""
    tags = ", ".join([t.strip() for t in (trend_tags or []) if t and len(t) <= 32])
    subject = topic.strip()
    persona_hint = "portrait photo"
    context = "photorealistic, natural skin, studio lighting, shallow depth of field, editorial composition"
    base = f"{persona_hint}, {subject}{', ' + tags if tags else ''}, {context}. no text, no logo, no watermark, no poster, no banner, no frame."
    positive = _strip_forbidden(base)
    negative = "blurry, lowres, overexposed, jpeg artifacts, deformed hands, extra fingers, bad anatomy, text, caption, logo, watermark, poster, banner, frame"
    return positive, negative

def build_image_prompt_from_persona(persona: dict | None, *, topic: str, trend_tags: list[str] | None) -> tuple[str, str]:
    """Persona-alapú prompt (pozitív/negatív)."""
    identity = (persona or {}).get("identity_hint") or "person"
    style = (persona or {}).get("style") or "photo_realistic"
    mood = (persona or {}).get("mood") or "neutral"
    bg = (persona or {}).get("bg") or "studio_gray"
    trend = ", ".join([t for t in (trend_tags or []) if t])

    positive = (
        f"portrait photo of {identity}, {style}, {mood}, {bg}, "
        f"topic: {topic.strip()}"
        + (f", {trend}" if trend else "")
        + ", natural skin, editorial lighting, shallow depth of field"
    )
    negative = (
        "text, caption, title, subtitle, poster, banner, watermark, logo, frame, "
        "typography, graphic design, lowres, overexposed, underexposed, blurry, jpeg artifacts"
    )
    return positive, negative

# --- OpenAI img2img (1024x1024 támogatott) + 4:5 padosítás (nem torzít) ---
async def generate_openai_img2img(
    init_image_path: str,
    prompt: str,
    model: str | None = None,
    size: str = "1024x1024",   # ← OpenAI által engedélyezett default
    pad_to_portrait: bool = True,
) -> tuple[str, str]:
    """
    OpenAI Images Edit (img2img):
    - Méret: 1024x1024 (OpenAI ezt támogatja); utána opcionális 4:5 padosítás (vászon bővítés, NEM nyújtás).
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(500, "OPENAI_API_KEY not configured")
    model = model or os.getenv("OPENAI_IMAGE_MODEL", settings.OPENAI_IMAGE_MODEL)

    # 1) base image beolvasása és PNG
    try:
        base = Image.open(init_image_path).convert("RGB")
    except FileNotFoundError:
        raise HTTPException(400, f"Init image not found: {init_image_path}")

    buf = io.BytesIO()
    base.save(buf, format="PNG")
    buf.seek(0)
    png_bytes = buf.read()

    # 2) /v1/images/edits hívás
    url = "https://api.openai.com/v1/images/edits"
    headers = {"Authorization": f"Bearer {key}"}
    files = {
        "image": ("init.png", png_bytes, "image/png"),
        "prompt": (None, prompt),
        "model": (None, model),
        "size": (None, size),  # ← csak a támogatott méretek egyike!
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(url, headers=headers, files=files)
        if r.status_code >= 400:
            raise HTTPException(502, f"OpenAI {r.status_code}: {r.text[:400]}")
        data = r.json()

    # 3) base64 -> PIL Image
    import base64
    b64 = data["data"][0].get("b64_json")
    if not b64:
        raise HTTPException(502, "OpenAI response missing b64_json")
    out_bytes = base64.b64decode(b64)
    image = Image.open(io.BytesIO(out_bytes)).convert("RGB")  # várhatóan 1024x1024

    # 4) 4:5 padosítás – NEM nyújtunk, csak vásznat bővítünk
    if pad_to_portrait:
        w, h = image.size
        target_w = w
        target_h = int(round(target_w * 5 / 4))  # 4:5 arány
        canvas = Image.new("RGB", (target_w, target_h), (17, 24, 39))  # #111827
        top = (target_h - h) // 2
        canvas.paste(image, (0, top))
        image = canvas

    # 5) Mentés
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    img_id = str(uuid.uuid4())
    out_path = MEDIA_DIR / f"{img_id}.jpg"
    image.save(out_path, format="JPEG", quality=92)
    url = f"{settings.BASE_URL}/uploads/images/{img_id}.jpg"
    return img_id, url
