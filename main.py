import os
import asyncio
import logging
from threading import Thread
from database_supabase import Database
from bot import create_bot
from web_app import app
from notifications import NotificationScheduler

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# المتغيرات البيئية
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
PORT = int(os.getenv('PORT', 10000))

def run_web_app():
    """تشغيل تطبيق الويب"""
    logger.info(f"🌐 بدء تشغيل موقع الويب على المنفذ {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)

async def run_notification_system(bot_token, db):
    """تشغيل نظام التنبيهات"""
    scheduler = NotificationScheduler(bot_token, db)
    await scheduler.start()

def main():
    """النقطة الرئيسية لتشغيل النظام"""
    logger.info("=" * 60)
    logger.info("🚀 بدء تشغيل نظام إدارة المعاملات v1.0.0")
    logger.info("=" * 60)
    
    # التحقق من المتغيرات البيئية
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود في المتغيرات البيئية")
        return
    
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL غير موجود في المتغيرات البيئية")
        return
    
    # إنشاء اتصال قاعدة البيانات
    logger.info("📊 الاتصال بقاعدة البيانات...")
    db = Database(DATABASE_URL)
    
    # التحقق من الاتصال
    if not db.check_connection():
        logger.error("❌ فشل الاتصال بقاعدة البيانات")
        return
    
    logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح")
    
    # تشغيل موقع الويب في خيط منفصل
    logger.info("🌐 تشغيل موقع الويب...")
    web_thread = Thread(target=run_web_app, daemon=True)
    web_thread.start()
    
    # تشغيل نظام التنبيهات في خيط منفصل
    logger.info("🔔 تشغيل نظام التنبيهات...")
    async def notification_task():
        await run_notification_system(BOT_TOKEN, db)
    
    notification_thread = Thread(
        target=lambda: asyncio.run(notification_task()), 
        daemon=True
    )
    notification_thread.start()
    
    # تشغيل البوت (blocking - يعمل في الخيط الرئيسي)
    logger.info("🤖 تشغيل بوت تيليجرام...")
    bot = create_bot(BOT_TOKEN, db)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("⚠️ تم إيقاف البوت يدوياً")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
    finally:
        db.close()
        logger.info("👋 تم إيقاف النظام")

if __name__ == "__main__":
    main()
