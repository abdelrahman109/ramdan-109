from app.db import connect
from app.config import EVENT_CAPACITY

def dashboard_stats():
    with connect() as conn:
        # التحقق من وجود الأعمدة الجديدة
        cursor = conn.execute("PRAGMA table_info(bookings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # إحصائيات أساسية
        total = conn.execute("SELECT COUNT(*) c FROM bookings").fetchone()["c"]
        paid = conn.execute("SELECT COUNT(*) c FROM bookings WHERE status IN ('paid','used')").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) c FROM bookings WHERE status IN ('pending_proof','pending_review')").fetchone()["c"]
        used = conn.execute("SELECT COUNT(*) c FROM bookings WHERE status='used'").fetchone()["c"]
        
        # الحضور والمساهمين
        attendees = conn.execute("SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND status IN ('paid','used')").fetchone()["c"]
        contributors = conn.execute("SELECT COUNT(*) c FROM bookings WHERE is_attending=0 AND status IN ('paid','used')").fetchone()["c"]
        
        # إجمالي الإيرادات
        revenue = conn.execute("SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE status IN ('paid','used')").fetchone()["s"]
        
        # آخر الحجوزات
        latest = conn.execute("SELECT * FROM bookings ORDER BY id DESC LIMIT 10").fetchall()
        
        # =============== إحصائيات InstaPay ===============
        # عدد العمليات
        instapay_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='instapay' AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        # قيمة الحضور
        instapay_attendees_value = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # قيمة المساهمات
        instapay_contributions_value = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # عدد الحضور (للعرض فقط)
        instapay_attendees_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='instapay' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        # عدد المساهمات (للعرض فقط)
        instapay_contributions_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='instapay' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        instapay_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # =============== إحصائيات المحفظة ===============
        # عدد العمليات
        wallet_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='wallet' AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        # قيمة الحضور
        wallet_attendees_value = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # قيمة المساهمات
        wallet_contributions_value = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # عدد الحضور (للعرض فقط)
        wallet_attendees_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='wallet' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        # عدد المساهمات (للعرض فقط)
        wallet_contributions_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='wallet' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        wallet_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # =============== إحصائيات الضيوف والبروش ===============
        if 'extra_people' in columns:
            total_extra_people = conn.execute(
                "SELECT COALESCE(SUM(extra_people),0) s FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
            ).fetchone()["s"]
        else:
            total_extra_people = 0
            
        if 'pin_medal' in columns:
            total_pin_medal = conn.execute(
                "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND pin_medal=1 AND status IN ('paid','used')"
            ).fetchone()["c"]
        else:
            total_pin_medal = 0
        
        # إحصائيات تفصيلية للضيوف
        attendees_with_extra = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND extra_people>0 AND status IN ('paid','used')"
        ).fetchone()["c"] if 'extra_people' in columns else 0
        
        attendees_without_extra = attendees - attendees_with_extra
        
        total_guests = attendees + total_extra_people
        remaining_capacity = max(EVENT_CAPACITY - total_guests, 0)

    return {
        # أساسيات
        "total": total,
        "paid": paid,
        "pending": pending,
        "used": used,
        "attendees": attendees,
        "contributors": contributors,
        "revenue": revenue,
        "remaining": remaining_capacity,
        "latest": latest,
        
        # =============== إحصائيات InstaPay ===============
        "instapay": {
            "count": instapay_count,                          # عدد العمليات (حصر)
            "attendees_value": instapay_attendees_value,      # قيمة الحضور (بالجنيه)
            "contributions_value": instapay_contributions_value, # قيمة المساهمات (بالجنيه)
            "attendees_count": instapay_attendees_count,      # عدد الحضور (للعرض)
            "contributions_count": instapay_contributions_count, # عدد المساهمات (للعرض)
            "total": instapay_total                            # الإجمالي الكلي
        },
        
        # =============== إحصائيات المحفظة ===============
        "wallet": {
            "count": wallet_count,                             # عدد العمليات (حصر)
            "attendees_value": wallet_attendees_value,         # قيمة الحضور (بالجنيه)
            "contributions_value": wallet_contributions_value, # قيمة المساهمات (بالجنيه)
            "attendees_count": wallet_attendees_count,         # عدد الحضور (للعرض)
            "contributions_count": wallet_contributions_count, # عدد المساهمات (للعرض)
            "total": wallet_total                               # الإجمالي الكلي
        },
        
        # =============== إحصائيات الضيوف والبروش ===============
        "guests": {
            "total_guests": total_guests,
            "attendees": attendees,
            "extra_people": total_extra_people,
            "with_extra": attendees_with_extra,
            "without_extra": attendees_without_extra
        },
        
        "pin_medal": {
            "count": total_pin_medal
        }
    }
