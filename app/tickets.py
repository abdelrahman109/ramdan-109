import os
from PIL import Image, ImageDraw, ImageFont
from app.config import EVENT_TIME, EVENT_LOCATION
from app.utils import ticket_label

ASSET_LOGO = "assets/logo109.png"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

TITLE_LINE_1 = "حفل إفطار و تكريم أسر الشهداء"
TITLE_LINE_2 = "الدفعة ١٠٩ كليات و معاهد عسكرية"

BG_COLOR = "#f6efe1"
GOLD = "#9a7b2f"
GOLD_LIGHT = "#d8b86a"
TEXT = "#1e1a12"
MUTED = "#6f5d34"

def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def draw_center(draw, text, y, used_font, width, fill=TEXT):
    bbox = draw.textbbox((0, 0), text, font=used_font)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    draw.text((x, y), text, fill=fill, font=used_font)

def create_ticket_image(booking, qr_image_path, out_path):
    width, height = 1200, 1600
    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((24, 24, width - 24, height - 24), radius=28, outline=GOLD, width=7)
    draw.rounded_rectangle((48, 48, width - 48, height - 48), radius=22, outline=GOLD_LIGHT, width=3)
    draw.line((120, 70, 380, 70), fill=GOLD, width=4)
    draw.line((820, 70, 1080, 70), fill=GOLD, width=4)

    y = 95

    if os.path.exists(ASSET_LOGO):
        logo = Image.open(ASSET_LOGO).convert("RGBA").resize((400, 400))
        img.paste(logo, ((width - 400) // 2, y), logo)
    y += 430

    title_font = font(58)
    subtitle_font = font(44)
    name_font = font(50)
    body_font = font(34)
    small_font = font(28)

    draw_center(draw, TITLE_LINE_1, y, title_font, width, fill=GOLD)
    y += 78
    draw_center(draw, TITLE_LINE_2, y, subtitle_font, width, fill=MUTED)
    y += 110

    draw.line((190, y, width - 190, y), fill=GOLD_LIGHT, width=3)
    y += 45

    draw_center(draw, booking["name"], y, name_font, width, fill=TEXT)
    y += 95
    draw_center(draw, f"نوع التذكرة: {ticket_label(booking['ticket_type'])}", y, body_font, width)
    y += 68
    draw_center(draw, f"موعد الحفل: {EVENT_TIME}", y, body_font, width)
    y += 68
    draw_center(draw, f"المكان: {EVENT_LOCATION}", y, body_font, width)
    y += 95

    card_x1, card_y1 = 330, y
    card_x2, card_y2 = 870, y + 460
    draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=28, outline=GOLD, width=4, fill="#fffaf0")

    qr = Image.open(qr_image_path).convert("RGB").resize((380, 380))
    img.paste(qr, ((width - 380) // 2, y + 40))
    y += 520

    draw_center(draw, "VIP INVITATION", y, small_font, width, fill=GOLD)
    y += 52
    draw_center(draw, "التذكرة صالحة لدخول مرة واحدة فقط", y, body_font, width, fill="#7e1f1f")
    y += 56
    draw_center(draw, "يرجى إبراز هذه التذكرة عند الدخول", y, small_font, width, fill=MUTED)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
