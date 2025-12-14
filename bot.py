"""
🤖 Telegram Bot - النسخة الاحترافية التفاعلية
نظام إضافة متدرج مع قاعدة بيانات مؤقتة وملخص قبل الحفظ
"""
import os
import logging
from datetime import datetime, timedelta
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from database_supabase import Database
from ai_agent import AIAgent
import json

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== الحالات (States) ====================
(SELECT_MAIN_TYPE, SELECT_SUBTYPE, ENTER_TITLE, ENTER_END_DATE,
 SELECT_RESPONSIBLE, SELECT_RECIPIENTS, ENTER_DESCRIPTION, 
 CONFIRM_TRANSACTION) = range(8)

# ==================== قاعدة البيانات المؤقتة ====================
user_temp_data = {}

# ==================== Helper Functions ====================

def get_user_temp_data(user_id: int) -> dict:
    """الحصول على البيانات المؤقتة للمستخدم"""
    if user_id not in user_temp_data:
        user_temp_data[user_id] = {
            'stage': None,
            'data': {},
            'selected_recipients': []
        }
    return user_temp_data[user_id]

def clear_user_temp_data(user_id: int):
    """حذف البيانات المؤقتة"""
    if user_id in user_temp_data:
        del user_temp_data[user_id]

def format_date(date_str: str) -> str:
    """تنسيق التاريخ"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_str

def calculate_days_left(end_date: str) -> int:
    """حساب الأيام المتبقية"""
    try:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        return (end - today).days
    except:
        return 0

def get_priority_emoji(days_left: int) -> str:
    """الحصول على رمز الأولوية"""
    if days_left <= 0:
        return '⚫'
    elif days_left <= 3:
        return '🔴'
    elif days_left <= 7:
        return '🟡'
    else:
        return '🟢'

# ==================== Database Instance ====================
db = Database()
ai_agent = AIAgent(db)

# ==================== أوامر رئيسية ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    user = update.effective_user
    user_id = user.id
    
    # التحقق من المستخدم في قاعدة البيانات
    db_user = db.get_user(user_id)
    
    if not db_user:
        # تسجيل مستخدم جديد
        db.add_user(
            user_id=user_id,
            phone_number=f"+{user_id}",  # مؤقت
            full_name=user.full_name or user.username or "مستخدم",
            telegram_username=user.username
        )
        db_user = db.get_user(user_id)
    
    role_emoji = {
        'admin': '👑',
        'manager': '👔',
        'user': '👤'
    }
    
    role_name = {
        'admin': 'مدير النظام',
        'manager': 'مدير',
        'user': 'مستخدم'
    }
    
    welcome_message = f"""
╔════════════════════════╗
  🎯 نظام إدارة المعاملات
╚════════════════════════╝

مرحباً {user.first_name}! 👋

{role_emoji.get(db_user['role'], '👤')} الصلاحية: {role_name.get(db_user['role'], 'مستخدم')}
📊 معاملاتك: {db_user.get('total_transactions', 0)}
🔴 عاجلة: {db_user.get('critical_count', 0)}

اختر من القائمة:
"""
    
    keyboard = [
        [
            InlineKeyboardButton("➕ إضافة معاملة", callback_data='add_transaction'),
            InlineKeyboardButton("📋 معاملاتي", callback_data='my_transactions')
        ],
        [
            InlineKeyboardButton("🔍 بحث", callback_data='search'),
            InlineKeyboardButton("📊 الإحصائيات", callback_data='statistics')
        ],
        [
            InlineKeyboardButton("🤖 المساعد الذكي", callback_data='ai_assistant'),
            InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings')
        ]
    ]
    
    # إضافة زر لوحة التحكم للمدراء
    if db_user['role'] in ['admin', 'manager']:
        keyboard.append([
            InlineKeyboardButton("🎛️ لوحة التحكم", callback_data='admin_panel')
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# ==================== إضافة معاملة - النظام التفاعلي ====================

async def add_transaction_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية عملية إضافة معاملة"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # مسح البيانات المؤقتة القديمة
    clear_user_temp_data(user_id)
    temp_data = get_user_temp_data(user_id)
    temp_data['stage'] = 'select_main_type'
    temp_data['data']['user_id'] = user_id
    
    # جلب الأنواع الرئيسية
    main_types = db.get_main_types()
    
    keyboard = []
    for type_obj in main_types:
        keyboard.append([
            InlineKeyboardButton(
                f"{type_obj['icon']} {type_obj['name']}", 
                callback_data=f"maintype_{type_obj['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
╔════════════════════════╗
  ➕ إضافة معاملة جديدة
╚════════════════════════╝

🔹 الخطوة 1/7: اختر نوع المعاملة:
"""
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SELECT_MAIN_TYPE

async def select_main_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار النوع الرئيسي"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    # استخراج ID
    type_id = int(query.data.split('_')[1])
    temp_data['data']['main_type_id'] = type_id
    
    # جلب التفريعات
    subtypes = db.get_subtypes(type_id)
    
    if not subtypes:
        # لا توجد تفريعات، ننتقل مباشرة لإدخال العنوان
        temp_data['data']['transaction_type_id'] = type_id
        temp_data['stage'] = 'enter_title'
        
        message = """
╔════════════════════════╗
  ✏️ إدخال العنوان
╚════════════════════════╝

🔹 الخطوة 2/7: أدخل عنوان المعاملة:

مثال: "عقد أحمد محمد - تجديد"
"""
        
        await query.edit_message_text(message)
        return ENTER_TITLE
    
    # عرض التفريعات
    keyboard = []
    for subtype in subtypes:
        keyboard.append([
            InlineKeyboardButton(
                f"{subtype['icon']} {subtype['name']}", 
                callback_data=f"subtype_{subtype['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='add_transaction')])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    type_info = db.get_transaction_types()[type_id - 1]
    
    message = f"""
╔════════════════════════╗
  {type_info['icon']} {type_info['name']}
╚════════════════════════╝

🔹 الخطوة 2/7: اختر التفصيل:
"""
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SELECT_SUBTYPE

async def select_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار التفريع"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    # استخراج ID
    subtype_id = int(query.data.split('_')[1])
    temp_data['data']['transaction_type_id'] = subtype_id
    temp_data['stage'] = 'enter_title'
    
    message = """
╔════════════════════════╗
  ✏️ إدخال العنوان
╚════════════════════════╝

🔹 الخطوة 3/7: أدخل عنوان المعاملة:

مثال: "تأمين سيارة - أ ب ج 1234"

📝 اكتب العنوان الآن:
"""
    
    await query.edit_message_text(message)
    return ENTER_TITLE

async def enter_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال العنوان"""
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    title = update.message.text.strip()
    
    if len(title) < 3:
        await update.message.reply_text("❌ العنوان قصير جداً. أدخل عنواناً أطول:")
        return ENTER_TITLE
    
    temp_data['data']['title'] = title
    temp_data['stage'] = 'enter_end_date'
    
    # حفظ مؤقتاً
    message = f"""
✅ تم الحفظ مؤقتاً!

╔════════════════════════╗
  📅 تاريخ الانتهاء
╚════════════════════════╝

🔹 الخطوة 4/7: متى تنتهي المعاملة؟

📝 أدخل التاريخ بصيغة: YYYY-MM-DD
مثال: 2026-01-15

أو اختر من الأزرار:
"""
    
    # أزرار تواريخ سريعة
    today = datetime.now().date()
    keyboard = [
        [
            InlineKeyboardButton("📅 بعد أسبوع", callback_data=f"quickdate_{(today + timedelta(days=7)).strftime('%Y-%m-%d')}"),
            InlineKeyboardButton("📅 بعد شهر", callback_data=f"quickdate_{(today + timedelta(days=30)).strftime('%Y-%m-%d')}")
        ],
        [
            InlineKeyboardButton("📅 بعد 3 أشهر", callback_data=f"quickdate_{(today + timedelta(days=90)).strftime('%Y-%m-%d')}"),
            InlineKeyboardButton("📅 بعد 6 أشهر", callback_data=f"quickdate_{(today + timedelta(days=180)).strftime('%Y-%m-%d')}")
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data='cancel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    return ENTER_END_DATE

async def quick_date_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار تاريخ سريع"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    # استخراج التاريخ
    date_str = query.data.split('_')[1]
    temp_data['data']['end_date'] = date_str
    
    # الانتقال لاختيار المسؤول
    return await show_responsible_selection(query, user_id, temp_data)

async def enter_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال تاريخ الانتهاء"""
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    date_text = update.message.text.strip()
    
    # التحقق من صحة التاريخ
    try:
        date_obj = datetime.strptime(date_text, '%Y-%m-%d')
        today = datetime.now().date()
        
        if date_obj.date() < today:
            await update.message.reply_text("❌ التاريخ في الماضي! أدخل تاريخاً في المستقبل:")
            return ENTER_END_DATE
        
        temp_data['data']['end_date'] = date_text
        
        # الانتقال لاختيار المسؤول
        return await show_responsible_selection_message(update, user_id, temp_data)
        
    except ValueError:
        await update.message.reply_text("""
❌ صيغة التاريخ خاطئة!

استخدم: YYYY-MM-DD
مثال: 2026-01-15
""")
        return ENTER_END_DATE

async def show_responsible_selection_message(update: Update, user_id: int, temp_data: dict):
    """عرض اختيار المسؤول (من رسالة)"""
    users = db.get_all_users()
    
    keyboard = []
    for user in users[:10]:  # أول 10 مستخدمين
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {user['full_name']}", 
                callback_data=f"responsible_{user['user_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⏭️ تخطي", callback_data='responsible_skip')])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
✅ تم الحفظ مؤقتاً!

╔════════════════════════╗
  👤 الشخص المسؤول
╚════════════════════════╝

🔹 الخطوة 5/7: من المسؤول عن هذه المعاملة؟

اختر من القائمة أو تخطي:
"""
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    return SELECT_RESPONSIBLE

async def show_responsible_selection(query, user_id: int, temp_data: dict):
    """عرض اختيار المسؤول (من callback)"""
    users = db.get_all_users()
    
    keyboard = []
    for user in users[:10]:
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {user['full_name']}", 
                callback_data=f"responsible_{user['user_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⏭️ تخطي", callback_data='responsible_skip')])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
✅ تم الحفظ مؤقتاً!

╔════════════════════════╗
  👤 الشخص المسؤول
╚════════════════════════╝

🔹 الخطوة 5/7: من المسؤول عن هذه المعاملة؟

اختر من القائمة أو تخطي:
"""
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SELECT_RESPONSIBLE

async def select_responsible(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار المسؤول"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    if query.data == 'responsible_skip':
        temp_data['data']['responsible_person_id'] = None
    else:
        responsible_id = int(query.data.split('_')[1])
        temp_data['data']['responsible_person_id'] = responsible_id
    
    # الانتقال لاختيار المستلمين
    return await show_recipients_selection(query, user_id, temp_data)

async def show_recipients_selection(query, user_id: int, temp_data: dict):
    """عرض اختيار المستلمين"""
    users = db.get_all_users()
    selected = temp_data.get('selected_recipients', [])
    
    keyboard = []
    for user in users[:10]:
        is_selected = user['user_id'] in selected
        emoji = "✅" if is_selected else "⬜"
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {user['full_name']}", 
                callback_data=f"recipient_toggle_{user['user_id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("➕ جميع المدراء", callback_data='recipient_all_managers')
    ])
    keyboard.append([
        InlineKeyboardButton(f"✅ تأكيد ({len(selected)} مُختار)", callback_data='recipients_confirm'),
        InlineKeyboardButton("⏭️ تخطي", callback_data='recipients_skip')
    ])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
╔════════════════════════╗
  📧 مستلمي التنبيهات
╚════════════════════════╝

🔹 الخطوة 6/7: من سيستلم التنبيهات؟

✅ المُختارون: {len(selected)}

اختر واحد أو أكثر:
"""
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SELECT_RECIPIENTS

async def toggle_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل اختيار مستلم"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    if 'selected_recipients' not in temp_data:
        temp_data['selected_recipients'] = []
    
    recipient_id = int(query.data.split('_')[2])
    
    if recipient_id in temp_data['selected_recipients']:
        temp_data['selected_recipients'].remove(recipient_id)
    else:
        temp_data['selected_recipients'].append(recipient_id)
    
    # تحديث العرض
    return await show_recipients_selection(query, user_id, temp_data)

async def add_all_managers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة جميع المدراء"""
    query = update.callback_query
    await query.answer("✅ تم إضافة جميع المدراء")
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    managers = db.get_managers()
    
    if 'selected_recipients' not in temp_data:
        temp_data['selected_recipients'] = []
    
    for manager in managers:
        if manager['user_id'] not in temp_data['selected_recipients']:
            temp_data['selected_recipients'].append(manager['user_id'])
    
    return await show_recipients_selection(query, user_id, temp_data)

async def confirm_recipients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد المستلمين"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    temp_data['data']['reminder_recipients'] = temp_data.get('selected_recipients', [])
    
    # الانتقال للملاحظات
    message = """
╔════════════════════════╗
  📝 ملاحظات إضافية
╚════════════════════════╝

🔹 الخطوة 7/7: هل تريد إضافة ملاحظات؟

📝 اكتب ملاحظاتك أو تفاصيل إضافية:
(مثل: رقم اللوحة، رقم العقد، إلخ)

أو اضغط "تخطي" للانتقال للملخص:
"""
    
    keyboard = [[InlineKeyboardButton("⏭️ تخطي", callback_data='description_skip')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return ENTER_DESCRIPTION

async def skip_recipients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي المستلمين"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    temp_data['data']['reminder_recipients'] = []
    
    # الانتقال للملاحظات
    message = """
╔════════════════════════╗
  📝 ملاحظات إضافية
╚════════════════════════╝

🔹 الخطوة 7/7: هل تريد إضافة ملاحظات؟

📝 اكتب ملاحظاتك أو تفاصيل إضافية:

أو اضغط "تخطي" للانتقال للملخص:
"""
    
    keyboard = [[InlineKeyboardButton("⏭️ تخطي", callback_data='description_skip')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return ENTER_DESCRIPTION

async def enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال الملاحظات"""
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    description = update.message.text.strip()
    temp_data['data']['description'] = description
    
    # عرض الملخص
    return await show_summary(update, user_id, temp_data)

async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي الملاحظات"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    
    temp_data['data']['description'] = None
    
    # عرض الملخص
    return await show_summary_from_callback(query, user_id, temp_data)

async def show_summary(update: Update, user_id: int, temp_data: dict):
    """عرض ملخص المعاملة"""
    data = temp_data['data']
    
    # جلب المعلومات
    trans_type = db.get_transaction_types()[data['transaction_type_id'] - 1]
    responsible_name = "غير محدد"
    if data.get('responsible_person_id'):
        resp_user = db.get_user(data['responsible_person_id'])
        responsible_name = resp_user['full_name'] if resp_user else "غير محدد"
    
    recipients_count = len(data.get('reminder_recipients', []))
    
    days_left = calculate_days_left(data['end_date'])
    priority_emoji = get_priority_emoji(days_left)
    
    summary = f"""
╔════════════════════════════════╗
  📋 ملخص المعاملة (معاينة)
╚════════════════════════════════╝

{trans_type['icon']} النوع: {trans_type['name']}
📝 العنوان: {data['title']}
📅 تاريخ الانتهاء: {format_date(data['end_date'])}
⏰ الأيام المتبقية: {days_left} يوم {priority_emoji}
👤 المسؤول: {responsible_name}
📧 المستلمون: {recipients_count} شخص
"""
    
    if data.get('description'):
        summary += f"\n📝 الملاحظات:\n{data['description'][:100]}..."
    
    summary += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n❓ هل المعلومات صحيحة؟"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأكيد وحفظ", callback_data='transaction_confirm'),
            InlineKeyboardButton("✏️ تعديل", callback_data='transaction_edit')
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data='cancel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(summary, reply_markup=reply_markup)
    return CONFIRM_TRANSACTION

async def show_summary_from_callback(query, user_id: int, temp_data: dict):
    """عرض ملخص المعاملة من callback"""
    data = temp_data['data']
    
    trans_type = None
    all_types = db.get_transaction_types()
    for t in all_types:
        if t['id'] == data['transaction_type_id']:
            trans_type = t
            break
    
    responsible_name = "غير محدد"
    if data.get('responsible_person_id'):
        resp_user = db.get_user(data['responsible_person_id'])
        responsible_name = resp_user['full_name'] if resp_user else "غير محدد"
    
    recipients_count = len(data.get('reminder_recipients', []))
    
    days_left = calculate_days_left(data['end_date'])
    priority_emoji = get_priority_emoji(days_left)
    
    summary = f"""
╔════════════════════════════════╗
  📋 ملخص المعاملة (معاينة)
╚════════════════════════════════╝

{trans_type['icon']} النوع: {trans_type['name']}
📝 العنوان: {data['title']}
📅 تاريخ الانتهاء: {format_date(data['end_date'])}
⏰ الأيام المتبقية: {days_left} يوم {priority_emoji}
👤 المسؤول: {responsible_name}
📧 المستلمون: {recipients_count} شخص
"""
    
    if data.get('description'):
        summary += f"\n📝 الملاحظات:\n{data['description'][:100]}..."
    
    summary += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n❓ هل المعلومات صحيحة؟"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأكيد وحفظ", callback_data='transaction_confirm'),
            InlineKeyboardButton("✏️ تعديل", callback_data='transaction_edit')
        ],
        [InlineKeyboardButton("❌ إلغاء", callback_data='cancel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(summary, reply_markup=reply_markup)
    return CONFIRM_TRANSACTION

async def confirm_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد وحفظ المعاملة"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    temp_data = get_user_temp_data(user_id)
    data = temp_data['data']
    
    # رسالة الانتظار
    await query.edit_message_text("⏳ جاري الحفظ في قاعدة البيانات...")
    
    # حساب الأولوية
    days_left = calculate_days_left(data['end_date'])
    if days_left <= 3:
        priority = 'critical'
    elif days_left <= 7:
        priority = 'high'
    else:
        priority = 'normal'
    
    # حفظ في قاعدة البيانات
    transaction_id = db.add_transaction(
        transaction_type_id=data['transaction_type_id'],
        user_id=data['user_id'],
        title=data['title'],
        end_date=data['end_date'],
        responsible_person_id=data.get('responsible_person_id'),
        reminder_recipients=data.get('reminder_recipients', []),
        description=data.get('description'),
        priority=priority
    )
    
    if transaction_id:
        # نجح الحفظ
        trans_type = None
        all_types = db.get_transaction_types()
        for t in all_types:
            if t['id'] == data['transaction_type_id']:
                trans_type = t
                break
        
        success_message = f"""
✅ تم رفع المعاملة بنجاح!

━━━━━━━━━━━━━━━━━━━━━━━━
🎉 المعاملة #{transaction_id} محفوظة
━━━━━━━━━━━━━━━━━━━━━━━━

{trans_type['icon']} {data['title']}
📅 تنتهي: {format_date(data['end_date'])}
⏰ بعد: {days_left} يوم

📊 إحصائياتك:
• إجمالي معاملاتك: {db.get_user(user_id)['total_transactions']}
• التنبيهات: مجدولة تلقائياً ✅

━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📋 عرض المعاملة", callback_data=f'view_trans_{transaction_id}'),
                InlineKeyboardButton("➕ إضافة أخرى", callback_data='add_transaction')
            ],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_message, reply_markup=reply_markup)
        
        # حذف البيانات المؤقتة
        clear_user_temp_data(user_id)
        
        return ConversationHandler.END
    else:
        # فشل الحفظ
        await query.edit_message_text("""
❌ فشل حفظ المعاملة!

حدث خطأ أثناء الحفظ في قاعدة البيانات.
يُرجى المحاولة مرة أخرى.
""")
        
        clear_user_temp_data(user_id)
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = update.effective_user.id
        clear_user_temp_data(user_id)
        
        await query.edit_message_text("""
❌ تم إلغاء العملية

جميع البيانات المؤقتة تم حذفها.

/start - للعودة للقائمة الرئيسية
""")
    
    return ConversationHandler.END

# ==================== عرض المعاملات ====================

async def my_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معاملات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    transactions = db.get_transactions_by_role(user_id)
    
    if not transactions:
        message = """
📋 معاملاتك

لا توجد معاملات حالياً.

➕ ابدأ بإضافة معاملة جديدة!
"""
        keyboard = [[InlineKeyboardButton("➕ إضافة معاملة", callback_data='add_transaction')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        return
    
    # تصنيف المعاملات
    critical = [t for t in transactions if t['days_left'] <= 3]
    warning = [t for t in transactions if 3 < t['days_left'] <= 7]
    upcoming = [t for t in transactions if t['days_left'] > 7]
    
    message = f"""
📋 معاملاتك ({len(transactions)})

🔴 عاجلة: {len(critical)}
🟡 تحذير: {len(warning)}
🟢 قادمة: {len(upcoming)}

اختر فئة لعرضها:
"""
    
    keyboard = [
        [
            InlineKeyboardButton(f"🔴 عاجلة ({len(critical)})", callback_data='filter_critical'),
            InlineKeyboardButton(f"🟡 تحذير ({len(warning)})", callback_data='filter_warning')
        ],
        [
            InlineKeyboardButton(f"🟢 قادمة ({len(upcoming)})", callback_data='filter_upcoming'),
            InlineKeyboardButton("📊 الكل", callback_data='filter_all')
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

# ==================== الإحصائيات والمساعد الذكي ====================

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الإحصائيات"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    stats = db.get_stats(user_id if user['role'] != 'admin' else None)
    
    message = f"""
📊 الإحصائيات الشاملة

📈 نظرة عامة:
• إجمالي المعاملات: {stats['total']}
• 🔴 عاجلة: {stats['critical']}
• 🟡 تحذير: {stats['warning']}
• 🟢 قادمة: {stats['upcoming']}
• ⚪ آمنة: {stats['safe']}

📂 حسب النوع:
"""
    
    for type_data in stats['by_type'][:5]:
        message += f"\n{type_data['icon']} {type_data['name']}: {type_data['count']}"
    
    message += "\n\n━━━━━━━━━━━━━━━━━━"
    
    keyboard = [
        [InlineKeyboardButton("🤖 تحليل ذكي", callback_data='ai_analyze')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المساعد الذكي"""
    query = update.callback_query
    await query.answer()
    
    message = """
🤖 المساعد الذكي

اختر ما تريد:
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 تحليل شامل", callback_data='ai_analyze')],
        [InlineKeyboardButton("📅 جدولة ذكية", callback_data='ai_schedule')],
        [InlineKeyboardButton("💡 توصيات", callback_data='ai_recommendations')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def ai_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحليل الذكي"""
    query = update.callback_query
    await query.answer("⏳ جاري التحليل...")
    
    user_id = update.effective_user.id
    
    analysis = ai_agent.analyze_all_transactions(user_id)
    
    message = f"""
🤖 التحليل الذكي

📊 الإحصائيات:
• إجمالي: {analysis['total_transactions']}
• 🔴 عاجلة: {len(analysis['critical'])}
• 🟡 تحذير: {len(analysis['warning'])}
• ⚫ منتهية: {len(analysis['overdue'])}

💡 التوصيات الرئيسية:
"""
    
    for i, rec in enumerate(analysis['recommendations'][:3], 1):
        message += f"\n{i}. {rec['icon']} {rec['title']}\n   {rec['message']}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='ai_assistant')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

# ==================== القائمة الرئيسية ====================

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للقائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    
    # إعادة عرض القائمة
    await start(update, context)

# ==================== تشغيل البوت ====================

def run_bot():
    """تشغيل البوت"""
    token = os.environ.get('BOT_TOKEN')
    if not token:
        logger.error("❌ BOT_TOKEN غير موجود!")
        return
    
    application = Application.builder().token(token).build()
    
    # المحادثة الرئيسية لإضافة معاملة
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_transaction_start, pattern='^add_transaction$')],
        states={
            SELECT_MAIN_TYPE: [CallbackQueryHandler(select_main_type, pattern='^maintype_')],
            SELECT_SUBTYPE: [CallbackQueryHandler(select_subtype, pattern='^subtype_')],
            ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_title)],
            ENTER_END_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_end_date),
                CallbackQueryHandler(quick_date_select, pattern='^quickdate_')
            ],
            SELECT_RESPONSIBLE: [
                CallbackQueryHandler(select_responsible, pattern='^responsible_')
            ],
            SELECT_RECIPIENTS: [
                CallbackQueryHandler(toggle_recipient, pattern='^recipient_toggle_'),
                CallbackQueryHandler(add_all_managers, pattern='^recipient_all_managers$'),
                CallbackQueryHandler(confirm_recipients, pattern='^recipients_confirm$'),
                CallbackQueryHandler(skip_recipients, pattern='^recipients_skip$')
            ],
            ENTER_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_description),
                CallbackQueryHandler(skip_description, pattern='^description_skip$')
            ],
            CONFIRM_TRANSACTION: [
                CallbackQueryHandler(confirm_transaction, pattern='^transaction_confirm$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern='^cancel$'),
            CommandHandler('cancel', cancel)
        ]
    )
    
    application.add_handler(conv_handler)
    
    # الأوامر الأساسية
    application.add_handler(CommandHandler("start", start))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(my_transactions, pattern='^my_transactions$'))
    application.add_handler(CallbackQueryHandler(statistics, pattern='^statistics$'))
    application.add_handler(CallbackQueryHandler(ai_assistant, pattern='^ai_assistant$'))
    application.add_handler(CallbackQueryHandler(ai_analyze, pattern='^ai_analyze$'))
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern='^main_menu$'))
    
    logger.info("✅ البوت جاهز!")
    
    # تشغيل البوت
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    run_bot()
