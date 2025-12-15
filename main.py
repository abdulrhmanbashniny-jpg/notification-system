import os
import logging
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot_thread():
    try:
        from bot import run_bot
        logger.info("🤖 Starting bot...")
        run_bot()
    except Exception as e:
        logger.error(f"❌ Bot failed: {e}")

def run_notifications_thread():
    """تشغيل نظام التنبيهات"""
    try:
        from notifications import NotificationScheduler
        
        scheduler = NotificationScheduler(check_interval=3600)  # كل ساعة
        logger.info("🔔 Starting notifications...")
        scheduler.start()
        
    except Exception as e:
        logger.error(f"❌ Notifications failed: {e}")

def run_web_thread():
    try:
        from web_app import run_web
        logger.info("🌐 Starting web...")
        run_web()
    except Exception as e:
        logger.error(f"❌ Web failed: {e}")
        raise

def main():
    logger.info("="*60)
    logger.info("🚀 Transactions System - Starting")
    logger.info("="*60)
    
    required_vars = ['BOT_TOKEN', 'DATABASE_URL']
    missing = [v for v in required_vars if not os.environ.get(v)]
    
    if missing:
        logger.error(f"❌ Missing: {', '.join(missing)}")
        return
    
    logger.info("✅ All environment variables present")
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True, name="BotThread")
    bot_thread.start()
    logger.info("✅ Bot thread started")
    
    # Start notifications in separate thread
    notifications_thread = threading.Thread(target=run_notifications_thread, daemon=True, name="NotificationsThread")
    notifications_thread.start()
    logger.info("✅ Notifications thread started")
    
    # Start web in main thread
    logger.info("✅ Web starting in main thread")
    logger.info("="*60)
    logger.info("🎉 All systems operational!")
    logger.info("="*60)
    
    run_web_thread()

if __name__ == '__main__':
    main()
