import httpx, json
from typing import List, Tuple
from app.core.settings import settings

SYSTEM_PROMPT = (
    "You are an assistant that writes Instagram captions for a lifestyle persona. "
    "Style: friendly, motivating, concise. Avoid medical/coach claims. No dangerous advice. "
    "Use at most 2 emojis total. English language only."
)
CAPTION_RULES = (
    "Write 1 caption of 90–140 characters for the given topic. "
    "Then propose 10 short, relevant hashtags (lowercase, no diacritics). "
    "Do not repeat brand tag; do not include #ai unless asked. "
    "Return strict JSON with keys: caption (string), hashtags (array)."
)

async def gen_caption_and_tags(
    topic: str,
    category: str,
    brand_tag: str = "fitai",
    custom_text: str | None = None
) -> Tuple[str, List[str]]:
    """
    Cheap text LLM call. If no key set -> safe fallback.
    """
    if not settings.OPENAI_API_KEY:
        return (
            f"{topic} — save it for later! 💪",
            [brand_tag,"gym","fitness","lifestyle","workout","inspo","fit","training","health","motivation"],
        )

    style_hint = f"\nStyle hints: {custom_text}" if (custom_text and custom_text.strip()) else ""
    user = f"{CAPTION_RULES}\n\nTopic: {topic}\nCategory: {category}\nBrand tag: #{brand_tag}{style_hint}"

    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "temperature": 0.8,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        obj = json.loads(data["choices"][0]["message"]["content"])

    caption = (obj.get("caption") or "").strip()[:160]
    tags = [h.lstrip("#") for h in obj.get("hashtags", []) if 2 <= len(h) <= 24][:10]
    if brand_tag not in tags:
        tags = [brand_tag] + tags
        tags = tags[:10]
    return caption, tags
