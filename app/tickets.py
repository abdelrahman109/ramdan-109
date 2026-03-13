import os
from PIL import Image, ImageDraw, ImageFont
from app.config import EVENT_NAME, EVENT_TIME, EVENT_LOCATION
from app.utils import ticket_label
from app.constants import TICKET_CONTRIBUTION, PRICE_EXTRA_MEAL, PRICE_PIN_MEDAL

ASSET_LOGO = "assets/logo109.png"
ASSET_TEMPLATE = "assets/ticket_template.png"

# مسارات خط Arial Bold في أنظمة مختلفة
FONT_PATHS = [
    "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",  # Linux (MS Core Fonts)
    "/usr/share/fonts/truetype/arial/arialbd.ttf",            # Linux بديل
    "C:/Windows/Fonts/arialbd.ttf",                            # Windows
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",      # Mac
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # DejaVu Bold (بديل)
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Liberation Bold (بديل)
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",          # Ubuntu Bold (بديل)
]

def _font(size: int, bold=True):
    """تحميل خط Arial Bold"""
    font_path = None
    for path in FONT_PATHS:
        if os.path.exists(path):
            font_path = path
            break
    
    try:
        if font_path:
            return ImageFont.truetype(font_path, size=size)
        else:
            return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

def create_ticket_image(booking, qr_image_path, out_path):
    """إنشاء صورة التذكرة مع توسيط كل النصوص بخط Arial Bold"""
    
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
        logo.thumbnail((250, 250))
        img.paste(logo, ((1200 - logo.width) // 2, 40), logo)
    
    # تحديد الأحجام - كلها Arial Bold
    title_font1 = _font(60)      # Arial Bold 60 للسطر الأول
    title_font2 = _font(60)      # Arial Bold 60 للسطر الثاني
    name_font = _font(36)        # Arial Bold 36 للاسم
    body_font = _font(32)        # Arial Bold 32 للنصوص العادية
    small_font = _font(24)       # Arial Bold 24 للنصوص الصغيرة
    
    y = 320  # بداية الكتابة بعد اللوجو
    
    # العنوان على 3 أسطر
    draw.text((600, y), "حفل إفطار وتكريم", fill="#7a5a12", font=title_font1, anchor="mt")
    y += 100
    draw.text((600, y), "أسر شهداء الدفعة 109", fill="#7a5a12", font=title_font2, anchor="mt")
    y += 85
    draw.text((600, y), "كليات ومعاهد عسكرية", fill="#7a5a12", font=title_font2, anchor="mt")
    y += 120
    
    # اسم الشخص
    draw.text((600, y), f"الاسم: {booking['name']}", fill="black", font=name_font, anchor="mt")
    y += 70
    
    # نوع التذكرة
    draw.text((600, y), f"نوع التذكرة: {ticket_label(booking['ticket_type'])}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # كود التذكرة
    draw.text((600, y), f"كود التذكرة: {booking['booking_code']}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # تفاصيل الحضور (للتذاكر العادية فقط)
    if booking['ticket_type'] != TICKET_CONTRIBUTION:
        # استخدام الأقواس المربعة بدل .get
        base_amount = 150
        extra_people = booking['extra_people'] if 'extra_people' in booking.keys() else 0
        extra_cost = extra_people * PRICE_EXTRA_MEAL
        pin_medal = booking['pin_medal'] if 'pin_medal' in booking.keys() else 0
        pin_cost = PRICE_PIN_MEDAL if pin_medal else 0
        
        draw.text((600, y), f"القيمة الأساسية: {base_amount} جنيه", fill="black", font=body_font, anchor="mt")
        y += 50
        if extra_people > 0:
            draw.text((600, y), f"أفراد إضافيين: {extra_people} × {PRICE_EXTRA_MEAL} = {extra_cost} جنيه", fill="black", font=body_font, anchor="mt")
            y += 50
        if pin_medal:
            draw.text((600, y), f"بروش + ميدالية: {PRICE_PIN_MEDAL} جنيه", fill="black", font=body_font, anchor="mt")
            y += 50
    
    # إجمالي المبلغ
    draw.text((600, y), f"الإجمالي: {booking['amount']} جنيه", fill="#9a7b2f", font=name_font, anchor="mt")
    y += 70
    
    # موعد الحفل
    draw.text((600, y), f"موعد الحفل: {EVENT_TIME}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # مكان الحفل
    draw.text((600, y), f"المكان: {EVENT_LOCATION}", fill="black", font=body_font, anchor="mt")
    y += 60
    
    # QR Code
    if os.path.exists(qr_image_path):
        qr = Image.open(qr_image_path).convert("RGB").resize((400, 400))
        img.paste(qr, ((1200 - 400) // 2, 1000))
    
    # النص السفلي
    draw.text((600, 1480), "التذكرة صالحة لدخول مرة واحدة فقط", fill="#8a0000", font=body_font, anchor="mt")
    draw.text((600, 1540), "يرجى الاحتفاظ بهذه التذكرة وإبرازها عند الدخول", fill="black", font=small_font, anchor="mt")
    
    # حفظ الصورة
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, quality=95)
