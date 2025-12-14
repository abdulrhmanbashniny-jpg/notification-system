"""
🎯 Main Entry Point - نقطة التشغيل الرئيسية
تشغيل البوت + الموقع + Keep-Alive في نفس الوقت
"""
import os
import threading
import time
import logging
from datetime import datetime
import requests

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== Keep-Alive ====================

class KeepAlive:
    """نظام Keep-Alive لمنع النوم على Render"""
    
    def __init__(self, url: str, interval: int = 300):
        """
        Args:
            url: رابط الموقع
            interval: الفترة بالثواني (افتراضي 5 دقائق)
        """
        self.url = url
        self.interval = interval
        self.is_running = False
        self.thread = None
        
    def start(self):
        """بدء Keep-Alive"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()
        logger.info(f"✅ Keep-Alive بدأ: {self.url} كل {self.interval} ثانية")
    
    def stop(self):
        """إيقاف Keep-Alive"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️ Keep-Alive توقف")
    
    def _keep_alive_loop(self):
        """حلقة Keep-Alive"""
        # انتظار 30 ثانية قبل البدء
        time.sleep(30)
        
        while self.is_running:
            try:
                response = requests.get(f"{self.url}/health", timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"💓 Keep-Alive نجح: {response.json()}")
                else:
                    logger.warning(f"⚠️ Keep-Alive غير طبيعي: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Keep-Alive فشل: {e}")
            
            # الانتظار للفترة التالية
            time.sleep(self.interval)

# ==================== تشغيل البوت ====================

def run_bot_thread():
    """تشغيل البوت في Thread منفصل"""
    try:
        from bot import run_bot
        logger.info("🤖 بدء تشغيل البوت...")
        run_bot()
    except Exception as e:
        logger.error(f"❌ فشل تشغيل البوت: {e}")
        raise

# ==================== تشغيل الموقع ====================

def run_web_thread():
    """تشغيل الموقع في Thread منفصل"""
    try:
        from web_app import run_web
        logger.info("🌐 بدء تشغيل الموقع...")
        run_web()
    except Exception as e:
        logger.error(f"❌ فشل تشغيل الموقع: {e}")
        raise

# ==================== تشغيل التنبيهات ====================

def run_notifications_thread():
    """تشغيل نظام التنبيهات في Thread منفصل"""
    try:
        from notifications import NotificationScheduler
        
        scheduler = NotificationScheduler()
        logger.info("🔔 بدء تشغيل نظام التنبيهات...")
        scheduler.start()
        
        # إبقاء الـ thread حي
        while True:
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"❌ فشل تشغيل التنبيهات: {e}")
        raise

# ==================== التشغيل الرئيسي ====================

def main():
    """التشغيل الرئيسي للنظام"""
    
    logger.info("="*60)
    logger.info("🚀 نظام إدارة المعاملات - بدء التشغيل")
    logger.info("="*60)
    
    # التحقق من المتغيرات
    required_vars = ['BOT_TOKEN', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ متغيرات مفقودة: {', '.join(missing_vars)}")
        return
    
    logger.info("✅ جميع المتغيرات موجودة")
    
    # تحديد رابط الموقع
    app_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not app_url:
        # محاولة بناء الرابط من APP_NAME
        app_name = os.environ.get('APP_NAME', 'transactions-system')
        app_url = f"https://{app_name}.onrender.com"
    
    logger.info(f"🌐 رابط الموقع: {app_url}")
    
    # بدء Keep-Alive
    keep_alive = KeepAlive(app_url, interval=300)  # كل 5 دقائق
    keep_alive.start()
    
    # إنشاء Threads
    threads = []
    
    # 1. البوت
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True, name="BotThread")
    bot_thread.start()
    threads.append(bot_thread)
    logger.info("✅ البوت يعمل في thread منفصل")
    
    # 2. التنبيهات
    notifications_thread = threading.Thread(target=run_notifications_thread, daemon=True, name="NotificationsThread")
    notifications_thread.start()
    threads.append(notifications_thread)
    logger.info("✅ التنبيهات تعمل في thread منفصل")
    
    # 3. الموقع (في الـ main thread)
    logger.info("✅ الموقع سيعمل في main thread")
    
    logger.info("="*60)
    logger.info("🎉 جميع الأنظمة تعمل بنجاح!")
    logger.info("="*60)
    
    # تشغيل الموقع (هذا يحافظ على البرنامج مستيقظاً)
    try:
        run_web_thread()
    except KeyboardInterrupt:
        logger.info("\n⏹️ إيقاف النظام...")
        keep_alive.stop()
        logger.info("👋 تم إيقاف النظام بنجاح")

# ==================== نقطة الدخول ====================

if __name__ == '__main__':
    main()
