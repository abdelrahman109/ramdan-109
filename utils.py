import io
import os
import secrets
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import qrcode

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / 'uploads' / 'payment_proofs'
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')
EVENT_NAME = os.getenv('EVENT_NAME', 'حفلة 400 شخص')
EVENT_DATE = os.getenv('EVENT_DATE', '2026-04-25 20:00')
EVENT_LOCATION = os.getenv('EVENT_LOCATION', 'القاهرة')
EVENT_CAPACITY = int(os.getenv('EVENT_CAPACITY', '400'))
TICKET_PRICE_EGP = int(os.getenv('TICKET_PRICE_EGP', '500'))
VIP_EXTRA_EGP = int(os.getenv('VIP_EXTRA_EGP', '300'))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'change-me')
INSTAPAY_IPA = os.getenv('INSTAPAY_IPA', 'example@instapay')
INSTAPAY_PHONE = os.getenv('INSTAPAY_PHONE', '01000000000')
WALLET_PHONE = os.getenv('WALLET_PHONE', INSTAPAY_PHONE)


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def new_ticket_code() -> str:
    return f'EVT-{secrets.token_hex(4).upper()}'


def new_secret() -> str:
    return secrets.token_urlsafe(24)


def build_qr_payload(secret: str, full_name: str, booker_name: str, ticket_code: str) -> str:
    query = urlencode({
        'ticket': ticket_code,
        'holder': full_name,
        'booker': booker_name,
    })
    return f'{BASE_URL}/validate/{secret}?{query}'


def build_qr_png(secret: str, full_name: str, booker_name: str, ticket_code: str) -> io.BytesIO:
    payload = build_qr_payload(secret, full_name, booker_name, ticket_code)
    image = qrcode.make(payload)
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf


def build_instapay_message(ticket_code: str, amount: int) -> str:
    return (
        f'ادفع {amount} جنيه عبر InstaPay إلى:\n'
        f'IPA: {INSTAPAY_IPA}\n'
        f'الهاتف: {INSTAPAY_PHONE}\n\n'
        f'احتفظ بكود الحجز التالي:\n'
        f'{ticket_code}\n\n'
        f'بعد الدفع ابعت رقم المرجع ثم ارفع سكرين شوت التحويل داخل البوت.'
    )


def build_wallet_message(ticket_code: str, amount: int) -> str:
    return (
        f'حوّل {amount} جنيه على رقم المحفظة:\n'
        f'{WALLET_PHONE}\n\n'
        f'احتفظ بكود الحجز التالي:\n'
        f'{ticket_code}\n\n'
        f'بعد التحويل ابعت رقم العملية ثم ارفع سكرين شوت الدفع داخل البوت.'
    )
