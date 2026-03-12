from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from app.config import SECRET_KEY, ADMIN_PASSWORD, EVENT_NAME, EVENT_LOCATION, EVENT_MAP, EVENT_TIME, UPLOADS_DIR
from app.db import init_db, connect
from app.utils import ticket_label, payment_label, basename
from app.analytics import dashboard_stats
from app.reports import bookings_csv_response, checkins_csv_response
from app.services import list_bookings, get_booking_by_id, approve_booking, reject_booking, generate_ticket_for_booking, validate_for_checkin, checkin, get_booking_by_qr_token
from app.notifications import send_ticket_message, send_thank_you_message, send_rejected_message, send_broadcast

app = Flask(__name__)
app.secret_key = SECRET_KEY
init_db()

@app.context_processor
def inject_globals():
    stats = dashboard_stats()
    return {"EVENT_NAME": EVENT_NAME, "EVENT_LOCATION": EVENT_LOCATION, "EVENT_MAP": EVENT_MAP, "EVENT_TIME": EVENT_TIME, "ticket_label": ticket_label, "payment_label": payment_label, "remaining_tickets": stats["remaining"], "basename": basename}

def is_admin():
    return session.get("admin_logged_in") is True

@app.route("/")
def home():
    return render_template("public/home.html")

@app.route("/ticket/<token>")
def ticket_status(token):
    booking = get_booking_by_qr_token(token)
    if not booking:
        return render_template("public/ticket_status.html", status="invalid", booking=None)
    return render_template("public/ticket_status.html", status=booking["status"], booking=booking)

@app.route("/uploads/payment_proofs/<path:filename>")
def uploaded_payment_proof(filename):
    return send_from_directory(UPLOADS_DIR, filename)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("كلمة المرور غير صحيحة")
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_admin():
        return redirect(url_for("admin_login"))
    return render_template("admin/dashboard.html", stats=dashboard_stats())

@app.route("/admin/bookings")
def admin_bookings():
    if not is_admin():
        return redirect(url_for("admin_login"))
    bookings = list_bookings(
        status=request.args.get("status") or None,
        ticket_type=request.args.get("ticket_type") or None,
        payment_method=request.args.get("payment_method") or None,
        search=request.args.get("search") or None,
    )
    return render_template("admin/bookings.html", bookings=bookings)

@app.route("/admin/bookings/<int:booking_id>")
def admin_booking_details(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    booking = get_booking_by_id(booking_id)
    return render_template("admin/booking_details.html", booking=booking)

@app.route("/admin/bookings/<int:booking_id>/approve", methods=["POST"])
def admin_approve_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    booking = approve_booking(booking_id)
    if booking["is_attending"]:
        booking = generate_ticket_for_booking(booking)
        send_ticket_message(booking)
    else:
        send_thank_you_message(booking)
    flash("تم اعتماد الدفع بنجاح")
    return redirect(request.referrer or url_for("admin_bookings"))

@app.route("/admin/bookings/<int:booking_id>/reject", methods=["POST"])
def admin_reject_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    booking = reject_booking(booking_id)
    send_rejected_message(booking)
    flash("تم رفض الدفع")
    return redirect(request.referrer or url_for("admin_bookings"))

@app.route("/admin/bookings/<int:booking_id>/resend-ticket", methods=["POST"])
def admin_resend_ticket(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    booking = get_booking_by_id(booking_id)
    if booking and booking["is_attending"] and booking["status"] in ("paid", "used"):
        send_ticket_message(booking)
        flash("تمت إعادة إرسال التذكرة")
    else:
        flash("لا يمكن إعادة إرسال هذه التذكرة")
    return redirect(url_for("admin_booking_details", booking_id=booking_id))

@app.route("/admin/reports/bookings.csv")
def export_bookings():
    if not is_admin():
        return redirect(url_for("admin_login"))
    return bookings_csv_response()

@app.route("/admin/reports/checkins.csv")
def export_checkins():
    if not is_admin():
        return redirect(url_for("admin_login"))
    return checkins_csv_response()

@app.route("/admin/broadcast", methods=["GET", "POST"])
def admin_broadcast():
    if not is_admin():
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        target = request.form.get("target_group", "attendees")
        message = request.form.get("message", "").strip()
        if message:
            with connect() as conn:
                if target == "attendees":
                    rows = conn.execute("SELECT telegram_chat_id FROM bookings WHERE is_attending=1 AND status IN ('paid','used') AND telegram_chat_id IS NOT NULL").fetchall()
                elif target == "contributors":
                    rows = conn.execute("SELECT telegram_chat_id FROM bookings WHERE is_attending=0 AND status='paid' AND telegram_chat_id IS NOT NULL").fetchall()
                else:
                    rows = conn.execute("SELECT telegram_chat_id FROM bookings WHERE status IN ('paid','used') AND telegram_chat_id IS NOT NULL").fetchall()
                sent = send_broadcast([r["telegram_chat_id"] for r in rows], message)
                conn.execute("INSERT INTO broadcast_logs (message_title, message_body, target_group, sent_count, sent_by, sent_at) VALUES (?, ?, ?, ?, ?, datetime('now'))", ("broadcast", message, target, sent, "admin"))
            flash(f"تم إرسال الرسالة إلى {sent} مستخدم")
        return redirect(url_for("admin_broadcast"))
    return render_template("admin/broadcast.html")

@app.route("/scan")
def scanner_page():
    return render_template("scan/scanner.html")

@app.route("/api/validate-ticket", methods=["POST"])
def api_validate_ticket():
    data = request.get_json(force=True)
    result = validate_for_checkin(data.get("qr_token", ""))
    booking = result.get("booking")
    return jsonify({"status": result["status"], "message": result["message"], "name": booking["name"] if booking else None, "ticket_type": ticket_label(booking["ticket_type"]) if booking else None, "booking_code": booking["booking_code"] if booking else None})

@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    data = request.get_json(force=True)
    result = checkin(data.get("qr_token", ""), data.get("gate_name", ""), data.get("checked_in_by", ""))
    booking = result.get("booking")
    return jsonify({"status": result["status"], "message": result["message"], "name": booking["name"] if booking else None, "ticket_type": ticket_label(booking["ticket_type"]) if booking else None, "booking_code": booking["booking_code"] if booking else None})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
