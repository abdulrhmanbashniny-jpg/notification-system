import logging
import asyncio
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self, database, bot_token):
        self.db = database
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
        self.scheduler = BackgroundScheduler()
        
    def check_and_send_notifications(self):
        """التحقق من التنبيهات المعلقة وإرسالها"""
        try:
            logger.info("🔔 Checking for pending notifications...")
            
            # استخدام get_pending_notifications بدلاً من get_due_notifications
            pending_notifications = self.db.get_pending_notifications()
            
            if not pending_notifications:
                logger.info("✅ No pending notifications")
                return
            
            logger.info(f"📬 Found {len(pending_notifications)} pending notifications")
            
            # إرسال كل تنبيه
            for notification in pending_notifications:
                self.send_notification(notification)
                
        except Exception as e:
            logger.error(f"❌ Error checking notifications: {e}")
    
    def send_notification(self, notification):
        """إرسال تنبيه واحد"""
        try:
            notification_id = notification['notification_id']
            message = notification['message']
            recipients = notification['recipients']
            
            # إرسال لكل مستلم
            for user_id in recipients:
                try:
                    # استخدام asyncio لإرسال الرسالة
                    asyncio.run(self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    ))
                    logger.info(f"✅ Sent notification {notification_id} to user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to send to user {user_id}: {e}")
            
            # تحديث حالة التنبيه
            self.db.mark_notification_sent(notification_id)
            
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
    
    def start(self):
        """بدء نظام التنبيهات"""
        logger.info("🔔 Starting notification system...")
        
        # إضافة مهمة التحقق من التنبيهات كل ساعة
        self.scheduler.add_job(
            self.check_and_send_notifications,
            'interval',
            hours=1,
            id='check_notifications'
        )
        
        # بدء الـ Scheduler
        self.scheduler.start()
        logger.info("✅ Notification scheduler started")
        
        # إبقاء الـ Thread يعمل
        try:
            while True:
                asyncio.run(asyncio.sleep(60))
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            logger.info("🛑 Notification system stopped")
