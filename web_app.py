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

@app.route('/admin/add-sample-data')
def add_sample_data_route():
    """صفحة إضافة البيانات التجريبية"""
    from datetime import datetime, timedelta
    
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
            ("عقد عمل - أحمد محمد", {"اسم_الموظف": "أحمد محمد العلي", "رقم_العقد": "C-2025-001", "المسمى_الوظيفي": "مدير مبيعات", "الراتب": "15000"}, 1001, 90),
            ("عقد عمل - فاطمة سعيد", {"اسم_الموظف": "فاطمة سعيد الأحمدي", "رقم_العقد": "C-2025-002", "المسمى_الوظيفي": "محاسبة", "الراتب": "12000"}, 1002, 120),
            ("عقد عمل - خالد عبدالله", {"اسم_الموظف": "خالد عبدالله القحطاني", "رقم_العقد": "C-2025-003", "المسمى_الوظيفي": "مهندس برمجيات", "الراتب": "18000"}, 1003, 180),
            ("عقد عمل - نورة حسن", {"اسم_الموظف": "نورة حسن المطيري", "رقم_العقد": "C-2025-004", "المسمى_الوظيفي": "مديرة موارد بشرية", "الراتب": "16000"}, 1004, 150),
            ("عقد عمل - سعد فهد", {"اسم_الموظف": "سعد فهد الدوسري", "رقم_العقد": "C-2025-005", "المسمى_الوظيفي": "مدير مشاريع", "الراتب": "20000"}, 1005, 200),
            ("عقد عمل - مريم علي", {"اسم_الموظف": "مريم علي الزهراني", "رقم_العقد": "C-2025-006", "المسمى_الوظيفي": "مصممة جرافيك", "الراتب": "10000"}, 1006, 60),
            ("عقد عمل - عبدالعزيز راشد", {"اسم_الموظف": "عبدالعزيز راشد العتيبي", "رقم_العقد": "C-2025-007", "المسمى_الوظيفي": "مسؤول تسويق", "الراتب": "14000"}, 1007, 100),
            ("عقد عمل - هند محمد", {"اسم_الموظف": "هند محمد الشمري", "رقم_العقد": "C-2025-008", "المسمى_الوظيفي": "سكرتيرة تنفيذية", "الراتب": "9000"}, 1008, 75),
            ("عقد عمل - ماجد يوسف", {"اسم_الموظف": "ماجد يوسف الغامدي", "رقم_العقد": "C-2025-009", "المسمى_الوظيفي": "فني صيانة", "الراتب": "8000"}, 1009, 45),
            ("عقد عمل - ريم إبراهيم", {"اسم_الموظف": "ريم إبراهيم السبيعي", "رقم_العقد": "C-2025-010", "المسمى_الوظيفي": "مديرة خدمة عملاء", "الراتب": "13000"}, 1010, 110),
        ]
        
        for title, data, user_id, days_until in contracts:
            end_date = (datetime.now() + timedelta(days=days_until)).strftime('%Y-%m-%d')
            trans_id = db.add_transaction(1, user_id, title, data, end_date)
            db.add_notification(trans_id, 30, [user_id, 1001])
            db.add_notification(trans_id, 7, [user_id, 1001])
        
        # إضافة إجازات
        vacations = [
            ("إجازة - أحمد محمد", {"اسم_الموظف": "أحمد محمد العلي", "الوظيفة": "مدير مبيعات", "الموظف_البديل": "خالد عبدالله"}, 1001, 15),
            ("إجازة - فاطمة سعيد", {"اسم_الموظف": "فاطمة سعيد الأحمدي", "الوظيفة": "محاسبة", "الموظف_البديل": "نورة حسن"}, 1002, 7),
            ("إجازة - خالد عبدالله", {"اسم_الموظف": "خالد عبدالله القحطاني", "الوظيفة": "مهندس برمجيات", "الموظف_البديل": "ماجد يوسف"}, 1003, 20),
            ("إجازة - نورة حسن", {"اسم_الموظف": "نورة حسن المطيري", "الوظيفة": "مديرة موارد بشرية", "الموظف_البديل": "هند محمد"}, 1004, 10),
            ("إجازة - سعد فهد", {"اسم_الموظف": "سعد فهد الدوسري", "الوظيفة": "مدير مشاريع", "الموظف_البديل": "عبدالعزيز راشد"}, 1005, 30),
            ("إجازة - مريم علي", {"اسم_الموظف": "مريم علي الزهراني", "الوظيفة": "مصممة جرافيك", "الموظف_البديل": "ريم إبراهيم"}, 1006, 5),
            ("إجازة - عبدالعزيز راشد", {"اسم_الموظف": "عبدالعزيز راشد العتيبي", "الوظيفة": "مسؤول تسويق", "الموظف_البديل": "سعد فهد"}, 1007, 12),
            ("إجازة - هند محمد", {"اسم_الموظف": "هند محمد الشمري", "الوظيفة": "سكرتيرة تنفيذية", "الموظف_البديل": "فاطمة سعيد"}, 1008, 8),
            ("إجازة - ماجد يوسف", {"اسم_الموظف": "ماجد يوسف الغامدي", "الوظيفة": "فني صيانة", "الموظف_البديل": "أحمد محمد"}, 1009, 14),
            ("إجازة - ريم إبراهيم", {"اسم_الموظف": "ريم إبراهيم السبيعي", "الوظيفة": "مديرة خدمة عملاء", "الموظف_البديل": "مريم علي"}, 1010, 6),
        ]
        
        for title, data, user_id, days_until in vacations:
            end_date = (datetime.now() + timedelta(days=days_until)).strftime('%Y-%m-%d')
            trans_id = db.add_transaction(2, user_id, title, data, end_date)
            db.add_notification(trans_id, 3, [user_id, 1001])
        
        # إضافة سيارات
        vehicles = [
            ("سيارة - أ ب ج 1234", {"رقم_اللوحة": "أ ب ج 1234", "الرقم_التسلسلي": "VIN001"}, 1001, 45, 50, 60),
            ("سيارة - د هـ و 5678", {"رقم_اللوحة": "د هـ و 5678", "الرقم_التسلسلي": "VIN002"}, 1002, 90, 95, 100),
            ("سيارة - ز ح ط 9012", {"رقم_اللوحة": "ز ح ط 9012", "الرقم_التسلسلي": "VIN003"}, 1003, 120, 125, 130),
            ("سيارة - ي ك ل 3456", {"رقم_اللوحة": "ي ك ل 3456", "الرقم_التسلسلي": "VIN004"}, 1004, 30, 35, 40),
            ("سيارة - م ن س 7890", {"رقم_اللوحة": "م ن س 7890", "الرقم_التسلسلي": "VIN005"}, 1005, 150, 155, 160),
            ("سيارة - ع ف ص 2345", {"رقم_اللوحة": "ع ف ص 2345", "الرقم_التسلسلي": "VIN006"}, 1006, 75, 80, 85),
            ("سيارة - ق ر ش 6789", {"رقم_اللوحة": "ق ر ش 6789", "الرقم_التسلسلي": "VIN007"}, 1007, 60, 65, 70),
            ("سيارة - ت ث خ 1111", {"رقم_اللوحة": "ت ث خ 1111", "الرقم_التسلسلي": "VIN008"}, 1008, 100, 105, 110),
            ("سيارة - ذ ض ظ 2222", {"رقم_اللوحة": "ذ ض ظ 2222", "الرقم_التسلسلي": "VIN009"}, 1009, 40, 45, 50),
            ("سيارة - غ ء آ 3333", {"رقم_اللوحة": "غ ء آ 3333", "الرقم_التسلسلي": "VIN010"}, 1010, 80, 85, 90),
        ]
        
        for title, data, user_id, insurance_days, reg_days, license_days in vehicles:
            insurance_date = (datetime.now() + timedelta(days=insurance_days)).strftime('%Y-%m-%d')
            registration_date = (datetime.now() + timedelta(days=reg_days)).strftime('%Y-%m-%d')
            license_date = (datetime.now() + timedelta(days=license_days)).strftime('%Y-%m-%d')
            trans_id = db.add_transaction(3, user_id, title, data, insurance_date)
            db.add_vehicle_dates(trans_id, insurance_date, license_date, registration_date)
            db.add_notification(trans_id, 7, [user_id, 1001])
        
        # إضافة تراخيص
        licenses = [
            ("ترخيص تجاري - شركة الرياض", {"نوع_الترخيص": "سجل تجاري", "المنصة": "وزارة التجارة"}, 1001, 180),
            ("ترخيص صحي - عيادة النور", {"نوع_الترخيص": "ترخيص صحي", "المنصة": "وزارة الصحة"}, 1002, 200),
            ("ترخيص بناء - مشروع جدة", {"نوع_الترخيص": "رخصة بناء", "المنصة": "البلدية"}, 1003, 150),
            ("ترخيص تشغيل - مصنع الدمام", {"نوع_الترخيص": "ترخيص تشغيل", "المنصة": "الدفاع المدني"}, 1004, 120),
            ("ترخيص مطعم - مطعم الخليج", {"نوع_الترخيص": "ترخيص مطعم", "المنصة": "البلدية"}, 1005, 90),
            ("ترخيص نقل - شركة التوصيل", {"نوع_الترخيص": "رخصة نقل", "المنصة": "هيئة النقل"}, 1006, 250),
            ("ترخيص حرفة - ورشة الصيانة", {"نوع_الترخيص": "ترخيص حرفة", "المنصة": "وزارة التجارة"}, 1007, 100),
            ("ترخيص استيراد - شركة الواردات", {"نوع_الترخيص": "رخصة استيراد", "المنصة": "الجمارك"}, 1008, 300),
            ("ترخيص تعليمي - أكاديمية المعرفة", {"نوع_الترخيص": "ترخيص تعليمي", "المنصة": "وزارة التعليم"}, 1009, 220),
            ("ترخيص سياحي - فندق النخيل", {"نوع_الترخيص": "ترخيص سياحي", "المنصة": "هيئة السياحة"}, 1010, 160),
        ]
        
        for title, data, user_id, days_until in licenses:
            end_date = (datetime.now() + timedelta(days=days_until)).strftime('%Y-%m-%d')
            trans_id = db.add_transaction(4, user_id, title, data, end_date)
            db.add_notification(trans_id, 30, [user_id, 1001])
            db.add_notification(trans_id, 15, [user_id, 1001])
        
        # إضافة قضايا
        court_cases = [
            ("قضية تجارية - رقم 2025/001", {"رقم_القضية": "2025/001", "بيان_القضية": "نزاع تجاري بين شركتين"}, 1001, 25),
            ("قضية عمالية - رقم 2025/002", {"رقم_القضية": "2025/002", "بيان_القضية": "مطالبة مالية موظف"}, 1002, 18),
            ("قضية عقارية - رقم 2025/003", {"رقم_القضية": "2025/003", "بيان_القضية": "نزاع ملكية أرض"}, 1003, 35),
            ("قضية مدنية - رقم 2025/004", {"رقم_القضية": "2025/004", "بيان_القضية": "تعويض أضرار"}, 1004, 42),
            ("قضية أسرية - رقم 2025/005", {"رقم_القضية": "2025/005", "بيان_القضية": "نزاع حضانة"}, 1005, 28),
            ("قضية تجارية - رقم 2025/006", {"رقم_القضية": "2025/006", "بيان_القضية": "مطالبة بديون"}, 1006, 50),
            ("قضية إدارية - رقم 2025/007", {"رقم_القضية": "2025/007", "بيان_القضية": "طعن في قرار إداري"}, 1007, 15),
            ("قضية عمالية - رقم 2025/008", {"رقم_القضية": "2025/008", "بيان_القضية": "فصل تعسفي"}, 1008, 33),
            ("قضية مرورية - رقم 2025/009", {"رقم_القضية": "2025/009", "بيان_القضية": "حادث سير تعويضات"}, 1009, 21),
            ("قضية تجارية - رقم 2025/010", {"رقم_القضية": "2025/010", "بيان_القضية": "إخلال بعقد توريد"}, 1010, 40),
        ]
        
        for title, data, user_id, days_until in court_cases:
            session_date = (datetime.now() + timedelta(days=days_until)).strftime('%Y-%m-%d')
            trans_id = db.add_transaction(5, user_id, title, data, session_date)
            db.add_court_session(trans_id, session_date, "", "جلسة أولى")
            db.add_notification(trans_id, 7, [user_id, 1001])
            db.add_notification(trans_id, 3, [user_id, 1001])
        
        return '''
        <html dir="rtl">
        <head><meta charset="UTF-8"><title>تم بنجاح!</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h1>🎉 تم إضافة البيانات بنجاح!</h1>
            <p style="font-size: 20px; margin: 30px 0;">تم إضافة 60 معاملة و 10 مستخدمين</p>
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

@app.route('/admin/register-admin', methods=['GET', 'POST'])
def register_admin():
    """صفحة تسجيل المسؤول الأول"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        user_id = request.form.get('user_id', '999999')  # ID افتراضي
        
        try:
            user_id = int(user_id)
            success = db.add_user(user_id, phone, name, 1)  # 1 = مسؤول
            
            if success:
                return '''
                <html dir="rtl">
                <head><meta charset="UTF-8"><title>تم بنجاح!</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .success-box {
                        background: white;
                        padding: 40px;
                        border-radius: 15px;
                        text-align: center;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    }
                    h1 { color: #28a745; margin-bottom: 20px; }
                    .btn {
                        display: inline-block;
                        background: #667eea;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 5px;
                        margin-top: 20px;
                    }
                </style>
                </head>
                <body>
                    <div class="success-box">
                        <h1>✅ تم التسجيل بنجاح!</h1>
                        <p style="font-size: 18px;">مرحباً ''' + name + '''</p>
                        <p>رقم الجوال: ''' + phone + '''</p>
                        <p><strong>أنت الآن مسؤول النظام! 👑</strong></p>
                        <a href="/" class="btn">الذهاب للرئيسية</a>
                        <br><br>
                        <p style="color: #666; font-size: 14px;">الآن يمكنك استخدام البوت على تليجرام برقمك هذا</p>
                    </div>
                </body>
                </html>
                '''
            else:
                return '<h1>❌ فشل التسجيل - ربما الرقم مسجل مسبقاً</h1><a href="/admin/register-admin">حاول مرة أخرى</a>'
        except Exception as e:
            return f'<h1>❌ خطأ: {str(e)}</h1><a href="/admin/register-admin">حاول مرة أخرى</a>'
    
    # صفحة النموذج
    return '''
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>تسجيل المسؤول</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                max-width: 500px;
                width: 100%;
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
                text-align: center;
            }
            p {
                color: #666;
                margin-bottom: 30px;
                text-align: center;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: bold;
            }
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            .info {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                font-size: 14px;
                color: #1976d2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👑 تسجيل مسؤول النظام</h1>
            <p>سجل بياناتك لتصبح مسؤول النظام</p>
            
            <form method="POST">
                <div class="form-group">
                    <label>رقم الجوال 📱</label>
                    <input type="text" name="phone" placeholder="مثال: +966599222345" value="+966599222345" required>
                </div>
                
                <div class="form-group">
                    <label>الاسم الكامل 👤</label>
                    <input type="text" name="name" placeholder="أدخل اسمك الكامل" required>
                </div>
                
                <div class="form-group">
                    <label>معرف تليجرام (Telegram ID) 🆔</label>
                    <input type="number" name="user_id" placeholder="اتركه فارغاً إذا لم تعرفه" value="999999">
                    <small style="color: #666; font-size: 12px; display: block; margin-top: 5px;">
                        سيتم تحديثه تلقائياً عند استخدام البوت
                    </small>
                </div>
                
                <button type="submit">✅ تسجيل كمسؤول</button>
                
                <div class="info">
                    💡 <strong>ملاحظة:</strong> بعد التسجيل، استخدم نفس رقم الجوال هذا عند التسجيل في البوت على تليجرام
                </div>
            </form>
        </div>
    </body>
    </html>
    '''


if __name__ == '__main__':
    run_web_app()
