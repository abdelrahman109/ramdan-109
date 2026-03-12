import os
import telebot
from app.config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_IDS, EVENT_NAME, EVENT_TIME, EVENT_LOCATION, EVENT_MAP, EVENT_PRE_ARRIVAL_TEXT, BASE_URL
from app.utils import ticket_label

_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

def notify_admin_new_proof(booking):
    """إرسال إشعار للأدمن مع صورة الإيصال وأزرار قبول/رفض"""
    if not _bot:
        return
    
    # نص الرسالة
    caption = (
        f"📌 طلب دفع جديد\n\n"
        f"👤 الاسم: {booking['name']}\n"
        f"📞 الهاتف: {booking['phone']}\n"
        f"🎫 نوع التذكرة: {ticket_label(booking['ticket_type'])}\n"
        f"💰 المبلغ: {booking['amount']} جنيه\n"
        f"💳 طريقة الدفع: {booking['payment_method']}\n"
        f"🆔 الكود: {booking['booking_code']}\n\n"
        f"رابط المراجعة: {BASE_URL}/admin/bookings/{booking['id']}"
    )
    
    # أزرار القبول والرفض
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn_approve = telebot.types.InlineKeyboardButton(
        "✅ قبول", 
        callback_data=f"approve_{booking['id']}"
    )
    btn_reject = telebot.types.InlineKeyboardButton(
        "❌ رفض", 
        callback_data=f"reject_{booking['id']}"
    )
    btn_review = telebot.types.InlineKeyboardButton(
        "🔍 مراجعة", 
        url=f"{BASE_URL}/admin/bookings/{booking['id']}"
    )
    markup.add(btn_approve, btn_reject, btn_review)
    
    # إرسال الصورة مع الأزرار لكل أدمن
    for admin_chat_id in ADMIN_CHAT_IDS:
        try:
            # لو فيه صورة إيصال، أرسلها
            if booking['payment_proof_path'] and os.path.exists(booking['payment_proof_path']):
                with open(booking['payment_proof_path'], 'rb') as photo:
                    _bot.send_photo(
                        admin_chat_id,
                        photo,
                        caption=caption,
                        reply_markup=markup
                    )
            else:
                # لو مفيش صورة، أرسل رسالة عادية
                _bot.send_message(
                    admin_chat_id,
                    caption + "\n\n⚠️ لا توجد صورة إيصال",
                    reply_markup=markup
                )
        except Exception as e:
            print(f"Error sending to admin {admin_chat_id}: {e}")

def send_rejected_message(booking):
    """إرسال رسالة رفض للمستخدم"""
    if _bot and booking['telegram_chat_id']:
        try:
            _bot.send_message(
                booking['telegram_chat_id'], 
                "❌ لم يتم اعتماد صورة السداد الحالية. برجاء إعادة رفع صورة أوضح أو التواصل مع الإدارة."
            )
        except Exception as e:
            print(f"Error sending rejected: {e}")

def send_ticket_message(booking):
    """إرسال التذكرة للمستخدم بعد القبول (بدون لوجو)"""
    if not _bot or not booking['telegram_chat_id']:
        return
    try:
        # رسالة نصية فقط - من غير لوجو
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
        
        # إرسال الرسالة النصية أولاً
        _bot.send_message(booking['telegram_chat_id'], msg)
        
        # ثم إرسال صورة التذكرة (بدون لوجو إضافي)
        if booking['ticket_image_path'] and os.path.exists(booking['ticket_image_path']):
            with open(booking['ticket_image_path'], "rb") as f:
                _bot.send_photo(booking['telegram_chat_id'], f)
        
    except Exception as e:
        print(f"Error sending ticket: {e}")

def send_thank_you_message(booking):
    """إرسال رسالة شكر للمساهم"""
    if _bot and booking['telegram_chat_id']:
        try:
            _bot.send_message(
                booking['telegram_chat_id'],
                f"❤️ تم تأكيد المساهمة بنجاح\n\n{EVENT_NAME}\n\n💰 قيمة المساهمة\n{booking['amount']} جنيه\n\nنشكر دعمكم الكريم ومساهمتكم في هذا الحدث الإنساني.\nونسأل الله أن يجعلها في ميزان حسناتكم."
            )
        except Exception as e:
            print(f"Error sending thank you: {e}")

def send_broadcast(chat_ids, message):
    """إرسال رسالة جماعية لمجموعة من المستخدمين"""
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
