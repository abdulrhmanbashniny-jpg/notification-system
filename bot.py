async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار - نسخة محسنة"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_user(user_id)
    
    if not db_user:
        await query.message.reply_text("⚠️ يرجى التسجيل أولاً بإرسال /start")
        return
    
    # ✅ إضافة رسالة فورية للمستخدم
    loading_msg = None
    
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
        # ✅ رسالة تحميل فورية
        try:
            await query.message.edit_text("⏳ جاري تحميل المعاملات...")
        except:
            pass
        
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
        # ✅ رسالة تحميل فورية
        try:
            await query.message.edit_text("⏳ جاري حساب الإحصائيات...")
        except:
            pass
        
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
            # ✅ رسالة تحميل فورية
            try:
                await query.message.edit_text("⏳ جاري تحميل لوحة الإدارة...")
            except:
                pass
            
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
