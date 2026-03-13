import os
from PIL import Image, ImageDraw, ImageFont
from app.config import EVENT_NAME, EVENT_TIME, EVENT_LOCATION
from app.utils import ticket_label

ASSET_LOGO = "assets/logo109.png"
ASSET_TEMPLATE = "assets/ticket_template.png"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def _font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size=size)
    except Exception:
        return ImageFont.load_default()

def create_ticket_image(booking, qr_image_path, out_path):
    """إنشاء صورة التذكرة مع توسيط كل النصوص"""
    
    # فتح القالب أو إنشاء خلفية جديدة
    if os.path.exists(ASSET_TEMPLATE):
        img = Image.open(ASSET_TEMPLATE).convert("RGB").resize((1200, 1600))
    else:
        img = Image.new("RGB", (1200, 1600), "#f7f2e7")
    
    draw = ImageDraw.Draw(img)
    
    # إطار خارجي
    draw.rounded_rectangle((30, 30, 1170, 1570), radius=25, outline="#9a7b2f", width=6)
    draw.rounded_rectangle((60, 60, 1140, 1540), radius=18, outline="#d9b96d", width=2)
    
    # لوجو الدفعة (لو موجود)
    if os.path.exists(ASSET_LOGO):
        logo = Image.open(ASSET_LOGO).convert("RGBA")
        logo.thumbnail((300, 300))
        # توسيط اللوجو
        img.paste(logo, ((1200 - logo.width) // 2, 80), logo)
    
    # تحديد الأحجام
    title_font = _font(48)      # للعنوان الرئيسي
    name_font = _font(36)        # للاسم
    body_font = _font(32)        # للنصوص العادية
    small_font = _font(24)       # للنصوص الصغيرة
    
    y = 400  # بداية الكتابة بعد اللوجو
    
    # اسم الحدث - في النص
    draw.text((600, y), EVENT_NAME, fill="#7a5a12", font=title_font, anchor="mt")
    y += 80
    
    # اسم الشخص - في النص
    draw.text((600, y), f"الاسم: {booking['name']}", fill="black", font=name_font, anchor="mt")
    y += 70
    
    # نوع التذكرة - في النص
    draw.text((600, y), f"نوع التذكرة: {ticket_label(booking['ticket_type'])}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # كود التذكرة - في النص
    draw.text((600, y), f"كود التذكرة: {booking['booking_code']}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # قيمة التذكرة - في النص
    draw.text((600, y), f"القيمة: {booking['amount']} جنيه", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # موعد الحفل - في النص
    draw.text((600, y), f"موعد الحفل: {EVENT_TIME}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # مكان الحفل - في النص
    draw.text((600, y), f"المكان: {EVENT_LOCATION}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # QR Code - في النص
    if os.path.exists(qr_image_path):
        qr = Image.open(qr_image_path).convert("RGB").resize((360, 360))
        # توسيط QR
        img.paste(qr, ((1200 - 360) // 2, 960))
    
    # النص السفلي - في النص
    draw.text((600, 1380), "التذكرة صالحة لدخول مرة واحدة فقط", fill="#8a0000", font=body_font, anchor="mt")
    draw.text((600, 1450), "يرجى الاحتفاظ بهذه التذكرة وإبرازها عند الدخول", fill="black", font=small_font, anchor="mt")
    
    # حفظ الصورة
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, quality=95)
