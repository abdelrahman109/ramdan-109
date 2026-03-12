from app.db import connect
from app.config import EVENT_CAPACITY

def dashboard_stats():
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) c FROM bookings"
        ).fetchone()["c"]

        paid = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE status IN ('paid','used')"
        ).fetchone()["c"]

        pending = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE status IN ('pending_proof','pending_review')"
        ).fetchone()["c"]

        used = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE status='used'"
        ).fetchone()["c"]

        attendees = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["c"]

        contributors = conn.execute(
            "SELECT COUNT(*) c FROM bookings WHERE is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["c"]

        revenue = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE status IN ('paid','used')"
        ).fetchone()["s"]

        latest = conn.execute(
            "SELECT * FROM bookings ORDER BY id DESC LIMIT 10"
        ).fetchall()

        instapay_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND status IN ('paid','used')"
        ).fetchone()["s"]

        wallet_total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND status IN ('paid','used')"
        ).fetchone()["s"]

        instapay_attendees = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]

        wallet_attendees = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND is_attending=1 AND status IN ('paid','used')"
        ).fetchone()["s"]

        instapay_contributions = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='instapay' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["s"]

        wallet_contributions = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE payment_method='wallet' AND is_attending=0 AND status IN ('paid','used')"
        ).fetchone()["s"]

    return {
        "total": total,
        "paid": paid,
        "pending": pending,
        "used": used,
        "attendees": attendees,
        "contributors": contributors,
        "revenue": revenue,
        "remaining": max(EVENT_CAPACITY - attendees, 0),
        "latest": latest,
        "instapay_total": instapay_total,
        "wallet_total": wallet_total,
        "instapay_attendees": instapay_attendees,
        "wallet_attendees": wallet_attendees,
        "instapay_contributions": instapay_contributions,
        "wallet_contributions": wallet_contributions,
    }
