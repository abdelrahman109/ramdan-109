import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_IDS = [int(x.strip()) for x in os.getenv("ADMIN_CHAT_IDS", "").split(",") if x.strip().isdigit()]

EVENT_NAME = os.getenv("EVENT_NAME", "حفل إفطار أسر شهداء الدفعة ١٠٩ كليات ومعاهد عسكرية")
EVENT_TIME = os.getenv("EVENT_TIME", "5:30 مساءً")
EVENT_PRE_ARRIVAL_TEXT = os.getenv("EVENT_PRE_ARRIVAL_TEXT", "يفضل التواجد قبل الحفل بساعة لتسهيل عملية الدخول")
EVENT_LOCATION = os.getenv("EVENT_LOCATION", "دار الأسلحة والذخيرة")
EVENT_MAP = os.getenv("EVENT_MAP", "")
EVENT_CAPACITY = int(os.getenv("EVENT_CAPACITY", "400"))

ACCOUNT_NAME_AR = os.getenv("ACCOUNT_NAME_AR", "")
ACCOUNT_NAME_EN = os.getenv("ACCOUNT_NAME_EN", "")
INSTAPAY_PHONE = os.getenv("INSTAPAY_PHONE", "")
WALLET_PHONE = os.getenv("WALLET_PHONE", "")
INSTAPAY_LINK = os.getenv("INSTAPAY_LINK", "")

DB_PATH = os.getenv("DB_PATH", "instance/tickets.db")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads/payment_proofs")
GENERATED_TICKETS_DIR = os.getenv("GENERATED_TICKETS_DIR", "static/generated/tickets")
GENERATED_QR_DIR = os.getenv("GENERATED_QR_DIR", "generated/qr")
