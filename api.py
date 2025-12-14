from flask import Flask, jsonify, request
from database_supabase import Database
from datetime import datetime
import os

# ==================== استيراد AI Agent ====================
from ai_agent import AIAgent

api = Flask(__name__)
api.secret_key = os.environ.get('API_SECRET_KEY', 'your-secret-key-here')
db = Database()
ai_agent = AIAgent()  # ✅ إضافة AI Agent

# Middleware للمصادقة
def require_api_key(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== المعاملات ====================

@api.route('/api/v1/transactions', methods=['GET'])
@require_api_key
def get_transactions():
    """جلب جميع المعاملات"""
    user_id = request.args.get('user_id', type=int)
    transactions = db.get_active_transactions(user_id=user_id)
    return jsonify({
        'success': True,
        'count': len(transactions),
        'data': transactions
    })

@api.route('/api/v1/transactions/<int:transaction_id>', methods=['GET'])
@require_api_key
def get_transaction(transaction_id):
    """جلب معاملة واحدة"""
    transaction = db.get_transaction(transaction_id)
    if not transaction:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    return jsonify({'success': True, 'data': transaction})

@api.route('/api/v1/transactions', methods=['POST'])
@require_api_key
def create_transaction():
    """إضافة معاملة جديدة"""
    data = request.json
    
    required_fields = ['transaction_type_id', 'user_id', 'title', 'end_date']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    transaction_id = db.add_transaction(
        transaction_type_id=data['transaction_type_id'],
        user_id=data['user_id'],
        title=data['title'],
        data=data.get('data', {}),
        end_date=data['end_date']
    )
    
    if transaction_id:
        return jsonify({'success': True, 'transaction_id': transaction_id}), 201
    return jsonify({'success': False, 'error': 'Failed to create transaction'}), 500

@api.route('/api/v1/transactions/<int:transaction_id>', methods=['PUT'])
@require_api_key
def update_transaction(transaction_id):
    """تحديث معاملة"""
    data = request.json
    success = db.update_transaction(
        transaction_id=transaction_id,
        title=data.get('title'),
        end_date=data.get('end_date'),
        data=data.get('data')
    )
    
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to update transaction'}), 500

@api.route('/api/v1/transactions/<int:transaction_id>', methods=['DELETE'])
@require_api_key
def delete_transaction(transaction_id):
    """حذف معاملة"""
    success = db.delete_transaction(transaction_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete transaction'}), 500

# ==================== المستخدمين ====================

@api.route('/api/v1/users', methods=['GET'])
@require_api_key
def get_users():
    """جلب جميع المستخدمين"""
    users = db.get_all_users()
    return jsonify({'success': True, 'count': len(users), 'data': users})

@api.route('/api/v1/users/<int:user_id>', methods=['GET'])
@require_api_key
def get_user(user_id):
    """جلب مستخدم"""
    user = db.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    return jsonify({'success': True, 'data': user})

@api.route('/api/v1/users', methods=['POST'])
@require_api_key
def create_user():
    """إضافة مستخدم"""
    data = request.json
    success = db.add_user(
        user_id=data['user_id'],
        phone_number=data['phone_number'],
        full_name=data['full_name'],
        is_admin=data.get('is_admin', 0)
    )
    
    if success:
        return jsonify({'success': True}), 201
    return jsonify({'success': False, 'error': 'Failed to create user'}), 500

# ==================== الإحصائيات ====================

@api.route('/api/v1/stats', methods=['GET'])
@require_api_key
def get_stats():
    """إحصائيات النظام"""
    transactions = db.get_active_transactions()
    users = db.get_all_users()
    
    today = datetime.now().date()
    critical = 0
    warning = 0
    
    for trans in transactions:
        try:
            end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
            days_left = (end_date - today).days
            if days_left <= 3:
                critical += 1
            elif days_left <= 7:
                warning += 1
        except:
            pass
    
    return jsonify({
        'success': True,
        'data': {
            'total_transactions': len(transactions),
            'total_users': len(users),
            'critical_transactions': critical,
            'warning_transactions': warning,
            'safe_transactions': len(transactions) - critical - warning
        }
    })

# ==================== Webhooks ====================

@api.route('/api/v1/webhook/transaction', methods=['POST'])
@require_api_key
def webhook_transaction():
    """استقبال webhooks من أنظمة خارجية"""
    data = request.json
    
    # معالجة البيانات وإضافة المعاملة
    transaction_id = db.add_transaction(
        transaction_type_id=data['type'],
        user_id=data['user_id'],
        title=data['title'],
        data=data.get('metadata', {}),
        end_date=data['end_date']
    )
    
    if transaction_id:
        # إرسال تنبيه تليجرام (اختياري)
        return jsonify({'success': True, 'transaction_id': transaction_id}), 201
    
    return jsonify({'success': False}), 500

# ==================== AI Agent Endpoints ✨ ====================

@api.route('/api/v1/ai/analyze', methods=['GET'])
@require_api_key
def ai_analyze():
    """تحليل ذكي بواسطة AI"""
    user_id = request.args.get('user_id', type=int)
    analysis = ai_agent.analyze_transactions(user_id=user_id)
    return jsonify({'success': True, 'analysis': analysis})

@api.route('/api/v1/ai/schedule', methods=['GET'])
@require_api_key
def ai_schedule():
    """جدولة ذكية"""
    transactions = db.get_active_transactions()
    schedule = ai_agent.smart_scheduling(transactions)
    return jsonify({'success': True, 'schedule': schedule})

@api.route('/api/v1/ai/predict/<int:transaction_id>', methods=['GET'])
@require_api_key
def ai_predict(transaction_id):
    """توقع التأخيرات"""
    prediction = ai_agent.predict_delays(transaction_id)
    return jsonify({'success': True, 'prediction': prediction})

# ==================== Health Check ====================

@api.route('/api/v1/health', methods=['GET'])
def health_check():
    """فحص صحة API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api.route('/api/v1/docs', methods=['GET'])
def api_docs():
    """توثيق API"""
    docs = {
        'version': '1.0.0',
        'base_url': '/api/v1',
        'authentication': 'API Key in X-API-Key header',
        'endpoints': {
            'GET /transactions': 'جلب جميع المعاملات',
            'GET /transactions/:id': 'جلب معاملة واحدة',
            'POST /transactions': 'إضافة معاملة',
            'PUT /transactions/:id': 'تحديث معاملة',
            'DELETE /transactions/:id': 'حذف معاملة',
            'GET /users': 'جلب المستخدمين',
            'GET /users/:id': 'جلب مستخدم',
            'POST /users': 'إضافة مستخدم',
            'GET /stats': 'الإحصائيات',
            'POST /webhook/transaction': 'استقبال webhook',
            'GET /ai/analyze': '🤖 تحليل ذكي بواسطة AI',
            'GET /ai/schedule': '🤖 جدولة ذكية',
            'GET /ai/predict/:id': '🤖 توقع التأخيرات',
            'GET /health': 'فحص الصحة',
            'GET /docs': 'التوثيق'
        }
    }
    return jsonify(docs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    api.run(host='0.0.0.0', port=port, debug=False)
