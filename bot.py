from database_supabase import Database
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
from datetime import datetime, timedelta
import os

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
(MAIN_MENU, TRANSACTION_TYPE, TRANSACTION_TITLE, TRANSACTION_DATE, 
 TRANSACTION_DETAILS, NOTIFICATION_DAYS, NOTIFICATION_RECIPIENTS,
 ADMIN_MENU, ADD_USER_ID, ADD_USER_PHONE, ADD_USER_NAME) = range(11)

# قاعدة البيانات
db = Database()

# توكن البوت (ضعه في متغير بيئة أو هنا مؤقتاً)
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ==================== دوال المساعدة ====================

def is_admin(user_id):
    """التحقق من صلاحيات المسؤول"""
    user = db.get_user(user_id)
    return user and user.get('is_admin', 0) == 1

def get_main_keyboard(user_id):
    """لوحة المفاتيح الرئيسية"""
    keyboard = [
        [KeyboardButton("➕ إضافة معاملة"), KeyboardButton("📋 معاملاتي")],
        [KeyboardButton("🔍 البحث"), KeyboardButton("📊 الإحصائيات")],
    ]
    
    if is_admin(user_id):
        keyboard.append([KeyboardButton("👨‍💼 لوحة المسؤول")])
    
    keyboard.append([KeyboardButton("ℹ️ المساعدة")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    """لوحة مفاتيح المسؤول"""
    keyboard = [
        [KeyboardButton("👥 إدارة المستخدمين"), KeyboardButton("📋 جميع المعاملات")],
        [KeyboardButton("📊 إحصائيات عامة"), KeyboardButton("🔔 التنبيهات")],
        [KeyboardButton("🔙 العودة للقائمة الرئيسية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_transaction_types_keyboard():
    """لوحة اختيار نوع المعاملة"""
    keyboard = [
        [InlineKeyboardButton("📝 عقد عمل", callback_data="type_1")],
        [InlineKeyboardButton("🏖️ إجازة موظف", callback_data="type_2")],
        [InlineKeyboardButton("🚗 استمارة سيارة", callback_data="type_3")],
        [InlineKeyboardButton("📄 ترخيص", callback_data="type_4")],
        [InlineKeyboardButton("⚖️ جلسة قضائية", callback_data="type_5")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def format_transaction_message(trans):
    """تنسيق رسالة المعاملة"""
    type_icons = {
        1: "📝", 2: "🏖️", 3: "🚗", 4: "📄", 5: "⚖️"
    }
    
    type_names = {
        1: "عقد عمل", 2: "إجازة موظف", 3: "استمارة سيارة",
        4: "ترخيص", 5: "جلسة قضائية"
    }
    
    icon = type_icons.get(trans['transaction_type_id'], "📄")
    type_name = type_names.get(trans['transaction_type_id'], "معاملة")
    
    # حساب الأيام المتبقية
    try:
        end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        days_left = (end_date - today).days
        
        if days_left < 0:
            days_text = f"⚠️ منتهية منذ {abs(days_left)} يوم"
        elif days_left == 0:
            days_text = "🔥 ينتهي اليوم!"
        elif days_left == 1:
            days_text = "⚠️ ينتهي غداً"
        elif days_left <= 3:
            days_text = f"🔴 باقي {days_left} أيام"
        elif days_left <= 7:
            days_text = f"🟡 باقي {days_left} أيام"
        else:
            days_text = f"🟢 باقي {days_left} يوم"
    except:
        days_text = "غير محدد"
    
    message = f"""
{icon} *{type_name}*

📌 *العنوان:* {trans['title']}
📅 *تاريخ الانتهاء:* {trans['end_date']}
⏰ *الحالة:* {days_text}
🆔 *رقم المعاملة:* `{trans['transaction_id']}`
📆 *تاريخ الإضافة:* {trans['created_at'][:10]}
    """
    
    return message.strip()

def calculate_days_left(end_date_str):
    """حساب الأيام المتبقية"""
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        return (end_date - today).days
    except:
        return 999

# ==================== معالجات الأوامر الأساسية ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء /start"""
    user = update.effective_user
    user_id = user.id
    
    # التحقق من تسجيل المستخدم
    db_user = db.get_user(user_id)
    
    if not db_user:
        await update.message.reply_text(
            f"👋 مرحباً *{user.first_name}*!\n\n"
            "⚠️ أنت غير مسجل في النظام.\n"
            "📞 يرجى التواصل مع المسؤول لإضافتك.\n\n"
            f"🆔 معرفك: `{user_id}`\n"
            "📋 أرسل هذا المعرف للمسؤول",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    welcome_message = f"""
🎯 *مرحباً {db_user['full_name']}!*

أنا بوت إدارة المعاملات والتنبيهات 🤖

✨ *ماذا أستطيع أن أفعل؟*
━━━━━━━━━━━━━━━━━
➕ إضافة معاملات جديدة
📋 عرض معاملاتك
🔔 إرسال تنبيهات تلقائية
📊 عرض الإحصائيات
🔍 البحث عن المعاملات

━━━━━━━━━━━━━━━━━
استخدم القائمة أدناه للبدء 👇
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user_id)
    )
    
    return MAIN_MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    help_text = """
📚 *دليل الاستخدام*

*الأوامر المتاحة:*
━━━━━━━━━━━━━━━━━
/start - بدء البوت
/help - عرض المساعدة
/cancel - إلغاء العملية الحالية

*الأزرار الرئيسية:*
━━━━━━━━━━━━━━━━━
➕ *إضافة معاملة* - إضافة معاملة جديدة
📋 *معاملاتي* - عرض معاملاتك
🔍 *البحث* - البحث في المعاملات
📊 *الإحصائيات* - عرض إحصائيات مفصلة

*للمسؤولين:*
━━━━━━━━━━━━━━━━━
👨‍💼 لوحة المسؤول - إدارة كاملة للنظام
👥 إدارة المستخدمين
📋 عرض جميع المعاملات
🔔 إدارة التنبيهات

💡 *نصيحة:* استخدم الأزرار لسهولة التنقل!
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "❌ تم إلغاء العملية.\n"
        "استخدم القائمة للبدء من جديد.",
        reply_markup=get_main_keyboard(user_id)
    )
    
    context.user_data.clear()
    return ConversationHandler.END
# ==================== إضافة معاملة جديدة ====================

async def add_transaction_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة معاملة"""
    user_id = update.effective_user.id
    
    # التحقق من التسجيل
    if not db.get_user(user_id):
        await update.message.reply_text("⚠️ أنت غير مسجل في النظام!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "➕ *إضافة معاملة جديدة*\n\n"
        "الخطوة 1️⃣: اختر نوع المعاملة:",
        parse_mode='Markdown',
        reply_markup=get_transaction_types_keyboard()
    )
    
    return TRANSACTION_TYPE

async def transaction_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحديد نوع المعاملة"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ تم إلغاء العملية")
        return ConversationHandler.END
    
    type_id = int(query.data.split('_')[1])
    context.user_data['transaction_type_id'] = type_id
    
    type_names = {
        1: "عقد عمل 📝",
        2: "إجازة موظف 🏖️",
        3: "استمارة سيارة 🚗",
        4: "ترخيص 📄",
        5: "جلسة قضائية ⚖️"
    }
    
    await query.edit_message_text(
        f"✅ تم اختيار: *{type_names[type_id]}*\n\n"
        "الخطوة 2️⃣: أرسل عنوان المعاملة\n"
        "مثال: عقد عمل - أحمد محمد",
        parse_mode='Markdown'
    )
    
    return TRANSACTION_TITLE

async def transaction_title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال عنوان المعاملة"""
    title = update.message.text.strip()
    
    if len(title) < 3:
        await update.message.reply_text("⚠️ العنوان قصير جداً! أرسل عنوان أطول:")
        return TRANSACTION_TITLE
    
    context.user_data['title'] = title
    
    await update.message.reply_text(
        f"✅ العنوان: *{title}*\n\n"
        "الخطوة 3️⃣: أرسل تاريخ الانتهاء\n"
        "بالصيغة: YYYY-MM-DD\n"
        "مثال: 2025-12-31",
        parse_mode='Markdown'
    )
    
    return TRANSACTION_DATE

async def transaction_date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال تاريخ الانتهاء"""
    date_str = update.message.text.strip()
    
    # التحقق من صحة التاريخ
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # التحقق من أن التاريخ في المستقبل
        if date_obj.date() < datetime.now().date():
            await update.message.reply_text(
                "⚠️ التاريخ في الماضي!\n"
                "أرسل تاريخ في المستقبل بصيغة: YYYY-MM-DD"
            )
            return TRANSACTION_DATE
        
        context.user_data['end_date'] = date_str
        
        # طلب بيانات إضافية حسب النوع
        type_id = context.user_data['transaction_type_id']
        
        if type_id == 1:  # عقد عمل
            await update.message.reply_text(
                "✅ التاريخ: *" + date_str + "*\n\n"
                "الخطوة 4️⃣: أرسل بيانات العقد بهذا الترتيب:\n"
                "اسم الموظف | رقم العقد | المسمى الوظيفي | الراتب\n\n"
                "مثال:\n"
                "أحمد محمد | 2025/001 | محاسب | 8000",
                parse_mode='Markdown'
            )
        elif type_id == 2:  # إجازة
            await update.message.reply_text(
                "✅ التاريخ: *" + date_str + "*\n\n"
                "الخطوة 4️⃣: أرسل بيانات الإجازة:\n"
                "اسم الموظف | نوع الإجازة | الموظف البديل\n\n"
                "مثال:\n"
                "سارة أحمد | سنوية | فاطمة علي",
                parse_mode='Markdown'
            )
        elif type_id == 3:  # سيارة
            await update.message.reply_text(
                "✅ التاريخ: *" + date_str + "*\n\n"
                "الخطوة 4️⃣: أرسل بيانات السيارة:\n"
                "رقم اللوحة | نوع السيارة | VIN\n\n"
                "مثال:\n"
                "أ ب ج 1234 | كامري 2023 | ABC123XYZ",
                parse_mode='Markdown'
            )
        elif type_id == 4:  # ترخيص
            await update.message.reply_text(
                "✅ التاريخ: *" + date_str + "*\n\n"
                "الخطوة 4️⃣: أرسل بيانات الترخيص:\n"
                "نوع الترخيص | رقم الترخيص | الجهة المصدرة\n\n"
                "مثال:\n"
                "سجل تجاري | 1234567890 | وزارة التجارة",
                parse_mode='Markdown'
            )
        elif type_id == 5:  # قضية
            await update.message.reply_text(
                "✅ التاريخ: *" + date_str + "*\n\n"
                "الخطوة 4️⃣: أرسل بيانات القضية:\n"
                "رقم القضية | المحكمة | بيان القضية\n\n"
                "مثال:\n"
                "2025/001 | المحكمة التجارية | نزاع تجاري",
                parse_mode='Markdown'
            )
        
        return TRANSACTION_DETAILS
        
    except ValueError:
        await update.message.reply_text(
            "⚠️ صيغة التاريخ غير صحيحة!\n"
            "أرسل التاريخ بصيغة: YYYY-MM-DD\n"
            "مثال: 2025-12-31"
        )
        return TRANSACTION_DATE

async def transaction_details_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال البيانات التفصيلية"""
    details = update.message.text.strip()
    parts = [p.strip() for p in details.split('|')]
    
    type_id = context.user_data['transaction_type_id']
    data = {}
    
    try:
        if type_id == 1:  # عقد عمل
            if len(parts) >= 3:
                data = {
                    'employee_name': parts[0],
                    'contract_number': parts[1],
                    'job_title': parts[2],
                    'salary': parts[3] if len(parts) > 3 else ''
                }
        elif type_id == 2:  # إجازة
            if len(parts) >= 2:
                data = {
                    'employee_name': parts[0],
                    'vacation_type': parts[1],
                    'substitute': parts[2] if len(parts) > 2 else ''
                }
        elif type_id == 3:  # سيارة
            if len(parts) >= 2:
                data = {
                    'plate_number': parts[0],
                    'vehicle_type': parts[1],
                    'vin': parts[2] if len(parts) > 2 else ''
                }
        elif type_id == 4:  # ترخيص
            if len(parts) >= 2:
                data = {
                    'license_type': parts[0],
                    'license_number': parts[1],
                    'issuing_authority': parts[2] if len(parts) > 2 else ''
                }
        elif type_id == 5:  # قضية
            if len(parts) >= 2:
                data = {
                    'case_number': parts[0],
                    'court_name': parts[1],
                    'case_description': parts[2] if len(parts) > 2 else ''
                }
        
        context.user_data['data'] = data
        
        # حفظ المعاملة
        user_id = update.effective_user.id
        transaction_id = db.add_transaction(
            transaction_type_id=context.user_data['transaction_type_id'],
            user_id=user_id,
            title=context.user_data['title'],
            data=data,
            end_date=context.user_data['end_date']
        )
        
        if transaction_id:
            await update.message.reply_text(
                "✅ *تم إضافة المعاملة بنجاح!*\n\n"
                f"🆔 رقم المعاملة: `{transaction_id}`\n"
                f"📌 العنوان: {context.user_data['title']}\n"
                f"📅 تاريخ الانتهاء: {context.user_data['end_date']}\n\n"
                "🔔 هل تريد إضافة تنبيهات؟\n"
                "أرسل عدد الأيام قبل الانتهاء (مثال: 7)\n"
                "أو أرسل /skip للتخطي",
                parse_mode='Markdown'
            )
            
            context.user_data['transaction_id'] = transaction_id
            return NOTIFICATION_DAYS
        else:
            await update.message.reply_text(
                "❌ حدث خطأ في إضافة المعاملة!",
                reply_markup=get_main_keyboard(user_id)
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error in transaction_details_received: {e}")
        await update.message.reply_text(
            "⚠️ خطأ في البيانات المدخلة!\n"
            "تأكد من الصيغة الصحيحة وأعد المحاولة."
        )
        return TRANSACTION_DETAILS

async def notification_days_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال عدد أيام التنبيه"""
    user_id = update.effective_user.id
    
    if update.message.text == '/skip':
        await update.message.reply_text(
            "✅ تم حفظ المعاملة بدون تنبيهات",
            reply_markup=get_main_keyboard(user_id)
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        days = int(update.message.text.strip())
        
        if days < 1 or days > 365:
            await update.message.reply_text("⚠️ أدخل رقم بين 1 و 365")
            return NOTIFICATION_DAYS
        
        # إضافة التنبيه
        transaction_id = context.user_data['transaction_id']
        db.add_notification(
            transaction_id=transaction_id,
            days_before=days,
            recipients=[user_id]
        )
        
        await update.message.reply_text(
            f"✅ تم إضافة تنبيه قبل {days} يوم من الانتهاء!",
            reply_markup=get_main_keyboard(user_id)
        )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("⚠️ أدخل رقم صحيح!")
        return NOTIFICATION_DAYS
# ==================== عرض المعاملات ====================

async def show_my_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معاملات المستخدم"""
    user_id = update.effective_user.id
    
    transactions = db.get_active_transactions(user_id=user_id)
    
    if not transactions:
        await update.message.reply_text(
            "📭 *ليس لديك معاملات حالياً*\n\n"
            "استخدم ➕ إضافة معاملة لإضافة معاملة جديدة",
            parse_mode='Markdown'
        )
        return
    
    # ترتيب حسب الأيام المتبقية
    for trans in transactions:
        trans['days_left'] = calculate_days_left(trans['end_date'])
    
    transactions.sort(key=lambda x: x['days_left'])
    
    message = f"📋 *معاملاتك ({len(transactions)})*\n"
    message += "━━━━━━━━━━━━━━━━━\n\n"
    
    for trans in transactions[:10]:  # أول 10 معاملات
        message += format_transaction_message(trans) + "\n"
        message += "━━━━━━━━━━━━━━━━━\n"
    
    if len(transactions) > 10:
        message += f"\n📌 وهناك {len(transactions) - 10} معاملة أخرى"
    
    # إضافة أزرار للتفاعل
    keyboard = []
    for trans in transactions[:5]:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ حذف: {trans['title'][:30]}",
                callback_data=f"delete_{trans['transaction_id']}"
            )
        ])
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

async def delete_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف معاملة"""
    query = update.callback_query
    await query.answer()
    
    transaction_id = int(query.data.split('_')[1])
    
    if db.delete_transaction(transaction_id):
        await query.edit_message_text(
            "✅ تم حذف المعاملة بنجاح!"
        )
    else:
        await query.edit_message_text(
            "❌ حدث خطأ في حذف المعاملة!"
        )

# ==================== البحث والإحصائيات ====================

async def search_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث في المعاملات"""
    await update.message.reply_text(
        "🔍 *البحث في المعاملات*\n\n"
        "أرسل كلمة للبحث عنها في العناوين:",
        parse_mode='Markdown'
    )

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الإحصائيات"""
    user_id = update.effective_user.id
    
    transactions = db.get_active_transactions(user_id=user_id)
    
    total = len(transactions)
    critical = 0
    warning = 0
    safe = 0
    
    for trans in transactions:
        days_left = calculate_days_left(trans['end_date'])
        if days_left <= 3:
            critical += 1
        elif days_left <= 7:
            warning += 1
        else:
            safe += 1
    
    stats_message = f"""
📊 *إحصائيات معاملاتك*
━━━━━━━━━━━━━━━━━

📈 *الإجمالي:* {total} معاملة

🔴 *عاجل (3 أيام):* {critical}
🟡 *قريب (7 أيام):* {warning}
🟢 *آمن:* {safe}

━━━━━━━━━━━━━━━━━
📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')

# ==================== لوحة المسؤول ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المسؤول"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⚠️ هذا الأمر للمسؤولين فقط!")
        return MAIN_MENU
    
    await update.message.reply_text(
        "👨‍💼 *لوحة المسؤول*\n\n"
        "اختر أحد الخيارات من القائمة:",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )
    
    return ADMIN_MENU

async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة المستخدمين"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⚠️ هذا الأمر للمسؤولين فقط!")
        return
    
    users = db.get_all_users()
    
    message = f"👥 *قائمة المستخدمين ({len(users)})*\n"
    message += "━━━━━━━━━━━━━━━━━\n\n"
    
    for user in users:
        admin_badge = "👑" if user['is_admin'] else "👤"
        message += f"{admin_badge} *{user['full_name']}*\n"
        message += f"   📞 {user['phone_number']}\n"
        message += f"   🆔 `{user['user_id']}`\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مستخدم", callback_data="add_user")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_admin")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة مستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("⚠️ هذا الأمر للمسؤولين فقط!")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "➕ *إضافة مستخدم جديد*\n\n"
        "الخطوة 1️⃣: أرسل معرف تليجرام (User ID)\n\n"
        "💡 للحصول على المعرف:\n"
        "1. اطلب من المستخدم فتح @userinfobot\n"
        "2. أرسل أي رسالة للبوت\n"
        "3. انسخ الرقم الذي يظهر",
        parse_mode='Markdown'
    )
    
    return ADD_USER_ID

async def add_user_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال معرف المستخدم"""
    try:
        user_id = int(update.message.text.strip())
        context.user_data['new_user_id'] = user_id
        
        await update.message.reply_text(
            f"✅ المعرف: `{user_id}`\n\n"
            "الخطوة 2️⃣: أرسل رقم الجوال\n"
            "مثال: +966512345678",
            parse_mode='Markdown'
        )
        
        return ADD_USER_PHONE
        
    except ValueError:
        await update.message.reply_text("⚠️ أدخل رقم صحيح!")
        return ADD_USER_ID

async def add_user_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال رقم الجوال"""
    phone = update.message.text.strip()
    context.user_data['new_user_phone'] = phone
    
    await update.message.reply_text(
        f"✅ الجوال: {phone}\n\n"
        "الخطوة 3️⃣: أرسل الاسم الكامل"
    )
    
    return ADD_USER_NAME

async def add_user_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال اسم المستخدم وإضافته"""
    name = update.message.text.strip()
    user_id = update.effective_user.id
    
    # إضافة المستخدم
    success = db.add_user(
        user_id=context.user_data['new_user_id'],
        phone_number=context.user_data['new_user_phone'],
        full_name=name,
        is_admin=0
    )
    
    if success:
        await update.message.reply_text(
            "✅ *تم إضافة المستخدم بنجاح!*\n\n"
            f"👤 الاسم: {name}\n"
            f"📞 الجوال: {context.user_data['new_user_phone']}\n"
            f"🆔 المعرف: `{context.user_data['new_user_id']}`",
            parse_mode='Markdown',
            reply_markup=get_admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ حدث خطأ في إضافة المستخدم!",
            reply_markup=get_admin_keyboard()
        )
    
    context.user_data.clear()
    return ConversationHandler.END

async def show_all_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع المعاملات (للمسؤول)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⚠️ هذا الأمر للمسؤولين فقط!")
        return
    
    transactions = db.get_active_transactions()
    
    if not transactions:
        await update.message.reply_text("📭 لا توجد معاملات في النظام")
        return
    
    # ترتيب حسب الأيام المتبقية
    for trans in transactions:
        trans['days_left'] = calculate_days_left(trans['end_date'])
    
    transactions.sort(key=lambda x: x['days_left'])
    
    message = f"📋 *جميع المعاملات ({len(transactions)})*\n"
    message += "━━━━━━━━━━━━━━━━━\n\n"
    
    # المعاملات العاجلة فقط
    urgent = [t for t in transactions if t['days_left'] <= 7]
    
    if urgent:
        message += "🔥 *المعاملات العاجلة:*\n\n"
        for trans in urgent[:10]:
            message += format_transaction_message(trans) + "\n"
            message += "━━━━━━━━━━━━━━━━━\n"
    else:
        message += "✅ لا توجد معاملات عاجلة\n"
        message += "جميع المعاملات تحت السيطرة!"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def show_general_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات عامة (للمسؤول)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⚠️ هذا الأمر للمسؤولين فقط!")
        return
    
    transactions = db.get_active_transactions()
    users = db.get_all_users()
    
    total = len(transactions)
    critical = sum(1 for t in transactions if calculate_days_left(t['end_date']) <= 3)
    warning = sum(1 for t in transactions if 3 < calculate_days_left(t['end_date']) <= 7)
    
    stats_message = f"""
📊 *إحصائيات النظام*
━━━━━━━━━━━━━━━━━

👥 *المستخدمين:* {len(users)}
📋 *المعاملات:* {total}

🔴 *عاجل:* {critical}
🟡 *قريب:* {warning}
🟢 *آمن:* {total - critical - warning}

━━━━━━━━━━━━━━━━━
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')
# ==================== معالجات الرسائل النصية ====================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية من الأزرار"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "➕ إضافة معاملة":
        return await add_transaction_start(update, context)
    
    elif text == "📋 معاملاتي":
        await show_my_transactions(update, context)
    
    elif text == "🔍 البحث":
        await search_transactions(update, context)
    
    elif text == "📊 الإحصائيات":
        await show_statistics(update, context)
    
    elif text == "ℹ️ المساعدة":
        await help_command(update, context)
    
    elif text == "👨‍💼 لوحة المسؤول":
        return await admin_panel(update, context)
    
    elif text == "👥 إدارة المستخدمين":
        await manage_users(update, context)
    
    elif text == "📋 جميع المعاملات":
        await show_all_transactions(update, context)
    
    elif text == "📊 إحصائيات عامة":
        await show_general_statistics(update, context)
    
    elif text == "🔔 التنبيهات":
        await update.message.reply_text(
            "🔔 *نظام التنبيهات*\n\n"
            "✅ التنبيهات التلقائية مفعلة\n"
            "📬 سيتم إرسال تنبيهات قبل انتهاء المعاملات",
            parse_mode='Markdown'
        )
    
    elif text == "🔙 العودة للقائمة الرئيسية":
        await update.message.reply_text(
            "🏠 القائمة الرئيسية",
            reply_markup=get_main_keyboard(user_id)
        )
        return MAIN_MENU
    
    else:
        await update.message.reply_text(
            "🤔 لم أفهم طلبك.\n"
            "استخدم الأزرار أو /help للمساعدة"
        )
    
    return MAIN_MENU

# ==================== معالج الأخطاء ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع!\n"
                "حاول مرة أخرى أو تواصل مع المسؤول."
            )
    except:
        pass

# ==================== الوظيفة الرئيسية ====================

def main():
    """تشغيل البوت"""
    
    if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ خطأ: BOT_TOKEN غير محدد!")
        print("ضع التوكن في متغير البيئة أو في الكود مباشرة")
        return
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # معالج المحادثة لإضافة معاملة
    add_transaction_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^➕ إضافة معاملة$'), add_transaction_start)
        ],
        states={
            TRANSACTION_TYPE: [CallbackQueryHandler(transaction_type_selected)],
            TRANSACTION_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_title_received)],
            TRANSACTION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_date_received)],
            TRANSACTION_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_details_received)],
            NOTIFICATION_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, notification_days_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # معالج المحادثة لإضافة مستخدم
    add_user_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_user_start, pattern='^add_user$')
        ],
        states={
            ADD_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user_id_received)],
            ADD_USER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user_phone_received)],
            ADD_USER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user_name_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # إضافة المعالجات
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_handler(add_transaction_conv)
    application.add_handler(add_user_conv)
    application.add_handler(CallbackQueryHandler(delete_transaction, pattern='^delete_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("🤖 بوت تليجرام يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
