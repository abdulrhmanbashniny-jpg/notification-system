import os
import threading
import logging
from dotenv import load_dotenv
from database_supabase import Database
from bot import TransactionBot
from notifications import NotificationSystem
from web_app import run_web

# تحميل المتغيرات من .env
load_dotenv()

# إعداد Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    نقطة البداية الرئيسية للتطبيق
    يشغل 3 مكونات بالتوازي:
    1. Telegram Bot (في Thread منفصل)
    2. Notification System (في Thread منفصل)
    3. Web Server (في Main Thread)
    """
    try:
        print("🚀 Starting application...")
        
        # 1. إنشاء قاعدة البيانات
        db = Database()
        print("✅ Database initialized")
        
        # 2. إنشاء البوت
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables")
        
        bot = TransactionBot(db)
        print("✅ Bot initialized")
        
        # 3. إنشاء نظام الإشعارات
        notifier = NotificationSystem(db, bot_token)
        print("✅ Notification system initialized")
        
        # 4. تشغيل البوت في Thread منفصل
        bot_thread = threading.Thread(
            target=bot.run,
            daemon=True,
            name="BotThread"
        )
        bot_thread.start()
        print("✅ Bot thread started")
        
        # 5. تشغيل نظام الإشعارات في Thread منفصل
        notif_thread = threading.Thread(
            target=notifier.start,
            daemon=True,
            name="NotificationThread"
        )
        notif_thread.start()
        print("✅ Notifications thread started")
        
        # 6. تشغيل Web Server في Main Thread
        # هذا يبقي البرنامج يعمل ويسمح لـ Render بمراقبة الـ Port
        print("✅ Web starting in main thread")
        run_web()
        
    except Exception as e:
        logging.error(f"❌ Error in main: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
