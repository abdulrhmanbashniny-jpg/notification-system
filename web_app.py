from flask import Flask, render_template_string, send_file, request, redirect
from database import Database
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
db = Database()

# ==================== الصفحة الرئيسية ====================

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام إدارة المعاملات</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }
        .header h1 { font-size: 36px; margin-bottom: 15px; }
        .header p { font-size: 18px; opacity: 0.9; }
        .header-buttons { margin-top: 25px; }
        .header-buttons a { 
            background: white; color: #667eea; padding: 15px 35px; 
            text-decoration: none; border-radius: 8px; font-weight: bold; 
            display: inline-block; margin: 8px; font-size: 16px;
            transition: all 0.3s;
        }
        .header-buttons a:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .container { max-width: 1400px; margin: 30px auto; padding: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-bottom: 35px; }
        .stat-card { 
            background: white; padding: 35px; border-radius: 12px; 
            text-align: center; box-shadow: 0 3px 15px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        .stat-card h2 { font-size: 56px; color: #667eea; margin-bottom: 12px; font-weight: bold; }
        .stat-card p { color: #666; font-size: 20px; font-weight: 500; }
        .card { 
            background: white; border-radius: 12px; padding: 35px; 
            margin-bottom: 25px; box-shadow: 0 3px 15px rgba(0,0,0,0.1); 
        }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 26px; }
        .btn { 
            background: #667eea; color: white; padding: 14px 28px; 
            border: none; border-radius: 6px; text-decoration: none; 
            display: inline-block; margin: 6px; font-weight: bold; 
            font-size: 15px; cursor: pointer; transition: all 0.3s;
        }
        .btn:hover { background: #764ba2; transform: translateY(-2px); }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 16px; text-align: right; border-bottom: 1px solid #e0e0e0; }
        th { background: #667eea; color: white; font-weight: 600; }
        tbody tr { transition: background 0.2s; }
        tbody tr:hover { background: #f8f9fa; }
        .empty { text-align: center; padding: 70px; color: #999; font-size: 20px; }
        .badge { padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: bold; }
        .badge-admin { background: #ffd700; color: #333; }
        .badge-user { background: #e3f2fd; color: #1976d2; }
        .footer { text-align: center; padding: 30px; color: #999; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 نظام إدارة المعاملات والتنبيهات</h1>
        <p>إدارة شاملة ومتقدمة لجميع المعاملات</p>
        <div class="header-buttons">
            <a href="/add-sample-data">📊 إضافة بيانات تجريبية</a>
            <a href="/register-admin">👑 تسجيل مسؤول</a>
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
            <p style="color: #666; margin-bottom: 20px; font-size: 16px;">اختر نوع المعاملات لتصديرها:</p>
            <a href="/export/all" class="btn btn-success">📊 تصدير جميع البيانات</a>
            <a href="/export/contracts" class="btn">📝 عقود العمل</a>
            <a href="/export/vacations" class="btn">🏖️ الإجازات</a>
            <a href="/export/vehicles" class="btn">🚗 السيارات</a>
            <a href="/export/licenses" class="btn">📄 التراخيص</a>
            <a href="/export/courts" class="btn">⚖️ القضايا</a>
        </div>
        
        <div class="card">
            <h2>📋 المعاملات النشطة (آخر 20 معاملة)</h2>
            {% if transactions %}
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>العنوان</th>
                        <th style="width: 150px;">تاريخ الانتهاء</th>
                        <th style="width: 100px;">الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in transactions[:20] %}
                    <tr>
                        <td><strong>{{ loop.index }}</strong></td>
                        <td>{{ t.title }}</td>
                        <td>{{ t.end_date }}</td>
                        <td><span class="badge" style="background: #28a745; color: white;">✅ نشطة</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty">📭 لا توجد معاملات نشطة حالياً<br><small style="color: #ccc;">اضغط على "إضافة بيانات تجريبية" لإضافة معاملات تجريبية</small></div>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>👥 المستخدمين المسجلين</h2>
            {% if users %}
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>الاسم الكامل</th>
                        <th style="width: 180px;">رقم الجوال</th>
                        <th style="width: 120px;">الصلاحية</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td><strong>{{ loop.index }}</strong></td>
                        <td>{{ u.full_name }}</td>
                        <td>{{ u.phone_number }}</td>
                        <td>
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
            <div class="empty">👤 لا يوجد مستخدمين مسجلين<br><small style="color: #ccc;">ابدأ بتسجيل مسؤول النظام</small></div>
            {% endif %}
        </div>
    </div>
    
    <div class="footer">
        <p>🤖 نظام إدارة المعاملات والتنبيهات | {{ current_year }}</p>
        <p style="font-size: 13px; margin-top: 10px; color: #ccc;">Powered by Flask & Python</p>
    </div>
</body>
</html>
'''

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
        return f"<h1 style='text-align:center;color:red;padding:50px;'>❌ خطأ في الصفحة</h1><p style='text-align:center;'>{str(e)}</p>", 500

# ==================== تصدير Excel ====================

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
        return f"<h1 style='color:red;'>خطأ</h1><p>{str(e)}</p>", 500

# ==================== إضافة بيانات تجريبية ====================

@app.route('/add-sample-data')
def add_sample_data():
    """إضافة بيانات تجريبية"""
    try:
        # إضافة 10 مستخدمين
        users = [
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
        
        for uid, phone, name, admin in users:
            try:
                db.add_user(uid, phone, name, admin)
            except:
                pass  # تجاهل إذا كان موجود
        
        # إضافة 10 معاملات متنوعة
        transactions = [
            (1, 1001, "عقد عمل - أحمد محمد العلي", {"الموظف": "أحمد محمد العلي", "المسمى": "مدير مبيعات"}, 90),
            (1, 1002, "عقد عمل - فاطمة سعيد", {"الموظف": "فاطمة سعيد الأحمدي", "المسمى": "محاسبة"}, 120),
            (2, 1003, "إجازة - خالد عبدالله", {"الموظف": "خالد عبدالله القحطاني", "البديل": "ماجد يوسف"}, 15),
            (2, 1004, "إجازة - نورة حسن", {"الموظف": "نورة حسن المطيري", "البديل": "هند محمد"}, 25),
            (3, 1005, "سيارة - م ن س 7890", {"اللوحة": "م ن س 7890", "VIN": "VIN12345"}, 45),
            (3, 1006, "سيارة - ع ف ص 2345", {"اللوحة": "ع ف ص 2345", "VIN": "VIN67890"}, 60),
            (4, 1007, "ترخيص تجاري - شركة النجاح", {"النوع": "سجل تجاري", "الجهة": "وزارة التجارة"}, 180),
            (4, 1008, "ترخيص صحي - عيادة الصحة", {"النوع": "ترخيص صحي", "الجهة": "وزارة الصحة"}, 200),
            (5, 1009, "قضية تجارية - رقم 2025/001", {"رقم_القضية": "2025/001", "البيان": "نزاع تجاري"}, 30),
            (5, 1010, "قضية عمالية - رقم 2025/002", {"رقم_القضية": "2025/002", "البيان": "مطالبة مالية"}, 40),
        ]
        
        added_count = 0
        for type_id, user_id, title, data, days in transactions:
            try:
                end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                trans_id = db.add_transaction(type_id, user_id, title, data, end_date)
                db.add_notification(trans_id, 7, [user_id])
                added_count += 1
            except:
                pass
        
        return f'''
        <html dir="rtl">
        <head><meta charset="UTF-8"><title>نجح!</title>
        <style>
            body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .box {{ background: white; padding: 60px; border-radius: 20px; text-align: center; box-shadow: 0 15px 50px rgba(0,0,0,0.4); max-width: 500px; }}
            h1 {{ color: #28a745; margin-bottom: 25px; font-size: 42px; }}
            p {{ font-size: 20px; margin: 15px 0; color: #555; }}
            a {{ display: inline-block; background: #667eea; color: white; padding: 18px 45px; text-decoration: none; border-radius: 8px; margin-top: 35px; font-weight: bold; font-size: 18px; transition: all 0.3s; }}
            a:hover {{ background: #764ba2; transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }}
        </style>
        </head>
        <body>
            <div class="box">
                <h1>✅ تم بنجاح!</h1>
                <p><strong>تم إضافة:</strong></p>
                <p>👥 {len(users)} مستخدمين</p>
                <p>📋 {added_count} معاملات</p>
                <a href="/">العودة للرئيسية</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f"<h1 style='color:red;text-align:center;'>خطأ</h1><p style='text-align:center;'>{str(e)}</p><a href='/' style='display:block;text-align:center;margin-top:20px;'>رجوع</a>", 500

# ==================== تسجيل مسؤول ====================

@app.route('/register-admin', methods=['GET', 'POST'])
def register_admin():
    """صفحة تسجيل المسؤول"""
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        name = request.form.get('name', '').strip()
        user_id = request.form.get('user_id', '999999').strip()
        
        if not phone or not name:
            return "<h1 style='color:red;text-align:center;'>❌ يرجى إدخال جميع البيانات</h1><a href='/register-admin' style='display:block;text-align:center;'>رجوع</a>", 400
        
        try:
            user_id = int(user_id)
            success = db.add_user(user_id, phone, name, 1)
            
            if success:
                return f'''
                <html dir="rtl">
                <head><meta charset="UTF-8"><title>نجح!</title>
                <style>
                    body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                    .box {{ background: white; padding: 50px; border-radius: 15px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }}
                    h1 {{ color: #28a745; margin-bottom: 20px; }}
                    a {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin-top: 30px; font-weight: bold; }}
                </style>
                </head>
                <body>
                    <div class="box">
                        <h1>✅ تم التسجيل بنجاح!</h1>
                        <p style="font-size: 20px; margin: 15px 0;">مرحباً <strong>{name}</strong></p>
                        <p>رقم الجوال: <strong>{phone}</strong></p>
                        <p style="color: #667eea; font-weight: bold; margin-top: 20px;">👑 أنت الآن مسؤول النظام!</p>
                        <a href="/">الذهاب للرئيسية</a>
                    </div>
                </body>
                </html>
                '''
            else:
                return "<h1 style='color:red;text-align:center;'>❌ فشل التسجيل - ربما الرقم مسجل مسبقاً</h1><a href='/register-admin' style='display:block;text-align:center;margin-top:20px;'>حاول مرة أخرى</a>", 400
        except Exception as e:
            return f"<h1 style='color:red;text-align:center;'>خطأ</h1><p style='text-align:center;'>{str(e)}</p><a href='/register-admin' style='display:block;text-align:center;'>رجوع</a>", 500
    
    # GET - عرض النموذج
    return '''
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>تسجيل مسؤول</title>
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
                padding: 45px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                max-width: 500px;
                width: 100%;
            }
            h1 { color: #667eea; margin-bottom: 15px; text-align: center; font-size: 32px; }
            p { color: #666; margin-bottom: 30px; text-align: center; font-size: 16px; }
            .form-group { margin-bottom: 22px; }
            label { display: block; margin-bottom: 10px; color: #333; font-weight: 600; font-size: 15px; }
            input {
                width: 100%;
                padding: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus { outline: none; border-color: #667eea; }
            button {
                width: 100%;
                padding: 16px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.2s;
            }
            button:hover { transform: translateY(-2px); }
            .info {
                background: #e3f2fd;
                padding: 18px;
                border-radius: 8px;
                margin-top: 25px;
                font-size: 14px;
                color: #1976d2;
                line-height: 1.6;
            }
            small { color: #999; font-size: 13px; display: block; margin-top: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👑 تسجيل مسؤول النظام</h1>
            <p>سجل بياناتك لتصبح مسؤول النظام</p>
            
            <form method="POST">
                <div class="form-group">
                    <label>رقم الجوال 📱</label>
                    <input type="text" name="phone" placeholder="+966599222345" value="+966599222345" required>
                </div>
                
                <div class="form-group">
                    <label>الاسم الكامل 👤</label>
                    <input type="text" name="name" placeholder="أدخل اسمك الكامل" required>
                </div>
                
                <div class="form-group">
                    <label>معرف تليجرام (اختياري) 🆔</label>
                    <input type="number" name="user_id" placeholder="999999" value="999999">
                    <small>سيتم تحديثه تلقائياً عند استخدام البوت</small>
                </div>
                
                <button type="submit">✅ تسجيل كمسؤول</button>
                
                <div class="info">
                    💡 <strong>ملاحظة:</strong> بعد التسجيل، يمكنك استخدام هذا الرقم للدخول إلى البوت على تليجرام (عندما يتم تفعيله)
                </div>
            </form>
        </div>
    </body>
    </html>
    '''

def run_web_app():
    """تشغيل التطبيق"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_web_app()
