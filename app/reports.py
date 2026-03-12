import csv, io
from flask import Response
from app.db import connect

def bookings_csv_response():
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["الكود","الاسم","الهاتف","نوع التذكرة","القيمة","طريقة الدفع","الحالة","التاريخ"])
    with connect() as conn:
        rows = conn.execute("SELECT booking_code,name,phone,ticket_type,amount,payment_method,status,created_at FROM bookings ORDER BY id DESC").fetchall()
        for r in rows:
            writer.writerow([r["booking_code"], r["name"], r["phone"], r["ticket_type"], r["amount"], r["payment_method"], r["status"], r["created_at"]])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=bookings.csv"})

def checkins_csv_response():
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["الكود","وقت الدخول","البوابة","الموظف","النتيجة"])
    with connect() as conn:
        rows = conn.execute("SELECT booking_code,checked_in_at,gate_name,checked_in_by,result FROM checkins ORDER BY id DESC").fetchall()
        for r in rows:
            writer.writerow([r["booking_code"], r["checked_in_at"], r["gate_name"], r["checked_in_by"], r["result"]])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=checkins.csv"})
