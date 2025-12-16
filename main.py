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
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
