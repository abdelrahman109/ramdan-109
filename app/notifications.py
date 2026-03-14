import os
import telebot
import traceback
from app.config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_IDS, EVENT_NAME, EVENT_TIME, EVENT_LOCATION, EVENT_MAP, EVENT_PRE_ARRIVAL_TEXT, BASE_URL
from app.utils import ticket_label
from app.constants import PRICE_EXTRA_MEAL, PRICE_PIN_MEDAL

_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

def notify_admin_new_proof(booking):
    """إرسال إشعار للأدمن مع صورة الإيصال وأزرار قبول/رفض وتفاصيل الحجز"""
    if not _bot:
        return
    
    try:
        # التحقق من وجود المفاتيح المطلوبة
        name = booking['name'] if 'name' in booking.keys() else 'غير معروف'
        phone = booking['phone'] if 'phone' in booking.keys() else 'غير معروف'
        ticket_type = booking['ticket_type'] if 'ticket_type' in booking.keys() else 'غير معروف'
        amount = booking['amount'] if 'amount' in booking.keys() else 0
        payment_method = booking['payment_method'] if 'payment_method' in booking.keys() else 'غير معروف'
        booking_code = booking['booking_code'] if 'booking_code' in booking.keys() else 'غير معروف'
        booking_id = booking['id'] if 'id' in booking.keys() else 0
        is_attending = booking['is_attending'] if 'is_attending' in booking.keys() else 0
        
        # تفاصيل إضافية للحضور
        extra_people = booking['extra_people'] if 'extra_people' in booking.keys() else 0
        pin_medal = booking['pin_medal'] if 'pin_medal' in booking.keys() else 0
        
        # بناء نص التفاصيل الإضافية
        extra_details = ""
        if is_attending:
            extra_details = f"\n👥 أفراد إضافيين: {extra_people}"
            extra_details += f"\n🎖️ بروش + ميدالية: {'نعم' if pin_medal else 'لا'}"
        
        # نص الرسالة
        caption = (
            f"📌 **طلب دفع جديد**\n\n"
            f"👤 **الاسم:** {name}\n"
            f"📞 **الهاتف:** {phone}\n"
            f"🎫 **نوع التذكرة:** {ticket_label(ticket_type)}\n"
            f"💰 **المبلغ:** {amount} جنيه\n"
            f"💳 **طريقة الدفع:** {payment_method}\n"
            f"🆔 **الكود:** {booking_code}\n"
            f"{extra_details}\n\n"
            f"🔗 **رابط المراجعة:** {BASE_URL}/admin/bookings/{booking_id}"
        )
        
        # أزرار القبول والرفض
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        btn_approve = telebot.types.InlineKeyboardButton("✅ قبول", callback_data=f"approve_{booking_id}")
        btn_reject = telebot.types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{booking_id}")
        btn_review = telebot.types.InlineKeyboardButton("🔍 مراجعة", url=f"{BASE_URL}/admin/bookings/{booking_id}")
        markup.add(btn_approve, btn_reject, btn_review)
        
        # إرسال الصورة مع الأزرار لكل أدمن
        for admin_chat_id in ADMIN_CHAT_IDS:
            try:
                payment_proof_path = booking['payment_proof_path'] if 'payment_proof_path' in booking.keys() else None
                if payment_proof_path and os.path.exists(payment_proof_path):
                    with open(payment_proof_path, 'rb') as photo:
                        _bot.send_photo(
                            admin_chat_id,
                            photo,
                            caption=caption,
                            reply_markup=markup,
                            parse_mode='Markdown'
                        )
                else:
                    _bot.send_message(admin_chat_id, caption + "\n\n⚠️ لا توجد صورة إيصال", reply_markup=markup, parse_mode='Markdown')
            except Exception as e:
                print(f"Error sending to admin {admin_chat_id}: {e}")
    except Exception as e:
        print(f"Error in notify_admin_new_proof: {e}")
        traceback.print_exc()

def send_rejected_message(booking):
    """إرسال رسالة رفض للمستخدم"""
    if not _bot:
        return
    
    try:
        chat_id = booking['telegram_chat_id'] if 'telegram_chat_id' in booking.keys() else None
        if chat_id:
            _bot.send_message(
                chat_id, 
                "❌ لم يتم اعتماد صورة السداد الحالية. برجاء إعادة رفع صورة أوضح أو التواصل مع الإدارة."
            )
    except Exception as e:
        print(f"Error sending rejected: {e}")
        traceback.print_exc()

def send_ticket_message(booking):
    """إرسال التذكرة للمستخدم بعد القبول"""
    if not _bot:
        print("❌ Cannot send ticket: no bot")
        return
    
    try:
        chat_id = booking['telegram_chat_id'] if 'telegram_chat_id' in booking.keys() else None
        if not chat_id:
            print("❌ Cannot send ticket: no chat_id")
            return
        
        ticket_type = booking['ticket_type'] if 'ticket_type' in booking.keys() else 'unknown'
        amount = booking['amount'] if 'amount' in booking.keys() else 0
        ticket_image_path = booking['ticket_image_path'] if 'ticket_image_path' in booking.keys() else None
        is_attending = booking['is_attending'] if 'is_attending' in booking.keys() else 0
        
        # تفاصيل إضافية للحضور
        extra_people = booking['extra_people'] if 'extra_people' in booking.keys() else 0
        pin_medal = booking['pin_medal'] if 'pin_medal' in booking.keys() else 0
        
        # بناء نص التفاصيل الإضافية
        extra_details = ""
        if is_attending and (extra_people > 0 or pin_medal):
            extra_details = "\n📋 **تفاصيل الحجز:**"
            if extra_people > 0:
                extra_details += f"\n   • أفراد إضافيين: {extra_people}"
            if pin_medal:
                extra_details += f"\n   • بروش + ميدالية: نعم"
        
        msg = (
            f"🎉 **تم تأكيد الدفع بنجاح**\n\n"
            f"🎟 {EVENT_NAME} 🇪🇬\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            f"🎫 **نوع التذكرة**\n{ticket_label(ticket_type)}\n"
            f"💰 **قيمة التذكرة**\n{amount} جنيه\n"
            f"{extra_details}\n\n"
            f"🕠 **موعد الحفل**\n{EVENT_TIME}\n\n"
            f"⏰ {EVENT_PRE_ARRIVAL_TEXT}\n\n"
            f"📍 **مكان الحفل**\n{EVENT_LOCATION}\n{EVENT_MAP}\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "📲 يرجى الاحتفاظ بالـ QR Code لإبرازه عند الدخول.\n"
            "⚠️ التذكرة صالحة لدخول مرة واحدة فقط."
        )
        _bot.send_message(chat_id, msg, parse_mode='Markdown')
        
        if ticket_image_path and os.path.exists(ticket_image_path):
            with open(ticket_image_path, "rb") as f:
                _bot.send_photo(chat_id, f)
        
        # تم تعديل هذا السطر - إزالة .get()
        name = booking['name'] if 'name' in booking.keys() else 'unknown'
        print(f"✅ Ticket sent to {name}")
        
    except Exception as e:
        print(f"Error sending ticket: {e}")
        traceback.print_exc()

def send_thank_you_message(booking):
    """إرسال رسالة شكر للمساهم"""
    if not _bot:
        return
    
    try:
        chat_id = booking['telegram_chat_id'] if 'telegram_chat_id' in booking.keys() else None
        amount = booking['amount'] if 'amount' in booking.keys() else 0
        
        if chat_id:
            _bot.send_message(
                chat_id,
                f"❤️ **تم تأكيد المساهمة بنجاح**\n\n{EVENT_NAME}\n\n💰 **قيمة المساهمة**\n{amount} جنيه\n\nنشكر دعمكم الكريم ومساهمتكم في هذا الحدث الإنساني.\nونسأل الله أن يجعلها في ميزان حسناتكم.",
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Error sending thank you: {e}")
        traceback.print_exc()

def send_broadcast(chat_ids, message):
    """إرسال رسالة جماعية لمجموعة من المستخدمين"""
    count = 0
    if not _bot:
        return count
    for cid in chat_ids:
        try:
            _bot.send_message(cid, message, parse_mode='Markdown')
            count += 1
        except Exception:
            pass
    return count

# =============== دالة إرسال رسالة للمستخدم (معدلة لدعم العربية) ===============
def send_message_to_user(chat_id, message):
    """إرسال رسالة مباشرة لمستخدم (مع دعم العربية)"""
    if not _bot:
        return False
    
    try:
        # إضافة حرف تحكم RTL في بداية الرسالة
        rtl_message = "\u202B" + message
        
        _bot.send_message(chat_id, rtl_message, parse_mode='Markdown')
        print(f"✅ Message sent to user {chat_id}")
        return True
    except Exception as e:
        print(f"❌ Error sending message to user {chat_id}: {e}")
        return False
