"""
🔔 Notification System - نظام التنبيهات التلقائي
"""
import os
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import asyncio
import time
from database_supabase import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationScheduler:
    """جدولة وإرسال التنبيهات التلقائية"""
    
    def __init__(self, check_interval: int = 3600):
        """
        Args:
            check_interval: فترة الفحص بالثواني (افتراضي: ساعة واحدة)
        """
        self.db = Database()
        self.bot_token = os.environ.get('BOT_TOKEN')
        self.check_interval = check_interval
        self.is_running = False
        
        if not self.bot_token:
            raise Exception("❌ BOT_TOKEN غير موجود!")
        
        logger.info("✅ Notification system initialized")
    
    def start(self):
        """بدء نظام التنبيهات"""
        self.is_running = True
        logger.info("🔔 Notification system running...")
        
        # إرسال تنبيه فوري عند البداية
        asyncio.run(self.check_and_send_notifications())
        
        # حلقة التنبيهات
        while self.is_running:
            try:
                asyncio.run(self.check_and_send_notifications())
                logger.info(f"⏰ Waiting {self.check_interval} seconds for next check...")
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in notification loop: {e}")
                time.sleep(60)  # انتظار دقيقة ثم إعادة المحاولة
    
    def stop(self):
        """إيقاف نظام التنبيهات"""
        self.is_running = False
        logger.info("⏹️ Notification system stopped")
    
    async def check_and_send_notifications(self):
        """فحص وإرسال التنبيهات"""
        try:
            logger.info("🔍 Checking for pending notifications...")
            
            # جلب التنبيهات المعلقة
            pending_notifications = self.db.get_pending_notifications()
            
            if not pending_notifications:
                logger.info("✅ No pending notifications")
                return
            
            logger.info(f"📨 Found {len(pending_notifications)} pending notification(s)")
            
            # إنشاء bot instance
            bot = Bot(token=self.bot_token)
            
            sent_count = 0
            failed_count = 0
            
            # إرسال كل تنبيه
            for notification in pending_notifications:
                try:
                    success = await self.send_notification(bot, notification)
                    
                    if success:
                        # تعليم التنبيه كمُرسل
                        self.db.mark_notification_sent(notification['notification_id'])
                        sent_count += 1
                        
                        # انتظار قصير لتجنب rate limit
                        await asyncio.sleep(1)
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Failed to send notification {notification['notification_id']}: {e}")
                    failed_count += 1
            
            logger.info(f"✅ Sent {sent_count} notification(s), Failed {failed_count}")
            
        except Exception as e:
            logger.error(f"❌ Error checking notifications: {e}")
    
    async def send_notification(self, bot: Bot, notification: dict) -> bool:
        """
        إرسال تنبيه واحد
        
        Args:
            bot: Bot instance
            notification: بيانات التنبيه
            
        Returns:
            bool: نجح الإرسال أم لا
        """
        try:
            # بناء الرسالة
            message = self.build_notification_message(notification)
            
            # إرسال للمستلمين
            recipients = notification.get('recipients', [])
            
            if not recipients:
                logger.warning(f"⚠️ Notification {notification['notification_id']} has no recipients")
                return False
            
            success_count = 0
            
            for recipient_id in recipients:
                try:
                    await bot.send_message(
                        chat_id=recipient_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    success_count += 1
                    logger.info(f"✅ Notification sent to {recipient_id}")
                    
                except TelegramError as e:
                    logger.error(f"❌ Failed to send to {recipient_id}: {e}")
                
                # انتظار قصير بين كل مستلم
                await asyncio.sleep(0.5)
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
            return False
    
    def build_notification_message(self, notification: dict) -> str:
        """
        بناء رسالة التنبيه
        
        Args:
            notification: بيانات التنبيه
            
        Returns:
            str: نص الرسالة
        """
        trans = notification
        days_before = notification['days_before']
        
        # تحديد الأيقونة والنص
        if days_before == 0:
            emoji = "🔴"
            urgency = "تنتهي اليوم!"
        elif days_before <= 3:
            emoji = "🟡"
            urgency = f"تنتهي خلال {days_before} يوم"
        elif days_before <= 7:
            emoji = "🟢"
            urgency = f"تنتهي خلال {days_before} يوم"
        else:
            emoji = "📅"
            urgency = f"تنتهي خلال {days_before} يوم"
        
        # بناء الرسالة
        message = f"""
{emoji} <b>تنبيه معاملة</b>

<b>العنوان:</b> {trans['title']}
<b>النوع:</b> {trans['type_icon']} {trans['type_name']}
<b>تاريخ الانتهاء:</b> {trans['end_date']}
<b>الحالة:</b> {urgency}

<b>صاحب المعاملة:</b> {trans['user_name']}

━━━━━━━━━━━━━━━━━━━━━

💡 تأكد من متابعة هذه المعاملة
"""
        
        if trans.get('priority') == 'critical':
            message += "\n⚠️ <b>الأولوية: عاجلة جداً!</b>"
        
        return message

# ==================== Test Function ====================

def test_notifications():
    """اختبار نظام التنبيهات"""
    logger.info("🧪 Testing notification system...")
    
    try:
        scheduler = NotificationScheduler(check_interval=60)
        asyncio.run(scheduler.check_and_send_notifications())
        logger.info("✅ Test successful!")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == '__main__':
    test_notifications()
