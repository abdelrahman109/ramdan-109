import os
import telebot
from app.config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_IDS, EVENT_NAME, EVENT_TIME, EVENT_LOCATION, EVENT_MAP, EVENT_PRE_ARRIVAL_TEXT
from app.utils import ticket_label
from telebot import types

_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

def notify_admin_new_proof(booking):
    if not _bot:
        return

    text = (
        "💳 تم رفع صورة دفع جديدة\n\n"
        f"👤 الاسم: {booking['name']}\n"
        f"📱 الهاتف: {booking['phone']}\n"
        f"🎫 نوع التذكرة: {ticket_label(booking['ticket_type'])}\n"
        f"💰 المبلغ: {booking['amount']} جنيه\n"
        f"💳 طريقة الدفع: {booking['payment_method']}\n"
        f"🆔 كود الحجز: {booking['booking_code']}\n\n"
        "اختر الإجراء المناسب:"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            "✅ اعتماد الدفع",
            callback_data=f"admin_approve:{booking['id']}"
        ),
        types.InlineKeyboardButton(
            "❌ رفض الدفع",
            callback_data=f"admin_reject:{booking['id']}"
        ),
    )
    keyboard.add(
        types.InlineKeyboardButton(
            "فتح الحجز في الداشبورد",
            url=f"{BASE_URL}/admin/bookings/{booking['id']}"
        )
    )

    for cid in ADMIN_CHAT_IDS:
        try:
            proof_path = booking["payment_proof_path"]

            if proof_path and os.path.exists(proof_path):
                with open(proof_path, "rb") as photo:
                    _bot.send_photo(
                        cid,
                        photo,
                        caption=text,
                        reply_markup=keyboard
                    )
            else:
                _bot.send_message(
                    cid,
                    text,
                    reply_markup=keyboard
                )
        except Exception as e:
            print(f"notify_admin_new_proof error: {e}")
def send_rejected_message(booking):
    if _bot and booking["telegram_chat_id"]:
        _bot.send_message(booking["telegram_chat_id"], "❌ لم يتم اعتماد صورة السداد الحالية. برجاء إعادة رفع صورة أوضح أو التواصل مع الإدارة.")

def send_ticket_message(booking):
    if not _bot or not booking["telegram_chat_id"]:
        return
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
    if booking["ticket_image_path"] and os.path.exists(booking["ticket_image_path"]):
        with open(booking["ticket_image_path"], "rb") as f:
            _bot.send_photo(booking["telegram_chat_id"], f)

def send_thank_you_message(booking):
    if _bot and booking["telegram_chat_id"]:
        _bot.send_message(
            booking["telegram_chat_id"],
            f"❤️ تم تأكيد المساهمة بنجاح\n\n{EVENT_NAME}\n\n💰 قيمة المساهمة\n{booking['amount']} جنيه\n\nنشكر دعمكم الكريم ومساهمتكم في هذا الحدث الإنساني.\nونسأل الله أن يجعلها في ميزان حسناتكم."
        )

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
