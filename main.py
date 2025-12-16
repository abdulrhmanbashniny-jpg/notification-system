import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

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
        return
    
    try:
        cursor = conn.cursor()
        
        # جدول المعاملات
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
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Bot is active"
    })

@app.route('/health')
def health():
    # اختبار قاعدة البيانات
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
    
    return jsonify({
        "status": "ok",
        "database": db_status
    })

@app.route('/transactions')
def transactions():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            "count": len(rows),
            "transactions": rows
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # إنشاء الجداول عند بدء التشغيل
    print("🚀 Starting application...")
    init_db()
    
    port = int(os.environ.get('PORT', 10000))
    print(f"✅ Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
