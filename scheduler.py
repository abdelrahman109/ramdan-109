#!/usr/bin/env python3
"""
مجدول المهام - تشغيل مهام دورية
- إلغاء الحجوزات المنتهية كل دقيقة (بعد 10 دقائق من عدم رفع الصورة)
"""

import time
import schedule
import logging
from datetime import datetime, timedelta
from app.services import cancel_expired_bookings, get_expired_bookings_count
from app.db import init_db
from app.notifications import send_auto_cancel_notification

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_expired_bookings():
    """التحقق من الحجوزات المنتهية وإلغائها (بعد 10 دقائق)"""
    try:
        logger.info("🔍 Checking for expired bookings...")
        
        # الحصول على عدد الحجوزات المنتهية قبل الإلغاء
        expired_count = get_expired_bookings_count()
        
        if expired_count > 0:
            logger.info(f"📊 Found {expired_count} expired bookings")
            
            # إلغاء الحجوزات المنتهية
            cancelled = cancel_expired_bookings()
            
            if cancelled > 0:
                logger.info(f"✅ Successfully cancelled {cancelled} bookings")
                
                # إرسال إشعارات للمستخدمين (الـ notifications.py هتتعامل مع ده)
            else:
                logger.warning("⚠️ Found expired bookings but cancellation failed")
        else:
            logger.info("✅ No expired bookings found")
            
    except Exception as e:
        logger.error(f"❌ Error checking expired bookings: {e}")

def main():
    """تشغيل المجدول"""
    logger.info("🚀 Scheduler started (10 minutes timeout)")
    
    # تهيئة قاعدة البيانات
    init_db()
    
    # جدولة المهام - تشغيل كل دقيقة
    schedule.every(1).minutes.do(check_expired_bookings)
    
    # تشغيل مرة واحدة عند البدء
    check_expired_bookings()
    
    # حلقة التشغيل المستمر
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Scheduler crashed: {e}")
