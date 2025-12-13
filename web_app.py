from flask import Flask, render_template_string, jsonify, request, send_file
from database import Database
import pandas as pd
from io import BytesIO
from datetime import datetime

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
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .container { max-width: 1200px; margin: 20px auto; padding: 20px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-box h3 { font-size: 32px; margin-bottom: 5px; }
        .stat-box p { opacity: 0.9; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: right; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; }
        .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
        .btn:hover { background: #764ba2; }
        .footer { text-align: center; padding: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 لوحة التحكم - نظام إدارة المعاملات</h1>
        <p>إدارة شاملة لجميع المعاملات والتنبيهات</p>
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
            <h2>📊 تصدير البيانات إلى Excel</h2>
            <p>اختر نوع المعاملات لتصديرها:</p>
            <a href="/export/all" class="btn">📥 تصدير الكل</a>
            <a href="/export/contracts" class="btn">📝 عقود العمل</a>
            <a href="/export/vacations" class="btn">🏖️ الإجازات</a>
            <a href="/export/vehicles" class="btn">🚗 السيارات</a>
            <a href="/export/licenses" class="btn">📄 التراخيص</a>
            <a href="/export/court" class="btn">⚖️ القضايا</a>
        </div>
        
        <div class="card">
            <h2>📋 آخر المعاملات النشطة</h2>
            {% if recent_transactions %}
            <table>
                <thead>
                    <tr>
                        <th>العنوان</th>
                        <th>النوع</th>
                        <th>المنشئ</th>
                        <th>تاريخ الانتهاء</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trans in recent_transactions %}
                    <tr>
                        <td>{{ trans.title }}</td>
                        <td>{{ trans.type_name }}</td>
                        <td>{{ trans.creator_name }}</td>
                        <td>{{ trans.end_date or 'غير محدد' }}</td>
                        <td>✅ نشط</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #999;">لا توجد معاملات نشطة حالياً</p>
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
                    {% for user in users %}
                    <tr>
                        <td>{{ user.full_name }}</td>
                        <td>{{ user.phone_number }}</td>
                        <td>{{ '👑 مسؤول' if user.is_admin else '👤 مستخدم' }}</td>
                        <td>{{ user.created_at }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #999;">لا يوجد مستخدمين مسجلين</p>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p>© 2025 نظام إدارة المعاملات والتنبيهات | تم التطوير بواسطة الذكاء الاصطناعي 🤖</p>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """الصفحة الرئيسية - الداش بورد"""
    transactions = db.get_active_transactions()
    users = db.get_all_users()
    
    stats = {
        'total_transactions': len(transactions),
        'total_users': len(users),
        'pending_notifications': len(db.get_due_notifications())
    }
    
    recent_transactions = transactions[:10]
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                   stats=stats, 
                                   recent_transactions=recent_transactions,
                                   users=users)

@app.route('/export/<type>')
def export_excel(type):
    """تصدير البيانات إلى Excel"""
    if type == 'all':
        transactions = db.get_active_transactions()
        filename_prefix = 'جميع_المعاملات'
    else:
        type_map = {
            'contracts': 'عقد_عمل',
            'vacations': 'إجازة_موظف',
            'vehicles': 'استمارة_سيارة',
            'licenses': 'ترخيص',
            'court': 'جلسة_قضائية'
        }
        type_name = type_map.get(type, 'أخرى')
        transactions = [t for t in db.get_active_transactions() if t['type_name'] == type_name]
        filename_prefix = type_name.replace('_', ' ')
    
    if not transactions:
        return "لا توجد بيانات للتصدير", 404
    
    # تحويل للـ DataFrame
    data = []
    for trans in transactions:
        row = {
            'العنوان': trans['title'],
            'النوع': trans['type_name'].replace('_', ' '),
            'المنشئ': trans['creator_name'],
            'تاريخ_الانتهاء': trans.get('end_date', 'غير محدد'),
            'الحالة': 'نشط' if trans['status'] == 'active' else 'مؤرشف',
            'تاريخ_الإنشاء': trans['created_at']
        }
        
        # إضافة البيانات التفصيلية
        if trans.get('data'):
            for key, value in trans['data'].items():
                row[key] = value
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # إنشاء ملف Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='المعاملات')
        
        # تنسيق الورقة
        workbook = writer.book
        worksheet = writer.sheets['المعاملات']
        
        # تعديل عرض الأعمدة
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    output.seek(0)
    
    filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(output, 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=filename)

@app.route('/api/transactions')
def api_transactions():
    """API للحصول على المعاملات بصيغة JSON"""
    transactions = db.get_active_transactions()
    return jsonify(transactions)

@app.route('/api/users')
def api_users():
    """API للحصول على المستخدمين بصيغة JSON"""
    users = db.get_all_users()
    return jsonify(users)

@app.route('/api/stats')
def api_stats():
    """API للإحصائيات"""
    transactions = db.get_active_transactions()
    users = db.get_all_users()
    
    stats = {
        'total_transactions': len(transactions),
        'total_users': len(users),
        'pending_notifications': len(db.get_due_notifications()),
        'transaction_types': {}
    }
    
    # إحصائيات حسب النوع
    for trans in transactions:
        type_name = trans['type_name']
        stats['transaction_types'][type_name] = stats['transaction_types'].get(type_name, 0) + 1
    
    return jsonify(stats)

def run_web_app():
    """تشغيل الموقع"""
    from config import WEB_PORT, WEB_HOST
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)

if __name__ == '__main__':
    run_web_app()
