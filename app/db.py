import sqlite3
import time
from contextlib import contextmanager
from app.config import DB_PATH
from app.utils import ensure_dirs, now_str

ensure_dirs("instance")

# متغير عام لتخزين الاتصال الوحيد (Singleton pattern)
_connection = None

def get_connection():
    """الحصول على اتصال واحد فقط بقاعدة البيانات (Singleton)"""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        # تفعيل WAL mode لتحسين التزامن
        _connection.execute("PRAGMA journal_mode=WAL")
        # زيادة حجم cache
        _connection.execute("PRAGMA cache_size=10000")
        # تفعيل foreign keys
        _connection.execute("PRAGMA foreign_keys=ON")
        print("✅ Database connection established (WAL mode enabled)")
    return _connection

@contextmanager
def connect():
    """إدارة اتصال قاعدة البيانات - يستخدم نفس الاتصال لكل الطلبات"""
    conn = get_connection()
    retries = 3
    for attempt in range(retries):
        try:
            yield conn
            conn.commit()
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                print(f"⚠️ Database locked, retrying... ({attempt + 1}/{retries})")
                time.sleep(0.5)
                continue
            else:
                conn.rollback()
                raise e

def close_connection():
    """إغلاق اتصال قاعدة البيانات (يستخدم عند إيقاف التطبيق)"""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        print("✅ Database connection closed")

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
        
        # إنشاء جدول checkins
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
        
        # إنشاء جدول admin_actions
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
        
        # إنشاء جدول broadcast_logs
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
        
        # إنشاء جدول bot_sessions
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bot_sessions (
                telegram_chat_id INTEGER PRIMARY KEY,
                state TEXT,
                data_json TEXT,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # =============== جدول سجل الرسائل (جديد) ===============
        conn.execute('''
            CREATE TABLE IF NOT EXISTS message_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                booking_code TEXT NOT NULL,
                admin_name TEXT,
                message TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                status TEXT DEFAULT 'sent'
            )
        ''')
        
        print("✅ Database initialized successfully")
