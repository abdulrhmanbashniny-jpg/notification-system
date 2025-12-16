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
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Bot is active",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    # اختبار قاعدة البيانات
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    
    # اختبار الجداول
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
        "tables_ready": tables_exist
    })

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
        
        # تحويل النتائج لـ JSON
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

if __name__ == '__main__':
    print("🚀 Starting application...")
    
    # إنشاء الجداول عند بدء التشغيل
    if init_db():
        print("✅ Database initialized successfully")
    else:
        print("⚠️ Database initialization failed, but continuing...")
    
    port = int(os.environ.get('PORT', 10000))
    print(f"✅ Web server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
