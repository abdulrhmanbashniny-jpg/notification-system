import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from database_supabase import Database
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# حالات المحادثة
(MAIN_MENU, ADD_TRANSACTION, EDIT_TRANSACTION, DELETE_TRANSACTION, 
 SELECT_TYPE, ENTER_TITLE, ENTER_DESCRIPTION, ENTER_START_DATE, 
 ENTER_END_DATE, SELECT_PRIORITY, CONFIRM_ADD, SELECT_TRANSACTION_TO_EDIT,
 EDIT_FIELD, EDIT_VALUE, SELECT_TRANSACTION_TO_DELETE, CONFIRM_DELETE,
 SEARCH_TRANSACTIONS, FILTER_TRANSACTIONS) = range(18)

class TransactionBot:
    def __init__(self, token: str, database: Database):
        self.token = token
        self.db = database
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
        # بيانات مؤقتة للمستخدمين
        self.user_data = {}
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر والرسائل"""
        
        # معالج المحادثة الرئيسي
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_command)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.add_transaction_start, pattern='^add_transaction$'),
                    CallbackQueryHandler(self.edit_transaction_start, pattern='^edit_transaction$'),
                    CallbackQueryHandler(self.delete_transaction_start, pattern='^delete_transaction$'),
                    CallbackQueryHandler(self.search_transactions_start, pattern='^search_transactions$'),
                    CallbackQueryHandler(self.filter_transactions_start, pattern='^filter_transactions$'),
                    CallbackQueryHandler(self.my_transactions, pattern='^my_transactions$'),
                    CallbackQueryHandler(self.statistics, pattern='^statistics$'),
                ],
                SELECT_TYPE: [CallbackQueryHandler(self.select_type_callback)],
                ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_title)],
                ENTER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_description)],
                ENTER_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_start_date)],
                ENTER_END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_end_date)],
                SELECT_PRIORITY: [CallbackQueryHandler(self.select_priority_callback)],
                CONFIRM_ADD: [CallbackQueryHandler(self.confirm_add_callback)],
                SELECT_TRANSACTION_TO_EDIT: [CallbackQueryHandler(self.select_transaction_to_edit_callback)],
                EDIT_FIELD: [CallbackQueryHandler(self.edit_field_callback)],
                EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.edit_value)],
                SELECT_TRANSACTION_TO_DELETE: [CallbackQueryHandler(self.select_transaction_to_delete_callback)],
                CONFIRM_DELETE: [CallbackQueryHandler(self.confirm_delete_callback)],
                SEARCH_TRANSACTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_transactions)],
                FILTER_TRANSACTIONS: [CallbackQueryHandler(self.filter_transactions_callback)],
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel),
                CommandHandler('menu', self.start_command)
            ],
        )
        
        self.app.add_handler(conv_handler)
        self.app.add_handler(CommandHandler('help', self.help_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية - القائمة الرئيسية"""
        user = update.effective_user
        user_id = user.id
        
        # تسجيل المستخدم في قاعدة البيانات إذا لم يكن موجوداً
        if not self.db.get_user(user_id):
            self.db.add_user(
                user_id=user_id,
                full_name=user.full_name or user.username,
                telegram_username=user.username
            )
        
        keyboard = [
            [
                InlineKeyboardButton("➕ إضافة معاملة", callback_data='add_transaction'),
                InlineKeyboardButton("✏️ تعديل معاملة", callback_data='edit_transaction')
            ],
            [
                InlineKeyboardButton("🗑️ حذف معاملة", callback_data='delete_transaction'),
                InlineKeyboardButton("🔍 بحث", callback_data='search_transactions')
            ],
            [
                InlineKeyboardButton("📊 معاملاتي", callback_data='my_transactions'),
                InlineKeyboardButton("📈 الإحصائيات", callback_data='statistics')
            ],
            [
                InlineKeyboardButton("🎯 فلترة حسب النوع", callback_data='filter_transactions')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🎉 مرحباً {user.full_name}!

📋 **نظام إدارة المعاملات**
v1.0.0

اختر من القائمة أدناه:
        """
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        
        return MAIN_MENU
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        help_text = """
📚 **دليل الاستخدام:**

**الأوامر الأساسية:**
/start - القائمة الرئيسية
/menu - العودة للقائمة
/cancel - إلغاء العملية الحالية
/help - عرض المساعدة

**الميزات المتاحة:**
✅ إضافة معاملات جديدة
✅ تعديل المعاملات الموجودة
✅ حذف المعاملات
✅ البحث عن المعاملات
✅ الفلترة حسب النوع/الحالة
✅ عرض إحصائيات شاملة
✅ تنبيهات تلقائية قبل انتهاء المعاملات

**التنبيهات التلقائية:**
🔔 سيتم إرسال تنبيهات قبل:
• 30 يوم من انتهاء المعاملة
• 15 يوم
• 7 أيام
• 3 أيام
• يوم الانتهاء

⏰ وقت الإرسال: 9:00 صباحاً يومياً
        """
        await update.message.reply_text(help_text)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء العملية الحالية"""
        user_id = update.effective_user.id
        if user_id in self.user_data:
            del self.user_data[user_id]
        
        await update.message.reply_text("❌ تم إلغاء العملية.")
        return await self.start_command(update, context)
    
    # ==================== إضافة معاملة ====================
    
    async def add_transaction_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بداية إضافة معاملة"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        self.user_data[user_id] = {'step': 'add_transaction'}
        
        # جلب أنواع المعاملات الرئيسية
        transaction_types = self.db.get_transaction_types(level=1)
        
        if not transaction_types:
            await query.edit_message_text("❌ لا توجد أنواع معاملات متاحة.")
            return MAIN_MENU
        
        keyboard = []
        for t_type in transaction_types:
            keyboard.append([InlineKeyboardButton(
                f"{t_type['icon']} {t_type['name']}", 
                callback_data=f"type_{t_type['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            "📝 **إضافة معاملة جديدة**\n\n1️⃣ اختر نوع المعاملة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_TYPE
    
    async def select_type_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختيار نوع المعاملة"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'back_to_menu':
            return await self.start_command(update, context)
        
        user_id = update.effective_user.id
        type_id = int(query.data.split('_')[1])
        
        self.user_data[user_id]['type_id'] = type_id
        
        # التحقق من وجود أنواع فرعية
        subtypes = self.db.get_transaction_types(parent_id=type_id)
        
        if subtypes:
            keyboard = []
            for subtype in subtypes:
                keyboard.append([InlineKeyboardButton(
                    f"{subtype['icon']} {subtype['name']}", 
                    callback_data=f"type_{subtype['id']}"
                )])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_types')])
            
            await query.edit_message_text(
                "📝 اختر النوع الفرعي:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return SELECT_TYPE
        
        await query.edit_message_text("2️⃣ أدخل عنوان المعاملة:")
        return ENTER_TITLE
    
    async def enter_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدخال عنوان المعاملة"""
        user_id = update.effective_user.id
        title = update.message.text
        
        self.user_data[user_id]['title'] = title
        
        await update.message.reply_text("3️⃣ أدخل وصف المعاملة (أو اكتب 'تخطي'):")
        return ENTER_DESCRIPTION
    
    async def enter_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدخال وصف المعاملة"""
        user_id = update.effective_user.id
        description = update.message.text if update.message.text.lower() != 'تخطي' else ''
        
        self.user_data[user_id]['description'] = description
        
        await update.message.reply_text(
            "4️⃣ أدخل تاريخ البداية (مثال: 2024-12-20 أو اكتب 'اليوم'):"
        )
        return ENTER_START_DATE
    
    async def enter_start_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدخال تاريخ البداية"""
        user_id = update.effective_user.id
        date_text = update.message.text
        
        try:
            if date_text.lower() == 'اليوم':
                start_date = datetime.now().date()
            else:
                start_date = datetime.strptime(date_text, '%Y-%m-%d').date()
            
            self.user_data[user_id]['start_date'] = start_date
            
            await update.message.reply_text(
                "5️⃣ أدخل تاريخ الانتهاء (مثال: 2024-12-31):"
            )
            return ENTER_END_DATE
            
        except ValueError:
            await update.message.reply_text(
                "❌ تنسيق التاريخ خاطئ. الرجاء إدخال التاريخ بالشكل: YYYY-MM-DD"
            )
            return ENTER_START_DATE
    
    async def enter_end_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدخال تاريخ الانتهاء"""
        user_id = update.effective_user.id
        date_text = update.message.text
        
        try:
            end_date = datetime.strptime(date_text, '%Y-%m-%d').date()
            start_date = self.user_data[user_id]['start_date']
            
            if end_date < start_date:
                await update.message.reply_text(
                    "❌ تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية. حاول مرة أخرى:"
                )
                return ENTER_END_DATE
            
            self.user_data[user_id]['end_date'] = end_date
            
            # اختيار الأولوية
            keyboard = [
                [InlineKeyboardButton("🟢 عادية", callback_data='priority_normal')],
                [InlineKeyboardButton("🟡 مهمة", callback_data='priority_high')],
                [InlineKeyboardButton("🔴 حرجة", callback_data='priority_critical')]
            ]
            
            await update.message.reply_text(
                "6️⃣ اختر أولوية المعاملة:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return SELECT_PRIORITY
            
        except ValueError:
            await update.message.reply_text(
                "❌ تنسيق التاريخ خاطئ. الرجاء إدخال التاريخ بالشكل: YYYY-MM-DD"
            )
            return ENTER_END_DATE
    
    async def select_priority_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختيار الأولوية"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        priority = query.data.split('_')[1]
        
        self.user_data[user_id]['priority'] = priority
        
        # عرض ملخص المعاملة
        data = self.user_data[user_id]
        type_name = self.db.get_transaction_type_name(data['type_id'])
        
        priority_emoji = {'normal': '🟢', 'high': '🟡', 'critical': '🔴'}
        priority_text = {'normal': 'عادية', 'high': 'مهمة', 'critical': 'حرجة'}
        
        summary = f"""
📋 **ملخص المعاملة الجديدة:**

📌 النوع: {type_name}
📝 العنوان: {data['title']}
📄 الوصف: {data.get('description', 'لا يوجد')}
📅 تاريخ البداية: {data['start_date']}
📅 تاريخ الانتهاء: {data['end_date']}
{priority_emoji[priority]} الأولوية: {priority_text[priority]}

هل تريد حفظ هذه المعاملة؟
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ حفظ", callback_data='confirm_yes'),
                InlineKeyboardButton("❌ إلغاء", callback_data='confirm_no')
            ]
        ]
        
        await query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM_ADD
    
    async def confirm_add_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد إضافة المعاملة"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if query.data == 'confirm_yes':
            data = self.user_data[user_id]
            
            # إضافة المعاملة لقاعدة البيانات
            transaction_id = self.db.add_transaction(
                transaction_type_id=data['type_id'],
                user_id=user_id,
                title=data['title'],
                description=data.get('description', ''),
                start_date=data['start_date'],
                end_date=data['end_date'],
                priority=data['priority']
            )
            
            if transaction_id:
                await query.edit_message_text(
                    f"✅ تم إضافة المعاملة بنجاح!\n\n🆔 رقم المعاملة: {transaction_id}"
                )
            else:
                await query.edit_message_text("❌ حدث خطأ أثناء إضافة المعاملة.")
            
            del self.user_data[user_id]
        else:
            await query.edit_message_text("❌ تم إلغاء إضافة المعاملة.")
            del self.user_data[user_id]
        
        await context.bot.send_message(
            chat_id=user_id,
            text="اضغط /menu للعودة للقائمة الرئيسية"
        )
        return ConversationHandler.END
    
    # ==================== تعديل معاملة ====================
    
    async def edit_transaction_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بداية تعديل معاملة"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # جلب معاملات المستخدم النشطة
        transactions = self.db.get_user_transactions(user_id, status='active')
        
        if not transactions:
            await query.edit_message_text("❌ ليس لديك معاملات نشطة للتعديل.")
            await context.bot.send_message(
                chat_id=user_id,
                text="اضغط /menu للعودة للقائمة"
            )
            return ConversationHandler.END
        
        keyboard = []
        for trans in transactions:
            keyboard.append([InlineKeyboardButton(
                f"📋 {trans['title']} (#{trans['transaction_id']})",
                callback_data=f"edit_{trans['transaction_id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            "✏️ **تعديل معاملة**\n\nاختر المعاملة التي تريد تعديلها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_TRANSACTION_TO_EDIT
    
    async def select_transaction_to_edit_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختيار المعاملة للتعديل"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'back_to_menu':
            return await self.start_command(update, context)
        
        user_id = update.effective_user.id
        transaction_id = int(query.data.split('_')[1])
        
        self.user_data[user_id] = {'transaction_id': transaction_id}
        
        # جلب تفاصيل المعاملة
        transaction = self.db.get_transaction(transaction_id)
        
        if not transaction:
            await query.edit_message_text("❌ المعاملة غير موجودة.")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("📝 تعديل العنوان", callback_data='edit_field_title')],
            [InlineKeyboardButton("📄 تعديل الوصف", callback_data='edit_field_description')],
            [InlineKeyboardButton("📅 تعديل تاريخ الانتهاء", callback_data='edit_field_end_date')],
            [InlineKeyboardButton("🎯 تعديل الأولوية", callback_data='edit_field_priority')],
            [InlineKeyboardButton("✅ تغيير الحالة", callback_data='edit_field_status')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')]
        ]
        
        await query.edit_message_text(
            f"✏️ **تعديل المعاملة #{transaction_id}**\n\n"
            f"📝 {transaction['title']}\n\n"
            f"اختر الحقل الذي تريد تعديله:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDIT_FIELD
    
    async def edit_field_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختيار الحقل المراد تعديله"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'back_to_menu':
            return await self.start_command(update, context)
        
        user_id = update.effective_user.id
        field = query.data.split('_')[2]
        
        self.user_data[user_id]['edit_field'] = field
        
        if field == 'priority':
            keyboard = [
                [InlineKeyboardButton("🟢 عادية", callback_data='new_value_normal')],
                [InlineKeyboardButton("🟡 مهمة", callback_data='new_value_high')],
                [InlineKeyboardButton("🔴 حرجة", callback_data='new_value_critical')]
            ]
            await query.edit_message_text(
                "اختر الأولوية الجديدة:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return EDIT_VALUE
        elif field == 'status':
            keyboard = [
                [InlineKeyboardButton("✅ نشطة", callback_data='new_value_active')],
                [InlineKeyboardButton("🎉 مكتملة", callback_data='new_value_completed')],
                [InlineKeyboardButton("❌ ملغية", callback_data='new_value_cancelled')]
            ]
            await query.edit_message_text(
                "اختر الحالة الجديدة:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return EDIT_VALUE
        else:
            prompts = {
                'title': 'أدخل العنوان الجديد:',
                'description': 'أدخل الوصف الجديد:',
                'end_date': 'أدخل تاريخ الانتهاء الجديد (YYYY-MM-DD):'
            }
            await query.edit_message_text(prompts.get(field, 'أدخل القيمة الجديدة:'))
            return EDIT_VALUE
    
    async def edit_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تطبيق التعديل"""
        user_id = update.effective_user.id
        data = self.user_data[user_id]
        
        if update.callback_query:
            # قيمة من زر
            new_value = update.callback_query.data.split('_')[2]
            await update.callback_query.answer()
            message = update.callback_query
        else:
            # قيمة من نص
            new_value = update.message.text
            message = update.message
        
        field = data['edit_field']
        transaction_id = data['transaction_id']
        
        # التحقق من صحة التاريخ
        if field == 'end_date':
            try:
                new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
            except ValueError:
                await update.message.reply_text(
                    "❌ تنسيق التاريخ خاطئ. استخدم: YYYY-MM-DD"
                )
                return EDIT_VALUE
        
        # تحديث قاعدة البيانات
        success = self.db.update_transaction(transaction_id, {field: new_value})
        
        if success:
            text = f"✅ تم تعديل {field} بنجاح!"
        else:
            text = "❌ حدث خطأ أثناء التعديل."
        
        if update.callback_query:
            await message.edit_message_text(text)
        else:
            await message.reply_text(text)
        
        del self.user_data[user_id]
        await context.bot.send_message(
            chat_id=user_id,
            text="اضغط /menu للعودة للقائمة"
        )
        return ConversationHandler.END
    
    # ==================== حذف معاملة ====================
    
    async def delete_transaction_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بداية حذف معاملة"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        transactions = self.db.get_user_transactions(user_id, status='active')
        
        if not transactions:
            await query.edit_message_text("❌ ليس لديك معاملات للحذف.")
            await context.bot.send_message(
                chat_id=user_id,
                text="اضغط /menu للعودة للقائمة"
            )
            return ConversationHandler.END
        
        keyboard = []
        for trans in transactions:
            keyboard.append([InlineKeyboardButton(
                f"🗑️ {trans['title']} (#{trans['transaction_id']})",
                callback_data=f"delete_{trans['transaction_id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            "🗑️ **حذف معاملة**\n\nاختر المعاملة التي تريد حذفها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_TRANSACTION_TO_DELETE
    
    async def select_transaction_to_delete_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختيار المعاملة للحذف"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'back_to_menu':
            return await self.start_command(update, context)
        
        user_id = update.effective_user.id
        transaction_id = int(query.data.split('_')[1])
        
        self.user_data[user_id] = {'transaction_id': transaction_id}
        
        transaction = self.db.get_transaction(transaction_id)
        
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم، احذف", callback_data='confirm_delete_yes'),
                InlineKeyboardButton("❌ لا، إلغاء", callback_data='confirm_delete_no')
            ]
        ]
        
        await query.edit_message_text(
            f"⚠️ **تأكيد الحذف**\n\n"
            f"هل أنت متأكد من حذف المعاملة:\n\n"
            f"📝 {transaction['title']}\n"
            f"🆔 #{transaction_id}\n\n"
            f"⚠️ لا يمكن التراجع عن هذا الإجراء!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRM_DELETE
    
    async def confirm_delete_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد حذف المعاملة"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if query.data == 'confirm_delete_yes':
            transaction_id = self.user_data[user_id]['transaction_id']
            
            success = self.db.delete_transaction(transaction_id)
            
            if success:
                await query.edit_message_text(f"✅ تم حذف المعاملة #{transaction_id} بنجاح!")
            else:
                await query.edit_message_text("❌ حدث خطأ أثناء الحذف.")
        else:
