TICKET_FULL = "full_package"
TICKET_BREAKFAST = "breakfast_only"
TICKET_CONTRIBUTION = "contribution"

PAY_INSTAPAY = "instapay"
PAY_WALLET = "wallet"

STATUS_PENDING_PROOF = "pending_proof"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_PAID = "paid"
STATUS_REJECTED = "rejected"
STATUS_USED = "used"

TICKETS = {
    TICKET_FULL: {"label": "حضور الحفل + الإفطار + ميدالية + بروش", "amount": 565, "attending": True},
    TICKET_BREAKFAST: {"label": "حضور الحفل + إفطار فقط", "amount": 415, "attending": True},
    TICKET_CONTRIBUTION: {"label": "مساهمة في إفطار أسر الشهداء بدون حضور", "amount": None, "attending": False},
}

CONTRIBUTION_AMOUNTS = [200, 300, 400, 500, 600, 700, 800, 900, 1000]

PAYMENT_METHODS = {
    PAY_INSTAPAY: "InstaPay",
    PAY_WALLET: "محفظة إلكترونية",
}
