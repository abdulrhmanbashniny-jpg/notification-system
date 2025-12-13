from flask import Flask, render_template_string, jsonify, request, send_file
from database import Database
import pandas as pd
from io import BytesIO
from datetime import datetime
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
        <p>🤖 نظام إدارة المعاملات والتنبيهات | تم التطوير بواسطة Perplexity AI</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """الصفحة الرئيسية - Dashboard"""
    stats = {
        'total_transactions': len(db.get_active_transactions()),
        'total_users': len(db.get_all_users()),
        'pending_notifications': len(db.get_pending_notifications())
    }
    
    # جلب آخر المعاملات مع أسماء المستخدمين
    transactions = db.get_active_transactions()
    users = db.get_all_users()
    types = db.get_transaction_types()
    
    # إضافة أسماء المستخدمين وأنواع المعاملات
    for t in transactions:
        user = next((u for u in users if u['user_id'] == t['user_id']), None)
        t['user_name'] = user['full_name'] if user else 'غير معروف'
        
        trans_type = next((ty for ty in types if ty['id'] == t['transaction_type_id']), None)
        t['type_name'] = trans_type['name'] if trans_type else 'غير محدد'
    
    return render_template_string(DASHBOARD_TEMPLATE, stats=stats, transactions=transactions, users=users)

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

@app.route('/add-transaction', methods=['GET', 'POST'])
def add_transaction():
    """صفحة إضافة معاملة جديدة"""
    if request.method == 'POST':
        try:
            transaction_type_id = int(request.form.get('transaction_type_id'))
            user_id = int(request.form.get('user_id'))
            title = request.form.get('title')
            end_date = request.form.get('end_date')
            
            # جمع البيانات الإضافية حسب نوع المعاملة
            data = {}
            
            # عقد عمل
            if transaction_type_id == 1:
                data = {
                    "اسم_الموظف": request.form.get('employee_name'),
                    "رقم_العقد": request.form.get('contract_number'),
                    "المسمى_الوظيفي": request.form.get('job_title'),
                    "الراتب": request.form.get('salary')
                }
            
            # إجازة موظف
            elif transaction_type_id == 2:
                data = {
                    "اسم_الموظف": request.form.get('employee_name'),
                    "الوظيفة": request.form.get('position'),
                    "الموظف_البديل": request.form.get('substitute')
                }
            
            # استمارة سيارة
            elif transaction_type_id == 3:
                data = {
                    "رقم_اللوحة": request.form.get('plate_number'),
                    "الرقم_التسلسلي": request.form.get('vin')
                }
            
            # ترخيص
            elif transaction_type_id == 4:
                data = {
                    "نوع_الترخيص": request.form.get('license_type'),
                    "المنصة": request.form.get('platform')
                }
            
            # جلسة قضائية
            elif transaction_type_id == 5:
                data = {
                    "رقم_القضية": request.form.get('case_number'),
                    "بيان_القضية": request.form.get('case_description'),
                    "رابط_الجلسة": request.form.get('session_link', '')
                }
            
            # إضافة المعاملة
            trans_id = db.add_transaction(transaction_type_id, user_id, title, data, end_date)
            
            # إضافة تنبيهات افتراضية
            notification_days = request.form.getlist('notification_days[]')
            for days in notification_days:
                if days:
                    db.add_notification(trans_id, int(days), [user_id])
            
            # إضافة بيانات إضافية للسيارات
            if transaction_type_id == 3:
                license_date = request.form.get('license_date', end_date)
                registration_date = request.form.get('registration_date', end_date)
                db.add_vehicle_dates(trans_id, end_date, license_date, registration_date)
            
            # إضافة بيانات الجلسة القضائية
            elif transaction_type_id == 5:
                session_link = request.form.get('session_link', '')
                session_notes = request.form.get('session_notes', 'جلسة قضائية')
                db.add_court_session(trans_id, end_date, session_link, session_notes)
            
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
                    max-width: 500px;
                }
                h1 { color: #28a745; margin-bottom: 20px; }
                .btn {
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 5px;
                    font-weight: bold;
                }
                .btn:hover { background: #764ba2; }
            </style>
            </head>
            <body>
                <div class="success-box">
                    <h1>✅ تم إضافة المعاملة بنجاح!</h1>
                    <p style="font-size: 18px; margin: 20px 0;">''' + title + '''</p>
                    <p style="color: #666;">تاريخ الانتهاء: ''' + end_date + '''</p>
                    <div style="margin-top: 30px;">
                        <a href="/add-transaction" class="btn">➕ إضافة معاملة أخرى</a>
                        <a href="/" class="btn">🏠 الرئيسية</a>
                    </div>
                </div>
            </body>
            </html>
            '''
        except Exception as e:
            return f'''
            <html dir="rtl">
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1>❌ حدث خطأ</h1>
                <p>{str(e)}</p>
                <a href="/add-transaction" style="color: #667eea;">حاول مرة أخرى</a>
            </body>
            </html>
            '''
    
    # GET request - عرض النموذج
    users = db.get_all_users()
    transaction_types = db.get_transaction_types()
    
    ADD_TRANSACTION_TEMPLATE = '''
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>إضافة معاملة جديدة</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
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
            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                font-family: inherit;
            }
            input:focus, select:focus, textarea:focus {
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
                margin-top: 20px;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
            .back-btn {
                display: inline-block;
                padding: 10px 20px;
                background: #6c757d;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            #dynamic-fields {
                border-top: 2px solid #eee;
                margin-top: 20px;
                padding-top: 20px;
            }
            .notification-group {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 15px;
            }
            .notification-item {
                margin: 10px 0;
            }
            .notification-item input[type="checkbox"] {
                width: auto;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← رجوع للرئيسية</a>
            
            <h1>➕ إضافة معاملة جديدة</h1>
            
            <form method="POST">
                <div class="form-group">
                    <label>نوع المعاملة *</label>
                    <select name="transaction_type_id" id="transaction_type" required onchange="updateFields()">
                        <option value="">-- اختر نوع المعاملة --</option>
                        {% for t in transaction_types %}
                        <option value="{{ t['id'] }}">{{ t['name'] }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>المستخدم المسؤول *</label>
                    <select name="user_id" required>
                        <option value="">-- اختر المستخدم --</option>
                        {% for u in users %}
                        <option value="{{ u['user_id'] }}">{{ u['full_name'] }} ({{ u['phone_number'] }})</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>عنوان المعاملة *</label>
                    <input type="text" name="title" placeholder="مثال: عقد عمل - أحمد محمد" required>
                </div>
                
                <div class="form-group">
                    <label>تاريخ الانتهاء *</label>
                    <input type="date" name="end_date" required>
                </div>
                
                <div id="dynamic-fields">
                    <!-- سيتم ملء الحقول الإضافية هنا بناءً على نوع المعاملة -->
                </div>
                
                <div class="notification-group">
                    <label>التنبيهات (اختر متى تريد التنبيه):</label>
                    <div class="notification-item">
                        <input type="checkbox" name="notification_days[]" value="30">
                        <label style="display: inline; font-weight: normal;">قبل 30 يوم</label>
                    </div>
                    <div class="notification-item">
                        <input type="checkbox" name="notification_days[]" value="15">
                        <label style="display: inline; font-weight: normal;">قبل 15 يوم</label>
                    </div>
                    <div class="notification-item">
                        <input type="checkbox" name="notification_days[]" value="7" checked>
                        <label style="display: inline; font-weight: normal;">قبل 7 أيام</label>
                    </div>
                    <div class="notification-item">
                        <input type="checkbox" name="notification_days[]" value="3">
                        <label style="display: inline; font-weight: normal;">قبل 3 أيام</label>
                    </div>
                    <div class="notification-item">
                        <input type="checkbox" name="notification_days[]" value="1">
                        <label style="display: inline; font-weight: normal;">قبل يوم واحد</label>
                    </div>
                </div>
                
                <button type="submit">✅ إضافة المعاملة</button>
            </form>
        </div>
        
        <script>
        function updateFields() {
            const type = document.getElementById('transaction_type').value;
            const container = document.getElementById('dynamic-fields');
            
            let html = '<h3 style="color: #667eea; margin-bottom: 15px;">بيانات إضافية:</h3>';
            
            if (type == '1') {  // عقد عمل
                html += `
                    <div class="form-group">
                        <label>اسم الموظف *</label>
                        <input type="text" name="employee_name" required>
                    </div>
                    <div class="form-group">
                        <label>رقم العقد *</label>
                        <input type="text" name="contract_number" required>
                    </div>
                    <div class="form-group">
                        <label>المسمى الوظيفي *</label>
                        <input type="text" name="job_title" required>
                    </div>
                    <div class="form-group">
                        <label>الراتب</label>
                        <input type="text" name="salary" placeholder="مثال: 10000">
                    </div>
                `;
            } else if (type == '2') {  // إجازة موظف
                html += `
                    <div class="form-group">
                        <label>اسم الموظف *</label>
                        <input type="text" name="employee_name" required>
                    </div>
                    <div class="form-group">
                        <label>الوظيفة</label>
                        <input type="text" name="position">
                    </div>
                    <div class="form-group">
                        <label>الموظف البديل</label>
                        <input type="text" name="substitute">
                    </div>
                `;
            } else if (type == '3') {  // استمارة سيارة
                html += `
                    <div class="form-group">
                        <label>رقم اللوحة *</label>
                        <input type="text" name="plate_number" placeholder="مثال: أ ب ج 1234" required>
                    </div>
                    <div class="form-group">
                        <label>الرقم التسلسلي (VIN)</label>
                        <input type="text" name="vin">
                    </div>
                    <div class="form-group">
                        <label>تاريخ انتهاء الرخصة</label>
                        <input type="date" name="license_date">
                    </div>
                    <div class="form-group">
                        <label>تاريخ تجديد الاستمارة</label>
                        <input type="date" name="registration_date">
                    </div>
                `;
            } else if (type == '4') {  // ترخيص
                html += `
                    <div class="form-group">
                        <label>نوع الترخيص *</label>
                        <input type="text" name="license_type" placeholder="مثال: سجل تجاري" required>
                    </div>
                    <div class="form-group">
                        <label>المنصة *</label>
                        <input type="text" name="platform" placeholder="مثال: وزارة التجارة" required>
                    </div>
                `;
            } else if (type == '5') {  // جلسة قضائية
                html += `
                    <div class="form-group">
                        <label>رقم القضية *</label>
                        <input type="text" name="case_number" placeholder="مثال: 2025/001" required>
                    </div>
                    <div class="form-group">
                        <label>بيان القضية *</label>
                        <textarea name="case_description" rows="3" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>رابط الجلسة (اختياري)</label>
                        <input type="url" name="session_link" placeholder="https://...">
                    </div>
                    <div class="form-group">
                        <label>ملاحظات الجلسة</label>
                        <textarea name="session_notes" rows="2"></textarea>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(ADD_TRANSACTION_TEMPLATE, users=users, transaction_types=transaction_types)

@app.route('/admin/register-admin', methods=['GET', 'POST'])
def register_admin():
    """صفحة تسجيل المسؤول الأول"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        user_id = request.form.get('user_id', '999999')
        
        try:
            user_id = int(user_id)
            success = db.add_user(user_id, phone, name, 1)
            
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
    
    REGISTER_ADMIN_TEMPLATE = '''
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
            small {
                color: #666;
                font-size: 12px;
                display: block;
                margin-top: 5px;
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
                    <small>سيتم تحديثه تلقائياً عند استخدام البوت</small>
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
    
    return render_template_string(REGISTER_ADMIN_TEMPLATE)

@app.route('/admin/add-sample-data')
def add_sample_data_route():
    """صفحة إضافة البيانات التجريبية"""
    from datetime import timedelta
    
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
        
        # إضافة إجازات (10 معاملات)
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
        
        # إضافة سيارات (10 معاملات)
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
        
        # إضافة تراخيص (10 معاملات)
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
        
        # إضافة قضايا (10 معاملات)
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

def run_web_app():
    """تشغيل الموقع"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_web_app()
