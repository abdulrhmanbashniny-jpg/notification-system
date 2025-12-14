import threading
import time
from datetime import datetime, timedelta
from database import Database
import os
import requests
import logging

logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self):
        self.db = Database()
        self.bot_token = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
        self.running = False
        self.thread = None
    
    def send_telegram_message(self, chat_id, message):
        """إرسال رسالة عبر تليجرام"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة تليجرام: {e}")
            return False
    
    def check_notifications(self):
        """فحص وإرسال التنبيهات"""
        logger.info("🔍 فحص التنبيهات...")
        
        transactions = self.db.get_active_transactions()
        today = datetime.now().date()
        sent_count = 0
        
        for trans in transactions:
            try:
                end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
                days_left = (end_date - today).days
                
                # إرسال تنبيه إذا كانت المعاملة ستنتهي قريباً
                if days_left <= 7 and days_left >= 0:
                    user_id = trans['user_id']
                    
                    if days_left == 0:
                        message = f"🔥 *تنبيه عاجل!*\n\n"
                        message += f"المعاملة تنتهي *اليوم*:\n"
                    elif days_left == 1:
                        message = f"⚠️ *تنبيه مهم!*\n\n"
                        message += f"المعاملة تنتهي *غداً*:\n"
                    else:
                        message = f"📢 *تذكير:*\n\n"
                        message += f"المعاملة تنتهي بعد *{days_left} أيام*:\n"
                    
                    message += f"\n📌 {trans['title']}\n"
                    message += f"📅 تاريخ الانتهاء: {trans['end_date']}\n"
                    message += f"🆔 رقم المعاملة: `{trans['transaction_id']}`"
                    
                    if self.send_telegram_message(user_id, message):
                        sent_count += 1
                        logger.info(f"✅ تم إرسال تنبيه للمعاملة {trans['transaction_id']}")
                
            except Exception as e:
                logger.error(f"خطأ في معالجة المعاملة {trans.get('transaction_id')}: {e}")
                continue
        
        logger.info(f"📬 تم إرسال {sent_count} تنبيه")
    
    def notification_loop(self):
        """حلقة فحص التنبيهات"""
        logger.info("⏰ نظام التنبيهات بدأ العمل")
        
        while self.running:
            try:
                self.check_notifications()
            except Exception as e:
                logger.error(f"خطأ في نظام التنبيهات: {e}")
            
            # الانتظار ساعة واحدة
            for _ in range(3600):
                if not self.running:
                    break
                time.sleep(1)
    
    def start(self):
        """بدء نظام التنبيهات"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.notification_loop, daemon=True)
            self.thread.start()
            logger.info("✅ نظام التنبيهات يعمل")
    
    def stop(self):
        """إيقاف نظام التنبيهات"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️ تم إيقاف نظام التنبيهات")
