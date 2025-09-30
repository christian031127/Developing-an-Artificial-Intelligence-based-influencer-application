from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1080, 1350  # IG portrait 4:5

def _load_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def _draw_watermark(draw: ImageDraw.ImageDraw, text: str):
    if not text:
        return
    font = _load_font(36)
    tw = draw.textlength(text, font=font)
    margin = 24
    draw.text((W - tw - margin, H - 36 - margin), text, fill=(255,255,255,160), font=font)

def _wrap(draw, text: str, font, max_w: int) -> str:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return "\n".join(lines[:6])

def preset_clean(title: str, subtitle: str, watermark: str) -> bytes:
    img = Image.new("RGB", (W, H), (245, 246, 248))
    d = ImageDraw.Draw(img)
    d.rectangle((40, 40, W-40, H-40), outline=(220,223,228), width=6)
    ft = _load_font(86)
    wrapped = _wrap(d, title, ft, W - 200)
    d.text((100, 180), wrapped, fill=(16,24,40), font=ft, spacing=10)
    fs = _load_font(42)
    chip_w = int(d.textlength(subtitle, font=fs)) + 40
    chip_y = 180 + 100 + wrapped.count("\n") * 86
    d.rounded_rectangle((100, chip_y, 100+chip_w, chip_y+64), 16, fill=(29,78,216))
    d.text((120, chip_y+12), subtitle, fill=(255,255,255), font=fs)
    _draw_watermark(d, watermark)
    buf = BytesIO(); img.save(buf, "JPEG", quality=92); return buf.getvalue()

def preset_gradient(title: str, subtitle: str, watermark: str) -> bytes:
    top = (79,70,229); bottom = (236,72,153)
    bg = Image.new("RGB", (W,H), top)
    dgrad = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        r = int(top[0]*(1-t)+bottom[0]*t); g = int(top[1]*(1-t)+bottom[1]*t); b = int(top[2]*(1-t)+bottom[2]*t)
        dgrad.line([(0,y),(W,y)], fill=(r,g,b))
    img = bg.filter(ImageFilter.GaussianBlur(0.5))
    d = ImageDraw.Draw(img)
    card = Image.new("RGBA", (W-160, H-260), (255,255,255,60))
    card = ImageOps.expand(card, border=1, fill=(255,255,255,90))
    img.paste(card, (80,130), card)
    ft = _load_font(78)
    wrapped = _wrap(d, title, ft, W - 240)
    d.text((120, 180), wrapped, fill=(255,255,255), font=ft, spacing=8)
    fs = _load_font(40)
    s_w = int(d.textlength(subtitle, font=fs)) + 40
    s_y = 180 + 90 + wrapped.count("\n") * 78
    d.rounded_rectangle((120, s_y, 120+s_w, s_y+60), 24, fill=(255,255,255,180))
    d.text((140, s_y+12), subtitle, fill=(31,41,55), font=fs)
    _draw_watermark(d, watermark)
    buf = BytesIO(); img.save(buf, "JPEG", quality=92); return buf.getvalue()

def preset_polaroid(title: str, subtitle: str, watermark: str) -> bytes:
    bg = Image.new("RGB", (W,H), (245,245,245))
    d = ImageDraw.Draw(bg)
    shadow = Image.new("RGBA", (W-260, H-420), (0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle((0,0,shadow.size[0],shadow.size[1]), 24, fill=(0,0,0,80))
    bg.paste(shadow, (138,172), shadow)
    pol = Image.new("RGB", (W-260, H-420), (255,255,255))
    ph = Image.new("RGB", (pol.size[0]-80, pol.size[1]-200), (210, 220, 230)).filter(ImageFilter.GaussianBlur(0.6))
    pol.paste(ph, (40,40))
    bg.paste(pol, (130,160))
    ft = _load_font(48)
    wrapped = _wrap(d, title, ft, pol.size[0]-120)
    d.text((190, 160+40 + (pol.size[1]-200) + 60), wrapped, fill=(31,41,55), font=ft, spacing=6)
    fs = _load_font(32)
    d.text((190, 160+40 + (pol.size[1]-200) + 140), subtitle, fill=(75,85,99), font=fs)
    _draw_watermark(d, watermark)
    buf = BytesIO(); bg.save(buf, "JPEG", quality=92); return buf.getvalue()

def render_composite(style: str, title: str, subtitle: str, watermark: str) -> bytes:
    s = (style or "clean").lower()
    if s == "gradient":
        return preset_gradient(title, subtitle, watermark)
    if s == "polaroid":
        return preset_polaroid(title, subtitle, watermark)
    return preset_clean(title, subtitle, watermark)
