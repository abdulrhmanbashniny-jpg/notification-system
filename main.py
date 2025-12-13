import threading
import time
from bot import main as run_bot
from web_app import run_web_app
from notifications import NotificationSystem

def main():
    """
    الملف الرئيسي لتشغيل جميع مكونات النظام
    """
    print("="*60)
    print("🚀 بدء تشغيل نظام إدارة المعاملات والتنبيهات")
    print("="*60)
    print()
    
    # بدء نظام التنبيهات التلقائي
    print("⏰ تشغيل نظام التنبيهات...")
    notification_system = NotificationSystem()
    notification_system.start()
    time.sleep(1)
    
    # تشغيل الموقع الإلكتروني في خيط منفصل
    print("🌐 تشغيل الموقع الإلكتروني...")
    web_thread = threading.Thread(target=run_web_app, daemon=True)
    web_thread.start()
    time.sleep(2)
    
    print()
    print("="*60)
    print("✅ جميع الأنظمة تعمل بنجاح!")
    print("="*60)
    print()
    print("📱 البوت: متصل بتليجرام")
    print("🌐 الموقع: http://localhost:5000")
    print("⏰ التنبيهات: نشطة وتفحص كل ساعة")
    print()
    print("="*60)
    print()
    
    # تشغيل البوت في الخيط الرئيسي
    print("🤖 بدء تشغيل البوت...")
    print()
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n\n⚠️ جاري إيقاف النظام...")
        notification_system.stop()
        print("✅ تم إيقاف النظام بنجاح")

if __name__ == '__main__':
    main()
