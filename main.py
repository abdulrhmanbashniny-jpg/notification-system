import threading
import time
from web_app import run_web_app
from notifications import NotificationSystem

def main():
    """
    الملف الرئيسي - البوت متوقف مؤقتاً
    """
    print("="*60)
    print("🚀 بدء تشغيل نظام إدارة المعاملات")
    print("="*60)
    print()
    
    # بدء نظام التنبيهات
    print("⏰ تشغيل نظام التنبيهات...")
    notification_system = NotificationSystem()
    notification_system.start()
    time.sleep(1)
    
    print()
    print("="*60)
    print("✅ النظام يعمل الآن!")
    print("="*60)
    print()
    print("🌐 الموقع: متصل")
    print("⏰ التنبيهات: نشطة")
    print("🤖 البوت: متوقف مؤقتاً (للصيانة)")
    print()
    print("="*60)
    print()
    
    # تشغيل الموقع فقط
    print("🌐 بدء تشغيل الموقع...")
    run_web_app()

if __name__ == '__main__':
    main()
