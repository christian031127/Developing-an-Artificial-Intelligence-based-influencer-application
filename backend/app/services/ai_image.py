# backend/app/services/ai_image.py
import io, uuid, time
from pathlib import Path
import httpx
from fastapi import HTTPException
from PIL import Image
from ..core.settings import settings

MEDIA_DIR = Path("/app/uploads/images").resolve()
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


HF_ENDPOINT = lambda model: f"https://api-inference.huggingface.co/models/{model}"

# --- ÚJ: prompt-építő (persona + topic + trend-tags) ---
def build_prompt(*, persona_name: str | None, topic: str, trend_tags: list[str] | None) -> tuple[str, str]:
    tags = ", ".join([t for t in (trend_tags or []) if t])  # "gym, beginner, form"
    subject = f"{topic.strip()}"
    context = "modern lifestyle photo, soft natural light, editorial composition, shallow depth of field, high detail"
    persona_hint = f"portrait of {persona_name}" if persona_name else "portrait"
    positive = f"{persona_hint}, {subject}{', ' + tags if tags else ''}, {context}"
    negative = "blurry, lowres, overexposed, text, watermark, logo, deformed hands, extra fingers, bad anatomy, jpeg artifacts"
    return positive, negative

# --- KISMÉRTÉKŰ módosítás: a meglévő generate_sdxl kapjon width/height/steps/guidance-t ---
async def generate_sdxl(prompt: str, negative_prompt: str | None = None,
                        width: int = 896, height: int = 1152,
                        steps: int = 28, guidance: float = 7.5) -> tuple[str, str]:
    if not settings.HF_TOKEN:
        raise HTTPException(500, detail="HF_TOKEN not configured")

    headers = {
        "Authorization": f"Bearer {settings.HF_TOKEN}",
        "Accept": "image/png",
        "Content-Type": "application/json"
    }
    body = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt or "blurry, deformed hands, extra fingers, watermark, text",
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
            "seed": int(time.time() * 1000) % 2_000_000_000,
        },
        "options": {"wait_for_model": True}
    }

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(HF_ENDPOINT(settings.SDXL_MODEL), headers=headers, json=body)
        if r.status_code != 200:
            raise HTTPException(502, detail=r.text)
        png_bytes = r.content

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    img_id = str(uuid.uuid4())
    out_path = MEDIA_DIR / f"{img_id}.jpg"
    img.save(out_path, format="JPEG", quality=90)
    print("Saved file:", out_path)

    url = f"{settings.BASE_URL}/uploads/images/{img_id}.jpg"
    return img_id, url

# --- ÚJ: SDXL img2img (HF serverless, multipart/form-data) ---
async def generate_sdxl_img2img(
    init_image_path: str,
    prompt: str,
    negative_prompt: str | None = None,
    strength: float = 0.7,
    guidance: float = 7.5,
    steps: int = 30,
) -> tuple[str, str]:
    if not settings.HF_TOKEN:
        raise HTTPException(500, detail="HF_TOKEN not configured")

    model = settings.SDXL_MODEL
    url = HF_ENDPOINT(model)

    # 1) Képet megnyitjuk és **PNG-be** re-encode-oljuk, hogy a MIME és a tartalom is stimmeljen
    try:
        from PIL import Image
        import io, json, uuid, httpx
        img = Image.open(init_image_path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        png_bytes = buf.read()
    except FileNotFoundError:
        raise HTTPException(400, detail=f"Init image not found: {init_image_path}")
    except Exception as e:
        raise HTTPException(400, detail=f"Init image error: {e}")

    files = {
        # MIME és fájlnév is PNG
        "image": ("init.png", png_bytes, "image/png"),
        "inputs": (
            None,
            json.dumps({
                "prompt": prompt,
                "strength": strength,
                "guidance_scale": guidance,
                "num_inference_steps": steps,
                "negative_prompt": negative_prompt or "blurry, deformed hands, watermark, text",
            }),
            "application/json",
        ),
        # HF serverless opciók: várjunk a modelre
        "options": (None, json.dumps({"wait_for_model": True}), "application/json"),
    }
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}", "Accept": "image/png"}

    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(url, headers=headers, files=files)
        if r.status_code != 200:
            # LOG segítség: dobd vissza a HF üzenetét, ezt látod majd a backend logban
            raise HTTPException(502, detail=f"HF {r.status_code}: {r.text[:400]}")

    # mentés mint eddig
    out = Image.open(io.BytesIO(r.content)).convert("RGB")
    img_id = str(uuid.uuid4())
    out_path = MEDIA_DIR / f"{img_id}.jpg"
    out.save(out_path, format="JPEG", quality=90)
    url = f"{settings.BASE_URL}/uploads/images/{img_id}.jpg"
    return img_id, url
