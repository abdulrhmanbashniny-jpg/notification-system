from flask import Flask, render_template_string, send_file, request, redirect
from database import Database
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
db = Database()

# ==================== HTML Templates ====================

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام إدارة المعاملات والتنبيهات</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎯</text></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .header { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 30px 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .header h1 { 
            font-size: 42px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 12px;
            font-weight: 800;
        }
        
        .header p { 
            font-size: 18px;
            color: #666;
            margin-bottom: 25px;
        }
        
        .header-buttons { margin-top: 20px; }
        
        .header-buttons a { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 35px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 700;
            display: inline-block;
            margin: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .header-buttons a:hover { 
            transform: translateY(-3px);
            box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
        }
        
        .container { 
            max-width: 1400px;
            margin: 30px auto;
            padding: 20px;
        }
        
        .stats { 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 35px;
        }
        
        .stat-card { 
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 5px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .stat-card:hover { 
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        
        .stat-card h2 { 
            font-size: 64px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
            font-weight: 900;
        }
        
        .stat-card p { 
            color: #666;
            font-size: 20px;
            font-weight: 600;
        }
        
        .card { 
            background: white;
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .card h2 { 
            color: #333;
            margin-bottom: 25px;
            font-size: 28px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 28px;
            border: none;
            border-radius: 50px;
            text-decoration: none;
            display: inline-block;
            margin: 8px 5px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        
        .btn-success { 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }
        
        .btn-success:hover { 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.5);
        }
        
        table { 
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td { 
            padding: 18px;
            text-align: right;
            border-bottom: 1px solid #e8e8e8;
        }
        
        th { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 700;
            font-size: 15px;
        }
        
        tbody tr { 
            transition: all 0.2s ease;
        }
        
        tbody tr:hover { 
            background: linear-gradient(to right, #f8f9ff, #fff);
            transform: scale(1.01);
        }
        
        .empty { 
            text-align: center;
            padding: 80px 20px;
            color: #999;
            font-size: 20px;
        }
        
        .badge { 
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
            display: inline-block;
        }
        
        .badge-admin { 
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #333;
        }
        
        .badge-user { 
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            color: #1976d2;
        }
        
        .badge-active {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .footer { 
            text-align: center;
            padding: 40px;
            color: white;
            margin-top: 50px;
            opacity: 0.9;
        }
        
        .footer p { 
            margin: 8px 0;
            font-size: 15px;
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 32px; }
            .stat-card h2 { font-size: 48px; }
            .card h2 { font-size: 22px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 نظام إدارة المعاملات والتنبيهات</h1>
        <p>منصة متكاملة لإدارة جميع المعاملات بكفاءة وذكاء</p>
        <div class="header-buttons">
            <a href="/add-sample-data">📊 إضافة بيانات تجريبية</a>
            <a href="/setup-admin">👑 إعداد حساب المسؤول</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h2>{{ total_transactions }}</h2>
                <p>📋 معاملة نشطة</p>
            </div>
            <div class="stat-card">
                <h2>{{ total_users }}</h2>
                <p>👥 مستخدم مسجل</p>
            </div>
            <div class="stat-card">
                <h2>{{ total_types }}</h2>
                <p>📑 نوع معاملة</p>
            </div>
        </div>
        
        <div class="card">
            <h2>📥 تصدير البيانات إلى Excel</h2>
            <p style="color: #666; margin-bottom: 25px; font-size: 16px;">
                قم بتصدير المعاملات بصيغة Excel للحصول على تحليل مفصل:
            </p>
            <a href="/export/all" class="btn btn-success">📊 تصدير جميع البيانات</a>
            <a href="/export/contracts" class="btn">📝 عقود العمل</a>
            <a href="/export/vacations" class="btn">🏖️ الإجازات</a>
            <a href="/export/vehicles" class="btn">🚗 السيارات</a>
            <a href="/export/licenses" class="btn">📄 التراخيص</a>
            <a href="/export/courts" class="btn">⚖️ القضايا</a>
        </div>
        
        <div class="card">
            <h2>📋 المعاملات النشطة</h2>
            {% if transactions %}
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px; text-align: center;">#</th>
                        <th>عنوان المعاملة</th>
                        <th style="width: 180px;">تاريخ الانتهاء</th>
                        <th style="width: 120px; text-align: center;">الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in transactions[:20] %}
                    <tr>
                        <td style="text-align: center;"><strong>{{ loop.index }}</strong></td>
                        <td><strong>{{ t.title }}</strong></td>
                        <td>📅 {{ t.end_date }}</td>
                        <td style="text-align: center;">
                            <span class="badge badge-active">✅ نشطة</span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if transactions|length > 20 %}
            <p style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
                <em>يتم عرض أول 20 معاملة فقط • الإجمالي: {{ transactions|length }}</em>
            </p>
            {% endif %}
            {% else %}
            <div class="empty">
                📭 لا توجد معاملات نشطة حالياً
                <br><br>
                <small style="color: #ccc; font-size: 16px;">
                    اضغط على "إضافة بيانات تجريبية" لإنشاء معاملات تجريبية
                </small>
            </div>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>👥 المستخدمين المسجلين</h2>
            {% if users %}
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px; text-align: center;">#</th>
                        <th>الاسم الكامل</th>
                        <th style="width: 200px;">رقم الجوال</th>
                        <th style="width: 150px; text-align: center;">الصلاحية</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td style="text-align: center;"><strong>{{ loop.index }}</strong></td>
                        <td><strong>{{ u.full_name }}</strong></td>
                        <td>📱 {{ u.phone_number }}</td>
                        <td style="text-align: center;">
                            {% if u.is_admin %}
                            <span class="badge badge-admin">👑 مسؤول</span>
                            {% else %}
                            <span class="badge badge-user">👤 مستخدم</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty">
                👤 لا يوجد مستخدمين مسجلين
                <br><br>
                <small style="color: #ccc; font-size: 16px;">
                    ابدأ بإعداد حساب المسؤول الأول
                </small>
            </div>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p><strong>🤖 نظام إدارة المعاملات والتنبيهات</strong></p>
        <p style="font-size: 14px; opacity: 0.8;">{{ current_year }} © جميع الحقوق محفوظة</p>
        <p style="font-size: 13px; margin-top: 15px; opacity: 0.7;">
            Powered by Flask • Python • Telegram Bot API
        </p>
    </div>
</body>
</html>
'''

SUCCESS_PAGE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
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
        .box { 
            background: white;
            padding: 60px;
            border-radius: 25px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            animation: slideUp 0.5s ease;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 { 
            color: #28a745;
            margin-bottom: 25px;
            font-size: 48px;
        }
        p { 
            font-size: 20px;
            margin: 18px 0;
            color: #555;
            line-height: 1.6;
        }
        .info {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 20px;
            border-radius: 15px;
            margin: 25px 0;
        }
        .info p {
            margin: 10px 0;
            font-size: 18px;
        }
        a { 
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 50px;
            text-decoration: none;
            border-radius: 50px;
            margin-top: 35px;
            font-weight: bold;
            font-size: 18px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        a:hover { 
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }
    </style>
</head>
<body>
    <div class="box">
        {{ content|safe }}
    </div>
</body>
</html>
'''
# ==================== Routes ====================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    try:
        transactions = db.get_active_transactions()
        users = db.get_all_users()
        types = db.get_transaction_types()
        
        return render_template_string(
            DASHBOARD_HTML,
            total_transactions=len(transactions),
            total_users=len(users),
            total_types=len(types),
            transactions=transactions,
            users=users,
            current_year=datetime.now().year
        )
    except Exception as e:
        return f"<h1 style='text-align:center;color:red;padding:50px;'>❌ خطأ: {str(e)}</h1>", 500

@app.route('/export/<transaction_type>')
def export_data(transaction_type):
    """تصدير البيانات إلى Excel"""
    try:
        transactions = db.get_active_transactions()
        
        if transaction_type != 'all':
            type_map = {
                'contracts': 1,
                'vacations': 2,
                'vehicles': 3,
                'licenses': 4,
                'courts': 5
            }
            type_id = type_map.get(transaction_type)
            if type_id:
                transactions = [t for t in transactions if t.get('transaction_type_id') == type_id]
        
        if not transactions:
            return "<h1 style='text-align:center;padding:50px;'>📭 لا توجد بيانات للتصدير</h1>", 404
        
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
        return f"<h1 style='color:red;text-align:center;'>خطأ: {str(e)}</h1>", 500

@app.route('/setup-admin')
def setup_admin():
    """إعداد حساب المسؤول - عبدالرحمن سالم"""
    try:
        user_id = 218601139
        phone = "+966599222345"
        name = "عبدالرحمن سالم"
        
        existing = db.get_user(user_id)
        
        if existing:
            content = f'''
                <h1>⚠️ الحساب موجود مسبقاً</h1>
                <div class="info">
                    <p><strong>الاسم:</strong> {existing['full_name']}</p>
                    <p><strong>الجوال:</strong> {existing['phone_number']}</p>
                    <p><strong>الصلاحية:</strong> {'👑 مسؤول' if existing['is_admin'] else '👤 مستخدم'}</p>
                </div>
                <p style="color: #666;">الحساب مسجل بالفعل في النظام</p>
                <a href="/">العودة للرئيسية</a>
            '''
        else:
            success = db.add_user(user_id, phone, name, 1)
            
            if success:
                content = f'''
                    <h1>✅ تم إعداد الحساب بنجاح!</h1>
                    <p style="font-size: 24px; margin: 25px 0;">مرحباً <strong>{name}</strong> 👋</p>
                    <div class="info">
                        <p><strong>📱 رقم الجوال:</strong> {phone}</p>
                        <p><strong>🆔 معرف تليجرام:</strong> {user_id}</p>
                        <p><strong>👑 الصلاحية:</strong> مسؤول النظام</p>
                    </div>
                    <p style="color: #28a745; font-weight: bold; font-size: 18px;">
                        🎉 أنت الآن المسؤول الأول للنظام!
                    </p>
                    <p style="color: #666; margin-top: 20px;">
                        يمكنك الآن استخدام البوت على تليجرام بهذا الرقم
                    </p>
                    <a href="/">الذهاب للرئيسية</a>
                '''
            else:
                content = '''
                    <h1>❌ فشل إعداد الحساب</h1>
                    <p>حدث خطأ أثناء إنشاء الحساب</p>
                    <p style="color: #999;">يرجى المحاولة مرة أخرى</p>
                    <a href="/">رجوع</a>
                '''
        
        return render_template_string(SUCCESS_PAGE, title="إعداد حساب المسؤول", content=content)
        
    except Exception as e:
        content = f'''
            <h1>❌ خطأ</h1>
            <p>{str(e)}</p>
            <a href="/">رجوع</a>
        '''
        return render_template_string(SUCCESS_PAGE, title="خطأ", content=content), 500

@app.route('/add-sample-data')
def add_sample_data():
    """إضافة البيانات التجريبية"""
    try:
        users = [
            (218601139, "+966599222345", "عبدالرحمن سالم", 1),
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
        
        users_added = 0
        for uid, phone, name, admin in users:
            try:
                if db.add_user(uid, phone, name, admin):
                    users_added += 1
            except:
                pass
        
        transactions = [
            (1, 218601139, "عقد عمل - عبدالرحمن سالم", {"الموظف": "عبدالرحمن سالم", "المسمى": "مدير عام", "الراتب": "25000"}, 365),
            (1, 1002, "عقد عمل - فاطمة سعيد", {"الموظف": "فاطمة سعيد الأحمدي", "المسمى": "محاسبة", "الراتب": "12000"}, 180),
            (1, 1003, "عقد عمل - خالد عبدالله", {"الموظف": "خالد عبدالله القحطاني", "المسمى": "مهندس برمجيات", "الراتب": "18000"}, 240),
            (1, 1004, "عقد عمل - نورة حسن", {"الموظف": "نورة حسن المطيري", "المسمى": "مديرة موارد بشرية", "الراتب": "16000"}, 200),
            (1, 1005, "عقد عمل - سعد فهد", {"الموظف": "سعد فهد الدوسري", "المسمى": "مدير مشاريع", "الراتب": "20000"}, 300),
            (2, 1002, "إجازة - فاطمة سعيد", {"الموظف": "فاطمة سعيد", "النوع": "سنوية", "البديل": "نورة حسن"}, 15),
            (2, 1003, "إجازة - خالد عبدالله", {"الموظف": "خالد عبدالله", "النوع": "مرضية", "البديل": "ماجد يوسف"}, 7),
            (2, 1006, "إجازة - مريم علي", {"الموظف": "مريم علي", "النوع": "طارئة", "البديل": "هند محمد"}, 3),
            (2, 1007, "إجازة - عبدالعزيز راشد", {"الموظف": "عبدالعزيز راشد", "النوع": "سنوية", "البديل": "سعد فهد"}, 25),
            (2, 1010, "إجازة - ريم إبراهيم", {"الموظف": "ريم إبراهيم", "النوع": "أمومة", "البديل": "فاطمة سعيد"}, 90),
            (3, 218601139, "سيارة - أ ب ج 1234", {"اللوحة": "أ ب ج 1234", "النوع": "كامري 2023", "VIN": "VIN12345"}, 60),
            (3, 1005, "سيارة - د هـ و 5678", {"اللوحة": "د هـ و 5678", "النوع": "يوكن 2022", "VIN": "VIN67890"}, 45),
            (3, 1006, "سيارة - ز ح ط 9012", {"اللوحة": "ز ح ط 9012", "النوع": "أكورد 2024", "VIN": "VIN11223"}, 90),
            (3, 1009, "سيارة - ي ك ل 3456", {"اللوحة": "ي ك ل 3456", "النوع": "هايلكس 2021", "VIN": "VIN44556"}, 30),
            (4, 218601139, "ترخيص - سجل تجاري رئيسي", {"النوع": "سجل تجاري", "الرقم": "1010123456", "الجهة": "وزارة التجارة"}, 180),
            (4, 1004, "ترخيص - فرع جدة", {"النوع": "ترخيص فرع", "الرقم": "2020234567", "الجهة": "البلدية"}, 120),
            (4, 1008, "ترخيص - شهادة صحية", {"النوع": "شهادة صحية", "الرقم": "3030345678", "الجهة": "وزارة الصحة"}, 90),
            (5, 218601139, "قضية تجارية - 2025/001", {"رقم_القضية": "2025/001", "البيان": "نزاع تجاري مع مورد", "المحكمة": "المحكمة التجارية"}, 40),
            (5, 1005, "قضية عمالية - 2025/002", {"رقم_القضية": "2025/002", "البيان": "مطالبة مالية موظف سابق", "المحكمة": "محكمة العمل"}, 25),
            (5, 1007, "قضية مدنية - 2025/003", {"رقم_القضية": "2025/003", "البيان": "نزاع عقاري", "المحكمة": "المحكمة العامة"}, 50),
        ]
        
        trans_added = 0
        for type_id, user_id, title, data, days in transactions:
            try:
                end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                trans_id = db.add_transaction(type_id, user_id, title, data, end_date)
                
                if days <= 30:
                    db.add_notification(trans_id, 3, [user_id, 218601139])
                elif days <= 90:
                    db.add_notification(trans_id, 7, [user_id, 218601139])
                    db.add_notification(trans_id, 3, [user_id, 218601139])
                else:
                    db.add_notification(trans_id, 30, [user_id, 218601139])
                    db.add_notification(trans_id, 7, [user_id, 218601139])
                
                trans_added += 1
            except:
                pass
        
        content = f'''
            <h1>🎉 تم بنجاح!</h1>
            <p style="font-size: 22px; margin: 25px 0;">تم إضافة البيانات التجريبية بنجاح</p>
            <div class="info">
                <p><strong>👥 المستخدمين:</strong> {users_added} مستخدم</p>
                <p><strong>📋 المعاملات:</strong> {trans_added} معاملة</p>
                <p><strong>⏰ التنبيهات:</strong> تم إعدادها تلقائياً</p>
            </div>
            <p style="color: #28a745; font-weight: bold; margin-top: 20px;">
                ✅ النظام جاهز للاستخدام!
            </p>
            <p style="color: #666; font-size: 15px; margin-top: 15px;">
                📱 يمكنك الآن استخدام البوت على تليجرام برقم: +966599222345
            </p>
            <a href="/">عرض البيانات</a>
        '''
        
        return render_template_string(SUCCESS_PAGE, title="إضافة بيانات تجريبية", content=content)
        
    except Exception as e:
        content = f'''
            <h1>❌ خطأ</h1>
            <p>{str(e)}</p>
            <a href="/">رجوع</a>
        '''
        return render_template_string(SUCCESS_PAGE, title="خطأ", content=content), 500

def run_web_app():
    """تشغيل الموقع"""
    port = int(os.environ.get('PORT', 5000))
    print(f"   🌐 الموقع يعمل على: http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_web_app()
