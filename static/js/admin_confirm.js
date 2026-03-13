// تأكيد قبل الإجراءات
document.addEventListener('DOMContentLoaded', function() {
    // تأكيد للرفض
    const rejectForms = document.querySelectorAll('form[action*="reject"]');
    rejectForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('❌ هل أنت متأكد من رفض هذا الدفع؟')) {
                e.preventDefault();
            }
        });
    });
    
    // تأكيد للقبول
    const approveForms = document.querySelectorAll('form[action*="approve"]');
    approveForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('✅ هل أنت متأكد من قبول هذا الدفع؟')) {
                e.preventDefault();
            }
        });
    });
    
    // تأكيد لإعادة إرسال التذكرة
    const resendForms = document.querySelectorAll('form[action*="resend-ticket"]');
    resendForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('🔄 هل أنت متأكد من إعادة إرسال التذكرة؟')) {
                e.preventDefault();
            }
        });
    });
    
    // تأكيد للحذف
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('🚨 تحذير شديد: هل أنت متأكد من حذف هذا الحجز نهائياً؟\nهذا الإجراء لا يمكن التراجع عنه!')) {
                e.preventDefault();
            }
        });
    });
});
