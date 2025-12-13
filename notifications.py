from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import Database
import telegram
from config import TELEGRAM_BOT_TOKEN, NOTIFICATION_CHECK_INTERVAL_HOURS

class NotificationSystem:
    def __init__(self):
        self.db = Database()
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """بدء نظام التنبيهات"""
        # جدولة فحص التنبيهات كل ساعة
        self.scheduler.add_job(
            self.check_and_send_notifications,
            'interval',
            hours=NOTIFICATION_CHECK_INTERVAL_HOURS,
            id='notification_checker'
        )
        self.scheduler.start()
        print("✅ نظام التنبيهات يعمل الآن")
    
    def check_and_send_notifications(self):
        """فحص وإرسال التنبيهات المستحقة"""
        print(f"🔍 فحص التنبيهات في {datetime.now()}")
        
        due_notifications = self.db.get_due_notifications()
        
        for notification in due_notifications:
            self.send_notification(notification)
    
    def send_notification(self, notification):
        """إرسال تنبيه واحد"""
        try:
            # الحصول على المستلمين
            recipients = self.db.get_notification_recipients(notification['notification_id'])
            
            # بناء رسالة التنبيه
            message = self._build_notification_message(notification)
            
            # إرسال للمستلمين
            for recipient in recipients:
                try:
                    self.bot.send_message(
                        chat_id=recipient['user_id'],
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"خطأ في إرسال تنبيه للمستخدم {recipient['user_id']}: {e}")
            
            # تسجيل الإرسال
            self.db.mark_notification_sent(notification['notification_id'])
            print(f"✅ تم إرسال تنبيه: {notification['title']}")
        
        except Exception as e:
            print(f"❌ خطأ في إرسال التنبيه: {e}")
    
    def _build_notification_message(self, notification):
        """بناء نص التنبيه"""
        days_before = notification['days_before']
        title = notification['title']
        type_name = notification['type_name']
        end_date = notification['end_date']
        
        message = f"🔔 *تنبيه - {type_name}*\n\n"
        message += f"📋 *العنوان:* {title}\n"
        message += f"📅 *تاريخ الانتهاء:* {end_date}\n"
        message += f"⏰ *متبقي:* {days_before} يوم\n\n"
        
        # إضافة تفاصيل حسب النوع
        data = notification.get('data', {})
        if data:
            message += "*تفاصيل إضافية:*\n"
            for key, value in data.items():
                message += f"• {key}: {value}\n"
        
        message += "\n⚠️ يرجى اتخاذ الإجراء اللازم."
        
        return message
    
    def send_vacation_return_reminder(self, transaction_id):
        """إرسال تنبيه رجوع الموظف من الإجازة"""
        transaction = self.db.get_transaction(transaction_id)
        
        if transaction and transaction['type_name'] == 'إجازة_موظف':
            data = transaction['data']
            
            message = f"🏖️ *تنبيه رجوع من إجازة*\n\n"
            message += f"👤 *الموظف:* {data.get('اسم_الموظف', 'غير محدد')}\n"
            message += f"💼 *الوظيفة:* {data.get('الوظيفة', 'غير محدد')}\n"
            message += f"🔄 *الموظف البديل:* {data.get('الموظف_البديل', 'غير محدد')}\n"
            message += f"📅 *تاريخ الرجوع:* {transaction['end_date']}\n\n"
            message += "يرجى التحضير لعودة الموظف."
            
            # إرسال للمسؤولين
            notifications = self.db.get_notifications_for_transaction(transaction_id)
            for notif in notifications:
                recipients = self.db.get_notification_recipients(notif['notification_id'])
                for recipient in recipients:
                    try:
                        self.bot.send_message(
                            chat_id=recipient['user_id'],
                            text=message,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"خطأ: {e}")
    
    def stop(self):
        """إيقاف نظام التنبيهات"""
        self.scheduler.shutdown()
        print("❌ تم إيقاف نظام التنبيهات")
