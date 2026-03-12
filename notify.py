import os
import sys

from dotenv import load_dotenv
import telebot

from storage import get_ticket_by_code
from utils import EVENT_DATE, EVENT_LOCATION, EVENT_NAME, build_qr_png

load_dotenv()


def send_paid_ticket_notification(ticket_code: str) -> bool:
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    if not token:
        return False
    ticket = get_ticket_by_code(ticket_code)
    if not ticket:
        return False
    bot = telebot.TeleBot(token, parse_mode='HTML')
    qr = build_qr_png(ticket['qr_secret'], ticket['full_name'], ticket['booker_name'] or ticket['full_name'], ticket['ticket_code'])
    caption = (
        f"🎟 <b>{EVENT_NAME}</b>\n"
        f"اسم الحاضر: {ticket['full_name']}\n"
        f"اسم القائم بالحجز: {ticket['booker_name'] or ticket['full_name']}\n"
        f"الكود: <code>{ticket['ticket_code']}</code>\n"
        f"النوع: {ticket['ticket_type']}\n"
        f"التاريخ: {EVENT_DATE}\n"
        f"المكان: {EVENT_LOCATION}\n"
        f"الحالة: مدفوع"
    )
    bot.send_message(int(ticket['chat_id']), 'تم تأكيد الدفع ✅\nدي تذكرتك:')
    bot.send_photo(int(ticket['chat_id']), qr, caption=caption)
    return True


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python notify.py EVT-XXXX')
    ok = send_paid_ticket_notification(sys.argv[1])
    if not ok:
        raise SystemExit('Failed to notify user')


if __name__ == '__main__':
    main()
