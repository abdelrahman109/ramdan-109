@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_admin_decision(call):
    """معالج قرارات الأدمن من الأزرار"""
    try:
        print(f"Received callback: {call.data} from user {call.from_user.id}")
        
        # التحقق أن المرسل هو أدمن
        if call.from_user.id not in ADMIN_CHAT_IDS:
            bot.answer_callback_query(call.id, "غير مصرح لك بهذا الإجراء")
            return
        
        action, booking_id_str = call.data.split('_')
        booking_id = int(booking_id_str)
        print(f"Action: {action}, Booking ID: {booking_id}")
        
        # جلب بيانات الحجز
        booking = get_booking_by_id(booking_id)
        if not booking:
            bot.answer_callback_query(call.id, "الحجز غير موجود")
            return
        
        print(f"Booking found: {booking['booking_code']}")
        
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
            try:
                if call.message.caption:
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=call.message.caption + "\n\n✅ **تم القبول**",
                        reply_markup=None
                    )
            except Exception as e:
                print(f"Error editing admin message: {e}")
            
        elif action == 'reject':
            # رفض الدفع
            booking = reject_booking(booking_id)
            send_rejected_message(booking)
            response_text = "❌ تم رفض الدفع وإشعار المستخدم"
            
            try:
                if call.message.caption:
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=call.message.caption + "\n\n❌ **تم الرفض**",
                        reply_markup=None
                    )
            except Exception as e:
                print(f"Error editing admin message: {e}")
        
        bot.answer_callback_query(call.id, response_text)
        
    except Exception as e:
        print(f"Error in admin decision: {e}")
        import traceback
        traceback.print_exc()
        bot.answer_callback_query(call.id, f"حدث خطأ: {str(e)}")
