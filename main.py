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

def main():
    """
    🚀 نظام إدارة المعاملات والتنبيهات - الإصدار النهائي
    """
    print("="*70)
    print("🎯 نظام إدارة المعاملات والتنبيهات".center(70))
    print("="*70)
    print()
    
    try:
        # 1. بدء نظام التنبيهات التلقائي
        print("⏰ [1/3] تشغيل نظام التنبيهات التلقائية...")
        notification_system = NotificationSystem()
        notification_system.start()
        print("   ✅ نظام التنبيهات يعمل الآن (فحص كل ساعة)")
        time.sleep(1)
        
        # 2. تشغيل الموقع في خيط منفصل
        print("🌐 [2/3] تشغيل الموقع الإلكتروني...")
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
        print("   📱 بوت تليجرام: جاري التشغيل...")
        print()
        print("="*70)
        print()
        
        # 3. تشغيل البوت في الخيط الرئيسي
        print("🤖 [3/3] بدء تشغيل بوت تليجرام...")
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
