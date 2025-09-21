import base64
import io
from typing import Optional
import httpx
from PIL import Image
from app.core.settings import settings

# Prompt sablon – ízléses, non-NSFW fitness lifestyle
def _build_prompt(title: str, style_hint: Optional[str] = None) -> str:
    base = (
    "Instagram fitness lifestyle photo of an adult woman (age 25-35) training in a gym; "
    "realistic, clean composition, soft lighting, tasteful, non-NSFW; "
    "athletic outfit suitable for workout, no cleavage, no midriff focus; "
    "portrait orientation; editorial quality."
    )
    if style_hint:
        base += f" Style: {style_hint}."
    base += f" Concept/topic: {title}."
    # negatív kérések promptban (OpenAI Images nem támogat külön negative promptot)
    base += " Avoid: nsfw, watermark, overexposed, text overlays, deformed hands."
    return base

async def generate_image_bytes(title: str, style_hint: Optional[str] = None) -> bytes:
    """
    OpenAI Images (gpt-image-1) használata.
    Kérünk portrait méretet (1024x1536), majd pontosan 1080x1350-re igazítjuk.
    """
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-image-1",
        "prompt": _build_prompt(title, style_hint),
        "n": 1,
        "size": "1024x1024",  # portrait
    }

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post("https://api.openai.com/v1/images/generations",
                          headers=headers, json=payload)
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        # fontos: a response body tele van hasznos hibával
        raise RuntimeError(f"image api error {r.status_code}: {r.text}") from e
    data = r.json()

    b64 = data["data"][0]["b64_json"]
    raw = base64.b64decode(b64)

    # pontos Insta-portrait (1080x1350) előállítása
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    target_w, target_h = 1080, 1350
    # aránymegőrzés + középre vágás
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if img_ratio > target_ratio:
        # túl széles → magasságra illesztünk, bal-jobb vágás
        new_h = target_h
        new_w = int(new_h * img_ratio)
    else:
        # túl magas → szélességre illesztünk, fel-le vágás
        new_w = target_w
        new_h = int(new_w / img_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    return out.getvalue()
