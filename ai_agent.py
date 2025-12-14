import os
import requests
from datetime import datetime, timedelta
from database_supabase import Database

class AIAgent:
    """وكيل ذكي لتحليل المعاملات وتقديم توصيات"""
    
    def __init__(self):
        self.db = Database()
        self.deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    
    def analyze_transactions(self, user_id=None):
        """تحليل ذكي للمعاملات"""
        transactions = self.db.get_active_transactions(user_id=user_id)
        today = datetime.now().date()
        
        analysis = {
            'total': len(transactions),
            'critical': [],
            'recommendations': [],
            'patterns': {}
        }
        
        for trans in transactions:
            try:
                end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
                days_left = (end_date - today).days
                
                if days_left <= 3:
                    analysis['critical'].append({
                        'id': trans['transaction_id'],
                        'title': trans['title'],
                        'days_left': days_left,
                        'urgency': 'عاجل جداً'
                    })
            except:
                pass
        
        # توصيات ذكية
        if len(analysis['critical']) > 5:
            analysis['recommendations'].append({
                'type': 'workload',
                'message': 'لديك عدد كبير من المعاملات العاجلة. نوصي بإعادة جدولة بعضها.'
            })
        
        return analysis
    
    def predict_delays(self, transaction_id):
        """توقع التأخيرات بناءً على البيانات التاريخية"""
        # يمكن تطويره لاحقاً باستخدام ML
        return {
            'probability': 0.15,
            'factors': ['عدد المعاملات الحالية', 'الموسم']
        }
    
    def smart_scheduling(self, transactions):
        """جدولة ذكية للمعاملات"""
        # ترتيب حسب الأولوية
        sorted_trans = sorted(
            transactions,
            key=lambda x: datetime.strptime(x['end_date'], '%Y-%m-%d')
        )
        
        return {
            'today': [t for t in sorted_trans if self._is_today(t['end_date'])],
            'this_week': [t for t in sorted_trans if self._is_this_week(t['end_date'])],
            'upcoming': [t for t in sorted_trans if not self._is_this_week(t['end_date'])]
        }
    
    def _is_today(self, date_str):
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date == datetime.now().date()
    
    def _is_this_week(self, date_str):
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        week_end = datetime.now().date() + timedelta(days=7)
        return date <= week_end
