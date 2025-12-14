"""
🌐 Web Application + Dashboard - النسخة الاحترافية
موقع ويب تفاعلي مع لوحة تحكم مدمجة
"""
import os
from flask import Flask, render_template_string, request, redirect, jsonify, session
from datetime import datetime, timedelta
from database_supabase import Database
from ai_agent import AIAgent
import secrets
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# قاعدة البيانات
db = Database()
ai_agent = AIAgent(db)

# ==================== Helper Functions ====================

def calculate_days_left(end_date):
    """حساب الأيام المتبقية"""
    try:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        return (end - today).days
    except:
        return 0

def get_priority_class(days_left):
    """الحصول على CSS class حسب الأولوية"""
    if days_left <= 0:
        return 'expired'
    elif days_left <= 3:
        return 'critical'
    elif days_left <= 7:
        return 'warning'
    elif days_left <= 30:
        return 'upcoming'
    else:
        return 'safe'

def get_priority_color(days_left):
    """الحصول على اللون"""
    if days_left <= 0:
        return '#000000'
    elif days_left <= 3:
        return '#DC2626'
    elif days_left <= 7:
        return '#F59E0B'
    elif days_left <= 30:
        return '#10B981'
    else:
        return '#6B7280'

# ==================== الصفحة الرئيسية ====================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    
    # جلب المعاملات
    transactions = db.get_active_transactions()
    
    # الإحصائيات
    stats = db.get_stats()
    
    # الفلترة
    filter_type = request.args.get('type')
    filter_priority = request.args.get('priority')
    search_query = request.args.get('q')
    
    if filter_type:
        transactions = [t for t in transactions if str(t['transaction_type_id']) == filter_type]
    
    if filter_priority:
        if filter_priority == 'critical':
            transactions = [t for t in transactions if t['days_left'] <= 3]
        elif filter_priority == 'warning':
            transactions = [t for t in transactions if 3 < t['days_left'] <= 7]
        elif filter_priority == 'upcoming':
            transactions = [t for t in transactions if t['days_left'] > 7]
    
    if search_query:
        transactions = [t for t in transactions if search_query.lower() in t['title'].lower()]
    
    # الأنواع للفلترة
    types = db.get_main_types()
    
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 نظام إدارة المعاملات</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* Header */
        .header {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-card .label {
            color: #666;
            font-size: 1em;
        }
        
        .stat-card.critical .number { color: #DC2626; }
        .stat-card.warning .number { color: #F59E0B; }
        .stat-card.upcoming .number { color: #10B981; }
        .stat-card.total .number { color: #667eea; }
        
        /* Filters */
        .filters {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .filters-row {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filter-group {
            flex: 1;
            min-width: 200px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: 600;
        }
        
        .filter-group select,
        .filter-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        .filter-group select:focus,
        .filter-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #6B7280;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #4B5563;
        }
        
        /* Transactions Grid */
        .transactions-grid {
            display: grid;
            gap: 20px;
        }
        
        .transaction-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-right: 5px solid #667eea;
            transition: all 0.3s;
        }
        
        .transaction-card:hover {
            transform: translateX(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .transaction-card.critical { border-right-color: #DC2626; }
        .transaction-card.warning { border-right-color: #F59E0B; }
        .transaction-card.upcoming { border-right-color: #10B981; }
        .transaction-card.safe { border-right-color: #6B7280; }
        
        .transaction-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        
        .transaction-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            flex: 1;
        }
        
        .transaction-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-right: 10px;
        }
        
        .badge-critical {
            background: #FEE2E2;
            color: #DC2626;
        }
        
        .badge-warning {
            background: #FEF3C7;
            color: #F59E0B;
        }
        
        .badge-upcoming {
            background: #D1FAE5;
            color: #10B981;
        }
        
        .badge-safe {
            background: #F3F4F6;
            color: #6B7280;
        }
        
        .transaction-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #666;
        }
        
        .meta-item strong {
            color: #333;
        }
        
        .transaction-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #f3f4f6;
        }
        
        .btn-action {
            padding: 8px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        
        .btn-view {
            background: #667eea;
            color: white;
        }
        
        .btn-view:hover {
            background: #5568d3;
        }
        
        .btn-edit {
            background: #10B981;
            color: white;
        }
        
        .btn-edit:hover {
            background: #059669;
        }
        
        .btn-delete {
            background: #DC2626;
            color: white;
        }
        
        .btn-delete:hover {
            background: #B91C1C;
        }
        
        .btn-notify {
            background: #F59E0B;
            color: white;
        }
        
        .btn-notify:hover {
            background: #D97706;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .empty-state h2 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .empty-state p {
            color: #666;
            font-size: 1.1em;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 30px;
            color: white;
            margin-top: 40px;
        }
        
        /* Navigation */
        .nav-menu {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .nav-link {
            padding: 10px 25px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .nav-link:hover {
            background: white;
            color: #667eea;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .filters-row {
                flex-direction: column;
            }
            
            .transaction-meta {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🎯 نظام إدارة المعاملات</h1>
            <p>النظام الاحترافي لمتابعة المعاملات والتنبيهات الذكية</p>
            
            <div class="nav-menu">
                <a href="/" class="nav-link">🏠 الرئيسية</a>
                <a href="/dashboard" class="nav-link">📊 لوحة التحكل</a>
                <a href="/api/v1/docs" class="nav-link">📚 API</a>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card total">
                <div class="label">📊 إجمالي المعاملات</div>
                <div class="number">{{ stats.total }}</div>
            </div>
            <div class="stat-card critical">
                <div class="label">🔴 عاجلة</div>
                <div class="number">{{ stats.critical }}</div>
            </div>
            <div class="stat-card warning">
                <div class="label">🟡 تحذير</div>
                <div class="number">{{ stats.warning }}</div>
            </div>
            <div class="stat-card upcoming">
                <div class="label">🟢 قادمة</div>
                <div class="number">{{ stats.upcoming }}</div>
            </div>
        </div>
        
        <!-- Filters -->
        <div class="filters">
            <form method="GET" action="/">
                <div class="filters-row">
                    <div class="filter-group">
                        <label>🔍 بحث</label>
                        <input type="text" name="q" placeholder="ابحث بالعنوان..." 
                               value="{{ request.args.get('q', '') }}">
                    </div>
                    
                    <div class="filter-group">
                        <label>📂 النوع</label>
                        <select name="type">
                            <option value="">جميع الأنواع</option>
                            {% for type in types %}
                            <option value="{{ type.id }}" 
                                    {% if request.args.get('type') == type.id|string %}selected{% endif %}>
                                {{ type.icon }} {{ type.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>⚡ الأولوية</label>
                        <select name="priority">
                            <option value="">جميع الأولويات</option>
                            <option value="critical" 
                                    {% if request.args.get('priority') == 'critical' %}selected{% endif %}>
                                🔴 عاجلة
                            </option>
                            <option value="warning" 
                                    {% if request.args.get('priority') == 'warning' %}selected{% endif %}>
                                🟡 تحذير
                            </option>
                            <option value="upcoming" 
                                    {% if request.args.get('priority') == 'upcoming' %}selected{% endif %}>
                                🟢 قادمة
                            </option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>&nbsp;</label>
                        <button type="submit" class="btn btn-primary">🔍 بحث</button>
                    </div>
                    
                    {% if request.args %}
                    <div class="filter-group">
                        <label>&nbsp;</label>
                        <a href="/" class="btn btn-secondary">🔄 إعادة تعيين</a>
                    </div>
                    {% endif %}
                </div>
            </form>
        </div>
        
        <!-- Transactions -->
        {% if transactions %}
        <div class="transactions-grid">
            {% for trans in transactions %}
            <div class="transaction-card {{ get_priority_class(trans.days_left) }}">
                <div class="transaction-header">
                    <div class="transaction-title">
                        {{ trans.type_icon }} {{ trans.title }}
                    </div>
                    <span class="transaction-badge badge-{{ get_priority_class(trans.days_left) }}">
                        {% if trans.days_left <= 0 %}
                            ⚫ منتهي
                        {% elif trans.days_left <= 3 %}
                            🔴 عاجل
                        {% elif trans.days_left <= 7 %}
                            🟡 تحذير
                        {% else %}
                            🟢 عادي
                        {% endif %}
                    </span>
                </div>
                
                <div class="transaction-meta">
                    <div class="meta-item">
                        📂 <strong>{{ trans.type_name }}</strong>
                    </div>
                    <div class="meta-item">
                        📅 <strong>{{ trans.end_date }}</strong>
                    </div>
                    <div class="meta-item">
                        ⏰ <strong>{{ trans.days_left }} يوم</strong>
                    </div>
                    <div class="meta-item">
                        👤 <strong>{{ trans.user_name }}</strong>
                    </div>
                    {% if trans.responsible_person_name %}
                    <div class="meta-item">
                        👔 <strong>{{ trans.responsible_person_name }}</strong>
                    </div>
                    {% endif %}
                </div>
                
                {% if trans.description %}
                <div style="margin-top: 15px; color: #666; font-size: 0.95em;">
                    📝 {{ trans.description[:100] }}{% if trans.description|length > 100 %}...{% endif %}
                </div>
                {% endif %}
                
                <div class="transaction-actions">
                    <a href="/transaction/{{ trans.transaction_id }}" class="btn-action btn-view">
                        👁️ عرض
                    </a>
                    <a href="/edit-transaction/{{ trans.transaction_id }}" class="btn-action btn-edit">
                        ✏️ تعديل
                    </a>
                    <a href="/send-notification/{{ trans.transaction_id }}" class="btn-action btn-notify">
                        📧 تنبيه فوري
                    </a>
                    <a href="/delete/{{ trans.transaction_id }}" 
                       class="btn-action btn-delete"
                       onclick="return confirm('هل أنت متأكد من الحذف؟')">
                        🗑️ حذف
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <h2>📋 لا توجد معاملات</h2>
            <p>لم يتم العثور على أي معاملات تطابق البحث</p>
        </div>
        {% endif %}
        
        <!-- Footer -->
        <div class="footer">
            <p>🚀 نظام إدارة المعاملات v2.0 | مدعوم بـ Supabase & AI</p>
            <p style="margin-top: 10px; opacity: 0.8;">
                آخر تحديث: {{ datetime.now().strftime('%Y-%m-%d %H:%M') }}
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(
        html,
        transactions=transactions,
        stats=stats,
        types=types,
        request=request,
        get_priority_class=get_priority_class,
        datetime=datetime
    )

# ==================== صفحة المعاملة ====================

@app.route('/transaction/<int:transaction_id>')
def view_transaction(transaction_id):
    """عرض تفاصيل معاملة"""
    transaction = db.get_transaction(transaction_id)
    
    if not transaction:
        return "المعاملة غير موجودة", 404
    
    # التنبؤ بالتأخيرات
    prediction = ai_agent.predict_delays(transaction_id)
    
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تفاصيل المعاملة</title>
    <style>
        /* نفس الـ CSS السابق */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .badge-critical { background: #FEE2E2; color: #DC2626; }
        .badge-warning { background: #FEF3C7; color: #F59E0B; }
        .badge-upcoming { background: #D1FAE5; color: #10B981; }
        
        .details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .detail-item {
            padding: 20px;
            background: #f9fafb;
            border-radius: 10px;
        }
        
        .detail-item .label {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .detail-item .value {
            color: #333;
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .prediction-box {
            background: #FEF3C7;
            padding: 25px;
            border-radius: 15px;
            border-right: 5px solid #F59E0B;
            margin: 20px 0;
        }
        
        .prediction-box h3 {
            color: #92400E;
            margin-bottom: 15px;
        }
        
        .factor-item {
            padding: 10px;
            background: white;
            border-radius: 8px;
            margin: 8px 0;
        }
        
        .btn-back {
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-back:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>{{ trans.type_icon }} {{ trans.title }}</h1>
                <span class="badge badge-{{ get_priority_class(trans.days_left) }}">
                    {% if trans.days_left <= 0 %}⚫ منتهي
                    {% elif trans.days_left <= 3 %}🔴 عاجل
                    {% elif trans.days_left <= 7 %}🟡 تحذير
                    {% else %}🟢 عادي{% endif %}
                </span>
            </div>
            
            <div class="details-grid">
                <div class="detail-item">
                    <div class="label">📂 النوع</div>
                    <div class="value">{{ trans.type_name }}</div>
                </div>
                <div class="detail-item">
                    <div class="label">📅 تاريخ الانتهاء</div>
                    <div class="value">{{ trans.end_date }}</div>
                </div>
                <div class="detail-item">
                    <div class="label">⏰ الأيام المتبقية</div>
                    <div class="value">{{ trans.days_left }} يوم</div>
                </div>
                <div class="detail-item">
                    <div class="label">👤 صاحب المعاملة</div>
                    <div class="value">{{ trans.user_name }}</div>
                </div>
                {% if trans.responsible_person_name %}
                <div class="detail-item">
                    <div class="label">👔 المسؤول</div>
                    <div class="value">{{ trans.responsible_person_name }}</div>
                </div>
                {% endif %}
                <div class="detail-item">
                    <div class="label">📧 عدد المستلمين</div>
                    <div class="value">{{ trans.reminder_recipients|length }} شخص</div>
                </div>
            </div>
            
            {% if trans.description %}
            <div style="padding: 20px; background: #f9fafb; border-radius: 10px; margin: 20px 0;">
                <div style="color: #666; margin-bottom: 10px;">📝 الملاحظات:</div>
                <div style="color: #333; line-height: 1.6;">{{ trans.description }}</div>
            </div>
            {% endif %}
            
            <!-- AI Prediction -->
            <div class="prediction-box">
                <h3>🤖 التنبؤ الذكي بالتأخيرات</h3>
                <div style="margin: 15px 0;">
                    <strong>مستوى الخطر:</strong> {{ prediction.risk_label }}
                    ({{ prediction.probability }})
                </div>
                
                <div style="margin-top: 15px;">
                    <strong>العوامل المؤثرة:</strong>
                    {% for factor in prediction.factors %}
                    <div class="factor-item">
                        {{ factor.factor }} - التأثير: {{ factor.impact }}
                    </div>
                    {% endfor %}
                </div>
                
                <div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px;">
                    <strong>💡 التوصية:</strong> {{ prediction.recommendation }}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" class="btn-back">🔙 العودة للرئيسية</a>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(
        html,
        trans=transaction,
        prediction=prediction,
        get_priority_class=get_priority_class
    )
# ==================== Dashboard ====================

@app.route('/dashboard')
def dashboard():
    """لوحة التحكم الشاملة"""
    
    # التحليل الذكي
    analysis = ai_agent.analyze_all_transactions()
    
    # الجدولة الذكية
    schedule = ai_agent.smart_scheduling()
    
    # الإحصائيات
    stats = analysis['statistics']
    
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 لوحة التحكم</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .dashboard-header {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .dashboard-header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        /* Stats Grid */
        .stats-mega-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .mega-stat-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .mega-stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .mega-stat-card .icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .mega-stat-card .number {
            font-size: 3em;
            font-weight: bold;
            margin: 15px 0;
        }
        
        .mega-stat-card .label {
            color: #666;
            font-size: 1.1em;
        }
        
        .mega-stat-card.red .number { color: #DC2626; }
        .mega-stat-card.yellow .number { color: #F59E0B; }
        .mega-stat-card.green .number { color: #10B981; }
        .mega-stat-card.blue .number { color: #667eea; }
        
        /* Recommendations */
        .recommendations-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .recommendations-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .recommendation-item {
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-right: 5px solid #667eea;
            background: #f9fafb;
        }
        
        .recommendation-item.critical {
            background: #FEE2E2;
            border-right-color: #DC2626;
        }
        
        .recommendation-item.high {
            background: #FEF3C7;
            border-right-color: #F59E0B;
        }
        
        .recommendation-item.normal {
            background: #DBEAFE;
            border-right-color: #667eea;
        }
        
        .recommendation-item .rec-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        .recommendation-item .rec-icon {
            font-size: 2em;
        }
        
        .recommendation-item .rec-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .recommendation-item .rec-message {
            color: #666;
            margin-top: 10px;
            line-height: 1.6;
        }
        
        /* Schedule */
        .schedule-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .schedule-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .schedule-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .schedule-item {
            padding: 15px;
            margin: 10px 0;
            background: #f9fafb;
            border-radius: 8px;
            border-right: 3px solid #667eea;
        }
        
        .schedule-item.critical { border-right-color: #DC2626; }
        .schedule-item.warning { border-right-color: #F59E0B; }
        .schedule-item.safe { border-right-color: #10B981; }
        
        .schedule-item-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .schedule-item-meta {
            color: #666;
            font-size: 0.9em;
        }
        
        /* Charts Section */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .chart-card h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .chart-bar {
            margin: 15px 0;
        }
        
        .chart-bar-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .chart-bar-fill {
            height: 30px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 5px;
            transition: width 0.3s;
        }
        
        .btn-back {
            display: inline-block;
            padding: 15px 40px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .btn-back:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .stats-mega-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .schedule-section {
                grid-template-columns: 1fr;
            }
            
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="dashboard-header">
            <h1>📊 لوحة التحكم الذكية</h1>
            <p>تحليل شامل مدعوم بالذكاء الاصطناعي</p>
            <p style="color: #999; margin-top: 10px;">آخر تحديث: {{ analysis.analyzed_at }}</p>
        </div>
        
        <!-- Mega Stats -->
        <div class="stats-mega-grid">
            <div class="mega-stat-card blue">
                <div class="icon">📊</div>
                <div class="number">{{ analysis.total_transactions }}</div>
                <div class="label">إجمالي المعاملات</div>
            </div>
            
            <div class="mega-stat-card red">
                <div class="icon">🔴</div>
                <div class="number">{{ analysis.critical|length }}</div>
                <div class="label">معاملات عاجلة</div>
            </div>
            
            <div class="mega-stat-card yellow">
                <div class="icon">🟡</div>
                <div class="number">{{ analysis.warning|length }}</div>
                <div class="label">معاملات تحذير</div>
            </div>
            
            <div class="mega-stat-card green">
                <div class="icon">🟢</div>
                <div class="number">{{ analysis.upcoming|length }}</div>
                <div class="label">معاملات قادمة</div>
            </div>
            
            {% if analysis.overdue|length > 0 %}
            <div class="mega-stat-card" style="border: 3px solid #DC2626;">
                <div class="icon">⚫</div>
                <div class="number" style="color: #000;">{{ analysis.overdue|length }}</div>
                <div class="label" style="color: #DC2626; font-weight: bold;">معاملات منتهية!</div>
            </div>
            {% endif %}
            
            {% if analysis.today_ending|length > 0 %}
            <div class="mega-stat-card" style="border: 3px solid #F59E0B;">
                <div class="icon">⚡</div>
                <div class="number" style="color: #F59E0B;">{{ analysis.today_ending|length }}</div>
                <div class="label" style="color: #F59E0B; font-weight: bold;">تنتهي اليوم!</div>
            </div>
            {% endif %}
        </div>
        
        <!-- AI Recommendations -->
        <div class="recommendations-section">
            <h2>🤖 التوصيات الذكية</h2>
            
            {% if analysis.recommendations %}
                {% for rec in analysis.recommendations %}
                <div class="recommendation-item {{ rec.priority }}">
                    <div class="rec-header">
                        <div class="rec-icon">{{ rec.icon }}</div>
                        <div class="rec-title">{{ rec.title }}</div>
                    </div>
                    <div class="rec-message">{{ rec.message }}</div>
                </div>
                {% endfor %}
            {% else %}
                <div style="text-align: center; padding: 30px; color: #10B981;">
                    <div style="font-size: 3em;">🎉</div>
                    <div style="font-size: 1.3em; margin-top: 10px;">لا توجد توصيات! الوضع ممتاز!</div>
                </div>
            {% endif %}
        </div>
        
        <!-- Smart Schedule -->
        <h2 style="color: white; text-align: center; margin-bottom: 20px; font-size: 2em;">
            📅 الجدولة الذكية
        </h2>
        
        <div class="schedule-section">
            <!-- Today -->
            <div class="schedule-card">
                <h3>⚡ اليوم ({{ schedule.today|length }})</h3>
                {% if schedule.today %}
                    {% for trans in schedule.today[:5] %}
                    <div class="schedule-item critical">
                        <div class="schedule-item-title">{{ trans.title }}</div>
                        <div class="schedule-item-meta">
                            {{ trans.type_icon }} {{ trans.type_name }} • {{ trans.days_left }} يوم
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #999; padding: 20px;">لا توجد معاملات اليوم</p>
                {% endif %}
            </div>
            
            <!-- This Week -->
            <div class="schedule-card">
                <h3>📆 هذا الأسبوع ({{ schedule.this_week|length }})</h3>
                {% if schedule.this_week %}
                    {% for trans in schedule.this_week[:5] %}
                    <div class="schedule-item warning">
                        <div class="schedule-item-title">{{ trans.title }}</div>
                        <div class="schedule-item-meta">
                            {{ trans.type_icon }} {{ trans.type_name }} • {{ trans.days_left }} يوم
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #999; padding: 20px;">لا توجد معاملات</p>
                {% endif %}
            </div>
            
            <!-- Next Week -->
            <div class="schedule-card">
                <h3>📅 الأسبوع القادم ({{ schedule.next_week|length }})</h3>
                {% if schedule.next_week %}
                    {% for trans in schedule.next_week[:5] %}
                    <div class="schedule-item safe">
                        <div class="schedule-item-title">{{ trans.title }}</div>
                        <div class="schedule-item-meta">
                            {{ trans.type_icon }} {{ trans.type_name }} • {{ trans.days_left }} يوم
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="text-align: center; color: #999; padding: 20px;">لا توجد معاملات</p>
                {% endif %}
            </div>
        </div>
        
        <!-- Charts -->
        <div class="charts-grid">
            <!-- By Type -->
            <div class="chart-card">
                <h3>📊 حسب النوع</h3>
                {% for type_name, type_data in analysis.by_type.items() %}
                <div class="chart-bar">
                    <div class="chart-bar-label">
                        <span>{{ type_data.icon }} {{ type_name }}</span>
                        <span>{{ type_data.count }}</span>
                    </div>
                    <div style="background: #e5e7eb; border-radius: 5px;">
                        <div class="chart-bar-fill" 
                             style="width: {{ (type_data.count / analysis.total_transactions * 100)|round }}%;">
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- By Priority -->
            <div class="chart-card">
                <h3>⚡ حسب الأولوية</h3>
                
                <div class="chart-bar">
                    <div class="chart-bar-label">
                        <span>🔴 عاجلة</span>
                        <span>{{ analysis.by_priority.critical }}</span>
                    </div>
                    <div style="background: #e5e7eb; border-radius: 5px;">
                        <div class="chart-bar-fill" 
                             style="width: {{ (analysis.by_priority.critical / analysis.total_transactions * 100)|round if analysis.total_transactions > 0 else 0 }}%; background: #DC2626;">
                        </div>
                    </div>
                </div>
                
                <div class="chart-bar">
                    <div class="chart-bar-label">
                        <span>🟠 عالية</span>
                        <span>{{ analysis.by_priority.high }}</span>
                    </div>
                    <div style="background: #e5e7eb; border-radius: 5px;">
                        <div class="chart-bar-fill" 
                             style="width: {{ (analysis.by_priority.high / analysis.total_transactions * 100)|round if analysis.total_transactions > 0 else 0 }}%; background: #F59E0B;">
                        </div>
                    </div>
                </div>
                
                <div class="chart-bar">
                    <div class="chart-bar-label">
                        <span>🟢 عادية</span>
                        <span>{{ analysis.by_priority.normal }}</span>
                    </div>
                    <div style="background: #e5e7eb; border-radius: 5px;">
                        <div class="chart-bar-fill" 
                             style="width: {{ (analysis.by_priority.normal / analysis.total_transactions * 100)|round if analysis.total_transactions > 0 else 0 }}%; background: #10B981;">
                        </div>
                    </div>
                </div>
                
                <div class="chart-bar">
                    <div class="chart-bar-label">
                        <span>⚪ منخفضة</span>
                        <span>{{ analysis.by_priority.low }}</span>
                    </div>
                    <div style="background: #e5e7eb; border-radius: 5px;">
                        <div class="chart-bar-fill" 
                             style="width: {{ (analysis.by_priority.low / analysis.total_transactions * 100)|round if analysis.total_transactions > 0 else 0 }}%; background: #6B7280;">
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Back Button -->
        <div style="text-align: center; margin: 40px 0;">
            <a href="/" class="btn-back">🏠 العودة للرئيسية</a>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(
        html,
        analysis=analysis,
        schedule=schedule,
        stats=stats
    )

# ==================== API Routes ====================

@app.route('/api/v1/transactions', methods=['GET'])
def api_get_transactions():
    """API: جلب المعاملات"""
    try:
        user_id = request.args.get('user_id', type=int)
        transactions = db.get_transactions_by_role(user_id)
        
        return jsonify({
            'success': True,
            'count': len(transactions),
            'data': transactions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/transaction/<int:transaction_id>', methods=['GET'])
def api_get_transaction(transaction_id):
    """API: جلب معاملة واحدة"""
    try:
        transaction = db.get_transaction(transaction_id)
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': transaction
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/stats', methods=['GET'])
def api_get_stats():
    """API: الإحصائيات"""
    try:
        user_id = request.args.get('user_id', type=int)
        stats = db.get_stats(user_id)
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/ai/analyze', methods=['GET'])
def api_ai_analyze():
    """API: التحليل الذكي"""
    try:
        user_id = request.args.get('user_id', type=int)
        analysis = ai_agent.analyze_all_transactions(user_id)
        
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/docs')
def api_docs():
    """توثيق API"""
    
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 API Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
            direction: rtl;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .endpoint {
            background: #16213e;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
            border-right: 5px solid #667eea;
        }
        
        .endpoint .method {
            display: inline-block;
            padding: 8px 15px;
            border-radius: 5px;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .method.get {
            background: #10B981;
        }
        
        .method.post {
            background: #3B82F6;
        }
        
        .endpoint .path {
            font-size: 1.3em;
            color: #F59E0B;
            margin: 10px 0;
        }
        
        .endpoint .description {
            color: #aaa;
            margin: 15px 0;
        }
        
        .code-block {
            background: #0f1419;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            overflow-x: auto;
        }
        
        .code-block pre {
            color: #10B981;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 API Documentation</h1>
            <p>نظام إدارة المعاملات - REST API v1.0</p>
        </div>
        
        <!-- Endpoint 1 -->
        <div class="endpoint">
            <span class="method get">GET</span>
            <div class="path">/api/v1/transactions</div>
            <div class="description">جلب جميع المعاملات</div>
            
            <h3 style="margin-top: 20px;">Parameters:</h3>
            <div class="code-block">
                <pre>user_id (optional): معرف المستخدم</pre>
            </div>
            
            <h3>Response:</h3>
            <div class="code-block">
<pre>{
  "success": true,
  "count": 10,
  "data": [...]
}</pre>
            </div>
            
            <h3>Example:</h3>
            <div class="code-block">
                <pre>curl https://your-app.onrender.com/api/v1/transactions?user_id=123456789</pre>
            </div>
        </div>
        
        <!-- Endpoint 2 -->
        <div class="endpoint">
            <span class="method get">GET</span>
            <div class="path">/api/v1/transaction/{id}</div>
            <div class="description">جلب معاملة واحدة بالتفصيل</div>
            
            <h3>Response:</h3>
            <div class="code-block">
<pre>{
  "success": true,
  "data": {
    "transaction_id": 1,
    "title": "عقد موظف",
    "end_date": "2026-01-15",
    "days_left": 32,
    ...
  }
}</pre>
            </div>
        </div>
        
        <!-- Endpoint 3 -->
        <div class="endpoint">
            <span class="method get">GET</span>
            <div class="path">/api/v1/stats</div>
            <div class="description">الإحصائيات الشاملة</div>
            
            <h3>Parameters:</h3>
            <div class="code-block">
                <pre>user_id (optional): معرف المستخدم</pre>
            </div>
            
            <h3>Response:</h3>
            <div class="code-block">
<pre>{
  "success": true,
  "data": {
    "total": 50,
    "critical": 5,
    "warning": 10,
    "upcoming": 20,
    "safe": 15,
    ...
  }
}</pre>
            </div>
        </div>
        
        <!-- Endpoint 4 -->
        <div class="endpoint">
            <span class="method get">GET</span>
            <div class="path">/api/v1/ai/analyze</div>
            <div class="description">التحليل الذكي الشامل</div>
            
            <h3>Parameters:</h3>
            <div class="code-block">
                <pre>user_id (optional): معرف المستخدم</pre>
            </div>
            
            <h3>Response:</h3>
            <div class="code-block">
<pre>{
  "success": true,
  "data": {
    "version": "1.0.0",
    "total_transactions": 50,
    "critical": [...],
    "recommendations": [...],
    "statistics": {...}
  }
}</pre>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <a href="/" style="color: #667eea; text-decoration: none; font-size: 1.2em;">
                🏠 العودة للرئيسية
            </a>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(html)

# ==================== Health Check ====================

@app.route('/health')
def health():
    """فحص صحة النظام"""
    try:
        # اختبار قاعدة البيانات
        db.get_stats()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== Run ====================

def run_web():
    """تشغيل الموقع"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_web()
