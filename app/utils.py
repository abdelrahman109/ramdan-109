import os
import re
import secrets
import string
from datetime import datetime
from app.constants import TICKETS, PAYMENT_METHODS

def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def now_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def now_file_str():
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")

def generate_booking_code():
    rand = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"EVT-{rand}"

def generate_token():
    return secrets.token_urlsafe(24)

def ticket_label(ticket_type):
    return TICKETS[ticket_type]["label"]

def payment_label(method):
    return PAYMENT_METHODS.get(method, method)

def normalize_phone(phone):
    return re.sub(r"\s+", "", phone.strip())

def is_valid_phone(phone):
    phone = normalize_phone(phone)
    return bool(re.fullmatch(r"01\d{9}", phone))

def basename(path):
    return os.path.basename(path) if path else ""
