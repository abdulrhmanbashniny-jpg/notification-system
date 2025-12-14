"""
🌐 Web Application 2025 - التصميم العصري
موقع تفاعلي بتقنيات حديثة: Dark Mode, Real-time, Animations
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

db = Database()
ai_agent = AIAgent(db)

# ==================== Health Check ====================

@app.route('/health')
def health():
    """نقطة فحص الصحة"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'transactions-system'
    })

# ==================== الصفحة الرئيسية ====================

@app.route('/')
def index():
    """الصفحة الرئيسية - تصميم 2025 حديث"""
    
    transactions = db.get_active_transactions()
    stats = db.get_stats()
    types = db.get_main_types()
    
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 نظام إدارة المعاملات 2025</title>
    
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #1f2937;
            --light: #f9fafb;
            --text: #111827;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --shadow: rgba(0, 0, 0, 0.1);
            --shadow-lg: rgba(0, 0, 0, 0.15);
        }
        
        [data-theme="dark"] {
            --primary: #818cf8;
            --secondary: #a78bfa;
            --dark: #111827;
            --light: #1f2937;
            --text: #f9fafb;
            --text-light: #9ca3af;
            --border: #374151;
            --shadow: rgba(0, 0, 0, 0.3);
            --shadow-lg: rgba(0, 0, 0, 0.5);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--light);
            color: var(--text);
            transition: all 0.3s ease;
            min-height: 100vh;
        }
        
        .bg-animated {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: -1;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            opacity: 0.05;
        }
        
        [data-theme="dark"] .bg-animated {
            opacity: 0.03;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header-modern {
            background: var(--light);
            padding: 30px;
            border-radius: 24px;
            box-shadow: 0 4px 20px var(--shadow);
            margin-bottom: 30px;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }
        
        .header-modern::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
            opacity: 0.05;
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.05; }
            50% { transform: scale(1.1); opacity: 0.08; }
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .logo {
            font-size: 2.5em;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .theme-toggle {
            width: 60px;
            height: 32px;
            background: var(--border);
            border-radius: 16px;
            position: relative;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .theme-toggle:hover {
            background: var(--primary);
        }
        
        .theme-toggle::before {
            content: '☀️';
            position: absolute;
            width: 28px;
            height: 28px;
            background: white;
            border-radius: 50%;
            top: 2px;
            right: 2px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }
        
        [data-theme="dark"] .theme-toggle::before {
            content: '🌙';
            right: 30px;
        }
        
        .nav-pills {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        
        .nav-pill {
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .nav-pill:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px var(--shadow-lg);
            background: var(--primary-dark);
        }
        
        .stats-modern {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-modern {
            background: var(--light);
            padding: 24px;
            border-radius: 20px;
            box-shadow: 0 4px 12px var(--shadow);
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }
        
        .stat-modern:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px var(--shadow-lg);
        }
        
        .stat-modern::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }
        
        .stat-icon {
            font-size: 2.5em;
            margin-bottom: 12px;
            display: block;
        }
        
        .stat-number {
            font-size: 2.8em;
            font-weight: 800;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-label {
            color: var(--text-light);
            font-weight: 600;
        }
        
        .search-modern {
            background: var(--light);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 4px 12px var(--shadow);
            border: 1px solid var(--border);
            margin-bottom: 30px;
        }
        
        .search-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr auto;
            gap: 16px;
            align-items: end;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .form-label {
            font-weight: 600;
            color: var(--text-light);
            font-size: 0.9em;
        }
        
        .form-input {
            padding: 14px 16px;
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 1em;
            background: var(--light);
            color: var(--text);
            transition: all 0.3s;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .btn-modern {
            padding: 14px 28px;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 1em;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px var(--shadow-lg);
        }
        
        .transactions-modern {
            display: grid;
            gap: 20px;
        }
        
        .transaction-modern {
            background: var(--light);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 12px var(--shadow);
            border: 1px solid var(--border);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .transaction-modern:hover {
            transform: translateX(-4px);
            box-shadow: 0 12px 24px var(--shadow-lg);
        }
        
        .transaction-modern::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 6px;
            background: linear-gradient(180deg, var(--primary), var(--secondary));
        }
        
        .transaction-modern.critical::before {
            background: linear-gradient(180deg, var(--danger), #dc2626);
        }
        
        .transaction-modern.warning::before {
            background: linear-gradient(180deg, var(--warning), #d97706);
        }
        
        .transaction-modern.safe::before {
            background: linear-gradient(180deg, var(--success), #059669);
        }
        
        .transaction-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 16px;
        }
        
        .transaction-title {
            font-size: 1.4em;
            font-weight: 700;
            color: var(--text);
            flex: 1;
        }
        
        .badge-modern {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        
        .badge-critical {
            background: linear-gradient(135deg, #fee2e2, #fecaca);
            color: #dc2626;
        }
        
        .badge-warning {
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            color: #d97706;
        }
        
        .badge-safe {
            background: linear-gradient(135deg, #d1fae5, #a7f3d0);
            color: #059669;
        }
        
        .transaction-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-light);
            font-size: 0.95em;
        }
        
        .transaction-actions {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }
        
        .btn-action {
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 0.9em;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .btn-view { background: var(--primary); color: white; }
        .btn-edit { background: var(--success); color: white; }
        .btn-notify { background: var(--warning); color: white; }
        
        .btn-action:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow);
        }
        
        .empty-state {
            text-align: center;
            padding: 80px 20px;
            background: var(--light);
            border-radius: 20px;
            box-shadow: 0 4px 12px var(--shadow);
            border: 2px dashed var(--border);
        }
        
        .empty-icon {
            font-size: 5em;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .empty-title {
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 12px;
            color: var(--text);
        }
        
        .empty-text {
            color: var(--text-light);
            font-size: 1.1em;
        }
        
        .footer-modern {
            text-align: center;
            padding: 40px 20px;
            margin-top: 60px;
            background: var(--light);
            border-radius: 20px;
            box-shadow: 0 4px 12px var(--shadow);
            border: 1px solid var(--border);
        }
        
        .fab {
            position: fixed;
            bottom: 30px;
            left: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.8em;
            box-shadow: 0 8px 24px var(--shadow-lg);
            cursor: pointer;
            transition: all 0.3s;
            z-index: 1000;
            text-decoration: none;
        }
        
        .fab:hover {
            transform: scale(1.1) rotate(90deg);
            box-shadow: 0 12px 32px var(--shadow-lg);
        }
        
        @media (max-width: 768px) {
            .search-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-modern {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .nav-pills {
                justify-content: center;
            }
            
            .transaction-header {
                flex-direction: column;
                gap: 12px;
            }
            
            .transaction-actions {
                flex-wrap: wrap;
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .transaction-modern {
            animation: fadeIn 0.5s ease-out;
        }
        
        .transaction-modern:nth-child(1) { animation-delay: 0.05s; }
        .transaction-modern:nth-child(2) { animation-delay: 0.1s; }
        .transaction-modern:nth-child(3) { animation-delay: 0.15s; }
        .transaction-modern:nth-child(4) { animation-delay: 0.2s; }
        .transaction-modern:nth-child(5) { animation-delay: 0.25s; }
    </style>
</head>
<body>
    <div class="bg-animated"></div>
    
    <div class="container">
        <div class="header-modern">
            <div class="header-content">
                <div class="header-top">
                    <div class="logo">🚀 إدارة المعاملات</div>
                    <div class="theme-toggle" onclick="toggleTheme()"></div>
                </div>
                
                <p style="color: var(--text-light); font-size: 1.1em; margin-bottom: 20px;">
                    النظام الأذكى لإدارة معاملاتك بتقنيات 2025
                </p>
                
                <div class="nav-pills">
                    <a href="/" class="nav-pill">🏠 الرئيسية</a>
                    <a href="/dashboard" class="nav-pill">📊 Dashboard</a>
                    <a href="/add-transaction" class="nav-pill">➕ إضافة معاملة</a>
                    <a href="/api/v1/docs" class="nav-pill">📚 API</a>
                </div>
            </div>
        </div>
        
        <div class="stats-modern">
            <div class="stat-modern">
                <span class="stat-icon">📊</span>
                <div class="stat-number">{{ stats.total }}</div>
                <div class="stat-label">إجمالي المعاملات</div>
            </div>
            
            <div class="stat-modern">
                <span class="stat-icon">🔴</span>
                <div class="stat-number" style="background: linear-gradient(135deg, #ef4444, #dc2626); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {{ stats.critical }}
                </div>
                <div class="stat-label">عاجلة</div>
            </div>
            
            <div class="stat-modern">
                <span class="stat-icon">🟡</span>
                <div class="stat-number" style="background: linear-gradient(135deg, #f59e0b, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {{ stats.warning }}
                </div>
                <div class="stat-label">تحذير</div>
            </div>
            
            <div class="stat-modern">
                <span class="stat-icon">🟢</span>
                <div class="stat-number" style="background: linear-gradient(135deg, #10b981, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {{ stats.upcoming }}
                </div>
                <div class="stat-label">قادمة</div>
            </div>
        </div>
        
        <div class="search-modern">
            <form method="GET" action="/">
                <div class="search-grid">
                    <div class="form-group">
                        <label class="form-label">🔍 بحث سريع</label>
                        <input type="text" name="q" class="form-input" 
                               placeholder="ابحث عن معاملة..." 
                               value="{{ request.args.get('q', '') }}">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">📂 النوع</label>
                        <select name="type" class="form-input">
                            <option value="">الكل</option>
                            {% for type in types %}
                            <option value="{{ type.id }}" 
                                    {% if request.args.get('type') == type.id|string %}selected{% endif %}>
                                {{ type.icon }} {{ type.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">⚡ الأولوية</label>
                        <select name="priority" class="form-input">
                            <option value="">الكل</option>
                            <option value="critical">🔴 عاجلة</option>
                            <option value="warning">🟡 تحذير</option>
                            <option value="upcoming">🟢 قادمة</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">&nbsp;</label>
                        <button type="submit" class="btn-modern btn-primary">
                            🔍 بحث
                        </button>
                    </div>
                </div>
            </form>
        </div>
        
        {% if transactions %}
        <div class="transactions-modern">
            {% for trans in transactions %}
            <div class="transaction-modern {{ get_priority_class(trans.days_left) }}">
                <div class="transaction-header">
                    <div class="transaction-title">
                        {{ trans.type_icon }} {{ trans.title }}
                    </div>
                    <span class="badge-modern badge-{{ get_priority_class(trans.days_left) }}">
                        {% if trans.days_left <= 0 %}⚫ منتهي
                        {% elif trans.days_left <= 3 %}🔴 عاجل
                        {% elif trans.days_left <= 7 %}🟡 تحذير
                        {% else %}🟢 عادي{% endif %}
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
                </div>
                
                <div class="transaction-actions">
                    <a href="/transaction/{{ trans.transaction_id }}" class="btn-action btn-view">
                        👁️ عرض
                    </a>
                    <a href="#" class="btn-action btn-edit">
                        ✏️ تعديل
                    </a>
                    <a href="#" class="btn-action btn-notify">
                        📧 تنبيه
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <div class="empty-icon">📋</div>
            <div class="empty-title">لا توجد معاملات</div>
            <div class="empty-text">ابدأ بإضافة معاملة جديدة</div>
        </div>
        {% endif %}
        
        <div class="footer-modern">
            <p style="font-weight: 600; margin-bottom: 8px;">
                🚀 نظام إدارة المعاملات v2.0
            </p>
            <p style="color: var(--text-light);">
                مدعوم بـ Supabase + AI • {{ datetime.now().year }}
            </p>
        </div>
    </div>
    
    <a href="/add-transaction" class="fab" title="إضافة معاملة">
        ➕
    </a>
    
    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }
        
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
    </script>
</body>
</html>
    """
    
    return render_template_string(
        html,
        transactions=transactions,
        stats=stats,
        types=types,
        request=request,
        get_priority_class=lambda d: 'critical' if d <= 3 else 'warning' if d <= 7 else 'safe',
        datetime=datetime
    )

# ==================== صفحة إضافة معاملة ====================

@app.route('/add-transaction', methods=['GET', 'POST'])
def add_transaction():
    """صفحة إضافة معاملة تفاعلية"""
    
    if request.method == 'POST':
        try:
            transaction_type_id = int(request.form.get('transaction_type_id'))
            user_id = int(request.form.get('user_id'))
            title = request.form.get('title')
            end_date = request.form.get('end_date')
            responsible_person_id = request.form.get('responsible_person_id')
            description = request.form.get('description')
            
            recipients = request.form.getlist('reminder_recipients[]')
            recipients = [int(r) for r in recipients if r]
            
            days_left = (datetime.strptime(end_date, '%Y-%m-%d').date() - datetime.now().date()).days
            priority = 'critical' if days_left <= 3 else 'high' if days_left <= 7 else 'normal'
            
            transaction_id = db.add_transaction(
                transaction_type_id=transaction_type_id,
                user_id=user_id,
                title=title,
                end_date=end_date,
                responsible_person_id=int(responsible_person_id) if responsible_person_id else None,
                reminder_recipients=recipients,
                description=description if description else None,
                priority=priority
            )
            
            if transaction_id:
                return redirect(f'/transaction/{transaction_id}')
            else:
                error = "فشل حفظ المعاملة"
        except Exception as e:
            error = f"خطأ: {e}"
    
    main_types = db.get_main_types()
    all_types = db.get_transaction_types()
    users = db.get_all_users()
    
    # بناء خريطة التفريعات
    subtypes_map = {}
    for type_obj in all_types:
        if type_obj['parent_id']:
            parent_id = type_obj['parent_id']
            if parent_id not in subtypes_map:
                subtypes_map[parent_id] = []
            subtypes_map[parent_id].append(type_obj)
    
    subtypes_json = json.dumps({k: [dict(v) for v in vals] for k, vals in subtypes_map.items()})
    
    html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>➕ إضافة معاملة جديدة</title>
    
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --success: #10b981;
            --danger: #ef4444;
            --dark: #1f2937;
            --light: #f9fafb;
            --text: #111827;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --shadow: rgba(0, 0, 0, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .form-card {
            background: white;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }
        
        .form-header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .form-header h1 {
            font-size: 2.5em;
            color: var(--primary);
            margin-bottom: 10px;
        }
        
        .form-header p {
            color: var(--text-light);
            font-size: 1.1em;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-label {
            display: block;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 10px;
            font-size: 1.05em;
        }
        
        .form-label .required {
            color: var(--danger);
            margin-right: 5px;
        }
        
        .form-input,
        .form-select,
        .form-textarea {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 1em;
            font-family: inherit;
            transition: all 0.3s;
        }
        
        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .form-textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .form-hint {
            display: block;
            color: var(--text-light);
            font-size: 0.9em;
            margin-top: 6px;
        }
        
        .recipients-list {
            max-height: 200px;
            overflow-y: auto;
            border: 2px solid var(--border);
            border-radius: 12px;
            padding: 10px;
        }
        
        .recipient-item {
            display: flex;
            align-items: center;
            padding: 10px;
            border-radius: 8px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .recipient-item:hover {
            background: var(--light);
        }
        
        .recipient-item input[type="checkbox"] {
            width: 20px;
            height: 20px;
            margin-left: 10px;
            cursor: pointer;
        }
        
        .recipient-item label {
            flex: 1;
            cursor: pointer;
            font-weight: 500;
        }
        
        .form-actions {
            display: flex;
            gap: 15px;
            margin-top: 40px;
        }
        
        .btn {
            flex: 1;
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 1.1em;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            text-align: center;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(99, 102, 241, 0.3);
        }
        
        .btn-secondary {
            background: var(--border);
            color: var(--text);
        }
        
        .btn-secondary:hover {
            background: var(--dark);
            color: white;
        }
        
        .subtypes-group {
            display: none;
            animation: fadeIn 0.3s;
        }
        
        .subtypes-group.show {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @media (max-width: 768px) {
            .form-card {
                padding: 25px;
            }
            
            .form-header h1 {
                font-size: 2em;
            }
            
            .form-actions {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-card">
            <div class="form-header">
                <h1>➕ إضافة معاملة جديدة</h1>
                <p>املأ البيانات التالية بدقة</p>
            </div>
            
            <form method="POST" action="/add-transaction" id="transactionForm">
                
                <div class="form-group">
                    <label class="form-label">
                        <span class="required">*</span>
                        نوع المعاملة الرئيسي
                    </label>
                    <select name="main_type" id="mainType" class="form-select" required onchange="loadSubtypes(this.value)">
                        <option value="">-- اختر النوع --</option>
                        {% for type in main_types %}
                        <option value="{{ type.id }}">
                            {{ type.icon }} {{ type.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group subtypes-group" id="subtypesGroup">
                    <label class="form-label">
                        <span class="required">*</span>
                        التفصيل
                    </label>
                    <select name="subtype" id="subType" class="form-select">
                        <option value="">-- اختر التفصيل --</option>
                    </select>
                </div>
                
                <input type="hidden" name="transaction_type_id" id="finalTypeId" required>
                
                <div class="form-group">
                    <label class="form-label">
                        <span class="required">*</span>
                        عنوان المعاملة
                    </label>
                    <input type="text" name="title" class="form-input" 
                           placeholder="مثال: رخصة بناء عمارة سكنية" required minlength="3">
                    <span class="form-hint">أدخل عنواناً واضحاً ومختصراً</span>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        <span class="required">*</span>
                        تاريخ الانتهاء
                    </label>
                    <input type="date" name="end_date" class="form-input" 
                           required min="{{ datetime.now().strftime('%Y-%m-%d') }}">
                    <span class="form-hint">متى تنتهي صلاحية هذه المعاملة؟</span>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        <span class="required">*</span>
                        صاحب المعاملة
                    </label>
                    <select name="user_id" class="form-select" required>
                        <option value="">-- اختر المستخدم --</option>
                        {% for user in users %}
                        <option value="{{ user.user_id }}">
                            👤 {{ user.full_name }} {% if user.department %}({{ user.department }}){% endif %}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        الشخص المسؤول عن المتابعة
                    </label>
                    <select name="responsible_person_id" class="form-select">
                        <option value="">-- لا يوجد (اختياري) --</option>
                        {% for user in users %}
                        <option value="{{ user.user_id }}">
                            👤 {{ user.full_name }} {% if user.department %}({{ user.department }}){% endif %}
                        </option>
                        {% endfor %}
                    </select>
                    <span class="form-hint">من سيتابع هذه المعاملة؟</span>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        من سيستلم التنبيهات؟
                    </label>
                    <div class="recipients-list">
                        {% for user in users %}
                        <div class="recipient-item">
                            <input type="checkbox" 
                                   name="reminder_recipients[]" 
                                   value="{{ user.user_id }}" 
                                   id="recipient_{{ user.user_id }}">
                            <label for="recipient_{{ user.user_id }}">
                                👤 {{ user.full_name }} {% if user.department %}({{ user.department }}){% endif %}
                            </label>
                        </div>
                        {% endfor %}
                    </div>
                    <span class="form-hint">يمكنك اختيار أكثر من شخص</span>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        ملاحظات إضافية
                    </label>
                    <textarea name="description" class="form-textarea" 
                              placeholder="أي معلومات إضافية عن المعاملة..."></textarea>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">
                        ✅ حفظ المعاملة
                    </button>
                    <a href="/" class="btn btn-secondary">
                        ❌ إلغاء
                    </a>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        const subtypesData = {{ subtypes_json | safe }};
        
        function loadSubtypes(mainTypeId) {
            const subtypesGroup = document.getElementById('subtypesGroup');
            const subTypeSelect = document.getElementById('subType');
            const finalTypeInput = document.getElementById('finalTypeId');
            
            subTypeSelect.innerHTML = '<option value="">-- اختر التفصيل --</option>';
            
            if (!mainTypeId) {
                subtypesGroup.classList.remove('show');
                finalTypeInput.value = '';
                return;
            }
            
            const subtypes = subtypesData[mainTypeId] || [];
            
            if (subtypes.length > 0) {
                subtypes.forEach(subtype => {
                    const option = document.createElement('option');
                    option.value = subtype.id;
                    option.textContent = `${subtype.icon} ${subtype.name}`;
                    subTypeSelect.appendChild(option);
                });
                
                subtypesGroup.classList.add('show');
                finalTypeInput.value = '';
            } else {
                subtypesGroup.classList.remove('show');
                finalTypeInput.value = mainTypeId;
            }
        }
        
        document.getElementById('subType').addEventListener('change', function() {
            const finalTypeInput = document.getElementById('finalTypeId');
            finalTypeInput.value = this.value;
        });
        
        document.getElementById('transactionForm').addEventListener('submit', function(e) {
            const finalTypeId = document.getElementById('finalTypeId').value;
            
            if (!finalTypeId) {
                e.preventDefault();
                alert('❌ يرجى اختيار نوع المعاملة بالكامل');
                return false;
            }
        });
    </script>
</body>
</html>
    """
    
    return render_template_string(
        html,
        main_types=main_types,
        users=users,
        subtypes_json=subtypes_json,
        datetime=datetime
    )

# ==================== عرض معاملة واحدة ====================

@app.route('/transaction/<int:transaction_id>')
def view_transaction(transaction_id):
    """عرض تفاصيل معاملة"""
    transaction = db.get_transaction(transaction_id)
    
    if not transaction:
        return "المعاملة غير موجودة", 404
    
    return jsonify(transaction)

# ==================== Dashboard ====================

@app.route('/dashboard')
def dashboard():
    """لوحة التحكم"""
    return jsonify({
        'message': 'Dashboard قيد التطوير',
        'stats': db.get_stats()
    })

# ==================== API ====================

@app.route('/api/v1/transactions')
def api_transactions():
    """API: جلب المعاملات"""
    transactions = db.get_active_transactions()
    return jsonify(transactions)

@app.route('/api/v1/stats')
def api_stats():
    """API: الإحصائيات"""
    return jsonify(db.get_stats())

@app.route('/api/v1/docs')
def api_docs():
    """توثيق API"""
    return jsonify({
        'version': '1.0',
        'endpoints': {
            '/api/v1/transactions': 'GET - جلب جميع المعاملات',
            '/api/v1/stats': 'GET - الإحصائيات',
            '/health': 'GET - فحص الصحة'
        }
    })

# ==================== تشغيل الموقع ====================

def run_web():
    """تشغيل خادم الويب"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_web()
