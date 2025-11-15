import httpx, json
from typing import List, Tuple, Dict, Any
from app.core.settings import settings

SYSTEM_PROMPT = (
    "You are an assistant that writes Instagram captions for a lifestyle persona. "
    "Style: friendly, motivating, concise. Avoid medical/coach claims. No dangerous advice. "
    "Use at most 2 emojis total. English language only."
)

CAPTION_RULES = (
    "Write 1 caption of 90–140 characters for the given topic. "
    "Then propose 10 short, relevant hashtags (lowercase, no diacritics). "
    "Do not include brand tags and do not include #ai unless explicitly asked. "
    "Return strict JSON with keys: caption (string), hashtags (array)."
)

# Szöveg és hashtagek generálása OpenAI segítségével
async def gen_caption_and_tags(
    topic: str,
    category: str,
    custom_text: str | None = None
) -> Tuple[str, List[str]]:
    """
    Generates caption + hashtags via OpenAI.
    No hard-coded brand tags. Ensures 'ai_generated' is present in the result.
    """

    if not settings.OPENAI_API_KEY:
        caption = f"{topic} — quick tip inside."
        tags = ["inspiration", "daily", "motivation", "creative", "ideas", "lifestyle"]
        if "ai_generated" not in tags:
            tags.append("ai_generated")
        return caption, tags[:10]

    style_hint = f"\nStyle hints: {custom_text}" if (custom_text and custom_text.strip()) else ""
    user = f"{CAPTION_RULES}\n\nTopic: {topic}\nCategory: {category}{style_hint}"

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": getattr(settings, "OPENAI_TEXT_MODEL", "gpt-4o-mini"),
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
    tags = [str(h).lstrip("#").lower() for h in (obj.get("hashtags") or []) if isinstance(h, str)]

    # kiszűrjük a tiltottakat
    tags = [t for t in tags if t not in ("fitai", "aifitai", "ai")]

    # garantáljuk az ai_generated taget
    if "ai_generated" not in tags:
        tags.append("ai_generated")

    # ha 10-nél több tag van, az ai_generated maradjon biztosan benne
    if len(tags) > 10:
        # kivesszük, külön vesszük az ai_generated-et
        others = [t for t in tags if t != "ai_generated"]
        # első 9 másik + az ai_generated → összesen max 10
        tags = others[:9] + ["ai_generated"]

    return caption, tags

# Kategória kitalálása kulcsszavak alapján
CATEGORIES = [
    "education", "technology", "finance", "health", "fitness",
    "travel", "food", "lifestyle", "career", "productivity",
]

_KEYWORDS = {
    "education":    ["study", "thesis", "exam", "learn", "university", "school", "notes"],
    "technology":   ["artificial intelligence", "blockchain", "tech", "app", "software", "coding"],
    "finance":      ["etf", "stock", "crypto", "budget", "saving", "invest"],
    "health":       ["mental health", "mindfulness", "wellbeing", "sleep"],
    "fitness":      ["workout", "gym", "training", "run", "yoga"],
    "travel":       ["travel", "trip", "city", "europe", "flight", "hotel"],
    "food":         ["recipe", "food", "coffee", "meal", "snack"],
    "lifestyle":    ["fashion", "design", "home", "decor", "style"],
    "career":       ["job", "career", "interview", "cv", "portfolio"],
    "productivity": ["time", "productivity", "focus", "routine", "tasks", "schedule"],
}

def guess_category(topic: str, caption: str = "") -> str:
    text = f"{topic} {caption}".lower()
    for cat, keys in _KEYWORDS.items():
        if any(k in text for k in keys):
            return cat
    return "lifestyle"  # default


def generate_agent_critique(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valódi LLM-hívás (OpenAI /chat/completions) JSON-kimenettel.
    Visszaad: { insights[], recommendations[], nextDraftConfig{ caption?, hashtags[], image{...} } }
    """
    # ha nincs kulcs, marad a jelenlegi fallback-ágad
    if not settings.OPENAI_API_KEY:
        kpis = payload.get("kpis") or {}
        like_rate = kpis.get("likeRate", 0.0)
        comment_rate = kpis.get("commentRate", 0.0)
        category = (payload.get("category") or "lifestyle").lower()

        insights = [
            "Reach vs likes suggests the hook may be weak.",
            "Caption opening likely not inviting comments.",
        ]
        recs = [
            "Start with a question in the first line (≤100 chars).",
            "Use 2–3 niche hashtags, avoid generic tags.",
        ]
        img = {"style":"clean minimal","framing":"close-up","lighting":"soft daylight","background":"plain","textOverlay":"none"}
        if category == "meal":
            img = {"style":"warm food photography","framing":"top-down","lighting":"warm indoor","background":"wooden","textOverlay":"none"}
        elif category == "fitness":
            img = {"style":"high contrast","framing":"mid-shot","lighting":"gym ambient","background":"plain","textOverlay":"none"}
        elif category == "finance":
            img = {"style":"clean infographic","framing":"close-up","lighting":"neutral","background":"brand color","textOverlay":"short CTA"}

        if comment_rate < 0.003:
            recs.append("End with a direct question to drive comments.")
        if like_rate < 0.015:
            recs.append("Test a bolder thumbnail/cover (higher contrast).")

        return {
            "insights": insights[:3],
            "recommendations": recs[:5],
            "nextDraftConfig": {
                "caption": payload.get("caption")[:100] if payload.get("caption") else "Ask a question to spark comments.",
                "hashtags": (payload.get("hashtags") or [])[:3],
                "image": img,
            },
        }

    # --- valódi LLM hívás ---
    system_prompt = (
        "You are an Instagram content optimization assistant. "
        "Return ONLY valid JSON. No markdown, no explanations."
    )
    user_prompt = f"""
Analyze this Instagram post and give structured insights.

Post:
- category: {payload.get('category')}
- persona:  {payload.get('personaId')}
- title:    {payload.get('title')}
- caption:  {payload.get('caption')}
- hashtags: {', '.join(payload.get('hashtags') or [])}

KPIs:
- impressions:  {payload['kpis'].get('impressions')}
- reach:        {payload['kpis'].get('reach')}
- likes:        {payload['kpis'].get('likes')}
- comments:     {payload['kpis'].get('comments')}
- likeRate:     {payload['kpis'].get('likeRate')}
- commentRate:  {payload['kpis'].get('commentRate')}
- engagementRate:{payload['kpis'].get('engagementRate')}
- score:        {payload['kpis'].get('score')}

Return JSON with:
{{
  "insights": ["2–4 short factual points (<=120 chars)"],
  "recommendations": ["3–5 actionable improvements (<=140 chars)"],
  "nextDraftConfig": {{
     "caption": "improved caption (optional, <=120 chars)",
     "hashtags": ["2–5 niche tags"],
     "image": {{
        "style": "clean minimal | high contrast | warm editorial | cinematic",
        "framing": "close-up | mid-shot | top-down",
        "lighting": "soft daylight | warm indoor | neutral studio | outdoor overcast",
        "background": "plain | textured | brand color | wooden",
        "textOverlay": "none | short CTA"
     }}
  }}
}}
Only JSON output.
""".strip()

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": getattr(settings, "OPENAI_TEXT_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 500,
        "response_format": {"type": "json_object"},
    }

    with httpx.Client(timeout=60) as client:
        r = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        raw = data["choices"][0]["message"]["content"].strip()

    # JSON normalizálás + hiányok pótlása (hogy a frontend mindig kapjon képet is)
    obj = json.loads(raw)
    insights = [str(x)[:120] for x in obj.get("insights", [])][:4]
    recs = [str(x)[:140] for x in obj.get("recommendations", [])][:5]
    cfg = obj.get("nextDraftConfig") or {}
    if not isinstance(cfg, dict):
        cfg = {}
    image = cfg.get("image") or {}
    if not isinstance(image, dict):
        image = {}
    image.setdefault("style", "clean minimal")
    image.setdefault("framing", "close-up")
    image.setdefault("lighting", "soft daylight")
    image.setdefault("background", "plain")
    image.setdefault("textOverlay", "none")
    cfg["image"] = image
    if "hashtags" in cfg and not isinstance(cfg["hashtags"], list):
        cfg["hashtags"] = []

    return {"insights": insights, "recommendations": recs, "nextDraftConfig": cfg}

