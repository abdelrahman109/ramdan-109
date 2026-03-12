from pathlib import Path
from app.config import UPLOADS_DIR, GENERATED_QR_DIR, GENERATED_TICKETS_DIR
from app.utils import ensure_dirs, now_file_str

ensure_dirs(UPLOADS_DIR, GENERATED_QR_DIR, GENERATED_TICKETS_DIR)

def payment_proof_path(booking_code, ext=".jpg"):
    return str(Path(UPLOADS_DIR) / f"{booking_code}-{now_file_str()}{ext}")

def qr_path(booking_code):
    return str(Path(GENERATED_QR_DIR) / f"{booking_code}.png")

def ticket_path(booking_code):
    return str(Path(GENERATED_TICKETS_DIR) / f"{booking_code}.png")
