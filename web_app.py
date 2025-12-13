from flask import Flask, render_template_string, jsonify, request, send_file
from database import Database
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import os

app = Flask(__name__)
db = Database()

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - نظام إدارة المعاملات</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin-bottom: 10px; }
        .header-buttons { margin-top: 20px; }
        .header-buttons a { background: white; color: #667eea; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin: 5px; }
        .header-buttons a:hover { background: #f0f0f0; }
        .header-buttons a.secondary { background: rgba(255,255,255,0.2); color: white; }
        .header-buttons a.secondary:hover { background: rgba(255,255,255,0.3); }
        .container { max-width: 1200px; margin: 20px auto; padding: 20px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-box h3 { font-size: 32px; margin-bottom: 5px; }
        .stat-box p { opacity: 0.9; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: right; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; }
        tr:hover { background: #f5f5f5; }
        .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
        .btn:hover { background: #764ba2; }
        .footer { text-align: center; padding: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 لوحة التحكم - نظام إدارة المعاملات</h1>
        <p>إدارة شاملة لجميع المعاملات والتنبيهات</p>
        <div class="header-buttons">
            <a href="/add-transaction">➕ إضافة معاملة جديدة</a>
            <a href="/admin/register-admin" class="secondary">👤 تسجيل مسؤول</a>
            <a href="/admin/add-sample-data" class="secondary">📊 بيانات تجريبية</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-box">
                <h3>{{ stats.total_transactions }}</h3>
                <p>معاملة نشطة</p>
            </div>
            <div class="stat-box">
                <h3>{{ stats.total_users }}</h3>
                <p>مستخدم</p>
            </div>
            <div class="stat-box">
                <h3>{{ stats.pending_notifications }}</h3>
                <p>تنبيه قادم</p>
            </div>
        </div>
        
        <div class="card">
            <h2>📥 تصدير البيانات إلى Excel</h2>
            <p style="color: #666; margin-bottom: 15px;">اختر نوع المعاملات لتصديرها:</p>
            <a href="/export/contracts" class="btn">📝 عقود العمل</a>
            <a href="/export/vacations" class="btn">🏖️ الإجازات</a>
            <a href="/export/vehicles" class="btn">🚗 السيارات</a>
            <a href="/export/licenses" class="btn">📄 التراخيص</a>
            <a href="/export/courts" class="btn">⚖️ الجلسات القضائية</a>
            <a href="/export/all" class="btn" style="background: #28a745;">📊 تصدير الكل</a>
        </div>
        
        <div class="card">
            <h2>📋 آخر المعاملات النشطة</h2>
            {% if transactions %}
            <table>
                <thead>
                    <tr>
                        <th>العنوان</th>
                        <th>النوع</th>
                        <th>المستخدم</th>
                        <th>تاريخ الانتهاء</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in transactions[:10] %}
                    <tr>
                        <td>{{ t.title }}</td>
                        <td>{{ t.type_name }}</td>
                        <td>{{ t.user_name }}</td>
                        <td>{{ t.end_date }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #999; padding: 40px;">لا توجد معاملات نشطة حالياً</p>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>👥 المستخدمين المسجلين</h2>
            {% if users %}
            <table>
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>رقم الجوال</th>
                        <th>الصلاحية</th>
                        <th>تاريخ التسجيل</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td>{{ u.full_name }}</td>
                        <td>{{ u.phone_number }}</td>
                        <td>{% if u.is_admin %}👑 مسؤول{% else %}👤 مستخدم{% endif %}</td>
                        <td>{{ u.created_at }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #999; padding: 40px;">لا يوجد مستخدمين مسجلين</p>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p>🤖 نظام إدارة المعاملات والتنبيهات</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """الصفحة الرئيسية - Dashboard"""
    try:
        stats = {
            'total_transactions': len(db.get_active_transactions()),
            'total_users': len(db.get_all_users()),
            'pending_notifications': len(db.get_pending_notifications())
        }
        
        transactions = db.get_active_transactions()
        users = db.get_all_users()
        types = db.get_transaction_types()
        
        for t in transactions:
            user = next((u for u in users if u['user_id'] == t['user_id']), None)
            t['user_name'] = user['full_name'] if user else 'غير معروف'
            
            trans_type = next((ty for ty in types if ty['id'] == t['transaction_type_id']), None)
            t['type_name'] = trans_type['name'] if trans_type else 'غير محدد'
        
        return render_template_string(DASHBOARD_TEMPLATE, stats=stats, transactions=transactions, users=users)
    except Exception as e:
        return f"<h1>خطأ في الصفحة الرئيسية</h1><p>{str(e)}</p>", 500

@app.route('/export/<transaction_type>')
def export_data(transaction_type):
    """تصدير البيانات إلى Excel"""
    try:
        transactions = db.get_active_transactions()
        
        type_map = {
            'contracts': 1,
            'vacations': 2,
            'vehicles': 3,
            'licenses': 4,
            'courts': 5
        }
        
        if transaction_type != 'all':
            type_id = type_map.get(transaction_type)
            if type_id:
                transactions = [t for t in transactions if t['transaction_type_id'] == type_id]
        
        if not transactions:
            return "لا توجد بيانات لتصديرها", 404
        
        df = pd.DataFrame(transactions)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='المعاملات')
        
        output.seek(0)
        
        filename = f'transactions_{transaction_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return f"حدث خطأ: {str(e)}", 500

@app.route('/admin/add-sample-data')
def add_sample_data_route():
    """صفحة إضافة البيانات التجريبية"""
    try:
        # إضافة مستخدمين
        users_data = [
            (1001, "+966501234567", "أحمد محمد العلي", 1),
            (1002, "+966502345678", "فاطمة سعيد الأحمدي", 0),
            (1003, "+966503456789", "خالد عبدالله القحطاني", 0),
            (1004, "+966504567890", "نورة حسن المطيري", 0),
            (1005, "+966505678901", "سعد فهد الدوسري", 0),
            (1006, "+966506789012", "مريم علي الزهراني", 0),
            (1007, "+966507890123", "عبدالعزيز راشد العتيبي", 0),
            (1008, "+966508901234", "هند محمد الشمري", 0),
            (1009, "+966509012345", "ماجد يوسف الغامدي", 0),
            (1010, "+966500123456", "ريم إبراهيم السبيعي", 0),
        ]
        
        for user_id, phone, name, is_admin in users_data:
            db.add_user(user_id, phone, name, is_admin)
        
        # إضافة عقود عمل
        contracts = [
            ("عقد عمل - أحمد محمد", {"اسم_الموظف": "أحمد محمد العلي"}, 1001, 90),
            ("عقد عمل - فاطمة سعيد", {"اسم_الموظف": "فاطمة سعيد الأحمدي"}, 1002, 120),
            ("عقد عمل - خالد عبدالله", {"اسم_الموظف": "خالد عبدالله القحطاني"}, 1003, 180),
            ("عقد عمل - نورة حسن", {"اسم_الموظف": "نورة حسن المطيري"}, 1004, 150),
            ("عقد عمل - سعد فهد", {"اسم_الموظف": "سعد فهد الدوسري"}, 1005, 200),
        ]
        
        for title, data, user_id, days_until in contracts:
            end_date = (datetime.now() + timedelta(days=days_until)).strftime('%Y-%m-%d')
            trans_id = db.add_transaction(1, user_id, title, data, end_date)
            db.add_notification(trans_id, 30, [user_id])
        
        return '''
        <html dir="rtl">
        <head><meta charset="UTF-8"><title>تم بنجاح!</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h1>🎉 تم إضافة البيانات بنجاح!</h1>
            <p style="font-size: 20px; margin: 30px 0;">تم إضافة 10 مستخدمين و 5 معاملات</p>
            <a href="/" style="display: inline-block; background: white; color: #667eea; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px;">العودة للرئيسية</a>
        </body>
        </html>
        '''
    except Exception as e:
        return f'''
        <html dir="rtl">
        <head><meta charset="UTF-8"><title>خطأ</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ حدث خطأ</h1>
            <p>{str(e)}</p>
            <a href="/">العودة</a>
        </body>
        </html>
        '''

def run_web_app():
    """تشغيل الموقع"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_web_app()
