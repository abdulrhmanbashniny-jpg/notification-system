import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request
import psycopg2
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

app = Flask(__name__)

# متغيرات عامة
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://notification-system-cm5l.onrender.com')
bot_app = None

# وظيفة الاتصال بقاعدة البيانات
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Database error: {e}")
        return None

# إنشاء الجداول
def init_db():
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot initialize database")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                description TEXT,
                due_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database tables created")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

# ═══════════════════════════════════════
# Bot Commands
# ═══════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    await update.message.reply_text(
        "🤖 مرحباً بك في بوت إدارة المعاملات!\n\n"
        "الأوامر المتاحة:\n"
        "/start - عرض هذه الرسالة\n"
        "/list - عرض جميع المعاملات\n"
        "/help - المساعدة"
    )

async def list_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المعاملات"""
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("❌ خطأ في الاتصال بقاعدة البيانات")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, amount, description, due_date, status 
            FROM transactions 
            WHERE user_id = %s
            ORDER BY created_at DESC 
            LIMIT 10
        """, (update.effective_user.id,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            await update.message.reply_text("📋 لا توجد معاملات مسجلة بعد")
            return
        
        message = "📋 معاملاتك:\n\n"
        for row in rows:
            message += f"🆔 #{row[0]}\n"
            message += f"💰 المبلغ: {row[1]} ريال\n"
            message += f"📝 الوصف: {row[2]}\n"
            message += f"📅 الاستحقاق: {row[3]}\n"
            message += f"✅ الحالة: {row[4]}\n"
            message += "─────────────\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    await update.message.reply_text(
        "ℹ️ دليل الاستخدام\n\n"
        "هذا البوت يساعدك على إدارة معاملاتك المالية\n\n"
        "الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/list - عرض المعاملات\n"
        "/help - المساعدة"
    )

# ═══════════════════════════════════════
# Initialize Bot
# ═══════════════════════════════════════

def init_bot():
    """إنشاء البوت"""
    global bot_app
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found")
        return None
    
    try:
        print("🤖 Initializing Telegram Bot...")
        
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # تسجيل الأوامر
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("list", list_transactions))
        bot_app.add_handler(CommandHandler("help", help_command))
        
        print("✅ Bot initialized successfully")
        return bot_app
        
    except Exception as e:
        print(f"❌ Bot initialization error: {e}")
        return None

# ═══════════════════════════════════════
# Flask Routes
# ═══════════════════════════════════════

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Bot is active",
        "version": "3.0.0"
    })

@app.route('/health')
def health():
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    
    tables_exist = False
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'transactions'
                )
            """)
            tables_exist = cursor.fetchone()[0]
            cursor.close()
        except:
            pass
        conn.close()
    
    return jsonify({
        "status": "ok",
        "database": db_status,
        "tables_ready": tables_exist,
        "bot": "initialized" if bot_app else "not initialized"
    })

@app.route('/webhook', methods=['POST'])
async def webhook():
    """استقبال رسائل من Telegram"""
    if not bot_app:
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook')
async def set_webhook():
    """تفعيل الـ Webhook"""
    if not bot_app:
        return jsonify({"error": "Bot not initialized"}), 500
    
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await bot_app.bot.set_webhook(webhook_url)
        return jsonify({
            "status": "success",
            "webhook_url": webhook_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transactions')
def transactions():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, amount, description, due_date, status, created_at 
            FROM transactions 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        
        transactions_list = []
        for row in rows:
            transactions_list.append({
                "id": row[0],
                "user_id": row[1],
                "amount": float(row[2]),
                "description": row[3],
                "due_date": str(row[4]),
                "status": row[5],
                "created_at": str(row[6])
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "count": len(transactions_list),
            "transactions": transactions_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

if __name__ == '__main__':
    print("🚀 Starting application...")
    
    # إنشاء الجداول
    if init_db():
        print("✅ Database initialized")
    
    # إنشاء البوت
    init_bot()
    
    # تشغيل Web Server
    port = int(os.environ.get('PORT', 10000))
    print(f"✅ Web server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
