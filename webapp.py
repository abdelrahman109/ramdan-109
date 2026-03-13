from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from app.config import SECRET_KEY, ADMIN_PASSWORD, EVENT_NAME
from app.db import init_db, connect

app = Flask(__name__)
app.secret_key = SECRET_KEY
init_db()

def is_admin():
    return session.get("admin_logged_in") is True

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_bookings"))
        flash("كلمة المرور غير صحيحة")
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_admin():
        return redirect(url_for("admin_login"))
    return redirect(url_for("admin_bookings"))

@app.route("/admin/bookings")
def admin_bookings():
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    with connect() as conn:
        bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    return render_template("admin/bookings_simple.html", bookings=bookings)

@app.route("/admin/bookings/<int:booking_id>/approve", methods=["POST"])
def admin_approve_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE bookings SET status='paid', approved_at=datetime('now') WHERE id=?",
                (booking_id,)
            )
        flash(f"✅ تم قبول الحجز {booking_id}")
    except Exception as e:
        flash(f"❌ خطأ: {str(e)}")
    
    return redirect(url_for("admin_bookings"))

@app.route("/admin/bookings/<int:booking_id>/reject", methods=["POST"])
def admin_reject_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        with connect() as conn:
            conn.execute(
                "UPDATE bookings SET status='rejected', rejected_at=datetime('now') WHERE id=?",
                (booking_id,)
            )
        flash(f"❌ تم رفض الحجز {booking_id}")
    except Exception as e:
        flash(f"❌ خطأ: {str(e)}")
    
    return redirect(url_for("admin_bookings"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
