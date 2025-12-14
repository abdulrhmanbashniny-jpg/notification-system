"""
ملف اختبار شامل لـ API
يمكنك تشغيله محلياً أو على Render
"""

import requests
import json
from datetime import datetime, timedelta

# ==================== الإعدادات ====================
API_BASE_URL = "http://localhost:5001/api/v1"  # غيّره إلى رابط Render عند النشر
# API_BASE_URL = "https://your-app.onrender.com/api/v1"  # استخدم هذا عند النشر

API_KEY = "your-api-key-here"  # ضع API Key الخاص بك

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# ==================== دوال مساعدة ====================

def print_result(test_name, response):
    """طباعة نتيجة الاختبار بشكل جميل"""
    print(f"\n{'='*60}")
    print(f"🧪 اختبار: {test_name}")
    print(f"📊 الحالة: {response.status_code}")
    print(f"📄 الاستجابة:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print(f"{'='*60}\n")

# ==================== الاختبارات ====================

def test_1_health_check():
    """اختبار 1: فحص صحة API"""
    print("\n🔍 اختبار 1: فحص صحة API")
    response = requests.get(f"{API_BASE_URL}/health")
    print_result("Health Check", response)
    return response.status_code == 200

def test_2_get_docs():
    """اختبار 2: جلب التوثيق"""
    print("\n📚 اختبار 2: جلب التوثيق")
    response = requests.get(f"{API_BASE_URL}/docs")
    print_result("API Documentation", response)
    return response.status_code == 200

def test_3_get_stats():
    """اختبار 3: جلب الإحصائيات"""
    print("\n📊 اختبار 3: جلب الإحصائيات")
    response = requests.get(f"{API_BASE_URL}/stats", headers=HEADERS)
    print_result("Statistics", response)
    return response.status_code == 200

def test_4_get_users():
    """اختبار 4: جلب المستخدمين"""
    print("\n👥 اختبار 4: جلب المستخدمين")
    response = requests.get(f"{API_BASE_URL}/users", headers=HEADERS)
    print_result("Get Users", response)
    return response.status_code == 200

def test_5_add_user():
    """اختبار 5: إضافة مستخدم جديد"""
    print("\n➕ اختبار 5: إضافة مستخدم جديد")
    new_user = {
        "user_id": 999999999,
        "phone_number": "+966500000000",
        "full_name": "مستخدم تجريبي من API",
        "is_admin": 0
    }
    response = requests.post(f"{API_BASE_URL}/users", 
                            headers=HEADERS, 
                            json=new_user)
    print_result("Add User", response)
    return response.status_code in [200, 201]

def test_6_get_transactions():
    """اختبار 6: جلب المعاملات"""
    print("\n📋 اختبار 6: جلب جميع المعاملات")
    response = requests.get(f"{API_BASE_URL}/transactions", headers=HEADERS)
    print_result("Get Transactions", response)
    return response.status_code == 200

def test_7_add_transaction():
    """اختبار 7: إضافة معاملة جديدة"""
    print("\n➕ اختبار 7: إضافة معاملة جديدة")
    
    # تاريخ بعد 10 أيام من الآن
    end_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    
    new_transaction = {
        "transaction_type_id": 1,
        "user_id": 123456789,
        "title": "معاملة تجريبية من API - اختبار",
        "data": {
            "test": True,
            "created_via": "API Test Script",
            "timestamp": datetime.now().isoformat()
        },
        "end_date": end_date
    }
    
    response = requests.post(f"{API_BASE_URL}/transactions",
                            headers=HEADERS,
                            json=new_transaction)
    print_result("Add Transaction", response)
    
    # حفظ ID المعاملة للاختبارات القادمة
    if response.status_code in [200, 201]:
        global TRANSACTION_ID
        TRANSACTION_ID = response.json().get('transaction_id')
        print(f"✅ تم إنشاء المعاملة بـ ID: {TRANSACTION_ID}")
    
    return response.status_code in [200, 201]

def test_8_get_single_transaction():
    """اختبار 8: جلب معاملة واحدة"""
    print("\n🔍 اختبار 8: جلب معاملة محددة")
    
    if 'TRANSACTION_ID' not in globals():
        print("⚠️ لا يوجد ID معاملة من الاختبار السابق")
        return False
    
    response = requests.get(f"{API_BASE_URL}/transactions/{TRANSACTION_ID}",
                           headers=HEADERS)
    print_result(f"Get Transaction #{TRANSACTION_ID}", response)
    return response.status_code == 200

def test_9_update_transaction():
    """اختبار 9: تحديث معاملة"""
    print("\n✏️ اختبار 9: تحديث معاملة")
    
    if 'TRANSACTION_ID' not in globals():
        print("⚠️ لا يوجد ID معاملة من الاختبار السابق")
        return False
    
    update_data = {
        "title": "معاملة مُحدثة - تم التعديل عبر API",
        "end_date": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
    }
    
    response = requests.put(f"{API_BASE_URL}/transactions/{TRANSACTION_ID}",
                           headers=HEADERS,
                           json=update_data)
    print_result(f"Update Transaction #{TRANSACTION_ID}", response)
    return response.status_code == 200

def test_10_ai_analyze():
    """اختبار 10: تحليل ذكي بواسطة AI"""
    print("\n🤖 اختبار 10: تحليل ذكي AI")
    response = requests.get(f"{API_BASE_URL}/ai/analyze", headers=HEADERS)
    print_result("AI Analysis", response)
    return response.status_code == 200

def test_11_ai_schedule():
    """اختبار 11: جدولة ذكية AI"""
    print("\n🤖 اختبار 11: جدولة ذكية AI")
    response = requests.get(f"{API_BASE_URL}/ai/schedule", headers=HEADERS)
    print_result("AI Smart Scheduling", response)
    return response.status_code == 200

def test_12_ai_predict():
    """اختبار 12: توقع التأخيرات AI"""
    print("\n🤖 اختبار 12: توقع التأخيرات AI")
    
    if 'TRANSACTION_ID' not in globals():
        print("⚠️ لا يوجد ID معاملة من الاختبار السابق")
        return False
    
    response = requests.get(f"{API_BASE_URL}/ai/predict/{TRANSACTION_ID}",
                           headers=HEADERS)
    print_result(f"AI Predict Delays for #{TRANSACTION_ID}", response)
    return response.status_code == 200

def test_13_delete_transaction():
    """اختبار 13: حذف معاملة"""
    print("\n🗑️ اختبار 13: حذف معاملة")
    
    if 'TRANSACTION_ID' not in globals():
        print("⚠️ لا يوجد ID معاملة من الاختبار السابق")
        return False
    
    response = requests.delete(f"{API_BASE_URL}/transactions/{TRANSACTION_ID}",
                              headers=HEADERS)
    print_result(f"Delete Transaction #{TRANSACTION_ID}", response)
    return response.status_code == 200

def test_14_webhook():
    """اختبار 14: Webhook"""
    print("\n🔗 اختبار 14: استقبال Webhook")
    
    webhook_data = {
        "type": 1,
        "user_id": 123456789,
        "title": "معاملة من Webhook خارجي",
        "metadata": {
            "source": "external_system",
            "webhook_test": True
        },
        "end_date": (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    }
    
    response = requests.post(f"{API_BASE_URL}/webhook/transaction",
                            headers=HEADERS,
                            json=webhook_data)
    print_result("Webhook Test", response)
    return response.status_code in [200, 201]

def test_15_unauthorized():
    """اختبار 15: محاولة دخول غير مصرح"""
    print("\n🔒 اختبار 15: محاولة دخول بدون API Key")
    response = requests.get(f"{API_BASE_URL}/transactions")
    print_result("Unauthorized Access", response)
    return response.status_code == 401

# ==================== تشغيل جميع الاختبارات ====================

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*60)
    print("🚀 بدء تشغيل جميع اختبارات API")
    print("="*60)
    
    tests = [
        test_1_health_check,
        test_2_get_docs,
        test_3_get_stats,
        test_4_get_users,
        test_5_add_user,
        test_6_get_transactions,
        test_7_add_transaction,
        test_8_get_single_transaction,
        test_9_update_transaction,
        test_10_ai_analyze,
        test_11_ai_schedule,
        test_12_ai_predict,
        test_13_delete_transaction,
        test_14_webhook,
        test_15_unauthorized
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append({
                'name': test.__name__,
                'passed': result
            })
        except Exception as e:
            print(f"❌ خطأ في {test.__name__}: {str(e)}")
            results.append({
                'name': test.__name__,
                'passed': False
            })
    
    # ==================== النتائج النهائية ====================
    print("\n" + "="*60)
    print("📊 النتائج النهائية")
    print("="*60)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    for result in results:
        status = "✅ نجح" if result['passed'] else "❌ فشل"
        print(f"{status} - {result['name']}")
    
    print("\n" + "="*60)
    print(f"📈 النتيجة: {passed}/{total} اختبار نجح ({(passed/total)*100:.1f}%)")
    print("="*60 + "\n")

# ==================== تشغيل ====================

if __name__ == "__main__":
    run_all_tests()
