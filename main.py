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
        
        # 1. استيراد Database
        from database_supabase import Database
        db = Database()
        print("✅ Database initialized")
        
        # 2. استيراد وإنشاء Bot
        from bot import TransactionBot
        bot = TransactionBot(db)
        print("✅ Bot initialized")
        
        # 3. تشغيل Bot في Thread منفصل
        def run_bot():
            try:
                bot.run()
            except Exception as e:
                logging.error(f"Bot error: {e}")
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot thread started")
        
        # 4. تشغيل Web Server في Main Thread
        from web_app import run_web
        print("✅ Starting web server...")
        run_web()
        
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
