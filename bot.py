import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database
from ai_assistant import AIAssistant
from notifications import NotificationSystem
from config import TELEGRAM_BOT_TOKEN, MAX_NOTIFICATIONS_PER_ITEM, TRANSACTION_TYPES
import json
from datetime import datetime

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة الأنظمة
db = Database()
ai = AIAssistant()
notification_system = NotificationSystem()

# حالات المحادثة
WAITING_FOR_PHONE = 1
WAITING_FOR_NAME = 2
SELECTING_TRANSACTION_TYPE = 3
ENTERING_TRANSACTION_DATA = 4
SETTING_NOTIFICATIONS = 5
AI_CHAT_MODE = 6

# تخزين مؤقت لبيانات المستخدمين
user_sessions = {}

# ========== وظائف البداية والتسجيل ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    user_id = user.id
    
    # التحقق من وجود المستخدم
    db_user = db.get_user(user_id)
    
    if not db_user:
        # طلب رقم الجوال للتسجيل
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
    
    # طلب الاسم الكامل
    user_sessions[user_id] = {
        'state': WAITING_FOR_NAME,
        'phone_number': phone_number
    }
    
    await update.message.reply_text(
        "شكراً! الآن أدخل اسمك الكامل:",
        reply_markup=telegram.ReplyKeyboardRemove()
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # التحقق من حالة المستخدم
    if user_id not in user_sessions:
        user_sessions[user_id] = {'state': None}
    
    session = user_sessions[user_id]
    state = session.get('state')
    
    # حالة إدخال الاسم
    if state == WAITING_FOR_NAME:
        full_name = text
        phone_number = session['phone_number']
        
        # إضافة المستخدم لقاعدة البيانات
        # أول مستخدم يكون مسؤول
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
    
    # وضع المحادثة مع الذكاء الاصطناعي
    elif state == AI_CHAT_MODE:
        await update.message.reply_text("⏳ جاري البحث...")
        response = ai.query(text, user_id)
        await update.message.reply_text(response)
    
    # حالات أخرى
    else:
        db_user = db.get_user(user_id)
        if db_user:
            await show_main_menu(update, context, db_user)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """عرض القائمة الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة معاملة جديدة", callback_data="add_transaction")],
        [InlineKeyboardButton("📋 معاملاتي النشطة", callback_data="my_transactions")],
        [InlineKeyboardButton("🤖 المساعد الذكي", callback_data="ai_assistant")],
        [InlineKeyboardButton("📊 تصدير Excel", callback_data="export_excel")],
    ]
    
    if user['is_admin']:
        keyboard.append([InlineKeyboardButton("⚙️ إدارة النظام", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = f"مرحباً {user['full_name']}! 👋\n\n"
    message_text += "اختر من القائمة:"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

# ========== وظائف إضافة المعاملات ==========

async def add_transaction_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية إضافة معاملة"""
    query = update.callback_query
    await query.answer()
    
    # عرض أنواع المعاملات
    types = db.get_transaction_types()
    
    keyboard = []
    for trans_type in types:
        keyboard.append([InlineKeyboardButton(
            trans_type['type_name'].replace('_', ' '),
            callback_data=f"type_{trans_type['type_id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "اختر نوع المعاملة:",
        reply_markup=reply_markup
    )

async def handle_transaction_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار نوع المعاملة"""
    query = update.callback_query
    await query.answer()
    
    type_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    # حفظ في الجلسة
    user_sessions[user_id] = {
        'state': ENTERING_TRANSACTION_DATA,
        'type_id': type_id,
        'data': {}
    }
    
    # الحصول على الحقول المطلوبة
    types = db.get_transaction_types()
    selected_type = next((t for t in types if t['type_id'] == type_id), None)
    
    if selected_type:
        await query.message.edit_text(
            f"إضافة معاملة: {selected_type['type_name'].replace('_', ' ')}\n\n"
            f"يرجى إرسال البيانات بالتنسيق التالي:\n\n"
            f"العنوان: [عنوان المعاملة]\n"
            f"التاريخ: YYYY-MM-DD\n"
            f"[أي معلومات إضافية]\n\n"
            f"أو اكتب 'إلغاء' للرجوع."
        )

# ========== (يتبع في التعليق التالي) ==========
