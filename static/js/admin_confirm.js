// تأكيد قبل الإجراءات
function confirmAction(message, form) {
    if (confirm(message)) {
        form.submit();
    }
    return false;
}

// إضافة تأكيد لكل الأزرار المهمة
document.addEventListener('DOMContentLoaded', function() {
    // تأكيد للرفض
    const rejectForms = document.querySelectorAll('form[action*="reject"]');
    rejectForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('❓ هل أنت متأكد من رفض هذا الدفع؟')) {
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
    
    // رسالة نجاح/فشل للمسح
    console.log('Admin confirm script loaded');
});

// دالة لنسخ النص
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('تم النسخ!');
    }, function() {
        alert('فشل النسخ');
    });
}
