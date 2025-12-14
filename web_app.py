from database_supabase import Database
from flask import Flask, render_template_string, send_file, request, redirect
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = 'change-this-secret-key-in-production'
db = Database()

# ==================== الصفحة الرئيسية ====================

MAIN_DASHBOARD = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام إدارة المعاملات</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Tajawal', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding-bottom: 50px; }
        .navbar { background: rgba(255, 255, 255, 0.98); backdrop-filter: blur(10px); box-shadow: 0 2px 20px rgba(0,0,0,0.1); padding: 15px 0; position: sticky; top: 0; z-index: 1000; }
        .navbar-content { max-width: 1400px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 28px; font-weight: 900; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav-links { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .nav-links a { color: #333; text-decoration: none; padding: 10px 20px; border-radius: 50px; font-weight: 600; transition: all 0.3s; }
        .nav-links a:hover, .nav-links a.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 1400px; margin: 30px auto; padding: 20px; }
        .alert-banner { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; padding: 20px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3); animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        .alert-banner h2 { font-size: 24px; margin-bottom: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: all 0.3s; position: relative; overflow: hidden; }
        .stat-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 5px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .stat-card:hover { transform: translateY(-8px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }
        .stat-icon { font-size: 40px; margin-bottom: 15px; }
        .stat-value { font-size: 48px; font-weight: 900; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }
        .stat-label { color: #666; font-size: 16px; font-weight: 600; }
        .quick-actions { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .quick-actions h2 { margin-bottom: 20px; font-size: 24px; color: #333; }
        .action-buttons { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .action-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; text-decoration: none; text-align: center; font-weight: 700; font-size: 16px; transition: all 0.3s; box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3); display: flex; align-items: center; justify-content: center; gap: 10px; }
        .action-btn:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.5); }
        .action-btn.success { background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%); }
        .action-btn.warning { background: linear-gradient(135deg, #ffd43b 0%, #fab005 100%); }
        .categories-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .category-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-decoration: none; transition: all 0.3s; position: relative; overflow: hidden; }
        .category-card:hover { transform: translateY(-10px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }
        .category-icon { font-size: 50px; margin-bottom: 15px; }
        .category-title { font-size: 22px; font-weight: 700; color: #333; margin-bottom: 10px; }
        .category-count { font-size: 36px; font-weight: 900; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .category-urgent { position: absolute; top: 15px; left: 15px; background: #ff6b6b; color: white; padding: 5px 12px; border-radius: 50px; font-size: 12px; font-weight: 700; }
        .urgent-section { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .urgent-section h2 { margin-bottom: 20px; font-size: 24px; color: #333; display: flex; align-items: center; gap: 10px; }
        .transaction-card { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 15px; margin-bottom: 15px; border-right: 5px solid #667eea; transition: all 0.3s; }
        .transaction-card:hover { transform: translateX(-5px); box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .transaction-card.critical { border-right-color: #ff6b6b; background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%); }
        .transaction-card.warning { border-right-color: #ffd43b; background: linear-gradient(135deg, #fffef5 0%, #ffeb99 100%); }
        .transaction-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .transaction-title { font-size: 18px; font-weight: 700; color: #333; }
        .transaction-badge { padding: 8px 16px; border-radius: 50px; font-size: 13px; font-weight: 700; }
        .badge-critical { background: #ff6b6b; color: white; animation: blink 1.5s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .badge-warning { background: #ffd43b; color: #333; }
        .badge-ok { background: #51cf66; color: white; }
        .transaction-info { color: #666; font-size: 14px; margin-top: 10px; }
        .transaction-actions { margin-top: 15px; display: flex; gap: 10px; }
        .btn-small { padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; transition: all 0.3s; }
        .btn-edit { background: #667eea; color: white; }
        .btn-delete { background: #ff6b6b; color: white; }
        .btn-small:hover { transform: scale(1.05); }
        .empty-state { text-align: center; padding: 60px 20px; color: #999; }
        .empty-state-icon { font-size: 80px; margin-bottom: 20px; }
        @media (max-width: 768px) { .logo { font-size: 22px; } .stat-value { font-size: 36px; } .nav-links { gap: 10px; } }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">🎯 نظام إدارة المعاملات</div>
            <div class="nav-links">
                <a href="/" class="active">الرئيسية</a>
                <a href="/users">👥 المستخدمين</a>
                <a href="/add-transaction">➕ معاملة جديدة</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% if critical_count > 0 %}
        <div class="alert-banner">
            <h2>⚠️ تنبيه عاجل!</h2>
            <p style="font-size: 18px;">لديك <strong>{{ critical_count }}</strong> معاملة تنتهي خلال 3 أيام أو أقل!</p>
        </div>
        {% endif %}
        
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-icon">🔥</div><div class="stat-value">{{ critical_count }}</div><div class="stat-label">عاجل (3 أيام)</div></div>
            <div class="stat-card"><div class="stat-icon">⚠️</div><div class="stat-value">{{ warning_count }}</div><div class="stat-label">قريب (7 أيام)</div></div>
            <div class="stat-card"><div class="stat-icon">📋</div><div class="stat-value">{{ total_active }}</div><div class="stat-label">معاملات نشطة</div></div>
            <div class="stat-card"><div class="stat-icon">👥</div><div class="stat-value">{{ total_users }}</div><div class="stat-label">مستخدم</div></div>
        </div>
        
        <div class="quick-actions">
            <h2>⚡ إجراءات سريعة</h2>
            <div class="action-buttons">
                <a href="/add-transaction" class="action-btn success">➕ إضافة معاملة جديدة</a>
                <a href="/import-excel" class="action-btn">📥 استيراد من Excel</a>
                <a href="/export/all" class="action-btn warning">📤 تصدير الكل</a>
                <a href="/users" class="action-btn">👥 إدارة المستخدمين</a>
            </div>
        </div>
        
        <div class="categories-grid">
            <a href="/category/contracts" class="category-card">
                {% if urgent_by_type.get(1, 0) > 0 %}<div class="category-urgent">{{ urgent_by_type.get(1, 0) }} عاجل</div>{% endif %}
                <div class="category-icon">📝</div><div class="category-title">عقود العمل</div><div class="category-count">{{ count_by_type.get(1, 0) }}</div>
            </a>
            <a href="/category/vacations" class="category-card">
                {% if urgent_by_type.get(2, 0) > 0 %}<div class="category-urgent">{{ urgent_by_type.get(2, 0) }} عاجل</div>{% endif %}
                <div class="category-icon">🏖️</div><div class="category-title">الإجازات</div><div class="category-count">{{ count_by_type.get(2, 0) }}</div>
            </a>
            <a href="/category/vehicles" class="category-card">
                {% if urgent_by_type.get(3, 0) > 0 %}<div class="category-urgent">{{ urgent_by_type.get(3, 0) }} عاجل</div>{% endif %}
                <div class="category-icon">🚗</div><div class="category-title">السيارات</div><div class="category-count">{{ count_by_type.get(3, 0) }}</div>
            </a>
            <a href="/category/licenses" class="category-card">
                {% if urgent_by_type.get(4, 0) > 0 %}<div class="category-urgent">{{ urgent_by_type.get(4, 0) }} عاجل</div>{% endif %}
                <div class="category-icon">📄</div><div class="category-title">التراخيص</div><div class="category-count">{{ count_by_type.get(4, 0) }}</div>
            </a>
            <a href="/category/courts" class="category-card">
                {% if urgent_by_type.get(5, 0) > 0 %}<div class="category-urgent">{{ urgent_by_type.get(5, 0) }} عاجل</div>{% endif %}
                <div class="category-icon">⚖️</div><div class="category-title">القضايا</div><div class="category-count">{{ count_by_type.get(5, 0) }}</div>
            </a>
        </div>
        
        <div class="urgent-section">
            <h2>🔥 المعاملات العاجلة (أقل من 7 أيام)</h2>
            {% if urgent_transactions %}
                {% for trans in urgent_transactions %}
                <div class="transaction-card {% if trans.days_left <= 3 %}critical{% elif trans.days_left <= 7 %}warning{% endif %}">
                    <div class="transaction-header">
                        <div class="transaction-title">{{ trans.title }}</div>
                        <div class="transaction-badge {% if trans.days_left <= 3 %}badge-critical{% elif trans.days_left <= 7 %}badge-warning{% else %}badge-ok{% endif %}">
                            {% if trans.days_left == 0 %}ينتهي اليوم!{% elif trans.days_left == 1 %}غداً{% else %}باقي {{ trans.days_left }} يوم{% endif %}
                        </div>
                    </div>
                    <div class="transaction-info">📅 تاريخ الانتهاء: <strong>{{ trans.end_date }}</strong></div>
                    <div class="transaction-actions">
                        <a href="/edit-transaction/{{ trans.transaction_id }}" class="btn-small btn-edit">✏️ تعديل</a>
                        <a href="/delete-transaction/{{ trans.transaction_id }}" class="btn-small btn-delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">🗑️ حذف</a>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <div class="empty-state-icon">✅</div>
                    <p style="font-size: 20px; font-weight: 600;">رائع! لا توجد معاملات عاجلة</p>
                    <p style="color: #999; margin-top: 10px;">جميع معاملاتك تحت السيطرة</p>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''
# ==================== صفحة إدارة المستخدمين ====================

USERS_PAGE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة المستخدمين</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Tajawal', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .navbar { background: white; padding: 20px; border-radius: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .navbar h1 { font-size: 28px; color: #333; }
        .back-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 25px; border-radius: 50px; text-decoration: none; font-weight: 600; }
        .add-user-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .add-user-card h2 { margin-bottom: 20px; color: #333; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr 1fr 100px 100px; gap: 15px; margin-bottom: 15px; }
        input, select { padding: 12px; border: 2px solid #e9ecef; border-radius: 10px; font-size: 15px; font-family: 'Tajawal', sans-serif; }
        input:focus, select:focus { outline: none; border-color: #667eea; }
        .btn-add { background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%); color: white; padding: 12px; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 15px; }
        .users-list { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .users-list h2 { margin-bottom: 20px; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 15px; text-align: right; border-bottom: 1px solid #e9ecef; }
        th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 700; }
        .badge { padding: 6px 14px; border-radius: 50px; font-size: 12px; font-weight: 700; }
        .badge-admin { background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); color: #333; }
        .badge-user { background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); color: #1976d2; }
        .btn-delete { background: #ff6b6b; color: white; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; }
        .btn-delete:hover { background: #ee5a6f; }
    </style>
</head>
<body>
    <div class="container">
        <div class="navbar">
            <h1>👥 إدارة المستخدمين</h1>
            <a href="/" class="back-btn">← العودة للرئيسية</a>
        </div>
        
        <div class="add-user-card">
            <h2>➕ إضافة مستخدم جديد</h2>
            <form method="POST" action="/add-user">
                <div class="form-row">
                    <input type="number" name="user_id" placeholder="معرف تليجرام (مثال: 218601139)" required>
                    <input type="text" name="phone_number" placeholder="رقم الجوال (مثال: +966599222345)" required>
                    <input type="text" name="full_name" placeholder="الاسم الكامل" required>
                    <select name="is_admin" required>
                        <option value="0">مستخدم</option>
                        <option value="1">مسؤول</option>
                    </select>
                    <button type="submit" class="btn-add">إضافة</button>
                </div>
            </form>
            <p style="color: #666; font-size: 13px; margin-top: 10px;">
                💡 معرف تليجرام: افتح البوت @userinfobot على تليجرام وأرسل أي رسالة لمعرفة الـ ID
            </p>
        </div>
        
        <div class="users-list">
            <h2>📋 قائمة المستخدمين ({{ users|length }})</h2>
            {% if users %}
            <table>
                <thead>
                    <tr>
                        <th>معرف تليجرام</th>
                        <th>الاسم الكامل</th>
                        <th>رقم الجوال</th>
                        <th>الصلاحية</th>
                        <th>الإجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td><code>{{ user.user_id }}</code></td>
                        <td><strong>{{ user.full_name }}</strong></td>
                        <td>{{ user.phone_number }}</td>
                        <td>
                            {% if user.is_admin %}
                            <span class="badge badge-admin">👑 مسؤول</span>
                            {% else %}
                            <span class="badge badge-user">👤 مستخدم</span>
                            {% endif %}
                        </td>
                        <td>
                            <a href="/delete-user/{{ user.user_id }}" class="btn-delete" onclick="return confirm('هل أنت متأكد من حذف {{ user.full_name }}؟')">🗑️ حذف</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align:center; padding: 40px; color: #999;">لا يوجد مستخدمين مسجلين</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# ==================== صفحة إضافة معاملة ====================

ADD_TRANSACTION_PAGE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إضافة معاملة جديدة</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Tajawal', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .form-header { text-align: center; margin-bottom: 40px; }
        .form-header h1 { font-size: 32px; color: #333; margin-bottom: 10px; }
        .form-header p { color: #666; font-size: 16px; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 10px; font-weight: 700; color: #333; font-size: 15px; }
        label span { color: #ff6b6b; }
        input, select, textarea { width: 100%; padding: 15px; border: 2px solid #e9ecef; border-radius: 10px; font-size: 16px; font-family: 'Tajawal', sans-serif; transition: all 0.3s; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        textarea { resize: vertical; min-height: 100px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .btn-submit { width: 100%; padding: 18px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 50px; font-size: 18px; font-weight: 700; cursor: pointer; transition: all 0.3s; margin-top: 20px; }
        .btn-submit:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4); }
        .back-link { display: block; text-align: center; margin-top: 20px; color: #667eea; text-decoration: none; font-weight: 600; }
        .back-link:hover { text-decoration: underline; }
        #dynamic-fields { margin-top: 30px; padding-top: 30px; border-top: 2px solid #e9ecef; }
        .field-description { font-size: 13px; color: #999; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-card">
            <div class="form-header">
                <h1>➕ إضافة معاملة جديدة</h1>
                <p>املأ البيانات التالية بعناية</p>
            </div>
            
            <form method="POST" action="/add-transaction">
                <div class="form-group">
                    <label>نوع المعاملة <span>*</span></label>
                    <select name="transaction_type_id" id="transaction_type" required onchange="updateDynamicFields()">
                        <option value="">-- اختر نوع المعاملة --</option>
                        <option value="1">📝 عقد عمل</option>
                        <option value="2">🏖️ إجازة موظف</option>
                        <option value="3">🚗 استمارة سيارة</option>
                        <option value="4">📄 ترخيص</option>
                        <option value="5">⚖️ جلسة قضائية</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>المستخدم المسؤول <span>*</span></label>
                    <select name="user_id" required>
                        <option value="">-- اختر المستخدم --</option>
                        {% for user in users %}
                        <option value="{{ user.user_id }}">{{ user.full_name }} ({{ user.phone_number }})</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>عنوان المعاملة <span>*</span></label>
                    <input type="text" name="title" placeholder="مثال: عقد عمل - أحمد محمد" required>
                    <div class="field-description">اكتب عنوان واضح ومختصر</div>
                </div>
                
                <div class="form-group">
                    <label>تاريخ الانتهاء <span>*</span></label>
                    <input type="date" name="end_date" required>
                </div>
                
                <div id="dynamic-fields"></div>
                
                <button type="submit" class="btn-submit">➕ إضافة المعاملة</button>
            </form>
            
            <a href="/" class="back-link">← العودة للرئيسية</a>
        </div>
    </div>
    
    <script>
    function updateDynamicFields() {
        const typeId = document.getElementById('transaction_type').value;
        const container = document.getElementById('dynamic-fields');
        
        let html = '<h3 style="margin-bottom: 20px; color: #333;">البيانات التفصيلية:</h3>';
        
        if (typeId == '1') {
            html += `
                <div class="form-row">
                    <div class="form-group"><label>اسم الموظف <span>*</span></label><input type="text" name="employee_name" required></div>
                    <div class="form-group"><label>رقم العقد <span>*</span></label><input type="text" name="contract_number" required></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>المسمى الوظيفي <span>*</span></label><input type="text" name="job_title" required></div>
                    <div class="form-group"><label>الراتب</label><input type="text" name="salary" placeholder="10000"></div>
                </div>
            `;
        } else if (typeId == '2') {
            html += `
                <div class="form-group"><label>اسم الموظف <span>*</span></label><input type="text" name="employee_name" required></div>
                <div class="form-row">
                    <div class="form-group"><label>نوع الإجازة</label><select name="vacation_type"><option value="سنوية">سنوية</option><option value="مرضية">مرضية</option><option value="طارئة">طارئة</option><option value="أمومة">أمومة</option></select></div>
                    <div class="form-group"><label>الموظف البديل</label><input type="text" name="substitute"></div>
                </div>
            `;
        } else if (typeId == '3') {
            html += `
                <div class="form-row">
                    <div class="form-group"><label>رقم اللوحة <span>*</span></label><input type="text" name="plate_number" placeholder="أ ب ج 1234" required></div>
                    <div class="form-group"><label>نوع السيارة</label><input type="text" name="vehicle_type" placeholder="كامري 2023"></div>
                </div>
                <div class="form-group"><label>الرقم التسلسلي (VIN)</label><input type="text" name="vin"></div>
            `;
        } else if (typeId == '4') {
            html += `
                <div class="form-row">
                    <div class="form-group"><label>نوع الترخيص <span>*</span></label><input type="text" name="license_type" placeholder="سجل تجاري" required></div>
                    <div class="form-group"><label>رقم الترخيص</label><input type="text" name="license_number"></div>
                </div>
                <div class="form-group"><label>الجهة المصدرة <span>*</span></label><input type="text" name="issuing_authority" placeholder="وزارة التجارة" required></div>
            `;
        } else if (typeId == '5') {
            html += `
                <div class="form-row">
                    <div class="form-group"><label>رقم القضية <span>*</span></label><input type="text" name="case_number" placeholder="2025/001" required></div>
                    <div class="form-group"><label>المحكمة</label><input type="text" name="court_name" placeholder="المحكمة التجارية"></div>
                </div>
                <div class="form-group"><label>بيان القضية <span>*</span></label><textarea name="case_description" required></textarea></div>
            `;
        }
        
        container.innerHTML = html;
    }
    
    window.addEventListener('DOMContentLoaded', function() { updateDynamicFields(); });
    </script>
</body>
</html>
'''
# ==================== الروابط والمسارات ====================

@app.route('/')
def dashboard():
    """الصفحة الرئيسية"""
    transactions = db.get_active_transactions()
    users = db.get_all_users()
    
    today = datetime.now().date()
    critical_count = 0
    warning_count = 0
    urgent_transactions = []
    count_by_type = {}
    urgent_by_type = {}
    
    for trans in transactions:
        try:
            end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
            days_left = (end_date - today).days
            trans['days_left'] = days_left
            
            type_id = trans['transaction_type_id']
            count_by_type[type_id] = count_by_type.get(type_id, 0) + 1
            
            if days_left <= 3:
                critical_count += 1
                urgent_by_type[type_id] = urgent_by_type.get(type_id, 0) + 1
                urgent_transactions.append(trans)
            elif days_left <= 7:
                warning_count += 1
                urgent_by_type[type_id] = urgent_by_type.get(type_id, 0) + 1
                urgent_transactions.append(trans)
        except:
            continue
    
    urgent_transactions.sort(key=lambda x: x['days_left'])
    
    return render_template_string(
        MAIN_DASHBOARD,
        critical_count=critical_count,
        warning_count=warning_count,
        total_active=len(transactions),
        total_users=len(users),
        urgent_transactions=urgent_transactions,
        count_by_type=count_by_type,
        urgent_by_type=urgent_by_type
    )

@app.route('/users')
def users_page():
    """صفحة إدارة المستخدمين"""
    users = db.get_all_users()
    return render_template_string(USERS_PAGE, users=users)

@app.route('/add-user', methods=['POST'])
def add_user():
    """إضافة مستخدم جديد"""
    try:
        user_id = int(request.form.get('user_id'))
        phone_number = request.form.get('phone_number')
        full_name = request.form.get('full_name')
        is_admin = int(request.form.get('is_admin', 0))
        
        db.add_user(user_id, phone_number, full_name, is_admin)
        return redirect('/users')
    except:
        return redirect('/users')

@app.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    """حذف مستخدم"""
    db.delete_user(user_id)
    return redirect('/users')

@app.route('/add-transaction', methods=['GET', 'POST'])
def add_transaction():
    """إضافة معاملة جديدة"""
    if request.method == 'GET':
        users = db.get_all_users()
        return render_template_string(ADD_TRANSACTION_PAGE, users=users)
    
    try:
        transaction_type_id = int(request.form.get('transaction_type_id'))
        user_id = int(request.form.get('user_id'))
        title = request.form.get('title')
        end_date = request.form.get('end_date')
        
        # جمع البيانات الإضافية
        data = {}
        for key in request.form.keys():
            if key not in ['transaction_type_id', 'user_id', 'title', 'end_date']:
                data[key] = request.form.get(key)
        
        db.add_transaction(transaction_type_id, user_id, title, data, end_date)
        return redirect('/')
    except Exception as e:
        print(f"خطأ في إضافة المعاملة: {e}")
        return redirect('/add-transaction')

@app.route('/delete-transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    """حذف معاملة"""
    db.delete_transaction(transaction_id)
    return redirect(request.referrer or '/')

@app.route('/category/<category_name>')
def category_page(category_name):
    """صفحة فئة معينة"""
    type_mapping = {
        'contracts': 1,
        'vacations': 2,
        'vehicles': 3,
        'licenses': 4,
        'courts': 5
    }
    
    type_id = type_mapping.get(category_name)
    if not type_id:
        return redirect('/')
    
    all_transactions = db.get_active_transactions()
    transactions = [t for t in all_transactions if t['transaction_type_id'] == type_id]
    
    today = datetime.now().date()
    for trans in transactions:
        try:
            end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
            trans['days_left'] = (end_date - today).days
        except:
            trans['days_left'] = 999
    
    transactions.sort(key=lambda x: x['days_left'])
    
    type_names = {
        1: 'عقود العمل 📝',
        2: 'الإجازات 🏖️',
        3: 'السيارات 🚗',
        4: 'التراخيص 📄',
        5: 'القضايا ⚖️'
    }
    
    category_title = type_names.get(type_id, 'المعاملات')
    
    html = f'''
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{category_title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Tajawal', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; padding: 30px; border-radius: 20px; margin-bottom: 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            .header h1 {{ font-size: 36px; color: #333; margin-bottom: 10px; }}
            .back-btn {{ display: inline-block; margin-top: 20px; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 50px; font-weight: 600; }}
            .transactions-grid {{ display: grid; gap: 20px; }}
            .transaction-card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); border-right: 5px solid #667eea; }}
            .transaction-card.critical {{ border-right-color: #ff6b6b; background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%); }}
            .transaction-card.warning {{ border-right-color: #ffd43b; background: linear-gradient(135deg, #fffef5 0%, #ffeb99 100%); }}
            .transaction-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .transaction-title {{ font-size: 20px; font-weight: 700; color: #333; }}
            .transaction-badge {{ padding: 8px 16px; border-radius: 50px; font-size: 13px; font-weight: 700; }}
            .badge-critical {{ background: #ff6b6b; color: white; }}
            .badge-warning {{ background: #ffd43b; color: #333; }}
            .badge-ok {{ background: #51cf66; color: white; }}
            .transaction-info {{ color: #666; font-size: 14px; margin-top: 10px; }}
            .transaction-actions {{ margin-top: 15px; display: flex; gap: 10px; }}
            .btn-small {{ padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; }}
            .btn-edit {{ background: #667eea; color: white; }}
            .btn-delete {{ background: #ff6b6b; color: white; }}
            .empty-state {{ background: white; padding: 60px; border-radius: 20px; text-align: center; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{category_title}</h1>
                <p style="font-size: 18px; color: #666; margin-top: 10px;">إجمالي المعاملات: <strong>{len(transactions)}</strong></p>
                <a href="/" class="back-btn">← العودة للرئيسية</a>
            </div>
            
            <div class="transactions-grid">
    '''
    
    if transactions:
        for trans in transactions:
            badge_class = 'badge-ok'
            card_class = ''
            
            if trans['days_left'] <= 3:
                badge_class = 'badge-critical'
                card_class = 'critical'
            elif trans['days_left'] <= 7:
                badge_class = 'badge-warning'
                card_class = 'warning'
            
            days_text = 'ينتهي اليوم!' if trans['days_left'] == 0 else f"باقي {trans['days_left']} يوم"
            
            html += f'''
            <div class="transaction-card {card_class}">
                <div class="transaction-header">
                    <div class="transaction-title">{trans['title']}</div>
                    <div class="transaction-badge {badge_class}">{days_text}</div>
                </div>
                <div class="transaction-info">📅 تاريخ الانتهاء: <strong>{trans['end_date']}</strong></div>
                <div class="transaction-actions">
                    <a href="/delete-transaction/{trans['transaction_id']}" class="btn-small btn-delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">🗑️ حذف</a>
                </div>
            </div>
            '''
    else:
        html += '''
        <div class="empty-state">
            <div style="font-size: 80px; margin-bottom: 20px;">📭</div>
            <p style="font-size: 20px; font-weight: 600;">لا توجد معاملات في هذه الفئة</p>
        </div>
        '''
    
    html += '''
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/export/all')
def export_all():
    """تصدير جميع المعاملات إلى Excel"""
    transactions = db.get_active_transactions()
    
    data = []
    for trans in transactions:
        data.append({
            'رقم المعاملة': trans['transaction_id'],
            'العنوان': trans['title'],
            'تاريخ الانتهاء': trans['end_date'],
            'تاريخ الإضافة': trans['created_at']
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='المعاملات')
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'transactions_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/health')
def health():
    """فحص صحة النظام"""
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}

def run_web_app():
    """تشغيل الموقع"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
@app.route('/edit-transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    """صفحة تعديل معاملة"""
    if request.method == 'GET':
        trans = db.get_transaction(transaction_id)
        if not trans:
            return redirect('/')
        
        return f"""
        <h1>تعديل المعاملة #{transaction_id}</h1>
        <p>هذه الميزة قيد التطوير</p>
        <a href="/">العودة</a>
        """
    
    # POST: تحديث المعاملة
    title = request.form.get('title')
    end_date = request.form.get('end_date')
    db.update_transaction(transaction_id, title, end_date)
    return redirect('/')

if __name__ == '__main__':
    run_web_app()
