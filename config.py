import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات البوت
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'ضع_توكن_البوت_هنا')

# إعدادات DeepSeek AI
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'ضع_مفتاح_DeepSeek_هنا')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# إعدادات قاعدة البيانات
DATABASE_PATH = 'data/notifications.db'

# إعدادات الموقع
WEB_PORT = int(os.getenv('PORT', 5000))
WEB_HOST = '0.0.0.0'

# إعدادات التنبيهات
MAX_NOTIFICATIONS_PER_ITEM = 3
NOTIFICATION_CHECK_INTERVAL_HOURS = 1

# أنواع المعاملات القابلة للتوسع
TRANSACTION_TYPES = [
    'عقد_عمل',
    'إجازة_موظف',
    'استمارة_سيارة',
    'ترخيص',
    'جلسة_قضائية',
    'أخرى'
]

# معرفات المسؤولين (أضف رقم تليجرام ID الخاص بك)
ADMIN_IDS = []  # سيتم ملؤه تلقائياً عند أول تشغيل
