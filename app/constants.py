# أنواع التذاكر
TICKET_FULL = "full_package"  # حضور
TICKET_CONTRIBUTION = "contribution"  # مساهمة

# الأسعار الجديدة
PRICE_BASE_ATTENDANCE = 150  # حضور الحفل (دخول فقط)
PRICE_EXTRA_MEAL = 265  # وجبة إضافية لكل فرد
PRICE_PIN_MEDAL = 150  # بروش + ميدالية

# طرق الدفع
PAY_INSTAPAY = "instapay"
PAY_WALLET = "wallet"

# حالات الحجز
STATUS_PENDING_PROOF = "pending_proof"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_PAID = "paid"
STATUS_REJECTED = "rejected"
STATUS_USED = "used"
STATUS_CANCELLED = "cancelled"

# التذاكر (للمساهمات)
TICKETS = {
    TICKET_FULL: {"label": "حضور الحفل", "amount": None, "attending": True},
    TICKET_CONTRIBUTION: {"label": "مساهمة بدون حضور", "amount": None, "attending": False},
}

# المساهمات (فاضية لأن المستخدم هيكتب المبلغ)
CONTRIBUTION_AMOUNTS = []

# أسماء طرق الدفع للعرض
PAYMENT_METHODS = {
    PAY_INSTAPAY: "InstaPay",
    PAY_WALLET: "محفظة إلكترونية",
}
