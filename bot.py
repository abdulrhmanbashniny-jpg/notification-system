import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

class TransactionBot:
    def __init__(self, token, database):
        self.token = token
        self.db = database
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر"""
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('help', self.help_command))
        self.app.add_handler(CommandHandler('stats', self.stats_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        user = update.effective_user
        
        # تسجيل المستخدم
        if not self.db.get_user(user.id):
            self.db.add_user(
                user_id=user.id,
                full_name=user.full_name or user.username,
                telegram_username=user.username
            )
        
        welcome_text = f"""
🎉 مرحباً {user.full_name}!

📋 **نظام إدارة المعاملات**

الأوامر المتاحة:
/start - القائمة الرئيسية
/help - المساعدة
/stats - الإحصائيات

✅ البوت يعمل بنجاح!
        """
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        help_text = """
📚 **دليل الاستخدام:**

**الأوامر:**
/start - القائمة الرئيسية
/help - المساعدة
/stats - عرض الإحصائيات

🔔 **التنبيهات التلقائية:**
سيتم إرسال تنبيهات قبل انتهاء المعاملات.
        """
        await update.message.reply_text(help_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الإحصائيات"""
        try:
            user_id = update.effective_user.id
            stats = self.db.get_user_statistics(user_id)
            
            stats_text = f"""
📈 **إحصائياتك:**

📊 إجمالي المعاملات: {stats.get('total_transactions', 0)}
✅ المعاملات النشطة: {stats.get('active_transactions', 0)}
🎉 المعاملات المكتملة: {stats.get('completed_transactions', 0)}

⚠️ تنتهي قريباً: {stats.get('due_soon', 0)}
            """
            
            await update.message.reply_text(stats_text)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ حدث خطأ في جلب الإحصائيات")
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🤖 بدء تشغيل البوت...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
