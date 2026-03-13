import sqlite3
from contextlib import contextmanager
from app.config import DB_PATH
from app.utils import ensure_dirs, now_str

ensure_dirs("instance")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def connect():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """إنشاء قاعدة البيانات مع التأكد من وجود جميع الأعمدة"""
    with connect() as conn:
        # إنشاء جدول bookings إذا لم يكن موجوداً
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_chat_id INTEGER,
                booking_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                ticket_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                payment_method TEXT NOT NULL,
                payment_proof_path TEXT,
                status TEXT NOT NULL,
                qr_token TEXT UNIQUE,
                ticket_image_path TEXT,
                is_attending INTEGER NOT NULL DEFAULT 0,
                proof_uploaded_at TEXT,
                approved_at TEXT,
                rejected_at TEXT,
                used_at TEXT,
                gate_name TEXT,
                checked_in_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # إضافة الأعمدة الجديدة إذا لم تكن موجودة
        try:
            conn.execute("ALTER TABLE bookings ADD COLUMN extra_people INTEGER DEFAULT 0")
            print("✅ Column 'extra_people' added successfully")
        except sqlite3.OperationalError:
            # العمود موجود بالفعل
            pass
            
        try:
            conn.execute("ALTER TABLE bookings ADD COLUMN pin_medal BOOLEAN DEFAULT 0")
            print("✅ Column 'pin_medal' added successfully")
        except sqlite3.OperationalError:
            # العمود موجود بالفعل
            pass
        
        # إنشاء جدول settings للعدادات
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT
            )
        ''')
        
        # إضافة عداد البروشات المتاحة (200)
        cursor = conn.execute("SELECT COUNT(*) as count FROM settings WHERE key='total_pin_medal_available'")
        if cursor.fetchone()['count'] == 0:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ('total_pin_medal_available', '200', now_str())
            )
            print("✅ Initialized pin medal counter with 200")
        
        # عداد البروشات المسلمة
        cursor = conn.execute("SELECT COUNT(*) as count FROM settings WHERE key='total_pin_medal_delivered'")
        if cursor.fetchone()['count'] == 0:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ('total_pin_medal_delivered', '0', now_str())
            )
            print("✅ Initialized delivered pin medal counter with 0")
        
        # إنشاء باقي الجداول
        conn.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                booking_code TEXT NOT NULL,
                checked_in_at TEXT NOT NULL,
                gate_name TEXT,
                checked_in_by TEXT,
                result TEXT NOT NULL
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                booking_code TEXT,
                action_type TEXT NOT NULL,
                admin_name TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS broadcast_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_title TEXT,
                message_body TEXT NOT NULL,
                target_group TEXT NOT NULL,
                sent_count INTEGER NOT NULL DEFAULT 0,
                sent_by TEXT,
                sent_at TEXT NOT NULL
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bot_sessions (
                telegram_chat_id INTEGER PRIMARY KEY,
                state TEXT,
                data_json TEXT,
                updated_at TEXT NOT NULL
            )
        ''')
        
        print("✅ Database initialized successfully")
