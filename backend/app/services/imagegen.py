from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

def make_portrait(title: str, subtitle: str = "", size=(1080, 1350)) -> bytes:
    """
    Cheap placeholder poster for previews (no external API cost).
    """
    img = Image.new("RGB", size, (18, 18, 22))
    d = ImageDraw.Draw(img)

    # subtle stripes background
    for y in range(0, size[1], 40):
        d.line([(0, y), (size[0], y)], fill=(28, 28, 32), width=1)

    font = ImageFont.load_default()

    # title centered
    wrapped = textwrap.fill(title.upper(), width=18)
    bbox = d.multiline_textbbox((0, 0), wrapped, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.multiline_text(((size[0] - tw) // 2, (size[1] - th) // 2 - 60),
                     wrapped, font=font, fill=(240, 240, 240), align="center")

    # subtitle (first hashtag)
    if subtitle:
        sb = d.textbbox((0, 0), subtitle, font=font)
        sw = sb[2] - sb[0]
        d.text(((size[0] - sw) // 2, (size[1] - th) // 2 + 20),
               subtitle, font=font, fill=(200, 200, 200))

    # watermark
    d.text((24, size[1] - 48), "@fit_ai", font=font, fill=(170, 170, 170))

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()
