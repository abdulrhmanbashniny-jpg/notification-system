import os
import threading
import logging
from dotenv import load_dotenv

# تحميل المتغيرات
load_dotenv()

# إعداد Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """نقطة البداية"""
    try:
        print("🚀 Starting application...")
        
        # 1. الحصول على المتغيرات البيئية
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        DATABASE_URL = os.getenv('DATABASE_URL')
        PORT = int(os.getenv('PORT', 10000))
        
        if not BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN not found")
        if not DATABASE_URL:
            raise ValueError("❌ DATABASE_URL not found")
        
        # 2. استيراد وإنشاء Database
        from database_supabase import Database
        db = Database(DATABASE_URL)
        print("✅ Database initialized")
        
        # 3. استيراد وإنشاء Bot
        from bot import TransactionBot
        bot = TransactionBot(BOT_TOKEN, db)
        print("✅ Bot initialized")
        
        # 4. استيراد وإنشاء Notification System
        from notifications import NotificationSystem
        notifier = NotificationSystem(db, BOT_TOKEN)
        print("✅ Notifications initialized")
        
        # 5. تشغيل Notifications في Thread منفصل
        def run_notifications():
            try:
                notifier.start()
            except Exception as e:
                logging.error(f"Notification error: {e}")
        
        notif_thread = threading.Thread(target=run_notifications, daemon=True)
        notif_thread.start()
        print("✅ Notifications thread started")
        
        # 6. تشغيل Bot في Thread منفصل
        def run_bot():
            try:
                bot.run()
            except Exception as e:
                logging.error(f"Bot error: {e}")
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot thread started")
        
        # 7. تشغيل Web Server في Main Thread
        from web_app import app
        print("✅ Starting web server...")
        app.run(host='0.0.0.0', port=PORT, debug=False)
        
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
