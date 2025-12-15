import os
from flask import Flask, jsonify
from database_supabase import Database

app = Flask(__name__)
db = Database()

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'transactions-system'})

@app.route('/')
def index():
    stats = db.get_stats()
    transactions = db.get_active_transactions()
    
    html = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام إدارة المعاملات</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; 
            padding: 20px;
            margin: 0;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 40px; 
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }}
        .stat {{ 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px; 
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .stat-number {{ 
            font-size: 3em; 
            font-weight: bold; 
        }}
        .stat-label {{ 
            font-size: 1.2em; 
            margin-top: 10px; 
        }}
        .transactions {{ 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 40px;
        }}
        .transactions h2 {{
            margin-top: 0;
            font-size: 1.8em;
        }}
        .transaction {{ 
            background: rgba(255,255,255,0.05); 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 10px; 
            border-right: 5px solid #10b981;
        }}
        .transaction.critical {{ 
            border-right-color: #ef4444; 
        }}
        .transaction.warning {{ 
            border-right-color: #f59e0b; 
        }}
        .footer {{
            text-align: center;
            padding: 30px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            margin-top: 40px;
        }}
        .footer p {{
            margin: 10px 0;
            font-size: 1.1em;
        }}
        .footer .developer {{
            font-weight: bold;
            font-size: 1.2em;
            color: #fbbf24;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 نظام إدارة المعاملات</h1>
            <p>النظام الذكي لإدارة معاملاتك</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{stats['total']}</div>
                <div class="stat-label">📊 إجمالي</div>
            </div>
            <div class="stat">
                <div class="stat-number">{stats['critical']}</div>
                <div class="stat-label">🔴 عاجلة</div>
            </div>
            <div class="stat">
                <div class="stat-number">{stats['warning']}</div>
                <div class="stat-label">🟡 تحذير</div>
            </div>
            <div class="stat">
                <div class="stat-number">{stats['upcoming']}</div>
                <div class="stat-label">🟢 قادمة</div>
            </div>
        </div>
        
        <div class="transactions">
            <h2>📋 المعاملات النشطة</h2>
"""
    
    for trans in transactions[:10]:
        days = trans.get('days_left', 0)
        css_class = 'critical' if days <= 3 else 'warning' if days <= 7 else ''
        emoji = "🔴" if days <= 3 else "🟡" if days <= 7 else "🟢"
        
        html += f"""
            <div class="transaction {css_class}">
                <strong>{emoji} {trans['title']}</strong><br>
                📅 {trans['end_date']} • ⏰ {days} يوم • 👤 {trans['user_name']}
            </div>
"""
    
    html += """
        </div>
        
        <div class="footer">
            <p>💻 تم تصميم هذا الموقع من قبل المبرمج</p>
            <p class="developer">عبدالرحمن سالم باشنيني</p>
        </div>
    </div>
</body>
</html>
"""
    return html

@app.route('/api/stats')
def api_stats():
    return jsonify(db.get_stats())

@app.route('/api/transactions')
def api_transactions():
    return jsonify(db.get_active_transactions())

def run_web():
    port = int(os.environ.get('PORT', 10000))  # ✅ يجب أن يكون هكذا
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    run_web()
