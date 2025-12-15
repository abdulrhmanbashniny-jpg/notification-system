import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database_supabase import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    db_user = db.get_user(user_id)
    if not db_user:
        db.add_user(user_id, f"+{user_id}", user.full_name or "مستخدم", telegram_username=user.username)
        db_user = db.get_user(user_id)
    
    stats = db.get_stats()
    
    message = f"""
🎯 نظام إدارة المعاملات

مرحباً {user.first_name}! 👋

📊 الإحصائيات:
📈 إجمالي: {stats['total']}
🔴 عاجلة: {stats['critical']}
🟡 تحذير: {stats['warning']}

اختر من القائمة:
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 معاملاتي", callback_data='my_transactions')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='statistics')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def my_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    transactions = db.get_transactions_by_role(user_id)
    
    if not transactions:
        await query.edit_message_text("📋 لا توجد معاملات")
        return
    
    message = f"📋 معاملاتك ({len(transactions)}):\n\n"
    
    for trans in transactions[:5]:
        days = trans.get('days_left', 0)
        emoji = "🔴" if days <= 3 else "🟡" if days <= 7 else "🟢"
        message += f"{emoji} {trans['title']}\n   📅 {trans['end_date']} • ⏰ {days} يوم\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]]
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    stats = db.get_stats()
    
    message = f"""
📊 الإحصائيات الشاملة

📈 إجمالي المعاملات: {stats['total']}
🔴 عاجلة (≤3 أيام): {stats['critical']}
🟡 تحذير (4-7 أيام): {stats['warning']}
🟢 قادمة (8-30 يوم): {stats['upcoming']}
⚪ آمنة (>30 يوم): {stats['safe']}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]]
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📋 معاملاتي", callback_data='my_transactions')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='statistics')]
    ]
    
    await query.edit_message_text("🎯 القائمة الرئيسية:", reply_markup=InlineKeyboardMarkup(keyboard))

def run_bot():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN مفقود!")
        return
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(my_transactions, pattern='^my_transactions$'))
    application.add_handler(CallbackQueryHandler(statistics, pattern='^statistics$'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    
    logger.info("✅ Bot ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    run_bot()
