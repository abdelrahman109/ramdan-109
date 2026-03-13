from app.db import connect
from app.config import EVENT_CAPACITY

def dashboard_stats():
    with connect() as conn:
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
        
        # إحصائيات InstaPay
        instapay_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND status IN ('paid','used')"
        ).fetchone()["s"]
        instapay_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='instapay'"
        ).fetchone()["c"]
        instapay_attendees = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]
        instapay_contributions = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # إحصائيات المحفظة
        wallet_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND status IN ('paid','used')"
        ).fetchone()["s"]
        wallet_count = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE payment_method='wallet'"
        ).fetchone()["c"]
        wallet_attendees = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]
        wallet_contributions = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # =============== إحصائيات جديدة (المطلوبة) ===============
        
        # إجمالي عدد الضيوف الإضافيين (extra_people)
        total_extra_people = conn.execute(
            "SELECT COALESCE(SUM(extra_people),0) s FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]
        
        # إجمالي عدد البروشات والميداليات المطلوبة
        total_pin_medal = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND pin_medal=1 AND status IN ('paid','used')"
        ).fetchone()["c"]
        
        # إجمالي عدد الضيوف الكلي (الأساسي + الإضافيين)
        total_guests = attendees + total_extra_people
        
        # تعديل السعة المتبقية بناءً على إجمالي الضيوف
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
        "remaining": remaining_capacity,  # تم التعديل لاستخدام total_guests
        "latest": latest,
        
        # إحصائيات InstaPay كاملة
        "instapay_total": instapay_total,
        "instapay_count": instapay_count,
        "instapay_attendees": instapay_attendees,
        "instapay_contributions": instapay_contributions,
        
        # إحصائيات المحفظة كاملة
        "wallet_total": wallet_total,
        "wallet_count": wallet_count,
        "wallet_attendees": wallet_attendees,
        "wallet_contributions": wallet_contributions,
        
        # =============== الإحصائيات الجديدة ===============
        "total_extra_people": total_extra_people,    # إجمالي الضيوف الإضافيين
        "total_pin_medal": total_pin_medal,          # إجمالي البروشات المطلوبة
        "total_guests": total_guests,                 # إجمالي الضيوف الكلي
    }
