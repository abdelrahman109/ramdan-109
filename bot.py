from pathlib import Path
import telebot
from telebot import types

from app.config import TELEGRAM_BOT_TOKEN, EVENT_NAME, EVENT_TIME, EVENT_PRE_ARRIVAL_TEXT, EVENT_LOCATION, EVENT_MAP, ACCOUNT_NAME_AR, ACCOUNT_NAME_EN, INSTAPAY_PHONE, WALLET_PHONE, INSTAPAY_LINK, ADMIN_CHAT_IDS
from app.constants import TICKET_FULL, TICKET_BREAKFAST, TICKET_CONTRIBUTION, CONTRIBUTION_AMOUNTS, TICKETS, PAY_INSTAPAY, PAY_WALLET
from app.db import init_db
from app.utils import normalize_phone, is_valid_phone
from app.services import set_session, get_session, clear_session, create_booking, update_payment_proof, get_booking_by_code, get_booking_by_id
from app.storage import payment_proof_path
from app.notifications import notify_admin_new_proof, send_ticket_message, send_thank_you_message, send_rejected_message
from app.services import approve_booking, reject_booking, generate_ticket_for_booking

init_db()
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

STATE_SELECT_TICKET = "select_ticket"
STATE_SELECT_CONTRIBUTION_AMOUNT = "select_contribution_amount"
STATE_ENTER_NAME = "enter_name"
STATE_ENTER_PHONE = "enter_phone"
STATE_WAITING_PAYMENT_PROOF = "waiting_payment_proof"

def main_reply_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("ابدأ الحجز"), types.KeyboardButton("أنواع التذاكر"))
    kb.add(types.KeyboardButton("طرق الدفع"), types.KeyboardButton("معلومات الحفل"))
    return kb

def ticket_inline_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("حضور + إفطار + ميدالية + بروش — 565", callback_data=f"ticket:{TICKET_FULL}"))
    kb.row(types.InlineKeyboardButton("حضور + إفطار فقط — 415", callback_data=f"ticket:{TICKET_BREAKFAST}"))
    kb.row(types.InlineKeyboardButton("مساهمة بدون حضور ❤️", callback_data=f"ticket:{TICKET_CONTRIBUTION}"))
    return kb

def contribution_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(*[types.InlineKeyboardButton(f"{amt} جنيه", callback_data=f"amount:{amt}") for amt in CONTRIBUTION_AMOUNTS])
    return kb

def payment_method_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("InstaPay", callback_data=f"pay:{PAY_INSTAPAY}"))
    kb.row(types.InlineKeyboardButton("محفظة إلكترونية", callback_data=f"pay:{PAY_WALLET}"))
    return kb

def event_info_text():
    return f"🎟 {EVENT_NAME}\n\n🕠 الموعد: {EVENT_TIME}\n⏰ {EVENT_PRE_ARRIVAL_TEXT}\n\n📍 المكان: {EVENT_LOCATION}\n{EVENT_MAP}"

def payment_info_text():
    return (
        "طرق الدفع المتاحة\n\n"
        "1) InstaPay\n"
        f"اسم الحساب: {ACCOUNT_NAME_AR}\n"
        f"Account Name: {ACCOUNT_NAME_EN}\n"
        f"رقم الموبايل: {INSTAPAY_PHONE}\n"
        f"لينك الدفع: {INSTAPAY_LINK}\n\n"
        "2) محفظة إلكترونية\n"
        f"رقم الموبايل: {WALLET_PHONE}"
    )

def ticket_types_text():
    return "أنواع التذاكر\n\n1) حضور الحفل + الإفطار + ميدالية + بروش — 565\n2) حضور الحفل + إفطار فقط — 415\n3) مساهمة بدون حضور — من 200 إلى 1000"

@bot.message_handler(commands=["start"])
def start(message):
    clear_session(message.chat.id)
    set_session(message.chat.id, STATE_SELECT_TICKET, {})
    bot.send_message(message.chat.id, event_info_text(), reply_markup=main_reply_keyboard())
    bot.send_message(message.chat.id, "اختر نوع التذكرة:", reply_markup=ticket_inline_keyboard())

@bot.message_handler(func=lambda m: m.text in ["ابدأ الحجز", "أنواع التذاكر", "طرق الدفع", "معلومات الحفل"])
def quick_actions(message):
    if message.text == "ابدأ الحجز":
        clear_session(message.chat.id)
        set_session(message.chat.id, STATE_SELECT_TICKET, {})
        bot.send_message(message.chat.id, "اختر نوع التذكرة:", reply_markup=ticket_inline_keyboard())
    elif message.text == "أنواع التذاكر":
        bot.send_message(message.chat.id, ticket_types_text(), reply_markup=main_reply_keyboard())
        bot.send_message(message.chat.id, "اختر نوع التذكرة:", reply_markup=ticket_inline_keyboard())
    elif message.text == "طرق الدفع":
        bot.send_message(message.chat.id, payment_info_text(), reply_markup=main_reply_keyboard())
    elif message.text == "معلومات الحفل":
        bot.send_message(message.chat.id, event_info_text(), reply_markup=main_reply_keyboard())

@bot.callback_query_handler(func=lambda c: c.data.startswith("ticket:"))
def on_ticket(c):
    ticket_type = c.data.split(":", 1)[1]
    if ticket_type == TICKET_CONTRIBUTION:
        set_session(c.message.chat.id, STATE_SELECT_CONTRIBUTION_AMOUNT, {"ticket_type": ticket_type})
        bot.send_message(c.message.chat.id, "اختر قيمة المساهمة", reply_markup=contribution_keyboard())
    else:
        set_session(c.message.chat.id, STATE_ENTER_NAME, {"ticket_type": ticket_type, "amount": TICKETS[ticket_type]["amount"]})
        bot.send_message(c.message.chat.id, "اكتب الاسم الكامل", reply_markup=main_reply_keyboard())
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("amount:"))
def on_amount(c):
    amount = int(c.data.split(":", 1)[1])
    session = get_session(c.message.chat.id)
    data = session["data"]
    data["amount"] = amount
    set_session(c.message.chat.id, STATE_ENTER_NAME, data)
    bot.send_message(c.message.chat.id, "اكتب الاسم الكامل", reply_markup=main_reply_keyboard())
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay:"))
def on_payment(c):
    payment_method = c.data.split(":", 1)[1]
    session = get_session(c.message.chat.id)
    if not session:
        bot.answer_callback_query(c.id, "ابدأ من /start")
        return
    data = session["data"]
    booking = create_booking(c.message.chat.id, data["name"], data["phone"], data["ticket_type"], data["amount"], payment_method)
    set_session(c.message.chat.id, STATE_WAITING_PAYMENT_PROOF, {"booking_code": booking["booking_code"], "booking_id": booking["id"]})
    if payment_method == PAY_INSTAPAY:
        text = (
            "الدفع عبر InstaPay\n\n"
            f"اسم صاحب الحساب\n{ACCOUNT_NAME_AR}\n\n"
            f"Account Name\n{ACCOUNT_NAME_EN}\n\n"
            f"رقم الموبايل\n{INSTAPAY_PHONE}\n\n"
            f"رابط الدفع\n{INSTAPAY_LINK}\n\n"
            "بعد التحويل برجاء رفع صورة السداد."
        )
    else:
        text = (
            "الدفع عبر محفظة إلكترونية\n\n"
            f"اسم صاحب الحساب\n{ACCOUNT_NAME_AR}\n\n"
            f"Account Name\n{ACCOUNT_NAME_EN}\n\n"
            f"رقم الموبايل\n{WALLET_PHONE}\n\n"
            "بعد التحويل برجاء رفع صورة السداد."
        )
    bot.send_message(c.message.chat.id, f"تم تسجيل طلبك برقم: {booking['booking_code']}\n\n{text}", reply_markup=main_reply_keyboard())
    bot.answer_callback_query(c.id)

@bot.message_handler(content_types=["photo"])
def on_photo(message):
    session = get_session(message.chat.id)
    if not session or session["state"] != STATE_WAITING_PAYMENT_PROOF:
        bot.reply_to(message, "أرسل /start للبدء أولًا.", reply_markup=main_reply_keyboard())
        return
    booking = get_booking_by_code(session["data"]["booking_code"])
    if not booking:
        bot.reply_to(message, "لم يتم العثور على الحجز.", reply_markup=main_reply_keyboard())
        return
    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    file_data = bot.download_file(file_info.file_path)
    path = payment_proof_path(booking["booking_code"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_data)
    update_payment_proof(booking["id"], path)
    booking = get_booking_by_code(booking["booking_code"])
    
    # إرسال إشعار للأدمن مع الصورة والأزرار
    notify_admin_new_proof(booking)
    
    bot.reply_to(message, "تم استلام إثبات الدفع ✅\nسيتم مراجعته قريبًا.", reply_markup=main_reply_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_admin_decision(call):
    """معالج قرارات الأدمن من الأزرار"""
    
    # التحقق أن المرسل هو أدمن
    if call.from_user.id not in ADMIN_CHAT_IDS:
        bot.answer_callback_query(call.id, "غير مصرح لك بهذا الإجراء")
        return
    
    action, booking_id = call.data.split('_')
    booking_id = int(booking_id)
    
    try:
        if action == 'approve':
            # قبول الدفع
            booking = approve_booking(booking_id)
            
            if booking['is_attending']:
                booking = generate_ticket_for_booking(booking)
                send_ticket_message(booking)
                response_text = "✅ تم قبول الدفع وإرسال التذكرة للمستخدم"
            else:
                send_thank_you_message(booking)
                response_text = "✅ تم قبول المساهمة وإرسال رسالة الشكر"
            
            # تعديل رسالة الأدمن
            if call.message.caption:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=call.message.caption + "\n\n✅ **تم القبول**",
                    reply_markup=None
                )
            
        elif action == 'reject':
            # رفض الدفع
            booking = reject_booking(booking_id)
            send_rejected_message(booking)
            
            # تعديل رسالة الأدمن
            if call.message.caption:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=call.message.caption + "\n\n❌ **تم الرفض**",
                    reply_markup=None
                )
            response_text = "❌ تم رفض الدفع وإشعار المستخدم"
        
        bot.answer_callback_query(call.id, response_text)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"حدث خطأ: {str(e)}")

@bot.message_handler(func=lambda m: True, content_types=["text"])
def on_text(message):
    session = get_session(message.chat.id)
    if not session:
        bot.reply_to(message, "استخدم /start للبدء.", reply_markup=main_reply_keyboard())
        return
    state = session["state"]
    data = session["data"]
    if state == STATE_ENTER_NAME:
        data["name"] = message.text.strip()
        set_session(message.chat.id, STATE_ENTER_PHONE, data)
        bot.reply_to(message, "اكتب رقم الموبايل", reply_markup=main_reply_keyboard())
        return
    if state == STATE_ENTER_PHONE:
        phone = normalize_phone(message.text)
        if not is_valid_phone(phone):
            bot.reply_to(message, "رقم الهاتف غير صحيح. اكتب رقمًا مصريًا صحيحًا يبدأ بـ 01", reply_markup=main_reply_keyboard())
            return
        data["phone"] = phone
        set_session(message.chat.id, "select_payment_method", data)
        bot.send_message(message.chat.id, "اختر طريقة الدفع المناسبة", reply_markup=payment_method_keyboard())
        return
    bot.reply_to(message, "استخدم الأزرار الموجودة بالأسفل أو أرسل /start", reply_markup=main_reply_keyboard())

print("Bot running...")
bot.infinity_polling(skip_pending=True)
