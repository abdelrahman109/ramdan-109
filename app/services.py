import json
import qrcode
import time
import sqlite3
from app.db import connect
from app.constants import TICKETS, STATUS_PENDING_PROOF, STATUS_PAID, STATUS_REJECTED
from app.utils import generate_booking_code, generate_token, now_str
from app.storage import qr_path, ticket_path
from app.tickets import create_ticket_image

# =============== دوال البروشات ===============
def get_pin_medal_stats():
    """الحصول على إحصائيات البروشات"""
    with connect() as conn:
        available = conn.execute(
            "SELECT value FROM settings WHERE key='total_pin_medal_available'"
        ).fetchone()
        delivered = conn.execute(
            "SELECT value FROM settings WHERE key='total_pin_medal_delivered'"
        ).fetchone()
        
        available_count = int(available['value']) if available else 200
        delivered_count = int(delivered['value']) if delivered else 0
        
        return {
            'available': available_count,
            'delivered': delivered_count,
            'remaining': available_count - delivered_count
        }

def increment_pin_medal_delivered():
    """زيادة عداد البروشات المسلمة عند الدخول"""
    with connect() as conn:
        current = conn.execute(
            "SELECT value FROM settings WHERE key='total_pin_medal_delivered'"
        ).fetchone()
        
        if current:
            new_value = int(current['value']) + 1
            conn.execute(
                "UPDATE settings SET value=?, updated_at=? WHERE key='total_pin_medal_delivered'",
                (str(new_value), now_str())
            )
            return new_value
    return 0

def check_pin_medal_available():
    """التحقق من وجود بروشات متاحة"""
    stats = get_pin_medal_stats()
    return stats['remaining'] > 0

def get_total_guests_stats():
    """الحصول على إحصائيات الضيوف الكلية"""
    with connect() as conn:
        # عدد الحضور الأساسي
        attendees = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        # عدد الضيوف الإضافيين
        extra_people = conn.execute(
            "SELECT COALESCE(SUM(extra_people),0) s FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        total_guests = attendees + extra_people
        
        return {
            'attendees': attendees,
            'extra_people': extra_people,
            'total_guests': total_guests
        }

# =============== دوال الحجوزات الأساسية ===============
def create_booking(chat_id, name, phone, ticket_type, amount, payment_method, extra_people=0, pin_medal=False):
    """إنشاء حجز جديد مع البيانات الإضافية"""
    code = generate_booking_code()
    ts = now_str()
    with connect() as conn:
        # التحقق من وجود البروشات المتاحة إذا كان الحجز يتضمن بروش
        if pin_medal:
            stats = get_pin_medal_stats()
            if stats['remaining'] <= 0:
                raise Exception("عذراً، نفذت كمية البروشات والميداليات")
        
        conn.execute('''
            INSERT INTO bookings (
                telegram_chat_id, booking_code, name, phone, ticket_type, amount,
                payment_method, status, is_attending, extra_people, pin_medal, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            chat_id, code, name, phone, ticket_type, amount, payment_method, 
            STATUS_PENDING_PROOF, 
            1 if TICKETS[ticket_type]["attending"] else 0,
            extra_people, 
            1 if pin_medal else 0,
            ts, ts
        ))
            
        return conn.execute("SELECT * FROM bookings WHERE booking_code = ?", (code,)).fetchone()

def get_booking_by_code(code):
    with connect() as conn:
        return conn.execute("SELECT * FROM bookings WHERE booking_code = ?", (code,)).fetchone()

def get_booking_by_id(booking_id):
    with connect() as conn:
        return conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()

def get_booking_by_qr_token(token):
    with connect() as conn:
        return conn.execute("SELECT * FROM bookings WHERE qr_token = ?", (token,)).fetchone()

def list_bookings(status=None, ticket_type=None, payment_method=None, search=None):
    where, params = [], []
    if status:
        where.append("status=?")
        params.append(status)
    if ticket_type:
        where.append("ticket_type=?")
        params.append(ticket_type)
    if payment_method:
        where.append("payment_method=?")
        params.append(payment_method)
    if search:
        where.append("(booking_code LIKE ? OR name LIKE ? OR phone LIKE ?)")
        params += [f"%{search}%"] * 3
    
    sql = "SELECT * FROM bookings"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"
    
    with connect() as conn:
        return conn.execute(sql, params).fetchall()

def update_payment_proof(booking_id, path):
    ts = now_str()
    with connect() as conn:
        conn.execute('''
            UPDATE bookings SET payment_proof_path=?, proof_uploaded_at=?, 
            status='pending_review', updated_at=? WHERE id=?
        ''', (path, ts, ts, booking_id))

def approve_booking(booking_id, admin_name="admin"):
    ts = now_str()
    with connect() as conn:
        conn.execute('''
            UPDATE bookings SET status=?, approved_at=?, updated_at=? WHERE id=?
        ''', (STATUS_PAID, ts, ts, booking_id))
        booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        conn.execute('''
            INSERT INTO admin_actions (booking_id, booking_code, action_type, admin_name, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (booking_id, booking["booking_code"], "approve_payment", admin_name, ts))
        return booking

def reject_booking(booking_id, admin_name="admin"):
    ts = now_str()
    with connect() as conn:
        conn.execute('''
            UPDATE bookings SET status=?, rejected_at=?, updated_at=? WHERE id=?
        ''', (STATUS_REJECTED, ts, ts, booking_id))
        booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        conn.execute('''
            INSERT INTO admin_actions (booking_id, booking_code, action_type, admin_name, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (booking_id, booking["booking_code"], "reject_payment", admin_name, ts))
        return booking

def generate_ticket_for_booking(booking):
    token = booking["qr_token"] or generate_token()
    qpath = qr_path(booking["booking_code"])
    qrcode.make(token).save(qpath)
    tpath = ticket_path(booking["booking_code"])
    create_ticket_image(booking, qpath, tpath)
    
    with connect() as conn:
        conn.execute('''
            UPDATE bookings SET qr_token=?, ticket_image_path=?, updated_at=? WHERE id=?
        ''', (token, tpath, now_str(), booking["id"]))
        return conn.execute("SELECT * FROM bookings WHERE id = ?", (booking["id"],)).fetchone()

def validate_for_checkin(qr_token):
    booking = get_booking_by_qr_token(qr_token)
    if not booking:
        return {"status": "invalid", "message": "تذكرة غير صالحة", "booking": None}
    if not booking["is_attending"]:
        return {"status": "invalid", "message": "هذه ليست تذكرة حضور", "booking": booking}
    if booking["status"] == "used":
        return {"status": "already_used", "message": "التذكرة مستخدمة مسبقاً", "booking": booking}
    if booking["status"] != "paid":
        return {"status": "unpaid", "message": "التذكرة غير مدفوعة", "booking": booking}
    return {"status": "valid", "message": "دخول مسموح", "booking": booking}

def checkin(qr_token, gate_name, checked_in_by):
    """تسجيل دخول مع إعادة المحاولة إذا كانت قاعدة البيانات مقفولة"""
    result = validate_for_checkin(qr_token)
    booking = result["booking"]
    ts = now_str()
    
    if not booking:
        return result
    
    # محاولة التنفيذ مع إعادة المحاولة إذا كانت قاعدة البيانات مقفولة
    max_retries = 5  # زودنا من 3 لـ 5
    for attempt in range(max_retries):
        try:
            with connect() as conn:
                if result["status"] == "valid":
                    conn.execute(
                        "UPDATE bookings SET status='used', used_at=?, gate_name=?, checked_in_by=?, updated_at=? WHERE id=?",
                        (ts, gate_name, checked_in_by, ts, booking["id"])
                    )
                    
                    # لو التذكرة فيها بروش، زود العداد
                    if booking['pin_medal'] and booking['pin_medal'] == 1:
                        increment_pin_medal_delivered()
                        print(f"✅ Pin medal delivered count increased for booking {booking['booking_code']}")
                    
                    conn.execute(
                        "INSERT INTO checkins (booking_id, booking_code, checked_in_at, gate_name, checked_in_by, result) VALUES (?, ?, ?, ?, ?, ?)",
                        (booking["id"], booking["booking_code"], ts, gate_name, checked_in_by, "success")
                    )
                    booking = conn.execute("SELECT * FROM bookings WHERE id=?", (booking["id"],)).fetchone()
                    return {"status": "success", "message": "دخول مسموح", "booking": booking}
                
                conn.execute(
                    "INSERT INTO checkins (booking_id, booking_code, checked_in_at, gate_name, checked_in_by, result) VALUES (?, ?, ?, ?, ?, ?)",
                    (booking["id"], booking["booking_code"], ts, gate_name, checked_in_by, result["status"])
                )
                return result
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"⚠️ Database locked, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(0.5)  # انتظار نصف ثانية قبل إعادة المحاولة
                continue
            else:
                print(f"❌ Database error after {attempt + 1} attempts: {e}")
                raise e
    return result

def set_session(chat_id, state, data):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO bot_sessions (telegram_chat_id, state, data_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_chat_id) DO UPDATE SET
                state=excluded.state,
                data_json=excluded.data_json,
                updated_at=excluded.updated_at
            """,
            (chat_id, state, json.dumps(data, ensure_ascii=False), now_str())
        )

def get_session(chat_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM bot_sessions WHERE telegram_chat_id=?", (chat_id,)).fetchone()
        if not row:
            return None
        return {"state": row["state"], "data": json.loads(row["data_json"]) if row["data_json"] else {}}

def clear_session(chat_id):
    with connect() as conn:
        conn.execute("DELETE FROM bot_sessions WHERE telegram_chat_id=?", (chat_id,))
