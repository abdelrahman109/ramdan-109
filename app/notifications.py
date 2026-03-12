import os
import telebot
from app.config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_IDS, EVENT_NAME, EVENT_TIME, EVENT_LOCATION, EVENT_MAP, EVENT_PRE_ARRIVAL_TEXT, BASE_URL
from app.utils import ticket_label

_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

def notify_admin_new_proof(booking):
    if not _bot:
        return
    text = (
        "طلب دفع جديد يحتاج مراجعة\n\n"
        f"الاسم: {booking['name']}\n"
        f"نوع التذكرة: {ticket_label(booking['ticket_type'])}\n"
        f"المبلغ: {booking['amount']} جنيه\n"
        f"طريقة الدفع: {booking['payment_method']}\n"
        f"الكود: {booking['booking_code']}\n\n"
        f"رابط المراجعة: {BASE_URL}/admin/bookings/{booking['id']}"
    )
    for cid in ADMIN_CHAT_IDS:
        try:
            _bot.send_message(cid, text)
        except Exception:
            pass

def send_rejected_message(booking):
    if _bot and booking.get("telegram_chat_id"):
        try:
            _bot.send_message(
                booking["telegram_chat_id"], 
                "❌ لم يتم اعتماد صورة السداد الحالية. برجاء إعادة رفع صورة أوضح أو التواصل مع الإدارة."
            )
        except Exception:
            pass

def send_ticket_message(booking):
    if not _bot or not booking.get("telegram_chat_id"):
        return
    try:
        msg = (
            "🎉 تم تأكيد الدفع بنجاح\n\n"
            f"🎟 {EVENT_NAME} 🇪🇬\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            f"🎫 نوع التذكرة\n{ticket_label(booking['ticket_type'])}\n\n"
            f"💰 قيمة التذكرة\n{booking['amount']} جنيه\n\n"
            f"🕠 موعد الحفل\n{EVENT_TIME}\n\n"
            f"⏰ {EVENT_PRE_ARRIVAL_TEXT}\n\n"
            f"📍 مكان الحفل\n{EVENT_LOCATION}\n{EVENT_MAP}\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "📲 يرجى الاحتفاظ بالـ QR Code لإبرازه عند الدخول.\n"
            "⚠️ التذكرة صالحة لدخول مرة واحدة فقط."
        )
        _bot.send_message(booking["telegram_chat_id"], msg)
        
        if booking.get("ticket_image_path") and os.path.exists(booking["ticket_image_path"]):
            with open(booking["ticket_image_path"], "rb") as f:
                _bot.send_photo(booking["telegram_chat_id"], f)
    except Exception as e:
        print(f"Error sending ticket: {e}")

def send_thank_you_message(booking):
    if _bot and booking.get("telegram_chat_id"):
        try:
            _bot.send_message(
                booking["telegram_chat_id"],
                f"❤️ تم تأكيد المساهمة بنجاح\n\n{EVENT_NAME}\n\n💰 قيمة المساهمة\n{booking['amount']} جنيه\n\nنشكر دعمكم الكريم ومساهمتكم في هذا الحدث الإنساني.\nونسأل الله أن يجعلها في ميزان حسناتكم."
            )
        except Exception:
            pass

def send_broadcast(chat_ids, message):
    count = 0
    if not _bot:
        return count
    for cid in chat_ids:
        try:
            _bot.send_message(cid, message)
            count += 1
        except Exception:
            pass
    return count
