import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
from database import Database

class AIAssistant:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.db = Database()
    
    def query(self, user_message, user_id):
        """إرسال استفسار للذكاء الاصطناعي مع بيانات المستخدم"""
        
        # جلب معلومات المستخدم ومعاملاته
        user = self.db.get_user(user_id)
        transactions = self.db.get_active_transactions(user_id=user_id)
        
        # بناء السياق للذكاء الاصطناعي
        context = self._build_context(user, transactions)
        
        # إعداد الرسالة
        messages = [
            {
                "role": "system",
                "content": f"""أنت مساعد ذكي لنظام إدارة المعاملات والتنبيهات. 
                مهمتك مساعدة المستخدم في الاستفسار عن معاملاته وتقديم معلومات دقيقة.
                
                معلومات المستخدم والمعاملات:
                {context}
                
                أجب باللغة العربية بشكل واضح ومختصر."""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        # إرسال الطلب للـ API
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي. الكود: {response.status_code}"
        
        except Exception as e:
            return f"عذراً، حدث خطأ: {str(e)}"
    
    def _build_context(self, user, transactions):
        """بناء السياق من بيانات المستخدم"""
        context = f"اسم المستخدم: {user.get('full_name', 'غير محدد')}\n\n"
        
        if transactions:
            context += "المعاملات النشطة:\n"
            for trans in transactions:
                context += f"- {trans['title']} (النوع: {trans['type_name']}, تنتهي في: {trans.get('end_date', 'غير محدد')})\n"
        else:
            context += "لا توجد معاملات نشطة حالياً.\n"
        
        return context
    
    def add_transaction_via_chat(self, user_message, user_id):
        """إضافة معاملة عبر المحادثة الطبيعية"""
        
        messages = [
            {
                "role": "system",
                "content": """أنت مساعد لاستخراج معلومات المعاملة من رسالة المستخدم.
                استخرج المعلومات التالية إذا وُجدت:
                - نوع المعاملة (عقد_عمل، إجازة_موظف، استمارة_سيارة، ترخيص، جلسة_قضائية، أخرى)
                - العنوان
                - التاريخ
                - أي معلومات إضافية
                
                أرجع النتيجة بصيغة JSON فقط."""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.3
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_data = result['choices'][0]['message']['content']
                return json.loads(extracted_data)
            else:
                return None
        
        except Exception as e:
            return None
