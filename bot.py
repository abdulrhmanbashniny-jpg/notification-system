import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database
from ai_assistant import AIAssistant
from config import TELEGRAM_BOT_TOKEN, MAX_NOTIFICATIONS_PER_ITEM

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()
ai = AIAssistant()

user_sessions = {}

WAITING_FOR_PHONE = 1
WAITING_FOR_NAME = 2
AI_CHAT_MODE = 3

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    user_id = user.id
    
    db_user = db.get_user(user_id)
    
    if not db_user:
        keyboard = [[KeyboardButton("مشاركة رقم الجوال 📱", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "مرحباً بك في نظام إدارة المعاملات والتنبيهات! 🎉\n\n"
            "للبدء، يرجى مشاركة رقم جوالك:",
            reply_markup=reply_markup
        )
        user_sessions[user_id] = {'state': WAITING_FOR_PHONE}
    else:
        await show_main_menu(update, context, db_user)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استلام رقم الجوال"""
    contact = update.message.contact
    user_id = contact.user_id
    phone_number = contact.phone_number
    
    user_sessions[user_id] = {
        'state': WAITING_FOR_NAME,
        'phone_number': phone_number
    }
    
    await update.message.reply_text(
        "شكراً! الآن أدخل اسمك الكامل:",
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {'state': None}
    
    session = user_sessions[user_id]
    state = session.get('state')
    
    if state == WAITING_FOR_NAME:
        full_name = text
        phone_number = session['phone_number']
        
        is_admin = 1 if len(db.get_all_users()) == 0 else 0
        
        success = db.add_user(user_id, phone_number, full_name, is_admin)
        
        if success:
            db_user = db.get_user(user_id)
            await update.message.reply_text(
                f"تم التسجيل بنجاح! ✅\n\n"
                f"الاسم: {full_name}\n"
                f"{'أنت مسؤول النظام 👑' if is_admin else 'تم تسجيلك كمستخدم عادي'}"
            )
            user_sessions[user_id]['state'] = None
            await show_main_menu(update, context, db_user)
        else:
            await update.message.reply_text("حدث خطأ في التسجيل. حاول مرة أخرى.")
    
    elif state == AI_CHAT_MODE:
        if text.lower() in ['رجوع', 'quit', 'exit']:
            user_sessions[user_id]['state'] = None
            db_user = db.get_user(user_id)
            await show_main_menu(update, context, db_user)
        else:
            await update.message.reply_text("⏳ جاري البحث...")
            response = ai.query(text, user_id)
            await update.message.reply_text(response)
    
    else:
        db_user = db.get_user(user_id)
        if db_user:
            await show_main_menu(update, context, db_user)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """عرض القائمة الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة معاملة", callback_data="add_transaction")],
        [InlineKeyboardButton("📋 معاملاتي", callback_data="my_transactions")],
        [InlineKeyboardButton("🤖 المساعد الذكي", callback_data="ai_assistant")],
    ]
    
    if user['is_admin']:
        keyboard.append([InlineKeyboardButton("⚙️ الإدارة", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = f"مرحباً {user['full_name']}! 👋\n\nاختر من القائمة:"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_user(user_id)
    
    if query.data == "main_menu":
        await show_main_menu(update, context, db_user)
    
    elif query.data == "ai_assistant":
        user_sessions[user_id] = {'state': AI_CHAT_MODE}
        await query.message.edit_text(
            "🤖 *المساعد الذكي*\n\n"
            "اسألني أي سؤال عن معاملاتك!\n\n"
            "مثال: ما هي المعاملات التي تنتهي هذا الشهر؟\n\n"
            "اكتب 'رجوع' للعودة للقائمة.",
            parse_mode='Markdown'
        )
    
    elif query.data == "my_transactions":
        transactions = db.get_active_transactions(user_id=user_id if not db_user['is_admin'] else None)
        
        if transactions:
            message = "📋 *المعاملات النشطة:*\n\n"
            for trans in transactions[:10]:
                message += f"• {trans['title']} - ينتهي في {trans.get('end_date', 'غير محدد')}\n"
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("لا توجد معاملات نشطة.", reply_markup=reply_markup)
    
    elif query.data == "add_transaction":
        await query.message.edit_text(
            "ميزة إضافة المعاملات ستكون متاحة قريباً.\n"
            "يمكنك الآن استخدام المساعد الذكي أو الموقع الإلكتروني.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]])
        )
    
    elif query.data == "admin_panel":
        if db_user['is_admin']:
            users = db.get_all_users()
            types = db.get_transaction_types()
            
            message = "⚙️ *لوحة الإدارة*\n\n"
            message += f"👥 عدد المستخدمين: {len(users)}\n"
            message += f"📊 أنواع المعاملات: {len(types)}\n\n"
            message += "استخدم الموقع الإلكتروني للإدارة الكاملة."
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.message.edit_text("ليس لديك صلاحيات المسؤول.")

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
