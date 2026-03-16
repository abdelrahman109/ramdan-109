from pathlib import Path
from app.config import UPLOADS_DIR, GENERATED_QR_DIR, GENERATED_TICKETS_DIR
from app.utils import ensure_dirs, now_file_str

# تأكد من إنشاء المجلدات القديمة والجديدة
ensure_dirs(UPLOADS_DIR, GENERATED_QR_DIR)
ensure_dirs(str(Path("static") / "generated" / "tickets"))  # المجلد الجديد

def payment_proof_path(booking_code, ext=".jpg"):
    return str(Path(UPLOADS_DIR) / f"{booking_code}-{now_file_str()}{ext}")

def qr_path(booking_code):
    return str(Path(GENERATED_QR_DIR) / f"{booking_code}.png")

def ticket_path(booking_code):
    """توليد مسار حفظ صورة التذكرة - استخدام المسار الجديد"""
    # استخدام المسار الجديد مباشرة
    new_path = Path("static") / "generated" / "tickets" / f"{booking_code}.png"
    # تأكد من وجود المجلد
    new_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"📁 Ticket will be saved to: {new_path}")  # للتأكد
    return str(new_path)
