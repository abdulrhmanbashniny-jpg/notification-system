import threading
import time
import sys
from bot import main as run_bot
from web_app import run_web_app
from notifications import NotificationSystem
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def keep_alive_service():
    """خدمة Keep-Alive لمنع Sleep Mode"""
    import requests
    url = "https://notification-system-cm5l.onrender.com"
    
    while True:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ Keep-Alive: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Keep-Alive error: {e}")
        time.sleep(600)  # كل 10 دقائق

def main():
    """
    🚀 نظام إدارة المعاملات والتنبيهات - الإصدار النهائي
    """
    print("="*70)
    print("🎯 نظام إدارة المعاملات والتنبيهات".center(70))
    print("="*70)
    print()
    
    try:
        # 0. بدء Keep-Alive
        print("🔄 [0/4] تفعيل خدمة Keep-Alive...")
        keep_alive_thread = threading.Thread(target=keep_alive_service, daemon=True)
        keep_alive_thread.start()
        print("   ✅ Keep-Alive نشط (Ping كل 10 دقائق)")
        time.sleep(1)
        
        # 1. بدء نظام التنبيهات التلقائي
        print("⏰ [1/4] تشغيل نظام التنبيهات التلقائية...")
        notification_system = NotificationSystem()
        notification_system.start()
        print("   ✅ نظام التنبيهات يعمل الآن (فحص كل ساعة)")
        time.sleep(1)
        
        # 2. تشغيل الموقع في خيط منفصل
        print("🌐 [2/4] تشغيل الموقع الإلكتروني...")
        web_thread = threading.Thread(target=run_web_app, daemon=True)
        web_thread.start()
        print("   ✅ الموقع يعمل الآن على المنفذ 5000")
        time.sleep(2)
        
        print()
        print("="*70)
        print("✅ جميع الأنظمة تعمل بنجاح!".center(70))
        print("="*70)
        print()
        print("📊 حالة الأنظمة:")
        print("   🌐 الموقع الإلكتروني: نشط")
        print("   ⏰ نظام التنبيهات: نشط (فحص كل ساعة)")
        print("   🔄 Keep-Alive: نشط (منع Sleep Mode)")
        print("   📱 بوت تليجرام: جاري التشغيل...")
        print()
        print("="*70)
        print()
        
        # 3. تشغيل البوت في الخيط الرئيسي
        print("🤖 [3/4] بدء تشغيل بوت تليجرام...")
        print()
        run_bot()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  جاري إيقاف النظام...")
        notification_system.stop()
        print("✅ تم إيقاف النظام بنجاح")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل النظام: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
