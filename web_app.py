from flask import Flask, render_template_string, send_file, request, redirect, flash, jsonify
from database import Database
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
db = Database()

# ==================== الصفحة الرئيسية المطورة ====================

MAIN_DASHBOARD = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - نظام إدارة المعاملات</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎯</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding-bottom: 50px;
        }
        
        /* Navigation */
        .navbar {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 28px;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .nav-links a {
            color: #333;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 50px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .nav-links a:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .nav-links a.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        /* Container */
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 20px;
        }
        
        /* Alert Banner */
        .alert-banner {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
        
        .alert-banner h2 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .stat-icon {
            font-size: 40px;
            margin-bottom: 15px;
        }
        
        .stat-value {
            font-size: 48px;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 16px;
            font-weight: 600;
        }
        
        /* Quick Actions */
        .quick-actions {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .quick-actions h2 {
            margin-bottom: 20px;
            font-size: 24px;
            color: #333;
        }
        
        .action-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .action-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-decoration: none;
            text-align: center;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .action-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.5);
        }
        
        .action-btn.danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        }
        
        .action-btn.success {
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
        }
        
        .action-btn.warning {
            background: linear-gradient(135deg, #ffd43b 0%, #fab005 100%);
        }
        
        /* Urgent Transactions */
        .urgent-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .urgent-section h2 {
            margin-bottom: 20px;
            font-size: 24px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .transaction-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 15px;
            border-right: 5px solid #667eea;
            transition: all 0.3s;
            position: relative;
        }
        
        .transaction-card:hover {
            transform: translateX(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .transaction-card.critical {
            border-right-color: #ff6b6b;
            background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
        }
        
        .transaction-card.warning {
            border-right-color: #ffd43b;
            background: linear-gradient(135deg, #fffef5 0%, #ffeb99 100%);
        }
        
        .transaction-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .transaction-title {
            font-size: 18px;
            font-weight: 700;
            color: #333;
        }
        
        .transaction-badge {
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
        }
        
        .badge-critical {
            background: #ff6b6b;
            color: white;
            animation: blink 1.5s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .badge-warning {
            background: #ffd43b;
            color: #333;
        }
        
        .badge-ok {
            background: #51cf66;
            color: white;
        }
        
        .transaction-info {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .transaction-actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        
        .btn-small {
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-edit {
            background: #667eea;
            color: white;
        }
        
        .btn-delete {
            background: #ff6b6b;
            color: white;
        }
        
        .btn-small:hover {
            transform: scale(1.05);
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state-icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
        
        /* Categories Grid */
        .categories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .category-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-decoration: none;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .category-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        
        .category-icon {
            font-size: 50px;
            margin-bottom: 15px;
        }
        
        .category-title {
            font-size: 22px;
            font-weight: 700;
            color: #333;
            margin-bottom: 10px;
        }
        
        .category-count {
            font-size: 36px;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .category-urgent {
            position: absolute;
            top: 15px;
            left: 15px;
            background: #ff6b6b;
            color: white;
            padding: 5px 12px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 700;
        }
        
        @media (max-width: 768px) {
            .nav-links {
                flex-direction: column;
                gap: 10px;
            }
            
            .stat-value {
                font-size: 36px;
            }
            
            .logo {
                font-size: 22px;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">🎯 نظام إدارة المعاملات</div>
            <div class="nav-links">
                <a href="/" class="active">الرئيسية</a>
                <a href="/all-transactions">كل المعاملات</a>
                <a href="/add-transaction">➕ معاملة جديدة</a>
                <a href="/reports">📊 التقارير</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <!-- Alert Banner -->
        {% if critical_count > 0 %}
        <div class="alert-banner">
            <h2>⚠️ تنبيه عاجل!</h2>
            <p style="font-size: 18px;">لديك <strong>{{ critical_count }}</strong> معاملة تنتهي خلال 3 أيام أو أقل!</p>
        </div>
        {% endif %}
        
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🔥</div>
                <div class="stat-value">{{ critical_count }}</div>
                <div class="stat-label">عاجل (3 أيام)</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚠️</div>
                <div class="stat-value">{{ warning_count }}</div>
                <div class="stat-label">قريب (7 أيام)</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📋</div>
                <div class="stat-value">{{ total_active }}</div>
                <div class="stat-label">معاملات نشطة</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-value">{{ total_users }}</div>
                <div class="stat-label">مستخدم</div>
            </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="quick-actions">
            <h2>⚡ إجراءات سريعة</h2>
            <div class="action-buttons">
                <a href="/add-transaction" class="action-btn success">
                    ➕ إضافة معاملة جديدة
                </a>
                <a href="/import-excel" class="action-btn">
                    📥 استيراد من Excel
                </a>
                <a href="/export/all" class="action-btn warning">
                    📤 تصدير الكل
                </a>
                <a href="/setup-admin" class="action-btn">
                    👑 إعداد حساب مسؤول
                </a>
            </div>
        </div>
        
        <!-- Categories Grid -->
        <div class="categories-grid">
            <a href="/category/contracts" class="category-card">
                {% if urgent_by_type.get(1, 0) > 0 %}
                <div class="category-urgent">{{ urgent_by_type.get(1, 0) }} عاجل</div>
                {% endif %}
                <div class="category-icon">📝</div>
                <div class="category-title">عقود العمل</div>
                <div class="category-count">{{ count_by_type.get(1, 0) }}</div>
            </a>
            
            <a href="/category/vacations" class="category-card">
                {% if urgent_by_type.get(2, 0) > 0 %}
                <div class="category-urgent">{{ urgent_by_type.get(2, 0) }} عاجل</div>
                {% endif %}
                <div class="category-icon">🏖️</div>
                <div class="category-title">الإجازات</div>
                <div class="category-count">{{ count_by_type.get(2, 0) }}</div>
            </a>
            
            <a href="/category/vehicles" class="category-card">
                {% if urgent_by_type.get(3, 0) > 0 %}
                <div class="category-urgent">{{ urgent_by_type.get(3, 0) }} عاجل</div>
                {% endif %}
                <div class="category-icon">🚗</div>
                <div class="category-title">السيارات</div>
                <div class="category-count">{{ count_by_type.get(3, 0) }}</div>
            </a>
            
            <a href="/category/licenses" class="category-card">
                {% if urgent_by_type.get(4, 0) > 0 %}
                <div class="category-urgent">{{ urgent_by_type.get(4, 0) }} عاجل</div>
                {% endif %}
                <div class="category-icon">📄</div>
                <div class="category-title">التراخيص</div>
                <div class="category-count">{{ count_by_type.get(4, 0) }}</div>
            </a>
            
            <a href="/category/courts" class="category-card">
                {% if urgent_by_type.get(5, 0) > 0 %}
                <div class="category-urgent">{{ urgent_by_type.get(5, 0) }} عاجل</div>
                {% endif %}
                <div class="category-icon">⚖️</div>
                <div class="category-title">القضايا</div>
                <div class="category-count">{{ count_by_type.get(5, 0) }}</div>
            </a>
        </div>
        
        <!-- Urgent Transactions -->
        <div class="urgent-section">
            <h2>🔥 المعاملات العاجلة (أقل من 7 أيام)</h2>
            
            {% if urgent_transactions %}
                {% for trans in urgent_transactions %}
                <div class="transaction-card {% if trans.days_left <= 3 %}critical{% elif trans.days_left <= 7 %}warning{% endif %}">
                    <div class="transaction-header">
                        <div class="transaction-title">{{ trans.title }}</div>
                        <div class="transaction-badge {% if trans.days_left <= 3 %}badge-critical{% elif trans.days_left <= 7 %}badge-warning{% else %}badge-ok{% endif %}">
                            {% if trans.days_left == 0 %}
                                ينتهي اليوم!
                            {% elif trans.days_left == 1 %}
                                غداً
                            {% else %}
                                باقي {{ trans.days_left }} يوم
                            {% endif %}
                        </div>
                    </div>
                    <div class="transaction-info">
                        📅 تاريخ الانتهاء: <strong>{{ trans.end_date }}</strong>
                    </div>
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
# ==================== صفحة الأقسام ====================

CATEGORY_PAGE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ category_name }} - نظام إدارة المعاملات</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .navbar {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            padding: 15px 0;
        }
        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 24px;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .back-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 25px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
        }
        .back-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 20px;
        }
        .page-header {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-title {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .header-icon {
            font-size: 50px;
        }
        .header-text h1 {
            font-size: 32px;
            color: #333;
            margin-bottom: 5px;
        }
        .header-text p {
            color: #666;
            font-size: 16px;
        }
        .add-new-btn {
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(81, 207, 102, 0.3);
        }
        .add-new-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(81, 207, 102, 0.5);
        }
        .filters {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .filter-btn {
            padding: 10px 20px;
            border-radius: 50px;
            border: 2px solid #e9ecef;
            background: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .filter-btn:hover, .filter-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
        }
        .transactions-grid {
            display: grid;
            gap: 20px;
        }
        .transaction-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            border-right: 5px solid #667eea;
            transition: all 0.3s;
        }
        .transaction-card:hover {
            transform: translateX(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }
        .transaction-card.critical {
            border-right-color: #ff6b6b;
            background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
        }
        .transaction-card.warning {
            border-right-color: #ffd43b;
            background: linear-gradient(135deg, #fffef5 0%, #ffeb99 100%);
        }
        .transaction-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .transaction-title {
            font-size: 20px;
            font-weight: 700;
            color: #333;
        }
        .status-badge {
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 700;
        }
        .badge-critical {
            background: #ff6b6b;
            color: white;
            animation: blink 1.5s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .badge-warning {
            background: #ffd43b;
            color: #333;
        }
        .badge-ok {
            background: #51cf66;
            color: white;
        }
        .transaction-details {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }
        .detail-item {
            display: flex;
            margin-bottom: 10px;
            color: #666;
        }
        .detail-label {
            font-weight: 600;
            margin-left: 10px;
            min-width: 100px;
        }
        .transaction-actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 14px;
        }
        .btn-edit {
            background: #667eea;
            color: white;
        }
        .btn-delete {
            background: #ff6b6b;
            color: white;
        }
        .btn:hover {
            transform: scale(1.05);
        }
        .empty-state {
            background: white;
            padding: 80px 20px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .empty-icon {
            font-size: 100px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">{{ category_icon }} {{ category_name }}</div>
            <a href="/" class="back-btn">← العودة للرئيسية</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="page-header">
            <div class="header-title">
                <div class="header-icon">{{ category_icon }}</div>
                <div class="header-text">
                    <h1>{{ category_name }}</h1>
                    <p>إجمالي المعاملات: {{ transactions|length }}</p>
                </div>
            </div>
            <a href="/add-transaction?type={{ type_id }}" class="add-new-btn">➕ إضافة جديد</a>
        </div>
        
        {% if transactions %}
        <div class="transactions-grid">
            {% for trans in transactions %}
            <div class="transaction-card {% if trans.days_left <= 3 %}critical{% elif trans.days_left <= 7 %}warning{% endif %}">
                <div class="transaction-header">
                    <div class="transaction-title">{{ trans.title }}</div>
                    <div class="status-badge {% if trans.days_left <= 3 %}badge-critical{% elif trans.days_left <= 7 %}badge-warning{% else %}badge-ok{% endif %}">
                        {% if trans.days_left == 0 %}
                            ينتهي اليوم!
                        {% elif trans.days_left == 1 %}
                            غداً
                        {% elif trans.days_left < 0 %}
                            منتهي
                        {% else %}
                            باقي {{ trans.days_left }} يوم
                        {% endif %}
                    </div>
                </div>
                
                <div class="transaction-details">
                    <div class="detail-item">
                        <span class="detail-label">📅 تاريخ الانتهاء:</span>
                        <span>{{ trans.end_date }}</span>
                    </div>
                    {% if trans.data %}
                        {% for key, value in trans.data.items() %}
                        <div class="detail-item">
                            <span class="detail-label">{{ key }}:</span>
                            <span>{{ value }}</span>
                        </div>
                        {% endfor %}
                    {% endif %}
                </div>
                
                <div class="transaction-actions">
                    <a href="/edit-transaction/{{ trans.transaction_id }}" class="btn btn-edit">✏️ تعديل</a>
                    <a href="/delete-transaction/{{ trans.transaction_id }}" class="btn btn-delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">🗑️ حذف</a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <div class="empty-icon">{{ category_icon }}</div>
            <h2 style="color: #333; margin-bottom: 15px;">لا توجد معاملات في هذا القسم</h2>
            <p style="color: #666; margin-bottom: 30px;">ابدأ بإضافة معاملة جديدة</p>
            <a href="/add-transaction?type={{ type_id }}" class="add-new-btn">➕ إضافة أول معاملة</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

# ==================== صفحة إضافة/تعديل معاملة ====================

ADD_EDIT_TRANSACTION = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }} - نظام إدارة المعاملات</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .form-card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .form-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .form-header h1 {
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }
        .form-header p {
            color: #666;
            font-size: 16px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 700;
            color: #333;
            font-size: 15px;
        }
        label span {
            color: #ff6b6b;
        }
        input, select, textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 16px;
            font-family: 'Tajawal', sans-serif;
            transition: all 0.3s;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .btn-submit {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
        }
        .btn-submit:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        #dynamic-fields {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #e9ecef;
        }
        .field-description {
            font-size: 13px;
            color: #999;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-card">
            <div class="form-header">
                <h1>{{ page_title }}</h1>
                <p>املأ البيانات التالية بعناية</p>
            </div>
            
            <form method="POST" action="{{ action_url }}">
                <div class="form-group">
                    <label>نوع المعاملة <span>*</span></label>
                    <select name="transaction_type_id" id="transaction_type" required onchange="updateDynamicFields()">
                        <option value="">-- اختر نوع المعاملة --</option>
                        <option value="1" {{ 'selected' if trans_type == 1 else '' }}>📝 عقد عمل</option>
                        <option value="2" {{ 'selected' if trans_type == 2 else '' }}>🏖️ إجازة موظف</option>
                        <option value="3" {{ 'selected' if trans_type == 3 else '' }}>🚗 استمارة سيارة</option>
                        <option value="4" {{ 'selected' if trans_type == 4 else '' }}>📄 ترخيص</option>
                        <option value="5" {{ 'selected' if trans_type == 5 else '' }}>⚖️ جلسة قضائية</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>المستخدم المسؤول <span>*</span></label>
                    <select name="user_id" required>
                        <option value="">-- اختر المستخدم --</option>
                        {% for user in users %}
                        <option value="{{ user.user_id }}" {{ 'selected' if selected_user == user.user_id else '' }}>
                            {{ user.full_name }} ({{ user.phone_number }})
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>عنوان المعاملة <span>*</span></label>
                    <input type="text" name="title" value="{{ title or '' }}" placeholder="مثال: عقد عمل - أحمد محمد" required>
                    <div class="field-description">اكتب عنوان واضح ومختصر</div>
                </div>
                
                <div class="form-group">
                    <label>تاريخ الانتهاء <span>*</span></label>
                    <input type="date" name="end_date" value="{{ end_date or '' }}" required>
                </div>
                
                <div id="dynamic-fields"></div>
                
                <button type="submit" class="btn-submit">{{ submit_text }}</button>
            </form>
            
            <a href="/" class="back-link">← العودة للرئيسية</a>
        </div>
    </div>
    
    <script>
    function updateDynamicFields() {
        const typeId = document.getElementById('transaction_type').value;
        const container = document.getElementById('dynamic-fields');
        
        let html = '<h3 style="margin-bottom: 20px; color: #333;">البيانات التفصيلية:</h3>';
        
        if (typeId == '1') {  // عقد عمل
            html += `
                <div class="form-row">
                    <div class="form-group">
                        <label>اسم الموظف <span>*</span></label>
                        <input type="text" name="employee_name" required>
                    </div>
                    <div class="form-group">
                        <label>رقم العقد <span>*</span></label>
                        <input type="text" name="contract_number" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>المسمى الوظيفي <span>*</span></label>
                        <input type="text" name="job_title" required>
                    </div>
                    <div class="form-group">
                        <label>الراتب</label>
                        <input type="text" name="salary" placeholder="10000">
                    </div>
                </div>
            `;
        } else if (typeId == '2') {  // إجازة
            html += `
                <div class="form-group">
                    <label>اسم الموظف <span>*</span></label>
                    <input type="text" name="employee_name" required>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>نوع الإجازة</label>
                        <select name="vacation_type">
                            <option value="سنوية">سنوية</option>
                            <option value="مرضية">مرضية</option>
                            <option value="طارئة">طارئة</option>
                            <option value="أمومة">أمومة</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>الموظف البديل</label>
                        <input type="text" name="substitute">
                    </div>
                </div>
            `;
        } else if (typeId == '3') {  // سيارة
            html += `
                <div class="form-row">
                    <div class="form-group">
                        <label>رقم اللوحة <span>*</span></label>
                        <input type="text" name="plate_number" placeholder="أ ب ج 1234" required>
                    </div>
                    <div class="form-group">
                        <label>نوع السيارة</label>
                        <input type="text" name="vehicle_type" placeholder="كامري 2023">
                    </div>
                </div>
                <div class="form-group">
                    <label>الرقم التسلسلي (VIN)</label>
                    <input type="text" name="vin">
                </div>
            `;
        } else if (typeId == '4') {  // ترخيص
            html += `
                <div class="form-row">
                    <div class="form-group">
                        <label>نوع الترخيص <span>*</span></label>
                        <input type="text" name="license_type" placeholder="سجل تجاري" required>
                    </div>
                    <div class="form-group">
                        <label>رقم الترخيص</label>
                        <input type="text" name="license_number">
                    </div>
                </div>
                <div class="form-group">
                    <label>الجهة المصدرة <span>*</span></label>
                    <input type="text" name="issuing_authority" placeholder="وزارة التجارة" required>
                </div>
            `;
        } else if (typeId == '5') {  // قضية
            html += `
                <div class="form-row">
                    <div class="form-group">
                        <label>رقم القضية <span>*</span></label>
                        <input type="text" name="case_number" placeholder="2025/001" required>
                    </div>
                    <div class="form-group">
                        <label>المحكمة</label>
                        <input type="text" name="court_name" placeholder="المحكمة التجارية">
                    </div>
                </div>
                <div class="form-group">
                    <label>بيان القضية <span>*</span></label>
                    <textarea name="case_description" required></textarea>
                </div>
                <div class="form-group">
                    <label>رابط الجلسة (اختياري)</label>
                    <input type="url" name="session_link" placeholder="https://...">
                </div>
            `;
        }
        
        container.innerHTML = html;
    }
    
    // تحميل الحقول عند فتح الصفحة
    window.addEventListener('DOMContentLoaded', function() {
        updateDynamicFields();
    });
    </script>
</body>
</html>
'''

# ==================== صفحة استيراد Excel ====================

IMPORT_EXCEL_PAGE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>استيراد من Excel - نظام إدارة المعاملات</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .import-card {
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .import-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .import-icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
        .import-header h1 {
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }
        .import-header p {
            color: #666;
            font-size: 16px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8eeff 100%);
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 30px;
        }
        .upload-area:hover {
            background: linear-gradient(135deg, #e8eeff 0%, #d8deff 100%);
            border-color: #764ba2;
        }
        .upload-area input[type="file"] {
            display: none;
        }
        .upload-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        .upload-text {
            font-size: 20px;
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .upload-hint {
            color: #666;
            font-size: 14px;
        }
        .instructions {
            background: linear-gradient(135deg, #fff9e6 0%, #ffeb99 100%);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        .instructions h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 20px;
        }
        .instructions ol {
            margin-right: 25px;
        }
        .instructions li {
            margin-bottom: 10px;
            color: #666;
            line-height: 1.6;
        }
        .btn-download-template {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        .btn-download-template:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(81, 207, 102, 0.4);
        }
        .btn-submit {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-submit:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .btn-submit:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .file-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        .file-info.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="import-card">
            <div class="import-header">
                <div class="import-icon">📥</div>
                <h1>استيراد معاملات من Excel</h1>
                <p>قم برفع ملف Excel يحتوي على بيانات المعاملات</p>
            </div>
            
            <a href="/download-template" class="btn-download-template">
                📄 تحميل ملف Excel النموذجي
            </a>
            
            <div class="instructions">
                <h3>⚠️ تعليمات مهمة:</h3>
                <ol>
                    <li>حمّل الملف النموذجي أولاً</li>
                    <li>املأ البيانات في الملف حسب الأعمدة المحددة</li>
                    <li>تأكد من صحة التواريخ (بصيغة: YYYY-MM-DD)</li>
                    <li>لا تغير أسماء الأعمدة</li>
                    <li>احفظ الملف بصيغة .xlsx أو .xls</li>
                </ol>
            </div>
            
            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                <label for="file-upload" class="upload-area" id="dropZone">
                    <div class="upload-icon">📤</div>
                    <div class="upload-text">اضغط لاختيار ملف أو اسحب الملف هنا</div>
                    <div class="upload-hint">Excel files only (.xlsx, .xls)</div>
                    <input type="file" id="file-upload" name="file" accept=".xlsx,.xls" required>
                </label>
                
                <div class="file-info" id="fileInfo">
                    <strong>الملف المحدد:</strong> <span id="fileName"></span>
                </div>
                
                <button type="submit" class="btn-submit" id="submitBtn" disabled>
                    📥 رفع واستيراد البيانات
                </button>
            </form>
            
            <a href="/" class="back-link">← العودة للرئيسية</a>
        </div>
    </div>
    
    <script>
    const fileInput = document.getElementById('file-upload');
    const fileName = document.getElementById('fileName');
    const fileInfo = document.getElementById('fileInfo');
    const submitBtn = document.getElementById('submitBtn');
    const dropZone = document.getElementById('dropZone');
    
    fileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            fileName.textContent = this.files[0].name;
            fileInfo.classList.add('show');
            submitBtn.disabled = false;
        }
    });
    
    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#764ba2';
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '#667eea';
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#667eea';
        
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileName.textContent = e.dataTransfer.files[0].name;
            fileInfo.classList.add('show');
            submitBtn.disabled = false;
        }
    });
    </script>
</body>
</html>
'''
# ==================== Routes - المسارات ====================

@app.route('/')
def index():
    """الصفحة الرئيسية المطورة"""
    try:
        # جلب جميع المعاملات
        all_transactions = db.get_active_transactions()
        users = db.get_all_users()
        
        # حساب الأيام المتبقية لكل معاملة
        for trans in all_transactions:
            end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d')
            days_left = (end_date - datetime.now()).days
            trans['days_left'] = days_left
        
        # فلترة المعاملات العاجلة (أقل من 7 أيام)
        urgent_transactions = [t for t in all_transactions if t['days_left'] <= 7]
        urgent_transactions.sort(key=lambda x: x['days_left'])
        
        # حساب الإحصائيات
        critical_count = len([t for t in all_transactions if t['days_left'] <= 3])
        warning_count = len([t for t in all_transactions if 3 < t['days_left'] <= 7])
        
        # إحصائيات حسب النوع
        count_by_type = {}
        urgent_by_type = {}
        
        for trans in all_transactions:
            type_id = trans['transaction_type_id']
            count_by_type[type_id] = count_by_type.get(type_id, 0) + 1
            
            if trans['days_left'] <= 7:
                urgent_by_type[type_id] = urgent_by_type.get(type_id, 0) + 1
        
        return render_template_string(
            MAIN_DASHBOARD,
            urgent_transactions=urgent_transactions,
            critical_count=critical_count,
            warning_count=warning_count,
            total_active=len(all_transactions),
            total_users=len(users),
            count_by_type=count_by_type,
            urgent_by_type=urgent_by_type
        )
    except Exception as e:
        return f"<h1 style='text-align:center;color:red;padding:50px;'>❌ خطأ: {str(e)}</h1>", 500

@app.route('/category/<category>')
def category_page(category):
    """صفحة كل قسم"""
    try:
        # تحديد نوع المعاملة والأيقونة
        category_map = {
            'contracts': (1, 'عقود العمل', '📝'),
            'vacations': (2, 'الإجازات', '🏖️'),
            'vehicles': (3, 'السيارات', '🚗'),
            'licenses': (4, 'التراخيص', '📄'),
            'courts': (5, 'القضايا', '⚖️')
        }
        
        if category not in category_map:
            return redirect('/')
        
        type_id, category_name, category_icon = category_map[category]
        
        # جلب المعاملات حسب النوع
        all_transactions = db.get_active_transactions()
        transactions = [t for t in all_transactions if t['transaction_type_id'] == type_id]
        
        # حساب الأيام المتبقية
        for trans in transactions:
            end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d')
            days_left = (end_date - datetime.now()).days
            trans['days_left'] = days_left
            
            # تحويل data من JSON إلى dict
            if isinstance(trans.get('data'), str):
                trans['data'] = json.loads(trans['data'])
        
        # ترتيب حسب الأقرب للانتهاء
        transactions.sort(key=lambda x: x['days_left'])
        
        return render_template_string(
            CATEGORY_PAGE,
            category_name=category_name,
            category_icon=category_icon,
            type_id=type_id,
            transactions=transactions
        )
    except Exception as e:
        return f"<h1 style='text-align:center;color:red;'>خطأ: {str(e)}</h1>", 500

@app.route('/add-transaction', methods=['GET', 'POST'])
def add_transaction():
    """إضافة معاملة جديدة"""
    if request.method == 'POST':
        try:
            transaction_type_id = int(request.form.get('transaction_type_id'))
            user_id = int(request.form.get('user_id'))
            title = request.form.get('title')
            end_date = request.form.get('end_date')
            
            # جمع البيانات الإضافية حسب النوع
            data = {}
            
            if transaction_type_id == 1:  # عقد عمل
                data = {
                    "اسم_الموظف": request.form.get('employee_name'),
                    "رقم_العقد": request.form.get('contract_number'),
                    "المسمى_الوظيفي": request.form.get('job_title'),
                    "الراتب": request.form.get('salary', '')
                }
            elif transaction_type_id == 2:  # إجازة
                data = {
                    "اسم_الموظف": request.form.get('employee_name'),
                    "نوع_الإجازة": request.form.get('vacation_type', 'سنوية'),
                    "الموظف_البديل": request.form.get('substitute', '')
                }
            elif transaction_type_id == 3:  # سيارة
                data = {
                    "رقم_اللوحة": request.form.get('plate_number'),
                    "نوع_السيارة": request.form.get('vehicle_type', ''),
                    "VIN": request.form.get('vin', '')
                }
            elif transaction_type_id == 4:  # ترخيص
                data = {
                    "نوع_الترخيص": request.form.get('license_type'),
                    "رقم_الترخيص": request.form.get('license_number', ''),
                    "الجهة_المصدرة": request.form.get('issuing_authority')
                }
            elif transaction_type_id == 5:  # قضية
                data = {
                    "رقم_القضية": request.form.get('case_number'),
                    "المحكمة": request.form.get('court_name', ''),
                    "بيان_القضية": request.form.get('case_description'),
                    "رابط_الجلسة": request.form.get('session_link', '')
                }
            
            # إضافة المعاملة
            trans_id = db.add_transaction(transaction_type_id, user_id, title, data, end_date)
            
            # إضافة تنبيهات تلقائية
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            days_until = (end_date_obj - datetime.now()).days
            
            if days_until <= 30:
                db.add_notification(trans_id, 3, [user_id])
            elif days_until <= 90:
                db.add_notification(trans_id, 7, [user_id])
                db.add_notification(trans_id, 3, [user_id])
            else:
                db.add_notification(trans_id, 30, [user_id])
                db.add_notification(trans_id, 7, [user_id])
            
            # رسالة نجاح
            success_html = f'''
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="2;url=/">
                <title>تم بنجاح!</title>
                <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Tajawal', sans-serif;
                        background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .success-box {{
                        background: white;
                        padding: 60px;
                        border-radius: 25px;
                        text-align: center;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        animation: slideUp 0.5s ease;
                    }}
                    @keyframes slideUp {{
                        from {{ opacity: 0; transform: translateY(50px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    h1 {{
                        color: #51cf66;
                        font-size: 48px;
                        margin-bottom: 20px;
                    }}
                    p {{
                        font-size: 20px;
                        color: #333;
                        margin: 15px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="success-box">
                    <h1>✅ تم بنجاح!</h1>
                    <p>تم إضافة المعاملة بنجاح</p>
                    <p style="color: #666; font-size: 16px;">سيتم تحويلك تلقائياً...</p>
                </div>
            </body>
            </html>
            '''
            return success_html
            
        except Exception as e:
            return f"<h1 style='color:red;text-align:center;'>خطأ: {str(e)}</h1><a href='/add-transaction'>رجوع</a>", 500
    
    # GET - عرض النموذج
    users = db.get_all_users()
    trans_type = int(request.args.get('type', 0))
    
    return render_template_string(
        ADD_EDIT_TRANSACTION,
        page_title='إضافة معاملة جديدة',
        action_url='/add-transaction',
        submit_text='➕ إضافة المعاملة',
        users=users,
        trans_type=trans_type,
        selected_user=None,
        title='',
        end_date=''
    )

@app.route('/edit-transaction/<int:trans_id>', methods=['GET', 'POST'])
def edit_transaction(trans_id):
    """تعديل معاملة"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            end_date = request.form.get('end_date')
            
            # تحديث البيانات في قاعدة البيانات
            db.cursor.execute('''
                UPDATE transactions 
                SET title = ?, end_date = ?
                WHERE transaction_id = ?
            ''', (title, end_date, trans_id))
            db.conn.commit()
            
            # رسالة نجاح
            success_html = '''
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="2;url=/">
                <title>تم التحديث!</title>
                <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet">
                <style>
                    body {
                        font-family: 'Tajawal', sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .success-box {
                        background: white;
                        padding: 60px;
                        border-radius: 25px;
                        text-align: center;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }
                    h1 {
                        color: #667eea;
                        font-size: 48px;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="success-box">
                    <h1>✅ تم التحديث!</h1>
                    <p>سيتم تحويلك تلقائياً...</p>
                </div>
            </body>
            </html>
            '''
            return success_html
            
        except Exception as e:
            return f"<h1 style='color:red;'>خطأ: {str(e)}</h1>", 500
    
    # GET - عرض النموذج
    try:
        trans = db.cursor.execute('''
            SELECT * FROM transactions WHERE transaction_id = ?
        ''', (trans_id,)).fetchone()
        
        if not trans:
            return redirect('/')
        
        users = db.get_all_users()
        
        return render_template_string(
            ADD_EDIT_TRANSACTION,
            page_title='تعديل المعاملة',
            action_url=f'/edit-transaction/{trans_id}',
            submit_text='💾 حفظ التعديلات',
            users=users,
            trans_type=trans['transaction_type_id'],
            selected_user=trans['user_id'],
            title=trans['title'],
            end_date=trans['end_date']
        )
    except Exception as e:
        return f"<h1 style='color:red;'>خطأ: {str(e)}</h1>", 500

@app.route('/delete-transaction/<int:trans_id>')
def delete_transaction(trans_id):
    """حذف معاملة"""
    try:
        db.cursor.execute('DELETE FROM transactions WHERE transaction_id = ?', (trans_id,))
        db.cursor.execute('DELETE FROM notifications WHERE transaction_id = ?', (trans_id,))
        db.conn.commit()
        
        success_html = '''
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="1;url=/">
            <title>تم الحذف!</title>
            <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Tajawal', sans-serif;
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .success-box {
                    background: white;
                    padding: 60px;
                    border-radius: 25px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }
                h1 {
                    color: #ff6b6b;
                    font-size: 48px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="success-box">
                <h1>🗑️ تم الحذف!</h1>
                <p>سيتم تحويلك تلقائياً...</p>
            </div>
        </body>
        </html>
        '''
        return success_html
    except Exception as e:
        return f"<h1 style='color:red;'>خطأ: {str(e)}</h1>", 500

@app.route('/import-excel', methods=['GET', 'POST'])
def import_excel():
    """استيراد من Excel"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return "لم يتم رفع ملف", 400
            
            file = request.files['file']
            
            if file.filename == '':
                return "لم يتم اختيار ملف", 400
            
            # قراءة ملف Excel
            df = pd.read_excel(file)
            
            # التحقق من الأعمدة المطلوبة
            required_columns = ['نوع_المعاملة', 'المستخدم_ID', 'العنوان', 'تاريخ_الانتهاء']
            if not all(col in df.columns for col in required_columns):
                return "الملف لا يحتوي على الأعمدة المطلوبة", 400
            
            # إضافة المعاملات
            added_count = 0
            for _, row in df.iterrows():
                try:
                    trans_id = db.add_transaction(
                        int(row['نوع_المعاملة']),
                        int(row['المستخدم_ID']),
                        str(row['العنوان']),
                        {},
                        str(row['تاريخ_الانتهاء'])
                    )
                    db.add_notification(trans_id, 7, [int(row['المستخدم_ID'])])
                    added_count += 1
                except:
                    continue
            
            success_html = f'''
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3;url=/">
                <title>تم الاستيراد!</title>
                <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Tajawal', sans-serif;
                        background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .box {{
                        background: white;
                        padding: 60px;
                        border-radius: 25px;
                        text-align: center;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    }}
                    h1 {{
                        color: #51cf66;
                        font-size: 48px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>✅ تم الاستيراد!</h1>
                    <p style="font-size: 24px;">تم استيراد {added_count} معاملة</p>
                    <p style="color: #666;">سيتم تحويلك تلقائياً...</p>
                </div>
            </body>
            </html>
            '''
            return success_html
            
        except Exception as e:
            return f"<h1 style='color:red;'>خطأ: {str(e)}</h1>", 500
    
    # GET - عرض صفحة الاستيراد
    return render_template_string(IMPORT_EXCEL_PAGE)

@app.route('/download-template')
def download_template():
    """تحميل ملف Excel النموذجي"""
    try:
        # إنشاء ملف Excel نموذجي
        data = {
            'نوع_المعاملة': [1, 2, 3, 4, 5],
            'المستخدم_ID': [218601139, 218601139, 218601139, 218601139, 218601139],
            'العنوان': [
                'عقد عمل - مثال',
                'إجازة - مثال',
                'سيارة - مثال',
                'ترخيص - مثال',
                'قضية - مثال'
            ],
            'تاريخ_الانتهاء': [
                '2025-12-31',
                '2025-12-25',
                '2026-01-15',
                '2026-06-30',
                '2025-12-20'
            ]
        }
        
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='نموذج')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='template_transactions.xlsx'
        )
    except Exception as e:
        return f"خطأ: {str(e)}", 500

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
        return f"<h1 style='color:red;'>خطأ: {str(e)}</h1>", 500

@app.route('/setup-admin')
def setup_admin():
    """إعداد حساب المسؤول - عبدالرحمن سالم"""
    try:
        user_id = 218601139
        phone = "+966599222345"
        name = "عبدالرحمن سالم"
        
        existing = db.get_user(user_id)
        
        if not existing:
            db.add_user(user_id, phone, name, 1)
        
        return redirect('/')
    except:
        return redirect('/')

@app.route('/add-sample-data')
def add_sample_data():
    """إضافة البيانات التجريبية"""
    try:
        # المستخدمين
        users = [
            (218601139, "+966599222345", "عبدالرحمن سالم", 1),
            (1002, "+966502345678", "فاطمة سعيد الأحمدي", 0),
            (1003, "+966503456789", "خالد عبدالله القحطاني", 0),
            (1004, "+966504567890", "نورة حسن المطيري", 0),
            (1005, "+966505678901", "سعد فهد الدوسري", 0),
        ]
        
        for uid, phone, name, admin in users:
            try:
                db.add_user(uid, phone, name, admin)
            except:
                pass
        
        # المعاملات (20 معاملة)
        transactions = [
            (1, 218601139, "عقد عمل - عبدالرحمن سالم", {"الموظف": "عبدالرحمن سالم", "المسمى": "مدير عام"}, 365),
            (1, 1002, "عقد عمل - فاطمة سعيد", {"الموظف": "فاطمة سعيد"}, 180),
            (1, 1003, "عقد عمل - خالد عبدالله", {"الموظف": "خالد عبدالله"}, 240),
            (2, 1002, "إجازة - فاطمة سعيد", {"الموظف": "فاطمة سعيد"}, 5),
            (2, 1003, "إجازة - خالد عبدالله", {"الموظف": "خالد عبدالله"}, 2),
            (2, 1004, "إجازة - نورة حسن", {"الموظف": "نورة حسن"}, 15),
            (3, 218601139, "سيارة - أ ب ج 1234", {"اللوحة": "أ ب ج 1234"}, 6),
            (3, 1005, "سيارة - د هـ و 5678", {"اللوحة": "د هـ و 5678"}, 25),
            (3, 1002, "سيارة - ز ح ط 9012", {"اللوحة": "ز ح ط 9012"}, 45),
            (4, 218601139, "ترخيص - سجل تجاري", {"النوع": "سجل تجاري"}, 90),
            (4, 1003, "ترخيص - فرع جدة", {"النوع": "ترخيص فرع"}, 120),
            (5, 218601139, "قضية - 2025/001", {"رقم_القضية": "2025/001"}, 10),
            (5, 1005, "قضية - 2025/002", {"رقم_القضية": "2025/002"}, 30),
        ]
        
        for type_id, user_id, title, data, days in transactions:
            try:
                end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                trans_id = db.add_transaction(type_id, user_id, title, data, end_date)
                
                if days <= 30:
                    db.add_notification(trans_id, 3, [user_id, 218601139])
                else:
                    db.add_notification(trans_id, 7, [user_id, 218601139])
            except:
                pass
        
        return redirect('/')
    except:
        return redirect('/')

def run_web_app():
    """تشغيل الموقع"""
    port = int(os.environ.get('PORT', 5000))
    print(f"   🌐 الموقع يعمل على المنفذ: {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_web_app()
