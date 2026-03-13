from pathlib import Path
import telebot
import traceback
from telebot import types

from app.config import TELEGRAM_BOT_TOKEN, EVENT_NAME, EVENT_TIME, EVENT_PRE_ARRIVAL_TEXT, EVENT_LOCATION, EVENT_MAP, ACCOUNT_NAME_AR, ACCOUNT_NAME_EN, INSTAPAY_PHONE, WALLET_PHONE, INSTAPAY_LINK, ADMIN_CHAT_IDS
from app.constants import TICKET_FULL, TICKET_CONTRIBUTION, PRICE_BASE_ATTENDANCE, PRICE_EXTRA_MEAL, PRICE_PIN_MEDAL, PAY_INSTAPAY, PAY_WALLET
from app.db import init_db
from app.utils import normalize_phone, is_valid_phone
from app.services import set_session, get_session, clear_session, create_booking, update_payment_proof, get_booking_by_code, get_booking_by_id
from app.storage import payment_proof_path
from app.notifications import notify_admin_new_proof, send_ticket_message, send_thank_you_message, send_rejected_message
from app.services import approve_booking, reject_booking, generate_ticket_for_booking

# تهيئة قاعدة البيانات
init_db()

# تهيئة البوت
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# حالات البوت
STATE_SELECT_TICKET = "select_ticket"
STATE_ENTER_CONTRIBUTION_AMOUNT = "enter_contribution_amount"
STATE_ENTER_EXTRA_PEOPLE = "enter_extra_people"
STATE_ASK_PIN_MEDAL = "ask_pin_medal"
STATE_ENTER_NAME = "enter_name"
STATE_ENTER_PHONE = "enter_phone"
STATE_WAITING_PAYMENT_PROOF = "waiting_payment_proof"

# =============== لوحات المفاتيح ===============
def main_reply_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton("ابدأ الحجز"), types.KeyboardButton("أنواع التذاكر"))
    kb.add(types.KeyboardButton("طرق الدفع"), types.KeyboardButton("معلومات الحفل"))
    return kb

def ticket_inline_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🎫 حضور الحفل", callback_data=f"ticket:{TICKET_FULL}"))
    kb.row(types.InlineKeyboardButton("❤️ مساهمة بدون حضور", callback_data=f"ticket:{TICKET_CONTRIBUTION}"))
    return kb

def extra_people_keyboard():
    """كيبورد اختيار عدد الأفراد الإضافيين"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 أنا فقط", callback_data="extra:0"),
        types.InlineKeyboardButton("👥 +1 فرد", callback_data="extra:1"),
        types.InlineKeyboardButton("👥 +2 فرد", callback_data="extra:2"),
        types.InlineKeyboardButton("👥 +3 فرد", callback_data="extra:3"),
        types.InlineKeyboardButton("👥 +4 فرد", callback_data="extra:4"),
        types.InlineKeyboardButton("👥 +5 فرد", callback_data="extra:5"),
    )
    return kb

def pin_medal_keyboard():
    """كيبورد اختيار البروش والميدالية"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(f"✅ نعم (+{PRICE_PIN_MEDAL} جنيه)", callback_data="pin:yes"),
        types.InlineKeyboardButton("❌ لا", callback_data="pin:no"),
    )
    return kb

def payment_method_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("InstaPay", callback_data=f"pay:{PAY_INSTAPAY}"))
    kb.row(types.InlineKeyboardButton("محفظة إلكترونية", callback_data=f"pay:{PAY_WALLET}"))
    return kb

# =============== نصوص ===============
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
    return (
        "أنواع التذاكر:\n\n"
        f"1) 🎫 **حضور الحفل**\n"
        f"   • مساهمة وجبة أسر الشهداء: 150 جنيه\n"
        f"   • وجبة (لكل شخص): {PRICE_EXTRA_MEAL} جنيه\n"
        f"   • بروش + ميدالية (اختياري): {PRICE_PIN_MEDAL} جنيه\n\n"
        f"   مثال: أنت + فرد = 150 + (2×{PRICE_EXTRA_MEAL}) = {150 + (2 * PRICE_EXTRA_MEAL)} جنيه\n\n"
        f"2) ❤️ **مساهمة بدون حضور**\n"
        f"   • اكتب المبلغ اللي تحبه"
    )

# =============== معالجات البوت ===============
@bot.message_handler(commands=["start"])
def start(message):
    try:
        clear_session(message.chat.id)
        set_session(message.chat.id, STATE_SELECT_TICKET, {})
        bot.send_message(message.chat.id, event_info_text(), reply_markup=main_reply_keyboard())
        bot.send_message(message.chat.id, "اختر نوع التذكرة:", reply_markup=ticket_inline_keyboard())
    except Exception as e:
        print(f"Error in start: {e}")
        traceback.print_exc()

@bot.message_handler(func=lambda m: m.text in ["ابدأ الحجز", "أنواع التذاكر", "طرق الدفع", "معلومات الحفل"])
def quick_actions(message):
    try:
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
    except Exception as e:
        print(f"Error in quick_actions: {e}")
        traceback.print_exc()

@bot.callback_query_handler(func=lambda c: c.data.startswith("ticket:"))
def on_ticket(c):
    try:
        ticket_type = c.data.split(":", 1)[1]
        
        if ticket_type == TICKET_CONTRIBUTION:
            # مساهمة
            set_session(c.message.chat.id, STATE_ENTER_CONTRIBUTION_AMOUNT, {"ticket_type": ticket_type})
            bot.send_message(c.message.chat.id, "❤️ **مساهمة بدون حضور**\n\nاكتب قيمة المساهمة التي تريدها (مثلاً: 250 أو 750):", reply_markup=main_reply_keyboard())
        else:
            # حضور
            set_session(c.message.chat.id, STATE_ENTER_EXTRA_PEOPLE, {
                "ticket_type": ticket_type,
                "base_amount": 150,  # مساهمة وجبة أسر الشهداء
                "extra_people": 0,
                "pin_medal": False
            })
            
            price_info = (
                f"🎫 **حضور الحفل**\n\n"
                f"💰 مساهمة وجبة أسر الشهداء: 150 جنيه\n"
                f"🍽️ وجبة (لكل شخص): {PRICE_EXTRA_MEAL} جنيه\n"
                f"🎖️ بروش + ميدالية: {PRICE_PIN_MEDAL} جنيه (اختياري)\n\n"
                f"**ملاحظة:** كل فرد (أساسي أو إضافي) له وجبة بـ {PRICE_EXTRA_MEAL} جنيه\n"
                f"الضيوف من الدرجة الأولى (زوجة - ابن - ابنة)\n\n"
                f"الآن اختر عدد الأفراد الإضافيين:"
            )
            bot.send_message(c.message.chat.id, price_info, reply_markup=extra_people_keyboard())
        
        bot.answer_callback_query(c.id)
    except Exception as e:
        print(f"Error in on_ticket: {e}")
        traceback.print_exc()
        bot.answer_callback_query(c.id, "حدث خطأ، حاول مرة أخرى")

@bot.callback_query_handler(func=lambda c: c.data.startswith("extra:"))
def on_extra_people(c):
    try:
        extra_count = int(c.data.split(":", 1)[1])
        session = get_session(c.message.chat.id)
        data = session["data"]
        data["extra_people"] = extra_count
        
        # حساب عدد الأفراد الكلي (أساسي + إضافيين)
        total_people = 1 + extra_count
        
        # حساب المبلغ: مساهمة وجبة (150) + (عدد الأفراد الكلي × 265)
        current_total = data["base_amount"] + (total_people * PRICE_EXTRA_MEAL)
        
        set_session(c.message.chat.id, STATE_ASK_PIN_MEDAL, data)
        
        # تفاصيل الحساب
        details = f"👤 الأساسي: مساهمة وجبة {data['base_amount']} جنيه + وجبة {PRICE_EXTRA_MEAL} جنيه"
        if extra_count > 0:
            details += f"\n👥 {extra_count} فرد إضافي: {extra_count} × {PRICE_EXTRA_MEAL} = {extra_count * PRICE_EXTRA_MEAL} جنيه"
        
        msg = (
            f"✅ **تفاصيل الحجز:**\n\n"
            f"{details}\n"
            f"💰 **المبلغ الحالي: {current_total} جنيه**\n\n"
            f"🎖️ هل تريد إضافة البروش والميدالية (بـ {PRICE_PIN_MEDAL} جنيه)؟"
        )
        bot.send_message(c.message.chat.id, msg, reply_markup=pin_medal_keyboard())
        bot.answer_callback_query(c.id)
    except Exception as e:
        print(f"Error in on_extra_people: {e}")
        traceback.print_exc()

@bot.callback_query_handler(func=lambda c: c.data.startswith("pin:"))
def on_pin_medal(c):
    try:
        pin_choice = c.data.split(":", 1)[1]
        session = get_session(c.message.chat.id)
        data = session["data"]
        
        data["pin_medal"] = (pin_choice == "yes")
        
        # حساب عدد الأفراد الكلي
        total_people = 1 + data["extra_people"]
        
        # حساب المبلغ النهائي: مساهمة وجبة + (عدد الأفراد الكلي × 265) + (150 لو اختار)
        total = data["base_amount"] + (total_people * PRICE_EXTRA_MEAL)
        if data["pin_medal"]:
            total += PRICE_PIN_MEDAL
        data["amount"] = total
        
        set_session(c.message.chat.id, STATE_ENTER_NAME, data)
        
        # ملخص كامل
        summary = (
            f"✅ **ملخص حجزك:**\n\n"
            f"👤 الأساسي: مساهمة وجبة {data['base_amount']} + وجبة {PRICE_EXTRA_MEAL} = {data['base_amount'] + PRICE_EXTRA_MEAL} جنيه\n"
        )
        if data["extra_people"] > 0:
            summary += f"👥 {data['extra_people']} فرد إضافي: {data['extra_people']} × {PRICE_EXTRA_MEAL} = {data['extra_people'] * PRICE_EXTRA_MEAL} جنيه\n"
        summary += f"🎖️ بروش + ميدالية: {PRICE_PIN_MEDAL if data['pin_medal'] else 0} جنيه\n"
        summary += f"💰 **الإجمالي النهائي: {total} جنيه**\n\n"
        summary += "الآن اكتب الاسم الكامل (رباعي):"
        
        bot.send_message(c.message.chat.id, summary, reply_markup=main_reply_keyboard())
        bot.answer_callback_query(c.id)
    except Exception as e:
        print(f"Error in on_pin_medal: {e}")
        traceback.print_exc()

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay:"))
def on_payment(c):
    try:
        payment_method = c.data.split(":", 1)[1]
        session = get_session(c.message.chat.id)
        if not session:
            bot.answer_callback_query(c.id, "ابدأ من /start")
            return
        
        data = session["data"]
        if "name" not in data or "phone" not in data:
            bot.answer_callback_query(c.id, "بيانات غير كاملة، ابدأ من /start")
            return
        
        # التحقق من وجود البيانات الإضافية
        extra_people = data.get("extra_people", 0)
        pin_medal = data.get("pin_medal", False)
        
        print(f"Creating booking for {data['name']} with amount {data['amount']}")
        print(f"Extra people: {extra_people}, Pin medal: {pin_medal}")
        
        # إنشاء الحجز
        booking = create_booking(
            chat_id=c.message.chat.id,
            name=data["name"],
            phone=data["phone"],
            ticket_type=data["ticket_type"],
            amount=data["amount"],
            payment_method=payment_method,
            extra_people=extra_people,
            pin_medal=pin_medal
        )
        
        if not booking:
            bot.answer_callback_query(c.id, "فشل في إنشاء الحجز")
            return
        
        # حفظ حالة البوت
        set_session(c.message.chat.id, STATE_WAITING_PAYMENT_PROOF, {
            "booking_code": booking["booking_code"], 
            "booking_id": booking["id"]
        })
        
        # رسالة الدفع حسب الطريقة
        if payment_method == PAY_INSTAPAY:
            text = (
                "💰 **الدفع عبر InstaPay**\n\n"
                f"👤 اسم الحساب: {ACCOUNT_NAME_AR}\n"
                f"📞 رقم الموبايل: {INSTAPAY_PHONE}\n"
                f"🔗 رابط الدفع: {INSTAPAY_LINK}\n\n"
                "📌 **بعد التحويل، أرسل صورة الإيصال هنا**"
            )
        else:
            text = (
                "💰 **الدفع عبر محفظة إلكترونية**\n\n"
                f"👤 اسم الحساب: {ACCOUNT_NAME_AR}\n"
                f"📞 رقم الموبايل: {WALLET_PHONE}\n\n"
                "✅ فودافون كاش - أورنج كاش - إتصالات كاش - WE Pay\n\n"
                "📌 **بعد التحويل، أرسل صورة الإيصال هنا**"
            )
        
        # رسالة التأكيد الكاملة
        confirm_msg = (
            f"✅ **تم تسجيل طلبك بنجاح**\n\n"
            f"👤 **الاسم:** {data['name']}\n"
            f"💰 **المبلغ المطلوب:** {data['amount']} جنيه\n"
            f"🔢 **رقم الطلب:** {booking['booking_code']}\n\n"
            f"{text}"
        )
        
        bot.send_message(c.message.chat.id, confirm_msg, reply_markup=main_reply_keyboard())
        bot.answer_callback_query(c.id)
        
    except Exception as e:
        print(f"❌ Error in on_payment: {e}")
        traceback.print_exc()
        bot.answer_callback_query(c.id, "حدث خطأ، حاول مرة أخرى")

@bot.message_handler(content_types=["photo"])
def on_photo(message):
    try:
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
    except Exception as e:
        print(f"Error in on_photo: {e}")
        traceback.print_exc()
        bot.reply_to(message, "حدث خطأ في رفع الصورة، حاول مرة أخرى")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_admin_decision(call):
    """معالج قرارات الأدمن من الأزرار"""
    try:
        print(f"📌 Received callback: {call.data} from admin {call.from_user.id}")
        
        # التحقق أن المرسل هو أدمن
        if call.from_user.id not in ADMIN_CHAT_IDS:
            bot.answer_callback_query(call.id, "⛔ غير مصرح لك بهذا الإجراء")
            return
        
        action, booking_id_str = call.data.split('_')
        booking_id = int(booking_id_str)
        print(f"🔍 Action: {action}, Booking ID: {booking_id}")
        
        # جلب بيانات الحجز
        booking = get_booking_by_id(booking_id)
        if not booking:
            bot.answer_callback_query(call.id, "❌ الحجز غير موجود")
            return
        
        # تحويل sqlite3.Row إلى dict للتعامل الآمن
        booking_dict = {}
        for key in booking.keys():
            booking_dict[key] = booking[key]
        
        print(f"📋 Booking found: {booking_dict.get('booking_code', 'unknown')} - {booking_dict.get('name', 'unknown')}")
        print(f"📋 Extra people: {booking_dict.get('extra_people', 0)}, Pin medal: {booking_dict.get('pin_medal', 0)}")
        
        if action == 'approve':
            # قبول الدفع
            booking_result = approve_booking(booking_id)
            
            if booking_result['is_attending']:
                booking_result = generate_ticket_for_booking(booking_result)
                send_ticket_message(booking_result)
                response_text = "✅ تم قبول الدفع وإرسال التذكرة للمستخدم"
                admin_message = "✅ **تم قبول الدفع** وتم إرسال التذكرة"
            else:
                send_thank_you_message(booking_result)
                response_text = "✅ تم قبول المساهمة وإرسال رسالة الشكر"
                admin_message = "✅ **تم قبول المساهمة** وتم إرسال رسالة الشكر"
            
            # تعديل رسالة الأدمن
            try:
                if call.message.caption:
                    new_caption = call.message.caption + f"\n\n{admin_message}"
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=new_caption,
                        reply_markup=None
                    )
                else:
                    new_text = call.message.text + f"\n\n{admin_message}"
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=new_text,
                        reply_markup=None
                    )
                print("✅ Admin message updated successfully")
            except Exception as e:
                print(f"⚠️ Error editing admin message: {e}")
            
        elif action == 'reject':
            # رفض الدفع
            booking_result = reject_booking(booking_id)
            send_rejected_message(booking_result)
            response_text = "❌ تم رفض الدفع وإشعار المستخدم"
            admin_message = "❌ **تم رفض الدفع** وتم إشعار المستخدم"
            
            # تعديل رسالة الأدمن
            try:
                if call.message.caption:
                    new_caption = call.message.caption + f"\n\n{admin_message}"
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=new_caption,
                        reply_markup=None
                    )
                else:
                    new_text = call.message.text + f"\n\n{admin_message}"
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=new_text,
                        reply_markup=None
                    )
                print("✅ Admin message updated successfully")
            except Exception as e:
                print(f"⚠️ Error editing admin message: {e}")
        
        # إرسال رد للمستخدم
        bot.answer_callback_query(call.id, response_text)
        
    except Exception as e:
        print(f"❌ Error in admin decision: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, f"حدث خطأ: {str(e)}")

@bot.message_handler(func=lambda m: True, content_types=["text"])
def on_text(message):
    try:
        session = get_session(message.chat.id)
        if not session:
            bot.reply_to(message, "استخدم /start للبدء.", reply_markup=main_reply_keyboard())
            return
        state = session["state"]
        data = session["data"]
        
        if state == STATE_ENTER_CONTRIBUTION_AMOUNT:
            try:
                amount_text = message.text.strip().replace(',', '').replace(' ', '')
                amount = int(float(amount_text))
                
                if amount < 50:
                    bot.reply_to(message, "❌ أقل قيمة للمساهمة 50 جنيه. اكتب مبلغ أكبر:")
                    return
                if amount > 50000:
                    bot.reply_to(message, "❌ أكبر قيمة للمساهمة 50000 جنيه. اكتب مبلغ أقل:")
                    return
                
                data["amount"] = amount
                set_session(message.chat.id, STATE_ENTER_NAME, data)
                bot.reply_to(message, f"❤️ تم اختيار مساهمة بقيمة **{amount} جنيه**\n\nالآن اكتب الاسم الكامل (رباعي):", reply_markup=main_reply_keyboard())
                return
                
            except ValueError:
                bot.reply_to(message, "❌ قيمة غير صالحة. اكتب رقماً صحيحاً (مثلاً: 250 أو 750):")
                return
        
        elif state == STATE_ENTER_NAME:
            if not message.text or len(message.text.strip()) < 3:
                bot.reply_to(message, "الاسم قصير جداً، اكتب الاسم الكامل (رباعي)", reply_markup=main_reply_keyboard())
                return
            data["name"] = message.text.strip()
            set_session(message.chat.id, STATE_ENTER_PHONE, data)
            bot.reply_to(message, "اكتب رقم الموبايل", reply_markup=main_reply_keyboard())
            return
            
        elif state == STATE_ENTER_PHONE:
            phone = normalize_phone(message.text)
            if not is_valid_phone(phone):
                bot.reply_to(message, "رقم الهاتف غير صحيح. اكتب رقمًا مصريًا صحيحًا يبدأ بـ 01", reply_markup=main_reply_keyboard())
                return
            data["phone"] = phone
            set_session(message.chat.id, "select_payment_method", data)
            bot.send_message(message.chat.id, "اختر طريقة الدفع المناسبة", reply_markup=payment_method_keyboard())
            return
            
        bot.reply_to(message, "استخدم الأزرار الموجودة بالأسفل أو أرسل /start", reply_markup=main_reply_keyboard())
    except Exception as e:
        print(f"Error in on_text: {e}")
        traceback.print_exc()
        bot.reply_to(message, "حدث خطأ، حاول مرة أخرى")

# =============== تشغيل البوت ===============
if __name__ == "__main__":
    print("✅ Bot is running...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            traceback.print_exc()
            print("🔄 Restarting bot in 5 seconds...")
            import time
            time.sleep(5)
