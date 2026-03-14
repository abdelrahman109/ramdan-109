from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import os
import atexit
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import SECRET_KEY, ADMIN_PASSWORD, EVENT_NAME, EVENT_LOCATION, EVENT_MAP, EVENT_TIME, UPLOADS_DIR, BASE_URL
from app.db import init_db, connect, close_connection
from app.utils import ticket_label, payment_label, basename
from app.analytics import dashboard_stats
from app.reports import bookings_csv_response, checkins_csv_response
from app.services import list_bookings, get_booking_by_id, approve_booking, reject_booking, generate_ticket_for_booking, validate_for_checkin, checkin, get_booking_by_qr_token, get_pin_medal_stats
from app.notifications import send_ticket_message, send_thank_you_message, send_rejected_message, send_broadcast, send_message_to_user

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.secret_key = SECRET_KEY
init_db()

# إغلاق اتصال قاعدة البيانات عند إيقاف التطبيق
atexit.register(close_connection)

@app.context_processor
def inject_globals():
    stats = dashboard_stats()
    return {
        "EVENT_NAME": EVENT_NAME, 
        "EVENT_LOCATION": EVENT_LOCATION, 
        "EVENT_MAP": EVENT_MAP, 
        "EVENT_TIME": EVENT_TIME, 
        "ticket_label": ticket_label, 
        "payment_label": payment_label, 
        "remaining_tickets": stats["remaining"], 
        "basename": basename,
        "BASE_URL": BASE_URL,
        "stats": stats
    }

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
    
    try:
        stats = dashboard_stats()
        return render_template("admin/dashboard.html", stats=stats)
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash(f"حدث خطأ: {str(e)}")
        return render_template("admin/dashboard.html", stats={})

@app.route("/admin/bookings")
def admin_bookings():
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        bookings = list_bookings(
            status=request.args.get("status") or None,
            ticket_type=request.args.get("ticket_type") or None,
            payment_method=request.args.get("payment_method") or None,
            search=request.args.get("search") or None,
        )
        return render_template("admin/bookings.html", bookings=bookings)
    except Exception as e:
        print(f"Error in admin_bookings: {e}")
        import traceback
        traceback.print_exc()
        flash(f"حدث خطأ: {str(e)}")
        return render_template("admin/bookings.html", bookings=[])

@app.route("/admin/bookings/<int:booking_id>")
def admin_booking_details(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        booking = get_booking_by_id(booking_id)
        if not booking:
            flash("الحجز غير موجود")
            return redirect(url_for("admin_bookings"))
        return render_template("admin/booking_details.html", booking=booking)
    except Exception as e:
        print(f"Error in admin_booking_details: {e}")
        import traceback
        traceback.print_exc()
        flash(f"حدث خطأ: {str(e)}")
        return redirect(url_for("admin_bookings"))

@app.route("/admin/bookings/<int:booking_id>/approve", methods=["POST"])
def admin_approve_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        booking = approve_booking(booking_id)
        
        if not booking:
            flash("❌ الحجز غير موجود")
            return redirect(request.referrer or url_for("admin_bookings"))
        
        if not booking['telegram_chat_id']:
            flash("⚠️ تحذير: لا يوجد معرف محادثة للمستخدم")
            return redirect(request.referrer or url_for("admin_bookings"))
        
        if booking["is_attending"]:
            booking = generate_ticket_for_booking(booking)
            send_ticket_message(booking)
            flash("✅ تم اعتماد الدفع وإرسال التذكرة للمستخدم")
        else:
            send_thank_you_message(booking)
            flash("✅ تم اعتماد المساهمة وإرسال رسالة الشكر")
        
    except Exception as e:
        print(f"Error in approve_booking: {e}")
        import traceback
        traceback.print_exc()
        flash(f"❌ حدث خطأ: {str(e)}")
    
    return redirect(request.referrer or url_for("admin_bookings"))

@app.route("/admin/bookings/<int:booking_id>/reject", methods=["POST"])
def admin_reject_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        booking = reject_booking(booking_id)
        
        if booking and booking['telegram_chat_id']:
            send_rejected_message(booking)
            flash("❌ تم رفض الدفع وإشعار المستخدم")
        else:
            flash("❌ تم رفض الدفع")
        
    except Exception as e:
        print(f"Error in reject_booking: {e}")
        import traceback
        traceback.print_exc()
        flash(f"❌ حدث خطأ: {str(e)}")
    
    return redirect(request.referrer or url_for("admin_bookings"))

@app.route("/admin/bookings/<int:booking_id>/resend-ticket", methods=["POST"])
def admin_resend_ticket(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        booking = get_booking_by_id(booking_id)
        if booking and booking["is_attending"] and booking["status"] in ("paid", "used"):
            if booking['telegram_chat_id']:
                send_ticket_message(booking)
                flash("✅ تمت إعادة إرسال التذكرة")
            else:
                flash("⚠️ لا يمكن إعادة الإرسال: لا يوجد معرف محادثة")
        else:
            flash("⚠️ لا يمكن إعادة إرسال هذه التذكرة")
        
    except Exception as e:
        print(f"Error in resend_ticket: {e}")
        import traceback
        traceback.print_exc()
        flash(f"❌ حدث خطأ: {str(e)}")
    
    return redirect(url_for("admin_booking_details", booking_id=booking_id))

@app.route("/admin/bookings/<int:booking_id>/delete", methods=["POST"])
def admin_delete_booking(booking_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        with connect() as conn:
            booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
            
            if not booking:
                flash("❌ الحجز غير موجود")
                return redirect(request.referrer or url_for("admin_bookings"))
            
            booking_code = booking['booking_code']
            
            # حذف السجلات المرتبطة
            conn.execute("DELETE FROM checkins WHERE booking_id = ?", (booking_id,))
            conn.execute("DELETE FROM admin_actions WHERE booking_id = ?", (booking_id,))
            conn.execute("DELETE FROM message_log WHERE booking_id = ?", (booking_id,))  # حذف سجل الرسائل
            
            # حذف الحجز
            conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            
            # حذف الصور المرتبطة
            try:
                if booking['payment_proof_path'] and os.path.exists(booking['payment_proof_path']):
                    os.remove(booking['payment_proof_path'])
                if booking['ticket_image_path'] and os.path.exists(booking['ticket_image_path']):
                    os.remove(booking['ticket_image_path'])
            except:
                pass
            
            flash(f"✅ تم حذف الحجز {booking_code} نهائياً")
            
    except Exception as e:
        print(f"Error deleting booking: {e}")
        import traceback
        traceback.print_exc()
        flash(f"❌ حدث خطأ في حذف الحجز: {str(e)}")
    
    return redirect(url_for("admin_bookings"))

# =============== رسائل للمستخدم (جديد) ===============
@app.route("/admin/bookings/<int:booking_id>/send-message", methods=["POST"])
def admin_send_message(booking_id):
    """إرسال رسالة للمستخدم وتسجيلها"""
    if not is_admin():
        return redirect(url_for("admin_login"))
    
    try:
        message = request.form.get("message", "").strip()
        if not message:
            flash("⚠️ الرجاء كتابة الرسالة")
            return redirect(url_for("admin_booking_details", booking_id=booking_id))
        
        booking = get_booking_by_id(booking_id)
        if not booking:
            flash("❌ الحجز غير موجود")
            return redirect(url_for("admin_bookings"))
        
        if not booking['telegram_chat_id']:
            flash("⚠️ لا يوجد معرف محادثة للمستخدم")
            return redirect(url_for("admin_booking_details", booking_id=booking_id))
        
        success = send_message_to_user(booking['telegram_chat_id'], message)
        
        if success:
            # تسجيل الرسالة في قاعدة البيانات
            with connect() as conn:
                conn.execute(
                    "INSERT INTO message_log (booking_id, booking_code, admin_name, message, sent_at, status) VALUES (?, ?, ?, ?, datetime('now'), ?)",
                    (booking_id, booking['booking_code'], session.get('admin_name', 'admin'), message, "sent")
                )
            flash("✅ تم إرسال الرسالة بنجاح")
        else:
            flash("❌ فشل إرسال الرسالة")
        
    except Exception as e:
        print(f"Error sending message: {e}")
        import traceback
        traceback.print_exc()
        flash(f"❌ حدث خطأ: {str(e)}")
    
    return redirect(url_for("admin_booking_details", booking_id=booking_id))

@app.route("/admin/bookings/<int:booking_id>/messages")
def admin_booking_messages(booking_id):
    """عرض سجل رسائل الحجز (API)"""
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        with connect() as conn:
            messages = conn.execute(
                "SELECT * FROM message_log WHERE booking_id = ? ORDER BY sent_at DESC",
                (booking_id,)
            ).fetchall()
        
        messages_list = []
        for msg in messages:
            messages_list.append({
                "id": msg["id"],
                "message": msg["message"],
                "sent_at": msg["sent_at"],
                "status": msg["status"]
            })
        
        return jsonify({"messages": messages_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
                    rows = conn.execute(
                        "SELECT telegram_chat_id FROM bookings WHERE is_attending=1 AND status IN ('paid','used') AND telegram_chat_id IS NOT NULL"
                    ).fetchall()
                elif target == "contributors":
                    rows = conn.execute(
                        "SELECT telegram_chat_id FROM bookings WHERE is_attending=0 AND status='paid' AND telegram_chat_id IS NOT NULL"
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT telegram_chat_id FROM bookings WHERE status IN ('paid','used') AND telegram_chat_id IS NOT NULL"
                    ).fetchall()
                
                chat_ids = [r["telegram_chat_id"] for r in rows if r["telegram_chat_id"]]
                sent = send_broadcast(chat_ids, message)
                
                conn.execute(
                    "INSERT INTO broadcast_logs (message_title, message_body, target_group, sent_count, sent_by, sent_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                    ("broadcast", message, target, sent, "admin")
                )
            
            flash(f"📨 تم إرسال الرسالة إلى {sent} مستخدم")
        
        return redirect(url_for("admin_broadcast"))
    
    return render_template("admin/broadcast.html")

@app.route("/scan")
def scanner_page():
    return render_template("scan/scanner.html")

@app.route("/api/validate-ticket", methods=["POST"])
def api_validate_ticket():
    try:
        data = request.get_json(force=True)
        result = validate_for_checkin(data.get("qr_token", ""))
        booking = result.get("booking")
        
        return jsonify({
            "status": result["status"], 
            "message": result["message"], 
            "name": booking["name"] if booking else None, 
            "ticket_type": ticket_label(booking["ticket_type"]) if booking else None, 
            "booking_code": booking["booking_code"] if booking else None
        })
    except Exception as e:
        print(f"Error in validate_ticket: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    try:
        data = request.get_json(force=True)
        result = checkin(
            data.get("qr_token", ""), 
            data.get("gate_name", ""), 
            data.get("checked_in_by", "")
        )
        booking = result.get("booking")
        
        return jsonify({
            "status": result["status"], 
            "message": result["message"], 
            "name": booking["name"] if booking else None, 
            "ticket_type": ticket_label(booking["ticket_type"]) if booking else None, 
            "booking_code": booking["booking_code"] if booking else None,
            "has_pin_medal": booking["pin_medal"] if booking and 'pin_medal' in booking.keys() else False
        })
    except Exception as e:
        print(f"Error in checkin: {e}")
        return jsonify({"status": "error", "message": str(e)})

# =============== Scanner API Routes ===============
@app.route("/api/stats", methods=["GET"])
def api_stats():
    try:
        with connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
            ).fetchone()["c"]
            
            checked_in = conn.execute(
                "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND status='used'"
            ).fetchone()["c"]
            
        return jsonify({
            "total": total,
            "checked_in": checked_in
        })
    except Exception as e:
        print(f"Error in stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/recent-scans", methods=["GET"])
def api_recent_scans():
    try:
        with connect() as conn:
            scans = conn.execute("""
                SELECT c.checked_in_at as time, 
                       b.name,
                       b.ticket_type,
                       c.result,
                       b.pin_medal
                FROM checkins c
                JOIN bookings b ON c.booking_id = b.id
                ORDER BY c.id DESC
                LIMIT 20
            """).fetchall()
            
        scans_list = []
        for scan in scans:
            scans_list.append({
                "time": scan["time"][5:16] if scan["time"] else "",
                "name": scan["name"],
                "ticket_type": ticket_label(scan["ticket_type"]),
                "result": scan["result"],
                "has_pin_medal": scan["pin_medal"] == 1
            })
            
        return jsonify({"scans": scans_list})
    except Exception as e:
        print(f"Error in recent scans: {e}")
        return jsonify({"error": str(e)}), 500

# =============== API Routes للإحصائيات ===============
@app.route("/api/guest-stats", methods=["GET"])
def api_guest_stats():
    """إحصائيات الضيوف للسكانر"""
    try:
        with connect() as conn:
            attendees = conn.execute(
                "SELECT COUNT(*) c FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
            ).fetchone()["c"]
            
            extra_people = conn.execute(
                "SELECT COALESCE(SUM(extra_people),0) s FROM bookings WHERE is_attending=1 AND status IN ('paid','used')"
            ).fetchone()["s"]
            
            total_guests = attendees + extra_people
            
        return jsonify({
            "total_guests": total_guests
        })
    except Exception as e:
        print(f"Error in guest stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/pin-stats", methods=["GET"])
def api_pin_stats():
    """إحصائيات البروش للسكانر"""
    try:
        stats = get_pin_medal_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"Error in pin stats: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
