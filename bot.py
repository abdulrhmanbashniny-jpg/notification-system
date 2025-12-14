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
            "🎯 *مرحباً بك في نظام إدارة المعاملات والتنبيهات!*\n\n"
            "📋 هذا النظام يساعدك على:\n"
            "• إدارة عقود العمل وانتهائها\n"
            "• تتبع إجازات الموظفين\n"
            "• تذكيرك بتجديد استمارات السيارات\n"
            "• متابعة التراخيص والجلسات القضائية\n"
            "• إرسال تنبيهات تلقائية قبل انتهاء المواعيد\n\n"
            "✨ للبدء، يرجى مشاركة رقم جوالك:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        user_sessions[user_id] = {'state': WAITING_FOR_PHONE}
    else:
        await show_main_menu(update, context, db_user)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استلام رقم الجوال"""
    contact = update.message.contact
    user_id = contact.user_id
    phone_number = contact.phone_number
    
    # تنسيق رقم الجوال
    if not phone_number.startswith('+'):
        if phone_number.startswith('00'):
            phone_number = '+' + phone_number[2:]
        elif phone_number.startswith('0'):
            phone_number = '+966' + phone_number[1:]
    
    # التحقق من وجود المستخدم بالرقم
    existing_user = None
    all_users = db.get_all_users()
    for u in all_users:
        if u['phone_number'] == phone_number:
            existing_user = u
            break
    
    if existing_user:
        # تحديث user_id في قاعدة البيانات
        db.cursor.execute('''
            UPDATE users SET user_id = ? WHERE phone_number = ?
        ''', (user_id, phone_number))
        db.conn.commit()
        
        await update.message.reply_text(
            f"✅ *مرحباً بعودتك {existing_user['full_name']}!*\n\n"
            f"تم تحديث حسابك بنجاح.\n"
            f"{'👑 أنت مسؤول النظام' if existing_user['is_admin'] else '👤 حسابك: مستخدم عادي'}",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        
        # تحديث existing_user بـ user_id الجديد
        existing_user['user_id'] = user_id
        await show_main_menu(update, context, existing_user)
    else:
        user_sessions[user_id] = {
            'state': WAITING_FOR_NAME,
            'phone_number': phone_number
        }
        
        await update.message.reply_text(
            "شكراً! 👍\n\nالآن أدخل اسمك الكامل:",
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
        full_name = text.strip()
        phone_number = session['phone_number']
        
        # التحقق من عدد المستخدمين
        all_users = db.get_all_users()
        is_admin = 1 if len(all_users) == 0 else 0
        
        success = db.add_user(user_id, phone_number, full_name, is_admin)
        
        if success:
            db_user = db.get_user(user_id)
            await update.message.reply_text(
                f"✅ *تم التسجيل بنجاح!*\n\n"
                f"👤 الاسم: *{full_name}*\n"
                f"📱 الجوال: `{phone_number}`\n"
                f"{'👑 أنت مسؤول النظام الأول!' if is_admin else '✨ تم تسجيلك كمستخدم'}\n\n"
                f"يمكنك الآن استخدام جميع ميزات النظام! 🎉",
                parse_mode='Markdown'
            )
            user_sessions[user_id]['state'] = None
            await show_main_menu(update, context, db_user)
        else:
            await update.message.reply_text(
                "❌ حدث خطأ في التسجيل.\n\n"
                "حاول مرة أخرى أو تواصل مع الدعم الفني."
            )
    
    elif state == AI_CHAT_MODE:
        if text.lower() in ['رجوع', 'quit', 'exit', 'خروج']:
            user_sessions[user_id]['state'] = None
            db_user = db.get_user(user_id)
            await show_main_menu(update, context, db_user)
        else:
            await update.message.reply_text("⏳ جاري البحث والتحليل...")
            response = ai.query(text, user_id)
            await update.message.reply_text(response, parse_mode='Markdown')
    
    else:
        db_user = db.get_user(user_id)
        if db_user:
            await show_main_menu(update, context, db_user)
        else:
            await start(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """عرض القائمة الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("📋 معاملاتي", callback_data="my_transactions")],
        [InlineKeyboardButton("🤖 المساعد الذكي", callback_data="ai_assistant")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="statistics")],
    ]
    
    if user['is_admin']:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"🎯 *القائمة الرئيسية*\n\n"
        f"مرحباً *{user['full_name']}*! 👋\n\n"
        f"اختر من القائمة أدناه:"
    )
    
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                message_text, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except:
            await update.callback_query.message.reply_text(
                message_text, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            message_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_user(user_id)
    
    if not db_user:
        await query.message.reply_text("⚠️ يرجى التسجيل أولاً بإرسال /start")
        return
    
    if query.data == "main_menu":
        await show_main_menu(update, context, db_user)
    
    elif query.data == "ai_assistant":
        user_sessions[user_id] = {'state': AI_CHAT_MODE}
        await query.message.edit_text(
            "🤖 *المساعد الذكي*\n\n"
            "اسألني أي سؤال عن معاملاتك!\n\n"
            "📝 *أمثلة:*\n"
            "• ما هي المعاملات التي تنتهي هذا الشهر؟\n"
            "• أعطني قائمة بالسيارات التي يجب تجديد تأمينها\n"
            "• متى موعد أقرب جلسة قضائية؟\n\n"
            "💡 اكتب 'رجوع' للعودة للقائمة الرئيسية",
            parse_mode='Markdown'
        )
    
    elif query.data == "my_transactions":
        is_admin = db_user['is_admin']
        transactions = db.get_active_transactions(user_id=None if is_admin else user_id)
        
        if transactions:
            message = "📋 *المعاملات النشطة:*\n\n"
            for i, trans in enumerate(transactions[:15], 1):
                message += f"{i}. *{trans['title']}*\n"
                message += f"   📅 ينتهي: `{trans.get('end_date', 'غير محدد')}`\n\n"
            
            if len(transactions) > 15:
                message += f"\n_... و {len(transactions) - 15} معاملة أخرى_"
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                "📭 *لا توجد معاملات نشطة حالياً*\n\n"
                "يمكنك إضافة معاملات جديدة من الموقع الإلكتروني.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    elif query.data == "statistics":
        transactions = db.get_active_transactions()
        users = db.get_all_users()
        types = db.get_transaction_types()
        
        # إحصائيات حسب النوع
        type_stats = {}
        for t in transactions:
            type_id = t['transaction_type_id']
            type_name = next((ty['name'] for ty in types if ty['id'] == type_id), 'غير معروف')
            type_stats[type_name] = type_stats.get(type_name, 0) + 1
        
        message = "📊 *إحصائيات النظام*\n\n"
        message += f"👥 عدد المستخدمين: *{len(users)}*\n"
        message += f"📋 المعاملات النشطة: *{len(transactions)}*\n"
        message += f"📑 أنواع المعاملات: *{len(types)}*\n\n"
        
        if type_stats:
            message += "📈 *التوزيع حسب النوع:*\n"
            for type_name, count in type_stats.items():
                message += f"• {type_name}: {count}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "admin_panel":
        if db_user['is_admin']:
            users = db.get_all_users()
            admins = [u for u in users if u['is_admin']]
            
            message = "⚙️ *لوحة الإدارة*\n\n"
            message += f"👥 إجمالي المستخدمين: *{len(users)}*\n"
            message += f"👑 عدد المسؤولين: *{len(admins)}*\n"
            message += f"👤 مستخدمون عاديون: *{len(users) - len(admins)}*\n\n"
            message += "🌐 للإدارة الكاملة، استخدم الموقع الإلكتروني."
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.message.edit_text(
                "⚠️ ليس لديك صلاحيات المسؤول.\n\n"
                "تواصل مع مسؤول النظام للحصول على الصلاحيات."
            )

def main():
    """تشغيل البوت"""
    try:
        print("   🔌 الاتصال بخوادم تليجرام...")
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        print("   📡 تسجيل معالجات الأوامر...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print("   ✅ البوت جاهز ويعمل الآن!")
        print()
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
    except Exception as e:
        print(f"   ❌ خطأ في تشغيل البوت: {str(e)}")
        raise

if __name__ == '__main__':
    main()
